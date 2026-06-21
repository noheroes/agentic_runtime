"""Seam `root_turn_start_hooks` — registro per-request de hooks de inicio de run.

El canónico drena las notificaciones background DENTRO del loop (turn-start), no en el
borde (`query.ts`). El consumidor (paquete separado: no es el loop) no puede alcanzar el
`AgentLoop` que `_run_loop` construye por dispatch para registrar su `drain` hook. Este
seam le da ese punto, espejo de `root_context_modifier`: un provider per-request cuyos
hooks `_run_loop` registra en el loop SOLO de la raíz (`parent_snapshot is None`). Los
subagentes drenan su propio canal por su propio fork, no por el seam de raíz.

La maquinaria del loop ya existe (`AgentLoop.register_turn_start_hook` /
`_run_turn_start_hooks`, disparado al arrancar `run()`); lo que faltaba era que el
runtime registrara los hooks del consumidor.

Contrato: `RuntimeConfig.root_turn_start_hooks: (task) -> list[hook]`, con
`hook = Callable[[], Awaitable[None]]`. Devuelve `[]` para sesiones desconocidas
(passthrough). Aplicado solo cuando `parent_snapshot is None`.
"""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.events import DoneEvent
from agentic_runtime.execution.fork import ForkSnapshot
from agentic_runtime.factory import RuntimeConfig, StorageConfig, create_runtime


def _make_caller(*events):
    class StubCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            async def _gen():
                for ev in events:
                    yield ev
            return _gen()
    return StubCaller()


@pytest.mark.asyncio
async def test_root_turn_start_hooks_registered_and_fired_at_root(tmp_path):
    """En la raíz: el provider recibe el task y sus hooks se disparan al arrancar el
    run (antes del primer turno, como el drain canónico)."""
    seen_tasks: list[str] = []
    fired: list[str] = []

    async def drain_hook() -> None:
        fired.append("drained")

    def provider(task):
        seen_tasks.append(task.description)
        return [drain_hook]

    rt = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=_make_caller(DoneEvent(stop_reason="stop")),
        root_turn_start_hooks=provider,
    ))

    async for _ in rt.stream(RuntimeTask(
        prompt="hola", description="root-task", session_id="S1", owner_id="U1",
    )):
        pass

    assert seen_tasks == ["root-task"]
    assert fired == ["drained"]


@pytest.mark.asyncio
async def test_root_turn_start_hooks_not_applied_to_subagents(tmp_path):
    """El provider es de la RAÍZ: un subagente (parent_snapshot != None) no registra
    sus hooks."""
    calls: list[str] = []

    def provider(task):
        calls.append(task.description)
        return []

    rt = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=_make_caller(DoneEvent(stop_reason="stop")),
        root_turn_start_hooks=provider,
    ))

    async for _ in rt.stream(RuntimeTask(prompt="p", description="root")):
        pass
    assert calls == ["root"]

    snap = ForkSnapshot(session_id="s-parent", user_id="u-parent")
    rec = rt._task_registry.register(description="sub")
    await rt._run_loop(rec.task_id, RuntimeTask(prompt="p2", description="sub"), snap)
    assert calls == ["root"], "el subagente NO debe aplicar el provider de raíz"


@pytest.mark.asyncio
async def test_provider_returning_empty_is_inert(tmp_path):
    """Provider que devuelve [] (sesión desconocida) no rompe el run."""
    rt = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=_make_caller(DoneEvent(stop_reason="stop")),
        root_turn_start_hooks=lambda task: [],
    ))
    async for _ in rt.stream(RuntimeTask(prompt="p", description="t")):
        pass


def test_runtime_config_defaults_root_turn_start_hooks_to_none():
    """Sin configurar, el seam es inerte (default None)."""
    assert RuntimeConfig().root_turn_start_hooks is None
