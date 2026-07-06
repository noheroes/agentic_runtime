from __future__ import annotations

from typing import TYPE_CHECKING

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext


class ReadFileTool:
    name = "read_file"
    description = "Read a file and return its contents."
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "offset": {"type": "integer"},
            "limit": {"type": "integer"},
        },
        "required": ["path"],
    }
    category = ToolCategory.FILE
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        try:
            path = ctx.fs.resolve(input["path"], for_write=False)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        try:
            content = path.read_text(errors="replace")
            lines = content.splitlines()
            offset = input.get("offset", 0)
            limit = input.get("limit", len(lines))
            selected = lines[offset : offset + limit]
            return ToolResult(tool_name=self.name, output="\n".join(selected))
        except Exception as exc:
            return ToolResult.error(self.name, str(exc))
