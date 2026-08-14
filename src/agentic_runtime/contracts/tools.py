from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from .abort import AbortReason
from .identity import Scope


class ToolCategory(str, Enum):
    UTILITY = "utility"
    SYSTEM = "system"
    FILE = "file"
    NETWORK = "network"
    BACKGROUND = "background"


class PermissionBehavior(str, Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


PERMISSION_ONCE_KEY = "permission_granted_once"


@dataclass(frozen=True)
class PermissionDecision:
    behavior: PermissionBehavior
    updated_input: dict[str, Any] | None = None
    message: str | None = None
    remember: bool = True
    deny_message: str | None = None

    @classmethod
    def allow(cls, updated_input: dict[str, Any] | None = None) -> PermissionDecision:
        return cls(PermissionBehavior.ALLOW, updated_input=updated_input)

    @classmethod
    def ask(
        cls,
        message: str,
        *,
        remember: bool = True,
        deny_message: str | None = None,
    ) -> PermissionDecision:
        return cls(
            PermissionBehavior.ASK,
            message=message,
            remember=remember,
            deny_message=deny_message,
        )

    @classmethod
    def deny(cls, message: str) -> PermissionDecision:
        return cls(PermissionBehavior.DENY, message=message)


def grant_permission_once(ctx: Any, tool_name: str) -> None:
    app_state = getattr(ctx, "app_state", None)
    if app_state is None:
        return
    granted = app_state.native.get(PERMISSION_ONCE_KEY)
    if not isinstance(granted, set):
        granted = set()
        app_state.native[PERMISSION_ONCE_KEY] = granted
    granted.add(tool_name)


def consume_permission_once(ctx: Any, tool_name: str) -> bool:
    app_state = getattr(ctx, "app_state", None)
    if app_state is None:
        return False
    granted = app_state.native.get(PERMISSION_ONCE_KEY)
    if not isinstance(granted, set) or tool_name not in granted:
        return False
    granted.discard(tool_name)
    return True


@runtime_checkable
class ToolContext(Protocol):
    @property
    def scope(self) -> Scope | None: ...

    @property
    def messages(self) -> list[Any]: ...


class ToolResult:
    def __init__(
        self,
        *,
        tool_name: str,
        output: str,
        is_error: bool = False,
        is_timeout: bool = False,
        is_aborted: bool = False,
        metadata: dict[str, Any] | None = None,
        context_modifier: Callable[[Any], Any] | None = None,
        ends_turn: bool = False,
        reason: AbortReason | None = None,
    ) -> None:
        self.tool_name = tool_name
        self.output = output
        self.is_error = is_error
        self.is_timeout = is_timeout
        self.is_aborted = is_aborted
        self.metadata = metadata or {}
        self.context_modifier = context_modifier
        self.ends_turn = ends_turn
        self.reason = reason

    @classmethod
    def error(cls, tool_name: str, message: str) -> ToolResult:
        return cls(tool_name=tool_name, output=message, is_error=True)

    @classmethod
    def timeout(cls, tool_name: str) -> ToolResult:
        return cls(tool_name=tool_name, output=f"timeout: {tool_name}", is_timeout=True)

    @classmethod
    def aborted(cls, tool_name: str, reason: AbortReason | None = None) -> ToolResult:
        sufijo = f" ({reason.value})" if reason is not None else ""
        return cls(
            tool_name=tool_name,
            output=f"aborted: {tool_name}{sufijo}",
            is_aborted=True,
            reason=reason,
        )


@runtime_checkable
class ToolProtocol(Protocol):
    name: str
    description: str
    input_schema: dict[str, Any]
    category: ToolCategory
    requires_permission: bool
    safe_for_background: bool
    timeout_seconds: float

    async def execute(self, input: dict[str, Any], ctx: Any) -> ToolResult: ...


def tool_is_enabled(tool: Any) -> bool:
    flag = getattr(tool, "is_enabled", True)
    return bool(flag() if callable(flag) else flag)


async def tool_check_permissions(
    tool: Any, input: dict[str, Any], ctx: Any
) -> PermissionDecision:
    check = getattr(tool, "check_permissions", None)
    if check is None:
        return PermissionDecision.allow(input)
    decision = check(input, ctx)
    if inspect.isawaitable(decision):
        decision = await decision
    if not isinstance(decision, PermissionDecision):
        return PermissionDecision.allow(input)
    return decision


__all__ = [
    "PERMISSION_ONCE_KEY",
    "PermissionBehavior",
    "PermissionDecision",
    "ToolCategory",
    "ToolContext",
    "ToolProtocol",
    "ToolResult",
    "consume_permission_once",
    "grant_permission_once",
    "tool_check_permissions",
    "tool_is_enabled",
]
