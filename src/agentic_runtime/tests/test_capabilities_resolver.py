"""Tests para runtime/capabilities/ — CapabilitiesResolver."""
import asyncio
import pytest

from agentic_runtime.capabilities import CapabilitiesResolver, ResolvedCapabilities
from agentic_runtime.tools import ToolCategory, ToolRegistry, ToolResult
from agentic_runtime.context.tool_use import ToolUseContext


# ---------------------------------------------------------------------------
# Stub tools
# ---------------------------------------------------------------------------

class NativeTool:
    name = "native_tool"
    description = "A native tool"
    input_schema: dict = {}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input, ctx):
        return ToolResult(tool_name=self.name, output="ok")


class PermissionedNativeTool:
    name = "permissioned_native"
    description = "Requires permission"
    input_schema: dict = {}
    category = ToolCategory.SYSTEM
    requires_permission = True
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input, ctx):
        return ToolResult(tool_name=self.name, output="secret")


# ---------------------------------------------------------------------------
# Stub SkillCatalog
# ---------------------------------------------------------------------------

class InstantSkillCatalog:
    async def list_schemas(self, ctx) -> list[dict]:
        return [{"name": "skill_a", "description": "A skill"}]


class SlowSkillCatalog:
    async def list_schemas(self, ctx) -> list[dict]:
        await asyncio.sleep(10)
        return [{"name": "skill_b"}]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resolver_includes_native_tools():
    reg = ToolRegistry()
    reg.register(NativeTool())
    resolver = CapabilitiesResolver(tool_registry=reg)
    ctx = ToolUseContext(session_id="s1")

    resolved = await resolver.resolve(ctx)

    assert isinstance(resolved, ResolvedCapabilities)
    tool_names = [t["name"] for t in resolved.tool_schemas]
    assert "native_tool" in tool_names


@pytest.mark.asyncio
async def test_resolver_respects_permission_context():
    reg = ToolRegistry()
    reg.register(NativeTool())
    reg.register(PermissionedNativeTool())
    resolver = CapabilitiesResolver(tool_registry=reg)
    ctx = ToolUseContext(session_id="s1")  # sin permisos

    resolved = await resolver.resolve(ctx)

    tool_names = [t["name"] for t in resolved.tool_schemas]
    assert "native_tool" in tool_names
    assert "permissioned_native" not in tool_names


@pytest.mark.asyncio
async def test_resolver_includes_skill_catalog_schemas():
    reg = ToolRegistry()
    resolver = CapabilitiesResolver(tool_registry=reg, skill_catalog=InstantSkillCatalog())
    ctx = ToolUseContext(session_id="s1")

    resolved = await resolver.resolve(ctx)

    tool_names = [t["name"] for t in resolved.tool_schemas]
    assert "skill_a" in tool_names


@pytest.mark.asyncio
async def test_resolver_timeout_returns_partial():
    reg = ToolRegistry()
    reg.register(NativeTool())
    resolver = CapabilitiesResolver(
        tool_registry=reg,
        skill_catalog=SlowSkillCatalog(),
        resolve_timeout_seconds=0.05,
    )
    ctx = ToolUseContext(session_id="s1")

    resolved = await resolver.resolve(ctx)

    # Debe retornar las tools nativas sin lanzar por el timeout de skills
    tool_names = [t["name"] for t in resolved.tool_schemas]
    assert "native_tool" in tool_names


@pytest.mark.asyncio
async def test_resolver_without_skill_catalog():
    reg = ToolRegistry()
    reg.register(NativeTool())
    resolver = CapabilitiesResolver(tool_registry=reg)
    ctx = ToolUseContext(session_id="s1")

    resolved = await resolver.resolve(ctx)

    assert len(resolved.tool_schemas) == 1
    assert resolved.tool_schemas[0]["name"] == "native_tool"


def test_resolver_does_not_import_skills_module():
    # importar capabilities no debe traer skills.* en su source
    import agentic_runtime.capabilities as caps_module
    import inspect
    source_file = inspect.getfile(caps_module)
    assert "skills" not in open(source_file).read()
