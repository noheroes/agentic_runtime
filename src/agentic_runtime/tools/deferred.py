from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from .native.tool_search import TOOL_SEARCH_TOOL_NAME

if TYPE_CHECKING:
    from ..context.tool_use import ToolUseContext
    from .protocol import ToolProtocol

_DISCOVERED_KEY = "discovered_tools"


def is_mcp_tool(tool: ToolProtocol) -> bool:
    info = getattr(tool, "mcp_info", None)
    return isinstance(info, dict) and bool(info.get("server_name"))


def is_deferred_tool(tool: ToolProtocol) -> bool:
    if tool.name == TOOL_SEARCH_TOOL_NAME:
        return False
    if is_mcp_tool(tool):
        return True
    return bool(getattr(tool, "deferred", False))


def discovered_tool_names(ctx: ToolUseContext) -> set[str]:
    return set(ctx.app_state.capabilities.get(_DISCOVERED_KEY, []) or [])


def mark_tools_discovered(ctx: ToolUseContext, names: Iterable[str]) -> None:
    current = discovered_tool_names(ctx)
    current.update(names)
    ctx.app_state.capabilities[_DISCOVERED_KEY] = sorted(current)


__all__ = [
    "discovered_tool_names",
    "is_deferred_tool",
    "is_mcp_tool",
    "mark_tools_discovered",
]
