"""Contrato de `AskUserQuestion` homologado al canónico: cuestionario de 1-4 preguntas.

El schema es `questions: array[1..4]` (no una sola pregunta) y el `execute` delega en el canal
DEDICADO `app_state.native["ask_user_fn"]` (separado del HITL de permisos), que devuelve una
respuesta por pregunta (texto elegido o libre 'Other'). Fuente canónica:
`claude-code/src/tools/AskUserQuestionTool/AskUserQuestionTool.tsx:62` (`questions.min(1).max(4)`).
"""
from __future__ import annotations

import asyncio

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.tools.native.ask_user import AskUserQuestionTool


def test_schema_es_cuestionario_1_a_4():
    schema = AskUserQuestionTool.input_schema
    assert schema["required"] == ["questions"]
    q = schema["properties"]["questions"]
    assert q["type"] == "array" and q["minItems"] == 1 and q["maxItems"] == 4
    item = q["items"]["properties"]
    assert set(item) == {"question", "header", "options", "multiSelect"}
    assert q["items"]["required"] == ["question", "header", "options"]
    assert item["options"]["minItems"] == 2 and item["options"]["maxItems"] == 4


def test_execute_delega_en_ask_user_fn_y_formatea_respuestas():
    recibido: dict = {}

    async def fake_ask_user_fn(questions):
        recibido["questions"] = questions
        return ["10K", "52 min, 4 días"]  # una respuesta por pregunta (2ª es libre 'Other')

    ctx = ToolUseContext(session_id="s1")
    ctx.app_state.native["ask_user_fn"] = fake_ask_user_fn

    questions = [
        {"question": "¿Qué distancia?", "header": "Distancia",
         "options": [{"label": "5K"}, {"label": "10K"}]},
        {"question": "¿Tu marca y días/semana?", "header": "Datos",
         "options": [{"label": "Principiante"}, {"label": "Avanzado"}]},
    ]
    result = asyncio.run(AskUserQuestionTool().execute({"questions": questions}, ctx))

    # el canal dedicado recibió el cuestionario íntegro (N preguntas), no de a una
    assert recibido["questions"] == questions
    # el resultado enlaza cada pregunta con su respuesta (incluida la libre)
    assert "¿Qué distancia? -> 10K" in result.output
    assert "¿Tu marca y días/semana? -> 52 min, 4 días" in result.output


def test_execute_una_sola_pregunta_sigue_funcionando():
    async def fake(questions):
        return ["Correr"]

    ctx = ToolUseContext(session_id="s1")
    ctx.app_state.native["ask_user_fn"] = fake
    q = [{"question": "¿Tipo?", "header": "Tipo", "options": [{"label": "Correr"}, {"label": "Fuerza"}]}]
    result = asyncio.run(AskUserQuestionTool().execute({"questions": q}, ctx))
    assert "¿Tipo? -> Correr" in result.output
