from __future__ import annotations

import asyncio
import re
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

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


async def _run(cmd: list[str], cwd: str | None = None) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode or 0, stdout.decode(), stderr.decode()


class EnterWorktreeTool:
    name = ENTER_WORKTREE_TOOL_NAME
    description = "Create an isolated git worktree and switch the session into it."
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

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        if ctx.app_state.native.get(_WORKTREE_KEY):
            return ToolResult.error(self.name, "Already in a worktree session.")

        name = input.get("name") or f"agent-{uuid.uuid4().hex[:8]}"
        err = _validate_slug(name)
        if err:
            return ToolResult.error(self.name, err)

        branch = f"worktree/{name}"

        # Find git root
        rc, stdout, stderr = await _run(["git", "rev-parse", "--show-toplevel"])
        if rc != 0:
            return ToolResult.error(self.name, f"Not a git repository: {stderr.strip()}")
        git_root = stdout.strip()

        worktree_path = str(Path(git_root).parent / f".worktrees/{name}")

        rc, _, stderr = await _run(
            ["git", "worktree", "add", "-b", branch, worktree_path],
            cwd=git_root,
        )
        if rc != 0:
            return ToolResult.error(self.name, f"git worktree add failed: {stderr.strip()}")

        def modifier(c: "ToolUseContext") -> "ToolUseContext":
            c.app_state.native[_WORKTREE_KEY] = {
                "path": worktree_path,
                "branch": branch,
                "original_cwd": git_root,
            }
            return c

        result = ToolResult(
            tool_name=self.name,
            output=f"Created worktree at {worktree_path} on branch {branch}.",
        )
        result.context_modifier = modifier  # type: ignore[attr-defined]
        return result


class ExitWorktreeTool:
    name = EXIT_WORKTREE_TOOL_NAME
    description = "Exit the current git worktree session, keeping or removing it."
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

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        session = ctx.app_state.native.get(_WORKTREE_KEY)
        if not session:
            return ToolResult.error(self.name, "Not currently in a worktree session.")

        action = input.get("action", "keep")
        discard = input.get("discard_changes", False)
        path = session["path"]
        branch = session.get("branch", "")

        if action == "remove":
            # Check for uncommitted changes
            rc, stdout, _ = await _run(["git", "status", "--porcelain"], cwd=path)
            if rc == 0 and stdout.strip() and not discard:
                return ToolResult.error(
                    self.name,
                    "Worktree has uncommitted changes. Set discard_changes=true to proceed.",
                )
            rc, _, stderr = await _run(
                ["git", "worktree", "remove", "--force", path]
            )
            if rc != 0:
                return ToolResult.error(self.name, f"git worktree remove failed: {stderr.strip()}")
            if branch:
                await _run(["git", "branch", "-D", branch])

        def modifier(c: "ToolUseContext") -> "ToolUseContext":
            c.app_state.native.pop(_WORKTREE_KEY, None)
            return c

        result = ToolResult(
            tool_name=self.name,
            output=f"Exited worktree (action={action}). Path: {path}",
        )
        result.context_modifier = modifier  # type: ignore[attr-defined]
        return result
