"""Flujo de REGISTRO de skills + invocación, end-to-end por el runtime.

Dos formas de registro (responsabilidad del integrador dónde viven):
- `skill_dirs`: skills como DIRECTORIOS (<dir>/<skill>/SKILL.md + scripts) — el caso de
  docx/xlsx. Se cargan al construir el runtime.
- `SkillStore`: contenido SKILL.md sobre StorageProtocol — se carga en startup.

Verifica que el runtime los ENCUENTRA y que invocar `Skill` activa la skill y habilita
sus allowed-tools.
"""
from pathlib import Path

import pytest

from agentic_runtime.capabilities.skills import SkillsProvider
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.events import DoneEvent, TokenEvent, ToolCallEvent
from agentic_runtime.factory import CapabilitiesConfig, RuntimeConfig, StorageConfig, create_runtime

_REAL_SKILLS = Path("/tmp/skills")


def _write_skill_dir(root: Path, name: str, allowed: str, body: str) -> None:
    d = root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\ndescription: skill {name}\nallowed-tools: {allowed}\n---\n{body}",
        encoding="utf-8",
    )
    (d / "scripts").mkdir()
    (d / "scripts" / "run.sh").write_text("echo hi\n", encoding="utf-8")  # archivo bundled


class _CallerInvokesSkill:
    """turno1 invoca Skill(<name>); turno2 observa las tools ya habilitadas; fin."""

    def __init__(self, skill_name: str):
        self._name = skill_name
        self.turns: list[list[str]] = []
        self.last_messages: list = []

    async def complete(self, messages, tools, *, stop=None, model_id=""):
        self.turns.append([t["name"] for t in tools])
        self.last_messages = list(messages)
        n = len(self.turns)

        async def gen():
            if n == 1:
                yield ToolCallEvent(tool_name="Skill", tool_input={"command": self._name}, call_id="c1")
                yield DoneEvent(stop_reason="tool_calls")
            else:
                yield TokenEvent(content="ok")
                yield DoneEvent(stop_reason="stop")

        return gen()


# ---------------------------------------------------------------------------
# Registro por directorio (self-contained) + invocación por el runtime
# ---------------------------------------------------------------------------

async def test_skill_dir_registration_and_invocation_via_runtime(tmp_path):
    skills_root = tmp_path / "skills"
    _write_skill_dir(skills_root, "myskill", "bash", "Usa bash para la tarea.")

    caller = _CallerInvokesSkill("myskill")
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        capabilities=CapabilitiesConfig(skill_dirs=[skills_root]),
    ))
    await runtime.startup()

    task_id = await runtime.dispatch(RuntimeTask(prompt="usa la skill", description="reg"))
    rec = runtime._task_registry.get(task_id)
    await rec.asyncio_task
    await runtime.shutdown()

    # turno 1: la tool Skill estaba disponible para invocar
    assert "Skill" in caller.turns[0]
    # la invocación rindió las instrucciones de la skill (no reinvoca)
    contents = " ".join(str(m.get("content", "")) for m in caller.last_messages)
    assert "Usa bash para la tarea." in contents
    # turno 2: tras la skill, su allowed-tool (bash) quedó habilitada → se anuncia
    assert "bash" in caller.turns[1]


# ---------------------------------------------------------------------------
# Tus skills REALES (docx/xlsx) — gated en presencia de /tmp/skills
# ---------------------------------------------------------------------------

def _has_real_skills() -> bool:
    return (_REAL_SKILLS / "docx" / "SKILL.md").exists()


@pytest.mark.skipif(not _has_real_skills(), reason="no hay skills reales en /tmp/skills")
async def test_real_docx_xlsx_skills_register_and_invoke(tmp_path):
    # registro por directorio (lo correcto para skills con scripts bundled)
    caller = _CallerInvokesSkill("docx")
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        capabilities=CapabilitiesConfig(skill_dirs=[_REAL_SKILLS]),
    ))
    await runtime.startup()

    # ambas skills reales en el catálogo del manager
    catalog = {c.name for c in runtime._capability_manager.catalog(ToolUseContext(session_id="s"))}
    assert {"docx", "xlsx"} <= catalog

    task_id = await runtime.dispatch(RuntimeTask(prompt="crea un word", description="real"))
    rec = runtime._task_registry.get(task_id)
    await rec.asyncio_task
    await runtime.shutdown()

    # docx declara allowed-tools: bash → tras invocarla, bash habilitada
    assert "bash" in caller.turns[1]
    contents = " ".join(str(m.get("content", "")) for m in caller.last_messages)
    assert "docx" in contents.lower()


# ---------------------------------------------------------------------------
# Carga directa de tus skills reales (parseo tolerante del frontmatter rico)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _has_real_skills(), reason="no hay skills reales en /tmp/skills")
def test_real_skills_parse_tolerantly():
    provider = SkillsProvider()
    loaded = {s.name: s for s in provider.load_dir(_REAL_SKILLS)}
    assert {"docx", "xlsx"} <= set(loaded)
    # frontmatter rico (when_to_use/deps/version/license/context) no rompe; defaults por campo
    assert loaded["docx"].allowed_tools == ["bash"]   # 'allowed-tools: bash' (string) → lista
    assert loaded["docx"].model is None               # sin model → hereda
    assert loaded["docx"].description                 # descripción multilínea parseada
    assert loaded["docx"].name == "docx"              # nombre desde el directorio (sin 'name')
    # base_dir apunta al directorio de la skill (para localizar scripts/ bundled)
    assert loaded["docx"].base_dir.endswith("/docx")
    assert (Path(loaded["docx"].base_dir) / "scripts").is_dir()


# ---------------------------------------------------------------------------
# base_dir: el modelo recibe la ruta de la skill para acceder a sus subcarpetas
# ---------------------------------------------------------------------------

def test_skill_render_exposes_base_dir_for_bundled_files(tmp_path):
    from agentic_runtime.capabilities.skills import render_skill

    skills_root = tmp_path / "skills"
    _write_skill_dir(skills_root, "bundled", "bash", "Ejecuta scripts/run.sh.")
    provider = SkillsProvider()
    skill = provider.load_dir(skills_root)[0]

    rendered = render_skill(skill)
    # el render antepone el base dir (espejo del canónico) → el modelo localiza scripts/
    assert f"Base directory for this skill: {skill.base_dir}" in rendered
    assert skill.base_dir.endswith("/bundled")
    assert (Path(skill.base_dir) / "scripts" / "run.sh").exists()


def test_content_only_skill_has_no_base_dir():
    from agentic_runtime.capabilities.skills import render_skill

    provider = SkillsProvider()
    skill = provider.add_skill_text("inline", "---\ndescription: d\n---\nhaz algo")
    assert skill.base_dir == ""
    assert "Base directory" not in render_skill(skill)  # sin dir → sin prefijo
