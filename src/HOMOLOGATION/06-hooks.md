# 06 · hooks

Runtime: `hooks/{protocol.py (72), runner.py (63), __init__.py}` — **146 LOC**.
Disparos reales: `loop/agent_loop.py:301` (PreToolUse) y `execution/local/runtime.py:289`
(SubagentStop, vía `_fire_stop`). Contratos anexos: `contracts/permissions.py` (33).

Contrapartes canónicas **leídas íntegras**:
- `entrypoints/sdk/coreTypes.ts:25` — `HOOK_EVENTS` (**27 eventos**, líneas 26–52; ver RE-AUDIT-HOOK-COUNT).
- `schemas/hooks.ts` (222) — tipos `command|prompt|agent|http`, `matcher`, `if`, `timeout`,
  `async`/`asyncRewake`, `once`, `statusMessage`, `shell`; `HookMatcherSchema`; `HooksSchema`.
- `types/hooks.ts` (290) — `syncHookResponseSchema` (hookSpecificOutput **por evento**),
  `HookCallback`/`HookCallbackContext`, `HookResult`, `AggregatedHookResult`.
- `utils/hooks/hookEvents.ts` (192) — bus de eventos de EJECUCIÓN de hook (started/progress/response).
- `utils/hooks/hookHelpers.ts` (83) — `createStructuredOutputTool`, `registerStructuredOutputEnforcement`.
- `utils/hooks.ts` (5022) — **DOS motores de ejecución** (RE-AUDIT-HOOK8):
  - `executeHooks` (1952, generador central, ~1030 LOC): hooks *dentro del turno* que **yield**ean
    `AggregatedHookResult` re-inyectado al modelo como system messages. Kill-switches centralizados
    (`shouldDisableAllHooksIncludingManaged`, `CLAUDE_CODE_SIMPLE`), trust gate central (1994),
    binding de `requestPrompt` para hooks `prompt`.
  - `executeHooksOutsideREPL` (3003, ~567 LOC): hooks *fuera del turno* (Notification/SessionEnd/…)
    que **solo loguean** y devuelven `HookOutsideReplResult[]` — **NO** re-inyectan al modelo.
  - Motor async: `executeInBackground` (184) — `async`/`asyncRewake`; en exit-code 2 el `asyncRewake`
    encola `enqueuePendingNotification({mode:'task-notification'})` que **despierta al modelo**.
  - Helpers: `createBaseHookInput` (301), `processHookJSONOutput` (489), `execCommandHook` (747),
    `matchesPattern` (1346), `prepareIfConditionMatcher` (1390), `getMatchingHooks` (1603),
    `hookDedupKey`/`isInternalHook`/`getHooksConfig`/`hasHookForEvent`, `hasBlockingResult` (2983),
    `parseHookOutput`/`parseHttpHookOutput`/`parseElicitationHookOutput`, `executeFunctionHook` (4740),
    `executeHookCallback` (4840), `getHookDefinitionsForTelemetry` (5005).
  - **Ejecutores por evento (enumeración COMPLETA — la lista previa omitía ~15, RE-AUDIT-HOOK-COMPLETO)**:
    `executePreToolHooks` (3394), `executePostToolHooks` (3450), `executePostToolUseFailureHooks` (3492),
    `executePermissionDeniedHooks` (3529), `executeNotificationHooks` (3570), `executeStopFailureHooks` (3594),
    `executeStopHooks` (3639, **unifica Stop y SubagentStop** vía `subagentId`; carga `last_assistant_message`),
    `executeTeammateIdleHooks` (3709), `executeTaskCreatedHooks` (3745), `executeTaskCompletedHooks` (3789),
    `executeUserPromptSubmitHooks` (3826), `executeSessionStartHooks` (3867), `executeSetupHooks` (3902),
    `executeSubagentStartHooks` (3932), `executePreCompactHooks` (3961), `executePostCompactHooks` (4034),
    `executeSessionEndHooks` (4097), `executePermissionRequestHooks` (4157, carga `permissionSuggestions`),
    `executeConfigChangeHooks` (4214), `executeCwdChangedHooks` (4260), `executeFileChangedHooks` (4278),
    `executeInstructionsLoadedHooks` (4335), `executeElicitationHooks` (4470), `executeElicitationResultHooks` (4525),
    `executeWorktreeCreateHook` (4928), `executeWorktreeRemoveHook` (4967).
    (⛔ UI: `executeStatusLineCommand` 4584, `executeFileSuggestionCommand` 4675.)
  - Message builders (salida → modelo): `getPreToolHookBlockingMessage` (1882), `getStopHookMessage` (1894),
    `getUserPromptSubmitHookBlockingMessage` (1936), `getTeammateIdle/TaskCreated/TaskCompletedHookMessage`.
- `query/stopHooks.ts` (473) — `handleStopHooks` (fin de turno; Stop + TeammateIdle/TaskCompleted).
- `services/tools/toolHooks.ts` (650) — `runPreToolUseHooks`, `runPostToolUseHooks`,
  `runPostToolUseFailureHooks`, **`resolveHookPermissionDecision`** (invariante clave).
- `hooks/toolPermission/PermissionContext.ts` (388) — decisión de permiso (allow/deny/ask, persistencia).
  `handlers/{interactiveHandler(536),coordinatorHandler(65 ⛔),swarmWorkerHandler(159 ⛔)}`.
- `utils/hooks/registerFrontmatterHooks.ts` (67) — hooks per-agente (Stop→SubagentStop).
- `utils/hooks/registerSkillHooks.ts` (64) — hooks per-skill (`once`).

## Tesis arquitectural

