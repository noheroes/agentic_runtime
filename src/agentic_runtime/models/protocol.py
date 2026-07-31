"""`S1` · la costura CENTRAL del runtime con el motor (`SEAMS §S1`, `TRAMO-1 C2`).

Lo que esta firma corrige es un caso de libro de *descarte silencioso*: el base
pedía al motor **menos de lo que el motor sabe hacer** (sin `temperature`, sin
`max_tokens`, sin `metadata`, sin razonamiento) y lo poco que pedía lo pedía con
el tipo equivocado —`stop: asyncio.Event`, que ningún provider sabe leer porque
todos consultan `.aborted` (`16·A6`, estado `existe-roto`)—. Ni una cosa ni la
otra daban error: daban un turno que corría bien y hacía menos.

**Límite honesto medido, no supuesto** (`agentic_models==0.2.0`, leída 1→EOF):
`temperature`, `max_tokens` y `metadata` son campos reales de `StreamOptions`;
`thinking`/`effort` **no son passthrough** —los traduce el puente a
`stream_simple(reasoning=…)`—; y `tool_choice`/`output_format` **no tienen
ninguna representación** en esa versión. El Protocol los declara igual porque la
costura describe lo que un motor puede ofrecer, no lo que ofrece el puente de
hoy; lo que no se permite es que un puente los reciba y los tire callando —
`AgenticModelsCaller` levanta `UnsupportedModelOptionError`. Ese descarte en
silencio es exactamente el defecto que produjo el `stop` roto.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Literal,
    Mapping,
    Protocol,
    runtime_checkable,
)

from ..contracts.abort import AbortSignal

if TYPE_CHECKING:
    from ..events.protocol import Event


class Effort(str, Enum):
    """Nivel de razonamiento pedido al motor (`16·A2`/`B5`).

    Los cinco niveles del corpus. Cada motor decide cómo los rinde: el puente a
    `agentic_models` los traduce a `SimpleStreamOptions.reasoning`, que el
    provider clampa (`xhigh → high`) si no los soporta todos.
    """

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"


@dataclass(frozen=True)
class ThinkingConfig:
    """Presupuesto de pensamiento (`16·A2`/`B7`).

    Distinto de `Effort` a propósito: `effort` es *cuánto esfuerzo*, esto es
    *cuántos tokens como techo*. `enabled=False` apaga el razonamiento aunque
    venga un `effort` — el apagado explícito manda sobre el nivel.
    """

    enabled: bool = True
    budget_tokens: int | None = None


@dataclass(frozen=True)
class OutputFormat:
    """Salida estructurada por schema (`16·B11`)."""

    json_schema: Mapping[str, Any]
    name: str = "response"
    strict: bool = True


@dataclass(frozen=True)
class ToolChoice:
    """Cómo se fuerza (o no) el uso de tools en el turno (`16·B10`).

    `mode="tool"` exige `tool_name`; el resto lo ignora.
    """

    mode: Literal["auto", "required", "none", "tool"] = "auto"
    tool_name: str | None = None


@dataclass(frozen=True)
class ModelOptions:
    """Las opciones de `S1` que NO dependen del turno, agrupadas para viajar.

    El Protocol las expande en kwargs explícitos (así lo fija `SEAMS §S1`), pero
    quien las porta —el integrador → `RuntimeConfig` → `AgentLoop`— necesita un
    solo objeto que atravesar. `metadata` es OPACA (`DEUDA-A ID-7`): el runtime
    la transporta hasta el cable y **no la lee** por el camino; su contenido es
    del integrador (T3), el slot es del motor (T1).
    """

    thinking: ThinkingConfig | None = None
    effort: Effort | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    output_format: OutputFormat | None = None
    tool_choice: ToolChoice | None = None
    metadata: Mapping[str, str] | None = None

    def as_kwargs(self) -> dict[str, Any]:
        """Sólo lo poblado. Un caller de terceros que aún no adopte un kwarg no
        se rompe por recibir `None` explícito en todos ellos."""
        pairs = (
            ("thinking", self.thinking),
            ("effort", self.effort),
            ("temperature", self.temperature),
            ("max_tokens", self.max_tokens),
            ("output_format", self.output_format),
            ("tool_choice", self.tool_choice),
            ("metadata", self.metadata),
        )
        return {k: v for k, v in pairs if v is not None}


class UnsupportedModelOptionError(NotImplementedError):
    """Un puente recibió una opción de `S1` que su motor no sabe expresar.

    Se levanta en vez de ignorarla: la alternativa —seguir adelante sin ella— es
    un turno que corre bien y hace algo distinto de lo pedido, que es justo el
    modo de fallo que este contrato existe para eliminar.
    """


@dataclass(frozen=True)
class ModelRequest:
    """Immutable model request — the loop builds this and passes it to the caller."""

    messages: list[dict]
    tools: list[dict]
    model_id: str
    stop: AbortSignal | None = field(default=None, compare=False)
    options: ModelOptions = field(default_factory=ModelOptions)


@runtime_checkable
class ModelCallerProtocol(Protocol):
    """
    Primitive the loop uses to call a model.
    Projects implement this protocol with their chosen LLM client.
    """

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        stop: AbortSignal | None = None,
        model_id: str = "",
        system_sections: list[str] | None = None,
        system_override: str | None = None,
        thinking: ThinkingConfig | None = None,
        effort: Effort | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        output_format: OutputFormat | None = None,
        tool_choice: ToolChoice | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> AsyncGenerator[Event, None]: ...

    def supports_native_tool_search(self, model_id: str = "") -> bool:
        """¿El provider resuelve tools diferidas server-side? El loop elige con
        esto entre la estrategia diferida nativa y la simulada."""
        ...


__all__ = [
    "Effort",
    "ModelCallerProtocol",
    "ModelOptions",
    "ModelRequest",
    "OutputFormat",
    "ThinkingConfig",
    "ToolChoice",
    "UnsupportedModelOptionError",
]
