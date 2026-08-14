from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

ASK_USER_QUESTION_TOOL_NAME = "AskUserQuestion"

ASK_USER_QUESTION_TOOL_CHIP_WIDTH = 12

_ANSWERED_TEMPLATE = (
    "User has answered your questions: {answers}. "
    "You can now continue with the user's answers in mind."
)

_OPTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "label": {
            "type": "string",
            "description": (
                "The display text for this option that the user will see and select. Should be "
                "concise (1-5 words) and clearly describe the choice."
            ),
        },
        "description": {
            "type": "string",
            "description": (
                "Explanation of what this option means or what will happen if chosen. Useful for "
                "providing context about trade-offs or implications."
            ),
        },
        "preview": {
            "type": "string",
            "description": (
                "Optional preview content rendered when this option is focused. Use for mockups, "
                "code snippets, or visual comparisons that help users compare options. See the "
                "tool description for the expected content format."
            ),
        },
    },
    "required": ["label", "description"],
}

_QUESTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "question": {
            "type": "string",
            "description": (
                "The complete question to ask the user. Should be clear, specific, and end with a "
                'question mark. Example: "Which library should we use for date formatting?" If '
                'multiSelect is true, phrase it accordingly, e.g. "Which features do you want to '
                'enable?"'
            ),
        },
        "header": {
            "type": "string",
            "description": (
                f"Very short label displayed as a chip/tag (max {ASK_USER_QUESTION_TOOL_CHIP_WIDTH} "
                'chars). Examples: "Auth method", "Library", "Approach".'
            ),
        },
        "options": {
            "type": "array",
            "items": _OPTION_SCHEMA,
            "minItems": 2,
            "maxItems": 4,
            "description": (
                "The available choices for this question. Must have 2-4 options. Each option should "
                "be a distinct, mutually exclusive choice (unless multiSelect is enabled). There "
                "should be no 'Other' option, that will be provided automatically."
            ),
        },
        "multiSelect": {
            "type": "boolean",
            "default": False,
            "description": (
                "Set to true to allow the user to select multiple options instead of just one. Use "
                "when choices are not mutually exclusive."
            ),
        },
    },
    "required": ["question", "header", "options", "multiSelect"],
}

_ANNOTATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "preview": {
            "type": "string",
            "description": "The preview content of the selected option, if the question used previews.",
        },
        "notes": {
            "type": "string",
            "description": "Free-text notes the user added to their selection.",
        },
    },
}


def render_answers(
    answers: dict[str, Any],
    annotations: dict[str, Any] | None = None,
) -> str:
    rendered: list[str] = []
    for question, answer in answers.items():
        annotation = (annotations or {}).get(question)
        parts = [f'"{question}"="{answer}"']
        if isinstance(annotation, dict):
            preview = annotation.get("preview")
            if preview:
                parts.append(f"selected preview:\n{preview}")
            notes = annotation.get("notes")
            if notes:
                parts.append(f"user notes: {notes}")
        rendered.append(" ".join(parts))
    return ", ".join(rendered)


class AskUserQuestionTool:
    name = ASK_USER_QUESTION_TOOL_NAME
    deferred = True
    search_hint = "prompt the user with a multiple-choice question"
    description = (
        "Use this tool when you need to ask the user questions during execution. This allows you to:\n"
        "1. Gather user preferences or requirements\n"
        "2. Clarify ambiguous instructions\n"
        "3. Get decisions on implementation choices as you work\n"
        "4. Offer choices to the user about what direction to take.\n"
        "\n"
        "Usage notes:\n"
        '- Users will always be able to select "Other" to provide custom text input\n'
        "- Use multiSelect: true to allow multiple answers to be selected for a question\n"
        "- If you recommend a specific option, make that the first option in the list and add "
        '"(Recommended)" at the end of the label\n'
        "\n"
        "Plan mode note: In plan mode, use this tool to clarify requirements or choose between "
        "approaches BEFORE finalizing your plan. Do NOT use this tool to ask \"Is my plan ready?\" or "
        "\"Should I proceed?\" - use ExitPlanMode for plan approval. IMPORTANT: Do not reference "
        '"the plan" in your questions (e.g., "Do you have feedback about the plan?", "Does the plan '
        'look good?") because the user cannot see the plan in the UI until you call ExitPlanMode. If '
        "you need plan approval, use ExitPlanMode instead.\n"
    )
    input_schema: dict[str, Any] = {  # noqa: RUF012
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": _QUESTION_SCHEMA,
                "minItems": 1,
                "maxItems": 4,
                "description": "Questions to ask the user (1-4 questions)",
            },
            "annotations": {
                "type": "object",
                "additionalProperties": _ANNOTATION_SCHEMA,
                "description": (
                    "Optional per-question annotations from the user (e.g., notes on preview "
                    "selections). Keyed by question text."
                ),
            },
            "answers": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "description": "User answers collected by the permission component",
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": (
                            'Optional identifier for the source of this question (e.g., "remember" '
                            "for /remember command). Used for analytics tracking."
                        ),
                    },
                },
                "description": "Optional metadata for tracking and analytics purposes. Not displayed to user.",
            },
        },
        "required": ["questions"],
    }
    category = ToolCategory.SYSTEM
    requires_permission = False
    requires_user_interaction = True
    safe_for_background = False
    timeout_seconds = 300.0

    def __init__(self, *, interactive: bool = False) -> None:
        self._interactive = interactive

    def is_enabled(self) -> bool:
        return self._interactive

    async def execute(self, input: dict[str, Any], ctx: ToolUseContext) -> ToolResult:
        answers = input.get("answers")
        annotations = input.get("annotations")
        return ToolResult(
            tool_name=self.name,
            output=_ANSWERED_TEMPLATE.format(
                answers=render_answers(
                    answers if isinstance(answers, dict) else {},
                    annotations if isinstance(annotations, dict) else {},
                )
            ),
        )
