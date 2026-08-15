"""Fase 1 (plumbing) de la memoria: hook system-prompt + canal de recall.

Verifica el cableado genérico (cualquier provider lo aprovecha, también Skills S3):
- `system_prompt_section` de los providers llega al `system_sections` que ve el caller.
- `active_context` se rinde por turno como `role:"user"` envuelto en `<system-reminder>`,
  con dedup contra la historia ya presente.
- Un manager sin aporte no altera ni el system prompt ni la historia.
"""
from pathlib import Path

from agentic_runtime.capabilities import CapabilityManager
from agentic_runtime.capabilities.memory.provider import MemoryProvider
from agentic_runtime.capabilities.memory.store import FilesystemMemoryStore
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.identity import Scope
from agentic_runtime.events import DoneEvent
from agentic_runtime.loop.agent_loop import AgentLoop, _as_reminder

_PROMPT = "cómo va el despliegue"
_MEMORIA = """---
name: despliegue
description: notas del despliegue en produccion
metadata:
  type: project
---

cuerpo
"""


def _memory_manager(root: Path) -> CapabilityManager:
    directorio = root / "s" / "main"
    directorio.mkdir(parents=True)
    (directorio / "despliegue.md").write_text(_MEMORIA, encoding="utf-8")
    return CapabilityManager([MemoryProvider(FilesystemMemoryStore(root))])


def _memory_ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1", scope=Scope("s"))


def _recall_rendido(root: Path) -> str:
    ruta = root / "s" / "main" / "despliegue.md"
    return _as_reminder(
        f"Memoria posiblemente relevante — despliegue ({ruta}):\n"
        "notas del despliegue en produccion"
    )


class _FakeProvider:
    """Provider mínimo: aporta una sección de system prompt y un recall fijo."""

    name = "fake"

    def __init__(self, *, section: str | None = None, recall: list[dict] | None = None) -> None:
        self._section = section
        self._recall = recall or []

    async def startup(self) -> None: ...
    async def shutdown(self) -> None: ...
    def catalog(self, context): return []
    def tools(self, context): return []
    def active_context(self, context): return list(self._recall)
    def compact_context(self, context): return list(self._recall)

    def system_prompt_section(self, context):
        return self._section


class _CapturingCaller:
    """Caller compatible con ModelCallerProtocol que registra lo recibido por turno."""

    def __init__(self, *events) -> None:
        self._events = events
        self.system_sections_seen: list[list[str] | None] = []
        self.messages_seen: list[list[dict]] = []

    async def complete(self, messages, tools, *, stop=None, model_id="", system_sections=None):
        self.system_sections_seen.append(system_sections)
        self.messages_seen.append([dict(m) for m in messages])

        async def _gen():
            for ev in self._events:
                yield ev

        return _gen()


def _loop(manager: CapabilityManager, caller: _CapturingCaller) -> AgentLoop:
    return AgentLoop(model_caller=caller, capability_manager=manager)


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


# ---------------------------------------------------------------------------
# system_prompt_section → system_sections del caller
# ---------------------------------------------------------------------------

async def test_system_prompt_section_reaches_caller():
    manager = CapabilityManager([_FakeProvider(section="INSTRUCCIONES DE MEMORIA")])
    caller = _CapturingCaller(DoneEvent(stop_reason="stop"))
    await _loop(manager, caller).run("hola", _ctx())

    assert caller.system_sections_seen == [["INSTRUCCIONES DE MEMORIA"]]


async def test_sections_aggregate_in_registration_order():
    manager = CapabilityManager([
        _FakeProvider(section="A"),
        _FakeProvider(section=None),  # no aporta → se ignora
        _FakeProvider(section="B"),
    ])
    caller = _CapturingCaller(DoneEvent(stop_reason="stop"))
    await _loop(manager, caller).run("hola", _ctx())

    assert caller.system_sections_seen == [["A", "B"]]


async def test_no_section_means_no_system_sections():
    manager = CapabilityManager([_FakeProvider(section=None)])
    caller = _CapturingCaller(DoneEvent(stop_reason="stop"))
    await _loop(manager, caller).run("hola", _ctx())

    # Sin secciones, el loop no pasa el kwarg (robustez ante terceros).
    assert caller.system_sections_seen == [None]


