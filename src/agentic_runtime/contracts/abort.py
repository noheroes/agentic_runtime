from __future__ import annotations

import asyncio
from enum import Enum
from typing import Protocol, runtime_checkable

INTERRUPT_MESSAGE = "[Request interrupted by user]"
INTERRUPT_MESSAGE_FOR_TOOL_USE = "[Request interrupted by user for tool use]"
TOOL_RESULT_INTERRUPTED = "Interrupted by user"


class AbortReason(str, Enum):
    USER_INTERRUPT = "user_interrupt"
    TIMEOUT = "timeout"
    AGENT_KILLED = "agent_killed"
    TURN_CANCELLED = "turn_cancelled"


@runtime_checkable
class AbortSignal(Protocol):

    @property
    def aborted(self) -> bool: ...

    def reason(self) -> AbortReason | None: ...

    async def wait(self) -> None: ...


class AbortController:

    __slots__ = ("_event", "_reason")

    def __init__(self) -> None:
        self._reason: AbortReason | None = None
        self._event: asyncio.Event | None = None

    @property
    def aborted(self) -> bool:
        return self._reason is not None

    def reason(self) -> AbortReason | None:
        return self._reason

    def abort(self, reason: AbortReason = AbortReason.USER_INTERRUPT) -> None:
        if self._reason is None:
            self._reason = reason
            if self._event is not None:
                self._event.set()

    async def wait(self) -> None:
        if self._reason is not None:
            return
        if self._event is None:
            self._event = asyncio.Event()
        await self._event.wait()


__all__ = [
    "INTERRUPT_MESSAGE",
    "INTERRUPT_MESSAGE_FOR_TOOL_USE",
    "TOOL_RESULT_INTERRUPTED",
    "AbortController",
    "AbortReason",
    "AbortSignal",
]
