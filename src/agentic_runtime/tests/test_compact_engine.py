"""Homologación K6·tramos 2 y 5 — prompts, guardas, cortacircuitos, frontera y reintento por PTL.

Contrapartes canónicas leídas ÍNTEGRAS:
- `services/compact/prompt.ts` (375) — `DETAILED_ANALYSIS_INSTRUCTION_BASE` (31-44)
  y `_PARTIAL` (46-59), `BASE_COMPACT_PROMPT` (61-143), `PARTIAL_COMPACT_PROMPT`
  (145-204), `PARTIAL_COMPACT_UP_TO_PROMPT` (208-267), `getPartialCompactPrompt`
  (274-291), `getCompactPrompt` (293-303), `formatCompactSummary` (311-335),
  `getCompactUserSummaryMessage` (337-374).
- `services/compact/compact.ts` (1706) — `stripImagesFromMessages` (145-200),
  constantes de error (225-226, 293-297), `CompactionResult` (299-310),
  `buildPostCompactMessages` (330-338), `mergeHookInstructions` (374-381),
  `compactConversation` (387-763) con la guarda de historia vacía (397-399), las
  del resumen (493-515) y la frontera (598-624), `createCompactCanUseTool`
  (1125-1134) y `streamCompactSummary` (1136-1396): systemPrompt propio (1302-1304),
  `thinkingConfig: {type:'disabled'}` (1305) y `getMessagesAfterCompactBoundary`
  como conjunto enviado (1296-1298).
- `services/compact/autoCompact.ts` (352) — `AutoCompactTrackingState` (51-60),
  `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES` (70), `shouldAutoCompact` (160-239),
  `autoCompactIfNeeded` (241-351) con el cortacircuitos (260-265), el reseteo al
  éxito (331-332) y el incremento al fallo (341-349).
- `services/compact/compact.ts` (1705), tramo 5 — `MAX_PTL_RETRIES` y `PTL_RETRY_MARKER`
  (227-228), `truncateHeadForPTLRetry` (243-291) y el lazo de reintento de
  `compactConversation` (445-491), gemelo del de `partialCompactConversation`
  (854-899).
- `services/compact/grouping.ts` (63) — `groupMessagesByApiRound` (24-50).
- `services/api/errors.ts` (1207) — `PROMPT_TOO_LONG_ERROR_MESSAGE` (62),
  `isPromptTooLongMessage` (64-77), `parsePromptTooLongTokenCounts` (85-96),
  `getPromptTooLongTokenGap` (104-118) y `getAssistantMessageFromError` (562-574),
  que es quien puebla el `errorDetails` del que sale el gap.
- `utils/messages.ts` (5513) — `createCompactBoundaryMessage` (4530-4555),
  `isCompactBoundaryMessage` (4608-4612), `findLastCompactBoundaryIndex`
  (4618-4629), `getMessagesAfterCompactBoundary` (4643-4656).

Divergencias DECLARADAS (`D-21`: lo inexpresable se rechaza y se dice, no se
descarta en silencio):
- `NO_TOOLS_PREAMBLE` (19-26) y `NO_TOOLS_TRAILER` (269-272) no se portan: B no
  manda tools en la llamada de compactación, y el texto antitool nombra tools de A
  (`Read, Bash, Grep…`) contra el dogma del prompt agnóstico.
- `ERROR_MESSAGE_PROMPT_TOO_LONG` pierde el `Press esc twice…` de A (293-294): es
  interacción de la TUI de A y el núcleo no la dicta.
- El apagado de razonamiento se pide siempre; si el puente no sabe expresarlo, se
  reintenta UNA vez sin él y el repliegue viaja en el `CompactionEvent`.
- La agrupación por vuelta no compara `message.id`: B añade un asistente por vuelta
  y esa puerta de A no tiene referente aquí.
- El PTL se clasifica también desde el `ErrorEvent` del puente, que es por donde
  llega en B; A sólo tiene el mensaje sintético con `errorDetails`.
- `compact_conversation` NO emite el evento de fallo que A registra en
  `tengu_compact_failed` (compact.ts:470-476): en B ese evento lo rinde
  `auto_compact_if_needed` desde su captura, y emitirlo en los dos sitios daría dos
  fallos por una sola compactación. Los intentos quemados viajan en la excepción.
"""
from __future__ import annotations

from typing import Any

import pytest

