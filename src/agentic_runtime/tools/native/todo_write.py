from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

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
    # `shouldDefer: true` del canónico (`TodoWriteTool/TodoWriteTool.ts:51`) — `GAP-TOOL4`.
    deferred = True
    # `searchHint` del canónico, grafía literal. Fuera del contrato T1
    # (`contracts/tools.py:5`); lo lee ToolSearch para rankear (+4 vs +2 de la descripción).
    search_hint = "manage the session task checklist"
    # Homologada contra `TodoWriteTool/prompt.ts:3-181` (`PROMPT`), `GAP-PROMPT-1`.
    # OMITIDO Y DECLARADO: `activeForm` (`:151-153`, `:176-178`) y las dos formas
    # imperativa/continua que lo acompañan — el esquema de B no tiene ese campo, y
    # anunciarlo repetiría `FIND-E11-3`.
    # ⚠ DIVERGENCIA EN PIE, no pagada aquí: B tiene un `priority` (high/medium/low)
    # que A **no tiene**. Es invención de B; por `L10` una divergencia no es mejora
    # hasta demostrarlo. No se retira en esta ventana porque tocar el esquema no es
    # pagar `GAP-PROMPT-1`; queda anotada para que no se acredite como homologada.
    description = """Use this tool to create and manage a structured task list for your current \
coding session. This helps you track progress, organize complex tasks, and demonstrate \
thoroughness to the user.
It also helps the user understand the progress of the task and overall progress of their requests.

## When to Use This Tool
Use this tool proactively in these scenarios:

1. Complex multi-step tasks - When a task requires 3 or more distinct steps or actions
2. Non-trivial and complex tasks - Tasks that require careful planning or multiple operations
3. User explicitly requests todo list - When the user directly asks you to use the todo list
4. User provides multiple tasks - When users provide a list of things to be done (numbered or \
comma-separated)
5. After receiving new instructions - Immediately capture user requirements as todos
6. When you start working on a task - Mark it as in_progress BEFORE beginning work. Ideally you \
should only have one todo as in_progress at a time
7. After completing a task - Mark it as completed and add any new follow-up tasks discovered \
during implementation

## When NOT to Use This Tool

Skip using this tool when:
1. There is only a single, straightforward task
2. The task is trivial and tracking it provides no organizational benefit
3. The task can be completed in less than 3 trivial steps
4. The task is purely conversational or informational

NOTE that you should not use this tool if there is only one trivial task to do. In this case you \
are better off just doing the task directly.

## Task States and Management

1. **Task States**: Use these states to track progress:
   - pending: Task not yet started
   - in_progress: Currently working on (limit to ONE task at a time)
   - completed: Task finished successfully

2. **Task Management**:
   - Update task status in real-time as you work
   - Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
   - Exactly ONE task must be in_progress at any time (not less, not more)
   - Complete current tasks before starting new ones
   - Remove tasks that are no longer relevant from the list entirely

3. **Task Completion Requirements**:
   - ONLY mark a task as completed when you have FULLY accomplished it
   - If you encounter errors, blockers, or cannot finish, keep the task as in_progress
   - When blocked, create a new task describing what needs to be resolved
   - Never mark a task as completed if:
     - Tests are failing
     - Implementation is partial
     - You encountered unresolved errors
     - You couldn't find necessary files or dependencies

4. **Task Breakdown**:
   - Create specific, actionable items
   - Break complex tasks into smaller, manageable steps
   - Use clear, descriptive task names

When in doubt, use this tool. Being proactive with task management demonstrates attentiveness and \
ensures you complete all requirements successfully.
"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
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

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        todos = input.get("todos", [])
        old_todos = ctx.app_state.native.get(_TODOS_KEY, [])

        def modifier(c: ToolUseContext) -> ToolUseContext:
            c.app_state.native[_TODOS_KEY] = todos
            return c

        return ToolResult(
            tool_name=self.name,
            output=json.dumps({"old_todos": old_todos, "new_todos": todos}),
            context_modifier=modifier,
        )
