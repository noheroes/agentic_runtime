"""Tests para runtime/tools/ — ToolProtocol, ToolRegistry, ToolDispatcher."""
import asyncio
import pytest

from agentic_runtime.contracts.abort import AbortController

from agentic_runtime.tools import (
    ToolCategory,
    ToolDispatcher,
    ToolProtocol,
    ToolRegistry,
    ToolResult,
)
from agentic_runtime.tools.pool import ToolPool
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


def _ctx(*tools: ToolProtocol, stop: AbortController | None = None) -> ToolUseContext:
    # El dispatcher resuelve desde ctx.tool_pool (alineado al canónico): las tools
    # del turno se siembran en el pool, no en un registry aparte.
    return ToolUseContext(
        session_id="s1",
        stop=stop,
        tool_pool=ToolPool(native_tools=list(tools)),
    )


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
    disp = ToolDispatcher()

    result = await disp.dispatch(tool_name="fast_tool", tool_input={}, ctx=_ctx(FastTool()))
    assert result.output == "done"
    assert not result.is_error


@pytest.mark.asyncio
async def test_dispatcher_unknown_tool_returns_error():
    disp = ToolDispatcher()

    result = await disp.dispatch(tool_name="ghost", tool_input={}, ctx=_ctx())
    assert result.is_error
    assert "ghost" in result.output


# ---------------------------------------------------------------------------
# ToolDispatcher — timeout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatcher_applies_timeout():
    disp = ToolDispatcher()

    result = await disp.dispatch(tool_name="slow_tool", tool_input={}, ctx=_ctx(SlowTool()))
    assert result.is_timeout


# ---------------------------------------------------------------------------
# ToolDispatcher — abort
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatcher_aborts_if_event_set():
    disp = ToolDispatcher()

    stop = AbortController()
    stop.abort()
    result = await disp.dispatch(tool_name="fast_tool", tool_input={}, ctx=_ctx(FastTool(), stop=stop))
    assert result.is_aborted


# ---------------------------------------------------------------------------
# ToolDispatcher — permisos
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatcher_checks_permission_denied():
    disp = ToolDispatcher()

    # PermissionContext por defecto no tiene permisos
    result = await disp.dispatch(tool_name="permissioned_tool", tool_input={}, ctx=_ctx(PermissionedTool()))
    assert result.is_error


@pytest.mark.asyncio
async def test_dispatcher_allows_permissioned_tool_when_granted():
    from agentic_runtime.context.tool_use import AppState

    disp = ToolDispatcher()

    perms = PermissionContext(always_allow_command=["permissioned_tool"])
    ctx = ToolUseContext(
        session_id="s1",
        app_state=AppState(permissions=perms),
        tool_pool=ToolPool(native_tools=[PermissionedTool()]),
    )
    result = await disp.dispatch(tool_name="permissioned_tool", tool_input={}, ctx=ctx)
    assert not result.is_error
    assert result.output == "secret"


# ---------------------------------------------------------------------------
# ToolProtocol structural check
# ---------------------------------------------------------------------------

def test_fast_tool_satisfies_protocol():
    assert isinstance(FastTool(), ToolProtocol)


# ---------------------------------------------------------------------------
# GAP medido: el timeout del dispatcher NO acota a una tool que bloquea el loop
# ---------------------------------------------------------------------------

class _BlockingTool:
    """Tool que hace E/S SINCRONA dentro de `async def` — la forma real de
    `web_fetch.py:53` y `web_search.py:111` (`urllib.request.urlopen`)."""

    name = "blocking_tool"
    description = "bloquea el event loop"
    input_schema: dict = {}
    category = ToolCategory.NETWORK
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 0.2

    async def execute(self, input: dict, ctx=None) -> ToolResult:
        import time
        # Silenciado a propósito: el `time.sleep` síncrono dentro de `async def` ES el
        # defecto que este test demuestra. Arreglar el lint aquí borraría la prueba.
        time.sleep(1.0)  # noqa: ASYNC251
        return ToolResult(tool_name=self.name, output="termine igual")


@pytest.mark.xfail(
    strict=True,
    reason=(
        "GAP MEDIDO (2026-08-01): `dispatcher.py:76` confia el cap a `asyncio.wait_for`, "
        "que NO puede preemptar una llamada sincrona bloqueante. Medido: cap de 0.30s, "
        "transcurrido 2.00s, y el resultado vuelve como EXITO, no como `ToolResult.timeout`. "
        "Falsifica la afirmacion firmada en `11-cap-mcp.md:656-658` ('una tool que tarde "
        ">30s FALLA'). Instancias vivas: `web_fetch`/`web_search` (urlopen sincrono, hasta "
        "20s cada una) — durante ese tiempo `ctx.stop` tampoco puede surtir efecto, porque "
        "el abort solo se pre-chequea (`dispatcher.py:54`). Arreglarlo (offload a executor "
        "o cliente async) es `10·tools-native` mas alla de las 2 tools de `C6` => ARRIBA de "
        "la LINEA DE CORTE del tramo 1. `strict=True` a proposito: si alguien lo paga, este "
        "test se pone ROJO y obliga a actualizar el tracker."
    ),
)
@pytest.mark.asyncio
async def test_dispatcher_timeout_bounds_a_blocking_tool():
    import time

    reg = ToolRegistry()
    reg.register(_BlockingTool())
    ctx = ToolUseContext(tool_pool=ToolPool(native_tools=reg.all_tools()))

    t0 = time.monotonic()
    result = await ToolDispatcher().dispatch("blocking_tool", {}, ctx)
    elapsed = time.monotonic() - t0

    assert result.is_error, "una tool que excede su timeout_seconds debe fallar"
    assert elapsed < 0.5, f"el cap de 0.2s no acoto: {elapsed:.2f}s"