from agentic_runtime.context.compact import (
    COMPACT_BOUNDARY_KEY,
    COMPACT_SUMMARY_KEY,
    COMPACT_SYSTEM_PROMPT,
    MAX_PTL_RETRIES,
    PROMPT_TOO_LONG_ERROR_MESSAGE,
    PTL_RETRY_MARKER,
    ApiErrorSummaryError,
    AutoCompactTracking,
    IncompleteResponseError,
    NotEnoughMessagesError,
    PromptTooLongError,
    SummaryTooShortError,
    auto_compact_if_needed,
    build_post_compact_messages,
    compact_conversation,
    create_compact_boundary_message,
    find_last_compact_boundary_index,
    format_compact_summary,
    get_compact_prompt,
    get_compact_user_summary_message,
    get_partial_compact_prompt,
    group_messages_by_api_round,
    is_compact_boundary_message,
    is_prompt_too_long_text,
    is_ptl_retry_marker_message,
    messages_after_compact_boundary,
    parse_prompt_too_long_token_counts,
    prompt_too_long_token_gap,
    should_auto_compact,
    strip_images_from_messages,
    truncate_head_for_ptl_retry,
)
from agentic_runtime.context.estimation import rough_token_count_for_messages
from agentic_runtime.context.window import resolve_context_window_policy
from agentic_runtime.contracts.events import (
    CompactionEvent,
    DoneEvent,
    ErrorEvent,
    TokenEvent,
)
from agentic_runtime.models.protocol import ThinkingConfig, UnsupportedModelOptionError

LOCAL_BUDGET = resolve_context_window_policy("local").budget(32_768, 4_096)
CANONICAL_BUDGET = resolve_context_window_policy("canonical").budget(200_000, 32_000)

LONG_SUMMARY = "<analysis>borrador</analysis>\n<summary>\n" + ("S" * 700) + "\n</summary>"
SHORT_SUMMARY = "<summary>corto</summary>"


class FakeCaller:
    def __init__(self, text: str, *, reject_thinking: bool = False, error: str = "") -> None:
        self.text = text
        self.reject_thinking = reject_thinking
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def complete(self, messages, tools, **kwargs):
        """El caller de B es una corrutina que DEVUELVE el generador: así lo consume
        `AgentLoop.run` (`agent_loop.py:573-587`), y el motor de compactación no
        estrena una forma de llamada propia."""
        self.calls.append({"messages": messages, "tools": tools, **kwargs})
        if self.reject_thinking and kwargs.get("thinking") is not None:
            raise UnsupportedModelOptionError("este motor no sabe apagar el razonamiento")

        async def stream():
            if self.error:
                yield ErrorEvent(message=self.error)
                return
            yield TokenEvent(content=self.text)
            yield DoneEvent()

        return stream()


class ScriptedCaller:
    def __init__(self, *responses: tuple[str, str]) -> None:
        """Cada entrada es `(canal, texto)`. `error` lo rinde como `ErrorEvent`, que es
        por donde el PTL llega en B; `token` como resumen. La última entrada se repite
        mientras sigan llegando llamadas."""
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def complete(self, messages, tools, **kwargs):
        self.calls.append({"messages": messages, "tools": tools, **kwargs})
        channel, text = self.responses[
            min(len(self.calls) - 1, len(self.responses) - 1)
        ]

        async def stream():
            if channel == "error":
                yield ErrorEvent(message=text)
                return
            yield TokenEvent(content=text)
            yield DoneEvent()

        return stream()


def _history(chars: int = 40, turns: int = 2) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for turn in range(turns):
        messages.append({"role": "user", "content": "u" * chars})
        messages.append({"role": "assistant", "content": f"a{turn}" * chars})
    return messages


def _collector() -> tuple[list[Any], Any]:
    seen: list[Any] = []

    async def emit(event: Any) -> None:
        seen.append(event)

    return seen, emit


# --- A · Prompts (par de prompt.ts) -----------------------------------------


def test_base_prompt_carries_the_nine_sections_and_the_analysis_scratchpad():
    prompt = get_compact_prompt()
    assert "<analysis>" in prompt
    for section in (
        "1. Primary Request and Intent",
        "5. Problem Solving",
        "9. Optional Next Step",
    ):
        assert section in prompt


