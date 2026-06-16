"""Tests de MCP resources como tools del provider (Fase M4).

Las resource tools (ListMcpResources/ReadMcpResource) acceden al McpState, no a un
loader global. Se exponen solo si hay resources, y fluyen por el pool (no nativas).
"""
from agentic_runtime.capabilities.mcp import (
    ListMcpResourcesTool,
    McpProvider,
    McpServerConfig,
    ReadMcpResourceTool,
)
from agentic_runtime.context.tool_use import ToolUseContext


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


class _ClientWithResources:
    def __init__(self, config: McpServerConfig) -> None:
        self.config = config

    async def connect(self):
        pass

    async def list_tools(self):
        return [{"name": "do_thing"}]

    async def list_resources(self):
        return [{"uri": "mcp://docs/readme", "name": "readme"}]

    async def call(self, tool_name, tool_input):
        return "ok"

    async def read_resource(self, uri):
        return f"contents-of:{uri}"

    async def aclose(self):
        pass


class _ClientNoResources(_ClientWithResources):
    async def list_resources(self):
        return []


async def _provider(client_cls) -> McpProvider:
    provider = McpProvider(client_factory=client_cls)
    provider.add_server("srv", {"command": "run"})
    await provider.connect_server("srv")
    return provider


# ---------------------------------------------------------------------------
# Exposición condicional
# ---------------------------------------------------------------------------

async def test_resource_tools_exposed_when_resources_present():
    provider = await _provider(_ClientWithResources)
    names = [t.name for t in provider.tools(_ctx())]
    assert "do_thing" in names
    assert "ListMcpResources" in names
    assert "ReadMcpResource" in names


async def test_resource_tools_absent_when_no_resources():
    provider = await _provider(_ClientNoResources)
    names = [t.name for t in provider.tools(_ctx())]
    assert "ListMcpResources" not in names
    assert "ReadMcpResource" not in names


# ---------------------------------------------------------------------------
# Ejecución de las resource tools (vía estado/clients, sin loader global)
# ---------------------------------------------------------------------------

async def test_list_resources_tool_returns_state_resources():
    provider = await _provider(_ClientWithResources)
    tool = ListMcpResourcesTool(provider.state)
    result = await tool.execute({}, _ctx())
    import json

    resources = json.loads(result.output)["resources"]
    assert resources[0]["uri"] == "mcp://docs/readme"
    assert resources[0]["server"] == "srv"


async def test_read_resource_tool_routes_to_owning_client():
    provider = await _provider(_ClientWithResources)
    tool = ReadMcpResourceTool(provider.state)
    result = await tool.execute({"uri": "mcp://docs/readme"}, _ctx())
    assert not result.is_error
    assert result.output == "contents-of:mcp://docs/readme"


async def test_read_resource_unknown_uri_errors():
    provider = await _provider(_ClientWithResources)
    tool = ReadMcpResourceTool(provider.state)
    result = await tool.execute({"uri": "mcp://nope"}, _ctx())
    assert result.is_error


# ---------------------------------------------------------------------------
# No son diferidas: se anuncian (a diferencia de las tools MCP)
# ---------------------------------------------------------------------------

def test_resource_tools_not_deferred():
    from agentic_runtime.capabilities.mcp.state import McpState
    from agentic_runtime.tools.deferred import is_deferred_tool

    state = McpState()
    assert is_deferred_tool(ListMcpResourcesTool(state)) is False
    assert is_deferred_tool(ReadMcpResourceTool(state)) is False
