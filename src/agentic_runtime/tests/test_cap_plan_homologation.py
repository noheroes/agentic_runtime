"""Homologación 14·capabilities/plan — `plan_file.py`/`provider.py`/`tools/native/plan_mode.py`
vs el subsistema de plan mode canónico (`tools/{Enter,Exit}PlanModeTool`, `utils/plans.ts`,
`utils/planModeV2.ts`, `tools/AgentTool/built-in/{planAgent,exploreAgent}.ts`, las instrucciones de
`utils/messages.ts` y la cadencia de `utils/attachments.ts`).

Los tests que PASAN codifican lo YA homologado (guard root-only por `is_subagent`, token de plan-file
fijo/subagente-aislado, lectura vía storage, one-shot de salida con plan inline, cadencia full→sparse,
reminder read-only de subagente, provider silencioso sin plan mode, ExitPlanMode cierra el turno).

Los `xfail(strict=True)` codifican los gaps FIND-PLAN1..14: fallan HOY (comportamiento ausente) y su fallo
ES la evidencia del gap. Si alguno empezara a pasar, el strict lo vuelve error → señal de reclasificar en
`14-cap-plan.md`. Los símbolos-target aún inexistentes se importan DENTRO de cada test para no romper la
colección.
"""
from __future__ import annotations

import pytest

from agentic_runtime.capabilities.plan import PlanModeProvider
from agentic_runtime.capabilities.plan.plan_file import (
    EXPLORE_AGENT_TYPE,
    PLAN_AGENT_TYPE,
    get_plan_file_path,
    is_session_plan_file,
)
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools.native.plan_mode import (
    _PLAN_EXIT_PENDING_KEY,
    _PLAN_MODE_KEY,
    EnterPlanModeTool,
    ExitPlanModeTool,
)


class _FakePlanStorage:
    """StorageContract mínimo: materializa `/plans/*.md` en un dict en memoria."""

    def __init__(self, plans: dict[str, str] | None = None) -> None:
        import tempfile
        from pathlib import Path

        self._dir = Path(tempfile.mkdtemp())
        for token, content in (plans or {}).items():
            (self._dir / token.rsplit("/", 1)[-1]).write_text(content, encoding="utf-8")

    def real_path(self, token: str):
        return self._dir / token.rsplit("/", 1)[-1]

    async def ensure_local(self, token: str):
        return self.real_path(token)

    async def commit(self, token: str, content: bytes, mime=None) -> str:
        host = self.real_path(token)
        host.write_bytes(content)
        return str(host)


def _ctx_in_plan(plan: str | None = None, **kw) -> ToolUseContext:
    plans = {"/plans/plan.md": plan} if plan is not None else {}
    ctx = ToolUseContext(session_id="s1", storage=_FakePlanStorage(plans), **kw)
    ctx.app_state.native[_PLAN_MODE_KEY] = True
    return ctx


# ===========================================================================
# Homologado (PASA)
# ===========================================================================

def test_plan_file_token_root_vs_subagent():
    """C1: token fijo root vs subagente-aislado, discriminado por is_subagent."""
    root = ToolUseContext(session_id="s1", agent_id="a-root", is_subagent=False)
    sub = ToolUseContext(session_id="s1", agent_id="a-child", is_subagent=True)
    assert get_plan_file_path(root) == "/plans/plan.md"
    assert get_plan_file_path(sub) == "/plans/plan-agent-a-child.md"


def test_is_session_plan_file():
    """C5: mecanismo de exención del candado (prefijo/sufijo)."""
    assert is_session_plan_file("/plans/plan.md")
    assert is_session_plan_file("/plans/plan-agent-x.md")
    assert not is_session_plan_file("/src/main.py")
    assert not is_session_plan_file("/plans/notes.txt")


async def test_enter_root_ok_subagent_blocked():
    """A3: guard root-only por is_subagent (no agent_id)."""
    root = ToolUseContext(session_id="s1", agent_id="a-root", is_subagent=False)
    res = await EnterPlanModeTool().execute({}, ctx=root)
    assert not res.is_error
    root = res.context_modifier(root)  # type: ignore[attr-defined]
    assert root.app_state.native[_PLAN_MODE_KEY] is True

    sub = ToolUseContext(session_id="s1", agent_id="a-child", is_subagent=True)
    res = await EnterPlanModeTool().execute({}, ctx=sub)
    assert res.is_error and "subagent" in res.output.lower()


async def test_exit_reads_disk_arms_oneshot_and_ends_turn():
    """B1/B3/B9/B10: lee plan de disco, cierra turno, arma one-shot con plan inline."""
    ctx = _ctx_in_plan("1. foo\n2. verify")
    res = await ExitPlanModeTool().execute({}, ctx)
    assert not res.is_error
    assert getattr(res, "ends_turn", False) is True
    ctx = res.context_modifier(ctx)  # type: ignore[attr-defined]
    assert _PLAN_MODE_KEY not in ctx.app_state.native
    assert ctx.app_state.native[_PLAN_EXIT_PENDING_KEY] is True

    out = PlanModeProvider().active_context(ctx)
    assert len(out) == 1 and "Exited Plan Mode" in out[0]["content"]
    assert "1. foo" in out[0]["content"]  # B10: plan inline (enriquecido)
    assert PlanModeProvider().active_context(ctx) == []  # one-shot


