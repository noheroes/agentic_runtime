# 14 · capabilities/plan

> **Estado: VALIDADA (2ª vuelta · gate 11 / L09 de ENTRADA) · 2026-07-20** — lado B (3 `plan/*.py` +
> `tools/native/plan_mode.py`) **y ENSAMBLADOR** (`factory.py` 267 + `manager.py` 111 + `agent_loop.py:85-234`
> + `execution/agents.py` 66 + `runtime.py:336-365`) leídos 1→EOF; lado A in-scope **RE-LEÍDO 1→EOF esta ronda**
> (los 7 archivos de código, citas exactas = evidencia L11). **1 discrepancia real** (FIND-PLAN1 sub-enumerado:
> el `prompt()` ausente aplica a AMBAS tools, el doc sólo capturó EnterPlanMode) + **2 precisiones de mecanismo**
> (FIND-PLAN8 dedup; FIND-PLAN6 cross-ref 13); **cero cambios de estado**; **código intacto**; tests no
> re-ejecutados (sin cambio de código). Ver bloque "Re-visita de COMPLETITUD" al pie.

Homologación de `capabilities/plan/{plan_file.py, provider.py}` + `tools/native/plan_mode.py`
(`EnterPlanModeTool`, `ExitPlanModeTool`) contra el subsistema de plan mode canónico:

- `tools/EnterPlanModeTool/{EnterPlanModeTool.ts, constants.ts, prompt.ts}`
- `tools/ExitPlanModeTool/{ExitPlanModeV2Tool.ts, constants.ts, prompt.ts}`
- `utils/plans.ts` (storage del plan-file: slug, dir, get/getPath, resume/fork/recover, snapshot)
- `utils/planModeV2.ts` (agent counts, interview-phase gate, pewter A/B)
- `tools/AgentTool/built-in/{planAgent.ts, exploreAgent.ts}` (agentes `Plan`/`Explore`)
- `utils/messages.ts` (attachments de instrucciones: `getPlanModeV2Instructions` full/sparse/subagent,
  interview, `plan_mode_exit`, `plan_mode_reentry`, `plan_file_reference`, Phase-4 variants)
- `utils/attachments.ts` (cadencia de emisión: throttle 5 turnos, full-cada-5ª, reentry, exit one-shot)
- `bootstrap/state.ts` (`handlePlanModeTransition`, flags `hasExitedPlanMode`/`needsPlanModeExitAttachment`, `planSlugCache`)
- `services/compact/compact.ts` (`createPlanAttachmentIfNeeded`, `createPlanModeAttachmentIfNeeded`)
- **⛔-abiertos (UI/front/remote, confirmados tras leer)**: `commands/plan/plan.tsx` (slash `/plan`),
  `commands/ultraplan.tsx` (CCR remoto, ant-only), `components/permissions/{Enter,Exit}PlanModePermissionRequest`,
  `components/messages/{PlanApprovalMessage, UserPlanMessage, UserToolResultMessage/RejectedPlanMessage}`.

> **Recordatorio de alcance**: el runtime opera con usuarios/sesiones y un **front** (BFF/KrakenD); UI/TUI/ink,
> slash-commands y el diálogo de aprobación son **de la capa front**, no del core. Ahí la homologación es **de
> comportamiento/contrato** (qué debe ofrecer el front), no de forma. El plan-file vive en MinIO (blob per-sesión)
> vía `StorageContract`, no en `~/.claude/plans/` local.

## Leyenda: ✅ homologado · 🟡 parcial · 🔀 diferente (deliberado o a revisar) · ❌ no portado · ⛔ N/A core

---

## Tabla feature-by-feature

### A · `EnterPlanModeTool` (canónico `EnterPlanModeTool.ts` + `prompt.ts`)

| # | Feature canónica | Runtime | Estado |
|---|---|---|---|
| A1 | nombre `EnterPlanMode`, sin parámetros | idem (`input_schema` vacío) | ✅ |
| A2 | `isReadOnly:true`, `isConcurrencySafe:true` | `category=SYSTEM`, `requires_permission=False`, `safe_for_background=False` | 🔀 (equiv. comportamiento) |
| A3 | guard root-only: `if(context.agentId) throw` | veta con `ctx.is_subagent` (no `agent_id`) | ✅ **mejora** (el root también recibe `agent_id` como identidad; `is_subagent` es el discriminador correcto — regresión ya arreglada, `test_enter_plan_mode_guard`) |
| A4 | `call`: `handlePlanModeTransition` + `setMode 'plan'` vía `applyPermissionUpdate(prepareContextForPlanMode(...))` | `modifier` siembra `native['plan_mode']=True` + resetea `plan_mode_full_shown` | 🔀 (usa flag `native` en vez de `toolPermissionContext.mode`; **no** ejecuta `prepareContextForPlanMode` — stripping/auto-classifier = B-02) |
| A5 | `mapToolResultToToolResultBlockParam`: reminder de 6 pasos (o corto si interview-phase) | `output` fijo de 3 líneas ("Entered plan mode… DO NOT write… ExitPlanMode") | 🟡 (sin rama interview-phase) |
| A6 | `prompt()` = `getEnterPlanModeToolPrompt` (external/ant): guía extensa "cuándo usar plan mode" (7 criterios, ejemplos GOOD/BAD) | `description` de una línea | ❌ **FIND-PLAN1** |
| A7 | `shouldDefer:true` + `searchHint` (tool diferida, descubrible) | no marca `deferred` → siempre anunciada | 🔀 **FIND-PLAN14** |
| A8 | `isEnabled=false` con `--channels` KAIROS (plan mode sin terminal = trampa) | sin concepto de channels | ⛔ (front/remote) |

### B · `ExitPlanModeTool` (canónico `ExitPlanModeV2Tool.ts` + `prompt.ts`)

