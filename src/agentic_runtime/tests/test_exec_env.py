"""B2 — ToolExecEnvironment inyectable: BashTool despacha al backend, no al host.

- default in-process (`LocalExecEnvironment`) sin cambio de comportamiento;
- BashTool usa `ctx.exec_env` cuando se inyecta (D5c) y **rehúsa ejecutar** cuando es
  None (problema `#2`): el default vive en el ensamblador, no en la tool;
- `BwrapExecEnvironment` monta workspace→/workspace y pasa el comando verbatim
  (build-side; bwrap no instalado en CI → el run real se skipea, no se finge — Regla 3).
"""
import asyncio
import shutil
from pathlib import Path

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools.exec_env import (
    BwrapExecEnvironment,
    LocalExecEnvironment,
    ShellResult,
    ToolExecEnvironment,
)
from agentic_runtime.tools.native.bash import BashTool


def test_local_runs_command_ok():
    res = asyncio.run(LocalExecEnvironment().run_shell("echo hola", timeout=5.0))
    assert res.returncode == 0
    assert "hola" in res.output


def test_local_reports_nonzero_returncode():
    res = asyncio.run(LocalExecEnvironment().run_shell("exit 3", timeout=5.0))
    assert res.returncode == 3


def test_protocol_isinstance():
    assert isinstance(LocalExecEnvironment(), ToolExecEnvironment)
    assert isinstance(BwrapExecEnvironment(workspace_root=Path("/tmp")), ToolExecEnvironment)


class _RecordingEnv:
    """Backend inyectado que registra la llamada en vez de tocar el host.

    La firma sigue al Protocol **incluido `cwd`**: un fake que se quede corto convierte
    el olvido de un parámetro del contrato en una excepción tragada por el `except` de
    la tool, y el test acreditaría en falso (`H-L4`).
    """

    def __init__(self, *, tracked_cwd: str | None = None) -> None:
        self.calls: list[tuple[str, str | None, float]] = []
        self._tracked_cwd = tracked_cwd

    async def run_shell(
        self, command: str, *, cwd: str | None = None, timeout: float
    ) -> ShellResult:
        self.calls.append((command, cwd, timeout))
        return ShellResult(output="from-injected-env", returncode=0, cwd=self._tracked_cwd)


def test_bash_dispatches_to_injected_env(tmp_path):
    env = _RecordingEnv()
    ctx = ToolUseContext(session_id="s1", exec_env=env, cwd=str(tmp_path))
    result = asyncio.run(BashTool().execute({"command": "rm -rf /"}, ctx))
    # no tocó el host, y el cwd declarado viajó hasta el backend
    assert env.calls == [("rm -rf /", str(tmp_path), BashTool.timeout_seconds)]
    assert result.output == "from-injected-env"
    assert result.is_error is False


def test_bash_adopts_the_cwd_that_the_backend_read_back(tmp_path):
    """`Shell.ts:385-421`: el cwd nuevo sale de releer el shell, no de suponerlo."""
    destino = tmp_path / "sub"
    destino.mkdir()
    env = _RecordingEnv(tracked_cwd=str(destino))
    ctx = ToolUseContext(session_id="s1", exec_env=env, cwd=str(tmp_path))
    asyncio.run(BashTool().execute({"command": "cd sub"}, ctx))
    assert ctx.cwd == str(destino)


def test_bash_keeps_its_cwd_when_the_backend_does_not_track_it(tmp_path):
    """`cwd=None` = el backend no rastrea (bwrap): no se adopta nada inventado."""
    env = _RecordingEnv(tracked_cwd=None)
    ctx = ToolUseContext(session_id="s1", exec_env=env, cwd=str(tmp_path))
    asyncio.run(BashTool().execute({"command": "cd sub"}, ctx))
    assert ctx.cwd == str(tmp_path)


def test_bash_falls_back_to_the_confinement_root_when_no_cwd_was_declared(tmp_path):
    """Sin cable, el cwd NO es el del proceso host: es la raíz ya confinada (`#1`)."""
    from agentic_runtime.tools.fs_env import ConfinedFilesystem

    env = _RecordingEnv()
    ctx = ToolUseContext(
        session_id="s1",
        exec_env=env,
        fs=ConfinedFilesystem(roots=[tmp_path], write_roots=[tmp_path]),
    )
    asyncio.run(BashTool().execute({"command": "pwd"}, ctx))
    assert env.calls[0][1] == str(tmp_path)