def test_the_two_partials_scope_differently_and_up_to_renames_the_last_sections():
    """`up_to` coloca el resumen ANTES de lo conservado (prompt.ts:206-208), así que
    sus secciones 8/9 son «Work Completed» y «Context for Continuing Work», no el
    «Current Work» del parcial `from`."""
    from_prompt = get_partial_compact_prompt(direction="from")
    up_to_prompt = get_partial_compact_prompt(direction="up_to")
    assert "RECENT portion" in from_prompt
    assert "8. Current Work" in from_prompt
    assert "8. Work Completed" in up_to_prompt
    assert "9. Context for Continuing Work" in up_to_prompt


def test_no_prompt_names_a_single_tool():
    """El preámbulo antitool del canónico enumera `Read, Bash, Grep, Glob, Edit,
    Write` (prompt.ts:21). B no manda tools en esta llamada: portarlo sería meter
    nombres de herramientas en el estático contra el dogma, sin referente."""
    for prompt in (
        get_compact_prompt(),
        get_partial_compact_prompt(direction="from"),
        get_partial_compact_prompt(direction="up_to"),
    ):
        for tool_name in ("Read", "Bash", "Grep", "Glob", "Edit", "Write"):
            assert tool_name not in prompt


def test_custom_instructions_are_appended_only_when_they_say_something():
    assert "Additional Instructions:\nfoco en los tests" in get_compact_prompt(
        "foco en los tests"
    )
    assert "Additional Instructions" not in get_compact_prompt("   ")
    assert "Additional Instructions" not in get_compact_prompt(None)


def test_the_local_reasoning_guard_travels_only_under_its_flag():
    """Medida de `prueba_modelo_local/agent/compact.py:33-35`: el modelo local se
    cuela una orden de «deja de planificar» desde su propio razonamiento y devuelve
    código en vez de resumen. A no la necesita; atarla a la política local en vez de
    al prompt base evita inventarle a A una conducta que no tiene."""
    assert "reasoning limit" not in get_compact_prompt()
    assert "reasoning limit" in get_compact_prompt(local_reasoning_guard=True)


def test_format_strips_the_scratchpad_and_titles_the_summary():
    formatted = format_compact_summary(
        "<analysis>ruido interno</analysis>\n\n\n<summary>\ncuerpo\n</summary>"
    )
    assert "ruido interno" not in formatted
    assert formatted == "Summary:\ncuerpo"


def test_format_is_a_noop_on_plain_text_beyond_collapsing_blank_runs():
    assert format_compact_summary("uno\n\n\n\ndos\n") == "uno\n\ndos"


def test_the_user_summary_message_declares_provenance_and_what_survives():
    message = get_compact_user_summary_message(
        LONG_SUMMARY, True, "/tmp/sesion.jsonl", True
    )
    assert message.startswith("This session is being continued from a previous conversation")
    assert "/tmp/sesion.jsonl" in message
    assert "Recent messages are preserved verbatim." in message
    assert "without asking the user any further questions" in message


def test_without_suppression_there_is_no_continuation_order():
    message = get_compact_user_summary_message(LONG_SUMMARY, False)
    assert "Pick up the last task" not in message


# --- B · Frontera (par de utils/messages.ts:4530-4656) -----------------------


def test_the_boundary_is_a_pure_discriminant_and_the_scan_takes_the_last_one():
    first = create_compact_boundary_message("auto", 1_000)
    second = create_compact_boundary_message("manual", 2_000)
    messages = [{"role": "user", "content": "a"}, first, {"role": "user", "content": "b"}, second]
    assert is_compact_boundary_message(first)
    assert not is_compact_boundary_message({"role": "user", "content": "a"})
    assert find_last_compact_boundary_index(messages) == 3
    assert find_last_compact_boundary_index([{"role": "user", "content": "a"}]) == -1
    assert messages[3][COMPACT_BOUNDARY_KEY]["trigger"] == "manual"


def test_the_slice_includes_the_boundary_and_falls_back_to_everything():
    """`getMessagesAfterCompactBoundary` corta en `slice(boundaryIndex)` — la
    frontera VIAJA. Excluirla dejaría al modelo sin la marca de que lo anterior ya
    está resumido."""
    boundary = create_compact_boundary_message("auto", 10)
    tail = {"role": "user", "content": "posterior"}
    messages = [{"role": "user", "content": "previo"}, boundary, tail]
    assert messages_after_compact_boundary(messages) == [boundary, tail]
    assert messages_after_compact_boundary([tail]) == [tail]


