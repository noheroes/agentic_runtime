from __future__ import annotations

import logging
from collections import defaultdict
from typing import Awaitable, Callable, Type, TypeVar

from .protocol import Event, EventHandler

T = TypeVar("T", bound=Event)

logger = logging.getLogger(__name__)


class EventBus:
    """
    Bus de eventos del runtime.

    Primitiva de extensión: proyectos llaman `subscribe(MyEvent, handler)` para
    registrar handlers sobre tipos propios o base sin modificar el runtime.
    """

    def __init__(self) -> None:
        self._handlers: dict[Type[Event], list[EventHandler]] = defaultdict(list)
        self._global_handlers: list[EventHandler] = []

    def subscribe(self, event_type: Type[T], handler: Callable[[T], Awaitable[None]]) -> None:
        # El registro es homogéneo en runtime (se invoca por tipo exacto); el cast
        # implícito a EventHandler es seguro porque `emit` solo entrega `event_type`.
        self._handlers[event_type].append(handler)  # type: ignore[arg-type]

    def subscribe_all(self, handler: EventHandler) -> None:
        """Suscribe un handler a TODOS los eventos, sin importar el tipo.

        Primitiva para consumir el stream completo en vivo (p.ej. un transporte SSE):
        recibe Token/ToolCall/ToolResult/Done/Error en orden de emisión.
        """
        self._global_handlers.append(handler)

    async def emit(self, event: Event) -> None:
        handlers = (*self._handlers.get(type(event), ()), *self._global_handlers)
        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                logger.exception("EventBus: error en handler %r para %r", handler, event)
