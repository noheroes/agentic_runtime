"""`FIND-SKILL9/17` (= `CG-SKILL-4`) — el catálogo de skills tiene que LLEGAR AL MODELO.

Estado antes de pagar, y conviene decirlo con precisión porque es peor que el de
`FIND-AGENT-LIST-1`: `SkillsProvider.catalog()` existía, estaba probado y **no lo
consumía nadie en producción** (el único `.catalog(` fuera de `capabilities/` vivía en
ficheros de test). El único punto por el que un nombre de skill alcanzaba al modelo era
el mensaje de ERROR de `skill_tool.py` — es decir, el modelo sólo podía aprender el
catálogo **fallando primero**, y para fallar tenía que haber adivinado un nombre.

Igual que en el listado de subagentes, casi todo se afirma sobre
`ScriptedCaller.seen_messages` —lo que el modelo vio— y no sobre el retorno de una
función auxiliar: un test sobre `format_skill_line` seguiría verde con el loop sin
cablear, que es exactamente el estado que el hallazgo describe (`H-L4`, `L09`).

Canónico: `utils/attachments.ts:2596-2765` (`getSkillListingAttachments`),
`utils/messages.ts:3728-3738` (render), `tools/SkillTool/prompt.ts:20-171`
(presupuesto y formato de línea), `commands.ts:563-581` (elegibilidad).
"""
from __future__ import annotations

from agentic_runtime.capabilities.contracts import CapabilitySummary
from agentic_runtime.capabilities.manager import CapabilityManager
from agentic_runtime.capabilities.skill_listing_delta import (
    DEFAULT_CHAR_BUDGET,
    MAX_LISTING_DESC_CHARS,
    SKILL_LISTING_KEY,
    SkillListingDelta,
    char_budget,
    compute_skill_listing_delta,
    format_entries_within_budget,
    format_skill_line,
    render_skill_listing_delta,
)
from agentic_runtime.capabilities.skills import SkillsProvider
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.events import DoneEvent
from agentic_runtime.loop.agent_loop import AgentLoop
from agentic_runtime.tools.registry import ToolRegistry

from .test_loop_homologation import RecordingTool, ScriptedCaller

_HEADER = "The following skills are available for use with the Skill tool:"


# ──────────────────────────────────────────────────────────────────────────────
# Dobles
# ──────────────────────────────────────────────────────────────────────────────

_SKILL = """---
description: {desc}
---
Cuerpo de la skill.
"""


def _provider(**skills: str) -> SkillsProvider:
    prov = SkillsProvider()
    for name, desc in skills.items():
        prov.add_skill_text(name, _SKILL.format(desc=desc))
    return prov


def _loop(provider: SkillsProvider | None, *, turns: int = 1, **kw):
    reg = ToolRegistry()
    reg.register(RecordingTool("echo"))
    caller = ScriptedCaller([[DoneEvent(stop_reason="stop")] for _ in range(turns)])
    manager = CapabilityManager([provider] if provider is not None else [])
    return (
        AgentLoop(
            model_caller=caller,
            tool_registry=reg,
            capability_manager=manager,
            **kw,
        ),
        caller,
    )


def _listing(caller: ScriptedCaller, turn: int = -1) -> str:
    """Listado anunciado EN ESE turno, no el que arrastra la historia acumulada."""
    vistos = caller.seen_messages
    idx = turn if turn >= 0 else len(vistos) + turn
    previos = len(vistos[idx - 1]) if idx > 0 else 0
    nuevos = vistos[idx][previos:]
    bloques = [
        m.get("content", "")
        for m in nuevos
        if m.get("role") == "user" and _HEADER in m.get("content", "")
    ]
    return bloques[0] if bloques else ""


# ──────────────────────────────────────────────────────────────────────────────
# La conducta: el listado llega al modelo
# ──────────────────────────────────────────────────────────────────────────────

async def test_el_catalogo_de_skills_llega_al_modelo():
    """El hueco entero, medido por su efecto.

    Antes, la tool `Skill` pedía un `command` de tipo `string` y NINGUNA lista decía qué
    valores existían. El formato de la línea es el de `formatCommandDescription`
    (`SkillTool/prompt.ts:52-66`), no uno propio."""
    loop, caller = _loop(_provider(commit="Crea un commit con el estilo del repo."))
    await loop.run("hola", ToolUseContext(session_id="s"))

    texto = _listing(caller)
    assert texto, "el modelo no recibió NINGÚN listado de skills"
    assert _HEADER in texto
    assert "- commit: Crea un commit con el estilo del repo." in texto


