"""Native tool: clona un repositorio git dentro del workspace de la sesión.

Cubre el hueco del cliente MCP de GitHub, que expone operaciones de API (crear repo,
fork, buscar, leer archivos) pero NO un `git clone` a un árbol de trabajo local.

Divergencia consciente del canónico (que no tiene tool de clone; clona por Bash con
credenciales ambientales del host y red normal). Aquí no es viable: el `bash` corre en
`BwrapExecEnvironment` con `--unshare-all` (sin red) y el token de GitHub vive en el MCP,
no en el entorno de Bash. Por eso:

- **Red (decisión A):** el `git clone` corre FUERA del sandbox, como subproceso
  privilegiado del runtime con red, escribiendo en el workspace. El árbol clonado queda
  visible en `/workspace/...` para los `bash` sandboxeados posteriores.
- **Credencial (decisión B):** se reutiliza el token del GitHub MCP per-tenant vía el seam
  `ctx.git_credentials` (lo cablea el integrador desde su config MCP). El token se pasa por
  un credential helper efímero: no aparece en `argv` ni queda persistido en el `.git/config`
  del repo clonado, y nunca se expone al modelo.
- **Confinamiento:** el destino se resuelve con `ctx.fs.resolve(..., for_write=True)`,
  reusando el allow-set de workspace (traversal/symlink-escape → `PathOutsideWorkspace`).
"""
from __future__ import annotations

import asyncio
import os
import re
from typing import TYPE_CHECKING, Protocol, runtime_checkable
from urllib.parse import urlparse

from ..fs_env import PathOutsideWorkspace
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext


@runtime_checkable
class GitCredentialProvider(Protocol):
    """Seam de credenciales git. El integrador lo implementa reutilizando el token del
    MCP per-tenant del host correspondiente. Devuelve `None` para clonar sin auth (público)."""

    def token(self, host: str) -> str | None: ...


_OWNER_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _normalize(repository: str) -> tuple[str, str, str]:
    """`repository` → (url_https_sin_token, host, nombre_por_defecto).

    Acepta `owner/repo` (asume github.com) o una URL https completa."""
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
    path = path[:-4] if path.endswith(".git") else path
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
    input_schema = {
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

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        repository = (input.get("repository") or "").strip()
        if not repository:
            return ToolResult.error(self.name, "repository es obligatorio")

        try:
            url, host, default_name = _normalize(repository)
        except ValueError as exc:
            return ToolResult.error(self.name, str(exc))

        directory = (input.get("directory") or default_name).strip() or default_name
        # El destino es un nombre relativo al workspace (no un path del modelo): se ancla
        # al write-root y luego se confina (traversal/symlink-escape → PathOutsideWorkspace).
        candidate = directory if os.path.isabs(directory) else str(ctx.fs.write_root / directory)
        try:
            dest = ctx.fs.resolve(candidate, for_write=True)
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
            # Credential helper efímero: el token viaja por env (no en argv) y NO se
            # persiste en el .git/config del clon (los `-c` de línea no se guardan).
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
        except asyncio.TimeoutError:
            return ToolResult.error(self.name, f"git clone excedió {self.timeout_seconds:.0f}s")

        output = stdout.decode(errors="replace")
        if proc.returncode != 0:
            return ToolResult(tool_name=self.name, output=output or "git clone falló", is_error=True)
        return ToolResult(
            tool_name=self.name,
            output=f"Clonado {url} en {directory}\n{output}".strip(),
        )
