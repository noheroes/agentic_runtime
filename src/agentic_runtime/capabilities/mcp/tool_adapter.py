from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from ...tools.protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

logger = logging.getLogger(__name__)

# El transporte real lo inyecta quien embebe el runtime: dado (tool_name, input)
# devuelve el texto de salida del server MCP. El shell no implementa transporte.
McpCall = Callable[[str, dict[str, Any]], Awaitable[str]]

# Claves de `_meta` de las que se lee el search hint, EN ORDEN de precedencia. El `_meta`
# de MCP es un espacio namespaced por vendor (`<vendor>/<campo>`) y el runtime es
# multi-modelo: no ancla ninguna marca en su default. La clave genérica va de serie; un
# integrador que hable el dialecto namespaced de un vendor concreto pasa la suya por
# `search_hint_meta_keys` — elegir dialecto es política del integrador (Filosofía B),
# igual que elegir modelo.
DEFAULT_SEARCH_HINT_META_KEYS: tuple[str, ...] = ("searchHint",)

#: Todo lo que no sea `[A-Za-z0-9_-]` en un nombre de tool MCP pasa a `_`, calcado de
#: `normalizeNameForMCP` (`services/mcp/normalization.ts:17-23`), que A aplica al nombre de
#: la tool en el propio ingreso (`buildMcpToolName`, `mcpStringUtils.ts:70-72`).
#: No es cosmético: el nombre lo escribe un server de terceros y viaja a DOS sitios donde
#: un salto de línea cambia el significado — el schema que ve el modelo y la lista de
#: diferidas, que se une por '\n' y se reconstruye leyéndola (`FIND-DEFER-1`). Con el
#: nombre crudo, un '\n' anunciaba dos tools inexistentes, perdía la real y el delta **no
#: convergía nunca**: se re-anunciaba en cada iteración del turno.
_UNSAFE_NAME_CHARS = re.compile(r"[^A-Za-z0-9_-]")

#: Cap de la descripción de una tool de TERCEROS que se expone al modelo, calcado de
#: `MAX_MCP_DESCRIPTION_LENGTH` (`services/mcp/client.ts:218`). El canónico razona el
#: número en su propio comentario (`:213-217`): «OpenAPI-generated MCP servers have been
#: observed dumping 15-60KB of endpoint docs into tool.description; this caps the p95 tail
#: without losing the intent». Es presupuesto de contexto Y superficie de inyección: el
#: texto lo escribe un tercero y viaja entero al prompt.
#: NO se aplica a las tools NATIVAS: en A el cap vive en el `prompt()` de la tool MCP
#: (`client.ts:1789-1794`), no en el serializador común (`api.ts:171`), y por eso una
#: descripción nativa larga —`Agent`, 16.6 KB en A— pasa sin tocar. Un cap en el
#: constructor de schemas truncaría esas también, que es divergencia por exceso.
MAX_MCP_DESCRIPTION_LENGTH = 2048

#: Sufijo literal del canónico (`client.ts:1792`): el modelo tiene que poder distinguir
#: «la tool se describe así» de «esto está cortado».
_TRUNCATION_SUFFIX = "… [truncated]"


#: Prefijo de los servers de claude.ai, que A trata aparte en la normalización
#: (`normalization.ts:8`): en esos nombres colapsa `_` repetidos y recorta los de los
#: extremos, porque `__` es el DELIMITADOR de `mcp__server__tool` y un nombre con dos
#: guiones bajos seguidos parte el nombre por donde no es.
_CLAUDEAI_SERVER_PREFIX = "claude.ai "


def normalize_mcp_tool_name(name: str) -> str:
    """Nombre saneado para exponer al modelo. El del server se conserva aparte.

    Calco de `normalizeNameForMCP` (`services/mcp/normalization.ts:17-23`), incluida su
    rama para los servers de claude.ai.
    """
    normalized = _UNSAFE_NAME_CHARS.sub("_", name)
    if name.startswith(_CLAUDEAI_SERVER_PREFIX):
        normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized


def mcp_tool_prefix(server_name: str) -> str:
    """`mcp__<server>__` — homólogo de `getMcpPrefix` (`mcpStringUtils.ts:38-41`)."""
    return f"mcp__{normalize_mcp_tool_name(server_name)}__"


