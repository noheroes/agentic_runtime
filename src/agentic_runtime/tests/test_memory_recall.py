"""Ranking de recall determinista (keyword + recencia)."""
from agentic_runtime.capabilities.memory import MemoryHeader, rank_memories


def _h(name: str, description: str, mtime: float = 0.0) -> MemoryHeader:
    return MemoryHeader(name=name, description=description, path=f"/m/{name}.md", mtime=mtime)


def test_overlap_selects_relevant_and_excludes_irrelevant():
    headers = [
        _h("auth-flow", "cómo funciona el login y los tokens de sesión"),
        _h("postres", "recetas de tarta de manzana"),
    ]
    ranked = rank_memories(headers, "necesito arreglar el login de sesión")
    assert [h.name for h in ranked] == ["auth-flow"]


def test_no_overlap_returns_empty():
    headers = [_h("postres", "recetas de tarta")]
    assert rank_memories(headers, "kubernetes despliegue") == []


def test_empty_query_returns_empty():
    headers = [_h("x", "login sesión token")]
    assert rank_memories(headers, "") == []


def test_recency_breaks_ties_deterministically():
    headers = [
        _h("viejo", "despliegue kubernetes", mtime=100.0),
        _h("nuevo", "despliegue kubernetes", mtime=200.0),
    ]
    ranked = rank_memories(headers, "despliegue kubernetes")
    # Mismo overlap → gana el más reciente (mtime mayor) primero, determinista.
    assert [h.name for h in ranked] == ["nuevo", "viejo"]


def test_limit_caps_results():
    headers = [_h(f"m{i}", "login token sesión", mtime=float(i)) for i in range(10)]
    ranked = rank_memories(headers, "login token sesión", limit=3)
    assert len(ranked) == 3
    # Determinismo: idéntica entrada → idéntico orden en dos llamadas.
    assert [h.name for h in ranked] == [h.name for h in rank_memories(headers, "login token sesión", limit=3)]
