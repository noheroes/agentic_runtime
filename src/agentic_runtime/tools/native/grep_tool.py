from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from ..fs_env import PathOutsideWorkspace
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
    # `searchHint` del canónico, grafía literal. Fuera del contrato T1
    # (`contracts/tools.py:5`); lo lee ToolSearch para rankear (+4 vs +2 de la descripción).
    search_hint = "search file contents with regex (ripgrep)"
    # Homologada contra `GrepTool/prompt.ts:7-17` (`GAP-PROMPT-1`). La primera línea de Usage
    # —«ALWAYS use this tool; NEVER invoke grep/rg as a shell command»— es la pieza que el
    # canónico usa para DIRIGIR la elección de tool, y es justo la que B no tenía.
    # DIVERGENCIA DECLARADA: A corre sobre ripgrep; B sobre `re` de Python. La descripción dice
    # el dialecto REAL en vez de copiar el de A: prometer sintaxis ripgrep sobre un motor `re`
    # sería peor que no decir nada. Por lo mismo se omiten `type`, `multiline` y los modos de
    # salida, que B no implementa.
    description = """A powerful search tool for finding content inside files.

Usage:
- ALWAYS use this tool for content search. NEVER invoke `grep` or `rg` as a shell command —
  this tool is optimized for correct permissions and workspace confinement.
- Supports Python regular expression syntax (e.g. "log.*Error", r"def\\s+\\w+")
- Filter which files are searched with the `glob` parameter (e.g. "*.py", "**/*.ts")
- Output is one line per match, formatted `path:line: text`; version-control directories
  are skipped and very long lines are elided
- Patterns match within a single line only
- Results are capped at 250 matching lines by default: use a more specific pattern or path,
  `offset` to paginate, or `head_limit=0` for everything (sparingly — it costs context)"""
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

    async def execute(self, input: dict[str, Any], ctx: "ToolUseContext") -> ToolResult:
        try:
            base = ctx.fs.resolve(input.get("path", "."), for_write=False)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
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
                # `S12`: ruta HOST → términos del deployment, una vez por archivo (no por línea).
                shown_path = ctx.presentation.to_llm(file_path)
                try:
                    for i, line in enumerate(file_path.read_text(errors="replace").splitlines(), 1):
                        if regex.search(line):
                            if len(line) > MAX_LINE_LEN:
                                line = line[:MAX_LINE_LEN] + "…"
                            results.append(f"{shown_path}:{i}: {line}")
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
