from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext


class GrepTool:
    name = "grep"
    description = "Search for a pattern in files."
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string"},
            "path": {"type": "string"},
            "glob": {"type": "string"},
        },
        "required": ["pattern"],
    }
    category = ToolCategory.FILE
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 15.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        base = Path(input.get("path", "."))
        pattern = input["pattern"]
        file_glob = input.get("glob", "**/*")
        try:
            regex = re.compile(pattern)
            results: list[str] = []
            for file_path in sorted(base.glob(file_glob)):
                if not file_path.is_file():
                    continue
                try:
                    for i, line in enumerate(file_path.read_text(errors="replace").splitlines(), 1):
                        if regex.search(line):
                            results.append(f"{file_path}:{i}: {line}")
                except OSError:
                    pass
            return ToolResult(tool_name=self.name, output="\n".join(results))
        except re.error as exc:
            return ToolResult.error(self.name, f"invalid regex: {exc}")
        except Exception as exc:
            return ToolResult.error(self.name, str(exc))
