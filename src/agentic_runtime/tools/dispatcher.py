from __future__ import annotations

import asyncio
from typing import Optional

import agentic_models

from .protocol import ToolResult

from ..context.tool_use import ToolUseContext


class ToolDispatcher:
    """
    Único punto de integración entre ToolUseContext y ToolProtocol.

    El loop llama a dispatch(); ni el loop ni las tools se tocan entre sí.

    Resolución alineada al canónico: la tool se resuelve por nombre desde el pool
    ensamblado del turno (`ctx.tool_pool`), igual que `findToolByName(options.tools,
    name)`. No hay registry nativo aparte para ejecutar: MCP/skills y nativas son
    uniformes en el pool. El loop puebla `ctx.tool_pool` por turno.
    """

    def __init__(self, *, timeout_override: Optional[float] = None) -> None:
        self._timeout_override = timeout_override

    async def dispatch(
        self,
        *,
        tool_name: str,
        tool_input: dict,
        ctx: ToolUseContext,
        timeout: Optional[float] = None,
    ) -> ToolResult:
        result = await self._run(tool_name=tool_name, tool_input=tool_input, ctx=ctx, timeout=timeout)
        # Choke point único de presentación: todo ToolResult (ok/error/timeout/aborted)
        # pasa por aquí antes de llegar a ctx.messages Y al EventBus. Texto libre
        # (stdout/errores) → sanitize_output; bajo identidad es no-op.
        presentation = getattr(ctx, "presentation", None)
        if presentation is not None:
            result.output = presentation.sanitize_output(result.output)
        return result

    async def _run(
        self,
        *,
        tool_name: str,
        tool_input: dict,
        ctx: ToolUseContext,
        timeout: Optional[float] = None,
    ) -> ToolResult:
        # Abort check — antes de cualquier trabajo
        if ctx.stop and ctx.stop.is_set():
            return ToolResult.aborted(tool_name)

        tool = ctx.tool_pool.find(tool_name, ctx.permission_context)
        if tool is None:
            return ToolResult.error(tool_name, f"tool '{tool_name}' no encontrado en el tool pool")

        # Permission check
        if tool.requires_permission:
            allowed = ctx.permission_context.allowed_names()
            if tool_name not in allowed:
                return ToolResult.error(tool_name, f"permiso denegado para '{tool_name}'")

        # Timeout: override per call > override en dispatcher > timeout del tool
        effective_timeout = timeout or self._timeout_override or tool.timeout_seconds

        try:
            validated = agentic_models.validate_tool_arguments(tool_name, tool.input_schema, tool_input)
        except ValueError as exc:
            return ToolResult.error(tool_name, str(exc))

        try:
            result = await asyncio.wait_for(
                tool.execute(validated, ctx),
                timeout=effective_timeout,
            )
            return result
        except asyncio.TimeoutError:
            return ToolResult.timeout(tool_name)
        except Exception as exc:
            return ToolResult.error(tool_name, str(exc))
