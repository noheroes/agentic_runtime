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
                return ToolResult.error(
                    tool_name, decision.deny_message or f"permiso denegado para '{tool_name}'"
                )
        elif decision.updated_input is not None:
            validated = decision.updated_input

        return await self._race(tool, validated, ctx, tool_name, effective_timeout)

    @staticmethod
    async def _race(
        tool: Any,
        validated: dict[str, Any],
        ctx: ToolUseContext,
        tool_name: str,
        effective_timeout: float,
    ) -> ToolResult:
        """La señal de aborto compite con la ejecución, en vez de esperar a que termine.

        `:43-44` sólo miraba `ctx.stop.aborted` ANTES de arrancar: una vez dentro del
        `await`, nadie escuchaba, y el aborto tenía que arbitrarlo un reloj de fuera. A no
        tiene ese reloj —`toolExecution.ts:1206-1222` es un `await tool.call(...)` pelado—
        porque allí la señal viaja DENTRO del contexto y la tool corta sola. Esto es esa
        misma escucha, puesta donde B puede ponerla.

        La cancelación no se espera: matar al hijo es cosa del backend que lo sostiene
        (`exec_env._collect`), que ya ha oído la misma señal. Esperar aquí a que la
        corrutina termine de cancelarse volvería a colgar el turno con la tool sorda que
        es justo el caso que se está pagando.
        """
        stop = getattr(ctx, "stop", None)
        execution: asyncio.Future[ToolResult] = asyncio.ensure_future(
            tool.execute(validated, ctx)
        )
        watch = asyncio.ensure_future(stop.wait()) if stop is not None else None
        waiters: set[asyncio.Future[Any]] = {execution}
        if watch is not None:
            waiters.add(watch)
        try:
            done, _ = await asyncio.wait(
                waiters, timeout=effective_timeout, return_when=asyncio.FIRST_COMPLETED
            )
            if execution in done:
                return execution.result()
            if not done:
                return ToolResult.timeout(tool_name)
            return ToolResult.aborted(tool_name, reason=stop.reason() if stop else None)
        except Exception as exc:  # noqa: BLE001
            return ToolResult.error(tool_name, str(exc))
        finally:
            if watch is not None and not watch.done():
                watch.cancel()
            if not execution.done():
                execution.cancel()
                execution.add_done_callback(_drain)


def _drain(task: asyncio.Future[Any]) -> None:
    if not task.cancelled():
        task.exception()
