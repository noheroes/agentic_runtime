from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ...contracts.abort import AbortSignal
from ...contracts.events import CompactionEvent, ErrorEvent, Event, TokenEvent
from ...hooks.protocol import HookDecision, HookEvent
from ...models.protocol import (
    ModelCallerProtocol,
    ThinkingConfig,
    UnsupportedModelOptionError,
)
from ..estimation import (
    UsageAnchor,
    rough_token_count_for_messages,
    token_count_with_estimation,
)
from ..window import (
    MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES,
    ContextBudget,
    evaluate_context_pressure,
)
from .prompt import (
    PartialCompactDirection,
    format_compact_summary,
    get_compact_prompt,
    get_compact_user_summary_message,
    get_partial_compact_prompt,
)
from .restore import create_post_compact_file_attachments

if TYPE_CHECKING:
    from ..tool_use import ToolUseContext

COMPACT_SYSTEM_PROMPT = "You are a helpful AI assistant tasked with summarizing conversations."
COMPACT_BOUNDARY_KEY = "compact_boundary"
COMPACT_BOUNDARY_CONTENT = "Conversation compacted"
COMPACT_SUMMARY_KEY = "is_compact_summary"

API_ERROR_PREFIX = "API Error"
PROMPT_TOO_LONG_ERROR_MESSAGE = "Prompt is too long"

MAX_PTL_RETRIES = 3
PTL_RETRY_MARKER = "[earlier conversation truncated for compaction retry]"
PTL_RETRY_MARKER_KEY = "is_meta"
PTL_FALLBACK_DROP_RATIO = 0.2

PROMPT_TOO_LONG_PATTERN = re.compile(
    r"prompt is too long[^0-9]*(\d+)\s*tokens?\s*>\s*(\d+)", re.IGNORECASE
)

ERROR_MESSAGE_NOT_ENOUGH_MESSAGES = "Not enough messages to compact."
ERROR_MESSAGE_PROMPT_TOO_LONG = "Conversation too long."
ERROR_MESSAGE_USER_ABORT = "API Error: Request was aborted."
ERROR_MESSAGE_INCOMPLETE_RESPONSE = (
    "Compaction interrupted · This may be due to network issues — please try again."
)
ERROR_MESSAGE_SUMMARY_TOO_SHORT = "Summary too short to replace the conversation."

MEDIA_MARKERS = {"image": "[image]", "document": "[document]"}

EmitFn = Callable[[Event], Awaitable[None]]
HookFn = Callable[[HookEvent, dict[str, Any]], Awaitable[HookDecision | None]]


class CompactionError(RuntimeError):
    reason = "error"


class NotEnoughMessagesError(CompactionError):
    reason = "not_enough_messages"

    def __init__(self, message: str = ERROR_MESSAGE_NOT_ENOUGH_MESSAGES) -> None:
        super().__init__(message)


class PromptTooLongError(CompactionError):
    reason = "prompt_too_long"

    def __init__(
        self,
        message: str = ERROR_MESSAGE_PROMPT_TOO_LONG,
        *,
        details: str = "",
        ptl_attempts: int = 0,
    ) -> None:
        super().__init__(message)
        self.details = details
        self.ptl_attempts = ptl_attempts


class IncompleteResponseError(CompactionError):
    reason = "no_summary"

    def __init__(self, message: str = ERROR_MESSAGE_INCOMPLETE_RESPONSE) -> None:
        super().__init__(message)


class ApiErrorSummaryError(CompactionError):
    reason = "api_error"


class SummaryTooShortError(CompactionError):
    reason = "summary_too_short"

    def __init__(self, message: str = ERROR_MESSAGE_SUMMARY_TOO_SHORT) -> None:
        super().__init__(message)


class CompactionBlockedError(CompactionError):
    reason = "hook_blocked"


def starts_with_api_error_prefix(text: str) -> bool:
    return text.startswith(API_ERROR_PREFIX)


def is_prompt_too_long_text(text: str | None) -> bool:
    return PROMPT_TOO_LONG_ERROR_MESSAGE.lower() in (text or "").lower()


def parse_prompt_too_long_token_counts(text: str | None) -> tuple[int, int] | None:
    match = PROMPT_TOO_LONG_PATTERN.search(text or "")
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def prompt_too_long_token_gap(text: str | None) -> int | None:
    counts = parse_prompt_too_long_token_counts(text)
    if counts is None:
        return None
    gap = counts[0] - counts[1]
    return gap if gap > 0 else None


