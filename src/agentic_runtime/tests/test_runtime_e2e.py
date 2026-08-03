"""R7 — Integración E2E del runtime ensamblado vía `create_runtime()`.

A diferencia de test_runtime_v2 (primitivas cableadas a mano) y test_runtime_factory
(cableado del factory), aquí cada escenario ejerce el runtime COMPLETO tal como lo
arma `create_runtime()`: el consumidor solo inyecta caller/tools/storage por config.

Caller faux determinista (sin red). Las tres vías de D5 se demuestran al final.

Nota de alcance (Regla 3): SignalBus (cascada) y ModeManager (transición de modo) son
primitivas independientes aún NO cableadas en `_run_loop` (track BORDES B1-B4 pendiente);
su comportamiento se cubre en test_signal_bus.py / test_mode_manager.py. Aquí se cubre el
abort tal como está integrado hoy: `runtime.cancel()` → cancelación del asyncio.Task.
"""
from __future__ import annotations

import asyncio

import pytest

from agentic_runtime.contracts.runtime import RuntimeTask
from agentic_runtime.events import DoneEvent, TokenEvent, ToolCallEvent
from agentic_runtime.execution.fork import ForkSnapshot
from agentic_runtime.execution.local import LocalAgentRuntime
from agentic_runtime.execution.local.notification import drain_notifications
from agentic_runtime.execution.tasks.status import TaskStatus
from agentic_runtime.factory import (
    CapabilitiesConfig,
    RuntimeConfig,
    StorageConfig,
    ToolsConfig,
    create_runtime,
)
from agentic_runtime.tools import ToolCategory, ToolResult
from agentic_runtime.contracts.identity import Scope


# ──────────────────────────────────────────────────────────────────────────────
# Dobles deterministas
# ──────────────────────────────────────────────────────────────────────────────

class ScriptedCaller:
    """Caller faux: reproduce un guion fijo de eventos por turno.

    Registra los schemas de tools y los mensajes que recibe en cada turno para
    poder afirmar sobre lo que el loop expone al modelo.
    """

    def __init__(self, script: list[list]) -> None:
        self._script = script
        self._turn = 0
        self.seen_tools: list[list[str]] = []
        self.seen_messages: list[list] = []

    async def complete(self, messages, tools, *, stop=None, model_id=""):
        self.seen_tools.append([t["name"] for t in tools])
        self.seen_messages.append(list(messages))
        events = self._script[self._turn] if self._turn < len(self._script) else [DoneEvent(stop_reason="stop")]
        self._turn += 1

        async def _gen():
            for ev in events:
                yield ev
        return _gen()


class BlockingCaller:
    """Caller que bloquea indefinidamente para probar cancelación."""

    def __init__(self) -> None:
        self.entered = asyncio.Event()

    async def complete(self, messages, tools, *, stop=None, model_id=""):
        entered = self.entered

        async def _gen():
            entered.set()
            await asyncio.Event().wait()  # nunca resuelve
            yield DoneEvent()  # pragma: no cover
        return _gen()


class EchoTool:
    name = "echo"
    description = "Devuelve el texto recibido"
    input_schema: dict = {"type": "object", "properties": {"text": {"type": "string"}}}
    category = ToolCategory.UTILITY
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx) -> ToolResult:
        return ToolResult(tool_name=self.name, output=input.get("text", ""))


class GuardedTool:
    name = "guarded"
    description = "Requiere permiso explícito"
    input_schema: dict = {"type": "object", "properties": {}}
    category = ToolCategory.UTILITY
    requires_permission = True
    safe_for_background = False
    timeout_seconds = 5.0

    async def execute(self, input: dict, ctx) -> ToolResult:
        return ToolResult(tool_name=self.name, output="ok")


async def _await_task(runtime, task_id):
    rec = runtime._task_registry.get(task_id)
    if rec is not None and rec.asyncio_task is not None:
        await rec.asyncio_task


def _runtime(tmp_path, caller, *, tools=(), capabilities=None):
    return create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        tools=ToolsConfig(extras=list(tools)),
        capabilities=capabilities or CapabilitiesConfig(),
    ))


# ──────────────────────────────────────────────────────────────────────────────
# 1. Turno único sin tools
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_single_turn_no_tools(tmp_path):
    caller = ScriptedCaller([[TokenEvent(content="hola mundo"), DoneEvent(stop_reason="stop")]])
    runtime = _runtime(tmp_path, caller)
    task_id = await runtime.dispatch(RuntimeTask(prompt="saluda", description="single", session_id="sess-test"))
    await _await_task(runtime, task_id)
    assert runtime.status(task_id) == TaskStatus.COMPLETED
    assert runtime.result(task_id) == "hola mundo"


