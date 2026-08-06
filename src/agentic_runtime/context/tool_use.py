from __future__ import annotations

import asyncio
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from ..contracts.abort import AbortSignal
from ..contracts.identity import Scope
from ..contracts.permissions import PermissionContext


def _default_pool() -> "Any":
    from ..tools.pool import ToolPool
    return ToolPool()


def _default_presentation() -> "Any":
    # Default seguro simétrico al de `fs`: identidad (= comportamiento CLI canónico,
    # el FS del usuario ES el del agente). Antes era `None` y cada consumidor repetía
    # el fallback `ctx.presentation or IdentityPresentation()` por su cuenta; una tool
    # que olvidara la guarda emitía la ruta host cruda bajo un deployment fake-path.
    from .presentation import IdentityPresentation
    return IdentityPresentation()


def _default_fs() -> "Any":
    # Default seguro: confina a cwd() — nunca ilimitado. El consumidor lo sobreescribe
    # con el allow-set real (workspace_dir / pwd) por sesión.
    from ..tools.fs_env import ConfinedFilesystem
    return ConfinedFilesystem()


class AppState(BaseModel):
    """Provider-agnostic runtime-visible application state."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    permissions: PermissionContext = Field(default_factory=PermissionContext)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    native: dict[str, Any] = Field(default_factory=dict)


class ToolUseContext(BaseModel):
    """Operational context for one agentic runtime turn.

    **`user_id` ya no existe aquí (`C9` · `DEUDA-A ID-1`/`ID-3`, `D-11`).** El runtime
    no interpreta identidad de usuario y no la inventa; lo que necesitaba de ella era
    *scoping de persistencia*, y eso ahora viaja por `scope`, un token opaco que
    **produce el integrador**. Un turno completo corre sin conocer ningún `user_id`
    (gate `E6` del tramo 1) — que es la prueba de que Filosofía B se cumple.
    """

    # `extra="forbid"` (`C9`/`AC-39`): un kwarg con la grafía vieja del cable de
    # identidad —`user_id=…`— debe REVENTAR, no descartarse en silencio dejando verde
    # un test que ya no prueba nada.
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    session_id: str
    # Frontera de aislamiento de los repos (memoria, tokens MCP, skills, transcript).
    # `None` = sin scope: los repos que necesiten clave **fallan**, no inventan una.
    scope: Scope | None = None
    agent_id: str | None = None
    is_subagent: bool = False  # kind: subagente unattended → toolset filtrado a safe_for_background
    # Tipo del subagente — identidad ESTABLE entre despachos (`ID-5`). El `agent_id` es
    # un uuid por fork y por tanto inservible como clave persistente: keyear la memoria
    # por él hacía que un subagente-de-tipo-X no recuperara nunca su memoria.
    subagent_type: str | None = None
    subagent_depth: int = 0  # profundidad de anidamiento; la tool Agent la usa como tope
    turn_count: int = 0
    messages: list[Any] = Field(default_factory=list)
    tool_pool: Any = Field(default_factory=_default_pool)
    app_state: AppState = Field(default_factory=AppState)
    # `C2`/`S2`: señal de abort CONSULTABLE (`.aborted`/`.reason()`), no `asyncio.Event`.
    # El tipo viejo viajaba hasta el provider y ningún provider sabía leerlo.
    stop: AbortSignal | None = None
    event_queue: asyncio.Queue | None = None
    storage: Any = None
    # `S12`: traducción de rutas host → texto que ve el modelo. `to_llm` en el punto de
    # emisión (forward, exacto) + `sanitize_output` en el choke del dispatcher (red de
    # seguridad, regex y por tanto perdible — `FIND-VOICE1` probó que la red se escapa).
    presentation: Any = Field(default_factory=_default_presentation)
    exec_env: Any = None
    fs: Any = Field(default_factory=_default_fs)
    # Directorio de trabajo de los comandos de shell. Es un CABLE, no estado compuesto
    # por el runtime (`D-11`): `None` = el integrador no lo declaró, y entonces `BashTool`
    # cae al `write_root` del confinamiento en vez de heredar el cwd del PROCESO host
    # —que era el defecto de contrato #1—. A lo lleva en estado de sesión (`pwd()` /
    # `getCwdState()`, `cwd.ts`); aquí viaja por turno y `BashTool` lo reescribe con el
    # `pwd -P` releído, de modo que un `cd` persiste ENTRE COMANDOS DEL TURNO. La
    # persistencia ENTRE TURNOS es del integrador (`root_context_modifier`): el runtime
    # abre `Session` fresca por turno (`S20`) y no compone identidad ni sesión.
    cwd: str | None = None
    # Seam de credenciales git (clone_repository): el integrador lo cablea al token del
    # MCP per-tenant. None → clones sin auth (repos públicos). GitCredentialProvider.
    git_credentials: Any = None
    # `S18` (`C8`): el runner de subagentes que la tool `Agent` usa para delegar. Lo
    # threadea el runtime desde su propia inyección — aquí murió el singleton global
    # `get_runner()`, que nadie poblaba en producción (`FIND-EXEC1`). `None` = costura sin
    # poblar: la tool devuelve `is_error` limpio, no revienta.
    runner: Any = None
    # `S19` (`C7`): el registry de tasks que ven las tools `Task*`. Antes iban por el
    # global `get_registry()` mientras el runtime usaba su instancia inyectada — dos
    # caminos que podían divergir, y de hecho divergían: nadie llamaba `set_registry`, así
    # que las seis tools reventaban en producción. Un solo camino: el del runtime.
    task_registry: Any = None

    @property
    def permission_context(self) -> PermissionContext:
        return self.app_state.permissions

    def with_permissions(self, permissions: PermissionContext) -> "ToolUseContext":
        return self.model_copy(
            update={"app_state": self.app_state.model_copy(update={"permissions": permissions})}
        )


ContextModifier = Callable[[ToolUseContext], ToolUseContext]


__all__ = ["AppState", "ContextModifier", "ToolUseContext"]
