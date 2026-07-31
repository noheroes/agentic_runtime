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
    # --- espejo literal del canónico ---
    COMPLETED = "completed"                    # query.ts:1264/1357
    MAX_TURNS = "max_turns"                    # query.ts:1711
    MODEL_ERROR = "model_error"                # query.ts:996
    ABORTED_STREAMING = "aborted_streaming"    # query.ts:1051 — corte a mitad de stream
    ABORTED_TOOLS = "aborted_tools"            # query.ts:1515 — corte en la frontera de vuelta

    # --- propios del runtime, declarados como tales ---
    #: la señal ya estaba activa antes de empezar: no llegó a haber turno.
    ABORTED_PRE_RUN = "aborted_pre_run"
    #: `S11` resolvió la entrada sin modelo (espejo de `shouldQuery === false`,
    #: que en el canónico se decide *antes* de entrar al loop).
    SHORT_CIRCUIT = "short_circuit"
    #: una tool pidió cerrar el turno (HITL multivuelta: `ToolResult.ends_turn`).
    ENDS_TURN = "ends_turn"
    #: el loop se compuso sin `S1`. Es un fallo de cableado, y tiene código propio
    #: para que una prueba pueda aseverarlo en vez de leer un log.
    NO_MODEL_CALLER = "no_model_caller"


@dataclass(frozen=True)
class LoopOutcome:
    """Cómo terminó `AgentLoop.run`. `turn_count` es el nº de vueltas consumidas."""

    reason: LoopEndReason
    turn_count: int = 0
    #: detalle libre del motivo (mensaje de error del modelo, razón del abort).
    detail: str | None = None

    @property
    def aborted(self) -> bool:
        return self.reason in (
            LoopEndReason.ABORTED_PRE_RUN,
            LoopEndReason.ABORTED_STREAMING,
            LoopEndReason.ABORTED_TOOLS,
        )


__all__ = ["LoopEndReason", "LoopOutcome"]
