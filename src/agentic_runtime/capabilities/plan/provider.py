from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .plan_file import (
    _PLAN_EXIT_PENDING_KEY,
    _PLAN_KEY,
    _PLAN_MODE_KEY,
    EXPLORE_AGENT_TYPE,
    PLAN_AGENT_TYPE,
    get_plan_file_path,
    plan_file_exists,
)

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext
    from ...tools.protocol import ToolProtocol
    from ..contracts import CapabilitySummary

TURNS_BETWEEN_ATTACHMENTS = 5
FULL_REMINDER_EVERY_N_ATTACHMENTS = 5

_REMINDER_TAG = "<system-reminder>"
_PLAN_MARKERS = ("Plan mode is active", "Plan mode still active")
_REENTRY_MARKER = "## Re-entering Plan Mode"
_EXIT_MARKER = "## Exited Plan Mode"


def _marked(message: dict[str, Any], markers: tuple[str, ...]) -> bool:
    if message.get("role") != "user":
        return False
    content = message.get("content")
    if not isinstance(content, str) or _REMINDER_TAG not in content:
        return False
    return any(marker in content for marker in markers)


def _is_human_turn(message: dict[str, Any]) -> bool:
    if message.get("role") != "user":
        return False
    content = message.get("content")
    return not isinstance(content, str) or _REMINDER_TAG not in content


def _plan_attachment_turn_count(messages: list[dict[str, Any]]) -> tuple[int, bool]:
    turns = 0
    for message in reversed(messages):
        if _marked(message, (*_PLAN_MARKERS, _REENTRY_MARKER)):
            return turns, True
        if _is_human_turn(message):
            turns += 1
    return turns, False


def _plan_attachments_since_exit(messages: list[dict[str, Any]]) -> int:
    count = 0
    for message in reversed(messages):
        if _marked(message, (_EXIT_MARKER,)):
            break
        if _marked(message, _PLAN_MARKERS):
            count += 1
    return count


def _reentry_pending(messages: list[dict[str, Any]]) -> bool:
    for message in reversed(messages):
        if _marked(message, (_REENTRY_MARKER,)):
            return False
        if _marked(message, (_EXIT_MARKER,)):
            return True
    return False


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


def _render_plan_full(context: ToolUseContext) -> str:
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


def _render_plan_sparse(context: ToolUseContext) -> str:
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


def _render_plan_reentry(context: ToolUseContext) -> str:
    token = get_plan_file_path(context)
    return f"""## Re-entering Plan Mode

You are returning to plan mode after having previously exited it. A plan file exists at {token} from your previous planning session.

**Before proceeding with any new planning, you should:**
1. Read the existing plan file to understand what was previously planned
2. Evaluate the user's current request against that plan
3. Decide how to proceed:
   - **Different task**: If the user's request is for a different task—even if it's similar or related—start fresh by overwriting the existing plan
   - **Same task, continuing**: If this is explicitly a continuation or refinement of the exact same task, modify the existing plan while cleaning up outdated or irrelevant sections
4. Continue on with the plan process and most importantly you should always edit the plan file one way or the other before calling ExitPlanMode

Treat this as a fresh planning session. Do not assume the existing plan is relevant without evaluating it first."""


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

    def catalog(self, context: ToolUseContext) -> list[CapabilitySummary]:
        return []

    def tools(self, context: ToolUseContext) -> list[ToolProtocol]:
        return []

    def active_context(self, context: ToolUseContext) -> list[dict[str, Any]]:
        native = context.app_state.native
        if not native.get(_PLAN_MODE_KEY):
            if not native.pop(_PLAN_EXIT_PENDING_KEY, False):
                return []
            plan = native.get(_PLAN_KEY, "")
            return [{"role": "system", "content": _render_exit_reminder(plan)}]

        native.pop(_PLAN_EXIT_PENDING_KEY, None)
        messages = context.messages
        turns, found = _plan_attachment_turn_count(messages)
        if found and turns < TURNS_BETWEEN_ATTACHMENTS:
            return []

        out: list[dict[str, Any]] = []
        if _reentry_pending(messages) and plan_file_exists(context):
            out.append({"role": "system", "content": _render_plan_reentry(context)})
        if context.is_subagent:
            out.append({"role": "system", "content": _render_subagent_reminder()})
            return out
        count = _plan_attachments_since_exit(messages) + 1
        if count % FULL_REMINDER_EVERY_N_ATTACHMENTS == 1:
            out.append({"role": "system", "content": _render_plan_full(context)})
        else:
            out.append({"role": "system", "content": _render_plan_sparse(context)})
        return out

    def compact_context(self, context: ToolUseContext) -> list[dict[str, Any]]:
        return []


__all__ = ["PlanModeProvider"]
