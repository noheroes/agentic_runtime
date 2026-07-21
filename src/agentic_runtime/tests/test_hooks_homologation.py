"""Homologación 06·hooks — runtime `hooks/` vs canónico.

Contrapartes canónicas leídas ÍNTEGRAS: `schemas/hooks.ts` (222, tipos de hook
command/prompt/agent/http + matcher + if), `types/hooks.ts` (290, syncHookResponse
per-evento + HookResult/AggregatedHookResult), `utils/hooks/hookEvents.ts` (192),
`utils/hooks/hookHelpers.ts` (83), `utils/hooks.ts` (5022: createBaseHookInput,
processHookJSONOutput, execCommandHook, matchesPattern, prepareIfConditionMatcher,
getMatchingHooks, executeHooks, executores por evento), `query/stopHooks.ts` (473,
handleStopHooks), `services/tools/toolHooks.ts` (650, runPre/PostToolUseHooks +
resolveHookPermissionDecision), `hooks/toolPermission/PermissionContext.ts` (388),
`utils/hooks/registerFrontmatterHooks.ts` (67), `registerSkillHooks.ts` (64),
`entrypoints/sdk/coreTypes.ts::HOOK_EVENTS` (28 eventos).

El runtime `hooks/` (146 LOC) es un REGISTRY EN-PROCESO (HookEvent enum + HookDecision
+ HookRunner). El canónico es un SISTEMA CONFIGURABLE dirigido por settings.json
(command/prompt/agent/http, matchers, if, async, once, per-source). La homologación
correcta es *de comportamiento del seam*: el runtime dispara PUNTOS y pasa PAYLOAD; la
política (incl. leer settings.json y exec de comandos) la implementa el integrador en su
handler. Por eso los gaps reales no son "falta el exec de bash", sino: (1) faltan eventos
en la taxonomía, (2) casi ningún punto se dispara, (3) el punto PreToolUse pierde
semántica (permission behavior/ask/stop/additional_context), (4) HookDecision no puede
expresar la salida rica del canónico.

Los xfail(strict) codifican esos gaps: fallan HOY (evidencia del gap); al homologar,
pasan y se retira el marcador.
"""
from __future__ import annotations

import dataclasses

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.events import DoneEvent, ToolCallEvent
from agentic_runtime.hooks import HookDecision, HookEvent, HookRunner
from agentic_runtime.loop import AgentLoop
from agentic_runtime.tools import ToolCategory, ToolRegistry, ToolResult
from agentic_runtime.tools.dispatcher import ToolDispatcher


# --- Contraparte canónica: los 28 eventos de HOOK_EVENTS (coreTypes.ts:25) ---
CANONICAL_HOOK_EVENTS = {
    "PreToolUse", "PostToolUse", "PostToolUseFailure", "Notification",
    "UserPromptSubmit", "SessionStart", "SessionEnd", "Stop", "StopFailure",
    "SubagentStart", "SubagentStop", "PreCompact", "PostCompact",
    "PermissionRequest", "PermissionDenied", "Setup", "TeammateIdle",
    "TaskCreated", "TaskCompleted", "Elicitation", "ElicitationResult",
    "ConfigChange", "WorktreeCreate", "WorktreeRemove", "InstructionsLoaded",
    "CwdChanged", "FileChanged",
}

# Subconjunto de eventos canónicos EN ALCANCE del core (no coordinator/swarm ⛔ ni
# UI/terminal ⛔) que el runtime NO declara. Justificación por evento en 06-hooks.md.
CORE_MISSING_EVENTS = {
    "PostCompact",       # simétrico a PreCompact; motor de compactación (02)
    "SubagentStart",     # inyecta additionalContexts al subagente (runAgent.ts:532)
    "PermissionRequest", # el hook de DECISIÓN de permiso (hogar de GAP-02)
    "PermissionDenied",  # permite retry tras denegación
    "Setup",             # lifecycle de arranque de sesión
}


