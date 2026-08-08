"""
Homologación · subsistema 02 · loop.

Evidencia sintética (fakes) + e2e real del `AgentLoop` contra el ciclo canónico
`query()` / `queryLoop()` (query.ts), `handleStopHooks` (query/stopHooks.ts),
`checkTokenBudget` (query/tokenBudget.ts) y la resolución de modelo/fallback.

Los tests que PASAN codifican el comportamiento ya homologado del turno agente:
inserción del prompt, multi-turno hasta agotar tool_calls, gate PreToolUse
(≡ canUseTool: deny + updatedInput), ends_turn (HITL), inyección de recall como
`<system-reminder>` con dedup, restricción de tools de subagente y techo de turnos.

Los `xfail(strict=True)` codifican el comportamiento HOMOLOGADO AUSENTE — su fallo
ES la evidencia de los gaps documentados en HOMOLOGATION/02-loop.md (GAP-L1..L5).
Primera pasada: solo documentar — no se ajusta el runtime para hacerlos pasar.
"""
from __future__ import annotations

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.abort import AbortController
from agentic_runtime.contracts.user_input import ProcessedInput
from agentic_runtime.events import DoneEvent, ErrorEvent, TokenEvent, ToolCallEvent
from agentic_runtime.events.event_types import MessageEvent, TurnStartEvent
from agentic_runtime.hooks import HookEvent
from agentic_runtime.hooks.protocol import HookDecision
from agentic_runtime.hooks.runner import HookRunner
from agentic_runtime.loop.agent_loop import AgentLoop
from agentic_runtime.loop.outcome import LoopEndReason
from agentic_runtime.tools import ToolCategory, ToolResult
from agentic_runtime.tools.dispatcher import ToolDispatcher
from agentic_runtime.tools.pool import ToolPool
from agentic_runtime.tools.registry import ToolRegistry

# asyncio_mode = "auto" (pyproject): las corrutinas de test se ejecutan sin marca.


# ──────────────────────────────────────────────────────────────────────────────
# Dobles deterministas
# ──────────────────────────────────────────────────────────────────────────────

class ScriptedCaller:
    """Caller faux: reproduce un guion fijo de eventos por turno.

    Acepta los kwargs que el loop pasa condicionalmente (`system_sections`,
    `system_override`) para poder afirmar sobre lo que expone al modelo.
    """

    def __init__(self, script: list[list]) -> None:
        self._script = script
        self._turn = 0
        self.seen_tools: list[list[str]] = []
        self.seen_messages: list[list] = []
        self.seen_system_sections: list = []
        self.seen_system_override: list = []

    async def complete(
        self, messages, tools, *, stop=None, model_id="",
        system_sections=None, system_override=None,
    ):
        self.seen_tools.append([t["name"] for t in tools])
        self.seen_messages.append(list(messages))
        self.seen_system_sections.append(system_sections)
        self.seen_system_override.append(system_override)
        events = (
            self._script[self._turn]
            if self._turn < len(self._script)
            else [DoneEvent(stop_reason="stop")]
        )
        self._turn += 1

        async def _gen():
            for ev in events:
                yield ev
        return _gen()


class RecordingSink:
    """Sink que registra CADA HookEvent que el runner dispara."""

    def __init__(self) -> None:
        self.events: list[HookEvent] = []

    async def handle(self, event: HookEvent, payload: dict) -> None:
        self.events.append(event)


class RecordingTool:
    """Tool nativa que registra sus ejecuciones e inputs. Sin permiso requerido
    para que el único gate observable sea el hook PreToolUse."""

    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0
    input_schema: dict = {"type": "object", "properties": {"text": {"type": "string"}}}  # noqa: RUF012

    def __init__(self, name: str = "echo") -> None:
        self.name = name
        self.description = "Devuelve el texto recibido; registra la llamada"
        self.calls: list[dict] = []

    async def execute(self, input: dict, ctx) -> ToolResult:
        self.calls.append(dict(input))
        return ToolResult(tool_name=self.name, output=input.get("text", ""))


class UnsafeTool(RecordingTool):
    """Tool NO apta para background (kind subagente unattended la excluye)."""
    safe_for_background = False


class StopSettingTool(RecordingTool):
    """Tool que activa ctx.stop al ejecutarse (para probar abort entre turnos)."""

    async def execute(self, input: dict, ctx) -> ToolResult:
        self.calls.append(dict(input))
        if ctx.stop is not None:
            ctx.stop.abort()
        return ToolResult(tool_name=self.name, output="stopped")


