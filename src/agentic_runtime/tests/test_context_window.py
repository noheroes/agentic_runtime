"""Homologación K6·tramo-1 — estimador de tokens y presupuestos post-compactación.

Contrapartes canónicas leídas ÍNTEGRAS:
- `services/tokenEstimation.ts` (495) — `roughTokenCountEstimation` (203-208),
  `bytesPerTokenForFileType` (215-224), `roughTokenCountEstimationForMessages`
  (327-339), `...ForMessage` (341-369), `...ForContent` (371-389),
  `...ForBlock` (391-435).
- `utils/tokens.ts` (261) — `getTokenCountFromUsage` y `tokenCountWithEstimation`:
  última medida real + estimación de lo añadido después.
- `services/compact/autoCompact.ts` (351) — `MAX_OUTPUT_TOKENS_FOR_SUMMARY` (30),
  los cuatro buffers (62-65), `getEffectiveContextWindowSize` (33-49),
  `getAutoCompactThreshold` (72-91), `calculateTokenWarningState` (93-145).
- `services/compact/compact.ts` (1705) — las cinco constantes `POST_COMPACT_*`
  (122-130).

Criterio: la aritmética canónica se reproduce EXACTA bajo la política `canonical`;
la política `local` escala por ventana los nueve valores canónicos, y NO escala los
dos que son medida empírica de `~/python/prueba_modelo_local` (`compact.py:41`
`MIN_RESUMEN_CHARS=600`; `loop.py:330` el 1.5x de rebrote) — escalarlos por 0.16
destruiría el valor medido, que es lo único que los justifica.
"""
from __future__ import annotations

from agentic_runtime.context.estimation import (
    MEDIA_BLOCK_TOKENS,
    UsageAnchor,
    bytes_per_token_for_file_type,
    rough_token_count,
    rough_token_count_for_content,
    rough_token_count_for_message,
    rough_token_count_for_messages,
    token_count_with_estimation,
    truncate_to_tokens,
)
from agentic_runtime.context.window import (
    AUTOCOMPACT_BUFFER_TOKENS,
    CANONICAL_REFERENCE_WINDOW,
    MAX_OUTPUT_TOKENS_FOR_SUMMARY,
    MIN_SUMMARY_CHARS_LOCAL,
    POST_COMPACT_MAX_TOKENS_PER_FILE,
    POST_COMPACT_SKILLS_TOKEN_BUDGET,
    POST_COMPACT_TOKEN_BUDGET,
    RECOMPACTION_GROWTH_RATIO_LOCAL,
    resolve_context_window_policy,
)

# --- A · Estimador por bloque (par de tokenEstimation.ts:391-435) -----------


def test_rough_count_is_four_bytes_per_token_rounded_half_up():
    assert rough_token_count("") == 0
    assert rough_token_count("x" * 8) == 2
    assert rough_token_count("x" * 10) == 3


def test_dense_file_types_use_two_bytes_per_token():
    assert bytes_per_token_for_file_type("json") == 2
    assert bytes_per_token_for_file_type("jsonl") == 2
    assert bytes_per_token_for_file_type(".JSONC") == 2
    assert bytes_per_token_for_file_type("py") == 4


def test_media_blocks_are_a_flat_constant_not_their_payload():
    """El catch-all `jsonStringify` cobraría ~325k tokens por un PDF de 1MB en
    base64 (tokenEstimation.ts:405-411); el canónico corta con 2000 fijos."""
    huge = "A" * 400_000
    image = {"type": "image", "source": {"type": "base64", "data": huge}}
    document = {"type": "document", "source": {"type": "base64", "data": huge}}
    assert rough_token_count_for_content([image]) == MEDIA_BLOCK_TOKENS
    assert rough_token_count_for_content([document]) == MEDIA_BLOCK_TOKENS


