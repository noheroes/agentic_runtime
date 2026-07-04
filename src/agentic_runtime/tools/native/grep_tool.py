from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

# Cap por defecto de líneas emitidas cuando `head_limit` no se especifica. Sin cap, un grep
# sobre un árbol grande vuelca MBs al contexto (session.json crece hasta romper al proveedor).
# Espejo de `GrepTool.DEFAULT_HEAD_LIMIT` del canónico. `head_limit=0` = ilimitado (escape hatch).
DEFAULT_HEAD_LIMIT = 250
# Longitud máxima por línea; evita que base64/minificados llenen la salida. Espejo de `--max-columns 500`.
MAX_LINE_LEN = 500
# Directorios de control de versiones excluidos (ruido de metadata). Espejo de `VCS_DIRECTORIES_TO_EXCLUDE`.
_VCS_DIRS = {".git", ".svn", ".hg", ".bzr", ".jj", ".sl"}


class GrepTool:
    name = "grep"
    description = "Search for a pattern in files."
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string"},
            "path": {"type": "string"},
            "glob": {"type": "string"},
            "head_limit": {
                "type": "integer",
                "description": (
                    "Limit output to first N matching lines (defaults to 250). Pass 0 for "
                    "unlimited (use sparingly — large result sets waste context)."
                ),
            },
            "offset": {
                "type": "integer",
                "description": "Skip first N matching lines before applying head_limit (defaults to 0).",
            },
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
        head_limit = input.get("head_limit", DEFAULT_HEAD_LIMIT)
        offset = input.get("offset", 0)
        try:
            regex = re.compile(pattern)
            results: list[str] = []
            for file_path in sorted(base.glob(file_glob)):
                if any(part in _VCS_DIRS for part in file_path.parts):
                    continue
                if not file_path.is_file():
                    continue
                try:
                    for i, line in enumerate(file_path.read_text(errors="replace").splitlines(), 1):
                        if regex.search(line):
                            if len(line) > MAX_LINE_LEN:
                                line = line[:MAX_LINE_LEN] + "…"
                            results.append(f"{file_path}:{i}: {line}")
                except OSError:
                    pass
            total = len(results)
            selected = results[offset:] if head_limit == 0 else results[offset : offset + head_limit]
            output = "\n".join(selected)
            if head_limit != 0 and total - offset > head_limit:
                output += (
                    f"\n\n[Showing {len(selected)} of {total} matches. Use a more specific "
                    f"pattern/path, offset to paginate, or head_limit=0 for all.]"
                )
            return ToolResult(tool_name=self.name, output=output)
        except re.error as exc:
            return ToolResult.error(self.name, f"invalid regex: {exc}")
        except Exception as exc:
            return ToolResult.error(self.name, str(exc))