class FakeCapabilityManager:
    """CapabilityManager mínimo: aporta pool, secciones de system prompt y recall."""

    def __init__(self, *, recall: list[dict] | None = None, sections: list[str] | None = None) -> None:
        self._recall = recall or []
        self._sections = sections or []

    def build_tool_pool(self, native, ctx) -> ToolPool:
        return ToolPool(native_tools=list(native))

    def system_prompt_sections(self, ctx) -> list[str]:
        return list(self._sections)

    def active_context(self, ctx) -> list[dict]:
        return list(self._recall)

    def catalog(self, ctx) -> list:
        # Miembro del contrato (`capabilities/contracts.py:76`), no un extra: el doble lo
        # omitía porque nadie se lo pedía todavía. El loop lo consume desde
        # `_announce_skill_listing`, así que un doble sin `catalog` es un doble incompleto
        # — misma clase de `H-L4` que los xfail que aseveraban sobre `_FakeTool`.
        return []


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _ctx(**kw) -> ToolUseContext:
    return ToolUseContext(session_id="loop-homolog", **kw)


def _registry(*tools) -> ToolRegistry:
    reg = ToolRegistry()
    for t in tools:
        reg.register(t)
    return reg


def _tool_call_turn(name: str, text: str, call_id: str) -> list:
    return [
        ToolCallEvent(tool_name=name, tool_input={"text": text}, call_id=call_id),
        DoneEvent(stop_reason="tool_calls"),
    ]


# ══════════════════════════════════════════════════════════════════════════════
# PARTE A · comportamiento homologado (tests que PASAN)
# ══════════════════════════════════════════════════════════════════════════════

async def test_loop_inserts_prompt_and_ends_single_turn_without_tools():
    """Un turno sin tool_calls: el prompt entra como user y el loop cierra."""
    caller = ScriptedCaller([[TokenEvent(content="hola"), DoneEvent(stop_reason="stop")]])
    loop = AgentLoop(model_caller=caller)
    ctx = _ctx()
    await loop.run("saluda", ctx)

    assert ctx.turn_count == 1
    assert ctx.messages[0] == {"role": "user", "content": "saluda"}
    assert any(m["role"] == "assistant" and m["content"] == "hola" for m in ctx.messages)
    assert len(caller.seen_messages) == 1


async def test_loop_drives_multi_turn_until_no_tool_calls():
    """Multi-turno: tras ejecutar la tool el resultado reingresa como contexto y
    el loop re-llama al modelo hasta que un DoneEvent no pide tool_calls."""
    tool = RecordingTool()
    caller = ScriptedCaller([
        _tool_call_turn("echo", "PONG", "c1"),
        [TokenEvent(content="terminado"), DoneEvent(stop_reason="stop")],
    ])
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_registry(tool),
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _ctx()
    await loop.run("usa echo", ctx)

    assert ctx.turn_count == 2
    assert tool.calls == [{"text": "PONG"}]
    # El tool result reingresó como rol tool en el 2º turno.
    assert any(m["role"] == "tool" and m["content"] == "PONG" for m in ctx.messages)
    assert [m["role"] for m in caller.seen_messages[1] if m["role"] == "tool"] == ["tool"]


async def test_loop_pretooluse_block_denies_without_executing():
    """Gate PreToolUse (≡ canUseTool deny): block → no ejecuta, reingresa denegación."""
    tool = RecordingTool()
    runner = HookRunner()

    async def deny(event, payload):
        return HookDecision.blocked("bloqueado por política")

    runner.register(HookEvent.PRE_TOOL_USE, deny)
    caller = ScriptedCaller([
        _tool_call_turn("echo", "X", "c1"),
        [DoneEvent(stop_reason="stop")],
    ])
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_registry(tool),
        tool_dispatcher=ToolDispatcher(),
        hook_runner=runner,
    )
    ctx = _ctx()
    await loop.run("usa echo", ctx)

    assert tool.calls == []  # jamás se ejecutó
    assert any(
        m["role"] == "tool" and "bloqueado por política" in m["content"]
        for m in ctx.messages
    )


async def test_loop_pretooluse_modified_input_replaces_input():
    """Gate PreToolUse (≡ canUseTool updatedInput): modified_input reemplaza el input."""
    tool = RecordingTool()
    runner = HookRunner()

    async def rewrite(event, payload):
        return HookDecision(modified_input={"text": "REESCRITO"})

    runner.register(HookEvent.PRE_TOOL_USE, rewrite)
    caller = ScriptedCaller([
        _tool_call_turn("echo", "ORIGINAL", "c1"),
        [DoneEvent(stop_reason="stop")],
    ])
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_registry(tool),
        tool_dispatcher=ToolDispatcher(),
        hook_runner=runner,
    )
    ctx = _ctx()
    await loop.run("usa echo", ctx)

    assert tool.calls == [{"text": "REESCRITO"}]


