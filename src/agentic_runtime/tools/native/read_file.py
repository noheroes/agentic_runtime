from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...context.file_state import record_read_file
from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

_MAX_SIZE_BYTES = 256 * 1024


def _numerar(lineas: list[str], primera: int) -> str:
    salida = []
    for desplazamiento, linea in enumerate(lineas):
        numero = str(desplazamiento + primera)
        prefijo = numero if len(numero) >= 6 else numero.rjust(6)
        salida.append(f"{prefijo}→{linea}")
    return "\n".join(salida)


class ReadFileTool:
    name = "read_file"
    search_hint = "read files, images, PDFs, notebooks"
    description = """NEVER call this tool to confirm or extend lines a content search already
returned: search results quote the file verbatim and list every match. When you want more than
the search showed — how something is used, where else it appears, what surrounds it — search
again with a wider pattern: it is cheaper, and it answers across files where one file cannot.
Read a file when the task needs the file itself: its structure or flow as a whole, or a region
no pattern can name.

Reads a file from the local filesystem. You can access any file inside the
workspace directly by using this tool. If the user provides a path to a file, assume that path
is valid. It is okay to read a file that does not exist; an error will be returned.

Usage:
- The `path` parameter should be an absolute path
- Results are returned with line numbers, starting at 1, so you can cite `file:line`
- You can optionally specify `offset` (1-indexed) and `limit`; when you already know which
  part of the file you need, read only that part — this matters for large files
- Reading a whole file without `limit` fails if the file exceeds the size cap; the error
  tells you to use `offset`/`limit` or to search for the content instead
- This tool reads files, not directories. Use the glob tool to list files"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "path": {"type": "string"},
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

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        try:
            path = ctx.fs.resolve(input["path"], for_write=False, cwd=ctx.cwd)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        try:
            limit = input.get("limit")
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
            offset = input.get("offset", 1)
            inicio = 0 if offset == 0 else offset - 1
            selected = lines[inicio:] if limit is None else lines[inicio : inicio + limit]
            record_read_file(ctx.app_state, str(path))
            return ToolResult(tool_name=self.name, output=_numerar(selected, inicio + 1))
        except Exception as exc:  # noqa: BLE001
            return ToolResult.error(self.name, str(exc))
