from __future__ import annotations

import asyncio
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from ..contracts.permissions import PermissionContext


def _default_pool() -> "Any":
    from ..tools.pool import ToolPool
    return ToolPool()


class AppState(BaseModel):
    """Provider-agnostic runtime-visible application state."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    permissions: PermissionContext = Field(default_factory=PermissionContext)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    native: dict[str, Any] = Field(default_factory=dict)


class ToolUseContext(BaseModel):
    """Operational context for one agentic runtime turn."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    user_id: str | None = None  # identidad de ciclo de vida (peer de session_id); hereda al hijo vía ForkSnapshot
    agent_id: str | None = None
    is_subagent: bool = False  # kind: subagente unattended → toolset filtrado a safe_for_background
    subagent_depth: int = 0  # profundidad de anidamiento; la tool Agent la usa como tope
    turn_count: int = 0
    messages: list[Any] = Field(default_factory=list)
    tool_pool: Any = Field(default_factory=_default_pool)
    app_state: AppState = Field(default_factory=AppState)
    stop: asyncio.Event | None = None
    event_queue: asyncio.Queue | None = None
    storage: Any = None
    presentation: Any = None
    exec_env: Any = None

    @property
    def permission_context(self) -> PermissionContext:
        return self.app_state.permissions

    def with_permissions(self, permissions: PermissionContext) -> "ToolUseContext":
        return self.model_copy(
            update={"app_state": self.app_state.model_copy(update={"permissions": permissions})}
        )


ContextModifier = Callable[[ToolUseContext], ToolUseContext]


__all__ = ["AppState", "ContextModifier", "ToolUseContext"]
