from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

TOOL_SEARCH_TOOL_NAME = "ToolSearch"


class ToolSearchTool:
    name = TOOL_SEARCH_TOOL_NAME
    description = (
        "Search for available tools by keyword or select by name. "
        "Use 'select:<tool_name>' for direct selection or keywords to search. "
        "Required before calling deferred tools."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Query to find tools. Use 'select:<tool_name>' for direct selection "
                    "or keywords to search."
                ),
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum results to return (default: 5).",
                "default": 5,
            },
        },
        "required": ["query"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        from ..deferred import is_deferred_tool, mark_tools_discovered

        query = input.get("query", "").strip()
        max_results = int(input.get("max_results", 5))

        # Solo las diferidas necesitan descubrirse; las no-diferidas ya se anuncian.
        deferred = [t for t in ctx.tool_pool.assemble(ctx.permission_context) if is_deferred_tool(t)]

        if query.startswith("select:"):
            name = query[len("select:"):].strip()
            matches = [t for t in deferred if t.name == name]
        else:
            terms = query.lower().split()
            def score(tool) -> int:
                haystack = f"{tool.name} {tool.description}".lower()
                return sum(1 for term in terms if term in haystack)
            scored = [(score(t), t) for t in deferred if score(t) > 0]
            scored.sort(key=lambda x: -x[0])
            matches = [t for _, t in scored[:max_results]]

        # Descubrir = activar: las matched pasan a anunciarse en los próximos turnos
        # y su schema completo se devuelve aquí para que el modelo las invoque ya.
        mark_tools_discovered(ctx, [t.name for t in matches])

        return ToolResult(
            tool_name=self.name,
            output=json.dumps({
                "query": query,
                "matches": [
                    {"name": t.name, "description": t.description, "parameters": t.input_schema}
                    for t in matches
                ],
                "total_deferred_tools": len(deferred),
            }),
        )
