from __future__ import annotations

import asyncio
import re
import urllib.error
import urllib.parse
import urllib.request
from html import unescape
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Any, ClassVar

from ...tls import default_ssl_context
from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

WEB_FETCH_TOOL_NAME = "WebFetch"

# `utils.ts:128` — truncado para no gastar tokens de más.
MAX_MARKDOWN_LENGTH = 100_000
TRUNCATION_MARKER = "\n\n[Content truncated due to length...]"
# `utils.ts:106` — tope de longitud de URL (mitiga exfiltración por URL).
MAX_URL_LENGTH = 2000
# `utils.ts:112` — tope de cuerpo descargado.
MAX_HTTP_CONTENT_LENGTH = 10 * 1024 * 1024
# `utils.ts:125` — tope de saltos de redirección del MISMO host. Sin él, un servidor
# hostil monta un bucle /a→/b→/a y el timeout se renueva en cada salto.
MAX_REDIRECTS = 10


class InvalidURL(ValueError):
    """URL rechazada por `_validate_url` — homólogo del `throw new Error('Invalid URL')`."""


def _validate_url(url: str) -> None:
    """Homólogo de `validateURL` (`utils.ts:139-169`). B no tenía NADA de esto.

    Tres controles, y ninguno es cosmético: el largo (exfiltración por URL), las
    credenciales embebidas (`user:pass@`), y el hostname de al menos dos etiquetas, que es
    lo que descarta `localhost` y los nombres internos no resolubles públicamente.
    NO se comprueba el esquema aquí: se sube http→https en `_upgrade_scheme`.
    """
    if len(url) > MAX_URL_LENGTH:
        raise InvalidURL(f"URL demasiado larga ({len(url)} > {MAX_URL_LENGTH}).")
    parsed = urllib.parse.urlsplit(url)
    if not parsed.hostname:
        raise InvalidURL("URL sin host.")
    if parsed.username or parsed.password:
        raise InvalidURL("URL con credenciales embebidas.")
    if len(parsed.hostname.split(".")) < 2:
        raise InvalidURL(
            f"host '{parsed.hostname}' no es públicamente resoluble (se exige dominio con punto)."
        )


def _upgrade_scheme(url: str) -> str:
    """`utils.ts:375-379`: http se sube a https antes de pedir nada."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme == "http":
        return urllib.parse.urlunsplit(parsed._replace(scheme="https"))
    return url


def _is_permitted_redirect(original: str, redirect: str) -> bool:
    """`isPermittedRedirect` (`utils.ts:212-243`).

    Se sigue sólo lo que NO cambia de origen: mismo esquema, mismo puerto, sin
    credenciales, y mismo host salvo por el `www.`. Cualquier otra cosa se le DEVUELVE al
    modelo en vez de seguirla — es la contramedida contra open-redirect: un dominio de
    confianza que rebota a uno hostil no debe arrastrar la petición en silencio.
    """
    try:
        o = urllib.parse.urlsplit(original)
        r = urllib.parse.urlsplit(redirect)
    except ValueError:
        return False
    if r.scheme != o.scheme or r.port != o.port:
        return False
    if r.username or r.password:
        return False

    def _sin_www(host: str | None) -> str:
        return re.sub(r"^www\.", "", host or "")

    return _sin_www(o.hostname) == _sin_www(r.hostname)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """No sigue NINGUNA redirección: la decisión la toma `_descargar`, no urllib."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


class _Redirect:
    """Redirección que NO se siguió — el modelo recibe la URL y decide."""

    def __init__(self, original: str, destino: str, code: int) -> None:
        self.original = original
        self.destino = destino
        self.code = code


class _Descarga:
    def __init__(self, cuerpo: str, content_type: str, code: int) -> None:
        self.cuerpo = cuerpo
        self.content_type = content_type
        self.code = code


def _descargar(url: str, profundidad: int = 0) -> _Descarga | _Redirect:
    """Descarga SÍNCRONA, pensada para correr en un thread (`asyncio.to_thread`).

    Vive aparte de `execute` a propósito: así el bloqueo queda encerrado en una función
    que NO es corrutina, y es imposible volver a llamarla desde el event loop por
    descuido sin que se vea en el diff.
    """
    if profundidad > MAX_REDIRECTS:
        raise InvalidURL(f"demasiadas redirecciones (más de {MAX_REDIRECTS}).")

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "agent-runtime/1.0",
            "Accept": "text/markdown, text/html, */*",
        },
    )
    # El handler https lleva la CA extra del proceso (`AGENTIC_EXTRA_CA_CERTS`). En A no
    # hay línea equivalente porque Node aplica `NODE_EXTRA_CA_CERTS` a todo el proceso y
    # `fetch` la hereda; en B el opener se construye a mano, así que si no se le da el
    # contexto se queda con el almacén por defecto. `None` = defaults de la stdlib.
    opener = urllib.request.build_opener(
        _NoRedirect, urllib.request.HTTPSHandler(context=default_ssl_context())
    )
    try:
        # esquema validado por el llamante a http/https (mitiga CWE-22)
        with opener.open(req, timeout=20) as resp:  # nosec B310
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read(MAX_HTTP_CONTENT_LENGTH)
            content_type = resp.headers.get("content-type", "") or ""
            code = int(resp.status)
    except urllib.error.HTTPError as exc:
        if exc.code in (301, 302, 307, 308):
            location = exc.headers.get("location") if exc.headers else None
            if not location:
                raise InvalidURL("redirección sin cabecera Location.") from exc
            destino = urllib.parse.urljoin(url, location)
            if _is_permitted_redirect(url, destino):
                return _descargar(destino, profundidad + 1)
            return _Redirect(url, destino, exc.code)
        raise

    return _Descarga(raw.decode(charset, errors="replace"), content_type, code)


