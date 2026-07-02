from __future__ import annotations

import asyncio
from typing import Any

from .tool_use import AppState, ToolUseContext
from ..contracts.permissions import PermissionContext
from ..tools.pool import ToolPool


def tool_use_context_from_session(
    session: Any,
    *,
    tool_pool: ToolPool | None = None,
    stop: asyncio.Event | None = None,
    event_queue: asyncio.Queue | None = None,
    storage: Any = None,
    presentation: Any = None,
) -> ToolUseContext:
    """Build a provider-agnostic runtime context from the current Session shape."""

    metadata = getattr(session, "metadata", None)
    permission_grants = list(getattr(metadata, "permission_grants", []) or [])
    invoked_skills = list(getattr(metadata, "invoked_skills", []) or [])

    messages = (
        session.get_messages_for_llm()
        if hasattr(session, "get_messages_for_llm")
        else list(getattr(session, "messages", []) or [])
    )

    permissions = PermissionContext(always_allow_session=permission_grants)
    app_state = AppState(
        permissions=permissions,
        capabilities={"invoked_skills": invoked_skills},
    )

    return ToolUseContext(
        session_id=getattr(session, "session_id", ""),
        turn_count=getattr(session, "turn_count", 0),
        messages=messages,
        tool_pool=tool_pool or ToolPool(),
        app_state=app_state,
        stop=stop,
        event_queue=event_queue,
        storage=storage,
        presentation=presentation,
    )


def sync_session_from_tool_use_context(session: Any, context: ToolUseContext) -> None:
    """Synchronize legacy Session fields from ToolUseContext."""

    metadata = getattr(session, "metadata", None)
    if metadata is None:
        return
    metadata.permission_grants = list(context.permission_context.always_allow_session)


def apply_context_modifier_compat(
    modifier,
    *,
    session: Any,
    context: ToolUseContext,
) -> ToolUseContext:
    """Apply a context modifier during the transition to ToolUseContext."""

    try:
        updated = modifier(context)
    except AttributeError:
        modifier(session)
        return context

    if isinstance(updated, ToolUseContext):
        sync_session_from_tool_use_context(session, updated)
        return updated
    sync_session_from_tool_use_context(session, context)
    return context


__all__ = [
    "apply_context_modifier_compat",
    "sync_session_from_tool_use_context",
    "tool_use_context_from_session",
]
