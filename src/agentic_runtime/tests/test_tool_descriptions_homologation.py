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

import re

import pytest

from agentic_runtime.tools.native.agent import AgentTool
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

def test_agent_no_promete_el_listado_de_subagentes_que_b_no_tiene():
    """`FIND-AGENT-LIST-1` no se tapa con una frase.

    A resuelve el listado por una de dos vías (`AgentTool/prompt.ts:196-199`): inline en
    la descripción, o la frase «Available agent types are listed in <system-reminder>
    messages» cuando el listado viaja como attachment. B **no tiene ninguna de las dos**.
    Escribir esa frase en B sería mandar al modelo a buscar una lista que no existe:
    una coartada, no un pago. Este test la prohíbe hasta que el listado exista de verdad.
    """
    texto = AgentTool.description
    assert "Available agent types are listed in" not in texto, (
        "se anunció el listado de subagentes por attachment sin que B lo emita "
        "(`FIND-AGENT-LIST-1` sigue ABIERTO)"
    )
    # Lo que sí debe estar: el when-NOT-to-use, que es lo que evita que el modelo
    # delegue en un subagente lo que resuelve leyendo un fichero (`:235-239`).
    assert "When NOT to use the Agent tool:" in texto


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