async def test_loop_tool_result_ends_turn_stops_reprompt():
    """ends_turn (HITL multi-turno, p. ej. AskUserQuestion): una tool puede cerrar
    el turno tras ejecutarse; el loop NO re-llama al modelo aunque hubo tool_calls."""

    class AskTool(RecordingTool):
        async def execute(self, input: dict, ctx) -> ToolResult:
            self.calls.append(dict(input))
            result = ToolResult(tool_name=self.name, output="pregunta emitida")
            result.ends_turn = True  # type: ignore[attr-defined]
            return result

    tool = AskTool(name="ask")
    caller = ScriptedCaller([
        _tool_call_turn("ask", "?", "c1"),
        [TokenEvent(content="NO_DEBERIA_LLEGAR"), DoneEvent(stop_reason="stop")],
    ])
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_registry(tool),
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _ctx()
    await loop.run("pregunta", ctx)

    assert ctx.turn_count == 1  # el turno cerró; no hubo re-prompt
    assert len(caller.seen_messages) == 1
    assert not any("NO_DEBERIA_LLEGAR" in str(m.get("content", "")) for m in ctx.messages)


async def test_loop_injects_recall_as_system_reminder_with_dedup():
    """Recall del manager rendido como role:user en `<system-reminder>`, deduplicado
    contra la historia ya presente (espejo collectSurfacedMemories)."""
    tool = RecordingTool()
    caps = FakeCapabilityManager(recall=[{"role": "system", "content": "MEMORIA_X"}])
    caller = ScriptedCaller([
        _tool_call_turn("echo", "a", "c1"),  # turno 1 inyecta
        [DoneEvent(stop_reason="stop")],      # turno 2 debe deduplicar
    ])
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_registry(tool),
        tool_dispatcher=ToolDispatcher(),
        capability_manager=caps,
    )
    ctx = _ctx()
    await loop.run("trabaja", ctx)

    reminders = [
        m for m in ctx.messages
        if m["role"] == "user" and "<system-reminder>" in m["content"] and "MEMORIA_X" in m["content"]
    ]
    assert len(reminders) == 1  # inyectado una sola vez pese a dos turnos


async def test_loop_subagent_pool_filtered_to_background():
    """Subagente unattended (is_subagent): el pool se filtra a safe_for_background."""
    safe, unsafe = RecordingTool("safe"), UnsafeTool("unsafe")
    caller = ScriptedCaller([[DoneEvent(stop_reason="stop")]])
    loop = AgentLoop(model_caller=caller, tool_registry=_registry(safe, unsafe))
    ctx = _ctx(is_subagent=True)
    await loop.run("x", ctx)

    exposed = caller.seen_tools[0]
    assert "safe" in exposed
    assert "unsafe" not in exposed


async def test_loop_agent_allowed_tools_restricts_pool():
    """Subagente especializado: agent_allowed_tools restringe el pool anunciado
    (espejo resolveAgentTools)."""
    echo, other = RecordingTool("echo"), RecordingTool("other")
    caller = ScriptedCaller([[DoneEvent(stop_reason="stop")]])
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_registry(echo, other),
        agent_allowed_tools=("echo",),
    )
    await loop.run("x", _ctx())

    assert caller.seen_tools[0] == ["echo"]


async def test_loop_agent_system_prompt_override_passed_to_caller():
    """system_prompt_override (subagent_type) llega al caller como system_override;
    `""` = heredar el base (no se pasa el kwarg)."""
    caller = ScriptedCaller([[DoneEvent(stop_reason="stop")]])
    loop = AgentLoop(model_caller=caller, system_prompt_override="ERES_UN_SUBAGENTE")
    await loop.run("x", _ctx())
    assert caller.seen_system_override[0] == "ERES_UN_SUBAGENTE"

    caller2 = ScriptedCaller([[DoneEvent(stop_reason="stop")]])
    loop2 = AgentLoop(model_caller=caller2)  # sin override
    await loop2.run("x", _ctx())
    assert caller2.seen_system_override[0] is None


async def test_loop_abort_before_start_makes_no_model_call():
    """ctx.stop activo antes de empezar → el loop no llama al modelo."""
    caller = ScriptedCaller([[DoneEvent(stop_reason="stop")]])
    loop = AgentLoop(model_caller=caller)
    stop = AbortController()
    stop.abort()
    await loop.run("x", _ctx(stop=stop))
    assert caller.seen_messages == []


