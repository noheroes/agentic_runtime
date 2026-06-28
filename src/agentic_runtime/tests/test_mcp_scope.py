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
# exclusividad de scopes administrados (managed/enterprise)
# ---------------------------------------------------------------------------

def test_managed_present_suppresses_lower_scopes():
    scoped = {
        McpScope.USER: {"u": {"url": "https://u"}},
        McpScope.MANAGED: {"m": {"url": "https://m"}},
    }
    merged = merge_scoped(scoped)
    assert set(merged) == {"m"}
    assert merged["m"].scope is McpScope.MANAGED


def test_enterprise_present_suppresses_all_non_exclusive():
    scoped = {
        McpScope.USER: {"u": {"url": "https://u"}},
        McpScope.PROJECT: {"p": {"url": "https://p"}},
        McpScope.LOCAL: {"l": {"url": "https://l"}},
        McpScope.ENTERPRISE: {"e": {"url": "https://e"}},
    }
    merged = merge_scoped(scoped)
    assert set(merged) == {"e"}


def test_enterprise_wins_over_managed_when_both_present():
    scoped = {
        McpScope.MANAGED: {"s": {"url": "https://managed"}},
        McpScope.ENTERPRISE: {"s": {"url": "https://enterprise"}},
    }
    merged = merge_scoped(scoped)
    assert merged["s"].scope is McpScope.ENTERPRISE
    assert merged["s"].raw["url"] == "https://enterprise"


def test_empty_exclusive_scope_does_not_suppress():
    # Un scope exclusivo registrado pero VACÍO no debe suprimir a los demás.
    scoped = {
        McpScope.MANAGED: {},
        McpScope.USER: {"u": {"url": "https://u"}},
    }
    merged = merge_scoped(scoped)
    assert set(merged) == {"u"}


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


def test_exclusive_scopes_are_managed_and_enterprise():
    assert EXCLUSIVE_SCOPES == frozenset({McpScope.MANAGED, McpScope.ENTERPRISE})
