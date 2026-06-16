"""Tests para capabilities/mcp/ — McpProvider shell (Fase M0).

Foco: contrato CapabilityProvider + robustez ante MCP de terceros
(estricto en identidad/seguridad, tolerante en lo operativo, aislamiento por ítem).
"""
import pytest

from agentic_runtime.capabilities import CapabilityManager, CapabilityProvider
from agentic_runtime.capabilities.mcp import (
    McpProvider,
    McpServerConfig,
    build_mcp_tool,
    load_server_configs,
    parse_server_config,
)
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools import ToolCategory, ToolResult


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


async def _echo_call(name: str, input: dict) -> str:
    return f"{name}:{input}"


# ---------------------------------------------------------------------------
# Contrato
# ---------------------------------------------------------------------------

def test_provider_satisfies_capability_protocol():
    assert isinstance(McpProvider(), CapabilityProvider)
    assert McpProvider().name == "mcp"


# ---------------------------------------------------------------------------
# Config: estricta en identidad (borde de seguridad)
# ---------------------------------------------------------------------------

def test_parse_server_config_requires_one_transport():
    with pytest.raises(ValueError):
        parse_server_config("bad", {})  # ni command ni url
    with pytest.raises(ValueError):
        parse_server_config("bad", {"command": "x", "url": "http://y"})  # ambos


def test_add_server_strict_raises_on_invalid():
    provider = McpProvider()
    with pytest.raises(ValueError):
        provider.add_server("bad", {})
    assert "bad" not in provider.state.servers


def test_server_config_open_schema_keeps_unknown_props():
    # props no estándar de un registro de terceros no rompen el parseo
    cfg = parse_server_config("third", {"command": "run", "weird_prop": 42, "model": "x"})
    assert isinstance(cfg, McpServerConfig)
    assert cfg.model == "x"
    assert cfg.model_extra and cfg.model_extra.get("weird_prop") == 42


# ---------------------------------------------------------------------------
# Config: tolerante en bloque (aislamiento por ítem)
# ---------------------------------------------------------------------------

def test_load_servers_skips_invalid_keeps_valid():
    provider = McpProvider()
    configs = provider.load_servers({
        "good": {"command": "run"},
        "bad": {},  # inválido → se salta con log
        "good2": {"url": "http://x"},
    })
    names = {c.name for c in configs}
    assert names == {"good", "good2"}
    assert set(provider.state.servers) == {"good", "good2"}


def test_load_server_configs_pure_function_tolerant():
    configs = load_server_configs({"a": {"command": "x"}, "b": {"command": "x", "url": "y"}})
    assert [c.name for c in configs] == ["a"]


# ---------------------------------------------------------------------------
# Tool adapter: tolerante con annotations opcionales
# ---------------------------------------------------------------------------

def test_build_mcp_tool_skips_spec_without_name():
    assert build_mcp_tool({}, _echo_call, server_name="s") is None
    assert build_mcp_tool({"name": 123}, _echo_call) is None  # name no string


def test_build_mcp_tool_defaults_when_annotations_absent():
    tool = build_mcp_tool({"name": "t"}, _echo_call)
    assert tool is not None
    assert tool.description == ""
    assert tool.input_schema == {}
    # tercero no anotado: requiere permiso, no safe_for_background
    assert tool.requires_permission is True
    assert tool.safe_for_background is False


def test_build_mcp_tool_read_only_hint_enables_background():
    tool = build_mcp_tool(
        {"name": "t", "annotations": {"readOnlyHint": True}},
        _echo_call,
    )
    assert tool is not None
    assert tool.safe_for_background is True


def test_build_mcp_tool_malformed_input_schema_degrades():
    tool = build_mcp_tool({"name": "t", "inputSchema": "not-a-dict"}, _echo_call)
    assert tool is not None and tool.input_schema == {}


@pytest.mark.asyncio
async def test_mcp_tool_execute_calls_injected_transport():
    tool = build_mcp_tool({"name": "t"}, _echo_call)
    result = await tool.execute({"k": "v"}, _ctx())
    assert not result.is_error
    assert result.output.startswith("t:")


@pytest.mark.asyncio
async def test_mcp_tool_execute_wraps_transport_error():
    async def boom(name, input):
        raise RuntimeError("down")

    tool = build_mcp_tool({"name": "t"}, boom)
    result = await tool.execute({}, _ctx())
    assert result.is_error
    assert "down" in result.output


# ---------------------------------------------------------------------------
# Provider: tools / catalog / resources / aislamiento
# ---------------------------------------------------------------------------

def test_register_tools_skips_malformed_and_exposes_rest():
    provider = McpProvider()
    provider.add_server("srv", {"command": "run"})
    provider.register_tools_from_specs(
        "srv",
        [{"name": "ok"}, {"no_name": True}, {"name": "ok2"}],
        _echo_call,
    )
    names = [t.name for t in provider.tools(_ctx())]
    assert names == ["ok", "ok2"]


def test_catalog_emits_mcp_tool_summaries():
    provider = McpProvider()
    provider.add_server("srv", {"command": "run"})
    provider.register_tools_from_specs("srv", [{"name": "ok", "description": "d"}], _echo_call)
    catalog = provider.catalog(_ctx())
    assert len(catalog) == 1
    assert catalog[0].kind == "mcp_tool"
    assert catalog[0].provider == "mcp"
    assert catalog[0].description == "d"


def test_resources_exposed_from_state():
    provider = McpProvider()
    provider.add_server("srv", {"command": "run"})
    provider.register_resources("srv", [{"uri": "mcp://x"}])
    assert provider.resources(_ctx()) == [{"uri": "mcp://x", "server": "srv"}]


def test_provider_uses_server_timeout_for_tools():
    provider = McpProvider()
    provider.add_server("srv", {"command": "run", "timeout_seconds": 99.0})
    provider.register_tools_from_specs("srv", [{"name": "ok"}], _echo_call)
    assert provider.tools(_ctx())[0].timeout_seconds == 99.0


# ---------------------------------------------------------------------------
# Convergencia con C0: las tools MCP fluyen por el manager
# ---------------------------------------------------------------------------

class _NativeTool:
    name = "read"
    description = "native"
    input_schema: dict = {}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input, ctx):
        return ToolResult(tool_name=self.name, output="ok")


def test_mcp_tools_converge_through_capability_manager():
    provider = McpProvider()
    provider.add_server("srv", {"command": "run"})
    provider.register_tools_from_specs("srv", [{"name": "mcp_x"}], _echo_call)

    mgr = CapabilityManager([provider])
    pool = mgr.build_tool_pool([_NativeTool()], _ctx())
    assembled = [t.name for t in pool.assemble()]

    # native como prefijo, mcp después (paridad con assembleToolPool)
    assert assembled == ["read", "mcp_x"]
