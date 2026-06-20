"""
Identidad (user_id, session_id) consistente en los 3 modos + eliminación de los
dos objetos de contexto remanentes (ExecutionContext / AgentContext).

La identidad de ciclo de vida viaja por DATO explícito (ToolUseContext.user_id,
ForkSnapshot.user_id, RuntimeTask.{owner_id,session_id}), no por ContextVar ambiental.
"""
from __future__ import annotations

import importlib

import pytest

from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.execution.fork import (
    ForkContext,
    ForkPolicy,
    ForkSnapshot,
    RuntimeContextForker,
)
from agentic_runtime.execution.local.runtime import LocalAgentRuntime
from agentic_runtime.execution.runner import set_runner


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


# --- 2. user_id como ciudadano de primera (peer de session_id) -------------

def test_tool_use_context_has_user_id():
    ctx = ToolUseContext(session_id="s1", user_id="u1")
    assert ctx.user_id == "u1"


def test_fork_snapshot_has_user_id():
    snap = ForkSnapshot(session_id="s1", user_id="u1")
    assert snap.user_id == "u1"


def test_runtime_task_accepts_session_id():
    task = RuntimeTask(prompt="p", description="d", session_id="s1", owner_id="u1")
    assert task.session_id == "s1"
    assert task.owner_id == "u1"


# --- 3. Inyección vs autogeneración en la raíz (simétrica) ------------------

def test_build_child_root_uses_injected_ids():
    rt = LocalAgentRuntime()
    task = RuntimeTask(prompt="p", description="d", session_id="ext-sess", owner_id="ext-user")
    ctx, parent_sid, depth = rt._build_child(task, None)
    assert ctx.session_id == "ext-sess"
    assert ctx.user_id == "ext-user"
    assert parent_sid is None and depth == 0


def test_build_child_root_generates_when_absent():
    rt = LocalAgentRuntime()
    ctx, _, _ = rt._build_child(RuntimeTask(prompt="p", description="d"), None)
    assert ctx.session_id.startswith("sess_")
    assert ctx.user_id.startswith("user_")


# --- 4. user_id cruza al hijo por dato, igual que session_id ---------------

def test_forker_child_inherits_user_id_like_session_id():
    snap = ForkSnapshot(session_id="parent-sess", user_id="parent-user")
    child = RuntimeContextForker().fork(
        ForkContext(prompt="x", policy=ForkPolicy(), parent_snapshot=snap)
    )
    assert child.session_id == "parent-sess"
    assert child.user_id == "parent-user"


@pytest.mark.asyncio
async def test_agent_tool_snapshot_carries_parent_user_id():
    from agentic_runtime.tools.native.agent import AgentTool

    captured: dict = {}

    class _CapturingRunner:
        async def run(self, fork_ctx, *, background):
            captured["fork_ctx"] = fork_ctx
            return "task-xyz"

    set_runner(_CapturingRunner())
    ctx = ToolUseContext(session_id="s1", user_id="u-parent")
    await AgentTool().execute({"prompt": "go", "description": "d"}, ctx)

    assert captured["fork_ctx"].parent_snapshot.user_id == "u-parent"


# --- 5. Tier 2: memoria scopeada por usuario -------------------------------

def test_memory_scope_separates_users(tmp_path):
    from agentic_runtime.capabilities.memory.store import FilesystemMemoryStore
    from agentic_runtime.capabilities.memory.provider import MemoryProvider

    store = FilesystemMemoryStore(tmp_path)
    scope_u1 = MemoryProvider._scope(ToolUseContext(session_id="s1", user_id="u1"))
    scope_u2 = MemoryProvider._scope(ToolUseContext(session_id="s2", user_id="u2"))

    assert scope_u1 == "u1/main" and scope_u2 == "u2/main"
    dir_u1 = store.ensure_dir(scope_u1)
    dir_u2 = store.ensure_dir(scope_u2)
    assert dir_u1 != dir_u2
    assert dir_u1 == tmp_path / "u1" / "main"
    assert dir_u2 == tmp_path / "u2" / "main"


def test_memory_subagent_isolated_within_user():
    from agentic_runtime.capabilities.memory.provider import MemoryProvider

    scope = MemoryProvider._scope(
        ToolUseContext(session_id="s1", user_id="u1", agent_id="agent_abc", is_subagent=True)
    )
    assert scope == "u1/agent_abc"


# --- 6. Tier 2: canal de notificación con clave (user_id, session_id) ------

def test_notification_channel_keyed_by_user_and_session():
    from agentic_runtime.execution.local.notification import (
        BackgroundNotification,
        drain_notifications,
        put_notification,
    )

    put_notification(BackgroundNotification(
        parent_user_id="u1", parent_session_id="s1", task_id="t1",
        status="completed", description="d", notification_text="ok",
    ))
    # mismo session_id pero otro usuario → no hay fuga
    assert drain_notifications("u2", "s1") == []
    drained = drain_notifications("u1", "s1")
    assert len(drained) == 1 and drained[0].task_id == "t1"
    # el canal queda vacío tras drenar
    assert drain_notifications("u1", "s1") == []
