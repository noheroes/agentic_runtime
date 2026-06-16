from __future__ import annotations

import logging
from collections import defaultdict
from typing import Type

from .protocol import Event, EventHandler

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

    def subscribe(self, event_type: Type[Event], handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

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
