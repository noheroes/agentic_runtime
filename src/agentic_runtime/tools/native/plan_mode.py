from __future__ import annotations

from typing import TYPE_CHECKING

from ..protocol import ToolCategory, ToolResult
# La capa plan-file (token + lectura vía storage inyectado) vive en un módulo hoja para que tanto
# esta tool como el `PlanModeProvider` la importen sin ciclo. Re-exportados aquí por compat.
from ...capabilities.plan.plan_file import (  # noqa: F401
    _PLAN_EXIT_PENDING_KEY,
    _PLAN_FULL_SHOWN_KEY,
    _PLAN_KEY,
    _PLAN_MODE_KEY,
    get_plan,
    get_plan_file_path,
)

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

ENTER_PLAN_MODE_TOOL_NAME = "EnterPlanMode"
EXIT_PLAN_MODE_TOOL_NAME = "ExitPlanMode"


class EnterPlanModeTool:
    name = ENTER_PLAN_MODE_TOOL_NAME
    # Homologada contra `EnterPlanModeTool/prompt.ts:16-99`, `GAP-PROMPT-1`, rama **EXTERNAL**
    # (`getEnterPlanModeToolPromptExternal`). El selector es `process.env.USER_TYPE ===
    # 'ant'` (`:166-170`): B no es un build interno, así que la rama Ant (`:101-164`),
    # que es MÁS restrictiva («genuine ambiguity»), no le corresponde.
    # Incluye `WHAT_HAPPENS_SECTION` (`:4-14`) porque en B no hay `plan_mode` attachment
    # que la traiga por otra vía; en A se omite justo cuando esa vía existe (`:19-21`).
    # ADAPTADO: los nombres de tool son los de B (`glob`, `grep`, `read_file`).
    # OMITIDO Y DECLARADO: «with explore agent» (`:63`) — B no publica ningún listado de
    # subagentes (`FIND-AGENT-LIST-1`), así que nombrar uno concreto sería falso.
    description = """Use this tool proactively when you're about to start a non-trivial \
implementation task. Getting user sign-off on your approach before writing code prevents wasted \
effort and ensures alignment. This tool transitions you into plan mode where you can explore the \
codebase and design an implementation approach for user approval.

## When to Use This Tool

**Prefer using EnterPlanMode** for implementation tasks unless they're simple. Use it when ANY of \
these conditions apply:

1. **New Feature Implementation**: Adding meaningful new functionality
   - Example: "Add a logout button" - where should it go? What should happen on click?
   - Example: "Add form validation" - what rules? What error messages?

2. **Multiple Valid Approaches**: The task can be solved in several different ways
   - Example: "Add caching to the API" - could use Redis, in-memory, file-based, etc.
   - Example: "Improve performance" - many optimization strategies possible

3. **Code Modifications**: Changes that affect existing behavior or structure
   - Example: "Update the login flow" - what exactly should change?
   - Example: "Refactor this component" - what's the target architecture?

4. **Architectural Decisions**: The task requires choosing between patterns or technologies
   - Example: "Add real-time updates" - WebSockets vs SSE vs polling
   - Example: "Implement state management" - Redux vs Context vs custom solution

5. **Multi-File Changes**: The task will likely touch more than 2-3 files
   - Example: "Refactor the authentication system"
   - Example: "Add a new API endpoint with tests"

6. **Unclear Requirements**: You need to explore before understanding the full scope
   - Example: "Make the app faster" - need to profile and identify bottlenecks
   - Example: "Fix the bug in checkout" - need to investigate root cause

7. **User Preferences Matter**: The implementation could reasonably go multiple ways
   - If you would use AskUserQuestion to clarify the approach, use EnterPlanMode instead
   - Plan mode lets you explore first, then present options with context

## When NOT to Use This Tool

Only skip EnterPlanMode for simple tasks:
- Single-line or few-line fixes (typos, obvious bugs, small tweaks)
- Adding a single function with clear requirements
- Tasks where the user has given very specific, detailed instructions
- Pure research/exploration tasks (use the Agent tool instead)

## What Happens in Plan Mode

In plan mode, you'll:
1. Thoroughly explore the codebase using glob, grep, and read_file tools
2. Understand existing patterns and architecture
3. Design an implementation approach
4. Present your plan to the user for approval
5. Use AskUserQuestion if you need to clarify approaches
6. Exit plan mode with ExitPlanMode when ready to implement

## Examples

### GOOD - Use EnterPlanMode:
User: "Add user authentication to the app"
- Requires architectural decisions (session vs JWT, where to store tokens, middleware structure)

User: "Optimize the database queries"
- Multiple approaches possible, need to profile first, significant impact

User: "Implement dark mode"
- Architectural decision on theme system, affects many components

User: "Add a delete button to the user profile"
- Seems simple but involves: where to place it, confirmation dialog, API call, error handling, \
state updates

User: "Update the error handling in the API"
- Affects multiple files, user should approve the approach

### BAD - Don't use EnterPlanMode:
User: "Fix the typo in the README"
- Straightforward, no planning needed

User: "Add a console.log to debug this function"
- Simple, obvious implementation

User: "What files handle routing?"
- Research task, not implementation planning

## Important Notes

- This tool REQUIRES user approval - they must consent to entering plan mode
- If unsure whether to use it, err on the side of planning - it's better to get alignment upfront \
than to redo work
- Users appreciate being consulted before significant changes are made to their codebase
"""
    input_schema = {"type": "object", "properties": {}}
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = False
    timeout_seconds = 5.0

    # `FIND-TOOL-ENABLED-1` — plan mode es una PUERTA DE UN SOLO SENTIDO cuando no
    # hay humano: se entra sin aprobación (`requires_permission = False`, pese a que
    # la descripción de arriba promete «This tool REQUIRES user approval»), el régimen
    # que impone dice «This supercedes any other instructions you have received», y la
    # única salida —`ExitPlanMode`— cierra el turno esperando una aprobación que nadie
    # va a dar. Medido dos veces en el E2g (`GATE_E2G_SEED` 29525785 y 1561952726).
    #
    # Es LITERALMENTE el caso que A guarda, y con la misma razón escrita en el
    # canónico (`EnterPlanModeTool.ts:56-67`): *«ExitPlanMode is disabled (its approval
    # dialog needs the terminal). Disable entry too so plan mode isn't a trap the model
    # can enter but never leave»*. Se apagan LAS DOS, como en A: apagar sólo la entrada
    # dejaría a `ExitPlanMode` publicada sin nada que la haga alcanzable.
    #
    # ⚠ NO se paga aquí, y queda DECLARADO — `FIND-PLAN-FILE-1`: aun con host
    # interactivo, el recordatorio de 5 fases ordena escribir el plan en `/plans/plan.md`
    # (`capabilities/plan/provider.py:41`) y `is_session_plan_file` —la exención del
    # candado que `plan_file.py:58-63` documenta como «lo consume el integrador»— no
    # tiene NINGÚN consumidor fuera de tests, en ninguno de los dos repos. Este apagado
    # saca plan mode de la medida headless; no arregla el cable que le falta.
    def __init__(self, *, interactive: bool = False) -> None:
        self._interactive = interactive

    def is_enabled(self) -> bool:
        return self._interactive

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        # El discriminador de subagente es `is_subagent`, no `agent_id` (que también se
        # asigna al contexto raíz como identidad). Mismo criterio que el resto del runtime
        # (resolver/agent_loop/runtime). Canónico: EnterPlanMode es root-only.
        if ctx.is_subagent:
            return ToolResult.error(
                self.name, "EnterPlanMode cannot be used inside a subagent."
            )

        def modifier(c: "ToolUseContext") -> "ToolUseContext":
            c.app_state.native[_PLAN_MODE_KEY] = True
            # Reinicia la cadencia: la primera iteración del nuevo plan mode rinde el reminder full.
            c.app_state.native.pop(_PLAN_FULL_SHOWN_KEY, None)
            return c

        return ToolResult(
            tool_name=self.name,
            output=(
                "Entered plan mode. Explore the codebase and design an implementation approach. "
                "DO NOT write or edit any files yet. "
                "When ready, use ExitPlanMode to present your plan for approval."
            ),
            context_modifier=modifier,
        )


