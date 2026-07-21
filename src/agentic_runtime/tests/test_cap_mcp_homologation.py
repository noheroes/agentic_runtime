"""Homologación 11·capabilities/mcp — provider/client/config/scope/auth/tool_adapter/resources
vs el core MCP canónico (`services/mcp/{client,config,auth,types,utils,mcpStringUtils,envExpansion}.ts`,
`tools/{MCPTool,McpAuthTool,*McpResource*}`).

Los tests que PASAN codifican el comportamiento YA homologado (transportes/inferencia, validación
estricta identidad+auth, precedencia/exclusividad/mutabilidad de scope, merge, carga tolerante,
`McpToolError` envuelto sin re-llamar, reconcile datos-puros, resource tools condicionales, herencia
en fork). Los `xfail(strict=True)` codifican los gaps FIND-MCP: fallan HOY (comportamiento homologado
ausente) y su fallo ES la evidencia del gap. Si alguno empezara a pasar, el strict lo vuelve error →
señal de reclasificar el estado en 11-cap-mcp.md.
"""
from __future__ import annotations

import asyncio

import pytest

from agentic_runtime.capabilities.mcp.config import (
    McpServerConfig,
    load_server_configs,
    parse_server_config,
)
from agentic_runtime.capabilities.mcp.provider import McpProvider
from agentic_runtime.capabilities.mcp.reconcile import ReconcilePlan, plan_reconcile
from agentic_runtime.capabilities.mcp.resource_tools import ReadMcpResourceTool
from agentic_runtime.capabilities.mcp.scope import (
    EXCLUSIVE_SCOPES,
    MUTABLE_SCOPES,
    McpScope,
    ScopedConfig,
    assert_mutable,
    is_mutable,
    merge_scoped,
)
from agentic_runtime.capabilities.mcp.state import McpState, ServerStatus
from agentic_runtime.capabilities.mcp.tool_adapter import build_mcp_tool
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools.deferred import is_deferred_tool


def _ctx(**kw) -> ToolUseContext:
    return ToolUseContext(session_id="s1", stop=asyncio.Event(), **kw)


async def _call_ok(tool_name: str, tool_input: dict) -> str:  # McpCall de prueba
    return "output"


# ===========================================================================
# A · Config e identidad — lo homologado (PASA)
# ===========================================================================

def test_transport_inference():
    """A: command→stdio, url→http, type explícito respetado."""
    assert McpServerConfig(name="a", command="x").resolved_transport() == "stdio"
    assert McpServerConfig(name="b", url="https://h/mcp").resolved_transport() == "http"
    assert McpServerConfig(name="c", type="sse", url="https://h/sse").resolved_transport() == "sse"


def test_bearer_requires_token_and_not_on_stdio():
    """A: bearer sin token y auth HTTP en stdio son bordes de seguridad → rechazados."""
    with pytest.raises(ValueError):
        parse_server_config("a", {"url": "https://h", "auth": "bearer"})
    with pytest.raises(ValueError):
        parse_server_config("b", {"command": "x", "auth": "bearer", "token": "t"})


def test_bearer_auth_headers():
    """A: bearer compone Authorization junto a los headers explícitos."""
    cfg = McpServerConfig(name="a", url="https://h", auth="bearer", token="tok", headers={"X": "1"})
    hdrs = cfg.auth_headers()
    assert hdrs["Authorization"] == "Bearer tok"
    assert hdrs["X"] == "1"


def test_load_servers_tolerant():
    """A: carga en bloque aísla por ítem — inválido se salta, válidos cargan."""
    configs = load_server_configs({
        "good": {"command": "run"},
        "bad": {"auth": "bearer", "url": "https://h"},  # bearer sin token
    })
    assert [c.name for c in configs] == ["good"]


# ===========================================================================
# B · Scope / precedencia / mutabilidad — lo homologado (PASA)
# ===========================================================================

def test_scope_precedence_and_exclusivity():
    """B: enterprise exclusivo suprime a los demás; sin él, precedencia por nombre."""
    merged = merge_scoped({
        McpScope.USER: {"s": {"command": "u"}},
        McpScope.LOCAL: {"s": {"command": "l"}},
    })
    assert merged["s"].scope is McpScope.LOCAL  # local > user

    merged2 = merge_scoped({
        McpScope.USER: {"s": {"command": "u"}, "only_user": {"command": "x"}},
        McpScope.ENTERPRISE: {"s": {"command": "e"}},
    })
    assert set(merged2) == {"s"}  # enterprise exclusivo → user descartado
    assert merged2["s"].scope is McpScope.ENTERPRISE


