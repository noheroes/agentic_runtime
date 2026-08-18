from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext


class WriteFileTool:
    name = "write_file"
    search_hint = "create or overwrite files"
    description = """Writes a file to the local filesystem.

Usage:
- This tool will overwrite the existing file if there is one at the provided path.
- Prefer the Edit tool for modifying existing files — it only sends the diff. Only use this
  tool to create new files or for complete rewrites.
- Parent directories are created as needed.
- NEVER create documentation files (*.md) or README files unless explicitly requested.
- Only use emojis if the user explicitly requests it."""
    input_schema: dict[str, Any] = {  # noqa: RUF012
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

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        try:
            path = ctx.fs.resolve(input["path"], for_write=True, cwd=ctx.cwd)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        try:
            existia = path.exists()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(input["content"])
            mostrado = ctx.presentation.to_llm(path)
            cierre = "(this call would have errored if the write had failed; the file exists with exactly this content — no need to check it back)"
            if existia:
                salida = f"The file {mostrado} has been updated successfully. {cierre}"
            else:
                salida = f"File created successfully at: {mostrado} {cierre}"
            return ToolResult(tool_name=self.name, output=salida)
        except Exception as exc:  # noqa: BLE001
            return ToolResult.error(self.name, str(exc))
