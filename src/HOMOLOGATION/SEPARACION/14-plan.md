# 14 · capabilities/plan — SEPARACION (Filosofía B)

> Ruta base `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/14-plan.md`.
> Tracker de origen: `../14-cap-plan.md` (503 LOC, leído ÍNTEGRO 1→EOF este ciclo). Esquema: `00-LEGEND.md §3`.
> PASO 0 (11 lecciones skill) ejecutado. B (4 archivos: `capabilities/plan/{plan_file.py, provider.py, __init__.py}`
> + `tools/native/plan_mode.py`) + ENSAMBLADOR (`factory.py`/`capabilities/manager.py`/`loop/agent_loop.py`/
> `execution/local/runtime.py`/`execution/agents.py`/`capabilities/resolver.py`/`contracts/permissions.py`/
> `tools/factory.py`) **RE-ABIERTOS 1→EOF EN ESTE CICLO** (L09/L11, **NO** heredados de la re-visita gate-11 del
> tracker 2026-07-20) + grep-de-ausencia por-término (legítimo sólo para ausencia).

---

## 0. Tesis de separación (Filosofía B)

Plan mode es un **compuesto de cuatro piezas** que la SEPARACION reparte, no un módulo monolítico: (i) un **modo de
permiso** (candado read-only excepto el plan-file), (ii) una **capa de instrucciones por-turno** (`PlanModeProvider`,
contexto puro como la memoria — `tools()==[]`/`catalog()==[]`, verificado provider.py:136-140), (iii) **dos tools
nativas** (`EnterPlanMode`/`ExitPlanMode`) y (iv) el **plan-file** (token + lectura vía `ctx.storage`). Como en
11/12/13, se descompone en tres capas:

1. **Base = MECANISMO de activación + contratos + seams.** El `CapabilityProvider` (seam por el que el plan enchufa,
   home 12/general, **NO nuevo de 14**) + su agregación per-turno en el manager (`active_context` manager:98-102) + su
   consumo en el loop (`_inject_recall` agent_loop:218) = **T2-BASE-MECANISMO**, COMPARTIDO con skills/mcp/memory. El
   **modo de permiso** `PermissionContext.mode` (el candado, HOY AUSENTE = keystone, home 06·GAP-02) y el contrato
   `ToolResult` (`context_modifier`/`ends_turn`, home 10/01) son base/contrato. El **plan-file** cuelga del seam
   `StorageContract` (`ctx.storage`, home 15) — HOY NO ligado.
2. **El plan-mode concreto = BATTERY `battery_plan` opcional** sobre esos seams: `PlanModeProvider` (instrucciones
   full/sparse/subagent/exit + reentry/interview a construir) + `EnterPlanMode`/`ExitPlanMode` + `plan_file.py` (token
   + get_plan) + las **AgentDefinition built-in `Explore`/`Plan`** (hoy inexistentes). **Anti-padding L10:** un
   integrador puede NO querer plan mode, o sustituir su workflow → por eso es battery. Que la battery esté **a medio
   construir** (candado no forzado, agentes no registrados, storage inerte, prompts recortados) = **CORE-GAPs que la
   battery+base DEBEN cerrar** (el canónico SÍ tiene la capacidad — distinto de un shape opcional que nadie reclama).
3. **Aprobación (modo-resultante/clear-context/feedback/auto-name), el permiso de ENTRAR, la inyección del
   `agent_resolver`, el backing de `ctx.storage` y la interfaz (`/plan`, diálogos, renderers) = integrador.**

**La promesa está a MEDIO CUMPLIR (verificado por cableado ESTE ciclo, no heredado):** el registro del provider
funciona y se inyecta per-turno (agent_loop:218), el one-shot de salida rinde el plan aprobado inline (provider:160-163,
mejora 🔀), y `context_modifier`/`ends_turn` se aplican en el loop (agent_loop:332-339). **PERO** el **candado** es
sólo texto del reminder (`PermissionContext` sin `mode`, `is_session_plan_file` sin consumidor), los **agentes
Explore/Plan del workflow de 5 fases no resuelven** (agent_resolver=None → fork genérico), el **plan-file es inerte**
en standalone (`ctx.storage` nunca ligado), y falta la cadencia/reentry/interview/preservación-tras-compact.

### 0.1 DESAMBIGUACIÓN load-bearing (4 hallazgos de cableado ESTE ciclo)

