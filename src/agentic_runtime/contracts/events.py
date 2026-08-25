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
    cache_read: int = 0
    cache_write: int = 0

    @property
    def context_tokens(self) -> int:
        return self.input_tokens + self.cache_write + self.cache_read + self.output_tokens


@dataclass(frozen=True, kw_only=True)
class Event:
    """Tipo base de todos los eventos del runtime. Frozen — inmutable post-construcción.

    Los cinco campos de identidad son **atribución opaca** (`ID-6`/`K4`): el
    runtime los puebla y no los lee; el consumidor filtra por ellos.

    **Dónde se pueblan (`FIND-STREAM-1`).** En un **sumidero único**, `AgentLoop._emit`,
    espejo de `insertMessageChain` del canónico (`sessionStorage.ts:993-1083`), que
    decora todo mensaje de salida en un solo choke point en vez de pedirle a cada
    emisor que recuerde los campos. El sellado es **incondicional**, no «sólo si está
    vacío»: el comentario portante de `sessionStorage.ts:1049-1056` documenta que
    sellar condicionalmente reintroduce la identidad cruzada al reemitir.

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
class ThinkingEvent(Event):
    """Razonamiento del modelo — el canal que faltaba en el bus.

    Existe por dos motivos distintos que conviene no confundir:

    1. **Presentación.** El motor emite el resumen de razonamiento mientras
       piensa; sin este evento el consumidor no tiene por dónde recibirlo y la
       espera es una pantalla muda.
    2. **Round-trip.** `signature` es el **item de razonamiento entero**, opaco
       y serializado por el motor (incluye su `encrypted_content` cuando lo
       hay). Es lo que hay que devolver en el request siguiente para que el
       modelo continúe su cadena en vez de re-razonar desde cero. El runtime no
       lo interpreta: lo transporta y lo persiste.

    `final=False` son los deltas en vivo; `final=True` cierra el bloque y es el
    único que trae `signature`. `model_id` viaja porque **las firmas están atadas
    al modelo** que las generó: reproducirlas contra otro modelo es un 400 (el
    canónico lo resuelve igual, `query.ts:924` → `stripSignatureBlocks`).
    """

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
    """Un mensaje añadido a la historia del turno, visible en el stream público.

    Propiedad canónica que reproduce (`#10`): **el stream lleva lo mismo que la
    historia**. `query.ts` no tiene un canal aparte para anuncios — rinde los mismos
    `Message` que persiste, y cada anuncio (delta de diferidas, listado de skills,
    recall, memoria) es un `AttachmentMessage` yieldado al stream (`:1588`, `:1610`,
    `:1624`). Sin esto un consumidor no ve NADA de lo que el runtime le inyecta al
    modelo, que es justo donde vive el patrón de fallo dominante del barrido.

    `origin` clasifica la procedencia sin interpretarla: el runtime la rotula, el
    consumidor filtra por ella.
    """

    role: str = ""
    content: str = ""
    origin: str = ""


@dataclass(frozen=True)
class TurnStartEvent(Event):
    """Frontera de turno y **plan de tools como DATO**.

    Espejo de `{type:'stream_request_start'}` (`query.ts:337`), que A rinde una vez
    por iteración. Lleva además los nombres anunciados y cuáles iban diferidos: A los
    contabiliza (`analyzeContext.ts`) y sin ellos el consumidor tendría que
    re-parsear el texto del anuncio — que es exactamente la enfermedad diagnosticada
    en `FIND-DEFER-1`, no su remedio.
    """

    turn: int = 0
    tool_names: tuple[str, ...] = ()
    deferred_names: tuple[str, ...] = ()


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
    "MessageEvent",
    "ThinkingEvent",
    "TokenEvent",
    "ToolCallEvent",
    "ToolResultEvent",
    "TurnStartEvent",
    "Usage",
]
