from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext
    from ..protocol import ToolProtocol

TOOL_SEARCH_TOOL_NAME = "ToolSearch"

_MCP_PREFIX = "mcp__"


def _parse_tool_name(name: str) -> tuple[list[str], str, bool]:
    """Homólogo de `parseToolName` (`ToolSearchTool.ts:132-161`).

    Devuelve `(partes, nombre_completo, es_mcp)`. Las MCP se parten por `__` y `_`;
    las normales por CamelCase y `_`.
    """
    if name.startswith(_MCP_PREFIX):
        without_prefix = name[len(_MCP_PREFIX):].lower()
        parts = [p for chunk in without_prefix.split("__") for p in chunk.split("_") if p]
        full = without_prefix.replace("__", " ").replace("_", " ")
        return parts, full, True

    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", name).replace("_", " ").lower()
    parts = [p for p in spaced.split() if p]
    return parts, " ".join(parts), False


def _word_boundary(term: str) -> re.Pattern[str]:
    """`compileTermPatterns` (`:167-175`): frontera de palabra sobre el término escapado.

    La frontera importa — sin ella «read» puntúa dentro de «already» y la búsqueda por
    keyword devuelve ruido.
    """
    return re.compile(rf"\b{re.escape(term)}\b")


def _search_hint(tool: Any) -> str:
    """`Tool.searchHint` (`Tool.ts:373-378`) — frase curada de capacidad, +4 en el ranking.

    Se lee con `getattr` A PROPÓSITO: `contracts/tools.py:5` deja `search_hint` FUERA del
    contrato del tramo 1, y esto no lo asciende. Lo que se homologa aquí es el MECANISMO de
    ranking (que si la tool trae la pista, pese más que la descripción), no el miembro.
    Nota del canónico (`prompt.ts:110-114`): el hint NO se renderiza en el anuncio de
    diferidas — el A/B no mostró beneficio; su único efecto es este, la puntuación.
    """
    return str(getattr(tool, "search_hint", "") or "").lower()


