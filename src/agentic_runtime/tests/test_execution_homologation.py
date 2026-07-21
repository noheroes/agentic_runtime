"""05·execution — homologación del subsistema `execution/` contra el canónico.

Contrapartes canónicas leídas íntegras: `Task.ts`, `tasks.ts`, `tasks/types.ts`,
`tasks/stopTask.ts`, `tasks/LocalAgentTask/LocalAgentTask.tsx`, `tools/AgentTool/`
(`AgentTool.tsx`, `runAgent.ts`, `forkSubagent.ts`, `agentToolUtils.ts`,
`loadAgentsDir.ts`, `prompt.ts`, `constants.ts`, `builtInAgents.ts`),
`services/AgentSummary/agentSummary.ts`. (`utils/tasks.ts` es el TODO/tasklist → 10,
NO el registry de ejecución.)

Estos tests fijan:
- lo homologado (paridad de TaskStatus, precedencia de `getAgentModel`, política de fork,
  canal de notificación desacoplado, tope de profundidad);
- los gaps como `xfail(strict)` — cada uno codifica comportamiento canónico ausente.

Ver `HOMOLOGATION/05-execution.md` para la tabla feature-by-feature.
"""
from __future__ import annotations

import inspect

import pytest

from agentic_runtime.execution.agents import INHERIT, resolve_subagent_model
from agentic_runtime.execution.fork import (
    ForkContext,
    ForkPolicy,
    ForkSnapshot,
    RuntimeContextForker,
)
from agentic_runtime.execution.local import runtime as local_runtime
from agentic_runtime.execution.local.notification import (
    BackgroundNotification,
    drain_notifications,
    put_notification,
)
from agentic_runtime.execution.tasks.registry import TaskRecord
from agentic_runtime.execution.tasks.status import TaskStatus


# --- lo homologado -----------------------------------------------------------

def test_task_status_parity_with_canonical():
    """TaskStatus del runtime = TaskStatus canónico (Task.ts) exacto, con is_terminal."""
    assert {s.value for s in TaskStatus} == {
        "pending", "running", "completed", "failed", "killed"
    }
    assert TaskStatus.COMPLETED.is_terminal()
    assert TaskStatus.FAILED.is_terminal()
    assert TaskStatus.KILLED.is_terminal()
    assert not TaskStatus.PENDING.is_terminal()
    assert not TaskStatus.RUNNING.is_terminal()


def test_resolve_subagent_model_precedence_mirrors_get_agent_model():
    """getAgentModel: override explícito > modelo del agente > herencia del padre.
    `None`/`inherit` heredan; el NOMBRE del agente nunca participa."""
    # override gana sobre todo
    assert resolve_subagent_model("haiku", "opus", model_override="sonnet") == "sonnet"
    # sin override, gana el del agente
    assert resolve_subagent_model("haiku", "opus") == "haiku"
    # None hereda del padre
    assert resolve_subagent_model(None, "opus") == "opus"
    # sentinel "inherit" hereda del padre
    assert resolve_subagent_model(INHERIT, "opus") == "opus"


def test_fork_policy_defaults_isolate_messages_share_state():
    """Política de fork por defecto: NO hereda mensajes, SÍ hereda permisos/tools/caps/abort.
    Espeja el contenedor-independiente-valores-compartidos del canónico."""
    p = ForkPolicy()
    assert p.inherit_messages is False
    assert p.inherit_permissions is True
    assert p.inherit_tool_pool is True
    assert p.inherit_capabilities is True
    assert p.propagate_abort is True


def test_fork_produces_child_context_with_fresh_agent_id():
    """RuntimeContextForker.fork devuelve un ctx hijo con agent_id nuevo y depth+heredado."""
    forker = RuntimeContextForker()
    snap = ForkSnapshot(session_id="s1", user_id="u1", subagent_depth=2)
    ctx = forker.fork(ForkContext(prompt="do", policy=ForkPolicy(), parent_snapshot=snap))
    assert ctx.session_id == "s1"
    assert ctx.user_id == "u1"
    assert ctx.agent_id.startswith("agent_")


