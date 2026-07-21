"""Homologación 09·tools-infra — contrato/registry/pool/dispatcher/deferred/exec/fs
vs el core de tools canónico (`Tool.ts`, `tools.ts`, `toolSearch.ts`, `filesystem.ts`, `path.ts`).

Los tests que PASAN codifican el comportamiento YA homologado (contrato mínimo, pool assembly,
resolución del mismo pool, path-guards). Los `xfail(strict=True)` codifican los gaps FIND-TOOL/
GAP-TOOL: fallan HOY (comportamiento homologado ausente) y su fallo ES la evidencia del gap.
Si alguno empezara a pasar, el strict lo vuelve error → señal de reclasificar el estado en 09-tools-infra.md.
"""
from __future__ import annotations

import asyncio

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.permissions import PermissionContext
from agentic_runtime.tools.deferred import is_deferred_tool
from agentic_runtime.tools.deferred_strategy import (
    NativeDeferredStrategy,
    SimulatedDeferredStrategy,
)
from agentic_runtime.tools.dispatcher import ToolDispatcher
from agentic_runtime.tools.factory import create_tools
from agentic_runtime.tools.fs_env import (
    ConfinedFilesystem,
    PathOutsideWorkspace,
    contains_path_traversal,
)
from agentic_runtime.tools.native.tool_search import TOOL_SEARCH_TOOL_NAME
from agentic_runtime.tools.pool import ToolPool, assemble_tool_pool
from agentic_runtime.tools.protocol import ToolCategory, ToolProtocol, ToolResult


# ---------------------------------------------------------------------------
# Fake tool mínima (implementa ToolProtocol estructural)
# ---------------------------------------------------------------------------

class _FakeTool:
    def __init__(self, name: str, *, deferred: bool = False, output: str = "ok") -> None:
        self.name = name
        self.description = f"desc-{name}"
        self.input_schema: dict = {"type": "object", "properties": {}}
        self.category = ToolCategory.UTILITY
        self.requires_permission = False
        self.safe_for_background = True
        self.timeout_seconds = 5.0
        self.deferred = deferred
        self._output = output

    async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult:
        return ToolResult(tool_name=self.name, output=self._output)


def _ctx(**kw) -> ToolUseContext:
    return ToolUseContext(session_id="s1", stop=asyncio.Event(), **kw)


# ===========================================================================
# A · Contrato — lo homologado (PASA)
# ===========================================================================

def test_fake_tool_satisfies_protocol_minimal_surface():
    """ToolProtocol es un subconjunto de 8 miembros del `Tool` canónico (~60). Verifica
    que la superficie mínima es la esperada (runtime_checkable)."""
    t = _FakeTool("Bash")
    assert isinstance(t, ToolProtocol)


def test_tool_result_flags_ok_error_timeout_aborted():
    """ToolResult lleva output+flags (A22). Espejo aplanado del ToolResult<T> canónico."""
    assert ToolResult.error("x", "boom").is_error
    assert ToolResult.timeout("x").is_timeout
    assert ToolResult.aborted("x").is_aborted


# ===========================================================================
# B/C · Registry + pool assembly — lo homologado (PASA)
# ===========================================================================

def test_create_tools_registers_native_and_extras():
    """create_tools = getAllBaseTools (B1): nativas + extras del integrador."""
    extra = _FakeTool("MyCustom")
    reg = create_tools(extras=[extra])
    assert reg.resolve("MyCustom") is extra
    assert reg.resolve("bash") is not None


def test_assemble_pool_native_precedence_and_sorted():
    """assemble_tool_pool = assembleToolPool (C1): native gana en colisión, sort per-partición,
    dedup. Estabilidad de prompt-cache."""
    native = [_FakeTool("Zeta"), _FakeTool("Alpha")]
    cap = [_FakeTool("Alpha", output="CAP"), _FakeTool("Beta")]
    out = assemble_tool_pool(native, cap, PermissionContext())
    names = [t.name for t in out]
    # sort per-PARTICIÓN (native contiguo primero: Alpha,Zeta), luego capability (Beta;
    # Alpha ya visto → dedup). NO es un sort global — el prefijo native contiguo es el
    # invariante de cache-breakpoint del canónico (assembleToolPool).
    assert names == ["Alpha", "Zeta", "Beta"]
    alpha = next(t for t in out if t.name == "Alpha")
    assert alpha._output == "ok"  # native gana (no la capability con output="CAP")


def test_assemble_pool_applies_deny_by_name():
    """B4: deny por NOMBRE exacto (denied_names). Nota: sin MCP server-prefix (gap documentado)."""
    native = [_FakeTool("Bash"), _FakeTool("Danger")]
    pc = PermissionContext(always_deny=["Danger"])
    out = assemble_tool_pool(native, [], pc)
    assert [t.name for t in out] == ["Bash"]


def test_pool_find_resolves_from_same_assembled_pool():
    """C2/D1: ejecución y anuncio resuelven del MISMO pool (findToolByName). Invariante clave."""
    pool = ToolPool(native_tools=[_FakeTool("Bash")], capability_tools=[_FakeTool("mcp__x__y", deferred=True)])
    assert pool.find("Bash") is not None
    # deferred = visibilidad, no disponibilidad: sigue resoluble desde el pool
    assert pool.find("mcp__x__y") is not None


