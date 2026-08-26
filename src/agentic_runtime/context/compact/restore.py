from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from typing import TYPE_CHECKING, Any

from ..estimation import rough_token_count_for_message, truncate_to_tokens
from ..file_state import ReadFileEntry, clear_read_file_state, read_file_state
from ..window import ContextBudget

if TYPE_CHECKING:
    from ..tool_use import ToolUseContext

READ_FILE_TOOL_NAME = "read_file"

POST_COMPACT_ATTACHMENT_KEY = "post_compact_attachment"
POST_COMPACT_RESTORE_EXCLUSION_KEY = "post_compact_restore_exclusion"

FILE_TRUNCATION_MARKER = (
    "\n\n[... file content truncated for compaction; "
    "read the file again if you need the full text]"
)

RestoreExclusion = Callable[[str], bool]


def _tool_call_arguments(call: Any) -> dict[str, Any] | None:
    if not isinstance(call, dict):
        return None
    function = call.get("function")
    if not isinstance(function, dict):
        return None
    if function.get("name") != READ_FILE_TOOL_NAME:
        return None
    arguments = function.get("arguments")
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except (TypeError, ValueError):
            return None
    return arguments if isinstance(arguments, dict) else None


def collect_read_tool_file_paths(messages: Sequence[Any]) -> set[str]:
    paths: set[str] = set()
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        for call in message.get("tool_calls") or []:
            arguments = _tool_call_arguments(call)
            if arguments is None:
                continue
            path = arguments.get("path")
            if isinstance(path, str) and path:
                paths.add(path)
    return paths


def resolve_restore_exclusions(app_state: Any) -> list[RestoreExclusion]:
    native = getattr(app_state, "native", None)
    if not isinstance(native, dict):
        return []
    declared = native.get(POST_COMPACT_RESTORE_EXCLUSION_KEY)
    if declared is None:
        return []
    if callable(declared):
        return [declared]
    if isinstance(declared, (list, tuple)):
        return [item for item in declared if callable(item)]
    return []


def _excluded(path: str, exclusions: Sequence[RestoreExclusion]) -> bool:
    for exclusion in exclusions:
        try:
            if exclusion(path):
                return True
        except Exception:  # noqa: BLE001
            continue
    return False


def select_files_to_restore(
    entries: Iterable[ReadFileEntry],
    *,
    max_files: int,
    exclusions: Sequence[RestoreExclusion] = (),
    already_visible: Iterable[str] = (),
) -> list[str]:
    if max_files <= 0:
        return []
    visible = set(already_visible)
    candidates = [
        entry
        for entry in entries
        if entry.path not in visible and not _excluded(entry.path, exclusions)
    ]
    candidates.sort(key=lambda entry: entry.timestamp, reverse=True)
    return [entry.path for entry in candidates[:max_files]]


def _resolved(ctx: ToolUseContext, path: str) -> str | None:
    try:
        return str(ctx.fs.resolve(path, for_write=False, cwd=ctx.cwd))
    except Exception:  # noqa: BLE001
        return None


def render_post_compact_file_attachment(path: str, content: str) -> dict[str, Any]:
    return {
        "role": "user",
        "content": (
            "<system-reminder>\n"
            f"{path} was in context before the conversation was compacted. "
            "This is its current content on disk:\n\n"
            f"{content}\n"
            "</system-reminder>"
        ),
        POST_COMPACT_ATTACHMENT_KEY: {"path": path},
    }


async def create_post_compact_file_attachments(
    ctx: ToolUseContext,
    budget: ContextBudget,
    *,
    messages_to_keep: Sequence[Any] = (),
) -> list[dict[str, Any]]:
    entries = read_file_state(ctx.app_state)
    clear_read_file_state(ctx.app_state)
    if not entries:
        return []

    visible: set[str] = set()
    for path in collect_read_tool_file_paths(messages_to_keep):
        resolved = _resolved(ctx, path)
        if resolved is not None:
            visible.add(resolved)

    selected = select_files_to_restore(
        entries,
        max_files=budget.post_compact_max_files_to_restore,
        exclusions=resolve_restore_exclusions(ctx.app_state),
        already_visible=visible,
    )
    if not selected:
        return []

    from ...tools.native.read_file import ReadFileTool

    tool = ReadFileTool()
    attachments: list[dict[str, Any]] = []
    used_tokens = 0
    for path in selected:
        result = await tool.execute({"path": path}, ctx)
        if getattr(result, "is_error", False) or not result.output:
            continue
        attachment = render_post_compact_file_attachment(
            path,
            truncate_to_tokens(
                result.output,
                budget.post_compact_max_tokens_per_file,
                FILE_TRUNCATION_MARKER,
            ),
        )
        tokens = rough_token_count_for_message(attachment)
        if used_tokens + tokens > budget.post_compact_token_budget:
            continue
        used_tokens += tokens
        attachments.append(attachment)
    return attachments


__all__ = [
    "FILE_TRUNCATION_MARKER",
    "POST_COMPACT_ATTACHMENT_KEY",
    "POST_COMPACT_RESTORE_EXCLUSION_KEY",
    "READ_FILE_TOOL_NAME",
    "RestoreExclusion",
    "collect_read_tool_file_paths",
    "create_post_compact_file_attachments",
    "render_post_compact_file_attachment",
    "resolve_restore_exclusions",
    "select_files_to_restore",
]
