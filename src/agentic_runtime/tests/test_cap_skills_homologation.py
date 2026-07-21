"""Homologación 12·capabilities/skills — loader/frontmatter/provider/skill_tool/commands/store/state
vs el subsistema de skills canónico (`skills/{loadSkillsDir,bundledSkills,mcpSkillBuilders}.ts`,
`tools/SkillTool/*`, el motor de `commands.ts`, `utils/skills/*`, `utils/hooks/{registerSkillHooks,skillImprovement}.ts`,
`utils/suggestions/skillUsageTracking.ts`, los seams de entrega en `utils/attachments.ts`/`bootstrap/state.ts`/`utils/messages.ts`,
y el naming prompt-vs-skill de `services/mcp/utils.ts`).

Los tests que PASAN codifican lo YA homologado (loader tolerante, identidad desde el directorio, description
derivada, model=inherit→None, allowed-tools CSV/lista, aislamiento por-ítem, tool `Skill` con context_modifier
que activa allowed-tools + active_skills, active/compact_context "continúa siguiendo", slash-command desacoplado,
store inyectable + unregister-en-vivo, SkillTool no-diferida, base_dir en el render).

Los `xfail(strict=True)` codifican los gaps FIND-SKILL/FIND-MCP16: fallan HOY (comportamiento ausente) y su
fallo ES la evidencia del gap. Si alguno empezara a pasar, el strict lo vuelve error → señal de reclasificar el
estado en `12-cap-skills.md`. Los imports de símbolos-target aún inexistentes viven DENTRO de cada test para no
romper la colección.
"""
from __future__ import annotations

import asyncio

import pytest

from agentic_runtime.capabilities.skills import (
    SkillDefinition,
    SkillFrontmatter,
    SkillsProvider,
    SkillsState,
    SkillTool,
    build_skill_context_modifier,
    load_skill_text,
    load_skills_dir,
    parse_frontmatter,
    parse_slash_command,
    process_slash_command,
    render_skill,
)
from agentic_runtime.capabilities.skills.store import StorageBackedSkillStore
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools.deferred import is_deferred_tool


def _ctx(**kw) -> ToolUseContext:
    return ToolUseContext(session_id="s1", stop=asyncio.Event(), **kw)


_SKILL_MD = """---
name: greet
description: Saluda al usuario
allowed-tools: Bash, Read
model: inherit
---
# Greet

Di hola de forma amable.
"""


# ===========================================================================
# Homologado (PASA)
# ===========================================================================

def test_frontmatter_tolerant_and_identity_from_dir():
    """Frontmatter corrupto → defaults; la identidad la garantiza el nombre del dir."""
    front, body = parse_frontmatter("---\nname: [oops]\n---\ncuerpo")
    assert front.name is None  # valor no-string degrada a None, no a error
    skill = load_skill_text("dirname", "---\n: : :\n---\nHola mundo")
    assert skill.name == "dirname"  # identidad ← dir aunque el frontmatter falle


def test_description_derived_from_body():
    skill = load_skill_text("x", "Primer parrafo real.\n\nSegundo parrafo.")
    assert skill.description == "Primer parrafo real."


def test_model_inherit_to_none_and_explicit():
    assert load_skill_text("a", "---\nmodel: inherit\n---\nb").model is None
    assert load_skill_text("a", "---\n---\nb").model is None
    assert load_skill_text("a", "---\nmodel: opus\n---\nb").model == "opus"


def test_allowed_tools_csv_and_list():
    csv = load_skill_text("a", "---\nallowed-tools: Bash, Read , Grep\n---\nb")
    assert csv.allowed_tools == ["Bash", "Read", "Grep"]
    lst = parse_frontmatter("---\nallowed-tools:\n  - Bash\n  - Edit\n---\nx")[0]
    assert lst.allowed_tools == ["Bash", "Edit"]


def test_load_skills_dir_isolation_and_order(tmp_path):
    (tmp_path / "b" ).mkdir()
    (tmp_path / "a").mkdir()
    (tmp_path / "b" / "SKILL.md").write_text("---\ndescription: B\n---\nbody b")
    (tmp_path / "a" / "SKILL.md").write_text("---\ndescription: A\n---\nbody a")
    # una skill rota no tumba el resto
    (tmp_path / "c").mkdir()
    (tmp_path / "c" / "SKILL.md").write_bytes(b"\xff\xfe not utf8 ok\n---\n")
    skills = load_skills_dir(tmp_path)
    names = [s.name for s in skills]
    assert "a" in names and "b" in names
    assert names == sorted(names)  # orden estable por ruta


def test_skill_tool_activates_allowed_tools_and_active_skills():
    state = SkillsState()
    state.set_skill(load_skill_text("greet", _SKILL_MD))
    tool = SkillTool(state)
    ctx = _ctx()
    result = asyncio.run(tool.execute({"command": "greet"}, ctx))
    assert not result.is_error
    # el context_modifier muta el ctx: allowed-tools + estado activo estructurado
    result.context_modifier(ctx)  # type: ignore[attr-defined]
    caps = ctx.app_state.capabilities
    assert "greet" in caps["active_skills"]
    assert caps["active_skills"]["greet"]["allowed_tools"] == ["Bash", "Read"]
    assert "Bash" in ctx.app_state.permissions.always_allow_command


