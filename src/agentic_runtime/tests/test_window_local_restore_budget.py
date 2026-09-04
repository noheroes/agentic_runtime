"""El tope de ficheros a restaurar no es una magnitud en tokens y no se escala.

Medido en la corrida `20260903T202324-abe9213653af.jsonl` (115 turnos, 10
compactaciones, ventana 65.536): las diez restauraciones post-compactación
trajeron UN solo fichero, truncado a ~1.638 tokens, mientras el presupuesto
global disponible era de 16.384. Se usó el 10% de la propia asignación. El
modelo respondió releyendo: 107 `read_file` sobre 19 ficheros distintos, y el
primer `Edit` de la corrida no llegó hasta el minuto 73 de 115.

Criterio: `POST_COMPACT_MAX_FILES_TO_RESTORE` cuenta unidades de trabajo, no
tokens. El proyecto no encoge con la ventana del modelo. Quien acota el gasto es
`post_compact_token_budget`, que sí escala y que `restore.py:167` aplica adjunto
a adjunto; escalar además el recuento cuenta dos veces la misma protección.

Por construcción del canónico (`compact.ts:122-130`) los cinco ficheros caben
siempre: `5 × POST_COMPACT_MAX_TOKENS_PER_FILE = 25.000 <= 50.000 =
POST_COMPACT_TOKEN_BUDGET`, y ambos escalan por el mismo factor.
"""
from __future__ import annotations

from agentic_runtime.context.window import (
    POST_COMPACT_MAX_FILES_TO_RESTORE,
    POST_COMPACT_MAX_TOKENS_PER_FILE,
    POST_COMPACT_TOKEN_BUDGET,
    resolve_context_window_policy,
)

MEASURED_WINDOW = 65_536


def test_the_file_count_does_not_shrink_with_the_model_window():
    budget = resolve_context_window_policy("local").budget(MEASURED_WINDOW, MEASURED_WINDOW)

    assert budget.post_compact_max_files_to_restore == POST_COMPACT_MAX_FILES_TO_RESTORE


def test_the_full_file_count_still_fits_the_scaled_token_budget():
    """El colateral que el cambio podría causar: que la restauración se coma la
    ventana. No puede — el presupuesto global sigue escalando y sigue mandando."""
    for window in (16_384, 32_768, MEASURED_WINDOW, 128_000):
        budget = resolve_context_window_policy("local").budget(window, window)
        worst_case = (
            budget.post_compact_max_files_to_restore
            * budget.post_compact_max_tokens_per_file
        )

        assert worst_case <= budget.post_compact_token_budget
        assert worst_case < window // 2


def test_the_token_budgets_keep_scaling_with_the_window():
    scale = MEASURED_WINDOW / 200_000
    budget = resolve_context_window_policy("local").budget(MEASURED_WINDOW, MEASURED_WINDOW)

    assert budget.post_compact_token_budget == int(POST_COMPACT_TOKEN_BUDGET * scale)
    assert budget.post_compact_max_tokens_per_file == int(
        POST_COMPACT_MAX_TOKENS_PER_FILE * scale
    )


def test_the_measured_run_would_have_restored_more_than_it_did():
    """La corrida restauró 1.638 tokens de los 16.384 que tenía asignados."""
    budget = resolve_context_window_policy("local").budget(MEASURED_WINDOW, MEASURED_WINDOW)
    restored = (
        budget.post_compact_max_files_to_restore * budget.post_compact_max_tokens_per_file
    )

    assert restored > 4 * budget.post_compact_max_tokens_per_file
    assert restored == (
        POST_COMPACT_MAX_FILES_TO_RESTORE * budget.post_compact_max_tokens_per_file
    )
