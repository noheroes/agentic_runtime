from __future__ import annotations

from typing import TYPE_CHECKING

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

# Cap de tamaño, mímica de `utils/file.ts:48` (`MAX_OUTPUT_SIZE = 0.25 MB`). Sobre el
# tamaño TOTAL del fichero, no sobre la porción seleccionada — la propia tabla de
# `FileReadTool/limits.ts` lo llama «known mismatch» y lo deja así a propósito.
_MAX_SIZE_BYTES = 256 * 1024


def _numerar(lineas: list[str], primera: int) -> str:
    """Numera como `addLineNumbers` (`utils/file.ts:290-318`): ancho 6 y flecha.

    Sin numeración el modelo no puede citar `fichero:línea` sin contar a mano, que es
    la mitad del valor de la tool. `primera` es 1-indexada, igual que el `startLine`
    que A le pasa (`FileReadTool.ts:1052`).
    """
    salida = []
    for desplazamiento, linea in enumerate(lineas):
        numero = str(desplazamiento + primera)
        prefijo = numero if len(numero) >= 6 else numero.rjust(6)
        salida.append(f"{prefijo}→{linea}")
    return "\n".join(salida)


class ReadFileTool:
    name = "read_file"
    description = "Read a file and return its contents."
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            # 1-indexado, como `FileReadTool.ts:497` (`{ offset = 1 }`). Va en el schema
            # porque es lo único que el modelo lee: un off-by-one silencioso en la tool
            # con la que cita código envenena cada referencia que produce.
            "offset": {
                "type": "integer",
                "description": "Line number to start reading from (1-indexed).",
            },
            "limit": {"type": "integer", "description": "Number of lines to read."},
        },
        "required": ["path"],
    }
    category = ToolCategory.FILE
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        try:
            path = ctx.fs.resolve(input["path"], for_write=False)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        try:
            limit = input.get("limit")
            # El cap SÓLO rige la lectura sin `limit` explícito: A pasa
            # `limit === undefined ? maxSizeBytes : undefined` (`FileReadTool.ts:1023`),
            # porque pedir un rango acotado ya es la salida que el error recomienda. Y
            # **lanza** en vez de truncar: probaron truncar (#21841) y lo revirtieron,
            # el error cuesta ~100 B y truncar costaba 25 K tokens (`limits.ts:1-14`).
            if limit is None:
                tamano = path.stat().st_size
                if tamano > _MAX_SIZE_BYTES:
                    return ToolResult.error(
                        self.name,
                        f"File content ({tamano} B) exceeds maximum allowed size "
                        f"({_MAX_SIZE_BYTES} B). Use offset and limit parameters to read "
                        f"specific portions of the file, or search for specific content "
                        f"instead of reading the whole file.",
                    )

            content = path.read_text(errors="replace")
            lines = content.splitlines()
            # `offset` 1-indexado, con la regla exacta de A: el 0 y el 1 nombran la misma
            # primera línea (`FileReadTool.ts:1020`, `offset === 0 ? 0 : offset - 1`), así
            # que un llamante que aún pase 0 no se desplaza.
            offset = input.get("offset", 1)
            inicio = 0 if offset == 0 else offset - 1
            selected = lines[inicio:] if limit is None else lines[inicio : inicio + limit]
            return ToolResult(tool_name=self.name, output=_numerar(selected, inicio + 1))
        except Exception as exc:
            return ToolResult.error(self.name, str(exc))
