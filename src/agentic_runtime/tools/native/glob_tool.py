from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from pathlib import Path

    from ...context.tool_use import ToolUseContext

# Cap de archivos emitidos; sin él un patrón amplio vuelca miles de rutas al contexto.
# Espejo de `globLimits.maxResults` (100) del canónico.
DEFAULT_GLOB_LIMIT = 100


class GlobTool:
    name = "glob"
    # `searchHint` del canónico, grafía literal. Fuera del contrato T1
    # (`contracts/tools.py:5`); lo lee ToolSearch para rankear (+4 vs +2 de la descripción).
    search_hint = "find files by name pattern or wildcard"
    # Homologada contra `GlobTool/prompt.ts:3-7` (`GAP-PROMPT-1`). Lo que la API recibe como
    # `description` es en A el retorno de `tool.prompt()` (`utils/api.ts:169-178`), no la
    # constante `DESCRIPTION`; el homólogo en B es este atributo. Se omite la línea de A que
    # deriva a la tool de subagente en búsquedas abiertas porque B no expone ese contrato aquí.
    description = """- Fast file pattern matching tool that works with any codebase size
- Supports glob patterns like "**/*.py" or "src/**/*.ts"
- Returns matching file paths sorted by modification time (oldest first)
- Only files are returned, never directories
- Use this tool when you need to find files by name patterns
- Results are capped; if truncated, narrow the pattern or the path rather than paging"""
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

    async def execute(self, input: dict[str, Any], ctx: "ToolUseContext") -> ToolResult:
        try:
            base = ctx.fs.resolve(input.get("path", "."), for_write=False)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        pattern = input["pattern"]
        try:
            # Orden por mtime ASCENDENTE y recorte DESPUÉS, como A: `--sort=modified`
            # (`utils/glob.ts:94-104`, comprobado además contra `rg` real: es ascendente,
            # «oldest first») y `slice(offset, offset + limit)` en `:127`. `GlobTool.ts:154-170`
            # no reordena, así que ese es el orden que ve el modelo.
            #
            # No es cosmético: **con un cap, el orden es SELECCIÓN**, no presentación — decide
            # cuáles 100 de 130 llegan al contexto (`FIND-GLOB-1`).
            #
            # Y sólo FICHEROS: A pasa `--files` (`:98`), B casaba también los directorios cuyo
            # nombre encajara en el patrón (`FIND-GLOB-2`, medido: un dir `carpeta.txt` salía
            # como resultado de `*.txt`).
            encontrados = [p for p in base.glob(pattern) if p.is_file()]
            # `stat` puede fallar en un enlace roto que el glob sí casa; ese archivo no tiene
            # mtime utilizable y se ordena como el más antiguo en vez de tumbar la llamada.
            def _mtime(p: Path) -> float:
                try:
                    return p.stat().st_mtime
                except OSError:
                    return 0.0

            # `S12`: cada match es una ruta HOST; se presenta en los términos del deployment.
            matches = [ctx.presentation.to_llm(p) for p in sorted(encontrados, key=_mtime)]
            shown = matches[:DEFAULT_GLOB_LIMIT]
            output = "\n".join(shown)
            if len(matches) > DEFAULT_GLOB_LIMIT:
                output += "\n(Results are truncated. Consider using a more specific path or pattern.)"
            return ToolResult(tool_name=self.name, output=output)
        except Exception as exc:
            return ToolResult.error(self.name, str(exc))
