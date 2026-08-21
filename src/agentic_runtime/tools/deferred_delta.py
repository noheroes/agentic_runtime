from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .deferred import is_deferred_tool
from .native.tool_search import TOOL_SEARCH_TOOL_NAME

if TYPE_CHECKING:
    from .protocol import ToolProtocol

_ADDED_HEADER = "The following deferred tools are now available via ToolSearch"
_REMOVED_HEADER = "The following deferred tools are no longer available"


def render_deferred_tools_delta(added_names: list[str], removed_names: list[str]) -> str:
    parts: list[str] = []
    if added_names:
        parts.append(
            f"{_ADDED_HEADER}. Their schemas are NOT loaded — calling them directly will fail "
            f'with InputValidationError. Use {TOOL_SEARCH_TOOL_NAME} with query '
            '"select:<name>[,<name>...]" to load tool schemas before calling them:\n'
            + "\n".join(added_names)
        )
    if removed_names:
        parts.append(
            f"{_REMOVED_HEADER} (their MCP server disconnected). Do not search for them — "
            f"{TOOL_SEARCH_TOOL_NAME} will return no match:\n" + "\n".join(removed_names)
        )
    return "\n\n".join(parts)


def _parse_section_names(content: str, header: str) -> list[str]:
    lines = content.splitlines()
    names: list[str] = []
    collecting = False
    for line in lines:
        if header in line:
            collecting = True
            continue
        if not collecting:
            continue
        stripped = line.strip()
        if not stripped or stripped == "</system-reminder>":
            break
        if _ADDED_HEADER in line or _REMOVED_HEADER in line:
            break
        names.append(stripped)
    return names


def _announced_deferred_names(messages: list[dict[str, Any]]) -> set[str]:
    announced: set[str] = set()
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, str):
            continue
        if _ADDED_HEADER in content:
            announced.update(_parse_section_names(content, _ADDED_HEADER))
        if _REMOVED_HEADER in content:
            for name in _parse_section_names(content, _REMOVED_HEADER):
                announced.discard(name)
    return announced


def compute_deferred_tools_delta(
    pool_tools: list[ToolProtocol], messages: list[dict[str, Any]]
) -> tuple[list[str], list[str]] | None:
    announced = _announced_deferred_names(messages)
    deferred_names = {t.name for t in pool_tools if is_deferred_tool(t)}
    pool_names = {t.name for t in pool_tools}

    added = sorted(n for n in deferred_names if n not in announced)
    removed = sorted(
        n for n in announced if n not in deferred_names and n not in pool_names
    )
    if not added and not removed:
        return None
    return added, removed


__all__ = [
    "compute_deferred_tools_delta",
    "render_deferred_tools_delta",
]
