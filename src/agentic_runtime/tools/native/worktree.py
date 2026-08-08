"""Native tools: `EnterWorktree` / `ExitWorktree` — aislamiento por git worktree.

Tres reglas de costura que estas tools deben honrar y que en la primera versión NO
honraban (halladas en el barrido de las 18 tools nativas, ventana de `C6`):

- **`S15`**: git NO se lanza con `asyncio.create_subprocess_exec` directo. Se despacha por
  `ctx.exec_env.run_argv`, igual que `bash` despacha por `run_shell`. Con un
  `BwrapExecEnvironment` inyectado, la versión anterior dejaba `bash` aislado pero corría
  git **en el host**.
- **`S14`**: el destino del worktree se confina con `ctx.fs.resolve(..., for_write=True)`.
  Antes se componía a mano (`Path(git_root).parent / ".worktrees/…"`) y no pasaba por
  ningún allow-set.
- **`S12`**: los paths que salen al modelo se traducen con `ctx.presentation.to_llm`. Antes
  se interpolaba la ruta host cruda en `output=` (dos puntos de emisión).

Los paths que viajan en el `argv` de git son **relativos** al `cwd` a propósito: un argv con
path absoluto del host no significa lo mismo dentro del sandbox, donde el único árbol montado
es el workspace en `/workspace`. El `cwd` sí es absoluto del host porque `run_argv` lo traduce.

**Divergencia declarada**: el worktree se crea DENTRO del write-root (`.worktrees/<name>`),
no como hermano del git root. Un hermano cae fuera del allow-set de escritura, así que con la
ubicación anterior el confinamiento era inexpresable. Git admite worktrees anidados.
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..exec_env import ExecEnvironmentUnavailable, require_exec_env
from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

ENTER_WORKTREE_TOOL_NAME = "EnterWorktree"
EXIT_WORKTREE_TOOL_NAME = "ExitWorktree"

_WORKTREE_KEY = "worktree_session"
_SLUG_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _validate_slug(name: str) -> str | None:
    """Returns error message if invalid, None if ok."""
    if "/" in name:
        parts = name.split("/")
        if any(not _SLUG_RE.match(p) for p in parts if p):
            return "Each segment must contain only letters, digits, dots, underscores, dashes."
    elif not _SLUG_RE.match(name):
        return "Name must contain only letters, digits, dots, underscores, dashes (max 64 chars)."
    return None


async def _run(
    ctx: "ToolUseContext", argv: list[str], *, cwd: str, timeout: float
) -> tuple[int, str]:
    """Lanza `argv` por el `ToolExecEnvironment` inyectado. Devuelve (rc, salida combinada).

    `run_argv` combina stdout y stderr (es lo que `ShellResult` modela), así que las tools
    ya no discriminan una de otra: el mensaje de error usa la salida entera.
    """
    # Sin costura poblada **lanza** (problema `#2`): el fallback silencioso corría git en
    # el host con un `BwrapExecEnvironment` inyectado, que es el mismo bypass que la
    # cabecera de este módulo dice haber cerrado, un nivel más abajo.
    exec_env = require_exec_env(ctx)
    result = await exec_env.run_argv(argv, cwd=cwd, timeout=timeout)
    return result.returncode, result.output


class EnterWorktreeTool:
    name = ENTER_WORKTREE_TOOL_NAME
    # Homologada contra `EnterWorktreeTool/prompt.ts:2-26` (`getEnterWorktreeToolPrompt()`),
    # `GAP-PROMPT-1`.
    # OMITIDO Y DECLARADO:
    #   · los hooks `WorktreeCreate`/`WorktreeRemove` y la rama «fuera de un repo git»
    #     (`:19`, `:23`) — B no tiene esa costura: sin repo git, falla.
    #   · «prompted to keep or remove it on session exit» (`:25`) — es conducta de la CLI
    #     de A, no del runtime.
    # ADAPTADO a la divergencia YA declarada en la cabecera de este módulo: el worktree
    # se crea en `.worktrees/<name>` DENTRO del write-root, no en `.claude/worktrees/`
    # como dice `:23`. Decirlo aquí es obligatorio: si la descripción mintiera sobre la
    # ubicación, el modelo buscaría los ficheros donde no están.
    description = """Use this tool ONLY when the user explicitly asks to work in a worktree. \
