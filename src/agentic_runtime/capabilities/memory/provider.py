from __future__ import annotations

from typing import TYPE_CHECKING

from .prompt import build_memory_activation
from .recall import rank_memories
from .store import MemoryHeader, MemoryStore

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext
    from ...tools.protocol import ToolProtocol
    from ..contracts import CapabilitySummary


def _last_user_text(context: "ToolUseContext") -> str:
    """Último texto del usuario, ignorando los recordatorios inyectados por el loop.

    El recall se rinde como `role:"user"` envuelto en `<system-reminder>`; la query de
    recall debe basarse en la intención real del usuario, no en un recordatorio previo.
    """
    for message in reversed(context.messages):
        if message.get("role") != "user":
            continue
        content = message.get("content") or ""
        if "<system-reminder>" in content:
            continue
        return content
    return ""


def _render_recall(header: MemoryHeader) -> str:
    # Incluye el path: marcador estable que el dedup del loop usa, y le dice al modelo
    # dónde está el fichero para leerlo completo con `read_file` si decide usarlo.
    return f"Memoria posiblemente relevante — {header.name} ({header.path}):\n{header.description}".strip()


class MemoryProvider:
    """`CapabilityProvider` de memoria — activación + recall, SIN tools propias.

    La memoria no es una capability seleccionable: es contexto + instrucciones. Por
    eso `tools()`/`catalog()` son `[]`. Se activa por dos superficies, como el
    canónico: (1) una sección estable en el system prompt (`system_prompt_section`);
    (2) recall por turno (`active_context`), que el loop rinde como `<system-reminder>`.
    El guardado lo hace el modelo con `write_file` (sin tool `remember`).
    """

    name = "memory"

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    @staticmethod
    def _scope(context: "ToolUseContext") -> str:
        """Clave de scope de la memoria: `<user_id>/<agent>`.

        Se scopea primero por USUARIO (identidad de ciclo de vida) para que un runtime
        multi-tenant no mezcle memorias entre usuarios. Dentro del usuario, el agente
        principal usa el slot ESTABLE `'main'` (su `agent_id` es un uuid distinto por
        despacho, inservible como clave persistente) y los subagentes se aíslan por su
        `agent_id` (A no ve memorias de B)."""
        user = context.user_id or "anon"
        agent = context.agent_id if context.is_subagent else "main"
        return f"{user}/{agent}"

    async def startup(self) -> None:
        # No-op: el dir de cada `<user_id>/<agent>` se crea de forma perezosa por turno
        # (`system_prompt_section` → `ensure_dir`); en multi-tenant no se conocen los
        # usuarios al arrancar, así que no hay un dir único que pre-crear aquí.
        ...

    async def shutdown(self) -> None: ...

    def catalog(self, context: "ToolUseContext") -> list["CapabilitySummary"]:
        return []

    def tools(self, context: "ToolUseContext") -> list["ToolProtocol"]:
        return []

    def system_prompt_section(self, context: "ToolUseContext") -> str | None:
        """Bloque de activación (instrucciones + índice) scopeado por agente."""
        agent = self._scope(context)
        memory_dir = self._store.ensure_dir(agent)
        index = self._store.read_index(agent)
        return build_memory_activation(str(memory_dir), index)

    def active_context(self, context: "ToolUseContext") -> list[dict]:
        """Recall: ≤5 memorias relevantes al último texto del usuario.

        Scoped por agente (un subagente no ve memorias de otro). Excluye `MEMORY.md`
        (ya va en el system prompt) — el `scan` del store lo omite. Devuelve dicts
        `role:"system"`; el loop los rinde como recordatorio."""
        agent = self._scope(context)
        headers = self._store.scan(agent)
        ranked = rank_memories(headers, _last_user_text(context))
        return [{"role": "system", "content": _render_recall(header)} for header in ranked]

    def compact_context(self, context: "ToolUseContext") -> list[dict]:
        """Tras compactación: mismas memorias relevantes (sobreviven al recorte)."""
        return self.active_context(context)


__all__ = ["MemoryProvider"]
