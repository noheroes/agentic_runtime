from __future__ import annotations

from typing import TYPE_CHECKING

from ...execution.fork import ForkSnapshot
from ...execution.runner import SubagentSpec
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

AGENT_TOOL_NAME = "Agent"

_MAX_SUBAGENT_DEPTH = 5


class AgentTool:
    name = AGENT_TOOL_NAME
    # Homologada contra `AgentTool/prompt.ts:66-287` (`getPrompt()`), `GAP-PROMPT-1`, rama NO-coordinator
    # y con `isForkSubagentEnabled()` en falso (`:78`), que es la que corresponde a B:
    # B no forkea omitiendo `subagent_type`, tiene un parámetro propio
    # (`inherit_messages`) con mecánica distinta, así que la sección «When to fork»
    # (`:83-96`) describiría una conducta que B no tiene.
    #
    # OMITIDO Y DECLARADO — nada de esto existe en el esquema ni en la superficie de B,
    # y anunciarlo repetiría `FIND-E11-3`:
    #   · `isolation: "worktree"` / `"remote"` (`:272-275`)
    #   · `name`, `team_name`, `mode` (`:277-283`) — ramas de teammate
    #   · la continuación vía `SendMessage` (`:267`): esa tool no está en el censo de B
    #   · el `concurrencyNote` por tipo de suscripción (`:245-249`)
    #
    # ⚠ HUECO CONOCIDO Y NO TAPADO AQUÍ: el `agentListSection` (`:196-199`), que es lo
    # único que le dice al modelo QUÉ subagentes existen. B no tiene ni la enumeración
    # ni el listado, y por eso NO se escribe aquí la frase de A «Available agent types
    # are listed in <system-reminder> messages»: en B sería FALSA. Es `FIND-AGENT-LIST-1`
    # y se paga entero y aparte; taparlo con una frase sería fabricar una coartada.
    description = """Launch a new agent to handle complex, multi-step tasks autonomously.

The Agent tool launches specialized agents (subprocesses) that autonomously handle complex tasks. \
Each agent type has specific capabilities and tools available to it.

When using the Agent tool, specify a subagent_type parameter to select which agent type to use. \
If omitted, the general-purpose agent is used.

When NOT to use the Agent tool:
- If you want to read a specific file path, use the read_file tool or the glob tool instead of the \
Agent tool, to find the match more quickly
- If you are searching for a specific class definition like "class Foo", use the glob tool instead, \
to find the match more quickly
- If you are searching for code within a specific file or set of 2-3 files, use the read_file tool \
instead of the Agent tool, to find the match more quickly
- Other tasks that are not related to the agent descriptions above

Usage notes:
- Always include a short description (3-5 words) summarizing what the agent will do
- When the agent is done, it will return a single message back to you. The result returned by the \
agent is not visible to the user. To show the user the result, you should send a text message back \
to the user with a concise summary of the result.
- You can optionally run agents in the background using the run_in_background parameter. When an \
agent runs in the background, you will be automatically notified when it completes — do NOT sleep, \
poll, or proactively check on its progress. Continue with other work or respond to the user instead.
- **Foreground vs background**: Use foreground (default) when you need the agent's results before \
you can proceed — e.g., research agents whose findings inform your next steps. Use background when \
you have genuinely independent work to do in parallel.
- Each Agent invocation starts fresh — provide a complete task description.
- The agent's outputs should generally be trusted
- Clearly tell the agent whether you expect it to write code or just to do research (search, file \
reads, web fetches, etc.), since it is not aware of the user's intent
- If the agent description mentions that it should be used proactively, then you should try your \
best to use it without the user having to ask for it first. Use your judgement.
- If the user specifies that they want you to run agents "in parallel", you MUST send a single \
message with multiple Agent tool use content blocks. For example, if you need to launch both a \
build-validator agent and a test-runner agent in parallel, send a single message with both tool \
calls.

## Writing the prompt

Brief the agent like a smart colleague who just walked into the room — it hasn't seen this \
conversation, doesn't know what you've tried, doesn't understand why this task matters.
- Explain what you're trying to accomplish and why.
- Describe what you've already learned or ruled out.
- Give enough context about the surrounding problem that the agent can make judgment calls rather \
than just following a narrow instruction.
- If you need a short response, say so ("report in under 200 words").
- Lookups: hand over the exact command. Investigations: hand over the question — prescribed steps \
become dead weight when the premise is wrong.

Terse command-style prompts produce shallow, generic work.

**Never delegate understanding.** Don't write "based on your findings, fix the bug" or "based on \
the research, implement it." Those phrases push synthesis onto the agent instead of doing it \
yourself. Write prompts that prove you understood: include file paths, line numbers, what \
specifically to change.
"""
    input_schema = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The task or question for the subagent.",
            },
            "description": {
                "type": "string",
                "description": "Short description of what the subagent will do.",
            },
            "run_in_background": {
                "type": "boolean",
                "description": (
                    "Set to true to run this agent in the background. "
                    "You will be notified when it completes."
                ),
                "default": False,
            },
            "subagent_type": {
                "type": "string",
                "description": "The type of specialized agent to use for this task.",
            },
            "model_override": {
                "type": "string",
                "description": "Optional model ID to use for the subagent.",
            },
            "inherit_messages": {
                "type": "boolean",
                "description": "Whether the subagent inherits the current conversation history.",
                "default": False,
            },
        },
        "required": ["prompt", "description"],
    }
    category = ToolCategory.BACKGROUND
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 600.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        prompt = input.get("prompt", "")
        run_in_background: bool = bool(input.get("run_in_background", False))
        subagent_type: str | None = input.get("subagent_type")
        model_override: str | None = input.get("model_override")
        inherit_messages: bool = bool(input.get("inherit_messages", False))

        if not prompt:
            return ToolResult.error(self.name, "prompt is required.")

        if ctx.subagent_depth >= _MAX_SUBAGENT_DEPTH:
            return ToolResult.error(
                self.name,
                f"Maximum subagent depth ({_MAX_SUBAGENT_DEPTH}) reached.",
            )

        # `S18` por DI (`C8`): la costura llega en el `ctx`, puesta por el runtime que
        # la recibió del ensamblador. Con el singleton global esto era
        # `get_runner()`, que en producción **siempre** levantaba `RuntimeError` porque
        # `create_runtime` no llamaba a `set_runner` (`FIND-EXEC1`).
        runner = ctx.runner
        if runner is None:
            return ToolResult.error(
                self.name,
                "Subagent runner not wired: this runtime was assembled without `S18` "
                "(RuntimeConfig.subagent_runner_factory / LocalAgentRuntime(runner_factory=…)).",
            )

        snapshot = ForkSnapshot(
            session_id=ctx.session_id,
            scope=ctx.scope,
            subagent_depth=ctx.subagent_depth,
            messages=tuple(ctx.messages) if inherit_messages else (),
            permissions=ctx.permission_context,
            tool_pool=ctx.tool_pool,
            capabilities=ctx.app_state.capabilities,
        )

        spec = SubagentSpec(
            prompt=prompt,
            description=input.get("description", "") or prompt[:80],
            subagent_type=subagent_type,
            model_override=model_override,
            # Token OPACO heredado: el runtime lo transporta, no lo interpreta (`D-11`).
            parent_session_id=ctx.session_id,
            parent_snapshot=snapshot,
            inherit_messages=inherit_messages,
        )

        try:
            result = await runner.run(spec, background=run_in_background)
        except Exception as e:
            return ToolResult.error(self.name, f"Subagent failed: {e}")

        if run_in_background:
            task_id = result or "unknown"
            return ToolResult(
                tool_name=self.name,
                output=f"Subagent started in background. Task ID: {task_id}",
            )

        return ToolResult(
            tool_name=self.name,
            output=result or "(no output)",
        )
