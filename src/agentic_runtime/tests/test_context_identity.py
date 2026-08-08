"""
Identidad por DATO EXPLÍCITO, nunca ambiental y nunca inventada (`C9`, `DEUDA-A ID-1`).

Reescrito en el tramo 1. Antes este archivo acreditaba que `user_id` era *«ciudadano de
primera»* del `ToolUseContext` y que la raíz **autogeneraba** `user_<hex>`/`sess_<hex>`
cuando no venían. Eso no era un default benigno: era la mímica, y tenía un fallo
funcional detrás (`H-1` — la clave de memoria cambiaba en cada despacho, así que el
agente principal no recuperaba su memoria nunca).

Lo que se acredita ahora:
  · el runtime **no conoce usuarios** — `user_id` ya no existe en el contexto;
  · lo que necesitaba de ellos (scoping de persistencia) viaja por `Scope`, opaco;
  · sin identidad atribuida el runtime **falla en voz alta**, no fabrica una;
  · sin `scope` no hay scope: `None`, jamás un uuid.
"""
from __future__ import annotations

import importlib

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.errors import RuntimeIdentityError
from agentic_runtime.contracts.identity import Scope
from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.execution.fork import (
    ForkContext,
    ForkPolicy,
    ForkSnapshot,
    RuntimeContextForker,
)
from agentic_runtime.execution.local.runtime import LocalAgentRuntime

# --- 1. Los remanentes muertos ya no existen -------------------------------

def test_execution_context_module_removed():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("agentic_runtime.context.execution")


def test_agent_context_module_removed():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("agentic_runtime.execution.context.agent_context")


def test_context_package_drops_execution_context_exports():
    import agentic_runtime.context as ctx_pkg

    for symbol in (
        "ExecutionContext",
        "RuntimeState",
        "get_execution_context",
        "set_execution_context",
        "run_with_context",
    ):
        assert not hasattr(ctx_pkg, symbol)


# --- 2. El scope es el cable de persistencia; `user_id` ya no existe -------

def test_tool_use_context_carries_scope_and_no_user_id():
    ctx = ToolUseContext(session_id="s1", scope=Scope("u1"))
    assert ctx.scope == Scope("u1")
    assert not hasattr(ctx, "user_id"), "el runtime no vuelve a conocer usuarios (C9)"


def test_fork_snapshot_carries_scope():
    snap = ForkSnapshot(session_id="s1", scope=Scope("u1"))
    assert snap.scope == Scope("u1")
    assert not hasattr(snap, "user_id")


def test_scope_cannot_be_empty():
    """Un scope vacío colisiona entre tenants — es el defecto que `ID-3` documenta."""
    with pytest.raises(ValueError):
        Scope("")


def test_runtime_task_accepts_session_id():
    task = RuntimeTask(prompt="p", description="d", session_id="s1", owner_id="u1")
    assert task.session_id == "s1"
    assert task.owner_id == "u1"


# --- 3. Atribución sí; autogeneración NO (el corazón de `ID-1`) ------------

def test_build_child_root_uses_attributed_ids():
    rt = LocalAgentRuntime(scope=Scope("host-scope"))
    task = RuntimeTask(prompt="p", description="d", session_id="ext-sess")
    ctx, parent_sid, depth = rt._build_child(task, None)
    assert ctx.session_id == "ext-sess"
    assert ctx.scope == Scope("host-scope")
    assert parent_sid is None and depth == 0


def test_task_scope_wins_over_host_scope():
    """Un integrador multi-tenant sirve muchos scopes desde un solo host (`D-11`)."""
    rt = LocalAgentRuntime(scope=Scope("host-scope"))
    task = RuntimeTask(prompt="p", description="d", session_id="s", scope=Scope("tenant-7"))
    ctx, _, _ = rt._build_child(task, None)
    assert ctx.scope == Scope("tenant-7")


def test_build_child_root_refuses_to_invent_a_session_id():
    """Aquí vivía `session_id = task.session_id or f"sess_{uuid4}"`. Ya no."""
    rt = LocalAgentRuntime()
    with pytest.raises(RuntimeIdentityError):
        rt._build_child(RuntimeTask(prompt="p", description="d"), None)


def test_build_child_root_leaves_scope_none_when_absent():
    """Ausencia de scope es `None` — un hecho que se propaga, no un `user_<hex>`."""
    rt = LocalAgentRuntime()
    ctx, _, _ = rt._build_child(RuntimeTask(prompt="p", description="d", session_id="s"), None)
    assert ctx.scope is None


# --- 4. El scope cruza al hijo por dato, igual que session_id -------------

def test_forker_child_inherits_scope_like_session_id():
    snap = ForkSnapshot(session_id="parent-sess", scope=Scope("parent-scope"))
    child = RuntimeContextForker().fork(
        ForkContext(prompt="x", policy=ForkPolicy(), parent_snapshot=snap)
    )
    assert child.session_id == "parent-sess"
    assert child.scope == Scope("parent-scope")


