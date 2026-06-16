"""Tests del cableado capability ↔ runtime (M2 / fases C).

Alineado al canónico: el loop ensambla UN pool por turno (native + capability) en
ctx.tool_pool, deriva los schemas de él y el dispatcher ejecuta desde el MISMO pool
(findToolByName). Verifica que una tool de capability (MCP/skill) se anuncia Y se
ejecuta en un turno real, sin registrarla en el ToolRegistry nativo.
"""
from agentic_runtime.capabilities import CapabilityManager
from agentic_runtime.capabilities.mcp import McpProvider, McpServerConfig
from agentic_runtime.context.tool_use import AppState, ToolUseContext
from agentic_runtime.contracts.permissions import PermissionContext
from agentic_runtime.events import DoneEvent, ToolCallEvent
from agentic_runtime.factory import CapabilitiesConfig, RuntimeConfig, create_runtime
from agentic_runtime.loop.agent_loop import AgentLoop
from agentic_runtime.tools import ToolCategory, ToolRegistry, ToolResult
from agentic_runtime.tools.dispatcher import ToolDispatcher


def _ctx_allowing(*names: str) -> ToolUseContext:
    # Las tools MCP requieren permiso (no confiables); el integrador las concede.
    perms = PermissionContext(always_allow_command=list(names))
    return ToolUseContext(session_id="s1", app_state=AppState(permissions=perms))


class _NativeEcho:
    name = "echo"
    description = "native echo"
    input_schema: dict = {"type": "object", "properties": {}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input, ctx):
        return ToolResult(tool_name=self.name, output="native-ok")


class _FakeMcpClient:
    def __init__(self, config: McpServerConfig) -> None:
        self.config = config

    async def connect(self) -> None:
        pass

    async def list_tools(self) -> list[dict]:
        return [{"name": "mcp_ping", "description": "ping via mcp"}]

    async def list_resources(self) -> list[dict]:
        return []

    async def call(self, tool_name: str, tool_input: dict) -> str:
        return f"pong:{tool_input}"

    async def aclose(self) -> None:
        pass


def _make_caller(*events):
    class StubCaller:
        captured_tools: list[dict] = []

        async def complete(self, messages, tools, *, stop=None, model_id=""):
            StubCaller.captured_tools = list(tools)

            async def _gen():
                for ev in events:
                    yield ev

            return _gen()

    return StubCaller()


# ---------------------------------------------------------------------------
# Loop: pool ensamblado native + capability, anuncio + ejecución
# ---------------------------------------------------------------------------

async def _connected_mcp_provider() -> McpProvider:
    provider = McpProvider(client_factory=_FakeMcpClient)
    provider.add_server("srv", {"command": "run"})
    await provider.connect_server("srv")
    return provider


async def test_loop_assembles_native_plus_capability_pool_and_announces():
    provider = await _connected_mcp_provider()
    manager = CapabilityManager([provider])
    reg = ToolRegistry()
    reg.register(_NativeEcho())

    caller = _make_caller(DoneEvent(stop_reason="stop"))
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=reg,
        capability_manager=manager,
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _ctx_allowing("mcp_ping")
    await loop.run("hola", ctx)

    announced = {t["name"] for t in type(caller).captured_tools}
    # native como prefijo + capability anunciada en el mismo pool
    assert "echo" in announced
    assert "mcp_ping" in announced
    # y el pool del ctx quedó poblado con ambas
    pool_names = {t.name for t in ctx.tool_pool.assemble()}
    assert {"echo", "mcp_ping"} <= pool_names


async def test_loop_executes_capability_tool_from_pool():
    provider = await _connected_mcp_provider()
    manager = CapabilityManager([provider])
    reg = ToolRegistry()  # registry nativo VACÍO — la tool MCP no vive aquí

    caller = _make_caller(
        ToolCallEvent(tool_name="mcp_ping", tool_input={"x": 1}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=reg,
        capability_manager=manager,
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _ctx_allowing("mcp_ping")
    await loop.run("usa mcp", ctx)

    tool_msgs = [m for m in ctx.messages if m.get("role") == "tool"]
    assert tool_msgs and "pong:" in tool_msgs[0]["content"]


# ---------------------------------------------------------------------------
# Factory: registra providers y expone lifecycle; ejecución end-to-end
# ---------------------------------------------------------------------------

def test_factory_builds_runtime_with_capability_manager(tmp_path):
    config = RuntimeConfig(
        capabilities=CapabilitiesConfig(mcp_servers={"srv": {"command": "run"}}),
    )
    config.storage.root = tmp_path
    runtime = create_runtime(config=config)

    mgr = runtime._capability_manager
    assert mgr is not None
    # el provider MCP quedó registrado con su server (sin conectar aún)
    mcp = [p for p in mgr.providers if p.name == "mcp"][0]
    assert "srv" in mcp.state.servers


async def test_runtime_startup_connects_capability_providers(tmp_path):
    provider = McpProvider(client_factory=_FakeMcpClient)
    provider.add_server("srv", {"command": "run"})

    config = RuntimeConfig(capabilities=CapabilitiesConfig(extra_providers=[provider]))
    config.storage.root = tmp_path
    # inyectamos el manager ya construido vía extra_providers → factory lo registra
    runtime = create_runtime(config=config)
    await runtime.startup()

    mcp = [p for p in runtime._capability_manager.providers if p.name == "mcp"][0]
    assert mcp.state.connected_servers() == ["srv"]
    await runtime.shutdown()