def test_media_is_replaced_by_markers_including_inside_tool_results():
    """`stripImagesFromMessages` existe porque la propia llamada de compactación
    revienta el límite con imágenes que no aportan al resumen (compact.ts:133-143)."""
    messages = [
        {"role": "user", "content": [{"type": "image", "source": {"data": "x" * 100}}]},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "t1",
                    "content": [{"type": "document", "source": {"data": "y" * 100}}],
                }
            ],
        },
        {"role": "assistant", "content": "sin media"},
    ]
    stripped = strip_images_from_messages(messages)
    assert stripped[0]["content"] == [{"type": "text", "text": "[image]"}]
    assert stripped[1]["content"][0]["content"] == [{"type": "text", "text": "[document]"}]
    assert stripped[2] is messages[2]


# --- C · Motor (par de compact.ts:387-763 y 1136-1396) ----------------------


async def test_the_summary_call_goes_without_tools_with_its_own_system_and_no_thinking():
    """Tres decisiones canónicas en una: `createCompactCanUseTool` deniega TODO uso
    de tool (1125-1134), el system prompt es propio y único (1302-1304) y el
    razonamiento va explícitamente apagado (1305)."""
    caller = FakeCaller(LONG_SUMMARY)
    await compact_conversation(_history(), caller, LOCAL_BUDGET, model_id="m")
    call = caller.calls[0]
    assert call["tools"] == []
    assert call["system_override"] == COMPACT_SYSTEM_PROMPT
    assert call["thinking"] == ThinkingConfig(enabled=False)
    assert call["max_tokens"] == LOCAL_BUDGET.reserved_for_summary


async def test_only_what_follows_the_last_boundary_is_sent_plus_the_request():
    caller = FakeCaller(LONG_SUMMARY)
    boundary = create_compact_boundary_message("auto", 10)
    messages = [{"role": "user", "content": "viejo"}, boundary, {"role": "user", "content": "nuevo"}]
    await compact_conversation(messages, caller, LOCAL_BUDGET)
    sent = caller.calls[0]["messages"]
    assert [m.get("content") for m in sent[:2]] == ["Conversation compacted", "nuevo"]
    assert sent[-1]["content"].startswith("Your task is to create a detailed summary")


async def test_the_result_adds_a_boundary_and_a_summary_without_touching_the_history():
    """El núcleo NO reemplaza la historia: rinde las piezas y el integrador decide
    (D-42). `buildPostCompactMessages` fija el orden canónico (compact.ts:330-338)."""
    messages = _history()
    original = [dict(m) for m in messages]
    result = await compact_conversation(messages, FakeCaller(LONG_SUMMARY), LOCAL_BUDGET)
    assert messages == original
    assert is_compact_boundary_message(result.boundary_marker)
    assert result.summary_messages[0][COMPACT_SUMMARY_KEY] is True
    assert build_post_compact_messages(result)[0] is result.boundary_marker
    assert result.pre_compact_token_count > 0
    assert result.true_post_compact_token_count > 0


async def test_an_empty_history_is_refused_before_calling_the_model():
    caller = FakeCaller(LONG_SUMMARY)
    with pytest.raises(NotEnoughMessagesError):
        await compact_conversation([], caller, LOCAL_BUDGET)
    assert caller.calls == []


async def test_an_api_error_as_summary_is_a_failure_not_a_summary():
    """Sin esta guarda (compact.ts:507-515) el texto «API Error: …» SUSTITUYE a la
    conversación entera: la sesión pierde todo su estado y nadie se entera."""
    with pytest.raises(ApiErrorSummaryError):
        await compact_conversation(
            _history(), FakeCaller("API Error: overloaded"), LOCAL_BUDGET
        )


async def test_an_empty_response_is_a_failure():
    with pytest.raises(IncompleteResponseError):
        await compact_conversation(_history(), FakeCaller("   "), LOCAL_BUDGET)


async def test_a_conversation_with_a_single_round_has_no_head_to_truncate():
    """`truncateHeadForPTLRetry` devuelve `null` con menos de dos grupos (compact.ts:257):
    sin cabecera que soltar, reintentar sería repetir la misma llamada."""
    caller = FakeCaller(f"{PROMPT_TOO_LONG_ERROR_MESSAGE}: 300000 tokens > 200000")
    with pytest.raises(PromptTooLongError):
        await compact_conversation(
            [{"role": "user", "content": "u" * 40}], caller, LOCAL_BUDGET
        )
    assert len(caller.calls) == 1


