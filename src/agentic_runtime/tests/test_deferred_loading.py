"""Tests de deferred loading (Fase M3).

Alineado al canónico: las tools MCP son diferidas (no se anuncian hasta que ToolSearch
las descubre), pero SIEMPRE ejecutables desde el pool. ToolSearch descubre (activa) y
devuelve schemas. Deferred es visibilidad, no disponibilidad.
"""
import json

from agentic_runtime.capabilities import CapabilityManager
from agentic_runtime.capabilities.mcp import McpProvider, McpServerConfig
from agentic_runtime.context.tool_use import AppState, ToolUseContext
from agentic_runtime.contracts.permissions import PermissionContext
from agentic_runtime.events import DoneEvent, ToolCallEvent
from agentic_runtime.loop.agent_loop import AgentLoop
from agentic_runtime.tools import ToolCategory, ToolRegistry, ToolResult
from agentic_runtime.tools.deferred import (
    discovered_tool_names,
    is_deferred_tool,
    mark_tools_discovered,
)
from agentic_runtime.tools.dispatcher import ToolDispatcher
from agentic_runtime.tools.native import ToolSearchTool


class _NativeEcho:
    name = "echo"
    description = "native echo"
    input_schema: dict = {}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input, ctx):
        return ToolResult(tool_name=self.name, output="ok")


class _FakeMcpClient:
    def __init__(self, config: McpServerConfig) -> None:
        self.config = config

    async def connect(self):
        pass

    async def list_tools(self):
        return [{"name": "drawio_create", "description": "create a drawio diagram"}]

    async def list_resources(self):
        return []

    async def call(self, tool_name, tool_input):
        return f"drew:{tool_input}"

    async def aclose(self):
        pass


def _ctx_allowing(*names: str) -> ToolUseContext:
    perms = PermissionContext(always_allow_command=list(names))
    return ToolUseContext(session_id="s1", app_state=AppState(permissions=perms))


async def _connected_provider() -> McpProvider:
    provider = McpProvider(client_factory=_FakeMcpClient)
    provider.add_server("srv", {"command": "run"})
    await provider.connect_server("srv")
    return provider


def _make_caller(*events):
    class StubCaller:
        captured: list[dict] = []

        async def complete(self, messages, tools, *, stop=None, model_id=""):
            StubCaller.captured = list(tools)

            async def _gen():
                for ev in events:
                    yield ev

            return _gen()

    return StubCaller()


# ---------------------------------------------------------------------------
# is_deferred_tool
# ---------------------------------------------------------------------------

def test_mcp_tool_is_deferred_native_is_not():
    from agentic_runtime.capabilities.mcp import build_mcp_tool

    async def call(n, i):
        return ""

    assert is_deferred_tool(build_mcp_tool({"name": "x"}, call)) is True
    assert is_deferred_tool(_NativeEcho()) is False
    assert is_deferred_tool(ToolSearchTool()) is False  # nunca diferido


# ---------------------------------------------------------------------------
# Anuncio: diferidas ocultas hasta descubrir; ToolSearch visible solo si hay diferidas
# ---------------------------------------------------------------------------

async def test_deferred_mcp_tool_hidden_until_discovered():
    provider = await _connected_provider()
    manager = CapabilityManager([provider])
    reg = ToolRegistry()
    reg.register(_NativeEcho())
    reg.register(ToolSearchTool())

    caller = _make_caller(DoneEvent(stop_reason="stop"))
    loop = AgentLoop(
        model_caller=caller, tool_registry=reg, capability_manager=manager,
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _ctx_allowing("drawio_create")
    await loop.run("hola", ctx)

    announced = {t["name"] for t in type(caller).captured}
    assert "echo" in announced
    assert "ToolSearch" in announced       # hay diferidas → ToolSearch visible
    assert "drawio_create" not in announced  # diferida no descubierta → oculta


async def test_discovered_deferred_tool_is_announced():
    provider = await _connected_provider()
    manager = CapabilityManager([provider])
    reg = ToolRegistry()
    reg.register(_NativeEcho())
    reg.register(ToolSearchTool())

    caller = _make_caller(DoneEvent(stop_reason="stop"))
    loop = AgentLoop(
        model_caller=caller, tool_registry=reg, capability_manager=manager,
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _ctx_allowing("drawio_create")
    mark_tools_discovered(ctx, ["drawio_create"])  # ya descubierta
    await loop.run("hola", ctx)

    announced = {t["name"] for t in type(caller).captured}
    assert "drawio_create" in announced


async def test_tool_search_hidden_when_no_deferred_tools():
    reg = ToolRegistry()
    reg.register(_NativeEcho())
    reg.register(ToolSearchTool())

    caller = _make_caller(DoneEvent(stop_reason="stop"))
    loop = AgentLoop(
        model_caller=caller, tool_registry=reg,
        tool_dispatcher=ToolDispatcher(),
    )
    await loop.run("hola", ToolUseContext(session_id="s1"))

    announced = {t["name"] for t in type(caller).captured}
    assert "ToolSearch" not in announced  # sin diferidas, nada que buscar


# ---------------------------------------------------------------------------
# ToolSearch descubre (activa) y devuelve schemas
# ---------------------------------------------------------------------------

async def test_tool_search_discovers_and_returns_schema():
    provider = await _connected_provider()
    manager = CapabilityManager([provider])
    ctx = _ctx_allowing("drawio_create")
    ctx.tool_pool = manager.build_tool_pool([ToolSearchTool()], ctx)

    result = await ToolSearchTool().execute({"query": "select:drawio_create"}, ctx)
    payload = json.loads(result.output)

    assert [m["name"] for m in payload["matches"]] == ["drawio_create"]
    assert payload["matches"][0]["description"] == "create a drawio diagram"
    assert payload["total_deferred_tools"] == 1
    # quedó descubierta en el estado del contexto
    assert "drawio_create" in discovered_tool_names(ctx)


async def test_tool_search_keyword_only_matches_deferred():
    provider = await _connected_provider()
    manager = CapabilityManager([provider])
    ctx = _ctx_allowing("drawio_create")
    # native echo en el pool no debe aparecer como match (no es diferida)
    ctx.tool_pool = manager.build_tool_pool([_NativeEcho(), ToolSearchTool()], ctx)

    result = await ToolSearchTool().execute({"query": "diagram"}, ctx)
    names = [m["name"] for m in json.loads(result.output)["matches"]]
    assert names == ["drawio_create"]


# ---------------------------------------------------------------------------
# Ejecución: la diferida es ejecutable desde el pool aun sin anunciar
# ---------------------------------------------------------------------------

async def test_deferred_tool_executable_from_pool_even_if_not_announced():
    provider = await _connected_provider()
    manager = CapabilityManager([provider])
    reg = ToolRegistry()
    reg.register(ToolSearchTool())

    caller = _make_caller(
        ToolCallEvent(tool_name="drawio_create", tool_input={"k": 1}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    loop = AgentLoop(
        model_caller=caller, tool_registry=reg, capability_manager=manager,
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _ctx_allowing("drawio_create")  # permitida pero NO descubierta
    await loop.run("usa drawio", ctx)

    tool_msgs = [m for m in ctx.messages if m.get("role") == "tool"]
    assert tool_msgs and "drew:" in tool_msgs[0]["content"]
