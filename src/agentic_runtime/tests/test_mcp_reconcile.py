"""Tests del motor de reconciliación MCP (diff deseado-vs-vivo → connect/disconnect/refresh).

Motor genérico que consumen tanto la mutación in-process (vector 1) como el watcher
de fuente externa (vector 2). El plan es DATOS puros (sin efectos); el applier los
ejecuta sobre el provider. Comparación de config por igualdad explícita (Regla 1: sin
heurísticas).
"""
from agentic_runtime.capabilities.mcp.config import parse_server_config
from agentic_runtime.capabilities.mcp.reconcile import (
    ReconcilePlan,
    apply_reconcile,
    plan_reconcile,
)


def _cfg(name: str, url: str = "https://x", **extra):
    return parse_server_config(name, {"url": url, **extra})


# ---------------------------------------------------------------------------
# plan_reconcile — diff puro
# ---------------------------------------------------------------------------

def test_connects_new_servers():
    plan = plan_reconcile(desired={"a": _cfg("a")}, live={})
    assert plan.to_connect == ("a",)
    assert plan.to_disconnect == () and plan.to_refresh == ()


def test_disconnects_removed_servers():
    plan = plan_reconcile(desired={}, live={"a": _cfg("a")})
    assert plan.to_disconnect == ("a",)
    assert plan.to_connect == () and plan.to_refresh == ()


def test_disconnects_disabled_servers():
    plan = plan_reconcile(
        desired={"a": _cfg("a", enabled=False)}, live={"a": _cfg("a")}
    )
    assert plan.to_disconnect == ("a",)
    assert plan.to_connect == () and plan.to_refresh == ()


def test_disabled_not_in_live_is_noop():
    plan = plan_reconcile(desired={"a": _cfg("a", enabled=False)}, live={})
    assert plan.is_empty


def test_refreshes_changed_config():
    plan = plan_reconcile(
        desired={"a": _cfg("a", url="https://new")},
        live={"a": _cfg("a", url="https://old")},
    )
    assert plan.to_refresh == ("a",)
    assert plan.to_connect == () and plan.to_disconnect == ()


def test_noop_when_in_sync():
    same = {"a": _cfg("a")}
    plan = plan_reconcile(desired=same, live={"a": _cfg("a")})
    assert plan.is_empty


def test_plan_is_data_only_and_deterministic():
    plan = plan_reconcile(
        desired={"b": _cfg("b"), "a": _cfg("a")}, live={}
    )
    assert plan.to_connect == ("a", "b")  # orden determinista
    assert isinstance(plan, ReconcilePlan)


# ---------------------------------------------------------------------------
# apply_reconcile — ejecuta el plan sobre el provider
# ---------------------------------------------------------------------------

class _FakeProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def connect_server(self, name: str) -> bool:
        self.calls.append(("connect", name))
        return True

    async def disconnect_server(self, name: str) -> None:
        self.calls.append(("disconnect", name))

    async def reconnect_server(self, name: str) -> bool:
        self.calls.append(("reconnect", name))
        return True


async def test_apply_invokes_provider_actions():
    provider = _FakeProvider()
    plan = ReconcilePlan(
        to_connect=("c",), to_disconnect=("d",), to_refresh=("r",)
    )
    await apply_reconcile(plan, provider)
    assert ("disconnect", "d") in provider.calls
    assert ("connect", "c") in provider.calls
    assert ("reconnect", "r") in provider.calls


async def test_apply_disconnects_before_connecting():
    provider = _FakeProvider()
    plan = ReconcilePlan(to_connect=("c",), to_disconnect=("d",), to_refresh=())
    await apply_reconcile(plan, provider)
    assert provider.calls.index(("disconnect", "d")) < provider.calls.index(
        ("connect", "c")
    )


async def test_apply_empty_plan_is_noop():
    provider = _FakeProvider()
    await apply_reconcile(ReconcilePlan((), (), ()), provider)
    assert provider.calls == []
