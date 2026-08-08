from __future__ import annotations

import json
import logging
import time
from dataclasses import replace
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Optional

from ..capabilities.resolver import CapabilitiesResolver
from ..context.tool_use import ToolUseContext
from ..contracts.notifications import NotificationSink, apply_notification
from ..contracts.user_input import NoopUserInputProcessor, UserInputProcessor
from ..events.bus import EventBus
from ..events.event_types import (
    DoneEvent,
    ErrorEvent,
    Event,
    MessageEvent,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnStartEvent,
)
from ..hooks import HookEvent
from ..models.protocol import ModelCallerProtocol, ModelOptions
from ..tools.dispatcher import ToolDispatcher
from ..tools.pool import ToolPool
from .outcome import LoopEndReason, LoopOutcome

if TYPE_CHECKING:
    from ..capabilities.manager import CapabilityManager
    from ..tools.deferred_strategy import DeferredToolStrategy
    from ..tools.protocol import ToolProtocol
    from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

_MAX_TURNS = 50  # techo de seguridad por DEFECTO — `max_turns` del constructor lo sustituye


def _vacio(valor: Any) -> bool:
    """¿El campo viene sin poblar? (`FIND-LOOP-1`, ver `_adoptar_ctx_modificado`).

    Un fork ingenuo del ctx no deja los campos en `None`: los deja en su
    `default_factory` —lista vacía, dict vacío—, que es justo lo que hace que la
    pérdida sea invisible. Por eso «vacío» incluye el contenedor sin elementos.
    """
    if valor is None:
        return True
    if isinstance(valor, (list, dict, tuple, set, str)):
        return len(valor) == 0
    return False