class ExitPlanModeTool:
    name = EXIT_PLAN_MODE_TOOL_NAME
    # Homologada contra `ExitPlanModeTool/prompt.ts:7-27` (`EXIT_PLAN_MODE_V2_TOOL_PROMPT`),
    # `GAP-PROMPT-1`. Portada ÍNTEGRA: el stub externo del canónico ya excluye la sección
    # Ant-only (`:1`), y la conducta de B coincide — el plan se lee del plan-file, no se
    # pasa por parámetro, que es justo lo que el texto explica en `:11`.
    description = """Use this tool when you are in plan mode and have finished writing your plan \
to the plan file and are ready for user approval.

## How This Tool Works
- You should have already written your plan to the plan file specified in the plan mode system \
message
- This tool does NOT take the plan content as a parameter - it will read the plan from the file \
you wrote
- This tool simply signals that you're done planning and ready for the user to review and approve
- The user will see the contents of your plan file when they review it

## When to Use This Tool
IMPORTANT: Only use this tool when the task requires planning the implementation steps of a task \
that requires writing code. For research tasks where you're gathering information, searching \
files, reading files or in general trying to understand the codebase - do NOT use this tool.

## Before Using This Tool
Ensure your plan is complete and unambiguous:
- If you have unresolved questions about requirements or approach, use AskUserQuestion first (in \
earlier phases)
- Once your plan is finalized, use THIS tool to request approval

**Important:** Do NOT use AskUserQuestion to ask "Is this plan okay?" or "Should I proceed?" - \
that's exactly what THIS tool does. ExitPlanMode inherently requests user approval of your plan.

## Examples

1. Initial task: "Search for and understand the implementation of vim mode in the codebase" - Do \
not use the exit plan mode tool because you are not planning the implementation steps of a task.
2. Initial task: "Help me implement yank mode for vim" - Use the exit plan mode tool after you \
have finished planning the implementation steps of the task.
3. Initial task: "Add a new feature to handle user authentication" - If unsure about auth method \
(OAuth, JWT, etc.), use AskUserQuestion first, then use exit plan mode tool after clarifying the \
approach.
"""
    # Sin arg `plan`: el plan se lee del plan-file (fuente de verdad que el modelo escribió durante
    # plan mode). Homólogo de `ExitPlanModeV2Tool` (inputSchema interno sin `plan`, plan leído de
    # disco vía `getPlan`). Schema vacío = el modelo lo llama sin argumentos.
    input_schema = {"type": "object", "properties": {}}
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = False
    timeout_seconds = 5.0

    # Ver `EnterPlanModeTool.is_enabled`: en A la premisa del apagado es justamente que
    # ESTA tool no puede operar sin terminal, y la entrada se apaga en consecuencia.
    def __init__(self, *, interactive: bool = False) -> None:
        self._interactive = interactive

    def is_enabled(self) -> bool:
        return self._interactive

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        plan = await get_plan(ctx)
        if not plan or not plan.strip():
            return ToolResult.error(
                self.name,
                f"No plan found at {get_plan_file_path(ctx)}. Write your plan to the plan file "
                "before calling ExitPlanMode.",
            )
        plan = plan.strip()

        def modifier(c: "ToolUseContext") -> "ToolUseContext":
            c.app_state.native.pop(_PLAN_MODE_KEY, None)
            c.app_state.native.pop(_PLAN_FULL_SHOWN_KEY, None)
            # Cachea el plan leído del plan-file para el one-shot de salida del provider (sync),
            # que no puede releer storage (async). La fuente de verdad sigue siendo el plan-file.
            c.app_state.native[_PLAN_KEY] = plan
            c.app_state.native[_PLAN_EXIT_PENDING_KEY] = True
            return c

        # Presentar el plan CIERRA el turno: el agente se detiene a esperar la aprobación del
        # usuario en vez de seguir generando (sin esto el modelo narra el plan como aprobado y
        # anuncia implementación).
        #
        # ⚠ Esto **no** es espejo del canónico, y la nota anterior que lo llamaba «espejo de
        # `requiresUserInteraction()->true`» sobre-afirmaba: `requiresUserInteraction()` existe
        # en A (`AskUserQuestionTool.tsx:155`) pero NO cierra el turno — marca que la tool
        # necesita al usuario para que el gate de permisos la resuelva por
        # `checkPermissions → behavior:'ask' + updatedInput`, y el turno **continúa**. `endsTurn`
        # no existe en A. Es cable propio de B mientras esa capa de interacción (`GAP-02`/`K1`)
        # esté por encima de la línea de corte. Ver `ToolResult.ends_turn`.
        return ToolResult(
            tool_name=self.name,
            output=f"Plan submitted for approval:\n\n{plan}",
            context_modifier=modifier,
            ends_turn=True,
        )
