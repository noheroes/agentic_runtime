"""E2E real COMPLEJO vía la PRIMITIVA pública de stream del runtime ensamblado.

Versión anterior manejaba `AgentLoop` a mano para tener handle del bus (la API pública no
exponía el stream). Ahora el runtime expone `dispatch(on_event=...)` / `stream(...)`: este
test ejerce el runtime COMPLETO (`create_runtime()`) y consume el stream SSE por la primitiva,
confirmando que opera igual que la versión hand-driven.

Escenario: procedimiento encadenado de 3 herramientas dependientes (listar → leer → enviar),
con tokens únicos no adivinables, de modo que el éxito solo es posible usando de verdad la
salida de cada paso como entrada del siguiente.

Verifica:
  - éxito funcional: cadena de tools completa, acuse final correcto;
  - primitiva SSE: el stream surface Token/ToolCall/ToolResult/Done en orden;
  - coherencia stream↔estado: el texto de los TokenEvent contiene el acuse final;
  - integridad del SSE: cada ToolResultEvent referencia un ToolCallEvent previo;
  - completitud/coherencia del CONTEXTO PERSISTIDO: todo tool_call tiene su mensaje tool;
  - valor del log como herramienta de depuración: traza por turno y por dispatch.
"""
from __future__ import annotations

import json
import logging
import uuid

import pytest

