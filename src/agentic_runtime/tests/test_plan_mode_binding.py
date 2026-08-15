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
from agentic_runtime.capabilities.plan.provider import (
    FULL_REMINDER_EVERY_N_ATTACHMENTS,
    TURNS_BETWEEN_ATTACHMENTS,
)
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.tools import PermissionBehavior
from agentic_runtime.loop.agent_loop import _as_reminder
from agentic_runtime.tools.native.plan_mode import (
    _PLAN_EXIT_PENDING_KEY,
    _PLAN_KEY,
    _PLAN_MODE_KEY,
    NOT_IN_PLAN_MODE_MESSAGE,
    PLAN_APPROVED_TEMPLATE,
    PLAN_REJECTION_PREFIX,
    ExitPlanModeTool,
)

PLAN = "1. Tocar foo.py\n2. Verificar: pytest tests/test_foo.py"


def _attach(provider: PlanModeProvider, ctx: ToolUseContext) -> list[str]:
    emitidos = provider.active_context(ctx)
    for msg in emitidos:
        ctx.messages.append({"role": "user", "content": _as_reminder(msg["content"])})
    return [msg["content"] for msg in emitidos]


def _human_turn(ctx: ToolUseContext) -> None:
    ctx.messages.append({"role": "user", "content": "sigue"})


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


async def test_exit_pide_aprobacion_y_el_execute_no_cierra_el_turno():
    ctx = _ctx_in_plan(PLAN)
    tool = ExitPlanModeTool()

    decision = await tool.check_permissions({}, ctx)
    assert decision.behavior is PermissionBehavior.ASK
    assert decision.message == PLAN
    assert decision.remember is False
    assert decision.deny_message == f"{PLAN_REJECTION_PREFIX}{PLAN}"

    result = await tool.execute({}, ctx)
    assert not result.is_error
    assert getattr(result, "ends_turn", False) is False
    assert result.output == PLAN_APPROVED_TEMPLATE.format(plan=PLAN)


async def test_exit_sin_plan_file_lo_deniega_el_gate_de_permiso():
    ctx = _ctx_in_plan(None)
    decision = await ExitPlanModeTool().check_permissions({}, ctx)
    assert decision.behavior is PermissionBehavior.DENY
    assert "No plan found at /plans/plan.md" in (decision.message or "")
    assert _PLAN_MODE_KEY in ctx.app_state.native
    assert _PLAN_EXIT_PENDING_KEY not in ctx.app_state.native


async def test_exit_fuera_de_plan_mode_lo_deniega_el_gate_de_permiso():
    ctx = _ctx_in_plan(PLAN)
    ctx.app_state.native.pop(_PLAN_MODE_KEY)
    decision = await ExitPlanModeTool().check_permissions({}, ctx)
    assert decision.behavior is PermissionBehavior.DENY
    assert decision.message == NOT_IN_PLAN_MODE_MESSAGE


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
    provider = PlanModeProvider()
    ctx = ToolUseContext(session_id="s1")
    ctx.app_state.native[_PLAN_MODE_KEY] = True

    primero = _attach(provider, ctx)
    assert len(primero) == 1
    full = primero[0]
    assert "Plan mode is active" in full
    assert "MUST NOT" in full
    assert "Phase 1" in full and "Phase 5" in full
    assert "Explore" in full and "Plan" in full
    assert "/plans/plan.md" in full
    assert "ExitPlanMode" in full

    for _ in range(TURNS_BETWEEN_ATTACHMENTS - 1):
        assert _attach(provider, ctx) == []
        _human_turn(ctx)
    assert _attach(provider, ctx) == []

    _human_turn(ctx)
    segundo = _attach(provider, ctx)
    assert len(segundo) == 1
    sparse = segundo[0]
    assert sparse != full
    assert "Plan mode still active" in sparse
    assert "ExitPlanMode" in sparse

    rendidos = [full, sparse]
    while len(rendidos) < FULL_REMINDER_EVERY_N_ATTACHMENTS + 1:
        for _ in range(TURNS_BETWEEN_ATTACHMENTS):
            _human_turn(ctx)
        emitido = _attach(provider, ctx)
        assert len(emitido) == 1
        rendidos.append(emitido[0])

    assert rendidos[1:FULL_REMINDER_EVERY_N_ATTACHMENTS] == [sparse] * (
        FULL_REMINDER_EVERY_N_ATTACHMENTS - 1
    )
    assert rendidos[FULL_REMINDER_EVERY_N_ATTACHMENTS] == full


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
