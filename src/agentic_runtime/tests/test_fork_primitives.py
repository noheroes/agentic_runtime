"""Tests for Fase 7: fork as a runtime primitive.

Covers ForkContext, ForkSnapshot, ForkPolicy, RuntimeContextForker contracts.
Regression: test_fork_skill.py and test_subagent_depth_guard.py must continue passing.
"""
from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.execution.fork import (
    ForkContext,
    ForkPolicy,
    ForkSnapshot,
    RuntimeContextForker,
)
from agentic_runtime.contracts.permissions import PermissionContext


# ---------------------------------------------------------------------------
# ToolUseContext.agent_id
# ---------------------------------------------------------------------------

def test_tool_use_context_has_agent_id_none_by_default():
    """ToolUseContext created directly has agent_id=None."""
    ctx = ToolUseContext(session_id="s1")
    assert ctx.agent_id is None


# ---------------------------------------------------------------------------
# ForkContext validation
# ---------------------------------------------------------------------------

def test_fork_context_requires_prompt():
    """ForkContext raises ValidationError if prompt is missing."""
    with pytest.raises(ValidationError):
        ForkContext(
            policy=ForkPolicy(),
            parent_snapshot=ForkSnapshot(session_id="s1"),
        )


def test_fork_context_instantiates_with_required_fields():
    """ForkContext instantiates correctly when all required fields are present."""
    ctx = ForkContext(
        prompt="do something",
        policy=ForkPolicy(),
        parent_snapshot=ForkSnapshot(session_id="s1"),
    )
    assert ctx.prompt == "do something"


# ---------------------------------------------------------------------------
# ForkSnapshot immutability
# ---------------------------------------------------------------------------

def test_fork_snapshot_rejects_mutation():
    """ForkSnapshot raises on direct field assignment (frozen model)."""
    snap = ForkSnapshot(session_id="s1", messages=({"role": "user", "content": "hi"},))
    with pytest.raises(Exception):
        snap.messages = ()  # type: ignore[misc]


def test_fork_snapshot_child_messages_do_not_alter_snapshot():
    """List returned for child is independent of the immutable snapshot tuple."""
    snap = ForkSnapshot(
        session_id="s1",
        messages=({"role": "user", "content": "hi"},),
    )
    policy = ForkPolicy(inherit_messages=True)
    child = RuntimeContextForker().fork(
        ForkContext(prompt="go", policy=policy, parent_snapshot=snap)
    )
    child.messages.append({"role": "assistant", "content": "done"})
    assert len(snap.messages) == 1  # snapshot unchanged


# ---------------------------------------------------------------------------
# ForkPolicy — permission inheritance
# ---------------------------------------------------------------------------

def test_fork_policy_inherits_permissions():
    """Child ToolUseContext has parent permissions when inherit_permissions=True."""
    perm = PermissionContext(always_allow_command=["bash"])
    snap = ForkSnapshot(session_id="s1", permissions=perm)
    policy = ForkPolicy(inherit_permissions=True)
    child = RuntimeContextForker().fork(
        ForkContext(prompt="go", policy=policy, parent_snapshot=snap)
    )
    assert "bash" in child.permission_context.always_allow_command


def test_fork_policy_isolates_permissions():
    """Child gets empty permissions when inherit_permissions=False."""
    perm = PermissionContext(always_allow_command=["bash"])
    snap = ForkSnapshot(session_id="s1", permissions=perm)
    policy = ForkPolicy(inherit_permissions=False)
    child = RuntimeContextForker().fork(
        ForkContext(prompt="go", policy=policy, parent_snapshot=snap)
    )
    assert "bash" not in child.permission_context.always_allow_command


# ---------------------------------------------------------------------------
# ForkPolicy — tool pool isolation
# ---------------------------------------------------------------------------

def test_fork_policy_isolates_tool_pool():
    """Child gets empty tool pool when inherit_tool_pool=False."""
    snap = ForkSnapshot(session_id="s1")
    policy = ForkPolicy(inherit_tool_pool=False)
    child = RuntimeContextForker().fork(
        ForkContext(prompt="go", policy=policy, parent_snapshot=snap)
    )
    assert len(child.tool_pool.native_tools) == 0
    assert len(child.tool_pool.capability_tools) == 0