def create_ptl_retry_marker_message() -> dict[str, Any]:
    return {
        "role": "user",
        "content": PTL_RETRY_MARKER,
        PTL_RETRY_MARKER_KEY: True,
    }


def is_ptl_retry_marker_message(message: Any) -> bool:
    return (
        isinstance(message, dict)
        and message.get("role") == "user"
        and bool(message.get(PTL_RETRY_MARKER_KEY))
        and message.get("content") == PTL_RETRY_MARKER
    )


def group_messages_by_api_round(
    messages: Sequence[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for message in messages:
        if message.get("role") == "assistant" and current:
            groups.append(current)
            current = []
        current.append(message)
    if current:
        groups.append(current)
    return groups


def truncate_head_for_ptl_retry(
    messages: Sequence[dict[str, Any]],
    error_text: str | None,
) -> list[dict[str, Any]] | None:
    head = messages[0] if messages else None
    body = list(messages[1:]) if is_ptl_retry_marker_message(head) else list(messages)

    groups = group_messages_by_api_round(body)
    if len(groups) < 2:
        return None

    gap = prompt_too_long_token_gap(error_text)
    if gap is not None:
        accumulated = 0
        drop_count = 0
        for group in groups:
            accumulated += rough_token_count_for_messages(group)
            drop_count += 1
            if accumulated >= gap:
                break
    else:
        drop_count = max(1, int(len(groups) * PTL_FALLBACK_DROP_RATIO))

    drop_count = min(drop_count, len(groups) - 1)
    if drop_count < 1:
        return None

    sliced = [message for group in groups[drop_count:] for message in group]
    if sliced and sliced[0].get("role") == "assistant":
        return [create_ptl_retry_marker_message(), *sliced]
    return sliced


def create_compact_boundary_message(
    trigger: str,
    pre_tokens: int,
    user_context: str | None = None,
    messages_summarized: int | None = None,
) -> dict[str, Any]:
    return {
        "role": "system",
        "content": COMPACT_BOUNDARY_CONTENT,
        COMPACT_BOUNDARY_KEY: {
            "trigger": trigger,
            "pre_tokens": pre_tokens,
            "user_context": user_context,
            "messages_summarized": messages_summarized,
        },
    }


def is_compact_boundary_message(message: Any) -> bool:
    return isinstance(message, dict) and COMPACT_BOUNDARY_KEY in message


def find_last_compact_boundary_index(messages: Sequence[dict[str, Any]]) -> int:
    for index in range(len(messages) - 1, -1, -1):
        if is_compact_boundary_message(messages[index]):
            return index
    return -1


def messages_after_compact_boundary(
    messages: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    index = find_last_compact_boundary_index(messages)
    if index == -1:
        return list(messages)
    return list(messages[index:])


def _strip_media_from_block(block: Any) -> tuple[Any, bool]:
    if not isinstance(block, dict):
        return block, False

    marker = MEDIA_MARKERS.get(block.get("type", ""))
    if marker is not None:
        return {"type": "text", "text": marker}, True

    if block.get("type") == "tool_result" and isinstance(block.get("content"), list):
        found = False
        new_content = []
        for item in block["content"]:
            replaced, hit = _strip_media_from_block(item)
            found = found or hit
            new_content.append(replaced)
        if found:
            return {**block, "content": new_content}, True

    return block, False


def strip_images_from_messages(
    messages: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    stripped: list[dict[str, Any]] = []
    for message in messages:
        content = message.get("content")
        if message.get("role") != "user" or not isinstance(content, list):
            stripped.append(message)
            continue

        found = False
        new_content = []
        for block in content:
            replaced, hit = _strip_media_from_block(block)
            found = found or hit
            new_content.append(replaced)

        stripped.append({**message, "content": new_content} if found else message)
    return stripped


@dataclass
class AutoCompactTracking:
    compacted: bool = False
    turn_counter: int = 0
    turn_id: str = ""
    consecutive_failures: int = 0
    last_compacted_tokens: int = 0


@dataclass(frozen=True)
class CompactionResult:
    boundary_marker: dict[str, Any]
    summary_messages: list[dict[str, Any]]
    attachments: list[dict[str, Any]] = field(default_factory=list)
    hook_results: list[dict[str, Any]] = field(default_factory=list)
    messages_to_keep: list[dict[str, Any]] | None = None
    user_display_message: str | None = None
    summary: str = ""
    pre_compact_token_count: int = 0
    true_post_compact_token_count: int = 0
    thinking_disabled: bool = True
    reasoning_fallback: bool = False


def build_post_compact_messages(result: CompactionResult) -> list[dict[str, Any]]:
    return [
        result.boundary_marker,
        *result.summary_messages,
        *(result.messages_to_keep or []),
        *result.attachments,
        *result.hook_results,
    ]


def merge_hook_instructions(
    user_instructions: str | None,
    hook_instructions: str | None,
) -> str | None:
    if not hook_instructions:
        return user_instructions or None
    if not user_instructions:
        return hook_instructions
    return f"{user_instructions}\n\n{hook_instructions}"


def should_auto_compact(
    messages: Sequence[dict[str, Any]],
    budget: ContextBudget,
    *,
    enabled: bool = True,
    anchor: UsageAnchor | None = None,
    tracking: AutoCompactTracking | None = None,
    snip_tokens_freed: int = 0,
) -> bool:
    if not enabled:
        return False

    token_count = token_count_with_estimation(list(messages), anchor) - snip_tokens_freed
    pressure = evaluate_context_pressure(token_count, budget)
    if not pressure.above_autocompact:
        return False

    if tracking is not None and tracking.last_compacted_tokens > 0:
        floor = tracking.last_compacted_tokens * budget.recompaction_growth_ratio
        if token_count < floor:
            return False

    return True


async def _run_pre_compact_hook(
    hooks: HookFn | None,
    trigger: str,
    custom_instructions: str | None,
) -> tuple[str | None, str | None]:
    if hooks is None:
        return custom_instructions, None

    decision = await hooks(
        HookEvent.PRE_COMPACT,
        {"trigger": trigger, "custom_instructions": custom_instructions},
    )
    if decision is None:
        return custom_instructions, None
    if decision.block or decision.stop:
        raise CompactionBlockedError(decision.message or "PreCompact hook blocked compaction")
    return (
        merge_hook_instructions(custom_instructions, decision.additional_context),
        decision.message,
    )


def _as_reminder(content: str) -> str:
    return f"<system-reminder>\n{content.strip()}\n</system-reminder>"


def _combine_display_messages(*messages: str | None) -> str | None:
    present = [message for message in messages if message]
    return "\n".join(present) or None


async def _run_post_compact_hook(
    hooks: HookFn | None,
    trigger: str,
    summary: str,
) -> tuple[list[dict[str, Any]], str | None]:
    if hooks is None:
        return [], None

    decision = await hooks(
        HookEvent.POST_COMPACT,
        {"trigger": trigger, "compact_summary": summary},
    )
    if decision is None:
        return [], None

    messages: list[dict[str, Any]] = []
    if decision.additional_context:
        messages.append(
            {"role": "user", "content": _as_reminder(decision.additional_context)}
        )
    return messages, decision.message


async def _collect_summary_text(
    caller: ModelCallerProtocol,
    request_messages: list[dict[str, Any]],
    *,
    model_id: str,
    max_tokens: int,
    stop: AbortSignal | None,
    thinking: ThinkingConfig | None,
) -> str:
    chunks: list[str] = []
    kwargs: dict[str, Any] = {
        "stop": stop,
        "model_id": model_id,
        "system_override": COMPACT_SYSTEM_PROMPT,
        "max_tokens": max_tokens,
    }
    if thinking is not None:
        kwargs["thinking"] = thinking

    stream = await caller.complete(request_messages, [], **kwargs)
    async for event in stream:
        if isinstance(event, TokenEvent):
            chunks.append(event.content)
        elif isinstance(event, ErrorEvent):
            if is_prompt_too_long_text(event.message):
                raise PromptTooLongError(details=event.message)
            raise CompactionError(event.message or ERROR_MESSAGE_INCOMPLETE_RESPONSE)

    return "".join(chunks).strip()


async def _summarize_once(
    caller: ModelCallerProtocol,
    request_messages: list[dict[str, Any]],
    *,
    model_id: str,
    max_tokens: int,
    stop: AbortSignal | None,
) -> tuple[str, bool, bool]:
    try:
        summary = await _collect_summary_text(
            caller,
            request_messages,
            model_id=model_id,
            max_tokens=max_tokens,
            stop=stop,
            thinking=ThinkingConfig(enabled=False),
        )
    except UnsupportedModelOptionError:
        summary = await _collect_summary_text(
            caller,
            request_messages,
            model_id=model_id,
            max_tokens=max_tokens,
            stop=stop,
            thinking=None,
        )
        return summary, False, True
    return summary, True, False


async def compact_conversation(
    messages: Sequence[dict[str, Any]],
    caller: ModelCallerProtocol,
    budget: ContextBudget,
    *,
    model_id: str = "",
    trigger: str = "auto",
    custom_instructions: str | None = None,
    suppress_follow_up_questions: bool = True,
    transcript_path: str | None = None,
    messages_to_keep: Sequence[dict[str, Any]] | None = None,
    direction: PartialCompactDirection | None = None,
    user_context: str | None = None,
    anchor: UsageAnchor | None = None,
    stop: AbortSignal | None = None,
    hooks: HookFn | None = None,
    emit: EmitFn | None = None,
    ctx: ToolUseContext | None = None,
    provider_messages: Sequence[dict[str, Any]] | None = None,
) -> CompactionResult:
    if not messages:
        raise NotEnoughMessagesError

    pre_compact_token_count = token_count_with_estimation(list(messages), anchor)
    custom_instructions, user_display_message = await _run_pre_compact_hook(
        hooks, trigger, custom_instructions
    )

    local_guard = budget.min_summary_chars > 0
    if direction is None:
        prompt = get_compact_prompt(
            custom_instructions, local_reasoning_guard=local_guard
        )
    else:
        prompt = get_partial_compact_prompt(
            custom_instructions, direction, local_reasoning_guard=local_guard
        )

    to_summarize = strip_images_from_messages(messages_after_compact_boundary(messages))

    thinking_disabled = True
    reasoning_fallback = False
    ptl_attempts = 0
    while True:
        try:
            summary, thinking_disabled, reasoning_fallback = await _summarize_once(
                caller,
                [*to_summarize, {"role": "user", "content": prompt}],
                model_id=model_id,
                max_tokens=budget.reserved_for_summary,
                stop=stop,
            )
            error_text = summary if summary.startswith(PROMPT_TOO_LONG_ERROR_MESSAGE) else ""
        except PromptTooLongError as error:
            summary = ""
            error_text = error.details or str(error)

        if not error_text:
            break

        ptl_attempts += 1
        truncated = (
            truncate_head_for_ptl_retry(to_summarize, error_text)
            if ptl_attempts <= MAX_PTL_RETRIES
            else None
        )
        if truncated is None:
            raise PromptTooLongError(details=error_text, ptl_attempts=ptl_attempts)

        if emit is not None:
            await emit(
                CompactionEvent(
                    trigger=trigger,
                    outcome="ptl_retry",
                    reason="prompt_too_long",
                    pre_tokens=pre_compact_token_count,
                    ptl_attempt=ptl_attempts,
                    dropped_messages=len(to_summarize) - len(truncated),
                    remaining_messages=len(truncated),
                )
            )
        to_summarize = truncated

    if not summary:
        raise IncompleteResponseError
    if starts_with_api_error_prefix(summary):
        raise ApiErrorSummaryError(summary)

    formatted = format_compact_summary(summary)
    if len(formatted) < budget.min_summary_chars:
        raise SummaryTooShortError

    kept = list(messages_to_keep or [])
    boundary_marker = create_compact_boundary_message(
        trigger,
        pre_compact_token_count,
        user_context,
        len(messages) - len(kept),
    )
    summary_messages = [
        {
            "role": "user",
            "content": get_compact_user_summary_message(
                summary,
                suppress_follow_up_questions,
                transcript_path,
                bool(kept),
            ),
            COMPACT_SUMMARY_KEY: True,
        }
    ]
    attachments: list[dict[str, Any]] = []
    if ctx is not None:
        attachments.extend(
            await create_post_compact_file_attachments(ctx, budget, messages_to_keep=kept)
        )
    attachments.extend(provider_messages or [])

    hook_results, post_display_message = await _run_post_compact_hook(
        hooks, trigger, summary
    )
    user_display_message = _combine_display_messages(
        user_display_message, post_display_message
    )

    true_post_compact_token_count = rough_token_count_for_messages(
        [boundary_marker, *summary_messages, *kept, *attachments, *hook_results]
    )

    result = CompactionResult(
        boundary_marker=boundary_marker,
        summary_messages=summary_messages,
        attachments=attachments,
        hook_results=hook_results,
        messages_to_keep=kept or None,
        user_display_message=user_display_message,
        summary=summary,
        pre_compact_token_count=pre_compact_token_count,
        true_post_compact_token_count=true_post_compact_token_count,
        thinking_disabled=thinking_disabled,
        reasoning_fallback=reasoning_fallback,
    )

    if emit is not None:
        await emit(
            CompactionEvent(
                trigger=trigger,
                outcome="compacted",
                pre_tokens=pre_compact_token_count,
                post_tokens=true_post_compact_token_count,
                summary_chars=len(formatted),
                thinking_disabled=thinking_disabled,
                reasoning_fallback=reasoning_fallback,
                ptl_attempt=ptl_attempts,
            )
        )

    return result


async def auto_compact_if_needed(
    messages: Sequence[dict[str, Any]],
    caller: ModelCallerProtocol,
    budget: ContextBudget,
    *,
    tracking: AutoCompactTracking | None = None,
    enabled: bool = True,
    model_id: str = "",
    anchor: UsageAnchor | None = None,
    snip_tokens_freed: int = 0,
    transcript_path: str | None = None,
    stop: AbortSignal | None = None,
    hooks: HookFn | None = None,
    emit: EmitFn | None = None,
    ctx: ToolUseContext | None = None,
    provider_messages: Sequence[dict[str, Any]] | None = None,
) -> CompactionResult | None:
    if not enabled:
        return None

    if tracking is not None and tracking.consecutive_failures >= MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES:
        if emit is not None:
            await emit(
                CompactionEvent(
                    trigger="auto",
                    outcome="skipped",
                    reason="circuit_breaker",
                    consecutive_failures=tracking.consecutive_failures,
                )
            )
        return None

    if not should_auto_compact(
        messages,
        budget,
        enabled=enabled,
        anchor=anchor,
        tracking=tracking,
        snip_tokens_freed=snip_tokens_freed,
    ):
        return None

    try:
        result = await compact_conversation(
            messages,
            caller,
            budget,
            model_id=model_id,
            trigger="auto",
            transcript_path=transcript_path,
            anchor=anchor,
            stop=stop,
            hooks=hooks,
            emit=emit,
            ctx=ctx,
            provider_messages=provider_messages,
        )
    except CompactionError as error:
        if tracking is not None:
            tracking.consecutive_failures += 1
        failures = tracking.consecutive_failures if tracking is not None else 1
        if emit is not None:
            await emit(
                CompactionEvent(
                    trigger="auto",
                    outcome="failed",
                    reason=getattr(error, "reason", "error"),
                    consecutive_failures=failures,
                    ptl_attempt=getattr(error, "ptl_attempts", 0),
                )
            )
        return None

    if tracking is not None:
        tracking.consecutive_failures = 0
        tracking.compacted = True
        tracking.turn_counter = 0
        tracking.last_compacted_tokens = result.true_post_compact_token_count

    return result


__all__ = [
    "API_ERROR_PREFIX",
    "COMPACT_BOUNDARY_CONTENT",
    "COMPACT_BOUNDARY_KEY",
    "COMPACT_SUMMARY_KEY",
    "COMPACT_SYSTEM_PROMPT",
    "ERROR_MESSAGE_INCOMPLETE_RESPONSE",
    "ERROR_MESSAGE_NOT_ENOUGH_MESSAGES",
    "ERROR_MESSAGE_PROMPT_TOO_LONG",
    "ERROR_MESSAGE_SUMMARY_TOO_SHORT",
    "ERROR_MESSAGE_USER_ABORT",
    "MAX_PTL_RETRIES",
    "PROMPT_TOO_LONG_ERROR_MESSAGE",
    "PROMPT_TOO_LONG_PATTERN",
    "PTL_FALLBACK_DROP_RATIO",
    "PTL_RETRY_MARKER",
    "PTL_RETRY_MARKER_KEY",
    "ApiErrorSummaryError",
    "AutoCompactTracking",
    "CompactionBlockedError",
    "CompactionError",
    "CompactionResult",
    "IncompleteResponseError",
    "NotEnoughMessagesError",
    "PromptTooLongError",
    "SummaryTooShortError",
    "auto_compact_if_needed",
    "build_post_compact_messages",
    "compact_conversation",
    "create_compact_boundary_message",
    "create_ptl_retry_marker_message",
    "find_last_compact_boundary_index",
    "group_messages_by_api_round",
    "is_compact_boundary_message",
    "is_prompt_too_long_text",
    "is_ptl_retry_marker_message",
    "merge_hook_instructions",
    "messages_after_compact_boundary",
    "parse_prompt_too_long_token_counts",
    "prompt_too_long_token_gap",
    "should_auto_compact",
    "starts_with_api_error_prefix",
    "strip_images_from_messages",
    "truncate_head_for_ptl_retry",
]
