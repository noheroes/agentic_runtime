from __future__ import annotations

from typing import TYPE_CHECKING

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

# Cap de archivos emitidos; sin él un patrón amplio vuelca miles de rutas al contexto.
# Espejo de `globLimits.maxResults` (100) del canónico.
DEFAULT_GLOB_LIMIT = 100


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
        try:
            base = ctx.fs.resolve(input.get("path", "."), for_write=False)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        pattern = input["pattern"]
        try:
            matches = sorted(str(p) for p in base.glob(pattern))
            shown = matches[:DEFAULT_GLOB_LIMIT]
            output = "\n".join(shown)
            if len(matches) > DEFAULT_GLOB_LIMIT:
                output += "\n(Results are truncated. Consider using a more specific path or pattern.)"
            return ToolResult(tool_name=self.name, output=output)
        except Exception as exc:
            return ToolResult.error(self.name, str(exc))
