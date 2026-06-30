"""Slice B/C — aplicación de la AgentDefinition al subagente (homologación subagent_type).

Espejo de `runAgent`: un subagente especializado corre con (a) el modelo de su definición
(inherit-aware, NUNCA el nombre del agente), (b) su system prompt REEMPLAZANDO el base
(getAgentSystemPrompt → [agentPrompt]) y (c) su subconjunto de tools (resolveAgentTools).

Cubre el loop (override + restricción) y el dispatch end-to-end vía el resolver inyectado.
"""
from __future__ import annotations

import pytest

from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.events import DoneEvent
from agentic_runtime.execution.agents import AgentDefinition
from agentic_runtime.factory import (
    RuntimeConfig,
    StorageConfig,
    ToolsConfig,
    create_runtime,
)
from agentic_runtime.loop import AgentLoop
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools import ToolCategory, ToolRegistry, ToolResult
from agentic_runtime.tools.dispatcher import ToolDispatcher

pytestmark = pytest.mark.asyncio


class _RecordingCaller:
    """Captura lo que el loop pasa al modelo: tools anunciadas, model_id, system_override."""

    def __init__(self) -> None:
        self.tool_names: list[str] = []
        self.model_id: str | None = None
        self.system_override: str | None = None

    async def complete(
        self, messages, tools, *, stop=None, model_id="", system_sections=None,
        system_override=None,
    ):
        self.tool_names = [t["name"] for t in tools]
        self.model_id = model_id
        self.system_override = system_override

        async def gen():
            yield DoneEvent(stop_reason="stop")

        return gen()


def _tool(name: str):
    class _T:
        pass

    t = _T()
    t.name = name
    t.description = name
    t.input_schema = {"type": "object", "properties": {}}
    t.category = ToolCategory.UTILITY
    t.requires_permission = False
    t.safe_for_background = True
    t.timeout_seconds = 5.0

    async def _execute(input, ctx):
        return ToolResult(tool_name=name, output="")

    t.execute = _execute
    return t


def _registry(*names) -> ToolRegistry:
    reg = ToolRegistry()
    for n in names:
        reg.register(_tool(n))
    return reg


# --- Loop: restricción de tools (espejo resolveAgentTools) -----------------------------

async def test_loop_restricts_tools_to_allowed_subset():
    caller = _RecordingCaller()
    loop = AgentLoop(
        model_caller=caller, tool_registry=_registry("alpha", "bravo"),
        tool_dispatcher=ToolDispatcher(), agent_allowed_tools=("alpha",),
    )
    await loop.run("hi", ToolUseContext(session_id="s1"))
    assert "alpha" in caller.tool_names
    assert "bravo" not in caller.tool_names


async def test_loop_no_restriction_announces_all():
    caller = _RecordingCaller()
    loop = AgentLoop(
        model_caller=caller, tool_registry=_registry("alpha", "bravo"),
        tool_dispatcher=ToolDispatcher(),  # agent_allowed_tools = () → todas
    )
    await loop.run("hi", ToolUseContext(session_id="s1"))
    assert {"alpha", "bravo"} <= set(caller.tool_names)


async def test_loop_wildcard_announces_all():
    caller = _RecordingCaller()
    loop = AgentLoop(
        model_caller=caller, tool_registry=_registry("alpha", "bravo"),
        tool_dispatcher=ToolDispatcher(), agent_allowed_tools=("*",),
    )
    await loop.run("hi", ToolUseContext(session_id="s1"))
    assert {"alpha", "bravo"} <= set(caller.tool_names)


# --- Loop: system prompt override (espejo getAgentSystemPrompt → [agentPrompt]) ---------

async def test_loop_passes_system_override_when_set():
    caller = _RecordingCaller()
    loop = AgentLoop(
        model_caller=caller, tool_registry=_registry(), tool_dispatcher=ToolDispatcher(),
        system_prompt_override="Eres un agente de investigación.",
    )
    await loop.run("hi", ToolUseContext(session_id="s1"))
    assert caller.system_override == "Eres un agente de investigación."


async def test_loop_inherits_base_when_no_override():
    caller = _RecordingCaller()
    loop = AgentLoop(
        model_caller=caller, tool_registry=_registry(), tool_dispatcher=ToolDispatcher(),
    )
    await loop.run("hi", ToolUseContext(session_id="s1"))
    assert caller.system_override is None  # hereda el base del caller


# --- Dispatch end-to-end: subagent_type → def → modelo heredado + override + tools -----

class _Resolver:
    def __init__(self, defn: AgentDefinition) -> None:
        self._defn = defn

    def resolve(self, subagent_type: str):
        return self._defn if subagent_type == self._defn.subagent_type else None


async def _dispatch_and_wait(runtime, task: RuntimeTask) -> None:
    await runtime.startup()
    try:
        task_id = await runtime.dispatch(task)
        rec = runtime._task_registry.get(task_id)
        await rec.asyncio_task
    finally:
        await runtime.shutdown()


async def test_dispatch_resolves_definition_inherits_model_and_applies_prompt_tools(tmp_path):
    caller = _RecordingCaller()
    defn = AgentDefinition(
        subagent_type="researcher",
        model=None,  # hereda → modelo del padre, NO 'researcher'
        system_prompt="Solo investiga; no escribas.",
        allowed_tools=("alpha",),
    )
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        model_id="parent-model",
        tools=ToolsConfig(extras=[_tool("alpha"), _tool("bravo")]),
        agent_resolver=_Resolver(defn),
    ))
    await _dispatch_and_wait(runtime, RuntimeTask(
        prompt="busca", description="research", subagent_type="researcher",
    ))
    # Modelo heredado del padre (la regresión era model_id='researcher' → ModelNotFound).
    assert caller.model_id == "parent-model"
    # System prompt de la def reemplaza el base.
    assert caller.system_override == "Solo investiga; no escribas."
    # Tools restringidas al subconjunto de la def.
    assert "alpha" in caller.tool_names
    assert "bravo" not in caller.tool_names


async def test_dispatch_without_subagent_type_is_generic_fork(tmp_path):
    caller = _RecordingCaller()
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        model_id="parent-model",
        tools=ToolsConfig(extras=[_tool("alpha"), _tool("bravo")]),
        agent_resolver=_Resolver(AgentDefinition(subagent_type="researcher")),
    ))
    await _dispatch_and_wait(runtime, RuntimeTask(prompt="x", description="y"))
    assert caller.model_id == "parent-model"
    assert caller.system_override is None
    assert {"alpha", "bravo"} <= set(caller.tool_names)
