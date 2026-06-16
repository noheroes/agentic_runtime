from __future__ import annotations

from typing import Protocol

from ..context.tool_use import ToolUseContext


class CompactionProvider(Protocol):
    """Provider hook for contributing context during compaction."""

    def compact_context(self, context: ToolUseContext) -> list[dict]:
        ...


def collect_compaction_context(
    providers: list[CompactionProvider],
    context: ToolUseContext,
) -> list[dict]:
    """Collect compaction messages from providers in registration order."""

    messages: list[dict] = []
    for provider in providers:
        messages.extend(provider.compact_context(context))
    return messages


__all__ = ["CompactionProvider", "collect_compaction_context"]
