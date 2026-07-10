"""`PlanModeProvider` — capa de instrucciones de plan mode (por-turno) + one-shot de salida.

Homólogo de la capa de attachments del canónico (`utils/messages.ts:getPlanModeV2Instructions`
+ `getPlanModeV2SparseInstructions` + `getPlanModeV2SubAgentInstructions`, y el `plan_mode_exit`).
NO es system prompt base: es contexto por-turno que se regenera MIENTRAS `mode==='plan'`, con
cadencia **full→sparse** (la primera iteración rinde el workflow completo de 5 fases; las
siguientes, un recordatorio escueto). Al salir, rinde UNA vez el plan aprobado.

Sin tools ni catálogo: contexto puro (como `MemoryProvider`). El plan-file es la fuente de verdad
(el modelo lo escribe durante plan mode vía la write-tool); ver `plan_file.py`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .plan_file import (
    _PLAN_EXIT_PENDING_KEY,
    _PLAN_FULL_SHOWN_KEY,
    _PLAN_KEY,
    _PLAN_MODE_KEY,
    EXPLORE_AGENT_TYPE,
    PLAN_AGENT_TYPE,
    get_plan_file_path,
    plan_file_exists,
)

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext
    from ..contracts import CapabilitySummary
    from ...tools.protocol import ToolProtocol


def _plan_file_info(token: str, exists: bool) -> str:
    """Espejo de `planFileInfo` (messages.ts:3223): existe → editar incremental; no → crear."""
    if exists:
        return (
            f"A plan file already exists at {token}. You can read it and make incremental edits "
            "using the Edit tool."
        )
    return (
        f"No plan file exists yet. You should create your plan at {token} using the write_file tool."
    )


def _render_plan_full(context: "ToolUseContext") -> str:
    """Workflow completo de 5 fases (espejo de `getPlanModeV2Instructions`, messages.ts:3207).

    El ROOT orquesta: lanza subagentes `Explore` (P1) y `Plan` (P2), revisa (P3), escribe el
    plan-file (P4) y llama `ExitPlanMode` (P5). El plan-file es el ÚNICO write permitido."""
    token = get_plan_file_path(context)
    plan_file_info = _plan_file_info(token, plan_file_exists(context))
    return f"""Plan mode is active. The user indicated that they do not want you to execute yet -- you MUST NOT make any edits (with the exception of the plan file mentioned below), run any non-readonly tools (including changing configs or making commits), or otherwise make any changes to the system. This supercedes any other instructions you have received.

## Plan File Info:
{plan_file_info}
You should build your plan incrementally by writing to or editing this file. NOTE that this is the only file you are allowed to edit - other than this you are only allowed to take READ-ONLY actions.

## Plan Workflow

### Phase 1: Initial Understanding
Goal: Gain a comprehensive understanding of the user's request by reading through code. Critical: in this phase you should only use the {EXPLORE_AGENT_TYPE} subagent type.
Launch one or more {EXPLORE_AGENT_TYPE} agents IN PARALLEL (a single message with multiple Agent tool calls, each with subagent_type={EXPLORE_AGENT_TYPE!r}) to explore efficiently. Use 1 agent for a small targeted change or when the user gave specific paths; use several when the scope is uncertain or multiple areas are involved. Give each agent a specific search focus.

### Phase 2: Design
Goal: Design an implementation approach.
Launch {PLAN_AGENT_TYPE} agent(s) (the Agent tool with subagent_type={PLAN_AGENT_TYPE!r}) to design the implementation based on the user's intent and your Phase 1 exploration. The {PLAN_AGENT_TYPE} agent is READ-ONLY: it designs and reports, it does NOT write files or exit plan mode. In the agent prompt: provide comprehensive background from Phase 1 (filenames, code-path traces), describe requirements and constraints, and request a detailed implementation plan.

### Phase 3: Review
Goal: Review the plan(s) from Phase 2 and ensure alignment with the user's intentions.
1. Read the critical files identified by the agents to deepen your understanding.
2. Ensure the plans align with the user's original request.
3. Use AskUserQuestion to clarify any remaining questions with the user.

### Phase 4: Final Plan
Goal: Write your final plan to the plan file (the only file you can edit).
- Begin with a **Context** section: why this change is being made — the problem it addresses and the intended outcome.
- Include only your recommended approach, not all alternatives.
- Include the paths of critical files to be modified, and existing functions/utilities to reuse (with their file paths).
- Include a **Verification** section: how to test the changes end-to-end.

