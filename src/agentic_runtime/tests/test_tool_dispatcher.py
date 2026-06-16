"""Tests para runtime/tools/ — ToolProtocol, ToolRegistry, ToolDispatcher."""
import asyncio
import pytest

from agentic_runtime.tools import (
    ToolCategory,
    ToolDispatcher,
    ToolProtocol,
    ToolRegistry,
    ToolResult,
)
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.permissions import PermissionContext


# ---------------------------------------------------------------------------
# Helpers — stubs de tools
# ---------------------------------------------------------------------------

class FastTool:
    name = "fast_tool"
    description = "Does nothing quickly"
    input_schema: dict = {}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult:
        return ToolResult(tool_name=self.name, output="done")


class SlowTool:
    name = "slow_tool"
    description = "Sleeps forever"
    input_schema: dict = {}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = False
    timeout_seconds = 0.05  # muy corto para el test

    async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult:
        await asyncio.sleep(10)
        return ToolResult(tool_name=self.name, output="never")


class PermissionedTool:
    name = "permissioned_tool"
    description = "Requires explicit permission"
    input_schema: dict = {}
    category = ToolCategory.SYSTEM
    requires_permission = True
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult:
        return ToolResult(tool_name=self.name, output="secret")


def _ctx(stop: asyncio.Event | None = None) -> ToolUseContext:
    return ToolUseContext(session_id="s1", stop=stop)


# ---------------------------------------------------------------------------
# ToolRegistry
# ---------------------------------------------------------------------------

def test_registry_resolve_registered_tool():
    reg = ToolRegistry()
    reg.register(FastTool())
    tool = reg.resolve("fast_tool")
    assert tool is not None
    assert tool.name == "fast_tool"


def test_registry_resolve_unknown_returns_none():
    reg = ToolRegistry()
    assert reg.resolve("nonexistent") is None


def test_registry_list_available_excludes_unsafe_in_background():
    reg = ToolRegistry()
    reg.register(FastTool())   # safe_for_background=True
    reg.register(SlowTool())   # safe_for_background=False
    available = reg.list_available(mode="background")
    names = [t.name for t in available]
    assert "fast_tool" in names
    assert "slow_tool" not in names


def test_registry_list_available_includes_all_in_foreground():
    reg = ToolRegistry()
    reg.register(FastTool())
    reg.register(SlowTool())
    available = reg.list_available(mode="foreground")
    names = [t.name for t in available]
    assert "fast_tool" in names
    assert "slow_tool" in names


# ---------------------------------------------------------------------------
# ToolDispatcher — dispatch básico
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatcher_resolves_and_executes():
    reg = ToolRegistry()
    reg.register(FastTool())
    disp = ToolDispatcher(registry=reg)

    result = await disp.dispatch(tool_name="fast_tool", tool_input={}, ctx=_ctx())
    assert result.output == "done"
    assert not result.is_error


@pytest.mark.asyncio
async def test_dispatcher_unknown_tool_returns_error():
    reg = ToolRegistry()
    disp = ToolDispatcher(registry=reg)

    result = await disp.dispatch(tool_name="ghost", tool_input={}, ctx=_ctx())
    assert result.is_error
    assert "ghost" in result.output


# ---------------------------------------------------------------------------
# ToolDispatcher — timeout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatcher_applies_timeout():
    reg = ToolRegistry()
    reg.register(SlowTool())
    disp = ToolDispatcher(registry=reg)

    result = await disp.dispatch(tool_name="slow_tool", tool_input={}, ctx=_ctx())
    assert result.is_timeout


# ---------------------------------------------------------------------------
# ToolDispatcher — abort
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatcher_aborts_if_event_set():
    reg = ToolRegistry()
    reg.register(FastTool())
    disp = ToolDispatcher(registry=reg)

    stop = asyncio.Event()
    stop.set()
    result = await disp.dispatch(tool_name="fast_tool", tool_input={}, ctx=_ctx(stop=stop))
    assert result.is_aborted


# ---------------------------------------------------------------------------
# ToolDispatcher — permisos
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatcher_checks_permission_denied():
    reg = ToolRegistry()
    reg.register(PermissionedTool())
    disp = ToolDispatcher(registry=reg)

    # PermissionContext por defecto no tiene permisos
    result = await disp.dispatch(tool_name="permissioned_tool", tool_input={}, ctx=_ctx())
    assert result.is_error


@pytest.mark.asyncio
async def test_dispatcher_allows_permissioned_tool_when_granted():
    from agentic_runtime.context.tool_use import AppState

    reg = ToolRegistry()
    reg.register(PermissionedTool())
    disp = ToolDispatcher(registry=reg)

    perms = PermissionContext(always_allow_command=["permissioned_tool"])
    ctx = ToolUseContext(session_id="s1", app_state=AppState(permissions=perms))
    result = await disp.dispatch(tool_name="permissioned_tool", tool_input={}, ctx=ctx)
    assert not result.is_error
    assert result.output == "secret"


# ---------------------------------------------------------------------------
# ToolProtocol structural check
# ---------------------------------------------------------------------------

def test_fast_tool_satisfies_protocol():
    assert isinstance(FastTool(), ToolProtocol)
