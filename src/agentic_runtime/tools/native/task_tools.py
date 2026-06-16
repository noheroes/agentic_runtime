"""
Task management tools — equivalente Python de TaskCreate/Get/List/Update/Stop/Output del canónico.
Todos operan vía get_registry() para mantenerse desacoplados de LocalAgentRuntime.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ...execution.tasks.registry import get_registry
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext


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
        record = get_registry().register(description=f"{subject}: {description}")
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
        record = get_registry().get(task_id)
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
    input_schema = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Filter by status (pending, running, completed, failed, killed). Omit for all.",
            }
        },
    }
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        status_filter = input.get("status")
        registry = get_registry()
        # TaskRegistryProtocol exposes list_all or we enumerate via internal dict
        # Use duck typing — if list_all exists use it, otherwise use events workaround
        if hasattr(registry, "list_all"):
            records = registry.list_all()
        else:
            # Fallback: registry may not expose list_all — return empty
            records = []

        if status_filter:
            records = [r for r in records if r.status == status_filter]

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
        record = get_registry().get(task_id)
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
        killed = get_registry().kill(task_id)
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
        record = get_registry().get(task_id)
        if record is None:
            return ToolResult.error(self.name, f"No task found with id: {task_id}")
        if record.result is None:
            return ToolResult(
                tool_name=self.name,
                output=f"Task {task_id} has status '{record.status}' and no result yet.",
            )
        return ToolResult(tool_name=self.name, output=record.result)
