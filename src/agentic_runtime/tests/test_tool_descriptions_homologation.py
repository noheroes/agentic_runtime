"""Homologación de las DESCRIPCIONES de las tools nativas (`GAP-PROMPT-1`).

`GAP-PROMPT-1` es la deuda de que A dirige la elección de tool desde la capa de prompt
y B no tenía equivalente. Se pagó en dos entregas: `ba2ac47` (8 descripciones) y esta
ventana (las 13 restantes, contra el `prompt()`/`DESCRIPTION` canónico de cada una).

Por qué este fichero existe, dicho sin adorno: de las 13 descripciones sin portar, **una
sola** tenía test que declarase la deuda (`FIND-PLAN1`, un `xfail(strict=True)` que se puso
rojo por XPASS al pagarla). Las otras 12 eran invisibles para la suite — se podían dejar en
una línea indefinidamente con el verde intacto. Eso es `H-L4`.

El test que carga el peso NO es «la descripción contiene tal frase» (eso lo satisface un
copy-paste y no prueba conducta). Es `test_ninguna_descripcion_anuncia_parametros_que_su_
esquema_no_acepta`: la propiedad que cobró en `FIND-E11-3`, donde el modelo leyó un campo
anunciado, lo mandó, y la tool lo descartó en silencio devolviendo un resultado
indistinguible de la respuesta legítima. Portar un prompt canónico VERBATIM es precisamente
la vía más fácil de reintroducir ese fallo, porque los prompts de A describen esquemas de A.
"""
from __future__ import annotations

import inspect
import re

import pytest

from agentic_runtime.loop import agent_loop
from agentic_runtime.tools.native.agent import AgentTool
from agentic_runtime.tools.native.bash import BashTool
from agentic_runtime.tools.native.config import ConfigTool
from agentic_runtime.tools.native.plan_mode import EnterPlanModeTool, ExitPlanModeTool
from agentic_runtime.tools.native.task_tools import (
    TaskCreateTool,
    TaskGetTool,
    TaskListTool,
    TaskOutputTool,
    TaskStopTool,
    TaskUpdateTool,
)
from agentic_runtime.tools.native.todo_write import TodoWriteTool
from agentic_runtime.tools.native.worktree import EnterWorktreeTool, ExitWorktreeTool

#: Las 13 pagadas en esta ventana. `clone_repository` NO está: es divergencia declarada
#: (`L10`), no deuda, y meterla aquí la acreditaría como homologada sin serlo.
PAGADAS = [
    AgentTool,
    # `bash` se pagó en `ba2ac47` con el bloque de preferencia de tools y entra aquí al
    # completarse con el protocolo de git de A (`D-18`): el guard de `FIND-E11-3` importa
    # el doble en la tool cuyo esquema es de UN campo y cuyo canónico anuncia tres.
    BashTool,
    ConfigTool,
    EnterPlanModeTool,
    ExitPlanModeTool,
    EnterWorktreeTool,
    ExitWorktreeTool,
    TodoWriteTool,
    TaskCreateTool,
    TaskGetTool,
    TaskListTool,
    TaskUpdateTool,
    TaskStopTool,
    TaskOutputTool,
]


def _ids(clases):
    return [c.name for c in clases]


# ===========================================================================
# El guard de fondo: `FIND-E11-3` no se puede reintroducir portando prompts
# ===========================================================================

#: Campos que los prompts CANÓNICOS anuncian y que los esquemas de B **no** tienen.
#: Cada uno es un `FIND-E11-3` en potencia si se cuela al portar el texto de A.
CAMPOS_DE_A_QUE_B_NO_TIENE = {
    "activeForm",
    "blocks",
    "blockedBy",
    "addBlocks",
    "addBlockedBy",
    "owner",
    "metadata",
    "isolation",
    "team_name",
    "taskId",
    # De `bash`: A los tiene como parámetros (`BashTool/prompt.ts:335`, `:39`), B no —
    # el timeout es fijo (`timeout_seconds = 30.0`) y no hay ejecución en segundo plano.
    # Portar esas dos frases prometería palancas que el esquema de un solo campo ignora.
    "run_in_background",
    "timeout",
}


