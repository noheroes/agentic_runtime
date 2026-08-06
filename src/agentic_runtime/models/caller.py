"""
Concrete ModelCallerProtocol implementation backed by agentic_models.

Bridges agentic_runtime's dict-based message format to agentic_models Context
and maps agentic_models stream events to agentic_runtime event types.
"""
from __future__ import annotations

import json
from typing import Any, AsyncGenerator, Mapping

from ..contracts.abort import AbortSignal
from ..events.event_types import DoneEvent, ErrorEvent, TokenEvent, ToolCallEvent, Usage
from .protocol import (  # noqa: F401 — ModelCallerProtocol: satisfies Protocol
    Effort,
    ModelCallerProtocol,
    OutputFormat,
    ThinkingConfig,
    ToolChoice,
    UnsupportedModelOptionError,
)


def _compose_system_prompt(
    base: str | None,
    sections: list[str] | None,
) -> str | None:
    """Ensambla el system prompt base (integrador) + secciones (runtime).

    El runtime ensambla, el caller solo transporta. Mantener las secciones al final
    y en orden estable preserva un buen prefijo de caché entre turnos. Sin secciones
    el resultado es el base intacto (backward-compatible).
    """
    parts = [p for p in [base, *(sections or [])] if p]
    if not parts:
        return None
    return "\n\n".join(parts)


def _dict_messages_to_context(
    messages: list[dict],
    tools: list[dict],
    system_prompt: str | None,
) -> Any:
    """Convert dict messages + tool schemas to agentic_models.Context."""
    from agentic_models.model_types import (
        AssistantMessage,
        Context,
        TextContent,
        ThinkingContent,
        Tool,
        ToolCall,
        ToolResultMessage,
        UserMessage,
    )

    def _to_message(m: dict):
        role = m.get("role")
        content = m.get("content") or ""

        if role == "user":
            return UserMessage(content=content)

        if role == "assistant":
            parts: list[Any] = []
            if content:
                parts.append(TextContent(text=content))
            for tc in m.get("tool_calls") or []:
                fn = tc.get("function") or {}
                raw_args = fn.get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except Exception:
                    args = {}
                parts.append(ToolCall(
                    id=tc.get("id") or "",
                    name=fn.get("name") or "",
                    arguments=args,
                ))
            thinking = m.get("thinking")
            if thinking:
                parts.insert(0, ThinkingContent(thinking=thinking))
            return AssistantMessage(content=parts)

        if role == "tool":
            return ToolResultMessage(
                tool_call_id=m.get("tool_call_id") or "",
                tool_name=m.get("name") or "",
                content=[TextContent(text=content)] if content else [],
            )

        # system or unknown — skip (system goes into Context.system_prompt)
        return None

    typed_messages = [r for m in messages if (r := _to_message(m)) is not None]
    typed_tools = [
        Tool(
            name=t.get("name") or (t.get("function") or {}).get("name") or "",
            description=t.get("description") or (t.get("function") or {}).get("description") or "",
            parameters=(t.get("parameters") or (t.get("function") or {}).get("parameters") or {}),
            defer_loading=bool(t.get("defer_loading")),
        )
        for t in tools
    ]
    return Context(
        messages=typed_messages,
        system_prompt=system_prompt,
        tools=typed_tools,
    )