# --------------------------------------------------------------------------- #
# Helpers (espejo de test_pre_tool_use_hook.py)
# --------------------------------------------------------------------------- #
def _make_caller(*events):
    class StubCaller:
        async def complete(self, messages, tools, *, stop=None, model_id=""):
            async def _gen():
                for ev in events:
                    yield ev
            return _gen()
    return StubCaller()


class RecordingTool:
    name = "echo"
    description = "Echoes input"
    input_schema: dict = {"type": "object", "properties": {"text": {"type": "string"}}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def execute(self, input: dict, ctx) -> ToolResult:
        self.calls.append(input)
        return ToolResult(tool_name=self.name, output=input.get("text", ""))


def _make_registry(*tools) -> ToolRegistry:
    reg = ToolRegistry()
    for t in tools:
        reg.register(t)
    return reg


def _loop(caller, reg, hook_runner):
    return AgentLoop(
        model_caller=caller,
        tool_registry=reg,
        tool_dispatcher=ToolDispatcher(),
        hook_runner=hook_runner,
    )


def _one_tool_call(tool_name="echo", text="mundo"):
    return _make_caller(
        ToolCallEvent(tool_name=tool_name, tool_input={"text": text}, call_id="c1"),
        DoneEvent(stop_reason="stop"),
    )


# ========================================================================== #
# HOMOLOGADO (✅) — el seam en-proceso y el punto PreToolUse
# ========================================================================== #
def test_hookdecision_shape_is_subset_of_canonical_output():
    """✅ HookDecision expresa el subconjunto núcleo de la salida canónica: block
    (decision:block / permissionDecision:deny), stop (continue:false), message
    (reason/stopReason), modified_input (updatedInput), additional_context."""
    fields = {f.name for f in dataclasses.fields(HookDecision)}
    assert {"block", "stop", "message", "modified_input", "additional_context"} <= fields


@pytest.mark.asyncio
async def test_pretooluse_is_the_only_gate_fired_in_loop():
    """✅ El loop dispara PreToolUse antes de cada tool con el payload homologado
    (tool_name/tool_input/call_id/ctx), espejo de canUseTool."""
    seen: list[dict] = []

    async def handler(event, payload):
        seen.append(payload)
        return None

    runner = HookRunner()
    runner.register(HookEvent.PRE_TOOL_USE, handler)
    tool = RecordingTool()
    await _loop(_one_tool_call(), _make_registry(tool), runner).run(
        "usa echo", ToolUseContext(session_id="s1")
    )
    assert len(seen) == 1
    assert seen[0]["tool_name"] == "echo" and seen[0]["call_id"] == "c1"


@pytest.mark.asyncio
async def test_pretooluse_block_maps_to_deny():
    """✅ block → denegar sin ejecutar (permissionDecision:deny del canónico)."""
    async def handler(event, payload):
        return HookDecision.blocked("no")

    runner = HookRunner()
    runner.register(HookEvent.PRE_TOOL_USE, handler)
    tool = RecordingTool()
    await _loop(_one_tool_call(), _make_registry(tool), runner).run(
        "x", ToolUseContext(session_id="s1")
    )
    assert tool.calls == []


# ========================================================================== #
# GAPS (xfail strict) — evidencia de lo NO homologado
# ========================================================================== #
@pytest.mark.xfail(strict=True, reason="FIND-HOOK1: taxonomía incompleta — faltan "
                   "eventos core (PostCompact/SubagentStart/PermissionRequest/"
                   "PermissionDenied/Setup); 11 declarados vs 28 canónicos")
def test_taxonomy_covers_core_canonical_events():
    values = {e.value for e in HookEvent}
    missing = CORE_MISSING_EVENTS - values
    assert not missing, f"eventos core ausentes: {missing}"


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason="FIND-HOOK2: PostToolUse declarado pero NUNCA "
                   "disparado — el loop solo dispara PreToolUse (+ runtime SubagentStop)")
