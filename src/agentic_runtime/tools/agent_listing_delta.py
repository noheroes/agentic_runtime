"""Anuncio del catálogo de subagentes al modelo — homólogo del attachment
`agent_listing_delta` canónico (`utils/attachments.ts:691-700`, `:1490-1556`;
render en `utils/messages.ts:4194-4215`; línea en `tools/AgentTool/prompt.ts:36-46`).

`FIND-AGENT-LIST-1`. Sin este anuncio el modelo tiene la tool `Agent` con un parámetro
`subagent_type` de tipo `string` y **ninguna forma de saber qué valores existen**: o no
delega nunca, o inventa un tipo que el resolver no resuelve. En el canónico el listado
llega por una de DOS vías (`prompt.ts:196-199`): inline en la descripción de la tool, o
—cuando `shouldInjectAgentListInMessages()` está activo— por este attachment, con la
descripción diciendo «Available agent types are listed in <system-reminder> messages».
B implementa la vía de attachment; el porqué de elegir ésa está en `AgentTool.description`.

**Los TRES filtros de A que aquí NO se aplican, dichos y no disfrazados.** Antes de emitir,
`getAgentListingDeltaAttachment` filtra el catálogo por (1) `filterAgentsByMcpRequirements`,
(2) `filterDeniedAgents(..., permissionContext, AGENT_TOOL_NAME)` y (3) `allowedAgentTypes`
(`attachments.ts:1508-1518`). En B ninguno tiene homólogo alcanzable desde este punto:
`PermissionContext` **sólo ve nombres de tool** por contrato explícito
(`contracts/permissions.py:28-31`), así que una regla que deniegue `Agent(subagent_type:X)`
no es expresable, y los requisitos MCP por agente son campos que la `AgentDefinition` de B no
porta (`05-execution.md §AgentDefinition`, filas `requiredMcpServers`/`mcpServers` ⛔→11).
La consecuencia es concreta y hay que decirla: **B puede anunciar un tipo que el host luego
deniegue**. Lo que el host SÍ controla es qué devuelve `list_agents()`. La guarda que sí se
aplica es la de la tool (ver `agent_tool_available`). Carencia declarada, no filtro
«simplificado»: el sitio donde se paga es el contrato de permisos, no este módulo.

**Reconstrucción de lo ya anunciado.** El canónico rehace el conjunto anunciado leyendo
los campos ESTRUCTURADOS de los attachments previos (`addedTypes`/`removedTypes`), no el
texto rendido. B hace lo mismo: el mensaje del recordatorio lleva el sidecar
`ANNOUNCED_KEY` con las altas y bajas como datos. Re-parsear el texto sería repetir
`FIND-DEFER-1` — y aquí ni siquiera sería recuperable, porque la `description` de una
definición puede contener saltos de línea (el canónico incluso los des-escapa,
`loadAgentsDir.ts:565`), así que «una línea = una entrada» es falso por construcción.
El caller ignora las claves que no conoce (`models/caller.py:58-94`), así que el sidecar
viaja por la conversación sin llegar al modelo, igual que el attachment de A.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ..contracts.agents import AgentDefinition

#: Clave sidecar del mensaje con los tipos anunciados (homólogo de `addedTypes`/
#: `removedTypes` del attachment canónico). No la lee el modelo.
ANNOUNCED_KEY = "agent_listing_delta"

_INITIAL_HEADER = "Available agent types for the Agent tool:"
_UPDATE_HEADER = "New agent types are now available for the Agent tool:"
_REMOVED_HEADER = "The following agent types are no longer available:"


def format_agent_tools(
    allowed_tools: Sequence[str], disallowed_tools: Sequence[str]
) -> str:
    """Gramática de la sección `(Tools: …)` — espejo exacto de `getToolsDescription`
    (`AgentTool/prompt.ts:15-34`), con sus CUATRO ramas.

    El orden importa: con allowlist Y denylist el canónico RESTA y, si no queda nada,
    dice `None` — no `All tools`, que sería lo contrario de lo que la definición pide."""
    has_allow = bool(allowed_tools)
    has_deny = bool(disallowed_tools)
    if has_allow and has_deny:
        deny = set(disallowed_tools)
        effective = [t for t in allowed_tools if t not in deny]
        if not effective:
            return "None"
        return ", ".join(effective)
    if has_allow:
        return ", ".join(allowed_tools)
    if has_deny:
        return f"All tools except {', '.join(disallowed_tools)}"
    return "All tools"


def format_agent_line(definition: AgentDefinition) -> str:
    """Una entrada del listado — espejo de `formatAgentLine` (`prompt.ts:36-46`).

    El campo que describe CUÁNDO usar el agente es `description` (el `whenToUse` del
    canónico, que sale del `description:` del frontmatter, `loadAgentsDir.ts:550`).
    Hasta `FIND-AGENT-LIST-1` ese campo no lo leía nadie en B: era campo MUERTO."""
    tools = format_agent_tools(
        definition.allowed_tools, tuple(sorted(definition.disallowed_tools))
    )
    return f"- {definition.subagent_type}: {definition.description} (Tools: {tools})"


@dataclass(frozen=True)
class AgentListingDelta:
    """Delta del catálogo contra lo ya anunciado en esta conversación."""

    added_types: tuple[str, ...]
    added_lines: tuple[str, ...]
    removed_types: tuple[str, ...]
    #: Primer anuncio de la conversación → cambia la cabecera (`messages.ts:4197-4199`).
    is_initial: bool


def render_agent_listing_delta(delta: AgentListingDelta) -> str:
    """Texto del recordatorio (sin el envoltorio `<system-reminder>`, que pone el loop).

    Espejo de `messages.ts:4194-4215`. La nota de concurrencia de A (`:4207-4211`) NO se
    emite: allí está condicionada al tipo de SUSCRIPCIÓN (`getSubscriptionType() !== 'pro'`),
    que es política del host y el runtime no puede conocer ni inventar. El efecto que esa
    nota persigue —que el modelo lance subagentes en paralelo— lo produce en B la
    instrucción incondicional que ya vive en `AgentTool.description`, y hay un test que se
    pone rojo si desaparece. Es divergencia declarada, no hueco."""
    parts: list[str] = []
    if delta.added_lines:
        header = _INITIAL_HEADER if delta.is_initial else _UPDATE_HEADER
        parts.append(header + "\n" + "\n".join(delta.added_lines))
    if delta.removed_types:
        parts.append(
            _REMOVED_HEADER + "\n" + "\n".join(f"- {t}" for t in delta.removed_types)
        )
    return "\n\n".join(parts)


def _announced_agent_types(messages: list[dict[str, Any]]) -> set[str]:
    """Conjunto ya anunciado, reconstruido de los sidecars ESTRUCTURADOS previos.

    Espejo de `getAgentListingDeltaAttachment` (`attachments.ts:1519-1531`): suma las
    altas y resta las bajas, en orden de conversación. Un mensaje sin sidecar (o con uno
    ilegible, p.ej. tras un round-trip de persistencia que descarte claves desconocidas)
    simplemente no aporta: la degradación es RE-ANUNCIAR, nunca anunciar de menos."""
    announced: set[str] = set()
    for msg in messages:
        sidecar = msg.get(ANNOUNCED_KEY)
        if not isinstance(sidecar, dict):
            continue
        added = sidecar.get("added_types")
        if isinstance(added, (list, tuple)):
            announced.update(str(t) for t in added)
        removed = sidecar.get("removed_types")
        if isinstance(removed, (list, tuple)):
            for t in removed:
                announced.discard(str(t))
    return announced


def compute_agent_listing_delta(
    definitions: Sequence[AgentDefinition],
    messages: list[dict[str, Any]],
    *,
    agent_tool_available: bool,
) -> AgentListingDelta | None:
    """Delta del catálogo actual contra lo anunciado, o `None` si no hay nada que decir.

    `agent_tool_available` es la guarda del canónico (`attachments.ts:1500-1506`): si la
    tool `Agent` no está publicada en el pool de este turno, el listado sería
    **inaccionable** y no se emite. Importa desde `FIND-POOL-1`: el pool publicado no es
    el censo, así que la guarda tiene que mirar el pool, no el registro.

    El orden es determinista (`attachments.ts:1536-1541`): el catálogo del host puede
    llegar en cualquier orden y dos órdenes distintos del mismo conjunto no pueden
    producir dos anuncios distintos."""
    if not agent_tool_available:
        return None
    announced = _announced_agent_types(messages)
    by_type = {d.subagent_type: d for d in definitions}
    added_types = tuple(sorted(t for t in by_type if t not in announced))
    removed_types = tuple(sorted(t for t in announced if t not in by_type))
    if not added_types and not removed_types:
        return None
    return AgentListingDelta(
        added_types=added_types,
        added_lines=tuple(format_agent_line(by_type[t]) for t in added_types),
        removed_types=removed_types,
        is_initial=not announced,
    )


__all__ = [
    "ANNOUNCED_KEY",
    "AgentListingDelta",
    "compute_agent_listing_delta",
    "format_agent_line",
    "format_agent_tools",
    "render_agent_listing_delta",
]