El runtime `hooks/` **NO es** el sistema de hooks del canónico. El canónico es un
**sistema CONFIGURABLE dirigido por settings.json**: eventos → matchers → hooks tipados
(`command` shell / `prompt` LLM / `agent` verificador / `http`), con `if` (permission-rule
syntax), `async`/`once`, resolución multi-fuente (settings/plugin/skill/frontmatter/SDK),
dedup, y una salida JSON rica (`processHookJSONOutput`).

El runtime `HookRunner` es un **REGISTRY EN-PROCESO**: `register(event, handler)` /
`register_sink` / `run(event, payload) → HookDecision`. Handlers Python async, sin
persistencia, sin tipos de hook, sin matchers.

**La homologación correcta es de COMPORTAMIENTO DEL SEAM, no de forma**: el runtime debe
*disparar los puntos* y *pasar el payload*; la POLÍTICA — incluyendo leer settings.json,
hacer exec de comandos, evaluar prompts/agentes verificadores, resolver matchers/`if` — la
implementa el integrador en su handler (que es exactamente el modelo `HookSinkProtocol`).
Bajo esa lente, **el sistema configurable en sí es 🔀 delegado al integrador** (no un gap
del core). Los gaps REALES son los que impiden al integrador construirlo encima:

1. **Taxonomía incompleta** (faltan eventos core que el integrador necesitaría poder oír).
2. **Casi ningún punto se dispara** (2 de 11 declarados; el resto es enum muerto).
3. **El punto PreToolUse pierde semántica** (sin permission behavior/`ask`, sin merge con
   reglas, `stop`/`additional_context` ignorados).
4. **`HookDecision` no expresa la salida rica** del canónico (ask, updated_output,
   system_message, retry, watchPaths, initialUserMessage).
5. **PreToolUse ≠ PermissionRequest** — el runtime los conflaciona; permission modes (GAP-02)
   siguen sin hogar.

## Tabla feature-by-feature

### A · Taxonomía de eventos
| Feature | Canónico | Runtime | Estado |
|---|---|---|---|
| Eventos declarados | **27** (`HOOK_EVENTS`, coreTypes.ts:26–52) | 11 (`HookEvent`) | 🟡 |
| PreToolUse / PostToolUse / PostToolUseFailure | ✅ | declarados | 🟡 (solo Pre se dispara) |
| Notification / UserPromptSubmit / SessionStart / SessionEnd | ✅ | declarados | ❌ (nunca disparados) |
| Stop / StopFailure / PreCompact / SubagentStop | ✅ | declarados | 🟡 (solo SubagentStop dispara) |
| **PostCompact** | ✅ | ausente | ❌ FIND-HOOK1 |
| **SubagentStart** (inyecta additionalContexts al subagente) | ✅ **`executeSubagentStartHooks` (utils/hooks.ts:3932)**; disparo runAgent.ts:532 | ausente | ❌ FIND-HOOK1 |
| **PermissionRequest / PermissionDenied** | ✅ | ausente | ❌ FIND-HOOK1 (liga GAP-02) |
| **Setup / InstructionsLoaded / ConfigChange** | ✅ | ausente | ❌ FIND-HOOK1 |
| CwdChanged / FileChanged / WorktreeCreate / WorktreeRemove | ✅ | ausente | 🔀 (lifecycle de infra; parte a 18/09) |
| Elicitation / ElicitationResult | ✅ (MCP) | ausente | 🔀 → 11·mcp |
| TeammateIdle / TaskCreated / TaskCompleted | ✅ | ausente | ⛔ coordinator/swarm |

### B · Tipos de hook (sistema configurable) — 🔀 delegado al integrador
| Feature | Canónico | Runtime | Estado |
|---|---|---|---|
| `command` (shell, `shell:bash/powershell`, `timeout`) | ✅ execCommandHook | — | 🔀 (política del handler) |
| `prompt` (LLM, `$ARGUMENTS`, `model`) | ✅ | — | 🔀 |
| `agent` (verificador agéntico, StructuredOutputTool) | ✅ | — | 🔀 |
| `http` (POST JSON, headers env, SSRF guard) | ✅ execHttpHook/ssrfGuard | — | 🔀 |
| `callback` / `function` (en-proceso) | ✅ | `HookHandler` (async Python) | ✅ (equivalente directo) |
| Config schema (matcher, `if`, `once`, `async`, `asyncRewake`) | ✅ schemas/hooks.ts | — | 🔀 (no lo persiste el runtime) |

### C · Resolución de hooks (getMatchingHooks) — 🔀 delegado
| Feature | Canónico | Runtime | Estado |
|---|---|---|---|
| Matcher por tool name (`matchesPattern`: exact/pipe/regex) | ✅ | — | 🔀 (el runner entrega a TODOS los handlers del evento) |
| `matchQuery` por evento (tool_name/source/trigger/reason/…) | ✅ | — | 🔀 |
| `if` condition (permission-rule syntax, `prepareIfConditionMatcher`) | ✅ | — | 🔀 |
| Fuentes: settings snapshot + registered + session + frontmatter + skill + plugin | ✅ getHooksConfig | 1 sola (register en-proceso) | 🔀 |
| Dedup namespaced (`hookDedupKey`) | ✅ | — | 🔀 |
| Trust gate (`shouldSkipHookDueToTrust`) | ✅ | — | ⛔ terminal |

