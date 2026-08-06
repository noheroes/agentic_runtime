from __future__ import annotations

from typing import TYPE_CHECKING

from ..exec_env import LocalExecEnvironment
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext


class BashTool:
    name = "bash"
    # Homologada contra `getSimplePrompt()` (`BashTool/prompt.ts:275-369`) — `GAP-PROMPT-1`.
    # El bloque PORTANTE es el de preferencia de tools (`:280-291` + el IMPORTANT de `:359`):
    # es como A DIRIGE la elección hacia las tools dedicadas, y su ausencia en B costaba ~25 %
    # de las corridas de `E2g` (el modelo llegaba a `glob` y se rendía sin leer el fichero).
    # A lo emite CONDICIONALMENTE (`:276-286`: lo retira si el build lleva find/grep embebidos),
    # luego es deliberado, no decorativo.
    # OMITIDO A PROPÓSITO lo que B no tiene: `timeout` y `run_in_background` como parámetros
    # (el timeout aquí es fijo), el sandbox, y el bloque de git/PR de `:42-161` —ese último
    # describe un flujo del integrador, no del runtime—. Sí se conserva la guía de git de
    # `:304-308`, que es advertencia de conducta y aplica igual.
    description = """Executes a given shell command and returns its output.

The working directory persists between commands, but shell state does not.

IMPORTANT: Avoid using this tool to run `find`, `grep`, `cat`, `head`, `tail`, `sed`, `awk`,
or `echo` commands, unless explicitly instructed or after you have verified that a dedicated
tool cannot accomplish your task. Instead, use the appropriate dedicated tool:

- File search: Use glob (NOT find or ls)
- Content search: Use grep (NOT grep or rg as shell commands)
- Read files: Use read_file (NOT cat/head/tail)
- Edit files: Use Edit (NOT sed/awk)
- Write files: Use write_file (NOT echo > or cat <<EOF)
- Communication: Output text directly (NOT echo/printf)

While this tool can do similar things, the dedicated tools are better: they are confined to
the workspace, return structured results, and are easier to review.

# Instructions
- If your command will create new directories or files, first verify the parent directory
  exists and is the correct location.
- Always quote file paths that contain spaces with double quotes.
- Prefer absolute paths and avoid `cd`, so the working directory stays stable.
- When issuing multiple commands:
  - If they are independent, make multiple tool calls in a single message so they run in
    parallel.
  - If they depend on each other, use a single call chaining them with '&&'.
  - Use ';' only when order matters but earlier failures do not.
  - Do NOT use newlines to separate commands (newlines are fine inside quoted strings).
- For git commands:
  - Prefer creating a new commit over amending an existing one.
  - Before destructive operations (`git reset --hard`, `git push --force`, `git checkout --`),
    consider whether a safer alternative achieves the same goal.
  - Never skip hooks (`--no-verify`) or bypass signing unless the user explicitly asked. If a
    hook fails, investigate and fix the underlying issue.
  - Never use interactive flags (`-i`), which cannot work here.
- Avoid unnecessary `sleep` commands: do not sleep between commands that can run immediately,
  and do not retry failing commands in a sleep loop — diagnose the root cause instead."""
    input_schema = {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = True
    safe_for_background = True
    timeout_seconds = 30.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        command = input.get("command", "")
        exec_env = getattr(ctx, "exec_env", None) or LocalExecEnvironment()
        try:
            result = await exec_env.run_shell(command, timeout=self.timeout_seconds)
            return ToolResult(
                tool_name=self.name,
                output=result.output,
                is_error=result.returncode != 0,
            )
        except Exception as exc:
            return ToolResult.error(self.name, str(exc))
