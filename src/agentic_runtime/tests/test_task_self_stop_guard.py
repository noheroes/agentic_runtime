"""`FIND-TASK-SELF-1` — la tarea EN CURSO no es materia de las tools `Task*`.

Hallazgo (medido, 2026-08-07, RONDA 6 del E2g con `seed 986409977`): el modelo eligió
`TaskStop` y la tarea murió «CANCELADA esperando el stream del modelo», con la respuesta
vacía. La cadena es entera de B:

  · `execution/local/runtime.py:192-194` — la tarea RAÍZ se registra con
    `session_id=task.session_id`, el mismo que acaba en `ctx.session_id` (`:292-293`).
  · `execution/tasks/registry.py:106` — `list_for` filtra SÓLO por `owner_session_id`
    ⇒ la raíz sale en `TaskList`.
  · `tools/native/task_tools.py:_scoped_get` — filtra SÓLO por sesión ⇒ la raíz es
    resoluble por id.
  · `TaskStopTool.execute` — llama `kill(task_id)` sin guarda contra el propio llamante.
  · `execution/tasks/registry.py:118-125` — `kill` hace `asyncio_task.cancel()`.

En A esto es estructuralmente imposible, y **no por una guarda: por la topología**. A
tiene DOS registros. `TaskStopTool.ts` valida contra `appState.tasks[id]` con
`status === 'running'`, y ahí sólo viven tareas de FONDO (shells, agentes async,
sesiones remotas); el turno principal no es una entrada de ese registro. `TaskList/Get/
Update` leen la otra estructura, la lista por sesión. B fusionó ambas en un único
`InMemoryTaskRegistry`, y esa fusión es lo que mete la raíz al alcance del modelo.

Alcance de lo que se paga AQUÍ: la tarea en curso deja de ser alcanzable por las seis
tools. La separación de los dos registros de A es más ancha y queda DECLARADA, no
pagada aquí — es la misma raíz que `FIND-TASK-1` (en B el modelo no puede mover el
`status` de una tarea porque el `status` es el del ciclo de vida de ejecución, no el
de un TODO).

Los tests aseveran CONDUCTA (`H-L4`), no firma: hay dos de unidad sobre las tools y uno
E2E sobre el runtime ensamblado por `create_runtime`, que es donde el defecto se
manifestó de verdad.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.events import DoneEvent, TokenEvent, ToolCallEvent
from agentic_runtime.execution.tasks.registry import InMemoryTaskRegistry
from agentic_runtime.execution.tasks.status import TaskStatus
from agentic_runtime.factory import (
    CapabilitiesConfig,
    RuntimeConfig,
    StorageConfig,
    create_runtime,
)
from agentic_runtime.tools.native.task_tools import (
    TaskGetTool,
    TaskListTool,
    TaskOutputTool,
    TaskStopTool,
    TaskUpdateTool,
)

# ──────────────────────────────────────────────────────────────────────────────
# 1 · Unidad — la tarea en curso no se resuelve por id en NINGUNA de las tools
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "tool, payload",
    [
        (TaskStopTool(), {}),
        (TaskGetTool(), {}),
        (TaskUpdateTool(), {"description": "reescrita por el propio turno"}),
        (TaskOutputTool(), {}),
    ],
    ids=["stop", "get", "update", "output"],
)
async def test_own_task_is_not_addressable(tool, payload):
    reg = InMemoryTaskRegistry()
    propia = reg.register(description="el turno en curso", session_id="s1")
    reg.start(propia.task_id, asyncio_task=None)
    ctx = ToolUseContext(session_id="s1", task_id=propia.task_id, task_registry=reg)

    result = await tool.execute({"task_id": propia.task_id, **payload}, ctx=ctx)

    assert result.is_error, (
        f"`{tool.name}` alcanzó la tarea EN CURSO ({propia.task_id}). En A el turno "
        f"principal no está en `appState.tasks`, así que ninguna tool puede tocarlo. "
        f"Salida: {result.output!r}"
    )
    # Y no basta con el `is_error`: la tarea no puede haber quedado tocada.
    assert reg.get(propia.task_id).status is TaskStatus.RUNNING
    assert reg.get(propia.task_id).description == "el turno en curso"


async def test_own_task_is_not_listed():
    reg = InMemoryTaskRegistry()
    propia = reg.register(description="el turno en curso", session_id="s1")
    hija = reg.register(description="una de fondo, ésa sí", session_id="s1")
    ctx = ToolUseContext(session_id="s1", task_id=propia.task_id, task_registry=reg)

    result = await TaskListTool().execute({}, ctx=ctx)
    ids = {t["task_id"] for t in json.loads(result.output)}

    assert propia.task_id not in ids, (
        "`TaskList` enumeró la tarea EN CURSO: el modelo ve —y puede apuntar a— el "
        f"turno que lo está ejecutando. Listado: {ids}"
    )
    # La guarda es quirúrgica: las demás tareas de la sesión siguen a la vista.
    assert hija.task_id in ids, ids


async def test_sibling_task_of_same_session_remains_stoppable():
    """Control positivo: la guarda no puede convertirse en «TaskStop no para nada»."""
    reg = InMemoryTaskRegistry()
    propia = reg.register(description="el turno en curso", session_id="s1")
    otra = reg.register(description="de fondo", session_id="s1")
    reg.start(otra.task_id, asyncio_task=None)
    ctx = ToolUseContext(session_id="s1", task_id=propia.task_id, task_registry=reg)

    result = await TaskStopTool().execute({"task_id": otra.task_id}, ctx=ctx)

    assert not result.is_error, result.output
    assert reg.get(otra.task_id).status is TaskStatus.KILLED


# ──────────────────────────────────────────────────────────────────────────────
# 2 · E2E — el turno sobrevive a que el modelo se apunte a sí mismo
# ──────────────────────────────────────────────────────────────────────────────

class _SelfStopCaller:
    """Turno 1 → `TaskList`. Turno 2 → `TaskStop` sobre lo que la lista devolvió.

    Reproduce la RONDA 6: el modelo no inventó un id, lo LEYÓ de `TaskList`. Si la
    lista no le ofrece la raíz, el turno 2 no tiene a qué apuntar.
    """

    def __init__(self) -> None:
        self.turn = 0
        self.listed: list = []
        self.stopped_id = ""
        self.reached_final_turn = False

    async def complete(self, messages, tools, *, stop=None, model_id=""):
        self.turn += 1
        turn = self.turn
        if turn == 1:
            events = [
                ToolCallEvent(tool_name="TaskList", tool_input={}, call_id="c1"),
                DoneEvent(stop_reason="tool_calls"),
            ]
        elif turn == 2:
            payload = next(
                (str(m.get("content", "")) for m in reversed(list(messages))
                 if m.get("role") == "tool"),
                "",
            )
            try:
                self.listed = json.loads(payload)
            except (ValueError, TypeError):
                self.listed = []
            self.stopped_id = (
                self.listed[0]["task_id"] if self.listed else "no-hay-nada-que-parar"
            )
            events = [
                ToolCallEvent(
                    tool_name="TaskStop",
                    tool_input={"task_id": self.stopped_id},
                    call_id="c2",
                ),
                DoneEvent(stop_reason="tool_calls"),
            ]
        else:
            self.reached_final_turn = True
            events = [TokenEvent(content="RESPUESTA-FINAL"), DoneEvent(stop_reason="stop")]

        # El turno final ESPERA, como espera un stream real. Sin esta espera la
        # cancelación llega tarde y el defecto se disfraza de verde (medido: el
        # registry decía COMPLETED mientras quien aguardaba la tarea recibía
        # `CancelledError`).
        lento = turn >= 3

        async def _gen():
            if lento:
                await asyncio.sleep(0.2)
            for ev in events:
                yield ev

        return _gen()


async def test_model_cannot_kill_its_own_turn(tmp_path: Path):
    caller = _SelfStopCaller()
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        capabilities=CapabilitiesConfig(),
    ))
    task_id = await runtime.dispatch(RuntimeTask(
        prompt="lista las tareas y para la primera",
        description="auto-stop",
        session_id="sess-self-stop",
    ))
    rec = runtime._task_registry.get(task_id)
    cancelado = False
    try:
        await rec.asyncio_task
    except asyncio.CancelledError:
        cancelado = True

    assert not cancelado, (
        "el turno raíz salió por `CancelledError`: el modelo se detuvo a sí mismo"
    )
    assert task_id not in [r.get("task_id") for r in caller.listed], (
        f"`TaskList` le sirvió al modelo su propia tarea raíz: {caller.listed}"
    )
    assert runtime.status(task_id) is TaskStatus.COMPLETED, runtime.status(task_id)
    assert runtime.result(task_id) == "RESPUESTA-FINAL", runtime.result(task_id)
    assert caller.reached_final_turn