**(a) El candado de plan mode NO se hace cumplir en el base — es el keystone = GAP-02.** El canónico deniega toda
escritura ≠ plan-file vía `toolPermissionContext.mode==='plan'`. El runtime: (1) `contracts/permissions.py` **1→33
ÍNTEGRO** = `PermissionContext` con SÓLO `always_allow_command`/`always_allow_session`/`always_deny` — **sin campo
`mode`** (grep `.mode`=0); (2) `EnterPlanMode.execute` siembra un flag `app_state.native["plan_mode"]=True`
(plan_mode.py:46), NO un modo de permiso; (3) `is_session_plan_file` (plan_file.py:58-63, el predicado de exención)
tiene **0 consumidores de prod** (grep: sólo su def + `__all__`). Resultado: el candado ("MUST NOT edit except the
plan file") vive SÓLO en el texto del reminder (provider.py:52/56/105); ningún gate deniega writes ≠ plan-file. **Es
la realización plan-mode de 06·CG-HOOK-8 / 03·GAP-CTX2 / 01·GAP-02** — se UNIFICA, no se reinventa (CG-PLAN-1).

**(b) `PlanModeProvider` se registra INCONDICIONAL — a diferencia de MCP/skills/memory.** `factory.
_build_capability_manager` **1→267 ÍNTEGRO**: la lista arranca `providers = [PlanModeProvider()]` (**factory.py:146**),
mientras MCP (:148 `if caps.mcp_servers or mcp_config_store`), skills (:160 `if caps.skill_dirs or skill_store`) y
memory (:166 `if memory_store or memory_root`) son **condicionales**. En B esto es una **decisión de composición**: el
plan está hardwired como capability nativa siempre-presente. No es bug (el canónico también tiene plan mode siempre),
pero la pregunta "¿`battery_plan` es opt-in como las otras o default del base?" se decide en A3.CAT (§2.2).

**(c) El plan-file es INERTE en standalone — `ctx.storage` NUNCA se liga.** `execution/local/runtime.py` **1→435
ÍNTEGRO**: `_run_loop` (306-416) liga `ctx.presentation` (:317), `ctx.exec_env` (:318), `ctx.git_credentials` (:321),
`ctx.fs` (:324-325) — pero **cero `ctx.storage`** (grep `.storage =` en runtime/loop = 0). `plan_file.get_plan`
(plan_file.py:86-88) y `plan_file_exists` (:71-72) devuelven `None`/`False` si `ctx.storage is None`. `ExitPlanMode.
execute` llama `get_plan` (plan_mode.py:79) → siempre `None` en standalone → error "No plan found". **Es la cara-14 del
cabo 15·OI-STOR-C** (`ctx.storage` inerte, ya anticipado en 15·§0.1) — aterriza aquí como CG-PLAN-3.

**Razón MECÁNICA de (c), destapada al abrir el CONTRATO en la 2ª iteración:** `context/tool_use.py` **1→70 ÍNTEGRO** —
`storage: Any = None` (**:49**) es el ÚNICO seam de I/O **sin default y sin tipar**, mientras `fs: Any =
Field(default_factory=_default_fs)` (**:52**) trae un default seguro (`ConfinedFilesystem`, :16-20). Es decir: las
tools de fichero funcionan en standalone por construcción y el plan-file **no puede** hacerlo — la inercia de (c) no
es un olvido del `_run_loop`, es la forma del contrato. Además `storage` es `Any`, no `StorageContract`: no hay
ligadura estática con `contracts/storage.py` (**1→40 ÍNTEGRO**, `real_path`/`ensure_local`/`commit`/`teardown` :25-31),
aunque `plan_file.py` llame exactamente `real_path` (:75) y `ensure_local` (:91) — el acoplamiento es por duck-typing.
CG-PLAN-3 + OI-PLAN-C se enuncian ahora contra el contrato abierto, no inferidos del consumo.

**(d) `battery_plan` NO usa el seam de system prompt — todo el plan mode viaja como contexto VOLÁTIL.**
`capabilities/contracts.py` **1→76 ÍNTEGRO**: `CapabilityProvider` declara catalog/tools/active_context/
compact_context (:66-69) **y un hook OPCIONAL `system_prompt_section`** (:49-58) documentado como "instrucciones
permanentes y **cache-friendly** (mismo texto entre turnos = buen prefijo de caché), no contexto volátil — eso va por
`active_context`". `PlanModeProvider` **no lo implementa** (provider.py 1→171): el reminder de 5 fases se re-emite
per-turno por `active_context`. Esto **no es gap** (el canónico también lo entrega como attachment per-turno, no como
system prompt) pero **sí es el fundamento del coste que CG-PLAN-8 mitiga**: sin throttle, un texto largo y volátil
per-turno rompe el prefijo de caché justo donde el contrato base avisa. Es la **misma asimetría documentada en
11·§0.2** (MCP tampoco lo implementa). `CapabilityActivation` (:26-38, = LAT-CAP1 de 12) comprobado: **no aterriza en
14** (plan no activa capabilities; rinde `tools()==[]`/`catalog()==[]`).

### 0.2 nota-identidad — dos ejes (persistencia + ejecución)

- **Persistencia (durable): el plan-file.** Token `/plans/plan.md` (root) / `/plans/plan-agent-{agent_id}.md`
  (subagente, discriminado por `is_subagent`, plan_file.py:53-55). Patrón **id opaco + repo**: el token es opaco; el
  mapeo token→blob MinIO + materialización lo hace el `StorageContract`/`PathStorage` del integrador (que ya mapea la
  familia `/plans/<name>`). El word-slug del canónico (retry-colisión + cache) NO aplica: el namespace de sesión da la
  unicidad, token FIJO (C3 🔀 deliberado). **Sub-matiz de seguridad:** la variante subagente incrusta `agent_id` (uuid
  volátil, fork:69) — si el integrador no sanitiza el componente al mapear, mismo riesgo que **15·CG-STOR-3**
  (guard-path unificado); pero el plan-file atraviesa `ctx.storage` (StorageContract del integrador), no el blob crudo.
- **Ejecución (efímero): el flag `plan_mode`.** `app_state.native["plan_mode"]` + `plan_mode_full_shown` +
  `plan_mode_exit_pending` + `plan` (cache del one-shot) — estado por-turno, no durable. Es el mecanismo-hack que
  CG-PLAN-1 reemplaza por `PermissionContext.mode`.

Ambos ejes se consolidan en el rollup `DEUDA-A.md` (nota-identidad), no categoría-a-categoría.

---

## 1. Tabla por finding (grid del tracker · A1-A8 · B1-B11 · C1-C9 · D1-D4 · E1-E3 · F1-F8 · G1-G6 · H1-H5 = **54 filas**)

> Los findings-resumen `FIND-PLAN1..14` + `FIND-PLAN-APPROVAL-CONTRACT` = **capa de remediación** que reagrupa celdas
> del grid (PLAN1→A6/B11, PLAN2→B4, PLAN3→E1-E3, PLAN4→A4/C5, PLAN5→F7, PLAN6→F8, PLAN7→C7, PLAN8→G1/G2, PLAN9→D3/F6,
> PLAN10→D1/D2, PLAN11→B6/B8, PLAN12→F4, PLAN13→H3, PLAN14→A7, APPROVAL→H4); los `PlR1-14` = §Plan desarrollado (6
> campos L05) en el tracker — se **referencian** para la cara-base y se desarrolla la cara-integrador simétrica aquí
> (§2.5). **No se re-cuentan** (patrón 06/10/04/13/15).

### A · `EnterPlanModeTool` (`EnterPlanModeTool.ts`+`prompt.ts` vs `tools/native/plan_mode.py`)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| A1 | nombre `EnterPlanMode`, sin params | núcleo | BATTERY | `EnterPlanModeTool` (`battery_plan`) | — | ✅ `input_schema` vacío (plan_mode.py:30) |
| A2 | `isReadOnly`/`isConcurrencySafe` | núcleo | T1-CONTRATO + BATTERY | flags `ToolProtocol` (10/01) · `battery_plan` | — | 🔀 equiv.: `category=SYSTEM`+`requires_permission=False`+`safe_for_background=False` (plan_mode.py:31-33) |
| A3 | guard root-only (`if agentId throw`) | núcleo | BATTERY | `EnterPlanMode.execute` guard | — | ✅ **mejora**: veta por `ctx.is_subagent` (:40), discriminador correcto |
| A4 | `call`: `handlePlanModeTransition`+`setMode 'plan'`+`prepareContextForPlanMode` | núcleo | **CORE-GAP** | **CG-PLAN-1** (`PermissionContext.mode`, =06·GAP-02) | ejecución | 🔀→❌: siembra flag `native['plan_mode']` (:46), NO modo de permiso; sin stripping/auto-classifier |
| A5 | `mapToolResult`: reminder 6-pasos (o corto si interview) | núcleo | BATTERY | `battery_plan` (rama interview=CG-PLAN-9) | — | 🟡 `output` fijo 3 líneas (plan_mode.py:52-58), sin rama interview |
| A6 | `prompt()` = guía extensa "cuándo usar plan mode" | núcleo | **CORE-GAP** | **CG-PLAN-6** (contrato `prompt()` tool) | — | ❌ **FIND-PLAN1**: sólo `description` 1 línea (:26-29) |
| A7 | `shouldDefer:true`+`searchHint` (tool diferida) | núcleo | **CORE-GAP**/🔀 | **CG-PLAN-11** (deferral, 09) | — | 🔀 **FIND-PLAN14**: sin atributo `deferred`→siempre anunciada |
| A8 | `isEnabled=false` con `--channels` KAIROS | cáscara-CLI | CLI-ONLY/⛔ | integrador (channels) | — | ⛔ front/remote (abierto→confirmado) |

### B · `ExitPlanModeTool` (`ExitPlanModeV2Tool.ts`+`prompt.ts` vs `plan_mode.py`)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| B1 | nombre `ExitPlanMode`, schema vacío, plan de disco | núcleo | BATTERY | `ExitPlanModeTool` | persistencia | ✅ plan vía `get_plan` (plan_mode.py:79), sin arg |
| B2 | `_sdkInputSchema` inyecta plan/planFilePath + `allowedPrompts` | núcleo/producto | BATTERY + ⛔(classifier ant) | `battery_plan` / ⛔ | — | 🟡 sin inyección SDK, sin allowedPrompts |
| B3 | `requiresUserInteraction()`→detiene turno para aprobación | núcleo | T1-CONTRATO + BATTERY | `ToolResult.ends_turn` (10/01) | — | ✅ `ends_turn=True` (plan_mode.py:106), mismo primitivo que AskUserQuestion |
| B4 | `validateInput`: rechaza si `mode!=='plan'` | núcleo | **CORE-GAP** | **CG-PLAN-7** (guard mode-activo) | ejecución | 🟡 **FIND-PLAN2**: guard sólo por ausencia de plan-file (:80), no verifica plan_mode activo |
| B5 | `checkPermissions`: no-teammate→`ask` "Exit plan mode?" | cáscara/producto | T3-INTEGRADOR | **OI-PLAN-A** (aprobación) | — | 🔀 aprobación = front/BFF vía `ends_turn` |
| B6 | `call`: escribe plan + snapshot + restaura `prePlanMode` + auto-mode fallback | núcleo | **CORE-GAP** + BATTERY | **CG-PLAN-10**/CG-PLAN-1 (restore-mode) | ejecución | 🟡 **FIND-PLAN11**: saca flag, cachea plan (:88-94); sin restaurar modo previo, sin snapshot, sin auto-mode |
| B7 | teammate `isPlanModeRequired`→mailbox del líder | cáscara | T3-INTEGRADOR/⛔ | integrador (teams→05) | — | ⛔ teams |
| B8 | `mapToolResult`: ramas teammate/`isAgent`/empty/teamHint/label-"edited" | núcleo | **CORE-GAP** + BATTERY | **CG-PLAN-10** | — | 🟡 **FIND-PLAN11**: `output` plano "Plan submitted…" (:99) |
| B9 | one-shot de salida (`plan_mode_exit` attachment vía flag) | núcleo | T2-BASE-MECANISMO + BATTERY | `provider._render_exit_reminder` | — | ✅ pop `exit_pending` UNA vez (provider:160-163) |
| B10 | `plan_mode_exit` canónico **sólo referencia el path** | núcleo | BATTERY | `provider` (mejora) | — | 🔀 **enriquecido**: runtime inlinea el plan aprobado (provider:112-124) |
| B11 | `prompt()` = `EXIT_PLAN_MODE_V2_TOOL_PROMPT` (cuándo/cómo) | núcleo | **CORE-GAP** | **CG-PLAN-6** | — | 🟡 **FIND-PLAN1** (cara Exit): `description` mecánica (:65-68), sin guía |

### C · plan-file (`plans.ts`/`filesystem.ts` vs `plan_file.py`)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| C1 | `getPlanFilePath` root/subagente | núcleo | BATTERY | `plan_file.get_plan_file_path` | persistencia | ✅ `/plans/plan.md` / `plan-agent-{id}.md` (plan_file.py:48-55) |
| C2 | `getPlan` readFileSync, ENOENT→null | núcleo | BATTERY + **CORE-GAP** | `plan_file.get_plan` + **CG-PLAN-3** (`ctx.storage`, 15) | persistencia | ✅ concepto (:80-94) PERO **INERTE**: `ctx.storage` nunca ligado (§0.1c) |
| C3 | word-slug per-sesión + retry-colisión + cache | núcleo | 🔀/BATTERY | `plan_file` (token fijo) | persistencia | 🔀 **deliberado** L10: MinIO blob per-sesión → token FIJO, unicidad por namespace |
| C4 | `getPlansDirectory`: `settings.plansDirectory` override | núcleo/producto | T3-INTEGRADOR | **OI-PLAN-C** (`ctx.storage`/`PathStorage`) | persistencia | 🔀 prefijo `/plans` mapeado por el integrador |
| C5 | `isSessionPlanFile` = **exención del candado** | núcleo | **CORE-GAP** | **CG-PLAN-1** (predicado de exención, 06·GAP-02) | persistencia | 🟡 **FIND-PLAN4**: portado (:58-63) pero **0 consumidores prod** → candado no forzado |
| C6 | `copyPlanForResume` + recuperación snapshot | núcleo | 🔀/⛔ | ⛔ (MinIO durable) | persistencia | 🔀 re-lee blob; recovery-de-transcript N/A |
| C7 | `copyPlanForFork`: nuevo slug + copia contenido | núcleo | **CORE-GAP** | **CG-PLAN-5** (05·fork) | ejecución | ❌ **FIND-PLAN7**: fork usa path propio pero NO hereda plan del padre |
| C8 | `recoverPlanFromMessages` (3 fuentes) | núcleo | 🔀 | ⛔ (MinIO durable, N/A) | — | 🔀 durable → N/A |
| C9 | `persistFileSnapshotIfRemote` | núcleo | 🔀 | ⛔ (MinIO durable, N/A) | persistencia | 🔀 durable → N/A |

### D · `planModeV2.ts` (conteos + interview + pewter)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| D1 | `getPlanModeV2AgentCount` (Plan): 1-3 por tier | núcleo/producto | **CORE-GAP** + T3 | **CG-PLAN-10** (inyectar count) + integrador (tier) | — | 🟡 **FIND-PLAN10**: reminder genérico "agent(s)" (provider:66) |
| D2 | `getPlanModeV2ExploreAgentCount`: default 3 | núcleo/producto | **CORE-GAP** + T3 | **CG-PLAN-10** | — | 🟡 **FIND-PLAN10** |
| D3 | `isPlanModeInterviewPhaseEnabled` → workflow iterativo | núcleo | **CORE-GAP** | **CG-PLAN-9** (interview) | — | ❌ **FIND-PLAN9**: sólo el 5-fases (provider:45-84) |
| D4 | `getPewterLedgerVariant` (A/B Phase-4) | producto | ⛔ | ⛔ (experimento) | — | ⛔ texto Phase-4 único (≈control) |

### E · Agentes built-in `Plan`/`Explore` (`planAgent.ts`/`exploreAgent.ts` vs `execution/agents.py`)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| E1 | `PLAN_AGENT`: read-only, `disallowed=[Agent,ExitPlanMode,Edit,Write,NotebookEdit]`, model inherit | núcleo | **CORE-GAP** + T3 | **CG-PLAN-2** (`AgentDefinition` built-in) + **OI-PLAN-B** | ejecución | ❌ **FIND-PLAN3**: no registrado (`agents.py` sin tabla built-ins, 1→66) |
| E2 | `EXPLORE_AGENT`: read-only, model haiku/inherit | núcleo | **CORE-GAP** + T3 | **CG-PLAN-2** (cross 05/10) | ejecución | ❌ **FIND-PLAN3** |
| E3 | reminder 5-fases **referencia** estos `subagent_type` | núcleo | **CORE-GAP** | **CG-PLAN-2** (el cableado) | — | ❌ **FIND-PLAN3** (gap MAYOR): `agent_resolver=None`→fork genérico (runtime:342-353) → tipos no resuelven, no read-only → instrucción core letra muerta |

### F · Instrucciones (attachments) — `messages.ts` vs `PlanModeProvider`
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| F1 | `getPlanModeV2Instructions` (full 5-fases) | núcleo | T2-BASE-MECANISMO + BATTERY | `provider._render_plan_full` | — | 🟡 reproduce 5 fases (provider:45-84), sin agentCount/pewter/NOTE (CG-PLAN-8/10) |
| F2 | `planFileInfo` (existe→Edit/no→write) | núcleo | BATTERY | `provider._plan_file_info` | persistencia | ✅ (provider:33-42) |
| F3 | `getPlanModeV2SparseInstructions` | núcleo | BATTERY | `provider._render_plan_sparse` | — | ✅ (provider:87-96) |
| F4 | `getPlanModeV2SubAgentInstructions`: read-only + **su plan-file path** | núcleo | **CORE-GAP** | **CG-PLAN-10** (path subagente) | persistencia | 🟡 **FIND-PLAN12**: genérico sin plan-file path (provider:99-109) |
| F5 | `plan_mode_exit` attachment | núcleo | BATTERY | `provider._render_exit_reminder` | — | ✅/🔀-enriquecido (ver B9/B10) |
| F6 | `getPlanModeInterviewInstructions` (iterativo) | núcleo | **CORE-GAP** | **CG-PLAN-9** | — | ❌ **FIND-PLAN9** |
| F7 | `plan_mode_reentry` attachment (fresh/continúa) | núcleo | **CORE-GAP** | **CG-PLAN-9** (reentry) | — | ❌ **FIND-PLAN5**: re-entrar sólo resetea `full_shown`→re-emite 5-fases |
| F8 | `plan_file_reference` (preserva plan **a través de compactación**) | núcleo | **CORE-GAP** | **CG-PLAN-4** (motor-compact 01/02) | — | ❌ **FIND-PLAN6**: `compact_context`==[] (provider:165-168) |

### G · Cadencia de emisión — `attachments.ts`/`state.ts` vs loop `_inject_recall`
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| G1 | throttle `TURNS_BETWEEN_ATTACHMENTS=5` (turnos **humanos**) | núcleo | **CORE-GAP** | **CG-PLAN-8** (throttle + human-turn count en ctx) | — | 🔀 **FIND-PLAN8**: emite cada iteración; el dedup del loop (agent_loop:121-130) suprime el sparse repetido → ruido menor de lo enunciado, pero sin throttle por turnos-humanos |
| G2 | full/sparse: full cada 5ª adjunción | núcleo | **CORE-GAP** | **CG-PLAN-8** | — | 🔀 **FIND-PLAN8**: full UNA vez, luego sparse |
| G3 | reset ciclo full/sparse en re-entrada | núcleo | BATTERY | `provider` (`plan_mode_full_shown` reset) | — | ✅ reset en enter/exit (plan_mode.py:48/90) |
| G4 | `handlePlanModeTransition` to-plan/from-plan | núcleo | BATTERY | Enter/ExitPlanMode `modifier` | ejecución | ✅ comportamiento (estructura 🔀): Enter siembra/resetea, Exit saca/arma |
| G5 | flags `hasExitedPlanMode`/`needsPlanModeExitAttachment` | núcleo | BATTERY | `plan_file` native keys | ejecución | ✅ `plan_mode_exit_pending` (plan_file.py:25) |
| G6 | exit one-shot guardado, excluyente con plan_mode | núcleo | BATTERY | `provider.active_context` (exclusividad) | — | ✅ Exit hace pop+arma en el mismo turno (provider:150-163) |

### H · Front/UI/remoto (⛔ core — abiertos y confirmados, L02/L07)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| H1 | `/plan` toggle/mostrar/open-editor | cáscara-CLI | CLI-ONLY/INTERFAZ | **OI-PLAN-D** | — | ⛔ afordancia del front/BFF |
| H2 | `/ultraplan` (ant-only): multi-agente CCR remoto + teleport | cáscara-CLI | CLI-ONLY + ⛔(remote) | **OI-PLAN-D** / remote-tasks | — | ⛔ satélite entero de remote |
| H3 | `EnterPlanModePermissionRequest`: aprobar para ENTRAR | cáscara | T3-INTEGRADOR | **OI-PLAN-A** (permiso-entrar) | — | ⛔ **FIND-PLAN13**: runtime entra sin aprobar (`requires_permission=False`) |
| H4 | `ExitPlanModePermissionRequest` (768 LOC): modo-resultante / clear-context-and-implement / feedback / auto-name-session | cáscara | T3-INTEGRADOR | **OI-PLAN-A** (contrato de aprobación) | — | ⛔ **FIND-PLAN-APPROVAL-CONTRACT** |
| H5 | `PlanApprovalMessage`/`UserPlanMessage`/`RejectedPlanMessage` | cáscara-CLI | CLI-ONLY/INTERFAZ | **OI-PLAN-D** | — | ⛔ renderers ink |

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica (nombre · productor invoca · consumidor implementa)
- **`CapabilityProvider`** (T2-COSTURA, home 12/general, **NO nuevo de 14**) — el seam por el que el plan enchufa.
  Productor: `PlanModeProvider` (contexto puro, `tools()==[]`/`catalog()==[]`, provider:136-140). Consumido per-turno
  por el manager (`active_context` manager:98-102) + el loop (`_inject_recall` agent_loop:218). Verificado 1→EOF.
- **`PermissionContext.mode` + candado de plan mode** (T2-COSTURA/T1, **UNIFICADO con 06·CG-HOOK-8/GAP-02**) — el modo
  de permiso que deniega writes ≠ plan-file. Productor: el gate PreToolUse del loop (agent_loop:301) / el dispatcher.
  Consumidor: `PermissionContext` (hoy sin `mode`) + `is_session_plan_file` (el predicado de exención, hoy sin
  consumidor). **Keystone (CG-PLAN-1).** Cruza 06/09/03.
- **`StorageContract` (`ctx.storage`)** (T2-COSTURA, home 15) — el plan-file cuelga de aquí. Productor: `plan_file.
  get_plan`/`plan_file_exists`/`ExitPlanMode.execute`. Consumidor: el runtime que liga `ctx.storage` (**hoy NO lo
  liga**, §0.1c). CG-PLAN-3 = cara-14 del cabo 15·OI-STOR-C.
- **`AgentDefinitionResolver` + AgentDefinition built-in `Explore`/`Plan`** (T2-COSTURA home 05 + defs battery) — el
  workflow de 5 fases las nombra. Productor: el reminder (provider:61-93). Consumidor: `runtime._run_loop:342-353`
  (resuelve por `agent_resolver`, hoy None → fork genérico). CG-PLAN-2.
- **`ToolResult.context_modifier`/`ends_turn`** (T1-CONTRATO, home 10·§J/01) — Enter/ExitPlanMode las usan
  (plan_mode.py:59/101/106); el loop las aplica (agent_loop:332-339). Su NO-declaración en `ToolResult` = DEUDA-B ya
  homed en 10.
- **deferral (`DeferredToolStrategy`)** (T2-COSTURA home 09) — FIND-PLAN14 (A7). Productor: `_resolve_deferred_strategy`
  (agent_loop:132-150). Consumidor: atributo `deferred` de las tools (hoy ausente en Enter/ExitPlanMode).
- **human-turn count en `ToolUseContext`** (T1-CONTRATO, extensión NUEVA) — lo requiere CG-PLAN-8 (throttle por turnos
  HUMANOS, no iteraciones). Hoy sólo hay `ctx.turn_count` (iteraciones del loop, agent_loop:189), no turnos-humanos.

### 2.2 Batteries que alimenta
- **`battery_plan`** — el plan-mode concreto, componible (catálogo → A3.CAT): `PlanModeProvider` (full/sparse/subagent/
  exit + reentry/interview CG-PLAN-9) + `EnterPlanMode`/`ExitPlanMode` (con `prompt()` CG-PLAN-6, guard CG-PLAN-7,
  deferral CG-PLAN-11, tool_result enriquecido CG-PLAN-10) + `plan_file.py` (token + get_plan, ligado a `ctx.storage`
  CG-PLAN-3) + cadencia (CG-PLAN-8). Su incompletitud = los CORE-GAPs §2.3, NO gaps del base (L10).
- **`battery_builtin_agents`** (o sub-módulo de `battery_plan`) — las `AgentDefinition` `Explore`/`Plan` read-only
  (CG-PLAN-2). Compartida con 05·execution (Explore/Plan son built-ins de agente, no exclusivos de plan mode). El
  integrador las inyecta vía `agent_resolver` (OI-PLAN-B). Decisión de empaquetado (¿parte de `battery_plan` o battery
  propia?) → A3.CAT.
- **Decisión de composición (§0.1b):** hoy `PlanModeProvider()` es INCONDICIONAL (factory:146). Si `battery_plan` es
  opt-in como MCP/skills/memory, el registro debe volverse condicional (`if plan enabled`). Si el plan es capability
  nativa siempre-presente del base, se queda. → A3.CAT resuelve; no es bug (L10, no se cuenta como deuda).

### 2.3 CORE-GAPs (brechas A↔B reales que `battery_plan`+base DEBEN cerrar → rollup `DEUDA-A.md`)
Keystone-first. Los 6 campos L05 ya desarrollados en el tracker (PlR1-14); aquí se anclan con su ID de rollup:
- **CG-PLAN-1** (A4/C5, FIND-PLAN4, **keystone = GAP-02**) — **modo de permiso `plan` + candado read-only**: deniega
  toda tool no-readonly EXCEPTO write/edit cuyo target sea `is_session_plan_file(token)`. Hoy sólo texto del reminder
  (`PermissionContext` sin `mode`, exención sin consumidor). **UNIFICADO con 06·CG-HOOK-8** (`PermissionContext.mode`
  ausente) + **03·GAP-CTX2/B2** (hack `native['plan_mode']`) + **09·fs_env** (confinamiento write). Base = PlR4. El
  predicado `is_session_plan_file` = la costura de exención pre-cableada a medias que ESTE gap consume (cara-B, NO
  orphan nuevo — §2.4).
- **CG-PLAN-2** (E1-E3, FIND-PLAN3, **gap funcional MAYOR**) — **AgentDefinition built-in `Explore`/`Plan`
  read-only** (`disallowed=[Agent,ExitPlanMode,Edit,Write,NotebookEdit]`, model haiku/inherit) registradas y
  **resueltas** por el `agent_resolver`. Sin esto el reminder de 5 fases nombra tipos que no resuelven → fork genérico
  con TODAS las tools (runtime:350-353) → instrucción core no-funcional. Base = PlR3. Cross **05·agents** (defs) + **10**
  (read-only toolset) + **OI-PLAN-B** (integrador inyecta el resolver).
- **CG-PLAN-3** (C2, FIND-PLAN4-caraB, **cabo 15·OI-STOR-C**) — **ligar `ctx.storage`** para que el plan-file
  (`get_plan`/`plan_file_exists`) sea vivo. Hoy el runtime nunca liga `ctx.storage` (§0.1c) → `ExitPlanMode` siempre
  falla "No plan found" en standalone. Cross **15·CG-STOR-5** (frontera StorageContract) + **OI-PLAN-C**.
- **CG-PLAN-4** (F8, FIND-PLAN6) — **preservar el plan a través de la compactación** (re-inyectar `plan_file_reference`).
  `compact_context`==[] (provider:165-168) Y toda la cadena tiene 0 caller prod (§2.4) → cara aguas-abajo del **motor de
  compactación NO portado (01·CompactionProvider/02·GAP-L4)**. Base = PlR6.
- **CG-PLAN-5** (C7, FIND-PLAN7) — **fork hereda el plan del padre** (`copyPlanForFork`): al forkear, copiar el
  plan-file del padre al path `plan-agent-{child_id}`. Cross **05·fork**. Base = PlR7. nota-id ejecución.
- **CG-PLAN-6** (A6/B11, FIND-PLAN1) — **`prompt()` extenso en AMBAS tools** (distinto del `description` corto): Enter
  "cuándo usar plan mode" (criterios + GOOD/BAD); Exit "sólo planning no research" + "no uses AskUserQuestion para
  aprobar". Base = PlR1.
- **CG-PLAN-7** (B4, FIND-PLAN2) — **guard mode-activo en `ExitPlanMode`**: error "You are not in plan mode" si el modo
  no está activo, ANTES de leer el plan. Base = PlR2. (Se refina sobre CG-PLAN-1: leer `mode` en vez del flag.)
- **CG-PLAN-8** (G1/G2, FIND-PLAN8) — **cadencia con throttle 5-turnos-HUMANOS + full-cada-5ª**. Requiere exponer el
  conteo de turnos-humanos en el ctx (hoy sólo `ctx.turn_count`=iteraciones). Base = PlR8. (El dedup del loop mitiga
  el ruido pero no reproduce la política.)
- **CG-PLAN-9** (D3/F6/F7, FIND-PLAN9+FIND-PLAN5) — **variante interview-phase (iterativo) + attachment de reentry**
  bajo gate de config. Base = PlR5/PlR9.
- **CG-PLAN-10** (D1/D2/B6/B8/F4, FIND-PLAN10+11+12) — **enriquecimientos**: conteos de agentes por tier inyectados +
  tool_result de Exit rico (`isAgent`/`teamHint`/label-"edited"/restaurar-modo-previo) + plan-file path propio en el
  reminder de subagente. Base = PlR10/PlR11/PlR12. (La parte "restaurar modo previo" depende de CG-PLAN-1.)
- **CG-PLAN-11** (A7, FIND-PLAN14) — **diferir las plan-tools** (`deferred`+`search_hint`) si se decide alinear con el
  canónico (`shouldDefer`). Cross **09·deferral**. Base = PlR14. (🔀 si se decide always-available deliberado.)

### 2.4 DEUDA-B (higiene interna — L10, NO A↔B)
- **NINGUNA propia de 14** (anti-padding L10, como 04/13). Verificado leyendo B 1→EOF:
  - **`is_session_plan_file` sin consumidor** (plan_file.py:58-63) — **NO es B-orphan nuevo**: es la **costura de
    exención pre-cableada a medias del candado** (CG-PLAN-1). Su cableado es parte de la remediación de CG-PLAN-1 (el
    gate la consumirá para eximir el plan-file). Cara-B-interna de un ❌ A↔B ya conocido, como `LAT-HOOK1`/`to_llm` —
    **no se cuenta como deuda A↔B adicional** (L10/L11; ruling explícito del tracker 2ª-vuelta re-confirmado ESTE ciclo
    por grep 0-consumidores).
  - **`compact_context` sin consumidor prod** (provider:165-168, manager:104-108) — cara aguas-abajo del **motor de
    compactación NO portado** (01/02), transversal a TODOS los providers (plan/skills/mcp/memory). Grep ESTE ciclo:
    prod-callers = sólo agregadores (`manager.py:107`, `contracts/compaction.py:23`) + defs; **cero** caller de
    loop/runtime → **no se re-cuenta ni se registra como B-orphan** (L10, idéntico a 13·§2.4).
  - **`EXPLORE_AGENT_TYPE`/`PLAN_AGENT_TYPE`** (plan_file.py:44-45) — **NO orphans**: SÍ se consumen en el reminder
    (provider:61-93, verificado grep). Son el CONTRATO-con-integrador (stems que el `agent_resolver` debe registrar);
    su falta de resolución = CG-PLAN-2, no maquinaria muerta.
  - **Registro incondicional `[PlanModeProvider()]`** (factory:146) — decisión de composición (§0.1b/§2.2), no bug ni
    orphan. → A3.CAT.
  - Cero costuras latentes NUEVAS tipo `to_llm`/`LAT-*`.

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05/§1.1)

