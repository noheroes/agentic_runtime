# 06 · hooks — SEPARACION (Filosofía B)

> Ruta base `/home/noheroes/python`. Formato = `00-LEGEND.md §3` (plantilla ejercida por `03-context.md`/`10-tools-native.md`).
> Fuente = tracker `../06-hooks.md` (464 líneas, leído íntegro 1→EOF) + re-apertura EN ESTE CICLO del ensamblador real
> de B (L09/L11: los ✅/🔀 del gate-11 del tracker NO se heredan como evidencia — se re-abren aquí).
>
> ⚙ **Reconciliado contra el tracker en `A-CIERRE-P4 §12` (2026-07-28, par 7/18).** Saldo 74/74 unidades:
> 54 CONSERVADAS · 10 ENRIQUECIDAS · 10 COMPRIMIDAS-CON-PÉRDIDA · **0 INVENTADAS** · 1 PERDIDA sin colocar
> (kill-switches, hoy `KH7`). Las **11 pérdidas `P4-06-1..11` están remediadas *in situ* en este documento**
> (§0.1, §1, §1.0, §2.x, §3.x); los extras locales `K*` quedan **renumerados `KH*`** (colisionaban con los
> keystones globales `K1..K8` de `DEUDA-A` — `§12.4·I5`); las 5 inversiones **aguas arriba** se tabulan en
> **§2.6**. Nada de esto es re-clasificación de findings: es restitución de contenido perdido al destilar.

## 0.1 Contrapartes canónicas leídas por el tracker — inventario con LOC y anclas (`P4-06-11`)

> **Por qué existe esta sección.** El destilado había perdido la cabecera del tracker (`../06-hooks.md:7-49`):
> el inventario de contrapartes con LOC —**lo único que acredita la escala de lo leído en A**— y las **7 anclas
> `archivo:línea`** (retención medida: **7 → 0 = 100 % de pérdida**, `A-CIERRE-P4 §12.0`). Sin ellas, cada ficha
> de este documento afirma un comportamiento canónico que Fase B no puede ir a verificar. Restituidas del
> tracker; **no se reabrió `claude-code/src`** (`D-01`: el insumo es el tracker).

**Runtime (B):** `hooks/{protocol.py (72), runner.py (63), __init__.py (11)}` = **146 LOC**. Disparos reales: 2 —
`loop/agent_loop.py:301` (PreToolUse) y `execution/local/runtime.py:289` (SubagentStop, vía `_fire_stop`).
Contrato anexo `contracts/permissions.py` (33).

**Canónico (A) — leído íntegro por el tracker (1ª pasada + re-audit 2026-07-12):**

| archivo canónico | LOC | qué aporta |
|---|---|---|
| `entrypoints/sdk/coreTypes.ts` | — | `HOOK_EVENTS` = **27 eventos** (**`:25`**, cuerpo **`:26-52`**) |
| `schemas/hooks.ts` | 222 | tipos `command\|prompt\|agent\|http`, `matcher`, `if`, `timeout`, `async`/`asyncRewake`, `once`, `statusMessage`, `shell`; `HookMatcherSchema`; `HooksSchema` |
| `types/hooks.ts` | 290 | `syncHookResponseSchema` (hookSpecificOutput **por evento**), `HookCallback`/`HookCallbackContext`, `HookResult`, `AggregatedHookResult` |
| `utils/hooks/hookEvents.ts` | 192 | bus de eventos de EJECUCIÓN de hook (started/progress/response) → `J1` |
| `utils/hooks/hookHelpers.ts` | 83 | `createStructuredOutputTool`, `registerStructuredOutputEnforcement` → `G5` |
| `utils/hooks.ts` | **5022** | los **dos motores** + los 26 ejecutores por evento (§1.0) + kill-switches (`KH7`). Anclas: **`:434`** y **`:622-641`** (`additionalContext` inyectable en PreToolUse) |
| `query/stopHooks.ts` | 473 | `handleStopHooks` (fin de turno; Stop + TeammateIdle/TaskCompleted) → `G1-G3` |
| `services/tools/toolHooks.ts` | 650 | `runPreToolUseHooks`, `runPostToolUseHooks`, `runPostToolUseFailureHooks`, **`resolveHookPermissionDecision`** — anclas **`:332`** (invariante), **`:372`** (*«Hook allow skips prompt but deny/ask rules still apply»*), **`:510-561`** (`permissionBehavior` allow/ask/deny) |
| `hooks/toolPermission/PermissionContext.ts` | 388 | decisión de permiso (allow/deny/ask, persistencia); `handlers/{interactiveHandler(536), coordinatorHandler(65 ⛔), swarmWorkerHandler(159 ⛔)}` |
| `utils/hooks/registerFrontmatterHooks.ts` | 67 | hooks per-agente (Stop→SubagentStop) → `I1`/`I2` |
| `utils/hooks/registerSkillHooks.ts` | 64 | hooks per-skill (`once`) → `I3` |

**Las 7 anclas `.ts:línea` restituidas** (las que el destilado había perdido al 100 %): `coreTypes.ts:25` ·
`coreTypes.ts:26-52` · `utils/hooks.ts:3932` (`executeSubagentStartHooks`, → `A6`/`E9`) · `runAgent.ts:532`
(su disparo, → `A6`/`E9`) · `toolHooks.ts:332` · `toolHooks.ts:372` · `toolHooks.ts:510-561` ·
`utils/hooks.ts:434` · `utils/hooks.ts:622-641`.

**Helpers canónicos con línea** (insumo directo de `battery_hooks_config`, §2.2): `createBaseHookInput` (301) ·
`processHookJSONOutput` (489) · `execCommandHook` (747) · `matchesPattern` (1346) ·
`prepareIfConditionMatcher` (1390) · `getMatchingHooks` (1603) · `hasBlockingResult` (2983) ·
`executeFunctionHook` (4740) · `executeHookCallback` (4840) · `getHookDefinitionsForTelemetry` (5005) ·
`hookDedupKey`/`isInternalHook`/`getHooksConfig`/`hasHookForEvent` ·
`parseHookOutput`/`parseHttpHookOutput`/`parseElicitationHookOutput`. **Message builders** (salida → modelo):
`getPreToolHookBlockingMessage` (1882) · `getStopHookMessage` (1894) ·
`getUserPromptSubmitHookBlockingMessage` (1936) · `getTeammateIdle/TaskCreated/TaskCompletedHookMessage`.

## 1.0 · `KH2` — los 26 ejecutores canónicos por evento, con línea (`P4-06-1`, tabla `D-02`)

> **La pérdida más cara del par, y es una pérdida de `D-02`.** El tracker (`:29-42`) enumera los **26 ejecutores
> por evento con su línea**: es **la única tabla de comportamientos canónicos de la categoría 06**, y nació
> como auto-corrección de superficialidad (`RE-AUDIT-HOOK-COMPLETO`: *«la lista previa omitía ~15»*). El
> destilado la había reducido a una línea de meta-honestidad (`K2`, TIER `meta`, `det. N/A`), es decir **fuera
> de la capa que Fase B lee**. Bajo `D-02` una unidad sin tabla de comportamientos no entra en Fase B — y aquí
> la tabla **existía** y se descartó por clasificarla como higiene documental. Restituida íntegra.

**Consecuencia que esta tabla desbloquea:** el propio `utils/hooks.ts` contiene ejecutores dedicados para casi
los 27 eventos. Eso refuta la lectura de que varios eventos «viven en otros archivos» (SubagentStart se creía
sólo en `runAgent.ts`; Stop sólo en `query/stopHooks.ts`) y **fija el objetivo de `CG-HOOK-2`**: qué punto hay
que disparar y con qué nombre canónico.