| # | Feature canónica | Runtime | Estado |
|---|---|---|---|
| B1 | nombre `ExitPlanMode`; schema interno vacío, plan leído de disco (no arg `plan`) | idem (`input_schema` vacío, plan vía `get_plan`) | ✅ |
| B2 | `_sdkInputSchema` inyecta `plan`/`planFilePath` (visible a SDK/hooks); `allowedPrompts` (ant classifier) | sin inyección SDK, sin `allowedPrompts` | 🟡 (allowedPrompts=B-02/classifier ant) |
| B3 | `requiresUserInteraction()`: no-teammate → true (detiene turno para aprobación) | `result.ends_turn=True` | ✅ (mismo primitivo que AskUserQuestion) |
| B4 | `validateInput`: rechaza si `mode!=='plan'` ("You are not in plan mode…") + analítica; teammate bypass | guard sólo por **ausencia de plan-file**; NO verifica que plan_mode esté activo | 🟡 **FIND-PLAN2** |
| B5 | `checkPermissions`: no-teammate → `ask` "Exit plan mode?"; teammate → `allow` | `requires_permission=False`; la aprobación la orquesta el front vía `ends_turn` | 🔀 (aprobación = front/BFF) |
| B6 | `call`: escribe plan editado a disco + `persistFileSnapshotIfRemote`; restaura `prePlanMode` (con fallback gate auto-mode); `setNeedsPlanModeExitAttachment(true)`; `setHasExitedPlanMode(true)` | `modifier` saca `plan_mode`, cachea plan en `native['plan']`, arma `plan_mode_exit_pending` | 🟡 (sin restaurar modo previo — no hay `prePlanMode`; sin snapshot; sin auto-mode fallback) **FIND-PLAN11** |
| B7 | teammate `isPlanModeRequired()`: escribe `plan_approval_request` al mailbox del líder | ❌ | ⛔ (teams → 05/implementador) |
| B8 | `mapToolResult`: ramas teammate-awaiting / **isAgent** ("respond ok") / empty-plan / plan + **teamHint** + label "edited" | `output` = "Plan submitted for approval:\n\n{plan}" | 🟡 **FIND-PLAN11** (sin rama isAgent/teamHint/edited-label) |
| B9 | one-shot de salida: `plan_mode_exit` attachment vía flag | `PlanModeProvider` rinde `_render_exit_reminder` UNA vez (pop `exit_pending`) | ✅ |
| B10 | el `plan_mode_exit` canónico **sólo referencia el path** del plan | runtime **inlinea el plan aprobado** en el reminder | 🔀 **enriquecido** (defecto observado 2026-06-30: plan se perdía como `tool_result` transitorio; `test_plan_mode_binding`) |
| B11 | `prompt()` = `EXIT_PLAN_MODE_V2_TOOL_PROMPT` (`prompt.ts:6-29`): "When to Use — sólo planning, no research" + "no preguntes con AskUserQuestion si el plan está ok" + ejemplos | `description` de 2 líneas (mecánica), sin la guía de cuándo/cómo | 🟡 **FIND-PLAN1** (cara ExitPlanMode, ampliada 2ª vuelta) |

### C · `plans.ts` (storage del plan-file)

| # | Feature canónica | Runtime | Estado |
|---|---|---|---|
| C1 | `getPlanFilePath(agentId)`: `{slug}.md` root / `{slug}-agent-{id}.md` subagente | `/plans/plan.md` root / `/plans/plan-agent-{agent_id}.md` (por `is_subagent`) | ✅ (aislamiento subagente) |
| C2 | `getPlan(agentId)`: `readFileSync`, ENOENT→null | `get_plan` async vía `storage.ensure_local` + `read_text`, miss→None | ✅ |
| C3 | word-slug per-sesión con retry-colisión (10×), cache `planSlugCache`, `setPlanSlug`/`clearPlanSlug`/`clearAllPlanSlugs` | token **FIJO** `/plans/plan.md`; unicidad por namespace de sesión (MinIO blob) | 🔀 **deliberado** (contenedor + MinIO ≠ dir plano local) |
| C4 | `getPlansDirectory`: `settings.plansDirectory` (project-rel, guard traversal) o `~/.claude/plans`; memoizado | prefijo `/plans`; mapeo→MinIO es política del `PathStorage` del integrador | 🔀 (sin override `plansDirectory`) |
| C5 | `isSessionPlanFile` (en `filesystem.ts`): prefijo `/plans/` + `.md` — **exención del candado** de plan mode | `is_session_plan_file` portado (prefijo+sufijo) | 🟡 **sin consumidor** — el candado read-only (sólo plan-file escribible) **no se hace cumplir** en core **FIND-PLAN4** |
| C6 | `copyPlanForResume`: restaura slug del log; en ENOENT recupera de snapshot/historial (remoto/CCR) | ❌ | 🔀 (MinIO durable → re-lee blob; recovery-de-transcript N/A) |
| C7 | `copyPlanForFork`: **nuevo** slug para la sesión forkeada + copia contenido (anti-clobber) | fork usa path `plan-agent-{id}` propio pero **no hereda** el plan del padre | ❌ **FIND-PLAN7** (cross-ref 05·fork) |
| C8 | `recoverPlanFromMessages`: 3 fuentes (tool_use input / `user.planContent` / `plan_file_reference`) | ❌ | 🔀 (MinIO durable, N/A) |
| C9 | `persistFileSnapshotIfRemote`: snapshot del plan al transcript (sólo remoto) | ❌ | 🔀 (MinIO durable, N/A) |

### D · `planModeV2.ts`

| # | Feature canónica | Runtime | Estado |
|---|---|---|---|
| D1 | `getPlanModeV2AgentCount` (Plan agents): 1-3 por tier (max20x/enterprise/team=3) + env | reminder generico ("agent(s)"), sin cap computado | 🟡 **FIND-PLAN10** |
| D2 | `getPlanModeV2ExploreAgentCount`: default 3 + env | idem generico | 🟡 **FIND-PLAN10** |
| D3 | `isPlanModeInterviewPhaseEnabled`: gate (ant on / env / growthbook) → **workflow iterativo alternativo** | ❌ sólo el 5-fases | ❌ **FIND-PLAN9** |
| D4 | `getPewterLedgerVariant` (trim/cut/cap/null): experimento tamaño Phase-4 | texto Phase-4 único (≈control) | ⛔ (A/B experiment; se documenta) |

### E · Agentes built-in `Plan`/`Explore` (`planAgent.ts`, `exploreAgent.ts`)

| # | Feature canónica | Runtime | Estado |
|---|---|---|---|
| E1 | `PLAN_AGENT`: `agentType:'Plan'`, system-prompt read-only, `disallowedTools=[Agent,ExitPlanMode,FileEdit,FileWrite,NotebookEdit]`, `model:inherit`, `omitClaudeMd` | **no registrado** (`plan_file.py` sólo declara `PLAN_AGENT_TYPE="Plan"` como *contrato con integrador*) | ❌ **FIND-PLAN3** |
| E2 | `EXPLORE_AGENT`: `agentType:'Explore'`, read-only, `model:haiku`(ext)/`inherit`(ant), mismos `disallowedTools` | **no registrado** (`EXPLORE_AGENT_TYPE="Explore"`) | ❌ **FIND-PLAN3** (compartido con 05/10) |
| E3 | el reminder de 5 fases **referencia** estos `subagent_type` | el reminder los nombra pero no hay agentes que resuelvan → tipo inexistente | ❌ **FIND-PLAN3** (rompe la instrucción core del workflow) |

### F · Instrucciones (attachments) — `messages.ts`, espejadas por `PlanModeProvider`