**Must-be universal (CONTRATO BASE COMÚN — obligación de TODO integrador con plan mode):**
- **OI-PLAN-A · Orquestar la aprobación del plan + el modo resultante + el permiso de ENTRAR.** Capacidad: `ExitPlanMode`
  cierra el turno (`ends_turn`, plan_mode.py:106) → el integrador presenta el plan, recoge aprobar/rechazar/feedback,
  **selecciona el modo de permiso resultante** (accept-edits/default/bypass/auto), opcionalmente **clear-context-and-
  implement** (regenera sesión + inyecta "Implement the following plan:" con transcript-hint/team-hint/feedback) y
  **auto-name-session-from-plan**; además pide **aprobación para ENTRAR** a plan mode (H3, el canónico sí pregunta).
  Costura: la frontera de turno (`ends_turn`) + `PermissionContext.mode` (CG-PLAN-1) + `user_input`/BFF. Firma
  (detalle simétrico): un contrato `PlanApprovalOutcome{approved, resulting_mode, feedback?, clear_context?,
  session_name?}` que el integrador produce y el runtime aplica sobre el ctx del turno siguiente. Realización:
  agentic_code = diálogo terminal (`ExitPlanModePermissionRequest` 768 LOC: opciones de modo, reject-con-imagen,
  auto-name); agentic_assistant = endpoint de aprobación front/BFF. Criterio: aprobar con "accept-edits" deja el
  turno siguiente con writes permitidos; rechazar re-inyecta el feedback en plan mode. (B5/H3/H4, FIND-PLAN13/
  APPROVAL-CONTRACT.)