async def test_loop_abort_between_turns_stops_reprompt():
    """Abort entre turnos: si ctx.stop se activa durante los tools, el loop no
    re-llama al modelo en el turno siguiente (chequeo al tope del bucle)."""
    tool = StopSettingTool("stopper")
    caller = ScriptedCaller([
        _tool_call_turn("stopper", "x", "c1"),
        [TokenEvent(content="NO_DEBERIA"), DoneEvent(stop_reason="stop")],
    ])
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_registry(tool),
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _ctx(stop=AbortController())
    outcome = await loop.run("trabaja", ctx)

    assert len(caller.seen_messages) == 1  # solo el 1er turno llegó al modelo
    assert tool.calls == [{"text": "x"}]
    # `H-L3`: el corte tiene NOMBRE, y es el de la frontera de vuelta — no el del
    # corte a mitad de stream ni el pre-run. El integrador decide por este código.
    assert outcome.reason is LoopEndReason.ABORTED_TOOLS
    assert outcome.aborted is True


async def test_loop_max_turns_ceiling_bounds_runaway():
    """Techo de seguridad `_MAX_TURNS`: un modelo que siempre pide tool_calls no
    hace loop infinito — el bucle corta en 50 turnos."""
    from agentic_runtime.loop.agent_loop import _MAX_TURNS

    tool = RecordingTool()
    # Guion que SIEMPRE pide tool_calls (ScriptedCaller repite DoneEvent 'stop'
    # al agotarse, pero damos margen > _MAX_TURNS con guion cíclico).
    caller = ScriptedCaller([_tool_call_turn("echo", "x", f"c{i}") for i in range(_MAX_TURNS + 5)])
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_registry(tool),
        tool_dispatcher=ToolDispatcher(),
    )
    ctx = _ctx()
    outcome = await loop.run("loop", ctx)

    assert ctx.turn_count == _MAX_TURNS  # cortó en el techo, no siguió
    # `H-L3`: agotar el techo no es «completado». El canónico lo distingue con su
    # propio reason-code y adjunta el tope (`query.ts:1705-1711`); B también, y hasta
    # ahora nadie lo aseveraba — un loop que cerrara por COMPLETED pasaba igual.
    assert outcome.reason is LoopEndReason.MAX_TURNS
    assert outcome.detail == str(_MAX_TURNS)
    assert outcome.aborted is False  # agotar vueltas no es un abort


# ══════════════════════════════════════════════════════════════════════════════
# PARTE B · gaps de homologación (xfail strict = evidencia del gap)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.xfail(
    strict=True,
    reason="GAP-L1: el loop no dispara el hook Stop/SubagentStop al cerrar el turno "
    "(canónico: handleStopHooks). Solo PRE_TOOL_USE se dispara dentro del loop. "
    "Ver 02-loop.md.",
)
async def test_loop_fires_stop_hook_at_turn_end():
    """Homologado: al terminar el turno (sin tool_calls) el loop corre los Stop
    hooks (extract-memories, prevent-continuation, teammate idle…)."""
    sink = RecordingSink()
    runner = HookRunner()
    runner.register_sink(sink)  # todos los eventos
    caller = ScriptedCaller([[TokenEvent(content="fin"), DoneEvent(stop_reason="stop")]])
    loop = AgentLoop(model_caller=caller, hook_runner=runner)
    await loop.run("x", _ctx())

    assert HookEvent.STOP in sink.events


@pytest.mark.xfail(
    strict=True,
    reason="GAP-L1b: el loop no dispara PostToolUse tras ejecutar una tool "
    "(canónico: post-sampling/post-tool hooks). Ver 02-loop.md.",
)
async def test_loop_fires_post_tool_use_hook():
    """Homologado: tras cada dispatch de tool el loop corre PostToolUse."""
    sink = RecordingSink()
    runner = HookRunner()
    runner.register_sink(sink)
    tool = RecordingTool()
    caller = ScriptedCaller([
        _tool_call_turn("echo", "x", "c1"),
        [DoneEvent(stop_reason="stop")],
    ])
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_registry(tool),
        tool_dispatcher=ToolDispatcher(),
        hook_runner=runner,
    )
    await loop.run("x", _ctx())

    assert HookEvent.POST_TOOL_USE in sink.events


