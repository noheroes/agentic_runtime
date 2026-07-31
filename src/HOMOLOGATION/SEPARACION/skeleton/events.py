"""S5 · `EventBus` (canal único ordenado) — T2-BASE-MECANISMO (SEAMS §S5).

`existe-fiel` en la mímica (`bus.py:26-45`); aquí se re-encarna el mecanismo en
clean-room B para que el spike lo ejercite. Invariante 07·A4: `emit` aísla cada
handler con try/except — un handler que revienta NO tumba el canal ni a los demás.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar, cast

from skeleton.contracts import Event

E = TypeVar("E", bound=Event)

Unsubscribe = Callable[[], None]


class EventBus:
    """Bus in-proc. `subscribe` (por tipo) y `subscribe_all` (todo) — el integrador
    consume por `subscribe_all` (-> S6 wire) o por `async for` sobre `stream()`."""

    def __init__(self) -> None:
        # Guardamos el par (tipo|None, handler-widened). None = subscribe_all.
        self._handlers: list[tuple[type[Event] | None, Callable[[Event], None]]] = []

    def subscribe(self, event_type: type[E], handler: Callable[[E], None]) -> Unsubscribe:
        entry: tuple[type[Event] | None, Callable[[Event], None]] = (
            event_type,
            cast(Callable[[Event], None], handler),
        )
        self._handlers.append(entry)
        return lambda: self._remove(entry)

    def subscribe_all(self, handler: Callable[[Event], None]) -> Unsubscribe:
        entry: tuple[type[Event] | None, Callable[[Event], None]] = (None, handler)
        self._handlers.append(entry)
        return lambda: self._remove(entry)

    def emit(self, event: Event) -> None:
        # Copia defensiva: un handler podría (des)suscribir durante el despacho.
        for event_type, handler in list(self._handlers):
            if event_type is not None and not isinstance(event, event_type):
                continue
            try:
                handler(event)
            except Exception:  # noqa: BLE001 — 07·A4: aislar el handler, no tumbar el canal.
                # En el runtime real esto va a un `ErrorEvent`/log del propio bus;
                # en el spike basta con no propagar (evidencia: el turno no se rompe).
                pass

    def _remove(self, entry: tuple[type[Event] | None, Callable[[Event], None]]) -> None:
        try:
            self._handlers.remove(entry)
        except ValueError:
            pass