def test_provider_full_then_sparse_and_subagent_reminder():
    """F1/F3/F4: full→sparse en root; subagente recibe read-only, no 5-fases."""
    prov = PlanModeProvider()
    ctx = ToolUseContext(session_id="s1")
    ctx.app_state.native[_PLAN_MODE_KEY] = True
    full = prov.active_context(ctx)[0]["content"]
    assert "Phase 1" in full and "Phase 5" in full
    assert EXPLORE_AGENT_TYPE in full and PLAN_AGENT_TYPE in full
    sparse = prov.active_context(ctx)[0]["content"]
    assert sparse != full and "still active" in sparse

    sub = ToolUseContext(session_id="s1", is_subagent=True, agent_id="a1")
    sub.app_state.native[_PLAN_MODE_KEY] = True
    rem = prov.active_context(sub)[0]["content"]
    assert "READ-ONLY" in rem and "Phase 1" not in rem


def test_provider_silent_without_plan_mode():
    assert PlanModeProvider().active_context(ToolUseContext(session_id="s1")) == []


# ===========================================================================
# Gaps (xfail strict) — su fallo ES la evidencia del gap
# ===========================================================================

def test_enter_has_when_to_use_prompt():
    """`FIND-PLAN1` PAGADO (`GAP-PROMPT-1`): el `prompt()` de `EnterPlanMode` está portado.

    Era un `xfail(strict=True)` y se puso ROJO por XPASS al pagarse la deuda, que es
    exactamente para lo que estaba el `strict`. Al convertirlo en aserción dura se
    aprovecha para subir el listón (`H-L4`): la versión anterior se conformaba con
    `"When to Use" in text`, y eso lo cumple casi cualquier texto con secciones. Lo
    que hay que acreditar es que se portó **la rama que le toca a B**.
    """
    tool = EnterPlanModeTool()
    prompt = getattr(tool, "prompt", None)
    text = prompt() if callable(prompt) else (tool.description or "")

    # Estructura del canónico (`EnterPlanModeTool/prompt.ts:25-97`).
    assert "## When to Use This Tool" in text
    assert "## When NOT to Use This Tool" in text
    assert "### GOOD - Use EnterPlanMode:" in text
    assert "### BAD - Don't use EnterPlanMode:" in text

    # Discriminador de RAMA, que es lo que el test viejo no miraba: B no es un build
    # interno (`:166-170`, `USER_TYPE === 'ant'`), así que le corresponde la EXTERNAL.
    # Las dos aperturas son mutuamente excluyentes y distinguen las ramas sin ambigüedad.
    assert "**Prefer using EnterPlanMode** for implementation tasks unless they're simple" in text
    assert "genuine ambiguity about the right approach" not in text, (
        "se portó la rama Ant (`:108`), que es más restrictiva y no le corresponde a B"
    )

    # `WHAT_HAPPENS_SECTION` (`:4-14`): en A se omite sólo cuando el `plan_mode`
    # attachment la trae por otra vía (`:19-21`); en B no existe esa vía, así que va.
    assert "## What Happens in Plan Mode" in text
    # …y con los nombres de tool de B, no los de A: anunciar `Glob`/`Read` mandaría al
    # modelo a tools que en B no se llaman así.
    assert "using glob, grep, and read_file tools" in text


async def test_exit_outside_plan_mode_is_error():
    """`FIND-PLAN2`/`FIND-EXITPLAN` — PAGADO. Espejo de `ExitPlanModeV2Tool.ts:203-218`
    (`validateInput`, errorCode 1): fuera de plan mode se rechaza, **aunque haya plan-file**.
    Con plan-file y sin modo activo, antes la salida tenía éxito y armaba el one-shot de
    aprobación de un modo que no estaba puesto."""
    ctx = ToolUseContext(session_id="s1", storage=_FakePlanStorage({"/plans/plan.md": "p"}))
    # plan_mode NO activo
    res = await ExitPlanModeTool().execute({}, ctx)
    assert res.is_error and "plan mode" in res.output.lower()
    # Mensaje canónico literal, no una paráfrasis nuestra.
    assert "You are not in plan mode." in res.output
    # No sembró el one-shot de aprobación.
    assert _PLAN_EXIT_PENDING_KEY not in ctx.app_state.native


@pytest.mark.xfail(strict=True, reason="FIND-PLAN3: agentes built-in Explore/Plan no registrados")
def test_builtin_explore_plan_agents_registered():
    from agentic_runtime.execution.agents import BUILTIN_AGENTS  # type: ignore

    types = {a.agent_type for a in BUILTIN_AGENTS}
    assert EXPLORE_AGENT_TYPE in types and PLAN_AGENT_TYPE in types


@pytest.mark.xfail(strict=True, reason="FIND-PLAN5: plan_mode_reentry no portado")
def test_reentry_guidance_on_existing_plan():
    prov = PlanModeProvider()
    ctx = _ctx_in_plan("existing plan")
    ctx.app_state.native.pop("plan_mode_full_shown", None)
    ctx.app_state.native["plan_mode_reentered"] = True  # sembrado esperado por EnterPlanMode
    content = prov.active_context(ctx)[0]["content"]
    assert "Re-entering Plan Mode" in content


@pytest.mark.xfail(strict=True, reason="FIND-PLAN6: plan no re-inyectado tras compactación")
def test_compact_context_preserves_plan():
    prov = PlanModeProvider()
    ctx = _ctx_in_plan("the plan body")
    out = prov.compact_context(ctx)
    assert out and "the plan body" in out[0]["content"]


@pytest.mark.xfail(strict=True, reason="FIND-PLAN12: reminder de subagente sin su plan-file path")
def test_subagent_reminder_includes_plan_path():
    prov = PlanModeProvider()
    sub = ToolUseContext(session_id="s1", is_subagent=True, agent_id="a1")
    sub.app_state.native[_PLAN_MODE_KEY] = True
    rem = prov.active_context(sub)[0]["content"]
    assert "/plans/plan-agent-a1.md" in rem