async def test_loop_accepts_configurable_max_turns():
    """`GAP-L2` pagado por `C4`: `maxTurns` es del consumidor, no una constante.

    Y se comprueba **corriendo**, no con `inspect.signature`: la versión anterior de
    este test aseveraba que el parámetro existía en la firma, que es exactamente el
    modo de fallo de `L09` (existir ≠ estar cableado). Aquí el tope tiene que
    **morder**: 3 vueltas y ni una más, con su reason-code.
    """
    tool = RecordingTool()
    caller = ScriptedCaller([_tool_call_turn("echo", "x", f"c{i}") for i in range(20)])
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_registry(tool),
        tool_dispatcher=ToolDispatcher(),
        max_turns=3,
    )
    ctx = _ctx()
    outcome = await loop.run("loop", ctx)

    assert ctx.turn_count == 3
    assert len(caller.seen_messages) == 3
    assert outcome.reason is LoopEndReason.MAX_TURNS


# ── `C4` · `S11` cableado pre-turno (`GAP-01`) y `LoopOutcome` (`02·A4`) ───────

class _ShortCircuitProcessor:
    """`S11` que resuelve la entrada localmente — el caso del slash-command."""

    def __init__(self, text: str = "resuelto sin modelo") -> None:
        self.seen: list[str] = []
        self._text = text

    async def process(self, prompt, ctx):
        self.seen.append(prompt)
        return ProcessedInput(prompt=prompt, short_circuit=True, result_text=self._text)


class _RewritingProcessor:
    """`S11` que reescribe el prompt (expansión) y deja seguir el turno."""

    async def process(self, prompt, ctx):
        return ProcessedInput(prompt=f"[expandido] {prompt}")


async def test_loop_consumes_user_input_processor_and_honors_short_circuit():
    """El corte de `S11` es *load-bearing*: el modelo **no** se llama.

    Espejo del canónico: `processUserInput` devuelve `shouldQuery=false` y
    `QueryEngine.ts:556` no entra al loop — pero los mensajes ya se empujaron al
    historial (`:431`), así que el usuario y la salida local quedan en la
    conversación.
    """
    caller = ScriptedCaller([[TokenEvent(content="no debería"), DoneEvent(stop_reason="stop")]])
    proc = _ShortCircuitProcessor()
    loop = AgentLoop(model_caller=caller, input_processor=proc)
    ctx = _ctx()
    outcome = await loop.run("/comando", ctx)

    assert proc.seen == ["/comando"]          # el loop lo invocó, y con el prompt crudo
    assert caller.seen_messages == []         # y NO llamó al modelo
    assert ctx.turn_count == 0
    assert outcome.reason is LoopEndReason.SHORT_CIRCUIT
    assert outcome.detail == "resuelto sin modelo"
    # el historial conserva la entrada del usuario y la respuesta ya resuelta
    assert [m["role"] for m in ctx.messages] == ["user", "assistant"]
    assert ctx.messages[0]["content"] == "/comando"
    assert ctx.messages[1]["content"] == "resuelto sin modelo"


async def test_loop_sends_the_prompt_rewritten_by_the_processor():
    """Lo que llega al modelo es lo que `S11` devolvió, no lo que escribió el usuario."""
    caller = ScriptedCaller([[TokenEvent(content="ok"), DoneEvent(stop_reason="stop")]])
    loop = AgentLoop(model_caller=caller, input_processor=_RewritingProcessor())
    ctx = _ctx()
    outcome = await loop.run("hola", ctx)

    assert caller.seen_messages[0][0]["content"] == "[expandido] hola"
    assert outcome.reason is LoopEndReason.COMPLETED


async def test_loop_without_processor_behaves_exactly_as_before():
    """El default (`NoopUserInputProcessor`) no cambia nada: es la no-regresión de `C4`."""
    caller = ScriptedCaller([[TokenEvent(content="ok"), DoneEvent(stop_reason="stop")]])
    loop = AgentLoop(model_caller=caller)
    ctx = _ctx()
    outcome = await loop.run("hola", ctx)

    assert caller.seen_messages[0][0] == {"role": "user", "content": "hola"}
    assert outcome.reason is LoopEndReason.COMPLETED
    assert outcome.turn_count == 1


async def test_loop_outcome_distinguishes_missing_model_caller():
    """Un loop sin `S1` no es «un turno vacío»: es un fallo de cableado con nombre."""
    outcome = await AgentLoop().run("hola", _ctx())
    assert outcome.reason is LoopEndReason.NO_MODEL_CALLER


