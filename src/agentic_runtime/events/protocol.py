"""Reexport del contrato T1 de eventos (`contracts.events`).

El shape vive en `contracts/` porque es invariante; aquí queda sólo el punto de
importación histórico del base. No añadir definiciones nuevas en este archivo.
"""
from __future__ import annotations

from typing import TypeVar

from ..contracts.events import Event, EventBusProtocol, EventHandler

T = TypeVar("T", bound=Event)

__all__ = ["Event", "EventBusProtocol", "EventHandler", "T"]