This tool creates an isolated git worktree and switches the current session into it.

## When to Use

- The user explicitly says "worktree" (e.g., "start a worktree", "work in a worktree", "create a \
worktree", "use a worktree")

## When NOT to Use

- The user asks to create a branch, switch branches, or work on a different branch — use git \
commands instead
- The user asks to fix a bug or work on a feature — use normal git workflow unless they \
specifically mention worktrees
- Never use this tool unless the user explicitly mentions "worktree"

## Requirements

- Must be in a git repository
- Must not already be in a worktree

## Behavior

- Creates a new git worktree inside `.worktrees/` with a new branch based on HEAD
- Switches the session's working directory to the new worktree
- Use ExitWorktree to leave the worktree mid-session (keep or remove)

## Parameters

- `name` (optional): A name for the worktree. If not provided, a random name is generated.
"""
    input_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": (
                    "Optional name for the worktree branch. Each '/'-separated segment "
                    "may contain only letters, digits, dots, underscores, dashes (max 64 chars). "
                    "A random name is generated if not provided."
                ),
            }
        },
    }
    category = ToolCategory.SYSTEM
    requires_permission = True
    safe_for_background = False
    timeout_seconds = 30.0

    async def execute(self, input: dict[str, Any], ctx: "ToolUseContext") -> ToolResult:
        # Esta tool SIEMPRE lanza git; sin costura de ejecución no hay nada que hacer.
        try:
            require_exec_env(ctx)
        except ExecEnvironmentUnavailable as exc:
            return ToolResult.error(self.name, str(exc))
        if ctx.app_state.native.get(_WORKTREE_KEY):
            return ToolResult.error(self.name, "Already in a worktree session.")

        name = input.get("name") or f"agent-{uuid.uuid4().hex[:8]}"
        err = _validate_slug(name)
        if err:
            return ToolResult.error(self.name, err)

        branch = f"worktree/{name}"
        # El repo es el write-root de la sesión, no el cwd del proceso: sin `cwd` git
        # resolvía el toplevel del repo en que corre el RUNTIME, no el del workspace.
        root = ctx.fs.write_root
        relative = f".worktrees/{name}"

        rc, out = await _run(
            ctx, ["git", "rev-parse", "--is-inside-work-tree"], cwd=str(root), timeout=self.timeout_seconds
        )
        if rc != 0:
            return ToolResult.error(self.name, f"Not a git repository: {out.strip()}")

        try:
            worktree_path = ctx.fs.resolve(str(root / relative), for_write=True)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))

        rc, out = await _run(
            ctx,
            ["git", "worktree", "add", "-b", branch, relative],
            cwd=str(root),
            timeout=self.timeout_seconds,
        )
        if rc != 0:
            return ToolResult.error(self.name, f"git worktree add failed: {out.strip()}")

        shown = ctx.presentation.to_llm(worktree_path)

        def modifier(c: "ToolUseContext") -> "ToolUseContext":
            c.app_state.native[_WORKTREE_KEY] = {
                "path": str(worktree_path),
                "relative": relative,
                "branch": branch,
                "original_cwd": str(root),
            }
            return c

        return ToolResult(
            tool_name=self.name,
            output=f"Created worktree at {shown} on branch {branch}.",
            context_modifier=modifier,
        )


class ExitWorktreeTool:
    name = EXIT_WORKTREE_TOOL_NAME
    # Homologada contra `ExitWorktreeTool/prompt.ts:2-31` (`getExitWorktreeToolPrompt()`),
    # `GAP-PROMPT-1`.
    # OMITIDO Y DECLARADO: la sesión tmux (`:29`) — B no la tiene. El resto se porta,
    # incluida la sección `## Scope`, que es la que impide que el modelo crea que esta
    # tool borra worktrees creados a mano.
    description = """Exit a worktree session created by EnterWorktree and return the session to \
