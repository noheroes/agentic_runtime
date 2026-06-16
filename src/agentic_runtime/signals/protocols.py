from enum import Enum
from typing import Protocol


class SignalType(str, Enum):
    ABORT = "abort"
    PAUSE = "pause"
    RESUME = "resume"


class SignalHandler(Protocol):
    """Cualquier objeto que pueda recibir una señal."""

    async def handle_signal(self, signal: SignalType) -> None: ...
