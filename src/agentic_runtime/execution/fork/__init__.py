"""Fork primitives for the agentic runtime.

ForkContext  — declarative descriptor of what a fork should produce.
ForkSnapshot — immutable capture of parent state at fork time.
ForkPolicy   — rules for what the child inherits vs. isolates.
RuntimeContextForker — service that applies the policy and returns a child ToolUseContext.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ...context.tool_use import AppState, ToolUseContext
from ...contracts.permissions import PermissionContext
from ...tools.pool import ToolPool


class ForkPolicy(BaseModel):
    """Rules for what a child agent inherits from its parent."""

    inherit_messages: bool = False
    inherit_permissions: bool = True
    inherit_tool_pool: bool = True
    propagate_abort: bool = True


class ForkSnapshot(BaseModel):
    """Immutable capture of parent state at the moment of fork."""

    model_config = ConfigDict(frozen=True)

    session_id: str
    user_id: str | None = None
    subagent_depth: int = 0
    messages: tuple[Any, ...] = ()
    permissions: PermissionContext = Field(default_factory=PermissionContext)
    tool_pool: ToolPool = Field(default_factory=ToolPool)


class ForkContext(BaseModel):
    """Declarative descriptor of a fork request."""

    prompt: str
    policy: ForkPolicy
    parent_snapshot: ForkSnapshot
    subagent_type: str | None = None
    model_override: str | None = None
    timeout_seconds: float | None = None
    max_turns: int | None = None


class RuntimeContextForker:
    """Applies a ForkContext and returns a child ToolUseContext ready for execution."""

    def fork(
        self,
        fork_ctx: ForkContext,
        parent_stop: asyncio.Event | None = None,
    ) -> ToolUseContext:
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        snap = fork_ctx.parent_snapshot
        policy = fork_ctx.policy

        messages: list[Any] = list(snap.messages) if policy.inherit_messages else []
        permissions = snap.permissions if policy.inherit_permissions else PermissionContext()
        tool_pool = snap.tool_pool if policy.inherit_tool_pool else ToolPool()

        if policy.propagate_abort:
            stop = parent_stop
        else:
            stop = asyncio.Event()

        return ToolUseContext(
            session_id=snap.session_id,
            user_id=snap.user_id,
            agent_id=agent_id,
            messages=messages,
            tool_pool=tool_pool,
            app_state=AppState(permissions=permissions),
            stop=stop,
        )


__all__ = ["ForkContext", "ForkPolicy", "ForkSnapshot", "RuntimeContextForker"]