from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.events.event_types import (
    DoneEvent,
    ErrorEvent,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from agentic_runtime.execution.tasks.status import TaskStatus
from agentic_runtime.factory import RuntimeConfig, StorageConfig, ToolsConfig, create_runtime
from agentic_runtime.tools import ToolCategory, ToolResult

from ._azure_real import build_caller
from ._azure_real import skip_marker as pytest_skip

pytestmark = pytest.mark.asyncio


# ──────────────────────────────────────────────────────────────────────────────
# Herramientas encadenadas (cada paso depende de la salida del anterior)
# ──────────────────────────────────────────────────────────────────────────────

class ListDocumentsTool:
    name = "list_documents"
    description = "Lista los documentos disponibles. Sin argumentos."
    input_schema = {"type": "object", "properties": {}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, input: dict, ctx) -> ToolResult:
        self.calls += 1
        return ToolResult(tool_name=self.name, output="documentos: reporte.txt, notas.txt")


class ReadDocumentTool:
    name = "read_document"
    description = "Lee el contenido de un documento por nombre."
    input_schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    def __init__(self, code: str) -> None:
        self._code = code
        self.calls: list[dict] = []

    async def execute(self, input: dict, ctx) -> ToolResult:
        self.calls.append(input)
        if str(input.get("name")) == "reporte.txt":
            return ToolResult(
                tool_name=self.name,
                output=f"Informe trimestral.\nIncidencias resueltas.\nCODIGO-INTERNO: {self._code}",
            )
        return ToolResult(tool_name=self.name, output="documento vacío")


class SubmitCodeTool:
    name = "submit_code"
    description = "Envía el CODIGO-INTERNO extraído y devuelve el acuse oficial."
    input_schema = {
        "type": "object",
        "properties": {"code": {"type": "string"}},
        "required": ["code"],
    }
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    def __init__(self, expected_code: str, ack: str) -> None:
        self._expected = expected_code
        self._ack = ack
        self.calls: list[dict] = []

    async def execute(self, input: dict, ctx) -> ToolResult:
        self.calls.append(input)
        if str(input.get("code")) == self._expected:
            return ToolResult(tool_name=self.name, output=f"VALIDADO. Acuse: {self._ack}")
        return ToolResult(tool_name=self.name, output="RECHAZADO: código no coincide")


# ──────────────────────────────────────────────────────────────────────────────
# Captura del stream SSE (vía la primitiva on_event) y del log
# ──────────────────────────────────────────────────────────────────────────────

class StreamCapture:
    """Sink para `dispatch(on_event=...)`: guarda los eventos en orden de emisión.

    Es lo que un transporte SSE serializaría hacia el frontend.
    """

    def __init__(self) -> None:
        self.events: list = []

    async def sink(self, event) -> None:
        self.events.append(event)

    def of(self, cls) -> list:
        return [e for e in self.events if isinstance(e, cls)]

    def streamed_text(self) -> str:
        return "".join(e.content for e in self.of(TokenEvent))


class LogCapture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest_skip
async def test_real_complex_chain_via_primitive(tmp_path):
    code = f"CI-{uuid.uuid4().hex[:8].upper()}"
    ack = f"ACK-{uuid.uuid4().hex[:10].upper()}"
    t_list, t_read, t_submit = ListDocumentsTool(), ReadDocumentTool(code), SubmitCodeTool(code, ack)

    caller = build_caller(
        "Eres un agente que ejecuta procedimientos paso a paso usando herramientas. "
        "Nunca inventes datos: si necesitas un valor, obtenlo con la herramienta adecuada. "
        "Sigue el orden indicado y reporta al final el acuse EXACTO que recibas."
    )
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        tools=ToolsConfig(extras=[t_list, t_read, t_submit]),
    ))

    cap = StreamCapture()
    logcap = LogCapture()
    rt_logger = logging.getLogger("agentic_runtime")
    prev_level = rt_logger.level
    rt_logger.setLevel(logging.DEBUG)
    rt_logger.addHandler(logcap)

    prompt = (
        "Procedimiento: (1) lista los documentos, (2) abre 'reporte.txt', "
        "(3) extrae el CODIGO-INTERNO que contiene, (4) envíalo con submit_code, "
        "(5) dime el acuse exacto que recibas."
    )
    task = RuntimeTask(prompt=prompt, description="cmplx", owner_id="user-cmplx")
    try:
        # Primitiva pública: dispatch con suscripción al stream en vivo + task_id para control.
        task_id = await runtime.dispatch(task, on_event=cap.sink)
        rec = runtime._task_registry.get(task_id)
        await rec.asyncio_task
    finally:
        rt_logger.removeHandler(logcap)
        rt_logger.setLevel(prev_level)

    final_text = runtime.result(task_id) or ""
    persisted = await _load_persisted_messages(runtime, "user-cmplx")

    _dump_evidence(cap, rec, persisted, logcap, final_text, code, ack)

    # ── 1. Éxito funcional ──────────────────────────────────────────────────────
    assert runtime.status(task_id) == TaskStatus.COMPLETED
    assert t_list.calls >= 1, "no listó documentos"
    assert any(c.get("name") == "reporte.txt" for c in t_read.calls), "no leyó reporte.txt"
    assert any(c.get("code") == code for c in t_submit.calls), "no envió el código real extraído"
    assert ack in final_text, "el acuse final no proviene de la herramienta"

    # ── 2. Multi-turno real ─────────────────────────────────────────────────────
    assert rec.turn_count >= 3, f"esperaba ≥3 turnos, hubo {rec.turn_count}"

    # ── 3. Primitiva SSE: surface tokens (rec.events NO los captura) + tool/done ─
    assert cap.of(TokenEvent), "el stream no surface TokenEvents"
    assert len(cap.of(ToolCallEvent)) >= 3
    assert len(cap.of(ToolResultEvent)) >= 3
    assert cap.of(DoneEvent), "el stream no emitió DoneEvent de cierre"
    assert not cap.of(ErrorEvent)

    # ── 4. Integridad del SSE: cada tool_result referencia un tool_call previo ──
    seen: set[str] = set()
    for ev in cap.events:
        if isinstance(ev, ToolCallEvent):
            seen.add(ev.call_id)
        elif isinstance(ev, ToolResultEvent):
            assert ev.call_id in seen, "tool_result sin tool_call previo en el stream"

    # ── 5. Coherencia stream↔estado ─────────────────────────────────────────────
    assert ack in cap.streamed_text(), "el acuse no viajó por el stream de tokens"

    # ── 6. Completitud/coherencia del CONTEXTO persistido ───────────────────────
    _assert_context_coherent(persisted)

    # ── 7. Valor del log: traza accionable por turno + por dispatch ─────────────
    msgs = [r.getMessage() for r in logcap.records]
    invocaciones = [m for m in msgs if "invocando modelo" in m]
    dispatches = [m for m in msgs if "tool " in m and " -> " in m]
    assert len(invocaciones) >= 3, f"el log no traza cada turno: {msgs}"
    assert len(dispatches) >= 3, f"el log no traza cada dispatch: {msgs}"
    assert any(code in m for m in dispatches), "el log no permite seguir el dato real entre pasos"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