def test_notification_channel_scoped_by_user_and_session():
    """Canal <task-notification> desacoplado y escopado por (user_id, session_id):
    supera al canónico (single-user). El hijo escribe sin referencia viva al padre."""
    put_notification(BackgroundNotification(
        parent_user_id="userA", parent_session_id="sessX", task_id="t1",
        status="completed", description="d", notification_text="done",
    ))
    # otro usuario, mismo session_id: aislado
    assert drain_notifications("userB", "sessX") == []
    drained = drain_notifications("userA", "sessX")
    assert len(drained) == 1 and drained[0].task_id == "t1"
    # drenar es destructivo (pop)
    assert drain_notifications("userA", "sessX") == []


def test_subagent_depth_cap_enforced_by_agent_tool():
    """El runtime topa la profundidad de anidamiento explícitamente (_MAX_SUBAGENT_DEPTH)."""
    from agentic_runtime.tools.native.agent import _MAX_SUBAGENT_DEPTH
    assert _MAX_SUBAGENT_DEPTH >= 1


# --- FIND-EXEC1: el runner de subagentes NO está cableado en producción -------

@pytest.mark.xfail(
    strict=True,
    reason="FIND-EXEC1: factory._build_local nunca llama set_runner(); AgentTool→"
    "get_runner().run() reventaría (RuntimeError). Falta el adaptador "
    "ForkContext→RuntimeTask que puentee AgentTool ↔ LocalAgentRuntime.dispatch. "
    "Sólo los tests registran un runner.",
)
def test_factory_wires_subagent_runner():
    """El factory debería cablear el runner para que AgentTool pueda spawnear subagentes."""
    from agentic_runtime import factory as factory_mod

    src = inspect.getsource(factory_mod)
    assert "set_runner" in src


# --- FIND-EXEC2: el fork con inherit_messages no filtra tool_use colgantes ----

@pytest.mark.xfail(
    strict=True,
    reason="FIND-EXEC2: RuntimeContextForker copia tuple(snap.messages) crudo. El "
    "canónico llama filterIncompleteToolCalls(forkContextMessages) (runAgent.ts) al "
    "heredar, eliminando assistant-msgs con tool_use sin tool_result (invariante API, "
    "misma clase que FIND-L1/yieldMissingToolResultBlocks). Forkear a mitad de turno "
    "hereda un tool_use colgante → error de API.",
)
def test_fork_filters_incomplete_tool_calls_from_inherited_messages():
    """Al heredar mensajes, el hijo NO debe recibir assistant-msgs con tool_use sin
    su tool_result correspondiente."""
    forker = RuntimeContextForker()
    dangling = {
        "role": "assistant",
        "content": [{"type": "tool_use", "id": "tu_1", "name": "bash", "input": {}}],
    }
    snap = ForkSnapshot(session_id="s1", messages=(dangling,))
    ctx = forker.fork(ForkContext(
        prompt="continue",
        policy=ForkPolicy(inherit_messages=True),
        parent_snapshot=snap,
    ))
    has_dangling = any(
        isinstance(m, dict)
        and m.get("role") == "assistant"
        and any(
            isinstance(b, dict) and b.get("type") == "tool_use"
            for b in (m.get("content") or [])
        )
        for m in ctx.messages
    )
    assert not has_dangling, "el fork heredó un tool_use colgante (viola invariante API)"


# --- FIND-EXEC3: la notificación de kill descarta el trabajo parcial ----------

@pytest.mark.xfail(
    strict=True,
    reason="FIND-EXEC3: en la rama CancelledError, _run_loop llama _notify(...,'killed',"
    "'Agent was killed...', final_text='') — descarta lo hecho. El canónico preserva "
    "extractPartialResult(agentMessages) (agentToolUtils.ts) en la notificación de kill, "
    "aunque ctx.messages está disponible.",
)
def test_kill_notification_preserves_partial_result():
    """La rama de kill debería extraer el texto parcial de ctx.messages (extractPartialResult),
    no enviar un texto estático con final vacío."""
    src = inspect.getsource(local_runtime.LocalAgentRuntime._run_loop)
    # localiza la rama CancelledError y verifica que referencia el rescate de ctx.messages
    cancel_idx = src.find("CancelledError")
    assert cancel_idx != -1
    cancel_branch = src[cancel_idx:src.find("except Exception", cancel_idx)]
    assert "_last_assistant_text" in cancel_branch or "ctx.messages" in cancel_branch