# ---------------------------------------------------------------------------
# RuntimeContextForker — agent_id uniqueness
# ---------------------------------------------------------------------------

def test_forker_assigns_unique_agent_id():
    """Each fork produces a distinct non-None agent_id."""
    snap = ForkSnapshot(session_id="s1")
    policy = ForkPolicy()
    forker = RuntimeContextForker()
    c1 = forker.fork(ForkContext(prompt="a", policy=policy, parent_snapshot=snap))
    c2 = forker.fork(ForkContext(prompt="b", policy=policy, parent_snapshot=snap))
    assert c1.agent_id is not None
    assert c2.agent_id is not None
    assert c1.agent_id != c2.agent_id


def test_forker_child_has_parent_session_id():
    """Child ToolUseContext inherits session_id from the parent snapshot."""
    snap = ForkSnapshot(session_id="parent-session-xyz")
    child = RuntimeContextForker().fork(
        ForkContext(prompt="go", policy=ForkPolicy(), parent_snapshot=snap)
    )
    assert child.session_id == "parent-session-xyz"


# ---------------------------------------------------------------------------
# RuntimeContextForker — abort propagation
# ---------------------------------------------------------------------------

def test_forker_propagate_abort_shares_stop_event():
    """When propagate_abort=True, child receives the same stop event as parent."""
    parent_stop = asyncio.Event()
    snap = ForkSnapshot(session_id="s1")
    child = RuntimeContextForker().fork(
        ForkContext(prompt="go", policy=ForkPolicy(propagate_abort=True), parent_snapshot=snap),
        parent_stop=parent_stop,
    )
    assert child.stop is parent_stop


def test_forker_no_propagate_abort_gets_own_stop_event():
    """When propagate_abort=False, child receives a different stop event."""
    parent_stop = asyncio.Event()
    snap = ForkSnapshot(session_id="s1")
    child = RuntimeContextForker().fork(
        ForkContext(prompt="go", policy=ForkPolicy(propagate_abort=False), parent_snapshot=snap),
        parent_stop=parent_stop,
    )
    assert child.stop is not parent_stop


# ---------------------------------------------------------------------------
# ForkSnapshot — subagent_depth accessible to caller
# ---------------------------------------------------------------------------

def test_fork_snapshot_exposes_subagent_depth():
    """ForkSnapshot.subagent_depth is accessible so caller can compute child depth."""
    snap = ForkSnapshot(session_id="s1", subagent_depth=2)
    assert snap.subagent_depth == 2


def test_forker_does_not_mutate_snapshot():
    """fork() does not alter the parent snapshot."""
    snap = ForkSnapshot(session_id="s1", subagent_depth=1)
    RuntimeContextForker().fork(
        ForkContext(prompt="go", policy=ForkPolicy(), parent_snapshot=snap)
    )
    assert snap.subagent_depth == 1
    assert snap.session_id == "s1"



@pytest.mark.asyncio
async def test_nested_fork_grandchild_gets_own_unique_agent_id():
    """Each nested fork gets a unique agent_id from RuntimeContextForker."""
    from agentic_runtime.execution.fork import ForkContext, ForkPolicy, ForkSnapshot, RuntimeContextForker

    snap_a = ForkSnapshot(session_id="parent-a", subagent_depth=0)
    snap_b = ForkSnapshot(session_id="parent-b", subagent_depth=1)
    policy = ForkPolicy()

    ctx_a = RuntimeContextForker().fork(ForkContext(prompt="first", policy=policy, parent_snapshot=snap_a))
    ctx_b = RuntimeContextForker().fork(ForkContext(prompt="second", policy=policy, parent_snapshot=snap_b))

    assert ctx_a.agent_id is not None
    assert ctx_b.agent_id is not None
    assert ctx_a.agent_id != ctx_b.agent_id
