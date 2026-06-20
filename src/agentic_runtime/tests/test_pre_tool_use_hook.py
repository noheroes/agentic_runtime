"""Tests del gate PreToolUse en AgentLoop.

El runtime dispara `HookEvent.PRE_TOOL_USE` antes de ejecutar cada tool (espejo de
`canUseTool` del canónico) y honra el `HookDecision` que devuelve el HookRunner:
`block` → denegar sin ejecutar, `modified_input` → reemplazar el input. La POLÍTICA
(candado de plan mode, aprobación HITL) la pone el integrador en su handler; estos
tests verifican el cableado del punto de extensión, no una política concreta.
"""
import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.events import DoneEvent, ToolCallEvent
from agentic_runtime.hooks import HookDecision, HookEvent, HookRunner
from agentic_runtime.tools import ToolCategory, ToolRegistry, ToolResult
from agentic_runtime.tools.dispatcher import ToolDispatcher
from agentic_runtime.loop import AgentLoop


def _make_caller(*events):
    class StubCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            async def _gen():
                for ev in events:
                    yield ev
            return _gen()
    return StubCaller()


class RecordingTool:
    """Tool nativa que registra cada ejecución para asertar si corrió o no."""
    name = "echo"
    description = "Echoes input"
    input_schema: dict = {"type": "object", "properties": {"text": {"type": "string"}}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def execute(self, input: dict, ctx) -> ToolResult:
        self.calls.append(input)
        return ToolResult(tool_name=self.name, output=input.get("text", ""))


class GatedTool(RecordingTool):
    """Como RecordingTool pero requiere permiso (escenario plan-lock / HITL)."""
    name = "write_file"
    requires_permission = True


def _make_registry(*tools) -> ToolRegistry:
    reg = ToolRegistry()
    for t in tools:
        reg.register(t)
    return reg


def _loop(caller, reg, hook_runner):
    return AgentLoop(
        model_caller=caller,
        tool_registry=reg,
        tool_dispatcher=ToolDispatcher(),
        hook_runner=hook_runner,
    )


def _one_tool_call(tool_name="echo", text="mundo"):
    return _make_caller(
        ToolCallEvent(tool_name=tool_name, tool_input={"text": text}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )


# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pre_tool_use_fires_with_payload():
    """El hook recibe tool_name, tool_input, call_id y el ctx antes de ejecutar."""
    seen: list[dict] = []

    async def handler(event, payload):
        seen.append(payload)
        return None  # no opina → la tool corre

    runner = HookRunner()
    runner.register(HookEvent.PRE_TOOL_USE, handler)

    tool = RecordingTool()
    await _loop(_one_tool_call(), _make_registry(tool), runner).run("usa echo", ToolUseContext(session_id="s1"))

    assert len(seen) == 1
    assert seen[0]["tool_name"] == "echo"
    assert seen[0]["tool_input"] == {"text": "mundo"}
    assert seen[0]["call_id"] == "c1"
    assert isinstance(seen[0]["ctx"], ToolUseContext)
    assert tool.calls == [{"text": "mundo"}]  # corrió


@pytest.mark.asyncio
async def test_pre_tool_use_block_denies_execution():
    """`block` impide la ejecución y deja un tool message de error con el mensaje."""
    async def handler(event, payload):
        return HookDecision.blocked("denegado por política")

    runner = HookRunner()
    runner.register(HookEvent.PRE_TOOL_USE, handler)

    tool = RecordingTool()
    ctx = ToolUseContext(session_id="s1")
    await _loop(_one_tool_call(), _make_registry(tool), runner).run("usa echo", ctx)

    assert tool.calls == [], "la tool NO debe ejecutarse si el hook bloquea"
    tool_msgs = [m for m in ctx.messages if m["role"] == "tool"]
    assert tool_msgs and "denegado por política" in tool_msgs[0]["content"]


@pytest.mark.asyncio
async def test_pre_tool_use_modified_input_replaces_input():
    """`modified_input` reemplaza el input que recibe la tool."""
    async def handler(event, payload):
        return HookDecision(modified_input={"text": "reemplazado"})

    runner = HookRunner()
    runner.register(HookEvent.PRE_TOOL_USE, handler)

    tool = RecordingTool()
    await _loop(_one_tool_call(text="original"), _make_registry(tool), runner).run("x", ToolUseContext(session_id="s1"))

    assert tool.calls == [{"text": "reemplazado"}]


@pytest.mark.asyncio
async def test_no_hook_runner_executes_normally():
    """Sin hook_runner el comportamiento es el de antes (no-op)."""
    tool = RecordingTool()
    await _loop(_one_tool_call(), _make_registry(tool), None).run("x", ToolUseContext(session_id="s1"))
    assert tool.calls == [{"text": "mundo"}]


@pytest.mark.asyncio
async def test_plan_mode_lock_via_hook():
    """Escenario candado: el hook lee app_state.native['plan_mode'] y deniega escrituras."""
    async def plan_lock(event, payload):
        ctx = payload["ctx"]
        if ctx.app_state.native.get("plan_mode") and payload["tool_name"] == "write_file":
            return HookDecision.blocked("plan mode activo: escritura bloqueada")
        return None

    runner = HookRunner()
    runner.register(HookEvent.PRE_TOOL_USE, plan_lock)

    tool = GatedTool()
    ctx = ToolUseContext(session_id="s1")
    ctx.app_state.native["plan_mode"] = True
    # sembrar permiso para aislar el candado del gate de permisos del dispatcher
    ctx.app_state.permissions = ctx.app_state.permissions.with_command_allow(["write_file"])

    caller = _make_caller(
        ToolCallEvent(tool_name="write_file", tool_input={"text": "x"}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    await _loop(caller, _make_registry(tool), runner).run("escribe", ctx)

    assert tool.calls == [], "en plan mode la escritura no debe ejecutarse"
    tool_msgs = [m for m in ctx.messages if m["role"] == "tool"]
    assert tool_msgs and "plan mode activo" in tool_msgs[0]["content"]


@pytest.mark.asyncio
async def test_hitl_grant_then_execute():
    """Escenario HITL: tool con permiso NO concedido; el hook 'aprueba' mutando
    app_state.permissions y la tool se ejecuta a través del dispatcher real."""
    async def approve(event, payload):
        ctx = payload["ctx"]
        if payload["tool_name"] == "write_file" and "write_file" not in ctx.permission_context.allowed_names():
            ctx.app_state.permissions = ctx.app_state.permissions.with_command_allow(["write_file"])
        return None

    runner = HookRunner()
    runner.register(HookEvent.PRE_TOOL_USE, approve)

    tool = GatedTool()
    ctx = ToolUseContext(session_id="s1")  # arranca sin permisos
    caller = _make_caller(
        ToolCallEvent(tool_name="write_file", tool_input={"text": "ok"}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    await _loop(caller, _make_registry(tool), runner).run("escribe", ctx)

    assert tool.calls == [{"text": "ok"}], "tras conceder el permiso, la tool debe ejecutarse"
    assert "write_file" in ctx.permission_context.allowed_names()