async def test_posttooluse_fires_after_tool():
    fired: list[dict] = []

    async def handler(event, payload):
        fired.append(payload)
        return None

    runner = HookRunner()
    runner.register(HookEvent.POST_TOOL_USE, handler)
    tool = RecordingTool()
    await _loop(_one_tool_call(), _make_registry(tool), runner).run(
        "x", ToolUseContext(session_id="s1")
    )
    assert fired, "PostToolUse debería dispararse tras ejecutar una tool"


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason="FIND-HOOK2: Stop de fin de turno no portado — "
                   "el loop no dispara Stop (handleStopHooks del canónico ausente)")
async def test_stop_hook_fires_at_turn_end():
    fired: list[dict] = []

    async def handler(event, payload):
        fired.append(payload)
        return None

    runner = HookRunner()
    runner.register(HookEvent.STOP, handler)
    await _loop(
        _make_caller(DoneEvent(stop_reason="stop")), _make_registry(), runner
    ).run("hola", ToolUseContext(session_id="s1"))
    assert fired, "Stop debería dispararse al terminar el turno"


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason="FIND-HOOK3: PreToolUse pierde additional_context "
                   "— el loop solo consume block/modified_input; el additionalContext "
                   "del hook no se inyecta al contexto del modelo")
async def test_pretooluse_additional_context_injected():
    async def handler(event, payload):
        return HookDecision(additional_context="ctx-inyectado")

    runner = HookRunner()
    runner.register(HookEvent.PRE_TOOL_USE, handler)
    tool = RecordingTool()
    ctx = ToolUseContext(session_id="s1")
    await _loop(_one_tool_call(), _make_registry(tool), runner).run("x", ctx)
    blob = "".join(str(m.get("content", "")) for m in ctx.messages)
    assert "ctx-inyectado" in blob, "additionalContext del PreToolUse debe llegar al modelo"


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason="FIND-HOOK3: PreToolUse `stop` inerte — el loop "
                   "ignora HookDecision.stop en este punto (no detiene la ejecución)")
async def test_pretooluse_stop_halts_loop():
    async def handler(event, payload):
        return HookDecision.stopped("alto en pretool")

    runner = HookRunner()
    runner.register(HookEvent.PRE_TOOL_USE, handler)
    tool = RecordingTool()
    ctx = ToolUseContext(session_id="s1")
    # Tras el stop, un 2º tool call NO debería ejecutarse.
    caller = _make_caller(
        ToolCallEvent(tool_name="echo", tool_input={"text": "a"}, call_id="c1"),
        ToolCallEvent(tool_name="echo", tool_input={"text": "b"}, call_id="c2"),
        DoneEvent(stop_reason="stop"),
    )
    await _loop(caller, _make_registry(tool), runner).run("x", ctx)
    assert tool.calls == [], "stop en PreToolUse debe abortar sin ejecutar tools"


@pytest.mark.xfail(strict=True, reason="FIND-HOOK7: HookDecision no expresa permission "
                   "behavior `ask` (HITL prompt del canónico permissionDecision:ask)")
def test_hookdecision_can_express_ask():
    fields = {f.name for f in dataclasses.fields(HookDecision)}
    assert "permission_behavior" in fields or hasattr(HookDecision, "ask")


@pytest.mark.xfail(strict=True, reason="FIND-HOOK7: HookDecision no expresa updated_output "
                   "(PostToolUse updatedMCPToolOutput) ni system_message/retry")
def test_hookdecision_can_rewrite_tool_output():
    fields = {f.name for f in dataclasses.fields(HookDecision)}
    assert "updated_output" in fields


@pytest.mark.xfail(strict=True, reason="FIND-HOOK5/GAP-02: PermissionContext sin `mode` "
                   "(default/plan/acceptEdits/bypassPermissions) — permission modes no "
                   "homologados; su hogar canónico es hooks/toolPermission/")
def test_permission_context_has_mode():
    from agentic_runtime.contracts.permissions import PermissionContext
    fields = set(PermissionContext.model_fields)
    assert "mode" in fields