### D · Salida de hook → decisión (processHookJSONOutput vs HookDecision)
| Feature | Canónico (`SyncHookJSONOutput`) | Runtime (`HookDecision`) | Estado |
|---|---|---|---|
| `continue:false` → prevenir continuación | `preventContinuation`+`stopReason` | `stop`+`message` | 🟡 (no re-inyecta al loop) |
| `decision: approve/block` | permissionBehavior allow/deny | `block` | 🟡 (solo deny, no allow explícito) |
| `permissionDecision: allow/deny/**ask**` (PreToolUse) | ✅ | — | ❌ FIND-HOOK7 (sin `ask`) |
| `updatedInput` | ✅ | `modified_input` | ✅ |
| `additionalContext` | ✅ (por evento) | `additional_context` | 🟡 (existe pero no se inyecta, ver E) |
| `updatedMCPToolOutput` (PostToolUse reescribe output) | ✅ | — | ❌ FIND-HOOK7 |
| `systemMessage` (warning al usuario) | ✅ | — | ❌ FIND-HOOK7 |
| `retry` (PermissionDenied) | ✅ | — | ❌ FIND-HOOK7 |
| `initialUserMessage` / `watchPaths` (SessionStart/FileChanged) | ✅ | — | ❌ FIND-HOOK7 |
| Validación Zod + hint de schema + event-name check | ✅ validateHookJson | — | 🔀 (handler tipado Python) |
| Agregación de múltiples handlers | ✅ (executeHooks) | ✅ (`run` acumula ctx, corta en block/stop) | ✅ |

### E · Puntos de disparo (firing) — el gap operativo central
| Punto | Canónico | Runtime | Estado |
|---|---|---|---|
| PreToolUse (antes de cada tool) | ✅ runPreToolUseHooks | ✅ agent_loop.py:301 | ✅ (payload) / 🟡 (consumo, ver F) |
| PostToolUse (tras éxito de tool) | ✅ | — | ❌ **FIND-HOOK2** |
| PostToolUseFailure (tras error de tool) | ✅ | — | ❌ FIND-HOOK2 |
| UserPromptSubmit (input del usuario) | ✅ | — | ❌ FIND-HOOK2 |
| SessionStart / SessionEnd | ✅ | — | ❌ FIND-HOOK2 |
| Stop (fin de turno, puede bloquear) | ✅ handleStopHooks | — | ❌ **FIND-HOOK6** (ver G) |
| PreCompact / PostCompact | ✅ | — | ❌ FIND-HOOK2 (liga 02·compactación) |
| Notification | ✅ | — | ❌ FIND-HOOK2 |
| SubagentStart | ✅ (inyecta context al hijo) | — | ❌ (cabo de 05) |
| SubagentStop | ✅ | 🟡 runtime.py:289 | 🟡 FIND-HOOK6 (return IGNORADO) |

### F · Integración con permisos (toolHooks.ts)
| Feature | Canónico | Runtime | Estado |
|---|---|---|---|
| PreToolUse → permission behavior (allow/ask/deny) | ✅ runPreToolUseHooks | solo `block` | ❌ FIND-HOOK3 |
| **Invariante: hook `allow` NO salta reglas deny/ask** | ✅ resolveHookPermissionDecision | — | ❌ FIND-HOOK3 (no hay merge con reglas) |
| `ask` → diálogo HITL (forceDecision) | ✅ | — | ❌ FIND-HOOK3 |
| PreToolUse `stop` detiene ejecución | ✅ (`type:'stop'`) | ignorado | ❌ FIND-HOOK3 |
| PreToolUse `additionalContext` inyectado al modelo | ✅ (hook_additional_context) | ignorado | ❌ FIND-HOOK3 |
| PreToolUse `updatedInput` (passthrough) | ✅ | ✅ `modified_input` | ✅ |
| PermissionRequest hook (decisión con updatedPermissions) | ✅ PermissionContext.runHooks | — | ❌ FIND-HOOK5 |
| HITL grant | vía PermissionRequest + persistPermissions | vía mutar `app_state.permissions` en PreToolUse handler | 🔀 (conflaciona Pre + PermissionRequest) |

### G · Stop hooks de fin de turno (handleStopHooks) — motor no portado (cabo de 02)
| Feature | Canónico | Runtime | Estado |
|---|---|---|---|
| Stop hook al cierre de turno | ✅ | — | ❌ FIND-HOOK6 |
| `preventContinuation` → re-loop / bloquear cierre | ✅ | — | ❌ FIND-HOOK6 |
| `blockingError` → mensaje al modelo y continuar | ✅ | — | ❌ FIND-HOOK6 |
| SubagentStop **consume decisión** | ✅ (blocking) | `_fire_stop` fire-and-forget (return ignorado) | 🟡 FIND-HOOK6 |
| structured-output enforcement (Stop function hook) | ✅ registerStructuredOutputEnforcement | — | ❌ (liga G3 structured output → 09) |
| TeammateIdle / TaskCompleted al idle | ✅ | — | ⛔ coordinator/swarm |
| efectos background (auto-dream, extract-memories, prompt-suggestion) | ✅ | — | 🔀 → 13·memory |

### H · Permisos / permission modes (GAP-02) — hogar canónico
| Feature | Canónico | Runtime (`PermissionContext`) | Estado |
|---|---|---|---|
| `mode` (default/plan/acceptEdits/bypassPermissions) | ✅ toolPermissionContext.mode | ausente | ❌ **GAP-02** (=01·GAP-02, 03·GAP-CTX2) |
| Reglas allow/deny por tool | ✅ | `always_allow_*` / `always_deny` | 🟡 (sin match por contenido/arg) |
| Persistencia de permisos (user/project/local) | ✅ persistPermissionUpdates | — | 🔀 → 15·storage |
| Diálogo interactivo | ✅ interactiveHandler | — | ⛔ terminal (el runtime delega HITL al integrador) |