| # | Feature canónica | Runtime | Estado |
|---|---|---|---|
| F1 | `getPlanModeV2Instructions` (full 5-fases: Explore→Plan→review→plan-file→ExitPlanMode) | `_render_plan_full` reproduce las 5 fases + Explore/Plan + Phase-4(Context/approach/files/verification) + Phase-5 | 🟡 (sin `agentCount` inyectado, sin pewter variant, sin NOTE "pregunta cuando quieras") |
| F2 | `planFileInfo` (existe→Edit / no→write) | `_plan_file_info` idem (write_file/Edit) | ✅ |
| F3 | `getPlanModeV2SparseInstructions` (recordatorio escueto) | `_render_plan_sparse` idem | ✅ |
| F4 | `getPlanModeV2SubAgentInstructions`: read-only **+ su propio plan-file path** | `_render_subagent_reminder`: read-only genérico, **sin** plan-file path del subagente | 🟡 **FIND-PLAN12** |
| F5 | `plan_mode_exit` attachment | `_render_exit_reminder` (ver B9/B10) | ✅/🔀-enriquecido |
| F6 | `getPlanModeInterviewInstructions` (workflow iterativo) | ❌ | ❌ **FIND-PLAN9** |
| F7 | `plan_mode_reentry` attachment ("vuelves a plan mode, lee el plan, decide fresh/continúa") | ❌ (al re-entrar sólo resetea full_shown → re-emite 5-fases) | ❌ **FIND-PLAN5** |
| F8 | `plan_file_reference` attachment (preserva el plan **a través de compactación**) | `compact_context` devuelve `[]`; el plan queda en `native` (re-leíble) pero **no se re-inyecta** | ❌ **FIND-PLAN6** |

### G · Cadencia de emisión — `attachments.ts` / `state.ts`

| # | Feature canónica | Runtime | Estado |
|---|---|---|---|
| G1 | throttle `TURNS_BETWEEN_ATTACHMENTS=5` (re-adjunta cada 5 **turnos humanos**) | `active_context` emite **cada iteración** (full 1ª, luego sparse siempre) | 🔀 **FIND-PLAN8** (sin throttle por turnos-humanos) |
| G2 | full/sparse: full en la 1ª, 6ª, 11ª… (cada 5ª adjunción) | full **una** vez, luego sparse hasta re-entrar | 🔀 **FIND-PLAN8** (no re-muestra full cada 5ª) |
| G3 | reset del ciclo full/sparse en re-entrada (`countPlanModeAttachmentsSinceLastExit`) | `plan_mode_full_shown` reseteado en enter/exit | ✅ (mirror parcial) |
| G4 | `handlePlanModeTransition`: to-plan limpia exit-pending; from-plan arma exit-pending | repartido: EnterPlanMode siembra plan_mode/resetea full_shown; ExitPlanMode saca plan_mode/arma exit_pending | ✅ (comportamiento; estructura 🔀) |
| G5 | flags `hasExitedPlanMode` / `needsPlanModeExitAttachment` | flags `native` (`plan_mode_exit_pending`) | ✅ |
| G6 | exit one-shot guardado (skip si volvió a plan mode); mutuamente excluyente con plan_mode | `active_context`: si `plan_mode` activo NO mira exit_pending; ExitPlanMode pop+arma en el mismo turno | ✅ (exclusividad documentada) |

### H · Front/UI/remoto (⛔ core — abiertos y confirmados)

| # | Feature canónica | Naturaleza | Estado |
|---|---|---|---|
| H1 | `/plan` (`plan.tsx`): toggle plan mode / mostrar plan / `/plan open` (editor) | slash-command TUI | ⛔ front (el toggle user-initiated es afordancia del front/BFF) |
| H2 | `/ultraplan` (`ultraplan.tsx`, ant-only): plan multi-agente en CCR remoto + teleport | command + remote/CCR + diálogos TUI | ⛔ (satélite entero de remote/tasks) |
| H3 | `EnterPlanModePermissionRequest`: diálogo yes/no → `setMode plan` | ink dialog | ⛔ front — **matiz**: canónico **pide aprobación para ENTRAR**; runtime entra sin aprobar (`requires_permission=False`) **FIND-PLAN13** |
| H4 | `ExitPlanModePermissionRequest` (768 LOC): opciones de modo-resultante (accept-edits/default/bypass/auto), **clear-context-and-implement**, ultraplan, plan-feedback, paste-imagen-en-reject, **auto-name-session-from-plan** | ink dialog + permisos + lifecycle sesión | ⛔ front — **contrato pendiente FIND-PLAN-APPROVAL-CONTRACT** |
| H5 | `PlanApprovalMessage` (mailbox teammate), `UserPlanMessage`, `RejectedPlanMessage` | renderers ink | ⛔ UI |

---

## Findings (Deuda A · subsistema-local salvo destino explícito)

- **FIND-PLAN1** (A6 · **B — ampliado 2ª vuelta**) — `prompt()` no portado en **AMBAS** plan-tools: la guía
  extensa que el canónico rinde vía `prompt()` (distinta del `description()` corto) no existe en el runtime, que
  colapsa todo a un `description` de 1-2 líneas. (a) `EnterPlanMode.prompt()` = "When to Use This Tool"
  (7 criterios external / 3 ant + GOOD/BAD, `prompt.ts:16-170`) — cómo el modelo **decide** entrar. (b)
  `ExitPlanMode.prompt()` = `EXIT_PLAN_MODE_V2_TOOL_PROMPT` (`ExitPlanModeTool/prompt.ts:6-29`): "When to Use —
  sólo planning de implementación, NO research" + "no uses AskUserQuestion para preguntar si el plan está ok
  (eso lo hace ESTA tool)" + ejemplos. El runtime `ExitPlanModeTool.description` (`plan_mode.py:65-68`) capta el
  "how it works" mecánico pero **no** esa guía de cuándo/cómo. **Sub-enumeración detectada al re-leer A 1→EOF
  (gate 11)**: la 1ª pasada sólo registró la cara EnterPlanMode. 🟡 (ambas tools).
- **FIND-PLAN2** (B4) — `ExitPlanMode` sin guard de "no estás en plan mode": sólo verifica que exista plan-file;
  llamable fuera de plan mode. 🟡
- **FIND-PLAN3** (E1/E2/E3) — **agentes built-in `Explore`/`Plan` no registrados**: el reminder de 5 fases nombra
  `subagent_type='Explore'/'Plan'` que no resuelven → instrucción core no-funcional. ❌ **(gap mayor)**. Cross-ref
  **05·execution/agents** (Explore/Plan son built-ins compartidos, read-only por `disallowedTools`).
- **FIND-PLAN4** (C5) — candado read-only de plan mode **no se hace cumplir** en core: `is_session_plan_file`
  existe pero **sin consumidor**; la única barrera es el texto del reminder ("MUST NOT edit"). El canónico deniega
  writes ≠ plan-file vía `toolPermissionContext.mode==='plan'`. ❌ → destino **B-02 (gate de permisos)** + write-tools.
- **FIND-PLAN5** (F7) — `plan_mode_reentry` no portado: al re-entrar a plan mode con plan existente no hay guía
  fresh/continúa. ❌
- **FIND-PLAN6** (F8) — plan no re-surface tras compactación: `compact_context` vacío. El canónico re-inyecta
  `plan_file_reference`. ❌
- **FIND-PLAN7** (C7) — fork no hereda el plan del padre (`copyPlanForFork`). ❌ Cross-ref **05·fork**.
- **FIND-PLAN8** (G1/G2) — cadencia distinta: runtime emite sparse **cada** iteración (sin throttle de 5 turnos
  humanos, sin re-mostrar full cada 5ª adjunción). 🔀 → revisar (riesgo de ruido de contexto).
