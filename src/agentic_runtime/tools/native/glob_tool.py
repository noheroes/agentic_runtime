from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from pathlib import Path

    from ...context.tool_use import ToolUseContext

DEFAULT_GLOB_LIMIT = 100


class GlobTool:
    name = "glob"
    search_hint = "find files by name pattern or wildcard"
    description = """- Fast file pattern matching tool that works with any codebase size
- Supports glob patterns like "**/*.py" or "src/**/*.ts"
- Returns matching file paths sorted by modification time (oldest first)
- Only files are returned, never directories
- Use this tool when you need to find files by name patterns
- This tool matches on file names and paths only; it cannot see inside files. When the
  question is about what the code contains, search contents directly — listing the tree
  first adds nothing to that answer
- Results are capped; if truncated, narrow the pattern or the path rather than paging"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
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

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        try:
            base = ctx.fs.resolve(input.get("path", "."), for_write=False, cwd=ctx.cwd)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        pattern = input["pattern"]
        try:
            encontrados = [p for p in base.glob(pattern) if p.is_file()]

            def _mtime(p: Path) -> float:
                try:
                    return p.stat().st_mtime
                except OSError:
                    return 0.0

            matches = [ctx.presentation.to_llm(p) for p in sorted(encontrados, key=_mtime)]
            shown = matches[:DEFAULT_GLOB_LIMIT]
            output = "\n".join(shown)
            if len(matches) > DEFAULT_GLOB_LIMIT:
                output += "\n(Results are truncated. Consider using a more specific path or pattern.)"
            return ToolResult(tool_name=self.name, output=output)
        except Exception as exc:  # noqa: BLE001
            return ToolResult.error(self.name, str(exc))