@pytest.mark.xfail(
    strict=True,
    reason="GAP-L3: el loop no soporta modelo de fallback (canónico: fallbackModel + "
    "FallbackTriggeredError → reintento con otro modelo). Un ErrorEvent corta sin "
    "recuperación. Ver 02-loop.md.",
)
async def test_loop_recupera_con_modelo_de_fallback():
    """Homologado: el loop resuelve un fallback cuando el modelo primario falla.

    ⚠ `H-L4` — reescrito 2026-08-02 de FIRMA a COMPORTAMIENTO. Antes decía
    `assert "fallback_model" in inspect.signature(AgentLoop.__init__).parameters`, y ese
    xfail acredita el gap como pagado en cuanto **alguien añada el parámetro sin
    implementar nada**: pasa a XPASS ⇒ rojo ⇒ «gap cerrado» sin que el loop recupere de
    nada. Un gap se fija por el comportamiento ausente, no por el parámetro ausente
    (mismo criterio que `test_loop_accepts_configurable_max_turns`, abajo).
    """
    intentos: list[str] = []

    class _CallerQueFallaUnaVez:
        async def complete(self, messages, tools, *, stop=None, model_id="", **kw):
            intentos.append(model_id)

            async def _gen():
                if len(intentos) == 1:
                    yield ErrorEvent(message="primario caído")
                else:
                    yield TokenEvent(content="respondido por el fallback")
                    yield DoneEvent(stop_reason="stop")

            return _gen()

    loop = AgentLoop(model_caller=_CallerQueFallaUnaVez(), model_id="primario")
    ctx = _ctx()
    outcome = await loop.run("x", ctx)

    # Lo que un loop homologado haría: reintentar con el otro modelo y COMPLETAR.
    assert len(intentos) == 2, f"no reintentó con el fallback (intentos={intentos})"
    assert outcome.reason is LoopEndReason.COMPLETED
    assert "fallback" in ctx.messages[-1]["content"]


@pytest.mark.xfail(
    strict=True,
    reason="GAP-L4: el loop no tiene motor de compactación (canónico: microcompact/"
    "autocompact/snip + presupuesto). CompactionProvider (contracts) existe pero el "
    "loop no lo consulta. Ver 02-loop.md.",
)
async def test_loop_compacta_el_historial_al_exceder_el_presupuesto():
    """Homologado: el loop compacta cuando el historial excede el presupuesto.

    ⚠ `H-L4` — reescrito 2026-08-02 de FIRMA a COMPORTAMIENTO, por el mismo motivo que
    el de arriba: `assert "compaction_provider" in params` se satisface añadiendo un
    parámetro que nadie consulta. Lo que se asevera es el EFECTO: que el historial deje
    de crecer sin límite a lo largo de los turnos.
    """
    tool = RecordingTool()
    caller = ScriptedCaller([_tool_call_turn("echo", "x" * 4000, f"c{i}") for i in range(30)])
    loop = AgentLoop(
        model_caller=caller,
        tool_registry=_registry(tool),
        tool_dispatcher=ToolDispatcher(),
        max_turns=30,
    )
    ctx = _ctx()
    await loop.run("trabaja largo", ctx)

    # Con 30 vueltas de mensajes de 4 kB, un loop con motor de compactación no arrastra
    # el historial entero hasta el final. Hoy `ctx.messages` crece monótonamente.
    assert len(ctx.messages) < 30, (
        f"el historial creció sin compactar ({len(ctx.messages)} mensajes): "
        "no hay motor de compactación"
    )


# ══════════════════════════════════════════════════════════════════════════════
# PARTE C · e2e real — loop conducido por LocalAgentRuntime (dispatcher/pool reales)
# ══════════════════════════════════════════════════════════════════════════════

async def _await_task(runtime, task_id):
    rec = runtime._task_registry.get(task_id)
    if rec is not None and rec.asyncio_task is not None:
        await rec.asyncio_task


def _real_runtime(tmp_path, caller, *, tools=()):
    from agentic_runtime.factory import (
        RuntimeConfig,
        StorageConfig,
        ToolsConfig,
        create_runtime,
    )
    return create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        tools=ToolsConfig(extras=list(tools)),
    ))


async def test_e2e_loop_multi_turn_real_dispatch(tmp_path):
    """El loop, ensamblado por create_runtime (ToolDispatcher/ToolPool/EventBus
    reales), conduce un multi-turno con tool call de punta a punta."""
    from agentic_runtime.contracts.runtime import RuntimeTask
    from agentic_runtime.execution.tasks.status import TaskStatus

    tool = RecordingTool()
    caller = ScriptedCaller([
        _tool_call_turn("echo", "PONG", "c1"),
        [TokenEvent(content="listo"), DoneEvent(stop_reason="stop")],
    ])
    runtime = _real_runtime(tmp_path, caller, tools=(tool,))
    task_id = await runtime.dispatch(RuntimeTask(prompt="usa echo", description="e2e-loop", session_id="sess-test"))
    await _await_task(runtime, task_id)

    assert runtime.status(task_id) == TaskStatus.COMPLETED
    assert runtime.result(task_id) == "listo"
    assert tool.calls == [{"text": "PONG"}]  # dispatch real ejecutó la tool


