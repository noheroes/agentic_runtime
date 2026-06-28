"""Scope/procedencia de servers MCP — homologado al canónico (`claude-code/src`).

El runtime provee el SET COMPLETO de scopes y la maquinaria (precedencia,
exclusividad, gate de mutabilidad, merge por nombre). Quien integra el runtime
decide QUÉ scopes usa y con qué productor (ver `config_store.ScopedMcpConfigStore`).

Decisiones (contrastadas con `services/mcp/config.ts` y `types.ts`):
- Enum canónico `ConfigScope` (`types.ts:10-20`).
- Precedencia por nombre: enterprise > local > project > user (`config.ts:1046-1057`);
  el merge escribe de menor a mayor, el mayor sobreescribe (`config.ts:1231-1238`).
  `dynamic`/`claudeai` quedan por debajo de `user` (no entran al lookup canónico).
- Exclusividad: si un scope administrado (managed/enterprise) aporta servers, los
  scopes no exclusivos se descartan (`config.ts:1084` para enterprise).
- Gate de mutabilidad: el usuario solo puede mutar user/project/local; managed,
  enterprise, claudeai y dynamic son de solo lectura (`config.ts:705-709`).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class McpScope(str, Enum):
    """Procedencia de la config de un server MCP (espejo de `ConfigScope`)."""

    ENTERPRISE = "enterprise"
    MANAGED = "managed"
    LOCAL = "local"
    PROJECT = "project"
    USER = "user"
    CLAUDEAI = "claudeai"
    DYNAMIC = "dynamic"


# Ranking de precedencia: mayor número gana en el merge por nombre.
_PRECEDENCE: dict[McpScope, int] = {
    McpScope.DYNAMIC: 0,
    McpScope.CLAUDEAI: 1,
    McpScope.USER: 2,
    McpScope.PROJECT: 3,
    McpScope.LOCAL: 4,
    McpScope.MANAGED: 5,
    McpScope.ENTERPRISE: 6,
}

# Scopes administrados: si alguno aporta servers, suprime a los no exclusivos.
EXCLUSIVE_SCOPES = frozenset({McpScope.MANAGED, McpScope.ENTERPRISE})

# Scopes que el usuario puede mutar (add/toggle/remove). El resto es solo lectura.
MUTABLE_SCOPES = frozenset({McpScope.USER, McpScope.PROJECT, McpScope.LOCAL})


@dataclass(frozen=True)
class ScopedConfig:
    """Config cruda de un server con su procedencia resuelta tras el merge."""

    scope: McpScope
    raw: dict


def is_mutable(scope: McpScope) -> bool:
    return scope in MUTABLE_SCOPES


def assert_mutable(scope: McpScope) -> None:
    """Borde de seguridad: lanza si se intenta mutar un scope de solo lectura."""
    if not is_mutable(scope):
        raise ValueError(
            f"scope {scope.value!r} no es mutable por el usuario "
            f"(mutables: {sorted(s.value for s in MUTABLE_SCOPES)})"
        )


def merge_scoped(scoped: dict[McpScope, dict[str, dict]]) -> dict[str, ScopedConfig]:
    """Mergea configs por nombre aplicando precedencia y exclusividad.

    `scoped`: {scope: {name: raw}}. Devuelve {name: ScopedConfig} con la
    procedencia ganadora. Si hay servers en un scope exclusivo, solo los scopes
    exclusivos contribuyen (entre ellos sigue aplicando precedencia)."""
    has_exclusive = any(scoped.get(s) for s in EXCLUSIVE_SCOPES)
    active = {
        scope: configs
        for scope, configs in scoped.items()
        if configs and (not has_exclusive or scope in EXCLUSIVE_SCOPES)
    }
    merged: dict[str, ScopedConfig] = {}
    for scope in sorted(active, key=lambda s: _PRECEDENCE[s]):
        for name, raw in active[scope].items():
            merged[name] = ScopedConfig(scope=scope, raw=raw)
    return merged


__all__ = [
    "EXCLUSIVE_SCOPES",
    "MUTABLE_SCOPES",
    "McpScope",
    "ScopedConfig",
    "assert_mutable",
    "is_mutable",
    "merge_scoped",
]
