from __future__ import annotations

import fnmatch
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


def _por_nombre(patron: str) -> str:
    return patron if "/" in patron else f"**/{patron}"


def _reglas_ignore(base: Path) -> list[tuple[str, bool, bool]]:
    directorios: list[Path] = []
    actual = base if base.is_dir() else base.parent
    while True:
        directorios.append(actual)
        if (actual / ".git").exists() or actual.parent == actual:
            break
        actual = actual.parent
    reglas: list[tuple[str, bool, bool]] = []
    for directorio in reversed(directorios):
        fichero = directorio / ".gitignore"
        if not fichero.is_file():
            continue
        try:
            lineas = fichero.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for cruda in lineas:
            linea = cruda.strip()
            if not linea or linea.startswith("#"):
                continue
            negada = linea.startswith("!")
            if negada:
                linea = linea[1:]
            solo_dir = linea.endswith("/")
            linea = linea.strip("/")
            if linea:
                reglas.append((linea, negada, solo_dir))
    return reglas


def _ignorado(relativa: str, reglas: list[tuple[str, bool, bool]]) -> bool:
    partes = relativa.split("/")
    prefijos = ["/".join(partes[: i + 1]) for i in range(len(partes))]
    estado = False
    for patron, negada, solo_dir in reglas:
        objetivos = prefijos if "/" in patron else partes
        if solo_dir:
            objetivos = objetivos[:-1]
        if any(fnmatch.fnmatch(objetivo, patron) for objetivo in objetivos):
            estado = not negada
    return estado


def _es_texto(ruta: Path) -> bool | None:
    try:
        with ruta.open("rb") as fh:
            return b"\0" not in fh.read(BINARY_SNIFF_BYTES)
    except OSError:
        return None


def _recorta(linea: str) -> str:
    return linea[:MAX_LINE_LEN] + "…" if len(linea) > MAX_LINE_LEN else linea


