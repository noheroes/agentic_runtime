"""Primitiva DeferredToolStrategy: rama nativa vs simulada + selección por capability."""
import json

from agentic_runtime.capabilities import CapabilityManager
from agentic_runtime.capabilities.mcp import McpProvider, McpServerConfig
from agentic_runtime.context.tool_use import AppState, ToolUseContext
from agentic_runtime.contracts.permissions import PermissionContext
from agentic_runtime.events import DoneEvent
from agentic_runtime.loop.agent_loop import AgentLoop
from agentic_runtime.tools import ToolCategory, ToolRegistry, ToolResult
from agentic_runtime.tools.deferred import mark_tools_discovered
from agentic_runtime.tools.deferred_strategy import (
    NativeDeferredStrategy,
    SimulatedDeferredStrategy,
)
from agentic_runtime.tools.dispatcher import ToolDispatcher
from agentic_runtime.tools.native import ToolSearchTool
from agentic_runtime.tools.native.tool_search import TOOL_SEARCH_TOOL_NAME


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


async def _pool_with_mcp(ctx: ToolUseContext):
    provider = McpProvider(client_factory=_FakeMcpClient)
    provider.add_server("srv", {"command": "run"})
    await provider.connect_server("srv")
    manager = CapabilityManager([provider])
    ctx.tool_pool = manager.build_tool_pool([_NativeEcho(), ToolSearchTool()], ctx)
    return ctx.tool_pool.assemble(ctx.permission_context)


def _make_caller(*events, native: bool):
    class StubCaller:
        captured: list[dict] = []

        def supports_native_tool_search(self, model_id=""):
            return native

        async def complete(self, messages, tools, *, stop=None, model_id="", **kw):
            StubCaller.captured = list(tools)

            async def _gen():
                for ev in events:
                    yield ev

            return _gen()

    return StubCaller()


# ── Rama simulada (comportamiento vigente) ────────────────────────────────────

async def test_simulated_hides_undiscovered_and_announces_names():
    ctx = _ctx_allowing("drawio_create")
    pool = await _pool_with_mcp(ctx)

    plan = SimulatedDeferredStrategy().prepare_turn(ctx, pool)
    names = {s["name"] for s in plan.tool_schemas}

    assert "echo" in names
    assert TOOL_SEARCH_TOOL_NAME in names          # hay diferidas → ToolSearch visible
    assert "drawio_create" not in names            # oculta hasta descubrir
    assert not any("defer_loading" in s for s in plan.tool_schemas)
    assert plan.announcements and "drawio_create" in plan.announcements[0]
    assert SimulatedDeferredStrategy().owns_search_dispatch() is True


async def test_simulated_discovered_tool_becomes_visible():
    ctx = _ctx_allowing("drawio_create")
    mark_tools_discovered(ctx, ["drawio_create"])
    pool = await _pool_with_mcp(ctx)

    plan = SimulatedDeferredStrategy().prepare_turn(ctx, pool)
    assert "drawio_create" in {s["name"] for s in plan.tool_schemas}


# ── Rama nativa (Responses server-side) ───────────────────────────────────────

async def test_native_includes_all_marks_deferred_and_drops_client_search():
    ctx = _ctx_allowing("drawio_create")
    pool = await _pool_with_mcp(ctx)

    plan = NativeDeferredStrategy().prepare_turn(ctx, pool)
    by_name = {s["name"]: s for s in plan.tool_schemas}

    # todas incluidas sin filtrar; la diferida marcada; la nativa no
    assert by_name["drawio_create"]["defer_loading"] is True
    assert "defer_loading" not in by_name["echo"]
    # el tool_search client-side no se anuncia (el provider añade el suyo server-side)
    assert TOOL_SEARCH_TOOL_NAME not in by_name
    # sin reminder de nombres: la API muestra nombre+descripción vía el flag
    assert plan.announcements == []
    assert NativeDeferredStrategy().owns_search_dispatch() is False


# ── Selección por capability desde el loop ────────────────────────────────────

async def test_loop_selects_native_when_caller_declares_capability():
    provider = McpProvider(client_factory=_FakeMcpClient)
    provider.add_server("srv", {"command": "run"})
    await provider.connect_server("srv")
    manager = CapabilityManager([provider])
    reg = ToolRegistry()
    reg.register(_NativeEcho())
    reg.register(ToolSearchTool())

    caller = _make_caller(DoneEvent(stop_reason="stop"), native=True)
    loop = AgentLoop(
        model_caller=caller, tool_registry=reg, capability_manager=manager,
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _ctx_allowing("drawio_create")
    await loop.run("hola", ctx)

    by_name = {t["name"]: t for t in type(caller).captured}
    assert by_name["drawio_create"]["defer_loading"] is True  # diferida anunciada + marcada
    assert TOOL_SEARCH_TOOL_NAME not in by_name
    # ningún reminder de nombres inyectado
    assert not any(
        m.get("role") == "user" and "now available via ToolSearch" in (m.get("content") or "")
        for m in ctx.messages
    )


async def test_loop_defaults_simulated_without_capability():
    reg = ToolRegistry()
    reg.register(_NativeEcho())
    reg.register(ToolSearchTool())

    class BareCaller:
        captured: list[dict] = []

        async def complete(self, messages, tools, *, stop=None, model_id="", **kw):
            BareCaller.captured = list(tools)

            async def _gen():
                yield DoneEvent(stop_reason="stop")

            return _gen()

    loop = AgentLoop(model_caller=BareCaller(), tool_registry=reg, tool_dispatcher=ToolDispatcher())
    await loop.run("hola", ToolUseContext(session_id="s1"))
    # sin capability declarada → simulada: sin diferidas, ToolSearch oculto
    assert TOOL_SEARCH_TOOL_NAME not in {t["name"] for t in BareCaller.captured}
