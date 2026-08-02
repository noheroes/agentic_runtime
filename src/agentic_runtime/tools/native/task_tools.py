"""
Task management tools — equivalente Python de TaskCreate/Get/List/Update/Stop/Output del canónico.

**`C7` retira el doble camino.** Estas seis tools iban por el global `get_registry()`
mientras `LocalAgentRuntime` usaba **su propia instancia inyectada**: dos caminos que
podían divergir (`SEAMS §S19`, `existe-doble-camino`) y que de hecho divergían, porque
nadie llamaba `set_registry` en producción ⇒ las seis reventaban con `RuntimeError`, el
mismo modo de fallo que `FIND-EXEC1`. Ahora hay UN camino: el registry del runtime,
threadeado al `ctx` (`S19` por DI).
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

_NO_REGISTRY = (
    "Task registry not wired: this runtime was assembled without `S19` "
    "(RuntimeConfig.task_registry → LocalAgentRuntime → ctx.task_registry)."
)


def _session_of(ctx: "ToolUseContext | None") -> str | None:
    """Lista activa = sesión del contexto (espejo de `getTaskListId()`)."""
    return getattr(ctx, "session_id", None)


def _registry_of(ctx: "ToolUseContext | None") -> Any:
    """El registry del turno. `None` = costura sin poblar: la tool devuelve `is_error`
    limpio, no levanta — que es lo que el global hacía y por lo que nadie lo notaba."""
    return getattr(ctx, "task_registry", None)


def _scoped_get(task_id: str, ctx: "ToolUseContext | None"):
    """Resuelve un task SÓLO si pertenece a la lista de la sesión activa.

    Un `task_id` de otra sesión es invisible (espejo: no está en el tasks-dir
    de esta sesión) → se trata como inexistente."""
    registry = _registry_of(ctx)
    if registry is None:
        return None
    record = registry.get(task_id)
    if record is None or record.owner_session_id != _session_of(ctx):
        return None
    return record


class TaskCreateTool:
    name = "TaskCreate"
    description = "Create a task in the task registry to track background or async work."
    input_schema = {
        "type": "object",
        "properties": {
            "subject": {"type": "string", "description": "Brief title for the task."},
            "description": {"type": "string", "description": "What needs to be done."},
        },
        "required": ["subject", "description"],
    }
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        subject = input.get("subject", "")
        description = input.get("description", "")
        registry = _registry_of(ctx)
        if registry is None:
            return ToolResult.error(self.name, _NO_REGISTRY)
        record = registry.register(
            description=f"{subject}: {description}", session_id=_session_of(ctx)
        )
        return ToolResult(
            tool_name=self.name,
            output=json.dumps({"task_id": record.task_id, "subject": subject}),
        )


class TaskGetTool:
    name = "TaskGet"
    description = "Get the current status and result of a task."
    input_schema = {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "The ID of the task."}
        },
        "required": ["task_id"],
    }
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        task_id = input.get("task_id", "")
        record = _scoped_get(task_id, ctx)
        if record is None:
            return ToolResult.error(self.name, f"No task found with id: {task_id}")
        return ToolResult(
            tool_name=self.name,
            output=json.dumps({
                "task_id": record.task_id,
                "description": record.description,
                "status": record.status,
                "result": record.result,
            }),
        )


class TaskListTool:
    name = "TaskList"
    description = "List all tasks currently tracked by the registry."
    #: **Sin parámetros, como el canónico** (`TaskListTool.ts:13`:
    #: `inputSchema = z.strictObject({})`).
    #:
    #: ⚠ Aquí había un `status` de filtro que **A no tiene**, y que cobró en `E11`
    #: (`FIND-E11-3`): el modelo leyó «Filter by status (pending, running, …). Omit
    #: for all.» y llamó con `status="all"`. Como el campo era `string` libre —sin
    #: `enum` que acotara el dominio— y el filtro comparaba por igualdad, un valor
    #: fuera de dominio se tragaba en silencio y devolvía `[]`: **indistinguible de
    #: «no hay tareas»**. El modelo concluyó que la sesión no tenía trabajos y
    #: respondió eso, con dos tareas sembradas delante. No es un fallo del modelo:
    #: es una invención de B, mal acotada, que hace mentir a la tool. `L10` —una
    #: divergencia con el canónico no es una mejora hasta que se demuestre— así que
    #: se retira en vez de parchearse con un `enum`.
    input_schema = {"type": "object", "properties": {}}
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        registry = _registry_of(ctx)
        if registry is None:
            return ToolResult.error(self.name, _NO_REGISTRY)
        # Escopado a la lista de la sesión activa (espejo de `getTaskListId()` →
        # `getSessionId()`): una sesión sólo ve sus propias tareas, sin bleed.
        records = registry.list_for(_session_of(ctx))

        return ToolResult(
            tool_name=self.name,
            output=json.dumps([
                {
                    "task_id": r.task_id,
                    "description": r.description,
                    "status": r.status,
                }
                for r in records
            ]),
        )


class TaskUpdateTool:
    name = "TaskUpdate"
    description = "Update the description of an existing task."
    input_schema = {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "The task ID to update."},
            "description": {"type": "string", "description": "New description."},
        },
        "required": ["task_id"],
    }
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        task_id = input.get("task_id", "")
        record = _scoped_get(task_id, ctx)
        if record is None:
            return ToolResult.error(self.name, f"No task found with id: {task_id}")

        new_desc = input.get("description")
        if new_desc is not None:
            record.description = new_desc

        return ToolResult(
            tool_name=self.name,
            output=json.dumps({"task_id": task_id, "description": record.description}),
        )


class TaskStopTool:
    name = "TaskStop"
    description = "Stop (kill) a running background task."
    input_schema = {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "The ID of the task to stop."}
        },
        "required": ["task_id"],
    }
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        task_id = input.get("task_id", "")
        if _scoped_get(task_id, ctx) is None:
            return ToolResult.error(
                self.name, f"Task {task_id} not found or already terminal."
            )
        killed = _registry_of(ctx).kill(task_id)
        if not killed:
            return ToolResult.error(
                self.name, f"Task {task_id} not found or already terminal."
            )
        return ToolResult(
            tool_name=self.name,
            output=f"Task {task_id} stopped.",
        )


class TaskOutputTool:
    name = "TaskOutput"
    description = "Get the output/result of a completed or failed task."
    input_schema = {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "The ID of the task."}
        },
        "required": ["task_id"],
    }
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        task_id = input.get("task_id", "")
        record = _scoped_get(task_id, ctx)
        if record is None:
            return ToolResult.error(self.name, f"No task found with id: {task_id}")
        if record.result is None:
            return ToolResult(
                tool_name=self.name,
                output=f"Task {task_id} has status '{record.status}' and no result yet.",
            )
        return ToolResult(tool_name=self.name, output=record.result)
