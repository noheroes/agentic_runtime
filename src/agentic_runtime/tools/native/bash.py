from __future__ import annotations

import os
from typing import TYPE_CHECKING

from ..exec_env import ExecEnvironmentUnavailable, require_exec_env
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

    @staticmethod
    def _workspace_root(ctx: ToolUseContext) -> str | None:
        """Raíz declarada por el integrador — el análogo de `getOriginalCwd()` de A.

        Es el `write_root` del confinamiento y no una constante: el workspace al que ya
        están confinadas `read_file`/`write_file`. Que `bash` corriera en otro sitio es
        justo el defecto #1.
        """
        root = getattr(getattr(ctx, "fs", None), "write_root", None)
        return str(root) if root is not None else None

    def _resolve_cwd(self, ctx: ToolUseContext) -> tuple[str | None, str | None]:
        """`(cwd, error)` — recuperación calcada de `Shell.ts:220-238`.

        Si el cwd vigente desapareció del disco (un comando puede borrar su propio
        directorio), A **no** deja que el spawn reviente: cae al cwd original y, si ese
        tampoco existe, falla con un mensaje accionable en vez de con un errno.
        """
        fallback = self._workspace_root(ctx)
        cwd = getattr(ctx, "cwd", None) or fallback
        if cwd is None:
            return None, None  # sin workspace declarado: comportamiento previo (cwd del proceso)
        if os.path.isdir(cwd):
            return cwd, None
        if fallback is not None and fallback != cwd and os.path.isdir(fallback):
            return fallback, None
        return None, (
            f'Working directory "{cwd}" no longer exists. '
            "Please restart from an existing directory."
        )

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        command = input.get("command", "")
        # Sin costura de ejecución NO se ejecuta (problema `#2`). El default vive en el
        # ensamblador (`factory.py:256`), no aquí: un `or LocalExecEnvironment()` local
        # degradaba en silencio de «sandbox inyectado» a «host», que es el footgun que A
        # cerró en #34044 (`sandbox-adapter.ts:549-560`). Se comprueba ANTES del cwd para
        # que el motivo que sale sea el real y no el del directorio.
        try:
            exec_env = require_exec_env(ctx)
        except ExecEnvironmentUnavailable as exc:
            return ToolResult.error(self.name, str(exc))
        cwd, cwd_error = self._resolve_cwd(ctx)
        if cwd_error is not None:
            return ToolResult.error(self.name, cwd_error)
        try:
            result = await exec_env.run_shell(command, cwd=cwd, timeout=self.timeout_seconds)
            # Escritura de vuelta del cwd releído (A: `setCwd(newCwd)`, `Shell.ts:385-421`):
            # así un `cd` persiste entre comandos DEL TURNO. `None` = el backend no lo
            # rastrea (bwrap) y entonces no se toca nada: adoptar un path no verificado
            # sería peor que no persistir.
            tracked = getattr(result, "cwd", None)
            # `preventCwdChanges = !isMainThread` (`Shell.ts:385`, ítem B11 de `10-tools-native`):
            # A gatea justo esta escritura para los no-main-thread. Un subagente puede hacer
            # `cd` dentro de SU comando, pero no mover el cwd que comparte con quien lo lanzó.
            # Sin esta guarda, hacer persistir el cwd habría abierto un agujero que A cierra.
            if getattr(ctx, "is_subagent", False):
                tracked = None
            if tracked:
                try:
                    ctx.cwd = tracked
                except (AttributeError, ValueError):
                    pass  # ctx sin el cable (fake de test): el comando ya corrió, no se rompe
            return ToolResult(
                tool_name=self.name,
                output=result.output,
                is_error=result.returncode != 0,
            )
        except Exception as exc:
            return ToolResult.error(self.name, str(exc))