def test_scope_mutability_gate():
    """B: sólo user/project/local mutables; managed/enterprise/claudeai/dynamic read-only."""
    assert MUTABLE_SCOPES == frozenset({McpScope.USER, McpScope.PROJECT, McpScope.LOCAL})
    assert EXCLUSIVE_SCOPES == frozenset({McpScope.ENTERPRISE})
    assert is_mutable(McpScope.USER) is True
    for ro in (McpScope.MANAGED, McpScope.ENTERPRISE, McpScope.CLAUDEAI, McpScope.DYNAMIC):
        assert is_mutable(ro) is False
        with pytest.raises(ValueError):
            assert_mutable(ro)


# ===========================================================================
# C · Reconcile datos-puros — lo homologado (PASA)
# ===========================================================================

def test_reconcile_plan():
    """C: diff deseado-vs-vivo → connect/disconnect/refresh; disabled deseado no-conectado."""
    desired = {
        "new": McpServerConfig(name="new", command="a"),
        "same": McpServerConfig(name="same", command="b"),
        "changed": McpServerConfig(name="changed", command="c2"),
        "off": McpServerConfig(name="off", command="d", enabled=False),
    }
    live = {
        "same": McpServerConfig(name="same", command="b"),
        "changed": McpServerConfig(name="changed", command="c1"),
        "off": McpServerConfig(name="off", command="d"),
        "gone": McpServerConfig(name="gone", command="e"),
    }
    plan = plan_reconcile(desired, live)
    assert plan.to_connect == ("new",)
    assert plan.to_refresh == ("changed",)
    assert set(plan.to_disconnect) == {"off", "gone"}
    assert ReconcilePlan((), (), ()).is_empty is True


# ===========================================================================
# D · Adapter + McpToolError — lo homologado (PASA)
# ===========================================================================

def test_build_mcp_tool_tolerant_and_readonly_bg():
    """D: sin name → omitida; readOnlyHint → safe_for_background; requiere permiso siempre."""
    assert build_mcp_tool({"description": "x"}, _call_ok, server_name="s") is None
    t = build_mcp_tool(
        {"name": "read", "annotations": {"readOnlyHint": True}}, _call_ok, server_name="s"
    )
    assert t is not None
    assert t.requires_permission is True
    assert t.safe_for_background is True


def test_mcp_tool_error_wrapped_without_recall():
    """D: isError del server → McpToolError → ToolResult.error, sin segunda llamada."""
    from agentic_runtime.capabilities.mcp.client import McpToolError

    calls = {"n": 0}

    async def call_iserror(name: str, inp: dict) -> str:
        calls["n"] += 1
        raise McpToolError("boom")

    tool = build_mcp_tool({"name": "t"}, call_iserror, server_name="s")
    res = asyncio.run(tool.execute({}, _ctx()))
    assert res.is_error
    assert "boom" in res.output
    assert calls["n"] == 1


def test_resource_tools_only_when_resources_present():
    """D: las special tools se exponen sólo si hay resources descubiertos."""
    state = McpState()
    prov = McpProvider(state)
    assert prov.tools(_ctx()) == []
    state.set_server(McpServerConfig(name="s", command="x"))
    state.set_resources("s", [{"uri": "u://1", "name": "r"}])
    names = {t.name for t in prov.tools(_ctx())}
    assert {"ListMcpResources", "ReadMcpResource"} <= names


# ===========================================================================
# xfail — gaps FIND-MCP (fallan HOY; el fallo ES la evidencia)
# ===========================================================================

@pytest.mark.xfail(strict=True, reason="FIND-MCP1: tool sin naming mcp__<server>__<tool>")
def test_mcp_tool_name_fully_qualified():
    t = build_mcp_tool({"name": "commit"}, _call_ok, server_name="git")
    assert t.name == "mcp__git__commit"
    assert getattr(t, "mcp_info", None) == {"server_name": "git", "tool_name": "commit"}


@pytest.mark.xfail(strict=True, reason="FIND-MCP1: nombre con chars inválidos no normalizado")
def test_mcp_tool_name_normalized():
    t = build_mcp_tool({"name": "do.it"}, _call_ok, server_name="my server")
    assert t.name == "mcp__my_server__do_it"


@pytest.mark.xfail(strict=True, reason="FIND-MCP2: adapter setea deferred=True a mano, sin is_mcp")
def test_mcp_tool_has_is_mcp_flag():
    t = build_mcp_tool({"name": "t"}, _call_ok, server_name="s")
    assert getattr(t, "is_mcp", False) is True


@pytest.mark.xfail(strict=True, reason="FIND-MCP2/GAP-MCP1: is_deferred_tool sin precedencia is_mcp")
def test_is_deferred_precedence_is_mcp_and_always_load():
    class _T:
        name = "mcp__s__t"
        is_mcp = True
        # sin `deferred` explícito: hoy is_deferred_tool devuelve False
    assert is_deferred_tool(_T()) is True

    class _A:
        name = "mcp__s__t"
        is_mcp = True
        always_load = True  # opt-out gana primero
    assert is_deferred_tool(_A()) is False


