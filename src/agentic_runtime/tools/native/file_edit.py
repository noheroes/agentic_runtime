from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult
from .edit_text import (
    FILE_NOT_FOUND_CWD_NOTE,
    MAX_EDIT_FILE_SIZE,
    EditNotApplied,
    apply_edit,
    find_actual_string,
    find_similar_file,
    format_file_size,
    is_unc_path,
    preserve_quote_style,
    read_file_with_metadata,
    suggest_path_under_cwd,
    write_text_content,
)

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

FILE_EDIT_TOOL_NAME = "Edit"

EDIT_CONFIG_VALIDATORS_KEY = "edit_config_validators"


class FileEditTool:
    name = FILE_EDIT_TOOL_NAME
    search_hint = "modify file contents in place"
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

        if is_unc_path(file_path):
            return ToolResult.error(
                self.name, "UNC paths cannot be edited from this workspace."
            )

        if old_string == new_string:
            return ToolResult.error(
                self.name,
                "No changes to make: old_string and new_string are exactly the same.",
            )

        if not Path(file_path).is_absolute():
            return ToolResult.error(self.name, "file_path must be absolute.")
        try:
            path = ctx.fs.resolve(file_path, for_write=True)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))

        try:
            size = path.stat().st_size
        except OSError:
            size = None
        if size is not None and size > MAX_EDIT_FILE_SIZE:
            return ToolResult.error(
                self.name,
                f"File is too large to edit ({format_file_size(size)}). "
                f"Maximum editable file size is {format_file_size(MAX_EDIT_FILE_SIZE)}.",
            )

        try:
            content, encoding, endings = read_file_with_metadata(path)
        except FileNotFoundError:
            content = None
            encoding, endings = "utf-8", "LF"
        except Exception as e:  # noqa: BLE001
            return ToolResult.error(self.name, f"Cannot read file: {e}")

        if content is None:
            if old_string != "":
                return ToolResult.error(self.name, self._not_found_message(file_path, path, ctx))
            content = ""
        elif old_string == "":
            if content.strip() != "":
                return ToolResult.error(
                    self.name, "Cannot create new file - file already exists."
                )

        if old_string != "":
            actual_old_string = find_actual_string(content, old_string)
            if actual_old_string is None:
                return ToolResult.error(
                    self.name,
                    f"String to replace not found in file.\nString: {old_string}",
                )

            matches = content.count(actual_old_string)
            if matches > 1:
                return ToolResult.error(
                    self.name,
                    f"Found {matches} matches of the string to replace. Provide more context "
                    f"to uniquely identify the instance.\nString: {old_string}",
                )
            new_string = preserve_quote_style(old_string, actual_old_string, new_string)
        else:
            actual_old_string = ""

        try:
            updated = apply_edit(content, actual_old_string, new_string)
        except EditNotApplied as exc:
            return ToolResult.error(self.name, str(exc))

        rejection = self._config_validation_error(ctx, path, content, updated)
        if rejection is not None:
            return ToolResult.error(self.name, rejection)

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            write_text_content(path, updated, encoding, endings)
        except Exception as e:  # noqa: BLE001
            return ToolResult.error(self.name, f"Cannot write file: {e}")

        return ToolResult(
            tool_name=self.name,
            output=f"The file {file_path} has been updated successfully.",
        )

    def _not_found_message(self, file_path: str, path: Path, ctx: ToolUseContext) -> str:
        cwd = getattr(ctx, "cwd", "") or ""
        message = f"File does not exist. {FILE_NOT_FOUND_CWD_NOTE} {cwd}."
        suggestion = suggest_path_under_cwd(str(path), cwd) if cwd else None
        if suggestion is None:
            suggestion = find_similar_file(path)
        if suggestion:
            message += f" Did you mean {suggestion}?"
        return message

    def _config_validation_error(
        self, ctx: ToolUseContext, path: Path, original: str, updated: str
    ) -> str | None:
        app_state = getattr(ctx, "app_state", None)
        native = getattr(app_state, "native", None)
        if not isinstance(native, dict):
            return None
        validators = native.get(EDIT_CONFIG_VALIDATORS_KEY) or ()

        target = str(path)
        for matches, validate in validators:
            if not matches(target):
                continue
            if validate(original) is not None:
                continue
            reason = validate(updated)
            if reason is not None:
                return f"Configuration file validation failed after edit: {reason}"
        return None