async def test_e2e_loop_stream_surfaces_tool_and_done_events(tmp_path):
    """La primitiva de stream del runtime surface la secuencia completa del loop:
    ToolCall → ToolResult → Token → Done."""
    from agentic_runtime.contracts.runtime import RuntimeTask
    from agentic_runtime.events import ToolResultEvent

    tool = RecordingTool()
    caller = ScriptedCaller([
        _tool_call_turn("echo", "PING", "c1"),
        [TokenEvent(content="ok"), DoneEvent(stop_reason="stop")],
    ])
    runtime = _real_runtime(tmp_path, caller, tools=(tool,))

    events = [
        ev async for ev in runtime.stream(
            RuntimeTask(prompt="usa echo", description="e2e-stream", session_id="sess-test")
        )
    ]
    types = [type(e).__name__ for e in events]
    assert "ToolCallEvent" in types
    assert "ToolResultEvent" in types
    # El último es el turno del asistente ya ensamblado, no el `DoneEvent` del stream
    # crudo: A rinde el `Message` DESPUÉS de consumir los deltas (`query.ts:1610`).
    assert types[-1] == "MessageEvent"
    call_ids = {e.call_id for e in events if isinstance(e, ToolCallEvent)}
    assert all(e.call_id in call_ids for e in events if isinstance(e, ToolResultEvent))


# ══════════════════════════════════════════════════════════════════════════════
# PARTE D · costura pública: el stream lleva lo mismo que la historia (`#10`)
#
# Propiedad canónica medida en `query.ts` 1→EOF: A **no tiene un canal aparte** para
# lo que el runtime le inyecta al modelo — rinde los mismos `Message` que persiste
# (`:1588`, `:1610`, `:1624`) y marca cada iteración con `stream_request_start`
# (`:337`). Antes de pagar esto, todo lo que B inyectaba (delta de diferidas, recall,
# prompt) entraba a `ctx.messages` y no salía por ninguna parte: el patrón de fallo
# dominante del barrido —B tiene el dato y no lo pone en ninguna lista que se vea—.
# ══════════════════════════════════════════════════════════════════════════════

class _DeferredTool(RecordingTool):
    """Tool diferida: no se anuncia al modelo hasta que ToolSearch la descubre."""
    deferred = True


async def _collect(ctx: ToolUseContext, prompt: str, **loop_kw) -> list:
    """Corre un turno con un sink suscrito a TODO el canal y devuelve lo que salió."""
    from agentic_runtime.events.bus import EventBus

    seen: list = []

    async def _sink(ev) -> None:
        seen.append(ev)

    bus = EventBus()
    bus.subscribe_all(_sink)
    await AgentLoop(event_bus=bus, **loop_kw).run(prompt, ctx)
    return seen


async def test_public_stream_carries_every_message_the_runtime_injects():
    """Lo que entra a `ctx.messages` sale por el stream — con su procedencia rotulada.

    Se afirma sobre la HISTORIA y sobre el CANAL a la vez: es la única forma de que un
    append nuevo que nadie rinda haga fallar el test en vez de pasar inadvertido.
    """
    caller = ScriptedCaller([[TokenEvent(content="hola"), DoneEvent(stop_reason="stop")]])
    ctx = _ctx()
    seen = await _collect(ctx, "saluda", model_caller=caller)

    mensajes = [e for e in seen if isinstance(e, MessageEvent)]
    assert [(m.role, m.content, m.origin) for m in mensajes] == [
        ("user", "saluda", "user"),
        ("assistant", "hola", "assistant"),
    ], [(m.role, m.content, m.origin) for m in mensajes]
    # Y coincide con lo que el modelo verá: mismo contenido, mismo orden.
    assert [(m["role"], m["content"]) for m in ctx.messages] == [
        (m.role, m.content) for m in mensajes
    ]


