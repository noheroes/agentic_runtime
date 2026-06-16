from __future__ import annotations

from typing import Callable, Optional

from .protocols import AgentMode


class ModeManager:
    """Registra y controla el modo de cada ejecución activa."""

    def __init__(self) -> None:
        self._modes: dict[str, AgentMode] = {}
        # Extension primitive: callbacks que se llaman ante cada transición
        self._listeners: list[Callable[[str, AgentMode, AgentMode], None]] = []

    def register(self, *, execution_id: str, mode: AgentMode) -> None:
        self._modes[execution_id] = mode

    def unregister(self, execution_id: str) -> None:
        self._modes.pop(execution_id, None)

    def get_mode(self, execution_id: str) -> Optional[AgentMode]:
        return self._modes.get(execution_id)

    def set_mode(self, execution_id: str, mode: AgentMode) -> None:
        current = self._modes.get(execution_id)
        if current == AgentMode.FORK:
            raise ValueError(f"execution_id '{execution_id}' es FORK — el modo es inmutable")
        if current is not None:
            for cb in self._listeners:
                cb(execution_id, current, mode)
        self._modes[execution_id] = mode

    def on_complete(self, execution_id: str) -> bool:
        """True si la ejecución debe emitir notificación al completar."""
        return self._modes.get(execution_id) == AgentMode.BACKGROUND

    # ------------------------------------------------------------------
    # Extension primitive
    # ------------------------------------------------------------------

    def on_transition(self, callback: Callable[[str, AgentMode, AgentMode], None]) -> None:
        """Registra un listener que se llama ante cada cambio de modo (id, de, a)."""
        self._listeners.append(callback)