# ===========================================================================
# D · Dispatcher — lo homologado (PASA)
# ===========================================================================

def test_dispatch_resolves_and_runs_from_ctx_pool():
    """D1/D4: el dispatcher resuelve de ctx.tool_pool y ejecuta."""
    ctx = _ctx(tool_pool=ToolPool(native_tools=[_FakeTool("Echo", output="hi")]))
    r = asyncio.run(ToolDispatcher().dispatch(tool_name="Echo", tool_input={}, ctx=ctx))
    assert r.output == "hi" and not r.is_error


def test_dispatch_aborts_before_work_when_stop_set():
    """D2: abort-check pre-ejecución (ctx.stop). Binario, sin reason (gap SIG2)."""
    ctx = _ctx(tool_pool=ToolPool(native_tools=[_FakeTool("Echo")]))
    ctx.stop.set()
    r = asyncio.run(ToolDispatcher().dispatch(tool_name="Echo", tool_input={}, ctx=ctx))
    assert r.is_aborted


def test_dispatch_unknown_tool_is_error():
    ctx = _ctx(tool_pool=ToolPool(native_tools=[]))
    r = asyncio.run(ToolDispatcher().dispatch(tool_name="Nope", tool_input={}, ctx=ctx))
    assert r.is_error


# ===========================================================================
# E · Deferred — lo homologado (PASA)
# ===========================================================================

def test_tool_search_never_deferred_and_flag_defers():
    """E1 (parcial): ToolSearch nunca diferida; `deferred=True` sí. (Sin alwaysLoad/isMcp: gap.)"""
    assert is_deferred_tool(_FakeTool(TOOL_SEARCH_TOOL_NAME, deferred=True)) is False
    assert is_deferred_tool(_FakeTool("mcp__x__y", deferred=True)) is True
    assert is_deferred_tool(_FakeTool("Bash")) is False


def test_simulated_strategy_hides_undiscovered_deferred():
    """E2: la simulada oculta diferidas no descubiertas y muestra ToolSearch si hay diferidas."""
    pool = [_FakeTool("Bash"), _FakeTool("mcp__x__y", deferred=True), _FakeTool(TOOL_SEARCH_TOOL_NAME)]
    ctx = _ctx()
    plan = SimulatedDeferredStrategy().prepare_turn(ctx, pool)
    names = {s["name"] for s in plan.tool_schemas}
    assert "Bash" in names
    assert TOOL_SEARCH_TOOL_NAME in names  # hay diferidas → visible
    assert "mcp__x__y" not in names  # oculta hasta ToolSearch
    assert SimulatedDeferredStrategy().owns_search_dispatch() is True


def test_native_strategy_marks_defer_loading_and_drops_toolsearch():
    """E3 (AÑADIDO): la nativa marca defer_loading y deja el tool_search al provider."""
    pool = [_FakeTool("Bash"), _FakeTool("mcp__x__y", deferred=True), _FakeTool(TOOL_SEARCH_TOOL_NAME)]
    plan = NativeDeferredStrategy().prepare_turn(_ctx(), pool)
    by_name = {s["name"]: s for s in plan.tool_schemas}
    assert TOOL_SEARCH_TOOL_NAME not in by_name  # provider lo añade server-side
    assert by_name["mcp__x__y"].get("defer_loading") is True
    assert "defer_loading" not in by_name["Bash"]
    assert NativeDeferredStrategy().owns_search_dispatch() is False


# ===========================================================================
# G · Path guards / confinamiento — lo homologado (PASA)
# ===========================================================================

def test_contains_path_traversal_matches_canonical():
    """G1: byte-idéntico a containsPathTraversal (path.ts:133)."""
    assert contains_path_traversal("../etc/passwd")
    assert contains_path_traversal("a/../b")
    assert not contains_path_traversal("a/b/c")


def test_confined_fs_blocks_outside_workspace(tmp_path):
    """G5/G6: resolve() confina contra roots; fuera → PathOutsideWorkspace."""
    (tmp_path / "inside.txt").write_text("x")
    fs = ConfinedFilesystem(roots=[tmp_path])
    assert fs.resolve(str(tmp_path / "inside.txt"), for_write=False)
    with pytest.raises(PathOutsideWorkspace):
        fs.resolve("/etc/passwd", for_write=False)


def test_write_roots_narrower_than_read_roots(tmp_path):
    """G7: split read/write roots — escritura más estrecha que lectura."""
    sub = tmp_path / "wr"
    sub.mkdir()
    fs = ConfinedFilesystem(roots=[tmp_path], write_roots=[sub])
    # lectura permitida en todo tmp_path
    assert fs.resolve(str(tmp_path / "a"), for_write=False)
    # escritura sólo en sub
    with pytest.raises(PathOutsideWorkspace):
        fs.resolve(str(tmp_path / "a"), for_write=True)
    assert fs.resolve(str(sub / "a"), for_write=True)


