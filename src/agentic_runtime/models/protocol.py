from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, AsyncGenerator, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..events.protocol import Event


@dataclass(frozen=True)
class ModelRequest:
    """Immutable model request — the loop builds this and passes it to the caller."""
    messages: list[dict]
    tools: list[dict]
    model_id: str
    stop: Optional[asyncio.Event] = field(default=None, compare=False)
    thinking_budget: Optional[int] = None


@runtime_checkable
class ModelCallerProtocol(Protocol):
    """
    Primitive the loop uses to call a model.
    Projects implement this protocol with their chosen LLM client.
    """

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        stop: Optional[asyncio.Event] = None,
        model_id: str = "",
    ) -> AsyncGenerator["Event", None]: ...