- **FIND-PLAN9** (D3/F6) — workflow **interview-phase** (iterativo, pair-planning) no portado. ❌
- **FIND-PLAN10** (D1/D2) — conteos de agentes Plan/Explore no computados por tier; reminder generico. 🟡
- **FIND-PLAN11** (B6/B8) — `ExitPlanMode` empobrecido: sin restaurar modo previo, sin rama `isAgent`/`teamHint`/
  label-"edited" en el `tool_result`. 🟡
- **FIND-PLAN12** (F4) — reminder de subagente omite el plan-file path propio del subagente. 🟡
- **FIND-PLAN13** (H3) — entrar a plan mode no requiere aprobación del usuario (canónico sí pregunta). 🔀 → front.
- **FIND-PLAN14** (A7) — plan-tools no diferidas (canónico `shouldDefer:true`+searchHint); en runtime siempre
  anunciadas. 🔀 → revisar (¿deliberado always-available?).
- **FIND-PLAN-APPROVAL-CONTRACT** (H4) — el core no ofrece selección de **modo-resultante** ni
  **clear-context-and-implement** ni **plan-feedback** ni **auto-name**; son responsabilidad del **front/BFF** pero
  el contrato (qué debe ofrecer el front al aprobar) está sin documentar. → destino **front + B-02**.

---

## Plan de homologación / remediación desarrollada

> DoD: cada finding con **comportamiento · seam · firma · cableado · orden · test**. Los xfail(strict) de
> `test_cap_plan_homologation.py` codifican los targets ❌/🟡.

### PlR1 · Prompt de Enter **y** ExitPlanMode (FIND-PLAN1 — ambas tools)
- **comportamiento**: `prompt()` devuelve la guía extensa de cada tool — Enter: "cuándo usar plan mode"
  (criterios + GOOD/BAD, variante ant/external); Exit: "When to Use — sólo planning, no research" + "no preguntes
  con AskUserQuestion si el plan está ok" + ejemplos.
- **seam**: constante(s) en `plan_mode.py` (o `tools/native/plan_mode_prompt.py`); `prompt` async en **ambas**
  clases (`EnterPlanModeTool`, `ExitPlanModeTool`).
- **firma**: `async def prompt(self) -> str`.
- **cableado**: el pool/deferred-search lee `prompt()` al describir la tool (hoy sólo hay `description`).
- **orden**: independiente.
- **test**: `EnterPlanModeTool().prompt()` contiene "When to Use" + ≥1 GOOD/BAD; `ExitPlanModeTool().prompt()`
  contiene "research" + la advertencia AskUserQuestion (xfail hasta portar).

### PlR2 · Guard mode-activo en ExitPlanMode (FIND-PLAN2)
- **comportamiento**: si `native['plan_mode']` no está activo → error "You are not in plan mode…" **antes** de leer el plan.
- **seam**: rama al inicio de `ExitPlanModeTool.execute`.
- **firma**: sin cambio (usa `ctx.app_state.native`).
- **cableado**: leer flag `_PLAN_MODE_KEY` de `native`.
- **orden**: antes de `get_plan`.
- **test**: exit con `plan_mode` ausente → `is_error`, sin armar exit_pending (xfail hasta añadir la rama).

### PlR3 · Agentes built-in Explore/Plan (FIND-PLAN3) — **con 05·execution**
- **comportamiento**: registrar `AgentDefinition(agent_type="Explore"|"Plan", read_only, disallowed=[Agent,ExitPlanMode,
  FileEdit,FileWrite,NotebookEdit], model=haiku|inherit, system_prompt=…)` como built-ins del resolver.
- **seam**: `execution/agents.py` — tabla de built-ins + `AgentDefinitionResolver` los expone.
- **firma**: `AgentDefinition` (ya existe); añadir `BUILTIN_AGENTS: list[AgentDefinition]`.
- **cableado**: el `factory` inyecta los built-ins al resolver; el reminder usa `EXPLORE_AGENT_TYPE`/`PLAN_AGENT_TYPE`
  (ya en `plan_file.py`) — deben **coincidir** con los `agent_type` registrados.
- **orden**: prerequisito del workflow de 5 fases (sin esto el reminder es letra muerta).
- **test**: el resolver resuelve `"Explore"` y `"Plan"`; ambos read-only (no exponen FileEdit/Write) (xfail).

### PlR4 · Candado read-only de plan mode (FIND-PLAN4) — **destino B-02**
- **comportamiento**: en plan mode, denegar toda tool no-readonly **excepto** write/edit cuyo target sea
  `is_session_plan_file(token)`.
- **seam**: gate de permisos (`PermissionContext`) — rama "modo plan".
- **firma**: `check(tool, input, ctx)` consulta `native['plan_mode']` + `is_session_plan_file`.
- **cableado**: el dispatcher pasa por el gate; write_file/file_edit exentos sólo para el plan-file.
- **orden**: tras PlR3; documentar en `DEUDA-B-transversal.md` (B-02).
- **test**: en plan mode, `write_file` a `/src/x.py` → denegado; a `/plans/plan.md` → permitido (xfail).

### PlR5 · plan_mode_reentry (FIND-PLAN5)
- **comportamiento**: al re-entrar a plan mode con plan-file existente, emitir UNA vez la guía reentry
  (leer plan / decidir fresh-vs-continúa) en vez del full directamente.
- **seam**: `PlanModeProvider.active_context` — rama reentry usando un flag `native['plan_mode_reentered']`
  sembrado por EnterPlanMode cuando `plan_file_exists`.
- **firma**: nuevo `_render_reentry(context)`.
- **cableado**: EnterPlanMode marca reentry si el plan-file ya existe.
- **orden**: independiente.
- **test**: enter con plan-file presente → primer `active_context` contiene "Re-entering Plan Mode" (xfail).

### PlR6 · Preservar plan tras compactación (FIND-PLAN6)
- **comportamiento**: `compact_context` emite `plan_file_reference` (path + contenido) si existe plan-file.
- **seam**: `PlanModeProvider.compact_context` (hoy `[]`).
- **firma**: async (lee `get_plan`); si el contrato de `compact_context` es sync, cachear el plan en `native`.
- **cableado**: el compactador llama `compact_context` de cada provider.
- **orden**: independiente.
- **test**: con plan-file presente, `compact_context` no vacío y contiene el contenido del plan (xfail).

### PlR7 · Fork hereda plan del padre (FIND-PLAN7) — **con 05·fork**
- **comportamiento**: al forkear, copiar el plan-file del padre al path `plan-agent-{child_id}.md`.
- **seam**: `execution/fork/` (`ForkSnapshot`/`RuntimeContextForker`) — paso de copia de plan.
- **firma**: en el snapshot, `await storage.commit(child_plan_token, parent_plan_bytes)`.
- **cableado**: el forker invoca la copia si el padre tiene plan.
- **orden**: tras localizar el punto de fork (05).
- **test**: fork de ctx con plan → `get_plan(child)` == plan del padre (xfail).

