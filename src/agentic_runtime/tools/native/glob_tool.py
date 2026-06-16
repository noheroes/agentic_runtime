from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext


class GlobTool:
    name = "glob"
    description = "Find files matching a glob pattern."
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string"},
            "path": {"type": "string"},
        },
        "required": ["pattern"],
    }
    category = ToolCategory.FILE
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        base = Path(input.get("path", "."))
        pattern = input["pattern"]
        try:
            matches = sorted(str(p) for p in base.glob(pattern))
            return ToolResult(tool_name=self.name, output="\n".join(matches))
        except Exception as exc:
            return ToolResult.error(self.name, str(exc))
