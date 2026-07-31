"""`LocalAgentRuntime` — realiza la façade S4 (AgentRuntime) sobre el bus S5 + loop.

A2.1: `stream(task)` = canal único ordenado (07·A2) que emite `InitEvent` -> eventos del
loop -> `ResultEvent`. A2.5 completa la façade S4: `dispatch`/`status`/`result` quedan
COHERENTES bajo el MISMO `task_id` (antes `dispatch` guardaba el resultado bajo un id
distinto ⇒ `result()` devolvía None), y el runtime threadea las costuras S18 (`runner`) y
S21 (`notifier`) al `ctx` del turno para que el `AgentTool` pueda SPAWNEAR un subagente.
El `spawn` de subagentes se realiza (S18 vía `AgentTool`→`LocalSubagentRunner`); `fork`
(hijo que hereda historial) y `reaping` de recursos (S23 teardown) se difieren a Fase C/F.
`cancel` (S2 abort) → 08·signals. El runtime lee sólo ids OPACOS (`owner_id`/`session_id`).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Mapping

from skeleton.contracts import (
    Event,
    InitEvent,
    ResultEvent,
    RuntimeTask,
    TaskStatus,
)
from skeleton.events import EventBus
from skeleton.loop import AgentLoop
from skeleton.seams import (
    AbortSignal,
    CompactionMotor,
    ModelCallerProtocol,
    NotificationSink,
    StubToolContext,
    SubagentRunnerProtocol,
    UserInputProcessor,
)
from skeleton.stubs import NullAbortSignal
from skeleton.tools import DeferredToolStrategy, ToolDispatcher, ToolPool


class LocalAgentRuntime:
    """Base default de S4. El integrador complejo (agentic_assistant) puede sustituirla."""

    def __init__(
        self,
        *,
        caller: ModelCallerProtocol,
        input_processor: UserInputProcessor,
        model_id: str = "stub-model",
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: Mapping[str, str] | None = None,
        tool_pool: ToolPool | None = None,
        dispatcher: ToolDispatcher | None = None,
        strategy: DeferredToolStrategy | None = None,
        compaction: CompactionMotor | None = None,
        runner: SubagentRunnerProtocol | None = None,
        notifier: NotificationSink | None = None,
    ) -> None:
        # S18/S21 — el factory las inyecta; `stream` las threadea al `ctx` del turno para
        # que el `AgentTool` pueda spawnear (runner) y el child publicar notificaciones.
        self._runner = runner
        self._notifier = notifier
        self._loop = AgentLoop(
            caller=caller,
            input_processor=input_processor,
            model_id=model_id,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
            tool_pool=tool_pool,
            dispatcher=dispatcher,
            strategy=strategy,
            compaction=compaction,
        )
        self._model_id = model_id
        self._results: dict[str, ResultEvent] = {}
        self._status: dict[str, TaskStatus] = {}

    async def stream(
        self,
        task: RuntimeTask,
        *,
        stop: AbortSignal | None = None,
        task_id: str | None = None,
    ) -> AsyncIterator[Event]:
        # `task_id` opcional: `dispatch` pasa el SUYO para que status/result queden coherentes
        # bajo el MISMO id (antes `dispatch` guardaba el resultado bajo un id distinto → bug).
        task_id = task_id if task_id is not None else uuid.uuid4().hex
        self._status[task_id] = TaskStatus.RUNNING
        abort = stop if stop is not None else NullAbortSignal()

        # Bus in-proc; convertimos emit -> async yield vía un buffer ordenado.
        bus = EventBus()
        buffer: list[Event] = []
        unsubscribe = bus.subscribe_all(buffer.append)

        try:
            bus.emit(InitEvent(task_id=task_id, model_id=task.model_override or self._model_id))
            # A2.5: el ctx porta las costuras S18/S21 (el `AgentTool` lee `ctx.runner`).
            ctx = StubToolContext(task=task, runner=self._runner, notifier=self._notifier)
            # El loop llena el buffer vía emit; drenamos tras completar (turno síncrono
            # en A2.1 — el streaming incremental real llega con el motor en A2.2).
            result = await self._loop.run(task, emit=bus.emit, stop=abort, ctx=ctx)
            self._results[task_id] = result
            self._status[task_id] = TaskStatus.COMPLETED
        finally:
            unsubscribe()

        for event in buffer:
            yield event

    async def dispatch(self, task: RuntimeTask) -> str:
        # S4 façade completa (A2.5): corre el turno bajo un task_id propio y deja status/result
        # consultables bajo ESE id. (Los subagentes se spawnan por S18/`AgentTool`, no por aquí;
        # el registro rico TaskRegistry S19 + background force-async S22 → Fase F.)
        task_id = uuid.uuid4().hex
        self._status[task_id] = TaskStatus.PENDING
        async for _ in self.stream(task, task_id=task_id):
            pass
        return task_id

    def status(self, task_id: str) -> TaskStatus:
        return self._status.get(task_id, TaskStatus.PENDING)

    def result(self, task_id: str) -> ResultEvent | None:
        return self._results.get(task_id)
