"""
`ToolExecEnvironment` — backend de ejecución de comandos shell, inyectable.

Las tools que corren comandos (hoy `BashTool`) NO asumen el host in-process: despachan
al backend que el consumidor inyecta vía ``ctx.exec_env``. Backends:

- `LocalExecEnvironment` (default): subproceso en el host, comportamiento canónico CLI/IDE.
- `BwrapExecEnvironment`: aísla en bubblewrap montando el workspace del host en `/workspace`.
  El fake path ES real dentro del sandbox → sin reescritura de comandos (Regla 1).
- remoto: el consumidor implementa el Protocol y lo inyecta (D5c).
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass
class ShellResult:
    """Salida de un comando shell: stdout+stderr combinados y código de retorno."""

    output: str
    returncode: int


@runtime_checkable
class ToolExecEnvironment(Protocol):
    """Ejecuta un comando shell en algún entorno (host / sandbox / remoto)."""

    async def run_shell(self, command: str, *, timeout: float) -> ShellResult: ...


class LocalExecEnvironment:
    """Default: corre el comando como subproceso del host, in-process."""

    async def run_shell(self, command: str, *, timeout: float) -> ShellResult:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return ShellResult(
            output=stdout.decode(errors="replace"),
            returncode=proc.returncode if proc.returncode is not None else -1,
        )


class BwrapExecEnvironment:
    """
    Corre el comando aislado con bubblewrap.

    Monta `workspace_root` del host en `/workspace` y fija el cwd ahí: el path que ve
    el LLM (`/workspace/...`) es real dentro del sandbox, sin reescribir el comando.
    Los binds de sistema son de solo lectura. El comando se pasa verbatim a `sh -c`.
    """

    # Directorios de sistema montados ro por default; ajustables por el consumidor.
    _DEFAULT_RO_BINDS = ("/usr", "/bin", "/lib", "/lib64", "/etc")

    def __init__(
        self,
        *,
        workspace_root: Path,
        bwrap_bin: str = "bwrap",
        ro_binds: tuple[str, ...] | None = None,
    ) -> None:
        self._workspace_root = Path(workspace_root)
        self._bwrap_bin = bwrap_bin
        self._ro_binds = ro_binds if ro_binds is not None else self._DEFAULT_RO_BINDS

    def _build_argv(self, command: str) -> list[str]:
        argv = [self._bwrap_bin, "--unshare-all", "--die-with-parent", "--proc", "/proc", "--dev", "/dev"]
        for d in self._ro_binds:
            if Path(d).exists():
                argv += ["--ro-bind", d, d]
        argv += [
            "--bind", str(self._workspace_root), "/workspace",
            "--chdir", "/workspace",
            "/bin/sh", "-c", command,
        ]
        return argv

    async def run_shell(self, command: str, *, timeout: float) -> ShellResult:
        argv = self._build_argv(command)
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return ShellResult(
            output=stdout.decode(errors="replace"),
            returncode=proc.returncode if proc.returncode is not None else -1,
        )


__all__ = [
    "BwrapExecEnvironment",
    "LocalExecEnvironment",
    "ShellResult",
    "ToolExecEnvironment",
]