### PlR8 · Cadencia con throttle + full-cada-5ª (FIND-PLAN8)
- **comportamiento**: emitir full en la 1ª/6ª/11ª adjunción y throttlear a 1 cada 5 turnos-humanos.
- **seam**: `PlanModeProvider` — contador `native['plan_mode_attach_count']` + turnos-humanos del contexto.
- **firma**: `active_context` calcula `full if count%5==1 else sparse` y salta si `human_turns_since<5`.
- **cableado**: requiere que el ctx exponga turnos-humanos (o mensajes) — verificar disponibilidad en `app_state`.
- **orden**: revisar primero si el ruido actual (sparse-cada-iter) es problema real; puede quedar 🔀-aceptado.
- **test**: 6 llamadas → full, sparse×4, full (xfail).

### PlR9 · Interview-phase workflow (FIND-PLAN9)
- **comportamiento**: workflow iterativo alternativo (explore→update-plan→ask, loop) bajo gate.
- **seam**: `_render_plan_interview` + flag de config en el provider.
- **firma**: `_render_plan_interview(context)`.
- **cableado**: gate de config (`CapabilitiesConfig`) elige full-5-fases vs interview.
- **orden**: baja prioridad (variante).
- **test**: con gate on, `active_context` contiene "Iterative Planning Workflow" (xfail).

### PlR10 · Conteos de agentes por tier (FIND-PLAN10)
- **comportamiento**: inyectar `explore_count`/`plan_count` en el reminder (default 3/1, override config).
- **seam**: constantes en `plan_file.py` + interpolación en `_render_plan_full`.
- **orden**: independiente. **test**: el full menciona el número (xfail).

### PlR11 · tool_result de ExitPlanMode enriquecido (FIND-PLAN11)
- **comportamiento**: rama `isAgent` ("respond ok"); `teamHint` si Agent-tool disponible; label "edited"; restaurar modo previo.
- **seam**: `ExitPlanModeTool.execute` / `_render` del tool_result.
- **orden**: modo-previo depende de que exista `prePlanMode` (no hay hoy → parcial). **test**: subagente → output "respond ok" (xfail).

### PlR12 · Plan-file path en reminder de subagente (FIND-PLAN12)
- **comportamiento**: `_render_subagent_reminder` incluye el `get_plan_file_path(ctx)` del subagente + planFileInfo.
- **seam**: `provider.py`. **orden**: trivial. **test**: reminder subagente contiene `/plans/plan-agent-` (xfail).

### PlR13 · Contrato de aprobación (FIND-PLAN-APPROVAL-CONTRACT, FIND-PLAN13) — **destino front + B-02**
- **comportamiento**: documentar en `DEUDA-B-transversal.md` qué debe ofrecer el front al aprobar/entrar:
  modo-resultante (accept-edits/default/bypass/auto), clear-context-and-implement (regenera sesión + inyecta
  "Implement the following plan:" con transcript-hint/team-hint/feedback), plan-feedback, auto-name; y aprobación
  para **entrar**.
- **seam**: contrato `PermissionContext`/`user_input` + BFF. **orden**: doc-only en esta pasada. **test**: n/a core.

### PlR14 · Diferir plan-tools (FIND-PLAN14)
- **comportamiento**: marcar `deferred=True` + `search_hint` en Enter/ExitPlanMode si se decide alinear.
- **seam**: atributos de clase en `plan_mode.py`. **orden**: decidir deliberadamente (always-available vs deferred).
- **test**: `is_deferred_tool(ExitPlanModeTool())` (xfail sólo si se decide portar).

---

## Ledger de lectura (honesto)

| Archivo | Lectura |
|---|---|
| **runtime** `capabilities/plan/plan_file.py` | íntegro (1→109) |
| **runtime** `capabilities/plan/provider.py` | íntegro (1→172) |
| **runtime** `capabilities/plan/__init__.py` | íntegro |
| **runtime** `tools/native/plan_mode.py` | íntegro (1→108) |
| **runtime** `tests/test_plan_mode_binding.py` | íntegro |
| **runtime** `tests/test_enter_plan_mode_guard.py` | íntegro |
| **runtime** `tools/deferred.py` | íntegro (1→45, para clasificar A7) |
| `EnterPlanModeTool.ts` | íntegro (1→126) |
| `ExitPlanModeV2Tool.ts` (más grande, 493) | íntegro 1→EOF |
| `utils/plans.ts` (397) | íntegro 1→EOF |
| `utils/planModeV2.ts` | íntegro (1→95) |
| `planAgent.ts` | íntegro (1→92) |
| `exploreAgent.ts` | íntegro (top-level completo) |
| `Enter/ExitPlanMode` `constants.ts` + `prompt.ts` | íntegros |
| `utils/messages.ts` (funciones plan) | tramos exactos: 3136-3417 (instrucciones full/sparse/subagent/interview/Phase-4), 3620-3643 (`plan_file_reference`), 3826-3859 (`plan_mode`/`reentry`/`exit`) — **enumerado cada variante** |
| `utils/attachments.ts` (emisión plan) | tramos exactos: 259-266 (config), 1131-1273 (turnCount/countSinceExit/getPlanModeAttachments/getPlanModeExitAttachment) |
| `bootstrap/state.ts` (plan) | tramos: 1333-1363 (flags + `handlePlanModeTransition`), 1468-1469 (`getPlanSlugCache`) |
| `services/compact/compact.ts` (plan) | tramos: 1465-1486 (`createPlanAttachmentIfNeeded`), 1542-1560 (`createPlanModeAttachmentIfNeeded`) |
| `commands/plan/plan.tsx` | **íntegro → ⛔** (1→121; slash-command front) |
| `commands/ultraplan.tsx` (470) | **íntegro → ⛔** (1→470; CCR remoto/TUI, ant-only) |
| `ExitPlanModePermissionRequest.tsx` (768) | **abierto → ⛔**: top-level 1→167 + `handleResponse` 274-473 + `buildPlanApprovalOptions` 674-767 (comportamiento capturado; resto = render ink) |
| `EnterPlanModePermissionRequest.tsx` | **íntegro → ⛔** (1→121) |
| `UserPlanMessage.tsx`, `RejectedPlanMessage.tsx`, `PlanApprovalMessage.tsx` | **íntegros → ⛔** (renderers ink) |

### §Nota de honestidad
- `ExitPlanModePermissionRequest.tsx` (768 LOC) **no** se leyó línea-a-línea 1→EOF: es un componente ink cuyo
  render (Select/Box/useEffect) está **fuera de alcance core**. Sí se leyeron **íntegros** los tramos de
  **comportamiento** (imports+ResponseValue+`buildPermissionUpdates`+`autoNameSessionFromPlan` 1-167; el switch
  completo `handleResponse` 274-473; el builder de opciones 674-767). Ninguna clasificación ⛔ se hizo sin abrir el
  archivo (lección 02): los 6 archivos front/UI se **abrieron** antes de marcarse ⛔.
- `messages.ts`/`attachments.ts`/`state.ts`/`compact.ts` son archivos enormes de **otros** subsistemas; se leyeron
  **los tramos exactos de plan** (rangos arriba), enumerando cada variante de attachment. No son in-scope-troceados
  (lección 07): pertenecen a 07·events/03·context/01·compact — aquí sólo se contrasta la **parte de plan**.

### 4 preguntas de cierre
1. ¿Todo cada archivo **canónico** revisado? **Sí** — core de plan (tools/plans/planModeV2/agents) íntegro 1→EOF;
   los satélites de otros subsistemas por tramos-de-plan exactos; los 6 front/UI abiertos y confirmados ⛔.