def build_mcp_tool_name(server_name: str, tool_name: str) -> str:
    """Nombre CUALIFICADO `mcp__<server>__<tool>` — `buildMcpToolName` (`:50-52`).

    No es cosmética ni «namespacing por si acaso»: el prefijo es la única señal de que
    la tool vive en OTRO espacio que el del workspace, y sin él el modelo las mezcla.
    Medido en sesión real (`FIND-MCP-NAME-1`): con nombres desnudos el modelo listó el
    vault con `vault_list`, vio `index.md` y lo intentó leer con la tool NATIVA de
    ficheros contra el cwd → `[Errno 2] No such file or directory`, tres veces, hasta
    rendirse; nunca llamó a `vault_read`.

    El canónico le da además un segundo trabajo, el de PERMISOS
    (`getToolNameForPermissionCheck`, `mcpStringUtils.ts:59-67`, con la razón escrita):
    un `deny` sobre una nativa —`Write`— no debe casar con una tool MCP que se llame
    igual. Con nombre desnudo esa colisión es silenciosa en ambos sentidos.
    """
    return f"{mcp_tool_prefix(server_name)}{normalize_mcp_tool_name(tool_name)}"


def cap_mcp_description(text: str) -> str:
    """Trunca al cap del canónico, con su mismo sufijo. Por debajo del cap, identidad."""
    if len(text) <= MAX_MCP_DESCRIPTION_LENGTH:
        return text
    return text[:MAX_MCP_DESCRIPTION_LENGTH] + _TRUNCATION_SUFFIX


class McpTool:
    """Adapter de una tool MCP a `ToolProtocol` — tolerante con campos opcionales.

    Robustez ante terceros: `annotations` es del estándar MCP pero opcional; cada
    hint ausente degrada a un default seguro (espejo de `?? false` del canónico).
    Default conservador para tools de terceros no anotadas: requiere permiso y no
    es safe_for_background hasta que un `readOnlyHint` lo afirme explícitamente.
    """

    category = ToolCategory.SYSTEM
    # Las tools MCP son diferidas (workflow-specific): no se anuncian hasta que
    # ToolSearch las descubre. Siguen ejecutables desde el pool (M3).
    deferred = True

    def __init__(
        self,
        *,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        call: McpCall,
        read_only: bool = False,
        timeout_seconds: float = 30.0,
        server_name: str = "",
        search_hint: str = "",
        remote_name: str | None = None,
    ) -> None:
        # `name` es lo que ve el MODELO; `remote_name` lo que se le dice al SERVER. A
        # mantiene la misma separación: `name` = `fullyQualifiedName` y `mcpInfo.toolName`
        # = el original (`client.ts:1767-1773`). Sin ella, cualificar el nombre rompería
        # la invocación real de la tool.
        #
        # La CUALIFICACIÓN se hace aquí, en el constructor, por lo mismo que el cap de la
        # descripción: es el único punto por el que pasan todas las tools MCP
        # (`build_mcp_tool` es esquivable). Este comentario DECÍA que `name` ya era el
        # nombre cualificado mientras el código sólo lo saneaba — declaración en lugar de
        # pago (`D-07`), y lo que llegaba al modelo eran `vault_read`, `vault_list`…
        # Sin `server_name` no hay con qué cualificar y se sanea, como antes.
        self.name = build_mcp_tool_name(server_name, name) if server_name else normalize_mcp_tool_name(name)
        self.remote_name = remote_name if remote_name is not None else name
        # El cap se aplica AQUÍ, en el constructor, y no en `build_mcp_tool`: en A vive
        # dentro del `prompt()` de la propia tool MCP (`client.ts:1789-1794`), o sea en el
        # accessor, y por eso NINGÚN consumidor puede saltárselo — ni el schema que va a la
        # API (`api.ts:171`), ni el scoring de ToolSearch (`ToolSearchTool.ts:72`), ni la
        # contabilidad de presupuesto de diferidas (`toolSearch.ts:350`). B no tiene
        # accessor —`description` es un atributo que cada consumidor lee directo— así que
        # el único punto equivalente por el que pasa TODO es el constructor. Ponerlo en
        # `build_mcp_tool` dejaría fuera a quien instancie `McpTool` a mano.
        self.description = cap_mcp_description(description)
        # El texto ÍNTEGRO del server, como el `description()` de A (`client.ts:1786-1788`),
        # que devuelve `tool.description` SIN capar mientras `prompt()` sí capa. Truncar es
        # una decisión sobre la superficie del MODELO, no sobre el dato: quien integra
        # (inventarios, diagnóstico, UI) sigue teniendo el original. Sin consumidor dentro
        # de `src/` hoy — se dice, no se disfraza de cableado.
        self.raw_description = description
        self.input_schema = input_schema
        # `searchHint` del `_meta` del server (`services/mcp/client.ts:1778-1784`). Es la
        # única pista curada que tiene una tool MCP y puntúa +4 en ToolSearch, por encima
        # del +2 de la descripción — que para una tool diferida es la diferencia entre que
        # el modelo la encuentre por keyword o no la encuentre.
        self.search_hint = search_hint
        self._call = call
        # Tools MCP de terceros son no confiables: requieren permiso siempre.
        self.requires_permission = True
        # Solo las read-only se consideran seguras en background (unattended).
        self.safe_for_background = read_only
        self.timeout_seconds = timeout_seconds
        self.server_name = server_name
        # Homólogo de `mcpInfo` (`client.ts:1770`): la identidad SIN cualificar, que es
        # lo que necesita quien tenga que deshacer el prefijo — el chequeo de permisos
        # (`getToolNameForPermissionCheck`) y cualquier UI que muestre el nombre corto.
        # Se guarda el nombre REMOTO, no el saneado: es el que identifica a la tool en
        # el server.
        self.mcp_info = {"server_name": server_name, "tool_name": self.remote_name}

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        from .client import McpToolError

        try:
            output = await self._call(self.remote_name, input)  # una sola llamada al server
        except McpToolError as exc:
            # El server respondió isError=True: error de la tool, no del transporte.
            return ToolResult.error(self.name, str(exc))
        except Exception as exc:  # noqa: BLE001 — fallo de transporte MCP → error de tool, no caída del turno
            return ToolResult.error(self.name, f"mcp call failed: {exc}")
        return ToolResult(tool_name=self.name, output=output)


