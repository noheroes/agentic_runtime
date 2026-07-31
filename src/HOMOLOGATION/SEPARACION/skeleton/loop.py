"""`AgentLoop` — el MECANISMO del turno (T2-BASE-MECANISMO, BLUEPRINT §1.3).

El canónico lo fusiona en `query.ts` (1729 LOC); B lo des-fusiona en un loop DELGADO
que invoca costuras. A2.1 = esqueleto mínimo (S11 → S1 → S5, sin tools). **A2.3 inserta
el bucle MULTIVUELTA**: cuando el modelo pide una tool (`ToolCallEvent` + stop_reason
`tool_calls`), el loop despacha (S16 vía `ToolDispatcher`) y RE-ENTRA al modelo con el
`ToolResultEvent` aplanado — el turno pasa a ser multi-vuelta hasta un `end_turn` o el
tope de vueltas. Sin tools (pool vacío) el comportamiento es idéntico a A2.2 (una vuelta).

SIN motores de compactación/budget/retry (A2.4/battery).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from skeleton.contracts import (
    CompactBoundaryEvent,
    DoneEvent,
    Event,
    Message,
    ResultEvent,
    RuntimeTask,
    ToolCall,
    ToolCallEvent,
    TokenEvent,
    Usage,
)
from skeleton.seams import (
    AbortSignal,
    CompactionMotor,
    ModelCallerProtocol,
    StubToolContext,
    UserInputProcessor,
)
from skeleton.tools import (
    DeferredToolStrategy,
    EagerToolStrategy,
    ToolDispatcher,
    ToolPool,
)

EventSink = Callable[[Event], None]

_DEFAULT_MAX_TURNS = 8  # tope de seguridad del bucle multivuelta (evita loops infinitos).


def _accumulate(total: Usage, turn: Usage) -> Usage:
    """Suma el usage de cada vuelta del modelo (un turno multivuelta = varias llamadas)."""
    return Usage(
        input_tokens=total.input_tokens + turn.input_tokens,
        output_tokens=total.output_tokens + turn.output_tokens,
        cache_read=total.cache_read + turn.cache_read,
        cache_write=total.cache_write + turn.cache_write,
        total_tokens=total.total_tokens + turn.total_tokens,
        cost_usd=total.cost_usd + turn.cost_usd,
    )


class AgentLoop:
    """Un turno = una llamada a `run`. Costuras inyectadas por constructor (S27 deps-DI)."""

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
        max_turns: int = _DEFAULT_MAX_TURNS,
    ) -> None:
        self._caller = caller
        self._input_processor = input_processor
        self._model_id = model_id
        self._system_prompt = system_prompt
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._metadata = metadata
        # Battery de compactación (S9), OPCIONAL. `None` = base sin battery ⇒ trigger no
        # dispara ⇒ comportamiento idéntico a A2.3. El base sólo conoce el Protocol
        # `CompactionMotor`; la battery concreta la inyecta el integrador (A2.4).
        self._compaction = compaction
        # Tools (A2.3). Pool vacío por defecto ⇒ ninguna tool anunciada ⇒ una sola vuelta
        # (idéntico a A2.2). `dispatcher` se deriva del pool si no se inyecta.
        self._tool_pool = tool_pool if tool_pool is not None else ToolPool()
        self._dispatcher = (
            dispatcher if dispatcher is not None else ToolDispatcher(self._tool_pool)
        )
        self._strategy: DeferredToolStrategy = (
            strategy if strategy is not None else EagerToolStrategy()
        )
        self._max_turns = max_turns

    async def run(
        self,
        task: RuntimeTask,
        *,
        emit: EventSink,
        stop: AbortSignal,
        ctx: StubToolContext,
    ) -> ResultEvent:
        model_id = task.model_override or self._model_id

        # 1) preproceso de entrada (S11). Un slash-command resuelto corta el turno.
        processed = await self._input_processor.process(task.prompt, ctx)
        if processed.short_circuit:
            result = ResultEvent(text=processed.result_text or "", usage=Usage())
            emit(result)
            return result

        # 2) historial inicial + tools anunciadas (S26 decide el subconjunto; eager = todo).
        messages: list[Message] = [Message(role="user", content=processed.prompt)]
        announced = self._strategy.filter_announced(self._tool_pool, frozenset())
        max_turns = task.max_turns if task.max_turns is not None else self._max_turns

        final_text = ""
        total = Usage()

        # 3) bucle MULTIVUELTA: pedir una vuelta, consumir el canal, y si el modelo pidió
        #    tools, despacharlas y re-entrar; si no, cerrar el turno.
        for _turn in range(max_turns):
            # Trigger LR1 (base-mecanismo, canónico `agent_loop.py:189`): en la frontera
            # de vuelta, si hay battery compuesta Y decide compactar, el base funde el
            # historial vía el MOTOR (S9) y emite la frontera — SIN conocer la battery.
            if self._compaction is not None and self._compaction.should_compact(messages, total):
                boundary = self._compaction.compact(messages)
                if boundary.collapsed > 0:
                    messages = boundary.messages
                    emit(CompactBoundaryEvent(collapsed=boundary.collapsed, reason=boundary.reason))

            turn_text: list[str] = []
            pending: list[ToolCall] = []
            usage = Usage()
            stop_reason = "end_turn"

            async for event in self._caller.complete(
                messages,
                announced,
                model_id=model_id,
                stop=stop,
                system_override=self._system_prompt,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                metadata=self._metadata,
            ):
                emit(event)
                if isinstance(event, TokenEvent) and event.kind == "text":
                    turn_text.append(event.text)
                elif isinstance(event, ToolCallEvent):
                    pending.append(
                        ToolCall(call_id=event.call_id, name=event.name, input=event.input)
                    )
                elif isinstance(event, DoneEvent):
                    usage = event.usage
                    stop_reason = event.stop_reason

            total = _accumulate(total, usage)
            final_text = "".join(turn_text)

            # A2.3: si no hay tools que despachar, el turno termina.
            if stop_reason != "tool_calls" or not pending:
                break

            # A2.3: re-inyectar el turno assistant (texto + tool_use) y despachar cada tool
            #       (S16), aplanando el resultado a un turno `tool` que re-entra al modelo.
            messages.append(
                Message(role="assistant", content=final_text, tool_calls=tuple(pending))
            )
            for call in pending:
                result_evt = await self._dispatcher.dispatch(call, ctx)
                emit(result_evt)
                messages.append(
                    Message(
                        role="tool",
                        content=result_evt.output,
                        tool_call_id=call.call_id,
                        tool_name=call.name,
                        is_error=result_evt.is_error,
                    )
                )

        # 4) `ResultEvent` terminal (07·D1/D2). `usage` acumula todas las vueltas.
        result = ResultEvent(text=final_text, usage=total)
        emit(result)
        return result