def test_active_and_compact_context_continue_to_follow():
    prov = SkillsProvider()
    prov.add_skill_text("greet", _SKILL_MD)
    ctx = _ctx()
    build_skill_context_modifier(prov.state.get("greet"))(ctx)
    active = prov.active_context(ctx)
    assert active and "greet" in active[0]["content"]
    # la compactación preserva el contenido, no sólo el nombre
    assert prov.compact_context(ctx) == active


def test_slash_command_desacoplado():
    state = SkillsState()
    state.set_skill(load_skill_text("greet", _SKILL_MD))
    ctx = _ctx()
    assert parse_slash_command("/greet hola").name == "greet"
    out = process_slash_command("/greet hola", state, ctx)
    assert out is not None and "greet" in out
    assert "greet" in ctx.app_state.capabilities["active_skills"]
    assert process_slash_command("no es slash", state, ctx) is None


def test_skill_tool_not_deferred():
    """La tool `Skill` NO es diferida (el modelo la necesita para activar skills)."""
    assert is_deferred_tool(SkillTool(SkillsState())) is False


def test_base_dir_prefix_in_render():
    skill = load_skill_text("greet", _SKILL_MD, source_path="/x/greet/SKILL.md")
    skill = SkillDefinition(**{**skill.model_dump(), "base_dir": "/x/greet"})
    rendered = render_skill(skill)
    assert "Base directory for this skill: /x/greet" in rendered


def test_store_backed_roundtrip_and_unregister():
    class _FakeStorage:
        def __init__(self):
            self.blobs: dict[str, bytes] = {}

        async def list_prefix(self, prefix):
            return [k for k in self.blobs if k.startswith(prefix)]

        async def exists(self, key):
            return key in self.blobs

        async def download(self, key):
            return self.blobs[key]

        async def upload(self, key, data, ctype):
            self.blobs[key] = data

        async def delete(self, key):
            self.blobs.pop(key, None)

    async def _run():
        store = StorageBackedSkillStore(_FakeStorage())
        prov = SkillsProvider(skill_store=store)
        await prov.register_skill("greet", _SKILL_MD)
        assert await store.list() == ["greet"]
        # rehidratación desde el store
        prov2 = SkillsProvider(skill_store=store)
        await prov2.startup()
        assert prov2.state.get("greet") is not None
        # unregister borra store + estado vivo
        assert await prov.unregister("greet") is True
        assert await store.list() == []

    asyncio.run(_run())


# ===========================================================================
# Gaps FIND-SKILL — xfail(strict): fallan HOY, su fallo ES la evidencia
# ===========================================================================

@pytest.mark.xfail(strict=True, reason="FIND-SKILL2: when_to_use separado de description")
def test_when_to_use_separate_from_description():
    skill = load_skill_text("a", "---\ndescription: D\nwhen_to_use: usar cuando X\n---\nbody")
    assert skill.when_to_use == "usar cuando X"
    assert skill.description == "D"


@pytest.mark.xfail(strict=True, reason="FIND-SKILL2: argument-hint + arguments")
def test_argument_hint_and_names():
    skill = load_skill_text("a", "---\nargument-hint: '<pr>'\narguments: [pr, extra]\n---\nb")
    assert skill.argument_hint == "<pr>"
    assert skill.argument_names == ["pr", "extra"]


@pytest.mark.xfail(strict=True, reason="FIND-SKILL3: user-invocable y disable-model-invocation ortogonales")
def test_two_enablement_axes_orthogonal():
    skill = load_skill_text(
        "a", "---\nuser-invocable: false\ndisable-model-invocation: true\n---\nb"
    )
    assert skill.user_invocable is False
    assert skill.disable_model_invocation is True
    assert skill.is_hidden is True


@pytest.mark.xfail(strict=True, reason="FIND-SKILL4: substitución de $ARGUMENTS/$1/${CLAUDE_SKILL_DIR}")
def test_render_substitutes_arguments_and_vars():
    skill = load_skill_text("a", "---\narguments: [name]\n---\nHola $name / $ARGUMENTS")
    rendered = render_skill(skill, "Ruben")  # render_skill(skill) es la firma actual (1 arg)
    assert "Hola Ruben" in rendered and "$ARGUMENTS" not in rendered


@pytest.mark.xfail(strict=True, reason="FIND-SKILL5 (=GAP-SKILL1/Deuda-B): gate de permisos ausente")
def test_skill_tool_requires_permission_and_gate():
    state = SkillsState()
    state.set_skill(load_skill_text("greet", _SKILL_MD))
    tool = SkillTool(state)
    assert tool.requires_permission is True
    decision = asyncio.run(tool.check_permission({"command": "greet"}, _ctx()))
    assert decision.behavior in ("ask", "allow", "deny")


@pytest.mark.xfail(strict=True, reason="FIND-SKILL6: fork dispatch en la propia tool (context: fork)")
def test_skill_context_fork_dispatches():
    skill = load_skill_text("worker", "---\ncontext: fork\nagent: general\n---\ntrabaja")
    assert skill.execution_context == "fork"


