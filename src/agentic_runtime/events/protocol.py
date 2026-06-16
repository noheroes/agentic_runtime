from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Protocol, Type, TypeVar

T = TypeVar("T", bound="Event")


@dataclass(frozen=True)
class Event:
    """Tipo base de todos los eventos del runtime. Frozen — inmutable post-construcción."""


EventHandler = Callable[[Event], Awaitable[None]]


class EventBusProtocol(Protocol):
    def subscribe(self, event_type: Type[Event], handler: EventHandler) -> None: ...
    def subscribe_all(self, handler: EventHandler) -> None: ...
    async def emit(self, event: Event) -> None: ...