class GrepTool:
    name = "grep"
    search_hint = "search file contents with a Python regex"
    description = """A powerful search tool for finding content inside files.

Usage:
- ALWAYS use this tool for content search. NEVER invoke `grep` or `rg` as a shell command —
  this tool is optimized for correct permissions and workspace confinement.
- Supports Python regular expression syntax (e.g. "log.*Error", r"def\\s+\\w+")
- Patterns are case-sensitive: pass `-i: true`, or prefix the pattern with `(?i)`, to match
  regardless of case (e.g. "(?i)level" finds LEVEL_NAMES, Level and level alike)
- Filter which files are searched with the `glob` parameter: one pattern, or several
  separated by commas or spaces (e.g. "*.py", "src/**/*.py,tests/**/*.py"); braces expand,
  so "*.{ts,tsx}" is the same as "*.ts,*.tsx"
- A glob with no `/` matches the file name at any depth, so "*.py" reaches src/pkg/mod.py;
  prefix a pattern with `!` to exclude what it matches (e.g. "*.py,!test_*.py")
- Files ignored by .gitignore are not searched, and neither are version-control directories;
  binary and unreadable files are skipped, and how many were skipped is stated in the
  closing line
- If the glob selects no files at all, the result says so explicitly — that is NOT the same
  as the pattern finding no matches, and the fix is a wider glob, not a different pattern
- `-C` (or `-A`/`-B` for one side only) returns the lines around each match in the same
  result, with context lines marked `path-line- text` and matches `path:line: text`
- `output_mode` selects the shape of the result: "content" (the default) is one line per
  match formatted `path:line: text`, "files_with_matches" lists only the paths, and "count"
  gives one `path:count` per file
- Patterns match within a single line only
- Results are capped at 250 matching lines by default: use a more specific pattern or path,
  `offset` to paginate, or `head_limit=0` for everything (sparingly — it costs context)"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "pattern": {"type": "string"},
            "path": {"type": "string"},
            "glob": {"type": "string"},
            "output_mode": {
                "type": "string",
                "enum": ["content", "files_with_matches", "count"],
                "description": (
                    'Shape of the result: "content" (default) one line per match, '
                    '"files_with_matches" only the paths, "count" one count per file. '
                    "-A/-B/-C apply to content only."
                ),
            },
            "-i": {
                "type": "boolean",
                "description": "Match regardless of case (defaults to false).",
            },
            "-A": {
                "type": "integer",
                "description": "Number of lines to show after each match (defaults to 0).",
            },
            "-B": {
                "type": "integer",
                "description": "Number of lines to show before each match (defaults to 0).",
            },
            "-C": {
                "type": "integer",
                "description": "Number of lines to show before and after each match.",
            },
            "context": {
                "type": "integer",
                "description": "Alias for -C.",
            },
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
        banderas = re.IGNORECASE if input.get("-i") else 0
        try:
            regex = re.compile(input["pattern"], banderas)
        except re.error as exc:
            return ToolResult.error(self.name, f"invalid regex: {exc}")
        file_glob = input.get("glob", "**/*")
        head_limit = input.get("head_limit", DEFAULT_HEAD_LIMIT)
        offset = input.get("offset", 0)
        modo = input.get("output_mode", "content")
        if modo not in ("content", "files_with_matches", "count"):
            return ToolResult.error(
                self.name,
                f'invalid output_mode "{modo}": use content, files_with_matches or count',
            )
        alrededor = input.get("context", input.get("-C"))
        if alrededor is not None:
            antes = despues = max(int(alrededor), 0)
        else:
            antes = max(int(input.get("-B") or 0), 0)
            despues = max(int(input.get("-A") or 0), 0)
        try:
            mostrada_base = ctx.presentation.to_llm(base)
            if base.is_file():
                candidatos = [base]
                alcance_glob = ""
            else:
                patrones = _separar_globs(file_glob) or ["**/*"]
                incluidos = [_por_nombre(p) for p in patrones if not p.startswith("!")]
                excluidos = [_por_nombre(p[1:]) for p in patrones if p.startswith("!") and len(p) > 1]
                if not incluidos:
                    incluidos = ["**/*"]
                descartados: set[Path] = set()
                for patron in excluidos:
                    try:
                        descartados |= set(base.glob(patron))
                    except ValueError as exc:
                        return ToolResult.error(self.name, f'invalid glob "{patron}": {exc}')
                reglas = _reglas_ignore(base)
                candidatos = []
                vistos: set[Path] = set()
                for patron in incluidos:
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
                        if ruta in descartados:
                            continue
                        if any(part in _VCS_DIRS for part in ruta.parts):
                            continue
                        if not ruta.is_file():
                            continue
                        if reglas and _ignorado(ruta.relative_to(base).as_posix(), reglas):
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

            coincidencias: list[tuple[Path, int]] = []
            lineas_por_fichero: dict[Path, list[str]] = {}
            for file_path in buscables:
                try:
                    lineas = file_path.read_text(errors="replace").splitlines()
                except OSError:
                    ilegibles += 1
                    continue
                indices = [i for i, linea in enumerate(lineas) if regex.search(linea)]
                if indices:
                    lineas_por_fichero[file_path] = lineas
                    coincidencias.extend((file_path, i) for i in indices)

            total = len(coincidencias)
            ficheros_con_coincidencia = len(lineas_por_fichero)
            scope = (
                f"{len(buscables)} file(s) searched under {mostrada_base}"
                f"{alcance_glob}{nota_saltados}"
            )

            if total == 0:
                return ToolResult(
                    tool_name=self.name,
                    output=f"[No matches for this pattern: {scope}.]",
                )

            if modo == "files_with_matches":
                rutas = [ctx.presentation.to_llm(p) for p in lineas_por_fichero]
                elegidas = rutas[offset:] if head_limit == 0 else rutas[offset : offset + head_limit]
                cuerpo = "\n".join(elegidas)
                return ToolResult(
                    tool_name=self.name,
                    output=(
                        f"{cuerpo}\n\n[{len(elegidas)} file(s) with matches; {scope}. "
                        f"Re-run with output_mode content to see the matching lines.]"
                    ),
                )

            if modo == "count":
                cuentas = []
                for file_path in lineas_por_fichero:
                    n = sum(1 for p, _ in coincidencias if p == file_path)
                    cuentas.append(f"{ctx.presentation.to_llm(file_path)}:{n}")
                elegidas = cuentas[offset:] if head_limit == 0 else cuentas[offset : offset + head_limit]
                cuerpo = "\n".join(elegidas)
                return ToolResult(
                    tool_name=self.name,
                    output=(
                        f"{cuerpo}\n\n[{total} match(es) across "
                        f"{ficheros_con_coincidencia} file(s); {scope}.]"
                    ),
                )

            seleccion = (
                coincidencias[offset:]
                if head_limit == 0
                else coincidencias[offset : offset + head_limit]
            )
            por_fichero: dict[Path, list[int]] = {}
            for file_path, indice in seleccion:
                por_fichero.setdefault(file_path, []).append(indice)

            results: list[str] = []
            for file_path, indices in por_fichero.items():
                shown_path = ctx.presentation.to_llm(file_path)
                lineas = lineas_por_fichero[file_path]
                marcadas = set(indices)
                bloques: list[tuple[int, int]] = []
                for indice in indices:
                    inicio = max(indice - antes, 0)
                    fin = min(indice + despues, len(lineas) - 1)
                    if bloques and inicio <= bloques[-1][1] + 1:
                        bloques[-1] = (bloques[-1][0], max(bloques[-1][1], fin))
                    else:
                        bloques.append((inicio, fin))
                for numero, (inicio, fin) in enumerate(bloques):
                    if numero and (antes or despues):
                        results.append("--")
                    for i in range(inicio, fin + 1):
                        separador = ":" if i in marcadas else "-"
                        results.append(
                            f"{shown_path}{separador}{i + 1}{separador} {_recorta(lineas[i])}"
                        )

            output = "\n".join(results)
            contexto_o_fichero = (
                "the lines around any of them come back in this same result with -C, -A or -B"
                if not (antes or despues)
                else "the surrounding lines you asked for are included above"
            )
            if head_limit != 0 and total - offset > head_limit:
                output += (
                    f"\n\n[Showing {len(seleccion)} of {total} matches in "
                    f"{ficheros_con_coincidencia} file(s); {scope}. Each line above is quoted "
                    f"verbatim from the file. Use a more specific pattern/path, offset to "
                    f"paginate, or head_limit=0 for all.]"
                )
            else:
                output += (
                    f"\n\n[{total} match(es) in {ficheros_con_coincidencia} file(s); {scope}. "
                    f"Every match is listed above, quoted verbatim from the file — "
                    f"{contexto_o_fichero}.]"
                )
            return ToolResult(tool_name=self.name, output=output)
        except Exception as exc:  # noqa: BLE001
            return ToolResult.error(self.name, str(exc))
