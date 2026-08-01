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
import os
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

    async def run_argv(
        self, argv: list[str], *, cwd: str | None = None, timeout: float
    ) -> ShellResult:
        """Ejecuta un **argv** (sin shell) en el mismo entorno que `run_shell`.

        **Enriquecimiento declarado de `S15`** (mismo patrón con que `S4` ganó
        `join(task_id)` y `S18` pasó a `SubagentSpec`), añadido para cerrar el bypass
        de `worktree.py`: esa tool lanzaba `asyncio.create_subprocess_exec` **directo**,
        así que con un `BwrapExecEnvironment` inyectado `bash` quedaba aislado pero
        `EnterWorktree` corría git **en el host**. `E7b` sólo acreditaba `bash`.

        Es `run_argv` y no `run_shell` **a propósito**: el argv lleva un nombre de rama
        que viene del MODELO. Serializarlo a un string de shell cambiaría una fuga de
        ruta por una **inyección de comandos**; la lista no se interpreta.
        """
        ...


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

    async def run_argv(
        self, argv: list[str], *, cwd: str | None = None, timeout: float
    ) -> ShellResult:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=cwd,
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

    def _sandbox_prefix(self, inner_cwd: str) -> list[str]:
        """Opciones de bwrap hasta (sin incluir) el programa a ejecutar."""
        argv = [self._bwrap_bin, "--unshare-all", "--die-with-parent", "--proc", "/proc", "--dev", "/dev"]
        for d in self._ro_binds:
            if Path(d).exists():
                argv += ["--ro-bind", d, d]
        argv += [
            "--bind", str(self._workspace_root), "/workspace",
            "--chdir", inner_cwd,
        ]
        return argv

    def _build_argv(self, command: str) -> list[str]:
        return self._sandbox_prefix("/workspace") + ["/bin/sh", "-c", command]

    def _inner_cwd(self, cwd: str | None) -> str:
        """Traduce un `cwd` del HOST al path que ese directorio tiene DENTRO del sandbox.

        Lo único montado es `workspace_root` en `/workspace`, así que un `cwd` fuera de él
        se **rechaza** en vez de ignorarse: ignorarlo dejaría el comando corriendo en
        `/workspace` como si nada, que es justo el modo de fallo (autorizar una cosa y
        ejecutar otra) que costó encontrar `FIND-C6-1`.
        """
        if cwd is None:
            return "/workspace"
        root = str(self._workspace_root)
        if cwd == root:
            return "/workspace"
        if cwd.startswith(root + os.sep):
            return "/workspace/" + cwd[len(root) + 1 :]
        raise ValueError(
            f"cwd {cwd!r} cae fuera del workspace montado ({root!r}): "
            "no hay forma de honrarlo dentro del sandbox"
        )

    async def run_shell(self, command: str, *, timeout: float) -> ShellResult:
        return await self._spawn(self._build_argv(command), timeout)

    async def run_argv(
        self, argv: list[str], *, cwd: str | None = None, timeout: float
    ) -> ShellResult:
        """Igual que `run_shell` pero sin `sh -c`: el argv entra **verbatim** al sandbox."""
        return await self._spawn(self._sandbox_prefix(self._inner_cwd(cwd)) + argv, timeout)

    async def _spawn(self, argv: list[str], timeout: float) -> ShellResult:
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
