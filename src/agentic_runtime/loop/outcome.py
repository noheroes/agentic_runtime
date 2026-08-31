"""`LoopOutcome` — por qué terminó el turno (`02·A4`, reason-codes).

Hasta `C4` el loop devolvía `None`: quien lo invocaba no podía distinguir «el
modelo cerró el turno» de «se acabaron las vueltas», de «alguien abortó», de «no
había model_caller cableado». El canónico sí lo distingue — `query.ts` retorna
`{reason: …}` en cada salida (`:1051` `aborted_streaming`, `:996` `model_error`,
`:1264`/`:1357` `completed`, `:1515` `aborted_tools`, `:1520` `hook_stopped`,
`:1711` `max_turns`) — y esa información es la que permite al integrador decidir
si reintenta, si avisa, o si cierra.

**Vocabulario:** los códigos que espejan al canónico llevan su nombre exacto. Los
que no existen allí van marcados como propios del runtime, porque en el canónico
el caso o no puede ocurrir (`no_model_caller`: el consumidor no entra a `query()`
sin motor) o se resuelve fuera del loop (`short_circuit`: el consumidor ni llega
a llamar a `query()` cuando `shouldQuery` es falso).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LoopEndReason(str, Enum):
    COMPLETED = "completed"
    MAX_TURNS = "max_turns"
    MODEL_ERROR = "model_error"
    ABORTED_STREAMING = "aborted_streaming"
    ABORTED_TOOLS = "aborted_tools"

    ABORTED_PRE_RUN = "aborted_pre_run"
    ABORTED_HARD = "aborted_hard"
    SHORT_CIRCUIT = "short_circuit"
    ENDS_TURN = "ends_turn"
    NO_MODEL_CALLER = "no_model_caller"


@dataclass(frozen=True)
class LoopOutcome:
    """Cómo terminó `AgentLoop.run`. `turn_count` es el nº de vueltas consumidas."""

    reason: LoopEndReason
    turn_count: int = 0
    detail: str | None = None

    @property
    def aborted(self) -> bool:
        return self.reason in (
            LoopEndReason.ABORTED_PRE_RUN,
            LoopEndReason.ABORTED_HARD,
            LoopEndReason.ABORTED_STREAMING,
            LoopEndReason.ABORTED_TOOLS,
        )


__all__ = ["LoopEndReason", "LoopOutcome"]