async def _load_persisted_messages(runtime, owner_id: str) -> list:
    """Lee el transcript que el runtime persistió en storage (estado real, no in-memory)."""
    keys = await runtime._storage.list_prefix(f"{owner_id}/")
    session_keys = [k for k in keys if k.endswith("/session.json")]
    assert session_keys, f"no se persistió la sesión: {keys}"
    raw = await runtime._storage.download(session_keys[0])
    return json.loads(raw)["messages"]


def _assert_context_coherent(messages: list) -> None:
    """El contexto persistido debe ser un transcript bien formado y autoexplicativo."""
    assert messages, "contexto vacío"
    assert messages[0]["role"] == "user", "el contexto no abre con el prompt del usuario"

    requested: list[str] = []
    for m in messages:
        if m.get("role") == "assistant":
            for tc in m.get("tool_calls") or []:
                requested.append(tc["id"])
    answered = {m.get("tool_call_id") for m in messages if m.get("role") == "tool"}
    for cid in requested:
        assert cid in answered, f"tool_call {cid} sin resultado en el contexto (hueco)"

    assert messages[-1]["role"] == "assistant", "el contexto no cierra con respuesta del assistant"
    assert messages[-1].get("content"), "la respuesta final del assistant está vacía"


def _dump_evidence(cap, rec, persisted, logcap, final_text, code, ack) -> None:
    print("\n" + "=" * 72)
    print("EVIDENCIA E2E REAL COMPLEJO — vía primitiva runtime.dispatch(on_event)")
    print("=" * 72)
    print(f"code={code}  ack={ack}  turnos={rec.turn_count}  status={rec.status.name}")
    print(f"\n── SSE stream ({len(cap.events)} eventos) ──")
    toks = 0
    for ev in cap.events:
        if isinstance(ev, TokenEvent):
            toks += 1
            continue
        print(f"  {type(ev).__name__:<16} {_fmt_event(ev)}")
    print(f"  (+{toks} TokenEvent; texto reconstruido: {cap.streamed_text()!r})")
    print(f"\n── Contexto persistido ({len(persisted)} mensajes) ──")
    for i, m in enumerate(persisted):
        tcs = m.get("tool_calls")
        extra = ""
        if tcs:
            extra = f" tool_calls={[t['function']['name'] for t in tcs]}"
        elif m.get("role") == "tool":
            extra = f" (id={m.get('tool_call_id')})"
        print(f"  [{i}] {m.get('role')}{extra}: {str(m.get('content', ''))[:80]!r}")
    print(f"\n── Log ({len(logcap.records)} registros) ──")
    for r in logcap.records:
        print(f"  {r.levelname:<7} {r.getMessage()[:100]}")
    print(f"\nRespuesta final: {final_text!r}")
    print("=" * 72)


def _fmt_event(ev) -> str:
    if isinstance(ev, ToolCallEvent):
        return f"{ev.tool_name}({ev.tool_input}) id={ev.call_id[:24]}…"
    if isinstance(ev, ToolResultEvent):
        return f"id={ev.call_id[:24]}… -> {ev.result[:50]!r}"
    if isinstance(ev, DoneEvent):
        return f"stop_reason={ev.stop_reason}"
    if isinstance(ev, ErrorEvent):
        return f"message={ev.message}"
    return str(ev)
