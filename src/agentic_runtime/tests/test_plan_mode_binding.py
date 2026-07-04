"""Plan aprobado como orientación durable en ejecución (hallazgo 2026-06-30).

Defecto observado en vivo: el plan llegaba sólo como `tool_result` transitorio de
`ExitPlanMode`; al empezar la ejecución el modelo lo perdía e improvisaba. Homologación del
`plan_mode_exit` del canónico: `ExitPlanMode` persiste el plan en `app_state.native` y
`PlanModeProvider` lo rinde UNA vez como `<system-reminder>` al salir.
"""
from __future__ import annotations

from agentic_runtime.capabilities.plan import PlanModeProvider
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools.native.plan_mode import (
    _PLAN_EXIT_PENDING_KEY,
    _PLAN_KEY,
    _PLAN_MODE_KEY,
    ExitPlanModeTool,
)

PLAN = "1. Tocar foo.py\n2. Verificar: pytest tests/test_foo.py"


async def _exit_with_plan(plan: str) -> ToolUseContext:
    ctx = ToolUseContext(session_id="s1")
    ctx.app_state.native[_PLAN_MODE_KEY] = True
    result = await ExitPlanModeTool().execute({"plan": plan}, ctx)
    assert not result.is_error
    modifier = getattr(result, "context_modifier", None)
    assert modifier is not None
    return modifier(ctx) or ctx


async def test_exit_persists_plan_and_arms_one_shot():
    ctx = await _exit_with_plan(PLAN)
    assert _PLAN_MODE_KEY not in ctx.app_state.native  # salió de plan mode
    assert ctx.app_state.native[_PLAN_KEY] == PLAN
    assert ctx.app_state.native[_PLAN_EXIT_PENDING_KEY] is True


async def test_exit_cierra_el_turno():
    """Presentar el plan CIERRA el turno (espejo del canónico `requiresUserInteraction()->true`):
    el agente se detiene a esperar aprobación en vez de narrar el plan como aprobado. Mismo
    primitivo `ends_turn` que `AskUserQuestion`."""
    ctx = ToolUseContext(session_id="s1")
    ctx.app_state.native[_PLAN_MODE_KEY] = True
    result = await ExitPlanModeTool().execute({"plan": PLAN}, ctx)
    assert getattr(result, "ends_turn", False) is True
    assert not result.is_error


async def test_provider_emits_plan_once_on_exit():
    ctx = await _exit_with_plan(PLAN)
    provider = PlanModeProvider()

    first = provider.active_context(ctx)
    assert len(first) == 1
    content = first[0]["content"]
    assert "Exited Plan Mode" in content
    assert PLAN in content

    # One-shot: la segunda llamada (siguiente iteración del loop) ya no re-emite.
    assert provider.active_context(ctx) == []
    # El plan sigue disponible en estado para que el modelo lo re-lea si hace falta.
    assert ctx.app_state.native[_PLAN_KEY] == PLAN


def test_provider_emits_in_plan_reminder_while_active():
    """Mientras `plan_mode` activo, el provider rinde la guía in-plan en cada iteración (durable),
    para que el modelo sepa que NO debe ejecutar el enunciado. Cierra el defecto: entrar por el flag
    sembraba el candado pero no orientaba al modelo."""
    provider = PlanModeProvider()
    ctx = ToolUseContext(session_id="s1")
    ctx.app_state.native[_PLAN_MODE_KEY] = True

    first = provider.active_context(ctx)
    assert len(first) == 1
    content = first[0]["content"]
    assert "Plan mode is active" in content
    assert "MUST NOT" in content
    assert "ExitPlanMode" in content
    # Durable, no one-shot: sigue emitiendo mientras plan_mode esté activo.
    assert provider.active_context(ctx) == first


def test_provider_silent_without_exit():
    provider = PlanModeProvider()
    assert provider.active_context(ToolUseContext(session_id="s1")) == []
    assert provider.tools(ToolUseContext(session_id="s1")) == []
    assert provider.catalog(ToolUseContext(session_id="s1")) == []
