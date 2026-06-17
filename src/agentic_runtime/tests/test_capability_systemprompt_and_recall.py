"""Fase 1 (plumbing) de la memoria: hook system-prompt + canal de recall.

Verifica el cableado genérico (cualquier provider lo aprovecha, también Skills S3):
- `system_prompt_section` de los providers llega al `system_sections` que ve el caller.
- `active_context` se rinde por turno como `role:"user"` envuelto en `<system-reminder>`,
  con dedup contra la historia ya presente.
- Un manager sin aporte no altera ni el system prompt ni la historia.
"""
from agentic_runtime.capabilities import CapabilityManager
from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.events import DoneEvent
from agentic_runtime.loop.agent_loop import AgentLoop


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


async def test_recall_deduped_across_turns():
    recall = [{"role": "system", "content": "Memoria relevante X"}]
    manager = CapabilityManager([_FakeProvider(recall=recall)])
    # Dos turnos: el modelo pide una tool-call inexistente (sin dispatcher → sigue) y luego termina.
    caller = _CapturingCaller(DoneEvent(stop_reason="stop"))
    ctx = _ctx()
    # Forzamos un segundo turno reusando el loop con el mismo ctx no aplica; en su lugar
    # pre-sembramos el reminder ya presente y comprobamos que no se duplica.
    rendered = "<system-reminder>\nMemoria relevante X\n</system-reminder>"
    ctx.messages.append({"role": "user", "content": rendered})

    await _loop(manager, caller).run("hola", ctx)

    reminders = [m for m in ctx.messages if m["content"] == rendered]
    assert len(reminders) == 1  # no se reinyecta el ya presente


async def test_empty_recall_leaves_history_untouched():
    manager = CapabilityManager([_FakeProvider(recall=[])])
    caller = _CapturingCaller(DoneEvent(stop_reason="stop"))
    ctx = _ctx()
    await _loop(manager, caller).run("hola", ctx)

    # Solo el prompt user; ningún reminder.
    assert all("<system-reminder>" not in m.get("content", "") for m in ctx.messages)
