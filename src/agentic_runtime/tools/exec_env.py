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
import shlex
import tempfile
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


class ExecEnvironmentUnavailable(RuntimeError):
    """La costura de ejecución no está poblada y por tanto NO se ejecuta nada.

    Es el problema **#2** del listado de `VALIDACION-AGENTIC-CODE.md`. Antes, cada tool
    que corría comandos hacía ``getattr(ctx, "exec_env", None) or LocalExecEnvironment()``:
    un default **silencioso y sin confinar**, en el punto equivocado. En producción el
    cable va siempre poblado (`runtime.py:415`, sin condición), así que ese fallback
    estaba muerto — pero es exactamente la forma que enmascaraba `FIND-EXEC1`: si el
    cable se rompiera, `bash` seguiría corriendo **en el host** con un
    `BwrapExecEnvironment` inyectado y nadie lo notaría.

    Lo DICTA el canónico (`D-08`), que trata esa degradación como fallo, no como default:

    - `sandbox-adapter.ts:704-717` — `wrapWithSandbox` **lanza** (`'Sandbox failed to
      initialize.'`) si el sandbox está habilitado y no hay inicialización. No cae a
      ejecutar sin sandbox.
    - `sandbox-adapter.ts:549-560` — el fix de #34044, con su razón escrita: antes
      `isSandboxingEnabled()` devolvía `false` en silencio al faltar dependencias, «giving
      users zero feedback that their explicit security setting was being ignored. **This is
      a security footgun**». La corrección fue hacerlo VISIBLE.
    - `sandbox-adapter.ts:479-485` — `failIfUnavailable` es una política explícita de
      «si no puedo confinar, no ejecuto».

    Y lo dicta también la propia costura de B, que ya resuelve así sus seams sin poblar:
    `runner=None` ⇒ la tool `Agent` devuelve `is_error` limpio (`tool_use.py:104-108`);
    `scope=None` ⇒ los repos que necesiten clave **fallan**, no inventan una (`:69`);
    `BwrapExecEnvironment._inner_cwd` **rechaza** un cwd que no puede honrar en vez de
    ignorarlo (`:197`). El default sigue existiendo y sigue siendo `LocalExecEnvironment`,
    pero en **un solo sitio**: el ensamblador (`factory.py:256`), que es donde `C10` dice
    que viven las decisiones de composición.

    Por qué `exec_env` NO recibe un `default_factory` como `fs` y `presentation`: aquellos
    dos tienen un default **seguro** (confinado a cwd / identidad). Un `LocalExecEnvironment`
    por defecto es lo contrario — ejecución sin confinar—, así que el default seguro aquí
    es no ejecutar.
    """


def require_exec_env(ctx: object) -> ToolExecEnvironment:
    """Devuelve el backend inyectado, o **lanza**. Nunca sustituye por uno propio.

    Punto único: una tool nueva que corra comandos pasa por aquí, y si alguien añade un
    camino que se lo salta, revienta (el dispatcher lo convierte en `ToolResult.error`,
    `dispatcher.py:85-86`) en vez de correr en el host en silencio.
    """
    env: ToolExecEnvironment | None = getattr(ctx, "exec_env", None)
    if env is None:
        raise ExecEnvironmentUnavailable(
            "no execution environment is wired for this session "
            "(ctx.exec_env is None): refusing to run the command on the host. "
            "Inject a ToolExecEnvironment — create_runtime() does it by default."
        )
    return env


def _read_tracked_cwd(path: str | None) -> str | None:
    """Relee el cwd que el propio shell escribió; `None` si no lo escribió."""
    if path is None:
        return None
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            tracked = handle.read().strip()
    except OSError:
        return None
    return tracked or None


