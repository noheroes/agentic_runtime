"""Tool de ejecución de comandos de shell."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from ..exec_env import ExecEnvironmentUnavailable, require_exec_env
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext


class BashTool:
    name = "bash"
    search_hint = "execute shell commands"
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

Do NOT use this tool for file work by way of an interpreter. A `python`, `python3`, `node`,
`perl` or `ruby` invocation — with `-c`, with a heredoc, or with a script file — that reads,
rewrites, renames or deletes files is the same prohibited shortcut as `sed`, and it is worse:
it silently changes line endings, encoding and permissions that the dedicated tools preserve.
This holds however many files are involved: to change N files, call the dedicated tool N
times. Reach for an interpreter only when the task is computation with no file work, or when
a dedicated tool has already failed at it.

While this tool can do similar things, the dedicated tools are better: they are confined to
the workspace, return structured results, and are easier to review.

# Instructions
- If your command will create new directories or files, first use this tool to run `ls` to
  verify the parent directory exists and is the correct location.
- Always quote file paths that contain spaces with double quotes.
- Try to maintain your current working directory throughout the session by using absolute
  paths and avoiding usage of `cd`. You may use `cd` if the user explicitly requests it.
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
- Avoid unnecessary `sleep` commands:
  - Do not sleep between commands that can run immediately — just run them.
  - Do not retry failing commands in a sleep loop — diagnose the root cause.
  - If you must poll an external process, use a check command (e.g. `gh run view`) rather
    than sleeping first.
  - If you must sleep, keep the duration short (1-5 seconds) to avoid blocking the user.

# Committing changes with git

Only create commits when requested by the user. If unclear, ask first. When the user asks you
to create a new git commit, follow these steps carefully:

You can call multiple tools in a single response. When multiple independent pieces of
information are requested and all commands are likely to succeed, run multiple tool calls in
parallel for optimal performance. The numbered steps below indicate which commands should be
batched in parallel.

Git Safety Protocol:
- NEVER update the git config
- NEVER run destructive git commands (push --force, reset --hard, checkout ., restore .,
  clean -f, branch -D) unless the user explicitly requests these actions. Taking unauthorized
  destructive actions is unhelpful and can result in lost work, so it's best to ONLY run these
  commands when given direct instructions
- NEVER skip hooks (--no-verify, --no-gpg-sign, etc) unless the user explicitly requests it
- NEVER run force push to main/master, warn the user if they request it
- CRITICAL: Always create NEW commits rather than amending, unless the user explicitly requests
  a git amend. When a pre-commit hook fails, the commit did NOT happen — so --amend would
  modify the PREVIOUS commit, which may result in destroying work or losing previous changes.
  Instead, after hook failure, fix the issue, re-stage, and create a NEW commit
- When staging files, prefer adding specific files by name rather than using "git add -A" or
  "git add .", which can accidentally include sensitive files (.env, credentials) or large
  binaries
- NEVER commit changes unless the user explicitly asks you to. It is VERY IMPORTANT to only
  commit when explicitly asked, otherwise the user will feel that you are being too proactive

1. Run the following bash commands in parallel, each using this tool:
  - Run a git status command to see all untracked files. IMPORTANT: Never use the -uall flag as
    it can cause memory issues on large repos.
  - Run a git diff command to see both staged and unstaged changes that will be committed.
  - Run a git log command to see recent commit messages, so that you can follow this
    repository's commit message style.
2. Analyze all staged changes (both previously staged and newly added) and draft a commit
   message:
  - Summarize the nature of the changes (eg. new feature, enhancement to an existing feature,
    bug fix, refactoring, test, docs, etc.). Ensure the message accurately reflects the changes
    and their purpose (i.e. "add" means a wholly new feature, "update" means an enhancement to
    an existing feature, "fix" means a bug fix, etc.).
  - Do not commit files that likely contain secrets (.env, credentials.json, etc). Warn the
    user if they specifically request to commit those files
  - Draft a concise (1-2 sentences) commit message that focuses on the "why" rather than the
    "what"
3. Run the following commands in parallel:
   - Add relevant untracked files to the staging area.
   - Create the commit with a message.
   - Run git status after the commit completes to verify success.
   Note: git status depends on the commit completing, so run it sequentially after the commit.
4. If the commit fails due to pre-commit hook: fix the issue and create a NEW commit

Important notes:
- NEVER run additional commands to read or explore code, besides git bash commands
- NEVER use the TodoWrite or Agent tools
- DO NOT push to the remote repository unless the user explicitly asks you to do so
- IMPORTANT: Never use git commands with the -i flag (like git rebase -i or git add -i) since
  they require interactive input which is not supported.
- IMPORTANT: Do not use --no-edit with git rebase commands, as the --no-edit flag is not a
  valid option for git rebase.
- If there are no changes to commit (i.e., no untracked files and no modifications), do not
  create an empty commit
- In order to ensure good formatting, ALWAYS pass the commit message via a HEREDOC, a la this
  example:
<example>
git commit -m "$(cat <<'EOF'
   Commit message here.
   EOF
   )"
</example>

# Creating pull requests
Use the gh command via this tool for ALL GitHub-related tasks including working with issues,
pull requests, checks, and releases. If given a Github URL use the gh command to get the
information needed.

IMPORTANT: When the user asks you to create a pull request, follow these steps carefully:

1. Run the following bash commands in parallel using this tool, in order to understand the
   current state of the branch since it diverged from the main branch:
   - Run a git status command to see all untracked files (never use -uall flag)
   - Run a git diff command to see both staged and unstaged changes that will be committed
   - Check if the current branch tracks a remote branch and is up to date with the remote, so
     you know if you need to push to the remote
   - Run a git log command and `git diff [base-branch]...HEAD` to understand the full commit
     history for the current branch (from the time it diverged from the base branch)
2. Analyze all changes that will be included in the pull request, making sure to look at all
   relevant commits (NOT just the latest commit, but ALL commits that will be included in the
   pull request!!!), and draft a pull request title and summary:
   - Keep the PR title short (under 70 characters)
   - Use the description/body for details, not the title
3. Run the following commands in parallel:
   - Create new branch if needed
   - Push to remote with -u flag if needed
   - Create PR using gh pr create with the format below. Use a HEREDOC to pass the body to
     ensure correct formatting.
<example>
gh pr create --title "the pr title" --body "$(cat <<'EOF'
## Summary
<1-3 bullet points>

## Test plan
[Bulleted markdown checklist of TODOs for testing the pull request...]
EOF
)"
</example>

Important:
- DO NOT use the TodoWrite or Agent tools
- Return the PR URL when you're done, so the user can see it

# Other common operations
- View comments on a Github PR: gh api repos/foo/bar/pulls/123/comments"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
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
        root = getattr(getattr(ctx, "fs", None), "write_root", None)
        return str(root) if root is not None else None

    def _resolve_cwd(self, ctx: ToolUseContext) -> tuple[str | None, str | None]:
        fallback = self._workspace_root(ctx)
        cwd = getattr(ctx, "cwd", None) or fallback
        if cwd is None:
            return None, None
        if os.path.isdir(cwd):
            return cwd, None
        if fallback is not None and fallback != cwd and os.path.isdir(fallback):
            return fallback, None
        return None, (
            f'Working directory "{cwd}" no longer exists. '
            "Please restart from an existing directory."
        )

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        command = input.get("command", "")
        try:
            exec_env = require_exec_env(ctx)
        except ExecEnvironmentUnavailable as exc:
            return ToolResult.error(self.name, str(exc))
        cwd, cwd_error = self._resolve_cwd(ctx)
        if cwd_error is not None:
            return ToolResult.error(self.name, cwd_error)
        try:
            result = await exec_env.run_shell(command, cwd=cwd, timeout=self.timeout_seconds)
            tracked = getattr(result, "cwd", None)
            if getattr(ctx, "is_subagent", False):
                tracked = None
            if tracked:
                try:
                    ctx.cwd = tracked
                except (AttributeError, ValueError):
                    pass
            return ToolResult(
                tool_name=self.name,
                output=result.output,
                is_error=result.returncode != 0,
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult.error(self.name, str(exc))