async def test_el_listado_va_envuelto_en_system_reminder():
    """`wrapMessagesInSystemReminder` (`messages.ts:3732`): es contexto del sistema, no
    una intervención del usuario."""
    loop, caller = _loop(_provider(commit="Crea un commit."))
    await loop.run("hola", ToolUseContext(session_id="s"))
    texto = _listing(caller)
    assert texto.startswith("<system-reminder>")
    assert texto.endswith("</system-reminder>")


async def test_sin_skills_no_se_anuncia_nada():
    """`getSkillListingAttachments` devuelve `[]` con la lista vacía (`:2740`), y el
    render descarta el attachment sin contenido (`messages.ts:3729-3731`)."""
    loop, caller = _loop(_provider())
    await loop.run("hola", ToolUseContext(session_id="s"))
    assert _listing(caller) == ""


async def test_sin_la_tool_skill_publicada_no_se_anuncia_nada():
    """Guarda del canónico (`attachments.ts:2712-2717`): si la tool `Skill` no está en
    las tools de este turno, el listado sería inaccionable y no se emite.

    La condición se mide sobre el pool PUBLICADO, no sobre el catálogo: desde
    `FIND-POOL-1` no son lo mismo.

    ⚠ Este test **acreditaba en falso** (`INY-121` salió VERDE con la guarda arrancada).
    Montaba un provider con TODAS las skills deshabilitadas, así que no había ni tool ni
    entradas de catálogo: el delta salía `None` por «nada que anunciar», no por la guarda,
    y arrancarla no cambiaba nada. El montaje correcto tiene que separar las dos cosas:
    catálogo LLENO y tool `Skill` fuera del pool. Es además el caso real —un subagente
    restringido (`resolveAgentTools`)— y no un montaje de laboratorio.
    """
    prov = _provider(commit="Crea un commit.")
    loop, caller = _loop(prov, agent_allowed_tools=("echo",))
    ctx = ToolUseContext(session_id="s")
    await loop.run("hola", ctx)

    # control positivo: el catálogo NO está vacío, luego el silencio es por la guarda
    assert [e.name for e in prov.catalog(ctx) if e.kind == "skill"] == ["commit"]
    assert _listing(caller) == ""


async def test_el_listado_no_se_repite_turno_a_turno():
    """`sentSkillNames` (`attachments.ts:2599`): sólo las NUEVAS. Sin esto el listado
    entero se reinyecta en cada turno y quema la caché de prefijo."""
    loop, caller = _loop(_provider(commit="Crea un commit."), turns=3)
    ctx = ToolUseContext(session_id="s")
    await loop.run("uno", ctx)
    await loop.run("dos", ctx)
    assert _listing(caller, 0) != ""
    assert _listing(caller, -1) == "", "el listado se re-anunció sin haber cambiado"


async def test_una_skill_nueva_se_anuncia_sola():
    """El delta es incremental: `newSkills = allCommands.filter(cmd => !sent.has(...))`
    (`attachments.ts:2731`). Lo ya anunciado no vuelve."""
    prov = _provider(commit="Crea un commit.")
    loop, caller = _loop(prov, turns=3)
    ctx = ToolUseContext(session_id="s")
    await loop.run("uno", ctx)
    prov.add_skill_text("review", _SKILL.format(desc="Revisa un PR."))
    await loop.run("dos", ctx)

    segundo = _listing(caller, -1)
    assert "- review: Revisa un PR." in segundo
    assert "commit" not in segundo, "se re-anunció una skill ya conocida"


async def test_una_skill_que_desaparece_fuerza_el_reanuncio_completo():
    """Homólogo de `resetSentSkillNames()` (`attachments.ts:2601-2606`), que el canónico
    dispara ante un cambio genuino del conjunto de skills y hace que el siguiente
    listado salga ENTERO.

    Sin esto el modelo se queda con un catálogo que ya no existe y no hay ninguna otra
    señal que lo desmienta: el canónico no tiene rama de «bajas», tiene reinicio."""
    prov = _provider(commit="Crea un commit.", review="Revisa un PR.")
    loop, caller = _loop(prov, turns=3)
    ctx = ToolUseContext(session_id="s")
    await loop.run("uno", ctx)
    prov.state.remove("review")
    await loop.run("dos", ctx)

    segundo = _listing(caller, -1)
    assert "- commit: Crea un commit." in segundo, "no se re-anunció el catálogo vigente"
    assert "review" not in segundo