class ToolSearchTool:
    name = TOOL_SEARCH_TOOL_NAME
    description = """Fetches full schema definitions for deferred tools so they can be called.

Deferred tools appear by name in <system-reminder> messages. Until fetched, only the name is
known — there is no parameter schema, so calling one directly fails with InputValidationError.
This tool takes a query, matches it against the deferred tool list, and returns the matched
tools' complete schemas. Once a tool's schema appears in that result, it is callable exactly
like any tool defined at the top of the prompt.

Query forms:
- "select:Read,Edit,Grep" — fetch these exact tools by name
- "notebook jupyter" — keyword search, up to max_results best matches
- "+slack send" — require "slack" in the name, rank by remaining terms"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Query to find deferred tools. Use 'select:<tool_name>' for direct "
                    "selection, or keywords to search."
                ),
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum results to return (default: 5).",
                "default": 5,
            },
        },
        "required": ["query"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = True
    timeout_seconds = 10.0

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        from ..deferred import is_deferred_tool, mark_tools_discovered

        query = input.get("query", "").strip()
        max_results = int(input.get("max_results", 5))

        # El set COMPLETO y el subconjunto diferido: A busca en el segundo pero cae al
        # primero (`:200-201`, `:374-375`), y esa caída es deliberada — «selecting an
        # already-loaded tool is a harmless no-op that lets the model proceed without
        # retry churn». Sin ella, un nombre ya cargado devuelve vacío y el modelo reintenta.
        todas = ctx.tool_pool.assemble(ctx.permission_context)
        deferred = [t for t in todas if is_deferred_tool(t)]

        select = re.match(r"^select:(.+)$", query, re.IGNORECASE)
        if select:
            matches = self._select(select.group(1), deferred, todas)
        else:
            matches = self._keyword_search(query, deferred, todas, max_results)

        # Descubrir = activar: las matched pasan a anunciarse en los próximos turnos
        # y su schema completo se devuelve aquí para que el modelo las invoque ya.
        mark_tools_discovered(ctx, [t.name for t in matches])

        return ToolResult(
            tool_name=self.name,
            output=json.dumps({
                "query": query,
                "matches": [
                    {"name": t.name, "description": t.description, "parameters": t.input_schema}
                    for t in matches
                ],
                "total_deferred_tools": len(deferred),
            }),
        )

    # ── select: ───────────────────────────────────────────────────────────────
    def _select(
        self, raw: str, deferred: list[ToolProtocol], todas: list[ToolProtocol]
    ) -> list[ToolProtocol]:
        """`ToolSearchTool.ts:363-406`: coma-separado, dedup por nombre, éxito PARCIAL.

        Los nombres no encontrados no anulan el resultado: si hay al menos uno, se
        devuelve lo hallado. Es lo contrario de fallar entero, y es lo que evita que un
        nombre alucinado tire abajo una selección buena.
        """
        pedidos = [s.strip() for s in raw.split(",") if s.strip()]
        encontradas: list[ToolProtocol] = []
        vistos: set[str] = set()
        for nombre in pedidos:
            tool = _find_by_name(deferred, nombre) or _find_by_name(todas, nombre)
            if tool is not None and tool.name not in vistos:
                encontradas.append(tool)
                vistos.add(tool.name)
        return encontradas

    # ── keyword ───────────────────────────────────────────────────────────────
    def _keyword_search(
        self,
        query: str,
        deferred: list[ToolProtocol],
        todas: list[ToolProtocol],
        max_results: int,
    ) -> list[ToolProtocol]:
        """`searchToolsWithKeywords` (`ToolSearchTool.ts:186-302`)."""
        q = query.lower().strip()

        # Atajo 1: el query ES un nombre de tool. Cubre a los modelos que mandan el nombre
        # desnudo sin `select:` (A lo documenta: «seen from subagents/post-compaction»).
        exacta = _find_lower(deferred, q) or _find_lower(todas, q)
        if exacta is not None:
            return [exacta]

        # Atajo 2: prefijo `mcp__server` — buscar por nombre de servidor.
        if q.startswith(_MCP_PREFIX) and len(q) > len(_MCP_PREFIX):
            por_prefijo = [t for t in deferred if t.name.lower().startswith(q)][:max_results]
            if por_prefijo:
                return por_prefijo

        terminos = [t for t in q.split() if t]
        requeridos = [t[1:] for t in terminos if t.startswith("+") and len(t) > 1]
        opcionales = [t for t in terminos if not (t.startswith("+") and len(t) > 1)]
        a_puntuar = [*requeridos, *opcionales] if requeridos else terminos
        patrones = {t: _word_boundary(t) for t in a_puntuar}

        candidatas = deferred
        if requeridos:
            candidatas = [
                t for t in deferred
                if all(_matches_term(t, term, patrones[term]) for term in requeridos)
            ]

        puntuadas: list[tuple[int, Any]] = []
        for tool in candidatas:
            score = self._score(tool, a_puntuar, patrones)
            if score > 0:
                puntuadas.append((score, tool))

        # `sort` estable sobre el orden del pool (ya alfabético por `assemble_tool_pool`):
        # empates deterministas, que es lo que la caché de prompt necesita.
        puntuadas.sort(key=lambda par: -par[0])
        return [t for _, t in puntuadas[:max_results]]

    def _score(
        self, tool: Any, terminos: list[str], patrones: dict[str, re.Pattern[str]]
    ) -> int:
        partes, completo, es_mcp = _parse_tool_name(tool.name)
        desc = (tool.description or "").lower()
        hint = _search_hint(tool)

        score = 0
        for term in terminos:
            patron = patrones[term]
            if term in partes:
                score += 12 if es_mcp else 10
            elif any(term in parte for parte in partes):
                score += 6 if es_mcp else 5

            # Reserva por nombre completo, sólo si nada más ha puntuado aún
            # (`:278-280` — la comparación es contra el acumulado, no por término).
            if term in completo and score == 0:
                score += 3

            if hint and patron.search(hint):
                score += 4
            if patron.search(desc):
                score += 2
        return score


def _matches_term(tool: Any, term: str, patron: re.Pattern[str]) -> bool:
    """Pre-filtro de términos requeridos (`:244-252`): nombre O descripción O hint."""
    partes, _completo, _es_mcp = _parse_tool_name(tool.name)
    if term in partes or any(term in parte for parte in partes):
        return True
    if patron.search((tool.description or "").lower()):
        return True
    hint = _search_hint(tool)
    return bool(hint and patron.search(hint))


def _find_by_name(tools: list[ToolProtocol], name: str) -> Any:
    """`findToolByName` (`Tool.ts:348-360`): nombre exacto o alias.

    `aliases` está fuera del contrato T1 (`contracts/tools.py:5`), así que se lee opcional:
    una tool que no lo traiga se resuelve sólo por nombre, como hoy.
    """
    for tool in tools:
        if tool.name == name or name in (getattr(tool, "aliases", None) or ()):
            return tool
    return None


def _find_lower(tools: list[ToolProtocol], lowered: str) -> Any:
    for tool in tools:
        if tool.name.lower() == lowered:
            return tool
    return None