2. ¿Todo cada archivo **runtime** revisado? **Sí** — los 4 archivos de `capabilities/plan` + `tools/native/plan_mode.py`
   + los 2 tests + `deferred.py` íntegros.
3. ¿Hallazgos exhaustivos (no superficiales)? **Sí** — 14 FIND + tabla A-H feature-by-feature; el gap mayor
   (FIND-PLAN3, agentes Explore/Plan sin registrar) se destapó al verificar el cableado, no por grep.
4. ¿Todo cubierto (nada pendiente)? **Sí** — Deuda A en §Plan (PlR1-14); lo transversal con destino explícito
   (FIND-PLAN4→B-02, FIND-PLAN3/7→05, FIND-PLAN-APPROVAL-CONTRACT→front).

### RE-AUDITORÍA 2026-07-14 (disparada por el usuario, tras el fallo de satélites de 15) — **CONFIRMADO sin cambios**
Re-leídos ÍNTEGROS de cero y diff contra el doc: `ExitPlanModeV2Tool.ts` (493, 1→EOF), `planAgent.ts` (92),
`exploreAgent.ts` (83), y **los huecos que el ledger había dejado sin leer** de `ExitPlanModePermissionRequest.tsx`
(168-273 y 474-673). Resultado: **todo el comportamiento estaba capturado** — `allowedPrompts` (B2), `persistFileSnapshotIfRemote`
(C9), restaurar `prePlanMode`+circuit-breaker auto-mode (B6), rama `isAgent`/`teamHint`/label-edited (B8),
`disallowedTools=[Agent,ExitPlanMode,Edit,Write,NotebookEdit]` de los agentes read-only (E1/E2/FIND-PLAN3),
reject-con-feedback+imágenes (H4). Los huecos sin leer resultaron ser **render ink + variaciones de comportamiento
ya capturado** (plan-vacío→restore-modo, display de allowedPrompts), no comportamiento nuevo. **A diferencia de 15,
14 no difirió ningún archivo in-scope por título**: el núcleo se leyó 1→EOF y el archivo ⛔-front se cubrió por sus
tramos behavioral. Sin findings nuevos; sin cambios de estado, tests ni recuento.

---

## Re-visita de COMPLETITUD (2ª vuelta · gate 11 / L09) · 2026-07-20

**Modo**: 2ª vuelta con **gate 11 de ENTRADA** (cada ✅/🔀 re-verificada abriendo el código de B **y el
ENSAMBLADOR** y siguiendo el dato, no la tabla; las ❌ convergen por lectura directa; A in-scope RE-LEÍDO 1→EOF
esta ronda, no apoyándose en la 1ª pasada — L11, reproche recurrente 11/12/13). **Resultado**: el doc (ya
re-auditado 2026-07-14) **se sostiene sobre base correcta**; **1 discrepancia real** (FIND-PLAN1 sub-enumerado)
+ **2 precisiones de mecanismo**; **cero cambios de estado**; **código intacto**; tests no re-ejecutados.

- **Leído íntegro (B) 1→EOF esta ronda**: `capabilities/plan/{plan_file.py 108, provider.py 171, __init__.py 3}`
  + `tools/native/plan_mode.py` 107 + **ENSAMBLADOR** `factory.py` 267 + `capabilities/manager.py` 111 +
  `loop/agent_loop.py:85-234` (cuerpo del ensamblado per-turno) + `execution/agents.py` 66 +
  `execution/local/runtime.py:336-365` (resolver de subagente) + `tools/factory.py:40-55` (registro) + grep
  prod-vs-test.
- **Lado A RE-LEÍDO 1→EOF ESTA ronda** (citas exactas = evidencia L11): `ExitPlanModeV2Tool.ts` 493 (el más
  grande, L08), `plans.ts` 397, `EnterPlanModeTool.ts` 126, `EnterPlanMode/prompt.ts` 170, `planModeV2.ts` 95,
  `planAgent.ts` 92, `exploreAgent.ts` 83, los 2 `constants.ts` + `ExitPlanMode/prompt.ts` 29. **CERO
  discrepancias en las filas ya documentadas**: A1-A8 (guard `is_subagent`:78-80, `call`+`prepareContextForPlanMode`
  :83-94, mapToolResult 6-pasos/interview:104-118, shouldDefer:55/searchHint:38, KAIROS:56-67), B1-B10
  (`getPlan`:253, `validateInput mode!=='plan'`:204-218, `checkPermissions` ask:234-238, `call` restore-prePlanMode
  +circuit-breaker:357-403, teammate-mailbox:264-313, mapToolResult isAgent/teamHint/edited:452-489, one-shot),
  C1-C9 (`getPlanFilePath`:119-129, slug-cache+retry-10×:32-73, `getPlansDirectory`+traversal-guard:79-111,
  `copyPlanForResume`:164-231, `copyPlanForFork` new-slug:239-264, `recoverPlanFromMessages` 3-fuentes:279-326,
  `persistFileSnapshotIfRemote`:360-397), D1-D4 (agentCount 1-3-por-tier:5-29, exploreCount:31-43, interviewPhase
  gate:50-62, pewter:88-95), E1-E3 (`PLAN_AGENT`/`EXPLORE_AGENT` read-only + `disallowedTools`:planAgent.ts:73-92/
  exploreAgent.ts:64-83). Todas verificadas 1→EOF, no por el ledger previo.

- **✅/🔀 sostenidos abriendo B + ENSAMBLADOR** (L09): `PlanModeProvider()` registrado **INCONDICIONAL**
  (`factory.py:146`, a diferencia de MCP/Skills/Memory condicionales — el plan es capability nativa siempre
  presente); `active_context` **inyectado PER-TURNO** (`agent_loop.py:218`→`_inject_recall`:112-130→
  `manager.active_context`:98-102→`PlanModeProvider.active_context`, hermano EXACTO de MCP/Skills/Memory);
  `context_modifier`/`ends_turn` de Enter/ExitPlanMode **aplicados en el loop** (`agent_loop.py:332-339`, ya
  confirmado cableado en 10·CORR-09-CTXMOD/02); tools registradas en el pool nativo (`tools/factory.py:47/49`),
  **sin atributo `deferred`** ⇒ siempre anunciadas (FIND-PLAN14 por cableado); one-shot de salida
  `_render_exit_reminder` con `pop(exit_pending)` (provider.py:160-163, exclusividad plan_mode↔exit verificada).

