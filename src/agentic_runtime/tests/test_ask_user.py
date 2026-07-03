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
    schema = AskUserQuestionTool.input_schema
    assert schema["required"] == ["questions"]
    q = schema["properties"]["questions"]
    assert q["type"] == "array" and q["minItems"] == 1 and q["maxItems"] == 4
    item = q["items"]["properties"]
    assert set(item) == {"question", "header", "options", "multiSelect"}
    assert q["items"]["required"] == ["question", "header", "options"]
    assert item["options"]["minItems"] == 2 and item["options"]["maxItems"] == 4


def test_execute_cierra_el_turno_sin_bloquear():
    ctx = ToolUseContext(session_id="s1")
    q = [{"question": "¿Tipo?", "header": "Tipo", "options": [{"label": "Correr"}, {"label": "Fuerza"}]}]
    result = asyncio.run(AskUserQuestionTool().execute({"questions": q}, ctx))
    # Señala corte de turno (HITL multi-turno); el resultado real lo reinyecta el consumidor.
    assert getattr(result, "ends_turn", False) is True
    assert "Awaiting" in result.output
    assert not result.is_error
