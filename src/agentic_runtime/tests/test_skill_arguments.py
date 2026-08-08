"""`LAT-SKILL1` — los `args` que B anunciaba y tiraba.

`SkillTool.input_schema` declara `args` («Optional arguments for the skill») y la
descripción de la tool, homologada contra `SkillTool/prompt.ts:181-183`, llega a poner un
EJEMPLO con args. `execute()` los leía… nunca: hacía `render_skill(skill)` y el valor se
perdía en silencio. Lo mismo por la segunda vía: `parse_slash_command` separa
`SlashCommand(name, args)` y `process_slash_command` sólo usaba `name`.

No es cosmética. Es una PROMESA FALSA en el contrato que ve el modelo: una skill escrita
para el canónico («revisa el PR $ARGUMENTS») se invoca con args, el placeholder queda
literal en las instrucciones y la skill opera sobre un dato que nadie sustituyó. El modelo
no tiene forma de enterarse — no hay error, hay un `$ARGUMENTS` en el texto.

Dictado: `substituteArguments` (`utils/argumentSubstitution.ts:94-145`), invocado desde
`getPromptForCommand` (`loadSkillsDir.ts:344-354`) sobre el contenido que YA lleva el
prefijo del `baseDir`, con `appendIfNoPlaceholder=true` y los `argumentNames` del
frontmatter (`:249-251`, parseados por `parseArgumentNames`, `:50-68`).
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from agentic_runtime.capabilities.skills import SkillsProvider, SkillTool
from agentic_runtime.capabilities.skills.arguments import (
    parse_argument_names,
    parse_arguments,
    substitute_arguments,
)
from agentic_runtime.capabilities.skills.loader import load_skill_text
from agentic_runtime.capabilities.skills.skill_tool import render_skill
from agentic_runtime.capabilities.skills.state import SkillsState
from agentic_runtime.context.tool_use import ToolUseContext


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


def _skill(body: str, front: str = "description: d") -> str:
    return f"---\n{front}\n---\n{body}"


# ──────────────────────────────────────────────────────────────────────────────
# `parse_arguments` — espejo de `parseArguments` (`:24-40`)
# ──────────────────────────────────────────────────────────────────────────────

def test_parse_arguments_respeta_las_comillas():
    """El troceo es de SHELL, no un `split()`: 'hello world' es UN argumento."""
    assert parse_arguments('foo "hello world" baz') == ["foo", "hello world", "baz"]
    assert parse_arguments("foo 'hello world' baz") == ["foo", "hello world", "baz"]


def test_parse_arguments_vacio_y_malformado():
    assert parse_arguments("") == []
    assert parse_arguments("   ") == []
    # Comilla sin cerrar: A cae al split por espacios en vez de lanzar (`:31-34`).
    assert parse_arguments('foo "sin cerrar') == ["foo", '"sin', "cerrar"]


def test_parse_arguments_no_expande_variables():
    """`$HOME` se preserva LITERAL (`:29-30`): el listado no es un shell."""
    assert parse_arguments("$HOME otro") == ["$HOME", "otro"]


def test_parse_argument_names_filtra_vacios_y_numericos():
    """Un nombre numérico colisionaría con el atajo `$0`/`$1` (`:57-59`)."""
    assert parse_argument_names("foo bar") == ["foo", "bar"]
    assert parse_argument_names(["foo", "", "1", "bar"]) == ["foo", "bar"]
    assert parse_argument_names(None) == []


# ──────────────────────────────────────────────────────────────────────────────
# `substitute_arguments` — espejo de `substituteArguments` (`:94-145`)
# ──────────────────────────────────────────────────────────────────────────────

def test_sin_args_el_contenido_no_se_toca():
    """`args is None` ≠ `args == ""` (`:100-104`): ausente deja el texto intacto."""
    assert substitute_arguments("revisa $ARGUMENTS", None) == "revisa $ARGUMENTS"


def test_cadena_vacia_sustituye_por_vacio_y_no_apendiza():
    """Invocada sin args es una entrada VÁLIDA: el placeholder se vacía y no se apendiza."""
    assert substitute_arguments("revisa $ARGUMENTS", "") == "revisa "


def test_arguments_completo():
    assert substitute_arguments("revisa $ARGUMENTS.", "PR 42") == "revisa PR 42."


def test_indexado_y_atajo():
    assert substitute_arguments("$ARGUMENTS[1]/$ARGUMENTS[0]", "a b") == "b/a"
    assert substitute_arguments("$1-$0", "a b") == "b-a"


def test_indice_fuera_de_rango_queda_vacio():
    """`parsedArgs[index] ?? ''` (`:126`, `:132`): hueco, no `undefined` literal."""
    assert substitute_arguments("[$ARGUMENTS[3]]", "a") == "[]"
    assert substitute_arguments("[$3]", "a") == "[]"


def test_nombrados_mapean_por_POSICION():
    """Los nombres son alias posicionales (`:109-121`), no un diccionario."""
    out = substitute_arguments(
        "de $origen a $destino", "main dev", argument_names=["origen", "destino"]
    )
    assert out == "de main a dev"


def test_nombrado_no_come_prefijos_de_otra_palabra():
    """La guarda `(?![\\[\\w])` (`:118`): `$org` no debe morder `$organizacion`."""
    out = substitute_arguments("$org $organizacion", "X", argument_names=["org"])
    assert out == "X $organizacion"


def test_nombre_sin_valor_queda_vacio():
    out = substitute_arguments("[$b]", "solo", argument_names=["a", "b"])
    assert out == "[]"


def test_sin_placeholder_se_apendiza():
    """Rama `appendIfNoPlaceholder` (`:138-142`): los args no se pierden nunca."""
    assert substitute_arguments("haz algo", "PR 42") == "haz algo\n\nARGUMENTS: PR 42"


def test_sin_placeholder_y_sin_args_no_apendiza():
    """`&& args` (`:140`): una cadena vacía no genera un `ARGUMENTS:` hueco."""
    assert substitute_arguments("haz algo", "") == "haz algo"


def test_el_nombre_de_argumento_es_regex_inerte():
    """Un `arguments: [.*]` de terceros no puede compilar como patrón y comerse el texto."""
    out = substitute_arguments("a.b $.* c", "V", argument_names=[".*"])
    assert out == "a.b V c"


# ──────────────────────────────────────────────────────────────────────────────
# Cableado: la tool `Skill`
# ──────────────────────────────────────────────────────────────────────────────

async def test_la_tool_sustituye_los_args_que_anuncia():
    """El defecto, en su forma directa: `args` llegaba y no hacía nada."""
    provider = SkillsProvider()
    provider.add_skill_text("review", _skill("Revisa el PR $ARGUMENTS y opina."))
    tool = SkillTool(provider.state)

    result = await tool.execute({"command": "review", "args": "42"}, _ctx())

    assert not result.is_error
    assert "Revisa el PR 42 y opina." in result.output
    assert "$ARGUMENTS" not in result.output


async def test_la_tool_sin_args_deja_el_placeholder_intacto():
    """Sin `args` no hay sustitución: `undefined` → contenido tal cual (`:102-104`)."""
    provider = SkillsProvider()
    provider.add_skill_text("review", _skill("Revisa el PR $ARGUMENTS."))
    tool = SkillTool(provider.state)

    result = await tool.execute({"command": "review"}, _ctx())

    assert "Revisa el PR $ARGUMENTS." in result.output


async def test_la_tool_apendiza_cuando_la_skill_no_tiene_placeholder():
    provider = SkillsProvider()
    provider.add_skill_text("review", _skill("Revisa lo que toque."))
    tool = SkillTool(provider.state)

    result = await tool.execute({"command": "review", "args": "el PR 42"}, _ctx())

    assert "ARGUMENTS: el PR 42" in result.output


async def test_la_tool_usa_los_nombres_del_frontmatter():
    provider = SkillsProvider()
    provider.add_skill_text(
        "deploy",
        _skill("despliega $entorno", front="description: d\narguments: entorno version"),
    )
    tool = SkillTool(provider.state)

    result = await tool.execute({"command": "deploy", "args": "prod 1.2"}, _ctx())

    assert "despliega prod" in result.output


async def test_la_sustitucion_no_alcanza_al_framing_del_runtime(tmp_path: Path):
    """A sustituye sobre el contenido de la SKILL (con su `baseDir`), no sobre el marco.

    En B el marco es la cabecera «Skill 'x' activada» y la coleta de «continúa». Si la
    sustitución se aplicara al texto entero, un `$0` que apareciera ahí —o peor, la rama
    de apéndice midiendo contra el marco— cambiaría instrucciones del runtime con datos
    del modelo. El `baseDir` SÍ entra, porque en A entra (`:345-354`).
    """
    d = tmp_path / "docs"
    d.mkdir()
    (d / "SKILL.md").write_text(_skill("Lee $ARGUMENTS[0] del $ARGUMENTS[1]."), encoding="utf-8")
    provider = SkillsProvider()
    provider.load_dir(tmp_path)
    tool = SkillTool(provider.state)

    result = await tool.execute({"command": "docs", "args": "a.md repo"}, _ctx())

    assert "Lee a.md del repo." in result.output
    assert "Skill 'docs' activada." in result.output
    assert f"Base directory for this skill: {d}" in result.output
    assert "no reinvoques la skill" in result.output

    # ⚠ Hasta aquí el test **acreditaba en falso** (`INY-135b` salió VERDE sustituyendo
    # sobre el texto ENTERO): el marco no contiene ningún placeholder, así que sustituir
    # de más es idempotente y no se nota. Donde SÍ se nota es en la rama de apéndice, que
    # mide «¿cambió algo?» — aplicada al todo, apendiza una segunda vez y lo hace DETRÁS
    # de la coleta, o sea fuera de las instrucciones de la skill.
    (d / "SKILL.md").write_text(_skill("Sin placeholders."), encoding="utf-8")
    provider2 = SkillsProvider()
    provider2.load_dir(tmp_path)
    salida = await SkillTool(provider2.state).execute({"command": "docs", "args": "x"}, _ctx())

    assert salida.output.count("ARGUMENTS: x") == 1, "el apéndice se aplicó dos veces"
    assert salida.output.index("ARGUMENTS: x") < salida.output.index("no reinvoques"), (
        "el apéndice cayó DETRÁS del marco: se midió contra el texto entero, no contra la skill"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Cableado: el slash command (`/skill args`)
# ──────────────────────────────────────────────────────────────────────────────

def test_el_slash_command_sustituye_sus_args():
    """`parse_slash_command` ya separaba los args; `process_slash_command` los tiraba."""
    provider = SkillsProvider()
    provider.add_skill_text("review", _skill("Revisa el PR $ARGUMENTS."))

    out = provider.process_slash_command("/review 42", _ctx())

    assert out is not None
    assert "Revisa el PR 42." in out


def test_el_slash_command_sin_args_no_apendiza_nada():
    """`/review` a secas es «invocada sin args»: cadena vacía, no `None`."""
    provider = SkillsProvider()
    provider.add_skill_text("review", _skill("Revisa lo que toque."))

    out = provider.process_slash_command("/review", _ctx())

    assert out is not None
    assert "ARGUMENTS:" not in out


# ──────────────────────────────────────────────────────────────────────────────
# El dato en la definición
# ──────────────────────────────────────────────────────────────────────────────

def test_los_nombres_de_argumento_viajan_en_la_definicion():
    skill = load_skill_text("d", _skill("x", front="description: d\narguments:\n  - uno\n  - dos"))
    assert skill.argument_names == ["uno", "dos"]


def test_frontmatter_sin_arguments_no_declara_nombres():
    assert load_skill_text("d", _skill("x")).argument_names == []


# ──────────────────────────────────────────────────────────────────────────────
# `${CLAUDE_SKILL_DIR}` y `${CLAUDE_SESSION_ID}` — `FIND-SKILL4`, segunda mitad
#
# El `xfail` de `FIND-SKILL4` rotulaba «$ARGUMENTS/$1/${CLAUDE_SKILL_DIR}» pero su
# aserción sólo miraba los args: retirarlo por XPASS habría acreditado en falso unas
# variables que B no sustituye en ningún sitio (`H-L4`). Dictado en
# `loadSkillsDir.ts:356-369`: se sustituyen DESPUÉS de los args, `SKILL_DIR` sólo si la
# skill tiene directorio, `SESSION_ID` siempre.
# ──────────────────────────────────────────────────────────────────────────────

def test_skill_dir_se_sustituye_por_el_directorio_de_la_skill(tmp_path: Path):
    d = tmp_path / "pdf"
    d.mkdir()
    (d / "SKILL.md").write_text(_skill("Ejecuta ${CLAUDE_SKILL_DIR}/scripts/run.sh"))
    provider = SkillsProvider()
    provider.load_dir(tmp_path)
    skill = provider.state.get("pdf")
    assert skill is not None

    out = render_skill(skill, "")

    assert f"Ejecuta {d}/scripts/run.sh" in out
    assert "${CLAUDE_SKILL_DIR}" not in out


def test_sin_base_dir_el_placeholder_de_skill_dir_se_queda(tmp_path: Path):
    """A sólo sustituye `if (baseDir)` (`:359`): sin directorio no hay valor que poner,
    y poner cadena vacía fabricaría rutas absolutas falsas (`/scripts/run.sh`)."""
    skill = load_skill_text("x", _skill("Ejecuta ${CLAUDE_SKILL_DIR}/run.sh"))
    assert skill.base_dir == ""

    assert "${CLAUDE_SKILL_DIR}/run.sh" in render_skill(skill, "")


def test_session_id_se_sustituye_por_el_de_la_sesion():
    skill = load_skill_text("x", _skill("Sesión ${CLAUDE_SESSION_ID} en curso"))

    assert "Sesión s-42 en curso" in render_skill(skill, "", session_id="s-42")


def test_la_tool_pasa_el_session_id_del_ctx():
    """`L09`: que `render_skill` sepa sustituir no prueba que alguien le pase el dato."""
    state = SkillsState()
    state.set_skill(load_skill_text("x", _skill("Sesión ${CLAUDE_SESSION_ID}")))
    out = asyncio.run(SkillTool(state).execute({"command": "x"}, _ctx()))

    assert "Sesión s1" in out.output
    assert "${CLAUDE_SESSION_ID}" not in out.output


def test_el_slash_command_pasa_el_session_id_del_ctx():
    provider = SkillsProvider()
    provider.add_skill_text("x", _skill("Sesión ${CLAUDE_SESSION_ID}"))

    out = provider.process_slash_command("/x", _ctx())

    assert out is not None and "Sesión s1" in out


def test_las_variables_se_sustituyen_despues_de_los_args():
    """Orden de A (`:349` antes que `:362`): un arg que contenga la variable la ve
    expandida. Se fija por test para que no se invierta sin darse cuenta."""
    skill = load_skill_text("x", _skill("$ARGUMENTS"))

    assert "s9" in render_skill(skill, "${CLAUDE_SESSION_ID}", session_id="s9")
