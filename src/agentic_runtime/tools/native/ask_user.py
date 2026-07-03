from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

ASK_USER_QUESTION_TOOL_NAME = "AskUserQuestion"

_OPTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "label": {
            "type": "string",
            "description": "The display text for this option (concise, 1-5 words).",
        },
        "description": {
            "type": "string",
            "description": "What this option means or what happens if chosen (trade-offs/implications).",
        },
    },
    "required": ["label"],
}

_QUESTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "question": {
            "type": "string",
            "description": "The complete question to ask the user. Clear, specific, ends with '?'.",
        },
        "header": {
            "type": "string",
            "description": "Very short label (max 12 chars) displayed as a chip. E.g. 'Objective'.",
        },
        "options": {
            "type": "array",
            "items": _OPTION_SCHEMA,
            "minItems": 2,
            "maxItems": 4,
            "description": (
                "2-4 distinct, mutually exclusive options (unless multiSelect). Do NOT add an 'Other' "
                "option: free-form input is always offered to the user automatically."
            ),
        },
        "multiSelect": {
            "type": "boolean",
            "description": "Allow selecting multiple options. Use when choices are not mutually exclusive.",
        },
    },
    "required": ["question", "header", "options"],
}


class AskUserQuestionTool:
    name = ASK_USER_QUESTION_TOOL_NAME
    description = (
        "Ask the user one or more multiple-choice questions to gather information, clarify ambiguity, "
        "understand preferences, or get decisions on direction. Presents a QUESTIONNAIRE of 1-4 "
        "questions that the user answers together in one interaction, each with 2-4 options; the user "
        "can always give a free-form answer ('Other') instead, so open-ended details (a number, a name) "
        "are fine. Prefer this over asking in free-form prose whenever you need input to proceed. GROUP "
        "related questions into a SINGLE call (up to 4) so the user can answer everything at once, "
        "rather than asking one at a time. If you recommend an option, list it first and append "
        "\"(Recommended)\" to its label."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": _QUESTION_SCHEMA,
                "minItems": 1,
                "maxItems": 4,
                "description": "The questions to ask the user (1-4). Group related ones into one call.",
            },
        },
        "required": ["questions"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = False
    safe_for_background = False
    timeout_seconds = 300.0

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        """HITL multi-turno: NO bloquea. Emite las preguntas (el consumidor las detecta por este
        `tool_call` en el stream) y CIERRA el turno vía `ends_turn`; el usuario responde y el
        resultado REAL ('User has answered your questions: …') lo reinyecta el consumidor como el
        tool_result de esta llamada al inicio del turno siguiente. Aquí solo dejamos un placeholder.
        """
        result = ToolResult(
            tool_name=self.name,
            output="Awaiting the user's answers to the questions above.",
        )
        result.ends_turn = True  # type: ignore[attr-defined]
        return result
