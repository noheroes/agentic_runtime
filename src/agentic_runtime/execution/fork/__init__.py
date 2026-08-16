"""Fork primitives for the agentic runtime.

ForkContext  — declarative descriptor of what a fork should produce.
ForkSnapshot — immutable capture of parent state at fork time.
ForkPolicy   — rules for what the child inherits vs. isolates.
RuntimeContextForker — service that applies the policy and returns a child ToolUseContext.
"""
from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ...context.tool_use import AppState, ToolUseContext
from ...contracts.abort import AbortController, AbortSignal
from ...contracts.identity import Scope
from ...contracts.permissions import PermissionContext
from ...tools.pool import ToolPool


class ForkPolicy(BaseModel):
    """Rules for what a child agent inherits from its parent."""

    inherit_messages: bool = False
    inherit_permissions: bool = True
    inherit_tool_pool: bool = True
    inherit_capabilities: bool = True
    propagate_abort: bool = True


class ForkSnapshot(BaseModel):
    """Immutable capture of parent state at the moment of fork.

    `extra="forbid"` no es celo: mientras el default de pydantic estuvo activo, un
    `ForkSnapshot(user_id=...)` —la grafía vieja del cable de identidad— se **descartaba
    en silencio** y el test que lo usaba seguía verde sin probar nada. Es `AC-39`
    mecanizado: cuatro grafías de un cable son cuatro implementaciones divergentes, y
    aquí el tipo las convierte en un error en vez de en un campo perdido.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str
    # El hijo hereda el SCOPE del padre, no un `user_id` (`C9`/`D-11`): su transcript y
    # su memoria caen bajo la misma frontera de aislamiento que los del padre.
    scope: Scope | None = None
    subagent_depth: int = 0
    messages: tuple[Any, ...] = ()
    permissions: PermissionContext = Field(default_factory=PermissionContext)
    tool_pool: ToolPool = Field(default_factory=ToolPool)
    # Bolsa de extensión per-request del integrador (AppState.capabilities). El hijo la
    # hereda por el contexto, igual que el canónico threadea options.mcpClients del padre
    # al subagente (runAgent.ts:648-656). Sin esto el delegador MCP per-tenant del
    # integrador no vería al provider del padre en subagentes.
    capabilities: dict[str, Any] = Field(default_factory=dict)
    cwd: str | None = None


class ForkContext(BaseModel):
    """Declarative descriptor of a fork request."""

    prompt: str
    policy: ForkPolicy
    parent_snapshot: ForkSnapshot
    subagent_type: str | None = None
    model_override: str | None = None
    timeout_seconds: float | None = None
    max_turns: int | None = None


class RuntimeContextForker:
    """Applies a ForkContext and returns a child ToolUseContext ready for execution."""

    def fork(
        self,
        fork_ctx: ForkContext,
        parent_stop: AbortSignal | None = None,
    ) -> ToolUseContext:
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        snap = fork_ctx.parent_snapshot
        policy = fork_ctx.policy

        messages: list[Any] = list(snap.messages) if policy.inherit_messages else []
        permissions = snap.permissions if policy.inherit_permissions else PermissionContext()
        tool_pool = snap.tool_pool if policy.inherit_tool_pool else ToolPool()
        # Contenedor independiente, valores compartidos (mismo provider vivo): espejo del
        # patrón de messages (tupla→list). El hijo puede añadir/quitar claves sin tocar al padre.
        capabilities = dict(snap.capabilities) if policy.inherit_capabilities else {}

        # Aislado = controlador PROPIO, no «sin señal»: el hijo tiene que poder
        # abortarse por su cuenta sin que eso toque al padre (`C2`/`S2`). Y si se pidió
        # propagar pero nadie pasó la señal del padre, el hijo nace igualmente con la
        # suya: quedarse en `None` dejaba al subagente literalmente inabortable.
        # ⚠ diferido nombrado: que la señal del PADRE llegue sola hasta aquí exige que
        # viaje con el despacho del subagente (hoy `_build_child` sólo tiene el
        # `ForkSnapshot`, que es estado serializable y no porta el controlador vivo).
        stop: AbortSignal | None = (
            parent_stop if (policy.propagate_abort and parent_stop is not None) else AbortController()
        )

        return ToolUseContext(
            session_id=snap.session_id,
            scope=snap.scope,
            agent_id=agent_id,
            # Identidad ESTABLE del subagente (`ID-5`): el `agent_id` de arriba sigue
            # siendo el handle de ESTA ejecución, pero la clave de scope persistente es
            # el tipo, que sí se repite entre despachos.
            subagent_type=fork_ctx.subagent_type,
            messages=messages,
            tool_pool=tool_pool,
            app_state=AppState(permissions=permissions, capabilities=capabilities),
            stop=stop,
            cwd=snap.cwd,
        )


__all__ = ["ForkContext", "ForkPolicy", "ForkSnapshot", "RuntimeContextForker"]