# ──────────────────────────────────────────────────────────────────────────────
# 2. Multi-turno con tool call vía ToolDispatcher
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_multi_turn_tool_call(tmp_path):
    caller = ScriptedCaller([
        [ToolCallEvent(tool_name="echo", tool_input={"text": "PONG"}, call_id="c1"),
         DoneEvent(stop_reason="tool_calls")],
        [TokenEvent(content="terminado"), DoneEvent(stop_reason="stop")],
    ])
    runtime = _runtime(tmp_path, caller, tools=(EchoTool(),))
    task_id = await runtime.dispatch(RuntimeTask(prompt="usa echo", description="multi", session_id="sess-test"))
    await _await_task(runtime, task_id)

    rec = runtime._task_registry.get(task_id)
    types = [e["type"] for e in rec.events]
    assert "tool_start" in types and "tool_result" in types
    assert any(e.get("output") == "PONG" for e in rec.events if e["type"] == "tool_result")
    # El resultado de la tool reingresó como contexto del 2º turno
    second_turn_roles = [m["role"] for m in caller.seen_messages[1]]
    assert "tool" in second_turn_roles
    assert runtime.result(task_id) == "terminado"


# ──────────────────────────────────────────────────────────────────────────────
# 2b. Primitiva de stream en vivo — surface eventos que rec.events descarta
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_stream_surfaces_full_event_sequence(tmp_path):
    from agentic_runtime.events import ToolResultEvent

    caller = ScriptedCaller([
        [ToolCallEvent(tool_name="echo", tool_input={"text": "PING"}, call_id="c1"),
         DoneEvent(stop_reason="tool_calls")],
        [TokenEvent(content="lis"), TokenEvent(content="to"), DoneEvent(stop_reason="stop")],
    ])
    runtime = _runtime(tmp_path, caller, tools=(EchoTool(),))

    events = [ev async for ev in runtime.stream(RuntimeTask(prompt="usa echo", description="stream", session_id="sess-test"))]

    types = [type(e).__name__ for e in events]
    # El stream surface TODO: tool call, tool result, tokens y cierres — no solo tool events.
    assert "ToolCallEvent" in types
    assert "ToolResultEvent" in types
    assert "TokenEvent" in types
    assert types[-1] == "DoneEvent"
    # Los TokenEvent (que rec.events NO captura) llegan por el stream y reconstruyen el texto.
    streamed = "".join(e.content for e in events if isinstance(e, TokenEvent))
    assert streamed == "listo"
    # El ToolResultEvent referencia el ToolCallEvent del stream.
    call_ids = {e.call_id for e in events if isinstance(e, ToolCallEvent)}
    assert all(e.call_id in call_ids for e in events if isinstance(e, ToolResultEvent))


# ──────────────────────────────────────────────────────────────────────────────
# 3. Abort / cancelación
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_cancel_kills_running_task(tmp_path):
    caller = BlockingCaller()
    runtime = _runtime(tmp_path, caller)
    task_id = await runtime.dispatch(RuntimeTask(prompt="bloquea", description="abort", session_id="sess-test"))
    await asyncio.wait_for(caller.entered.wait(), timeout=2.0)

    assert await runtime.cancel(task_id) is True
    rec = runtime._task_registry.get(task_id)
    with pytest.raises(asyncio.CancelledError):
        await rec.asyncio_task
    assert runtime.status(task_id) == TaskStatus.KILLED
    assert runtime.result(task_id) is None


# ──────────────────────────────────────────────────────────────────────────────
# 4. Subagente background → notificación + persistencia
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_background_subagent_notifies_and_persists(tmp_path):
    caller = ScriptedCaller([[TokenEvent(content="resultado hijo"), DoneEvent(stop_reason="stop")]])
    runtime = _runtime(tmp_path, caller)
    # La identidad de usuario del hijo viaja por el snapshot del padre (no por
    # task.owner_id, que un subagente no trae): así su transcript cae bajo user1.
    snap = ForkSnapshot(session_id="e2e-bg-sid", scope=Scope("user1"))
    task = RuntimeTask(prompt="trabaja", description="bg", session_id="sess-test")
    task_id = await runtime.dispatch(task, parent_snapshot=snap)
    await _await_task(runtime, task_id)

    notifs = drain_notifications("user1", "e2e-bg-sid")
    assert len(notifs) == 1
    assert notifs[0].status == "completed"
    assert notifs[0].final_text == "resultado hijo"

    keys = await runtime._storage.list_prefix("user1/e2e-bg-sid/subagents/")
    assert len(keys) == 1
    assert keys[0].endswith("/session.json")