def build_mcp_tool(
    spec: dict[str, Any],
    call: McpCall,
    *,
    timeout_seconds: float = 30.0,
    server_name: str = "",
    search_hint_meta_keys: tuple[str, ...] = DEFAULT_SEARCH_HINT_META_KEYS,
) -> McpTool | None:
    """Construye un `McpTool` desde el spec crudo del server, tolerante.

    Solo `name` es obligatorio (identidad). Sin nombre → se omite con log
    (aislamiento por ítem). `description`/`inputSchema`/`annotations` degradan
    a defaults seguros si faltan o vienen malformados.
    """
    name = spec.get("name")
    if not name or not isinstance(name, str):
        logger.warning("mcp: tool sin 'name' válido en server %r — omitida", server_name)
        return None

    description = spec.get("description")
    if not isinstance(description, str):
        description = ""

    input_schema = spec.get("inputSchema")
    if not isinstance(input_schema, dict):
        input_schema = {}

    # Search hint del `_meta` del server (homólogo de `client.ts:1778-1784`, cuya clave
    # namespaced la aporta el integrador vía `search_hint_meta_keys`). El COLAPSO DE
    # ESPACIOS no es cosmético y el canónico lo explica: `_meta` lo escribe un server de
    # terceros, y un salto de línea ahí inyecta líneas huérfanas en la lista de diferidas,
    # que se une por '\n'. Lo que no sea `str` degrada a vacío, como el resto del adapter.
    meta = spec.get("_meta")
    search_hint = ""
    if isinstance(meta, dict):
        for key in search_hint_meta_keys:
            raw_hint = meta.get(key)
            if isinstance(raw_hint, str) and raw_hint.strip():
                search_hint = " ".join(raw_hint.split())
                break

    annotations = spec.get("annotations")
    read_only = False
    if isinstance(annotations, dict):
        read_only = annotations.get("readOnlyHint") is True

    return McpTool(
        name=normalize_mcp_tool_name(name),
        remote_name=name,
        description=description,
        input_schema=input_schema,
        call=call,
        read_only=read_only,
        timeout_seconds=timeout_seconds,
        server_name=server_name,
        search_hint=search_hint,
    )


__all__ = [
    "MAX_MCP_DESCRIPTION_LENGTH",
    "McpCall",
    "McpTool",
    "build_mcp_tool",
    "build_mcp_tool_name",
    "cap_mcp_description",
    "mcp_tool_prefix",
    "normalize_mcp_tool_name",
]