async def test_el_sidecar_viaja_como_dato_no_como_texto_reparseado():
    """`FIND-DEFER-1` otra vez, y aquí sería igual de irrecuperable: una `description`
    puede llevar saltos de línea, luego «una línea = una entrada» es falso por
    construcción. Lo anunciado se reconstruye del sidecar ESTRUCTURADO.

    ⚠ Este test **acreditaba en falso** (`INY-122` salió VERDE re-parseando el texto):
    aseveraba que el sidecar se ESCRIBE, y el defecto está en el lado de LECTURA. Las dos
    mitades son independientes —se puede escribir el sidecar y no leerlo jamás—, así que
    ahora se miden las dos.
    """
    prov = _provider(commit="Crea un commit.")
    loop, _caller = _loop(prov, turns=2)
    ctx = ToolUseContext(session_id="s")
    await loop.run("uno", ctx)
    sidecars = [m.get(SKILL_LISTING_KEY) for m in ctx.messages if SKILL_LISTING_KEY in m]
    assert sidecars == [{"names": ["commit"]}]

    # LECTURA: el texto rendido SIN sidecar no acredita nada — quien lo lea del texto
    # creerá que `commit` ya se anunció y callará.
    entries = [e for e in prov.catalog(ctx) if e.kind == "skill"]
    solo_texto = [{"role": "user", "content": render_skill_listing_delta(
        SkillListingDelta(names=("commit",), content="- commit: Crea un commit."))}]
    assert compute_skill_listing_delta(
        entries, solo_texto, skill_tool_available=True
    ) is not None, "lo anunciado se reconstruyó del TEXTO, no del sidecar"

    # …y el sidecar SIN texto sí acredita: es el dato, no el render.
    solo_sidecar = [{"role": "user", "content": "", SKILL_LISTING_KEY: {"names": ["commit"]}}]
    assert compute_skill_listing_delta(entries, solo_sidecar, skill_tool_available=True) is None


async def test_una_descripcion_con_saltos_de_linea_no_rompe_la_convergencia():
    """El caso que hace que re-parsear el texto no sea una alternativa peor sino una
    incorrecta: con `\\n` en la descripción, contar líneas anuncia entradas que no
    existen y el delta no converge nunca.

    ⚠ La descripción de este test era `"linea1\\nlinea2"`, y con ella el re-parseo
    CONVERGE igual: sólo la primera línea empieza por `- `, así que sale exactamente
    `["commit"]` y el defecto no se ve (`INY-122` verde). El caso adversarial de verdad
    es una descripción que contenga una VIÑETA — texto perfectamente normal en un
    `SKILL.md`—, porque entonces el re-parseo inventa una entrada `otra-cosa` que no
    existe y pierde la real."""
    prov = SkillsProvider()
    prov.add_skill_text(
        "commit", "---\ndescription: \"hace dos cosas:\\n- otra-cosa: no soy una skill\"\n---\ncuerpo"
    )
    loop, caller = _loop(prov, turns=3)
    ctx = ToolUseContext(session_id="s")
    await loop.run("uno", ctx)
    await loop.run("dos", ctx)
    assert _listing(caller, 0) != ""
    assert _listing(caller, -1) == ""


async def test_una_skill_deshabilitada_no_se_lista():
    """El predicado de enablement ya existía y filtraba el catálogo; lo que faltaba era
    que el catálogo llegara a alguna parte."""
    prov = _provider(commit="Crea un commit.")
    prov.add_skill_text("oculta", "---\ndescription: d\nenabled: false\n---\ncuerpo")
    loop, caller = _loop(prov)
    await loop.run("hola", ToolUseContext(session_id="s"))
    texto = _listing(caller)
    assert "commit" in texto
    assert "oculta" not in texto


async def test_una_skill_con_disable_model_invocation_no_se_lista():
    """Mitad de ELEGIBILIDAD de `FIND-SKILL17`: `getSkillToolCommands` excluye
    `disableModelInvocation` (`commands.ts:568`). No es lo mismo que deshabilitada —
    sigue siendo invocable por el usuario con `/nombre`, que es su razón de existir."""
    prov = _provider(commit="Crea un commit.")
    prov.add_skill_text(
        "solo_usuario",
        "---\ndescription: d\ndisable-model-invocation: true\n---\ncuerpo",
    )
    loop, caller = _loop(prov)
    await loop.run("hola", ToolUseContext(session_id="s"))
    texto = _listing(caller)
    assert "commit" in texto
    assert "solo_usuario" not in texto


