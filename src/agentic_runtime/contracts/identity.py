"""Hilo de identidad — T1 invariante (C9 · `DEUDA-A §2`, `SEAMS §S20`, `00-LEGEND §2.4`).

Regla dura: **el runtime nunca interpreta la identidad; la transporta**. No hay
objeto global de identidad, no hay `userId`/`sessionId` interpretados en ningún
contrato, y el runtime lee de una sesión **sólo su `.id` opaco**.

Grafía **única y vinculante** del cable de scope: `scope`, token opaco
(`SEAMS §0` nota `AC-39`; el corpus llegó a tener cuatro grafías del mismo cable
y el nombre del parámetro **es parte de la costura**).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import NewType, Protocol, runtime_checkable

#: Identificador de sesión — **opaco**. El runtime no lo parsea ni lo compone.
SessionId = NewType("SessionId", str)


@dataclass(frozen=True)
class Scope:
    """Token opaco de scope de persistencia (`DEUDA-A ID-3`).

    Lo **produce el integrador** y cada repo lo antepone a su clave. El runtime no
    lo interpreta: para él es una cadena sin estructura. Ningún repo del runtime
    acepta `user_id: str` literal — ése es exactamente el defecto que `AC-39`
    prohíbe.
    """

    key: str

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("Scope.key no puede ser vacío: un scope vacío colisiona entre tenants")


@runtime_checkable
class RuntimeSessionProtocol(Protocol):
    """Lo que el runtime SÍ lee de una sesión: su id opaco, y nada más."""

    @property
    def id(self) -> str: ...


@dataclass(frozen=True)
class SessionInfo:
    """Entrada del índice de sesiones (`07·K5 SDKSessionInfo`).

    Mínima a propósito: el id opaco + la metadata **del integrador**, que el
    runtime transporta sin leer.
    """

    id: SessionId
    metadata: object = None


class SessionRepo[TMetadata](Protocol):
    """Repo genérico de sesión — el **nido** del hilo de identidad (`SEAMS §S20`).

    Es un seam **opcional**: el integrador degenerado lo usa como default
    single-session; el complejo posee su identidad por fuera y puede ignorarlo
    (blueprint de la referencia PI). Un diseño que lo hiciera obligatorio sería
    el error.

    `TMetadata` es la metadata de sesión **del integrador**: el repo sólo la
    consume (crear, consultar) y nunca la devuelve interpretada, que es justo lo
    que `00-LEGEND §2.4` prohíbe. Sintaxis `PEP 695` (el proyecto pide `>=3.12`)
    en vez de `Protocol[TMetadata]` con un `TypeVar` a mano: la varianza se
    **infiere** del uso en vez de declararse, luego no puede quedar mal declarada.
    La grafía del parámetro —`TMetadata`, `SEAMS §S20`— se conserva: es parte de
    la costura.
    """

    def create(self, metadata: TMetadata) -> SessionId: ...

    def open(self, session_id: SessionId) -> RuntimeSessionProtocol: ...

    def list(self, query: TMetadata) -> list[SessionInfo]: ...

    def delete(self, session_id: SessionId) -> None: ...

    def fork(self, session_id: SessionId) -> SessionId: ...


__all__ = [
    "RuntimeSessionProtocol",
    "Scope",
    "SessionId",
    "SessionInfo",
    "SessionRepo",
]