- **OI-PLAN-B · Inyectar el `agent_resolver` con las defs `Explore`/`Plan`.** Capacidad: el workflow de 5 fases resuelve
  sus subagentes read-only. Costura: `RuntimeConfig.agent_resolver` (factory:117→237, `AgentDefinitionResolver`).
  Firma: `resolve("Explore"|"Plan") -> AgentDefinition(read_only, disallowed=[Agent,ExitPlanMode,Edit,Write,
  NotebookEdit], model=haiku|inherit)`. Realización: ambos integradores componen `battery_builtin_agents` y las
  registran; agentic_code = resolver estático local; agentic_assistant = catálogo per-tenant. Criterio: el resolver
  resuelve `"Explore"`/`"Plan"` y ambos son read-only (no exponen Edit/Write). **La battery provee las defs; el
  integrador las inyecta** (el runtime es genérico, NO posee el catálogo — verificado agents.py:1-12). (E1-E3.)
- **OI-PLAN-C · Backing de `ctx.storage` para el plan-file** (= aterrizaje de **15·OI-STOR-C**). Capacidad: el plan-file
  persiste y se re-lee. Costura: el runtime liga `ctx.storage` (StorageContract) — HOY NO lo hace (§0.1c) — + el
  integrador mapea el token `/plans/<name>` → blob/FS. Firma: `ctx.storage` = `StorageContract` que resuelve
  `real_path(token)`/`ensure_local(token)`. Realización: agentic_code = FS local `session_plans_dir` (`/plans/plan.md`);
  agentic_assistant = MinIO blob per-sesión vía `PathStorage`. Criterio: `write_file(/plans/plan.md)` en plan mode →
  `ExitPlanMode` lo lee y lo presenta. **Nota-identidad:** sanitizar el componente `agent_id` del token subagente
  (guard-path unificado 15·CG-STOR-3). (C2/C4/FIND-PLAN4-caraB.)

