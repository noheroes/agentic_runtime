from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class PermissionMode(str, Enum):
    """Modo de permiso del turno (`GAP-02` = `K1`; `01·CTR-08`, `SEAMS §S17`).

    Hoy el runtime **no tenía modo**: se simulaba con `app_state.native["plan_mode"]`,
    un hack que `DEUDA-B B-02` cataloga y que muere al existir este campo.

    El **motor** de los modos (candado read-only de `plan` con exención del
    plan-file, carve-out de escritura memory-scoped, auto-allow de Skill, gate FQ
    de tools MCP) queda **fuera del tramo 1**, nombrado: es `K1`, por encima de la
    línea de corte. Aquí se **define** el contrato para que las firmas de C2..C10
    no tengan que reabrirse cuando el motor entre.
    """

    DEFAULT = "default"
    ACCEPT_EDITS = "acceptEdits"
    PLAN = "plan"
    BYPASS = "bypassPermissions"


class PermissionContext(BaseModel):
    """Runtime-level permission rules for assembling and executing tools.

    This is intentionally provider-agnostic. Skills, MCP, plugins, or project
    adapters may contribute rules, but the runtime only sees tool names.
    """

    #: El default es `default` y **nunca** `bypassPermissions`: un contrato cuyo
    #: default desactiva el gate convierte el olvido del integrador en ausencia
    #: silenciosa de política.
    mode: PermissionMode = PermissionMode.DEFAULT
    always_allow_command: list[str] = Field(default_factory=list)
    always_allow_session: list[str] = Field(default_factory=list)
    always_deny: list[str] = Field(default_factory=list)

    def allowed_names(self) -> set[str]:
        return set(self.always_allow_command) | set(self.always_allow_session)

    def denied_names(self) -> set[str]:
        return set(self.always_deny)

    def with_command_allow(self, names: list[str]) -> PermissionContext:
        merged = [*self.always_allow_command]
        seen = set(merged)
        for name in names:
            if name not in seen:
                merged.append(name)
                seen.add(name)
        return self.model_copy(update={"always_allow_command": merged})

    def with_mode(self, mode: PermissionMode) -> PermissionContext:
        return self.model_copy(update={"mode": mode})


__all__ = ["PermissionContext", "PermissionMode"]
