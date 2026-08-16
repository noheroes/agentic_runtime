from __future__ import annotations

import asyncio
import os
import re
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from urllib.parse import urlparse

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext


@runtime_checkable
class GitCredentialProvider(Protocol):
    def token(self, host: str) -> str | None: ...


_OWNER_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _normalize(repository: str) -> tuple[str, str, str]:
    repo = repository.strip()
    if _OWNER_REPO.match(repo):
        host = "github.com"
        path = repo
    else:
        parsed = urlparse(repo)
        if parsed.scheme not in ("https", "http") or not parsed.netloc:
            raise ValueError(f"repositorio no soportado: {repository!r} (usa owner/repo o URL https)")
        host = parsed.netloc
        path = parsed.path.lstrip("/")
    path = path.removesuffix(".git")
    if not path:
        raise ValueError(f"no se pudo derivar el path del repo de {repository!r}")
    name = path.rstrip("/").split("/")[-1]
    return f"https://{host}/{path}.git", host, name


class CloneRepositoryTool:
    name = "clone_repository"
    description = (
        "Clone a git repository into the workspace so it can be inspected with bash/grep/read. "
        "Accepts 'owner/repo' (GitHub) or a full https URL. Private repos are authenticated "
        "automatically; do not put tokens in the URL."
    )
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "repository": {
                "type": "string",
                "description": "'owner/repo' (GitHub) or a full https clone URL.",
            },
            "directory": {
                "type": "string",
                "description": "Destination directory name inside the workspace (default: repo name).",
            },
        },
        "required": ["repository"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = True
    safe_for_background = True
    timeout_seconds = 120.0

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        repository = (input.get("repository") or "").strip()
        if not repository:
            return ToolResult.error(self.name, "repository es obligatorio")

        try:
            url, host, default_name = _normalize(repository)
        except ValueError as exc:
            return ToolResult.error(self.name, str(exc))

        directory = (input.get("directory") or default_name).strip() or default_name
        candidate = directory if os.path.isabs(directory) else str(ctx.fs.write_root / directory)
        try:
            dest = ctx.fs.resolve(candidate, for_write=True, cwd=ctx.cwd)
        except PathOutsideWorkspace as exc:
            return ToolResult.error(self.name, str(exc))
        if dest.exists():
            return ToolResult.error(self.name, f"el destino ya existe: {directory}")

        token = None
        provider = getattr(ctx, "git_credentials", None)
        if provider is not None:
            token = provider.token(host)

        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        args = ["git"]
        if token:
            env["GIT_CLONE_TOKEN"] = token
            helper = '!f() { echo username=x-access-token; echo "password=$GIT_CLONE_TOKEN"; }; f'
            args += ["-c", f"credential.helper={helper}"]
        args += ["clone", url, str(dest)]

        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=self.timeout_seconds)
        except FileNotFoundError:
            return ToolResult.error(self.name, "git no está disponible en el entorno del runtime")
        except TimeoutError:
            return ToolResult.error(self.name, f"git clone excedió {self.timeout_seconds:.0f}s")

        output = stdout.decode(errors="replace").replace(str(dest), ctx.presentation.to_llm(dest))
        if proc.returncode != 0:
            return ToolResult(tool_name=self.name, output=output or "git clone falló", is_error=True)
        return ToolResult(
            tool_name=self.name,
            output=f"Clonado {url} en {directory}\n{output}".strip(),
        )