async def test_el_when_to_use_se_concatena_a_la_descripcion():
    """`getCommandDescription` (`prompt.ts:43-50`): `${description} - ${whenToUse}`.
    Antes B ponía la descripción en los DOS campos del `CapabilitySummary`, así que
    `when_to_use` no aportaba información: era un duplicado."""
    prov = SkillsProvider()
    prov.add_skill_text(
        "pdf", "---\ndescription: Trabaja con PDFs.\nwhen_to_use: Cuando haya un .pdf.\n---\ncuerpo"
    )
    loop, caller = _loop(prov)
    await loop.run("hola", ToolUseContext(session_id="s"))
    assert "- pdf: Trabaja con PDFs. - Cuando haya un .pdf." in _listing(caller)


# ──────────────────────────────────────────────────────────────────────────────
# Presupuesto (`SkillTool/prompt.ts:20-171`)
# ──────────────────────────────────────────────────────────────────────────────

def _entry(name: str, desc: str, *, source: str = "") -> CapabilitySummary:
    return CapabilitySummary(name=name, kind="skill", description=desc, source=source)


def test_el_presupuesto_por_defecto_es_el_del_canonico():
    assert char_budget(None) == DEFAULT_CHAR_BUDGET
    # 1 % de la ventana, en CARACTERES (`SKILL_BUDGET_CONTEXT_PERCENT` × `CHARS_PER_TOKEN`).
    assert char_budget(200_000) == 8_000
    assert char_budget(1_000_000) == 40_000


def test_una_descripcion_larga_se_corta_a_250_caracteres():
    """`MAX_LISTING_DESC_CHARS` (`prompt.ts:29`): el listado es para DESCUBRIR; la tool
    carga el contenido completo al invocar. Aplica también a las bundled."""
    linea = format_skill_line(_entry("x", "d" * 1000))
    descripcion = linea.split(": ", 1)[1]
    assert len(descripcion) == MAX_LISTING_DESC_CHARS
    assert descripcion.endswith("…")


def test_bajo_presupuesto_las_descripciones_se_truncan_pero_los_nombres_no():
    """Rama `description_trimmed` (`prompt.ts:163-170`): el nombre es lo único que hace
    invocable a la skill, así que es lo último que se pierde."""
    entradas = [_entry(f"skill{i}", "d" * 200) for i in range(10)]
    texto = format_entries_within_budget(entradas, char_budget_override=600)
    lineas = texto.splitlines()
    assert len(lineas) == 10
    for i, linea in enumerate(lineas):
        assert linea.startswith(f"- skill{i}: ")
        # reparto = (presupuesto − coste de los nombres) / nº de entradas, y el corte
        # incluye el '…' (`truncateToWidth`, `utils/truncate.ts:63-75`).
        assert len(linea.split(": ", 1)[1]) == 49
        assert linea.endswith("…")


def test_con_presupuesto_extremo_se_cae_a_solo_nombres():
    """Rama `names_only` (`prompt.ts:137-141`) cuando el reparto por entrada baja de
    `MIN_DESC_LENGTH`. Se pierde la descripción, nunca la invocabilidad."""
    entradas = [_entry(f"skill{i}", "d" * 200) for i in range(50)]
    texto = format_entries_within_budget(entradas, char_budget_override=400)
    assert texto.splitlines()[0] == "- skill0"
    assert "d" * 20 not in texto


def test_las_bundled_nunca_se_truncan():
    """`bundledIndices` (`prompt.ts:92-108`, `:166`): las de la casa conservan la
    descripción completa aunque el resto caiga a sólo nombres."""
    entradas = [_entry("propia", "x" * 240, source="bundled")]
    entradas += [_entry(f"skill{i}", "d" * 200) for i in range(50)]
    texto = format_entries_within_budget(entradas, char_budget_override=400)
    assert texto.splitlines()[0] == "- propia: " + "x" * 240
    assert texto.splitlines()[1] == "- skill0"


def test_sin_entradas_no_hay_delta():
    assert compute_skill_listing_delta([], [], skill_tool_available=True) is None