async def test_a_crumb_of_a_summary_is_rejected_under_the_local_floor_only():
    """Medida de `prueba_modelo_local/agent/compact.py:41`: el modelo local gasta su
    presupuesto de salida razonando y emite una migaja. A no tiene suelo, y la
    política canónica lo declara a 0 en vez de inventarle uno."""
    with pytest.raises(SummaryTooShortError):
        await compact_conversation(_history(), FakeCaller(SHORT_SUMMARY), LOCAL_BUDGET)

    result = await compact_conversation(
        _history(), FakeCaller(SHORT_SUMMARY), CANONICAL_BUDGET
    )
    assert result.summary == SHORT_SUMMARY


async def test_an_engine_that_cannot_silence_reasoning_is_retried_once_and_declared():
    """`D-21`: descartar la opción en silencio produce la misma captura que
    obedecerla — un resumen generado bajo condiciones distintas de las pedidas y
    nadie enterado. El repliegue sale por el evento."""
    caller = FakeCaller(LONG_SUMMARY, reject_thinking=True)
    seen, emit = _collector()
    result = await compact_conversation(_history(), caller, LOCAL_BUDGET, emit=emit)
    assert len(caller.calls) == 2
    assert "thinking" not in caller.calls[1]
    assert result.reasoning_fallback is True
    assert result.thinking_disabled is False
    event = next(e for e in seen if isinstance(e, CompactionEvent))
    assert event.reasoning_fallback is True


# --- C bis · Reintento por PTL (par de compact.ts:227-291 y 445-491) --------


def _tool_history(rounds: int) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [{"role": "user", "content": "arranque"}]
    for index in range(rounds):
        messages.append({"role": "assistant", "content": f"paso {index}"})
        messages.append(
            {"role": "tool", "tool_call_id": f"t{index}", "content": "salida " * 20}
        )
    return messages


def test_the_round_grouping_cuts_before_each_assistant_and_the_preamble_stands_alone():
    """`groupMessagesByApiRound` (grouping.ts:24-50) abre grupo en el asistente, así que
    cada grupo es «asistente + lo que su vuelta arrastra» y el grupo 0 es el preámbulo
    de usuario. Divergencia DECLARADA: A necesita además comparar `message.id` porque
    `normalizeMessages` rinde un `AssistantMessage` POR BLOQUE de contenido; B añade
    exactamente uno por vuelta (`agent_loop.py:490-500`) y esa puerta no tiene
    referente. El corte es el punto seguro: nunca separa un asistente de sus
    resultados de tool."""
    groups = group_messages_by_api_round(_tool_history(2))
    assert [[m["role"] for m in group] for group in groups] == [
        ["user"],
        ["assistant", "tool"],
        ["assistant", "tool"],
    ]
    assert group_messages_by_api_round([]) == []


def test_the_error_text_yields_the_gap_only_when_it_is_a_real_overflow():
    assert parse_prompt_too_long_token_counts(
        "API Error: prompt is too long: 300000 tokens > 200000 maximum"
    ) == (300_000, 200_000)
    assert prompt_too_long_token_gap("Prompt is too long: 300000 tokens > 200000") == 100_000
    assert prompt_too_long_token_gap("Prompt is too long") is None
    assert prompt_too_long_token_gap("prompt is too long: 100 tokens > 200") is None
    assert is_prompt_too_long_text("API Error: PROMPT IS TOO LONG")
    assert not is_prompt_too_long_text("API Error: overloaded")


def test_the_parsed_gap_decides_how_many_rounds_jump_in_one_retry():
    """A acumula grupo a grupo hasta cubrir el exceso declarado por el motor
    (compact.ts:263-272): soltar de uno en uno gastaría los tres intentos sin bajar
    del límite."""
    history = _tool_history(6)
    per_group = rough_token_count_for_messages(history[1:3])
    error = f"Prompt is too long: {200_000 + per_group * 2} tokens > 200000"
    truncated = truncate_head_for_ptl_retry(history, error)
    assert truncated is not None
    remaining = group_messages_by_api_round(
        truncated[1:] if is_ptl_retry_marker_message(truncated[0]) else truncated
    )
    assert len(remaining) == 4