def test_bash_recovers_when_the_cwd_vanished_from_disk(tmp_path):
    """`Shell.ts:220-238`: un comando puede borrar su propio cwd; A cae al original."""
    from agentic_runtime.tools.fs_env import ConfinedFilesystem

    desaparecido = tmp_path / "se-borro"
    env = _RecordingEnv()
    ctx = ToolUseContext(
        session_id="s1",
        exec_env=env,
        cwd=str(desaparecido),
        fs=ConfinedFilesystem(roots=[tmp_path], write_roots=[tmp_path]),
    )
    asyncio.run(BashTool().execute({"command": "pwd"}, ctx))
    assert env.calls[0][1] == str(tmp_path)


def test_bash_fails_readably_when_neither_cwd_nor_fallback_exist(tmp_path):
    from agentic_runtime.tools.fs_env import ConfinedFilesystem

    fantasma = tmp_path / "nada"
    env = _RecordingEnv()
    ctx = ToolUseContext(
        session_id="s1",
        exec_env=env,
        cwd=str(fantasma),
        fs=ConfinedFilesystem(roots=[fantasma], write_roots=[fantasma]),
    )
    result = asyncio.run(BashTool().execute({"command": "pwd"}, ctx))
    assert result.is_error is True
    assert "no longer exists" in result.output
    assert env.calls == []  # ni se spawnea, como en A


def test_local_honors_cwd(tmp_path):
    res = asyncio.run(LocalExecEnvironment().run_shell("pwd", cwd=str(tmp_path), timeout=5.0))
    assert res.output.strip() == str(Path(tmp_path).resolve())


def test_local_tracks_the_cwd_after_a_cd(tmp_path):
    (tmp_path / "sub").mkdir()
    res = asyncio.run(LocalExecEnvironment().run_shell("cd sub", cwd=str(tmp_path), timeout=5.0))
    assert res.cwd == str((tmp_path / "sub").resolve())


def test_local_does_not_track_when_the_command_failed(tmp_path):
    """`&&` de A: si el comando falla no se escribe cwd, y el llamante conserva el suyo.

    El código de salida sigue siendo el del comando — el `&&` cortocircuita.
    """
    (tmp_path / "sub").mkdir()
    res = asyncio.run(
        LocalExecEnvironment().run_shell("cd sub && false", cwd=str(tmp_path), timeout=5.0)
    )
    assert res.returncode == 1
    assert res.cwd is None


def test_local_tracking_survives_a_trailing_comment(tmp_path):
    """El `eval` de A (`bashProvider.ts:183`) es PORTANTE, no cosmética.

    Sin él, `<comando> && pwd -P >| f` se concatena en la misma línea y un comentario
    final —o un `&` de background— se traga el rastreo en silencio: el `cd` se perdería
    sin que nada se pusiera rojo.
    """
    (tmp_path / "sub").mkdir()
    res = asyncio.run(
        LocalExecEnvironment().run_shell("cd sub # comentario", cwd=str(tmp_path), timeout=5.0)
    )
    assert res.returncode == 0
    assert res.cwd == str((tmp_path / "sub").resolve())


def test_local_without_cwd_keeps_previous_behaviour():
    """`cwd=None` = no lo fijes ni lo rastrees: el llamante viejo no cambia de conducta."""
    res = asyncio.run(LocalExecEnvironment().run_shell("echo hola", timeout=5.0))
    assert res.returncode == 0
    assert res.cwd is None


def test_bash_refuses_to_run_on_the_host_when_no_exec_env_is_wired(tmp_path):
    """Problema `#2`: sin costura de ejecución **no se ejecuta**, y se dice por qué.

    Este test sustituye a `test_bash_defaults_to_local_when_no_env`, que aseveraba lo
    contrario y por tanto **consagraba la divergencia** (`H-L4`): el fallback
    `or LocalExecEnvironment()` degradaba en silencio de «sandbox inyectado» a «host»,
    que es el footgun que A cerró en #34044 (`sandbox-adapter.ts:549-560`) y lo que
    `wrapWithSandbox` (`:704-717`) resuelve **lanzando**.

    Se asevera por EFECTO, no por el mensaje: el comando dejaría un fichero en disco si
    llegara a correr, y no lo deja.
    """
    marcador = tmp_path / "corrio-en-el-host.txt"
    ctx = ToolUseContext(session_id="s1")  # exec_env=None
    result = asyncio.run(
        BashTool().execute({"command": f"touch {marcador}"}, ctx)
    )
    assert result.is_error is True
    assert not marcador.exists(), "el comando corrió en el host sin costura de ejecución"
    assert "exec_env" in result.output


