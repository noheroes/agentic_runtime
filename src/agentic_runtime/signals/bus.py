from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from .protocols import SignalType


@dataclass
class _Node:
    task_id: str
    parent_id: Optional[str]
    signal: Optional[SignalType] = field(default=None)


class SignalHandle:
    """Token que devuelve SignalBus.register(); permite al ejecutor consultar su señal."""

    def __init__(self, bus: "SignalBus", task_id: str, parent_id: Optional[str]) -> None:
        self._bus = bus
        self.task_id = task_id
        self.parent_id = parent_id

    def check(self) -> Optional[SignalType]:
        return self._bus.get_signal(self.task_id)


class SignalBus:
    """Bus de señales con árbol parent→children para cascada de abort/pause/resume."""

    def __init__(self) -> None:
        self._nodes: dict[str, _Node] = {}
        self._lock = asyncio.Lock()

    def register(self, *, task_id: str, parent_id: Optional[str]) -> SignalHandle:
        self._nodes[task_id] = _Node(task_id=task_id, parent_id=parent_id)
        return SignalHandle(bus=self, task_id=task_id, parent_id=parent_id)

    def unregister(self, task_id: str) -> None:
        self._nodes.pop(task_id, None)

    def get_signal(self, task_id: str) -> Optional[SignalType]:
        node = self._nodes.get(task_id)
        return node.signal if node else None

    async def send(
        self,
        *,
        task_id: str,
        signal: SignalType,
        cascade: bool = False,
    ) -> None:
        async with self._lock:
            self._apply(task_id, signal)
            if cascade:
                for child_id in self._children(task_id):
                    self._apply(child_id, signal)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _apply(self, task_id: str, signal: SignalType) -> None:
        node = self._nodes.get(task_id)
        if node is None:
            return
        if signal == SignalType.RESUME:
            node.signal = None
        else:
            node.signal = signal

    def _children(self, parent_id: str) -> list[str]:
        """DFS de todos los descendientes."""
        result: list[str] = []
        queue = [parent_id]
        while queue:
            current = queue.pop()
            for node in self._nodes.values():
                if node.parent_id == current:
                    result.append(node.task_id)
                    queue.append(node.task_id)
        return result

    # ------------------------------------------------------------------
    # Extension primitive — permite proyectos registrar handlers externos
    # ------------------------------------------------------------------

    def register_handler(self, task_id: str, handler: object) -> None:
        """Registra un handler adicional que recibe señales vía handle_signal."""
        node = self._nodes.get(task_id)
        if node is None:
            raise KeyError(f"task_id '{task_id}' no registrado")
        if not hasattr(node, "_handlers"):
            object.__setattr__(node, "_handlers", [])
        node._handlers.append(handler)  # type: ignore[attr-defined]
