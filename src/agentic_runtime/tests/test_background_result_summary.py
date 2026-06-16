"""Eje D — Summarización del resultado de subagentes background.

Cuando final_text supera un umbral de caracteres, se resume vía small_llm
antes de inyectar <task-notification> al padre. Esto evita saturar el
contexto del padre con outputs largos de researcher/reviewer.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(autouse=True)
def _roots(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_ROOT_PATH", str(tmp_path / "root"))
    monkeypatch.setenv("AGENT_TMP_ROOT_PATH", str(tmp_path / "tmp"))


# ── helper ────────────────────────────────────────────────────────────────────

def test_summarize_result_returns_short_text_unchanged():
    """Textos por debajo del umbral se devuelven tal cual."""
    from agentic_runtime.execution.local.summarizer import summarize_if_needed
    short = "x" * 100
    result = asyncio.run(summarize_if_needed(short, max_chars=2000, llm=None))
    assert result == short


def test_summarize_result_calls_llm_when_over_threshold():
    """Textos sobre el umbral se resumen usando el llm proporcionado."""
    from agentic_runtime.execution.local.summarizer import summarize_if_needed

    fake_llm = MagicMock()
    fake_llm.complete_simple = AsyncMock(return_value=("SUMMARY", None))

    long_text = "x" * 3000
    result = asyncio.run(
        summarize_if_needed(long_text, max_chars=2000, llm=fake_llm)
    )
    assert result == "SUMMARY"
    fake_llm.complete_simple.assert_called_once()


def test_summarize_result_passthrough_when_llm_is_none_even_over_threshold():
    """Sin llm disponible, el texto largo pasa tal cual (graceful degradation)."""
    from agentic_runtime.execution.local.summarizer import summarize_if_needed
    long_text = "x" * 3000
    result = asyncio.run(summarize_if_needed(long_text, max_chars=2000, llm=None))
    assert result == long_text


def test_summarize_result_passthrough_on_llm_error():
    """Si el llm falla, se devuelve el original (no se pierde el resultado)."""
    from agentic_runtime.execution.local.summarizer import summarize_if_needed

    fake_llm = MagicMock()
    fake_llm.complete_simple = AsyncMock(side_effect=RuntimeError("llm error"))

    long_text = "x" * 3000
    result = asyncio.run(summarize_if_needed(long_text, max_chars=2000, llm=fake_llm))
    assert result == long_text


# ── LocalAgentRuntime ─────────────────────────────────────────────────────────

def test_local_runtime_accepts_small_llm():
    """LocalAgentRuntime acepta small_llm opcional en su constructor."""
    from agentic_runtime.execution.local.runtime import LocalAgentRuntime
    rt = LocalAgentRuntime(small_llm=MagicMock())
    assert rt._small_llm is not None


def test_local_runtime_small_llm_defaults_to_none():
    from agentic_runtime.execution.local.runtime import LocalAgentRuntime
    rt = LocalAgentRuntime()
    assert rt._small_llm is None


def test_config_has_background_result_max_chars():
    """RuntimeConfig expone background_result_max_chars con default válido."""
    from agentic_runtime.factory import RuntimeConfig
    cfg = RuntimeConfig()
    assert isinstance(cfg.background_result_max_chars, int)
    assert cfg.background_result_max_chars > 0