# ──────────────────────────────────────────────────────────────────────────────
# 5. Fork → aislamiento de mensajes del padre
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_fork_isolates_parent_messages(tmp_path):
    caller = ScriptedCaller([[TokenEvent(content="hijo"), DoneEvent(stop_reason="stop")]])
    runtime = _runtime(tmp_path, caller)
    snap = ForkSnapshot(
        session_id="e2e-fork-sid",
        scope=Scope("user1"),
        messages=({"role": "user", "content": "SECRETO_DEL_PADRE"},),
    )
    task = RuntimeTask(prompt="trabaja aislado", description="fork", fork_context=False, session_id="sess-test")
    task_id = await runtime.dispatch(task, parent_snapshot=snap)
    await _await_task(runtime, task_id)
    drain_notifications("user1", "e2e-fork-sid")  # no contaminar el canal global

    first_turn = caller.seen_messages[0]
    assert not any("SECRETO_DEL_PADRE" in str(m.get("content", "")) for m in first_turn)
    assert first_turn[0]["content"] == "trabaja aislado"


# ──────────────────────────────────────────────────────────────────────────────
# 6. Capabilities — una tool que requiere permiso se anuncia (visibilidad ⟂ permiso)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_capabilities_announces_permissioned_tool(tmp_path):
    # Homologado al canónico: el anuncio ignora requires_permission. El gate de la tool
    # guarded vive en ejecución (dispatcher), no en su visibilidad.
    caller = ScriptedCaller([[TokenEvent(content="ok"), DoneEvent(stop_reason="stop")]])
    runtime = _runtime(tmp_path, caller, tools=(EchoTool(), GuardedTool()))
    task_id = await runtime.dispatch(RuntimeTask(prompt="x", description="caps", session_id="sess-test"))
    await _await_task(runtime, task_id)

    exposed = caller.seen_tools[0]
    assert "echo" in exposed       # sin permiso requerido → visible
    assert "guarded" in exposed    # requiere permiso pero se anuncia igual


# ──────────────────────────────────────────────────────────────────────────────
# 7. Capabilities — fuente externa lenta → resultado parcial, loop no se rompe
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_capabilities_partial_on_source_timeout(tmp_path):
    class SlowSource:
        async def list_schemas(self, ctx):
            await asyncio.sleep(1.0)
            return [{"name": "never", "description": "", "parameters": {}}]

    caller = ScriptedCaller([[TokenEvent(content="ok"), DoneEvent(stop_reason="stop")]])
    runtime = _runtime(
        tmp_path, caller, tools=(EchoTool(),),
        capabilities=CapabilitiesConfig(resolve_timeout_seconds=0.05),
    )
    runtime._capabilities_resolver.register_source(SlowSource())
    task_id = await runtime.dispatch(RuntimeTask(prompt="x", description="timeout", session_id="sess-test"))
    await _await_task(runtime, task_id)

    assert runtime.status(task_id) == TaskStatus.COMPLETED
    assert "echo" in caller.seen_tools[0]   # nativa presente pese al timeout
    assert "never" not in caller.seen_tools[0]


# ──────────────────────────────────────────────────────────────────────────────
# 8. D5 — las tres vías de provisión, sin modificar agentic_runtime/
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_d5_a_default_capabilities_used_as_is(tmp_path):
    """(a) Capacidad default: native tools disponibles sin registrar nada."""
    caller = ScriptedCaller([[TokenEvent(content="ok"), DoneEvent(stop_reason="stop")]])
    runtime = _runtime(tmp_path, caller)
    task_id = await runtime.dispatch(RuntimeTask(prompt="x", description="d5a", session_id="sess-test"))
    await _await_task(runtime, task_id)
    assert "read_file" in caller.seen_tools[0]
    assert runtime.status(task_id) == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_e2e_d5_b_custom_backend_via_factory(tmp_path):
    """(b) Implementación propia registrada por fábrica y resuelta por el runtime."""
    from agentic_runtime.storage import StorageRegistry
    from agentic_runtime.storage.filesystem import FilesystemStorage

    class TaggedStorage(FilesystemStorage):
        is_tagged = True

    StorageRegistry.register("tagged-e2e", TaggedStorage)
    caller = ScriptedCaller([[TokenEvent(content="ok"), DoneEvent(stop_reason="stop")]])
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="tagged-e2e", root=tmp_path),
        model_caller=caller,
    ))
    assert getattr(runtime._storage, "is_tagged", False) is True
    task_id = await runtime.dispatch(RuntimeTask(prompt="x", description="d5b", session_id="sess-test"))
    await _await_task(runtime, task_id)
    assert runtime.status(task_id) == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_e2e_d5_c_hand_composed_primitives(tmp_path):
    """(c) Primitivas compuestas a mano producen un runtime funcional."""
    from agentic_runtime.execution.tasks.registry import InMemoryTaskRegistry
    from agentic_runtime.storage.filesystem import FilesystemStorage
    from agentic_runtime.tools import ToolRegistry
    from agentic_runtime.tools.dispatcher import ToolDispatcher

    reg = ToolRegistry()
    reg.register(EchoTool())
    caller = ScriptedCaller([[TokenEvent(content="compuesto"), DoneEvent(stop_reason="stop")]])
    runtime = LocalAgentRuntime(
        model_caller=caller,
        tool_registry=reg,
        tool_dispatcher=ToolDispatcher(),
        task_registry=InMemoryTaskRegistry(),
        storage=FilesystemStorage(root=tmp_path),
    )
    task_id = await runtime.dispatch(RuntimeTask(prompt="x", description="d5c", session_id="sess-test"))
    await _await_task(runtime, task_id)
    assert runtime.result(task_id) == "compuesto"


