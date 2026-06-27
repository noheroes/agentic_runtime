"""`list_all` es parte del contrato `TaskRegistryProtocol` y `TaskList` lo usa.

Regresión de la omisión: antes el protocolo no declaraba `list_all`, `InMemoryTaskRegistry` no
lo implementaba y `TaskListTool` caía en un fallback que devolvía `[]` siempre. Espejo del
canónico, donde `TaskListTool` lista vía `listTasks()`.
"""
from __future__ import annotations

import json

from agentic_runtime.execution.tasks.registry import (
    InMemoryTaskRegistry,
    TaskRegistryProtocol,
    set_registry,
)
from agentic_runtime.tools.native.task_tools import TaskListTool


def test_inmemory_registry_satisfies_protocol_and_lists_all():
    reg = InMemoryTaskRegistry()
    # El contrato incluye list_all (runtime_checkable Protocol).
    assert isinstance(reg, TaskRegistryProtocol)

    assert reg.list_all() == []
    a = reg.register(description="alpha")
    b = reg.register(description="beta")

    ids = {r.task_id for r in reg.list_all()}
    assert ids == {a.task_id, b.task_id}


async def test_task_list_tool_returns_registered_tasks():
    reg = InMemoryTaskRegistry()
    set_registry(reg)
    rec = reg.register(description="probe-subject: una tarea")

    result = await TaskListTool().execute({}, ctx=None)  # execute no usa ctx
    assert not result.is_error
    listed = json.loads(result.output)
    assert any(t["task_id"] == rec.task_id for t in listed), listed
