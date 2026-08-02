"""Tests para runtime/loop/AgentLoop — ciclo real LLM → tools → acumula."""
import asyncio
import pytest

from agentic_runtime.contracts.abort import AbortController

from agentic_runtime.loop import AgentLoop, BasicLoop
from agentic_runtime.loop.outcome import LoopEndReason
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.events import DoneEvent, ErrorEvent, TokenEvent, ToolCallEvent
from agentic_runtime.tools import ToolCategory, ToolRegistry, ToolResult
from agentic_runtime.tools.dispatcher import ToolDispatcher


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

def _make_caller(*events):
    """Crea un ModelCallerProtocol stub que emite los eventos dados."""
    class StubCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            async def _gen():
                for ev in events:
                    yield ev
            return _gen()
    return StubCaller()


class EchoTool:
    name = "echo"
    description = "Echoes input"
    input_schema: dict = {"type": "object", "properties": {"text": {"type": "string"}}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx) -> ToolResult:
        return ToolResult(tool_name=self.name, output=input.get("text", ""))


def _make_registry(*tools) -> ToolRegistry:
    reg = ToolRegistry()
    for t in tools:
        reg.register(t)
    return reg


def _make_ctx(stop: AbortController | None = None) -> ToolUseContext:
    return ToolUseContext(session_id="s1", stop=stop)


# ---------------------------------------------------------------------------
# Ciclo básico
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_loop_single_turn_no_tools():
    caller = _make_caller(TokenEvent(content="hello"), DoneEvent(stop_reason="stop"))
    reg = _make_registry()
    dispatcher = ToolDispatcher()

    loop = AgentLoop(model_caller=caller, tool_registry=reg, tool_dispatcher=dispatcher)
    ctx = _make_ctx()

    await loop.run("hola", ctx)

    roles = [m["role"] for m in ctx.messages]
    assert "user" in roles
    assert "assistant" in roles


@pytest.mark.asyncio
async def test_loop_accumulates_assistant_tokens():
    caller = _make_caller(
        TokenEvent(content="hel"),
        TokenEvent(content="lo"),
        DoneEvent(stop_reason="stop"),
    )
    reg = _make_registry()
    dispatcher = ToolDispatcher()

    loop = AgentLoop(model_caller=caller, tool_registry=reg, tool_dispatcher=dispatcher)
    ctx = _make_ctx()

    await loop.run("hola", ctx)

    assistant_msgs = [m for m in ctx.messages if m["role"] == "assistant"]
    assert any("hello" in m["content"] for m in assistant_msgs)


