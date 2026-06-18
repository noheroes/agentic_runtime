from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Protocol, Type, TypeVar

T = TypeVar("T", bound="Event")


@dataclass(frozen=True)
class Event:
    """Tipo base de todos los eventos del runtime. Frozen — inmutable post-construcción."""


EventHandler = Callable[[Event], Awaitable[None]]


class EventBusProtocol(Protocol):
    # Genérico en el subtipo: un handler puede declarar el evento concreto que
    # consume (p.ej. `Callable[[TokenEvent], ...]`) sin romper el tipado.
    def subscribe(self, event_type: Type[T], handler: Callable[[T], Awaitable[None]]) -> None: ...
    def subscribe_all(self, handler: EventHandler) -> None: ...
    async def emit(self, event: Event) -> None: ...
