from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

FILE_EDIT_TOOL_NAME = "Edit"


class FileEditTool:
    name = FILE_EDIT_TOOL_NAME
    description = "A tool for editing files. Replaces an exact string in a file with a new string."
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to edit.",
            },
            "old_string": {
                "type": "string",
                "description": "The exact string to replace. Must match exactly, including whitespace.",
            },
            "new_string": {
                "type": "string",
                "description": "The string to replace old_string with.",
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    }
    category = ToolCategory.FILE
    requires_permission = True
    safe_for_background = True
    timeout_seconds = 10.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        file_path = input.get("file_path", "")
        old_string = input.get("old_string", "")
        new_string = input.get("new_string", "")

        if not Path(file_path).is_absolute():
            return ToolResult.error(self.name, "file_path must be absolute.")
        try:
            path = ctx.fs.resolve(file_path, for_write=True)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        if not path.exists():
            return ToolResult.error(self.name, f"File not found: {file_path}")

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return ToolResult.error(self.name, f"Cannot read file: {e}")

        count = content.count(old_string)
        if count == 0:
            return ToolResult.error(
                self.name,
                f"old_string not found in {file_path}. Verify the exact text including whitespace.",
            )
        if count > 1:
            return ToolResult.error(
                self.name,
                f"old_string matches {count} locations in {file_path}. Provide more context to make it unique.",
            )

        new_content = content.replace(old_string, new_string, 1)
        try:
            path.write_text(new_content, encoding="utf-8")
        except Exception as e:
            return ToolResult.error(self.name, f"Cannot write file: {e}")

        return ToolResult(tool_name=self.name, output=f"Edited {file_path}")
