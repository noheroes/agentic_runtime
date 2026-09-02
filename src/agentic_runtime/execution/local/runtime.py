from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from ...context.presentation import IdentityPresentation
from ...context.tool_use import ToolUseContext
from ...context.window import ContextBudget
from ...contracts.abort import AbortController, AbortReason
from ...contracts.errors import RuntimeIdentityError
from ...contracts.identity import Scope, SessionId, SessionRepo
from ...events.bus import EventBus
from ...events.event_types import DoneEvent, TokenEvent, ToolCallEvent, ToolResultEvent
from ...events.protocol import Event, EventHandler
from ...hooks import HookEvent, HookRunner
from ...loop.agent_loop import AgentLoop
from ...loop.outcome import LoopEndReason, LoopOutcome
from ...models.protocol import ModelOptions
from ...storage.protocol import StorageKeys, StorageProtocol
from ..agents import resolve_subagent_model
from ..fork import ForkContext, ForkPolicy, ForkSnapshot, RuntimeContextForker
from ..session import Session
from ..tasks.registry import InMemoryTaskRegistry, TaskRegistryProtocol
from ..tasks.status import TaskStatus
from .notification import BackgroundNotification, InProcessNotificationSink
from .summarizer import summarize_if_needed

if TYPE_CHECKING:
    from ...capabilities.resolver import CapabilitiesResolver
    from ...contracts.runtime import RuntimeTask
    from ...models.protocol import ModelCallerProtocol
    from ...tools.dispatcher import ToolDispatcher

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 300.0


def _last_assistant_text(messages: list[Any]) -> str:
    for m in reversed(messages):
        if isinstance(m, dict) and m.get("role") == "assistant":
            return m.get("content") or ""
    return ""


