from __future__ import annotations

from typing import Any, Protocol

from .tools import ToolContext


class CompactionProvider(Protocol):
    def compact_context(self, context: ToolContext) -> list[dict[str, Any]]:
        ...


def collect_compaction_context(
    providers: list[CompactionProvider],
    context: ToolContext,
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for provider in providers:
        messages.extend(provider.compact_context(context))
    return messages


__all__ = ["CompactionProvider", "collect_compaction_context"]