@pytest.mark.xfail(strict=True, reason="FIND-MCP3: annotations parciales (sólo readOnlyHint→bg)")
def test_mcp_annotations_full_mapping():
    t = build_mcp_tool(
        {"name": "t", "annotations": {"destructiveHint": True, "openWorldHint": True}},
        _call_ok,
        server_name="s",
    )
    assert getattr(t, "is_destructive", False) is True
    assert getattr(t, "is_open_world", False) is True


@pytest.mark.xfail(strict=True, reason="FIND-MCP4: sin estado NEEDS_AUTH")
def test_server_status_needs_auth_exists():
    assert getattr(ServerStatus, "NEEDS_AUTH", None) is not None
    assert getattr(ServerStatus, "DISABLED", None) is not None


@pytest.mark.xfail(strict=True, reason="FIND-MCP13: sin expansión de env vars en config")
def test_mcp_env_var_expansion(monkeypatch):
    monkeypatch.setenv("MCP_BASE", "https://host")
    cfg = parse_server_config("s", {"url": "${MCP_BASE}/mcp"})
    assert cfg.url == "https://host/mcp"


@pytest.mark.xfail(strict=True, reason="FIND-MCP13: sin default ${VAR:-x} en config")
def test_mcp_env_var_default():
    cfg = parse_server_config("s", {"url": "${MCP_MISSING:-https://fallback}/mcp"})
    assert cfg.url == "https://fallback/mcp"


@pytest.mark.xfail(strict=True, reason="FIND-MCP8: timeout de tool-call 30s vs efectivamente-infinito")
def test_mcp_tool_call_timeout_effectively_infinite():
    t = build_mcp_tool({"name": "t"}, _call_ok, server_name="s")
    assert t.timeout_seconds >= 86_400  # ~1 día; el canónico ~27.8h


@pytest.mark.xfail(strict=True, reason="FIND-MCP6/7: sin cap de tamaño de resultado (maxResultSizeChars)")
def test_mcp_tool_max_result_size():
    t = build_mcp_tool({"name": "t"}, _call_ok, server_name="s")
    assert getattr(t, "max_result_size_chars", None) == 100_000


@pytest.mark.xfail(strict=True, reason="FIND-MCP12: capabilities/instructions no capturados en el estado")
def test_mcp_state_captures_capabilities():
    state = McpState()
    assert hasattr(state, "set_capabilities") and hasattr(state, "server_instructions")


@pytest.mark.xfail(strict=True, reason="FIND-MCP14: sin módulo de política allow/deny")
def test_mcp_policy_module_exists():
    from agentic_runtime.capabilities.mcp import policy  # noqa: F401

    assert hasattr(policy, "is_server_allowed")


@pytest.mark.xfail(strict=True, reason="FIND-MCP17: ReadMcpResource con server opcional (canónico: requerido)")
def test_read_mcp_resource_requires_server():
    required = ReadMcpResourceTool.input_schema.get("required", [])
    assert "server" in required


@pytest.mark.xfail(strict=True, reason="FIND-MCP17: resource tools no diferidas (canónico shouldDefer)")
def test_mcp_resource_tools_deferred():
    state = McpState()
    state.set_server(McpServerConfig(name="s", command="x"))
    state.set_resources("s", [{"uri": "u://1", "name": "r"}])
    tools = McpProvider(state).tools(_ctx())
    read = next(t for t in tools if t.name == "ReadMcpResource")
    assert is_deferred_tool(read) is True


# --- findings destapados en la re-auditoría (MCP21-24) ---

@pytest.mark.xfail(strict=True, reason="FIND-MCP21: sin refresh por notificación *_list_changed")
def test_mcp_provider_refreshes_on_list_changed():
    prov = McpProvider(McpState())
    # el provider debe exponer un callback de refresh por categoría para los
    # notification handlers de list_changed (tools/prompts/resources)
    assert hasattr(prov, "on_list_changed")


@pytest.mark.xfail(strict=True, reason="FIND-MCP22: sin dedup por firma de config")
def test_mcp_dedup_by_signature():
    from agentic_runtime.capabilities.mcp.config import server_signature  # noqa: F401

    a = McpServerConfig(name="a", url="https://h/mcp")
    b = McpServerConfig(name="b", url="https://h/mcp")  # misma URL → mismo server
    assert server_signature(a) == server_signature(b)


@pytest.mark.xfail(strict=True, reason="FIND-MCP23: reconcile desconecta ausentes de cualquier scope")
def test_reconcile_keeps_absent_user_server():
    desired: dict = {}
    live = {"u": McpServerConfig(name="u", command="x")}
    # con procedencia user, un server ausente NO debe desconectarse (sólo dynamic)
    plan = plan_reconcile(desired, live, scope_of={"u": McpScope.USER})
    assert "u" not in plan.to_disconnect


@pytest.mark.xfail(strict=True, reason="FIND-MCP24: sin campo headers_helper")
def test_mcp_headers_helper_field():
    assert "headers_helper" in McpServerConfig.model_fields