def test_an_unreadable_error_drops_a_fifth_of_the_rounds():
    truncated = truncate_head_for_ptl_retry(_tool_history(9), "Prompt is too long")
    assert truncated is not None
    body = truncated[1:] if is_ptl_retry_marker_message(truncated[0]) else truncated
    assert len(group_messages_by_api_round(body)) == 8


def test_the_head_never_eats_the_last_round():
    """El tope `groups.length - 1` (compact.ts:275) es lo que impide que el reintento
    se quede sin conversación que resumir."""
    truncated = truncate_head_for_ptl_retry(
        _tool_history(2), "Prompt is too long: 900000 tokens > 1"
    )
    assert truncated is not None
    body = truncated[1:] if is_ptl_retry_marker_message(truncated[0]) else truncated
    assert len(group_messages_by_api_round(body)) == 1
    assert truncate_head_for_ptl_retry([{"role": "user", "content": "solo"}], "") is None


def test_a_head_that_starts_in_the_assistant_gets_the_synthetic_user_marker():
    """Soltar el grupo 0 deja la secuencia empezando en asistente, que el motor
    rechaza; A antepone un usuario sintético (compact.ts:280-287)."""
    truncated = truncate_head_for_ptl_retry(_tool_history(3), "Prompt is too long")
    assert truncated is not None
    assert is_ptl_retry_marker_message(truncated[0])
    assert truncated[0]["content"] == PTL_RETRY_MARKER


def test_the_previous_marker_is_removed_before_regrouping_so_the_second_retry_advances():
    """Sin la retirada de la cabecera (compact.ts:249-255) el marcador se convertiría en
    el grupo 0 del reintento siguiente: se soltaría el marcador en vez de conversación
    y el truncado se quedaría en el sitio."""
    first = truncate_head_for_ptl_retry(_tool_history(6), "Prompt is too long")
    assert first is not None
    second = truncate_head_for_ptl_retry(first, "Prompt is too long")
    assert second is not None
    assert sum(1 for m in second if is_ptl_retry_marker_message(m)) == 1
    assert len(group_messages_by_api_round(second[1:])) < len(
        group_messages_by_api_round(first[1:])
    )


async def test_prompt_too_long_is_retried_with_a_shorter_head_and_declared():
    caller = ScriptedCaller(
        ("error", "API Error: prompt is too long: 300000 tokens > 200000"),
        ("token", LONG_SUMMARY),
    )
    seen, emit = _collector()
    result = await compact_conversation(
        _tool_history(6), caller, LOCAL_BUDGET, emit=emit
    )
    assert len(caller.calls) == 2
    assert len(caller.calls[1]["messages"]) < len(caller.calls[0]["messages"])
    assert result.summary == LONG_SUMMARY
    retry = next(e for e in seen if e.outcome == "ptl_retry")
    assert retry.reason == "prompt_too_long"
    assert retry.ptl_attempt == 1
    assert retry.dropped_messages > 0
    assert retry.remaining_messages == len(caller.calls[1]["messages"]) - 1
    assert next(e for e in seen if e.outcome == "compacted").ptl_attempt == 1


async def test_the_prompt_too_long_also_arrives_as_the_summary_text():
    """Divergencia DECLARADA de camino, no de criterio: A recibe el PTL como mensaje de
    asistente sintético con el texto crudo en `errorDetails` (`errors.ts:562-574`) y lo
    detecta por `startsWith` (compact.ts:454). B no tiene ese camino — el puente rinde
    `ErrorEvent` con el texto del proveedor (`caller.py:430-437`) — así que se clasifica
    por los dos sitios y de ambos se parsea el gap."""
    caller = ScriptedCaller(
        ("token", f"{PROMPT_TOO_LONG_ERROR_MESSAGE}: 300000 tokens > 200000"),
        ("token", LONG_SUMMARY),
    )
    result = await compact_conversation(_tool_history(6), caller, LOCAL_BUDGET)
    assert len(caller.calls) == 2
    assert result.summary == LONG_SUMMARY


async def test_three_retries_is_the_ceiling_and_the_giving_up_carries_the_count():
    """El techo se fija en el número del canónico (`MAX_PTL_RETRIES = 3`,
    compact.ts:227), no en la constante de B: comprobarla contra sí misma dejaría
    pasar cualquier valor."""
    assert MAX_PTL_RETRIES == 3
    caller = ScriptedCaller(("error", "API Error: prompt is too long"))
    with pytest.raises(PromptTooLongError) as raised:
        await compact_conversation(_tool_history(12), caller, LOCAL_BUDGET)
    assert len(caller.calls) == 4
    assert raised.value.ptl_attempts == 4