### Phase 5: Call ExitPlanMode
At the very end of your turn, once you are happy with your final plan file, call ExitPlanMode to present it for approval. Your turn should ONLY end with either AskUserQuestion (to clarify) or ExitPlanMode (to request approval).

**Important:** Use AskUserQuestion ONLY to clarify requirements or choose between approaches. Use ExitPlanMode to request plan approval — do NOT ask about approval any other way (no text questions like "Is this plan okay?")."""


def _render_plan_sparse(context: "ToolUseContext") -> str:
    """Recordatorio escueto de iteraciones siguientes (espejo de `getPlanModeV2SparseInstructions`)."""
    token = get_plan_file_path(context)
    return (
        f"Plan mode still active (see full instructions earlier in the conversation). Read-only "
        f"except the plan file ({token}). Follow the 5-phase workflow: {EXPLORE_AGENT_TYPE} agents "
        f"→ {PLAN_AGENT_TYPE} agents → review → write the plan file → ExitPlanMode. End turns with "
        "AskUserQuestion (to clarify) or ExitPlanMode (for approval). Never ask about plan approval "
        "via text or AskUserQuestion."
    )


def _render_subagent_reminder() -> str:
    """Recordatorio para subagentes en plan mode (espejo de `getPlanModeV2SubAgentInstructions`).

    Los subagentes `Explore`/`Plan` ya son read-only por su toolset; este recordatorio refuerza la
    restricción y NO les pide orquestar (no lanzan otros agentes ni salen de plan mode)."""
    return (
        "Plan mode is active. You MUST NOT make any edits, run any non-readonly tools (including "
        "changing configs or making commits), or otherwise make any changes to the system. Take "
        "READ-ONLY actions only. Answer the query comprehensively; use AskUserQuestion if you need "
        "to clarify the user's intent before proceeding."
    )


def _render_exit_reminder(plan: str) -> str:
    """Espejo de `plan_mode_exit` con el plan aprobado inline (cacheado del plan-file en `native`).

    Lenguaje neutro y positivo (qué hacer): el plan ya está aprobado, síguelo."""
    plan = plan.strip()
    body = (
        "## Exited Plan Mode\n\n"
        "You have exited plan mode. You can now make edits, run tools, and take actions. "
        "The approved plan is below — follow it."
    )
    if plan:
        body += f"\n\n{plan}"
    return body


class PlanModeProvider:
    """`CapabilityProvider` del plan — sin tools ni catálogo (contexto puro)."""

    name = "plan"

    async def startup(self) -> None: ...

    async def shutdown(self) -> None: ...

    def catalog(self, context: "ToolUseContext") -> list["CapabilitySummary"]:
        return []

    def tools(self, context: "ToolUseContext") -> list["ToolProtocol"]:
        return []

    def active_context(self, context: "ToolUseContext") -> list[dict]:
        """Orientación de plan mode:

        - MIENTRAS `plan_mode` activo:
          - subagente → recordatorio read-only (no orquesta);
          - root → workflow de 5 fases con cadencia full (1ª iter) → sparse (siguientes).
        - AL SALIR (`ExitPlanMode` armó el one-shot): rinde el plan aprobado UNA vez.

        Excluyentes por estado: `ExitPlanMode` hace `pop(plan_mode)` y arma el exit_pending en el
        mismo turno, así que nunca coinciden."""
        native = context.app_state.native
        if native.get(_PLAN_MODE_KEY):
            if context.is_subagent:
                return [{"role": "system", "content": _render_subagent_reminder()}]
            if not native.get(_PLAN_FULL_SHOWN_KEY):
                native[_PLAN_FULL_SHOWN_KEY] = True
                return [{"role": "system", "content": _render_plan_full(context)}]
            return [{"role": "system", "content": _render_plan_sparse(context)}]
        if not native.pop(_PLAN_EXIT_PENDING_KEY, False):
            return []
        plan = native.get(_PLAN_KEY, "")
        return [{"role": "system", "content": _render_exit_reminder(plan)}]

    def compact_context(self, context: "ToolUseContext") -> list[dict]:
        # Tras compactación el flag ya se consumió; el plan sigue en `app_state.native`
        # y el modelo puede re-leerlo, pero no se re-emite el one-shot.
        return []


__all__ = ["PlanModeProvider"]