class LocalAgentRuntime:
    def __init__(
        self,
        *,
        model_caller: ModelCallerProtocol | None = None,
        tool_registry: Any = None,
        capability_manager: Any = None,
        capabilities_resolver: CapabilitiesResolver | None = None,
        tool_dispatcher: ToolDispatcher | None = None,
        task_registry: TaskRegistryProtocol | None = None,
        hook_runner: HookRunner | None = None,
        storage: StorageProtocol | None = None,
        owns_storage: bool = False,
        presentation: Any = None,
        exec_env: Any = None,
        fs: Any = None,
        storage_contract: Any = None,
        git_credentials: Any = None,
        small_llm: Any = None,
        background_result_max_chars: int = 2000,
        model_id: str = "",
        model_options: ModelOptions | None = None,
        input_processor: Any = None,
        initial_allowed_tools: list[str] | None = None,
        root_context_modifier: Any = None,
        root_turn_start_hooks: Any = None,
        stt: Any = None,
        tts: Any = None,
        agent_resolver: Any = None,
        runner_factory: Any = None,
        notification_sink: Any = None,
        scope: Scope | None = None,
        session_repo: SessionRepo[Any] | None = None,
        context_budget: ContextBudget | None = None,
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
        self._owns_storage = owns_storage
        self._presentation = presentation
        self._exec_env = exec_env
        self._fs = fs
        self._storage_contract = storage_contract
        self._git_credentials = git_credentials
        self._small_llm = small_llm
        self._max_chars = background_result_max_chars
        self._model_id = model_id
        self._model_options = model_options or ModelOptions()
        self._input_processor = input_processor
        self._initial_allowed_tools = list(initial_allowed_tools or [])
        self._root_context_modifier = root_context_modifier
        self._root_turn_start_hooks = root_turn_start_hooks
        self._agent_resolver = agent_resolver
        self._runner = runner_factory(self) if runner_factory is not None else None
        self._notification_sink = notification_sink or InProcessNotificationSink()
        self._stt = stt
        self._tts = tts
        self._scope = scope
        self._session_repo = session_repo
        self._context_budget = context_budget
        self._default_timeout = default_timeout

    @property
    def runtime_id(self) -> str:
        return "local"


    async def startup(self) -> None:
        if self._capability_manager is not None:
            await self._capability_manager.startup()

    async def shutdown(self) -> None:
        if self._capability_manager is not None:
            await self._capability_manager.shutdown()
        if self._owns_storage:
            teardown = getattr(self._storage, "teardown", None)
            if teardown is not None:
                await teardown()

    @property
    def capabilities(self) -> Any:
        return self._capability_manager


    async def dispatch(
        self,
        task: RuntimeTask,
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
        task: RuntimeTask,
        parent_snapshot: ForkSnapshot | None = None,
    ) -> AsyncIterator[Event]:
        queue: asyncio.Queue[Any] = asyncio.Queue()
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

    async def join(self, task_id: str) -> str | None:
        rec = self._task_registry.get(task_id)
        if rec is None:
            return None
        asyncio_task = rec.asyncio_task
        if asyncio_task is not None and not asyncio_task.done():
            await asyncio.wait([asyncio_task])
        return self.result(task_id)

    def status(self, task_id: str) -> TaskStatus | None:
        rec = self._task_registry.get(task_id)
        return rec.status if rec else None

    async def cancel(
        self, task_id: str, *, reason: AbortReason = AbortReason.TURN_CANCELLED
    ) -> bool:
        """Alza la señal y devuelve. No espera, no cronometra, no mata la task.

        El plazo de gracia que había aquí (`D-66`) era un `5.0` mío arbitrando algo cuya
        duración se desconoce, y además mataba lo que no tocaba: `_task_registry.kill`
        termina la task de asyncio, nunca el proceso del SO que la tool sostiene. A no
        cronometra el aborto en ningún punto; corta quien tiene el proceso, al oír la
        señal (`ShellCommand.ts:186-193`). El corte real vive ahora ahí.
        """
        rec = self._task_registry.get(task_id)
        if rec is None:
            return False
        stop = rec.stop
        abort = getattr(stop, "abort", None)
        asyncio_task = rec.asyncio_task
        if abort is None or asyncio_task is None or asyncio_task.done():
            return self._task_registry.kill(task_id)
        if not stop.aborted:
            abort(reason)
        return True

    def result(self, task_id: str) -> str | None:
        rec = self._task_registry.get(task_id)
        return rec.result if rec else None


    def _build_child(
        self, task: RuntimeTask, parent_snapshot: ForkSnapshot | None
    ) -> tuple[Any, str | None, int]:
        if parent_snapshot is not None:
            policy = ForkPolicy(inherit_messages=task.fork_context)
            ctx = RuntimeContextForker().fork(
                ForkContext(
                    prompt=task.prompt,
                    policy=policy,
                    parent_snapshot=parent_snapshot,
                    subagent_type=task.subagent_type,
                )
            )
            return ctx, parent_snapshot.session_id, parent_snapshot.subagent_depth + 1
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        if not task.session_id:
            raise RuntimeIdentityError(
                "RuntimeTask.session_id es obligatorio: el runtime transporta identidad, "
                "no la inventa (C9/ID-1). Atribúyela el integrador o su SessionRepo."
            )
        ctx = ToolUseContext(
            session_id=task.session_id,
            scope=task.scope or self._scope,
            agent_id=agent_id,
            stop=AbortController(),
        )
        if self._initial_allowed_tools:
            ctx = ctx.with_permissions(
                ctx.permission_context.with_command_allow(list(self._initial_allowed_tools))
            )
        return ctx, None, 0

    async def _resolve_prompt(self, task: RuntimeTask, ctx: ToolUseContext) -> str:
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

    async def _fire_stop(self, task_id: str, task: RuntimeTask, status: str,
                         result: str | None, duration_ms: int) -> None:
        if self._hook_runner is None:
            return
        await self._hook_runner.run(HookEvent.SUBAGENT_STOP, {
            "task_id": task_id, "description": task.description,
            "status": status, "result": result, "duration_ms": duration_ms,
        })

    def _notify(self, parent_scope: Scope | None, parent_session_id: str | None,
                task: RuntimeTask, task_id: str, status: str, text: str,
                final_text: str) -> None:
        if parent_session_id is None:
            return
        self._notification_sink.put(BackgroundNotification(
            parent_scope=parent_scope.key if parent_scope else "",
            parent_session_id=parent_session_id,
            task_id=task_id, status=status,
            description=task.description, notification_text=text,
            final_text=final_text,
        ))

    async def _run_loop(
        self,
        task_id: str,
        task: RuntimeTask,
        parent_snapshot: ForkSnapshot | None,
        on_event: EventHandler | None = None,
    ) -> None:
        t0 = time.monotonic()
        ctx: ToolUseContext | None = None
        parent_session_id: str | None = None
        session: Session | None = None
        outcome: LoopOutcome | None = None
        try:
            ctx, parent_session_id, subagent_depth = self._build_child(task, parent_snapshot)
            ctx.is_subagent = parent_snapshot is not None
            ctx.task_id = task_id
            ctx.subagent_depth = subagent_depth
            ctx.presentation = self._presentation
            ctx.exec_env = self._exec_env
            ctx.git_credentials = self._git_credentials
            ctx.runner = self._runner
            ctx.task_registry = self._task_registry
            self._task_registry.set_stop(task_id, ctx.stop)
            if self._fs is not None:
                ctx.fs = self._fs
            if self._storage_contract is not None:
                ctx.storage = self._storage_contract
            if self._root_context_modifier is not None and parent_snapshot is None:
                ctx = self._root_context_modifier(ctx, task)
            session = self._open_session(ctx.session_id)
            session.metadata.subagent_depth = subagent_depth
            bus = self._make_bus(task_id, on_event)
            self._wire_tts(bus, ctx)

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
                model_options=self._model_options,
                input_processor=self._input_processor,
                notification_sink=self._notification_sink,
                max_turns=task.max_turns,
                system_prompt_override=system_prompt_override,
                agent_allowed_tools=agent_allowed_tools,
                agent_resolver=self._agent_resolver,
                context_budget=self._context_budget,
            )

            if self._root_turn_start_hooks is not None and parent_snapshot is None:
                for hook in self._root_turn_start_hooks(task) or []:
                    loop.register_turn_start_hook(hook)

            prompt = await self._resolve_prompt(task, ctx)

            outcome = await loop.run(prompt, ctx)
        except asyncio.CancelledError:
            duration_ms = int((time.monotonic() - t0) * 1000)
            final_text = ""
            detail = None
            if ctx is not None:
                final_text = _last_assistant_text(ctx.messages)
                if ctx.stop is not None:
                    detail = getattr(ctx.stop.reason(), "value", None)
                if session is not None:
                    session.messages = list(ctx.messages)
                    session.turn_count = ctx.turn_count
            self._task_registry.kill(
                task_id,
                result=final_text,
                end_reason=LoopEndReason.ABORTED_HARD.value,
                end_detail=detail,
            )
            await self._shielded(
                self._fire_stop(task_id, task, "killed", final_text, duration_ms)
            )
            self._notify(ctx.scope if ctx is not None else None, parent_session_id,
                         task, task_id, "killed",
                         "Agent was killed (timeout or manual cancel)", final_text)
            if ctx is not None and session is not None:
                await self._shielded(self._persist(task, ctx, session))
            raise
        except Exception as exc:  # noqa: BLE001
            duration_ms = int((time.monotonic() - t0) * 1000)
            self._task_registry.fail(task_id, str(exc), duration_ms=duration_ms)
            await self._fire_stop(task_id, task, "failed", None, duration_ms)
            self._notify(ctx.scope if ctx is not None else None, parent_session_id,
                         task, task_id, "failed", f"Error: {exc}", "")
            logger.warning("agent %s failed: %s", task_id, exc)
            return

        assert ctx is not None and session is not None and outcome is not None
        final_text = _last_assistant_text(ctx.messages)
        session.messages = list(ctx.messages)
        session.turn_count = ctx.turn_count
        duration_ms = int((time.monotonic() - t0) * 1000)
        self._task_registry.complete(
            task_id, result=final_text, duration_ms=duration_ms,
            turn_count=session.turn_count,
            input_tokens=session.usage.input_tokens,
            output_tokens=session.usage.output_tokens,
            end_reason=outcome.reason.value,
            end_detail=outcome.detail,
        )
        await self._fire_stop(task_id, task, "completed", final_text, duration_ms)

        if parent_session_id is not None:
            notification_text = (
                await summarize_if_needed(final_text, self._max_chars, self._small_llm)
                if final_text else "(no output)"
            )
            self._notify(ctx.scope, parent_session_id, task, task_id, "completed",
                         notification_text, final_text)

        await self._persist(task, ctx, session)

    @staticmethod
    async def _shielded(coro: Any) -> None:
        fut = asyncio.ensure_future(coro)
        while True:
            try:
                await asyncio.shield(fut)
            except asyncio.CancelledError:
                if fut.done():
                    return
                continue
            except Exception as exc:  # noqa: BLE001
                logger.warning("cierre tras cancelación falló: %s", exc)
            return

    def _open_session(self, session_id: str) -> Session:
        if self._session_repo is None:
            return Session(session_id=session_id)
        handle = self._session_repo.open(SessionId(session_id))
        return Session(session_id=handle.id)

    async def _persist(self, task: RuntimeTask, ctx: ToolUseContext, session: Session) -> None:
        if self._storage is None:
            return
        if ctx.scope is None:
            logger.info(
                "persist omitido: la task no trae scope y el runtime no inventa uno "
                "(C9/ID-3). Inyecta `RuntimeConfig.scope` o `RuntimeTask.scope`."
            )
            return
        agent_id = (ctx.agent_id if ctx.is_subagent else "main") or "main"
        key = StorageKeys.transcript_key(ctx.scope, ctx.session_id, agent_id)
        try:
            await self._storage.upload(key, session.model_dump_json().encode(), "application/json")
        except Exception as exc:  # noqa: BLE001
            logger.warning("persist failed for %s: %s", key, exc)


__all__ = ["LocalAgentRuntime"]
