from __future__ import annotations

from typing import TYPE_CHECKING

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext


class WriteFileTool:
    name = "write_file"
    description = "Write content to a file."
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    }
    category = ToolCategory.FILE
    requires_permission = True
    safe_for_background = True
    timeout_seconds = 10.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        try:
            path = ctx.fs.resolve(input["path"], for_write=True)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(input["content"])
            return ToolResult(tool_name=self.name, output=str(path))
        except Exception as exc:
            return ToolResult.error(self.name, str(exc))
