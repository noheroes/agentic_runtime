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

from ...context.tool_use import ToolUseContext
from ...events.bus import EventBus
from ...events.event_types import ToolCallEvent, ToolResultEvent
from ...events.protocol import Event, EventHandler
from ...hooks import HookEvent, HookRunner
from ...loop.agent_loop import AgentLoop
from ...storage.protocol import StorageKeys, StorageProtocol
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
        reg_task = self._task_registry.register(description=task.description)
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
        ctx = ToolUseContext(session_id=f"sess_{uuid.uuid4().hex[:12]}", agent_id=agent_id)
        return ctx, None, 0

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

    def _notify(self, parent_session_id: str | None, task: "RuntimeTask",
                task_id: str, status: str, text: str, final_text: str) -> None:
        if parent_session_id is None:
            return
        put_notification(BackgroundNotification(
            parent_session_id=parent_session_id, task_id=task_id, status=status,
            description=task.description, notification_text=text,
            final_text=final_text, parent_execution_id=task.parent_execution_id,
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
        ctx.presentation = self._presentation
        ctx.exec_env = self._exec_env
        session = Session(session_id=ctx.session_id)
        session.metadata.subagent_depth = subagent_depth
        bus = self._make_bus(task_id, on_event)

        loop = AgentLoop(
            model_caller=self._model_caller,
            tool_registry=self._tool_registry,
            capability_manager=self._capability_manager,
            capabilities_resolver=self._capabilities_resolver,
            tool_dispatcher=self._tool_dispatcher,
            event_bus=bus,
            model_id=task.model_override or self._model_id,
        )

        try:
            await loop.run(task.prompt, ctx)
        except asyncio.CancelledError:
            duration_ms = int((time.monotonic() - t0) * 1000)
            self._task_registry.kill(task_id)
            await self._fire_stop(task_id, task, "killed", None, duration_ms)
            self._notify(parent_session_id, task, task_id, "killed",
                         "Agent was killed (timeout or manual cancel)", "")
            raise
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            self._task_registry.fail(task_id, str(exc), duration_ms=duration_ms)
            await self._fire_stop(task_id, task, "failed", None, duration_ms)
            self._notify(parent_session_id, task, task_id, "failed", f"Error: {exc}", "")
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
            self._notify(parent_session_id, task, task_id, "completed",
                         notification_text, final_text)

        await self._persist(task, ctx, session)

    async def _persist(self, task: "RuntimeTask", ctx: ToolUseContext, session: Session) -> None:
        if self._storage is None or not task.owner_id:
            return
        # El agent_id aleatorio discrimina el subtree solo para subagentes (kind);
        # el main vive en la raíz de la sesión.
        agent_id = ctx.agent_id if ctx.is_subagent else "main"
        key = StorageKeys.transcript_key(task.owner_id, ctx.session_id, agent_id)
        try:
            await self._storage.upload(key, session.model_dump_json().encode(), "application/json")
        except Exception as exc:
            logger.warning("persist failed for %s: %s", key, exc)


__all__ = ["LocalAgentRuntime"]