| # | ejecutor canónico (`utils/hooks.ts`) | línea | evento / ficha de este doc |
|---|---|---|---|
| 1 | `executePreToolHooks` | 3394 | PreToolUse → `E1`/`F1-F6` |
| 2 | `executePostToolHooks` | 3450 | PostToolUse → `E2` |
| 3 | `executePostToolUseFailureHooks` | 3492 | PostToolUseFailure → `E3` |
| 4 | `executePermissionDeniedHooks` | 3529 | PermissionDenied → `A7`/`CG-HOOK-3` |
| 5 | `executeNotificationHooks` | 3570 | Notification → `E8` |
| 6 | `executeStopFailureHooks` | 3594 | StopFailure → `A4` |
| 7 | `executeStopHooks` | 3639 | Stop **y SubagentStop unificados** vía `subagentId`; carga `last_assistant_message` → `G1`/`G4`/`E10` |
| 8 | `executeTeammateIdleHooks` | 3709 | TeammateIdle → `A11`/`G6` (⛔) |
| 9 | `executeTaskCreatedHooks` | 3745 | TaskCreated → `A11` (⛔) |
| 10 | `executeTaskCompletedHooks` | 3789 | TaskCompleted → `A11`/`G6` (⛔) |
| 11 | `executeUserPromptSubmitHooks` | 3826 | UserPromptSubmit → `E4` (=02·motor#4 / 01·CR2) |
| 12 | `executeSessionStartHooks` | 3867 | SessionStart → `E5` |
| 13 | `executeSetupHooks` | 3902 | Setup → `A8` |
| 14 | **`executeSubagentStartHooks`** | **3932** | SubagentStart → `A6`/`E9` (disparo en **`runAgent.ts:532`**) |
| 15 | `executePreCompactHooks` | 3961 | PreCompact → `E7` (=02·LR1) |
| 16 | `executePostCompactHooks` | 4034 | PostCompact → `A5`/`E7` (=02·LR1) |
| 17 | `executeSessionEndHooks` | 4097 | SessionEnd → `E5` |
| 18 | `executePermissionRequestHooks` | 4157 | PermissionRequest — **carga `permissionSuggestions`** → `F7`/`CG-HOOK-3` |
| 19 | `executeConfigChangeHooks` | 4214 | ConfigChange → `A8` |
| 20 | `executeCwdChangedHooks` | 4260 | CwdChanged → `A9` (→18) |
| 21 | `executeFileChangedHooks` | 4278 | FileChanged → `A9`/`D9` (→18/09) |
| 22 | `executeInstructionsLoadedHooks` | 4335 | InstructionsLoaded → `A8` |
| 23 | `executeElicitationHooks` | 4470 | Elicitation → `A10` (→11·mcp) |
| 24 | `executeElicitationResultHooks` | 4525 | ElicitationResult → `A10` (→11·mcp) |
| 25 | `executeWorktreeCreateHook` | 4928 | WorktreeCreate → `A9` (→18) |
| 26 | `executeWorktreeRemoveHook` | 4967 | WorktreeRemove → `A9` (→18) |

**⛔ UI, nombrados y excluidos con razón** (no son hooks de ciclo): `executeStatusLineCommand` (4584) ·
`executeFileSuggestionCommand` (4675).

**Los dos motores, con línea** (base de `CG-HOOK-7`/`KH4`): `executeHooks` (**1952**, generador central,
~1030 LOC, re-inyecta `AggregatedHookResult` como system message) vs `executeHooksOutsideREPL` (**3003**,
~567 LOC, **sólo loguea**, devuelve `HookOutsideReplResult[]`). Motor async: `executeInBackground` (**184**)
— `async`/`asyncRewake`, exit-code 2 → `enqueuePendingNotification({mode:'task-notification'})` (`KH3`).
Trust gate central en `executeHooks` (**1994**) y `shouldSkipHookDueToTrust` (**286**) → `C6` ⛔.

## 1.1 · §Evidencia del tracker — criterio de aceptación vigente (`P4-06-10`)

> **Restituida entera.** El destilado la había perdido completa (tracker `:285-288`). Es **5 de 5 pares con
> §Evidencia que la pierden** ⇒ agujero estructural del esquema de SEPARACION, no incidencia
> (`A-CIERRE-P4 §9.7·12`). Y es el único mecanismo del corpus que **detecta un doc rancio desde el código**:
> un `xfail(strict)` que pasa a verde por sorpresa significa que la brecha ya no existe.

- **`test_hooks_homologation.py`: 3 passed + 8 xfailed(strict)** — los 8 `xfail` **codifican los targets** de
  `CG-HOOK-1..8`; pasan a verde cuando se homologa (L05·6º campo).
- **Tests previos que cubren 06 (19):** `test_hooks.py` **8** · `test_pre_tool_use_hook.py` **7** ·
  `test_root_turn_start_hooks.py` **4**.
- **Suite global tras 06:** **571 passed · 3 skipped · 26 xfailed**. Lint verde (`ruff`/`mypy`/`bandit`).
- **`DB-07`/`LAT-HOOK1`** (§2.4) tiene su prueba nombrada en `DEUDA-B`: `test_hooks_homologation.py:212-215`,
  `xfail(strict)` → verde al cablear el consumo loop-side.

## 0. Tesis de separación (Filosofía B)

El tracker ya la fija y la SEPARACION la ratifica bajo B: el runtime `hooks/` **NO es** el sistema de hooks configurable
del canónico (settings.json → matchers → hooks tipados `command`/`prompt`/`agent`/`http`). Es un **REGISTRY EN-PROCESO
+ mecanismo de disparo**: el base **posee** los puntos de ciclo y los dispara pasando el payload; la **POLÍTICA**
(leer settings, exec de comandos, evaluar prompts/agentes verificadores, resolver matchers/`if`, dedup, SSRF) la
implementa el **handler del integrador** — que es exactamente `HookSinkProtocol`.

Reparto bajo los tres ejes:
- **T1-CONTRATO** — la vocabulario/shape que cruza el seam: `HookEvent` (taxonomía) + `HookDecision` (decisión rica) →
  `hooks/protocol.py`. Reimplementarlos desalinea a los dos integradores.
- **T2-BASE-MECANISMO** — el runtime OWNS: disparar cada punto en el sitio de ciclo, consumir la `HookDecision`,
  distinguir re-inyectable vs observacional (dos motores). → `hooks/runner.py` + `loop/agent_loop.py` + `execution/local/runtime.py`.
- **T2-COSTURA** — `HookSinkProtocol`/`HookRunner.register`/`register_sink` (ya existe, inyectado por `factory`). El
  integrador la rellena.
- **BATTERY `battery_hooks_config`** — el motor configurable estándar (typed hooks + matcher + `if` + dedup + settings +
  async/asyncRewake) derivado del canónico. **OPCIONAL**: `agentic_code` lo compone; `agentic_assistant` puede
  sustituirlo por su motor multi-tenant. Esto es el **🔀 delegado** del tracker, reificado como battery (no CORE-GAP).
- **T3-INTEGRADOR** — HITL de permiso (`ask`→diálogo), persistencia de grants, atribución.

Bajo esta lente, **el sistema configurable en sí NO es deuda del core** (L10 anti-padding): es battery+política del
integrador. Los CORE-GAPs REALES son los del **seam** que impiden al integrador construirlo encima: taxonomía
incompleta, casi ningún punto disparado, gate PreToolUse lossy, `HookDecision` pobre, PreToolUse conflacionado con
PermissionRequest, dos-motores no distinguidos, `mode` ausente (GAP-02).

---

## 1. Tabla por finding (grid del tracker A–J · 68 filas + KH-extras · 7)

Columnas: `núcleo|cáscara` · TIER · destino · estado-tracker · nota-identidad. `est.` = estado del tracker.

> **Namespace (`A-CIERRE-P4 §12.4·I5`, consecuencia c25).** Los extras locales se numeran **`KH*`**, no `K*`:
> `K1..K8` está tomado por los **keystones globales** de `DEUDA-A §1.1`. Un lector de Fase B que viniera del rollup
> leería `K5` como *keystone 5* y no como *`LAT-HOOK1`*. Renumerados `K1..K6` → **`KH1..KH6`**; `KH7` es nuevo
> (kill-switches, `P4-06-2`) y `KH2` deja de ser meta para volver a ser la tabla de comportamientos de §1.0.

### A · Taxonomía de eventos
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | id |
|---|---|---|---|---|---|---|
| A1 | 27 eventos canónicos vs 11 declarados | núcleo | T1-CONTRATO | `hooks/protocol.py` (`HookEvent`) | 🟡 | — |
| A2 | Pre/Post/PostToolUseFailure | núcleo | T2-BASE-MECANISMO | `agent_loop.py` (disparo) | 🟡 | ejec |
| A3 | Notification/UserPromptSubmit/SessionStart/SessionEnd | núcleo | T2-BASE-MECANISMO | loop + borde de sesión | ❌ | ejec·persist |
| A4 | Stop/StopFailure/PreCompact/SubagentStop | núcleo | T2-BASE-MECANISMO | loop + `runtime.py` | 🟡 | ejec |
| A5 | PostCompact | núcleo | T2-BASE-MECANISMO (liga 02·LR1) | loop compactación | ❌ FIND-HOOK1 | — |
| A6 | SubagentStart (inyecta context al hijo) — canónico `executeSubagentStartHooks` **`utils/hooks.ts:3932`**, disparo **`runAgent.ts:532`** | núcleo | T2-BASE-MECANISMO (cabo 05) | `runtime.py` (spawn) | ❌ FIND-HOOK1 | ejec |
| A7 | PermissionRequest/PermissionDenied | núcleo | T1-CONTRATO + T2-BASE (liga GAP-02) | `HookEvent` + gate B-02 | ❌ FIND-HOOK1 | — |
| A8 | Setup/InstructionsLoaded/ConfigChange | núcleo | T2-BASE-MECANISMO | loop lifecycle | ❌ FIND-HOOK1 | — |
| A9 | CwdChanged/FileChanged/WorktreeCreate/Remove | núcleo | T2-COSTURA (infra) | →18·factory / →09 | 🔀 | ejec |
| A10 | Elicitation/ElicitationResult | núcleo | T2-COSTURA (mcp) | →11·mcp | 🔀 | — |
| A11 | TeammateIdle/TaskCreated/TaskCompleted | — | ⛔-nombrado | ⛔ coordinator/swarm | ⛔ | — |

### B · Tipos de hook (sistema configurable) — battery
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | id |
|---|---|---|---|---|---|---|
| B1 | `command` (shell, timeout, **`shell: bash\|powershell`**) | núcleo | BATTERY | `battery_hooks_config` | 🔀 | — |
| B2 | `prompt` (LLM, `$ARGUMENTS`, model) | núcleo | BATTERY | `battery_hooks_config` | 🔀 | — |
| B3 | `agent` (verificador, StructuredOutputTool) | núcleo | BATTERY (liga 09·structured-output) | `battery_hooks_config` | 🔀 | — |
| B4 | `http` (POST JSON, SSRF guard, **`headers` con expansión de env**) | núcleo | BATTERY | `battery_hooks_config` | 🔀 | — |
| B5 | `callback`/`function` en-proceso | núcleo | T2-COSTURA | `HookHandler` (existe) | ✅ | — |
| B6 | Config schema (matcher/`if`/`once`/async) | núcleo | BATTERY | `battery_hooks_config` | 🔀 | — |

### C · Resolución de hooks (getMatchingHooks) — battery
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | id |
|---|---|---|---|---|---|---|
| C1 | Matcher por tool name (exact/pipe/regex) | núcleo | BATTERY | `battery_hooks_config` | 🔀 | — |
| C2 | `matchQuery` por evento — claves **`tool_name` · `source` · `trigger` · `reason` · …** (el matcher no es un string suelto: es un query tipado por evento) | núcleo | BATTERY | `battery_hooks_config` | 🔀 | — |
| C3 | `if` condition (permission-rule syntax) | núcleo | BATTERY (liga GAP-02 rule-syntax) | `battery_hooks_config` | 🔀 | — |
| C4 | Fuentes múltiples de `getHooksConfig` — **6**: snapshot de settings · **`registered`** (SDK/programáticos) · **`session`** (vivos, `clearSessionHooks`→I4) · frontmatter de agente · frontmatter de skill · plugin | núcleo | BATTERY | `battery_hooks_config` | 🔀 | — |
| C5 | Dedup namespaced (`hookDedupKey`) | núcleo | BATTERY | `battery_hooks_config` | 🔀 | — |
| C6 | Trust gate (`shouldSkipHookDueToTrust`) | — | ⛔-nombrado (terminal) | ⛔ política de confianza | ⛔ | — |

### D · Salida de hook → decisión (`HookDecision`)
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | id |
|---|---|---|---|---|---|---|
| D1 | `continue:false` + **`stopReason`** → prevenir continuación. 🟡 **porque** el runtime tiene `stop`+`message` pero **no re-inyecta al loop**: corta, no reanuda | núcleo | T1-CONTRATO (HR4) | `HookDecision.continue_loop` | 🟡 | — |
| D2 | `decision approve/block`. 🟡 **porque** el runtime sólo modela **deny** (`block`): **no hay `allow` explícito** que declare permitido lo que la política denegaría | núcleo | T1-CONTRATO | `HookDecision.block` | 🟡 | — |
| D3 | `permissionDecision allow/deny/**ask**` | núcleo | T1-CONTRATO (HR4) | `HookDecision.behavior` | ❌ FIND-HOOK7 | — |
| D4 | `updatedInput` | núcleo | T1-CONTRATO | `HookDecision.modified_input` | ✅ | — |
| D5 | `additionalContext` (existe, no se inyecta) | núcleo | T1-CONTRATO + DEUDA-B consumo | `additional_context` + loop | 🟡 | — |
| D6 | `updatedMCPToolOutput` (PostToolUse reescribe) | núcleo | T1-CONTRATO (HR4) | `HookDecision.updated_output` | ❌ FIND-HOOK7 | — |
| D7 | `systemMessage` (warning al usuario) | núcleo | T1-CONTRATO (HR4) | `HookDecision.system_message` | ❌ FIND-HOOK7 | — |
| D8 | `retry` (PermissionDenied) | núcleo | T1-CONTRATO (HR4) | `HookDecision.retry` | ❌ FIND-HOOK7 | — |
| D9 | `initialUserMessage`/`watchPaths` | núcleo | T1-CONTRATO (HR4) + T2-COSTURA (watch) | `HookDecision` + costura fs-watch | ❌ FIND-HOOK7 | — |
| D10 | Validación Zod + hint schema **+ check de nombre-de-evento** (el `hookSpecificOutput` debe corresponder al evento que se disparó) | núcleo | BATTERY (handler tipado Python) | `battery_hooks_config` | 🔀 | — |
| D11 | Agregación de múltiples handlers | núcleo | T2-BASE-MECANISMO | `runner.py:33-60` | ✅ | — |

### E · Puntos de disparo (firing) — el gap operativo central
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | id |
|---|---|---|---|---|---|---|
| E1 | PreToolUse (antes de cada tool) | núcleo | T2-BASE-MECANISMO | `agent_loop.py:301` | **✅ (payload) / 🟡 (consumo, ver F)** | ejec |
| E2 | PostToolUse (tras éxito) | núcleo | T2-BASE-MECANISMO | `agent_loop.py:~318` (ausente) | ❌ FIND-HOOK2 | ejec |
| E3 | PostToolUseFailure (tras error) | núcleo | T2-BASE-MECANISMO (liga 08·SIG12) | loop tras dispatch is_error | ❌ FIND-HOOK2 | ejec |
| E4 | UserPromptSubmit (preproceso input) | núcleo | T2-BASE-MECANISMO (=02·motor#4 / 01·CR2) | preproceso de input | ❌ FIND-HOOK2 | ejec |
| E5 | SessionStart/SessionEnd | núcleo | T2-BASE-MECANISMO | borde de sesión | ❌ FIND-HOOK2 | persist |
| E6 | Stop (fin de turno, puede bloquear) | núcleo | T2-BASE-MECANISMO (=02·LR3) | fin de turno | ❌ FIND-HOOK6 | ejec |
| E7 | PreCompact/PostCompact | núcleo | T2-BASE-MECANISMO (=02·LR1) | motor compactación | ❌ FIND-HOOK2 | — |
| E8 | Notification | núcleo | T2-BASE-MECANISMO (liga OI-B/05·S21) | drain de notificaciones | ❌ FIND-HOOK2 | ejec |
| E9 | SubagentStart (inyecta context al hijo) — `utils/hooks.ts:3932` / disparo `runAgent.ts:532` | núcleo | T2-BASE-MECANISMO (cabo 05) | `runtime.py` spawn | ❌ (=A6) | ejec |
| E10 | SubagentStop | núcleo | T2-BASE-MECANISMO | `runtime.py:289` (return ignorado) | 🟡 FIND-HOOK6 | ejec |

### F · Integración con permisos (toolHooks.ts)
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | id |
|---|---|---|---|---|---|---|
| F1 | PreToolUse→permission behavior allow/ask/deny | núcleo | T2-BASE-MECANISMO (HR5) + GAP-02 | gate `agent_loop.py:307-313` | ❌ FIND-HOOK3 | ejec |
| F2 | Invariante: hook `allow` NO salta reglas deny/ask | núcleo | T2-BASE-MECANISMO (HR5) | gate merge con `PermissionContext` | ❌ FIND-HOOK3 | — |
| F3 | `ask`→diálogo HITL (forceDecision) | integrador | T3-INTEGRADOR | →INTEGRADOR (OI-HOOK-B) | ❌ FIND-HOOK3 | ejec |
| F4 | PreToolUse `stop` detiene ejecución | núcleo | T2-BASE-MECANISMO (HR5) | gate `agent_loop.py` (ignorado) | ❌ FIND-HOOK3 | ejec |
| F5 | PreToolUse `additionalContext`→modelo | núcleo | T2-BASE-MECANISMO (HR5) + DEUDA-B (LAT-HOOK1) | gate inyecta al historial | ❌ FIND-HOOK3 | — |
| F6 | PreToolUse `updatedInput` (passthrough) | núcleo | T2-BASE-MECANISMO | `agent_loop.py:307-308` | ✅ | — |
| F7 | PermissionRequest hook (`updatedPermissions`) | núcleo | T1-CONTRATO + T2-BASE (HR3) | punto `PERMISSION_REQUEST` | ❌ FIND-HOOK5 | — |
| F8 | HITL grant (concede permiso) | ambas | T2-BASE (payload `ctx`) + T3 (política) | gate + INTEGRADOR (OI-HOOK-B/C) | 🔀 | ejec |

### G · Stop hooks de fin de turno (handleStopHooks) — cabo de 02
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | id |
|---|---|---|---|---|---|---|
| G1 | Stop hook al cierre de turno | núcleo | T2-BASE-MECANISMO (=02·LR3) | fin de turno | ❌ FIND-HOOK6 | ejec |
| G2 | `preventContinuation`→re-loop | núcleo | T2-BASE-MECANISMO (HR4·`continue_loop`) | loop re-entra | ❌ FIND-HOOK6 | ejec |
| G3 | `blockingError`→mensaje+continúa | núcleo | T2-BASE-MECANISMO (HR4) | loop inyecta+continúa | ❌ FIND-HOOK6 | ejec |
| G4 | SubagentStop **consume** decisión | núcleo | T2-BASE-MECANISMO (HR6) | `_fire_stop` `runtime.py:289` | 🟡 FIND-HOOK6 | ejec |
| G5 | structured-output enforcement (Stop fn-hook) | núcleo | BATTERY (liga 09/16) | →09·structured-output | ❌ | — |
| G6 | TeammateIdle/TaskCompleted al idle | — | ⛔-nombrado | ⛔ coordinator/swarm | ⛔ | — |
| G7 | efectos background (auto-dream/extract-memories) | núcleo | BATTERY | →13·memory | 🔀 | — |

### H · Permisos / permission modes (GAP-02) — hogar canónico
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | id |
|---|---|---|---|---|---|---|
| H1 | `mode` (default/plan/acceptEdits/bypass) | núcleo | T2-BASE-MECANISMO (**GAP-02**, =01·GAP-02/03·GAP-CTX2) | `PermissionContext.mode` (ausente) | ❌ GAP-02 | ejec |
| H2 | Reglas allow/deny por tool | núcleo | T2-BASE-MECANISMO | `PermissionContext` (sin match arg) | 🟡 | — |
| H3 | Persistencia de permisos (user/project/local) | integrador | T3-INTEGRADOR | →15·storage (OI-HOOK-C) | 🔀 | persist |
| H4 | Diálogo interactivo | integrador | T3-INTEGRADOR (terminal) | →INTEGRADOR (OI-HOOK-B) | ⛔ terminal | — |

### I · Registro per-agente / per-skill (frontmatter)
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | id |
|---|---|---|---|---|---|---|
| I1 | Hooks en frontmatter de agente | núcleo | T2-COSTURA (cabo 05·GAP-EXEC4) | `AgentDefinition.hooks` (→05) | ❌ | — |
| I2 | Conversión Stop→SubagentStop per-agente | núcleo | BATTERY (`battery_hooks_config`) | registro per-agente | ❌ | — |
| I3 | Hooks en frontmatter de skill (`once`) | núcleo | BATTERY (liga 12·skills) | →12·skills | ❌ | — |
| I4 | Limpieza de session hooks (`clearSessionHooks`) | núcleo | T2-BASE (registry muere con proceso) | `HookRunner` (in-proc) | 🔀 | ejec |

### J · Bus de EJECUCIÓN de hook (hookEvents.ts)
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | id |
|---|---|---|---|---|---|---|
| J1 | started/progress/response de la ejecución | — | ⛔-nombrado (obs. UI) | ⛔ (el eje real = EventBus 07) | ⛔ | — |

### KH · Extras nombrados del tracker (no-grid) — *renumerados desde `K*`, `§12.4·I5`*
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | id |
|---|---|---|---|---|---|---|
| KH1 | RE-AUDIT-HOOK-COUNT: `HOOK_EVENTS`=27 no 28 (corrección de dato) | — | meta (no-código) | §honestidad (dato) | — | — |
| KH2 | RE-AUDIT-HOOK-COMPLETO: **los 26 ejecutores canónicos por evento, con línea** — tabla de comportamientos `D-02`, restituida en **§1.0** | núcleo | **T1-CONTRATO (evidencia canónica `D-02`)** | **§1.0 → insumo directo de CG-HOOK-1/2** | ❌ | ejec |
| KH3 | RE-AUDIT-HOOK10: `asyncRewake` exit-2→`task-notification` despierta al modelo | núcleo | BATTERY (política) + T2-COSTURA (reawake) | `battery_hooks_config` + seam reawake (05·S21) | 🔀 | ejec |
| KH4 | FIND-HOOK8/RE-AUDIT-HOOK8: dos motores REINJECTING vs OBSERVATIONAL | núcleo | T2-BASE-MECANISMO (HR7) | `HOOK_KIND` en `runner.py` | ❌ | — |
| KH5 | LAT-HOOK1: `additional_context` agregado en `run()` pero **no consumido** | núcleo | DEUDA-B (cablear consumo) | `runner.py:54-59`→loop | tech-debt B | — |
| KH6 | GAP-02 rollup: permission modes, hogar canónico `hooks/toolPermission/` | núcleo | T2-BASE-MECANISMO (CORE-GAP transversal) | `PermissionContext.mode` (→A3.DA) | ❌ | ejec |
| KH7 | **Kill-switches centralizados** (tracker `:264-266`, `P4-06-2`): `shouldDisableAllHooksIncludingManaged` (managed `disableAllHooks`) y `CLAUDE_CODE_SIMPLE`, presentes en **ambos motores** — apagado global del subsistema, previo a matchers y a trust | núcleo | BATTERY (must-have de `battery_hooks_config`) | `battery_hooks_config` + guarda en `HookRunner` | ❌ | ejec |

> **`KH7` era la única unidad del par que se perdió sin quedar colocada en ninguna parte** (`A-CIERRE-P4 §12.1`,
> saldo `1 PERDIDA`). Importa porque es **precondición de operabilidad**: sin apagado global, un integrador
> multi-tenant (`agentic_assistant`) no puede desactivar hooks de un tenant sin reescribir su config, y una sesión
> de depuración no puede aislarse del subsistema. No es UI ni política de producto: está en **los dos** motores
> canónicos, por lo que pertenece al contrato del motor, no al integrador. El trust gate
> (`shouldSkipHookDueToTrust`, `:286`) también es central en ambos, pero ya está nombrado como `C6` ⛔ (terminal).

**Plegados (anotados, NO re-contados):** RE-AUDIT-HOOK9 (payload `last_assistant_message`/`agent_transcript_path`
empobrecido) → refuerza **E10/G4** (`_fire_stop` no transporta ese payload). RE-AUDIT-HOOK11
(`permissionSuggestions` propio) → refuerza **F7**. FIND-HOOK1-7 = capa de **resumen nombrado** sobre clusters del
grid; HR1-HR7 (§Plan del tracker) = capa de **remediación referenciada** — ninguna re-contada (espejo de 10·§Plan R0-R11).

> **⚠ Defecto de capa TRACKER, no de este destilado (`A-CIERRE-P4 §12.3·T1`).** La serie `FIND-HOOK*` del tracker
> **salta de `FIND-HOOK3` a `FIND-HOOK5`: no existe `FIND-HOOK4`**; y `HR7` (`../06-hooks.md:456`) cita un
> **`FIND-HOOK8` que tampoco existe** como tal — su contenido vive bajo el nombre `RE-AUDIT-HOOK8`. Este documento
> **reprodujo fielmente los alias del tracker y no inventó ninguno**: la comprobación se hizo abriendo `§Hallazgos`
> 1→EOF. Se deja anotado aquí para que Fase B no busque un hallazgo inexistente; la corrección pertenece al tracker.

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica
- **`HookSinkProtocol` / `HookRunner`** (T2-COSTURA, **ya existe, inyectada**) — productor: base (dispara en
  `agent_loop.py:301` + `runtime.py:289`); consumidor: handler del integrador. Cableado verificado en-ciclo:
  `factory.py:86`(`=None`)→`225`→`runtime.py:362`→`AgentLoop`; guardas `agent_loop.py:300`/`runtime.py:287` cortan sin
  inyección. **Modelo de delegación (como StorageRegistry), NO huérfano** (L10). `register`/`register_sink` sin call
  site de producción = extensión por diseño, no deuda.
- **`HookDecision` rico** (T1-CONTRATO, requiere HR4) — productor: handler del integrador; consumidor: loop/runtime.
  Extender con `behavior`(allow/ask/deny) · `updated_output` · `system_message` · `continue_loop` · `retry`.
- **Seam de reawake** (T2-COSTURA, KH3) — un hook `asyncRewake` que termina en exit-2 debe poder encolar una
  notificación que despierte al modelo idle → conecta con `NotificationSink` (05·S21 / OI-B de 03).
- **Costura fs-watch** (T2-COSTURA, D9·`watchPaths`) — un hook puede pedir observar rutas; el seam de watch vive en 09/18.

> **⚠ Ninguna de estas dos últimas está en el índice de 29 costuras de `SEAMS.md` (`§12.4·I3`, sonda c24).**
> `SEAMS` se destiló de {01, 16, 07, 02, 05, 09}: **06 nunca fue fuente**. Consecuencia operativa: quien planifique
> Fase B **desde `SEAMS`** no verá el seam de reawake (`KH3`) ni la costura fs-watch (`D9`) — y `OI-HOOK-E` depende
> del primero. Las dos primeras sí tienen destino porque son el `HookSinkProtocol` ya existente y el contrato
> `HookDecision`, que `DEUDA-A` sí recoge.
>
> **⚠ Remisión circular (`§12.4·I4`).** `SEAMS·S8` remite **a 06** el detalle del punto de disparo del reawake; y en
> 06 ese detalle vivía como `K3`, clasificado `meta`/`det. N/A`. A → B → A, sin que nadie lo desarrolle. Se rompe
> aquí: el punto de disparo canónico es `executeInBackground` (`utils/hooks.ts:184`), exit-code **2** →
> `enqueuePendingNotification({mode:'task-notification'})`; el consumidor es el `NotificationSink` de 05·S21.
> `KH3` deja de ser `meta` y pasa a `det. sí (OI-HOOK-E)`.

### 2.2 Batteries que alimenta
- **`battery_hooks_config`** — el **motor configurable estándar** derivado del canónico: hooks tipados
  (`command`/`prompt`/`agent`/`http` + SSRF), `matchesPattern` (exact/pipe/regex), `matchQuery`, `if`
  (permission-rule syntax), `once`, `async`/`asyncRewake`, dedup namespaced, resolución multi-fuente
  (settings/plugin/skill/frontmatter/SDK), `processHookJSONOutput` (validación + hint de schema). **OPCIONAL**:
  `agentic_code` lo compone (CLc-like); `agentic_assistant` puede sustituirlo por su motor de política multi-tenant.
  Alcance = todo B1-B4/B6 + C1-C5 + D10 + I2/I3 + G7 (efectos background→13) + KH3 (asyncRewake) + **KH7
  (kill-switches)**. Es el reificado del "🔀 delegado" del tracker: **battery, no CORE-GAP** (L10 anti-padding).
- **Must-have de la battery añadido por `P4-06-2`:** el **apagado global** (`KH7`) se evalúa **antes** de resolver
  matchers y antes del trust gate — `disableAllHooks` (managed settings, no anulable por el usuario) y
  `CLAUDE_CODE_SIMPLE` (modo mínimo). Debe existir además como **guarda en el propio `HookRunner`**, no sólo en la
  battery: un integrador que sustituya la battery (`OI-HOOK-D`) no puede perder el interruptor de emergencia.

### 2.3 CORE-GAPs (→ rollup `DEUDA-A.md`)
El base/battery **debe** reproducir el comportamiento observable y **hoy no** — con remediación desarrollada (L05).
La numeración HR es la del §Plan del tracker; aquí se ancla el seam+cableado+prueba en-ciclo.

- **CG-HOOK-1 (HR1 · FIND-HOOK1)** — taxonomía **11 → 27**.
  > **Corrección de un ENDURECIMIENTO propio (`A-CIERRE-P4 §12.5`).** Este documento decía *«11→~20
  > core-portables»*. El tracker dice **11 → 27** en sus tres menciones y **nunca fija un subconjunto numerado**:
  > `HR1` sólo pide que la cuenta *«sea ≥ los core-portables»*. El «~20» era una estimación de esta capa presentada
  > como cifra objetivo — exactamente el patrón *prosa en el nivel N citada como hecho estructural en N+1*. La cifra
  > de contrato es **27** (`coreTypes.ts:25`, cuerpo `:26-52`); el reparto de cuáles quedan fuera del enum del base
  > (⛔ teammate/swarm/trust/UI, infra →18, mcp →11) se hace **nominalmente abajo**, no por un número redondo.

  **comportamiento:** `HookEvent` debe declarar los eventos core que el integrador necesita oír (falta `PostCompact`,
  `SubagentStart`, `PermissionRequest`, `PermissionDenied`, `Setup`, `InstructionsLoaded`, `ConfigChange`).
  **seam/firma:** extender el enum en `hooks/protocol.py`; los ⛔ (teammate/swarm, trust, UI) se documentan fuera; los
  de infra (Cwd/File/Worktree) → 18. **cableado:** sólo el enum (el disparo es CG-HOOK-2). **orden:** primero.
  **prueba:** `test_hook_event_taxonomy_covers_core` (xfail existente → verde).
  **insumo:** la tabla de 26 ejecutores de **§1.0** (`KH2`) da el nombre canónico de cada evento — sin ella la
  extensión del enum se haría a ojo (`D-02`).
- **CG-HOOK-2 (HR2 · FIND-HOOK2)** — 9 de 11 eventos son enum muerto.
  **comportamiento:** disparar los core: `PostToolUse`/`PostToolUseFailure` (tras dispatch, `agent_loop.py:318`),
  `UserPromptSubmit` (preproceso input, =02·motor#4), `SessionStart`/`End` (borde de sesión), `Stop`/`StopFailure`
  (fin de turno → CG-HOOK-6), `PreCompact`/`PostCompact` (=02·LR1), `SubagentStart` (spawn, cabo 05), `Notification`
  (drain). **seam:** `await hook_runner.run(HookEvent.X, payload)` en cada sitio, honrando la decisión (CG-HOOK-4).
  **cableado:** loop + runtime + compaction. **orden:** tras CG-HOOK-1/4. **prueba:** `test_post_tool_use_hook_fires`,
  `test_stop_hook_fires`.
- **CG-HOOK-3 (HR3 · FIND-HOOK5)** — separar `PermissionRequest` de `PreToolUse`.
  **comportamiento:** PreToolUse precede; PermissionRequest **decide** el permiso con `permissionSuggestions:
  PermissionUpdate[]` propio (RE-AUDIT-HOOK11). El runtime los conflaciona (concede mutando `ctx.app_state.permissions`
  en el handler PreToolUse). **seam/firma:** nuevo `HookEvent.PERMISSION_REQUEST` disparado por el gate B-02 cuando la
  decisión es `ask`; `PERMISSION_DENIED` cuando `deny`. **cableado:** el gate por-tool (GAP-02) dispara; el integrador
  HITL responde (OI-HOOK-B). **orden:** junto a GAP-02. **prueba:** `test_permission_request_distinct_from_pretooluse`.
- **CG-HOOK-4 (HR4 · FIND-HOOK7)** — `HookDecision` expresivo.
  **comportamiento:** hoy sólo `block`/`stop`/`message`/`modified_input`/`additional_context` (verificado
  `protocol.py:42-46`). Falta `behavior`(allow/ask/deny), `updated_output` (PostToolUse reescribe salida),
  `system_message`, `continue_loop` (Stop re-loop), `retry`, `initial_user_message`. **seam/firma:** extender el
  frozen dataclass; `HookRunner.run` (ya agrega, `runner.py:33-60`) suma el merge de los nuevos campos (`updated_output`
  = último handler; `continue_loop` = OR). **cableado:** `PostToolUse` usa `updated_output` (reescribe `result.output`
  en `agent_loop.py:319-323`); `Stop` usa `continue_loop` (02·LR3). **orden:** temprano (CG-2/3/6 dependen).
  **prueba:** `test_hook_decision_carries_updated_output_and_continue`.
- **CG-HOOK-5 (HR5 · FIND-HOOK3)** — gate PreToolUse lossy → converge con GAP-02.
  **comportamiento:** el gate `agent_loop.py:307-313` (re-abierto en-ciclo) sólo honra `modified_input`(307)+`block`(309);
  el comentario 297-298 declara que ignora `stop`/`additional_context`; sin `behavior`, sin merge con reglas deny/ask
  (rompe el invariante canónico `resolveHookPermissionDecision`: hook `allow` NO salta deny/ask). **remediación:**
  (a) el loop honra `additional_context` (inyecta al historial) y `stop`; (b) la decisión tipada por-tool + merge con
  modos = **GAP-02** (CG-HOOK-8). Aquí sólo la parte del loop. **cableado:** loop 300-313. **orden:** junto a CG-4.
  **prueba:** `test_pretooluse_honors_additional_context`. **Nota:** el consumo de `additional_context` está
  **pre-cableado a medias** — `runner.py:54-59` ya lo agrega (LAT-HOOK1/DEUDA-B); falta sólo el consumo loop-side.
- **CG-HOOK-6 (HR6 · FIND-HOOK6)** — Stop de fin de turno + `_fire_stop` consume decisión.
  **comportamiento:** el motor `handleStopHooks` (`preventContinuation`/`blockingError` + payload
  `last_assistant_message`/`agent_transcript_path`, RE-AUDIT-HOOK9) se desarrolla en **02·LR3** (usa
  `HookDecision.continue_loop`). Aquí: `_fire_stop` (`runtime.py:289`, re-abierto en-ciclo) hace
  `await run(SUBAGENT_STOP…)` **sin asignar el retorno** → decisión descartada. **remediación:** `_fire_stop` asigna y
  **consume** la `HookDecision` (bloqueo/inyección) y transporta el payload rico. **cableado:** `runtime.py:289` +
  invocadores 384/391/406. **orden:** tras CG-4. **prueba:** `test_fire_stop_consumes_decision`.
- **CG-HOOK-7 (HR7 · RE-AUDIT-HOOK8/KH4)** — dos motores REINJECTING vs OBSERVATIONAL.
  **comportamiento:** el canónico bifurca `executeHooks` (re-inyecta `AggregatedHookResult` como system message:
  Pre/PostToolUse/Stop/UserPromptSubmit/SubagentStart/…) vs `executeHooksOutsideREPL` (sólo loguea:
  Notification/SessionEnd/ConfigChange/Cwd/FileChanged). El runtime los conflaciona en un `run()→HookDecision`.
  **seam/firma:** constante `HOOK_KIND: dict[HookEvent, Literal["reinjecting","observational"]]`; para
  observacionales `run()` NO produce `additional_context` re-inyectable (sólo side-effects/log). **cableado:**
  `HookRunner`. **orden:** independiente. **prueba:** `test_observational_hooks_do_not_reinject`.
  **anclas (§1.0):** `executeHooks` **1952** (~1030 LOC) vs `executeHooksOutsideREPL` **3003** (~567 LOC);
  `hasBlockingResult` **2983** sólo aplica al primero.
- **CG-HOOK-8 (GAP-02/KH6/H1)** — permission modes (transversal, hogar canónico = `hooks/toolPermission/`).
  **comportamiento:** `PermissionContext` (verificado `contracts/permissions.py:6-33`) tiene
  `always_allow_command/session`/`always_deny` pero **no `mode`** (default/plan/acceptEdits/bypassPermissions). El
  candado de plan mode hoy es el hack `app_state.native["plan_mode"]` (=03·B2/CtxR2). **seam/firma:** añadir
  `mode: Literal[...]` a `PermissionContext` + un gate por-tool que merge modo+reglas+decisión-de-hook (invariante
  CG-HOOK-5·(b)). **cableado:** el gate del loop consume `mode`; dispara PermissionRequest/Denied (CG-HOOK-3).
  **orden:** raíz transversal (liga 01·GAP-02, 03·GAP-CTX2, 04·modes). **prueba:**
  `test_permission_mode_gates_writes_in_plan`. **→ consolida en A3.DA + coordina con 04·modes.**

### 2.4 DEUDA-B (higiene interna del runtime, NO A↔B — L10)
- **KH5 · LAT-HOOK1** — `HookRunner.run` agrega `additional_context` de todos los handlers (`runner.py:54-55`) y lo
  devuelve unido (`runner.py:57-59`), **pero ningún consumidor de producción lo lee**: el único consumidor de decisión
  (`agent_loop.py:307-313`) sólo mira `modified_input`+`block`; `_fire_stop` descarta la decisión entera. Maquinaria
  **definido-no-consumido** (hermana de `to_llm`/03·D2, `LAT-EXEC1/2`/05). **Acción:** cablear el consumo loop-side
  (es exactamente la parte (a) de CG-HOOK-5); la mitad "agregación" ya existe muerta. NO deuda A↔B (esa es
  FIND-HOOK3/CG-HOOK-5); B-interno = la cañería a medias.

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05)
Con **capacidad observable · origen (costura del base) · firma que consume · cableado en el integrador · orden ·
criterio de aceptación**. El eje PRIMARIO = el **CONTRATO BASE COMÚN** (must-be de TODO integrador con hooks).

- **OI-HOOK-A · Implementar la POLÍTICA de hooks (el handler/sink)** *(contrato base común)* — **capacidad:** todo
  integrador que quiera hooks DEBE proveer un `HookSinkProtocol`: leer su configuración (settings.json o equivalente),
  resolver matchers/`if`, ejecutar los hooks tipados (`command`/`prompt`/`agent`/`http`) y devolver `HookDecision`.
  **origen:** T2-COSTURA `HookSinkProtocol`/`HookRunner.register_sink` (existe, §2.1). **firma:** `async def
  handle(event: HookEvent, payload: dict) -> HookDecision | None`; opcionalmente componiendo `battery_hooks_config`.
  **cableado:** `agentic_code` = handler que lee `~/.claude/settings.json` + proyecto y compone la battery;
  `agentic_assistant` = handler que lee config per-tenant de su store. **orden:** requiere el enum+disparos
  (CG-HOOK-1/2). **aceptación:** un `command` hook declarado en settings se dispara en PreToolUse y su exit-code
  bloquea/permite el tool (verificado por el integrador, no el runtime).
- **OI-HOOK-B · Resolver el HITL de permiso (`ask`→diálogo)** *(contrato base común, realización específica)* —
  **capacidad:** cuando la decisión del gate es `ask`, el integrador resuelve la aprobación humana y concede/deniega.
  **origen:** F3/F8 + CG-HOOK-3 (`PERMISSION_REQUEST`). **firma:** el handler recibe el payload con `suggestions` y
  responde mutando `ctx.app_state.permissions` o devolviendo `behavior=allow/deny`. **cableado:** `agentic_code` =
  diálogo en terminal (espejo `interactiveHandler`); `agentic_assistant` = prompt al front por SSE/websocket
  (round-trip bff). **orden:** junto a GAP-02/CG-HOOK-3. **aceptación:** un tool que dispara `ask` pausa hasta que el
  transporte del integrador devuelve la decisión; el runtime no conoce el medio.
- **OI-HOOK-C · Persistir los permisos concedidos** *(contrato base común, realización específica)* — **capacidad:**
  recordar allow/deny entre turnos/sesiones (user/project/local del canónico). **origen:** H3 + `persistPermissionUpdates`.
  **firma:** el integrador escribe a su capa de storage (costura 15·storage) tras un grant. **cableado:** `agentic_code`
  = `settings.local.json` del checkout; `agentic_assistant` = store per-tenant. **orden:** tras 15·storage.
  **aceptación:** un permiso concedido en un turno sigue vigente en el siguiente sin re-preguntar.
- **OI-HOOK-D · Componer o sustituir `battery_hooks_config`** *(contrato base común — decisión de composición)* —
  **capacidad:** el integrador decide usar la battery estándar o su propio motor. **origen:** §2.2. **firma:** compone
  la battery como parte de su `HookSinkProtocol`, o la reemplaza. **cableado:** `agentic_code` compone la battery
  verbatim (integrador degenerado); `agentic_assistant` la sustituye por su motor de política multi-tenant (matchers
  por tenant, SSRF por org). **orden:** con OI-HOOK-A. **aceptación:** el mismo contrato de hooks funciona con la
  battery estándar o con el motor propio del integrador, sin tocar el base.
- **OI-HOOK-E · Enrutar el reawake de hooks `async`** *(contrato base común)* — **capacidad:** un hook `asyncRewake`
  que termina en exit-2 debe despertar al modelo idle. **origen:** KH3/RE-AUDIT-HOOK10 + seam de reawake (§2.1) +
  `NotificationSink` (05·S21 / OI-B de 03). **firma:** el integrador drena el canal de reawake y lo enruta a su
  transporte (task-notification). **cableado:** `agentic_code` = re-inyecta en el REPL local; `agentic_assistant` =
  push/inbox al front. **orden:** junto a 05·execution + OI-B. **aceptación:** un hook async lento que resuelve tras el
  idle despierta el turno (no se pierde).

### 2.6 Inversiones **aguas arriba** — lo que los rollups no recogieron de 06 (`A-CIERRE-P4 §12.4`)

> **Consecuencia nueva 23 (sonda c23).** Hasta el par 06 se buscaban inversiones *aguas abajo* (una ficha cambia de
> estado al bajar de capa). Aquí el fallo es el simétrico y **más caro**: el destilado 06 está bien y **son los
> rollups los que no lo recogen**. Una ficha correcta con destino nombrado *dentro de su categoría* no llega a Fase B
> si el rollup que planifica Fase B no la reparte. La sonda queda incorporada al método: **buscar el nombre de la
> categoría en las secciones de REPARTO de los 5 rollups**, no sólo en el propio par.

| # | inversión | dónde | efecto sobre Fase B |
|---|---|---|---|
| **I1** | `DEUDA-A §1.2` **no reparte la categoría 06**: los siete `CG-HOOK-1..7` **no tienen destino en el rollup de CORE-GAPs** | `DEUDA-A §1.2` | quien planifique desde `DEUDA-A` no verá ninguno de los 7 CORE-GAPs de hooks. Es el rollup dueño de esa clase de unidad |
| **I2** | `BATTERIES·B17` (`battery_hooks_config`) declara *«CORE-GAPs que la completan»* = **«—»** | `BATTERIES §B17` | la battery aparece como autónoma cuando en realidad **no funciona** sin CG-HOOK-1/2 (enum + disparos): sin eventos que oír, la política no tiene entrada |
| **I3** | seam de reawake (`KH3`) y costura fs-watch (`D9`) **no están en el índice de 29 de `SEAMS`** (06 nunca fue fuente de `SEAMS`) | `SEAMS §índice` | `OI-HOOK-E` depende de un seam que el rollup de costuras no lista → ver nota en §2.1 |
| **I4** | remisión **circular**: `SEAMS·S8` remite el detalle del punto de disparo **a 06**, y 06 lo tenía como `meta`/`det. N/A` | `SEAMS·S8` ↔ `06·KH3` | nadie desarrolla el punto de disparo. **Roto en §2.1** (`executeInBackground` `:184`, exit-2) |
| **I5** | colisión de namespace `K*` (extras locales) con los keystones globales `K1..K8` de `DEUDA-A §1.1` | este doc | **corregido**: `K1..K6` → `KH1..KH6` (+`KH7`), ver nota de §1 |

**Estado:** `I5` queda **cerrada aquí** (renumeración aplicada). `I4` queda **cerrada aquí** por el lado de 06 (el
detalle ya está desarrollado); el lado de `SEAMS·S8` es edición de rollup. **`I1`, `I2` e `I3` NO se pueden cerrar
desde este documento**: son ediciones en `DEUDA-A`, `BATTERIES` y `SEAMS`. Quedan como **ítems de ledger de
`A-CIERRE`** — no como nota al pie de este par, porque una nota al pie en el par es precisamente el mecanismo por el
que se perdieron.

### 2.7 ENDURECIMIENTOS detectados (`A-CIERRE-P4 §12.5`)

*Endurecimiento* = prosa tentativa del nivel N citada como **contrato** en el nivel N+1. Dos casos en este par:

1. **Propio, ya corregido:** *«taxonomía 11→~20 core-portables»* (§2.3·CG-HOOK-1) → **11 → 27**. El «~20» no existe
   en el tracker.
2. **Del consolidador, NO corregible desde aquí — primer endurecimiento detectado en `00-INTEGRADORES`:**
   `00-INTEGRADORES §1.6` fija como **contrato del integrador** la firma
   `hook PRE_TOOL_USE(tool_name, tool_input, call_id, ctx) -> block | modified_input`.
   Eso es **exactamente el gate lossy que `CG-HOOK-5` declara insuficiente** (`agent_loop.py:307-313`: sólo
   `modified_input` + `block`; ignora `stop`, `additional_context`, `behavior`, y rompe el invariante
   `resolveHookPermissionDecision` de `toolHooks.ts:332/372`). El consolidador **eleva a contrato el defecto**: si
   Fase B implementa `00-INTEGRADORES §1.6` al pie de la letra, **construye el bug** y `CG-HOOK-5` queda
   estructuralmente incumplible. Además `§1.7:183` cubre **sólo `OI-HOOK-A` de las 5** obligaciones de §2.5.
   **Ítem de ledger de `A-CIERRE`.**

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor (lema de la etapa):**
> De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda; ninguna categoría
> se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar —o colocado sin
> abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — una fila por finding (**74 = grid 68 + KH-colocables 6**)

`ev.` = evidencia: `T`=tracker-leído · `E:archivo:L`=ensamblador abierto EN ESTE CICLO. `det.` = detalle L05: `sí`=6
campos en §2.3/§2.5 · `N/A`=⛔/DEUDA-B/meta.

> **⚠ Re-conteo honesto (`A-CIERRE-P4 §12.1`, consecuencia c26). El «74» anterior era falso, y fallaba en tres
> sitios a la vez:** la tabla tenía **72 filas contadas una a una** (68 grid + `K3/K4/K5/K6`); el **título** decía
> *«74 = grid 68 + K6»*, que suma **69**; y **§3.2·2** declaraba **74**. Tres cifras incompatibles en un mismo
> apartado — y ninguna reproducía la tabla. El «74» de ahora **no es el de antes recuperado**: es el resultado de
> **68 grid + `KH2` (promovida de meta a colocable, §1.0) + `KH3` + `KH4` + `KH5` + `KH6` + `KH7` (nueva) = 74**,
> con `KH1` fuera por ser meta-dato de honestidad. Que coincida con la cifra vieja es casualidad aritmética, no
> confirmación. **Contado fila a fila sobre la tabla de abajo.**

| ID | TIER | destino | cara | ev. | det. |
|---|---|---|---|---|---|
| A1 | T1-CONTRATO | `hooks/protocol.py` | base | E:`protocol.py:17-28` (enum 11) | sí (CG-1) |
| A2 | T2-BASE-MECANISMO | loop disparo | base | E:`agent_loop.py:301` | sí (CG-2) |
| A3 | T2-BASE-MECANISMO | loop+sesión | base | E:`protocol.py:21-24` (declarados) | sí (CG-2) |
| A4 | T2-BASE-MECANISMO | loop+`runtime.py` | base | E:`runtime.py:289` | sí (CG-2/6) |
| A5 | T2-BASE-MECANISMO | loop compactación | base | T (=02·LR1) | sí (CG-1/2) |
| A6 | T2-BASE-MECANISMO | `runtime.py` spawn | base | T (cabo 05) | sí (CG-1/2) |
| A7 | T1-CONTRATO+T2-BASE | `HookEvent`+gate | base | E:`protocol.py:17-28` (ausente) | sí (CG-1/3/8) |
| A8 | T2-BASE-MECANISMO | loop lifecycle | base | T | sí (CG-1/2) |
| A9 | T2-COSTURA (infra) | →18/→09 | base | T | sí (→18) |
| A10 | T2-COSTURA (mcp) | →11·mcp | base | T | sí (→11) |
| A11 | ⛔-nombrado | ⛔ coordinator/swarm | — | T | N/A (⛔) |
| B1 | BATTERY | `battery_hooks_config` | integrador | T | sí (§2.2/OI-D) |
| B2 | BATTERY | `battery_hooks_config` | integrador | T | sí (§2.2/OI-D) |
| B3 | BATTERY | `battery_hooks_config` | integrador | T | sí (§2.2/OI-D) |
| B4 | BATTERY | `battery_hooks_config` | integrador | T | sí (§2.2/OI-D) |
| B5 | T2-COSTURA | `HookHandler` | base | E:`protocol.py:62`+`runner.py:42` | sí (✅ existe) |
| B6 | BATTERY | `battery_hooks_config` | integrador | T | sí (§2.2/OI-D) |
| C1 | BATTERY | `battery_hooks_config` | integrador | T | sí (§2.2) |
| C2 | BATTERY | `battery_hooks_config` | integrador | T | sí (§2.2) |
| C3 | BATTERY | `battery_hooks_config` | integrador | T | sí (§2.2, liga GAP-02) |
| C4 | BATTERY | `battery_hooks_config` | integrador | T | sí (§2.2) |
| C5 | BATTERY | `battery_hooks_config` | integrador | T | sí (§2.2) |
| C6 | ⛔-nombrado | ⛔ trust/terminal | — | T | N/A (⛔) |
| D1 | T1-CONTRATO (HR4) | `HookDecision.continue_loop` | base | E:`protocol.py:42-46` (ausente) | sí (CG-4) |
| D2 | T1-CONTRATO | `HookDecision.block` | base | E:`protocol.py:42` | sí (CG-4) |
| D3 | T1-CONTRATO (HR4) | `HookDecision.behavior` | base | E:`protocol.py:42-46` (ausente) | sí (CG-4) |
| D4 | T1-CONTRATO | `HookDecision.modified_input` | base | E:`protocol.py:45`+`agent_loop.py:307-308` | sí (✅) |
| D5 | T1-CONTRATO+DEUDA-B | `additional_context`+loop | base | E:`protocol.py:46`+`runner.py:54-59` | sí (CG-5/KH5) |
| D6 | T1-CONTRATO (HR4) | `HookDecision.updated_output` | base | E:`protocol.py:42-46` (ausente) | sí (CG-4) |
| D7 | T1-CONTRATO (HR4) | `HookDecision.system_message` | base | E:`protocol.py:42-46` (ausente) | sí (CG-4) |
| D8 | T1-CONTRATO (HR4) | `HookDecision.retry` | base | E:`protocol.py:42-46` (ausente) | sí (CG-4) |
| D9 | T1-CONTRATO (HR4)+T2-COSTURA | `HookDecision`+fs-watch | base | E:`protocol.py:42-46` (ausente) | sí (CG-4/§2.1) |
| D10 | BATTERY | `battery_hooks_config` | integrador | T | sí (§2.2) |
| D11 | T2-BASE-MECANISMO | `runner.py:33-60` | base | E:`runner.py:33-60` | sí (✅ agrega) |
| E1 | T2-BASE-MECANISMO | `agent_loop.py:301` | base | E:`agent_loop.py:300-306` (payload ✅) + `307-313` (consumo 🟡) | sí (✅ dispara / 🟡 consume, CG-5) |
| E2 | T2-BASE-MECANISMO | `agent_loop.py:~318` | base | E:`agent_loop.py:314-323` (sin hook) | sí (CG-2) |
| E3 | T2-BASE-MECANISMO | loop is_error | base | E:`agent_loop.py:324-328` (sin hook) | sí (CG-2, liga 08) |
| E4 | T2-BASE-MECANISMO | preproceso input | base | T (=02·motor#4/01·CR2) | sí (CG-2) |
| E5 | T2-BASE-MECANISMO | borde de sesión | base | T | sí (CG-2) |
| E6 | T2-BASE-MECANISMO | fin de turno | base | E:`agent_loop.py:346-352` (sin Stop) | sí (CG-6/=02·LR3) |
| E7 | T2-BASE-MECANISMO | motor compactación | base | T (=02·LR1) | sí (CG-2) |
| E8 | T2-BASE-MECANISMO | drain notificaciones | base | E:`runtime.py:294-304` (`_notify` sin hook) | sí (CG-2/OI-E) |
| E9 | T2-BASE-MECANISMO | `runtime.py` spawn | base | E:`runtime.py:306-366` (sin SubagentStart) | sí (CG-2, =A6) |
| E10 | T2-BASE-MECANISMO | `runtime.py:289` | base | E:`runtime.py:285-292/384-406` | sí (CG-6) |
| F1 | T2-BASE-MECANISMO+GAP-02 | gate `agent_loop.py:307-313` | base | E:`agent_loop.py:307-313` | sí (CG-5/8) |
| F2 | T2-BASE-MECANISMO (HR5) | gate merge `PermissionContext` | base | E:`agent_loop.py:307-313`+`permissions.py:6-33` | sí (CG-5) |
| F3 | T3-INTEGRADOR | →INTEGRADOR (OI-B) | integrador | E:`agent_loop.py:291-298` (comentario) | sí (OI-HOOK-B) |
| F4 | T2-BASE-MECANISMO (HR5) | gate (ignorado) | base | E:`agent_loop.py:297-298/307-313` | sí (CG-5) |
| F5 | T2-BASE-MECANISMO (HR5)+DEUDA-B | gate inyecta historial | base | E:`agent_loop.py:307-313`+`runner.py:54-59` | sí (CG-5/KH5) |
| F6 | T2-BASE-MECANISMO | `agent_loop.py:307-308` | base | E:`agent_loop.py:307-308` | sí (✅) |
| F7 | T1-CONTRATO+T2-BASE (HR3) | punto `PERMISSION_REQUEST` | base | E:`protocol.py:17-28` (ausente) | sí (CG-3) |
| F8 | T2-BASE+T3 | gate+INTEGRADOR | ambas | E:`agent_loop.py:291-296/305` (`ctx` en payload) | sí (OI-B/C) |
| G1 | T2-BASE-MECANISMO | fin de turno | base | E:`agent_loop.py:346-352` | sí (CG-6/=02·LR3) |
| G2 | T2-BASE-MECANISMO (HR4) | loop re-entra | base | E:`agent_loop.py:348` (`break`) | sí (CG-6) |
| G3 | T2-BASE-MECANISMO (HR4) | loop inyecta+continúa | base | T (=02·LR3) | sí (CG-6) |
| G4 | T2-BASE-MECANISMO (HR6) | `_fire_stop` `runtime.py:289` | base | E:`runtime.py:285-292` (return ignorado) | sí (CG-6) |
| G5 | BATTERY (09/16) | →09·structured-output | base | T | sí (→09) |
| G6 | ⛔-nombrado | ⛔ coordinator/swarm | — | T | N/A (⛔) |
| G7 | BATTERY | →13·memory | base | T | sí (→13/§2.2) |
| H1 | T2-BASE-MECANISMO (GAP-02) | `PermissionContext.mode` | base | E:`permissions.py:6-33` (sin `mode`) | sí (CG-8) |
| H2 | T2-BASE-MECANISMO | `PermissionContext` | base | E:`permissions.py:13-21` | sí (CG-8, 🟡 sin match arg) |
| H3 | T3-INTEGRADOR | →15·storage | integrador | T | sí (OI-HOOK-C) |
| H4 | T3-INTEGRADOR (terminal) | →INTEGRADOR (OI-B) | integrador | T | sí (OI-HOOK-B) |
| I1 | T2-COSTURA (cabo 05) | `AgentDefinition.hooks` | base | T (→05·GAP-EXEC4) | sí (→05) |
| I2 | BATTERY | registro per-agente | integrador | T | sí (§2.2) |
| I3 | BATTERY (12) | →12·skills | integrador | T | sí (→12) |
| I4 | T2-BASE-MECANISMO | `HookRunner` (in-proc) | base | E:`runner.py:20-31` (in-proc dict) | sí (🔀 muere con proceso) |
| J1 | ⛔-nombrado (obs. UI) | ⛔ (eje real=EventBus 07) | — | T | N/A (⛔) |
| KH2 | T1-CONTRATO (evidencia canónica D-02) | §1.0 → CG-HOOK-1/2 | base | T (`../06-hooks.md:29-42`, 26 ejecutores con línea) | sí (§1.0/CG-1/2) |
| KH3 | BATTERY+T2-COSTURA | `battery_hooks_config`+reawake (05·S21) | ambas | T (RE-AUDIT-HOOK10) + `utils/hooks.ts:184` | sí (OI-HOOK-E) |
| KH4 | T2-BASE-MECANISMO (HR7) | `HOOK_KIND` en `runner.py` | base | E:`runner.py:33-60` (un solo `run`) | sí (CG-7) |
| KH5 | DEUDA-B | `runner.py:54-59`→loop | base | E:`runner.py:54-59`+`agent_loop.py:307-313` | N/A (DEUDA-B) |
| KH6 | T2-BASE-MECANISMO (CORE-GAP transv.) | `PermissionContext.mode` (→A3.DA) | base | E:`permissions.py:6-33` | sí (CG-8) |
| KH7 | BATTERY (must-have) + guarda en `HookRunner` | `battery_hooks_config` + `runner.py` | base | T (`../06-hooks.md:264-266`, ambos motores) | sí (§2.2/OI-D) |

(**`KH1`** = meta de honestidad —dato `HOOK_EVENTS`=27, no 28—, no colocable en runtime: ver §3.2·pregunta 5 y
§Honestidad; **no** cuenta entre las 74. **`KH2` sí cuenta**: dejó de ser meta al restituirse como tabla de
comportamientos `D-02` en §1.0 — ese fue el error que `P4-06-1` corrige.)

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../06-hooks.md`?** — **Sí**, líneas 1→464 (cabecera+contrapartes A + tesis + tablas A–J +
   Hallazgos FIND-HOOK1-8 + RE-AUDITORÍA HOOK-COUNT/COMPLETO/8/9/10/11 + cabos + recuento + evidencia + re-visita de
   completitud gate-11 2026-07-19 con ledger+4 preguntas+VEREDICTO + §Plan HR1-HR7).
2. **¿Reconcilia el conteo?** — **Ahora sí; antes no** (ver el aviso de §3.1). Grid **68** =
   A11+B6+C6+D11+E10+F8+G7+H4+I4+J1 (11+6+6+11+10+8+7+4+4+1). Extras **colocables** = **6** (`KH2`·`KH3`·`KH4`·
   `KH5`·`KH6`·`KH7`); `KH1` excluido por meta. **68 + 6 = 74 filas de ledger**, contadas fila a fila sobre la tabla
   de §3.1; colocados = **74**; **sin colocar = 0** (`KH7`, la única unidad que estaba sin colocar, quedó colocada
   en §2.2 + §3.1). RE-AUDIT-HOOK9/11 **plegados** (refuerzan E10/G4 y F7, no re-contados); FIND-HOOK1-7 = resumen
   nombrado y HR1-7 = remediación referenciada (no re-contados, espejo 10). ✅

   **§Recuento del tracker, restituido *con su corrección* (`P4-06-9` · `A-CIERRE-P4 §12.3·T2`).** El tracker
   (`../06-hooks.md:280-283`) declara **✅ 6 · 🟡 12 · 🔀 14 · ❌ 20 · ⛔ 6 = 58**. **Ninguna de las cinco cifras
   sobrevive al recuento del propio grid**, y el total tampoco: el grid tiene **68** filas, no 58. Contado aquí
   estado por estado sobre las tablas A–J:

   | estado | tracker declara | recuento real del grid | delta |
   |---|---|---|---|
   | ✅ | 6 | **4** (B5·D4·D11·F6) | −2 |
   | 🟡 | 12 | **9** (A1·A2·A4·D1·D2·D5·E10·G4·H2) | −3 |
   | 🔀 | 14 | **17** | +3 |
   | ❌ | 20 | **32** | +12 |
   | ⛔ | 6 | **5** (A11·C6·G6·H4·J1) | −1 |
   | *(compuesto)* | — | **1** (`E1` = ✅ payload / 🟡 consumo) | +1 |
   | **total** | **58** | **68** | **+10** |

   Es un **defecto de la capa TRACKER**, no de este destilado: el §Recuento se escribió sobre una versión anterior
   del grid y no se rehízo al ampliarlo. Se restituye **corregido** porque restituirlo tal cual habría propagado
   diez findings invisibles a Fase B. **La corrección del tracker es un ítem aparte** (este documento no edita la
   capa de arriba).
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador (sin grep)?** — **Sí, re-abierto EN ESTE CICLO
   contra el runtime real** (no heredado del gate-11 del tracker):
   - **E1 (compuesto) / ✅ F6 PreToolUse+modified_input** → `agent_loop.py:300-313`. **El disparo y el payload son
     ✅** (301-306); **el consumo es 🟡** (307-308 sólo `modified_input`, 309 `block`; 297-298 declara que ignora
     `stop`/`additional_context`) → por eso E1 no es un ✅ liso: el estado compuesto es lo que impide leer «PreToolUse
     está hecho» y saltarse `CG-HOOK-5`.
   - **✅ D11 agregación** → `runner.py:33-60` (corta en block/stop 50-51, agrega 52-59).
   - **✅ B5 callback** → `protocol.py:62` (`HookHandler`) + `runner.py:42` (invocado).
   - **🟡 E10/G4 SubagentStop** → `runtime.py:285-292` (`_fire_stop` sin asignar return) + 384/391/406 (invocado).
   - **🔀 F8 HITL grant / seam inyectado** → `agent_loop.py:305` (`ctx` en payload) + `factory.py:86/225`→
     `runtime.py:362`→`AgentLoop`; guardas `agent_loop.py:300`/`runtime.py:287` cortan sin inyección (delegación, no
     huérfano — L10).
   - **🔀 I4** → `runner.py:20-31` (registry `defaultdict` in-proceso, muere con el proceso).
   Las **ausencias** afirmadas (A5-A8/D1/D3/D6-D9/E2-E9/F1-F5/F7/H1/KH4/KH6/KH7) se confirmaron **leyendo la fuente** donde el
   campo/punto NO está: `protocol.py:17-28` (enum 11), `protocol.py:42-46` (`HookDecision` sin behavior/updated_output/
   system_message/continue_loop/retry), `permissions.py:6-33` (sin `mode`), `agent_loop.py:314-352` (sin
   Post/Stop-hook), `runtime.py:294-366` (sin SubagentStart/Notification-hook) — ausencia **leída en fuente**, no grep.
   Los homed-fuera puros (→05/09/11/12/13/16/18) van con destino nombrado y `T` — su cableado se verifica en su
   categoría-hogar (L07).
4. **¿La cara integrador quedó al MISMO detalle que la base?** — **Sí**: §2.5 desarrolla **5** obligaciones
   (OI-HOOK-A política/handler · OI-HOOK-B HITL `ask` · OI-HOOK-C persistir permisos · OI-HOOK-D componer/sustituir
   battery · OI-HOOK-E reawake async) con los 6 campos L05; ningún finding integrador cerrado con "→ integrador" a
   secas. El eje PRIMARIO (contrato base común: TODO integrador con hooks provee handler) está explícito.
5. **¿Doble filo (L10)?** — **Sí**. **No se infla deuda:** el sistema configurable entero (B1-B4/B6, C1-C5, D10, I2/I3)
   NO se cuenta como CORE-GAP — es **battery+política del integrador** (🔀 del tracker reificado como
   `battery_hooks_config`); contarlo como decenas de ❌ sería padding, pues el runtime **deliberadamente delega** la
   política. **No se oculta deuda:** los ❌ reales del **seam** (taxonomía CG-1, disparos CG-2, gate lossy CG-5, decisión
   pobre CG-4, PermissionRequest CG-3, dos-motores CG-7, `mode` CG-8, `_fire_stop` CG-6) se mantienen como CORE-GAP con
   remediación desarrollada — NO disfrazados de 🔀. LAT-HOOK1 = DEUDA-B interna (extensión sin contraparte A), NO deuda
   A↔B. `KH1` (dato 27≠28) = corrección de honestidad del tracker, sin efecto sobre ninguna clasificación de gap.
   **`KH2` ya NO es meta**: clasificarla como «corrección de honestidad» fue el error de este documento —era la
   **tabla de comportamientos canónicos** (26 ejecutores con línea) y su degradación a `det. N/A` la sacaba de la
   capa que Fase B lee (`D-02`). Restituida en §1.0, cuenta como unidad colocada. Ese error es el reverso del
   anti-padding: **no inflar deuda no autoriza a evaporar evidencia**.

### 3.3 §Honestidad
- **Lo re-abierto en-ciclo** (L09/L11, no heredado): `hooks/protocol.py` 1→72, `hooks/runner.py` 1→63,
  `contracts/permissions.py` 1→33 (íntegros); `agent_loop.py:288-352` (gate+dispatch+ends_turn),
  `runtime.py:283-411` (`_fire_stop`+`_notify`+`_run_loop`), `factory.py:210-234` (inyección). Confirmaron
  FIND-HOOK2/3/6 + LAT-HOOK1 + el 🔀 seam-inyectado **por cableado**, no por la tabla del tracker.
- **Lo NO re-leído íntegro en-ciclo** (declarado, no presentado como leído): la contraparte canónica A
  (`utils/hooks.ts` 5022, `toolHooks.ts`, `coreTypes.ts`) — su lectura íntegra ocurrió en la 1ª pasada + re-audit
  2026-07-12 del tracker; aquí la SEPARACION **re-clasifica findings ya destilados**, no re-audita A. Los sitios de
  ciclo `02·motor#4` (UserPromptSubmit), `02·LR1` (compactación), `02·LR3` (Stop de fin de turno) se **referencian**
  con destino a 02 (L07: su cableado se verifica en su hogar), no se re-abren aquí.
- **Conteo de grid = decisión de método declarada:** cada fila multi-evento del tracker (p.ej. A2
  Pre/Post/PostToolUseFailure) se cuenta como **1 finding** (granularidad de fila del tracker, espejo del grid de 10);
  los eventos individuales se despliegan en las tablas E/§2.3, no se re-cuentan.

**Addendum de honestidad de la reconciliación P4″ (2026-07-28) — lo NO verificado, primero:**

- **La tasa `DR-2` de este par no está medida.** Todo lo de arriba es `DR-1` (regresión **tracker → SEPARACION**),
  reparable contra el tracker. Lo que el **tracker** haya perdido respecto del canónico (`utils/hooks.ts` 5022 L y
  compañía) **no se ha comprobado y no se comprueba aquí** — es `P6″`/`O-11`, y sólo se resuelve abriendo
  `claude-code/src`. Ninguna afirmación de este documento debe leerse como *«el canónico dice exactamente esto»*:
  se lee como *«el tracker, que leyó el canónico, dice esto»* (`D-01`).
- **`I1`, `I2` e `I3` siguen abiertas** al cerrar este par: viven en `DEUDA-A`, `BATTERIES` y `SEAMS`. Este
  documento **no las arregla**, sólo las nombra (§2.6).
- **El ENDURECIMIENTO de `00-INTEGRADORES §1.6` sigue en pie** (§2.7·2). Mientras siga, el consolidador contradice
  a `CG-HOOK-5`.
- **Las 11 pérdidas `P4-06-1..11` se detectaron por reconciliación, no por revisión.** Es decir: leyendo este
  documento aislado **no eran visibles** — 54 de 74 fichas estaban intactas y el conjunto parecía sano. Eso es el
  argumento de por qué P4″ se hace par por par y no por muestreo.
- **Lo que este par salió bien, dicho sin adorno (L10, doble filo):** 54 CONSERVADAS · 10 ENRIQUECIDAS ·
  **0 INVENTADAS**. La tesis arquitectónica (`battery_hooks_config` como battery opcional, no CORE-GAP) llegó
  entera y es correcta. Lo que falló no fue el destilado de 06: fueron **los rollups que debían recogerlo**.

### 3.4 VEREDICTO

**⛔ PENDIENTE(S) — el par 06 queda *reconciliado*, no *cerrado*.**

- **Cerrado dentro de este documento:** las 11 pérdidas `P4-06-1..11` (restituidas §1.0/§1.1/§1/§2.2/§3.1/§3.2),
  la inversión `I5` (renumeración `K*`→`KH*`), la inversión `I4` por el lado de 06, el endurecimiento propio
  (`~20` → **27**), y el re-conteo `74` reproducido fila a fila.
- **Abierto fuera de este documento (ítems de ledger `A-CIERRE`):** `I1` (`DEUDA-A §1.2` no reparte 06 ⇒
  `CG-HOOK-1..7` sin destino) · `I2` (`BATTERIES·B17` declara «—» los CORE-GAPs que la completan) · `I3`
  (`SEAMS` no lista el seam de reawake ni la costura fs-watch) · el **ENDURECIMIENTO de `00-INTEGRADORES §1.6`**
  y la cobertura parcial de `§1.7:183` (1 de 5 `OI-HOOK-*`) · las **dos correcciones de la capa tracker**
  (`§Recuento` 58 vs 68; alias `FIND-HOOK4`/`FIND-HOOK8` inexistentes).
- **No medido:** `DR-2` (canónico → tracker) para esta categoría — `O-11`/`P6″`.

Los cabos de **remediación** con destino nombrado (CG-HOOK-1..8 → base/`battery_hooks_config`/A3.DA;
OI-HOOK-A..E → `00-INTEGRADORES.md`; homed-fuera → 02/05/09/11/12/13/15/16/18) **no** son pendientes de
verificación y no cuentan en el ⛔ de arriba. El ⛔ es por los seis ítems fuera del documento.
