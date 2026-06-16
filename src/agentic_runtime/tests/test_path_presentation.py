"""B1 — PathPresentation viva en el choke point único del ToolResult.

Verifica: (1) identidad = no-op; (2) bajo una presentation fake (FS de infra),
ninguna ruta real aparece ni en ctx.messages ni en los eventos emitidos al bus,
porque el dispatcher sanitiza en un único punto que alimenta ambas rutas.
"""
import asyncio
from pathlib import Path


from agentic_runtime.context.presentation import IdentityPresentation
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.storage import PathPresentation
from agentic_runtime.events import DoneEvent, EventBus, ToolCallEvent, ToolResultEvent
from agentic_runtime.loop.agent_loop import AgentLoop
from agentic_runtime.tools import ToolCategory, ToolDispatcher, ToolRegistry, ToolResult
from agentic_runtime.tools.pool import ToolPool


_REAL = "/srv/agents/u42/work/secret.txt"


class PathLeakingTool:
    """Emite una ruta real del host en su output (texto libre)."""

    name = "leak"
    description = "echoes a real host path"
    input_schema: dict = {}
    category = ToolCategory.FILE
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult:
        return ToolResult(tool_name=self.name, output=f"wrote {_REAL}")


class FakePresentation:
    """FS de infra: mapea la raíz real a /workspace en todo texto libre."""

    def to_llm(self, host_path: Path) -> str:
        return str(host_path).replace("/srv/agents/u42", "/workspace")

    def sanitize_output(self, text: str) -> str:
        return text.replace("/srv/agents/u42", "/workspace")


def _dispatcher() -> ToolDispatcher:
    return ToolDispatcher()


def _pool() -> ToolPool:
    # El dispatcher resuelve desde ctx.tool_pool (alineado al canónico).
    return ToolPool(native_tools=[PathLeakingTool()])


def test_identity_is_noop():
    ctx = ToolUseContext(session_id="s1", presentation=IdentityPresentation(), tool_pool=_pool())
    result = asyncio.run(
        _dispatcher().dispatch(tool_name="leak", tool_input={}, ctx=ctx)
    )
    assert result.output == f"wrote {_REAL}"


def test_no_presentation_is_noop():
    ctx = ToolUseContext(session_id="s1", tool_pool=_pool())  # presentation=None
    result = asyncio.run(
        _dispatcher().dispatch(tool_name="leak", tool_input={}, ctx=ctx)
    )
    assert result.output == f"wrote {_REAL}"


def test_fake_presentation_hides_real_path():
    ctx = ToolUseContext(session_id="s1", presentation=FakePresentation(), tool_pool=_pool())
    result = asyncio.run(
        _dispatcher().dispatch(tool_name="leak", tool_input={}, ctx=ctx)
    )
    assert "/srv/agents/u42" not in result.output
    assert result.output == "wrote /workspace/work/secret.txt"


def test_identity_satisfies_protocol():
    assert isinstance(IdentityPresentation(), PathPresentation)
    assert isinstance(FakePresentation(), PathPresentation)


class _ScriptedCaller:
    """Un turno: emite un tool call sobre 'leak', luego termina."""

    async def complete(self, messages, tools, *, stop=None, model_id=""):
        async def _gen():
            yield ToolCallEvent(tool_name="leak", tool_input={}, call_id="c1")
            yield DoneEvent(stop_reason="stop")
        return _gen()


def test_choke_point_covers_messages_and_bus():
    """El único punto de sanitización alimenta ctx.messages Y el EventBus."""
    reg = ToolRegistry()
    reg.register(PathLeakingTool())
    bus = EventBus()
    seen: list[str] = []

    async def _capture(ev: ToolResultEvent) -> None:
        seen.append(ev.result)

    bus.subscribe(ToolResultEvent, _capture)

    ctx = ToolUseContext(session_id="s1", presentation=FakePresentation())
    loop = AgentLoop(
        model_caller=_ScriptedCaller(),
        tool_registry=reg,
        tool_dispatcher=ToolDispatcher(),
        event_bus=bus,
    )
    asyncio.run(loop.run("go", ctx))

    tool_msgs = [m for m in ctx.messages if m.get("role") == "tool"]
    assert tool_msgs and all("/srv/agents/u42" not in m["content"] for m in tool_msgs)
    assert tool_msgs[0]["content"] == "wrote /workspace/work/secret.txt"
    assert seen == ["wrote /workspace/work/secret.txt"]
