from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Optional

from ..capabilities.resolver import CapabilitiesResolver
from ..context.tool_use import ToolUseContext
from ..events.bus import EventBus
from ..events.event_types import DoneEvent, ErrorEvent, Event, TokenEvent, ToolCallEvent, ToolResultEvent
from ..hooks import HookEvent
from ..models.protocol import ModelCallerProtocol
from ..tools.dispatcher import ToolDispatcher
from ..tools.pool import ToolPool

if TYPE_CHECKING:
    from ..capabilities.manager import CapabilityManager
    from ..tools.protocol import ToolProtocol
    from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

_MAX_TURNS = 50  # techo de seguridad para evitar loops infinitos


def _tool_schema(tool: "ToolProtocol") -> dict:
    return {"name": tool.name, "description": tool.description, "parameters": tool.input_schema}


def _as_reminder(content: str) -> str:
    """Envuelve el contenido de recall en `<system-reminder>` (espejo del canónico).

    El caller descarta `role:"system"`, así que el recall viaja como `role:"user"`;
    el marcado `<system-reminder>` le dice al modelo que es contexto del sistema, no
    una intervención del usuario."""
    return f"<system-reminder>\n{content.strip()}\n</system-reminder>"


class AgentLoop:
    """
    Loop agentico del runtime.

    Ciclo: hooks → inserta prompt → resuelve schemas → llama modelo →
    consume eventos → ejecuta tools → acumula → repite hasta DoneEvent sin tool_calls.

    Estado de registro: `ctx.messages`. Observación en vivo: si se inyecta un
    `event_bus`, el loop emite cada evento del stream (Token/ToolCall/Done/Error)
    y un `ToolResultEvent` tras cada dispatch. Esto separa estado (messages) de
    stream (bus), adaptando el modelo del canónico (que combina ambos en un yield).
    """

    def __init__(
        self,
        *,
        model_caller: Optional[ModelCallerProtocol] = None,
        tool_registry: "Optional[ToolRegistry]" = None,
        capability_manager: "Optional[CapabilityManager]" = None,
        capabilities_resolver: Optional[CapabilitiesResolver] = None,
        tool_dispatcher: Optional[ToolDispatcher] = None,
        event_bus: Optional[EventBus] = None,
        hook_runner: Optional[Any] = None,
        model_id: str = "",
        system_prompt_override: str = "",
        agent_allowed_tools: tuple[str, ...] = (),
    ) -> None:
        self._model_caller = model_caller
        self._tool_registry = tool_registry
        self._capability_manager = capability_manager
        self._capabilities_resolver = capabilities_resolver
        self._tool_dispatcher = tool_dispatcher
        self._event_bus = event_bus
        self._hook_runner = hook_runner
        self._model_id = model_id
        # Subagente especializado (homologación subagent_type): system prompt propio que
        # REEMPLAZA el base del padre (espejo getAgentSystemPrompt → [agentPrompt]); `""`
        # = heredar el base. `agent_allowed_tools` restringe el pool a ese subconjunto
        # (espejo resolveAgentTools); `()` o `("*",)` = todas.
        self._system_prompt_override = system_prompt_override
        self._agent_allowed_tools = agent_allowed_tools
        self._turn_start_hooks: list[Callable[[], Coroutine[Any, Any, None]]] = []

    def _build_tool_pool(self, ctx: ToolUseContext) -> ToolPool:
        """Ensambla el pool del turno (= `assembleToolPool`): native (filtrado por
        kind) + capability. El registry nativo es solo input; un subagente unattended
        recibe solo tools `safe_for_background` (B3)."""
        native: list["ToolProtocol"] = []
        if self._tool_registry is not None:
            mode = "background" if ctx.is_subagent else "foreground"
            native = self._tool_registry.list_available(mode=mode)
        if self._capability_manager is not None:
            pool = self._capability_manager.build_tool_pool(native, ctx)
        else:
            pool = ToolPool(native_tools=native)
        return self._restrict_to_agent_tools(pool)

    def _restrict_to_agent_tools(self, pool: ToolPool) -> ToolPool:
        """Restringe el pool al subconjunto de un subagente especializado (espejo de
        `resolveAgentTools`). `()` o `("*",)` → sin restricción. El filtro aplica tanto al
        anuncio como a la ejecución, porque el dispatcher resuelve del mismo pool."""
        allowed = self._agent_allowed_tools
        if not allowed or "*" in allowed:
            return pool
        names = set(allowed)
        return ToolPool(
            native_tools=[t for t in pool.native_tools if t.name in names],
            capability_tools=[t for t in pool.capability_tools if t.name in names],
        )

    def _inject_recall(self, ctx: ToolUseContext) -> None:
        """Inyecta el recall del manager como `<system-reminder>` (role:"user").

        Dedup: no reinyecta un contenido ya presente en `ctx.messages` (espejo de
        `collectSurfacedMemories`). El manager agrega los `active_context` de todos
        los providers; el loop los rinde — los providers no conocen el formato de
        reminder ni el rol final."""
        if self._capability_manager is None:
            return
        existing = {m.get("content") for m in ctx.messages if m.get("role") == "user"}
        for msg in self._capability_manager.active_context(ctx):
            content = (msg.get("content") or "").strip()
            if not content:
                continue
            rendered = _as_reminder(content)
            if rendered in existing:
                continue
            ctx.messages.append({"role": "user", "content": rendered})
            existing.add(rendered)

    def _inject_deferred_tools_delta(self, ctx: ToolUseContext) -> None:
        """Anuncia al modelo los NOMBRES de las tools diferidas nuevas (MCP) como
        `<system-reminder>` (role:"user"), y retira las de servers desconectados.

        Sin esto el modelo no sabe que hay diferidas detrás de ToolSearch y nunca las
        busca → las tools MCP quedan invisibles. Espejo del `deferred_tools_delta`
        canónico; STATELESS: el delta se computa contra lo ya anunciado en `ctx.messages`,
        así no se re-anuncia dentro del run pero sí se refleja un alta/baja a mitad de
        sesión (ver `tools/deferred_delta.py`)."""
        if ctx.tool_pool is None:
            return
        from ..tools.deferred_delta import (
            compute_deferred_tools_delta,
            render_deferred_tools_delta,
        )

        pool = ctx.tool_pool.assemble(ctx.permission_context)
        delta = compute_deferred_tools_delta(pool, ctx.messages)
        if delta is None:
            return
        added, removed = delta
        rendered = _as_reminder(render_deferred_tools_delta(added, removed))
        ctx.messages.append({"role": "user", "content": rendered})

    def _schemas_for_turn(self, ctx: ToolUseContext) -> list[dict]:
        """Schemas anunciados al modelo, derivados del pool ensamblado.

        - Visibilidad homologada al canónico (getTools): el anuncio solo filtra por deny
          (`assemble()` ya quitó las denegadas) y por las diferidas no descubiertas.
          `requires_permission` NO controla visibilidad — una tool que pide permiso se
          anuncia igual; su gate vive en ejecución (dispatcher + hook PRE_TOOL_USE, espejo
          de checkPermissions), que es lo que hace alcanzable la aprobación HITL.
        - Diferidas (M3, espejo de `claude.ts`): las tools diferidas (MCP) NO se
          anuncian hasta que ToolSearch las descubre; ToolSearch solo se anuncia si
          hay diferidas que descubrir. La ejecución no se ve afectada (viven en el pool).
        """
        from ..tools.deferred import discovered_tool_names, is_deferred_tool
        from ..tools.native.tool_search import TOOL_SEARCH_TOOL_NAME

        pool = ctx.tool_pool.assemble(ctx.permission_context)
        deferred_names = {t.name for t in pool if is_deferred_tool(t)}
        tool_search_active = bool(deferred_names)
        discovered = discovered_tool_names(ctx)

        schemas: list[dict] = []
        for tool in pool:
            if tool.name == TOOL_SEARCH_TOOL_NAME:
                if not tool_search_active:
                    continue  # sin diferidas, no hay nada que buscar
            elif tool.name in deferred_names and tool.name not in discovered:
                continue  # diferida no descubierta → oculta hasta ToolSearch
            schemas.append(_tool_schema(tool))
        return schemas

    async def _emit(self, event: Event) -> None:
        if self._event_bus is not None:
            await self._event_bus.emit(event)

    # ------------------------------------------------------------------
    # DrainableLoopProtocol
    # ------------------------------------------------------------------

    def register_turn_start_hook(self, hook: Callable[[], Coroutine[Any, Any, None]]) -> None:
        self._turn_start_hooks.append(hook)

    async def _run_turn_start_hooks(self) -> None:
        for hook in self._turn_start_hooks:
            await hook()

    # ------------------------------------------------------------------
    # Ciclo principal
    # ------------------------------------------------------------------

    async def run(self, prompt: str, ctx: ToolUseContext) -> None:
        # Abort antes de empezar
        if ctx.stop and ctx.stop.is_set():
            return

        await self._run_turn_start_hooks()

        # Inserta el prompt como mensaje user
        ctx.messages.append({"role": "user", "content": prompt})

        if self._model_caller is None:
            logger.warning("AgentLoop.run: no hay model_caller — loop no puede ejecutar")
            return

        for _turn in range(_MAX_TURNS):
            if ctx.stop and ctx.stop.is_set():
                break

            ctx.turn_count += 1

            # Resuelve tools del turno. Modelo alineado al canónico: se ensambla un
            # único pool (native + capability) en ctx.tool_pool y los schemas se
            # derivan de él; la ejecución (dispatcher) resuelve del MISMO pool.
            if self._tool_registry is not None or self._capability_manager is not None:
                ctx.tool_pool = self._build_tool_pool(ctx)
                self._inject_deferred_tools_delta(ctx)
                tool_schemas = self._schemas_for_turn(ctx)
            elif self._capabilities_resolver is not None:
                # Path legacy (solo schemas): el dispatcher resuelve de ctx.tool_pool,
                # así que NO ejecuta tools por esta vía — solo las anuncia.
                resolved = await self._capabilities_resolver.resolve(ctx)
                tool_schemas = resolved.tool_schemas
            else:
                tool_schemas = []

            # Secciones de system prompt aportadas por los providers (memoria, etc.):
            # el runtime las ensambla; el caller las concatena al system prompt base.
            system_sections: list[str] = []
            if self._capability_manager is not None:
                system_sections = self._capability_manager.system_prompt_sections(ctx)
                # Canal de recall por turno: cada mensaje de `active_context` se rinde
                # como `role:"user"` envuelto en `<system-reminder>`, con dedup contra
                # la historia ya presente (la compactación, al recortar, rehabilita el
                # re-surface). Activa también Skills S3 sin tocar su provider.
                self._inject_recall(ctx)

            logger.debug(
                "AgentLoop turno %d: invocando modelo (%d tools, %d mensajes)",
                ctx.turn_count, len(tool_schemas), len(ctx.messages),
            )
            # Llama al modelo. `system_sections` se pasa solo si hay secciones:
            # robustez ante callers de terceros que aún no adoptan el kwarg (un
            # caller compatible con `ModelCallerProtocol` lo acepta con default None).
            complete_kwargs: dict[str, Any] = {"stop": ctx.stop, "model_id": self._model_id}
            if system_sections:
                complete_kwargs["system_sections"] = system_sections
            # Subagente especializado: su system prompt REEMPLAZA el base del caller
            # (espejo getAgentSystemPrompt). Solo se pasa si la def trae cuerpo; `""`
            # = heredar el base. Se pasa condicional por la misma robustez que system_sections.
            if self._system_prompt_override:
                complete_kwargs["system_override"] = self._system_prompt_override
            stream = await self._model_caller.complete(
                ctx.messages,
                tool_schemas,
                **complete_kwargs,
            )

            # Consume eventos del stream
            token_buffer: list[str] = []
            tool_calls: list[ToolCallEvent] = []
            done: Optional[DoneEvent] = None
            error: Optional[ErrorEvent] = None

            async for event in stream:
                await self._emit(event)  # observación en vivo
                if isinstance(event, TokenEvent):
                    token_buffer.append(event.content)
                elif isinstance(event, ToolCallEvent):
                    tool_calls.append(event)
                elif isinstance(event, DoneEvent):
                    done = event
                    break
                elif isinstance(event, ErrorEvent):
                    error = event
                    break

            logger.debug(
                "AgentLoop turno %d: respuesta (%d tokens, %d tool_calls, stop=%s)",
                ctx.turn_count, len(token_buffer), len(tool_calls),
                error.message if error is not None else getattr(done, "stop_reason", None),
            )

            # Maneja error
            if error is not None:
                logger.error("AgentLoop: error del modelo — %s", error.message)
                ctx.messages.append({"role": "assistant", "content": f"[error: {error.message}]"})
                break

            # Persiste respuesta del asistente
            assistant_content = "".join(token_buffer)
            if assistant_content or tool_calls:
                msg: dict = {"role": "assistant", "content": assistant_content}
                if tool_calls:
                    msg["tool_calls"] = [
                        {"id": tc.call_id, "function": {"name": tc.tool_name, "arguments": json.dumps(tc.tool_input)}}
                        for tc in tool_calls
                    ]
                ctx.messages.append(msg)

            # Ejecuta tool calls y acumula resultados. `_ends_turn`: una tool puede señalar que el
            # turno debe CERRAR tras ejecutarla (HITL multi-turno; p. ej. AskUserQuestion emite las
            # preguntas y cede el control al usuario — la respuesta llega en un turno nuevo).
            _ends_turn = False
            for tc in tool_calls:
                if self._tool_dispatcher is None:
                    ctx.messages.append({"role": "tool", "tool_call_id": tc.call_id, "content": "[no dispatcher]"})
                    continue
                # PreToolUse — gate inyectado por el consumidor (espejo de `canUseTool`
                # del canónico). El runtime dispara el punto; la POLÍTICA vive en el
                # hook del integrador: leer `app_state.native["plan_mode"]` para denegar
                # escrituras (candado de plan mode) o resolver una aprobación HITL y
                # conceder el permiso mutando `app_state.permissions`. Se honra
                # `block` → denegar sin ejecutar, y `modified_input` → reemplazar el input
                # (deny/updatedInput del gate canónico). `stop`/`additional_context` no se
                # consumen en este punto.
                tool_input = tc.tool_input
                if self._hook_runner is not None:
                    decision = await self._hook_runner.run(HookEvent.PRE_TOOL_USE, {
                        "tool_name": tc.tool_name,
                        "tool_input": tool_input,
                        "call_id": tc.call_id,
                        "ctx": ctx,
                    })
                    if decision.modified_input is not None:
                        tool_input = decision.modified_input
                    if decision.block:
                        content = decision.message or f"permiso denegado para '{tc.tool_name}'"
                        ctx.messages.append({"role": "tool", "tool_call_id": tc.call_id, "content": content})
                        await self._emit(ToolResultEvent(call_id=tc.call_id, result=content, is_error=True))
                        continue
                result = await self._tool_dispatcher.dispatch(
                    tool_name=tc.tool_name,
                    tool_input=tool_input,
                    ctx=ctx,
                )
                ctx.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.call_id,
                    "content": result.output,
                })
                await self._emit(ToolResultEvent(
                    call_id=tc.call_id,
                    result=result.output,
                    is_error=getattr(result, "is_error", False),
                ))
                # Aplica el context_modifier que la tool haya producido (skills →
                # allowed-tools/skill activa; worktree/plan_mode → estado nativo).
                # Convención: el modifier muta ctx in-place y lo retorna (no forka).
                modifier = getattr(result, "context_modifier", None)
                if modifier is not None:
                    try:
                        ctx = modifier(ctx) or ctx
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("AgentLoop: context_modifier de %s falló: %s", tc.tool_name, exc)
                if getattr(result, "ends_turn", False):
                    _ends_turn = True
                logger.debug(
                    "AgentLoop turno %d: tool %s(%s) -> %s",
                    ctx.turn_count, tc.tool_name, tc.tool_input,
                    str(result.output)[:160],
                )

            # Decide si continuar. `_ends_turn`: una tool pidió cerrar el turno (HITL multi-turno) →
            # no se re-llama al modelo; el control vuelve al consumidor para recabar la respuesta.
            if _ends_turn or done is None or done.stop_reason != "tool_calls":
                break

        else:
            logger.warning("AgentLoop: alcanzado límite de %d turnos", _MAX_TURNS)
