"""
LocalAgentRuntime — ejecución local sobre AgentLoop, sin dependencias externas.

Compone las primitivas nativas: AgentLoop + EventBus + ToolDispatcher +
CapabilitiesResolver + ModelCaller + TaskRegistry + HookRunner + StorageProtocol.
No conoce a ningún consumidor: la identidad llega como owner_id opaco en RuntimeTask
y el padre llega como ForkSnapshot nativo.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import TYPE_CHECKING, Any, AsyncIterator, Optional

from ...context.presentation import IdentityPresentation
from ...context.tool_use import ToolUseContext
from ...contracts.permissions import PermissionContext
from ...events.bus import EventBus
from ...events.event_types import DoneEvent, TokenEvent, ToolCallEvent, ToolResultEvent
from ...events.protocol import Event, EventHandler
from ...hooks import HookEvent, HookRunner
from ...loop.agent_loop import AgentLoop
from ...storage.protocol import StorageKeys, StorageProtocol
from ..agents import resolve_subagent_model
from ..fork import ForkContext, ForkPolicy, ForkSnapshot, RuntimeContextForker
from ..session import Session
from ..tasks.registry import InMemoryTaskRegistry, TaskRegistryProtocol
from ..tasks.status import TaskStatus
from .notification import BackgroundNotification, put_notification
from .summarizer import summarize_if_needed

if TYPE_CHECKING:
    from ...capabilities.resolver import CapabilitiesResolver
    from ...contracts.runtime import RuntimeTask
    from ...models.protocol import ModelCallerProtocol
    from ...tools.dispatcher import ToolDispatcher

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 300.0


def _last_assistant_text(messages: list) -> str:
    for m in reversed(messages):
        if isinstance(m, dict) and m.get("role") == "assistant":
            return m.get("content") or ""
    return ""


class LocalAgentRuntime:
    """AgentRuntime local que ejecuta cada task como un AgentLoop en un asyncio.Task."""

    def __init__(
        self,
        *,
        model_caller: "Optional[ModelCallerProtocol]" = None,
        tool_registry: Any = None,
        capability_manager: Any = None,
        capabilities_resolver: "Optional[CapabilitiesResolver]" = None,
        tool_dispatcher: "Optional[ToolDispatcher]" = None,
        task_registry: Optional[TaskRegistryProtocol] = None,
        hook_runner: Optional[HookRunner] = None,
        storage: Optional[StorageProtocol] = None,
        presentation: Any = None,
        exec_env: Any = None,
        small_llm: Any = None,
        background_result_max_chars: int = 2000,
        model_id: str = "",
        initial_allowed_tools: Optional[list[str]] = None,
        root_context_modifier: Any = None,
        root_turn_start_hooks: Any = None,
        stt: Any = None,
        tts: Any = None,
        agent_resolver: Any = None,
        default_timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._model_caller = model_caller
        self._tool_registry = tool_registry
        self._capability_manager = capability_manager
        self._capabilities_resolver = capabilities_resolver
        self._tool_dispatcher = tool_dispatcher
        self._task_registry = task_registry or InMemoryTaskRegistry()
        self._hook_runner = hook_runner
        self._storage = storage
        self._presentation = presentation
        self._exec_env = exec_env
        self._small_llm = small_llm
        self._max_chars = background_result_max_chars
        self._model_id = model_id
        self._initial_allowed_tools = list(initial_allowed_tools or [])
        # Seam de autoría per-request del ctx raíz por el consumidor (ver RuntimeConfig).
        self._root_context_modifier = root_context_modifier
        # Seam per-request de hooks de inicio de run de la raíz (ver RuntimeConfig).
        self._root_turn_start_hooks = root_turn_start_hooks
        # Resolver de definiciones de subagente (subagent_type → AgentDefinition) que
        # provee el host (espejo de options.agentDefinitions). None = sin agentes
        # especializados: el subagente corre como fork genérico heredando al padre.
        self._agent_resolver = agent_resolver
        # Primitivas de voz ya resueltas por el factory (None = canal inactivo).
        self._stt = stt
        self._tts = tts
        self._default_timeout = default_timeout

    @property
    def runtime_id(self) -> str:
        return "local"

    # ------------------------------------------------------------------
    # Ciclo de vida de capabilities (conecta/cierra providers: MCP, ...)
    # ------------------------------------------------------------------

    async def startup(self) -> None:
        """Arranca los providers de capabilities (p.ej. conecta servers MCP).

        Lo invoca el integrador antes de despachar tasks. Idempotente a nivel de
        manager; sin manager es no-op (runtime solo-nativo)."""
        if self._capability_manager is not None:
            await self._capability_manager.startup()

    async def shutdown(self) -> None:
        if self._capability_manager is not None:
            await self._capability_manager.shutdown()

    # ------------------------------------------------------------------
    # AgentRuntime
    # ------------------------------------------------------------------

    async def dispatch(
        self,
        task: "RuntimeTask",
        parent_snapshot: ForkSnapshot | None = None,
        *,
        on_event: EventHandler | None = None,
    ) -> str:
        reg_task = self._task_registry.register(
            description=task.description, session_id=task.session_id
        )
        task_id = reg_task.task_id
        asyncio_task = asyncio.ensure_future(
            self._run_loop(task_id, task, parent_snapshot, on_event=on_event)
        )
        self._task_registry.start(task_id, asyncio_task=asyncio_task)
        self._task_registry.arm_watchdog(task_id, task.timeout_seconds or self._default_timeout)
        logger.info("dispatched agent %s: %s", task_id, task.description)
        return task_id

    async def stream(
        self,
        task: "RuntimeTask",
        parent_snapshot: ForkSnapshot | None = None,
    ) -> AsyncIterator[Event]:
        """Despacha la task y produce sus eventos en vivo, en orden, hasta el cierre.

        Azúcar sobre `dispatch(on_event=...)`: un consumidor (p.ej. un transporte SSE)
        itera `async for ev in runtime.stream(task)`. El centinela se encola cuando la
        asyncio.Task del loop termina, después de que el loop emitió todos sus eventos
        (emit se awaitea dentro de run()), garantizando que no se pierde ninguno.
        """
        queue: asyncio.Queue = asyncio.Queue()
        sentinel = object()

        async def _sink(event: Event) -> None:
            queue.put_nowait(event)

        task_id = await self.dispatch(task, parent_snapshot, on_event=_sink)
        rec = self._task_registry.get(task_id)
        at = rec.asyncio_task if rec is not None else None
        if at is not None:
            at.add_done_callback(lambda _t: queue.put_nowait(sentinel))

        while True:
            event = await queue.get()
            if event is sentinel:
                return
            yield event

    def status(self, task_id: str) -> TaskStatus | None:
        rec = self._task_registry.get(task_id)
        return rec.status if rec else None

    async def cancel(self, task_id: str) -> bool:
        return self._task_registry.kill(task_id)

    def result(self, task_id: str) -> str | None:
        rec = self._task_registry.get(task_id)
        return rec.result if rec else None

    # ------------------------------------------------------------------
    # Ciclo de ejecución
    # ------------------------------------------------------------------

    def _build_child(self, task: "RuntimeTask", parent_snapshot: ForkSnapshot | None):
        if parent_snapshot is not None:
            policy = ForkPolicy(inherit_messages=task.fork_context)
            ctx = RuntimeContextForker().fork(
                ForkContext(prompt=task.prompt, policy=policy, parent_snapshot=parent_snapshot)
            )
            return ctx, parent_snapshot.session_id, parent_snapshot.subagent_depth + 1
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        # Identidad inyectable por el consumidor; el interno solo se genera si no viene
        # (simétrico para user_id y session_id), de modo que el runtime corra solo.
        session_id = task.session_id or f"sess_{uuid.uuid4().hex[:12]}"
        user_id = task.owner_id or f"user_{uuid.uuid4().hex[:12]}"
        ctx = ToolUseContext(session_id=session_id, user_id=user_id, agent_id=agent_id)
        # Seed de permisos del agente principal: sin esto, tools `requires_permission`
        # (p.ej. `write_file`, que la memoria necesita para guardar) quedan fuera del
        # pool en un agente autónomo. Los subagentes los heredan vía snapshot.
        if self._initial_allowed_tools:
            ctx = ctx.with_permissions(
                PermissionContext(always_allow_command=list(self._initial_allowed_tools))
            )
        return ctx, None, 0

    async def _resolve_prompt(self, task: "RuntimeTask", ctx: ToolUseContext) -> str:
        """Entrada por voz: si hay audio y el STT está activo, lo transcribe y usa
        la transcripción como prompt del turno. Ante fallo o transcripción vacía,
        cae al `task.prompt` — la voz no debe tumbar la task."""
        audio = task.audio_prompt
        if self._stt is None or audio is None:
            return task.prompt
        try:
            text = await self._stt.transcribe(audio, ctx)
        except Exception as exc:  # noqa: BLE001
            logger.warning("STT: transcripción falló: %s", exc)
            return task.prompt
        return text or task.prompt

    def _wire_tts(self, bus: EventBus, ctx: ToolUseContext) -> None:
        """Salida por voz: deriva el stream del asistente a la primitiva TTS de
        forma incremental. Solo el agente principal habla (los subagentes son
        internos). El texto pasa por el choke point de `PathPresentation` antes de
        salir — nunca se leen en voz alta rutas reales de infra."""
        if self._tts is None or ctx.is_subagent:
            return
        presentation = ctx.presentation or IdentityPresentation()

        async def _on_token(event: Event) -> None:
            text = presentation.sanitize_output(getattr(event, "content", ""))
            if not text:
                return
            try:
                await self._tts.speak(text, ctx)
            except Exception as exc:  # noqa: BLE001
                logger.warning("TTS: speak falló: %s", exc)

        async def _on_done(event: Event) -> None:
            # Fin del turno de habla (no un corte por tool_calls) → el integrador vacía.
            if getattr(event, "stop_reason", None) == "tool_calls":
                return
            try:
                await self._tts.flush(ctx)
            except Exception as exc:  # noqa: BLE001
                logger.warning("TTS: flush falló: %s", exc)

        bus.subscribe(TokenEvent, _on_token)
        bus.subscribe(DoneEvent, _on_done)

    def _make_bus(self, task_id: str, on_event: EventHandler | None = None) -> EventBus:
        bus = EventBus()

        async def _on_tool_call(event: ToolCallEvent) -> None:
            self._task_registry.push_event(task_id, {
                "type": "tool_start", "name": event.tool_name,
                "call_id": event.call_id, "args": event.tool_input,
            })

        async def _on_tool_result(event: ToolResultEvent) -> None:
            self._task_registry.push_event(task_id, {
                "type": "tool_result", "call_id": event.call_id,
                "is_error": event.is_error, "output": event.result[:2000],
            })

        bus.subscribe(ToolCallEvent, _on_tool_call)
        bus.subscribe(ToolResultEvent, _on_tool_result)
        if on_event is not None:
            bus.subscribe_all(on_event)
        return bus

    async def _fire_stop(self, task_id: str, task: "RuntimeTask", status: str,
                         result: str | None, duration_ms: int) -> None:
        if self._hook_runner is None:
            return
        await self._hook_runner.run(HookEvent.SUBAGENT_STOP, {
            "task_id": task_id, "description": task.description,
            "status": status, "result": result, "duration_ms": duration_ms,
        })

    def _notify(self, parent_user_id: str | None, parent_session_id: str | None,
                task: "RuntimeTask", task_id: str, status: str, text: str,
                final_text: str) -> None:
        if parent_session_id is None:
            return
        put_notification(BackgroundNotification(
            parent_user_id=parent_user_id or "", parent_session_id=parent_session_id,
            task_id=task_id, status=status,
            description=task.description, notification_text=text,
            final_text=final_text,
        ))

    async def _run_loop(
        self,
        task_id: str,
        task: "RuntimeTask",
        parent_snapshot: ForkSnapshot | None,
        on_event: EventHandler | None = None,
    ) -> None:
        t0 = time.monotonic()
        ctx, parent_session_id, subagent_depth = self._build_child(task, parent_snapshot)
        ctx.is_subagent = parent_snapshot is not None
        ctx.subagent_depth = subagent_depth  # visible a la tool Agent para topar el anidamiento
        ctx.presentation = self._presentation
        ctx.exec_env = self._exec_env
        # Autoría per-request del consumidor SOLO en la raíz (los subagentes heredan su
        # estado por el ForkSnapshot). Corre tras fijar los defaults para que el
        # consumidor pueda sembrar `app_state.native` y/o sobrescribir `presentation`.
        if self._root_context_modifier is not None and parent_snapshot is None:
            ctx = self._root_context_modifier(ctx, task)
        session = Session(session_id=ctx.session_id)
        session.metadata.subagent_depth = subagent_depth
        bus = self._make_bus(task_id, on_event)
        # Salida por voz: el TTS se suscribe al stream antes de arrancar el loop.
        self._wire_tts(bus, ctx)

        # Subagente especializado (homologación subagent_type): resuelve la definición
        # por su tipo (host-provided) y deriva modelo/system_prompt/tools de ELLA. El
        # nombre del agente es la LLAVE de la definición, nunca el model_id. Sin resolver
        # o sin tipo, el fork es genérico y hereda al padre.
        agent_def = None
        if task.subagent_type and self._agent_resolver is not None:
            agent_def = self._agent_resolver.resolve(task.subagent_type)
        if agent_def is not None:
            model_id = resolve_subagent_model(
                agent_def.model, self._model_id, task.model_override
            )
            system_prompt_override = agent_def.system_prompt
            agent_allowed_tools = tuple(agent_def.allowed_tools)
        else:
            model_id = task.model_override or self._model_id
            system_prompt_override = ""
            agent_allowed_tools = ()

        loop = AgentLoop(
            model_caller=self._model_caller,
            tool_registry=self._tool_registry,
            capability_manager=self._capability_manager,
            capabilities_resolver=self._capabilities_resolver,
            tool_dispatcher=self._tool_dispatcher,
            event_bus=bus,
            hook_runner=self._hook_runner,
            model_id=model_id,
            system_prompt_override=system_prompt_override,
            agent_allowed_tools=agent_allowed_tools,
        )

        # Hooks de inicio de run per-request del consumidor — SOLO en la raíz (los
        # subagentes drenan su propio canal por su fork). Espeja el drain canónico
        # dentro del loop; el seam los registra en el AgentLoop que el consumidor no
        # puede alcanzar (ver RuntimeConfig.root_turn_start_hooks).
        if self._root_turn_start_hooks is not None and parent_snapshot is None:
            for hook in self._root_turn_start_hooks(task) or []:
                loop.register_turn_start_hook(hook)

        # Entrada por voz: el prompt efectivo puede venir de transcribir el audio.
        prompt = await self._resolve_prompt(task, ctx)

        try:
            await loop.run(prompt, ctx)
        except asyncio.CancelledError:
            duration_ms = int((time.monotonic() - t0) * 1000)
            self._task_registry.kill(task_id)
            await self._fire_stop(task_id, task, "killed", None, duration_ms)
            self._notify(ctx.user_id, parent_session_id, task, task_id, "killed",
                         "Agent was killed (timeout or manual cancel)", "")
            raise
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            self._task_registry.fail(task_id, str(exc), duration_ms=duration_ms)
            await self._fire_stop(task_id, task, "failed", None, duration_ms)
            self._notify(ctx.user_id, parent_session_id, task, task_id, "failed", f"Error: {exc}", "")
            logger.warning("agent %s failed: %s", task_id, exc)
            return

        final_text = _last_assistant_text(ctx.messages)
        session.messages = list(ctx.messages)
        session.turn_count = ctx.turn_count
        duration_ms = int((time.monotonic() - t0) * 1000)
        self._task_registry.complete(
            task_id, result=final_text, duration_ms=duration_ms,
            turn_count=session.turn_count,
            input_tokens=session.usage.input_tokens,
            output_tokens=session.usage.output_tokens,
        )
        await self._fire_stop(task_id, task, "completed", final_text, duration_ms)

        if parent_session_id is not None:
            notification_text = (
                await summarize_if_needed(final_text, self._max_chars, self._small_llm)
                if final_text else "(no output)"
            )
            self._notify(ctx.user_id, parent_session_id, task, task_id, "completed",
                         notification_text, final_text)

        await self._persist(task, ctx, session)

    async def _persist(self, task: "RuntimeTask", ctx: ToolUseContext, session: Session) -> None:
        if self._storage is None:
            return
        # La identidad de usuario vive en el ctx (raíz: del task o autogenerada;
        # subagente: heredada del snapshot del padre), no en task.owner_id —que un
        # subagente no trae—, de modo que su transcript caiga bajo el mismo usuario.
        user_id = ctx.user_id or "anon"
        # El agent_id aleatorio discrimina el subtree solo para subagentes (kind);
        # el main vive en la raíz de la sesión.
        agent_id = (ctx.agent_id if ctx.is_subagent else "main") or "main"
        key = StorageKeys.transcript_key(user_id, ctx.session_id, agent_id)
        try:
            await self._storage.upload(key, session.model_dump_json().encode(), "application/json")
        except Exception as exc:
            logger.warning("persist failed for %s: %s", key, exc)


__all__ = ["LocalAgentRuntime"]
