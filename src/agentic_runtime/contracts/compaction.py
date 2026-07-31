from __future__ import annotations

from typing import Any, Protocol

from .tools import ToolContext


class CompactionProvider(Protocol):
    """Provider hook for contributing context during compaction.

    El **motor** de compactación no existe (`K6`, por encima de la línea de
    corte): esto es sólo el seam de aporte. `compact_context()` devolviendo `[]`
    en memory/plan/skills/mcp es **una** cara de `K6`, no cuatro gaps.
    """

    def compact_context(self, context: ToolContext) -> list[dict[str, Any]]:
        ...


def collect_compaction_context(
    providers: list[CompactionProvider],
    context: ToolContext,
) -> list[dict[str, Any]]:
    """Collect compaction messages from providers in registration order."""

    messages: list[dict[str, Any]] = []
    for provider in providers:
        messages.extend(provider.compact_context(context))
    return messages


__all__ = ["CompactionProvider", "collect_compaction_context"]
