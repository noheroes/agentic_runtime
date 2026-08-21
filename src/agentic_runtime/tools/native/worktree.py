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
    if "/" in name:
        parts = name.split("/")
        if any(not _SLUG_RE.match(p) for p in parts if p):
            return "Each segment must contain only letters, digits, dots, underscores, dashes."
    elif not _SLUG_RE.match(name):
        return "Name must contain only letters, digits, dots, underscores, dashes (max 64 chars)."
    return None


async def _run(
    ctx: ToolUseContext, argv: list[str], *, cwd: str, timeout: float
) -> tuple[int, str]:
    exec_env = require_exec_env(ctx)
    result = await exec_env.run_argv(argv, cwd=cwd, timeout=timeout)
    return result.returncode, result.output


async def _run_no_throw(
    ctx: ToolUseContext, argv: list[str], *, cwd: str, timeout: float
) -> tuple[int, str]:
    try:
        return await _run(ctx, argv, cwd=cwd, timeout=timeout)
    except (OSError, TimeoutError) as exc:
        return -1, str(exc)


async def _count_worktree_changes(
    ctx: ToolUseContext, path: str, original_head: str, *, timeout: float
) -> tuple[int, int] | None:
    rc, out = await _run_no_throw(
        ctx, ["git", "status", "--porcelain"], cwd=path, timeout=timeout
    )
    if rc != 0:
        return None
    changed_files = sum(1 for line in out.split("\n") if line.strip())

    if not original_head:
        return None

    rc, out = await _run_no_throw(
        ctx,
        ["git", "rev-list", "--count", f"{original_head}..HEAD"],
        cwd=path,
        timeout=timeout,
    )
    if rc != 0:
        return None
    try:
        commits = int(out.strip())
    except ValueError:
        commits = 0

    return changed_files, commits


def _plural(n: int, singular: str, plural: str) -> str:
    return singular if n == 1 else plural


class EnterWorktreeTool:
    name = ENTER_WORKTREE_TOOL_NAME
    search_hint = "create an isolated git worktree and switch into it"
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

## Ownership

The worktree this tool creates belongs to the session, not just to the filesystem. \
ExitWorktree is the only supported way to end it — including when the user asks for it to be \
deleted. Removing it through the shell (`git worktree remove`, `git branch -D`, `rm -rf`) \
deletes the directory but leaves the session still believing it is inside a worktree: the next \
EnterWorktree will refuse, and ExitWorktree will operate on a path that no longer exists. A \
user asking to "exit and delete the worktree" is asking for ExitWorktree with \
`action: "remove"` — one call, not a shell command.

## Parameters

- `name` (optional): A name for the worktree. If not provided, a random name is generated.
"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
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

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
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
        root = ctx.fs.write_root
        relative = f".worktrees/{name}"

        rc, out = await _run(
            ctx, ["git", "rev-parse", "--is-inside-work-tree"], cwd=str(root), timeout=self.timeout_seconds
        )
        if rc != 0:
            return ToolResult.error(self.name, f"Not a git repository: {out.strip()}")

        rc, out = await _run(
            ctx, ["git", "rev-parse", "HEAD"], cwd=str(root), timeout=self.timeout_seconds
        )
        original_head = out.strip() if rc == 0 else ""

        try:
            worktree_path = ctx.fs.resolve(str(root / relative), for_write=True, cwd=ctx.cwd)
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

        def modifier(c: ToolUseContext) -> ToolUseContext:
            c.app_state.native[_WORKTREE_KEY] = {
                "path": str(worktree_path),
                "relative": relative,
                "branch": branch,
                "original_cwd": str(root),
                "original_head": original_head,
            }
            c.cwd = str(worktree_path)
            return c

        return ToolResult(
            tool_name=self.name,
            output=(
                f"Created worktree at {shown} on branch {branch}. The session is now working "
                f"inside it. When the work is done, end this session with ExitWorktree "
                f'(action "keep" or "remove"); do not delete the worktree from the shell — '
                f"that leaves the session pointing at a directory that no longer exists."
            ),
            context_modifier=modifier,
        )


class ExitWorktreeTool:
    name = EXIT_WORKTREE_TOOL_NAME
    search_hint = "exit a worktree session and return to the original directory"
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
remove it and list them. It also refuses when it cannot verify the worktree state at all. If the \
tool returns such an error, confirm with the user before re-invoking with `discard_changes: true`.