**Específicos (realización concreta de un integrador):**
- **OI-PLAN-D · Afordancias de interfaz** — `/plan` toggle/mostrar/open-editor (H1), `/ultraplan` multi-agente remoto
  (H2, ant-only, satélite de remote), renderers de plan (`PlanApprovalMessage`/`UserPlanMessage`/`RejectedPlanMessage`,
  H5). Realización: agentic_code = terminal (slash + ink); agentic_assistant = capa front. Criterio: `/plan` entra/sale
  de plan mode desde la UI; el plan aprobado se renderiza. (H1/H2/H5.)

**Cabos que aterrizan aquí (cerrados con destino):**
- **15·OI-STOR-C (`ctx.storage` inerte)** → **CG-PLAN-3 + OI-PLAN-C** (confirmado ESTE ciclo: runtime nunca liga
  `ctx.storage`, §0.1c).
- **06·CG-HOOK-8 / 01·GAP-02 (`PermissionContext.mode`)** → **UNIFICADO con CG-PLAN-1** (plan mode = el candado
  `mode='plan'`; el hack `native['plan_mode']` de 03·GAP-CTX2 es el mecanismo actual que CG-PLAN-1 reemplaza).
- **05·agents (Explore/Plan built-ins)** → **CG-PLAN-2** (defs) + **OI-PLAN-B** (inyección).
- **05·fork (`copyPlanForFork`)** → **CG-PLAN-5**.
- **01/02 motor-compactación** → **CG-PLAN-4** (F8).
- **10·D1/D2 (Enter/Exit `safe_for_background=False`, root-only)** → confirmado (plan_mode.py:33/75); tools no
  backgroundables, coherente con el filtro `list_available(mode="background")` (resolver:45-49).

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor:** De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda;
ninguna categoría se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar
—o colocado sin abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — una fila por finding (54 = A1-A8·8 + B1-B11·11 + C1-C9·9 + D1-D4·4 + E1-E3·3 + F1-F8·8 + G1-G6·6 + H1-H5·5)
| ID | TIER | destino | cara | evidencia | detalle | nota-id |
|---|---|---|---|---|---|---|
| A1 | BATTERY | EnterPlanModeTool | base | `plan_mode.py:30` 1→EOF | sí (§2.2) | — |
| A2 | T1-CONTRATO+BATTERY | ToolProtocol flags (10/01) | base | `plan_mode.py:31-33` | sí (§2.1) | — |
| A3 | BATTERY | Enter guard | base | `plan_mode.py:40` | sí (§2.2) | — |
| A4 | CORE-GAP | CG-PLAN-1 (06·GAP-02) | ambas | `plan_mode.py:46` + `permissions.py` 1→33 (sin `mode`) | sí (PlR4) | ejecución |
| A5 | BATTERY | battery_plan (interview) | base | `plan_mode.py:52-58` | sí (§2.3 CG-9) | — |
| A6 | CORE-GAP | CG-PLAN-6 | base | `plan_mode.py:26-29` | sí (PlR1) | — |
| A7 | CORE-GAP/🔀 | CG-PLAN-11 (09) | base | `plan_mode.py` 1→EOF (sin `deferred`) | sí (PlR14) | — |
| A8 | CLI-ONLY/⛔ | integrador (channels) | integrador | tracker-leído (abierto→⛔) | N/A (⛔) | — |
| B1 | BATTERY | ExitPlanModeTool | base | `plan_mode.py:72,79` | sí | persistencia |
| B2 | BATTERY+⛔ | battery_plan / ⛔ | ambas | tracker-leído | sí | — |
| B3 | T1-CONTRATO+BATTERY | ToolResult.ends_turn (10/01) | base | `plan_mode.py:106` + `agent_loop.py:338-339` | sí | — |
| B4 | CORE-GAP | CG-PLAN-7 | base | `plan_mode.py:80` | sí (PlR2) | ejecución |
| B5 | T3-INTEGRADOR | OI-PLAN-A | integrador | `plan_mode.py:106` (ends_turn) | sí (§2.5) | — |
| B6 | CORE-GAP+BATTERY | CG-PLAN-10/CG-PLAN-1 | ambas | `plan_mode.py:88-94` | sí (PlR11) | ejecución |
| B7 | T3-INTEGRADOR/⛔ | integrador (teams→05) | integrador | tracker-leído | N/A (⛔) | — |
| B8 | CORE-GAP+BATTERY | CG-PLAN-10 | base | `plan_mode.py:99` | sí (PlR11) | — |
| B9 | T2-BASE+BATTERY | provider._render_exit_reminder | base | `provider.py:160-163` 1→EOF | sí | — |
| B10 | BATTERY | provider (mejora) | base | `provider.py:112-124` | sí | — |
| B11 | CORE-GAP | CG-PLAN-6 | base | `plan_mode.py:65-68` | sí (PlR1) | — |
| C1 | BATTERY | plan_file.get_plan_file_path | base | `plan_file.py:48-55` 1→EOF | sí | persistencia |
| C2 | BATTERY+CORE-GAP | plan_file.get_plan + CG-PLAN-3 | ambas | `plan_file.py:80-94` + `runtime.py` 1→435 (sin ctx.storage) | sí (PlR6/OI-C) | persistencia |
| C3 | 🔀/BATTERY | plan_file (token fijo) | base | `plan_file.py:1-11,48-55` | sí (L10) | persistencia |
| C4 | T3-INTEGRADOR | OI-PLAN-C | integrador | `plan_file.py:8-11` | sí (§2.5) | persistencia |
| C5 | CORE-GAP | CG-PLAN-1 (exención) | ambas | `plan_file.py:58-63` + grep 0-consumidores | sí (PlR4) | persistencia |
| C6 | 🔀/⛔ | ⛔ (MinIO durable) | base | tracker-leído | N/A | persistencia |
| C7 | CORE-GAP | CG-PLAN-5 (05·fork) | base | `runtime.py:198-204` (fork sin copia plan) | sí (PlR7) | ejecución |
| C8 | 🔀 | ⛔ (durable N/A) | base | tracker-leído | N/A | — |
| C9 | 🔀 | ⛔ (durable N/A) | base | tracker-leído | N/A | persistencia |
| D1 | CORE-GAP+T3 | CG-PLAN-10 + integrador | ambas | `provider.py:66` | sí (PlR10) | — |
| D2 | CORE-GAP+T3 | CG-PLAN-10 | ambas | `provider.py:62` | sí (PlR10) | — |
| D3 | CORE-GAP | CG-PLAN-9 | base | `provider.py:45-84` (sólo 5-fases) | sí (PlR9) | — |
| D4 | ⛔ | ⛔ (experimento) | base | tracker-leído | N/A (⛔) | — |
| E1 | CORE-GAP+T3 | CG-PLAN-2 + OI-PLAN-B | ambas | `agents.py` 1→66 (sin tabla built-ins) | sí (PlR3) | ejecución |
| E2 | CORE-GAP+T3 | CG-PLAN-2 (05/10) | ambas | `agents.py` 1→66 | sí (PlR3) | ejecución |
| E3 | CORE-GAP | CG-PLAN-2 (cableado) | base | `runtime.py:342-353` (agent_resolver None→fork genérico) + grep `PLAN_AGENT_TYPE` sólo en reminder | sí (PlR3) | — |
| F1 | T2-BASE+BATTERY | provider._render_plan_full | base | `provider.py:45-84` + `agent_loop.py:212-218` 1→EOF | sí | — |
| F2 | BATTERY | provider._plan_file_info | base | `provider.py:33-42` | sí | persistencia |
| F3 | BATTERY | provider._render_plan_sparse | base | `provider.py:87-96` | sí | — |
| F4 | CORE-GAP | CG-PLAN-10 (path subagente) | base | `provider.py:99-109` | sí (PlR12) | persistencia |
| F5 | BATTERY | provider._render_exit_reminder | base | `provider.py:112-124` | sí | — |
| F6 | CORE-GAP | CG-PLAN-9 | base | `provider.py` 1→EOF (sin interview) | sí (PlR9) | — |
| F7 | CORE-GAP | CG-PLAN-9 (reentry) | base | `plan_mode.py:48` (sólo resetea full_shown) | sí (PlR5) | — |
| F8 | CORE-GAP | CG-PLAN-4 (motor-compact 01/02) | base | `provider.py:165-168` + grep compact_context 0-caller | sí (PlR6) | — |
| G1 | CORE-GAP | CG-PLAN-8 | base | `agent_loop.py:112-130,218` 1→EOF (dedup per-turno) | sí (PlR8) | — |
| G2 | CORE-GAP | CG-PLAN-8 | base | `provider.py:156-159` | sí (PlR8) | — |
| G3 | BATTERY | provider (full_shown reset) | base | `plan_mode.py:48,90` | sí | — |
| G4 | BATTERY | Enter/Exit modifier | base | `plan_mode.py:45-49,88-95` + `agent_loop.py:332-337` | sí | ejecución |
| G5 | BATTERY | plan_file native keys | base | `plan_file.py:20-34` | sí | ejecución |
| G6 | BATTERY | provider.active_context (exclusividad) | base | `provider.py:150-163` | sí | — |
| H1 | CLI-ONLY/INTERFAZ | OI-PLAN-D | integrador | tracker-leído (abierto→⛔) | sí (§2.5) | — |
| H2 | CLI-ONLY+⛔(remote) | OI-PLAN-D / remote | integrador | tracker-leído (abierto→⛔) | sí (§2.5) | — |
| H3 | T3-INTEGRADOR | OI-PLAN-A (permiso-entrar) | integrador | tracker-leído + `plan_mode.py:32` (requires_permission=False) | sí (§2.5) | — |
| H4 | T3-INTEGRADOR | OI-PLAN-A (contrato aprobación) | integrador | tracker-leído (768 LOC behavioral) | sí (§2.5) | — |
| H5 | CLI-ONLY/INTERFAZ | OI-PLAN-D | integrador | tracker-leído (abierto→⛔) | N/A (⛔) | — |

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../14-cap-plan.md`?** → **Sí**, 1→503: §Estado (VALIDADA gate-11), §alcance + ⛔-abiertos +
   recordatorio-de-alcance, tablas A-H, §Findings FIND-PLAN1-14+APPROVAL, §Plan PlR1-14, §Ledger de lectura + §Nota de
   honestidad + 4 preguntas, §Re-auditoría 2026-07-14, §Re-visita COMPLETITUD gate-11 (mini-ledger + honestidad + 4
   preguntas + VEREDICTO).
2. **¿Reconcilia el conteo?** findings-grid en `../14-cap-plan.md` = **54**; colocados = **54**; sin colocar = **0**.
   (A1-A8·8 + B1-B11·11 + C1-C9·9 + D1-D4·4 + E1-E3·3 + F1-F8·8 + G1-G6·6 + H1-H5·5 = 54. `FIND-PLAN1-14` +
   `APPROVAL-CONTRACT` + `PlR1-14` = capa de remediación referenciada, no re-contada — patrón 06/10/04/13/15.)
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ENSAMBLADOR (sin apoyarse en grep)?** → Ensambladores ABIERTOS
   1→EOF EN ESTE CICLO (no heredados del gate-11 2026-07-20):
   - **A4/C5/CG-PLAN-1 (candado=GAP-02)**: `contracts/permissions.py` **1→33 ÍNTEGRO** — `PermissionContext` sin campo
     `mode` (sólo allow_command/allow_session/deny); `plan_mode.py:46` siembra `native['plan_mode']` (flag, no modo).
     `is_session_plan_file` (plan_file.py:58-63) 0-consumidores (grep-de-ausencia legítimo).
   - **B9/F1/F3/G1 (provider per-turno)**: `capabilities/manager.py` **1→111 ÍNTEGRO** (`active_context:98-102`) +
     `loop/agent_loop.py` **1→352 ÍNTEGRO** (`_inject_recall:112-130,218` DENTRO del `for _turn in range(_MAX_TURNS):185`,
     dedup :121-130; `context_modifier`/`ends_turn` :332-339). `provider.py` 1→EOF.
   - **§0.1b PlanModeProvider incondicional + C2/CG-PLAN-3 (ctx.storage inerte) + E1-E3/CG-PLAN-2 (agent_resolver)**:
     `factory.py` **1→267 ÍNTEGRO** (`[PlanModeProvider()]` :146 incondicional vs MCP:148/skills:160/memory:166) +
     `execution/local/runtime.py` **1→435 ÍNTEGRO** (`_run_loop:306-416` liga presentation/exec_env/fs/git pero **cero
     `ctx.storage`**; `_build_child:198-218` fork sin copia de plan; `:342-353` `agent_resolver=None`→fork genérico
     TODAS-tools) + `execution/agents.py` **1→66 ÍNTEGRO** (sin tabla built-ins) + `capabilities/resolver.py` **1→82**
     (`list_available(mode="background")` :45-49) + `tools/factory.py` **1→75** (Enter/Exit registradas :47/49).
   - **CONTRATOS que la tesis apoya, abiertos 1→EOF en la 2ª iteración** (⚠ ver nota al pie de §3.3 — el 1er
     cierre NO los abrió): `capabilities/contracts.py` **1→76** (`CapabilityProvider` = catalog/tools/
     active_context/compact_context :66-69 + `system_prompt_section` **OPCIONAL vía getattr** :49-58 — funda §2.1 y
     añade §0.1d; `CapabilityActivation` :26-38 = LAT-CAP1 de 12, comprobado que **NO aterriza en 14**) ·
     `contracts/storage.py` **1→40** (`StorageContract` = `real_path`/`ensure_local`/`commit`/`teardown` :25-31 —
     funda la FIRMA de OI-PLAN-C, ahora verificada contra el contrato: `plan_file.py:75` llama `real_path` y `:91`
     `ensure_local`, exactamente los dos primeros métodos) · `context/tool_use.py` **1→70** (`storage: Any = None`
     :49 **sin tipar y sin default** frente a `fs` :52 **con default seguro** `ConfinedFilesystem` — asimetría que
     funda §0.1c: las tools de fichero SÍ operan por defecto y el plan-file NO; `turn_count:int` :43 = iteraciones,
     funda CG-PLAN-8; `AppState.native` :30 = el canal del hack, funda §0.2) · `tools/protocol.py` **1→61**
     (`ToolResult` :18-48 SIN `context_modifier`/`ends_turn` → confirma A2/B3 como gap T1 homed en 10·§J/01;
     `ToolProtocol` :51-61 sin `deferred` → confirma A7/CG-PLAN-11).
   - **grep-de-ausencia POR-TÉRMINO ESTE CICLO** (legítimo sólo para ausencia, L09): `is_session_plan_file` prod=0 ·
     `.mode` en permissions=0 · `.storage =` en runtime/loop=0 · `PlanModeProvider` registro=sólo factory:146 ·
     `compact_context` caller loop/runtime=0 (sólo agregadores) · `BUILTIN_AGENTS`=0 · `EXPLORE_AGENT_TYPE`/
     `PLAN_AGENT_TYPE` prod=sólo el reminder (provider:61-93). Confirmado por ausencia+lectura, no heredado.
4. **¿La cara integrador quedó al MISMO detalle que la base?** → **Sí.** OI-PLAN-A (aprobación + modo-resultante +
   permiso-entrar, con contrato `PlanApprovalOutcome` + realización code/assistant) · OI-PLAN-B (inyectar agent_resolver
   con defs Explore/Plan) · OI-PLAN-C (backing `ctx.storage`, = 15·OI-STOR-C) · OI-PLAN-D (afordancias `/plan`/`/ultraplan`/
   renderers), cada uno con capacidad·costura·firma·realización·criterio (§2.5). Ningún "→ integrador" a secas.
5. **¿Doble filo (L10)?** → **Sí, calibrado.** (a) Ningún ❌ disfrazado de 🔀: FIND-PLAN3 (agentes no resuelven, ❌
   mayor)/FIND-PLAN4 (candado no forzado, ❌ = GAP-02)/FIND-PLAN6 (compact)/FIND-PLAN7 (fork) son CORE-GAP honestos.
   (b) Sin deuda inflada: token-fijo vs word-slug (C3), no-override plansDirectory (C4), copyPlanForResume/recoverFrom
   Messages/persistSnapshot (C6/C8/C9) = **🔀 deliberado** (MinIO blob durable, mismo efecto, otra arquitectura) — NO ❌;
   B10 (inline plan) = 🔀 mejora; aprobación/`/plan`/renderers = T3/CLI-ONLY (integrador), no deuda del base; pewter/
   KAIROS-channels = ⛔ (experimento/producto). `is_session_plan_file` = cara-B de CG-PLAN-1 (no orphan);
   `compact_context` = cara del motor-compact ausente (01/02, no B-orphan); registro incondicional = decisión de
   composición (A3.CAT, no bug). **Cero DEUDA-B propia** (como 04/13).

### 3.3 §Honestidad
- **Leídos 1→EOF EN ESTE CICLO** (L08/L09, no heredados del gate-11): B = `capabilities/plan/{plan_file.py 108,
  provider.py 171, __init__.py 3}` + `tools/native/plan_mode.py 107`; **ENSAMBLADOR** = `factory.py` (267),
  `capabilities/manager.py` (111), `loop/agent_loop.py` (352), `execution/local/runtime.py` (435), `execution/agents.py`
  (66), `capabilities/resolver.py` (82), `contracts/permissions.py` (33), `tools/factory.py` (75) + grep-de-ausencia
  por-término (Q3); **CONTRATOS (2ª iteración)** = `capabilities/contracts.py` (76), `contracts/storage.py` (40),
  `context/tool_use.py` (70), `tools/protocol.py` (61).
- **⚠ CIERRE EN 2 ITERACIONES (gate auto-adversarial "¿EoF en todos?", reproche recurrente = 04/11/12 — 4ª vez).**
  El 1er cierre **SOBRE-DECLARÓ Q3 y además se auto-acreditó "1 iteración / lección aplicada preventivamente"**, lo
  cual era **falso**: abrí los 8 ensambladores de EJECUCIÓN pero **no** los 4 CONTRATOS sobre los que descansa la
  clasificación — `capabilities/contracts.py` (el seam `CapabilityProvider`, eje de la tesis §2.1, **inferido del
  consumo** = fallo L08 idéntico a 12/11), `contracts/storage.py` (la FIRMA de OI-PLAN-C afirmada sin abrir el
  contrato), `context/tool_use.py` (donde viven `storage`/`turn_count`/`native`, que fundan §0.1c/§0.2/CG-PLAN-8) y
  `tools/protocol.py` (donde A2/B3/A7 colocan gaps T1). Abiertos 1→EOF al reproche: **CERO cambios de clasificación**
  —los 54 se sostienen— pero eso sólo se sabe DESPUÉS de abrirlos, y aparecieron **dos fundamentos nuevos** que la
  inferencia no daba (§0.1d `system_prompt_section` opcional no usada por `battery_plan`; la asimetría
  `storage: Any = None` vs `fs` con default seguro, que es la razón mecánica de §0.1c). **La auto-acreditación de
  rigor es en sí misma un tell de defensividad: no se declara "preventivo" lo que no se ha comprobado abriendo.**
- **A canónico NO re-leído esta ronda** (honesto): el tracker documenta la re-lectura 1→EOF de los 7 archivos A de
  código + los 4 satélites (tramos-de-plan) en su gate-11 (2026-07-20), tras la re-audit 2026-07-14 con auto-corrección
  adversarial (drift de anclas cazado). Esta SEPARACION es MEJORA DE FORMA sobre findings ya establecidos, no una 3ª
  validación A↔B. La re-verificación de este ciclo se centró en **B + ENSAMBLADOR** (donde vive la clasificación
  TIER/destino/cableado, que es lo nuevo de la SEPARACION).
- **Cero costuras latentes NUEVAS** tipo `LAT-*`: `is_session_plan_file`-sin-consumidor = cara-B de CG-PLAN-1 (no
  orphan); `compact_context`-sin-caller = cara del motor-compact ausente (01/02, transversal); `EXPLORE/PLAN_AGENT_TYPE`
  SÍ consumidos (reminder). **Cero DEUDA-B propia** de 14 (anti-padding L10).
- **NO verificado (honesto):** el diseño fino de `PermissionContext.mode` + el gate del candado = **06·GAP-02/CG-HOOK-8**
  (aquí sólo la cara plan-mode + el predicado de exención); el ligado de `ctx.storage` = **15·CG-STOR-5/OI-STOR-C** +
  el runtime (Fase C/E); las defs built-in Explore/Plan + su resolución = **05·agents** + OI-PLAN-B; `copyPlanForFork`
  = **05·fork**; la preservación tras compactación = **01/02** motor-compact; el conteo de turnos-HUMANOS en el ctx
  (CG-PLAN-8) = extensión T1 a diseñar; el catálogo definitivo `battery_plan`/`battery_builtin_agents` + la decisión
  incondicional-vs-opt-in = **A3.CAT**. Suite NO re-ejecutada (fase de diseño, sin cambio de código — PLAN §1.6; el
  tracker reporta 6 passing/6 xfail de `test_cap_plan_homologation.py` intactos, targets PlR xfail siguen rojos = gaps
  vivos).

### 3.4 VEREDICTO
**✅ NADA PENDIENTE → A3·17·voice — GANADO EN 2 ITERACIONES** (el 1er cierre tenía **Q3 = ⛔**: contratos afirmados
sin abrir; ver ⚠ en §3.3. El veredicto ✅ es válido sólo con los 4 contratos ya abiertos 1→EOF).
Conteo 54=54=0. Las 5 preguntas: sí honestas (Q3 con ENSAMBLADOR `factory`/`manager`/`agent_loop`/`runtime`/`agents`/
`resolver`/`permissions`/`tools-factory` **+ CONTRATOS `capabilities/contracts`/`contracts/storage`/`context/tool_use`/
`tools/protocol`** 1→EOF ESTE ciclo + grep-de-ausencia por-término; Q5 doble-filo calibrado).
CORE-GAPs anclados con destino: CG-PLAN-1 (candado=**GAP-02**, keystone)→PlR4+06/09/03 · CG-PLAN-2 (agentes, gap
MAYOR)→PlR3+05/10+OI-B · CG-PLAN-3 (ctx.storage, **cabo 15·OI-STOR-C**)→PlR6+15+OI-C · CG-PLAN-4 (compact)→PlR6+01/02 ·
CG-PLAN-5 (fork)→PlR7+05 · CG-PLAN-6 (prompt)→PlR1 · CG-PLAN-7 (guard)→PlR2 · CG-PLAN-8 (cadencia)→PlR8 · CG-PLAN-9
(interview/reentry)→PlR5/9 · CG-PLAN-10 (enriquecimientos)→PlR10/11/12 · CG-PLAN-11 (deferral)→PlR14+09. Batteries
`battery_plan` + `battery_builtin_agents`→A3.CAT; DEUDA-B propia = ninguna (L10); OI-PLAN-A..D→`00-INTEGRADORES`.
Cabos 15·OI-STOR-C (ctx.storage inerte) + 06·GAP-02 (candado) + 05·agents/fork + 01/02·compact cerrados con destino.
Ningún pendiente de verificación (L04).
