from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...contracts.errors import RuntimeIdentityError
from .prompt import build_memory_activation
from .recall import rank_memories
from .store import MemoryHeader, MemoryStore

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext
    from ...tools.protocol import ToolProtocol
    from ..contracts import CapabilitySummary


def _last_user_text(context: ToolUseContext) -> str:
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


_RECALL_MARKER = "Memoria posiblemente relevante"


def _render_recall(header: MemoryHeader) -> str:
    return f"{_RECALL_MARKER} — {header.name} ({header.path}):\n{header.description}".strip()


def _surfaced_recalls(context: ToolUseContext) -> list[str]:
    surfaced: list[str] = []
    for message in context.messages:
        if message.get("role") != "user":
            continue
        content = message.get("content")
        if not isinstance(content, str) or "<system-reminder>" not in content:
            continue
        if _RECALL_MARKER in content:
            surfaced.append(content)
    return surfaced


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
    def _scope(context: ToolUseContext) -> str:
        """Clave de scope de la memoria: `<scope>/<agente>`.

        Se scopea primero por el `Scope` opaco del integrador (`C9`/`ID-3`) para que un
        runtime multi-tenant no mezcle memorias entre tenants. Dentro de él, el agente
        principal usa el slot ESTABLE `'main'`, y un subagente usa **su tipo**, que se
        repite entre despachos (`ID-5`).

        **Los dos defectos que esto corrige, ambos por keyear con un uuid:** el `user_id`
        era autogenerado nuevo en cada despacho (`H-1`) ⇒ el agente principal nunca
        recuperaba su memoria; y el `agent_id` es un uuid nuevo por fork ⇒ un
        subagente-de-tipo-X tampoco recuperaba la suya. Sin `subagent_type` se cae al
        `agent_id`, que aísla correctamente pero **no persiste** — y eso es un límite
        declarado, no un default benigno."""
        if context.scope is None:
            raise RuntimeIdentityError(
                "MemoryProvider necesita un `Scope` y el runtime no inventa uno "
                "(C9/ID-3): inyecta `RuntimeConfig.scope` o `RuntimeTask.scope`."
            )
        if not context.is_subagent:
            agent = "main"
        else:
            agent = context.subagent_type or context.agent_id or "unknown"
        return f"{context.scope.key}/{agent}"

    async def startup(self) -> None:
        # No-op: el dir de cada `<scope>/<agente>` se crea de forma perezosa por turno
        # (`system_prompt_section` → `ensure_dir`); en multi-tenant no se conocen los
        # scopes al arrancar, así que no hay un dir único que pre-crear aquí.
        ...

    async def shutdown(self) -> None: ...

    def catalog(self, context: ToolUseContext) -> list[CapabilitySummary]:
        return []

    def tools(self, context: ToolUseContext) -> list[ToolProtocol]:
        return []

    def system_prompt_section(self, context: ToolUseContext) -> str | None:
        """Bloque de activación (instrucciones + índice) scopeado por agente."""
        agent = self._scope(context)
        memory_dir = self._store.ensure_dir(agent)
        index = self._store.read_index(agent)
        return build_memory_activation(str(memory_dir), index)

    def active_context(self, context: ToolUseContext) -> list[dict[str, Any]]:
        agent = self._scope(context)
        headers = self._store.scan(agent)
        ranked = rank_memories(headers, _last_user_text(context))
        surfaced = _surfaced_recalls(context)
        out: list[dict[str, Any]] = []
        for header in ranked:
            token = f"({header.path}):"
            if any(token in content for content in surfaced):
                continue
            out.append({"role": "system", "content": _render_recall(header)})
        return out

    def compact_context(self, context: ToolUseContext) -> list[dict[str, Any]]:
        return self.active_context(context)


__all__ = ["MemoryProvider"]
