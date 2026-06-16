"""
Hooks — puntos de intercepción del ciclo de vida con poder de decisión.

Distinto del EventBus (events/), que solo emite progreso de forma unidireccional.
Un hook puede bloquear, modificar input, denegar, inyectar contexto o detener.

Taxonomía tomada del proyecto canónico
(claude-code/src/entrypoints/sdk/coreSchemas.ts:355).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Optional, Protocol, runtime_checkable


class HookEvent(str, Enum):
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    POST_TOOL_USE_FAILURE = "PostToolUseFailure"
    NOTIFICATION = "Notification"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    SESSION_START = "SessionStart"
    SESSION_END = "SessionEnd"
    STOP = "Stop"
    STOP_FAILURE = "StopFailure"
    SUBAGENT_STOP = "SubagentStop"
    PRE_COMPACT = "PreCompact"


@dataclass(frozen=True)
class HookDecision:
    """Resultado que un handler devuelve para influir en el ciclo.

    - block: rechaza la acción (p.ej. un tool en PreToolUse) sin detener el loop.
    - stop: detiene la ejecución del agente.
    - message: razón legible del block/stop.
    - modified_input: reemplazo del input de la herramienta (PreToolUse).
    - additional_context: texto a inyectar en el contexto del modelo.
    """

    block: bool = False
    stop: bool = False
    message: Optional[str] = None
    modified_input: Optional[dict] = None
    additional_context: Optional[str] = None

    @classmethod
    def allow(cls) -> "HookDecision":
        return cls()

    @classmethod
    def blocked(cls, message: str) -> "HookDecision":
        return cls(block=True, message=message)

    @classmethod
    def stopped(cls, message: str) -> "HookDecision":
        return cls(stop=True, message=message)


# Un handler recibe el payload del punto de ciclo y opcionalmente devuelve una decisión.
HookHandler = Callable[[HookEvent, dict], Awaitable[Optional[HookDecision]]]


@runtime_checkable
class HookSinkProtocol(Protocol):
    """Contrato que cualquier consumidor implementa para recibir hooks."""

    async def handle(self, event: HookEvent, payload: dict) -> Optional[HookDecision]: ...


__all__ = ["HookEvent", "HookDecision", "HookHandler", "HookSinkProtocol"]
