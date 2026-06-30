"""Aislamiento de la lista de tareas por sesión (espejo de `getTaskListId()` → `getSessionId()`).

Regresión del hallazgo (2026-06-30): `TaskList` de un tenant real devolvía tareas de otras
sesiones porque `InMemoryTaskRegistry` es singleton global y `TaskListTool` listaba `list_all()`
sin filtrar → bleed cross-sesión/tenant. El canónico escopa la lista por `getTaskListId()`
(per-sesión); aquí se escopa por `ctx.session_id`.
"""
from __future__ import annotations

import json

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.execution.tasks.registry import InMemoryTaskRegistry, set_registry
from agentic_runtime.tools.native.task_tools import (
    TaskGetTool,
    TaskListTool,
    TaskStopTool,
)


def test_list_for_filters_by_owner_session():
    reg = InMemoryTaskRegistry()
    a = reg.register(description="de s1", session_id="s1")
    b = reg.register(description="de s2", session_id="s2")

    assert {r.task_id for r in reg.list_for("s1")} == {a.task_id}
    assert {r.task_id for r in reg.list_for("s2")} == {b.task_id}


async def test_task_list_tool_does_not_leak_other_sessions():
    reg = InMemoryTaskRegistry()
    set_registry(reg)
    mine = reg.register(description="mía: x", session_id="s1")
    reg.register(description="ajena: y", session_id="s2")

    result = await TaskListTool().execute({}, ctx=ToolUseContext(session_id="s1"))
    listed = json.loads(result.output)
    ids = {t["task_id"] for t in listed}
    assert ids == {mine.task_id}, listed


async def test_task_get_other_session_is_invisible():
    reg = InMemoryTaskRegistry()
    set_registry(reg)
    other = reg.register(description="ajena", session_id="s2")

    result = await TaskGetTool().execute(
        {"task_id": other.task_id}, ctx=ToolUseContext(session_id="s1")
    )
    assert result.is_error


async def test_task_stop_other_session_is_invisible():
    reg = InMemoryTaskRegistry()
    set_registry(reg)
    other = reg.register(description="ajena", session_id="s2")

    result = await TaskStopTool().execute(
        {"task_id": other.task_id}, ctx=ToolUseContext(session_id="s1")
    )
    assert result.is_error