def _aborted(ctx: ToolUseContext) -> bool:
    """`S2`: la señal se CONSULTA (`.aborted`), no se espera.

    Un único punto de lectura para los tres chequeos del loop (pre-run, por turno
    y **por evento del stream**). El de por evento es el que hace que el abort
    corte de verdad: se midió en esta ventana que sólo el provider `anthropic`
    de `agentic_models 0.2.0` mira la señal dentro de su iterador SSE; el camino
    Azure/Responses la mira **después** de terminar el stream. Luego el corte a
    mitad tiene que ser del runtime, o no lo hay.
    """
    return ctx.stop is not None and ctx.stop.aborted


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
        deferred_strategy: "Optional[DeferredToolStrategy]" = None,
        model_options: Optional[ModelOptions] = None,
        input_processor: Optional[UserInputProcessor] = None,
        notification_sink: Optional[NotificationSink] = None,
        max_turns: Optional[int] = None,
    ) -> None:
        self._model_caller = model_caller
        self._tool_registry = tool_registry
        self._capability_manager = capability_manager
        self._capabilities_resolver = capabilities_resolver
        self._tool_dispatcher = tool_dispatcher
        self._event_bus = event_bus
        self._hook_runner = hook_runner
        self._model_id = model_id
        # `S1` enriquecida (`C2`): lo que el integrador quiere pedirle al motor y el
        # runtime sólo transporta (razonamiento, muestreo, techo de tokens, metadata
        # opaca de `ID-7`). Vacío = el motor decide, como hasta ahora.
        self._model_options = model_options or ModelOptions()
        # Subagente especializado (homologación subagent_type): system prompt propio que
        # REEMPLAZA el base del padre (espejo getAgentSystemPrompt → [agentPrompt]); `""`
        # = heredar el base. `agent_allowed_tools` restringe el pool a ese subconjunto
        # (espejo resolveAgentTools); `()` o `("*",)` = todas.
        self._system_prompt_override = system_prompt_override
        self._agent_allowed_tools = agent_allowed_tools
        # Estrategia de carga diferida: inyectable (tests / selección explícita del
        # consumidor); si no, se resuelve una vez por la capability del modelo activo
        # (nativa si el provider la soporta, simulada en caso contrario).
        self._deferred_strategy_override = deferred_strategy
        self._deferred_strategy_cached: "Optional[DeferredToolStrategy]" = None
        self._turn_start_hooks: list[Callable[[], Coroutine[Any, Any, None]]] = []
        # Contador del sumidero (`_emit`). Divergencia declarada frente a A, que no
        # tiene `seq` porque ordena por cadena `parentUuid` + timestamp ISO.
        self._event_seq = 0
        # `S11` (`C4`/`GAP-01`): el preproceso de entrada deja de ser superficie
        # exportada sin consumidor. Default = passthrough, para que un runtime que no
        # inyecte nada se comporte exactamente como antes de existir la costura.
        self._input_processor: UserInputProcessor = input_processor or NoopUserInputProcessor()
        # `S21` (`C8`, CORE-GAP `H-5`): el canal de notificaciones que este loop DRENA al
        # arrancar. `None` = sin canal (el loop se comporta como antes de existir la
        # costura); el runtime inyecta el suyo, y ése es el call-site que faltaba.
        self._notification_sink = notification_sink
        # `02·A5`: el tope de vueltas era una constante de módulo, y `RuntimeTask.max_turns`
        # existía en el contrato **sin llegar a ningún sitio** (`05·FIND-EXEC5`). Ahora entra
        # por constructor; `None` = el techo de seguridad por defecto.
        self._max_turns = max_turns if max_turns is not None else _MAX_TURNS

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

    def _adoptar_ctx_modificado(
        self, devuelto: ToolUseContext, vivo: ToolUseContext, tool_name: str
    ) -> ToolUseContext:
        """Adopta el ctx de un `context_modifier` sin perder el estado del turno.

        `FIND-LOOP-1`. El canónico no tiene este agujero **por construcción**: su único
        modifier real deriva por spread (`modifiedContext = {...modifiedContext, …}`,
        `SkillTool.ts:773-800`), así que un fork no puede dejar campos atrás. En B el ctx
        es un modelo con `default_factory` en casi todo, luego `ToolUseContext(session_id=…)`
        construido desde cero es válido **y mudo**: el pool sale vacío y las tool calls que
        quedaban del turno mueren con «no encontrado en el tool pool», indistinguibles de
        una tool que el modelo se inventó.

        Dos garantías, y ninguna es heurística:

        - `tool_pool` se **repone**. Es estado del turno cuyo dueño es el loop (lo puebla
          en `_build_tool_pool`) y ningún modifier lo fija: restringir el toolset se hace
          por `app_state`, y el pool se re-deriva al turno siguiente — igual que en A,
          donde la restricción de un modifier tampoco alcanza a las calls ya en vuelo.
        - lo demás sólo se **avisa**. `stop`/`event_queue`/`storage`/`fs`/`exec_env` los
          cablea el integrador y el loop no es su dueño, así que no los repone; pero
          perderlos deja de ser silencioso, que era el adjetivo del hallazgo.

        `tool_pool` no necesita excluirse del barrido de perdidos: cuando se llega a él ya
        está repuesto, y un `ToolPool` no es contenedor, luego `_vacio` nunca lo marca. Una
        guarda explícita habría sido una línea que ninguna prueba podría enrojecer.
        """
        if devuelto is vivo:
            return devuelto
        devuelto.tool_pool = vivo.tool_pool
        perdidos = sorted(
            nombre
            for nombre in type(vivo).model_fields
            if _vacio(getattr(devuelto, nombre, None))
            and not _vacio(getattr(vivo, nombre, None))
        )
        if perdidos:
            logger.warning(
                "AgentLoop: el context_modifier de %s devolvió un ctx forkeado que "
                "no arrastra %s; el turno continúa con esos cables vacíos.",
                tool_name, ", ".join(perdidos),
            )
        return devuelto

    async def _inject_recall(self, ctx: ToolUseContext) -> None:
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
            await self._append(ctx, {"role": "user", "content": rendered}, origin="recall")
            existing.add(rendered)

    def _resolve_deferred_strategy(self) -> "DeferredToolStrategy":
        """Estrategia diferida del loop. Inyectada → se usa tal cual; si no, se resuelve
        UNA vez por la capability del modelo activo: nativa si el caller declara
        `supports_native_tool_search(model_id)`, simulada en caso contrario (default seguro
        para callers de terceros que no exponen la capability). Espejo de §4 del contrato:
        el runtime lee la capability del provider y elige el mecanismo."""
        if self._deferred_strategy_override is not None:
            return self._deferred_strategy_override
        if self._deferred_strategy_cached is None:
            from ..tools.deferred_strategy import (
                NativeDeferredStrategy,
                SimulatedDeferredStrategy,
            )

            native = False
            probe = getattr(self._model_caller, "supports_native_tool_search", None)
            if callable(probe):
                native = bool(probe(self._model_id))
            self._deferred_strategy_cached = (
                NativeDeferredStrategy() if native else SimulatedDeferredStrategy()
            )
        return self._deferred_strategy_cached

    async def _emit(self, event: Event, ctx: ToolUseContext) -> None:
        """**Sumidero único** de la costura pública — espejo de `insertMessageChain`
        (`sessionStorage.ts:993-1083`).

        `FIND-STREAM-1`: los cinco campos de identidad del `Event` llegaban SIEMPRE
        vacíos (`seq=0`, `ts=0.0`) porque ningún sitio de producción los poblaba, y el
        docstring del contrato afirmaba lo contrario. El canónico no le pide a cada
        factoría que recuerde los campos de sesión: los estampa en un solo choke point
        por el que pasa todo mensaje de salida. Éste es ese punto.

        El sellado es **incondicional**, no «sólo si está vacío». No es gusto: el
        comentario portante de `sessionStorage.ts:1049-1056` documenta que sellar
        condicionalmente reintroduce la identidad CRUZADA en cuanto un mensaje se
        reemite — llevaría la sesión del emisor original, no la de este turno.

        `ctx` es **obligatorio y posicional a propósito**: con default, un emisor que lo
        olvidara emitiría identidad vacía en silencio, que es exactamente el defecto
        que este sumidero paga.

        Divergencia declarada, no deuda (`L10`): A **no tiene `seq`** —ordena por la
        cadena `parentUuid` más el timestamp ISO, lexicográficamente ordenable
        (`sessionStorage.ts:4647-4650`)—. Aquí el bus entrega objetos, no una cadena
        enlazada persistida, así que el orden lo porta un contador del sumidero. Y `ts`
        se sella aquí, no en una factoría como en A (`messages.ts`), porque B no tiene
        capa de factorías que interponer.
        """
        if self._event_bus is None:
            return
        self._event_seq += 1
        await self._event_bus.emit(replace(
            event,
            task_id=ctx.task_id,
            agent_id=ctx.agent_id or "",
            session_id=ctx.session_id,
            seq=self._event_seq,
            ts=time.time(),
        ))

    async def _append(
        self, ctx: ToolUseContext, message: dict[str, Any], origin: str
    ) -> None:
        """Añade a la historia del turno **y** lo rinde por el stream público (`#10`).

        Espejo de la propiedad canónica que `query.ts` cumple 1→EOF: lo que se persiste
        es lo que se yieldea (`:1588`, `:1610`, `:1624`). Antes, todo lo que el runtime
        le INYECTA al modelo —anuncios de diferidas, recall, resultados de tools— entraba
        a `ctx.messages` y no salía por ninguna parte, así que el consumidor no veía nada
        de ello: justo donde vive el patrón de fallo dominante del barrido (B tiene el
        dato y no lo pone en ninguna lista que se vea).
        """
        ctx.messages.append(message)
        await self._emit(
            MessageEvent(
                role=str(message.get("role", "")),
                content=str(message.get("content", "")),
                origin=origin,
            ),
            ctx,
        )

    # ------------------------------------------------------------------
    # DrainableLoopProtocol
    # ------------------------------------------------------------------

    def register_turn_start_hook(self, hook: Callable[[], Coroutine[Any, Any, None]]) -> None:
        self._turn_start_hooks.append(hook)

    async def _run_turn_start_hooks(self) -> None:
        for hook in self._turn_start_hooks:
            await hook()

    def _drain_notifications(self, ctx: ToolUseContext) -> int:
        """`S21`/`H-5`: aplica al historial VIVO lo que los hijos dejaron en el canal.

        Paso PROPIO del loop, no un `root_turn_start_hook`. La razón está medida
        (`SEAMS §S21`, `AC-h3`/`AC-07`): los hooks devuelven corrutinas **de cero
        argumentos**, así que un integrador podía drenar (tiene la task) pero **no podía
        aplicar** —`ctx.messages` no le llega—, y la única firma que existía escribía
        sobre `session.messages`, que `_run_loop` reasigna al terminar ⇒ el XML se
        descartaba en silencio. Delegarlo no estaba incompleto: era imposible.

        Frecuencia: una vez por `run()` = una por prompt de usuario, que es la del
        canónico (las notificaciones entran como *attachment* junto al input,
        `query.ts:1631-1633`), no una por turno de modelo.

        Orden: **antes** del mensaje del usuario y de `_inject_recall`, porque son
        hechos ya ocurridos — el modelo debe leer que su subagente terminó antes de leer
        lo que el usuario le pide ahora.

        Sólo la RAÍZ drena. El fork hereda `session_id` y `scope` del padre
        (`_build_child`), así que la clave del canal `(scope, session_id)` es **la
        misma** para padre e hijo: un subagente que drenase se comería la
        notificación de su hermano y el padre no se enteraría nunca. En el canónico
        las notificaciones entran por el input del usuario, que sólo la raíz tiene.
        """
        if self._notification_sink is None or ctx.is_subagent:
            return 0
        scope_key = ctx.scope.key if ctx.scope is not None else ""
        drained = self._notification_sink.drain(scope_key, ctx.session_id)
        for notification in drained:
            apply_notification(ctx.messages, notification)
        if drained:
            logger.debug("AgentLoop: %d notificación(es) aplicadas al historial", len(drained))
        return len(drained)

    # ------------------------------------------------------------------
    # Ciclo principal
    # ------------------------------------------------------------------

    async def run(self, prompt: str, ctx: ToolUseContext) -> LoopOutcome:
        # Abort antes de empezar
        if _aborted(ctx):
            return LoopOutcome(LoopEndReason.ABORTED_PRE_RUN, ctx.turn_count)

        await self._run_turn_start_hooks()

        # `S21`/`H-5`: el drain que el docstring del canal afirmaba y nadie hacía.
        self._drain_notifications(ctx)

        # `S11` PRE-TURNO (`C4`, paga `GAP-01`). El orden es el del canónico: el
        # preproceso corre **antes** de que nada entre al historial, porque puede
        # reescribir el prompt, y puede resolverlo entero sin modelo.
        processed = await self._input_processor.process(prompt, ctx)

        # El mensaje del usuario entra al historial en los DOS caminos, corte incluido:
        # el canónico empuja `messagesFromUserInput` siempre (`QueryEngine.ts:431`) y sólo
        # después mira `shouldQuery` (`:556`). Un slash-command resuelto no borra de la
        # conversación que el usuario lo escribió.
        await self._append(ctx, {"role": "user", "content": processed.prompt}, origin="user")

        if processed.short_circuit:
            # Turno resuelto localmente: NO se llama al modelo. Lo ya resuelto se
            # persiste como turno del asistente para que el consumidor lo lea por el
            # mismo camino que cualquier otra respuesta (`_last_assistant_text`).
            text = processed.result_text or ""
            if text:
                await self._append(
                    ctx, {"role": "assistant", "content": text}, origin="short_circuit"
                )
            logger.debug("AgentLoop: `S11` cortó el turno sin ir al modelo")
            return LoopOutcome(LoopEndReason.SHORT_CIRCUIT, ctx.turn_count, text or None)

        if self._model_caller is None:
            logger.warning("AgentLoop.run: no hay model_caller — loop no puede ejecutar")
            return LoopOutcome(LoopEndReason.NO_MODEL_CALLER, ctx.turn_count)

        reason = LoopEndReason.COMPLETED
        detail: Optional[str] = None

        for _turn in range(self._max_turns):
            if _aborted(ctx):
                # Frontera de vuelta: espejo del chequeo que el canónico hace tras las
                # tools (`query.ts:1515`).
                reason = LoopEndReason.ABORTED_TOOLS
                break

            ctx.turn_count += 1

            # Resuelve tools del turno. Modelo alineado al canónico: se ensambla un
            # único pool (native + capability) en ctx.tool_pool y los schemas se
            # derivan de él; la ejecución (dispatcher) resuelve del MISMO pool.
            deferred_names: tuple[str, ...] = ()
            announcements: list[str] = []
            if self._tool_registry is not None or self._capability_manager is not None:
                ctx.tool_pool = self._build_tool_pool(ctx)
                pool = ctx.tool_pool.assemble(ctx.permission_context)
                plan = self._resolve_deferred_strategy().prepare_turn(ctx, pool)
                tool_schemas = plan.tool_schemas
                deferred_names = plan.deferred_names
                announcements = plan.announcements
            elif self._capabilities_resolver is not None:
                # Path legacy (solo schemas): el dispatcher resuelve de ctx.tool_pool,
                # así que NO ejecuta tools por esta vía — solo las anuncia.
                resolved = await self._capabilities_resolver.resolve(ctx)
                tool_schemas = resolved.tool_schemas
            else:
                tool_schemas = []

            # Frontera de turno, y el plan de tools como DATO (`#10`). Va ANTES de los
            # anuncios y por los TRES caminos: el consumidor sabe a qué turno pertenece
            # lo que viene después, igual que A rinde `{type:'stream_request_start'}` una
            # vez por iteración (`query.ts:337`). El `TurnToolPlan` se construía y se
            # tiraba: nada de lo que decidía salía de esta función.
            await self._emit(
                TurnStartEvent(
                    turn=ctx.turn_count,
                    tool_names=tuple(str(s.get("name", "")) for s in tool_schemas),
                    deferred_names=deferred_names,
                ),
                ctx,
            )
            for announcement in announcements:
                await self._append(
                    ctx,
                    {"role": "user", "content": _as_reminder(announcement)},
                    origin="deferred_delta",
                )

            # Secciones de system prompt aportadas por los providers (memoria, etc.):
            # el runtime las ensambla; el caller las concatena al system prompt base.
            system_sections: list[str] = []
            if self._capability_manager is not None:
                system_sections = self._capability_manager.system_prompt_sections(ctx)
                # Canal de recall por turno: cada mensaje de `active_context` se rinde
                # como `role:"user"` envuelto en `<system-reminder>`, con dedup contra
                # la historia ya presente (la compactación, al recortar, rehabilita el
                # re-surface). Activa también Skills S3 sin tocar su provider.
                await self._inject_recall(ctx)

            logger.debug(
                "AgentLoop turno %d: invocando modelo (%d tools, %d mensajes)",
                ctx.turn_count, len(tool_schemas), len(ctx.messages),
            )
            # Llama al modelo. `system_sections` se pasa solo si hay secciones:
            # robustez ante callers de terceros que aún no adoptan el kwarg (un
            # caller compatible con `ModelCallerProtocol` lo acepta con default None).
            complete_kwargs: dict[str, Any] = {"stop": ctx.stop, "model_id": self._model_id}
            # Sólo lo poblado: un caller de terceros que aún no adopte un kwarg de
            # la `S1` enriquecida no se rompe si nadie pidió esa opción.
            complete_kwargs.update(self._model_options.as_kwargs())
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

            aborted_mid_stream = False
            async for event in stream:
                # Corte a mitad de stream: se consulta ANTES de rendir el evento, así
                # que lo que llegó tras el abort no se emite ni se acumula. Es el
                # único punto de control que existe para el camino Azure/Responses.
                if _aborted(ctx):
                    aborted_mid_stream = True
                    break
                await self._emit(event, ctx)  # observación en vivo
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

            if aborted_mid_stream:
                # Se cierra el generador para que el provider suelte la conexión en vez
                # de quedarse consumiendo la respuesta que ya no le importa a nadie.
                aclose = getattr(stream, "aclose", None)
                if callable(aclose):
                    await aclose()
                abort_reason = ctx.stop.reason() if ctx.stop is not None else None
                logger.info("AgentLoop turno %d: abortado a mitad de stream (%s)",
                            ctx.turn_count, getattr(abort_reason, "value", abort_reason))
                # Lo parcial NO se registra como turno del asistente ni se despachan sus
                # tool calls: un turno abortado no dejó una respuesta, dejó un corte.
                reason = LoopEndReason.ABORTED_STREAMING
                detail = str(getattr(abort_reason, "value", abort_reason) or "")
                break

            logger.debug(
                "AgentLoop turno %d: respuesta (%d tokens, %d tool_calls, stop=%s)",
                ctx.turn_count, len(token_buffer), len(tool_calls),
                error.message if error is not None else getattr(done, "stop_reason", None),
            )

            # Maneja error
            if error is not None:
                logger.error("AgentLoop: error del modelo — %s", error.message)
                await self._append(
                    ctx,
                    {"role": "assistant", "content": f"[error: {error.message}]"},
                    origin="model_error",
                )
                reason = LoopEndReason.MODEL_ERROR
                detail = error.message
                break

            # Persiste respuesta del asistente
            assistant_content = "".join(token_buffer)
            if assistant_content or tool_calls:
                msg: dict[str, Any] = {"role": "assistant", "content": assistant_content}
                if tool_calls:
                    msg["tool_calls"] = [
                        {"id": tc.call_id, "function": {"name": tc.tool_name, "arguments": json.dumps(tc.tool_input)}}
                        for tc in tool_calls
                    ]
                await self._append(ctx, msg, origin="assistant")

            # Ejecuta tool calls y acumula resultados. `_ends_turn`: una tool puede señalar que el
            # turno debe CERRAR tras ejecutarla (HITL multi-turno; p. ej. AskUserQuestion emite las
            # preguntas y cede el control al usuario — la respuesta llega en un turno nuevo).
            _ends_turn = False
            for tc in tool_calls:
                if self._tool_dispatcher is None:
                    await self._append(
                        ctx,
                        {"role": "tool", "tool_call_id": tc.call_id, "content": "[no dispatcher]"},
                        origin="tool",
                    )
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
                        # Este append y el del resultado real NO emiten `MessageEvent`:
                        # ya viajan por el stream como `ToolResultEvent`, que además
                        # lleva `call_id` e `is_error`. Duplicarlos sería ruido, no
                        # cobertura.
                        ctx.messages.append({"role": "tool", "tool_call_id": tc.call_id, "content": content})
                        await self._emit(
                            ToolResultEvent(call_id=tc.call_id, result=content, is_error=True), ctx
                        )
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
                await self._emit(
                    ToolResultEvent(
                        call_id=tc.call_id,
                        result=result.output,
                        is_error=getattr(result, "is_error", False),
                    ),
                    ctx,
                )
                # Aplica el context_modifier que la tool haya producido (skills →
                # allowed-tools/skill activa; worktree/plan_mode → estado nativo).
                # La convención es mutar in-place y retornar, pero forkar está soportado
                # y ya NO cuesta el turno: `_adoptar_ctx_modificado` (`FIND-LOOP-1`).
                # Lectura del miembro DECLARADO en `ToolResult` (`FIND-TOOL4/A24` pagado):
                # antes se sondeaba por `getattr` porque el contrato no lo tenía y las tools
                # lo inyectaban por monkeypatch. El `getattr` sobre `result` se conserva sólo
                # donde el objeto puede no ser nuestro `ToolResult` (tools de terceros).
                modifier = result.context_modifier
                if modifier is not None:
                    try:
                        devuelto = modifier(ctx) or ctx
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("AgentLoop: context_modifier de %s falló: %s", tc.tool_name, exc)
                    else:
                        ctx = self._adoptar_ctx_modificado(devuelto, ctx, tc.tool_name)
                if result.ends_turn:
                    _ends_turn = True
                logger.debug(
                    "AgentLoop turno %d: tool %s(%s) -> %s",
                    ctx.turn_count, tc.tool_name, tc.tool_input,
                    str(result.output)[:160],
                )

            # Decide si continuar. `_ends_turn`: una tool pidió cerrar el turno (HITL multi-turno) →
            # no se re-llama al modelo; el control vuelve al consumidor para recabar la respuesta.
            if _ends_turn or done is None or done.stop_reason != "tool_calls":
                reason = LoopEndReason.ENDS_TURN if _ends_turn else LoopEndReason.COMPLETED
                break

        else:
            # Tope agotado sin que el modelo cerrara: el canónico lo distingue con su
            # propio reason-code y adjunta `max_turns_reached` (`query.ts:1705-1711`).
            logger.warning("AgentLoop: alcanzado límite de %d turnos", self._max_turns)
            reason = LoopEndReason.MAX_TURNS
            detail = str(self._max_turns)

        return LoopOutcome(reason, ctx.turn_count, detail)
