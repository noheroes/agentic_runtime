"""
summarize_if_needed — condensa el resultado de un subagente background
cuando supera el umbral de caracteres, antes de inyectarlo al padre.

Comportamiento de degradación graceful:
- Sin llm disponible → texto pasa tal cual.
- llm falla → texto pasa tal cual (el resultado del subagente nunca se pierde).
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_SUMMARY_PROMPT = (
    "Summarize the following agent output concisely, preserving all key "
    "findings, decisions, file paths, and errors. "
    "Remove repetition and verbose explanations. "
    "Output only the summary, no preamble.\n\n"
    "{text}"
)


async def summarize_if_needed(
    text: str,
    max_chars: int,
    llm,
) -> str:
    if len(text) <= max_chars or llm is None:
        return text

    prompt = _SUMMARY_PROMPT.format(text=text)
    try:
        summary, _ = await llm.complete_simple(
            system="You are a concise summarizer. Preserve all key findings, decisions, file paths, and errors.",
            user_message=prompt,
            max_tokens=600,
        )
        if summary:
            logger.info(
                "background result summarized: %d → %d chars",
                len(text),
                len(summary),
            )
            return summary
    except Exception as exc:
        logger.warning("background result summarization failed: %s", exc)

    return text
