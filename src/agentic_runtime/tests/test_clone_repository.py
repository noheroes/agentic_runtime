"""CloneRepositoryTool: normalización de URL, confinamiento, inyección de credencial."""
from pathlib import Path

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools.fs_env import ConfinedFilesystem
from agentic_runtime.tools.native.clone_repository import CloneRepositoryTool, _normalize


class _FakeProc:
    def __init__(self, returncode=0, output=b"done"):
        self.returncode = returncode
        self._output = output

    async def communicate(self):
        return self._output, None


def _ctx(tmp: Path, *, token=None) -> ToolUseContext:
    ctx = ToolUseContext(session_id="s1")
    ctx.fs = ConfinedFilesystem(roots=[tmp], write_roots=[tmp])
    if token is not None:
        ctx.git_credentials = type("P", (), {"token": staticmethod(lambda host: token)})()
    return ctx


def _patch_git(monkeypatch, proc=None):
    captured = {}

    async def fake_exec(*args, stdout=None, stderr=None, env=None):
        captured["args"] = list(args)
        captured["env"] = env
        return proc or _FakeProc()

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)
    return captured


# ── _normalize ────────────────────────────────────────────────────────────────

def test_normalize_owner_repo_assumes_github():
    assert _normalize("noheroes/agentic_trace") == (
        "https://github.com/noheroes/agentic_trace.git", "github.com", "agentic_trace",
    )


def test_normalize_full_https_and_strips_git_suffix():
    assert _normalize("https://gitlab.com/grp/sub/proj.git") == (
        "https://gitlab.com/grp/sub/proj.git", "gitlab.com", "proj",
    )


def test_normalize_rejects_non_https():
    for bad in ("git@github.com:o/r.git", "ftp://x/y", "just-a-word"):
        with pytest.raises(ValueError):
            _normalize(bad)


# ── execute ───────────────────────────────────────────────────────────────────

async def test_clone_public_no_credential_helper(tmp_path, monkeypatch):
    cap = _patch_git(monkeypatch)
    res = await CloneRepositoryTool().execute({"repository": "o/r"}, _ctx(tmp_path))

    assert not res.is_error
    assert cap["args"] == ["git", "clone", "https://github.com/o/r.git", str(tmp_path / "r")]
    assert "GIT_CLONE_TOKEN" not in cap["env"]


async def test_clone_private_injects_token_via_helper_not_argv(tmp_path, monkeypatch):
    cap = _patch_git(monkeypatch)
    res = await CloneRepositoryTool().execute({"repository": "o/r"}, _ctx(tmp_path, token="ghp_secret"))

    assert not res.is_error
    # token pasa por env, nunca en argv, y no queda en la URL
    assert "ghp_secret" not in " ".join(cap["args"])
    assert cap["env"]["GIT_CLONE_TOKEN"] == "ghp_secret"
    assert any(a.startswith("credential.helper=") for a in cap["args"])
    assert "https://github.com/o/r.git" in cap["args"]


async def test_clone_custom_directory(tmp_path, monkeypatch):
    cap = _patch_git(monkeypatch)
    await CloneRepositoryTool().execute({"repository": "o/r", "directory": "dst"}, _ctx(tmp_path))
    assert cap["args"][-1] == str(tmp_path / "dst")


async def test_clone_rejects_path_outside_workspace(tmp_path, monkeypatch):
    _patch_git(monkeypatch)
    res = await CloneRepositoryTool().execute({"repository": "o/r", "directory": "../escape"}, _ctx(tmp_path))
    assert res.is_error and "workspace" in res.output.lower()


async def test_clone_rejects_existing_destination(tmp_path, monkeypatch):
    _patch_git(monkeypatch)
    (tmp_path / "r").mkdir()
    res = await CloneRepositoryTool().execute({"repository": "o/r"}, _ctx(tmp_path))
    assert res.is_error and "existe" in res.output.lower()


async def test_clone_reports_git_failure(tmp_path, monkeypatch):
    _patch_git(monkeypatch, proc=_FakeProc(returncode=128, output=b"fatal: repo not found"))
    res = await CloneRepositoryTool().execute({"repository": "o/r"}, _ctx(tmp_path))
    assert res.is_error and "fatal" in res.output


async def test_clone_git_not_installed(tmp_path, monkeypatch):
    async def boom(*a, **k):
        raise FileNotFoundError()
    monkeypatch.setattr("asyncio.create_subprocess_exec", boom)
    res = await CloneRepositoryTool().execute({"repository": "o/r"}, _ctx(tmp_path))
    assert res.is_error and "git" in res.output.lower()
