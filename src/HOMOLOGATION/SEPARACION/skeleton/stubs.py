"""Realizaciones PASARELA de las costuras para A2.1 (SEAMS §5: "stubs passthrough").

Cero I/O, cero red, cero modelo real: el andamiaje debe TIPAR y CORRER con eventos
CANNED, de modo que el mecanismo del loop quede validado antes de enchufar el motor
real (A2.2). Cada stub nombra la costura que realiza y qué ciclo lo sustituye.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Mapping

from skeleton.contracts import (
    DoneEvent,
    Event,
    Message,
    TokenEvent,
    ToolCallEvent,
    ToolSchema,
    Usage,
)
from skeleton.seams import (
    AbortSignal,
    Notification,
    ProcessedInput,
    SessionId,
    StubToolContext,
)


class NullAbortSignal:
    """Realiza S2 (`AbortSignal`) — nunca abortado. A2.2+ lo reemplaza por
    `CombinedAbortSignal(ctx.stop)` que envuelve el `asyncio.Event` del turno."""

    @property
    def aborted(self) -> bool:
        return False


class PassthroughInputProcessor:
    """Realiza S11 (`UserInputProcessor`) — passthrough. La battery `commands` (A3·12)
    la sustituye por el preproceso real de slash/inline con short-circuit."""

    async def process(self, prompt: str, ctx: StubToolContext) -> ProcessedInput:
        return ProcessedInput(prompt=prompt, short_circuit=False)


class InMemorySessionRepo:
    """Realiza S20 (`SessionRepo`) — default base single-proceso. Guarda la metadata RICA
    del integrador bajo un `SessionId` OPACO autogenerado (`sess_<uuid>`); el base sólo
    recibe ese id y NUNCA la metadata. `list(query)` scopea por subconjunto de metadata —
    el integrador filtra por SU eje (owner/tenant), demostrando que la identidad vive en el
    repo, no en el runtime. El integrador complejo (agentic_assistant) sustituye por un
    repo multi-tenant sobre MinIO; la firma no cambia."""

    def __init__(self) -> None:
        self._meta: dict[SessionId, Mapping[str, object]] = {}

    def create(self, metadata: Mapping[str, object]) -> SessionId:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        self._meta[session_id] = dict(metadata)
        return session_id

    def get_metadata(self, session_id: SessionId) -> Mapping[str, object] | None:
        return self._meta.get(session_id)

    def list(self, query: Mapping[str, object]) -> list[SessionId]:
        return [
            sid
            for sid, meta in self._meta.items()
            if all(meta.get(k) == v for k, v in query.items())
        ]


class InMemoryNotificationSink:
    """Realiza S21 (`NotificationSink`) — default base single-proceso. El child (runner)
    hace `put`; el integrador `drain`. El integrador complejo (agentic_assistant) la sustituye
    por un sink persistente/multi-tenant; la firma no cambia. `scope` filtra por subconjunto
    de metadata futura (07·E19) — en A2.5 el shape aún no la lleva, así que un scope no vacío
    no casa (drena []) y un scope vacío/None drena todo. Drenar VACÍA lo drenado."""

    def __init__(self) -> None:
        self._notes: list[Notification] = []

    def put(self, note: Notification) -> None:
        self._notes.append(note)

    def drain(self, scope: Mapping[str, object] | None = None) -> list[Notification]:
        if scope:
            # El shape reducido de A2.5 no expone metadata scopeable ⇒ un scope concreto no
            # casa con nada (07·E19 enriquecerá `Notification` para habilitar el filtrado).
            return []
        out = list(self._notes)
        self._notes.clear()
        return out


class StubModelCaller:
    """Realiza S1 (`ModelCallerProtocol`) con eventos CANNED — SIN modelo real.

    A2.2 lo reemplaza por el bridge `AgenticModelsCaller` cableado a `agentic_models`
    y VALIDA/corrige la firma S1 con un turno real (SKELETON-REPORT). Aquí sólo emite
    un `TokenEvent` de eco + `DoneEvent`, suficiente para ejercitar el canal del loop.
    """

    def __init__(self, *, reply_prefix: str = "stub-echo: ") -> None:
        self._reply_prefix = reply_prefix

    def supports_native_tool_search(self) -> bool:
        return False

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model_id: str,
        stop: AbortSignal,  # el stub no lo consulta (nunca aborta).
        system_override: str | None = None,
        system_sections: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: Mapping[str, str] | None = None,
        effort: str | None = None,
    ) -> AsyncIterator[Event]:
        # El stub ignora los knobs enriquecidos (A2.2): sólo el bridge real los honra.
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"),
            "",
        )
        yield TokenEvent(text=self._reply_prefix + last_user, kind="text")
        yield DoneEvent(usage=Usage(input_tokens=0, output_tokens=0), stop_reason="end_turn")


class StubToolModelCaller:
    """Realiza S1 con un round-trip de tool CANNED — SIN modelo real. Ejercita el bucle
    multivuelta de `AgentLoop` (A2.3) de forma determinista:

    - vuelta 1 (aún no hay turno `tool` en el historial): pide la tool `tool_name` con
      `input` fijos y cierra con `stop_reason="tool_calls"`.
    - vuelta 2 (ya ve el `ToolResultMessage` aplanado): responde en texto citando el
      resultado y cierra con `end_turn`.

    Prueba OFFLINE el gate A2.3 ("el modelo llama la tool y el resultado se aplana");
    `bridge.AgenticModelsCaller` lo hace con un modelo REAL en `skeleton._tools`.
    """

    def __init__(
        self,
        *,
        tool_name: str = "add_numbers",
        tool_input: dict[str, object] | None = None,
        call_id: str = "call-canned-1",
    ) -> None:
        self._tool_name = tool_name
        self._tool_input = tool_input if tool_input is not None else {"a": 17, "b": 25}
        self._call_id = call_id

    def supports_native_tool_search(self) -> bool:
        return False

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        *,
        model_id: str,
        stop: AbortSignal,
        system_override: str | None = None,
        system_sections: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: Mapping[str, str] | None = None,
        effort: str | None = None,
    ) -> AsyncIterator[Event]:
        answered = any(m.role == "tool" for m in messages)
        if not answered:
            yield ToolCallEvent(
                call_id=self._call_id, name=self._tool_name, input=dict(self._tool_input)
            )
            yield DoneEvent(usage=Usage(input_tokens=0, output_tokens=0), stop_reason="tool_calls")
            return
        tool_output = next(
            (m.content for m in reversed(messages) if m.role == "tool"), ""
        )
        yield TokenEvent(text=f"El resultado es {tool_output}.", kind="text")
        yield DoneEvent(usage=Usage(input_tokens=0, output_tokens=0), stop_reason="end_turn")
