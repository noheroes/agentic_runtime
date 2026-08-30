from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar

T = TypeVar("T", bound="Event")

THINKING_TOKENS_SOURCE_PROVIDER = "provider"
THINKING_TOKENS_SOURCE_COUNTED = "counted"
THINKING_TOKENS_SOURCE_UNAVAILABLE = "unavailable"

_THINKING_TOKENS_SOURCE_TRUST = (
    THINKING_TOKENS_SOURCE_PROVIDER,
    THINKING_TOKENS_SOURCE_COUNTED,
    THINKING_TOKENS_SOURCE_UNAVAILABLE,
)


def _thinking_tokens_source_rank(source: str) -> int:
    if source in _THINKING_TOKENS_SOURCE_TRUST:
        return _THINKING_TOKENS_SOURCE_TRUST.index(source)
    return len(_THINKING_TOKENS_SOURCE_TRUST)


def weakest_thinking_tokens_source(current: str, incoming: str) -> str:
    if not current:
        return incoming
    if not incoming:
        return current
    if _thinking_tokens_source_rank(incoming) > _thinking_tokens_source_rank(current):
        return incoming
    return current


THINKING_BUDGET_OVERSHOOT_FACTOR = 2
THINKING_BUDGET_OVERSHOOT_SLACK = 64


def derive_thinking_budget_honored(
    budget_tokens: int | None,
    thinking_tokens: int,
    thinking_tokens_source: str,
) -> bool | None:
    if budget_tokens is None or budget_tokens <= 0:
        return None
    if thinking_tokens_source == THINKING_TOKENS_SOURCE_UNAVAILABLE:
        return None
    ceiling = budget_tokens * THINKING_BUDGET_OVERSHOOT_FACTOR + THINKING_BUDGET_OVERSHOOT_SLACK
    return thinking_tokens <= ceiling


def weakest_thinking_budget_honored(current: bool | None, incoming: bool | None) -> bool | None:
    if current is False or incoming is False:
        return False
    if current is True or incoming is True:
        return True
    return None


@dataclass
class Usage:

    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    cache_read: int = 0
    cache_write: int = 0
    thinking_tokens_source: str = THINKING_TOKENS_SOURCE_UNAVAILABLE
    thinking_budget_tokens: int | None = None
    thinking_budget_honored: bool | None = None

    @property
    def context_tokens(self) -> int:
        return self.input_tokens + self.cache_write + self.cache_read + self.output_tokens


@dataclass(frozen=True, kw_only=True)
class Event:

    task_id: str = ""
    agent_id: str = ""
    session_id: str = ""
    seq: int = 0
    ts: float = 0.0


EventHandler = Callable[[Event], Awaitable[None]]


@dataclass(frozen=True)
class TokenEvent(Event):
    content: str = ""


@dataclass(frozen=True)
class ThinkingEvent(Event):

    content: str = ""
    signature: str = ""
    final: bool = False
    model_id: str = ""


@dataclass(frozen=True)
class ToolCallEvent(Event):
    tool_name: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)
    call_id: str = ""


@dataclass(frozen=True)
class ToolResultEvent(Event):
    call_id: str = ""
    result: str = ""
    is_error: bool = False


@dataclass(frozen=True)
class DoneEvent(Event):
    stop_reason: str = "stop"
    usage: Usage | None = None


@dataclass(frozen=True)
class ErrorEvent(Event):
    message: str = ""


@dataclass(frozen=True)
class MessageEvent(Event):

    role: str = ""
    content: str = ""
    origin: str = ""


@dataclass(frozen=True)
class TurnStartEvent(Event):

    turn: int = 0
    tool_names: tuple[str, ...] = ()
    deferred_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompactionEvent(Event):

    trigger: str = ""
    outcome: str = ""
    reason: str = ""
    direction: str = ""
    user_context: str = ""
    pre_tokens: int = 0
    post_tokens: int = 0
    summary_chars: int = 0
    messages_kept: int = 0
    messages_summarized: int = 0
    thinking_disabled: bool = True
    reasoning_fallback: bool = False
    consecutive_failures: int = 0
    ptl_attempt: int = 0
    dropped_messages: int = 0
    remaining_messages: int = 0


class EventBusProtocol(Protocol):
    def subscribe(self, event_type: type[T], handler: Callable[[T], Awaitable[None]]) -> None: ...
    def subscribe_all(self, handler: EventHandler) -> None: ...
    async def emit(self, event: Event) -> None: ...


__all__ = [
    "THINKING_BUDGET_OVERSHOOT_FACTOR",
    "THINKING_BUDGET_OVERSHOOT_SLACK",
    "THINKING_TOKENS_SOURCE_COUNTED",
    "THINKING_TOKENS_SOURCE_PROVIDER",
    "THINKING_TOKENS_SOURCE_UNAVAILABLE",
    "CompactionEvent",
    "DoneEvent",
    "ErrorEvent",
    "Event",
    "EventBusProtocol",
    "EventHandler",
    "MessageEvent",
    "ThinkingEvent",
    "TokenEvent",
    "ToolCallEvent",
    "ToolResultEvent",
    "TurnStartEvent",
    "Usage",
    "derive_thinking_budget_honored",
    "weakest_thinking_budget_honored",
    "weakest_thinking_tokens_source",
]
