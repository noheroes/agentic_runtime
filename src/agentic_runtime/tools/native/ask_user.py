from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

ASK_USER_QUESTION_TOOL_NAME = "AskUserQuestion"

_OPTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "label": {"type": "string"},
        "description": {"type": "string"},
    },
    "required": ["label"],
}


class AskUserQuestionTool:
    name = ASK_USER_QUESTION_TOOL_NAME
    description = (
        "Ask the user a question with structured options and wait for their response. "
        "Use when a decision requires explicit user input before proceeding."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question to ask the user.",
            },
            "options": {
                "type": "array",
                "items": _OPTION_SCHEMA,
                "minItems": 2,
                "maxItems": 4,
                "description": "2–4 mutually exclusive options for the user to choose from.",
            },
            "header": {
                "type": "string",
                "description": "Short label (max 12 chars) displayed as a chip.",
            },
        },
        "required": ["question", "options", "header"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = False
    timeout_seconds = 300.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        question = input.get("question", "")
        options = input.get("options", [])
        header = input.get("header", "")

        # Build the prompt shown to the user
        lines = [f"[{header}] {question}", ""]
        for i, opt in enumerate(options, 1):
            label = opt.get("label", "")
            desc = opt.get("description", "")
            lines.append(f"  {i}. {label}" + (f" — {desc}" if desc else ""))
        lines.append("")
        lines.append("Enter the number of your choice:")
        prompt_text = "\n".join(lines)

        # Delegate to app_state user_input processor if available,
        # otherwise fall back to stdin (headless/test contexts).
        user_input_fn = ctx.app_state.native.get("user_input_fn")
        if callable(user_input_fn):
            answer = await user_input_fn(prompt_text, options)
        else:
            loop = asyncio.get_event_loop()
            answer = await loop.run_in_executor(None, lambda: input_prompt(prompt_text))

        return ToolResult(tool_name=self.name, output=str(answer))


def input_prompt(prompt: str) -> str:
    print(prompt, flush=True)
    return input()
