from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..protocol import ToolCategory, ToolResult

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

ASK_USER_QUESTION_TOOL_NAME = "AskUserQuestion"

#: Ancho del chip, literal de A (`prompt.ts:5`): entra en la descripción de `header`.
ASK_USER_QUESTION_TOOL_CHIP_WIDTH = 12

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
    # A los tiene los dos requeridos (`z.object({label, description})`, sólo `preview`
    # es `.optional()`): B pedía únicamente `label` — divergencia, no mejora (`L10`).
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

#: `annotations` de A (`AskUserQuestionTool.tsx:26-30`): lo rellena la capa de
#: interacción al devolver las respuestas, no el modelo.
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


class AskUserQuestionTool:
    name = ASK_USER_QUESTION_TOOL_NAME
    # Mímica de lo que A manda REALMENTE al modelo: `api.ts:171` serializa
    # `description: await tool.prompt(…)`, o sea `ASK_USER_QUESTION_TOOL_PROMPT`
    # (`AskUserQuestionTool/prompt.ts:31-44`), no el `DESCRIPTION` corto —ése es el
    # `searchHint`/UI—. La sección de preview se omite porque A también la omite
    # cuando el consumidor no ha optado por un formato (`getQuestionPreviewFormat()
    # === undefined`, rama «SDK consumer»), que es exactamente el caso de B.
    #
    # ⚠ La versión anterior de B decía «Prefer this over asking in free-form prose…»
    # y «GROUP related questions into a SINGLE call»: **texto que A no tiene**
    # (`FIND-E11-4`). Empujaba más que el canónico, así que medía a un sujeto que no
    # es A. Retirado por `L10` — una divergencia no es una mejora hasta demostrarlo.
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
    input_schema = {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": _QUESTION_SCHEMA,
                "minItems": 1,
                "maxItems": 4,
                "description": "Questions to ask the user (1-4 questions)",
            },
            # Los tres de A que NO rellena el modelo sino la capa de interacción al
            # devolver las respuestas (`AskUserQuestionTool.tsx:26-62`). Van en el
            # schema porque en A van: quitarlos sería recortar el sujeto.
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
    safe_for_background = False
    timeout_seconds = 300.0

    # `FIND-TOOL-ENABLED-1` — tool de PUERTA ÚNICA: su `execute` cierra el turno
    # (`ends_turn=True`, abajo) a la espera de una respuesta humana. En un host sin
    # humano eso no es «esperar»: es un turno vacío garantizado, y el trabajo se
    # pierde. Medido en el E2g (`GATE_E2G_SEED=1780649320`, `archivos/nativa`):
    # `elegidas=['AskUserQuestion','glob']`, `respuesta=''`, centinela no emitido.
    #
    # Homólogo del criterio de A, que apaga la ENTRADA cuando la SALIDA no existe
    # (`EnterPlanModeTool.ts:56-67`, sobre `--channels`: *«its approval dialog needs
    # the terminal»*). Default `False` porque el runtime es headless salvo que el
    # integrador declare lo contrario — mismo criterio ya establecido para los
    # handlers OAuth de MCP (`CapabilitiesConfig`: «el runtime headless no abre
    # navegador»). El cable es `ToolsConfig.interactive`.
    def __init__(self, *, interactive: bool = False) -> None:
        self._interactive = interactive

    def is_enabled(self) -> bool:
        return self._interactive

    async def execute(self, input: dict, ctx: "ToolUseContext") -> ToolResult:
        """HITL multi-turno: NO bloquea. Emite las preguntas (el consumidor las detecta por este
        `tool_call` en el stream) y CIERRA el turno vía `ends_turn`; el usuario responde y el
        resultado REAL ('User has answered your questions: …') lo reinyecta el consumidor como el
        tool_result de esta llamada al inicio del turno siguiente. Aquí solo dejamos un placeholder.

        ⚠ **Divergencia declarada con A.** El canónico NO cierra el turno: su `call()` sólo
        devuelve `{data:{questions,answers,annotations}}` (leído 1→EOF en
        `AskUserQuestionTool.tsx:209-220`) y las respuestas llegan **dentro del mismo turno**
        por `checkPermissions → behavior:'ask' + updatedInput`, capa de interacción que en B
        es `GAP-02`/`K1` y está por encima de la línea de corte. `ends_turn` es el cable de B
        mientras eso no exista, no un espejo. Ver `ToolResult.ends_turn`.
        """
        return ToolResult(
            tool_name=self.name,
            output="Awaiting the user's answers to the questions above.",
            ends_turn=True,
        )