## Behavior

- Restores the session's working directory to where it was before EnterWorktree
- Once exited, EnterWorktree can be called again to create a fresh worktree
"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["keep", "remove"],
                "description": (
                    '"keep" leaves the worktree and branch on disk; "remove" deletes both.'
                ),
            },
            "discard_changes": {
                "type": "boolean",
                "description": (
                    'Required true when action is "remove" and the worktree has uncommitted '
                    "files or unmerged commits. The tool will refuse and list them otherwise."
                ),
            },
        },
        "required": ["action"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = True
    safe_for_background = False
    timeout_seconds = 30.0

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        session = ctx.app_state.native.get(_WORKTREE_KEY)
        if not session:
            return ToolResult.error(
                self.name,
                "No-op: there is no active EnterWorktree session to exit. This tool only "
                "operates on worktrees created by EnterWorktree in the current session — it "
                "will not touch worktrees created manually or in a previous session. No "
                "filesystem changes were made.",
            )

        action = input.get("action", "keep")
        discard = input.get("discard_changes", False)
        path = session["path"]
        relative = session.get("relative") or path
        root = session.get("original_cwd") or str(ctx.fs.write_root)
        branch = session.get("branch", "")
        original_head = session.get("original_head") or ""

        shown_path = ctx.presentation.to_llm(Path(path))
        shown_root = ctx.presentation.to_llm(Path(root))

        if action == "keep":

            def keep_modifier(c: ToolUseContext) -> ToolUseContext:
                c.app_state.native.pop(_WORKTREE_KEY, None)
                c.cwd = root
                return c

            on_branch = f" on branch {branch}" if branch else ""
            return ToolResult(
                tool_name=self.name,
                output=(
                    f"Exited worktree. Your work is preserved at {shown_path}{on_branch}. "
                    f"Session is now back in {shown_root}."
                ),
                context_modifier=keep_modifier,
            )

        try:
            require_exec_env(ctx)
        except ExecEnvironmentUnavailable as exc:
            return ToolResult.error(self.name, str(exc))

        if not discard:
            summary = await _count_worktree_changes(
                ctx, path, original_head, timeout=self.timeout_seconds
            )
            if summary is None:
                return ToolResult.error(
                    self.name,
                    f"Could not verify worktree state at {shown_path}. Refusing to remove "
                    "without explicit confirmation. Re-invoke with discard_changes: true to "
                    'proceed — or use action: "keep" to preserve the worktree.',
                )
            changed_files, commits = summary
            if changed_files > 0 or commits > 0:
                parts: list[str] = []
                if changed_files > 0:
                    parts.append(
                        f"{changed_files} uncommitted {_plural(changed_files, 'file', 'files')}"
                    )
                if commits > 0:
                    parts.append(
                        f"{commits} {_plural(commits, 'commit', 'commits')} on "
                        f"{branch or 'the worktree branch'}"
                    )
                return ToolResult.error(
                    self.name,
                    f"Worktree has {' and '.join(parts)}. Removing will discard this work "
                    "permanently. Confirm with the user, then re-invoke with "
                    'discard_changes: true — or use action: "keep" to preserve the worktree.',
                )

        recount = await _count_worktree_changes(
            ctx, path, original_head, timeout=self.timeout_seconds
        )
        changed_files, commits = recount if recount is not None else (0, 0)

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

        discard_parts: list[str] = []
        if commits > 0:
            discard_parts.append(f"{commits} {_plural(commits, 'commit', 'commits')}")
        if changed_files > 0:
            discard_parts.append(
                f"{changed_files} uncommitted {_plural(changed_files, 'file', 'files')}"
            )
        discard_note = f" Discarded {' and '.join(discard_parts)}." if discard_parts else ""

        def modifier(c: ToolUseContext) -> ToolUseContext:
            c.app_state.native.pop(_WORKTREE_KEY, None)
            c.cwd = root
            return c

        return ToolResult(
            tool_name=self.name,
            output=(
                f"Exited and removed worktree at {shown_path}.{discard_note} "
                f"Session is now back in {shown_root}."
            ),
            context_modifier=modifier,
        )
