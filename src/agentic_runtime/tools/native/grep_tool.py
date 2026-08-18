from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

DEFAULT_HEAD_LIMIT = 250
MAX_LINE_LEN = 500
_VCS_DIRS = {".git", ".svn", ".hg", ".bzr", ".jj", ".sl"}


class GrepTool:
    name = "grep"
    search_hint = "search file contents with a Python regex"
    description = """A powerful search tool for finding content inside files.

Usage:
- ALWAYS use this tool for content search. NEVER invoke `grep` or `rg` as a shell command —
  this tool is optimized for correct permissions and workspace confinement.
- Supports Python regular expression syntax (e.g. "log.*Error", r"def\\s+\\w+")
- Patterns are case-sensitive: prefix with `(?i)` to match regardless of case
  (e.g. "(?i)level" finds LEVEL_NAMES, Level and level alike)
- Filter which files are searched with the `glob` parameter (e.g. "*.py", "**/*.ts")
- Results include every readable file under `path`, generated and binary ones among them
  (`__pycache__`, build output): narrow with `glob` when the target is source
- Output is one line per match, formatted `path:line: text`; version-control directories
  are skipped and very long lines are elided
- Patterns match within a single line only
- Results are capped at 250 matching lines by default: use a more specific pattern or path,
  `offset` to paginate, or `head_limit=0` for everything (sparingly — it costs context)"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
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

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        try:
            base = ctx.fs.resolve(input.get("path", "."), for_write=False, cwd=ctx.cwd)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        pattern = input["pattern"]
        file_glob = input.get("glob", "**/*")
        head_limit = input.get("head_limit", DEFAULT_HEAD_LIMIT)
        offset = input.get("offset", 0)
        try:
            regex = re.compile(pattern)
            results: list[str] = []
            searched = 0
            matched_files = 0
            for file_path in sorted(base.glob(file_glob)):
                if any(part in _VCS_DIRS for part in file_path.parts):
                    continue
                if not file_path.is_file():
                    continue
                shown_path = ctx.presentation.to_llm(file_path)
                try:
                    hits_before = len(results)
                    for i, line in enumerate(file_path.read_text(errors="replace").splitlines(), 1):
                        if regex.search(line):
                            if len(line) > MAX_LINE_LEN:
                                line = line[:MAX_LINE_LEN] + "…"
                            results.append(f"{shown_path}:{i}: {line}")
                    searched += 1
                    if len(results) > hits_before:
                        matched_files += 1
                except OSError:
                    pass
            total = len(results)
            scope = f"{searched} file(s) searched under {ctx.presentation.to_llm(base)} (glob \"{file_glob}\")"
            selected = results[offset:] if head_limit == 0 else results[offset : offset + head_limit]
            output = "\n".join(selected)
            if total == 0:
                output = f"[No matches for this pattern: {scope}.]"
            elif head_limit != 0 and total - offset > head_limit:
                output += (
                    f"\n\n[Showing {len(selected)} of {total} matches in {matched_files} file(s); "
                    f"{scope}. Each line above is quoted verbatim from the file. Use a more specific "
                    f"pattern/path, offset to paginate, or head_limit=0 for all.]"
                )
            else:
                output += (
                    f"\n\n[{total} match(es) in {matched_files} file(s); {scope}. Every match is "
                    f"listed above, quoted verbatim from the file — open a file only when you need "
                    f"context beyond the matched lines.]"
                )
            return ToolResult(tool_name=self.name, output=output)
        except re.error as exc:
            return ToolResult.error(self.name, f"invalid regex: {exc}")
        except Exception as exc:  # noqa: BLE001
            return ToolResult.error(self.name, str(exc))
