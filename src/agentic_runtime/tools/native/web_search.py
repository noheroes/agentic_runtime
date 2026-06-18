from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

logger = logging.getLogger(__name__)

WEB_SEARCH_TOOL_NAME = "WebSearch"
_DEFAULT_TIMEOUT = 20
_DEFAULT_MAX_RESULTS = 5
_MAX_RESULTS_CAP = 20


class WebSearchTool:
    name = WEB_SEARCH_TOOL_NAME
    description = (
        "Search the web and return a list of results (title, URL, snippet). "
        "Use when you need to find current information, documentation, or resources."
    )
    input_schema = {
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

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
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

        return _serper_search(self.name, effective_query, max_results, api_key)


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
        # URL https fija (endpoint Serper), sin entrada de usuario en el esquema
        with urllib.request.urlopen(req, timeout=_DEFAULT_TIMEOUT) as resp:  # nosec B310
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return ToolResult.error(tool_name, f"Serper HTTP {e.code}: {e.reason}")
    except Exception as exc:
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
    return ToolResult(tool_name=tool_name, output="\n".join(lines))
