"""Homologación 10·tools-native — cada tool nativa (`tools/native/*.py`) vs su contraparte
canónica `tools/*Tool/` (uno a uno).

Los tests que PASAN codifican comportamiento YA homologado (naming de Edit, context_modifier/
ends_turn aplicados = CORR a 09, caps glob/grep espejo, plan-mode root-only, slug worktree). Los
`xfail(strict=True)` codifican los gaps FIND-NATIVE-*: fallan HOY (comportamiento homologado ausente)
y su fallo ES la evidencia del gap. Si alguno empezara a pasar, el strict lo vuelve error → señal de
reclasificar el estado en `10-tools-native.md`.
"""
from __future__ import annotations

import asyncio

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools.fs_env import ConfinedFilesystem
from agentic_runtime.tools.native.ask_user import AskUserQuestionTool
from agentic_runtime.tools.native.bash import BashTool
from agentic_runtime.tools.native.config import ConfigTool
from agentic_runtime.tools.native.file_edit import FileEditTool
from agentic_runtime.tools.native.glob_tool import DEFAULT_GLOB_LIMIT
from agentic_runtime.tools.native.grep_tool import DEFAULT_HEAD_LIMIT
from agentic_runtime.tools.native.plan_mode import EnterPlanModeTool
from agentic_runtime.tools.native.read_file import ReadFileTool
from agentic_runtime.tools.native.task_tools import TaskUpdateTool
from agentic_runtime.tools.native.todo_write import TodoWriteTool
from agentic_runtime.tools.native.worktree import EnterWorktreeTool, _validate_slug
from agentic_runtime.tools.native.write_file import WriteFileTool


def _ctx(tmp_path=None, **kw) -> ToolUseContext:
    if tmp_path is not None:
        kw.setdefault("fs", ConfinedFilesystem(roots=[tmp_path], write_roots=[tmp_path]))
    return ToolUseContext(session_id="s1", stop=asyncio.Event(), **kw)


# ===========================================================================
# HOMOLOGADO (PASA)
# ===========================================================================

def test_edit_tool_name_matches_canonical():
    """`FILE_EDIT_TOOL_NAME='Edit'` homologa el nombre canónico (a diferencia de sus hermanos fs)."""
    assert FileEditTool.name == "Edit"


def test_glob_and_grep_caps_mirror_canonical():
    """Caps espejo: glob maxResults 100, grep DEFAULT_HEAD_LIMIT 250 (§A13/A14)."""
    assert DEFAULT_GLOB_LIMIT == 100
    assert DEFAULT_HEAD_LIMIT == 250


def test_context_modifier_attached_and_applicable():
    """CORR a 09·A24/D7: plan/worktree/config/todo adjuntan `context_modifier` al ToolResult
    y el loop lo aplica (agent_loop.py:329-337). Verifica que el modifier existe y muta app_state."""
    ctx = _ctx()
    r = asyncio.run(TodoWriteTool().execute({"todos": []}, ctx))
    modifier = getattr(r, "context_modifier", None)
    assert modifier is not None
    modifier(ctx)
    assert ctx.app_state.native.get("todos") == []


def test_ends_turn_signalled_by_hitl_tools():
    """AskUserQuestion/ExitPlanMode ceden el turno con `ends_turn` (homólogo de
    requiresUserInteraction canónico, §C4/D2)."""
    ctx = _ctx()
    r = asyncio.run(AskUserQuestionTool().execute(
        {"questions": [{"question": "¿q?", "header": "h", "options": [{"label": "a"}, {"label": "b"}]}]},
        ctx,
    ))
    assert getattr(r, "ends_turn", False) is True


def test_enter_plan_mode_is_root_only():
    """EnterPlanMode canónico es main-thread-only; el runtime lo rechaza en subagente (§D1)."""
    ctx = _ctx(is_subagent=True)
    r = asyncio.run(EnterPlanModeTool().execute({}, ctx))
    assert r.is_error


def test_worktree_slug_validation():
    """Slug de worktree validado (letras/dígitos/._-; segmentos por '/'), §E1."""
    assert _validate_slug("feature-x") is None
    assert _validate_slug("bad name!") is not None


def test_config_get_returns_json():
    """Config get sobre app_state.native (homólogo funcional, §C1)."""
    ctx = _ctx()
    r = asyncio.run(ConfigTool().execute({"setting": "model"}, ctx))
    assert '"operation": "get"' in r.output