# ===========================================================================
# GAPS — xfail(strict): fallan HOY, su fallo ES la evidencia
# ===========================================================================

@pytest.mark.xfail(strict=True, reason="FIND-TOOL3=FIND-SIG4: interruptBehavior 'cancel'|'block' ausente del ToolProtocol")
def test_tool_protocol_declares_interrupt_behavior():
    t = _FakeTool("Bash")
    # Homologado: el protocolo expondría interrupt_behavior() → 'cancel'|'block' (default 'block').
    assert t.interrupt_behavior() in ("cancel", "block")


@pytest.mark.xfail(strict=True, reason="FIND-TOOL1/A3: sin isConcurrencySafe en el protocolo (ejecución concurrente no modelada)")
def test_tool_protocol_declares_concurrency_safe():
    t = _FakeTool("Grep")
    assert isinstance(t.is_concurrency_safe, (bool, type(lambda: None)))


@pytest.mark.xfail(strict=True, reason="FIND-TOOL2=GAP-02: el gate de permisos no ve el input ni aplica check_permissions por-tool")
def test_dispatcher_calls_per_tool_check_permissions():
    """Homologado: una tool con checkPermissions que niega ciertos inputs debería bloquear.
    Hoy el gate sólo mira requires_permission + nombre en allowed_names, nunca el input."""
    class _Guarded(_FakeTool):
        def __init__(self):
            super().__init__("Guarded")
            self.requires_permission = True

        async def check_permissions(self, input, ctx):  # homologado esperado
            return {"behavior": "deny"} if input.get("danger") else {"behavior": "allow"}

    ctx = _ctx(tool_pool=ToolPool(native_tools=[_Guarded()]))
    # con allowed_names vacío pero check_permissions que permitiría → hoy el dispatcher deniega por nombre
    r = asyncio.run(ToolDispatcher().dispatch(tool_name="Guarded", tool_input={"danger": False}, ctx=ctx))
    assert not r.is_error  # homologado: check_permissions permite → ejecuta


@pytest.mark.xfail(strict=True, reason="FIND-TOOL4/A23: ToolResult no transporta new_messages (tool que inyecta mensajes)")
def test_tool_result_carries_new_messages():
    r = ToolResult(tool_name="x", output="ok")
    assert isinstance(r.new_messages, list)


@pytest.mark.xfail(strict=True, reason="FIND-TOOL4/A24: ToolResult no transporta context_modifier")
def test_tool_result_carries_context_modifier():
    r = ToolResult(tool_name="x", output="ok")
    assert hasattr(r, "context_modifier") and r.context_modifier is not None


@pytest.mark.xfail(strict=True, reason="FIND-TOOL5/SIG10: ToolResult.aborted no lleva reason ni tool_use_id (str genérico)")
def test_aborted_result_carries_reason():
    r = ToolResult.aborted("bash")
    assert getattr(r, "reason", None) in ("cancel", "reject", "sibling_error")


@pytest.mark.xfail(strict=True, reason="FIND-TOOL6/E6: ToolSearch select: no soporta multi-select coma-separado que el delta-announce promete")
def test_tool_search_select_multi():
    from agentic_runtime.tools.native.tool_search import ToolSearchTool

    tools = [_FakeTool("Read", deferred=True), _FakeTool("Edit", deferred=True), _FakeTool("Grep", deferred=True)]
    ctx = _ctx(tool_pool=ToolPool(capability_tools=tools))
    r = asyncio.run(ToolSearchTool().execute({"query": "select:Read,Edit,Grep"}, ctx))
    import json

    matched = {m["name"] for m in json.loads(r.output)["matches"]}
    assert matched == {"Read", "Edit", "Grep"}  # homologado: coma-separado


@pytest.mark.xfail(strict=True, reason="GAP-TOOL3/E1: is_deferred_tool sin precedencia alwaysLoad (opt-out)")
def test_always_load_opts_out_of_deferral():
    t = _FakeTool("mcp__x__y", deferred=True)
    t.always_load = True  # homologado: alwaysLoad gana sobre isMcp/shouldDefer
    assert is_deferred_tool(t) is False


@pytest.mark.xfail(strict=True, reason="FIND-TOOL9/G8: ConfinedFilesystem no protege archivos peligrosos (.bashrc/.git/settings.json) dentro del workspace")
def test_confined_fs_blocks_dangerous_files_inside_workspace(tmp_path):
    (tmp_path / ".bashrc").write_text("x")
    fs = ConfinedFilesystem(roots=[tmp_path])
    # homologado (checkPathSafetyForAutoEdit): editar .bashrc dentro del workspace debería bloquearse
    with pytest.raises(PathOutsideWorkspace):
        fs.resolve(str(tmp_path / ".bashrc"), for_write=True)


@pytest.mark.xfail(strict=True, reason="GAP-02: PermissionContext no modela permission mode (default/acceptEdits/plan/bypass)")
def test_permission_context_has_mode():
    pc = PermissionContext()
    assert pc.mode in ("default", "acceptEdits", "plan", "bypassPermissions")
