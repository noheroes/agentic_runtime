"""Seam `root_context_modifier` — autoría per-request del ctx RAÍZ por el consumidor.

El runtime construye el `ToolUseContext` de la raíz en `_build_child` y el consumidor
(paquete separado: no es el loop, a diferencia del canónico) no puede alcanzarlo. Este
seam le da la MISMA autoría per-request que el canónico tiene gratis (construye el ctx
entero con `canUseTool`/`handleElicitation`/app_state), pero sobre los puntos de
extensión que YA existen (`app_state.native` + `ctx.presentation`), sin replicar la
bolsa monolítica del canónico.

Contrato: `RuntimeConfig.root_context_modifier: (ctx, task) -> ctx`, aplicado en
`_run_loop` SOLO cuando `parent_snapshot is None` (agente raíz). Los subagentes NO lo
reciben: heredan su identidad/estado por el `ForkSnapshot`.
"""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.events import DoneEvent, ToolCallEvent
from agentic_runtime.execution.fork import ForkSnapshot
from agentic_runtime.factory import RuntimeConfig, StorageConfig, ToolsConfig, create_runtime
from agentic_runtime.tools import ToolCategory, ToolResult


def _make_caller(*events):
    class StubCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            async def _gen():
                for ev in events:
                    yield ev
            return _gen()
    return StubCaller()


class ProbeTool:
    """Tool que registra lo que ve en su ctx (native + presentation)."""
    name = "probe"
    description = "probe"
    input_schema: dict = {"type": "object", "properties": {}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    def __init__(self) -> None:
        self.seen: list[dict] = []

    async def execute(self, input: dict, ctx) -> ToolResult:
        self.seen.append({
            "native_probe": ctx.app_state.native.get("probe"),
            "presentation": ctx.presentation,
        })
        return ToolResult(tool_name=self.name, output="ok")


class _Marker:
    """Sentinela para verificar que el modifier puede OVERRIDE la presentation."""


@pytest.mark.asyncio
async def test_root_modifier_runs_with_identity_and_seeds_native_and_presentation(tmp_path):
    """En la raíz: el modifier recibe el ctx con la identidad inyectada por el task,
    siembra `app_state.native` y puede sobrescribir `ctx.presentation`; ambos llegan a
    la tool ejecutada en ese turno."""
    captured: dict = {}
    marker = _Marker()

    def modifier(ctx, task):
        captured["session_id"] = ctx.session_id
        captured["user_id"] = ctx.user_id
        captured["description"] = task.description
        ctx.app_state.native["probe"] = "seeded"
        ctx.presentation = marker
        return ctx

    probe = ProbeTool()
    caller = _make_caller(
        ToolCallEvent(tool_name="probe", tool_input={}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    rt = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        tools=ToolsConfig(extras=[probe]),
        root_context_modifier=modifier,
    ))

    async for _ in rt.stream(RuntimeTask(
        prompt="usa probe", description="root-task",
        session_id="S-ext", owner_id="U-ext",
    )):
        pass

    assert captured == {"session_id": "S-ext", "user_id": "U-ext", "description": "root-task"}
    assert probe.seen and probe.seen[0]["native_probe"] == "seeded"
    assert probe.seen[0]["presentation"] is marker


@pytest.mark.asyncio
async def test_root_modifier_not_applied_to_subagents(tmp_path):
    """El modifier es de la RAÍZ: un subagente (parent_snapshot != None) no lo recibe
    (su estado viaja por el ForkSnapshot, no por el seam de raíz)."""
    calls: list[str] = []

    def modifier(ctx, task):
        calls.append(task.description)
        return ctx

    rt = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=_make_caller(DoneEvent(stop_reason="stop")),
        root_context_modifier=modifier,
    ))

    async for _ in rt.stream(RuntimeTask(prompt="p", description="root")):
        pass
    assert calls == ["root"], "la raíz SÍ aplica el modifier"

    snap = ForkSnapshot(session_id="s-parent", user_id="u-parent")
    rec = rt._task_registry.register(description="sub")
    await rt._run_loop(rec.task_id, RuntimeTask(prompt="p2", description="sub"), snap)
    assert calls == ["root"], "el subagente NO debe aplicar el modifier de raíz"


def test_runtime_config_defaults_root_context_modifier_to_none():
    """Sin configurar, el seam es inerte (default None)."""
    assert RuntimeConfig().root_context_modifier is None
