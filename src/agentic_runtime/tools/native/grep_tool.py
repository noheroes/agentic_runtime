from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

DEFAULT_HEAD_LIMIT = 250
MAX_LINE_LEN = 500
BINARY_SNIFF_BYTES = 8192
_VCS_DIRS = {".git", ".svn", ".hg", ".bzr", ".jj", ".sl"}


def _expandir_llaves(patron: str) -> list[str]:
    abre = patron.find("{")
    if abre == -1:
        return [patron]
    cierra = patron.find("}", abre)
    if cierra == -1:
        return [patron]
    prefijo = patron[:abre]
    sufijo = patron[cierra + 1 :]
    salida: list[str] = []
    for alternativa in patron[abre + 1 : cierra].split(","):
        salida.extend(_expandir_llaves(prefijo + alternativa + sufijo))
    return salida


def _separar_globs(bruto: str) -> list[str]:
    patrones: list[str] = []
    for crudo in bruto.split():
        trozos = [crudo] if ("{" in crudo and "}" in crudo) else [p for p in crudo.split(",") if p]
        for trozo in trozos:
            patrones.extend(_expandir_llaves(trozo))
    return patrones


def _es_texto(ruta: Path) -> bool | None:
    try:
        with ruta.open("rb") as fh:
            return b"\0" not in fh.read(BINARY_SNIFF_BYTES)
    except OSError:
        return None


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
- Filter which files are searched with the `glob` parameter: one pattern, or several
  separated by commas or spaces (e.g. "*.py", "src/**/*.py,tests/**/*.py"); braces expand,
  so "*.{ts,tsx}" is the same as "*.ts,*.tsx"
- Binary and unreadable files are skipped, and how many were skipped is stated in the
  closing line; version-control directories are skipped too
- If the glob selects no files at all, the result says so explicitly — that is NOT the same
  as the pattern finding no matches, and the fix is a wider glob, not a different pattern
- Output is one line per match, formatted `path:line: text`; very long lines are elided
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
        pedida = input.get("path", ".")
        try:
            base = ctx.fs.resolve(pedida, for_write=False, cwd=ctx.cwd)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        if not base.exists():
            return ToolResult.error(
                self.name,
                f"Path does not exist: {pedida}. Note: your current working directory is "
                f"{ctx.presentation.to_llm(ctx.cwd)}.",
            )
        try:
            regex = re.compile(input["pattern"])
        except re.error as exc:
            return ToolResult.error(self.name, f"invalid regex: {exc}")
        file_glob = input.get("glob", "**/*")
        head_limit = input.get("head_limit", DEFAULT_HEAD_LIMIT)
        offset = input.get("offset", 0)
        try:
            mostrada_base = ctx.presentation.to_llm(base)
            if base.is_file():
                candidatos = [base]
                alcance_glob = ""
            else:
                candidatos = []
                vistos: set[Path] = set()
                for patron in _separar_globs(file_glob) or ["**/*"]:
                    try:
                        encontrados = sorted(base.glob(patron))
                    except ValueError as exc:
                        return ToolResult.error(
                            self.name, f'invalid glob "{patron}": {exc}'
                        )
                    for ruta in encontrados:
                        if ruta in vistos:
                            continue
                        vistos.add(ruta)
                        if any(part in _VCS_DIRS for part in ruta.parts):
                            continue
                        if not ruta.is_file():
                            continue
                        candidatos.append(ruta)
                candidatos.sort()
                alcance_glob = f' (glob "{file_glob}")'

            binarios = 0
            ilegibles = 0
            buscables: list[Path] = []
            for ruta in candidatos:
                texto = _es_texto(ruta)
                if texto is None:
                    ilegibles += 1
                elif texto:
                    buscables.append(ruta)
                else:
                    binarios += 1

            saltados = []
            if binarios:
                saltados.append(f"{binarios} binary")
            if ilegibles:
                saltados.append(f"{ilegibles} unreadable")
            detalle_saltados = " and ".join(saltados)
            nota_saltados = f"; {detalle_saltados} file(s) skipped" if saltados else ""

            if not candidatos:
                return ToolResult(
                    tool_name=self.name,
                    output=(
                        f'[The glob "{file_glob}" selected no files under {mostrada_base}, so '
                        f"the pattern was never tested against anything. This is NOT the same "
                        f"as finding no matches: widen the glob, or omit it to search every "
                        f"file under the path.]"
                    ),
                )
            if not buscables:
                return ToolResult(
                    tool_name=self.name,
                    output=(
                        f"[{len(candidatos)} file(s) selected under {mostrada_base}"
                        f"{alcance_glob}, but every one of them was skipped "
                        f"({detalle_saltados}), so the pattern was never tested against "
                        f"anything. This is NOT the same as finding no matches.]"
                    ),
                )

            results: list[str] = []
            matched_files = 0
            for file_path in buscables:
                shown_path = ctx.presentation.to_llm(file_path)
                try:
                    hits_before = len(results)
                    for i, line in enumerate(
                        file_path.read_text(errors="replace").splitlines(), 1
                    ):
                        if regex.search(line):
                            if len(line) > MAX_LINE_LEN:
                                line = line[:MAX_LINE_LEN] + "…"
                            results.append(f"{shown_path}:{i}: {line}")
                    if len(results) > hits_before:
                        matched_files += 1
                except OSError:
                    ilegibles += 1

            total = len(results)
            scope = (
                f"{len(buscables)} file(s) searched under {mostrada_base}"
                f"{alcance_glob}{nota_saltados}"
            )
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
        except Exception as exc:  # noqa: BLE001
            return ToolResult.error(self.name, str(exc))
