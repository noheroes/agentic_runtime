"""
Concrete ModelCallerProtocol implementation backed by agentic_models.

Bridges agentic_runtime's dict-based message format to agentic_models Context
and maps agentic_models stream events to agentic_runtime event types.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Optional

from ..events.event_types import DoneEvent, ErrorEvent, TokenEvent, ToolCallEvent, Usage
from .protocol import ModelCallerProtocol  # noqa: F401 — satisfies Protocol


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
            model=get_model("claude-sonnet-4-6"),
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

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        stop: Optional[asyncio.Event] = None,
        model_id: str = "",
        system_sections: Optional[list[str]] = None,
    ) -> AsyncGenerator[Any, None]:
        return self._stream(
            messages, tools, stop=stop, model_id=model_id, system_sections=system_sections
        )

    async def _stream(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        stop: Optional[asyncio.Event] = None,
        model_id: str = "",
        system_sections: Optional[list[str]] = None,
    ) -> AsyncGenerator[Any, None]:
        from agentic_models import stream
        from agentic_models.model_types import StreamOptions

        context = _dict_messages_to_context(
            messages, tools, _compose_system_prompt(self._system_prompt, system_sections)
        )

        opts = self._options
        if opts is None:
            opts = StreamOptions()
        if self._api_key and not opts.api_key:
            from dataclasses import replace
            opts = replace(opts, api_key=self._api_key)
        if stop is not None:
            from dataclasses import replace
            opts = replace(opts, signal=stop)

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

        event_stream = stream(model, context, opts)

        # Providers push dicts; match on the "type" key
        async for event in event_stream:
            t = event.get("type") if isinstance(event, dict) else getattr(event, "type", None)

            if t == "text_delta":
                delta = event["delta"] if isinstance(event, dict) else event.delta
                yield TokenEvent(content=delta)

            elif t == "toolcall_end":
                tc = event["toolCall"] if isinstance(event, dict) else event.toolCall
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
