"""Contrato de `AskUserQuestion`: cuestionario canónico de 1-4 preguntas + HITL MULTI-TURNO.

El schema es `questions: array[1..4]` (fuente canónica `AskUserQuestionTool.tsx:62`). El `execute`
NO bloquea: emite las preguntas (el consumidor las detecta por el `tool_call` en el stream) y CIERRA
el turno vía `ends_turn`; la respuesta llega en un turno nuevo y el consumidor reinyecta el resultado
real. Esto homologa AskUserQuestion al HITL multi-turno propio del integrador (plan/tool approval),
no al modelo bloqueante del CLI canónico.
"""
from __future__ import annotations

import asyncio

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools.native.ask_user import AskUserQuestionTool


def test_schema_es_cuestionario_1_a_4():
    """Forma del schema, clavada contra A (`AskUserQuestionTool.tsx:14-67`, leído 1→EOF).

    ⚠ Actualizado 2026-08-02 con `FIND-E11-4`: este test clavaba la forma **vieja de
    B**, que era divergente de A —pedía sólo `label` en la opción y dejaba
    `multiSelect` fuera de `required`— y una divergencia no es una mejora (`L10`). En
    A `label` y `description` son ambos `z.string()` (sólo `preview` es
    `.optional()`), `multiSelect` es `.default(false)` (y por eso viaja en `required`
    al serializar), y el nivel superior lleva además `annotations`/`answers`/
    `metadata`, que no los rellena el modelo sino la capa de interacción.
    """
    schema = AskUserQuestionTool.input_schema
    assert schema["required"] == ["questions"]
    assert set(schema["properties"]) == {"questions", "annotations", "answers", "metadata"}
    q = schema["properties"]["questions"]
    assert q["type"] == "array" and q["minItems"] == 1 and q["maxItems"] == 4
    item = q["items"]["properties"]
    assert set(item) == {"question", "header", "options", "multiSelect"}
    assert q["items"]["required"] == ["question", "header", "options", "multiSelect"]
    assert item["multiSelect"]["default"] is False
    assert item["options"]["minItems"] == 2 and item["options"]["maxItems"] == 4
    opcion = item["options"]["items"]
    assert set(opcion["properties"]) == {"label", "description", "preview"}
    assert opcion["required"] == ["label", "description"]


def test_description_es_la_que_A_manda_al_modelo():
    """`FIND-E11-4`: lo que A serializa como `description` es `tool.prompt()`.

    `api.ts:171` manda `description: await tool.prompt(…)`, o sea
    `ASK_USER_QUESTION_TOOL_PROMPT` (`AskUserQuestionTool/prompt.ts:31-44`); el
    `DESCRIPTION` corto es el chip/UI. B tenía en su lugar un texto propio con dos
    cláusulas que A **no tiene**, y empujaba más que el canónico.
    """
    d = AskUserQuestionTool.description
    assert d.startswith("Use this tool when you need to ask the user questions during execution.")
    assert "Prefer this over asking in free-form prose" not in d
    assert "GROUP related questions into a SINGLE call" not in d
    for trozo in (
        "1. Gather user preferences or requirements",
        "Usage notes:",
        '- Users will always be able to select "Other" to provide custom text input',
        "Plan mode note:",
        "use ExitPlanMode for plan approval",
    ):
        assert trozo in d, trozo


def test_execute_cierra_el_turno_sin_bloquear():
    ctx = ToolUseContext(session_id="s1")
    q = [{"question": "¿Tipo?", "header": "Tipo", "options": [{"label": "Correr"}, {"label": "Fuerza"}]}]
    result = asyncio.run(AskUserQuestionTool().execute({"questions": q}, ctx))
    # Señala corte de turno (HITL multi-turno); el resultado real lo reinyecta el consumidor.
    assert getattr(result, "ends_turn", False) is True
    assert "Awaiting" in result.output
    assert not result.is_error
