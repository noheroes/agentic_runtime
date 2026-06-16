from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Optional

from ..capabilities.resolver import CapabilitiesResolver
from ..context.tool_use import ToolUseContext
from ..events.bus import EventBus
from ..events.event_types import DoneEvent, ErrorEvent, Event, TokenEvent, ToolCallEvent, ToolResultEvent
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
        model_id: str = "",
    ) -> None:
        self._model_caller = model_caller
        self._tool_registry = tool_registry
        self._capability_manager = capability_manager
        self._capabilities_resolver = capabilities_resolver
        self._tool_dispatcher = tool_dispatcher
        self._event_bus = event_bus
        self._model_id = model_id
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
            return self._capability_manager.build_tool_pool(native, ctx)
        return ToolPool(native_tools=native)

    def _schemas_for_turn(self, ctx: ToolUseContext) -> list[dict]:
        """Schemas anunciados al modelo, derivados del pool ensamblado.

        Filtra por permiso (una tool que requiere permiso solo se anuncia si está
        permitida); `assemble()` ya quitó las denegadas. La proyección de diferidas
        (ToolSearch) es M3 — aquí todas las tools del pool son visibles."""
        allowed = ctx.permission_context.allowed_names()
        schemas: list[dict] = []
        for tool in ctx.tool_pool.assemble(ctx.permission_context):
            if tool.requires_permission and tool.name not in allowed:
                continue
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
                tool_schemas = self._schemas_for_turn(ctx)
            elif self._capabilities_resolver is not None:
                # Path legacy (solo schemas): el dispatcher resuelve de ctx.tool_pool,
                # así que NO ejecuta tools por esta vía — solo las anuncia.
                resolved = await self._capabilities_resolver.resolve(ctx)
                tool_schemas = resolved.tool_schemas
            else:
                tool_schemas = []
            logger.debug(
                "AgentLoop turno %d: invocando modelo (%d tools, %d mensajes)",
                ctx.turn_count, len(tool_schemas), len(ctx.messages),
            )
            # Llama al modelo
            stream = await self._model_caller.complete(
                ctx.messages,
                tool_schemas,
                stop=ctx.stop,
                model_id=self._model_id,
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

            # Ejecuta tool calls y acumula resultados
            for tc in tool_calls:
                if self._tool_dispatcher is None:
                    ctx.messages.append({"role": "tool", "tool_call_id": tc.call_id, "content": "[no dispatcher]"})
                    continue
                result = await self._tool_dispatcher.dispatch(
                    tool_name=tc.tool_name,
                    tool_input=tc.tool_input,
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
                logger.debug(
                    "AgentLoop turno %d: tool %s(%s) -> %s",
                    ctx.turn_count, tc.tool_name, tc.tool_input,
                    str(result.output)[:160],
                )

            # Decide si continuar
            if done is None or done.stop_reason != "tool_calls":
                break

        else:
            logger.warning("AgentLoop: alcanzado límite de %d turnos", _MAX_TURNS)
