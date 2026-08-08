"""Contrato de tool — T1 invariante (`SEAMS §S16`, `09·A1-A26`).

**Mínimo a propósito.** Los miembros de *comportamiento* de `S16`
(`check_permissions` · `validate_input` · `output_schema` ·
`is_concurrency_safe` · `interrupt_behavior` · `aliases` · `search_hint`) quedan
**fuera del tramo 1**, declarados, no olvidados: van con `04·modes`/`06·hooks`/`09`.
`is_concurrency_safe` en particular **no es cosmético** — el canónico particiona
por él el fan-out (default diez, `CG-TOOL-CONC`), luego el tramo 1 corre en
**serie**, declarado y no fingido.

Igual con `ToolResult`: `new_messages`/`structured`/`mcp_meta` son `K5`, por
encima de la línea de corte.
"""
from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from .abort import AbortReason
from .identity import Scope


class ToolCategory(str, Enum):
    UTILITY = "utility"
    SYSTEM = "system"
    FILE = "file"
    NETWORK = "network"
    BACKGROUND = "background"


@runtime_checkable
class ToolContext(Protocol):
    """Lo que el **contrato** de tool fija del contexto de ejecución, y nada más.

    Deliberadamente estrecho: el `ToolUseContext` real del base es mucho más
    ancho, pero anclar el contrato T1 a él forkearía el ecosistema (quien
    reimplemente una tool tendría que reimplementar el contexto entero).

    `stop` **no** está aquí todavía: hoy el base tipa `ctx.stop` como
    `asyncio.Event` y el motor consulta `.aborted`, que un `Event` no tiene. El
    cambio de tipo a `AbortSignal` es **C2** y se hace de punta a punta o no se
    hace; declararlo aquí antes de flipar el cable sería declarar-como-pago.
    """

    @property
    def scope(self) -> Scope | None: ...

    @property
    def messages(self) -> list[Any]: ...


class ToolResult:
    """Resultado de la ejecución de un tool.

    `context_modifier` es **opcional y por defecto `None`**, grafía exacta de
    `Tool.ts:330` (`contextModifier?: (context: ToolUseContext) => ToolUseContext`).
    El canónico lo honra *sólo* para tools que no son concurrency-safe; el tramo 1
    corre en **serie** (`is_concurrency_safe` está fuera, arriba), así que aquí se
    honra sin condición — correcto-para-serie y **declarado**: cuando entre la
    concurrencia, este es el punto que vuelve a abrirse.

    `ends_turn` **no tiene homólogo en el canónico** (`endsTurn` no existe en A).
    Es extensión de B y se declara como tal: A cede el turno bloqueando en
    `checkPermissions → behavior:'ask' + updatedInput` (verificado 1→EOF en
    `AskUserQuestionTool.tsx`, cuyo `call()` sólo devuelve `data`), y esa capa de
    interacción es `GAP-02`/`K1`, **por encima de la línea de corte**. Mientras no
    exista, B necesita un cable para ceder el turno; cuando `check_permissions`
    entre, `ends_turn` se re-examina contra ella y no antes.

    Ambos estaban siendo **inyectados por monkeypatch** con `type: ignore[attr-defined]`
    desde 9 call-sites y leídos por `getattr` en el loop: portantes pero invisibles
    para cualquier tercero que implemente el contrato (`FIND-TOOL4/A24`).

    El tipo de `context_modifier` es `Callable[[Any], Any]` **a propósito**: el contrato
    no puede nombrar el `ToolUseContext` del base sin forkear el ecosistema (mismo motivo
    por el que existe `ToolContext`, e invariante que `test_contracts_invariant` vigila
    incluso bajo `TYPE_CHECKING`). El alias preciso vive en el base, donde sí puede
    nombrarlo: `context.tool_use.ContextModifier = (ToolUseContext) -> ToolUseContext`.
    """

    def __init__(
        self,
        *,
        tool_name: str,
        output: str,
        is_error: bool = False,
        is_timeout: bool = False,
        is_aborted: bool = False,
        metadata: dict[str, Any] | None = None,
        context_modifier: Callable[[Any], Any] | None = None,
        ends_turn: bool = False,
        reason: AbortReason | None = None,
    ) -> None:
        self.tool_name = tool_name
        self.output = output
        self.is_error = is_error
        self.is_timeout = is_timeout
        self.is_aborted = is_aborted
        self.metadata = metadata or {}
        self.context_modifier = context_modifier
        self.ends_turn = ends_turn
        self.reason = reason

    @classmethod
    def error(cls, tool_name: str, message: str) -> ToolResult:
        return cls(tool_name=tool_name, output=message, is_error=True)

    @classmethod
    def timeout(cls, tool_name: str) -> ToolResult:
        return cls(tool_name=tool_name, output=f"timeout: {tool_name}", is_timeout=True)

    @classmethod
    def aborted(cls, tool_name: str, reason: AbortReason | None = None) -> ToolResult:
        """El motivo del corte viaja con el resultado (`FIND-TOOL5/SIG10`).

        La señal ya lo lleva (`AbortController` deriva `aborted` de `AbortReason`);
        lo que se perdía era el tramo señal→resultado. Va también al `output`, que
        es lo único que el modelo lee.
        """
        sufijo = f" ({reason.value})" if reason is not None else ""
        return cls(
            tool_name=tool_name,
            output=f"aborted: {tool_name}{sufijo}",
            is_aborted=True,
            reason=reason,
        )


