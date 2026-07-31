"""T1-CONTRATO — shapes invariantes (BLUEPRINT §1.1). Ids opacos, sin identidad interpretada.

Subconjunto MÍNIMO para A2.1: lo justo para mover un turno de texto por el loop mínimo.
El shape rico (taxonomía completa de 07, `Usage` con cache/coste, `ToolResult` con
new_messages/context_modifier) se enriquece en A2.2+ — aquí sólo lo que el andamiaje ejercita.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# --- unidad de trabajo (01·CTR-02..CTR-15) -----------------------------------
@dataclass(frozen=True)
class RuntimeTask:
    """Entrada del runtime. `owner_id`/`session_id` = ids OPACOS (01·CTR-05): el
    runtime nunca los interpreta; el integrador los atribuye vía su repo (S20)."""

    prompt: str
    description: str | None = None
    subagent_type: str | None = None
    model_override: str | None = None  # 01·CTR-03
    max_turns: int | None = None  # 01·CTR-14
    timeout_seconds: float | None = None  # 01·CTR-15 (armado por S24)
    owner_id: str | None = None  # id opaco
    session_id: str | None = None  # id opaco


class TaskStatus(str, Enum):
    """05·E1 — estado del ciclo de vida de una task/subagente."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# --- mensajes / tools (contrato mínimo) --------------------------------------
@dataclass(frozen=True)
class ToolCall:
    """Una petición de tool DENTRO del historial (distinta de `ToolCallEvent`, que es
    del canal de eventos). A2.3 la usa para re-inyectar el turno assistant-con-tool_use
    en la siguiente vuelta del modelo (round-trip multivuelta). `input` = argumentos ya
    aplanados desde el stream del provider."""

    call_id: str
    name: str
    input: dict[str, object]


@dataclass(frozen=True)
class Message:
    """Contrato de historial. A2.1/A2.2: texto-solo (`role`+`content`). A2.3 lo enriquece
    para el round-trip de tools: un turno `assistant` puede portar `tool_calls`; un turno
    `tool` responde a un `tool_call_id` concreto (mapea a `ToolResultMessage` del motor)."""

    role: str  # "user" | "assistant" | "tool"
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()  # sólo en role=="assistant" (A2.3)
    tool_call_id: str | None = None  # sólo en role=="tool": qué call responde
    tool_name: str | None = None  # sólo en role=="tool"
    is_error: bool = False  # sólo en role=="tool": el dispatch falló/timeout


@dataclass(frozen=True)
class ToolSchema:
    """Lo que el caller anuncia al modelo (09·A1). El JSON-Schema lo valida `agentic_models`."""

    name: str
    description: str
    input_schema: dict[str, object]


@dataclass(frozen=True)
class ToolResult:
    """09·A22/A23 — crece con new_messages/context_modifier/structured en A2.3+."""

    output: str
    is_error: bool = False
    metadata: dict[str, object] = field(default_factory=dict)


# --- usage (07·E1 — enriquecido en A2.2 contra un turno REAL) -----------------
@dataclass(frozen=True)
class Usage:
    """Espejo de `agentic_models.Usage` (validado A2.2): el provider anthropic puebla
    cache_read/cache_write/total_tokens y `cost` (`calculate_cost_values`) en
    `message_start`/`message_delta` — la mímica `caller.py:228-232` los DESCARTABA
    (sólo input/output + `thinking_tokens=0`). Corrección: `agentic_models.Usage` NO
    tiene `thinking_tokens`; el campo ficticio se retira. `cost_usd` = `cost.total`."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0  # 07·E1 — anthropic `cache_read_input_tokens`
    cache_write: int = 0  # anthropic `cache_creation_input_tokens`
    total_tokens: int = 0
    cost_usd: float = 0.0  # `UsageCost.total` del provider


# --- taxonomía de eventos (07 — subconjunto A2.1) ----------------------------
@dataclass(frozen=True)
class Event:
    """07·A3 — base frozen extensible. Canal único ordenado (S5)."""


@dataclass(frozen=True)
class InitEvent(Event):  # 07·F0
    task_id: str
    model_id: str


@dataclass(frozen=True)
class TokenEvent(Event):  # 07·B — texto incremental
    text: str
    kind: str = "text"  # "text" | "thinking"


@dataclass(frozen=True)
class ThinkingEvent(Event):  # 07·B1 / 16·A4 (hoy skip en el caller mímica)
    text: str


@dataclass(frozen=True)
class ToolCallEvent(Event):  # el modelo pide una tool (dispatch = A2.3)
    call_id: str
    name: str
    input: dict[str, object]


@dataclass(frozen=True)
class ToolResultEvent(Event):
    call_id: str
    output: str
    is_error: bool = False


@dataclass(frozen=True)
class DoneEvent(Event):  # fin de UNA vuelta de modelo
    usage: Usage
    stop_reason: str = "end_turn"


@dataclass(frozen=True)
class ResultEvent(Event):  # 07·D1/D2 — TERMINAL del turno (hoy ausente en la mímica)
    text: str
    usage: Usage


@dataclass(frozen=True)
class ErrorEvent(Event):  # 07·D5 — `code` (no colapsar a str, 16·C1)
    code: str
    message: str


@dataclass(frozen=True)
class CompactBoundaryEvent(Event):  # 07·H1 — el loop emite esto cuando el trigger LR1 compacta
    """Emitido por el MECANISMO base (loop) cuando una battery de compactación (S9) colapsó
    el historial. `collapsed` = cuántos mensajes se fundieron; `reason` = por qué disparó.
    El base emite el evento SIN conocer la battery concreta que hizo el trabajo (A2.4)."""

    collapsed: int
    reason: str = "overflow"