def test_tool_use_counts_name_plus_serialized_input():
    block = {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}}
    assert rough_token_count_for_content([block]) == rough_token_count(
        'Bash{"command":"ls"}'
    )


def test_tool_result_recurses_into_its_content():
    nested = {"type": "text", "text": "y" * 16}
    block = {"type": "tool_result", "tool_use_id": "t1", "content": [nested]}
    assert rough_token_count_for_content([block]) == 4


def test_thinking_blocks_count_their_text_and_redacted_count_their_data():
    assert rough_token_count_for_content([{"type": "thinking", "thinking": "z" * 12}]) == 3
    assert rough_token_count_for_content([{"type": "redacted_thinking", "data": "z" * 12}]) == 3


def test_unknown_block_falls_back_to_its_serialized_form():
    block = {"type": "server_tool_use", "name": "web", "input": {}}
    assert rough_token_count_for_content([block]) > 0


def test_only_the_roles_that_travel_to_the_model_count():
    """Divergencia DECLARADA de forma, no de criterio. A cuenta `assistant`, `user` y
    `attachment` (tokenEstimation.ts:341-369) y con eso cubre el 100% de lo que viaja:
    en A los resultados de tool son bloques `tool_result` DENTRO de mensajes de
    usuario. En B viven en mensajes propios de rol `tool` (`agent_loop.py:533-537`),
    así que la lista literal de A dejaría la masa entera de salidas de tools valorada
    en cero — y con ella el umbral de autocompactación y el salto por gap del
    truncado de cabecera, que suma grupo a grupo. El marcador de frontera (`system`)
    sigue sin contar: es discriminante local, no viaja."""
    assert rough_token_count_for_message({"role": "system", "content": "x" * 400}) == 0
    assert rough_token_count_for_message({"role": "user", "content": "x" * 400}) == 100
    assert rough_token_count_for_message(
        {"role": "tool", "tool_call_id": "t1", "content": "x" * 400}
    ) == 100
    assert rough_token_count_for_messages(
        [{"role": "user", "content": "x" * 400}, {"role": "assistant", "content": "x" * 400}]
    ) == 200


# --- B · Ancla de medida (par de utils/tokens.ts::tokenCountWithEstimation) --


def test_without_anchor_everything_is_estimated():
    messages = [{"role": "user", "content": "x" * 400}]
    assert token_count_with_estimation(messages) == 100


def test_anchor_replaces_the_measured_prefix_and_estimates_only_the_tail():
    """La medida real del motor manda sobre el prefijo; sólo lo añadido después
    de esa medida se estima. Es la razón de ser de la función en el canónico."""
    messages = [
        {"role": "user", "content": "x" * 4000},
        {"role": "assistant", "content": "x" * 400},
    ]
    anchor = UsageAnchor(context_tokens=12_345, message_count=1)
    assert token_count_with_estimation(messages, anchor) == 12_445


def test_a_stale_anchor_is_discarded_instead_of_believed():
    """Si el historial encogió, el ancla ya no describe esta historia: estimar
    entera es la respuesta honesta, no sumar una medida que no le corresponde."""
    messages = [{"role": "user", "content": "x" * 400}]
    anchor = UsageAnchor(context_tokens=99_999, message_count=7)
    assert token_count_with_estimation(messages, anchor) == 100


def test_truncation_keeps_the_head_and_fits_the_budget():
    marker = "[cortado]"
    content = "c" * 10_000
    out = truncate_to_tokens(content, 100, marker)
    assert out.startswith("ccc") and out.endswith(marker)
    assert rough_token_count(out) <= 100


def test_truncation_is_a_noop_under_budget():
    assert truncate_to_tokens("corto", 100, "[m]") == "corto"


# --- C · Presupuesto canónico (par de autoCompact.ts + compact.ts:122-130) ---


