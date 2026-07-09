"""Estrategia de carga diferida de tools — primitiva seleccionada por capability del provider.

Reemplaza el par de seams del loop (anuncio de nombres + filtrado de schemas) por una única
interfaz con dos ramas:

- **Simulada (fallback):** filtra las diferidas no descubiertas y las anuncia por un
  `<system-reminder>` con sus NOMBRES; ToolSearch se resuelve client-side (dispatcher).
  Es el comportamiento vigente, movido tras la interfaz sin cambios de conducta.
- **Nativa (gpt-5 / Responses):** incluye TODAS las tools y marca las diferidas con
  `defer_loading=True`; `agentic_models` emite ese flag y añade el `tool_search` server-side,
  y la API descubre/expande las tools por su cuenta. Sin anuncio de nombres ni ToolSearch
  client-side.

Contrato durable: `new_core/PLAN_DEFERRED_LOADING_PRIMITIVA.md` §2-3.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .deferred import discovered_tool_names, is_deferred_tool
from .deferred_delta import compute_deferred_tools_delta, render_deferred_tools_delta
from .native.tool_search import TOOL_SEARCH_TOOL_NAME

if TYPE_CHECKING:
    from ..context.tool_use import ToolUseContext
    from .protocol import ToolProtocol


def _base_schema(tool: "ToolProtocol") -> dict:
    return {"name": tool.name, "description": tool.description, "parameters": tool.input_schema}


@dataclass(frozen=True)
class TurnToolPlan:
    """Plan de tools del turno: schemas a anunciar (cada uno puede llevar `defer_loading`)
    y mensajes `<system-reminder>` a insertar (el loop los envuelve y añade a `ctx.messages`)."""
    tool_schemas: list[dict]
    announcements: list[str] = field(default_factory=list)


@runtime_checkable
class DeferredToolStrategy(Protocol):
    def prepare_turn(self, ctx: "ToolUseContext", pool: list["ToolProtocol"]) -> TurnToolPlan:
        """Decide schemas (con/sin `defer_loading`) y anuncios a partir del pool ensamblado."""
        ...

    def owns_search_dispatch(self) -> bool:
        """True (simulada): el runtime ejecuta ToolSearch client-side y marca descubiertas.
        False (nativa): el provider resuelve el search server-side; el runtime no dispatcha."""
        ...


class SimulatedDeferredStrategy:
    """Fallback client-side — comportamiento vigente encapsulado (ver módulo)."""

    def prepare_turn(self, ctx: "ToolUseContext", pool: list["ToolProtocol"]) -> TurnToolPlan:
        deferred_names = {t.name for t in pool if is_deferred_tool(t)}
        tool_search_active = bool(deferred_names)
        discovered = discovered_tool_names(ctx)

        schemas: list[dict] = []
        for tool in pool:
            if tool.name == TOOL_SEARCH_TOOL_NAME:
                if not tool_search_active:
                    continue  # sin diferidas, no hay nada que buscar
            elif tool.name in deferred_names and tool.name not in discovered:
                continue  # diferida no descubierta → oculta hasta ToolSearch
            schemas.append(_base_schema(tool))

        announcements: list[str] = []
        delta = compute_deferred_tools_delta(pool, ctx.messages)
        if delta is not None:
            added, removed = delta
            announcements.append(render_deferred_tools_delta(added, removed))
        return TurnToolPlan(tool_schemas=schemas, announcements=announcements)

    def owns_search_dispatch(self) -> bool:
        return True


class NativeDeferredStrategy:
    """Rama nativa Responses — el provider resuelve el tool-search server-side."""

    def prepare_turn(self, ctx: "ToolUseContext", pool: list["ToolProtocol"]) -> TurnToolPlan:
        schemas: list[dict] = []
        for tool in pool:
            if tool.name == TOOL_SEARCH_TOOL_NAME:
                continue  # el provider añade su propio tool_search server-side
            schema = _base_schema(tool)
            if is_deferred_tool(tool):
                schema["defer_loading"] = True
            schemas.append(schema)
        return TurnToolPlan(tool_schemas=schemas, announcements=[])

    def owns_search_dispatch(self) -> bool:
        return False


__all__ = [
    "DeferredToolStrategy",
    "NativeDeferredStrategy",
    "SimulatedDeferredStrategy",
    "TurnToolPlan",
]
