from __future__ import annotations

import urllib.error
import urllib.request
from typing import TYPE_CHECKING

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

WEB_FETCH_TOOL_NAME = "WebFetch"
MAX_CONTENT_CHARS = 100_000


class WebFetchTool:
    name = WEB_FETCH_TOOL_NAME
    description = "Fetch content from a URL and return it as text."
    input_schema = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch content from.",
            },
            "prompt": {
                "type": "string",
                "description": "Optional instruction for how to process the fetched content.",
            },
        },
        "required": ["url"],
    }
    category = ToolCategory.NETWORK
    requires_permission = True
    safe_for_background = True
    timeout_seconds = 30.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        url = input.get("url", "")
        if not url:
            return ToolResult.error(self.name, "url is required.")

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "agent-runtime/1.0"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                raw = resp.read(MAX_CONTENT_CHARS * 4)
                content = raw.decode(charset, errors="replace")
        except urllib.error.HTTPError as e:
            return ToolResult.error(self.name, f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            return ToolResult.error(self.name, f"URL error: {e.reason}")
        except Exception as e:
            return ToolResult.error(self.name, f"Fetch failed: {e}")

        if len(content) > MAX_CONTENT_CHARS:
            content = content[:MAX_CONTENT_CHARS] + "\n[truncated]"

        return ToolResult(tool_name=self.name, output=content)
