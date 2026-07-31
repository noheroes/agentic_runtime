"""Battery TRIVIAL de compactación (ciclo A2.4) — realiza la costura S9 `CompactionMotor`.

**Este módulo NO pertenece al base framework.** Es un paquete-battery OPCIONAL, derivado
del canónico (motor de compactación de `query.ts`), que se COMPONE por fuera. Prueba de la
Filosofía B: **ningún módulo del base lo importa** — sólo el integrador/runner
(`skeleton._battery`) lo importa y lo inyecta por el seam deps-DI (S27). El base declara el
Protocol `CompactionMotor` (en `seams.py`) y dispara el trigger en el loop; jamás conoce
esta clase concreta. Fase C la sustituirá por la battery `compaction` completa
(microcompact/snip/collapse/budget); aquí basta la versión mínima para VALIDAR la costura.

Grep de aislamiento (gate A2.4): `import.*battery_compaction` sólo aparece en `_battery.py`.
"""

from __future__ import annotations

from skeleton.contracts import Message, Usage
from skeleton.seams import CompactBoundary


class SimpleCompactionBattery:
    """Motor de compactación trivial (realiza `CompactionMotor`, S9).

    - `should_compact`: dispara cuando el historial supera `threshold` mensajes (proxy
      determinista del overflow real `is_context_overflow`, 16·C2 — el usage real llega
      con la battery de Fase C).
    - `compact`: funde los mensajes de cabeza en UN resumen sintético y CONSERVA los
      `keep_last` finales. Conservar la cola mantiene el sub-round-trip de tools intacto
      (un `assistant(tool_use)`+`tool` colgando) ⇒ la secuencia resultante sigue siendo
      válida. La FIDELIDAD del resumen (qué preservar, budget de tokens) es competencia de
      la battery de Fase C, NO de A2.4: aquí sólo se valida que el base dispara el motor.
    """

    def __init__(self, *, threshold: int = 3, keep_last: int = 2) -> None:
        self._threshold = threshold
        self._keep_last = keep_last

    def should_compact(self, messages: list[Message], usage: Usage) -> bool:
        return len(messages) >= self._threshold

    def compact(self, messages: list[Message]) -> CompactBoundary:
        if len(messages) <= self._keep_last:
            return CompactBoundary(messages=list(messages), collapsed=0)
        head = messages[: -self._keep_last]
        tail = messages[-self._keep_last :]
        summary = Message(
            role="user",
            content=f"[compactado: {len(head)} mensaje(s) previos resumidos por la battery]",
        )
        return CompactBoundary(messages=[summary, *tail], collapsed=len(head))
