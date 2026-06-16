"""
RuntimeSession — contrato mínimo de sesión para el motor de ejecución.

No es la implementación de agent_core. Es lo que local.py y notification.py
necesitan saber de cualquier sesión para operar correctamente.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RuntimeSessionProtocol(Protocol):
    session_id: str
    messages: list[Any]
    turn_count: int
    subagent_depth: int
    input_tokens: int
    output_tokens: int