- **❌ re-confirmados por CABLEADO/AUSENCIA** (no por la tabla):
  - **FIND-PLAN3** (agentes Explore/Plan): `execution/agents.py` **NO tiene tabla de built-ins** — sólo el
    dataclass `AgentDefinition` + protocolo `AgentDefinitionResolver` (host-injected `factory.py:117`→
    `runtime.py:104`). `EXPLORE_AGENT_TYPE`/`PLAN_AGENT_TYPE` sólo aparecen en el **texto del reminder**
    (`provider.py:61-93`). En standalone `agent_resolver=None` ⇒ `runtime.py:342-343` no resuelve ⇒ fork
    **genérico** (350-353): hereda modelo del padre, **sin** system-prompt read-only ni restricción de tools
    (`agent_allowed_tools=()` = TODAS). El reminder de 5 fases nombra tipos que ni resuelven ni garantizan
    read-only ⇒ instrucción core no-funcional. **❌ (gap mayor) confirmado por lectura del ensamblador.** →05.
  - **FIND-PLAN4** (candado read-only): `is_session_plan_file` (`plan_file.py:58-63`) tiene **0 consumidores de
    prod** (grep: sólo su definición + tests + docstrings). El candado ("MUST NOT edit except plan file") es
    **sólo texto del reminder**; ningún gate deniega writes≠plan-file (el canónico sí, vía
    `toolPermissionContext.mode==='plan'`). **❌ confirmado por ausencia.** → **B-02** + write-tools (PlR4). La
    función `is_session_plan_file` = costura pre-cableada a medias de este ❌ (cara B-interna del gap A↔B ya
    conocido, como LAT-HOOK1 de FIND-HOOK3), **NO** B-orphan nuevo ni deuda-A↔B adicional (anti-padding L10/L11).
  - **FIND-PLAN7** (fork no hereda plan): confirmado — el fork usa path `plan-agent-{id}` propio pero no copia el
    plan del padre (no hay homólogo de `copyPlanForFork`). → 05·fork.

- **DISCREPANCIA REAL (FIND-PLAN1 sub-enumerado)**: al re-leer A 1→EOF apareció que el `prompt()` extenso
  (distinto del `description()` corto) que el runtime NO porta aplica a **AMBAS** plan-tools, no sólo a
  EnterPlanMode como registró la 1ª pasada. `ExitPlanMode` canónico tiene `prompt()` =
  `EXIT_PLAN_MODE_V2_TOOL_PROMPT` (`ExitPlanMode/prompt.ts:6-29`): "When to Use — sólo planning de implementación,
  NO research" + "no uses AskUserQuestion para preguntar si el plan está ok (eso lo hace ESTA tool)" + ejemplos.
  El runtime `ExitPlanModeTool.description` (`plan_mode.py:65-68`) capta el "how it works" mecánico pero **no**
  esa guía de cuándo/cómo. **Corregido**: FIND-PLAN1 ampliado a ambas tools, fila B11 añadida, PlR1 ampliado.
  Análogo a la sub-enumeración feat14/15 de 01 y GAP-MODE2 de 04. Es 🟡 nuevo (cara ExitPlanMode), **no** voltea
  ningún estado existente.

- **PRECISIÓN 1 (FIND-PLAN8 · dedup, no voltea estado)**: el doc dice "runtime emite sparse **cada** iteración".
  Al abrir el ensamblador: `_inject_recall` (`agent_loop.py:121-128`) **deduplica** contra `ctx.messages` — y el
  texto sparse es **idéntico** cada turno (mismo token `/plans/plan.md`) ⇒ se inyecta UNA vez (tras el full) y las
  siguientes se **suprimen**. El riesgo de "ruido de contexto" que el doc marcaba es **menor** de lo enunciado:
  full (1ª iter) → sparse (2ª) → deduplicado (3ª+). El 🔀 **se sostiene** (la cadencia sigue difiriendo del
  canónico full-cada-5ª-adjunción-por-turnos-humanos), sólo se afina el mecanismo.

- **PRECISIÓN 2 (FIND-PLAN6 · cross-ref 13, no voltea estado)**: el ❌ "plan no re-inyectado tras compactación"
  está **doblemente sostenido**: (a) `PlanModeProvider.compact_context` devuelve `[]` (provider.py:165-168); y
  (b) toda la cadena `compact_context` tiene **0 caller de prod** (grep: sólo agregadores `manager.py:104` +
  `contracts/compaction.py:23` + tests) — **la MISMA precisión transversal de 13·fila-D**. Aunque el provider
  emitiera algo, nadie lo drena. El canónico re-inyecta `plan_file_reference` (plans.ts:314-323); el runtime no.
  ❌ confirmado, con nexo explícito al motor-de-compactación NO portado (01·CompactionProvider / 02·GAP-L4).

- **Sin costuras latentes NUEVAS** tipo `to_llm`/`category`/LAT-EXEC1-2/LAT-HOOK1/LAT-MCP1/LAT-SKILL1:
  `is_session_plan_file` es la cara B-interna de FIND-PLAN4 (ya ❌ A↔B, no padding); `compact_context` es la
  costura transversal ya homed en 13. `modes/`/`observer/`/`SignalBus`/`NativeToolRegistry` no tocan plan.

### Ledger de lectura (2ª vuelta · gate 11) — columna "Lectura"
| Lado | Archivo | Lectura (esta ronda) |
|---|---|---|
| B | `capabilities/plan/plan_file.py` (108) | íntegro 1→EOF |
| B | `capabilities/plan/provider.py` (171, el más grande B, L08) | íntegro 1→EOF |
| B | `capabilities/plan/__init__.py` (3) | íntegro 1→EOF (re-export) |
| B | `tools/native/plan_mode.py` (107) | íntegro 1→EOF |
| B (ensamblador) | `factory.py` (267) | íntegro 1→EOF (`PlanModeProvider()` incondicional :146) |
| B (ensamblador) | `capabilities/manager.py` (111) | íntegro 1→EOF (active/compact_context agregan :98-108) |
| B (ensamblador) | `loop/agent_loop.py` | tramo íntegro 85-234 (ensamblado+`_inject_recall`+loop per-turno) |
| B (ensamblador) | `execution/agents.py` (66) | íntegro 1→EOF (sin tabla built-ins) |
| B (ensamblador) | `execution/local/runtime.py` | tramo 336-365 (resolver→fork genérico) |
| B | `tools/factory.py` | tramo 40-55 (registro Enter/ExitPlanMode en pool nativo) |
| A | `ExitPlanModeV2Tool.ts` (493, el más grande, L08) | **RE-LEÍDO íntegro 1→EOF esta ronda** |
| A | `utils/plans.ts` (397) | **RE-LEÍDO íntegro 1→EOF esta ronda** |
| A | `EnterPlanModeTool.ts` (126) | **RE-LEÍDO íntegro 1→EOF esta ronda** |
| A | `EnterPlanMode/prompt.ts` (170) | **RE-LEÍDO íntegro 1→EOF esta ronda** (destapó FIND-PLAN1 cara Exit) |
| A | `ExitPlanMode/prompt.ts` (29) | **RE-LEÍDO íntegro 1→EOF esta ronda** |
| A | `utils/planModeV2.ts` (95) | **RE-LEÍDO íntegro 1→EOF esta ronda** |
| A | `planAgent.ts` (92) · `exploreAgent.ts` (83) | **RE-LEÍDOS íntegros 1→EOF esta ronda** |
| A | `Enter/ExitPlanMode/constants.ts` | íntegros 1→EOF |
| A (satélite, tramos-de-plan in-scope F/G) | `utils/messages.ts` | **RE-LEÍDO esta ronda** 3136-3417 (full/interview/sparse/subagent + Phase-4 pewter) · 3636-3643 (`plan_file_reference`) · 3826-3859 (`plan_mode`/`reentry`/`exit`) — **anclas re-verificadas: el ledger 1ª pasada decía 3620-3643/3826-3859, drift real (L11)** |
| A (satélite, tramos-de-plan in-scope F/G) | `utils/attachments.ts` | **RE-LEÍDO esta ronda** 254-267 (`PLAN_MODE_ATTACHMENT_CONFIG` throttle=5/full-cada-5ª) · 1131-1273 (`getPlanModeAttachmentTurnCount` cuenta turnos-HUMANOS + `countPlanModeAttachmentsSinceLastExit` + `getPlanModeAttachments` + `getPlanModeExitAttachment`) |
| A (satélite, tramos-de-plan in-scope G) | `bootstrap/state.ts` | **RE-LEÍDO esta ronda** 1333-1363 (`handlePlanModeTransition` + flags `hasExitedPlanMode`/`needsPlanModeExitAttachment`) |
| A (satélite, tramos-de-plan in-scope F8/PLAN6) | `services/compact/compact.ts` | **RE-LEÍDO esta ronda** 1470-1486 (`createPlanAttachmentIfNeeded`→`plan_file_reference`) · 1542-1560 (`createPlanModeAttachmentIfNeeded`→`plan_mode` full) |

