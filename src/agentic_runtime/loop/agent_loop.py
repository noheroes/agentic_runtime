from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Coroutine
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from ..capabilities.resolver import CapabilitiesResolver
from ..capabilities.skill_listing_delta import (
    SKILL_LISTING_KEY,
    SKILL_TOOL_NAME,
    compute_skill_listing_delta,
    render_skill_listing_delta,
)
from ..context.compact import (
    AutoCompactTracking,
    auto_compact_if_needed,
    build_post_compact_messages,
    messages_after_compact_boundary,
)
from ..context.estimation import UsageAnchor
from ..context.tool_use import ToolUseContext
from ..context.window import ContextBudget
from ..contracts.abort import (
    INTERRUPT_MESSAGE,
    INTERRUPT_MESSAGE_FOR_TOOL_USE,
    TOOL_RESULT_INTERRUPTED,
)
from ..contracts.agents import enumerate_agent_definitions
from ..contracts.compaction import collect_compaction_context
from ..contracts.notifications import NotificationSink, apply_notification
from ..contracts.user_input import NoopUserInputProcessor, UserInputProcessor
from ..events.bus import EventBus
from ..events.event_types import (
    AbortEvent,
    DoneEvent,
    ErrorEvent,
    Event,
    MaxTurnsEvent,
    MessageEvent,
    ThinkingEvent,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnStartEvent,
)
from ..hooks import HookEvent
from ..models.protocol import (
    Effort,
    ModelCallerProtocol,
    ModelOptions,
    ThinkingConfig,
    UnsupportedModelOptionError,
)
from ..tools.agent_listing_delta import (
    ANNOUNCED_KEY,
    compute_agent_listing_delta,
    render_agent_listing_delta,
)
from ..tools.dispatcher import ToolDispatcher
from ..tools.native.agent import AGENT_TOOL_NAME
from ..tools.native.supported_settings import (
    EFFORT_APP_STATE_KEY,
    MODEL_APP_STATE_KEY,
    OFF_EFFORT_LEVEL,
    THINKING_APP_STATE_KEY,
)
from ..tools.pool import ToolPool
from .outcome import LoopEndReason, LoopOutcome

if TYPE_CHECKING:
    from ..capabilities.manager import CapabilityManager
    from ..tools.deferred_strategy import DeferredToolStrategy
    from ..tools.protocol import ToolProtocol
    from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def _vacio(valor: Any) -> bool:
    if valor is None:
        return True
    if isinstance(valor, (list, dict, tuple, set, str)):
        return len(valor) == 0
    return False


def _aborted(ctx: ToolUseContext) -> bool:
    return ctx.stop is not None and ctx.stop.aborted


def _with_effort(options: ModelOptions, level: str) -> ModelOptions:
    budget = options.thinking.budget_tokens if options.thinking is not None else None
    if level == OFF_EFFORT_LEVEL:
        return replace(
            options,
            effort=None,
            thinking=ThinkingConfig(enabled=False, budget_tokens=budget),
        )
    try:
        chosen = Effort(level)
    except ValueError as exc:
        raise UnsupportedModelOptionError(
            f"nivel de razonamiento desconocido en el estado de aplicación: {level!r}"
        ) from exc
    return replace(
        options,
        effort=chosen,
        thinking=ThinkingConfig(enabled=True, budget_tokens=budget),
    )


def _assistant_message(
    token_buffer: list[str],
    thinking_blocks: list[dict[str, str]],
    tool_calls: list[ToolCallEvent],
) -> dict[str, Any] | None:
    content = "".join(token_buffer)
    if not content and not tool_calls:
        return None
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if thinking_blocks:
        message["thinking_blocks"] = thinking_blocks
    if tool_calls:
        message["tool_calls"] = [
            {
                "id": tc.call_id,
                "function": {
                    "name": tc.tool_name,
                    "arguments": json.dumps(tc.tool_input),
                },
            }
            for tc in tool_calls
        ]
    return message


def _as_reminder(content: str) -> str:
    return f"<system-reminder>\n{content.strip()}\n</system-reminder>"