def test_forker_child_carries_subagent_type_as_stable_identity():
    """`ID-5`: el tipo se repite entre despachos; el `agent_id` es un uuid por fork."""
    snap = ForkSnapshot(session_id="s", scope=Scope("sc"))
    child = RuntimeContextForker().fork(
        ForkContext(prompt="x", policy=ForkPolicy(), parent_snapshot=snap, subagent_type="reviewer")
    )
    assert child.subagent_type == "reviewer"
    assert child.agent_id and child.agent_id != "reviewer"


@pytest.mark.asyncio
async def test_agent_tool_snapshot_carries_parent_scope():
    from agentic_runtime.tools.native.agent import AgentTool

    captured: dict = {}

    class _CapturingRunner:
        async def run(self, spec, *, background=False):
            captured["spec"] = spec
            return "task-xyz"

    # `C8`: la costura llega por el `ctx`, no por un global (`set_runner` ya no existe).
    ctx = ToolUseContext(
        session_id="s1", scope=Scope("u-parent"), runner=_CapturingRunner()
    )
    await AgentTool().execute({"prompt": "go", "description": "d"}, ctx)

    assert captured["spec"].parent_snapshot.scope == Scope("u-parent")


@pytest.mark.asyncio
async def test_agent_tool_snapshot_carries_parent_capabilities():
    """El snapshot captura app_state.capabilities del padre, para que el subagente
    herede el provider per-tenant del integrador (homologación canónico)."""
    from agentic_runtime.tools.native.agent import AgentTool

    captured: dict = {}

    class _CapturingRunner:
        async def run(self, spec, *, background=False):
            captured["spec"] = spec
            return "task-xyz"

    sentinel = object()
    ctx = ToolUseContext(
        session_id="s1", scope=Scope("u-parent"), runner=_CapturingRunner()
    )
    ctx.app_state.capabilities["mcp"] = sentinel
    await AgentTool().execute({"prompt": "go", "description": "d"}, ctx)

    assert captured["spec"].parent_snapshot.capabilities.get("mcp") is sentinel


# --- 5. Tier 2: memoria scopeada por usuario -------------------------------

def test_memory_scope_separates_users(tmp_path):
    from agentic_runtime.capabilities.memory.provider import MemoryProvider
    from agentic_runtime.capabilities.memory.store import FilesystemMemoryStore

    store = FilesystemMemoryStore(tmp_path)
    scope_u1 = MemoryProvider._scope(ToolUseContext(session_id="s1", scope=Scope("u1")))
    scope_u2 = MemoryProvider._scope(ToolUseContext(session_id="s2", scope=Scope("u2")))

    assert scope_u1 == "u1/main" and scope_u2 == "u2/main"
    dir_u1 = store.ensure_dir(scope_u1)
    dir_u2 = store.ensure_dir(scope_u2)
    assert dir_u1 != dir_u2
    assert dir_u1 == tmp_path / "u1" / "main"
    assert dir_u2 == tmp_path / "u2" / "main"


def test_memory_subagent_isolated_within_scope():
    from agentic_runtime.capabilities.memory.provider import MemoryProvider

    scope = MemoryProvider._scope(
        ToolUseContext(session_id="s1", scope=Scope("u1"), agent_id="agent_abc", is_subagent=True)
    )
    assert scope == "u1/agent_abc"


def test_memory_subagent_key_is_stable_across_dispatches():
    """`ID-5`: dos despachos del MISMO tipo comparten clave; el uuid por fork no."""
    from agentic_runtime.capabilities.memory.provider import MemoryProvider

    first = MemoryProvider._scope(ToolUseContext(
        session_id="s1", scope=Scope("u1"), agent_id="agent_aaa",
        subagent_type="reviewer", is_subagent=True))
    second = MemoryProvider._scope(ToolUseContext(
        session_id="s9", scope=Scope("u1"), agent_id="agent_zzz",
        subagent_type="reviewer", is_subagent=True))
    other = MemoryProvider._scope(ToolUseContext(
        session_id="s1", scope=Scope("u1"), agent_id="agent_bbb",
        subagent_type="writer", is_subagent=True))
    assert first == second == "u1/reviewer"
    assert other == "u1/writer"


def test_memory_refuses_to_invent_a_scope():
    from agentic_runtime.capabilities.memory.provider import MemoryProvider

    with pytest.raises(RuntimeIdentityError):
        MemoryProvider._scope(ToolUseContext(session_id="s1"))


# --- 6. Tier 2: canal de notificación con clave (scope, session_id) -------

def test_notification_channel_keyed_by_user_and_session():
    from agentic_runtime.execution.local.notification import (
        BackgroundNotification,
        drain_notifications,
        put_notification,
    )

    put_notification(BackgroundNotification(
        parent_scope="u1", parent_session_id="s1", task_id="t1",
        status="completed", description="d", notification_text="ok",
    ))
    # mismo session_id pero otro scope → no hay fuga entre tenants
    assert drain_notifications("u2", "s1") == []
    drained = drain_notifications("u1", "s1")
    assert len(drained) == 1 and drained[0].task_id == "t1"
    # el canal queda vacío tras drenar
    assert drain_notifications("u1", "s1") == []
