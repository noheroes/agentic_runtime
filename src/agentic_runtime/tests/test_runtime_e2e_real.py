"""E2E real del runtime con LLM (Azure gpt-5.4-mini) vía `create_runtime()`.

A diferencia de test_runtime_e2e (caller faux determinista), aquí el runtime COMPLETO
corre contra el modelo real. Se ejercita el modo foreground con varios turnos y uso de
herramientas: el LLM decide llamar tools, el ToolDispatcher las ejecuta, y el resultado
reingresa como contexto del siguiente turno.

Gating: se omite si no hay configuración Azure disponible (el `.env` de agent_core +
el CA bundle corporativo). El CI no corre este paquete; está pensado para evidencia local.

Las aserciones verifican comportamiento funcional genuino (la tool se despachó de verdad
y el modelo consumió su salida — tokens únicos no adivinables), no progreso aparente.
"""
from __future__ import annotations

import uuid

import pytest

from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.execution.tasks.status import TaskStatus
from agentic_runtime.factory import RuntimeConfig, StorageConfig, ToolsConfig, create_runtime
from agentic_runtime.tools import ToolCategory, ToolResult

from ._azure_real import build_caller as _build_caller
from ._azure_real import skip_marker as pytest_skip

pytestmark = pytest.mark.asyncio


def _runtime(tmp_path, caller, tools):
    return create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        tools=ToolsConfig(extras=list(tools)),
    ))


async def _run_foreground(runtime, prompt: str, description: str):
    task_id = await runtime.dispatch(RuntimeTask(prompt=prompt, description=description))
    rec = runtime._task_registry.get(task_id)
    await rec.asyncio_task
    return task_id, rec


def _tool_results(rec) -> list[dict]:
    return [e for e in rec.events if e["type"] == "tool_result"]


# ──────────────────────────────────────────────────────────────────────────────
# Tools deterministas con tokens únicos (el modelo NO puede adivinarlos)
# ──────────────────────────────────────────────────────────────────────────────

class LookupSecretTool:
    """Devuelve un token único asociado a una clave; el modelo solo puede obtenerlo
    llamando la tool (prueba que la salida se usó de verdad)."""

    name = "lookup_secret"
    description = "Devuelve el código secreto asociado a una clave dada."
    input_schema = {
        "type": "object",
        "properties": {"key": {"type": "string", "description": "La clave a consultar"}},
        "required": ["key"],
    }
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    def __init__(self, secret: str) -> None:
        self._secret = secret
        self.calls: list[dict] = []

    async def execute(self, input: dict, ctx) -> ToolResult:
        self.calls.append(input)
        return ToolResult(tool_name=self.name, output=f"El código para '{input.get('key')}' es {self._secret}")


class Step1Tool:
    """Entrega un token de un solo uso. El modelo debe llamarla antes de Step2."""

    name = "obtener_token"
    description = "Obtiene un token de acceso de un solo uso. Llámala sin argumentos."
    input_schema = {"type": "object", "properties": {}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    def __init__(self, token: str) -> None:
        self._token = token
        self.calls = 0

    async def execute(self, input: dict, ctx) -> ToolResult:
        self.calls += 1
        return ToolResult(tool_name=self.name, output=f"token={self._token}")


class Step2Tool:
    """Canjea el token del Step1 por el resultado final. Dependencia secuencial real."""

    name = "canjear_token"
    description = "Canjea un token (obtenido con obtener_token) y devuelve el resultado final."
    input_schema = {
        "type": "object",
        "properties": {"token": {"type": "string", "description": "El token de obtener_token"}},
        "required": ["token"],
    }
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    def __init__(self, expected_token: str, final_value: str) -> None:
        self._expected = expected_token
        self._final = final_value
        self.calls: list[dict] = []

    async def execute(self, input: dict, ctx) -> ToolResult:
        self.calls.append(input)
        if str(input.get("token")) == self._expected:
            return ToolResult(tool_name=self.name, output=f"resultado={self._final}")
        return ToolResult(tool_name=self.name, output="ERROR: token inválido")


# ──────────────────────────────────────────────────────────────────────────────
# 1. Foreground, multi-turno: una tool, el modelo consume su salida
# ──────────────────────────────────────────────────────────────────────────────

@pytest_skip
async def test_real_single_tool_use(tmp_path):
    secret = f"ZX-{uuid.uuid4().hex[:8].upper()}"
    tool = LookupSecretTool(secret)
    caller = _build_caller(
        "Eres un asistente. Cuando necesites un dato que no conoces, usa la herramienta "
        "disponible. Responde de forma concisa incluyendo el código exacto que obtengas."
    )
    runtime = _runtime(tmp_path, caller, (tool,))
    task_id, rec = await _run_foreground(
        runtime,
        "¿Cuál es el código secreto para la clave 'produccion'? Usa la herramienta.",
        "real-single-tool",
    )

    assert runtime.status(task_id) == TaskStatus.COMPLETED
    assert len(tool.calls) >= 1                      # la tool se despachó de verdad
    assert len(_tool_results(rec)) >= 1
    assert rec.turn_count >= 2                        # turno tool + turno respuesta
    assert secret in (runtime.result(task_id) or "")  # el modelo usó la salida real


# ──────────────────────────────────────────────────────────────────────────────
# 2. Foreground, varios turnos: dos tools con dependencia secuencial
# ──────────────────────────────────────────────────────────────────────────────

@pytest_skip
async def test_real_sequential_dependent_tools(tmp_path):
    token = f"TK-{uuid.uuid4().hex[:10]}"
    final = f"OK-{uuid.uuid4().hex[:8].upper()}"
    s1, s2 = Step1Tool(token), Step2Tool(token, final)
    caller = _build_caller(
        "Eres un asistente que sigue procesos paso a paso con herramientas. "
        "Primero obtén el token, luego canjéalo, y reporta el resultado final exacto."
    )
    runtime = _runtime(tmp_path, caller, (s1, s2))
    task_id, rec = await _run_foreground(
        runtime,
        "Necesito el resultado final del proceso: primero obtén un token y después "
        "canjéalo. Dime el resultado final.",
        "real-sequential",
    )

    assert runtime.status(task_id) == TaskStatus.COMPLETED
    assert s1.calls >= 1                              # llamó al paso 1
    assert len(s2.calls) >= 1                         # llamó al paso 2
    assert s2.calls[0].get("token") == token         # pasó el token REAL del paso 1
    assert len(_tool_results(rec)) >= 2              # dos despachos
    assert rec.turn_count >= 3                        # 2 tool turns + respuesta
    assert final in (runtime.result(task_id) or "")  # resultado dependiente correcto


# ──────────────────────────────────────────────────────────────────────────────
# 3. Foreground sin tools: turno único, texto real
# ──────────────────────────────────────────────────────────────────────────────

@pytest_skip
async def test_real_single_turn_text(tmp_path):
    caller = _build_caller("Responde con una sola palabra en minúsculas, sin puntuación.")
    runtime = _runtime(tmp_path, caller, ())
    task_id, rec = await _run_foreground(
        runtime,
        "Responde exactamente con la palabra: pong",
        "real-text",
    )
    assert runtime.status(task_id) == TaskStatus.COMPLETED
    assert "pong" in (runtime.result(task_id) or "").lower()
    assert rec.turn_count >= 1
