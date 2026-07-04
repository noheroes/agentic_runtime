"""Cap de salida de grep/glob (homologado al canónico).

Regresión: sin cap, grep sobre un árbol grande volcaba MBs al contexto (session.json crecía
hasta romper al proveedor). Estos casos ejercen el cap sobre un filesystem temporal REAL.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from ..context.tool_use import ToolUseContext
from ..tools.native.glob_tool import DEFAULT_GLOB_LIMIT, GlobTool
from ..tools.native.grep_tool import DEFAULT_HEAD_LIMIT, MAX_LINE_LEN, GrepTool


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


def _run(tool, input):
    return asyncio.run(tool.execute(input, _ctx()))


# --- grep -------------------------------------------------------------------

def test_grep_caps_at_default_head_limit(tmp_path: Path):
    f = tmp_path / "big.txt"
    f.write_text("\n".join("match" for _ in range(1000)), encoding="utf-8")
    res = _run(GrepTool(), {"pattern": "match", "path": str(tmp_path)})
    match_lines = [ln for ln in res.output.splitlines() if ln.endswith(": match")]
    assert len(match_lines) == DEFAULT_HEAD_LIMIT
    assert "Showing 250 of 1000 matches" in res.output


def test_grep_head_limit_zero_returns_all(tmp_path: Path):
    f = tmp_path / "big.txt"
    f.write_text("\n".join("match" for _ in range(1000)), encoding="utf-8")
    res = _run(GrepTool(), {"pattern": "match", "path": str(tmp_path), "head_limit": 0})
    match_lines = [ln for ln in res.output.splitlines() if ln.endswith(": match")]
    assert len(match_lines) == 1000
    assert "Showing" not in res.output


def test_grep_offset_paginates(tmp_path: Path):
    f = tmp_path / "n.txt"
    f.write_text("\n".join(f"match {i}" for i in range(100)), encoding="utf-8")
    res = _run(GrepTool(), {"pattern": "match", "path": str(tmp_path), "offset": 10, "head_limit": 5})
    lines = [ln for ln in res.output.splitlines() if ".txt:" in ln]
    assert len(lines) == 5
    assert "match 10" in lines[0]


def test_grep_excludes_vcs_dirs(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "cfg").write_text("secret match", encoding="utf-8")
    (tmp_path / "real.txt").write_text("real match", encoding="utf-8")
    res = _run(GrepTool(), {"pattern": "match", "path": str(tmp_path)})
    assert "real.txt" in res.output
    assert ".git" not in res.output


def test_grep_truncates_long_lines(tmp_path: Path):
    f = tmp_path / "long.txt"
    f.write_text("match " + "x" * 2000, encoding="utf-8")
    res = _run(GrepTool(), {"pattern": "match", "path": str(tmp_path)})
    body = res.output.splitlines()[0]
    # `path:1: ` prefijo + MAX_LINE_LEN chars + elipsis; muy por debajo de la línea cruda de 2006.
    assert len(body) < MAX_LINE_LEN + 100
    assert body.endswith("…")


def test_grep_invalid_regex_is_error(tmp_path: Path):
    res = _run(GrepTool(), {"pattern": "(", "path": str(tmp_path)})
    assert res.is_error
    assert "invalid regex" in res.output


# --- glob -------------------------------------------------------------------

def test_glob_caps_and_notes_truncation(tmp_path: Path):
    for i in range(DEFAULT_GLOB_LIMIT + 50):
        (tmp_path / f"f{i:04d}.txt").write_text("x", encoding="utf-8")
    res = _run(GlobTool(), {"pattern": "*.txt", "path": str(tmp_path)})
    file_lines = [ln for ln in res.output.splitlines() if ln.endswith(".txt")]
    assert len(file_lines) == DEFAULT_GLOB_LIMIT
    assert "Results are truncated" in res.output


def test_glob_under_limit_no_note(tmp_path: Path):
    for i in range(5):
        (tmp_path / f"f{i}.txt").write_text("x", encoding="utf-8")
    res = _run(GlobTool(), {"pattern": "*.txt", "path": str(tmp_path)})
    assert "truncated" not in res.output
    assert len([ln for ln in res.output.splitlines() if ln.endswith(".txt")]) == 5