async def test_turn_start_carries_the_tool_plan_as_data_not_as_text():
    """`TurnStartEvent` lleva el plan que `TurnToolPlan` decidía y se tiraba.

    Los nombres van como DATO. Si fueran sólo el texto del anuncio, el consumidor
    tendría que re-parsearlo para saber qué se ofreció — que es la enfermedad
    diagnosticada en `FIND-DEFER-1`, no su remedio.
    """
    visible, oculta = RecordingTool("echo"), _DeferredTool("mcp_lejos")
    caller = ScriptedCaller([[DoneEvent(stop_reason="stop")]])
    seen = await _collect(
        _ctx(), "x",
        model_caller=caller,
        tool_registry=_registry(visible, oculta),
        tool_dispatcher=ToolDispatcher(),
    )

    inicios = [e for e in seen if isinstance(e, TurnStartEvent)]
    assert len(inicios) == 1 and inicios[0].turn == 1
    # La diferida NO se anuncia al modelo…
    assert "mcp_lejos" not in inicios[0].tool_names
    assert "echo" in inicios[0].tool_names
    # …pero el consumidor SÍ sabe que existe y que está oculta: ése es el dato que
    # antes no salía de `prepare_turn`.
    assert inicios[0].deferred_names == ("mcp_lejos",)


async def test_deferred_announcement_reaches_the_consumer_not_only_the_model():
    """El delta de diferidas se le inyecta al modelo Y se rinde por el stream.

    Antes salía sólo hacia el modelo: el consumidor no tenía forma de saber qué se le
    había dicho, ni de auditarlo.
    """
    caller = ScriptedCaller([[DoneEvent(stop_reason="stop")]])
    seen = await _collect(
        _ctx(), "x",
        model_caller=caller,
        tool_registry=_registry(RecordingTool("echo"), _DeferredTool("mcp_lejos")),
        tool_dispatcher=ToolDispatcher(),
    )

    anuncios = [e for e in seen if isinstance(e, MessageEvent) and e.origin == "deferred_delta"]
    assert len(anuncios) == 1, [type(e).__name__ for e in seen]
    assert "mcp_lejos" in anuncios[0].content
    assert anuncios[0].role == "user"


async def test_recall_injected_by_the_runtime_is_visible_on_the_stream():
    """El recall (`active_context`) también es inyección del runtime — también se rinde."""
    caller = ScriptedCaller([[DoneEvent(stop_reason="stop")]])
    seen = await _collect(
        _ctx(), "x",
        model_caller=caller,
        capability_manager=FakeCapabilityManager(recall=[{"content": "recuerda X"}]),
    )

    recalls = [e for e in seen if isinstance(e, MessageEvent) and e.origin == "recall"]
    assert len(recalls) == 1 and "recuerda X" in recalls[0].content


async def test_sink_stamps_identity_on_events_it_did_not_build():
    """`FIND-STREAM-1`: el sellado ocurre en el sumidero, no en el emisor.

    Los `TokenEvent`/`DoneEvent` los construye el CALLER (aquí, un doble que no sabe
    nada de sesiones) y salen igualmente atribuidos. Es la propiedad que distingue un
    sumidero de «que cada emisor se acuerde»: un emisor de terceros no puede olvidarlo.
    """
    caller = ScriptedCaller([[TokenEvent(content="a"), DoneEvent(stop_reason="stop")]])
    ctx = _ctx(agent_id="agente-7")
    ctx.task_id = "tarea-3"
    seen = await _collect(ctx, "x", model_caller=caller)

    ajenos = [e for e in seen if isinstance(e, (TokenEvent, DoneEvent))]
    assert ajenos, [type(e).__name__ for e in seen]
    for ev in ajenos:
        assert (ev.session_id, ev.agent_id, ev.task_id) == ("loop-homolog", "agente-7", "tarea-3")
        assert ev.ts > 0
    # Orden total del canal: monótono, sin huecos, arrancando en 1.
    assert [e.seq for e in seen] == list(range(1, len(seen) + 1))


async def test_sink_restamps_identity_instead_of_respecting_what_came_in():
    """Sellado **incondicional**, no «sólo si está vacío».

    No es gusto: `sessionStorage.ts:1049-1056` documenta que sellar condicionalmente
    reintroduce la identidad CRUZADA — un evento reemitido llevaría la sesión del
    emisor original en vez de la de este turno. Aquí el caller emite un evento ya
    sellado con OTRA sesión y el sumidero debe pisarla.
    """
    caller = ScriptedCaller([[
        TokenEvent(content="a", session_id="sesion-de-otro", task_id="tarea-de-otro", seq=99),
        DoneEvent(stop_reason="stop"),
    ]])
    ctx = _ctx()
    ctx.task_id = "tarea-mia"
    seen = await _collect(ctx, "x", model_caller=caller)

    tokens = [e for e in seen if isinstance(e, TokenEvent)]
    assert len(tokens) == 1
    assert tokens[0].session_id == "loop-homolog" and tokens[0].task_id == "tarea-mia"
    assert tokens[0].seq != 99