# --- FIND-EXEC4: el subsistema observer/ está huérfano ------------------------

@pytest.mark.xfail(
    strict=True,
    reason="FIND-EXEC4: execution/observer/ (get/set_observer, SubagentStarted/Stopped) "
    "no lo invoca ninguna ruta. LocalAgentRuntime nunca llama on_subagent_started/stopped. "
    "Huérfano hermano de modes/ (FIND-MODE1). El eje real de observabilidad lo cubren "
    "EventBus (push_event) + hook SUBAGENT_STOP.",
)
def test_observer_is_wired_into_runtime():
    """Si observer/ estuviera cableado, LocalAgentRuntime lo emitiría en dispatch/complete."""
    src = inspect.getsource(local_runtime)
    assert (
        "get_observer" in src
        or "on_subagent_started" in src
        or "on_subagent_stopped" in src
    )


# --- FIND-EXEC5: max_turns de task/agent no se cablea al loop -----------------

@pytest.mark.xfail(
    strict=True,
    reason="FIND-EXEC5: AgentLoop usa _MAX_TURNS=50 fijo. RuntimeTask.max_turns y "
    "ForkContext.max_turns existen pero _run_loop construye AgentLoop sin pasarlos, y "
    "AgentLoop.__init__ ni siquiera acepta max_turns. El canónico pasa "
    "maxTurns ?? agentDefinition.maxTurns a query(). El fork declara maxTurns=200 y se ignora.",
)
def test_max_turns_threaded_to_loop():
    """AgentLoop debe aceptar un tope de turnos configurable por task/agent_def."""
    from agentic_runtime.loop.agent_loop import AgentLoop

    params = inspect.signature(AgentLoop.__init__).parameters
    assert "max_turns" in params


# --- GAP-EXEC1: TaskRecord no tiene flag de dedup `notified` ------------------

@pytest.mark.xfail(
    strict=True,
    reason="GAP-EXEC1: el canónico marca `notified` atómicamente (enqueueAgentNotification "
    "+ stopTask) para evitar doble notificación en la carrera TaskStop+completion. "
    "TaskRecord no tiene el flag y _notify puede encolar dos veces.",
)
def test_task_record_has_notified_dedup_flag():
    assert "notified" in TaskRecord.__dataclass_fields__


# --- GAP-EXEC2/GAP-MODE1: TaskRecord no discrimina el tipo de task ------------

@pytest.mark.xfail(
    strict=True,
    reason="GAP-EXEC2 (=GAP-MODE1): el canónico tipa cada task (local_bash/local_agent/"
    "remote_agent/in_process_teammate/…) con prefijo de id y dispatch polimórfico "
    "getTaskByType(type).kill(). TaskRecord no tiene discriminante `type`; el runtime "
    "asume un único tipo (agente local) y kill genérico.",
)
def test_task_record_has_type_discriminant():
    fields = TaskRecord.__dataclass_fields__
    assert "type" in fields or "task_type" in fields


# --- FIND-EXEC9: no hay promoción foreground→background de un subagente sync --

@pytest.mark.xfail(
    strict=True,
    reason="FIND-EXEC9 (re-audit): el canónico promueve un subagente SÍNCRONO a background "
    "a mitad de ejecución — registerAgentForeground devuelve un backgroundSignal + "
    "autoBackgroundMs (auto-bg tras 120s), y AgentTool.tsx corre una carrera "
    "next-message vs background-signal; al dispararse, desengancha el iterador, sigue en "
    "un closure detached y retorna async_launched. El runtime decide async SÓLO en el "
    "spawn (run_in_background); is_backgrounded es un flag mutable pero no hay primitiva "
    "que interrumpa el await del padre, desenganche y re-notifique.",
)
def test_foreground_to_background_promotion_supported():
    """Debe existir una primitiva de promoción foreground→background (backgroundSignal /
    autoBackground / promote) de un subagente sync ya en vuelo."""
    src = inspect.getsource(local_runtime) + inspect.getsource(
        __import__("agentic_runtime.tools.native.agent", fromlist=["AgentTool"])
    )
    assert (
        "background_signal" in src
        or "auto_background" in src
        or "promote" in src
    )


# --- FIND-EXEC10: no hay seam para forzar async todos los spawns (assistant) --