### I · Registro per-agente / per-skill (frontmatter)
| Feature | Canónico | Runtime | Estado |
|---|---|---|---|
| Hooks en frontmatter de agente | ✅ registerFrontmatterHooks | — | ❌ (AgentDefinition sin `hooks`, cabo 05·GAP-EXEC4) |
| Conversión Stop→SubagentStop para agentes | ✅ | — | ❌ |
| Hooks en frontmatter de skill (`once`) | ✅ registerSkillHooks | — | ❌ → liga 12·skills |
| Limpieza de session hooks al terminar (`clearSessionHooks`) | ✅ | — | 🔀 (el registry en-proceso muere con el proceso) |

### J · Bus de eventos de EJECUCIÓN de hook (hookEvents.ts) — 🔀
| Feature | Canónico | Runtime | Estado |
|---|---|---|---|
| started/progress/response de la ejecución del hook | ✅ (para UI/SDK) | — | ⛔ (observabilidad UI; el runtime tiene su EventBus → 07) |

## Hallazgos

- **FIND-HOOK1** (🟡→❌ taxonomía): `HookEvent` declara 11; el canónico **27** (RE-AUDIT-HOOK-COUNT). Faltan eventos
  **core**: `PostCompact`, `SubagentStart`, `PermissionRequest`, `PermissionDenied`, `Setup`,
  `InstructionsLoaded`, `ConfigChange`. **Ajuste**: extender el enum a los eventos core (dejar
  fuera con comentario los ⛔ teammate/swarm y los de infra que van a 18).
