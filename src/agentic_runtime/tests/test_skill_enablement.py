"""R2 — enablement como predicado de código (espejo del `isEnabled` canónico).

El canónico no persiste un toggle mutable: la enablement es un predicado evaluado al
construir el catálogo/menú. Aquí:

- `SkillDefinition.enabled` se declara en el frontmatter (`enabled: false`, default true),
  leído de forma TOLERANTE (solo `false` literal deshabilita; ausente/corrupto → habilitado).
- `SkillsProvider` acepta un predicado opcional `is_enabled(skill) -> bool`, default
  `lambda s: s.enabled`. Un skill deshabilitado NO se lista en `catalog()` NI es invocable
  por la tool `Skill` ni por slash command.
"""
from agentic_runtime.capabilities.skills import (
    SkillsProvider,
    load_skill_text,
    parse_frontmatter,
    process_slash_command,
)
from agentic_runtime.context.tool_use import ToolUseContext


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


def _md(front_extra: str = "") -> str:
    return f"---\ndescription: d\n{front_extra}---\ncuerpo"


# --- frontmatter `enabled`: tolerante, default habilitado --------------------

def test_enabled_absent_defaults_true():
    assert load_skill_text("a", _md()).enabled is True


def test_enabled_false_disables():
    assert load_skill_text("a", _md("enabled: false\n")).enabled is False


def test_enabled_string_false_disables():
    front, _ = parse_frontmatter(_md('enabled: "false"\n'))
    assert front.enabled is False


def test_enabled_malformed_defaults_true():
    # un valor no-bool no debe deshabilitar silenciosamente (default seguro = habilitado)
    assert load_skill_text("a", _md("enabled: [x]\n")).enabled is True


# --- frontmatter `version`: passthrough tolerante (trazabilidad del manifest) -

def test_version_passthrough_string():
    assert load_skill_text("a", _md("version: 1.2.3\n")).version == "1.2.3"


def test_version_absent_defaults_empty():
    assert load_skill_text("a", _md()).version == ""


def test_version_numeric_coerced_to_string():
    # YAML `version: 1.0` llega como float → se coacciona a str, no rompe
    assert load_skill_text("a", _md("version: 1.0\n")).version == "1.0"


# --- catalog filtra por el predicado ----------------------------------------

def test_catalog_excludes_disabled_skill_by_default_predicate():
    provider = SkillsProvider()
    provider.add_skill_text("on", _md())
    provider.add_skill_text("off", _md("enabled: false\n"))
    names = {c.name for c in provider.catalog(_ctx())}
    assert names == {"on"}


def test_catalog_honors_injected_predicate():
    # predicado del integrador (feature-flag style) tiene prioridad sobre el default
    provider = SkillsProvider(is_enabled=lambda s: s.name != "blocked")
    provider.add_skill_text("blocked", _md())
    provider.add_skill_text("ok", _md())
    names = {c.name for c in provider.catalog(_ctx())}
    assert names == {"ok"}


# --- la tool Skill no invoca un skill deshabilitado -------------------------

async def test_skill_tool_rejects_disabled_skill():
    provider = SkillsProvider()
    provider.add_skill_text("on", _md())               # habilitada → la tool Skill se ofrece
    provider.add_skill_text("off", _md("enabled: false\n"))
    tool = provider.tools(_ctx())[0]
    result = await tool.execute({"command": "off"}, _ctx())
    assert result.is_error
    assert "no encontrada" in result.output.lower()
    assert "off" not in result.output.split("Disponibles:")[-1]  # no se lista como disponible


async def test_skill_tool_invokes_enabled_skill():
    provider = SkillsProvider()
    provider.add_skill_text("on", _md())
    tool = provider.tools(_ctx())[0]
    result = await tool.execute({"command": "on"}, _ctx())
    assert not result.is_error
    assert "activada" in result.output


# --- slash command no activa un skill deshabilitado -------------------------

def test_slash_command_ignores_disabled_skill():
    provider = SkillsProvider()
    provider.add_skill_text("off", _md("enabled: false\n"))
    # vía el provider (que conoce su predicado)
    assert provider.process_slash_command("/off", _ctx()) is None


def test_slash_command_activates_enabled_skill():
    provider = SkillsProvider()
    provider.add_skill_text("on", _md())
    out = provider.process_slash_command("/on", _ctx())
    assert out is not None and "activada" in out


# --- process_slash_command directo honra el predicado pasado ----------------

def test_process_slash_command_predicate_arg_gates():
    provider = SkillsProvider()
    provider.add_skill_text("on", _md())
    state = provider.state
    assert process_slash_command("/on", state, _ctx(), is_enabled=lambda s: False) is None
    assert process_slash_command("/on", state, _ctx(), is_enabled=lambda s: True) is not None
