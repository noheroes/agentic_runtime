"""Tests para capabilities/manager.py — CapabilityManager (Fase C0)."""
import pytest

from agentic_runtime.capabilities import (
    CapabilityManager,
    CapabilityProvider,
    CapabilitySummary,
)
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.permissions import PermissionContext
from agentic_runtime.tools import ToolCategory, ToolPool, ToolResult


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

class _StubTool:
    def __init__(self, name: str) -> None:
        self.name = name
        self.description = name
        self.input_schema: dict = {}
        self.category = ToolCategory.UTILITY
        self.requires_permission = False
        self.safe_for_background = True
        self.timeout_seconds = 5.0

    async def execute(self, input, ctx):
        return ToolResult(tool_name=self.name, output="ok")


class StubProvider:
    """Provider de prueba que cumple el protocolo CapabilityProvider."""

    def __init__(
        self,
        name: str,
        *,
        tools: list | None = None,
        summaries: list[CapabilitySummary] | None = None,
        active: list[dict] | None = None,
        compact: list[dict] | None = None,
    ) -> None:
        self.name = name
        self._tools = tools or []
        self._summaries = summaries or []
        self._active = active or []
        self._compact = compact or []
        self.started = False
        self.stopped = False

    async def startup(self) -> None:
        self.started = True

    async def shutdown(self) -> None:
        self.stopped = True

    def catalog(self, context):
        return list(self._summaries)

    def tools(self, context):
        return list(self._tools)

    def active_context(self, context):
        return list(self._active)

    def compact_context(self, context):
        return list(self._compact)


def _ctx(agent_id=None) -> ToolUseContext:
    return ToolUseContext(session_id="s1", agent_id=agent_id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_stub_provider_satisfies_protocol():
    assert isinstance(StubProvider("a"), CapabilityProvider)


def test_tools_union_without_duplicates():
    p1 = StubProvider("p1", tools=[_StubTool("alpha"), _StubTool("shared")])
    p2 = StubProvider("p2", tools=[_StubTool("shared"), _StubTool("beta")])
    mgr = CapabilityManager([p1, p2])

    names = [t.name for t in mgr.tools(_ctx())]

    # union sin duplicados; primera aparición gana (orden de registro)
    assert names == ["alpha", "shared", "beta"]


def test_tools_with_provider_without_tools():
    p1 = StubProvider("p1", tools=[_StubTool("alpha")])
    p2 = StubProvider("p2")  # no expone tools
    mgr = CapabilityManager([p1, p2])

    names = [t.name for t in mgr.tools(_ctx())]

    assert names == ["alpha"]


def test_catalog_includes_all_providers():
    p1 = StubProvider("p1", summaries=[CapabilitySummary(name="s1", kind="skill")])
    p2 = StubProvider("p2", summaries=[CapabilitySummary(name="m1", kind="mcp_tool")])
    mgr = CapabilityManager([p1, p2])

    entries = mgr.catalog(_ctx())

    assert [e.name for e in entries] == ["s1", "m1"]


def test_compact_context_concatenates_in_registration_order():
    p1 = StubProvider("p1", compact=[{"role": "user", "content": "p1"}])
    p2 = StubProvider("p2", compact=[{"role": "user", "content": "p2"}])
    mgr = CapabilityManager()
    mgr.register(p1)
    mgr.register(p2)

    messages = mgr.compact_context(_ctx())

    assert [m["content"] for m in messages] == ["p1", "p2"]


def test_no_provider_fails_with_agent_id_none():
    p1 = StubProvider("p1", tools=[_StubTool("alpha")], summaries=[CapabilitySummary(name="s1", kind="skill")])
    mgr = CapabilityManager([p1])

    ctx = _ctx(agent_id=None)  # agente principal

    assert mgr.tools(ctx)
    assert mgr.catalog(ctx)
    assert mgr.active_context(ctx) == []
    assert mgr.compact_context(ctx) == []


@pytest.mark.asyncio
async def test_startup_and_shutdown_iterate_providers():
    p1 = StubProvider("p1")
    p2 = StubProvider("p2")
    mgr = CapabilityManager([p1, p2])

    await mgr.startup()
    await mgr.shutdown()

    assert p1.started and p2.started
    assert p1.stopped and p2.stopped


# ---------------------------------------------------------------------------
# Convergencia native + capability (paridad con assembleToolPool del canónico)
# ---------------------------------------------------------------------------

def test_build_tool_pool_partitions_native_and_capability():
    mgr = CapabilityManager([
        StubProvider("mcp", tools=[_StubTool("zeta_mcp"), _StubTool("alpha_mcp")]),
    ])
    native = [_StubTool("read"), _StubTool("bash")]

    pool = mgr.build_tool_pool(native, _ctx())

    assert isinstance(pool, ToolPool)
    assert [t.name for t in pool.native_tools] == ["read", "bash"]
    assert [t.name for t in pool.capability_tools] == ["zeta_mcp", "alpha_mcp"]


def test_converged_pool_keeps_native_as_contiguous_prefix():
    # invariante de prompt-cache del canónico: built-ins ordenadas primero, capability después
    mgr = CapabilityManager([
        StubProvider("mcp", tools=[_StubTool("aaa_mcp"), _StubTool("zzz_mcp")]),
    ])
    native = [_StubTool("read"), _StubTool("bash")]

    assembled = mgr.build_tool_pool(native, _ctx()).assemble()

    names = [t.name for t in assembled]
    # native (orden alfabético) como prefijo contiguo, luego capability (orden alfabético)
    assert names == ["bash", "read", "aaa_mcp", "zzz_mcp"]


def test_converged_pool_native_wins_on_name_collision():
    # dedup por nombre: la nativa gana sobre la capability con el mismo nombre
    native_read = _StubTool("read")
    cap_read = _StubTool("read")
    mgr = CapabilityManager([StubProvider("mcp", tools=[cap_read])])

    assembled = mgr.build_tool_pool([native_read], _ctx()).assemble()

    reads = [t for t in assembled if t.name == "read"]
    assert len(reads) == 1
    assert reads[0] is native_read


def test_converged_pool_applies_deny_to_both_partitions():
    mgr = CapabilityManager([
        StubProvider("mcp", tools=[_StubTool("denied_mcp"), _StubTool("ok_mcp")]),
    ])
    native = [_StubTool("denied_native"), _StubTool("ok_native")]
    perms = PermissionContext(always_deny=["denied_native", "denied_mcp"])

    assembled = mgr.build_tool_pool(native, _ctx()).assemble(perms)

    names = {t.name for t in assembled}
    assert names == {"ok_native", "ok_mcp"}


def test_manager_does_not_import_concrete_providers():
    # El manager coordina por contrato; no debe importar Skills/Mcp providers.
    import inspect

    import agentic_runtime.capabilities.manager as manager_module

    source = inspect.getsource(manager_module)
    assert "SkillsProvider" not in source
    assert "McpProvider" not in source