def test_ask_user_schema_shape():
    """Schema idéntico al canónico: 1-4 preguntas, 2-4 opciones, multiSelect, sin 'Other' (§C4)."""
    q = AskUserQuestionTool.input_schema["properties"]["questions"]
    assert q["minItems"] == 1 and q["maxItems"] == 4


# ===========================================================================
# GAPS — xfail(strict): fallan HOY, su fallo ES la evidencia
# ===========================================================================

@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-NAME: bash/read_file/write_file/glob/grep no homologan el nombre canónico (Bash/Read/Write/Glob/Grep)")
def test_fs_shell_tools_match_canonical_names():
    assert BashTool.name == "Bash"
    assert ReadFileTool.name == "Read"
    assert WriteFileTool.name == "Write"


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-READSTATE/A5: read_file no puebla un read_file_state en el ToolUseContext (base ausente de read-before-edit)")
def test_read_populates_read_file_state(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hola\nmundo\n")
    ctx = _ctx(tmp_path)
    asyncio.run(ReadFileTool().execute({"path": str(f)}, ctx))
    assert getattr(ctx, "read_file_state", None) and str(f) in ctx.read_file_state


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-EDITGUARDS=FIND-CTX1: file_edit no impone read-before-edit (canónico rechaza editar sin leer antes)")
def test_edit_requires_read_before_edit(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("alfa beta\n")
    ctx = _ctx(tmp_path)  # nunca se leyó f
    r = asyncio.run(FileEditTool().execute(
        {"file_path": str(f), "old_string": "alfa", "new_string": "gamma"}, ctx,
    ))
    assert r.is_error and "read it first" in r.output.lower()


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-EDITGUARDS=G8/FIND-TOOL9: write_file no bloquea dangerous-files (.claude/settings.json) dentro del workspace")
def test_write_blocks_dangerous_settings_file(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    ctx = _ctx(tmp_path)
    r = asyncio.run(WriteFileTool().execute({"path": str(settings), "content": "{}"}, ctx))
    assert r.is_error  # homologado: validateInputForSettingsFileEdit lo rechazaría


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-READ/A6: Edit no soporta replace_all (canónico sí)")
def test_edit_supports_replace_all():
    assert "replace_all" in FileEditTool.input_schema["properties"]


@pytest.mark.xfail(strict=True, reason="GAP-TOOL2/GAP-MODE2: worktree.safe_for_background=False pero el canónico lo incluye en ASYNC_AGENT_ALLOWED_TOOLS")
def test_worktree_allowed_in_background():
    assert EnterWorktreeTool.safe_for_background is True


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-TASK/G3: TaskUpdate no modela transiciones de status (canónico: pending/in_progress/completed/deleted)")
def test_task_update_has_status():
    assert "status" in TaskUpdateTool.input_schema["properties"]


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-BASH=FIND-TOOL8/F2: bash sin shell persistente — cd no persiste entre llamadas")
def test_bash_persistent_shell(tmp_path):
    ctx = _ctx()
    asyncio.run(BashTool().execute({"command": f"cd {tmp_path}"}, ctx))
    r = asyncio.run(BashTool().execute({"command": "pwd"}, ctx))
    assert str(tmp_path) in r.output


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-READ/A3b: read_file no prefija números de línea (canónico addLineNumbers, cat -n)")
def test_read_adds_line_numbers(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("alfa\nbeta\n")
    ctx = _ctx(tmp_path)
    r = asyncio.run(ReadFileTool().execute({"path": str(f)}, ctx))
    # homologado: cada línea con su número (p.ej. "     1\talfa")
    assert "1\talfa" in r.output or r.output.lstrip().startswith("1")


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-READ/A3c: read_file no rechaza binarios (canónico: 'cannot read binary files')")
def test_read_rejects_binary(tmp_path):
    png = tmp_path / "img.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\x00")
    ctx = _ctx(tmp_path)
    r = asyncio.run(ReadFileTool().execute({"path": str(png)}, ctx))
    assert r.is_error


@pytest.mark.xfail(strict=True, reason="FIND-NATIVE-BASH-DEPTH/B12: is_error=returncode!=0 a secas — grep sin match (rc=1) NO debería ser error (interpretCommandResult)")
def test_bash_grep_no_match_not_error(tmp_path):
    ctx = _ctx()
    r = asyncio.run(BashTool().execute({"command": "printf 'a\\nb\\n' | grep zzz"}, ctx))
    assert not r.is_error  # rc=1 semántico: "sin coincidencias", no fallo
