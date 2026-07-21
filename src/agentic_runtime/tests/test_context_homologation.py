"""Homologación 03·context — `ToolUseContext` / `AppState` / adapters contra el
canónico (`Tool.ts` tipo ToolUseContext, `context.ts`, `state/AppStateStore.tsx`).

Contrapartes canónicas leídas ÍNTEGRAS:
- `Tool.ts` (792 LOC) — tipo `ToolUseContext` (158-300), `ToolPermissionContext`
  (123-148), `contextModifier` en `ToolResult` (330).
- `context.ts` (189) — `getSystemContext`/`getUserContext`/`getGitStatus` (contexto
  prepend: git status + CLAUDE.md + fecha).
- `state/AppStateStore.ts` (570) — el TIPO real `AppState` (89-452) + `getDefaultAppState`.
- `utils/forkedAgent.ts::createSubagentContext` (345-462) — derivación del ctx hijo.

Sintéticos (fakes) verifican lo homologado; los `xfail(strict)` codifican los gaps
(FIND-CTX1 read-file-state / freshness de Edit; GAP-02 permission mode en AppState;
FIND-CTX2 agent_type no threadeado al ctx).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from agentic_runtime.context.adapters import (
    apply_context_modifier_compat,
    sync_session_from_tool_use_context,
    tool_use_context_from_session,
)
from agentic_runtime.context.tool_use import AppState, ContextModifier, ToolUseContext
from agentic_runtime.contracts.permissions import PermissionContext
from agentic_runtime.execution.fork import (
    ForkContext,
    ForkPolicy,
    ForkSnapshot,
    RuntimeContextForker,
)
from agentic_runtime.tools.pool import ToolPool


# --- A · ToolUseContext: forma núcleo (par de Tool.ts:158-300) --------------

def test_toolusecontext_core_fields_present():
    """Los campos operativos del turno existen y tienen defaults sanos.
    Par del canónico: messages, abortController(→stop), agentId, isSubagent(kind),
    subagent_depth, tool_pool(→options.tools), presentation, fs, storage."""
    ctx = ToolUseContext(session_id="s1")
    assert ctx.session_id == "s1"
    assert ctx.agent_id is None
    assert ctx.is_subagent is False
    assert ctx.subagent_depth == 0
    assert ctx.turn_count == 0
    assert ctx.messages == []
    assert isinstance(ctx.tool_pool, ToolPool)
    assert isinstance(ctx.app_state, AppState)
    assert ctx.stop is None
    # fs se autoconfina a cwd por defecto (nunca ilimitado); git_credentials opt-in.
    assert ctx.fs is not None
    assert ctx.git_credentials is None


def test_appstate_is_three_bag_seam():
    """AppState del runtime = 3 bolsas (permissions, capabilities, native), NO el
    store monolítico ~80-campos del canónico (AppStateStore.ts). Divergencia
    deliberada: lo core se queda; el resto lo aporta el integrador por bolsa."""
    st = AppState()
    assert isinstance(st.permissions, PermissionContext)
    assert st.capabilities == {}
    assert st.native == {}


def test_permission_context_property_and_immutable_copy():
    """`permission_context` proyecta app_state.permissions; `with_permissions`
    devuelve COPIA (inmutable-params, como el reducer del canónico)."""
    ctx = ToolUseContext(session_id="s1")
    assert ctx.permission_context is ctx.app_state.permissions

    new_perms = PermissionContext(always_allow_session=["Bash"])
    ctx2 = ctx.with_permissions(new_perms)
    assert ctx2 is not ctx
    assert ctx2.permission_context.always_allow_session == ["Bash"]
    # el original no muta
    assert ctx.permission_context.always_allow_session == []


def test_context_modifier_type_mirrors_toolresult_context_modifier():
    """`ContextModifier: (ToolUseContext) -> ToolUseContext` es el espejo directo
    de `ToolResult.contextModifier` del canónico (Tool.ts:330). Verificado como
    aplicación funcional que produce un ctx nuevo."""
    def modifier(c: ToolUseContext) -> ToolUseContext:
        return c.with_permissions(PermissionContext(always_deny=["Write"]))

    m: ContextModifier = modifier
    ctx = ToolUseContext(session_id="s1")
    out = m(ctx)
    assert out.permission_context.always_deny == ["Write"]


# --- B · Adapters (Session ⇄ ToolUseContext) --------------------------------

def _fake_session(**md):
    metadata = SimpleNamespace(
        permission_grants=md.get("permission_grants", []),
        invoked_skills=md.get("invoked_skills", []),
    )
    return SimpleNamespace(
        session_id=md.get("session_id", "s1"),
        turn_count=md.get("turn_count", 3),
        metadata=metadata,
        messages=md.get("messages", []),
    )


def test_adapter_from_session_maps_grants_and_skills():
    sess = _fake_session(
        permission_grants=["Bash", "Read"],
        invoked_skills=["dataviz"],
        turn_count=7,
    )
    ctx = tool_use_context_from_session(sess)
    assert ctx.session_id == "s1"
    assert ctx.turn_count == 7
    assert ctx.permission_context.always_allow_session == ["Bash", "Read"]
    assert ctx.app_state.capabilities["invoked_skills"] == ["dataviz"]


def test_adapter_prefers_get_messages_for_llm():
    """Si la sesión expone `get_messages_for_llm()` (vista para el modelo), el
    adapter la usa en vez de `.messages` crudo."""
    sess = _fake_session()
    sess.get_messages_for_llm = lambda: [{"role": "user", "content": "hi"}]
    ctx = tool_use_context_from_session(sess)
    assert ctx.messages == [{"role": "user", "content": "hi"}]


def test_adapter_sync_writes_grants_back():
    sess = _fake_session(permission_grants=[])
    ctx = ToolUseContext(session_id="s1").with_permissions(
        PermissionContext(always_allow_session=["Glob"])
    )
    sync_session_from_tool_use_context(sess, ctx)
    assert sess.metadata.permission_grants == ["Glob"]


def test_apply_context_modifier_compat_toolusecontext_path():
    """Modifier que acepta ctx → se aplica y se sincroniza de vuelta a la sesión."""
    sess = _fake_session(permission_grants=[])

    def modifier(c: ToolUseContext) -> ToolUseContext:
        return c.with_permissions(PermissionContext(always_allow_session=["Bash"]))

    ctx = ToolUseContext(session_id="s1")
    out = apply_context_modifier_compat(modifier, session=sess, context=ctx)
    assert out.permission_context.always_allow_session == ["Bash"]
    assert sess.metadata.permission_grants == ["Bash"]


def test_apply_context_modifier_compat_legacy_session_path():
    """Modifier legacy que sólo sabe mutar la sesión (lanza AttributeError sobre
    ctx) → fallback: muta la sesión y devuelve el ctx sin cambios."""
    sess = _fake_session()
    touched: list[str] = []

    def legacy_modifier(obj):
        # Falla si le pasan un ToolUseContext (no tiene .legacy_touch), forzando el
        # camino de compatibilidad con la sesión.
        obj.legacy_touch  # AttributeError sobre ToolUseContext
        touched.append("session")

    sess.legacy_touch = None  # la sesión sí lo tiene
    ctx = ToolUseContext(session_id="s1")
    out = apply_context_modifier_compat(legacy_modifier, session=sess, context=ctx)
    assert out is ctx
    assert touched == ["session"]


# --- C · Derivación de subagente (par de createSubagentContext) -------------

def test_subagent_context_isolation_defaults_mirror_canonical():
    """`RuntimeContextForker.fork` ≡ `createSubagentContext`: por defecto AÍSLA
    (messages fresco), pero HEREDA lo que el canónico threadea del padre
    (permissions, tool_pool, capabilities) y propaga el abort. Genera nuevo agent_id."""
    perms = PermissionContext(always_allow_session=["Bash"])
    pool = ToolPool()
    snap = ForkSnapshot(
        session_id="parent-sess",
        user_id="parent-user",
        messages=({"role": "user", "content": "parent turn"},),
        permissions=perms,
        tool_pool=pool,
        capabilities={"mcp": object()},
    )
    child = RuntimeContextForker().fork(
        ForkContext(prompt="x", policy=ForkPolicy(), parent_snapshot=snap)
    )
    # identidad de ciclo de vida hereda por dato
    assert child.session_id == "parent-sess"
    assert child.user_id == "parent-user"
    # nuevo agent_id (cada subagente el suyo, como createAgentId())
    assert child.agent_id is not None and child.agent_id.startswith("agent_")
    # messages AISLADOS por defecto (inherit_messages=False)
    assert child.messages == []
    # permissions / tool_pool / capabilities HEREDADOS (mismos valores vivos)
    assert child.permission_context.always_allow_session == ["Bash"]
    assert child.tool_pool is pool
    assert "mcp" in child.app_state.capabilities


def test_subagent_context_policy_can_inherit_messages():
    snap = ForkSnapshot(
        session_id="s", messages=({"role": "user", "content": "carry"},)
    )
    child = RuntimeContextForker().fork(
        ForkContext(
            prompt="x",
            policy=ForkPolicy(inherit_messages=True),
            parent_snapshot=snap,
        )
    )
    assert child.messages == [{"role": "user", "content": "carry"}]


# --- D · Gaps codificados (xfail strict = evidencia del gap) -----------------

@pytest.mark.xfail(strict=True, reason="FIND-CTX1: sin read-file-state/FileStateCache "
                   "en el ToolUseContext; Edit no tiene guard read-before-edit ni "
                   "modified-since-read (invariante del canónico, Tool.ts:181).")
def test_toolusecontext_tracks_read_file_state():
    ctx = ToolUseContext(session_id="s1")
    # El canónico lleva `readFileState: FileStateCache` (LRU {path -> {content, mtime}})
    # que alimenta el guard de frescura de Edit/Write y el dedup de nested-memory.
    assert hasattr(ctx, "read_file_state")


@pytest.mark.xfail(strict=True, reason="GAP-02 (01·contracts): PermissionContext no "
                   "tiene `mode` (PermissionMode); AppState.toolPermissionContext del "
                   "canónico sí — AppStateStore.ts:109 + Tool.ts:124.")
def test_appstate_permissions_carry_mode():
    st = AppState()
    assert hasattr(st.permissions, "mode")


@pytest.mark.xfail(strict=True, reason="FIND-CTX2: el ctx no threadea agent_type "
                   "(nombre del tipo de subagente); el canónico sí (Tool.ts:246) y lo "
                   "usan los hooks para distinguir el tipo. El runtime lo tiene en "
                   "ForkContext.subagent_type pero no lo baja al ctx ejecutor.")
def test_toolusecontext_carries_agent_type():
    ctx = ToolUseContext(session_id="s1")
    assert hasattr(ctx, "agent_type")
