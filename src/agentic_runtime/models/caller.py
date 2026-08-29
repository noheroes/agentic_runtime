from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Mapping
from typing import Any

from ..context.estimation import rough_token_count
from ..contracts.abort import AbortSignal
from ..events.event_types import (
    THINKING_TOKENS_SOURCE_COUNTED,
    THINKING_TOKENS_SOURCE_PROVIDER,
    THINKING_TOKENS_SOURCE_UNAVAILABLE,
    DoneEvent,
    ErrorEvent,
    ThinkingEvent,
    TokenEvent,
    ToolCallEvent,
    Usage,
)
from .protocol import (  # noqa: F401
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
    parts = [p for p in [base, *(sections or [])] if p]
    if not parts:
        return None
    return "\n\n".join(parts)


def _dict_messages_to_context(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    system_prompt: str | None,
    model: Any = None,
) -> Any:
    model_id = getattr(model, "id", "") or ""
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

    def _to_message(m: dict[str, Any]) -> Any:
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
                except Exception:  # noqa: BLE001
                    args = {}
                parts.append(ToolCall(
                    id=tc.get("id") or "",
                    name=fn.get("name") or "",
                    arguments=args,
                ))
            blocks = m.get("thinking_blocks") or []
            reasoning: list[Any] = []
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                origin = block.get("model_id") or ""
                if model_id and origin and origin != model_id:
                    continue
                reasoning.append(ThinkingContent(
                    thinking=block.get("thinking") or "",
                    thinking_signature=block.get("signature") or None,
                ))
            if not reasoning and (thinking := m.get("thinking")):
                reasoning.append(ThinkingContent(thinking=thinking))
            parts[:0] = reasoning
            rebuilt = AssistantMessage(content=parts)
            if model is not None:
                rebuilt.model = model_id
                rebuilt.provider = getattr(model, "provider", "") or ""
                rebuilt.api = getattr(model, "api", "") or ""
            return rebuilt

        if role == "tool":
            return ToolResultMessage(
                tool_call_id=m.get("tool_call_id") or "",
                tool_name=m.get("name") or "",
                content=[TextContent(text=content)] if content else [],
            )

        return None

    typed_messages = [r for m in messages if (r := _to_message(m)) is not None]
    typed_tools = [
        Tool(
            name=t.get("name") or (t.get("function") or {}).get("name") or "",
            description=t.get("description") or (t.get("function") or {}).get("description") or "",
            parameters=(t.get("parameters") or (t.get("function") or {}).get("parameters") or {}),
        )
        for t in tools
    ]
    return Context(
        messages=typed_messages,
        system_prompt=system_prompt,
        tools=typed_tools,
    )


class AgenticModelsCaller:

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
        self._options = options

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
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
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
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

        base = system_override if system_override else self._system_prompt

        model = self._model
        if model_id:
            from agentic_models import get_registry
            model = get_registry().get_by_provider(self._model.provider, model_id)

        context = _dict_messages_to_context(
            messages, tools, _compose_system_prompt(base, system_sections), model
        )

        from dataclasses import fields, replace

        opts = self._options
        if opts is None:
            opts = StreamOptions()
        if self._api_key and not opts.api_key:
            opts = replace(opts, api_key=self._api_key)
        if stop is not None:
            opts = replace(opts, signal=stop)
        if temperature is not None:
            opts = replace(opts, temperature=temperature)
        if max_tokens is not None:
            opts = replace(opts, max_tokens=max_tokens)
        if metadata:
            opts = replace(opts, metadata={**dict(opts.metadata or {}), **dict(metadata)})

        reasoning: str | None = effort.value if effort is not None else None

        if thinking is not None and not thinking.enabled:
            from agentic_models import get_registry

            if "off" not in get_registry().get_supported_thinking_levels(model):
                raise UnsupportedModelOptionError(
                    f"`thinking.enabled=False` no es expresable en {model.id!r} "
                    f"({model.provider}): el proveedor no admite el nivel `off` y el "
                    "motor aplicaría su nivel por defecto. Se rechaza en vez de "
                    "devolver un turno que razona cuando se pidió que no razonara."
                )
            reasoning = "off"

        if thinking is not None and thinking.budget_tokens is not None:
            from agentic_models import supports_thinking_budget

            if not supports_thinking_budget(model):
                raise UnsupportedModelOptionError(
                    f"`thinking.budget_tokens` no tiene representación en {model.api!r}: "
                    "el razonamiento se pide por nivel (`effort`), no por techo de tokens. "
                    "Ningún campo lo transporta, luego se rechaza en vez de descartarse."
                )
            if reasoning is None:
                raise UnsupportedModelOptionError(
                    "`thinking.budget_tokens` sin `effort`: agentic_models 0.2.0 sólo "
                    "aplica `thinking_budgets` cuando hay un nivel `reasoning`, luego un "
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
                b = thinking.budget_tokens
                budgets = ThinkingBudgets(minimal=b, low=b, medium=b, high=b)
            opts = replace(opts, reasoning=reasoning, thinking_budgets=budgets)

        event_stream = (
            stream_simple(model, context, opts)
            if reasoning is not None
            else stream(model, context, opts)
        )

        thinking_chunks: list[str] = []

        async for event in event_stream:
            t = event.get("type") if isinstance(event, dict) else getattr(event, "type", None)

            if t == "text_delta":
                delta = event["delta"] if isinstance(event, dict) else event.delta
                yield TokenEvent(content=delta)

            elif t == "thinking_delta":
                delta = event["delta"] if isinstance(event, dict) else event.delta
                thinking_chunks.append(delta)
                yield ThinkingEvent(content=delta, model_id=model.id)

            elif t == "toolcall_end":
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

                streamed = bool(thinking_chunks)
                for block in getattr(msg, "content", None) or []:
                    if getattr(block, "type", None) != "thinking":
                        continue
                    if not streamed:
                        thinking_chunks.append(getattr(block, "thinking", "") or "")
                    signature = getattr(block, "thinking_signature", None)
                    if not signature:
                        yield ThinkingEvent(
                            content=getattr(block, "thinking", "") or "",
                            final=True, model_id=model.id,
                        )
                        continue
                    yield ThinkingEvent(
                        content=getattr(block, "thinking", "") or "",
                        signature=signature,
                        final=True,
                        model_id=model.id,
                    )

                u = msg.usage
                reported = getattr(u, "reasoning", 0) or 0
                derived = rough_token_count("".join(thinking_chunks))
                if reported > 0:
                    thinking_tokens = reported
                    thinking_source = THINKING_TOKENS_SOURCE_PROVIDER
                elif derived > 0:
                    thinking_tokens = derived
                    thinking_source = THINKING_TOKENS_SOURCE_COUNTED
                else:
                    thinking_tokens = 0
                    thinking_source = THINKING_TOKENS_SOURCE_UNAVAILABLE
                yield DoneEvent(
                    stop_reason="tool_calls" if reason == "toolUse" else (reason or "stop"),
                    usage=Usage(
                        input_tokens=u.input,
                        output_tokens=u.output,
                        thinking_tokens=thinking_tokens,
                        cache_read=u.cache_read,
                        cache_write=u.cache_write,
                        thinking_tokens_source=thinking_source,
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

