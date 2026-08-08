"""Capa plan-file — homólogo de `utils/plans.ts` adaptado al modelo de storage del runtime.

Canónico: el plan-file vive en `~/.claude/plans/{slug}.md` (disco local single-user); el word-slug
existe para evitar colisiones en ese dir PLANO compartido entre sesiones. Aquí NO aplica:
agent_core es contenerizado, la fuente de verdad es MinIO (blob per-sesión vía `StorageContract`).
El namespace de sesión da la unicidad, así que no hace falta slug — el token es FIJO por sesión.

El wheel trata SOLO el token de plan-file (mecanismo) y lee vía `ctx.storage` inyectado; el mapeo
token→key MinIO + materialización al workspace del contenedor es política del consumidor
(el `PathStorage` del integrador ya mapea la familia `/plans/<name>`). Homólogo de
`getPlanFilePath` (plans.ts:119) / `getPlan` (:135) / `isSessionPlanFile` (filesystem.ts:245).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...context.tool_use import ToolUseContext

logger = logging.getLogger(__name__)

# ── Estado de plan runtime-visible (`app_state.native`) ─────────────────────────────────
# Flag: plan mode activo (lo siembra EnterPlanMode / el flag del integrador).
_PLAN_MODE_KEY = "plan_mode"
# One-shot: se acaba de salir de plan mode → el provider emite el recordatorio de salida una vez
# (espejo de `needsPlanModeExitAttachment`).
_PLAN_EXIT_PENDING_KEY = "plan_mode_exit_pending"
# Copia del plan aprobado para el one-shot de salida. Se NUTRE del plan-file (disco), no de un
# arg de entrada de ExitPlanMode — el plan-file es la fuente de verdad (el modelo lo escribió
# durante plan mode). El provider (sync) la rinde sin re-leer storage (async).
_PLAN_KEY = "plan"

# Cadencia full→sparse del reminder de 5-fases: la primera iteración rinde el texto completo,
# las siguientes uno escueto mientras plan mode siga activo (espejo de `getPlanModeV2Instructions`
# → `getPlanModeV2SparseInstructions`). Se limpia al entrar/salir de plan mode.
_PLAN_FULL_SHOWN_KEY = "plan_mode_full_shown"

# Prefijo del token de plan-file. Contrato con el `StorageContract` del consumidor
# (`FAKE_PLANS_PREFIX="/plans"` en el integrador → `session_plans_dir` local + `plans_key` blob).
_PLAN_TOKEN_PREFIX = "/plans"

# Tipos de subagente del workflow de plan mode. CONTRATO con el integrador: debe registrar agentes
# bajo estos stems (`Explore.md`/`Plan.md`). Homólogo de `EXPLORE_AGENT.agentType` (exploreAgent.ts:65)
# / `PLAN_AGENT.agentType` (planAgent.ts:74). El reminder de 5-fases los nombra; si no calzan con lo
# registrado, el modelo referencia un tipo inexistente.
EXPLORE_AGENT_TYPE = "Explore"
PLAN_AGENT_TYPE = "Plan"


def get_plan_file_path(ctx: ToolUseContext) -> str:
    """Token del plan-file de la sesión. Homólogo de `getPlanFilePath` (plans.ts:119).

    Root: `/plans/plan.md`. Subagente: `/plans/plan-agent-{agent_id}.md`. El discriminador es
    `is_subagent` (no `agent_id`, que también identifica al contexto raíz — ver `plan_mode.py`)."""
    if ctx.is_subagent and ctx.agent_id:
        return f"{_PLAN_TOKEN_PREFIX}/plan-agent-{ctx.agent_id}.md"
    return f"{_PLAN_TOKEN_PREFIX}/plan.md"


def is_session_plan_file(token: str) -> bool:
    """El token es un plan-file de sesión (mecanismo de exención del candado).

    Homólogo de `isSessionPlanFile` (filesystem.ts:245): prefijo `/plans/` + sufijo `.md`. El
    integrador lo consume para eximir el plan-file del candado de plan mode."""
    return token.startswith(f"{_PLAN_TOKEN_PREFIX}/") and token.endswith(".md")


def plan_file_exists(ctx: ToolUseContext) -> bool:
    """¿Existe ya el plan-file localmente? Chequeo SYNC (para el reminder activo del provider).

    Durante planning el archivo recién escrito por el modelo está materializado local, así que
    `real_path(token).exists()` basta sin hidratar del blob (async). Espejo de `planExists`."""
    storage = ctx.storage
    if storage is None:
        return False
    try:
        return bool(storage.real_path(get_plan_file_path(ctx)).exists())
    except Exception:  # noqa: BLE001 — sondeo de existencia: cualquier fallo es 'no hay plan'
        return False


async def get_plan(ctx: ToolUseContext) -> str | None:
    """Contenido del plan-file vía storage inyectado, o None si no existe.

    Homólogo de `getPlan` (plans.ts:135), leyendo del blob per-sesión (con materialización local)
    en vez del fs local del canónico. `ensure_local` en blob-miss devuelve el host inexistente
    (no lanza), así que el `read_text` fallido → None."""
    storage = ctx.storage
    if storage is None:
        return None
    token = get_plan_file_path(ctx)
    try:
        local: Path = await storage.ensure_local(token)
        return local.read_text(encoding="utf-8")
    except OSError:
        return None
    except (AttributeError, TypeError):
        # `FIND-PLAN-FILE-1` · corte 2: `ctx.storage` puede traer un objeto que NO cumple
        # `StorageContract`. No es hipotético — el storage NATIVO del runtime
        # (`FilesystemStorage`) implementa `StorageProtocol` (`upload/download/…`), que no
        # tiene `ensure_local`; enchufarlo aquí hacía REVENTAR a `ExitPlanMode` en vez de
        # errar, porque `except OSError` no atrapa un `AttributeError`. `plan_file_exists`
        # (arriba) ya degradaba a `False` por su `except Exception`: las dos mitades de la
        # misma capa se comportaban distinto ante la misma entrada.
        logger.warning(
            "plan-file: `ctx.storage` no cumple `StorageContract` (falta `ensure_local`); "
            "el plan-file queda inalcanzable. Inyecta `RuntimeConfig.storage_contract`."
        )
        return None


__all__ = [
    "EXPLORE_AGENT_TYPE",
    "PLAN_AGENT_TYPE",
    "_PLAN_EXIT_PENDING_KEY",
    "_PLAN_FULL_SHOWN_KEY",
    "_PLAN_KEY",
    "_PLAN_MODE_KEY",
    "get_plan",
    "get_plan_file_path",
    "is_session_plan_file",
    "plan_file_exists",
]
