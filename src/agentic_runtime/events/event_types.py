from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .protocol import Event


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0


@dataclass(frozen=True)
class TokenEvent(Event):
    content: str = ""


@dataclass(frozen=True)
class ToolCallEvent(Event):
    tool_name: str = ""
    tool_input: dict = field(default_factory=dict)
    call_id: str = ""


@dataclass(frozen=True)
class ToolResultEvent(Event):
    call_id: str = ""
    result: str = ""
    is_error: bool = False


@dataclass(frozen=True)
class DoneEvent(Event):
    stop_reason: str = "stop"
    usage: Optional[Usage] = None


@dataclass(frozen=True)
class ErrorEvent(Event):
    message: str = ""