the original working directory.

## Scope

This tool ONLY operates on worktrees created by EnterWorktree in this session. It will NOT touch:
- Worktrees you created manually with `git worktree add`
- Worktrees from a previous session (even if created by EnterWorktree then)
- The directory you're in if EnterWorktree was never called

If called outside an EnterWorktree session, the tool is a **no-op**: it reports that no worktree \
session is active and takes no action. Filesystem state is unchanged.

## When to Use

- The user explicitly asks to "exit the worktree", "leave the worktree", "go back", or otherwise \
end the worktree session
- Do NOT call this proactively — only when the user asks

## Parameters

- `action` (required): `"keep"` or `"remove"`
  - `"keep"` — leave the worktree directory and branch intact on disk. Use this if the user wants \
to come back to the work later, or if there are changes to preserve.
  - `"remove"` — delete the worktree directory and its branch. Use this for a clean exit when the \
work is done or abandoned.
- `discard_changes` (optional, default false): only meaningful with `action: "remove"`. If the \
worktree has uncommitted files or commits not on the original branch, the tool will REFUSE to \
remove it unless this is set to `true`. If the tool returns an error listing changes, confirm \
with the user before re-invoking with `discard_changes: true`.

## Behavior

- Restores the session's working directory to where it was before EnterWorktree
- Once exited, EnterWorktree can be called again to create a fresh worktree
"""
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["keep", "remove"],
                "description": '"keep" leaves the worktree on disk; "remove" deletes it.',
            },
            "discard_changes": {
                "type": "boolean",
                "description": (
                    "Required true when action is 'remove' and the worktree has "
                    "uncommitted changes. The tool will refuse otherwise."
                ),
            },
        },
        "required": ["action"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = True
    safe_for_background = False
    timeout_seconds = 30.0

    async def execute(self, input: dict[str, Any], ctx: "ToolUseContext") -> ToolResult:
        session = ctx.app_state.native.get(_WORKTREE_KEY)
        if not session:
            return ToolResult.error(self.name, "Not currently in a worktree session.")

        action = input.get("action", "keep")
        discard = input.get("discard_changes", False)
        path = session["path"]
        # `relative`/`original_cwd` pueden faltar en una sesión escrita por la versión
        # anterior de la tool; se degrada al path guardado en vez de reventar.
        relative = session.get("relative") or path
        root = session.get("original_cwd") or str(ctx.fs.write_root)
        branch = session.get("branch", "")

        if action == "remove":
            # Sólo esta rama lanza git: con `action="keep"` la tool no ejecuta nada y no
            # tiene por qué exigir la costura. Exigirla arriba habría convertido un camino
            # legítimo sin comandos en un error.
            try:
                require_exec_env(ctx)
            except ExecEnvironmentUnavailable as exc:
                return ToolResult.error(self.name, str(exc))
            rc, out = await _run(
                ctx, ["git", "status", "--porcelain"], cwd=path, timeout=self.timeout_seconds
            )
            if rc == 0 and out.strip() and not discard:
                return ToolResult.error(
                    self.name,
                    "Worktree has uncommitted changes. Set discard_changes=true to proceed.",
                )
            rc, out = await _run(
                ctx,
                ["git", "worktree", "remove", "--force", relative],
                cwd=root,
                timeout=self.timeout_seconds,
            )
            if rc != 0:
                return ToolResult.error(self.name, f"git worktree remove failed: {out.strip()}")
            if branch:
                await _run(
                    ctx, ["git", "branch", "-D", branch], cwd=root, timeout=self.timeout_seconds
                )

        def modifier(c: "ToolUseContext") -> "ToolUseContext":
            c.app_state.native.pop(_WORKTREE_KEY, None)
            return c

        return ToolResult(
            tool_name=self.name,
            output=f"Exited worktree (action={action}). Path: {ctx.presentation.to_llm(Path(path))}",
            context_modifier=modifier,
        )
