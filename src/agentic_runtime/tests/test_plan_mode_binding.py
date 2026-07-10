"""Plan aprobado como orientación durable en ejecución (hallazgo 2026-06-30).

Defecto observado en vivo: el plan llegaba sólo como `tool_result` transitorio de
`ExitPlanMode`; al empezar la ejecución el modelo lo perdía e improvisaba. Homologación del
`plan_mode_exit` del canónico: el plan-file (que el modelo escribe durante plan mode) es la
fuente de verdad; `ExitPlanMode` lo LEE de disco (vía `ctx.storage`, sin arg `plan`), lo cachea
en `app_state.native` para el one-shot, y `PlanModeProvider` lo rinde UNA vez al salir.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from agentic_runtime.capabilities.plan import PlanModeProvider
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools.native.plan_mode import (
    _PLAN_EXIT_PENDING_KEY,
    _PLAN_KEY,
    _PLAN_MODE_KEY,
    ExitPlanModeTool,
)

PLAN = "1. Tocar foo.py\n2. Verificar: pytest tests/test_foo.py"


class _FakePlanStorage:
    """`StorageContract` mínimo: materializa el plan-file en un tmp local.

    `ensure_local('/plans/plan.md')` devuelve el path del tmp con el contenido sembrado (o
    inexistente si `plan is None`, para probar el guard de "no plan found")."""

    def __init__(self, plan: str | None) -> None:
        self._dir = Path(tempfile.mkdtemp())
        if plan is not None:
            (self._dir / "plan.md").write_text(plan, encoding="utf-8")

    def real_path(self, token: str) -> Path:
        return self._dir / token.rsplit("/", 1)[-1]

    async def ensure_local(self, token: str) -> Path:
        return self.real_path(token)

    async def commit(self, token: str, content: bytes, mime: str | None = None) -> str:
        host = self.real_path(token)
        host.write_bytes(content)
        return str(host)

    async def teardown(self) -> None: ...


def _ctx_in_plan(plan: str | None) -> ToolUseContext:
    ctx = ToolUseContext(session_id="s1", storage=_FakePlanStorage(plan))
    ctx.app_state.native[_PLAN_MODE_KEY] = True
    return ctx


async def _exit_with_plan(plan: str) -> ToolUseContext:
    ctx = _ctx_in_plan(plan)
    result = await ExitPlanModeTool().execute({}, ctx)
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
    ctx = _ctx_in_plan(PLAN)
    result = await ExitPlanModeTool().execute({}, ctx)
    assert getattr(result, "ends_turn", False) is True
    assert not result.is_error


async def test_exit_sin_plan_file_es_error():
    """Sin plan-file escrito, `ExitPlanMode` es error (homólogo del guard del canónico): no se
    puede salir a "aprobación" sin un plan en disco. No arma el one-shot ni sale de plan mode."""
    ctx = _ctx_in_plan(None)
    result = await ExitPlanModeTool().execute({}, ctx)
    assert result.is_error
    assert _PLAN_MODE_KEY in ctx.app_state.native


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


def test_provider_emits_5phase_full_then_sparse_while_active():
    """Mientras `plan_mode` activo (ROOT), el provider rinde el workflow de 5 fases con cadencia
    full→sparse: la 1ª iteración el texto completo, las siguientes uno escueto (durable, no
    one-shot). Homólogo de `getPlanModeV2Instructions`→`getPlanModeV2SparseInstructions`."""
    provider = PlanModeProvider()
    ctx = ToolUseContext(session_id="s1")
    ctx.app_state.native[_PLAN_MODE_KEY] = True

    # 1ª iteración: full con las 5 fases y el disparo de subagentes Explore/Plan.
    first = provider.active_context(ctx)
    assert len(first) == 1
    full = first[0]["content"]
    assert "Plan mode is active" in full
    assert "MUST NOT" in full
    assert "Phase 1" in full and "Phase 5" in full
    assert "Explore" in full and "Plan" in full
    assert "/plans/plan.md" in full  # token del plan-file
    assert "ExitPlanMode" in full

    # 2ª iteración: sparse — sigue orientando (no calla) pero escueto y distinto al full.
    second = provider.active_context(ctx)
    assert len(second) == 1
    sparse = second[0]["content"]
    assert sparse != full
    assert "Plan mode still active" in sparse
    assert "ExitPlanMode" in sparse
    # Sigue sparse en adelante.
    assert provider.active_context(ctx) == second


def test_provider_subagent_gets_readonly_reminder_not_5phase():
    """Un subagente en plan mode recibe el recordatorio read-only, NO el workflow de 5 fases
    (no debe orquestar Explore/Plan ni salir de plan mode). Homólogo de
    `getPlanModeV2SubAgentInstructions`."""
    provider = PlanModeProvider()
    ctx = ToolUseContext(session_id="s1", is_subagent=True, agent_id="a1")
    ctx.app_state.native[_PLAN_MODE_KEY] = True

    out = provider.active_context(ctx)
    assert len(out) == 1
    content = out[0]["content"]
    assert "READ-ONLY" in content
    assert "Phase 1" not in content


def test_provider_silent_without_exit():
    provider = PlanModeProvider()
    assert provider.active_context(ToolUseContext(session_id="s1")) == []
    assert provider.tools(ToolUseContext(session_id="s1")) == []
    assert provider.catalog(ToolUseContext(session_id="s1")) == []
