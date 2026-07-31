"""Eventos del runtime — T1 invariante (`07·events`, `SEAMS §S5`).

**Decisión de forma vigente (`A3.DB §7.2`, forma de `K4`):** la identidad viaja
en **campos del `Event` BASE**, *no* en un `EventEnvelope` que envuelva. Razón
técnica verificada: `EventBus.emit` despacha por `type(event)` y
`subscribe(TokenEvent, handler)` es la API tipada — un envelope colapsaría todos
los tipos en uno y rompería el despacho tipado, que es lo mejor que hoy tiene el
bus. Añadir campos **con default** al base es viable porque los cinco subtipos
tienen todos sus campos con default.

Los campos de identidad son **opacos y no interpretados** por el runtime: sirven
para que un sink suscrito por la costura pública pueda atribuir (`ID-6`), que hoy
es imposible sin recibir el `ToolUseContext` entero.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar

T = TypeVar("T", bound="Event")


@dataclass
class Usage:
    """Contabilidad de tokens — **única** (unifica las dos divergentes, `07·E4`).

    Antes existían dos: un dataclass en `events/` con `thinking_tokens` y un
    `BaseModel` en `execution/session/` sin él. Dos shapes con el mismo nombre
    para el mismo concepto es un fork del ecosistema esperando a ocurrir.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0


@dataclass(frozen=True, kw_only=True)
class Event:
    """Tipo base de todos los eventos del runtime. Frozen — inmutable post-construcción.

    Los cinco campos de identidad son **atribución opaca** (`ID-6`/`K4`): el
    runtime los puebla y no los lee; el consumidor filtra por ellos.

    **`kw_only` no es cosmético — corrige la forma de `K4`.** `A3.DB §7.2` acreditó
    la viabilidad de añadir campos con default al base contra *los cinco subtipos
    propios*, que ya tenían todos sus campos con default. Pero el bus es una
    **primitiva de extensión**: un consumidor declara sus propios `Event`, y con
    campos posicionales en el base cualquier subtipo suyo con un campo **sin**
    default deja de construirse (`non-default argument follows default argument`).
    Es decir: la forma vigente de `K4`, tal como estaba escrita, imponía «todos tus
    campos con default» a todo el ecosistema. Con `kw_only=True` los campos de
    identidad salen del orden posicional y la restricción desaparece.
    Verificado corriendo: `tests/test_events.py::test_custom_event_type_works`.
    """

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


class EventBusProtocol(Protocol):
    # Genérico en el subtipo: un handler puede declarar el evento concreto que
    # consume (p.ej. `Callable[[TokenEvent], ...]`) sin romper el tipado.
    def subscribe(self, event_type: type[T], handler: Callable[[T], Awaitable[None]]) -> None: ...
    def subscribe_all(self, handler: EventHandler) -> None: ...
    async def emit(self, event: Event) -> None: ...


__all__ = [
    "DoneEvent",
    "ErrorEvent",
    "Event",
    "EventBusProtocol",
    "EventHandler",
    "TokenEvent",
    "ToolCallEvent",
    "ToolResultEvent",
    "Usage",
]
