"""Anuncio de tools diferidas al modelo — homólogo del `deferred_tools_delta` canónico
(`utils/messages.ts` / `utils/toolSearch.ts::getDeferredToolsDelta`).

Las tools diferidas (MCP) NO se anuncian en el schema hasta que ToolSearch las descubre
(ver `SimulatedDeferredStrategy`). Sin decirle al modelo QUÉ diferidas existen, éste no sabe que
hay capacidades detrás de ToolSearch y nunca busca — las tools MCP quedan invisibles. El
canónico resuelve esto inyectando un `<system-reminder>` que lista los NOMBRES de las
diferidas al quedar disponibles (y las removidas cuando su server MCP se desconecta).

El delta es STATELESS: lo ya anunciado se reconstruye escaneando los reminders previos de
la propia conversación (`ctx.messages`), igual que el canónico escanea los attachments
`deferred_tools_delta`. Así no se re-anuncia lo mismo dentro de un run, pero sí se anuncia
lo nuevo (un server MCP registrado a mitad de sesión) y se retira lo desconectado.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .deferred import is_deferred_tool

if TYPE_CHECKING:
    from .protocol import ToolProtocol

#: Frase-centinela del bloque de altas. Debe empezar EXACTO igual que el texto rendido
#: para que el escaneo reconstruya lo anunciado (contrato de parseo con `render_*`).
_ADDED_HEADER = "The following deferred tools are now available via ToolSearch"
#: Frase-centinela del bloque de bajas (server MCP desconectado).
_REMOVED_HEADER = "The following deferred tools are no longer available"


def render_deferred_tools_delta(added_names: list[str], removed_names: list[str]) -> str:
    """Texto del reminder (sin el envoltorio `<system-reminder>`, que lo pone el loop).

    Formato de parseo estable: cada sección termina su frase-cabecera en `:` y lista un
    nombre por línea; las secciones se separan por línea en blanco."""
    parts: list[str] = []
    if added_names:
        parts.append(
            f"{_ADDED_HEADER}. Their schemas are NOT loaded — before you can invoke one, "
            'call ToolSearch with "select:<tool_name>" (or a keyword query) to load its '
            "schema. Search whenever a task may need a capability you don't already see:\n"
            + "\n".join(added_names)
        )
    if removed_names:
        parts.append(
            f"{_REMOVED_HEADER} (their MCP server disconnected). Do not search for them — "
            "ToolSearch will return no match:\n" + "\n".join(removed_names)
        )
    return "\n\n".join(parts)


def _parse_section_names(content: str, header: str) -> list[str]:
    """Nombres listados bajo `header` en un reminder ya rendido.

    Toma las líneas tras la primera que contiene la cabecera (que termina en `:`), hasta
    una línea en blanco, la otra cabecera o el cierre `</system-reminder>`."""
    lines = content.splitlines()
    names: list[str] = []
    collecting = False
    for line in lines:
        if header in line:
            collecting = True
            continue
        if not collecting:
            continue
        stripped = line.strip()
        if not stripped or stripped == "</system-reminder>":
            break
        if _ADDED_HEADER in line or _REMOVED_HEADER in line:
            break
        names.append(stripped)
    return names


def _announced_deferred_names(messages: list[dict]) -> set[str]:
    """Reconstruye el conjunto de diferidas YA anunciadas escaneando reminders previos
    (espejo del escaneo de attachments `deferred_tools_delta` del canónico)."""
    announced: set[str] = set()
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, str):
            continue
        if _ADDED_HEADER in content:
            announced.update(_parse_section_names(content, _ADDED_HEADER))
        if _REMOVED_HEADER in content:
            for name in _parse_section_names(content, _REMOVED_HEADER):
                announced.discard(name)
    return announced


def compute_deferred_tools_delta(
    pool_tools: list["ToolProtocol"], messages: list[dict]
) -> tuple[list[str], list[str]] | None:
    """Diff del pool diferido actual contra lo ya anunciado en la conversación.

    Devuelve `(added, removed)` ordenados, o `None` si no cambió nada. Un nombre anunciado
    que dejó de ser diferido pero SIGUE en el pool NO se reporta como removido (ahora se
    carga directo; decir "no disponible" sería falso) — espejo de `getDeferredToolsDelta`.
    """
    announced = _announced_deferred_names(messages)
    deferred_names = {t.name for t in pool_tools if is_deferred_tool(t)}
    pool_names = {t.name for t in pool_tools}

    added = sorted(n for n in deferred_names if n not in announced)
    removed = sorted(
        n for n in announced if n not in deferred_names and n not in pool_names
    )
    if not added and not removed:
        return None
    return added, removed


__all__ = [
    "compute_deferred_tools_delta",
    "render_deferred_tools_delta",
]
