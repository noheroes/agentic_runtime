"""B2 — ToolExecEnvironment inyectable: BashTool despacha al backend, no al host.

- default in-process (`LocalExecEnvironment`) sin cambio de comportamiento;
- BashTool usa `ctx.exec_env` cuando se inyecta (D5c) y cae al local cuando es None;
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


def test_bash_defaults_to_local_when_no_env():
    ctx = ToolUseContext(session_id="s1")  # exec_env=None
    result = asyncio.run(BashTool().execute({"command": "echo inprocess"}, ctx))
    assert "inprocess" in result.output
    assert result.is_error is False


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