@runtime_checkable
class ToolProtocol(Protocol):
    """Contrato estructural de tool.

    `is_enabled` **no** se declara aquí a propósito, y no por olvido: es
    *defaultable*, exactamente como en el canónico. A lo tipa requerido en
    `Tool` (`Tool.ts:403`) pero lo lista en `DefaultableToolKeys` (`:708`) y
    `buildTool` lo rellena con `() => true` (`:749,758`), de modo que ninguna
    definición de tool está obligada a escribirlo. Aquí el equivalente de ese
    relleno es `tool_is_enabled()`: declararlo requerido en un `Protocol`
    estructural y `runtime_checkable` rompería el `isinstance` de toda tool de
    terceros que no lo implemente — que es justo lo contrario del default.
    """

    name: str
    description: str
    #: Variable de INSTANCIA, y por eso las tools nativas silencian `RUF012`
    #: sobre su `input_schema` de clase. Esa regla pide `ClassVar`/`Final`, y las dos
    #: rompen aquí: con `ClassVar` mypy responde «expected instance variable, got
    #: class variable», y con `Final`, «expected settable variable, got read-only».
    #: Declararla `ClassVar` en el propio Protocol sería peor: `McpTool` la asigna
    #: por instancia desde la respuesta del server (`mcp/tool_adapter.py:113`), así
    #: que dejaría fuera al caso de tercero más importante que hay. El dict de clase
    #: de una tool nativa es una constante compartida que nadie muta; el aviso de
    #: ruff es correcto en general y falso contra ESTE contrato.
    input_schema: dict[str, Any]
    category: ToolCategory
    requires_permission: bool
    safe_for_background: bool
    timeout_seconds: float

    async def execute(self, input: dict[str, Any], ctx: Any) -> ToolResult: ...


def tool_is_enabled(tool: Any) -> bool:
    """¿Publica el host esta tool en este ensamblado? Homólogo de `Tool.isEnabled()`.

    Predicado de PUBLICACIÓN, no de permisos: una tool deshabilitada no se
    anuncia **ni se puede ejecutar**, porque en el canónico el filtro se aplica
    en el ensamblado del pool (`tools.ts:325-326`) y la resolución por nombre
    sale de ese mismo pool. Deny es «el usuario la prohibió»; esto es «el host
    no puede sostenerla». Ver `assemble_tool_pool`.

    Default `True` (espejo de `TOOL_DEFAULTS.isEnabled`, `Tool.ts:758`): quien
    no se pronuncia, se publica. Fail-open es lo correcto AQUÍ y no contradice
    el fail-closed del resto de `TOOL_DEFAULTS` — lo que se decide es si la
    tool existe para el modelo, no si se le concede un permiso.

    Se acepta tanto un método como un atributo booleano: el contrato es la
    conducta (`H-L4`), no la firma.
    """
    flag = getattr(tool, "is_enabled", True)
    return bool(flag() if callable(flag) else flag)


__all__ = [
    "ToolCategory",
    "ToolContext",
    "ToolProtocol",
    "ToolResult",
    "tool_is_enabled",
]
