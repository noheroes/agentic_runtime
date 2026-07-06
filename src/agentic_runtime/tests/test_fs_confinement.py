"""
TDD del confinamiento fs (F5) — reproduce el hueco de seguridad P1: las fs-tools nativas
escribían/leían fuera del workspace. Homologado de `utils/permissions/filesystem.ts`.

Cubre: mecanismo homologado (traversal / symlink-escape / dentro-fuera), la costura
`ConfinedFilesystem.resolve`, y que una fs-tool (write_file) queda confinada por construcción
al enrutar por `ctx.fs` — sin código de confinamiento en la tool.
"""
import os

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools.fs_env import (
    ConfinedFilesystem,
    PathOutsideWorkspace,
    contains_path_traversal,
    path_in_allowed_working_path,
)
from agentic_runtime.tools.native.read_file import ReadFileTool
from agentic_runtime.tools.native.write_file import WriteFileTool


# ── Mecanismo homologado ────────────────────────────────────────────────────

def test_contains_path_traversal_detects_dotdot():
    assert contains_path_traversal("../etc/passwd")
    assert contains_path_traversal("a/../../b")
    assert not contains_path_traversal("a/b/c")
    assert not contains_path_traversal("..foo/bar")  # `..` no es un segmento


def test_inside_root_allowed(tmp_path):
    root = str(tmp_path)
    assert path_in_allowed_working_path(str(tmp_path / "sub" / "f.txt"), [root], root)


def test_outside_root_denied(tmp_path):
    root = str(tmp_path / "ws")
    os.makedirs(root)
    assert not path_in_allowed_working_path("/etc/passwd", [root], root)


def test_traversal_escape_denied(tmp_path):
    root = str(tmp_path / "ws")
    os.makedirs(root)
    escape = os.path.join(root, "..", "secret.txt")
    assert not path_in_allowed_working_path(escape, [root], root)


def test_symlink_escape_denied(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("top secret")
    link = root / "link"
    link.symlink_to(outside)  # dir dentro del root que apunta afuera
    # El path literal cae dentro, pero el realpath escapa → denegado.
    assert not path_in_allowed_working_path(str(link / "secret.txt"), [str(root)], str(root))


# ── Costura ConfinedFilesystem ───────────────────────────────────────────────

def test_resolve_inside_returns_path(tmp_path):
    fs = ConfinedFilesystem(roots=[tmp_path])
    resolved = fs.resolve(str(tmp_path / "a.txt"), for_write=True)
    assert resolved == tmp_path / "a.txt"


def test_resolve_outside_raises(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    fs = ConfinedFilesystem(roots=[root])
    with pytest.raises(PathOutsideWorkspace):
        fs.resolve("/etc/passwd", for_write=True)


def test_resolve_traversal_raises(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    fs = ConfinedFilesystem(roots=[root])
    with pytest.raises(PathOutsideWorkspace):
        fs.resolve(str(root / ".." / "escape.txt"), for_write=True)


def test_default_confines_to_cwd():
    fs = ConfinedFilesystem()
    resolved = fs.resolve(os.path.join(os.getcwd(), "x.txt"), for_write=True)
    assert str(resolved) == os.path.join(os.getcwd(), "x.txt")
    with pytest.raises(PathOutsideWorkspace):
        fs.resolve("/etc/passwd", for_write=True)


# ── Tool confinada por construcción (sin código extra en la tool) ────────────

def _ctx(root):
    return ToolUseContext(session_id="s", fs=ConfinedFilesystem(roots=[root]))


@pytest.mark.asyncio
async def test_write_file_inside_workspace_ok(tmp_path):
    ctx = _ctx(tmp_path)
    target = tmp_path / "out.txt"
    result = await WriteFileTool().execute(
        {"path": str(target), "content": "hello"}, ctx
    )
    assert not result.is_error
    assert target.read_text() == "hello"


@pytest.mark.asyncio
async def test_write_file_outside_workspace_denied(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    ctx = _ctx(ws)
    forbidden = tmp_path / "escape.txt"
    result = await WriteFileTool().execute(
        {"path": str(forbidden), "content": "pwned"}, ctx
    )
    assert result.is_error
    assert not forbidden.exists()


@pytest.mark.asyncio
async def test_read_file_outside_workspace_denied(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("classified")
    ctx = _ctx(ws)
    result = await ReadFileTool().execute({"path": str(secret)}, ctx)
    assert result.is_error
    assert "classified" not in result.output
