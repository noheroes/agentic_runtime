from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

CANONICAL_REFERENCE_WINDOW = 200_000
MAX_OUTPUT_TOKENS_FOR_SUMMARY = 20_000
AUTOCOMPACT_BUFFER_TOKENS = 13_000
WARNING_THRESHOLD_BUFFER_TOKENS = 20_000
ERROR_THRESHOLD_BUFFER_TOKENS = 20_000
MANUAL_COMPACT_BUFFER_TOKENS = 3_000
MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3

POST_COMPACT_MAX_FILES_TO_RESTORE = 5
POST_COMPACT_TOKEN_BUDGET = 50_000
POST_COMPACT_MAX_TOKENS_PER_FILE = 5_000
POST_COMPACT_MAX_TOKENS_PER_SKILL = 5_000
POST_COMPACT_SKILLS_TOKEN_BUDGET = 25_000

MIN_SUMMARY_CHARS_LOCAL = 600
RECOMPACTION_GROWTH_RATIO_LOCAL = 1.5


@dataclass(frozen=True)
class ContextBudget:
    policy: str
    context_window: int
    max_output_tokens: int
    reserved_for_summary: int
    effective_window: int
    autocompact_threshold: int
    warning_threshold: int
    error_threshold: int
    blocking_limit: int
    post_compact_max_files_to_restore: int
    post_compact_token_budget: int
    post_compact_max_tokens_per_file: int
    post_compact_max_tokens_per_skill: int
    post_compact_skills_token_budget: int
    min_summary_chars: int
    recompaction_growth_ratio: float


@dataclass(frozen=True)
class ContextPressure:
    context_tokens: int
    percent_left: int
    above_warning: bool
    above_error: bool
    above_autocompact: bool
    above_blocking: bool


class ContextWindowPolicy(Protocol):
    name: str

    def budget(self, context_window: int, max_output_tokens: int) -> ContextBudget: ...


def _unscaled(constant: int) -> int:
    return constant


def _assemble(
    policy: str,
    context_window: int,
    max_output_tokens: int,
    scaled: Callable[[int], int],
    min_summary_chars: int,
    recompaction_growth_ratio: float,
) -> ContextBudget:
    reserved = min(max_output_tokens, scaled(MAX_OUTPUT_TOKENS_FOR_SUMMARY))
    effective = context_window - reserved
    autocompact = effective - scaled(AUTOCOMPACT_BUFFER_TOKENS)
    return ContextBudget(
        policy=policy,
        context_window=context_window,
        max_output_tokens=max_output_tokens,
        reserved_for_summary=reserved,
        effective_window=effective,
        autocompact_threshold=autocompact,
        warning_threshold=autocompact - scaled(WARNING_THRESHOLD_BUFFER_TOKENS),
        error_threshold=autocompact - scaled(ERROR_THRESHOLD_BUFFER_TOKENS),
        blocking_limit=effective - scaled(MANUAL_COMPACT_BUFFER_TOKENS),
        post_compact_max_files_to_restore=scaled(POST_COMPACT_MAX_FILES_TO_RESTORE),
        post_compact_token_budget=scaled(POST_COMPACT_TOKEN_BUDGET),
        post_compact_max_tokens_per_file=scaled(POST_COMPACT_MAX_TOKENS_PER_FILE),
        post_compact_max_tokens_per_skill=scaled(POST_COMPACT_MAX_TOKENS_PER_SKILL),
        post_compact_skills_token_budget=scaled(POST_COMPACT_SKILLS_TOKEN_BUDGET),
        min_summary_chars=min_summary_chars,
        recompaction_growth_ratio=recompaction_growth_ratio,
    )


class CanonicalContextWindowPolicy:
    name = "canonical"

    def budget(self, context_window: int, max_output_tokens: int) -> ContextBudget:
        return _assemble(
            self.name,
            context_window,
            max_output_tokens,
            _unscaled,
            0,
            1.0,
        )


class LocalContextWindowPolicy:
    name = "local"

    def __init__(self, reference_window: int = CANONICAL_REFERENCE_WINDOW) -> None:
        self._reference = reference_window

    def scale_for(self, context_window: int) -> float:
        if self._reference <= 0:
            return 1.0
        return min(1.0, context_window / self._reference)

    def budget(self, context_window: int, max_output_tokens: int) -> ContextBudget:
        scale = self.scale_for(context_window)

        def scaled(constant: int) -> int:
            return max(1, int(constant * scale))

        return _assemble(
            self.name,
            context_window,
            max_output_tokens,
            scaled,
            MIN_SUMMARY_CHARS_LOCAL,
            RECOMPACTION_GROWTH_RATIO_LOCAL,
        )


_POLICIES: dict[str, type[ContextWindowPolicy]] = {
    CanonicalContextWindowPolicy.name: CanonicalContextWindowPolicy,
    LocalContextWindowPolicy.name: LocalContextWindowPolicy,
}

CONTEXT_WINDOW_POLICIES: tuple[str, ...] = tuple(sorted(_POLICIES))


def resolve_context_window_policy(name: str) -> ContextWindowPolicy:
    key = (name or "").strip().lower()
    policy = _POLICIES.get(key)
    if policy is None:
        raise ValueError(
            f"política de ventana de contexto desconocida: {name!r}; "
            "las disponibles son " + ", ".join(CONTEXT_WINDOW_POLICIES)
        )
    return policy()


def evaluate_context_pressure(context_tokens: int, budget: ContextBudget) -> ContextPressure:
    threshold = budget.autocompact_threshold
    if threshold > 0:
        ratio = (threshold - context_tokens) / threshold
        percent_left = math.floor(ratio * 100 + 0.5)
    else:
        percent_left = 0
    return ContextPressure(
        context_tokens=context_tokens,
        percent_left=percent_left,
        above_warning=context_tokens >= budget.warning_threshold,
        above_error=context_tokens >= budget.error_threshold,
        above_autocompact=context_tokens >= threshold,
        above_blocking=context_tokens >= budget.blocking_limit,
    )


__all__ = [
    "AUTOCOMPACT_BUFFER_TOKENS",
    "CANONICAL_REFERENCE_WINDOW",
    "CONTEXT_WINDOW_POLICIES",
    "ERROR_THRESHOLD_BUFFER_TOKENS",
    "MANUAL_COMPACT_BUFFER_TOKENS",
    "MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES",
    "MAX_OUTPUT_TOKENS_FOR_SUMMARY",
    "MIN_SUMMARY_CHARS_LOCAL",
    "POST_COMPACT_MAX_FILES_TO_RESTORE",
    "POST_COMPACT_MAX_TOKENS_PER_FILE",
    "POST_COMPACT_MAX_TOKENS_PER_SKILL",
    "POST_COMPACT_SKILLS_TOKEN_BUDGET",
    "POST_COMPACT_TOKEN_BUDGET",
    "RECOMPACTION_GROWTH_RATIO_LOCAL",
    "WARNING_THRESHOLD_BUFFER_TOKENS",
    "CanonicalContextWindowPolicy",
    "ContextBudget",
    "ContextPressure",
    "ContextWindowPolicy",
    "LocalContextWindowPolicy",
    "evaluate_context_pressure",
    "resolve_context_window_policy",
]