### §Nota de honestidad (2ª vuelta)
- La 1ª pasada + re-audit 2026-07-14 ya habían leído A+B íntegros (14 **no** fue confirmación-de-doc como 01/02
  ni difirió satélites como 15). Aun así, **por L11 se RE-LEYÓ todo A in-scope 1→EOF esta ronda** (no apoyarse en
  el ledger previo, reproche recurrente 11/12/13): las citas de línea coinciden exactas = evidencia de lectura
  real. El **value-add del gate 11** fue: (1) abrir el **ENSAMBLADOR** (factory/manager/loop/agents/runtime) y
  confirmar por cableado — no por tabla — que `PlanModeProvider` es incondicional, se inyecta per-turno, y que
  FIND-PLAN3 es letra muerta porque `agent_resolver=None`→fork genérico (no sólo "no registrado"); (2) el
  re-leído de A destapó la **sub-enumeración de FIND-PLAN1** (cara ExitPlanMode); (3) las 2 precisiones de
  mecanismo (dedup FIND-PLAN8; transversalidad compact_context FIND-PLAN6 con 13). Método interiorizado (07/09/
  11/12/13): conclusión de cableado = leer el ensamblador 1→EOF; grep sólo para AUSENCIA.
- **⚠ Auto-corrección (gate auto-adversarial del usuario, MISMO reproche recurrente 11/12/13)**: mi 1er cierre de
  esta re-visita re-leyó 1→EOF los **7 archivos de código** de A pero se **apoyó en el ledger de la 1ª pasada** para
  las filas **F1-F8** (attachments de instrucciones) y **G1-G6** (cadencia), cuyo lado A vive en los satélites
  `messages.ts`/`attachments.ts`/`state.ts`/`compact.ts` (fallo L11: heredar parte de A del doc previo). Al reproche
  ("¿lo has hecho con rigor, sin grep como único mecanismo, cero superficialidad, lectura A todo EOF?") **RE-LEÍ los
  tramos-de-plan de esos 4 archivos 1→EOF esta ronda** → **CERO discrepancias** con F1-F8/G1-G6, PERO las **anclas
  del ledger 1ª pasada habían driftado** (`messages.ts` `plan_file_reference` 3620→**3636**; `plan_mode/reentry/exit`
  3826→**3829/3848**) — exactamente lo que L11 obliga a cazar re-abriendo. Confirmaciones sustantivas del re-leído:
  **F4/FIND-PLAN12** (el subagent-instructions canónico SÍ incluye el `planFilePath` propio, messages.ts:3400/
  3403-3411; el runtime no); **B10 🔀-enriquecido** (el `plan_mode_exit` canónico 3848-3854 sólo referencia el path,
  NO inlinea el plan); **FIND-PLAN8** reforzado con la **propia justificación canónica** (el throttle cuenta turnos
  **HUMANOS**, comentario attachments.ts:1139-1142 "counting assistant messages would fire the reminder every 5 tool
  calls instead of every 5 human turns" — justo lo que el runtime `_inject_recall` por `_turn` hace); **FIND-PLAN6**
  doblemente confirmado (canónico tiene DOS attachments de compactación, compact.ts:1470-1486 contenido +
  1542-1560 instrucciones, ambos ausentes en el runtime `compact_context`). Regla re-interiorizada: **TODO A
  in-scope se RE-ABRE 1→EOF esta ronda, incluidos los tramos-de-plan de los archivos-satélite (L07 acota el
  archivo, no exime de re-leer el tramo in-scope)**.
- MODO VALIDACIÓN: sólo se corrigió el **doc** (FIND-PLAN1/B11/PlR1 + este bloque); **código intacto**; los
  xfail(strict) de `test_cap_plan_homologation.py` no se re-ejecutaron (sin cambio de código, patrón 05-12).

### 4 preguntas de cierre (2ª vuelta · gate 11)
1. ¿Todo cada archivo **A** revisado? **Sí, RE-LEÍDO 1→EOF esta ronda** — los 7 de código (el más grande
   `ExitPlanModeV2Tool.ts` 493 y `plans.ts` 397 íntegros) + `prompt.ts`/`constants.ts` **Y** los tramos-de-plan
   in-scope de los 4 satélites (`messages.ts`/`attachments.ts`/`state.ts`/`compact.ts`, F1-F8/G1-G6) **re-leídos
   esta ronda tras el gate auto-adversarial** (mi 1er cierre se apoyaba en la 1ª pasada para F/G — corregido; anclas
   driftadas cazadas, L11); los 6 front/UI ⛔ abiertos (L02). Citas exactas = evidencia.
2. ¿Todo cada archivo **B** revisado? **Sí** — los 3 `plan/*.py` + `plan_mode.py` + el **ENSAMBLADOR**
   (factory/manager/agent_loop:85-234/agents/runtime:336-365/tools-factory) 1→EOF esta ronda.
3. ¿Hallazgos exhaustivos (no superficiales)? **Sí** — cada ✅/🔀 abierta en B+ensamblador; FIND-PLAN3/4/6/7
   re-confirmados por CABLEADO/AUSENCIA (no tabla); FIND-PLAN1 **ampliado** al re-leer A (sub-enumeración cazada).
4. ¿Todo cubierto (nada pendiente)? **Sí** — Deuda A en §Plan (PlR1-14, PlR1 ampliado); transversal con destino
   (FIND-PLAN4→B-02, FIND-PLAN3/7→05, FIND-PLAN-APPROVAL-CONTRACT→front). Sin B-orphans nuevos.

### ⛔ VEREDICTO DE AVANCE
**✅ NADA PENDIENTE → avanzar a 15 · storage.** (01→14 completos con gate 11; A+B de 14 re-verificados 1→EOF
esta ronda con 1 sub-enumeración corregida y cero cambios de estado — cierre GANADO, no asumido; NO quedan
pendientes de verificación de la 2ª vuelta.)
