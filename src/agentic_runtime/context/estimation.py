from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

DEFAULT_BYTES_PER_TOKEN = 4
DENSE_BYTES_PER_TOKEN = 2
MEDIA_BLOCK_TOKENS = 2000
DENSE_FILE_EXTENSIONS = frozenset({"json", "jsonl", "jsonc"})
TRANSPORTED_ROLES = frozenset({"user", "assistant", "tool"})


def _stringify(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def rough_token_count(content: str, bytes_per_token: int = DEFAULT_BYTES_PER_TOKEN) -> int:
    if bytes_per_token <= 0:
        return 0
    return math.floor(len(content) / bytes_per_token + 0.5)


def bytes_per_token_for_file_type(file_extension: str) -> int:
    if file_extension.lstrip(".").lower() in DENSE_FILE_EXTENSIONS:
        return DENSE_BYTES_PER_TOKEN
    return DEFAULT_BYTES_PER_TOKEN


def rough_token_count_for_file_type(content: str, file_extension: str) -> int:
    return rough_token_count(content, bytes_per_token_for_file_type(file_extension))


def rough_token_count_for_block(block: Any) -> int:
    if isinstance(block, str):
        return rough_token_count(block)
    if not isinstance(block, dict):
        return rough_token_count(_stringify(block))

    kind = block.get("type")
    if kind == "text":
        return rough_token_count(str(block.get("text") or ""))
    if kind in ("image", "document"):
        return MEDIA_BLOCK_TOKENS
    if kind == "tool_result":
        return rough_token_count_for_content(block.get("content"))
    if kind == "tool_use":
        return rough_token_count(
            str(block.get("name") or "") + _stringify(block.get("input") or {})
        )
    if kind == "thinking":
        return rough_token_count(str(block.get("thinking") or ""))
    if kind == "redacted_thinking":
        return rough_token_count(str(block.get("data") or ""))
    return rough_token_count(_stringify(block))


def rough_token_count_for_content(content: Any) -> int:
    if not content:
        return 0
    if isinstance(content, str):
        return rough_token_count(content)
    if not isinstance(content, (list, tuple)):
        return rough_token_count(_stringify(content))
    return sum(rough_token_count_for_block(block) for block in content)


def rough_token_count_for_message(message: Any) -> int:
    if not isinstance(message, dict):
        return 0
    if message.get("role") not in TRANSPORTED_ROLES:
        return 0
    return rough_token_count_for_content(message.get("content"))


def rough_token_count_for_messages(messages: Any) -> int:
    if not messages:
        return 0
    return sum(rough_token_count_for_message(message) for message in messages)


@dataclass(frozen=True)
class UsageAnchor:
    context_tokens: int
    message_count: int


def token_count_with_estimation(
    messages: list[dict[str, Any]],
    anchor: UsageAnchor | None = None,
) -> int:
    if anchor is None or anchor.message_count > len(messages):
        return rough_token_count_for_messages(messages)
    return anchor.context_tokens + rough_token_count_for_messages(
        messages[anchor.message_count :]
    )


def truncate_to_tokens(content: str, max_tokens: int, marker: str) -> str:
    if rough_token_count(content) <= max_tokens:
        return content
    char_budget = max_tokens * DEFAULT_BYTES_PER_TOKEN - len(marker)
    if char_budget <= 0:
        return marker
    return content[:char_budget] + marker


__all__ = [
    "DEFAULT_BYTES_PER_TOKEN",
    "DENSE_BYTES_PER_TOKEN",
    "MEDIA_BLOCK_TOKENS",
    "TRANSPORTED_ROLES",
    "UsageAnchor",
    "bytes_per_token_for_file_type",
    "rough_token_count",
    "rough_token_count_for_block",
    "rough_token_count_for_content",
    "rough_token_count_for_file_type",
    "rough_token_count_for_message",
    "rough_token_count_for_messages",
    "token_count_with_estimation",
    "truncate_to_tokens",
]