class AgenticModelsCaller:
    """
    ModelCallerProtocol implementation that delegates to agentic_models.stream().

    Usage:
        from agentic_models import get_model, register_builtins
        register_builtins()
        caller = AgenticModelsCaller(
            model=get_model("<model-id>"),  # el id lo elige el integrador; el runtime es multi-modelo
            api_key="sk-...",
        )
    """

    def __init__(
        self,
        model: Any,
        *,
        api_key: str | None = None,
        system_prompt: str | None = None,
        options: Any | None = None,
    ) -> None:
        self._model = model
        self._api_key = api_key
        self._system_prompt = system_prompt
        self._options = options  # agentic_models.StreamOptions override

    def supports_native_tool_search(self, model_id: str = "") -> bool:
        """Capability del Model activo: ¿el provider resuelve tools diferidas server-side?

        El loop la consulta para elegir la estrategia diferida (nativa vs simulada). Se
        resuelve dentro del provider del modelo del constructor (misma identidad (provider, id)
        que `complete`); un id desconocido cae al default sin romper (→ simulada por defecto)."""
        model = self._model
        if model_id:
            from agentic_models import get_registry
            try:
                model = get_registry().get_by_provider(self._model.provider, model_id)
            except Exception:
                model = self._model
        return bool(getattr(model, "native_tool_search", False))

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        stop: AbortSignal | None = None,
        model_id: str = "",
        system_sections: list[str] | None = None,
        system_override: str | None = None,
        thinking: ThinkingConfig | None = None,
        effort: Effort | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        output_format: OutputFormat | None = None,
        tool_choice: ToolChoice | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> AsyncGenerator[Any, None]:
        # Lo que este motor no sabe expresar se rechaza AQUÍ, antes de abrir el
        # stream: si se dejara pasar, el turno correría y devolvería algo que no
        # es lo pedido (texto libre donde se pidió schema, tool opcional donde se
        # exigió obligatoria) sin una sola señal.
        if output_format is not None:
            raise UnsupportedModelOptionError(
                "`output_format` (salida estructurada) no existe en agentic_models 0.2.0: "
                "no hay campo equivalente en StreamOptions ni en SimpleStreamOptions. "
                "Se rechaza en vez de descartarse en silencio."
            )
        if tool_choice is not None and tool_choice.mode != "auto":
            raise UnsupportedModelOptionError(
                f"`tool_choice.mode={tool_choice.mode!r}` no existe en agentic_models 0.2.0; "
                "sólo el comportamiento por defecto ('auto') es representable."
            )
        return self._stream(
            messages, tools, stop=stop, model_id=model_id,
            system_sections=system_sections, system_override=system_override,
            thinking=thinking, effort=effort, temperature=temperature,
            max_tokens=max_tokens, metadata=metadata,
        )

    async def _stream(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        stop: AbortSignal | None = None,
        model_id: str = "",
        system_sections: list[str] | None = None,
        system_override: str | None = None,
        thinking: ThinkingConfig | None = None,
        effort: Effort | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> AsyncGenerator[Any, None]:
        from agentic_models import stream, stream_simple
        from agentic_models.model_types import SimpleStreamOptions, StreamOptions

        # Subagente especializado (homologación subagent_type): su system prompt REEMPLAZA
        # el base del integrador (espejo getAgentSystemPrompt → [agentPrompt]); las secciones
        # del runtime se concatenan igual. `None`/`""` → base intacto del constructor.
        base = system_override if system_override else self._system_prompt
        context = _dict_messages_to_context(
            messages, tools, _compose_system_prompt(base, system_sections)
        )

        from dataclasses import fields, replace

        opts = self._options
        if opts is None:
            opts = StreamOptions()
        if self._api_key and not opts.api_key:
            opts = replace(opts, api_key=self._api_key)
        if stop is not None:
            # `signal` es lo que los providers consultan por `.aborted`. Con el tipo
            # viejo (`asyncio.Event`) esto viajaba igual y no lo leía nadie.
            opts = replace(opts, signal=stop)
        if temperature is not None:
            opts = replace(opts, temperature=temperature)
        if max_tokens is not None:
            opts = replace(opts, max_tokens=max_tokens)
        if metadata:
            # `ID-7`: opaca. Se funde con la que traiga el integrador en sus options
            # y no se lee por el camino — el runtime sólo la transporta.
            opts = replace(opts, metadata={**dict(opts.metadata or {}), **dict(metadata)})

        # Razonamiento: NO es passthrough. `agentic_models` sólo lo expone por
        # `stream_simple(SimpleStreamOptions.reasoning=…)`, así que el puente TRADUCE
        # (`SEAMS §S1 A2.2`). Un `thinking.enabled=False` apaga aunque venga `effort`.
        reasoning: str | None = effort.value if effort is not None else None
        if thinking is not None and not thinking.enabled:
            reasoning = None
        if thinking is not None and thinking.enabled and reasoning is None:
            raise UnsupportedModelOptionError(
                "`thinking` sin `effort`: agentic_models 0.2.0 sólo aplica "
                "`thinking_budgets` cuando hay un nivel `reasoning`, luego un "
                "presupuesto suelto se perdería. Pásese también `effort`."
            )

        if reasoning is not None:
            from agentic_models.model_types import ThinkingBudgets

            if not isinstance(opts, SimpleStreamOptions):
                opts = SimpleStreamOptions(
                    **{f.name: getattr(opts, f.name) for f in fields(StreamOptions)}
                )
            budgets = opts.thinking_budgets
            if thinking is not None and thinking.budget_tokens is not None:
                # El techo pedido se aplica al nivel que se vaya a usar; se puebla
                # todo el mapa porque el provider clampa el nivel (`xhigh → high`)
                # y elegiría un presupuesto distinto del pedido.
                b = thinking.budget_tokens
                budgets = ThinkingBudgets(minimal=b, low=b, medium=b, high=b)
            opts = replace(opts, reasoning=reasoning, thinking_budgets=budgets)

        # Resolución del modelo por request: model_id manda; el del constructor es el default.
        # La identidad canónica de agentic_models es (provider, id): el mismo id existe en
        # varios providers. El puente es mono-provider por construcción (un solo api_key, un
        # solo modelo default), así que se resuelve DENTRO del provider del modelo del
        # constructor — resolver solo por id es ambiguo y podría devolver un Model de otro
        # provider cuyo api_key no corresponde. Un model_id desconocido en ese provider es un
        # error explícito (get_by_provider lanza ModelNotFoundError), no se cae al default.
        model = self._model
        if model_id:
            from agentic_models import get_registry
            model = get_registry().get_by_provider(self._model.provider, model_id)

        event_stream = (
            stream_simple(model, context, opts)  # type: ignore[arg-type]
            if reasoning is not None
            else stream(model, context, opts)
        )

        # Providers push dicts; match on the "type" key
        async for event in event_stream:
            t = event.get("type") if isinstance(event, dict) else getattr(event, "type", None)

            if t == "text_delta":
                delta = event["delta"] if isinstance(event, dict) else event.delta
                yield TokenEvent(content=delta)

            elif t == "toolcall_end":
                # Dos grafías vivas del mismo campo: los providers empujan dicts
                # camelCase (`toolCall`) y el dataclass de agentic_models 0.2.0 lo
                # llama `tool_call`. Se aceptan ambas — quedarse con una sola
                # rompería en silencio el día que el emisor cambie de forma.
                if isinstance(event, dict):
                    tc = event.get("toolCall") or event["tool_call"]
                else:
                    tc = getattr(event, "toolCall", None) or event.tool_call
                yield ToolCallEvent(
                    tool_name=tc.name,
                    tool_input=tc.arguments,
                    call_id=tc.id,
                )

            elif t == "done":
                msg = event["message"] if isinstance(event, dict) else event.message
                reason = event.get("reason") if isinstance(event, dict) else getattr(event, "reason", "stop")
                u = msg.usage
                yield DoneEvent(
                    stop_reason="tool_calls" if reason == "toolUse" else (reason or "stop"),
                    usage=Usage(
                        input_tokens=u.input,
                        output_tokens=u.output,
                        thinking_tokens=0,
                    ),
                )
                return

            elif t == "error":
                err = event.get("error") if isinstance(event, dict) else event.error
                msg_text = (
                    getattr(err, "error_message", None) or str(err)
                    if err is not None else "stream error"
                )
                yield ErrorEvent(message=msg_text)
                return

            # start, text_start, text_end, thinking_*, tool_call_start/delta — skip