class _AMarkdown(HTMLParser):
    """HTML→markdown. Homólogo FUNCIONAL de `turndown` (`utils.ts:456-458`), no idéntico.

    Se dice sin adornos: esto cubre el subconjunto que carga el peso —titulares, enlaces,
    listas, código, cita, énfasis, saltos de bloque— y descarta `script`/`style`/`head`.
    No es turndown (tablas, anidamiento arbitrario). Lo que resuelve es el problema real:
    antes se devolvía el HTML EN BRUTO, que ni es legible para el modelo ni cabe en el
    presupuesto de tokens de una página normal.
    """

    _IGNORAR: ClassVar[set[str]] = {"script", "style", "head", "noscript", "svg"}
    _BLOQUE: ClassVar[set[str]] = {
        "p", "div", "section", "article", "header", "footer", "tr", "br",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._partes: list[str] = []
        self._saltar = 0
        self._href: str | None = None
        self._en_pre = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._IGNORAR:
            self._saltar += 1
            return
        if self._saltar:
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._partes.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "li":
            self._partes.append("\n- ")
        elif tag in self._BLOQUE:
            self._partes.append("\n\n")
        elif tag == "a":
            self._href = dict(attrs).get("href")
            self._partes.append("[")
        elif tag in ("strong", "b"):
            self._partes.append("**")
        elif tag in ("em", "i"):
            self._partes.append("*")
        elif tag == "code":
            self._partes.append("`")
        elif tag == "pre":
            self._en_pre += 1
            self._partes.append("\n\n```\n")
        elif tag == "blockquote":
            self._partes.append("\n\n> ")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._IGNORAR:
            self._saltar = max(0, self._saltar - 1)
            return
        if self._saltar:
            return
        if tag == "a":
            destino = self._href or ""
            self._partes.append(f"]({destino})")
            self._href = None
        elif tag in ("strong", "b"):
            self._partes.append("**")
        elif tag in ("em", "i"):
            self._partes.append("*")
        elif tag == "code":
            self._partes.append("`")
        elif tag == "pre":
            self._en_pre = max(0, self._en_pre - 1)
            self._partes.append("\n```\n")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._partes.append("\n")

    def handle_data(self, data: str) -> None:
        if self._saltar:
            return
        self._partes.append(data if self._en_pre else re.sub(r"\s+", " ", data))

    def markdown(self) -> str:
        texto = unescape("".join(self._partes))
        texto = re.sub(r"\n{3,}", "\n\n", texto)
        return texto.strip()


def html_a_markdown(html: str) -> str:
    parser = _AMarkdown()
    parser.feed(html)
    parser.close()
    return parser.markdown()


class WebFetchTool:
    name = WEB_FETCH_TOOL_NAME
    # `Tool.searchHint` del canónico (`WebFetchTool.ts:68`), literal. Fuera del contrato T1
    # (`contracts/tools.py:5`) pero leído opcionalmente por ToolSearch para rankear.
    search_hint = "fetch and extract content from a URL"
    # Homologada contra `DESCRIPTION` + `prompt()` (`WebFetchTool/prompt.ts:3-21`,
    # `WebFetchTool.ts:181-190`) — `GAP-PROMPT-1`. Se conserva el aviso de URLs
    # autenticadas, que en A va PRIMERO y en mayúsculas porque gobierna conducta.
    # DIVERGENCIA DECLARADA `GAP-WEBFETCH-2`: A procesa el markdown con un modelo pequeño
    # (`applyPromptToMarkdown` → `queryHaiku`) y devuelve la RESPUESTA del modelo; B
    # devuelve el markdown y deja la extracción al modelo principal. No se finge: la
    # descripción dice qué devuelve B de verdad. Ver la nota de `execute` sobre el seam.
    description = """IMPORTANT: WebFetch WILL FAIL for authenticated or private URLs. Before using this
tool, check if the URL points to an authenticated service (e.g. Google Docs, Confluence,
Jira, GitHub). If so, look for a specialized tool that provides authenticated access.

- Fetches content from a specified URL, converts HTML to markdown, and returns it
- Takes a URL and a prompt describing what you want from the page
- Use this tool when you need to retrieve and analyze web content

Usage notes:
- The URL must be a fully-formed valid URL
- HTTP URLs will be automatically upgraded to HTTPS
- The content is returned as markdown for YOU to extract from; it is not pre-summarized
  by another model, so state in `prompt` what you are after and then read the result
- Long pages are truncated; the output says so when that happens
- This tool is read-only and does not modify any files
- When a URL redirects to a different host, the tool does NOT follow it: it reports the
  redirect URL and you should make a new WebFetch request with that URL
- For GitHub URLs, prefer the `gh` CLI via the bash tool (e.g. gh pr view, gh issue view)"""
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch content from.",
            },
            "prompt": {
                "type": "string",
                "description": "What you want to extract from the page.",
            },
        },
        # `prompt` es REQUERIDO en A (`WebFetchTool.ts:27`, `z.string()` sin `.optional()`).
        # En B era opcional Y SE IGNORABA, que era `GAP-WEBFETCH-1`.
        "required": ["url", "prompt"],
    }
    category = ToolCategory.NETWORK
    requires_permission = True
    safe_for_background = True
    timeout_seconds = 30.0

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        url = input.get("url", "")
        if not url:
            return ToolResult.error(self.name, "url is required.")
        # Solo http/https: cierra el esquema file:/ y custom (mitiga CWE-22).
        if urllib.parse.urlsplit(url).scheme not in ("http", "https"):
            return ToolResult.error(self.name, "solo se permiten URLs http/https.")
        try:
            _validate_url(url)
        except InvalidURL as exc:
            return ToolResult.error(self.name, f"URL inválida: {exc}")

        try:
            # `FIND-C6-2`: la descarga va a un THREAD, no al event loop. `urlopen` es
            # síncrono y hacerlo directamente aquí, dentro de un `async def`, congelaba el
            # único event loop hasta 20 s: durante ese rato ni el cap del dispatcher
            # (`asyncio.wait_for` no puede preemptar una corrutina que no cede) ni el
            # stream ni los subagentes ni las notificaciones avanzaban. A no tiene ese
            # problema porque su E/S de red es asíncrona de raíz y además lleva su propio
            # `timeout` (`utils.ts:116`, `FETCH_TIMEOUT_MS = 60_000`; B usa 20 s porque su
            # cap de dispatcher son 30 s — divergencia de valor, declarada).
            resultado = await asyncio.to_thread(_descargar, _upgrade_scheme(url))
        except InvalidURL as exc:
            return ToolResult.error(self.name, str(exc))
        except urllib.error.HTTPError as e:
            return ToolResult.error(self.name, f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            return ToolResult.error(self.name, f"URL error: {e.reason}")
        except Exception as e:  # noqa: BLE001 — tras los errores HTTP/URL nombrados; el resto también se reporta
            return ToolResult.error(self.name, f"Fetch failed: {e}")

        if isinstance(resultado, _Redirect):
            # `WebFetchTool.ts:227-235`: no se sigue, se INFORMA. El mensaje lleva la URL
            # de destino para que el modelo pueda reintentar con ella si procede.
            prompt = input.get("prompt", "")
            return ToolResult(
                tool_name=self.name,
                output=(
                    "REDIRECT DETECTED: The URL redirects to a different host.\n\n"
                    f"Original URL: {resultado.original}\n"
                    f"Redirect URL: {resultado.destino}\n"
                    f"Status: {resultado.code}\n\n"
                    "To complete your request, call WebFetch again with:\n"
                    f'- url: "{resultado.destino}"\n'
                    f'- prompt: "{prompt}"'
                ),
            )

        contenido = (
            html_a_markdown(resultado.cuerpo)
            if "text/html" in resultado.content_type
            else resultado.cuerpo
        )
        # `applyPromptToMarkdown` (`utils.ts:492-496`) trunca ANTES de procesar, con este
        # marcador. Aquí no hay modelo secundario que proteger, pero sí el presupuesto de
        # tokens del principal, que es la misma razón.
        #
        # `GAP-WEBFETCH-2` (lo que queda, NOMBRADO y no fingido): A pasa el markdown por
        # `queryHaiku` con `makeSecondaryModelPrompt` y devuelve la respuesta del modelo.
        # B no lo hace y NO se cablea aquí por decisión de frontera, no por comodidad:
        # `queryHaiku` FIJA un modelo, y elegir modelo es política del integrador — el
        # runtime que se lo inventa está componiendo lo que Filosofía B le prohíbe
        # componer. El pago pide un seam inyectado (como `runner`/`task_registry`), y eso
        # es una decisión de contrato, no un detalle de esta tool.
        if len(contenido) > MAX_MARKDOWN_LENGTH:
            contenido = contenido[:MAX_MARKDOWN_LENGTH] + TRUNCATION_MARKER

        return ToolResult(tool_name=self.name, output=contenido)