async def test_the_autocompaction_declares_the_attempts_it_burned_before_failing():
    caller = ScriptedCaller(("error", "API Error: prompt is too long"))
    tracking = AutoCompactTracking()
    seen, emit = _collector()
    history = [
        {"role": "user", "content": "x" * 440_000},
        {"role": "assistant", "content": "y" * 40},
        {"role": "user", "content": "z" * 40},
        {"role": "assistant", "content": "w" * 40},
    ]
    assert (
        await auto_compact_if_needed(
            history, caller, LOCAL_BUDGET, tracking=tracking, emit=emit
        )
        is None
    )
    assert seen[-1].outcome == "failed"
    assert seen[-1].reason == "prompt_too_long"
    assert seen[-1].ptl_attempt > 0
    assert tracking.consecutive_failures == 1


# --- D · Autocompactación, umbral y cortacircuitos (par de autoCompact.ts) ---


def test_below_the_threshold_nothing_fires():
    assert not should_auto_compact(_history(), LOCAL_BUDGET)


def test_above_the_threshold_it_fires_and_the_switch_still_wins():
    heavy = [{"role": "user", "content": "x" * 440_000}]
    assert should_auto_compact(heavy, LOCAL_BUDGET)
    assert not should_auto_compact(heavy, LOCAL_BUDGET, enabled=False)


def test_the_local_growth_brake_stops_the_immediate_recompaction():
    """Un resumen que ya nace por encima del umbral re-dispara en la vuelta
    siguiente y la sesión entra en bucle de compactar. El freno exige crecimiento
    real (1.5x medido) antes de volver a compactar; canónico lo declara a 1.0, que
    es no frenar."""
    heavy = [{"role": "user", "content": "x" * 440_000}]
    assert not should_auto_compact(
        heavy, LOCAL_BUDGET, tracking=AutoCompactTracking(last_compacted_tokens=110_000)
    )
    assert should_auto_compact(
        heavy, LOCAL_BUDGET, tracking=AutoCompactTracking(last_compacted_tokens=10_000)
    )

    huge = [{"role": "user", "content": "x" * 700_000}]
    assert should_auto_compact(
        huge, CANONICAL_BUDGET, tracking=AutoCompactTracking(last_compacted_tokens=174_000)
    )


async def test_a_successful_autocompaction_resets_the_failure_count():
    caller = FakeCaller(LONG_SUMMARY)
    tracking = AutoCompactTracking(consecutive_failures=2)
    result = await auto_compact_if_needed(
        [{"role": "user", "content": "x" * 440_000}],
        caller,
        LOCAL_BUDGET,
        tracking=tracking,
    )
    assert result is not None
    assert tracking.consecutive_failures == 0
    assert tracking.compacted is True
    assert tracking.last_compacted_tokens == result.true_post_compact_token_count


async def test_each_failure_counts_and_is_declared():
    caller = FakeCaller("API Error: overloaded")
    tracking = AutoCompactTracking()
    seen, emit = _collector()
    assert (
        await auto_compact_if_needed(
            [{"role": "user", "content": "x" * 440_000}],
            caller,
            LOCAL_BUDGET,
            tracking=tracking,
            emit=emit,
        )
        is None
    )
    assert tracking.consecutive_failures == 1
    assert seen[-1].outcome == "failed"
    assert seen[-1].reason == "api_error"


async def test_the_circuit_breaker_stops_calling_the_model_at_three_failures():
    """BQ 2026-03-10 del canónico: 1.279 sesiones con 50+ fallos consecutivos (hasta
    3.272) desperdiciando ~250K llamadas/día. Con el contexto irrecuperablemente por
    encima del límite, reintentar cada vuelta es quemar dinero sin cambiar nada."""
    caller = FakeCaller(LONG_SUMMARY)
    tracking = AutoCompactTracking(consecutive_failures=3)
    seen, emit = _collector()
    assert (
        await auto_compact_if_needed(
            [{"role": "user", "content": "x" * 440_000}],
            caller,
            LOCAL_BUDGET,
            tracking=tracking,
            emit=emit,
        )
        is None
    )
    assert caller.calls == []
    assert seen[-1].outcome == "skipped"
    assert seen[-1].reason == "circuit_breaker"