class AgentLoop:
    def __init__(
        self,
        *,
        model_caller: ModelCallerProtocol | None = None,
        tool_registry: ToolRegistry | None = None,
        capability_manager: CapabilityManager | None = None,
        capabilities_resolver: CapabilitiesResolver | None = None,
        tool_dispatcher: ToolDispatcher | None = None,
        event_bus: EventBus | None = None,
        hook_runner: Any | None = None,
        model_id: str = "",
        system_prompt_override: str = "",
        agent_allowed_tools: tuple[str, ...] = (),
        deferred_strategy: DeferredToolStrategy | None = None,
        model_options: ModelOptions | None = None,
        input_processor: UserInputProcessor | None = None,
        notification_sink: NotificationSink | None = None,
        max_turns: int | None = None,
        agent_resolver: Any | None = None,
        context_budget: ContextBudget | None = None,
    ) -> None:
        self._model_caller = model_caller
        self._tool_registry = tool_registry
        self._capability_manager = capability_manager
        self._capabilities_resolver = capabilities_resolver
        self._tool_dispatcher = tool_dispatcher
        self._event_bus = event_bus
        self._hook_runner = hook_runner
        self._model_id = model_id
        self._model_options = model_options or ModelOptions()
        self._system_prompt_override = system_prompt_override
        self._agent_allowed_tools = agent_allowed_tools
        self._deferred_strategy_override = deferred_strategy
        self._deferred_strategy_cached: DeferredToolStrategy | None = None
        self._turn_start_hooks: list[Callable[[], Coroutine[Any, Any, None]]] = []
        self._event_seq = 0
        self._input_processor: UserInputProcessor = input_processor or NoopUserInputProcessor()
        self._notification_sink = notification_sink
        self._max_turns = max_turns
        self._agent_resolver = agent_resolver
        self._context_budget = context_budget
        self._usage_anchor: UsageAnchor | None = None

    def _resolve_model_request(self, ctx: ToolUseContext) -> tuple[str, ModelOptions]:
        native = ctx.app_state.native
        model = native.get(MODEL_APP_STATE_KEY)
        model_id = str(model) if model else self._model_id
        options = self._model_options
        thinking = native.get(THINKING_APP_STATE_KEY)
        if thinking is not None:
            budget = options.thinking.budget_tokens if options.thinking is not None else None
            options = replace(
                options,
                thinking=ThinkingConfig(enabled=bool(thinking), budget_tokens=budget),
            )
        effort = native.get(EFFORT_APP_STATE_KEY)
        if effort is not None:
            options = _with_effort(options, str(effort))
        return model_id, options

    def _build_tool_pool(self, ctx: ToolUseContext) -> ToolPool:
        native: list[ToolProtocol] = []
        if self._tool_registry is not None:
            mode = "background" if ctx.is_subagent else "foreground"
            native = self._tool_registry.list_available(mode=mode)
        if self._capability_manager is not None:
            pool = self._capability_manager.build_tool_pool(native, ctx)
        else:
            pool = ToolPool(native_tools=native)
        return self._restrict_to_agent_tools(pool)

    async def _announce_agent_listing(
        self, ctx: ToolUseContext, published_names: frozenset[str]
    ) -> None:
        definitions = enumerate_agent_definitions(self._agent_resolver)
        delta = compute_agent_listing_delta(
            definitions,
            ctx.messages,
            agent_tool_available=AGENT_TOOL_NAME in published_names,
        )
        if delta is None:
            return
        await self._append(
            ctx,
            {
                "role": "user",
                "content": _as_reminder(render_agent_listing_delta(delta)),
                ANNOUNCED_KEY: {
                    "added_types": list(delta.added_types),
                    "removed_types": list(delta.removed_types),
                },
            },
            origin="agent_listing_delta",
        )

    async def _announce_skill_listing(
        self, ctx: ToolUseContext, published_names: frozenset[str]
    ) -> None:
        if self._capability_manager is None:
            return
        entries = [e for e in self._capability_manager.catalog(ctx) if e.kind == "skill"]
        delta = compute_skill_listing_delta(
            entries,
            ctx.messages,
            skill_tool_available=SKILL_TOOL_NAME in published_names,
        )
        if delta is None:
            return
        await self._append(
            ctx,
            {
                "role": "user",
                "content": _as_reminder(render_skill_listing_delta(delta)),
                SKILL_LISTING_KEY: {"names": list(delta.names)},
            },
            origin="skill_listing_delta",
        )

    def _compaction_provider_messages(self, ctx: ToolUseContext) -> list[dict[str, Any]]:
        if self._capability_manager is None:
            return []
        messages = collect_compaction_context(self._capability_manager.providers, ctx)
        return [
            {"role": "user", "content": _as_reminder(content)}
            for content in (
                str(message.get("content") or "").strip() for message in messages
            )
            if content
        ]

    def _restrict_to_agent_tools(self, pool: ToolPool) -> ToolPool:
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
        if self._capability_manager is None:
            return
        for msg in self._capability_manager.active_context(ctx):
            content = (msg.get("content") or "").strip()
            if not content:
                continue
            await self._append(
                ctx, {"role": "user", "content": _as_reminder(content)}, origin="recall"
            )

    def _resolve_deferred_strategy(self) -> DeferredToolStrategy:
        if self._deferred_strategy_override is not None:
            return self._deferred_strategy_override
        if self._deferred_strategy_cached is None:
            from ..tools.deferred_strategy import SoftwareDeferredStrategy

            self._deferred_strategy_cached = SoftwareDeferredStrategy()
        return self._deferred_strategy_cached

    async def _emit(self, event: Event, ctx: ToolUseContext) -> None:
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
        ctx.messages.append(message)
        await self._emit(
            MessageEvent(
                role=str(message.get("role", "")),
                content=str(message.get("content", "")),
                origin=origin,
            ),
            ctx,
        )


    async def _announce_abort(self, ctx: ToolUseContext, *, tool_use: bool) -> str:
        motivo = ctx.stop.reason() if ctx.stop is not None else None
        detail = str(getattr(motivo, "value", motivo) or "")
        await self._append(
            ctx,
            {
                "role": "user",
                "content": (
                    INTERRUPT_MESSAGE_FOR_TOOL_USE if tool_use else INTERRUPT_MESSAGE
                ),
            },
            origin="interrupt",
        )
        await self._emit(
            AbortEvent(reason=detail, turn=ctx.turn_count, tool_use=tool_use), ctx
        )
        return detail

    def register_turn_start_hook(self, hook: Callable[[], Coroutine[Any, Any, None]]) -> None:
        self._turn_start_hooks.append(hook)

    async def _run_turn_start_hooks(self) -> None:
        for hook in self._turn_start_hooks:
            await hook()

    def _drain_notifications(self, ctx: ToolUseContext) -> int:
        if self._notification_sink is None or ctx.is_subagent:
            return 0
        scope_key = ctx.scope.key if ctx.scope is not None else ""
        drained = self._notification_sink.drain(scope_key, ctx.session_id)
        for notification in drained:
            apply_notification(ctx.messages, notification)
        if drained:
            logger.debug("AgentLoop: %d notificación(es) aplicadas al historial", len(drained))
        return len(drained)


    async def run(self, prompt: str, ctx: ToolUseContext) -> LoopOutcome:
        if _aborted(ctx):
            motivo = ctx.stop.reason() if ctx.stop is not None else None
            detalle = str(getattr(motivo, "value", motivo) or "")
            await self._emit(
                AbortEvent(reason=detalle, turn=ctx.turn_count, tool_use=False), ctx
            )
            return LoopOutcome(LoopEndReason.ABORTED_PRE_RUN, ctx.turn_count, detalle or None)

        await self._run_turn_start_hooks()

        self._drain_notifications(ctx)

        processed = await self._input_processor.process(prompt, ctx)

        await self._append(ctx, {"role": "user", "content": processed.prompt}, origin="user")

        if processed.short_circuit:
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
        detail: str | None = None
        tracking = AutoCompactTracking()

        async def _compaction_emit(event: Event) -> None:
            await self._emit(event, ctx)

        while True:
            if _aborted(ctx):
                detail = await self._announce_abort(ctx, tool_use=True) or None
                if self._max_turns is not None and ctx.turn_count + 1 > self._max_turns:
                    await self._emit(
                        MaxTurnsEvent(
                            max_turns=self._max_turns,
                            turn_count=ctx.turn_count + 1,
                        ),
                        ctx,
                    )
                reason = LoopEndReason.ABORTED_TOOLS
                break

            if self._max_turns is not None and ctx.turn_count >= self._max_turns:
                await self._emit(
                    MaxTurnsEvent(
                        max_turns=self._max_turns,
                        turn_count=ctx.turn_count + 1,
                    ),
                    ctx,
                )
                reason = LoopEndReason.MAX_TURNS
                detail = str(self._max_turns)
                break

            ctx.turn_count += 1

            if self._context_budget is not None:
                compaction_model_id, _ = self._resolve_model_request(ctx)
                compaction = await auto_compact_if_needed(
                    messages_after_compact_boundary(ctx.messages),
                    self._model_caller,
                    self._context_budget,
                    tracking=tracking,
                    model_id=compaction_model_id,
                    anchor=self._usage_anchor,
                    stop=ctx.stop,
                    hooks=(
                        self._hook_runner.run if self._hook_runner is not None else None
                    ),
                    emit=_compaction_emit,
                    ctx=ctx,
                    provider_messages=self._compaction_provider_messages(ctx),
                )
                if compaction is not None:
                    self._usage_anchor = None
                    for compacted_message in build_post_compact_messages(compaction):
                        await self._append(ctx, compacted_message, origin="compact")

            deferred_names: tuple[str, ...] = ()
            announcements: list[str] = []
            published_names: frozenset[str] = frozenset()
            if self._tool_registry is not None or self._capability_manager is not None:
                ctx.tool_pool = self._build_tool_pool(ctx)
                pool = ctx.tool_pool.assemble(ctx.permission_context)
                published_names = frozenset(t.name for t in pool)
                plan = self._resolve_deferred_strategy().prepare_turn(ctx, pool)
                tool_schemas = plan.tool_schemas
                deferred_names = plan.deferred_names
                announcements = plan.announcements
            elif self._capabilities_resolver is not None:
                resolved = await self._capabilities_resolver.resolve(ctx)
                tool_schemas = resolved.tool_schemas
            else:
                tool_schemas = []

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
            await self._announce_agent_listing(ctx, published_names)
            await self._announce_skill_listing(ctx, published_names)

            system_sections: list[str] = []
            if self._capability_manager is not None:
                system_sections = self._capability_manager.system_prompt_sections(ctx)
                await self._inject_recall(ctx)

            logger.debug(
                "AgentLoop turno %d: invocando modelo (%d tools, %d mensajes)",
                ctx.turn_count, len(tool_schemas), len(ctx.messages),
            )
            model_id, options = self._resolve_model_request(ctx)
            complete_kwargs: dict[str, Any] = {"stop": ctx.stop, "model_id": model_id}
            complete_kwargs.update(options.as_kwargs())
            if system_sections:
                complete_kwargs["system_sections"] = system_sections
            if self._system_prompt_override:
                complete_kwargs["system_override"] = self._system_prompt_override
            visible_messages = messages_after_compact_boundary(ctx.messages)
            stream = await self._model_caller.complete(
                visible_messages,
                tool_schemas,
                **complete_kwargs,
            )

            token_buffer: list[str] = []
            thinking_blocks: list[dict[str, str]] = []
            tool_calls: list[ToolCallEvent] = []
            done: DoneEvent | None = None
            error: ErrorEvent | None = None

            aborted_mid_stream = False
            async for event in stream:
                if _aborted(ctx):
                    aborted_mid_stream = True
                    break
                await self._emit(event, ctx)
                if isinstance(event, TokenEvent):
                    token_buffer.append(event.content)
                elif isinstance(event, ThinkingEvent):
                    if event.final:
                        thinking_blocks.append({
                            "thinking": event.content,
                            "signature": event.signature,
                            "model_id": event.model_id,
                        })
                elif isinstance(event, ToolCallEvent):
                    tool_calls.append(event)
                elif isinstance(event, DoneEvent):
                    done = event
                    if done.usage is not None:
                        self._usage_anchor = UsageAnchor(
                            context_tokens=done.usage.context_tokens,
                            message_count=len(visible_messages),
                        )
                    break
                elif isinstance(event, ErrorEvent):
                    error = event
                    break

            if aborted_mid_stream:
                aclose = getattr(stream, "aclose", None)
                if callable(aclose):
                    await aclose()
                parcial = _assistant_message(token_buffer, thinking_blocks, tool_calls)
                if parcial is not None:
                    await self._append(ctx, parcial, origin="assistant")
                for tc in tool_calls:
                    ctx.messages.append({
                        "role": "tool",
                        "tool_call_id": tc.call_id,
                        "content": TOOL_RESULT_INTERRUPTED,
                    })
                    await self._emit(
                        ToolResultEvent(
                            call_id=tc.call_id,
                            result=TOOL_RESULT_INTERRUPTED,
                            is_error=True,
                        ),
                        ctx,
                    )
                detail = await self._announce_abort(ctx, tool_use=False) or None
                logger.info("AgentLoop turno %d: abortado a mitad de stream (%s)",
                            ctx.turn_count, detail)
                reason = LoopEndReason.ABORTED_STREAMING
                break

            logger.debug(
                "AgentLoop turno %d: respuesta (%d tokens, %d tool_calls, stop=%s)",
                ctx.turn_count, len(token_buffer), len(tool_calls),
                error.message if error is not None else getattr(done, "stop_reason", None),
            )

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

            msg = _assistant_message(token_buffer, thinking_blocks, tool_calls)
            if msg is not None:
                await self._append(ctx, msg, origin="assistant")

            _ends_turn = False
            for tc in tool_calls:
                if self._tool_dispatcher is None:
                    await self._append(
                        ctx,
                        {"role": "tool", "tool_call_id": tc.call_id, "content": "[no dispatcher]"},
                        origin="tool",
                    )
                    continue
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
                        is_error=bool(
                            getattr(result, "is_error", False)
                            or getattr(result, "is_aborted", False)
                            or getattr(result, "is_timeout", False)
                        ),
                    ),
                    ctx,
                )
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

            if tracking.compacted:
                tracking.turn_counter += 1

            if _ends_turn or done is None or done.stop_reason != "tool_calls":
                reason = LoopEndReason.ENDS_TURN if _ends_turn else LoopEndReason.COMPLETED
                break

        return LoopOutcome(reason, ctx.turn_count, detail)