def test_worktree_refuses_to_run_git_on_the_host_when_no_exec_env_is_wired(tmp_path):
    """El mismo fallback vivía en `worktree.py:64`, y la ficha del `#2` sólo nombraba `bash`.

    Ahí es peor de leer: la cabecera del módulo declara haber cerrado justo este bypass
    (`S15`, git por `run_argv` y no por `create_subprocess_exec` directo) un nivel más
    abajo, mientras el resolutor del backend lo reabría.
    """
    from agentic_runtime.tools.fs_env import ConfinedFilesystem
    from agentic_runtime.tools.native.worktree import EnterWorktreeTool

    ctx = ToolUseContext(
        session_id="s1",
        fs=ConfinedFilesystem(roots=[tmp_path], write_roots=[tmp_path]),
    )
    result = asyncio.run(EnterWorktreeTool().execute({"name": "demo"}, ctx))
    assert result.is_error is True
    assert "exec_env" in result.output
    assert "not a git repository" not in result.output.lower(), (
        "llegó a lanzar git: la guarda no se consultó"
    )


def test_the_worktree_command_launcher_itself_refuses_not_just_its_two_callers(tmp_path):
    """`INY-60` salió VERDE y eso es el hallazgo: nadie medía el choke de `worktree._run`.

    Las dos guardas de tool (`EnterWorktree` arriba, `ExitWorktree` en la rama `remove`)
    tapan hoy todos los caminos, así que reintroducir el fallback DENTRO de `_run` no
    ponía roja ninguna prueba — y `_run` es justo el sitio que una tercera rama futura
    usaría sin guarda. Se acredita por EFECTO: el `argv` tocaría un fichero y no lo toca.

    Límite dicho: se llama a `_run`, que es privado del módulo. Es el único camino para
    medir el choke; las guardas de arriba ya están medidas por sus propios tests.
    """
    import pytest

    from agentic_runtime.tools.exec_env import ExecEnvironmentUnavailable
    from agentic_runtime.tools.native.worktree import _run

    marcador = tmp_path / "git-corrio-en-el-host.txt"
    ctx = ToolUseContext(session_id="s1")  # exec_env=None
    with pytest.raises(ExecEnvironmentUnavailable):
        asyncio.run(_run(ctx, ["touch", str(marcador)], cwd=str(tmp_path), timeout=5.0))
    assert not marcador.exists(), "el argv corrió en el host sin costura de ejecución"


def test_exit_worktree_keeps_working_without_exec_env_because_it_runs_no_command(tmp_path):
    """CONTROL NEGATIVO de la guarda: `action="keep"` no lanza git, luego no la exige.

    Sin este control, «pedir la costura arriba del método» pasaría por correcto y
    rompería un camino legítimo que nunca ejecuta nada.
    """
    from agentic_runtime.tools.fs_env import ConfinedFilesystem
    from agentic_runtime.tools.native.worktree import _WORKTREE_KEY, ExitWorktreeTool

    ctx = ToolUseContext(
        session_id="s1",
        fs=ConfinedFilesystem(roots=[tmp_path], write_roots=[tmp_path]),
    )
    ctx.app_state.native[_WORKTREE_KEY] = {"path": str(tmp_path), "branch": "worktree/x"}
    result = asyncio.run(ExitWorktreeTool().execute({"action": "keep"}, ctx))
    assert result.is_error is False, result.output


def test_exit_worktree_remove_refuses_cleanly_instead_of_propagating(tmp_path):
    """`INY-62` salió VERDE: el control negativo de `action="keep"` no medía la rama `remove`.

    Sin este test, retirar la guarda de la rama que SÍ lanza git pasaba inadvertido: la
    tool dejaba subir `ExecEnvironmentUnavailable` cruda desde `_run`. La conducta
    homologada es la misma que la de `EnterWorktree` —error de tool limpio, no excepción—
    porque quien lo lee es el modelo, no un traceback.
    """
    from agentic_runtime.tools.fs_env import ConfinedFilesystem
    from agentic_runtime.tools.native.worktree import _WORKTREE_KEY, ExitWorktreeTool

    ctx = ToolUseContext(
        session_id="s1",
        fs=ConfinedFilesystem(roots=[tmp_path], write_roots=[tmp_path]),
    )
    ctx.app_state.native[_WORKTREE_KEY] = {"path": str(tmp_path), "branch": "worktree/x"}
    result = asyncio.run(ExitWorktreeTool().execute({"action": "remove"}, ctx))
    assert result.is_error is True
    assert "exec_env" in result.output
    assert ctx.app_state.native.get(_WORKTREE_KEY), (
        "cerró la sesión de worktree sin haber podido ejecutar el remove"
    )


