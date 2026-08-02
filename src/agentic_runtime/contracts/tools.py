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
    name: str
    description: str
    input_schema: dict[str, Any]
    category: ToolCategory
    requires_permission: bool
    safe_for_background: bool
    timeout_seconds: float

    async def execute(self, input: dict[str, Any], ctx: Any) -> ToolResult: ...


__all__ = ["ToolCategory", "ToolContext", "ToolProtocol", "ToolResult"]