@pytest.mark.xfail(strict=True, reason="FIND-SKILL7: context_modifier no aplica model/effort override")
def test_context_modifier_applies_model_and_effort():
    skill = load_skill_text("a", "---\nmodel: opus\neffort: high\n---\nb")
    ctx = _ctx()
    build_skill_context_modifier(skill)(ctx)
    assert ctx.app_state.effort_value == "high"


@pytest.mark.xfail(strict=True, reason="FIND-SKILL9/17: skill_listing incremental por-agente + budget")
def test_skill_listing_incremental_per_agent():
    prov = SkillsProvider()
    prov.add_skill_text("greet", _SKILL_MD)
    ctx = _ctx(agent_id="A")
    first = prov.skill_listing(ctx)
    assert first  # initial batch
    second = prov.skill_listing(ctx)
    assert second == []  # ya enviada → sólo deltas


@pytest.mark.xfail(strict=True, reason="FIND-SKILL10: cleanup selectivo por agent + skillPath")
def test_clear_invoked_skills_for_agent():
    prov = SkillsProvider()
    prov.add_skill_text("greet", _SKILL_MD)
    prov.clear_invoked_skills_for_agent("A")  # método aún inexistente


@pytest.mark.xfail(strict=True, reason="FIND-SKILL11: skill hooks del frontmatter")
def test_skill_hooks_parsed():
    skill = load_skill_text(
        "a", "---\nhooks:\n  PreToolUse:\n    - matcher: Bash\n      hooks: []\n---\nb"
    )
    assert skill.hooks is not None and "PreToolUse" in skill.hooks


@pytest.mark.xfail(strict=True, reason="FIND-SKILL12 (=GAP-SKILL3): skills condicionales por paths")
def test_conditional_skills_by_paths():
    from agentic_runtime.capabilities.skills import activate_conditional_skills_for_paths  # noqa: F401

    skill = load_skill_text("a", "---\npaths: 'src/**'\n---\nb")
    assert skill.paths == ["src"]


@pytest.mark.xfail(strict=True, reason="FIND-SKILL13: refresco de catálogo que resetea sent_skill_names")
def test_provider_refresh():
    prov = SkillsProvider()
    prov.refresh()  # método aún inexistente


@pytest.mark.xfail(strict=True, reason="FIND-SKILL14: ranking de uso")
def test_record_and_score_usage():
    from agentic_runtime.capabilities.skills.usage import (  # noqa: F401
        record_skill_usage,
        skill_usage_score,
    )


@pytest.mark.xfail(strict=True, reason="FIND-SKILL15: bundled skills programáticos")
def test_register_bundled_skill():
    from agentic_runtime.capabilities.skills.bundled import register_bundled_skill  # noqa: F401


@pytest.mark.xfail(strict=True, reason="FIND-SKILL16: resolución por alias / namespaced / strip-slash")
def test_find_skill_by_alias():
    state = SkillsState()
    skill = load_skill_text("greet", _SKILL_MD)
    skill = SkillDefinition(**{**skill.model_dump(), "aliases": ["hi"]})
    state.set_skill(skill)
    assert state.get("hi") is not None  # hoy sólo resuelve nombre exacto


@pytest.mark.xfail(strict=True, reason="FIND-SKILL17: catalog excluye disable-model-invocation")
def test_catalog_excludes_disable_model_invocation():
    prov = SkillsProvider()
    prov.add_skill_text("hidden", "---\ndisable-model-invocation: true\n---\nb")
    names = [c.name for c in prov.catalog(_ctx())]
    assert "hidden" not in names


@pytest.mark.xfail(strict=True, reason="FIND-SKILL18: prompt de la tool con BLOCKING REQUIREMENT")
def test_skill_tool_prompt_blocking_requirement():
    assert "BLOCKING REQUIREMENT" in SkillTool(SkillsState()).description


@pytest.mark.xfail(strict=True, reason="FIND-SKILL19: getPromptForCommand como callable async ctx-aware")
def test_skill_prompt_provider_callable():
    """El prompt lo produce un callable async con acceso al ctx, no un markdown estático."""
    async def _provider(args: str, ctx) -> str:
        return f"computed:{args}:{ctx.session_id}"

    skill = SkillDefinition(name="dyn", instructions="ignored")
    object.__setattr__(skill, "prompt_provider", _provider)  # campo aún inexistente
    out = asyncio.run(render_skill(skill, "X", _ctx()))  # render_skill hoy es sync y 1-arg
    assert out == "computed:X:s1"


@pytest.mark.xfail(strict=True, reason="FIND-MCP16: MCP skills invocables + prompts diferidos")
def test_mcp_skill_loaded_from_and_merge():
    skill = load_skill_text("srv:doc", "---\ndescription: D\n---\nb")
    assert getattr(skill, "loaded_from", "skills") == "skills"  # falta el campo loaded_from
    prov = SkillsProvider()
    prov.merge_mcp_skills([])  # método aún inexistente