@pytest.mark.parametrize("cls", PAGADAS, ids=_ids(PAGADAS))
def test_ninguna_descripcion_anuncia_parametros_que_su_esquema_no_acepta(cls):
    """Ningún campo de A ausente en B puede aparecer anunciado en la descripción.

    Ésta es la aserción que impide reintroducir `FIND-E11-3`. No mira estilo ni
    longitud: mira que el texto que lee el modelo no le prometa una palanca que la
    tool va a ignorar en silencio.
    """
    texto = cls.description or ""
    propiedades = set((cls.input_schema or {}).get("properties", {}))

    # Sólo cuentan las apariciones con FORMA DE PARÁMETRO. La primera versión de este
    # test usaba `\bcampo\b` a secas sobre la prosa y dio un falso positivo, cazado y
    # dejado escrito aquí a propósito: marcó `blocks` en `Agent` por la frase literal de
    # A «multiple Agent tool use content blocks` (`AgentTool/prompt.ts:271`), donde
    # `blocks` es un sustantivo inglés y no un campo. Un test que no distingue la prosa
    # del contrato manda a «arreglar» una descripción correcta.
    #
    # A anuncia sus parámetros siempre en una de estas formas —`**owner**`, `` `addBlocks` ``,
    # `"taskId"`, `{"taskId": "1"}`—, así que exigirlas es preciso sin ser laxo.
    def _anunciado_como_parametro(campo: str) -> bool:
        patrones = (
            rf"`{re.escape(campo)}`",  # `campo`
            rf"\*\*{re.escape(campo)}\*\*",  # **campo**
            rf'"{re.escape(campo)}"',  # "campo" y clave JSON
            rf"\b{re.escape(campo)}\s*[:=]",  # campo: … / campo=…
        )
        return any(re.search(p, texto) for p in patrones)

    colados = sorted(
        campo
        for campo in CAMPOS_DE_A_QUE_B_NO_TIENE
        if campo not in propiedades and _anunciado_como_parametro(campo)
    )
    assert not colados, (
        f"{cls.name}: la descripción anuncia {colados}, que su input_schema no acepta. "
        f"Es la trampa de `FIND-E11-3`: el modelo lo manda y la tool lo descarta en "
        f"silencio. Si el campo debe existir, se añade al esquema; si no, se omite del "
        f"texto Y se declara la omisión en comentario."
    )


@pytest.mark.parametrize("cls", PAGADAS, ids=_ids(PAGADAS))
def test_la_omision_esta_declarada_y_no_meramente_hecha(cls):
    """Toda descripción portada cita el canónico del que se portó.

    `D-07`/`declarar-no-es-pagar` va en la dirección de que declarar no basta; ésta es
    la dirección contraria y también hace falta: **omitir en silencio tampoco basta**.
    Sin la cita, la próxima ventana no puede distinguir «recortado a propósito porque B
    no lo tiene» de «se portó a medias», y la deuda se vuelve invisible otra vez.
    """
    import inspect

    fuente = inspect.getsource(cls)
    assert "GAP-PROMPT-1" in fuente, (
        f"{cls.name}: la descripción no cita `GAP-PROMPT-1` ni el canónico del que se "
        f"portó. Una descripción larga sin procedencia no es homologación acreditable."
    )
    assert re.search(r"prompt\.ts:\d+|\.tsx:\d+", fuente), (
        f"{cls.name}: falta la cita con FICHERO:LÍNEA del canónico portado."
    )


@pytest.mark.parametrize("cls", PAGADAS, ids=_ids(PAGADAS))
def test_ninguna_quedo_en_una_linea(cls):
    """Control de regresión de la deuda pagada, no métrica de calidad.

    El umbral es deliberadamente bajo (200 ch): no pretende medir si la descripción es
    buena —eso lo mide el E2g con el modelo delante—, sólo que ninguna volvió al
    one-liner que atraía al modelo. Las 13 estaban entre 38 y 213 ch antes de pagar.
    """
    assert len(cls.description or "") > 200, (
        f"{cls.name}: {len(cls.description or '')} ch — volvió al one-liner sin portar."
    )


# ===========================================================================
# Marcadores por tool: que se portó la rama y el contenido que toca
# ===========================================================================

def test_agent_anuncia_el_listado_por_la_via_que_b_emite_de_verdad():
    """`FIND-AGENT-LIST-1` PAGADO — y la frase sólo vale si el emisor existe.

    Este test era el guardián inverso: prohibía la frase «Available agent types are
    listed in <system-reminder> messages» mientras B no emitiera nada, porque escribirla
    sin emisor manda al modelo a buscar una lista inexistente. Ahora que B toma la vía de
    attachment de A (`AgentTool/prompt.ts:196-199`), la frase es obligatoria — pero la
    aserción que carga el peso es la SEGUNDA: que el emisor siga cableado. Aseverar sólo
    la frase acreditaría en falso exactamente igual que antes, al revés (`H-L4`).
    """
    texto = AgentTool.description
    assert "Available agent types are listed in <system-reminder> messages" in texto

    # El emisor, por su cableado real: el loop lo llama en el turno, no basta que el
    # módulo exista (`L09`).
    fuente_loop = inspect.getsource(agent_loop)
    assert "_announce_agent_listing" in fuente_loop
    assert fuente_loop.count("_announce_agent_listing") >= 2, (
        "el método existe pero nadie lo llama: la frase de la descripción sería falsa"
    )

    # Lo que ya estaba: el when-NOT-to-use, que evita que el modelo delegue en un
    # subagente lo que resuelve leyendo un fichero (`:235-239`).
    assert "When NOT to use the Agent tool:" in texto