def test_canonical_budget_reproduces_the_canonical_arithmetic():
    budget = resolve_context_window_policy("canonical").budget(
        CANONICAL_REFERENCE_WINDOW, 32_000
    )
    assert budget.reserved_for_summary == 20_000
    assert budget.effective_window == 180_000
    assert budget.autocompact_threshold == 167_000
    assert budget.warning_threshold == 147_000
    assert budget.error_threshold == 147_000
    assert budget.blocking_limit == 177_000


def test_canonical_post_compact_budgets_are_the_canonical_constants():
    budget = resolve_context_window_policy("canonical").budget(
        CANONICAL_REFERENCE_WINDOW, 32_000
    )
    assert budget.post_compact_max_files_to_restore == 5
    assert budget.post_compact_token_budget == 50_000
    assert budget.post_compact_max_tokens_per_file == 5_000
    assert budget.post_compact_max_tokens_per_skill == 5_000
    assert budget.post_compact_skills_token_budget == 25_000


def test_canonical_carries_no_empirical_guard():
    """A no tiene ni suelo de resumen ni freno de rebrote: sólo comprueba que el
    resumen no sea nulo (compact.ts:493). Declararlos a 0/1.0 los desactiva sin
    inventarle a A una conducta que no tiene."""
    budget = resolve_context_window_policy("canonical").budget(
        CANONICAL_REFERENCE_WINDOW, 32_000
    )
    assert budget.min_summary_chars == 0
    assert budget.recompaction_growth_ratio == 1.0


# --- D · Escalado local (D-41) y lo que NO se escala (D-22, medido) ----------


def test_local_scales_every_canonical_constant_by_window_ratio():
    window = 32_768
    scale = window / CANONICAL_REFERENCE_WINDOW
    budget = resolve_context_window_policy("local").budget(window, 4_096)
    assert budget.reserved_for_summary == int(MAX_OUTPUT_TOKENS_FOR_SUMMARY * scale)
    assert budget.effective_window == window - int(MAX_OUTPUT_TOKENS_FOR_SUMMARY * scale)
    assert budget.autocompact_threshold == budget.effective_window - int(
        AUTOCOMPACT_BUFFER_TOKENS * scale
    )
    assert budget.post_compact_token_budget == int(POST_COMPACT_TOKEN_BUDGET * scale)
    assert budget.post_compact_max_tokens_per_file == int(
        POST_COMPACT_MAX_TOKENS_PER_FILE * scale
    )
    assert budget.post_compact_skills_token_budget == int(
        POST_COMPACT_SKILLS_TOKEN_BUDGET * scale
    )


def test_local_restores_at_least_one_file():
    """5 ficheros × 5k en una ventana de 32k serían el 80% del contexto. Escalado
    da 0.81 ficheros; el suelo de 1 evita que la restauración quede muerta."""
    budget = resolve_context_window_policy("local").budget(32_768, 4_096)
    assert budget.post_compact_max_files_to_restore == 1


def test_local_empirical_guards_keep_their_measured_value():
    """Escalar 600 por 0.16 da 96 caracteres, que es longitud de migaja: sería
    exactamente lo que el guarda existe para rechazar."""
    budget = resolve_context_window_policy("local").budget(32_768, 4_096)
    assert budget.min_summary_chars == MIN_SUMMARY_CHARS_LOCAL == 600
    assert budget.recompaction_growth_ratio == RECOMPACTION_GROWTH_RATIO_LOCAL == 1.5


def test_local_at_the_reference_window_equals_canonical():
    """`scale_for` clampa a 1.0: la política local sobre una ventana canónica no
    inventa un presupuesto distinto — sólo se separa cuando la ventana es menor."""
    local = resolve_context_window_policy("local").budget(CANONICAL_REFERENCE_WINDOW, 32_000)
    canonical = resolve_context_window_policy("canonical").budget(
        CANONICAL_REFERENCE_WINDOW, 32_000
    )
    assert local.autocompact_threshold == canonical.autocompact_threshold
    assert local.post_compact_token_budget == canonical.post_compact_token_budget
