"""Tests para runtime/loop/AgentLoop — ciclo real LLM → tools → acumula."""
import asyncio
import pytest

from agentic_runtime.loop import AgentLoop, BasicLoop
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.events import DoneEvent, ErrorEvent, TokenEvent, ToolCallEvent
from agentic_runtime.tools import ToolCategory, ToolRegistry, ToolResult
from agentic_runtime.tools.dispatcher import ToolDispatcher


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

def _make_caller(*events):
    """Crea un ModelCallerProtocol stub que emite los eventos dados."""
    class StubCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            async def _gen():
                for ev in events:
                    yield ev
            return _gen()
    return StubCaller()


class EchoTool:
    name = "echo"
    description = "Echoes input"
    input_schema: dict = {"type": "object", "properties": {"text": {"type": "string"}}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx) -> ToolResult:
        return ToolResult(tool_name=self.name, output=input.get("text", ""))


def _make_registry(*tools) -> ToolRegistry:
    reg = ToolRegistry()
    for t in tools:
        reg.register(t)
    return reg


def _make_ctx(stop: asyncio.Event | None = None) -> ToolUseContext:
    return ToolUseContext(session_id="s1", stop=stop)


# ---------------------------------------------------------------------------
# Ciclo básico
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_loop_single_turn_no_tools():
    caller = _make_caller(TokenEvent(content="hello"), DoneEvent(stop_reason="stop"))
    reg = _make_registry()
    dispatcher = ToolDispatcher()

    loop = AgentLoop(model_caller=caller, tool_registry=reg, tool_dispatcher=dispatcher)
    ctx = _make_ctx()

    await loop.run("hola", ctx)

    roles = [m["role"] for m in ctx.messages]
    assert "user" in roles
    assert "assistant" in roles


@pytest.mark.asyncio
async def test_loop_accumulates_assistant_tokens():
    caller = _make_caller(
        TokenEvent(content="hel"),
        TokenEvent(content="lo"),
        DoneEvent(stop_reason="stop"),
    )
    reg = _make_registry()
    dispatcher = ToolDispatcher()

    loop = AgentLoop(model_caller=caller, tool_registry=reg, tool_dispatcher=dispatcher)
    ctx = _make_ctx()

    await loop.run("hola", ctx)

    assistant_msgs = [m for m in ctx.messages if m["role"] == "assistant"]
    assert any("hello" in m["content"] for m in assistant_msgs)


@pytest.mark.asyncio
async def test_loop_executes_tool_call():
    caller = _make_caller(
        ToolCallEvent(tool_name="echo", tool_input={"text": "mundo"}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    reg = _make_registry(EchoTool())
    dispatcher = ToolDispatcher()

    loop = AgentLoop(model_caller=caller, tool_registry=reg, tool_dispatcher=dispatcher)
    ctx = _make_ctx()

    await loop.run("usa echo", ctx)

    contents = [str(m.get("content", "")) for m in ctx.messages]
    assert any("mundo" in c for c in contents)


@pytest.mark.asyncio
async def test_loop_aborts_on_stop_event():
    stop = asyncio.Event()
    stop.set()

    called = []

    class TrackingCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            called.append(True)
            async def _gen():
                yield DoneEvent(stop_reason="stop")
            return _gen()

    reg = _make_registry()
    dispatcher = ToolDispatcher()
    loop = AgentLoop(model_caller=TrackingCaller(), tool_registry=reg, tool_dispatcher=dispatcher)

    await loop.run("hola", _make_ctx(stop=stop))

    assert called == [], "el modelo no debe llamarse si stop está seteado"


@pytest.mark.asyncio
async def test_loop_handles_error_event():
    caller = _make_caller(ErrorEvent(message="LLM explotó"))
    reg = _make_registry()
    dispatcher = ToolDispatcher()
    loop = AgentLoop(model_caller=caller, tool_registry=reg, tool_dispatcher=dispatcher)

    # No debe lanzar excepción
    await loop.run("hola", _make_ctx())


@pytest.mark.asyncio
async def test_loop_multi_turn_tool_calls():
    """Dos rondas de tool calls antes del DoneEvent final."""
    turn = {"n": 0}

    class MultiTurnCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            turn["n"] += 1
            async def _gen():
                if turn["n"] == 1:
                    yield ToolCallEvent(tool_name="echo", tool_input={"text": "vuelta1"}, call_id="c1")
                    yield DoneEvent(stop_reason="tool_calls")
                else:
                    yield TokenEvent(content="listo")
                    yield DoneEvent(stop_reason="stop")
            return _gen()

    reg = _make_registry(EchoTool())
    dispatcher = ToolDispatcher()
    loop = AgentLoop(model_caller=MultiTurnCaller(), tool_registry=reg, tool_dispatcher=dispatcher)
    ctx = _make_ctx()

    await loop.run("ejecuta dos veces", ctx)

    assert turn["n"] == 2
    contents = " ".join(str(m.get("content", "")) for m in ctx.messages)
    assert "vuelta1" in contents


# ---------------------------------------------------------------------------
# Emisión a EventBus (observación en vivo)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_loop_emits_events_to_bus():
    from agentic_runtime.events import EventBus, ToolResultEvent

    caller = _make_caller(
        TokenEvent(content="hi"),
        ToolCallEvent(tool_name="echo", tool_input={"text": "x"}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    reg = _make_registry(EchoTool())
    dispatcher = ToolDispatcher()
    bus = EventBus()

    seen: list[str] = []

    def _rec(label):
        async def handler(e):
            seen.append(label)
        return handler

    bus.subscribe(TokenEvent, _rec("token"))
    bus.subscribe(ToolCallEvent, _rec("toolcall"))
    bus.subscribe(ToolResultEvent, _rec("toolresult"))
    bus.subscribe(DoneEvent, _rec("done"))

    loop = AgentLoop(
        model_caller=caller, tool_registry=reg,
        tool_dispatcher=dispatcher, event_bus=bus,
    )
    await loop.run("hola", _make_ctx())

    assert "token" in seen
    assert "toolcall" in seen
    assert "toolresult" in seen  # emitido por el loop tras el dispatch
    assert "done" in seen


# ---------------------------------------------------------------------------
# Shim BasicLoop
# ---------------------------------------------------------------------------

def test_basic_loop_is_agent_loop():
    assert BasicLoop is AgentLoop
