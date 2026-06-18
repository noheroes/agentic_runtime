from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from .native.tool_search import TOOL_SEARCH_TOOL_NAME

if TYPE_CHECKING:
    from ..context.tool_use import ToolUseContext
    from .protocol import ToolProtocol

# Estado de descubrimiento scopeado por agente: vive en ctx.app_state.capabilities.
# Alineado al canónico, donde el descubrimiento se deriva del historial (tool_reference
# blocks); aquí lo materializamos como estado de capability por contexto (agent_id).
_DISCOVERED_KEY = "discovered_tools"


def is_deferred_tool(tool: "ToolProtocol") -> bool:
    """Una tool diferida no se anuncia hasta que ToolSearch la descubre.

    Espejo de `isDeferredTool`: las tools MCP son diferidas siempre (workflow-specific);
    ToolSearch nunca lo es (el modelo lo necesita para descubrir el resto). Las nativas
    no son diferidas salvo que se marquen explícitamente (`deferred = True`).
    Deferred es VISIBILIDAD, no disponibilidad: la tool sigue ejecutable desde el pool.
    """
    if tool.name == TOOL_SEARCH_TOOL_NAME:
        return False
    return bool(getattr(tool, "deferred", False))


def discovered_tool_names(ctx: "ToolUseContext") -> set[str]:
    return set(ctx.app_state.capabilities.get(_DISCOVERED_KEY, []) or [])


def mark_tools_discovered(ctx: "ToolUseContext", names: Iterable[str]) -> None:
    current = discovered_tool_names(ctx)
    current.update(names)
    ctx.app_state.capabilities[_DISCOVERED_KEY] = sorted(current)


__all__ = [
    "discovered_tool_names",
    "is_deferred_tool",
    "mark_tools_discovered",
]
