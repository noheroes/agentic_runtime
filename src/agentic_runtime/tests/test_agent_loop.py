"""Tests para runtime/loop/AgentLoop — ciclo real LLM → tools → acumula."""
import asyncio
import logging

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
# `S1` enriquecida: `model_options` viaja al caller
# ---------------------------------------------------------------------------

class _KwargsCaller:
    """Registra los kwargs EXACTOS con que el loop llama al modelo."""

    def __init__(self) -> None:
        self.kwargs: dict = {}

    async def complete(self, messages, tools, **kw):
        self.kwargs = dict(kw)

        async def _gen():
            yield DoneEvent(stop_reason="stop")

        return _gen()


@pytest.mark.asyncio
async def test_model_options_llegan_al_caller_como_kwargs():
    """`S1` (`C2`): el integrador pide razonamiento/muestreo/techo y el runtime lo
    TRANSPORTA. La `metadata` es opaca (`ID-7`): el runtime no la lee, la pasa entera."""
    from agentic_runtime.models.protocol import ModelOptions

    caller = _KwargsCaller()
    loop = AgentLoop(model_caller=caller, model_options=ModelOptions(
        temperature=0.2, max_tokens=1024, metadata={"tenant": "acme"},
    ))
    await loop.run("hola", _make_ctx())

    assert caller.kwargs["temperature"] == 0.2
    assert caller.kwargs["max_tokens"] == 1024
    assert caller.kwargs["metadata"] == {"tenant": "acme"}


@pytest.mark.asyncio
async def test_lo_no_pedido_NO_viaja_como_None_explicito():
    """Control negativo, y es la mitad que importa: `as_kwargs()` promete pasar «sólo lo
    poblado» para que un caller de terceros que aún no adopte un kwarg no se rompa. Si el
    loop mandara `temperature=None`, ese caller reventaría con `TypeError` — y el test de
    arriba seguiría verde, porque sólo mira lo que sí se pidió."""
    from agentic_runtime.models.protocol import ModelOptions

    caller = _KwargsCaller()
    loop = AgentLoop(model_caller=caller, model_options=ModelOptions(temperature=0.2))
    await loop.run("hola", _make_ctx())

    assert "temperature" in caller.kwargs
    for ausente in ("max_tokens", "thinking", "effort", "output_format", "tool_choice", "metadata"):
        assert ausente not in caller.kwargs, f"{ausente} no se pidió: no debe viajar"
    # Y sin opciones ningunas, ninguna de las siete aparece.
    caller_pelado = _KwargsCaller()
    await AgentLoop(model_caller=caller_pelado).run("hola", _make_ctx())
    assert set(caller_pelado.kwargs) == {"stop", "model_id"}


