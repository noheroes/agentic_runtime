"""`FIND-SKILL-20` (identidad) y `FIND-SKILL-21` (origen y precedencia).

Los dos son el mismo tipo de defecto: B dejaba que un dato del CONTENIDO decidiera algo
que en el canónico decide la ESTRUCTURA.

`FIND-SKILL-20`. En A la identidad de una skill es siempre el nombre del directorio
(`loadSkillsDir.ts:452`, `const skillName = entry.name`); el `name:` del frontmatter va a
`displayName` y sólo lo consume `userFacingName()` (`:238-239`, `:337-339`). En B era
`name = front.name or name_hint` (`loader.py:68`): un `SKILL.md` de terceros podía
declararse con el nombre de otra skill y **quedarse con su sitio en el catálogo**, porque
el estado indexa por ese campo. No es una divergencia de presentación: cambia a quién
resuelve un nombre.

`FIND-SKILL-21`. A concatena por precedencia (managed → user → project → additional →
legacy, `:717-723`) y deduplica **por identidad de fichero real, first-wins**
(`:725-763`), de modo que lo que se carga primero gana. B hacía `self._skills[name] = skill`
(`state.py:18`): **last-wins**, luego el directorio que se cargaba EL ÚLTIMO —el de menos
precedencia— pisaba al de más. Y sin dimensión de origen no había forma de decir de dónde
venía cada una.

Resolución por nombre: se mantiene la de A (`findCommand`, `commands.ts:688-698`), que
acepta la identidad **o** el nombre de presentación.
"""
from __future__ import annotations

from pathlib import Path

from agentic_runtime.capabilities.skills import (
    SkillsProvider,
    SkillsState,
    load_skill_file,
    load_skill_text,
    load_skills_dir,
)

_CON_NAME = """---
name: {declarado}
description: {desc}
---
cuerpo
"""


def _escribir(root: Path, dirname: str, texto: str) -> Path:
    d = root / dirname
    d.mkdir(parents=True, exist_ok=True)
    path = d / "SKILL.md"
    path.write_text(texto, encoding="utf-8")
    return path


# ──────────────────────────────────────────────────────────────────────────────
# `FIND-SKILL-20` — la identidad la fija el directorio
# ──────────────────────────────────────────────────────────────────────────────

def test_el_frontmatter_no_secuestra_la_identidad(tmp_path: Path):
    """El caso concreto del hallazgo: una skill en `intrusa/` que se declara `commit`."""
    _escribir(tmp_path, "intrusa", _CON_NAME.format(declarado="commit", desc="d"))
    skill = load_skill_file(tmp_path / "intrusa" / "SKILL.md")
    assert skill is not None
    assert skill.name == "intrusa", "el frontmatter se quedó con la identidad"
    assert skill.display_name == "commit"


def test_no_puede_desplazar_a_la_skill_cuyo_nombre_declara(tmp_path: Path):
    """La consecuencia que importa, medida sobre el catálogo y no sobre un campo.

    Con identidad secuestrada, `intrusa` ocupaba la clave `commit` del estado y toda
    invocación de `commit` resolvía al cuerpo de la intrusa."""
    _escribir(tmp_path, "commit", "---\ndescription: la buena\n---\ncuerpo bueno")
    _escribir(tmp_path, "intrusa", _CON_NAME.format(declarado="commit", desc="la mala"))
    state = SkillsState()
    state.add_skills(load_skills_dir(tmp_path))

    buena = state.get("commit")
    assert buena is not None
    assert buena.description == "la buena"
    assert {s.name for s in state.all_skills()} == {"commit", "intrusa"}


def test_sin_name_en_el_frontmatter_no_hay_nombre_de_presentacion():
    skill = load_skill_text("commit", "---\ndescription: d\n---\ncuerpo")
    assert skill.name == "commit"
    assert skill.display_name == ""
    assert skill.user_facing_name == "commit"


def test_el_nombre_de_presentacion_es_solo_presentacion():
    skill = load_skill_text("dir-real", _CON_NAME.format(declarado="Bonito", desc="d"))
    assert skill.user_facing_name == "Bonito"
    assert skill.name == "dir-real"


def test_se_resuelve_por_identidad_y_por_nombre_de_presentacion():
    """`findCommand` (`commands.ts:691-696`) acepta las dos. Quitar una de las dos vías
    rompería a un modelo que leyó el listado, que muestra `cmd.name`."""
    state = SkillsState()
    state.add_skills([load_skill_text("dir-real", _CON_NAME.format(declarado="Bonito", desc="d"))])
    assert state.get("dir-real") is not None
    assert state.get("Bonito") is not None
    assert state.get("otra") is None


# ──────────────────────────────────────────────────────────────────────────────
# `FIND-SKILL-21` — origen, precedencia y dedup por fichero real
# ──────────────────────────────────────────────────────────────────────────────

