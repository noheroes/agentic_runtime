"""Señal de abort — T1 invariante (`SEAMS §S2`).

Defecto que este contrato corrige, verificado a los dos extremos del cable:
`models/protocol.py` tipaba `stop: asyncio.Event` y los providers de
`agentic_models` consultan `getattr(signal, "aborted", False)` — un
`asyncio.Event` **no tiene** `.aborted`, luego el abort se ignoraba en silencio
de punta a punta (`16·A6`, estado `existe-roto`).
"""
from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable


class AbortReason(str, Enum):
    """Por qué se abortó. Separa abort de turno y abort de agente (`05·E36`/`08·SIG13`)."""

    USER_INTERRUPT = "user_interrupt"
    TIMEOUT = "timeout"
    AGENT_KILLED = "agent_killed"
    TURN_CANCELLED = "turn_cancelled"


@runtime_checkable
class AbortSignal(Protocol):
    """Lo que el motor consulta. **No** `asyncio.Event`."""

    @property
    def aborted(self) -> bool: ...

    def reason(self) -> AbortReason | None: ...


class AbortController:
    """Implementación concreta mínima de `AbortSignal` (`C2`).

    Existe porque el Protocol solo **no arma nada**: hasta ahora `ctx.stop` era un
    `asyncio.Event` que nadie seteaba y que además ningún provider sabía leer, así
    que el chequeo del loop y el del dispatcher estaban muertos a los dos lados.

    `aborted` se DERIVA de la razón: no hay abort sin motivo. Eso cierra de paso el
    `SIG2` («`ctx.stop` es binario → no puede portar reason») sin añadir un segundo
    campo que pudiera desincronizarse. El primer `abort()` gana — un abort no se
    revierte ni se reetiqueta, para que el motivo que lee el motor sea el que
    provocó de verdad el corte.

    Es deliberadamente **no** `asyncio.Event`: no se espera sobre él, se consulta.
    Quien necesite *esperar* el abort compone su propio Event por fuera; el cable
    que cruza al motor es sólo `.aborted`/`.reason()`.
    """

    __slots__ = ("_reason",)

    def __init__(self) -> None:
        self._reason: AbortReason | None = None

    @property
    def aborted(self) -> bool:
        return self._reason is not None

    def reason(self) -> AbortReason | None:
        return self._reason

    def abort(self, reason: AbortReason = AbortReason.USER_INTERRUPT) -> None:
        if self._reason is None:
            self._reason = reason


__all__ = ["AbortController", "AbortReason", "AbortSignal"]
