"""Tests del modelo de scope/procedencia de servers MCP — homologado al canónico.

Canónico (`claude-code/src/services/mcp`): enum `ConfigScope`
(local/user/project/dynamic/enterprise/claudeai/managed), precedencia por nombre
enterprise > local > project > user (`config.ts:1046-1057`), exclusividad enterprise
(`config.ts:1084`) y gate de mutabilidad que prohíbe add a dynamic/enterprise/claudeai
(`config.ts:705-709`). Aquí se verifica el modelo PURO, sin I/O.
"""
import pytest

from agentic_runtime.capabilities.mcp.scope import (
    EXCLUSIVE_SCOPES,
    MUTABLE_SCOPES,
    McpScope,
    ScopedConfig,
    assert_mutable,
    is_mutable,
    merge_scoped,
)


# ---------------------------------------------------------------------------
# enum canónico
# ---------------------------------------------------------------------------

def test_scope_enum_has_canonical_values():
    assert {s.value for s in McpScope} == {
        "enterprise", "managed", "local", "project", "user", "dynamic", "claudeai",
    }


# ---------------------------------------------------------------------------
# precedencia por nombre (scope mayor gana en el merge)
# ---------------------------------------------------------------------------

def test_precedence_local_over_project_over_user_over_dynamic():
    scoped = {
        McpScope.DYNAMIC: {"s": {"url": "https://dynamic", "_tag": "dyn"}},
        McpScope.USER: {"s": {"url": "https://user", "_tag": "user"}},
        McpScope.PROJECT: {"s": {"url": "https://project", "_tag": "proj"}},
        McpScope.LOCAL: {"s": {"url": "https://local", "_tag": "local"}},
    }
    merged = merge_scoped(scoped)
    assert merged["s"].scope is McpScope.LOCAL
    assert merged["s"].raw["_tag"] == "local"


def test_merge_preserves_unique_names_from_lower_scopes():
    scoped = {
        McpScope.USER: {"a": {"url": "https://a"}},
        McpScope.LOCAL: {"b": {"url": "https://b"}},
    }
    merged = merge_scoped(scoped)
    assert set(merged) == {"a", "b"}
    assert merged["a"].scope is McpScope.USER
    assert merged["b"].scope is McpScope.LOCAL


def test_merge_returns_typed_scoped_config():
    merged = merge_scoped({McpScope.USER: {"a": {"url": "https://a"}}})
    assert isinstance(merged["a"], ScopedConfig)
    assert merged["a"].scope is McpScope.USER
    assert merged["a"].raw == {"url": "https://a"}


# ---------------------------------------------------------------------------
# managed = baseline coexistente (capa plugin-like del canónico), NO exclusivo
# ---------------------------------------------------------------------------

def test_managed_coexists_with_user():
    # managed es el baseline de plataforma: convive con los servers del usuario,
    # no los suprime (a diferencia de enterprise). Espejo de los plugins del canónico.
    scoped = {
        McpScope.USER: {"u": {"url": "https://u"}},
        McpScope.MANAGED: {"m": {"url": "https://m"}},
    }
    merged = merge_scoped(scoped)
    assert set(merged) == {"m", "u"}
    assert merged["m"].scope is McpScope.MANAGED
    assert merged["u"].scope is McpScope.USER


def test_managed_wins_over_user_on_name_collision():
    # Coexisten por nombre; en colisión, managed (mayor precedencia) gana.
    scoped = {
        McpScope.USER: {"s": {"url": "https://user", "_tag": "user"}},
        McpScope.MANAGED: {"s": {"url": "https://managed", "_tag": "managed"}},
    }
    merged = merge_scoped(scoped)
    assert merged["s"].scope is McpScope.MANAGED
    assert merged["s"].raw["_tag"] == "managed"


# ---------------------------------------------------------------------------
# enterprise = lockdown corporativo: ÚNICO scope exclusivo (suprime el resto)
# ---------------------------------------------------------------------------

def test_enterprise_present_suppresses_all_non_exclusive():
    scoped = {
        McpScope.USER: {"u": {"url": "https://u"}},
        McpScope.PROJECT: {"p": {"url": "https://p"}},
        McpScope.LOCAL: {"l": {"url": "https://l"}},
        McpScope.MANAGED: {"m": {"url": "https://m"}},
        McpScope.ENTERPRISE: {"e": {"url": "https://e"}},
    }
    merged = merge_scoped(scoped)
    # enterprise suprime TODO lo demás, incluido managed.
    assert set(merged) == {"e"}


def test_empty_enterprise_scope_does_not_suppress():
    # El único scope exclusivo, registrado pero VACÍO, no suprime a los demás.
    scoped = {
        McpScope.ENTERPRISE: {},
        McpScope.MANAGED: {"m": {"url": "https://m"}},
        McpScope.USER: {"u": {"url": "https://u"}},
    }
    merged = merge_scoped(scoped)
    assert set(merged) == {"m", "u"}


# ---------------------------------------------------------------------------
# gate de mutabilidad
# ---------------------------------------------------------------------------

def test_mutable_scopes_are_user_project_local():
    assert MUTABLE_SCOPES == frozenset(
        {McpScope.USER, McpScope.PROJECT, McpScope.LOCAL}
    )
    for scope in MUTABLE_SCOPES:
        assert is_mutable(scope)


def test_managed_enterprise_claudeai_dynamic_not_mutable():
    for scope in (
        McpScope.MANAGED, McpScope.ENTERPRISE, McpScope.CLAUDEAI, McpScope.DYNAMIC,
    ):
        assert not is_mutable(scope)
        with pytest.raises(ValueError):
            assert_mutable(scope)


def test_exclusive_scopes_are_enterprise_only():
    # Solo enterprise es exclusivo (lockdown corporativo). managed es read-only
    # PERO coexistente (baseline plataforma), por eso NO está aquí.
    assert EXCLUSIVE_SCOPES == frozenset({McpScope.ENTERPRISE})
