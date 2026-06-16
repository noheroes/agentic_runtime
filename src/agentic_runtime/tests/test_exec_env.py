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
    """Backend inyectado que registra la llamada en vez de tocar el host."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, float]] = []

    async def run_shell(self, command: str, *, timeout: float) -> ShellResult:
        self.calls.append((command, timeout))
        return ShellResult(output="from-injected-env", returncode=0)


def test_bash_dispatches_to_injected_env():
    env = _RecordingEnv()
    ctx = ToolUseContext(session_id="s1", exec_env=env)
    result = asyncio.run(BashTool().execute({"command": "rm -rf /"}, ctx))
    assert env.calls == [("rm -rf /", BashTool.timeout_seconds)]  # no tocó el host
    assert result.output == "from-injected-env"
    assert result.is_error is False


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


@pytest.mark.skipif(shutil.which("bwrap") is None, reason="bwrap no instalado")
def test_bwrap_runs_isolated(tmp_path):
    (tmp_path / "marker.txt").write_text("inside")
    env = BwrapExecEnvironment(workspace_root=tmp_path)
    res = asyncio.run(env.run_shell("cat marker.txt", timeout=10.0))
    assert res.returncode == 0
    assert "inside" in res.output
