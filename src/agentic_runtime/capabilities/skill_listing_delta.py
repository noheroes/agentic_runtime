"""Anuncio del catálogo de skills al modelo — homólogo del attachment `skill_listing`
canónico (`utils/attachments.ts:2596-2765`; render en `utils/messages.ts:3728-3738`;
presupuesto y formato de línea en `tools/SkillTool/prompt.ts:20-171`).

`FIND-SKILL9/17` (= `CG-SKILL-4`). Antes de esto, `CapabilityManager.catalog()` existía,
estaba probado y **no lo llamaba nadie en producción**: el único punto por el que un
nombre de skill alcanzaba al modelo era el mensaje de ERROR de `SkillTool`, es decir, el
modelo sólo aprendía el catálogo **fallando primero**, y para fallar tenía que haber
adivinado un nombre. Es el patrón dominante del barrido EOF —B tiene el dato cargado y no
lo pone en ninguna lista que el modelo vea— en su forma más cara.

**Por qué vive en `capabilities/` y no en `capabilities/skills/`.** El runtime no habla
con el provider de skills: habla con el manager, y lo que recibe son `CapabilitySummary`.
Este módulo opera sobre esa forma, así que cualquier provider que declare `kind="skill"`
—incluidas las skills servidas por MCP, que en A entran por `uniqBy([...localCommands,
...mcpSkills])` (`attachments.ts:2724-2727`)— aparece en el listado sin tocar nada aquí.

**Elegibilidad.** El predicado de A (`getSkillToolCommands`, `commands.ts:563-581`) mira
campos del `Command` que en B son del provider (`disable_model_invocation`, enablement),
así que el filtro vive donde vive el dato: en `SkillsProvider.catalog()`. Aquí sólo llega
lo publicable. Las dos ramas de A que B no puede evaluar se dicen y no se disfrazan:
`source !== 'builtin'` (B no tiene skills built-in) y el `loadedFrom ∈ {bundled, skills,
commands_DEPRECATED} || hasUserSpecifiedDescription || whenToUse`, que en B siempre sería
cierto porque toda skill de B se carga por una de esas vías.

**Presupuesto.** `char_budget` reproduce `getCharBudget` (`prompt.ts:31-41`), pero B **no
tiene noción de ventana de contexto** en ninguna parte del runtime: no hay ni un
`context_window` que consultar. Así que el default de A (`DEFAULT_CHAR_BUDGET`) es lo que
se aplica salvo que el llamante pase el tamaño. Carencia declarada, con su consecuencia
dicha: en un modelo de ventana grande B recorta antes que A.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .skills.skill_tool import SKILL_TOOL_NAME

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .contracts import CapabilitySummary

#: Clave sidecar del mensaje con los nombres ya anunciados (homólogo del `sentSkillNames`
#: canónico, que allí es un `Map` de proceso). No la lee el modelo.
SKILL_LISTING_KEY = "skill_listing_delta"

_HEADER = "The following skills are available for use with the Skill tool:"

#: `SKILL_BUDGET_CONTEXT_PERCENT`/`CHARS_PER_TOKEN`/`DEFAULT_CHAR_BUDGET` (`prompt.ts:21-23`).
SKILL_BUDGET_CONTEXT_PERCENT = 0.01
CHARS_PER_TOKEN = 4
DEFAULT_CHAR_BUDGET = 8_000
#: Tope duro por entrada (`prompt.ts:29`): el listado es para DESCUBRIR; la tool carga el
#: contenido completo al invocar, así que un `when_to_use` verboso quema caché de turno 1
#: sin mejorar el emparejamiento. Aplica también a las bundled.
MAX_LISTING_DESC_CHARS = 250
#: Por debajo de esto la descripción no informa y se cae a sólo nombres (`prompt.ts:68`).
MIN_DESC_LENGTH = 20
#: Único valor de `source` que el runtime interpreta, y lo hace porque lo interpreta A
#: (`prompt.ts:97`): las de la casa nunca se truncan.
BUNDLED_SOURCE = "bundled"


def char_budget(context_window_tokens: int | None = None) -> int:
    """Presupuesto en CARACTERES — espejo de `getCharBudget` (`prompt.ts:31-41`)."""
    if context_window_tokens:
        return int(context_window_tokens * CHARS_PER_TOKEN * SKILL_BUDGET_CONTEXT_PERCENT)
    return DEFAULT_CHAR_BUDGET


def _truncate(text: str, max_len: int) -> str:
    """Espejo de `truncateToWidth` (`utils/truncate.ts:63-75`): el '…' cuenta.

    B mide en CARACTERES donde A mide en columnas de terminal (`stringWidth`). Es
    divergencia declarada y no arbitraria: el destinatario de este texto es el modelo,
    no el terminal, y `stringWidth` existe en A porque el mismo helper rinde en pantalla.
    """
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return "…"
    return text[: max_len - 1] + "…"


def _description(entry: CapabilitySummary) -> str:
    """`getCommandDescription` (`prompt.ts:43-50`): descripción + `when_to_use`, con tope."""
    desc = f"{entry.description} - {entry.when_to_use}" if entry.when_to_use else entry.description
    if len(desc) > MAX_LISTING_DESC_CHARS:
        return desc[: MAX_LISTING_DESC_CHARS - 1] + "…"
    return desc


def format_skill_line(entry: CapabilitySummary) -> str:
    """Una entrada del listado — espejo de `formatCommandDescription` (`prompt.ts:52-66`).

    Se rinde `entry.name`, que es la IDENTIDAD, no el nombre de presentación: es el valor
    que el modelo tiene que pasarle a la tool. A hace exactamente lo mismo y deja el
    `userFacingName` para un log de depuración (`:53-63`)."""
    return f"- {entry.name}: {_description(entry)}"


def format_entries_within_budget(
    entries: Sequence[CapabilitySummary],
    *,
    context_window_tokens: int | None = None,
    char_budget_override: int | None = None,
) -> str:
    """Listado completo dentro del presupuesto — espejo de `formatCommandsWithinBudget`.

    Las tres ramas de A, en su orden (`prompt.ts:70-171`): completo si cabe; si no,
    descripciones repartidas por igual entre las no-bundled; y si el reparto baja de
    `MIN_DESC_LENGTH`, sólo nombres. **Lo último que se pierde es el nombre**, porque es
    lo único que hace invocable a una skill: un listado sin descripciones sigue sirviendo,
    uno sin nombres no sirve para nada.
    """
    if not entries:
        return ""
    budget = char_budget_override if char_budget_override is not None else char_budget(
        context_window_tokens
    )

    full = [format_skill_line(e) for e in entries]
    if sum(len(line) for line in full) + (len(full) - 1) <= budget:
        return "\n".join(full)

    bundled = {i for i, e in enumerate(entries) if e.source == BUNDLED_SOURCE}
    rest = [e for i, e in enumerate(entries) if i not in bundled]
    if not rest:
        return "\n".join(full)

    bundled_chars = sum(len(full[i]) + 1 for i in bundled)
    remaining = budget - bundled_chars
    name_overhead = sum(len(e.name) + 4 for e in rest) + (len(rest) - 1)
    max_desc_len = (remaining - name_overhead) // len(rest)

    if max_desc_len < MIN_DESC_LENGTH:
        return "\n".join(
            full[i] if i in bundled else f"- {e.name}"
            for i, e in enumerate(entries)
        )
    return "\n".join(
        full[i] if i in bundled else f"- {e.name}: {_truncate(_description(e), max_desc_len)}"
        for i, e in enumerate(entries)
    )


@dataclass(frozen=True)
class SkillListingDelta:
    """Lo que toca anunciar en este turno."""

    #: Nombres que quedan anunciados TRAS este mensaje (no sólo los nuevos): es lo que el
    #: sidecar persiste, para que un re-anuncio completo no deje el conjunto a medias.
    names: tuple[str, ...]
    content: str


def render_skill_listing_delta(delta: SkillListingDelta) -> str:
    """Texto del recordatorio (sin el envoltorio `<system-reminder>`, que pone el loop).

    Espejo de `messages.ts:3732-3737`. La cabecera es única: A lleva `isInitial` en el
    attachment pero el render **no lo mira**, así que un segundo encabezado sería
    invención."""
    return f"{_HEADER}\n\n{delta.content}"


def _announced_skill_names(messages: list[dict[str, Any]]) -> set[str]:
    """Conjunto ya anunciado, reconstruido de los sidecars ESTRUCTURADOS previos.

    Nunca del texto rendido: una `description` puede llevar saltos de línea, luego «una
    línea = una entrada» es falso por construcción y el delta no convergería jamás
    (`FIND-DEFER-1`). Cada sidecar lleva el conjunto COMPLETO vigente tras su mensaje, no
    un incremento, así que el último manda — que es lo que hace correcto el re-anuncio
    íntegro tras una baja.
    """
    announced: set[str] = set()
    for msg in messages:
        sidecar = msg.get(SKILL_LISTING_KEY)
        if not isinstance(sidecar, dict):
            continue
        names = sidecar.get("names")
        if isinstance(names, (list, tuple)):
            announced = {str(n) for n in names}
    return announced


def compute_skill_listing_delta(
    entries: Sequence[CapabilitySummary],
    messages: list[dict[str, Any]],
    *,
    skill_tool_available: bool,
    context_window_tokens: int | None = None,
) -> SkillListingDelta | None:
    """Delta del catálogo contra lo anunciado, o `None` si no hay nada que decir.

    `skill_tool_available` es la guarda del canónico (`attachments.ts:2712-2717`): sin la
    tool `Skill` publicada el listado sería inaccionable y no se emite. Se mide sobre el
    pool PUBLICADO, no sobre el catálogo — desde `FIND-POOL-1` no son lo mismo.

    Bajas: A no tiene rama de «esta skill ya no está»; tiene `resetSentSkillNames()`
    (`:2601-2606`), que ante un cambio genuino del conjunto vacía lo enviado y hace que
    el siguiente listado salga ENTERO. Aquí se reproduce el EFECTO: si algo anunciado ya
    no está en el catálogo, se re-anuncia todo. Dejar al modelo con un catálogo que ya no
    existe sería peor que repetir un mensaje, y ninguna otra señal lo desmentiría.
    """
    if not skill_tool_available:
        return None
    announced = _announced_skill_names(messages)
    current = {e.name for e in entries}
    if announced - current:
        nuevas = list(entries)
    else:
        nuevas = [e for e in entries if e.name not in announced]
    if not nuevas:
        return None
    content = format_entries_within_budget(
        nuevas, context_window_tokens=context_window_tokens
    )
    if not content:
        return None
    return SkillListingDelta(names=tuple(sorted(current)), content=content)


__all__ = [
    "BUNDLED_SOURCE",
    "CHARS_PER_TOKEN",
    "DEFAULT_CHAR_BUDGET",
    "MAX_LISTING_DESC_CHARS",
    "MIN_DESC_LENGTH",
    "SKILL_BUDGET_CONTEXT_PERCENT",
    "SKILL_LISTING_KEY",
    "SKILL_TOOL_NAME",
    "SkillListingDelta",
    "char_budget",
    "compute_skill_listing_delta",
    "format_entries_within_budget",
    "format_skill_line",
    "render_skill_listing_delta",
]