def test_the_assembler_is_the_one_place_that_defaults_the_exec_environment(tmp_path):
    """CONTROL POSITIVO: quitar el fallback de la tool NO deja al integrador degenerado sin `bash`.

    El default sigue existiendo —`LocalExecEnvironment`— pero en el ensamblador
    (`factory.py:256`), que es donde `C10` dice que viven las decisiones de composición.

    Límite dicho: se llega al backend por `_exec_env` (privado) porque el runtime no
    publica accesor; lo que se asevera **no** es el atributo sino que ese backend
    EJECUTA.
    """
    from agentic_runtime.factory import RuntimeConfig, StorageConfig, create_runtime

    # sin `exec_env` en la config: lo único que se le da es el root del storage
    runtime = create_runtime(
        config=RuntimeConfig(storage=StorageConfig(backend="filesystem", root=tmp_path))
    )
    env = runtime._exec_env
    assert isinstance(env, LocalExecEnvironment)
    res = asyncio.run(env.run_shell("echo ensamblado", cwd=str(tmp_path), timeout=5.0))
    assert res.returncode == 0 and "ensamblado" in res.output


def test_bwrap_argv_mounts_workspace_and_passes_command_verbatim():
    env = BwrapExecEnvironment(workspace_root=Path("/srv/u42/work"), bwrap_bin="bwrap")
    cmd = "cat /workspace/secret.txt && echo $HOME"
    argv = env._build_argv(cmd)

    # workspace del host montado en /workspace, cwd en /workspace
    assert "--bind" in argv
    bind_i = argv.index("--bind")
    assert argv[bind_i + 1] == "/srv/u42/work"
    assert argv[bind_i + 2] == "/workspace"
    chdir_i = argv.index("--chdir")
    assert argv[chdir_i + 1] == "/workspace"
    # comando sin reescritura: pasa verbatim como último arg de sh -c (Regla 1)
    assert argv[-3:] == ["/bin/sh", "-c", cmd]


def test_bwrap_translates_the_cwd_into_the_sandbox():
    env = BwrapExecEnvironment(workspace_root=Path("/srv/u42/work"))
    argv = env._build_argv("pwd", "/srv/u42/work/pkg")
    assert argv[argv.index("--chdir") + 1] == "/workspace/pkg"


def test_bwrap_refuses_a_cwd_outside_the_mounted_workspace():
    """Ignorarlo dejaría el comando en `/workspace` como si nada (`FIND-C6-1`)."""
    env = BwrapExecEnvironment(workspace_root=Path("/srv/u42/work"))
    with pytest.raises(ValueError):
        env._build_argv("pwd", "/etc")


@pytest.mark.skipif(shutil.which("bwrap") is None, reason="bwrap no instalado")
def test_bwrap_runs_isolated(tmp_path):
    (tmp_path / "marker.txt").write_text("inside")
    env = BwrapExecEnvironment(workspace_root=tmp_path)
    res = asyncio.run(env.run_shell("cat marker.txt", timeout=10.0))
    assert res.returncode == 0
    assert "inside" in res.output


def test_a_subagent_cannot_move_the_shared_cwd(tmp_path):
    """`preventCwdChanges = !isMainThread` (`Shell.ts:385`, B11).

    El subagente puede hacer `cd` DENTRO de su comando; lo que no puede es dejar movido
    el cwd que comparte con quien lo lanzó. Hacer persistir el cwd sin esta guarda habría
    abierto un agujero que el canónico cierra explícitamente.
    """
    destino = tmp_path / "sub"
    destino.mkdir()
    env = _RecordingEnv(tracked_cwd=str(destino))
    ctx = ToolUseContext(session_id="s1", exec_env=env, cwd=str(tmp_path), is_subagent=True)
    asyncio.run(BashTool().execute({"command": "cd sub"}, ctx))
    assert ctx.cwd == str(tmp_path)
