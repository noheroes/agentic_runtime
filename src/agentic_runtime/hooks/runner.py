"""
HookRunner — dispara los hooks registrados en cada punto de ciclo y agrega
sus decisiones.

El runtime define los puntos (PreToolUse, SubagentStop, PreCompact, …) y los
dispara. El consumidor registra handlers vía `register`/`register_sink`; el runtime
no conoce a ningún consumidor concreto.
"""
from __future__ import annotations

import logging
from collections import defaultdict

from .protocol import HookDecision, HookEvent, HookHandler, HookSinkProtocol

logger = logging.getLogger(__name__)


class HookRunner:
    def __init__(self) -> None:
        self._handlers: dict[HookEvent, list[HookHandler]] = defaultdict(list)

    def register(self, event: HookEvent, handler: HookHandler) -> None:
        """Registra un handler para un evento. Primitiva de extensión."""
        self._handlers[event].append(handler)

    def register_sink(self, sink: HookSinkProtocol, *events: HookEvent) -> None:
        """Registra un sink que recibe los eventos indicados (todos si no se pasan)."""
        targets = events or tuple(HookEvent)
        for ev in targets:
            self._handlers[ev].append(sink.handle)

    async def run(self, event: HookEvent, payload: dict) -> HookDecision:
        """Corre los handlers del evento en orden de registro y agrega decisiones.

        Un block/stop corta y se devuelve de inmediato. Si nadie corta, se acumulan
        modified_input y additional_context en una decisión final de tipo allow.
        """
        modified_input: dict | None = None
        contexts: list[str] = []

        for handler in self._handlers.get(event, []):
            try:
                decision = await handler(event, payload)
            except Exception as exc:  # un handler no debe romper el ciclo
                logger.warning("hook handler raised on %s: %s", event.value, exc)
                continue
            if decision is None:
                continue
            if decision.block or decision.stop:
                return decision
            if decision.modified_input is not None:
                modified_input = decision.modified_input
            if decision.additional_context:
                contexts.append(decision.additional_context)

        return HookDecision(
            modified_input=modified_input,
            additional_context="\n".join(contexts) if contexts else None,
        )


__all__ = ["HookRunner"]
