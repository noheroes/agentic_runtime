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

import asyncio
import inspect

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.events import DoneEvent, TokenEvent, ToolCallEvent
from agentic_runtime.hooks import HookEvent
from agentic_runtime.hooks.protocol import HookDecision
from agentic_runtime.hooks.runner import HookRunner
from agentic_runtime.loop.agent_loop import AgentLoop
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
        return None


class RecordingTool:
    """Tool nativa que registra sus ejecuciones e inputs. Sin permiso requerido
    para que el único gate observable sea el hook PreToolUse."""

    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0
    input_schema: dict = {"type": "object", "properties": {"text": {"type": "string"}}}

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
            ctx.stop.set()
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
    stop = asyncio.Event()
    stop.set()
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
    ctx = _ctx(stop=asyncio.Event())
    await loop.run("trabaja", ctx)

    assert len(caller.seen_messages) == 1  # solo el 1er turno llegó al modelo
    assert tool.calls == [{"text": "x"}]


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
    await loop.run("loop", ctx)

    assert ctx.turn_count == _MAX_TURNS  # cortó en el techo, no siguió


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


@pytest.mark.xfail(
    strict=True,
    reason="GAP-L2: el loop tiene el techo hardcodeado _MAX_TURNS=50; no acepta un "
    "maxTurns configurable por el consumidor (canónico: QueryParams.maxTurns). "
    "Ver 02-loop.md.",
)
def test_loop_accepts_configurable_max_turns():
    """Homologado: maxTurns es un parámetro del consumidor, no una constante."""
    params = inspect.signature(AgentLoop.__init__).parameters
    assert "max_turns" in params


@pytest.mark.xfail(
    strict=True,
    reason="GAP-L3: el loop no soporta modelo de fallback (canónico: fallbackModel + "
    "FallbackTriggeredError → reintento con otro modelo). Un ErrorEvent corta sin "
    "recuperación. Ver 02-loop.md.",
)
def test_loop_accepts_fallback_model():
    """Homologado: el loop resuelve un fallback cuando el modelo primario falla."""
    params = inspect.signature(AgentLoop.__init__).parameters
    assert "fallback_model" in params


@pytest.mark.xfail(
    strict=True,
    reason="GAP-L4: el loop no tiene motor de compactación (canónico: microcompact/"
    "autocompact/snip + presupuesto). CompactionProvider (contracts) existe pero el "
    "loop no lo consulta. Ver 02-loop.md.",
)
def test_loop_wires_compaction_engine():
    """Homologado: el loop dispara compactación por umbral/presupuesto de tokens."""
    params = inspect.signature(AgentLoop.__init__).parameters
    assert "compaction_provider" in params or "compaction" in params


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
    task_id = await runtime.dispatch(RuntimeTask(prompt="usa echo", description="e2e-loop"))
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
            RuntimeTask(prompt="usa echo", description="e2e-stream")
        )
    ]
    types = [type(e).__name__ for e in events]
    assert "ToolCallEvent" in types
    assert "ToolResultEvent" in types
    assert types[-1] == "DoneEvent"
    call_ids = {e.call_id for e in events if isinstance(e, ToolCallEvent)}
    assert all(e.call_id in call_ids for e in events if isinstance(e, ToolResultEvent))
