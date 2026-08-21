from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .deferred import discovered_tool_names, is_deferred_tool
from .deferred_delta import compute_deferred_tools_delta, render_deferred_tools_delta
from .native.tool_search import TOOL_SEARCH_TOOL_NAME

if TYPE_CHECKING:
    from ..context.tool_use import ToolUseContext
    from .protocol import ToolProtocol


def _base_schema(tool: ToolProtocol) -> dict[str, Any]:
    return {"name": tool.name, "description": tool.description, "parameters": tool.input_schema}


@dataclass(frozen=True)
class TurnToolPlan:
    tool_schemas: list[dict[str, Any]]
    announcements: list[str] = field(default_factory=list)
    deferred_names: tuple[str, ...] = ()


@runtime_checkable
class DeferredToolStrategy(Protocol):
    def prepare_turn(self, ctx: ToolUseContext, pool: list[ToolProtocol]) -> TurnToolPlan:
        ...


class SoftwareDeferredStrategy:
    def prepare_turn(self, ctx: ToolUseContext, pool: list[ToolProtocol]) -> TurnToolPlan:
        deferred_names = {t.name for t in pool if is_deferred_tool(t)}
        tool_search_active = bool(deferred_names)
        discovered = discovered_tool_names(ctx)

        schemas: list[dict[str, Any]] = []
        for tool in pool:
            if tool.name == TOOL_SEARCH_TOOL_NAME:
                if not tool_search_active:
                    continue
            elif tool.name in deferred_names and tool.name not in discovered:
                continue
            schemas.append(_base_schema(tool))

        announcements: list[str] = []
        delta = compute_deferred_tools_delta(pool, ctx.messages)
        if delta is not None:
            added, removed = delta
            announcements.append(render_deferred_tools_delta(added, removed))
        return TurnToolPlan(
            tool_schemas=schemas,
            announcements=announcements,
            deferred_names=tuple(t.name for t in pool if is_deferred_tool(t)),
        )


__all__ = [
    "DeferredToolStrategy",
    "SoftwareDeferredStrategy",
    "TurnToolPlan",
]