def test_agent_conserva_la_instruccion_de_paralelismo():
    """Contrapartida declarada de la nota de concurrencia que B NO emite.

    A la mete en el attachment (`messages.ts:4207-4211`) condicionada al tipo de
    suscripción, que es política del host y el runtime no puede conocer. El efecto que
    persigue lo produce en B esta instrucción incondicional de la descripción; si
    desaparece, la divergencia declarada se convierte en hueco y este test lo dice.
    """
    assert 'run agents "in parallel"' in AgentTool.description


def test_task_update_no_promete_transiciones_de_estado():
    """`FIND-TASK-1`: en B el modelo no puede mover el `status` de una tarea.

    El `PROMPT` canónico (`TaskUpdateTool/prompt.ts:3-84`) es casi todo flujo de estados
    (`pending → in_progress → completed`, `deleted`). El `TaskUpdate` de B sólo reescribe
    `description`. La carencia es ESTRUCTURAL y no se paga con texto — pero el texto no
    puede mentir sobre ella mientras tanto.
    """
    texto = TaskUpdateTool.description
    assert "in_progress" not in texto and "deleted" not in texto, (
        "TaskUpdate anuncia transiciones de estado que su esquema no acepta"
    )
    assert set(TaskUpdateTool.input_schema["properties"]) == {"task_id", "description"}


def test_task_output_no_manda_al_modelo_a_un_output_file_inexistente():
    """El encabezado `DEPRECATED` de A (`TaskOutputTool.tsx:173`) NO se porta.

    A puede recomendar `Read` sobre el `output_file` porque sus tareas lo devuelven. Las
    de B no: el resultado vive en `record.result` y `TaskOutput` es la única vía. Portar
    el texto verbatim mandaría al modelo a un fichero que no existe — un caso donde
    copiar el canónico al pie de la letra produce una divergencia de CONDUCTA.
    """
    texto = TaskOutputTool.description
    assert "output file" not in texto.lower() and "DEPRECATED" not in texto
    assert "Retrieves output from a running or completed task" in texto


def test_config_no_inventa_un_dominio_de_ajustes():
    """`FIND-CFG-2`: B no tiene registro de ajustes, así que no hay lista que enumerar.

    A genera `## Configurable settings list` recorriendo `SUPPORTED_SETTINGS`
    (`ConfigTool/prompt.ts:18-46`). B acepta cualquier clave. Enumerar ajustes aquí
    fabricaría un dominio que la tool no valida.
    """
    texto = ConfigTool.description
    assert "Configurable settings list" not in texto
    assert "editorMode" not in texto and "permissions.defaultMode" not in texto
    assert "## Usage" in texto and "Omit the \"value\" parameter" in texto


def test_enter_worktree_dice_la_ubicacion_real_y_no_la_del_canonico():
    """La divergencia declarada del módulo tiene que llegar al modelo.

    `EnterWorktreeTool/prompt.ts:23` dice `.claude/worktrees/`. B crea el worktree en
    `.worktrees/` dentro del write-root, y eso está declarado en la cabecera de
    `worktree.py` desde la ventana de `C6`. Una descripción que repitiera la ruta de A
    haría buscar los ficheros donde no están.
    """
    texto = EnterWorktreeTool.description
    assert "`.worktrees/`" in texto
    assert ".claude/worktrees" not in texto


