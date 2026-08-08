from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext


class WriteFileTool:
    name = "write_file"
    # `searchHint` del canónico, grafía literal. Fuera del contrato T1
    # (`contracts/tools.py:5`); lo lee ToolSearch para rankear (+4 vs +2 de la descripción).
    search_hint = "create or overwrite files"
    # Homologada contra `getWriteToolDescription()` (`FileWriteTool/prompt.ts:10-18`).
    # OMITIDA la línea de lectura previa obligatoria (`:7`): A la puede prometer porque su tool
    # FALLA si no leíste antes; B no lo comprueba. Anunciar una comprobación inexistente sería
    # peor que callarla — queda como carencia declarada, no como texto falso.
    description = """Writes a file to the local filesystem.

Usage:
- This tool will overwrite the existing file if there is one at the provided path.
- Prefer the Edit tool for modifying existing files — it only sends the diff. Only use this
  tool to create new files or for complete rewrites.
- Parent directories are created as needed.
- NEVER create documentation files (*.md) or README files unless explicitly requested.
- Only use emojis if the user explicitly requests it."""
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    }
    category = ToolCategory.FILE
    requires_permission = True
    safe_for_background = True
    timeout_seconds = 10.0

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        try:
            path = ctx.fs.resolve(input["path"], for_write=True)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(input["content"])
            # `S12`: la ruta resuelta es HOST. El modelo debe verla en los términos del
            # deployment (`/workspace/...` bajo fake-path), no la real. Bajo identidad es no-op.
            return ToolResult(tool_name=self.name, output=ctx.presentation.to_llm(path))
        except Exception as exc:  # noqa: BLE001 — idem dispatcher: el fallo vuelve al modelo como texto
            return ToolResult.error(self.name, str(exc))