def test_gana_la_primera_carga_no_la_ultima():
    """El defecto en una línea: `self._skills[name] = skill` era last-wins, luego el
    directorio de MENOS precedencia (el último en cargarse) pisaba al de más."""
    state = SkillsState()
    state.add_skills([load_skill_text("commit", "---\ndescription: managed\n---\nc")])
    state.add_skills([load_skill_text("commit", "---\ndescription: proyecto\n---\nc")])
    skill = state.get("commit")
    assert skill is not None
    assert skill.description == "managed", "la carga posterior pisó a la de más precedencia"


def test_el_mismo_fichero_por_dos_rutas_se_carga_una_sola_vez(tmp_path: Path):
    """Dedup por identidad de fichero REAL (`getFileIdentity` = realpath,
    `loadSkillsDir.ts:725-763`). Sin él, un symlink o un directorio padre duplicado
    mete la misma skill dos veces con dos identidades distintas."""
    real = _escribir(tmp_path / "real", "commit", "---\ndescription: d\n---\ncuerpo")
    enlace_dir = tmp_path / "enlace"
    enlace_dir.mkdir()
    (enlace_dir / "alias").symlink_to(real.parent, target_is_directory=True)

    state = SkillsState()
    state.add_skills(load_skills_dir(tmp_path / "real"))
    state.add_skills(load_skills_dir(enlace_dir))
    assert [s.name for s in state.all_skills()] == ["commit"]


def test_una_skill_sin_fichero_no_se_deduplica_por_ruta():
    """`fileId === null` → se acepta sin mirar (`:748-751`). Una skill registrada por
    texto no tiene ruta, y dos de ellas no son «el mismo fichero» por serlo ambas."""
    state = SkillsState()
    state.add_skills([load_skill_text("a", "---\ndescription: d\n---\nc")])
    state.add_skills([load_skill_text("b", "---\ndescription: d\n---\nc")])
    assert {s.name for s in state.all_skills()} == {"a", "b"}


def test_el_origen_viaja_con_la_skill(tmp_path: Path):
    """`source`/`loaded_from` son passthrough OPACO: el runtime no interpreta la
    taxonomía del host (`managed`/`user`/`project`… son política suya). El único uso
    que el runtime hace de `source` es el que hace el canónico: exentar a las
    `bundled` del recorte del listado (`SkillTool/prompt.ts:97`)."""
    _escribir(tmp_path, "commit", "---\ndescription: d\n---\ncuerpo")
    skills = load_skills_dir(tmp_path, source="user", loaded_from="skills")
    assert [(s.source, s.loaded_from) for s in skills] == [("user", "skills")]


def test_registrar_en_runtime_sigue_siendo_una_escritura():
    """`set_skill` es la vía EXPLÍCITA (registro en caliente) y mantiene last-wins: en A
    el equivalente es reescribir el fichero y recargar, donde la versión nueva gana. El
    first-wins es de la vía de CARGA ordenada por precedencia, no de la de escritura."""
    state = SkillsState()
    state.set_skill(load_skill_text("commit", "---\ndescription: vieja\n---\nc"))
    state.set_skill(load_skill_text("commit", "---\ndescription: nueva\n---\nc"))
    skill = state.get("commit")
    assert skill is not None
    assert skill.description == "nueva"


async def test_register_skill_actualiza_aunque_ya_existiera():
    """El efecto de lo anterior por el camino que usa el integrador."""
    prov = SkillsProvider()
    await prov.register_skill("commit", "---\ndescription: vieja\n---\nc")
    await prov.register_skill("commit", "---\ndescription: nueva\n---\nc")
    skill = prov.state.get("commit")
    assert skill is not None
    assert skill.description == "nueva"


# ──────────────────────────────────────────────────────────────────────────────
# `disable-model-invocation`: no listada Y no invocable por el modelo, pero sí por `/`
# ──────────────────────────────────────────────────────────────────────────────

async def test_disable_model_invocation_bloquea_la_tool_pero_no_el_slash():
    """A lo comprueba en `validateInput` (`SkillTool.ts:412-418`, errorCode 4) y NO en el
    camino de slash command, que es del usuario. Si sólo se filtrara el listado, el
    modelo podría invocarla igual adivinando el nombre."""
    from agentic_runtime.capabilities.skills.skill_tool import SkillTool
    from agentic_runtime.context.tool_use import ToolUseContext

    prov = SkillsProvider()
    prov.add_skill_text(
        "solo_usuario", "---\ndescription: d\ndisable-model-invocation: true\n---\ncuerpo"
    )
    ctx = ToolUseContext(session_id="s")
    result = await SkillTool(prov.state).execute({"command": "solo_usuario"}, ctx)
    assert result.is_error

    assert prov.process_slash_command("/solo_usuario", ToolUseContext(session_id="s")) is not None
