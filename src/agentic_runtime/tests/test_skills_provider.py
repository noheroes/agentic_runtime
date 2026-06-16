"""Tests para capabilities/skills/ — SkillsProvider shell (Fase S0).

Foco: contrato CapabilityProvider + robustez ante skills de terceros
(frontmatter tolerante por campo, identidad desde el directorio, aislamiento por ítem).
"""
from pathlib import Path

from agentic_runtime.capabilities import CapabilityManager, CapabilityProvider
from agentic_runtime.capabilities.skills import (
    SkillDefinition,
    SkillFrontmatter,
    SkillsProvider,
    load_skill_text,
    load_skills_dir,
    parse_frontmatter,
)
from agentic_runtime.context.tool_use import ToolUseContext


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


def _skill_md(front: str, body: str) -> str:
    return f"---\n{front}\n---\n{body}"


# ---------------------------------------------------------------------------
# Contrato
# ---------------------------------------------------------------------------

def test_provider_satisfies_capability_protocol():
    assert isinstance(SkillsProvider(), CapabilityProvider)
    assert SkillsProvider().name == "skills"


# ---------------------------------------------------------------------------
# Frontmatter: parseo total que nunca lanza
# ---------------------------------------------------------------------------

def test_parse_frontmatter_absent_returns_empty_and_full_body():
    front, body = parse_frontmatter("solo cuerpo, sin frontmatter")
    assert front == SkillFrontmatter()
    assert body == "solo cuerpo, sin frontmatter"


def test_parse_frontmatter_open_block_is_treated_as_body():
    # apertura `---` sin cierre → no es frontmatter; todo es cuerpo
    text = "---\nname: x\nsin cierre"
    front, body = parse_frontmatter(text)
    assert front.name is None
    assert body == text


def test_parse_frontmatter_invalid_yaml_degrades_to_defaults():
    front, body = parse_frontmatter(_skill_md("name: [unclosed", "cuerpo"))
    assert front.name is None  # YAML inválido → {}
    assert body == "cuerpo"


def test_parse_frontmatter_non_mapping_degrades_to_defaults():
    front, _ = parse_frontmatter(_skill_md("- just\n- a\n- list", "cuerpo"))
    assert front == SkillFrontmatter()


def test_frontmatter_open_schema_keeps_unknown_keys():
    front, _ = parse_frontmatter(_skill_md("name: s\nweird-prop: 42", "b"))
    assert front.name == "s"
    assert front.model_extra and front.model_extra.get("weird-prop") == 42


def test_frontmatter_non_string_name_degrades_to_none():
    front, _ = parse_frontmatter(_skill_md("name:\n  nested: bad", "b"))
    assert front.name is None


def test_frontmatter_allowed_tools_accepts_list_and_csv():
    list_front, _ = parse_frontmatter(_skill_md("allowed-tools:\n  - Read\n  - Write", "b"))
    assert list_front.allowed_tools == ["Read", "Write"]
    csv_front, _ = parse_frontmatter(_skill_md("allowed-tools: Read, Write", "b"))
    assert csv_front.allowed_tools == ["Read", "Write"]


# ---------------------------------------------------------------------------
# Loader: defaults definidos por campo (robustez ante terceros)
# ---------------------------------------------------------------------------

def test_load_skill_minimal_uses_dir_name_and_derives_description():
    skill = load_skill_text("my-skill", "Primer párrafo útil.\n\nResto del cuerpo.")
    assert skill.name == "my-skill"  # identidad desde el directorio
    assert skill.description == "Primer párrafo útil."  # derivada del cuerpo
    assert skill.allowed_tools == []  # no activa tools extra
    assert skill.model is None  # hereda el modelo del padre


def test_load_skill_frontmatter_name_overrides_dir_hint():
    skill = load_skill_text("dir-name", _skill_md("name: explicit\ndescription: d", "b"))
    assert skill.name == "explicit"
    assert skill.description == "d"


def test_load_skill_model_inherit_normalizes_to_none():
    inherit = load_skill_text("s", _skill_md("model: inherit", "b"))
    assert inherit.model is None
    explicit = load_skill_text("s", _skill_md("model: gpt-5.4-mini", "b"))
    assert explicit.model == "gpt-5.4-mini"


def test_load_skill_is_typed_definition():
    assert isinstance(load_skill_text("s", "body"), SkillDefinition)


# ---------------------------------------------------------------------------
# Loader de directorio: aislamiento por ítem
# ---------------------------------------------------------------------------

def test_load_skills_dir_isolates_per_item(tmp_path: Path):
    good = tmp_path / "good"
    good.mkdir()
    (good / "SKILL.md").write_text(_skill_md("name: good\ndescription: ok", "cuerpo"))

    broken = tmp_path / "broken"
    broken.mkdir()
    # frontmatter con YAML inválido: carga igual, con defaults (no aborta el resto)
    (broken / "SKILL.md").write_text(_skill_md("name: [oops", "instrucciones rotas"))

    skills = load_skills_dir(tmp_path)
    by_name = {s.name: s for s in skills}
    assert "good" in by_name
    # la rota carga con identidad desde el directorio, sin excepción
    assert "broken" in by_name
    assert by_name["broken"].instructions == "instrucciones rotas"


def test_load_skills_dir_missing_root_returns_empty(tmp_path: Path):
    assert load_skills_dir(tmp_path / "no-existe") == []


# ---------------------------------------------------------------------------
# Provider: catálogo / shell honesto (tools/active/compact vacíos en S0)
# ---------------------------------------------------------------------------

def test_provider_catalog_emits_skill_summaries(tmp_path: Path):
    d = tmp_path / "diagrams"
    d.mkdir()
    (d / "SKILL.md").write_text(_skill_md("name: diagrams\ndescription: dibuja", "b"))

    provider = SkillsProvider()
    provider.load_dir(tmp_path)
    catalog = provider.catalog(_ctx())
    assert len(catalog) == 1
    assert catalog[0].kind == "skill"
    assert catalog[0].provider == "skills"
    assert catalog[0].description == "dibuja"
    assert catalog[0].when_to_use == "dibuja"


def test_provider_shell_returns_empty_for_unimplemented_phases():
    provider = SkillsProvider()
    provider.add_skill_text("s", _skill_md("description: d", "b"))
    ctx = _ctx()
    assert provider.tools(ctx) == []  # SkillTool es S1
    assert provider.active_context(ctx) == []  # S1/S3
    assert provider.compact_context(ctx) == []  # S5


def test_add_skill_text_registers_and_is_retrievable():
    provider = SkillsProvider()
    provider.add_skill_text("s", _skill_md("description: d", "b"))
    assert provider.state.get("s") is not None
    assert provider.state.get("s").description == "d"


# ---------------------------------------------------------------------------
# Convergencia con C0: el manager coordina el provider sin importarlo
# ---------------------------------------------------------------------------

def test_skills_catalog_flows_through_capability_manager():
    provider = SkillsProvider()
    provider.add_skill_text("alpha", _skill_md("description: a", "b"))
    provider.add_skill_text("beta", _skill_md("description: b", "b"))

    mgr = CapabilityManager([provider])
    catalog = mgr.catalog(_ctx())
    assert {c.name for c in catalog} == {"alpha", "beta"}
    assert all(c.kind == "skill" for c in catalog)
    # S0 no aporta tools: el pool sigue siendo solo el nativo
    assert mgr.tools(_ctx()) == []
