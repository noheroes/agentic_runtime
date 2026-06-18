"""Tests de slash commands de skills (S4).

El procesamiento de `/skill args` vive en el provider/command processor, NO en el loop.
Produce el mismo efecto que invocar la tool `Skill` (activa estado + allowed-tools).
"""
from agentic_runtime.capabilities.skills import (
    SkillsProvider,
    parse_slash_command,
)
from agentic_runtime.context.tool_use import ToolUseContext


def _skill_md(front: str, body: str) -> str:
    return f"---\n{front}\n---\n{body}"


def _provider() -> SkillsProvider:
    p = SkillsProvider()
    p.add_skill_text(
        "diagrams",
        _skill_md("name: diagrams\ndescription: d\nallowed-tools: drawio_create", "Usa drawio."),
    )
    return p


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------

def test_parse_slash_command_variants():
    assert parse_slash_command("/diagrams") == ("diagrams", "")
    assert parse_slash_command("/diagrams foo bar") == ("diagrams", "foo bar")
    assert parse_slash_command("hola mundo") is None  # no es slash
    assert parse_slash_command("/") is None
    assert parse_slash_command("   /x  ") == ("x", "")


# ---------------------------------------------------------------------------
# process: misma activación que la tool Skill
# ---------------------------------------------------------------------------

def test_process_slash_command_activates_known_skill():
    provider = _provider()
    ctx = _ctx()
    out = provider.process_slash_command("/diagrams algo", ctx)

    assert out is not None and "Usa drawio." in out
    assert ctx.app_state.capabilities["invoked_skills"] == ["diagrams"]
    assert "drawio_create" in ctx.permission_context.allowed_names()


def test_process_slash_command_unknown_skill_returns_none():
    provider = _provider()
    ctx = _ctx()
    assert provider.process_slash_command("/ghost", ctx) is None
    # ctx intacto: no activó nada
    assert "invoked_skills" not in ctx.app_state.capabilities


def test_process_non_slash_returns_none():
    provider = _provider()
    assert provider.process_slash_command("usa diagrams por favor", _ctx()) is None


# ---------------------------------------------------------------------------
# Desacople: el loop no importa el dispatcher de skills
# ---------------------------------------------------------------------------

def test_loop_module_does_not_import_skills():
    from pathlib import Path

    import agentic_runtime.loop.agent_loop as loop_mod

    source = Path(loop_mod.__file__).read_text(encoding="utf-8")
    assert "capabilities.skills" not in source
    assert "skills.commands" not in source