# ---------------------------------------------------------------------------
# Rama «[no dispatcher]»: el loop sin dispatcher no se cuelga ni miente
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sin_dispatcher_la_tool_call_se_contesta_y_el_turno_sigue():
    """Un loop mal cableado (sin `tool_dispatcher`) recibe una tool call y **no puede**
    ejecutarla. Lo que no puede hacer es dejar el `tool_call_id` sin contestar: el
    siguiente turno iría al modelo con una llamada colgando, que muchos proveedores
    rechazan con 400. Se contesta con un marcador explícito y el loop continúa."""
    caller = _make_caller(
        ToolCallEvent(tool_name="echo", tool_input={"text": "x"}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    loop = AgentLoop(model_caller=caller, tool_registry=_make_registry(EchoTool()))
    ctx = _make_ctx()
    outcome = await loop.run("usa echo", ctx)

    tool_msgs = [m for m in ctx.messages if m["role"] == "tool"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0]["tool_call_id"] == "c1"
    assert tool_msgs[0]["content"] == "[no dispatcher]"
    assert outcome.reason is LoopEndReason.COMPLETED


# ---------------------------------------------------------------------------
# `context_modifier` del ToolResult: aplicación, reemplazo y excepción TRAGADA
# ---------------------------------------------------------------------------

def _tool_con_modifier(name: str, modifier):
    class _T:
        pass

    t = _T()
    t.name = name
    t.description = name
    t.input_schema = {"type": "object", "properties": {}}
    t.category = ToolCategory.UTILITY
    t.requires_permission = False
    t.safe_for_background = True
    t.timeout_seconds = 5.0

    async def _execute(input, ctx):
        return ToolResult(tool_name=name, output="ok", context_modifier=modifier)

    t.execute = _execute
    return t


@pytest.mark.asyncio
async def test_un_modifier_que_revienta_no_tumba_el_turno():
    """`agent_loop.py:462-465` traga la excepción del modifier a propósito. Que sea a
    propósito no lo hacía nadie evidente: sin este test, cambiar el `except` por una
    propagación (o al revés) no rompía nada.

    Lo aseverado es el EFECTO de tragarla: el resultado de la tool YA está en el
    historial cuando el modifier corre, así que dejar subir la excepción perdería un
    turno de trabajo ya hecho y dejaría el `tool_call_id` contestado a medias.
    """
    def _explota(ctx):
        raise RuntimeError("el modifier está roto")

    caller = _make_caller(
        ToolCallEvent(tool_name="rota", tool_input={}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_make_registry(_tool_con_modifier("rota", _explota)),
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _make_ctx()
    outcome = await loop.run("usa rota", ctx)

    assert outcome.reason is LoopEndReason.COMPLETED, "la excepción del modifier no aborta el turno"
    tool_msgs = [m for m in ctx.messages if m["role"] == "tool"]
    assert tool_msgs and tool_msgs[0]["content"] == "ok", "el trabajo ya hecho se conserva"


@pytest.mark.asyncio
async def test_el_ctx_que_el_modifier_devuelve_es_el_que_ve_la_tool_siguiente():
    """Convención declarada: «el modifier muta ctx in-place y lo retorna (no forka)», y el
    loop hace `ctx = modifier(ctx) or ctx`. El efecto observable es que lo que el modifier
    siembra lo ve la tool que se ejecuta DESPUÉS, en el mismo turno — si el loop
    descartara el retorno, la segunda tool vería el ctx viejo."""
    visto: list = []

    def _siembra(ctx):
        ctx.app_state.native["marca"] = "sembrada"
        return ctx

    espia = _tool_con_modifier("espia", None)

    async def _execute_espia(input, ctx):
        visto.append(ctx.app_state.native.get("marca"))
        return ToolResult(tool_name="espia", output="visto")

    espia.execute = _execute_espia

    caller = _make_caller(
        ToolCallEvent(tool_name="siembra", tool_input={}, call_id="c1"),
        ToolCallEvent(tool_name="espia", tool_input={}, call_id="c2"),
        DoneEvent(stop_reason="stop"),
    )
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_make_registry(_tool_con_modifier("siembra", _siembra), espia),
        tool_dispatcher=ToolDispatcher(),
    )
    await loop.run("siembra y espía", _make_ctx())

    assert visto == ["sembrada"]


@pytest.mark.asyncio
async def test_si_el_modifier_devuelve_OTRO_ctx_el_loop_se_queda_con_ese():
    """El test anterior no distingue `ctx = modifier(ctx) or ctx` de un `modifier(ctx)` a
    secas: con la convención in-place la marca aparece igual. Lo que sí discrimina es un
    modifier que **devuelve otro objeto** — si el loop tirara el retorno, la tool
    siguiente seguiría hablando con el ctx viejo. El loop declara soportarlo, y el `or
    ctx` de la misma línea declara tolerar un modifier que no devuelva nada."""
    visto: list = []
    nuevo_ctx = ToolUseContext(session_id="s1")
    nuevo_ctx.app_state.native["marca"] = "del-ctx-nuevo"

    def _forka(ctx):
        # Un fork bien portado arrastra el estado DEL TURNO; ver `FIND-LOOP-1` abajo
        # para lo que pasa cuando no lo hace.
        nuevo_ctx.tool_pool = ctx.tool_pool
        nuevo_ctx.messages = ctx.messages
        return nuevo_ctx

    espia = _tool_con_modifier("espia", None)

    async def _execute_espia(input, ctx):
        visto.append((ctx is nuevo_ctx, ctx.app_state.native.get("marca")))
        return ToolResult(tool_name="espia", output="visto")

    espia.execute = _execute_espia

    caller = _make_caller(
        ToolCallEvent(tool_name="forka", tool_input={}, call_id="c1"),
        ToolCallEvent(tool_name="espia", tool_input={}, call_id="c2"),
        DoneEvent(stop_reason="stop"),
    )
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_make_registry(_tool_con_modifier("forka", _forka), espia),
        tool_dispatcher=ToolDispatcher(),
    )
    await loop.run("forka y espía", _make_ctx())

    assert visto == [(True, "del-ctx-nuevo")]


@pytest.mark.asyncio
async def test_FIND_LOOP_1_un_fork_ingenuo_del_ctx_no_mata_las_tool_calls_restantes():
    """`FIND-LOOP-1` **PAGADO** (el test nació rojo midiendo la conducta contraria).

    El loop soporta que el modifier devuelva OTRO ctx (`ctx = modifier(ctx) or ctx`),
    pero `ctx.tool_pool` es estado **del turno** cuyo dueño es el loop (lo puebla en
    `_build_tool_pool`). Un modifier que forkaba sin arrastrarlo dejaba al dispatcher
    resolviendo contra un pool VACÍO: las tool calls que quedaban del mismo turno morían
    con «no encontrado en el tool pool» — y morían **en silencio**, como un resultado de
    tool más, no como un error de cableado.

    El canónico no tiene el agujero por construcción: su único modifier real deriva por
    spread (`SkillTool.ts:773-800`), así que un fork no puede dejar campos atrás. En B el
    ctx es un modelo con `default_factory` en casi todo, luego el fork parcial es válido
    y mudo. El loop repone ahora lo que él posee.
    """
    visto: list = []
    huerfano = ToolUseContext(session_id="s1")  # fork ingenuo: sin tool_pool del turno

    espia = _tool_con_modifier("espia", None)

    async def _execute_espia(input, ctx):
        visto.append(ctx is huerfano)
        return ToolResult(tool_name="espia", output="visto")

    espia.execute = _execute_espia

    caller = _make_caller(
        ToolCallEvent(tool_name="forka", tool_input={}, call_id="c1"),
        ToolCallEvent(tool_name="espia", tool_input={}, call_id="c2"),
        DoneEvent(stop_reason="stop"),
    )
    ctx = _make_ctx()
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_make_registry(_tool_con_modifier("forka", lambda c: huerfano), espia),
        tool_dispatcher=ToolDispatcher(),
    )
    await loop.run("forka y espía", ctx)

    # 1) la tool que quedaba del turno se ejecuta, y lo hace sobre el ctx que el
    #    modifier impuso — el arreglo repone el pool, no revierte el fork.
    assert visto == [True], "la tool siguiente al fork tiene que ejecutarse"
    # 2) y no queda ningún resultado-de-tool fallido haciéndose pasar por respuesta.
    fallidos = [m for m in huerfano.messages
                if m.get("role") == "tool" and "no encontrado en el tool pool" in m["content"]]
    assert fallidos == [], "el fallo silencioso era exactamente esto"
    # 3) control de que el pool repuesto es el del turno, no uno vacío recién nacido.
    assert huerfano.tool_pool is ctx.tool_pool


@pytest.mark.asyncio
async def test_FIND_LOOP_1_un_fork_que_pierde_otros_cables_deja_de_ser_silencioso(caplog):
    """Lo que el loop NO posee no se repone —`stop`/`event_queue`/`storage`/`fs` los
    cablea el integrador— pero perderlos deja de ser mudo, que era el adjetivo del
    hallazgo. Sin este aviso, un fork ingenuo seguiría dejando el turno sin señal de
    abort y sin cola de eventos sin que nada lo dijera."""
    huerfano = ToolUseContext(session_id="s1")

    caller = _make_caller(
        ToolCallEvent(tool_name="forka", tool_input={}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    ctx = _make_ctx()
    ctx.storage = object()  # cable del integrador, poblado en el ctx vivo
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_make_registry(_tool_con_modifier("forka", lambda c: huerfano)),
        tool_dispatcher=ToolDispatcher(),
    )
    with caplog.at_level(logging.WARNING, logger="agentic_runtime.loop.agent_loop"):
        await loop.run("forka", ctx)

    avisos = [r.getMessage() for r in caplog.records if "no arrastra" in r.getMessage()]
    assert len(avisos) == 1, f"un aviso y sólo uno; hubo {len(avisos)}"
    assert "storage" in avisos[0], "cable en `None`: el caso obvio"
    # …y el caso que hace invisible la pérdida: el fork no deja el campo en `None`, lo deja
    # en su `default_factory`. Un historial vacío frente a uno poblado también es pérdida.
    assert "messages" in avisos[0], "contenedor en su default: la mitad que no se ve"
    assert "forka" in avisos[0], "el aviso tiene que nombrar la tool culpable"
    # control negativo: el campo que SÍ se repone no puede aparecer como perdido.
    assert "tool_pool" not in avisos[0]


@pytest.mark.asyncio
async def test_control_negativo_sin_modifier_la_marca_no_aparece():
    """Si la marca apareciese igual sin modifier, el test de arriba no discriminaría."""
    visto: list = []

    espia = _tool_con_modifier("espia", None)

    async def _execute_espia(input, ctx):
        visto.append(ctx.app_state.native.get("marca"))
        return ToolResult(tool_name="espia", output="visto")

    espia.execute = _execute_espia

    caller = _make_caller(
        ToolCallEvent(tool_name="espia", tool_input={}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )
    loop = AgentLoop(
        model_caller=caller, tool_registry=_make_registry(espia),
        tool_dispatcher=ToolDispatcher(),
    )
    await loop.run("espía", _make_ctx())

    assert visto == [None]


# ---------------------------------------------------------------------------
# Shim BasicLoop
# ---------------------------------------------------------------------------

def test_basic_loop_is_agent_loop():
    assert BasicLoop is AgentLoop