@pytest.mark.asyncio
async def test_loop_executes_tool_call():
    caller = _make_caller(
        ToolCallEvent(tool_name="echo", tool_input={"text": "mundo"}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    reg = _make_registry(EchoTool())
    dispatcher = ToolDispatcher()

    loop = AgentLoop(model_caller=caller, tool_registry=reg, tool_dispatcher=dispatcher)
    ctx = _make_ctx()

    await loop.run("usa echo", ctx)

    contents = [str(m.get("content", "")) for m in ctx.messages]
    assert any("mundo" in c for c in contents)


@pytest.mark.asyncio
async def test_loop_aborts_on_stop_event():
    stop = AbortController()
    stop.abort()

    called = []

    class TrackingCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            called.append(True)
            async def _gen():
                yield DoneEvent(stop_reason="stop")
            return _gen()

    reg = _make_registry()
    dispatcher = ToolDispatcher()
    loop = AgentLoop(model_caller=TrackingCaller(), tool_registry=reg, tool_dispatcher=dispatcher)

    await loop.run("hola", _make_ctx(stop=stop))

    assert called == [], "el modelo no debe llamarse si stop está seteado"


@pytest.mark.asyncio
async def test_loop_handles_error_event():
    """`H-L2` pagado: este test tenía por cuerpo `await loop.run(...)` y un comentario
    «no debe lanzar excepción» — **cero aserciones**. Un smoke test no dice si el error
    del modelo llega a alguna parte. Lo que el fuente promete (`agent_loop.py:389-394`)
    son tres efectos, y son los que se miden: el error entra al historial como turno del
    asistente, el outcome lo nombra, y el mensaje viaja en `detail`."""
    caller = _make_caller(ErrorEvent(message="LLM explotó"))
    loop = AgentLoop(
        model_caller=caller, tool_registry=_make_registry(), tool_dispatcher=ToolDispatcher(),
    )
    ctx = _make_ctx()

    outcome = await loop.run("hola", ctx)

    assert outcome.reason is LoopEndReason.MODEL_ERROR
    assert outcome.detail == "LLM explotó"
    assert ctx.messages[-1] == {"role": "assistant", "content": "[error: LLM explotó]"}
    assert outcome.aborted is False  # un error del modelo NO es un abort


# ---------------------------------------------------------------------------
# `H-L1`: abort A MITAD DE STREAM
#
# Los otros tres tests de abort cubren pre-run y frontera-de-vuelta. Éste cubre el
# tercer punto de lectura, que es el que el fuente declara decisivo
# (`agent_loop.py:347-380`): «el único punto de control que existe para el camino
# Azure/Responses», porque ese provider mira la señal DESPUÉS de terminar el stream.
# Sin este test, el corte a mitad no estaba probado en ninguna parte.
# ---------------------------------------------------------------------------

class _AbortingStream:
    """Stream que activa el abort a mitad y registra si le cerraron el generador."""

    def __init__(self, stop, events_tras_abort):
        self._stop = stop
        self._tras = events_tras_abort
        self.aclosed = False
        self.rendidos: list = []

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        yield TokenEvent(content="antes")
        self.rendidos.append("antes")
        self._stop.abort()  # el usuario corta justo aquí
        for ev in self._tras:
            self.rendidos.append(ev)
            yield ev

    async def aclose(self):
        self.aclosed = True


@pytest.mark.asyncio
async def test_abort_a_mitad_de_stream_corta_sin_registrar_ni_despachar():
    stop = AbortController()
    tool = EchoTool()
    dispatched: list = []

    class _SpyDispatcher(ToolDispatcher):
        async def dispatch(self, *, tool_name, tool_input, ctx):
            dispatched.append(tool_name)
            return await super().dispatch(tool_name=tool_name, tool_input=tool_input, ctx=ctx)

    stream = _AbortingStream(stop, [
        TokenEvent(content="DESPUES_DEL_ABORT"),
        ToolCallEvent(tool_name="echo", tool_input={"text": "x"}, call_id="c1"),
        DoneEvent(stop_reason="tool_calls"),
    ])

    class _StreamCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            return stream

    loop = AgentLoop(
        model_caller=_StreamCaller(),
        tool_registry=_make_registry(tool),
        tool_dispatcher=_SpyDispatcher(),
    )
    ctx = _make_ctx(stop=stop)

    outcome = await loop.run("trabaja", ctx)

    # (a) el loop nombra el corte, y lo nombra como abort
    assert outcome.reason is LoopEndReason.ABORTED_STREAMING
    assert outcome.aborted is True
    # (b) cerró el generador: el provider suelta la conexión en vez de seguir consumiendo
    assert stream.aclosed is True, "no se cerró el stream: la conexión queda colgando"
    # (c) lo posterior al abort no se acumuló: el turno parcial NO se registra
    assert not any("DESPUES_DEL_ABORT" in str(m.get("content", "")) for m in ctx.messages)
    assert not any(m.get("role") == "assistant" for m in ctx.messages), (
        "un turno abortado no dejó una respuesta, dejó un corte"
    )
    # (d) y sus tool calls NO se despachan
    assert dispatched == [], "se ejecutó una tool pedida por un turno que fue abortado"


@pytest.mark.asyncio
async def test_sin_abort_el_mismo_stream_se_consume_entero():
    """CONTROL POSITIVO de `H-L1`: mismo stream, misma tool, mismo dispatcher —
    sólo cambia que nadie aborta. Sin él, un loop que ignorase el stream entero
    dejaría verde el test de arriba por las razones equivocadas."""
    tool = EchoTool()
    dispatched: list = []

    class _SpyDispatcher(ToolDispatcher):
        async def dispatch(self, *, tool_name, tool_input, ctx):
            dispatched.append(tool_name)
            return await super().dispatch(tool_name=tool_name, tool_input=tool_input, ctx=ctx)

    loop = AgentLoop(
        model_caller=_make_caller(
            TokenEvent(content="antes"),
            TokenEvent(content="DESPUES_DEL_ABORT"),
            ToolCallEvent(tool_name="echo", tool_input={"text": "x"}, call_id="c1"),
            DoneEvent(stop_reason="stop"),
        ),
        tool_registry=_make_registry(tool),
        tool_dispatcher=_SpyDispatcher(),
    )
    ctx = _make_ctx(stop=AbortController())

    outcome = await loop.run("trabaja", ctx)

    assert outcome.reason is LoopEndReason.COMPLETED
    assert outcome.aborted is False
    assert any("DESPUES_DEL_ABORT" in str(m.get("content", "")) for m in ctx.messages)
    assert dispatched == ["echo"]


@pytest.mark.asyncio
async def test_abort_pre_run_y_su_reason():
    """`H-L3`: el abort previo tenía prueba de EFECTO (no se llama al modelo) pero
    nadie aseveraba el reason-code, que es lo que el integrador lee para decidir si
    reintenta o avisa (`outcome.py`)."""
    stop = AbortController()
    stop.abort()
    outcome = await AgentLoop(model_caller=_make_caller(DoneEvent(stop_reason="stop"))).run(
        "hola", _make_ctx(stop=stop),
    )
    assert outcome.reason is LoopEndReason.ABORTED_PRE_RUN
    assert outcome.aborted is True
    assert outcome.turn_count == 0  # no llegó a haber turno


@pytest.mark.asyncio
async def test_loop_multi_turn_tool_calls():
    """Dos rondas de tool calls antes del DoneEvent final."""
    turn = {"n": 0}

    class MultiTurnCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            turn["n"] += 1
            async def _gen():
                if turn["n"] == 1:
                    yield ToolCallEvent(tool_name="echo", tool_input={"text": "vuelta1"}, call_id="c1")
                    yield DoneEvent(stop_reason="tool_calls")
                else:
                    yield TokenEvent(content="listo")
                    yield DoneEvent(stop_reason="stop")
            return _gen()

    reg = _make_registry(EchoTool())
    dispatcher = ToolDispatcher()
    loop = AgentLoop(model_caller=MultiTurnCaller(), tool_registry=reg, tool_dispatcher=dispatcher)
    ctx = _make_ctx()

    await loop.run("ejecuta dos veces", ctx)

    assert turn["n"] == 2
    contents = " ".join(str(m.get("content", "")) for m in ctx.messages)
    assert "vuelta1" in contents


# ---------------------------------------------------------------------------
# Emisión a EventBus (observación en vivo)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_loop_emits_events_to_bus():
    from agentic_runtime.events import EventBus, ToolResultEvent

    caller = _make_caller(
        TokenEvent(content="hi"),
        ToolCallEvent(tool_name="echo", tool_input={"text": "x"}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    reg = _make_registry(EchoTool())
    dispatcher = ToolDispatcher()
    bus = EventBus()

    seen: list[str] = []

    def _rec(label):
        async def handler(e):
            seen.append(label)
        return handler

    bus.subscribe(TokenEvent, _rec("token"))
    bus.subscribe(ToolCallEvent, _rec("toolcall"))
    bus.subscribe(ToolResultEvent, _rec("toolresult"))
    bus.subscribe(DoneEvent, _rec("done"))

    loop = AgentLoop(
        model_caller=caller, tool_registry=reg,
        tool_dispatcher=dispatcher, event_bus=bus,
    )
    await loop.run("hola", _make_ctx())

    assert "token" in seen
    assert "toolcall" in seen
    assert "toolresult" in seen  # emitido por el loop tras el dispatch
    assert "done" in seen


# ---------------------------------------------------------------------------
# Corte de turno por tool (HITL multi-turno)
# ---------------------------------------------------------------------------

class _SuspendTool:
    """Tool HITL parametrizable por la señal. `ends_turn` viaja por el campo DECLARADO
    del contrato (`FIND-TOOL4/A24` pagado), no por monkeypatch sobre el resultado."""

    name = "suspend"
    description = "Ends the turn (HITL)"
    input_schema: dict = {"type": "object", "properties": {}}
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = False
    timeout_seconds = 5.0

    def __init__(self, ends_turn: bool = True) -> None:
        self._ends_turn = ends_turn

    async def execute(self, input: dict, ctx) -> ToolResult:
        return ToolResult(tool_name=self.name, output="awaiting", ends_turn=self._ends_turn)


def _counting_caller(calls: dict, *, max_tool_turns: int = 1):
    """Caller que pide `suspend` en los primeros `max_tool_turns` turnos y luego cierra.

    El tope importa para el CONTROL POSITIVO: sin él, la rama sin `ends_turn`
    tool-llamaría en bucle hasta `_MAX_TURNS` y el test mediría el techo de
    seguridad en vez de la re-entrada."""

    class CountingCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            calls["n"] += 1
            pedir_tool = calls["n"] <= max_tool_turns

            async def _gen():
                if pedir_tool:
                    yield ToolCallEvent(tool_name="suspend", tool_input={}, call_id=f"c{calls['n']}")
                    yield DoneEvent(stop_reason="tool_calls")
                else:
                    yield TokenEvent(content="ya está")
                    yield DoneEvent(stop_reason="stop")

            return _gen()

    return CountingCaller()


@pytest.mark.asyncio
async def test_tool_ends_turn_no_reinvoca_al_modelo():
    """Una tool con `ends_turn=True` corta el turno: el modelo NO se re-llama aunque el stop_reason
    sea 'tool_calls' (AskUserQuestion emite las preguntas y cede el control al usuario).

    Prueba de EFECTO, no de flag: se mide cuántas veces se llamó al modelo y con qué
    `LoopEndReason` cerró. Su discriminación la da el control positivo de abajo
    (`…_sin_la_senal_el_loop_reentra`): sin él, un loop roto que cortara SIEMPRE tras
    ejecutar tools dejaría este test verde igual.
    """
    calls = {"n": 0}
    loop = AgentLoop(
        model_caller=_counting_caller(calls),
        tool_registry=_make_registry(_SuspendTool(ends_turn=True)),
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _make_ctx()
    outcome = await loop.run("pregúntame", ctx)

    assert calls["n"] == 1, "el loop re-llamó al modelo pese a que la tool cedió el turno"
    assert ctx.turn_count == 1
    assert outcome.reason is LoopEndReason.ENDS_TURN


@pytest.mark.asyncio
async def test_tool_sin_la_senal_el_loop_reentra():
    """CONTROL POSITIVO del anterior: MISMO escenario, MISMA tool, MISMO caller —
    la única diferencia es la señal.

    Sin `ends_turn` el loop tiene que volver al modelo tras ejecutar la tool
    (`stop_reason == "tool_calls"`), y cerrar por `COMPLETED` cuando el modelo ya no
    pide nada. Es lo que hace que el test de arriba mida la SEÑAL y no la incapacidad
    del loop de dar una segunda vuelta.
    """
    calls = {"n": 0}
    loop = AgentLoop(
        model_caller=_counting_caller(calls),
        tool_registry=_make_registry(_SuspendTool(ends_turn=False)),
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _make_ctx()
    outcome = await loop.run("pregúntame", ctx)

    assert calls["n"] == 2, "el loop NO re-entró: cortaría igual con o sin la señal"
    assert ctx.turn_count == 2
    assert outcome.reason is LoopEndReason.COMPLETED
    # Y la segunda vuelta ocurrió DESPUÉS de que el resultado de la tool entrara al
    # historial: el modelo re-entra viendo lo que la tool devolvió, no a ciegas.
    roles = [m["role"] for m in ctx.messages]
    assert "tool" in roles and roles.index("tool") < len(roles) - 1


# ---------------------------------------------------------------------------
# Shim BasicLoop
# ---------------------------------------------------------------------------

def test_basic_loop_is_agent_loop():
    assert BasicLoop is AgentLoop