# ──────────────────────────────────────────────────────────────────────────────
# `FIND-E11-1` — restringir el toolset del agente RAÍZ
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_el_integrador_puede_recortar_el_catalogo_del_agente_raiz(tmp_path):
    """`FIND-E11-1` REFORMULADO Y CERRADO: la costura EXISTE y está CABLEADA.

    El hallazgo decía «no existe costura para restringir las tools del agente RAÍZ».
    Contrastado contra el canónico, tenía dos mitades y ninguna se sostiene como estaba
    escrita:

    1. Que `initial_allowed_tools` sea ADITIVO y no recorte nada es **fiel a A**, no un
       defecto: `createGetAppStateWithAllowedTools` (`forkedAgent.ts:147-171`) también
       suma sobre `alwaysAllowRules.command` y no quita del catálogo. Era mi andamio de
       `E11` el que asumía lo contrario.
    2. Lo que A sí tiene es el recorte por DENY antes del anuncio —
       `filterToolsByDenyRules` dentro de `getTools()` (`tools.ts:262-268`, comentario
       literal: *"before the model sees them — not just at call time"*), alimentado por
       `alwaysDenyRules: { cliArg: parsedDisallowedToolsCli }` (`permissionSetup.ts:983`)
       y por `--base-tools`, que deniega todo lo que no esté en el set (`:900-910`).

    Y B lo tiene igual: `assemble_tool_pool` filtra por `denied_names()` **al ensamblar**
    (`tools/pool.py:59-73`), y el integrador llega hasta ahí por `root_context_modifier`,
    que corre sobre el ctx RAÍZ (`runtime.py:427-428`) antes de que el loop construya el
    pool del turno (`agent_loop.py:350`). Este test lo prueba CORRIENDO, sobre el runtime
    ensamblado por `create_runtime()` y midiendo lo que el caller **ve anunciado**, que es
    lo único que importa: una tool que el modelo no ve no la puede elegir.
    """
    def recortar(ctx, task):
        # Se DERIVA del PermissionContext vivo, no se construye uno nuevo: así el deny
        # se suma a lo que el integrador ya hubiera sembrado en vez de pisarlo.
        return ctx.with_permissions(
            ctx.app_state.permissions.model_copy(update={"always_deny": ["echo"]})
        )

    caller = ScriptedCaller([[TokenEvent(content="ok"), DoneEvent(stop_reason="stop")]])
    runtime = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path),
        model_caller=caller,
        tools=ToolsConfig(extras=[EchoTool(), GuardedTool()]),
        root_context_modifier=recortar,
    ))
    task_id = await runtime.dispatch(RuntimeTask(prompt="x", description="deny", session_id="sess-test"))
    await _await_task(runtime, task_id)

    assert runtime.status(task_id) == TaskStatus.COMPLETED
    anunciadas = caller.seen_tools[0]
    assert "echo" not in anunciadas, f"la tool denegada llegó al anuncio: {anunciadas}"
    # CONTROL POSITIVO: el recorte es SELECTIVO, no un catálogo vacío por accidente —
    # sin esto, un pool roto pasaría por «deny funcionando».
    assert "read_file" in anunciadas, f"el recorte se llevó por delante el catálogo: {anunciadas}"

    # CONTROL NEGATIVO en el MISMO escenario: sin el modifier, `echo` sí se anuncia.
    caller2 = ScriptedCaller([[TokenEvent(content="ok"), DoneEvent(stop_reason="stop")]])
    runtime2 = create_runtime(config=RuntimeConfig(
        storage=StorageConfig(backend="filesystem", root=tmp_path / "b"),
        model_caller=caller2,
        tools=ToolsConfig(extras=[EchoTool(), GuardedTool()]),
    ))
    tid2 = await runtime2.dispatch(RuntimeTask(prompt="x", description="sin-deny", session_id="sess-test"))
    await _await_task(runtime2, tid2)
    assert "echo" in caller2.seen_tools[0], (
        f"`echo` no se anunciaba ni sin deny: el test no probaba el recorte: {caller2.seen_tools[0]}"
    )
