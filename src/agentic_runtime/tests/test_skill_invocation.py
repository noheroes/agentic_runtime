"""Tests de invocación de skills (S1/S2/S3/S5).

Invocar `Skill` deja estado activo estructurado y habilita allowed-tools vía
context_modifier (aplicado por el loop). El catálogo sirve para selección, no para
reinvocación; las skills activas sobreviven a la compactación.
"""
from agentic_runtime.capabilities import CapabilityManager
from agentic_runtime.capabilities.skills import SkillsProvider, SkillTool
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.events import DoneEvent, ToolCallEvent
from agentic_runtime.loop.agent_loop import AgentLoop
from agentic_runtime.tools import ToolRegistry
from agentic_runtime.tools.deferred import discovered_tool_names
from agentic_runtime.tools.dispatcher import ToolDispatcher


def _skill_md(front: str, body: str) -> str:
    return f"---\n{front}\n---\n{body}"


def _provider_with_skill() -> SkillsProvider:
    provider = SkillsProvider()
    provider.add_skill_text(
        "diagrams",
        _skill_md("name: diagrams\ndescription: dibuja\nallowed-tools:\n  - drawio_create", "Usa drawio."),
    )
    return provider


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


# ---------------------------------------------------------------------------
# S1: invocación deja estado activo estructurado
# ---------------------------------------------------------------------------

async def test_skill_tool_unknown_returns_error():
    tool = SkillTool(_provider_with_skill().state)
    result = await tool.execute({"command": "ghost"}, _ctx())
    assert result.is_error
    assert "diagrams" in result.output  # lista las disponibles


async def test_skill_invocation_renders_instructions_and_sets_modifier():
    tool = SkillTool(_provider_with_skill().state)
    result = await tool.execute({"command": "diagrams"}, _ctx())
    assert not result.is_error
    assert "Usa drawio." in result.output
    assert "no reinvoques" in result.output.lower()
    assert getattr(result, "context_modifier", None) is not None


async def test_skill_modifier_records_active_state_and_permissions():
    tool = SkillTool(_provider_with_skill().state)
    ctx = _ctx()
    result = await tool.execute({"command": "diagrams"}, ctx)
    ctx = result.context_modifier(ctx)

    caps = ctx.app_state.capabilities
    assert caps["invoked_skills"] == ["diagrams"]
    assert caps["active_skills"]["diagrams"]["content"] == "Usa drawio."
    # allowed-tools de la skill habilitadas en permisos…
    assert "drawio_create" in ctx.permission_context.allowed_names()
    # …y marcadas como descubiertas (cruce S2↔M3)
    assert "drawio_create" in discovered_tool_names(ctx)


# ---------------------------------------------------------------------------
# S2: el loop aplica el context_modifier tras el dispatch
# ---------------------------------------------------------------------------

async def test_loop_applies_skill_modifier_enabling_tools():
    provider = _provider_with_skill()
    manager = CapabilityManager([provider])
    reg = ToolRegistry()

    class _Caller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            async def _gen():
                yield ToolCallEvent(tool_name="Skill", tool_input={"command": "diagrams"}, call_id="c1")
                yield DoneEvent(stop_reason="stop")
            return _gen()

    loop = AgentLoop(
        model_caller=_Caller(), tool_registry=reg, capability_manager=manager,
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _ctx()
    await loop.run("usa la skill", ctx)

    # tras el turno, la skill quedó activa y sus tools permitidas en el ctx real
    assert ctx.app_state.capabilities["invoked_skills"] == ["diagrams"]
    assert "drawio_create" in ctx.permission_context.allowed_names()


# ---------------------------------------------------------------------------
# S3: catálogo para selección + active_context para 'continuar'
# ---------------------------------------------------------------------------

def test_provider_exposes_skill_tool_only_when_skills_present():
    empty = SkillsProvider()
    assert empty.tools(_ctx()) == []
    assert [t.name for t in _provider_with_skill().tools(_ctx())] == ["Skill"]


def test_active_context_says_continue_not_reinvoke():
    provider = _provider_with_skill()
    ctx = _ctx()
    # simula skill activa
    ctx.app_state.capabilities["active_skills"] = {"diagrams": {"content": "Usa drawio."}}
    msgs = provider.active_context(ctx)
    assert len(msgs) == 1
    assert "continúa siguiendo" in msgs[0]["content"].lower()
    assert "Usa drawio." in msgs[0]["content"]


# ---------------------------------------------------------------------------
# S5: compactación preserva skills activas (contenido, no solo nombre)
# ---------------------------------------------------------------------------

def test_compact_context_preserves_active_skill_content():
    provider = _provider_with_skill()
    ctx = _ctx()
    ctx.app_state.capabilities["active_skills"] = {"diagrams": {"content": "Usa drawio."}}
    compact = provider.compact_context(ctx)
    assert compact and "Usa drawio." in compact[0]["content"]
    assert "reinvoc" not in compact[0]["content"].lower()