@pytest.mark.xfail(
    strict=True,
    reason="FIND-EXEC10 (re-audit): el canónico deriva shouldRunAsync de VARIOS motores, "
    "no sólo del param — run_in_background || selectedAgent.background || isCoordinator || "
    "forceAsync(fork) || assistantForceAsync(appState.kairosEnabled) || proactive. En modo "
    "assistant (KAIROS) TODOS los subagentes se fuerzan async porque un subagente síncrono "
    "mantiene abierto el turno del main-loop del daemon y atasca el inputQueue. "
    "agentic_assistant ES un implementador assistant con usuarios/sesiones → necesita ese "
    "seam. El AgentTool del runtime decide async sólo por run_in_background.",
)
def test_force_async_policy_seam_exists():
    """Debe haber un seam para forzar async todos los spawns (política del integrador),
    no sólo el flag run_in_background por-call."""
    from agentic_runtime.tools.native import agent as agent_mod

    src = inspect.getsource(agent_mod)
    assert "force_async" in src or "always_background" in src


# --- FIND-EXEC11: sin cascada de limpieza de recursos hijos al terminar el agente

@pytest.mark.xfail(
    strict=True,
    reason="FIND-EXEC11 (re-audit): el finally de runAgent.ts (816-859) al terminar un "
    "subagente reap-ea sus recursos hijos: killShellTasksForAgent (mata los bash "
    "run_in_background que lanzó, si no quedan zombies PPID=1), libera AppState.todos[agentId], "
    "clearSessionHooks, mcpCleanup, killMonitorMcpTasksForAgent. _run_loop del runtime no tiene "
    "finally ni reaping por agent_id de los recursos que el subagente spawneó (aterriza con "
    "bash-bg en 10 / MCP de agente en 11 / skills en 12).",
)
def test_agent_termination_reaps_child_resources():
    """Al terminar (normal/abort/error) un subagente, el runtime debe reap-ear los recursos
    hijos que lanzó (tasks bash background, todos, hooks de sesión)."""
    src = inspect.getsource(local_runtime.LocalAgentRuntime._run_loop)
    assert "finally" in src and ("agent_id" in src.lower() and "kill" in src.lower())


# --- FIND-EXEC12: sin inyección de mensajes a un subagente EN EJECUCIÓN -------

@pytest.mark.xfail(
    strict=True,
    reason="FIND-EXEC12 (re-audit): el canónico inyecta mensajes en un local_agent VIVO — "
    "LocalAgentTaskState.pendingMessages + queuePendingMessage/drainPendingMessages "
    "(drenados en los límites de ronda de tools) — el mecanismo de SendMessage-continue. Es "
    "DISTINTO de GAP-EXEC3 (resume de un agente YA TERMINADO vía resumeAgent+metadata). "
    "Aterriza FIND-SIG13: un task canónico tiene dos abort controllers — "
    "currentWorkAbortController (corta el turno; el agente vive→SendMessage) vs abortController "
    "(mata el agente). TaskRecord no tiene cola pending_messages ni ese doble nivel.",
)
def test_running_agent_accepts_queued_messages():
    """Un subagente en ejecución debe poder recibir mensajes encolados (pendingMessages)
    drenados en el límite de ronda de tools."""
    fields = TaskRecord.__dataclass_fields__
    assert "pending_messages" in fields or "pending_input" in fields


# --- comprobación de aserción sobre estado global (no deja residuo) ----------

def test_registry_smoke_roundtrip():
    """InMemoryTaskRegistry: register→start→complete deja un record terminal consultable."""
    from agentic_runtime.execution.tasks.registry import InMemoryTaskRegistry

    reg = InMemoryTaskRegistry()
    rec = reg.register(description="probe", session_id="sess1")
    reg.start(rec.task_id, asyncio_task=None)
    assert reg.get(rec.task_id).status is TaskStatus.RUNNING
    reg.complete(rec.task_id, result="ok", turn_count=1)
    got = reg.get(rec.task_id)
    assert got.status is TaskStatus.COMPLETED and got.result == "ok"
    # aislamiento por sesión (espejo del tasks-dir per-sesión)
    assert reg.list_for("sess1") == [got]
    assert reg.list_for("other") == []
