# Handoff — Continuar con el Plan 2 (Capabilities: Skills / MCP / Voz / Memoria)

> Lee este archivo PRIMERO al entrar a Claude Code en `/home/noheroes/python/agentic_runtime/`.
> Es el punto de continuidad tras separar el runtime a su repo propio. La fuente de verdad del
> trabajo a hacer es **`PLAN_CAPABILITIES_SKILLS_MCP.md`** (raíz de este repo).

## Cómo retomar (enunciado sugerido al reentrar)

> "Retoma el Plan 2 en este repo. Lee HANDOFF_PLAN2.md y PLAN_CAPABILITIES_SKILLS_MCP.md.
> El runtime ya está estable (193 passed, 5 skipped). Arranca por el Orden Recomendado:
> CapabilityManager (C0) + contracts, sin mover comportamiento. TDD, 1 commit por fase."

---

## 1. Dónde estás

- **Repo standalone**: `/home/noheroes/python/agentic_runtime/` → `github.com/noheroes/agentic_runtime` (rama `main`).
- **Hermano**: `/home/noheroes/python/agentic_models/` → `github.com/noheroes/agentic_models`. El runtime
  depende de models por path: `agentic-models = { path = "../agentic_models", editable = true }`.
- **Layout**: src-layout. Paquete en `src/agentic_runtime/`, pyproject + uv.lock en la raíz. `uv.lock`,
  `.venv`, `__pycache__`, `.ruff_cache`, `*.egg-info` gitignored.
- **Verde actual**: `cd /home/noheroes/python/agentic_runtime && uv run python -m pytest src/agentic_runtime/tests/ -q`
  → **193 passed, 5 skipped**. Lint: `uvx ruff check src/agentic_runtime` → clean.
  - Los **5 skipped** = 1 skip preexistente + 4 E2E reales contra Azure que se omiten porque NO existe
    `agent_core/.env` ni `certs/` en este repo (gating correcto, ver §7). No son fallos.
- `agentic_models` aparte: `cd /home/noheroes/python/agentic_models && uv run python -m pytest src/agentic_models/tests/ -q` → 44 passed.

## 2. Qué se completó (por qué estamos listos para el Plan 2)

El runtime nuevo (sin agent_core, D4) está estable y verificado con LLM real:

- **Tracks cerrados**: runtime R0–R7, models M0–M3, **BORDES B1–B4** (presentation, exec_env/bwrap,
  filtro de toolset por kind, StorageKeys de dos planos).
- **E2E real con Azure gpt-5.4-mini** (foreground multi-turno + tools, cadena de 3 tools dependientes):
  funcional verde. Destapó y se corrigieron 3 defectos reales (port azure sync→async; `get_model`
  ambiguo → usar `get_by_provider`; `ctx.turn_count` nunca incrementado).
- **Primitiva de stream en vivo (SSE)** implementada y aprobada: `EventBus.subscribe_all`,
  `dispatch(task, *, on_event=...)` (devuelve task_id + stream completo) y `stream(task)` (async
  generator azúcar). El SSE es fiel: token deltas reconstruyen el texto final.

Conclusión: las **primitivas que el Plan 2 necesita ya existen de forma nativa** (fork, background,
`agent_id`, notificación, `EventBus`, presentation, exec_env). El Plan 2 construye SOLO la capa de
capabilities encima. No hay bloqueo para empezar.

## 3. Reglas NO NEGOCIABLES (embebidas — aquí NO está `.claude/rules/`)

Las reglas vivían en `new_core/.claude/`. En este repo no existen aún, pero **siguen aplicando**:

1. **Sin heurísticas (R1)**: ninguna decisión estructural por matching de texto/semejanza semántica.
   Si una decisión puede tomarse sin leer los datos reales, es heurística → prohibida.
2. **Sin alineación (R3)**: prohibido bajar criterios de cierre o forzar `can_finish`/SATISFIED para
   aparentar avance. Si un cambio hace que el loop/test termine antes sin mejorar la verificación
   funcional, es alineación → rechazar.
3. **Cambios arquitectónicos requieren aprobación EXPLÍCITA antes (R4)**: orden de fases del loop,
   responsabilidades de executor/projector/validator, criterio de cierre, quién genera IDs/secuencia.
   Ante duda: parar, describir, esperar OK.
4. **Salida del LLM tipada**: modelos Pydantic, nunca `dict[str, Any]` para lo que produce el modelo.
5. **Sin referencias a Claude/Anthropic** en commits/PRs/artefactos del repo (motivo legal). NO añadir
   `Co-Authored-By` de Claude.
