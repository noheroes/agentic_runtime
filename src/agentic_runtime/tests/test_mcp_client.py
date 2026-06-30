"""Tests para capabilities/mcp/ — ciclo de vida real de clients (Fase M1).

Foco: connect/discover/call/aclose, estado de conexión (pending/failed/connected),
aislamiento por ítem (un server caído no tumba al resto) y mapeo de isError.
El transporte se inyecta vía `client_factory` (cliente fake) — sin server real.
"""
import httpx
import mcp
import mcp.client.streamable_http as _shttp
import pytest

from agentic_runtime.capabilities.mcp import (
    McpProvider,
    McpServerConfig,
    McpToolError,
    ServerStatus,
    build_mcp_tool,
)
from agentic_runtime.capabilities.mcp.client import McpClient
from agentic_runtime.context.tool_use import ToolUseContext


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


class _FakeClient:
    """Cliente MCP fake — implementa la misma superficie que McpClient sin transporte."""

    def __init__(
        self,
        config: McpServerConfig,
        *,
        tools: list[dict] | None = None,
        resources: list[dict] | None = None,
        fail_on_connect: bool = False,
        tool_error: str | None = None,
    ) -> None:
        self.config = config
        self._tools = tools or []
        self._resources = resources or []
        self._fail = fail_on_connect
        self._tool_error = tool_error
        self.connected = False
        self.closed = False
        self.call_count = 0

    async def connect(self) -> None:
        if self._fail:
            raise RuntimeError("transporte caído")
        self.connected = True

    async def list_tools(self) -> list[dict]:
        return self._tools

    async def list_resources(self) -> list[dict]:
        return self._resources

    async def call(self, tool_name: str, tool_input: dict) -> str:
        self.call_count += 1
        if self._tool_error is not None:
            raise McpToolError(self._tool_error)
        return f"{tool_name}:{tool_input}"

    async def aclose(self) -> None:
        self.closed = True


def _provider_with(**fake_kwargs) -> McpProvider:
    def factory(config: McpServerConfig) -> _FakeClient:
        return _FakeClient(config, **fake_kwargs)

    return McpProvider(client_factory=factory)


# ---------------------------------------------------------------------------
# connect: descubrimiento de tools/resources + estado
# ---------------------------------------------------------------------------

async def test_connect_discovers_tools_and_marks_connected():
    provider = _provider_with(
        tools=[{"name": "alpha", "description": "a"}, {"name": "beta"}],
        resources=[{"uri": "mcp://r"}],
    )
    provider.add_server("srv", {"command": "run"})
    ok = await provider.connect_server("srv")

    assert ok is True
    assert provider.state.status("srv") is ServerStatus.CONNECTED
    tool_names = [t.name for t in provider.tools(_ctx())]
    assert tool_names[:2] == ["alpha", "beta"]  # tools del server como prefijo
    # con resources presentes, el provider añade además las resource tools (M4)
    assert {"ListMcpResources", "ReadMcpResource"} <= set(tool_names)
    assert provider.resources(_ctx()) == [{"uri": "mcp://r", "server": "srv"}]
    assert provider.state.connected_servers() == ["srv"]


async def test_connect_unregistered_server_returns_false():
    provider = _provider_with()
    assert await provider.connect_server("ghost") is False


# ---------------------------------------------------------------------------
# aislamiento por ítem: un server caído no tumba al resto
# ---------------------------------------------------------------------------

async def test_failed_server_is_isolated_and_recorded():
    def factory(config: McpServerConfig) -> _FakeClient:
        fail = config.name == "bad"
        return _FakeClient(config, fail_on_connect=fail, tools=[{"name": f"{config.name}_t"}])

    provider = McpProvider(client_factory=factory)
    provider.add_server("good", {"command": "run"})
    provider.add_server("bad", {"command": "run"})

    await provider.startup()

    assert provider.state.status("good") is ServerStatus.CONNECTED
    assert provider.state.status("bad") is ServerStatus.FAILED
    assert "transporte caído" in provider.state.failed_servers()["bad"]
    # las tools del bueno siguen expuestas; ninguna del malo
    assert [t.name for t in provider.tools(_ctx())] == ["good_t"]


# ---------------------------------------------------------------------------
# call: transporte del client + mapeo de isError
# ---------------------------------------------------------------------------

async def test_tool_call_routes_through_connected_client():
    provider = _provider_with(tools=[{"name": "alpha"}])
    provider.add_server("srv", {"command": "run"})
    await provider.connect_server("srv")

    tool = provider.tools(_ctx())[0]
    result = await tool.execute({"k": "v"}, _ctx())
    assert not result.is_error
    assert result.output.startswith("alpha:")


async def test_tool_is_error_maps_to_error_result_single_call():
    fake = _FakeClient(McpServerConfig(name="s", command="run"), tool_error="boom de tool")
    tool = build_mcp_tool({"name": "t"}, fake.call)

    result = await tool.execute({}, _ctx())
    assert result.is_error
    assert "boom de tool" in result.output
    assert fake.call_count == 1  # no doble llamada en error


# ---------------------------------------------------------------------------
# shutdown: cierra todos los clients
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# connect (streamable HTTP): el httpx.AsyncClient recibe el timeout configurado
# y NO el default de httpx (5s), que mata tools que tardan más (regresión real:
# create_drawio_diagram ~7s daba ReadTimeout en la 2ª llamada del turno).
# ---------------------------------------------------------------------------


def _patch_streamable_transport(monkeypatch) -> dict:
    """Stub del transporte streamable-HTTP que captura el timeout del httpx.AsyncClient,
    evitando server real. Devuelve el dict donde se registra lo capturado."""
    captured: dict = {}

    class _CapturingClient:
        def __init__(self, **kwargs) -> None:
            captured["timeout"] = kwargs.get("timeout")

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

    class _FakeStreams:
        async def __aenter__(self):
            return (object(), object())

        async def __aexit__(self, *exc):
            return False

    class _FakeSession:
        def __init__(self, *a, **k) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def initialize(self):
            return None

    monkeypatch.setattr(httpx, "AsyncClient", _CapturingClient)
    monkeypatch.setattr(_shttp, "streamable_http_client", lambda *a, **k: _FakeStreams())
    monkeypatch.setattr(mcp, "ClientSession", _FakeSession)
    return captured


async def test_streamable_http_uses_configured_timeout(monkeypatch):
    captured = _patch_streamable_transport(monkeypatch)
    cfg = McpServerConfig(name="s", url="http://x/mcp", type="http", timeout_seconds=42.0)
    await McpClient(cfg).connect()
    assert captured["timeout"] == 42.0


async def test_streamable_http_defaults_timeout_above_httpx_5s(monkeypatch):
    captured = _patch_streamable_transport(monkeypatch)
    cfg = McpServerConfig(name="s", url="http://x/mcp", type="http")  # timeout_seconds=None
    await McpClient(cfg).connect()
    # sin config explícita, debe usar el default operativo del provider (30s), nunca
    # quedarse con el default de httpx (5s) que regresa el bug.
    assert captured["timeout"] == 30.0


async def test_shutdown_closes_all_clients():
    clients: list[_FakeClient] = []

    def factory(config: McpServerConfig) -> _FakeClient:
        c = _FakeClient(config, tools=[{"name": "t"}])
        clients.append(c)
        return c

    provider = McpProvider(client_factory=factory)
    provider.add_server("a", {"command": "run"})
    provider.add_server("b", {"command": "run"})
    await provider.startup()
    await provider.shutdown()

    assert all(c.closed for c in clients)
    assert len(clients) == 2
