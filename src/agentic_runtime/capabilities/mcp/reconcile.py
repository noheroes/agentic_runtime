"""Motor de reconciliación MCP — diff deseado-vs-vivo → connect/disconnect/refresh.

Capacidad transversal de primera clase: el mismo motor lo consumen la mutación
in-process (admin REST add/toggle/delete) y el watcher de fuente externa. El plan
es DATOS puros (testeable sin efectos); el applier los ejecuta sobre el provider.

La detección de "config cambiada" es por IGUALDAD EXPLÍCITA del dump (Regla 1: sin
heurísticas — nunca por similitud)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .config import McpServerConfig


@dataclass(frozen=True)
class ReconcilePlan:
    """Acciones para converger el estado vivo al deseado. Orden determinista."""

    to_connect: tuple[str, ...]
    to_disconnect: tuple[str, ...]
    to_refresh: tuple[str, ...]

    @property
    def is_empty(self) -> bool:
        return not (self.to_connect or self.to_disconnect or self.to_refresh)


class _ReconcileTarget(Protocol):
    async def connect_server(self, name: str) -> bool: ...
    async def disconnect_server(self, name: str) -> None: ...
    async def reconnect_server(self, name: str) -> bool: ...


def plan_reconcile(
    desired: "dict[str, McpServerConfig]",
    live: "dict[str, McpServerConfig]",
) -> ReconcilePlan:
    """Calcula el plan de reconciliación.

    - `desired`: registro deseado completo (un server con `enabled=False` se desea
      NO conectado).
    - `live`: configs de los servers actualmente conectados.
    """
    connect: list[str] = []
    disconnect: list[str] = []
    refresh: list[str] = []

    for name, cfg in desired.items():
        if not cfg.enabled:
            if name in live:
                disconnect.append(name)
            continue
        if name not in live:
            connect.append(name)
        elif live[name].model_dump() != cfg.model_dump():
            refresh.append(name)

    for name in live:
        if name not in desired:
            disconnect.append(name)

    return ReconcilePlan(
        to_connect=tuple(sorted(connect)),
        to_disconnect=tuple(sorted(disconnect)),
        to_refresh=tuple(sorted(refresh)),
    )


async def apply_reconcile(plan: ReconcilePlan, target: _ReconcileTarget) -> None:
    """Ejecuta el plan: desconecta primero (libera nombres/recursos), luego conecta."""
    for name in plan.to_disconnect:
        await target.disconnect_server(name)
    for name in plan.to_connect:
        await target.connect_server(name)
    for name in plan.to_refresh:
        await target.reconnect_server(name)


__all__ = ["ReconcilePlan", "apply_reconcile", "plan_reconcile"]
