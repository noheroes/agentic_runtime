from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...capabilities.plan.plan_file import (
    _PLAN_EXIT_PENDING_KEY,
    _PLAN_FULL_SHOWN_KEY,
    _PLAN_KEY,
    _PLAN_MODE_KEY,
    get_plan,
    get_plan_file_path,
)
from ..protocol import PermissionDecision, ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

ENTER_PLAN_MODE_TOOL_NAME = "EnterPlanMode"
EXIT_PLAN_MODE_TOOL_NAME = "ExitPlanMode"

NOT_IN_PLAN_MODE_MESSAGE = (
    "You are not in plan mode. This tool is only for exiting plan mode after writing a "
    "plan. If your plan was already approved, continue with implementation."
)
PLAN_APPROVED_TEMPLATE = (
    "User has approved your plan. You can now start coding. Start with updating your todo "
    "list if applicable\n\n## Approved Plan:\n{plan}"
)
PLAN_APPROVED_EMPTY = "User has approved exiting plan mode. You can now proceed."
PLAN_REJECTION_PREFIX = (
    "The agent proposed a plan that was rejected by the user. The user chose to stay in "
    "plan mode rather than proceed with implementation.\n\nRejected plan:\n"
)


class EnterPlanModeTool:
    name = ENTER_PLAN_MODE_TOOL_NAME
    search_hint = "switch to plan mode to design an approach before coding"
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
    input_schema: dict[str, Any] = {"type": "object", "properties": {}}  # noqa: RUF012
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = False
    timeout_seconds = 5.0

    def __init__(self, *, interactive: bool = False) -> None:
        self._interactive = interactive

    def is_enabled(self) -> bool:
        return self._interactive

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        if ctx.is_subagent:
            return ToolResult.error(
                self.name, "EnterPlanMode cannot be used inside a subagent."
            )

        def modifier(c: ToolUseContext) -> ToolUseContext:
            c.app_state.native[_PLAN_MODE_KEY] = True
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
    search_hint = "present plan for approval and start coding (plan mode only)"
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
    input_schema: dict[str, Any] = {"type": "object", "properties": {}}  # noqa: RUF012
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = False
    timeout_seconds = 5.0

    def __init__(self, *, interactive: bool = False) -> None:
        self._interactive = interactive

    def is_enabled(self) -> bool:
        return self._interactive

    async def check_permissions(
        self, input: dict[str, Any], ctx: ToolUseContext
    ) -> PermissionDecision:
        if not ctx.app_state.native.get(_PLAN_MODE_KEY):
            return PermissionDecision.deny(NOT_IN_PLAN_MODE_MESSAGE)

        plan = await get_plan(ctx)
        if not plan or not plan.strip():
            return PermissionDecision.deny(
                f"No plan found at {get_plan_file_path(ctx)}. Write your plan to the plan file "
                "before calling ExitPlanMode."
            )
        plan = plan.strip()
        return PermissionDecision.ask(
            plan,
            remember=False,
            deny_message=f"{PLAN_REJECTION_PREFIX}{plan}",
        )

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        plan = (await get_plan(ctx) or "").strip()

        def modifier(c: ToolUseContext) -> ToolUseContext:
            c.app_state.native.pop(_PLAN_MODE_KEY, None)
            c.app_state.native.pop(_PLAN_FULL_SHOWN_KEY, None)
            c.app_state.native[_PLAN_KEY] = plan
            c.app_state.native[_PLAN_EXIT_PENDING_KEY] = True
            return c

        return ToolResult(
            tool_name=self.name,
            output=(
                PLAN_APPROVED_TEMPLATE.format(plan=plan) if plan else PLAN_APPROVED_EMPTY
            ),
            context_modifier=modifier,
        )
