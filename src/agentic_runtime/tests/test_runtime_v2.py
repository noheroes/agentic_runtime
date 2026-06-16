"""Tests de R2: LocalAgentRuntime nuevo (runtime_v2) sobre AgentLoop, sin agent_core."""
from __future__ import annotations

import pytest

from agentic_runtime.capabilities.resolver import CapabilitiesResolver
from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.events import DoneEvent, TokenEvent, ToolCallEvent
from agentic_runtime.execution.fork import ForkSnapshot
from agentic_runtime.execution.local.notification import drain_notifications
from agentic_runtime.execution.local.runtime import LocalAgentRuntime
from agentic_runtime.execution.tasks.registry import InMemoryTaskRegistry
from agentic_runtime.execution.tasks.status import TaskStatus
from agentic_runtime.hooks import HookEvent, HookRunner
from agentic_runtime.tools import ToolCategory, ToolRegistry, ToolResult
from agentic_runtime.tools.dispatcher import ToolDispatcher


def _make_caller(*events):
    class StubCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            async def _gen():
                for ev in events:
                    yield ev
            return _gen()
    return StubCaller()


class EchoTool:
    name = "echo"
    description = "echo"
    input_schema: dict = {"type": "object", "properties": {"text": {"type": "string"}}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx) -> ToolResult:
        return ToolResult(tool_name=self.name, output=input.get("text", ""))


def _make_runtime(caller, *, tools=(), task_registry=None, hook_runner=None, small_llm=None):
    reg = ToolRegistry()
    for t in tools:
        reg.register(t)
    return LocalAgentRuntime(
        model_caller=caller,
        capabilities_resolver=CapabilitiesResolver(tool_registry=reg),
        tool_dispatcher=ToolDispatcher(registry=reg),
        task_registry=task_registry or InMemoryTaskRegistry(),
        hook_runner=hook_runner,
        small_llm=small_llm,
    )


async def _await_task(runtime, task_id):
    rec = runtime._task_registry.get(task_id)
    if rec is not None and rec.asyncio_task is not None:
        await rec.asyncio_task


@pytest.mark.asyncio
async def test_dispatch_single_turn_completes():
    caller = _make_caller(TokenEvent(content="respuesta"), DoneEvent(stop_reason="stop"))
    runtime = _make_runtime(caller)
    task_id = await runtime.dispatch(RuntimeTask(prompt="hola", description="t"))
    await _await_task(runtime, task_id)
    assert runtime.status(task_id) == TaskStatus.COMPLETED
    assert runtime.result(task_id) == "respuesta"


@pytest.mark.asyncio
async def test_dispatch_executes_tool_and_pushes_events():
    caller = _make_caller(
        ToolCallEvent(tool_name="echo", tool_input={"text": "mundo"}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    registry = InMemoryTaskRegistry()
    runtime = _make_runtime(caller, tools=(EchoTool(),), task_registry=registry)
    task_id = await runtime.dispatch(RuntimeTask(prompt="usa echo", description="t"))
    await _await_task(runtime, task_id)
    rec = registry.get(task_id)
    types = [e["type"] for e in rec.events]
    assert "tool_start" in types
    assert "tool_result" in types
    assert any(e.get("output") == "mundo" for e in rec.events if e["type"] == "tool_result")


@pytest.mark.asyncio
async def test_subagent_stop_hook_fired_on_completion():
    caller = _make_caller(TokenEvent(content="ok"), DoneEvent(stop_reason="stop"))
    runner = HookRunner()
    fired: list[dict] = []

    async def handler(event, payload):
        fired.append(payload)

    runner.register(HookEvent.SUBAGENT_STOP, handler)
    runtime = _make_runtime(caller, hook_runner=runner)
    task_id = await runtime.dispatch(RuntimeTask(prompt="hola", description="t"))
    await _await_task(runtime, task_id)
    assert len(fired) == 1
    assert fired[0]["status"] == "completed"
    assert fired[0]["result"] == "ok"


@pytest.mark.asyncio
async def test_dispatch_with_parent_snapshot_notifies_parent():
    caller = _make_caller(TokenEvent(content="resultado hijo"), DoneEvent(stop_reason="stop"))
    runtime = _make_runtime(caller)
    snap = ForkSnapshot(session_id="parent-sid", subagent_depth=0)
    task_id = await runtime.dispatch(
        RuntimeTask(prompt="trabaja", description="bg"), parent_snapshot=snap
    )
    await _await_task(runtime, task_id)
    notifs = drain_notifications("parent-sid")
    assert len(notifs) == 1
    assert notifs[0].status == "completed"
    assert notifs[0].final_text == "resultado hijo"


@pytest.mark.asyncio
async def test_no_parent_snapshot_no_notification():
    caller = _make_caller(DoneEvent(stop_reason="stop"))
    runtime = _make_runtime(caller)
    task_id = await runtime.dispatch(RuntimeTask(prompt="x", description="t"))
    await _await_task(runtime, task_id)
    assert drain_notifications("parent-sid") == []
