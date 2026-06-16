from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

TODO_WRITE_TOOL_NAME = "TodoWrite"
_TODOS_KEY = "todos"

_TODO_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "content": {"type": "string"},
            "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
            "priority": {"type": "string", "enum": ["high", "medium", "low"]},
        },
        "required": ["id", "content", "status", "priority"],
    },
}


class TodoWriteTool:
    name = TODO_WRITE_TOOL_NAME
    description = (
        "Create and manage a structured task checklist for the current session. "
        "Use to track progress on multi-step tasks."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "todos": {
                **_TODO_SCHEMA,
                "description": "The complete updated todo list.",
            }
        },
        "required": ["todos"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        todos = input.get("todos", [])
        old_todos = ctx.app_state.native.get(_TODOS_KEY, [])

        def modifier(c: "ToolUseContext") -> "ToolUseContext":
            c.app_state.native[_TODOS_KEY] = todos
            return c

        result = ToolResult(
            tool_name=self.name,
            output=json.dumps({"old_todos": old_todos, "new_todos": todos}),
        )
        result.context_modifier = modifier  # type: ignore[attr-defined]
        return result
