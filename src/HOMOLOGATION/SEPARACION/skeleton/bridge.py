"""S1 · `AgenticModelsCaller` — bridge REAL al motor `agentic_models` (T1-MOTOR).

Ciclo **A2.2**: reemplaza `StubModelCaller` (eventos canned) por la costura crítica
cableada al motor con un TURNO REAL texto-solo. Es el consumidor por-defecto de
`ModelCallerProtocol` (SEAMS §S1: "battery por defecto `caller.py`"); aquí en versión
clean-room B, destilada de la mímica `models/caller.py` pero **corregida** por lo que el
turno real reveló (ver `seams.ModelCallerProtocol` docstring y `../SKELETON-REPORT` A2.5):

- La mímica pasaba `stop: asyncio.Event` a `StreamOptions.signal`; el provider chequea
  `getattr(signal, "aborted", False)` (anthropic.py:717/732) ⇒ `asyncio.Event` (sin
  `.aborted`) ignora el abort (16·A6). Aquí `stop: AbortSignal` **tiene** `.aborted` ⇒
  la forma correcta de la costura S2. (No ejercitado por el turno feliz de A2.2.)
- La mímica descartaba `usage.cache_read/cache_write/cost` y fabricaba `thinking_tokens=0`.
  Aquí `Usage` espeja el motor: cache/coste reales; sin `thinking_tokens`.

`agentic_models` no publica tipos (sin `py.typed`): sus símbolos entran como `Any`
(`type: ignore[import-untyped]`) para que `mypy --strict` del spike siga en 0 sin
que las llamadas al motor cuenten como "untyped calls".
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from typing import Any

from agentic_models import get_registry, stream
from agentic_models.model_types import (
    AssistantMessage,
    Context,
    StreamOptions,
    TextContent,
    Tool,
    ToolResultMessage,
    UserMessage,
)
from agentic_models.model_types import ToolCall as AmToolCall

from skeleton.contracts import (
    DoneEvent,
    ErrorEvent,
    Event,
    Message,
    ThinkingEvent,
    TokenEvent,
    ToolCallEvent,
    ToolSchema,
    Usage,
)
from skeleton.seams import AbortSignal


def _compose_system_prompt(base: str | None, sections: list[str] | None) -> str | None:
    """Ensambla base (integrador) + secciones (runtime). El runtime ensambla, el caller
    sólo transporta; secciones al final preservan el prefijo de caché (mímica caller.py:17)."""
    parts = [p for p in [base, *(sections or [])] if p]
    return "\n\n".join(parts) if parts else None


def _to_message(m: Message) -> Any:
    """skeleton.Message → mensaje del motor. A2.3 cablea el round-trip completo:
    - `user`      → `UserMessage`.
    - `assistant` → `AssistantMessage` con `TextContent` (si hay texto) + `ToolCall`
      por cada `tool_use` pedido — reproduce el turno que el modelo emitió, requisito
      del protocolo Anthropic para poder responder con `tool_result`.
    - `tool`      → `ToolResultMessage` (el `tool_call_id` casa con el `tool_use`;
      el provider lo mapea a `tool_use_id`, anthropic.py:213)."""
    if m.role == "assistant":
        content: list[Any] = []
        if m.content:
            content.append(TextContent(text=m.content))
        for tc in m.tool_calls:
            content.append(AmToolCall(id=tc.call_id, name=tc.name, arguments=dict(tc.input)))
        return AssistantMessage(content=content)
    if m.role == "tool":
        return ToolResultMessage(
            tool_call_id=m.tool_call_id or "",
            tool_name=m.tool_name or "",
            content=[TextContent(text=m.content)],
            is_error=m.is_error,
        )
    return UserMessage(content=m.content)


def _to_context(
    messages: list[Message],
    tools: list[ToolSchema],
    system_prompt: str | None,
) -> Any:
    """skeleton.Message → agentic_models.Context. Los tres roles del round-trip A2.3
    (user/assistant-con-tool_use/tool) se traducen por `_to_message`."""
    typed_messages: list[Any] = [_to_message(m) for m in messages]
    typed_tools: list[Any] = [
        Tool(name=t.name, description=t.description, parameters=t.input_schema)
        for t in tools
    ]
    return Context(
        messages=typed_messages,
        system_prompt=system_prompt,
        tools=typed_tools,
    )


class AgenticModelsCaller:
    """Realiza S1 delegando en `agentic_models.stream()`. Mono-provider por construcción
    (un `api_key`, un `model` default); un `model_id` por-request se re-resuelve DENTRO del
    provider del modelo del constructor (identidad canónica = (provider, id))."""

    def __init__(
        self,
        model: Any,
        *,
        api_key: str | None = None,
        client: Any | None = None,
        on_payload: Any | None = None,
    ) -> None:
        self._model = model
        self._api_key = api_key
        # `client` = cliente de motor pre-construido (`options.client`). Necesario para
        # OAUTH con anthropic-sdk 0.109.1 — ver HALLAZGO A2.2 en `complete`.
        self._client = client
        # `on_payload` = hook de observabilidad de `StreamOptions` (anthropic.py:573-576):
        # recibe el dict `params` EXACTO que va al SDK antes del envío. Seam legítimo del
        # motor; A2.2 lo usa para VERIFICAR el efecto-en-cable de temperature/max_tokens/metadata.
        self._on_payload = on_payload

    def supports_native_tool_search(self) -> bool:  # 16·A8
        return bool(getattr(self._model, "native_tool_search", False))

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
        effort: str | None = None,  # CORRECCIÓN A2.2: NO viaja por StreamOptions (ver seams.py). No ejercitado texto-solo.
    ) -> AsyncIterator[Event]:
        context = _to_context(
            messages, tools, _compose_system_prompt(system_override, system_sections)
        )

        # Reparto VALIDADO (anthropic._build_params): temperature/max_tokens/metadata/signal
        # viajan por StreamOptions; el resto es duck-typing (no aplicable a texto-solo).
        opts = StreamOptions(signal=stop)
        # HALLAZGO A2.2 (integración OAuth · anthropic-sdk 0.109.1): la rama oauth de
        # `agentic_models._create_client` (anthropic.py:396-411) construye el cliente con
        # `api_key="dummy"` + `auth_token`. Ese SDK emite AMBOS `X-Api-Key: dummy` y
        # `Authorization: Bearer` (auth_headers), y el server rechaza por x-api-key (401).
        # Anular `x-api-key` vía headers TAMPOCO sirve (el SDK rechaza header con valor None).
        # Resolución validada por el turno real: inyectar un cliente pre-construido
        # (`AsyncAnthropic(auth_token=..., default_headers={betas oauth+CC})`, SIN api_key) por
        # `options.client` ⇒ sólo Bearer. Arreglar de raíz en Fase D (agentic_models: la rama
        # oauth debe omitir api_key). `options.client` fuerza is_oauth=False en el motor, así
        # que el system-prompt CC y las betas oauth los provee el cliente/llamador (ver _motor).
        if self._client is not None:
            opts.client = self._client
        elif self._api_key:
            opts.api_key = self._api_key
        if temperature is not None:
            opts.temperature = temperature
        if max_tokens is not None:
            opts.max_tokens = max_tokens
        if metadata:
            opts.metadata = dict(metadata)  # el provider sólo reenvía user_id 【id-opaco】
        if self._on_payload is not None:
            opts.on_payload = self._on_payload

        model = self._model
        if model_id and model_id != getattr(self._model, "id", ""):
            model = get_registry().get_by_provider(self._model.provider, model_id)

        # Providers empujan DICTS; se casa por la clave "type" (mímica caller.py:206-245).
        async for raw in stream(model, context, opts):
            event: Any = raw
            etype = event["type"] if isinstance(event, dict) else getattr(event, "type", "")

            if etype == "text_delta":
                delta = event["delta"] if isinstance(event, dict) else event.delta
                yield TokenEvent(text=delta, kind="text")

            elif etype == "thinking_delta":  # no aplica a texto-solo; mapeado por completitud
                tdelta = event["delta"] if isinstance(event, dict) else event.delta
                yield ThinkingEvent(text=tdelta)

            elif etype == "toolcall_end":  # dispatch = A2.3; aquí se aplana el shape
                tc = event["toolCall"] if isinstance(event, dict) else event.toolCall
                yield ToolCallEvent(call_id=tc.id, name=tc.name, input=tc.arguments)

            elif etype == "done":
                msg = event["message"] if isinstance(event, dict) else event.message
                reason = (
                    event.get("reason") if isinstance(event, dict) else getattr(event, "reason", "stop")
                ) or "stop"
                u = msg.usage
                yield DoneEvent(
                    usage=Usage(
                        input_tokens=u.input,
                        output_tokens=u.output,
                        cache_read=u.cache_read,
                        cache_write=u.cache_write,
                        total_tokens=u.total_tokens,
                        cost_usd=u.cost.total,
                    ),
                    stop_reason="tool_calls" if reason == "toolUse" else reason,
                )
                return

            elif etype == "error":
                err: Any = event.get("error") if isinstance(event, dict) else event.error
                message: str = (
                    getattr(err, "error_message", None) or "stream error"
                    if err is not None
                    else "stream error"
                )
                yield ErrorEvent(code=reason_if_aborted(event), message=message)
                return


def reason_if_aborted(event: Any) -> str:
    """07·D5 / 16·C1 — `code` tipado, no colapsar a str. `error` vs `aborted`."""
    reason = event.get("reason") if isinstance(event, dict) else getattr(event, "reason", "error")
    return reason or "error"
