"""EnterPlanMode usa `is_subagent` (no `agent_id`) para vetar subagentes.

Regresión: el guard usaba `ctx.agent_id is not None`, pero el contexto RAÍZ también recibe un
`agent_id` (identidad asignada en `runtime.py`). Eso bloqueaba EnterPlanMode en el turno
principal. El discriminador correcto es `is_subagent` (root=False, fork=True), coherente con el
resto del runtime. Canónico: EnterPlanMode es root-only.
"""
from __future__ import annotations

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools.native.plan_mode import EnterPlanModeTool


async def test_enter_plan_mode_allowed_in_root_with_agent_id():
    # Root real: tiene agent_id (identidad) pero is_subagent=False.
    ctx = ToolUseContext(session_id="s", agent_id="agent_abc", is_subagent=False)
    result = await EnterPlanModeTool().execute({}, ctx=ctx)
    assert not result.is_error, result.output
    # Aplica el modifier → plan mode queda activo en app_state.
    ctx = result.context_modifier(ctx)  # type: ignore[attr-defined]
    assert ctx.app_state.native.get("plan_mode") is True


async def test_enter_plan_mode_blocked_in_subagent():
    ctx = ToolUseContext(session_id="s", agent_id="agent_child", is_subagent=True)
    result = await EnterPlanModeTool().execute({}, ctx=ctx)
    assert result.is_error
    assert "subagent" in result.output.lower()