def test_manager_tolerates_provider_without_hook():
    class _Bare:
        name = "bare"
        async def startup(self): ...
        async def shutdown(self): ...
        def catalog(self, c): return []
        def tools(self, c): return []
        def active_context(self, c): return []
        def compact_context(self, c): return []

    manager = CapabilityManager([_Bare()])
    assert manager.system_prompt_sections(_ctx()) == []


# ---------------------------------------------------------------------------
# active_context → recall como <system-reminder> role:"user", con dedup
# ---------------------------------------------------------------------------

async def test_recall_injected_as_user_system_reminder():
    recall = [{"role": "system", "content": "Memoria relevante X"}]
    manager = CapabilityManager([_FakeProvider(recall=recall)])
    caller = _CapturingCaller(DoneEvent(stop_reason="stop"))
    ctx = _ctx()
    await _loop(manager, caller).run("hola", ctx)

    reminders = [
        m for m in ctx.messages
        if m["role"] == "user" and "<system-reminder>" in m["content"]
    ]
    assert len(reminders) == 1
    assert "Memoria relevante X" in reminders[0]["content"]
    # El provider declaró role:"system"; el loop lo rinde como user (el caller lo descarta si no).
    assert reminders[0]["role"] == "user"


async def test_recall_no_se_reinyecta_si_ya_esta_en_la_historia(tmp_path):
    """Dedup contra un contenido YA presente (el caso de la historia recuperada).

    El dedup vive en el provider, no en el loop: el loop rinde lo que el manager le da.
    Por eso la prueba corre el `MemoryProvider` real, que es quien mira la historia."""
    manager = _memory_manager(tmp_path)
    caller = _CapturingCaller(DoneEvent(stop_reason="stop"))
    ctx = _memory_ctx()
    rendered = _recall_rendido(tmp_path)
    ctx.messages.append({"role": "user", "content": rendered})

    await _loop(manager, caller).run(_PROMPT, ctx)

    assert [m["content"] for m in ctx.messages].count(rendered) == 1


class _TwoTurnCaller(_CapturingCaller):
    """Primer turno `stop_reason="tool_calls"` (sin tool calls reales) ⇒ el loop reentra."""

    def __init__(self) -> None:
        super().__init__()
        self._n = 0

    async def complete(self, messages, tools, *, stop=None, model_id="", system_sections=None):
        self.system_sections_seen.append(system_sections)
        self.messages_seen.append([dict(m) for m in messages])
        self._n += 1
        primero = self._n == 1

        async def _gen():
            yield DoneEvent(stop_reason="tool_calls" if primero else "stop")

        return _gen()


async def test_recall_deduped_across_turns(tmp_path):
    """`_inject_recall` corre **por turno**, no por `run()`. Sin dedup real, un `run()` de
    N turnos mete el mismo recordatorio N veces y el contexto se llena de copias.

    **Reescrito**: la versión anterior se llamaba «across_turns» pero corría UN solo turno
    y pre-sembraba el mensaje a mano — media prueba con nombre de prueba entera. Aquí el
    loop da dos vueltas de verdad y el recall se emite en las dos, así que el dedup es lo
    único que puede evitar el duplicado."""
    manager = _memory_manager(tmp_path)
    caller = _TwoTurnCaller()
    ctx = _memory_ctx()

    await _loop(manager, caller).run(_PROMPT, ctx)

    assert len(caller.messages_seen) == 2, "hicieron falta dos turnos para que la prueba mida algo"
    rendered = _recall_rendido(tmp_path)
    assert [m["content"] for m in ctx.messages].count(rendered) == 1
    # …y el segundo turno tampoco lo vio duplicado al llamar al modelo.
    assert [m["content"] for m in caller.messages_seen[1]].count(rendered) == 1


async def test_empty_recall_leaves_history_untouched():
    manager = CapabilityManager([_FakeProvider(recall=[])])
    caller = _CapturingCaller(DoneEvent(stop_reason="stop"))
    ctx = _ctx()
    await _loop(manager, caller).run("hola", ctx)

    # Solo el prompt user; ningún reminder.
    assert all("<system-reminder>" not in m.get("content", "") for m in ctx.messages)
