from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.error
import urllib.request
from typing import TYPE_CHECKING, Any

from ...tls import default_ssl_context
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

logger = logging.getLogger(__name__)

WEB_SEARCH_TOOL_NAME = "WebSearch"
_DEFAULT_TIMEOUT = 20
_DEFAULT_MAX_RESULTS = 5
_MAX_RESULTS_CAP = 20

_RECORDATORIO = (
    "\n\nREMINDER: the above are titles, links and snippets — the pages themselves are NOT "
    "included here. When you need what a page actually says, retrieve that URL with the tool "
    "that fetches URL content and returns it as markdown. Do not write your own fetcher or "
    "HTML parser in a shell command to do it."
)


class WebSearchTool:
    name = WEB_SEARCH_TOOL_NAME
    # `shouldDefer: true` del canónico (`WebSearchTool/WebSearchTool.ts:156`) — `GAP-TOOL4`.
    deferred = True
    # `searchHint` del canónico, grafía literal. Fuera del contrato T1
    # (`contracts/tools.py:5`); lo lee ToolSearch para rankear (+4 vs +2 de la descripción).
    search_hint = "search the web for current information"
    # Homologada contra `getWebSearchPrompt()` (`WebSearchTool/prompt.ts:5-33`) — `GAP-PROMPT-1`.
    # Se conservan las DOS piezas que en A van en mayúsculas porque gobiernan conducta: la
    # sección «Sources:» obligatoria y el uso del año en curso en la consulta.
    # OMITIDO: «web search is only available in the US», que describe al proveedor de A.
    description = """- Searches the web and returns results as a list of title, URL and snippet
- Provides up-to-date information for current events and recent data
- Use this tool for information beyond your knowledge cutoff

CRITICAL REQUIREMENT - You MUST follow this:
- After answering the user's question, you MUST include a "Sources:" section at the end of
  your response
- In that section, list the relevant URLs from the search results as markdown links:
  [Title](URL)
- This is MANDATORY - never skip including sources

Usage notes:
- Domain filtering is supported via allowed_domains and blocked_domains
- max_results accepts 1-20 and defaults to 5

IMPORTANT - Use the correct year in search queries:
- When searching for recent information, documentation or current events, include the CURRENT
  year in the query, not last year's."""
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to use.",
            },
            "allowed_domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Only include search results from these domains.",
            },
            "blocked_domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Never include search results from these domains.",
            },
            "max_results": {
                "type": "integer",
                "description": "Max results to return (1–20, default 5).",
                "minimum": 1,
                "maximum": 20,
            },
        },
        "required": ["query"],
    }
    category = ToolCategory.NETWORK
    requires_permission = True
    safe_for_background = True
    timeout_seconds = 30.0

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        query: str = input.get("query", "")
        if not query:
            return ToolResult.error(self.name, "query is required.")

        allowed_domains: list[str] = input.get("allowed_domains") or []
        blocked_domains: list[str] = input.get("blocked_domains") or []
        max_results: int = min(
            int(input.get("max_results") or _DEFAULT_MAX_RESULTS),
            _MAX_RESULTS_CAP,
        )

        effective_query = _build_query(query, allowed_domains, blocked_domains)

        api_key = os.getenv("SERPER_API_KEY", "")
        if not api_key:
            return ToolResult.error(
                self.name,
                "SERPER_API_KEY is not set. WebSearch requires a Serper.dev API key.",
            )

        # `FIND-C6-2`: en un THREAD. `_serper_search` hace `urlopen` síncrono (hasta 20 s) y
        # llamarlo directo desde este `async def` congelaba el único event loop todo ese
        # rato, dejando el cap del dispatcher sin efecto. Ver la nota extensa en
        # `web_fetch.py`, que tenía el mismo defecto por la misma causa.
        return await asyncio.to_thread(
            _serper_search, self.name, effective_query, max_results, api_key
        )


def _build_query(
    query: str,
    allowed_domains: list[str],
    blocked_domains: list[str],
) -> str:
    if allowed_domains:
        site_filter = " OR ".join(f"site:{d}" for d in allowed_domains)
        query = f"({query}) ({site_filter})"
    if blocked_domains:
        block_filter = " ".join(f"-site:{d}" for d in blocked_domains)
        query = f"({query}) {block_filter}"
    return query


def _serper_search(tool_name: str, query: str, n: int, api_key: str) -> ToolResult:
    payload = json.dumps({"q": query, "num": n}).encode()
    req = urllib.request.Request(
        "https://google.serper.dev/search",
        data=payload,
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        # URL https fija (endpoint Serper), sin entrada de usuario en el esquema.
        # `context` lleva la CA extra del proceso (`AGENTIC_EXTRA_CA_CERTS`): en A esta
        # llamada la haría `fetch`, al que Node ya le aplicó `NODE_EXTRA_CA_CERTS`. Sin
        # esto, un proxy corporativo que intercepta TLS —el caso que el propio canónico
        # documenta en `errorUtils.ts:99`— rompe la búsqueda aunque el CA esté declarado.
        # `None` = defaults de la stdlib, o sea el comportamiento de siempre.
        with urllib.request.urlopen(  # nosec B310
            req, timeout=_DEFAULT_TIMEOUT, context=default_ssl_context()
        ) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return ToolResult.error(tool_name, f"Serper HTTP {e.code}: {e.reason}")
    except Exception as exc:  # noqa: BLE001 — tras `HTTPError`; el resto vuelve al modelo como texto
        return ToolResult.error(tool_name, f"Web search failed: {exc}")

    results = data.get("organic", [])[:n]
    if not results:
        return ToolResult(tool_name=tool_name, output="No results found.")

    lines: list[str] = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. **{r.get('title', '(no title)')}**")
        lines.append(f"   {r.get('link', '')}")
        if r.get("snippet"):
            lines.append(f"   {r['snippet']}")
    return ToolResult(tool_name=tool_name, output="\n".join(lines) + _RECORDATORIO)
