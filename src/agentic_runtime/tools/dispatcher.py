from __future__ import annotations

import asyncio
from typing import Any

import agentic_models

from ..context.tool_use import ToolUseContext
from .protocol import (
    PermissionBehavior,
    ToolResult,
    consume_permission_once,
    tool_check_permissions,
)


class ToolDispatcher:
    def __init__(self, *, timeout_override: float | None = None) -> None:
        self._timeout_override = timeout_override

    async def dispatch(
        self,
        *,
        tool_name: str,
        tool_input: dict[str, Any],
        ctx: ToolUseContext,
        timeout: float | None = None,
    ) -> ToolResult:
        result = await self._run(tool_name=tool_name, tool_input=tool_input, ctx=ctx, timeout=timeout)
        presentation = getattr(ctx, "presentation", None)
        if presentation is not None:
            result.output = presentation.sanitize_output(result.output)
        return result

    async def _run(
        self,
        *,
        tool_name: str,
        tool_input: dict[str, Any],
        ctx: ToolUseContext,
        timeout: float | None = None,
    ) -> ToolResult:
        if ctx.stop is not None and ctx.stop.aborted:
            return ToolResult.aborted(tool_name, reason=ctx.stop.reason())

        tool = ctx.tool_pool.find(tool_name, ctx.permission_context)
        if tool is None:
            return ToolResult.error(tool_name, f"tool '{tool_name}' no encontrado en el tool pool")

        if tool.requires_permission:
            allowed = ctx.permission_context.allowed_names()
            if tool_name not in allowed:
                return ToolResult.error(tool_name, f"permiso denegado para '{tool_name}'")

        effective_timeout = timeout or self._timeout_override or tool.timeout_seconds

        try:
            validated = agentic_models.validate_tool_arguments(tool_name, tool.input_schema, tool_input)
        except ValueError as exc:
            return ToolResult.error(tool_name, str(exc))

        decision = await tool_check_permissions(tool, validated, ctx)
        if decision.behavior is PermissionBehavior.DENY:
            return ToolResult.error(
                tool_name, decision.message or f"permiso denegado para '{tool_name}'"
            )
        if decision.behavior is PermissionBehavior.ASK:
            granted = tool_name in ctx.permission_context.allowed_names()
            if not granted and not consume_permission_once(ctx, tool_name):
                return ToolResult.error(tool_name, f"permiso denegado para '{tool_name}'")
        elif decision.updated_input is not None:
            validated = decision.updated_input

        try:
            result: ToolResult = await asyncio.wait_for(
                tool.execute(validated, ctx),
                timeout=effective_timeout,
            )
            return result
        except TimeoutError:
            return ToolResult.timeout(tool_name)
        except Exception as exc:  # noqa: BLE001
            return ToolResult.error(tool_name, str(exc))
