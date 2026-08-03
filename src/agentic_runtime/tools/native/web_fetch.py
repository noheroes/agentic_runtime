from __future__ import annotations

import asyncio
import urllib.error
import urllib.request
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

WEB_FETCH_TOOL_NAME = "WebFetch"
MAX_CONTENT_CHARS = 100_000


def _descargar(url: str) -> str:
    """Descarga SÍNCRONA, pensada para correr en un thread (`asyncio.to_thread`).

    Vive aparte de `execute` a propósito: así el bloqueo queda encerrado en una función
    que NO es corrutina, y es imposible volver a llamarla desde el event loop por
    descuido sin que se vea en el diff.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "agent-runtime/1.0"})
    # esquema validado por el llamante a http/https (mitiga CWE-22)
    with urllib.request.urlopen(req, timeout=20) as resp:  # nosec B310
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read(MAX_CONTENT_CHARS * 4)
    return str(raw.decode(charset, errors="replace"))


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
        # Solo http/https: cierra el esquema file:/ y custom (mitiga CWE-22).
        if urlparse(url).scheme not in ("http", "https"):
            return ToolResult.error(self.name, "solo se permiten URLs http/https.")

        try:
            # `FIND-C6-2`: la descarga va a un THREAD, no al event loop. `urlopen` es
            # síncrono y hacerlo directamente aquí, dentro de un `async def`, congelaba el
            # único event loop hasta 20 s: durante ese rato ni el cap del dispatcher
            # (`asyncio.wait_for` no puede preemptar una corrutina que no cede) ni el
            # stream ni los subagentes ni las notificaciones avanzaban. A no tiene ese
            # problema porque su E/S de red es asíncrona de raíz y además lleva su propio
            # `timeout` (`WebFetchTool/utils.ts:272-282`, `FETCH_TIMEOUT_MS = 60_000`).
            # Cediendo el control, el cap del dispatcher vuelve a valer lo que promete.
            content = await asyncio.to_thread(_descargar, url)
        except urllib.error.HTTPError as e:
            return ToolResult.error(self.name, f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            return ToolResult.error(self.name, f"URL error: {e.reason}")
        except Exception as e:
            return ToolResult.error(self.name, f"Fetch failed: {e}")

        if len(content) > MAX_CONTENT_CHARS:
            content = content[:MAX_CONTENT_CHARS] + "\n[truncated]"

        return ToolResult(tool_name=self.name, output=content)
