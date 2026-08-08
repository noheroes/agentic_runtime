from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

FILE_EDIT_TOOL_NAME = "Edit"


class FileEditTool:
    name = FILE_EDIT_TOOL_NAME
    # `searchHint` del canónico, grafía literal. Fuera del contrato T1
    # (`contracts/tools.py:5`); lo lee ToolSearch para rankear (+4 vs +2 de la descripción).
    search_hint = "modify file contents in place"
    # Homologada contra `getDefaultEditDescription()` (`FileEditTool/prompt.ts:20-27`).
    # La línea del PREFIJO DE NUMERACIÓN (`:23`) es la de más valor operativo y se conserva
    # adaptada al formato real de `read_file` (ancho 6 + flecha, `read_file.py:17-29`): sin
    # ella el modelo mete el prefijo dentro de `old_string` y el edit falla siempre.
    # OMITIDAS: la lectura previa obligatoria (`:22`, B no la comprueba) y `replace_all`
    # (`:26-27`, B no tiene ese parámetro — su unicidad es dura y falla con >1 coincidencia).
    description = """Performs exact string replacements in files.

Usage:
- When editing text taken from read_file output, preserve the exact indentation as it appears
  AFTER the line-number prefix. The prefix format is right-aligned number + arrow; everything
  after the arrow is the actual file content to match. NEVER include any part of the prefix
  in old_string or new_string.
- The edit FAILS if `old_string` is not found, and also if it matches more than once. Provide
  more surrounding context to make it unique — usually 2-4 adjacent lines is enough.
- ALWAYS prefer editing existing files over writing new ones.
- Only use emojis if the user explicitly requests it."""
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to edit.",
            },
            "old_string": {
                "type": "string",
                "description": "The exact string to replace. Must match exactly, including whitespace.",
            },
            "new_string": {
                "type": "string",
                "description": "The string to replace old_string with.",
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    }
    category = ToolCategory.FILE
    requires_permission = True
    safe_for_background = True
    timeout_seconds = 10.0

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        file_path = input.get("file_path", "")
        old_string = input.get("old_string", "")
        new_string = input.get("new_string", "")

        if not Path(file_path).is_absolute():
            return ToolResult.error(self.name, "file_path must be absolute.")
        try:
            path = ctx.fs.resolve(file_path, for_write=True)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        if not path.exists():
            return ToolResult.error(self.name, f"File not found: {file_path}")

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:  # noqa: BLE001 — idem dispatcher: el fallo vuelve al modelo como texto
            return ToolResult.error(self.name, f"Cannot read file: {e}")

        count = content.count(old_string)
        if count == 0:
            return ToolResult.error(
                self.name,
                f"old_string not found in {file_path}. Verify the exact text including whitespace.",
            )
        if count > 1:
            return ToolResult.error(
                self.name,
                f"old_string matches {count} locations in {file_path}. Provide more context to make it unique.",
            )

        new_content = content.replace(old_string, new_string, 1)
        try:
            path.write_text(new_content, encoding="utf-8")
        except Exception as e:  # noqa: BLE001 — idem dispatcher: el fallo vuelve al modelo como texto
            return ToolResult.error(self.name, f"Cannot write file: {e}")

        return ToolResult(tool_name=self.name, output=f"Edited {file_path}")
