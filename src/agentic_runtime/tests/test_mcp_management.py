"""Tests de gestión MCP en runtime (Fase M5).

No hay API HTTP en este repo: la "capa service" que una API /mcp llamaría son métodos
del provider (add/disconnect/remove/reconnect). Actualizan el estado del provider sin
tocar ningún registry nativo; el pool se reensambla por turno (vía el manager).
"""
from agentic_runtime.capabilities.mcp import McpProvider, McpServerConfig, ServerStatus
from agentic_runtime.context.tool_use import ToolUseContext


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


class _FakeClient:
    instances: list["_FakeClient"] = []

    def __init__(self, config: McpServerConfig) -> None:
        self.config = config
        self.closed = False
        _FakeClient.instances.append(self)

    async def connect(self):
        pass

    async def list_tools(self):
        return [{"name": f"{self.config.name}_t"}]

    async def list_resources(self):
        return []

    async def call(self, n, i):
        return "ok"

    async def aclose(self):
        self.closed = True


async def _provider() -> McpProvider:
    _FakeClient.instances = []
    provider = McpProvider(client_factory=_FakeClient)
    provider.add_server("srv", {"command": "run"})
    await provider.connect_server("srv")
    return provider


async def test_add_and_connect_updates_state_only():
    provider = await _provider()
    assert provider.state.connected_servers() == ["srv"]
    assert [t.name for t in provider.tools(_ctx())] == ["srv_t"]


async def test_disconnect_closes_client_keeps_config():
    provider = await _provider()
    await provider.disconnect_server("srv")

    assert _FakeClient.instances[0].closed is True
    assert provider.state.status("srv") is ServerStatus.CONFIGURED  # config conservada
    assert "srv" in provider.state.servers
    assert provider.tools(_ctx()) == []  # sus tools salen del pool
    assert provider.state.get_client("srv") is None


async def test_remove_server_drops_everything():
    provider = await _provider()
    await provider.remove_server("srv")

    assert "srv" not in provider.state.servers
    assert provider.state.status("srv") is None
    assert provider.tools(_ctx()) == []


async def test_reconnect_server_refreshes_client_and_tools():
    provider = await _provider()
    await provider.reconnect_server("srv")

    # nuevo client creado (2 instancias), el viejo cerrado, tools de vuelta
    assert len(_FakeClient.instances) == 2
    assert _FakeClient.instances[0].closed is True
    assert provider.state.status("srv") is ServerStatus.CONNECTED
    assert [t.name for t in provider.tools(_ctx())] == ["srv_t"]