def test_bash_lleva_el_protocolo_de_git_de_a():
    """`D-18`: la mitad del texto de A en `bash` es su bloque de git, y B no lo tenía.

    Se había descartado como «flujo del integrador». La comprobación dice que **ningún
    sitio de B lo llevaba** —ni esta descripción ni el prompt del integrador—, así que no
    estaba trasladado: estaba perdido. Es `getCommitAndPRInstructions()` en su rama
    EXTERNA (`BashTool/prompt.ts:81-160`), la que no depende de `USER_TYPE === 'ant'`.

    Se ancla en los literales que llevan la CONDUCTA, no en la longitud: un umbral de
    caracteres se pone verde con relleno.
    """
    texto = BashTool.description

    # Las cuatro prohibiciones del Git Safety Protocol (`:88-94`).
    assert "NEVER update the git config" in texto
    assert "NEVER run destructive git commands" in texto
    assert "NEVER run force push to main/master" in texto
    assert "NEVER commit changes unless the user explicitly asks you to" in texto
    # La regla de `--amend` tras hook fallido (`:92`), que es la que evita perder trabajo.
    assert "Always create NEW commits rather than amending" in texto
    assert "the commit did NOT happen" in texto
    # Los dos flujos numerados (`:96`, `:132`) y el HEREDOC (`:119-125`).
    assert "# Committing changes with git" in texto
    assert "# Creating pull requests" in texto
    assert "ALWAYS pass the commit message via a HEREDOC" in texto


def test_bash_no_arrastra_la_atribucion_ni_el_perfil_de_shell():
    """Las dos adaptaciones de `D-18`, cada una por su motivo, y ninguna por comodidad.

    1. La atribución interpolada de A (`getAttributionTexts()`, `:79`, `:107`, `:122`) es
       política del INTEGRADOR: qué firma lleva un commit no lo decide el núcleo genérico.
    2. La frase «The shell environment is initialized from the user's profile» (`:357`)
       sería FALSA aquí: `create_subprocess_shell` lanza `sh -c`, ni login ni interactivo.
       Copiar el canónico al pie de la letra también es divergencia cuando el entorno que
       describe no es el que hay.
    """
    texto = BashTool.description
    assert "Co-Authored-By" not in texto
    assert "Generated with" not in texto
    assert "initialized from the user's profile" not in texto


#: Las 12 tools donde A declara `searchHint` y B no lo tenía (`D-18`). Se portan con la
#: grafía literal de A; sólo `Sleep`, `ToolSearch` y `clone_repository` quedan sin hint,
#: y por razón: A no declara hint para las dos primeras y la tercera no existe en A.
HINTS_PORTADOS = {
    "Agent": "delegate work to a subagent",
    "AskUserQuestion": "prompt the user with a multiple-choice question",
    "bash": "execute shell commands",
    "EnterPlanMode": "switch to plan mode to design an approach before coding",
    "ExitPlanMode": "present plan for approval and start coding (plan mode only)",
    "EnterWorktree": "create an isolated git worktree and switch into it",
    "ExitWorktree": "exit a worktree session and return to the original directory",
    "TaskCreate": "create a task in the task list",
    "TaskGet": "retrieve a task by ID",
    "TaskList": "list all tasks",
    "TaskStop": "kill a running background task",
    "TaskUpdate": "update a task",
}


def test_el_censo_lleva_el_search_hint_que_a_declara():
    """`D-18`: el hint es la señal de ranking, y valía +4 donde la descripción vale +2.

    No es cosmético y no es opcional: bajo diferido `tool_search` decide con nombre,
    descripción y hint, y el ranking BONIFICA a las MCP —12/6 frente a 10/5 por nombre
    (`tool_search.py:211-213`, calcado de `ToolSearchTool.ts:186-302`)—. Una nativa sin
    hint entra a esa comparación con 4 puntos menos contra una tool de terceros cuyo
    texto lo escribe el propio server. 12 de las 25 estaban así.
    """
    from agentic_runtime.tools.factory import create_tools

    por_nombre = {t.name: t for t in create_tools().all_tools()}
    faltan = {
        nombre: hint
        for nombre, hint in HINTS_PORTADOS.items()
        if (getattr(por_nombre[nombre], "search_hint", "") or "") != hint
    }
    assert not faltan, f"hints ausentes o alterados respecto a A: {sorted(faltan)}"


def test_las_tres_sin_hint_lo_estan_por_razon_y_no_por_olvido():
    """La contrapartida: sin esta aserción, «faltan 3» y «sobran 12» son el mismo verde.

    `Sleep` y `ToolSearch` no llevan hint porque **A tampoco se lo declara**; hay que ir
    a inventarlo para ponérselo, y inventar hint es exactamente lo que este tramo evita.
    `clone_repository` no existe en A: es divergencia declarada (`L10`).
    """
    from agentic_runtime.tools.factory import create_tools

    sin_hint = {
        t.name for t in create_tools().all_tools() if not (getattr(t, "search_hint", "") or "")
    }
    assert sin_hint == {"Sleep", "ToolSearch", "clone_repository"}, (
        f"el censo sin hint cambió: {sorted(sin_hint)}"
    )