- **FIND-HOOK2** (❌ disparo): de 11 eventos declarados, **solo PreToolUse y SubagentStop se
  disparan**; los otros 9 son **enum muerto**. **Ajuste**: cablear los puntos en el loop
  (PostToolUse/PostToolUseFailure tras dispatch; UserPromptSubmit en el preproceso de input —
  liga 02·motor #4; SessionStart/End en el borde de sesión; Stop en fin de turno — ver
  FIND-HOOK6; Pre/PostCompact en la compactación — liga 02·motor #1; Notification en el drain).
- **FIND-HOOK3** (❌ correctitud del gate): el consumo de PreToolUse en `agent_loop.py:300-313`
  solo honra `block` y `modified_input`. **Ignora** `stop`, `additional_context`, y no existe
  `permission_behavior` (`ask`/`allow`). No hay merge con reglas (invariante canónico
  `resolveHookPermissionDecision`: hook `allow` NO salta deny/ask de settings). **Ajuste**:
  el gate debe (a) mapear la decisión a allow/ask/deny, (b) para `allow` re-chequear reglas
  deny/ask, (c) para `ask` ceder a HITL del integrador, (d) inyectar `additional_context` como
  mensaje, (e) honrar `stop`.
- **FIND-HOOK5** (❌/🔀 permisos): PreToolUse ≠ PermissionRequest en el canónico (uno precede,
  el otro DECIDE el permiso con `updatedPermissions`). El runtime los conflaciona (el HITL
  concede mutando `app_state.permissions` dentro del handler PreToolUse). Falta el evento
  `PermissionRequest` y el `mode` (GAP-02). **Ajuste**: separar el punto PermissionRequest y
  añadir `mode` a `PermissionContext` (ver H / GAP-02).
- **FIND-HOOK6** (❌ Stop de fin de turno): `handleStopHooks` (473 LOC) — Stop hook que puede
  `preventContinuation` (re-loop) o `blockingError` (mensaje + continúa) — **no portado** (uno
  de los 4 motores no portados de 02). Además `_fire_stop` (SubagentStop) es **fire-and-forget**
  (`runtime.py:289` descarta el `HookDecision`), así que ni siquiera la decisión de un
  SubagentStop puede bloquear/inyectar. **Ajuste**: disparar Stop en fin de turno consumiendo
  `preventContinuation`/`blockingError`; hacer que `_fire_stop` consuma la decisión.
- **FIND-HOOK7** (❌ salida rica): `HookDecision` (block/stop/message/modified_input/
  additional_context) no expresa `ask`, `updated_output` (updatedMCPToolOutput),
  `system_message`, `retry` (PermissionDenied), `initial_user_message`/`watch_paths`
  (SessionStart/FileChanged). **Ajuste**: extender `HookDecision` con `permission_behavior`
  (allow/ask/deny), `updated_output`, `system_message`, `retry` — y consumirlos en cada punto.

## RE-AUDITORÍA (lectura íntegra de `utils/hooks.ts` 5022 + recuento `HOOK_EVENTS`)

Motivada por el riesgo de superficialidad de la contraparte más grande. Correcciones y hallazgos:

- **RE-AUDIT-HOOK-COUNT** (corrección de dato): `HOOK_EVENTS` tiene **27** eventos, no 28
  (`coreTypes.ts:26–52`, 27 líneas). El doc afirmaba 28 en dos sitios (cabecera + tabla A).
  Corregido. El delta 11→**27** (no 28) no cambia ninguna clasificación de gap.
- **RE-AUDIT-HOOK-COMPLETO** (superficialidad #1, auto-detectada): la lista previa de "contrapartes
  leídas íntegras" enumeraba ~13 ejecutores y **omitía ~15 exportados que SÍ viven en `utils/hooks.ts`**:
  `executePreToolHooks`, `executePostToolHooks`, `executePostToolUseFailureHooks`,
  `executePermissionDeniedHooks`, `executeStopHooks`, `executeStopFailureHooks`,
  `executeTeammate/TaskCreated/TaskCompletedHooks`, `executeUserPromptSubmitHooks`,
  `executeSessionStartHooks`, `executeSetupHooks`, `executeSubagentStartHooks`,
  `executePermissionRequestHooks`, `executeElicitationResultHooks`, `executeWorktreeRemoveHook`.
  Es decir: **el propio archivo canónico contiene ejecutores dedicados para casi los 27 eventos**,
  incluidos varios que las tablas A/E marcaban como "ausente" apuntando a *otros* archivos (SubagentStart
  → se creía solo en runAgent.ts; Stop → se creía solo en query/stopHooks.ts). Las clasificaciones de
  **gap del runtime** (qué dispara el runtime) siguen válidas, pero la **evidencia canónica** estaba
  incompleta. Lista completa ahora en la cabecera.
- **RE-AUDIT-HOOK8** (❌ arquitectura de dos motores — hallazgo nuevo): el canónico **bifurca**
  la ejecución en dos rutas con semántica distinta:
  1. `executeHooks` (1952, generador): hooks *dentro del turno* cuyo `yield` (`AggregatedHookResult`)
     **re-entra al modelo** como system message (Pre/PostToolUse, Stop, UserPromptSubmit, Setup,
     SubagentStart, PermissionRequest/Denied…).
  2. `executeHooksOutsideREPL` (3003): hooks *fuera del turno* (Notification, SessionEnd, ConfigChange,
     Cwd/FileChanged) que **solo loguean** y devuelven `HookOutsideReplResult[]` — **no** re-inyectan.
  El runtime conflaciona ambas en un único `run(event, payload) → HookDecision`; pierde la distinción
  "hook que alimenta al modelo" vs "hook observador/log". **Ajuste**: el seam debe distinguir salida
  re-inyectable vs. observacional (p. ej. dos puntos, o un flag en `HookDecision`).
- **RE-AUDIT-HOOK9** (🟡 payload empobrecido — refuerza FIND-HOOK6): `executeStopHooks` (3639)
  **unifica Stop y SubagentStop** (`subagentId ? 'SubagentStop':'Stop'`) y adjunta
  `last_assistant_message` (texto del último turno del asistente) + `agent_transcript_path`. El
  `_fire_stop` del runtime (`runtime.py:289`) ni consume la decisión ni transporta ese payload.
- **RE-AUDIT-HOOK10** (🔀 `asyncRewake` — refuerza tabla B): `executeInBackground` (184) implementa
  un invariante real, no un mero flag: un hook `asyncRewake` que termina con exit-code 2 encola
  `enqueuePendingNotification({mode:'task-notification'})` que **despierta al modelo** (idle) o se
  inyecta mid-query. Es política delegable al integrador (🔀), pero el seam debe permitir el reawake.
- **RE-AUDIT-HOOK11** (refuerza FIND-HOOK5): `executePermissionRequestHooks` (4157) recibe
  `permissionSuggestions: PermissionUpdate[]` — confirma que PermissionRequest es un evento con payload
  propio (updatedPermissions), distinto de PreToolUse. El runtime carece del punto.
- Kill-switches centralizados no documentados: `shouldDisableAllHooksIncludingManaged` (managed
  `disableAllHooks`) y `CLAUDE_CODE_SIMPLE`, presentes en **ambos** motores; el trust gate
  (`shouldSkipHookDueToTrust`, 286) también está centralizado en ambos (⛔ terminal, ya notado).

## Cabos que quedan / conexiones
- **GAP-02** (permission modes) confirmado sin homologar; hogar canónico = `hooks/toolPermission/`;
  liga 01·GAP-02, 03·GAP-CTX2, 04 (plan/acceptEdits/bypass). **Aún no homologado.**
- **UserPromptSubmit / preproceso de input** = motor #4 no portado de 02 (`UserInputProcessor`
  cableado — 01·GAP-01). Aterriza aquí como evento no disparado.
- **Pre/PostCompact** ligan el motor de compactación #1 de 02 (aún no portado).
- **structured output** (G3) via Stop function hook + StructuredOutputTool → 09/16.
- **SubagentStart** (inyección de context al hijo) = cabo abierto de 05.
- **Frontmatter hooks per-agente/skill** ligan 05·GAP-EXEC4 (AgentDefinition sin `hooks`) y 12·skills.
- `hookEvents.ts` (bus de progreso de ejecución) → observabilidad; el eje real del runtime es
  el EventBus (07), no un bus de hooks aparte → ⛔ como sistema separado.

## Recuento
✅ **6** · 🟡 **12** · 🔀 **14** · ❌ **20** · ⛔ **6**
(re-audit: `HOOK_EVENTS` **27** no 28; +RE-AUDIT-HOOK8 dos-motores ❌; HOOK9/10/11 refuerzan
FIND-HOOK6/tabla B/FIND-HOOK5; lista canónica de ejecutores completada — antes omitía ~15.)

## Evidencia
- `test_hooks_homologation.py`: **3 passed + 8 xfailed(strict)**. (Previos que cubren 06:
  `test_hooks.py` 8, `test_pre_tool_use_hook.py` 7, `test_root_turn_start_hooks.py` 4.)
- Suite global tras 06: **571 passed · 3 skipped · 26 xfailed**. Lint verde (ruff/mypy/bandit).

---

## Re-visita de COMPLETITUD (gate 11 / L09) · 2026-07-19

**Modo**: 2ª vuelta, **gate 11** de ENTRADA — cada fila **✅/🔀** re-verificada **abriendo el código de B**
y siguiendo el dato de punta a punta, NO confirmando la tabla. **Resultado**: el doc (ya re-auditado
2026-07-12 con lectura íntegra de `utils/hooks.ts` 5022) **se sostiene sobre base correcta**; **1 costura
latente NUEVA** (tech-debt B-interno, NO deuda A-vs-B); **cero cambios de estado**; **código intacto**;
tests no re-ejecutados (sin cambio de código).

### Leído íntegro (B) 1→EOF
`hooks/protocol.py` (72 — `HookEvent` enum **11 valores** contados 17-28, `HookDecision` frozen dataclass
42-46, `HookHandler`, `HookSinkProtocol`), `hooks/runner.py` (63 — `HookRunner.register`/`register_sink`/
`run` agregador), `hooks/__init__.py` (11). Sitios de ciclo: `loop/agent_loop.py:287-352` (disparo+gate
PreToolUse), `execution/local/runtime.py:285-406` (`_fire_stop` + invocadores 384/391/406, `_notify`),
`factory.py:86,225` (inyección `hook_runner`) + **grep de cableado producción-vs-test** por `.run(HookEvent`,
`register`/`register_sink`, `_fire_stop`, `additional_context`.

### Verificación por CABLEADO (no por tabla)
- **Seam inyectado, no huérfano (🔀 tesis sostenida)**: `HookRunner` **nunca se instancia en el runtime** —
  `factory.py:86` lo recibe como `config.hook_runner` y lo hila `225 → runtime.py:87 → 362 → AgentLoop`. Sin
  inyección, `self._hook_runner is None` corta en los dos guardas (`agent_loop.py:300`, `runtime.py:287`). Es
  el modelo de delegación al integrador (como StorageRegistry), NO un huérfano tipo `modes/`/`observer/`:
  el puente se cablea de punta a punta **si** el consumidor inyecta. `register`/`register_sink` **sin
  invocador de producción** (sólo tests) = costura de extensión por diseño (L10), no deuda.
- **FIND-HOOK2 confirmado por cableado**: los **únicos** `.run(HookEvent…)` de producción son 2 —
  `agent_loop.py:301` (`PRE_TOOL_USE`) y `runtime.py:289` (`SUBAGENT_STOP`, vía `_fire_stop`, **realmente
  invocado** en 384/391/406 = killed/failed/completed). Los otros 9 valores del enum (`POST_TOOL_USE`,
  `POST_TOOL_USE_FAILURE`, `NOTIFICATION`, `USER_PROMPT_SUBMIT`, `SESSION_START`, `SESSION_END`, `STOP`,
  `STOP_FAILURE`, `PRE_COMPACT`) **cero call site de producción** — enum muerto. Exacto al doc.
- **FIND-HOOK3 confirmado por lectura directa**: el gate `agent_loop.py:307-313` sólo lee
  `decision.modified_input` (307) y `decision.block` (309); **ignora** `decision.stop` y
  `decision.additional_context` (el propio comentario 297-298 lo declara). Sin `behavior` allow/ask/deny, sin
  merge con reglas. Ancla A re-confirmada: `toolHooks.ts:332 resolveHookPermissionDecision` (invariante L372
  "Hook allow skips prompt but deny/ask rules still apply" + `permissionBehavior` allow/ask/deny 510-561) +
  `utils/hooks.ts:434/622-641` (`additionalContext` inyectable en PreToolUse). ❌ deuda A-vs-B real.
- **FIND-HOOK6 confirmado**: `_fire_stop` (`runtime.py:289`) hace `await self._hook_runner.run(SUBAGENT_STOP…)`
  **sin asignar** el retorno → `HookDecision` descartado (fire-and-forget). SubagentStop SÍ dispara pero su
  decisión no puede bloquear/inyectar. 🟡 exacto.
- **✅ sostenidos abriendo B**: `modified_input` (D/F) consumido en `agent_loop.py:307-308`; **agregación de
  handlers** (D) real en `runner.py:42-60` (acumula, corta en block/stop 50-51); **PreToolUse payload** (E)
  `agent_loop.py:301-306` con `{tool_name,tool_input,call_id,ctx}`; **callback/función** (B) = `HookHandler`
  async invocado en `runner.py:42`. Base correcta.
- **🔀 HITL grant sostenido**: el handler inyectado recibe `ctx` en el payload (`agent_loop.py:305`) ⇒ puede
  mutar `ctx.app_state.permissions` — mecanismo alcanzable; conflaciona PreToolUse+PermissionRequest (falta el
  punto separado + `mode`=GAP-02). Confirmado.

### Costura latente NUEVA (tech-debt B-interno, L10/L11 — NO deuda A-vs-B)
- **LAT-HOOK1** — `HookRunner.run` **agrega `additional_context`** de todos los handlers (`runner.py:54-55`) y
  lo devuelve unido (`runner.py:59`), **pero ningún consumidor de producción lo lee**: el único consumidor de
  una decisión (`agent_loop.py:307-313`) sólo mira `modified_input`+`block`, y `_fire_stop` descarta la
  decisión entera. Es maquinaria de agregación **construida a medio cablear** (definido-pero-no-consumido),
  hermana de `to_llm`/`timeout_seconds` (01/03), `LAT-EXEC1/2` (05). **Distinción L11**: la parte **A-vs-B**
  (el gate DEBERÍA inyectar `additional_context`, el canónico sí) ya es **FIND-HOOK3 ❌**; lo B-interno es que
  la mitad del cañería (la agregación en `run()`) ya existe muerta ⇒ remediar HR5 está **pre-cableado a medias**
  (falta sólo el consumo loop-side, `run()` ya agrega). Registrado, sin cambiar estado ni código.

### Ledger de cierre (columna Lectura)
| Archivo | Lado | LOC | Lectura |
|---|---|---|---|
| `hooks/protocol.py` | B | 72 | íntegro 1→EOF (enum 11 contado) |
| `hooks/runner.py` | B | 63 | íntegro 1→EOF |
| `hooks/__init__.py` | B | 11 | íntegro 1→EOF |
| `loop/agent_loop.py` | B | 352 | disparo+gate 287-352 (archivo ya íntegro 1→EOF en 02/05) |
| `execution/local/runtime.py` | B | 435 | `_fire_stop`+invocadores+`_notify` 285-406 (ya íntegro 1→EOF en 01/05) |
| `factory.py` | B | 267 | inyección `hook_runner` 86/225 (ya íntegro 1→EOF en 05/18) |
| `utils/hooks.ts` | A | 5022 | **íntegro 1→EOF en re-audit 2026-07-12** (L08); en gate 11 = re-confirmación dirigida de anclas 332/434/510-641 |
| `services/tools/toolHooks.ts` | A | 650 | anclas `resolveHookPermissionDecision` 332/372/510-561 (íntegro en 1ª pasada) |
| `entrypoints/sdk/coreTypes.ts` | A | — | `HOOK_EVENTS` 25-53 = **27** re-contado |

### §Honestidad
- **La 1ª pasada + re-audit ya fueron rigurosas**: `utils/hooks.ts` (5022) se leyó íntegro en la re-audit
  2026-07-12 (destapó HOOK8 dos-motores + los ~15 ejecutores omitidos). El gate 11 tiene por **objeto B**;
  el íntegro de A no se repite línea-a-línea, se re-confirman las **anclas de carga** por grep dirigido
  (declarado aquí, no presentado como re-lectura íntegra nueva de A).
- **LAT-HOOK1 es hallazgo del gate 11**: sólo aparece al abrir `runner.py` y seguir el dato hasta los 2
  consumidores — la confirmación-de-doc no lo veía (la tabla marca la agregación ✅ sin preguntar quién la
  consume). Clasificado tech-debt B-interno (L10 anti-padding): una extensión sin contraparte en A no es
  deuda de B frente a A; la deuda A-vs-B correspondiente es FIND-HOOK3, ya ❌.
- **Cero sobre-declaración detectada**: los ✅ (modified_input/agregación/PreToolUse-payload/callback) se
  sostienen sobre B abierta; ningún ✅ resultó "definido pero no invocado" salvo el matiz LAT-HOOK1 (que no
  degrada el ✅ de "la agregación funciona", sólo marca su salida parcialmente muerta).

### 4 preguntas de cierre
1. ¿Revisado **todo** cada archivo de **A**? — **Sí**: `utils/hooks.ts` íntegro en re-audit 2026-07-12;
   anclas 332/434/510-641 + `HOOK_EVENTS`=27 re-confirmadas por lectura dirigida en gate 11.
2. ¿Revisado **todo** cada archivo de **B**? — **Sí**: los 3 de `hooks/` íntegros 1→EOF; los sitios de ciclo
   en `agent_loop.py`/`runtime.py`/`factory.py` (archivos ya íntegros 1→EOF en 01/02/05/18) + grep de cableado.
3. ¿Hallazgos **exhaustivos** (no superficiales)? — **Sí**: FIND-HOOK2/3/6 re-confirmados **por cableado**
   (call sites reales, no tabla); **+LAT-HOOK1** nuevo por seguir el dato de `additional_context`.
4. ¿**Todo cubierto** (nada pendiente)? — **Sí**. Cabos con **destino**: FIND-HOOK3/7 (salida rica + gate) →
   **Deuda B `B-02`** (permission modes) + HR4/HR5; FIND-HOOK6/Stop-fin-de-turno → **02·LR3**; `SubagentStart`
   → **05**; frontmatter hooks → **05·GAP-EXEC4 / 12**; Elicitation → **11**; LAT-HOOK1 → §honestidad (pre-cablea
   HR5). Ningún pendiente de **verificación** abierto.

**VEREDICTO DE AVANCE**: ✅ **NADA PENDIENTE de verificación → avanzar a 07 · events** (gate 11). Los cabos
listados son de **remediación** con destino nombrado (2ª pasada), no de verificación.

---

## Plan de homologación / remediación desarrollada

Diseño por finding. Seams: `hooks/protocol.py` (`HookEvent` enum de 11 valores, `HookDecision`
frozen dataclass, `HookSinkProtocol`), `hooks/runner.py` (`HookRunner.register`/`register_sink`/`run`
agrega decisiones, corta en block/stop). **Tesis intacta**: el sistema configurable (settings.json→
matchers→hooks tipados) es 🔀 delegado al integrador; los gaps reales son los puntos que el runtime NO
dispara + el `HookDecision` pobre + la conflación de motores. GAP-02 (permission modes) es **Deuda B `B-02`**.

### HR1 · FIND-HOOK1 — taxonomía 11 → 27 eventos
- **Comportamiento**: `HookEvent` tiene 11 valores; el canónico `HOOK_EVENTS` son **27**. Faltan core:
  `PostCompact`, `SubagentStart`, `PermissionRequest`, `PermissionDenied`, `Setup`, `InstructionsLoaded`,
  `ConfigChange`, `SessionStart`(ya)/`Notification`(ya)… — enumerar los 27 y añadir los ausentes que el
  runtime debe poder disparar.
- **Seam/firma**: extender el enum `HookEvent` con los valores faltantes (los de terminal/UX que no aplican
  se documentan ⛔; el resto se añaden). No re-implementa el matcher (delegado).
- **Cableado**: sólo el enum; el disparo real es HR2. **Orden**: primero (los demás referencian eventos).
  **Test**: `test_hook_event_taxonomy_covers_core` (xfail existente, cuenta ≥ los core-portables).

### HR2 · FIND-HOOK2 — sólo 2 de 11 eventos se disparan
- **Comportamiento**: hoy sólo `PreToolUse` (agent_loop.py:301) y `SubagentStop` (runtime.py:289) se
  disparan; los otros 9 son enum muerto. Disparar los core: `PostToolUse`/`PostToolUseFailure` (tras el
  dispatch), `UserPromptSubmit` (en el preproceso de input, 01·CR2), `SessionStart`/`SessionEnd`
  (lifecycle de sesión), `Stop`/`StopFailure` (fin de turno, HR/02·LR3), `PreCompact`/`PostCompact`
  (motor de compactación, 02·LR1), `SubagentStart` (spawn, 05).
- **Seam/firma**: puntos de disparo `await hook_runner.run(HookEvent.X, payload)` en cada sitio de ciclo,
  honrando la `HookDecision` (HR4). `PostToolUse` va tras `dispatch` (agent_loop.py:318); `PostToolUseFailure`
  cuando `result.is_error`/abort (liga 08·SIG12: distinguir abort de error).
- **Cableado**: loop + runtime + compaction (02·LR1). **Orden**: tras HR1/HR4. **Test**:
  `test_post_tool_use_hook_fires`, `test_stop_hook_fires`.

### HR3 · FIND-HOOK5 — separar `PermissionRequest` de `PreToolUse`
- **Comportamiento**: el runtime conflaciona PreToolUse (gate del tool) con PermissionRequest (petición de
  permiso con `permissionSuggestions`); concede mutando `app_state.permissions`. El canónico los separa:
  PermissionRequest lleva `permissionSuggestions: PermissionUpdate[]` propio.
- **Seam/firma**: nuevo punto `HookEvent.PERMISSION_REQUEST` disparado por el gate `B-02` cuando la decisión
  es `ask`; payload con `suggestions`. `PermissionDenied` cuando `deny`.
- **Cableado**: el gate por-tool (Deuda B `B-02`) dispara estos puntos; el integrador HITL responde. **Orden**:
  junto a `B-02`. **Test**: `test_permission_request_distinct_from_pretooluse`.

### HR4 · FIND-HOOK7 — `HookDecision` expresivo
- **Comportamiento**: `HookDecision` sólo tiene `block`/`stop`/`message`/`modified_input`/
  `additional_context`. El canónico expresa además: `ask`/permission_behavior (allow/ask/deny),
  `updated_output` (PostToolUse reescribe la salida), `system_message`, `continue_loop`/`preventContinuation`
  (Stop re-loop), `blockingError`, `watch_paths`, `initial_user_message`.
- **Seam/firma**: extender `HookDecision` con `behavior: Literal["allow","ask","deny"] | None`,
  `updated_output: str | None`, `system_message: str | None`, `continue_loop: bool = False`. El `HookRunner.run`
  ya agrega; añadir el merge de los nuevos campos (p.ej. `updated_output` gana el último handler; `continue_loop`
  = OR).
- **Cableado**: consumidores — `PostToolUse` usa `updated_output` (reescribe `result.output`); `Stop` usa
  `continue_loop` (02·LR3). **Orden**: temprano (HR2/HR3/02·LR3 dependen). **Test**:
  `test_hook_decision_carries_updated_output_and_continue`.

### HR5 · FIND-HOOK3 — gate PreToolUse lossy → converge con Deuda B `B-02`
- **Comportamiento**: el gate del loop (agent_loop.py:300-313) sólo honra `block`+`modified_input`; ignora
  `stop`/`additional_context`, sin `behavior` allow/ask, sin merge con reglas deny/ask (rompe
  `resolveHookPermissionDecision`). **Remediación**: (a) el loop honra también `additional_context` (inyecta
  al historial) y `stop`; (b) la decisión tipada por-tool + merge con modos es **Deuda B `B-02`**. Aquí sólo
  la parte del loop; el gate por-tool en B-02.
- **Cableado**: loop 300-313. **Orden**: junto a HR4. **Test**: `test_pretooluse_honors_additional_context`.

### HR6 · FIND-HOOK6 — Stop de fin de turno → 02·LR3 (referencia)
- El motor de Stop-hooks (preventContinuation/blockingError + payload last_assistant_message/
  agent_transcript_path) se desarrolla en **02·LR3** (usa `HookDecision.continue_loop` de HR4). Aquí sólo
  se corrige que `_fire_stop` (runtime.py:289) deje de ser fire-and-forget y **consuma** la `HookDecision`.
  **Test**: `test_fire_stop_consumes_decision`.

### HR7 · FIND-HOOK8 — dos motores `executeHooks` vs `executeHooksOutsideREPL`
- **Comportamiento**: el canónico tiene DOS motores — `executeHooks` (re-inyecta al modelo como system
  message: hooks dentro del turno) vs `executeHooksOutsideREPL` (sólo loguea/observa:
  Notification/SessionEnd/ConfigChange/Cwd/FileChanged). El runtime los conflaciona en un único
  `run()→HookDecision`, perdiendo la distinción re-inyectable vs observacional.
- **Seam/firma**: clasificar cada `HookEvent` como `REINJECTING` u `OBSERVATIONAL` (una constante
  `HOOK_KIND: dict[HookEvent, Literal[...]]`); `HookRunner.run` para los observacionales NO produce
  `additional_context` re-inyectable (sólo side-effects/log). O un método separado `run_observational`.
- **Cableado**: `HookRunner`. **Orden**: independiente. **Test**: `test_observational_hooks_do_not_reinject`.