@dataclass
class ShellResult:
    """Salida de un comando shell: stdout+stderr combinados y código de retorno.

    `cwd` es el directorio de trabajo **con el que terminó** el comando, releído del
    propio shell (A: `pwd -P >| <tmp>`, `bashProvider.ts:186`), no supuesto. `None` =
    el backend no lo rastrea, y entonces el llamante NO debe actualizar su estado.
    """

    output: str
    returncode: int
    cwd: str | None = None


@runtime_checkable
class ToolExecEnvironment(Protocol):
    """Ejecuta un comando shell en algún entorno (host / sandbox / remoto)."""

    async def run_shell(
        self, command: str, *, cwd: str | None = None, timeout: float
    ) -> ShellResult:
        """Ejecuta un comando de shell, opcionalmente en `cwd`.

        **`cwd` es defecto de CONTRATO saldado** (problema #1 del listado de
        `VALIDACION-AGENTIC-CODE.md`): sin él, el comando heredaba el cwd del PROCESO
        host mientras el integrador confinaba `read_file`/`write_file` a un workspace
        distinto y se lo declaraba al modelo como autoritativo. Autorizar una cosa y
        ejecutar otra es exactamente el modo de fallo de `FIND-C6-1`.

        `None` = «no lo fijes», que preserva el comportamiento previo para todo llamante
        que aún no lo pase; el cwd efectivo lo decide `BashTool`, no este backend.
        """
        ...

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

    async def run_shell(
        self, command: str, *, cwd: str | None = None, timeout: float
    ) -> ShellResult:
        # Rastreo del cwd calcado de A (`bashProvider.ts:180-186`): `eval <comando> &&
        # pwd -P >| <tmp>`. Los dos detalles son portantes:
        #   · `eval` con el comando ENTERO citado — sin él, `&& pwd` se ata sólo al
        #     último tramo de un `a; b` o `a || b` y el rastreo mentiría.
        #   · `&&` — si el comando falla NO se escribe nada, así que el llamante
        #     conserva el cwd anterior en vez de adoptar uno a medias. El código de
        #     salida sigue siendo el del comando, porque `&&` cortocircuita.
        # `pwd -P` (físico) por consistencia con lo que ve el proceso, igual que A.
        track_path: str | None = None
        command_string = command
        if cwd is not None:
            fd, track_path = tempfile.mkstemp(prefix="agentic-cwd-")
            os.close(fd)
            command_string = (
                f"eval {shlex.quote(command)} && pwd -P >| {shlex.quote(track_path)}"
            )
        try:
            proc = await asyncio.create_subprocess_shell(
                command_string,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return ShellResult(
                output=stdout.decode(errors="replace"),
                returncode=proc.returncode if proc.returncode is not None else -1,
                cwd=_read_tracked_cwd(track_path),
            )
        finally:
            if track_path is not None:
                with suppress(OSError):
                    os.unlink(track_path)

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

    def _build_argv(self, command: str, cwd: str | None = None) -> list[str]:
        return self._sandbox_prefix(self._inner_cwd(cwd)) + ["/bin/sh", "-c", command]

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

    async def run_shell(
        self, command: str, *, cwd: str | None = None, timeout: float
    ) -> ShellResult:
        """Honra `cwd` traduciéndolo al path de DENTRO del sandbox (`_inner_cwd`).

        **Carencia declarada:** no rastrea el cwd de salida (`ShellResult.cwd` = `None`),
        así que bajo bwrap un `cd` no persiste entre comandos. Dos razones materiales, no
        pereza: el fichero temporal del host no existe dentro del sandbox, y el `pwd` de
        dentro es un path INTERNO (`/workspace/…`) que no es asignable a un `ctx.cwd` del
        host sin traducción inversa. Declararlo es preferible a devolver un path que el
        llamante adoptaría como si fuera del host.
        """
        return await self._spawn(self._build_argv(command, cwd), timeout)

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
    "ExecEnvironmentUnavailable",
    "LocalExecEnvironment",
    "ShellResult",
    "ToolExecEnvironment",
    "require_exec_env",
]