6. **Cadencia git**: 1 commit por fase, scoped con pathspec. TDD: cada funcionalidad con sus tests en
   el mismo commit/PR. Nunca push directo a `main` — rama de feature + PR. Cada PR su propia rama.
7. **Idioma**: respuestas en español (Perú).
8. **Mantenimiento de docs**: registrar avance en el `## Registro De Avance` del plan; el WHY, no el WHAT.

## 4. El Plan 2 — qué es y por dónde empezar

Objetivo (de `PLAN_CAPABILITIES_SKILLS_MCP.md`): capa de **capabilities** que conecte **Skills, MCP,
STT/TTS (voz) y Memoria** al runtime por contratos estables, replicando el comportamiento de
`claude-code`. **No mejora comportamiento aún — lo alinea.**

Principio rector: Skills y MCP NO viven dentro del runtime; son **providers** conectados por contratos
(aportan catálogo, tools, procesan comandos/llamadas, `context_modifier`, contexto de compactación,
estado propio). El runtime no debe saber si una tool viene de MCP, skill o plugin.

**Orden recomendado (del plan):**
1. (ya provisto por el runtime: fork/background/`agent_id`/`EventBus`)
2. **CapabilityManager** sin mover comportamiento ← **EMPIEZA AQUÍ** (C0) + `capabilities/contracts.py`.
3. Encapsular **MCP provider** primero.
4. Encapsular **SkillsProvider** después.
5. Cambiar tool pool.
6. Cambiar context modifiers.
7. Limpiar prompts/sections.
8. Limpiar metadata legacy.

Contratos a definir (ver §"Contratos Comunes" del plan): `CapabilityProvider`, `CapabilityManager`,
`CapabilitySummary`, `CapabilityActivation`. Invariantes clave: una capability **no genera `agent_id`**
(lo recibe del runtime vía `RuntimeContextForker`); el estado activo se scopea por `context.agent_id`;
los resultados background van al `BackgroundNotificationChannel` por `session_id`, no a `session.messages`.

**Proyecto de referencia**: `claude-code` en `/home/noheroes/python/claude-code/src` (el plan pide
replicar `appState.mcp.*`, `assembleToolPool`, `SkillTool`, `processPromptSlashCommand`, `invoked_skills`).

## 5. Estrategia de ramas en ESTE repo

Cambió respecto a new_core. Ya NO es "feature/capabilities_skills_mcp desde feature/runtime-agentico".
Ahora:
- Crear **`feature/capabilities`** (o similar) **desde `main`** de este repo.
- Trabajar ahí, 1 commit por fase. **PR `--base main`** al cerrar. Nunca commitear directo a `main`.

## 6. Reconciliación con el estado real (evita rehacer cosas)

El plan está fechado 2026-06-14, ANTES de cerrar BORDES B1–B4 (2026-06-15). Su nota final dice "falta
cablear `PathPresentation` y `ToolExecEnvironment`" — **ya están cableados**:
- **B1** cableó la presentation (`context/presentation.py`, choke point en `ToolDispatcher.dispatch`).
- **B2** cableó `ToolExecEnvironment` (`tools/exec_env.py`, `BwrapExecEnvironment`; bwrap no instalado →
  run real skipeado, no fingido).
No los re-implementes; consúmelos.

## 7. Entorno / config

- Los **E2E reales Azure** (`tests/test_runtime_e2e_real*.py`, helper `tests/_azure_real.py`) leen la
  config de `new_core/src/agent_core/.env` + `new_core/certs/cacert.pem`. Desde ESTE repo no existen →
  se omiten (skip). Para correrlos con LLM real hay que apuntarlos a esa config o portar un `.env` local.
  Recordatorio de config que funcionó: `AZURE_OPENAI_API_VERSION=preview` (NO `2024-12-01-preview`),
  `SSL_CERT_FILE` al CA corporativo, modelo vía `get_by_provider("azure-openai-responses","gpt-5.4-mini")`.
- **Diferidos (NO bloquean el Plan 2, viven en el repo `agentic_models`)**: transporte mistral (pin v1.x
  vs adaptar import) y deuda del port bedrock (`BotoConfig`/`use_bearer` sin cablear, marcados TODO+noqa).

## 8. Memoria / continuidad

La memoria persistente de Claude Code (`MEMORY.md` + `project_runtime_resume.md`, etc.) está keyed al
**proyecto new_core**. Una sesión nueva abierta en esta carpeta tendrá OTRO directorio de memoria y NO
cargará esas notas automáticamente. **Este archivo es la continuidad principal.** Si necesitas el
histórico detallado del runtime, está en `project_runtime_resume.md` (memoria de new_core) y en
`PLAN_COMPLEMENTARIO_RUNTIME.md` (raíz de este repo).
