# PROGRESS — retoma de la homologación (2ª vuelta / MODO VALIDACIÓN)

> Backbone portable de retoma. Una entrada por categoría **validada** en la 2ª vuelta.
> A = canónico (`/home/noheroes/python/claude-code/src`) · B = runtime
> (`/home/noheroes/python/agentic_runtime/src/agentic_runtime`) · Salida = este directorio
> (`.../agentic_runtime/src/HOMOLOGATION/`). Orden: 01→18 + Deuda B.
> PASO 0 de cada categoría: releer ÍNTEGRAS **SÓLO** `~/.claude/skills/analisis-comparativo-ab/lecciones/*.md`
> (00-05/07-11) y activar las puertas. **El mirror `learned_lessons/` quedó RETIRADO como fuente de método
> (2026-07-19)** — ya no se lee. Reconciliación: las menciones de "`learned_lessons/09`" en el log de abajo =
> lección **11** de la skill (validar-completitud-no-confirmar-doc); MODO VALIDACIÓN se rige por ese gate 11.

---

## 01 · contracts — VALIDADA (con corrección menor) · 2026-07-17

**Modo**: validación sobre doc existente. **Resultado**: discrepancia menor (sub-declaración) corregida en el doc; código intacto.

- **Leído íntegro (B)**: los 6 archivos de `contracts/` 1→EOF (`runtime.py` 67, `permissions.py` 33,
  `compaction.py` 27, `storage.py` 40, `user_input.py` 46, `__init__.py` 17 = 230 LOC) + tramos
  `loop/agent_loop.py:293,330` y `execution/local/runtime.py:208-209`.
- **Discrepancia encontrada**: la tabla de la 1ª pasada enumeraba 6 de 8 campos de `RuntimeTask` — omitía
  `max_turns` y `timeout_seconds`. Añadidos como feat 14/15. Conteo 13→15 features (✅4·🟡6·🔀3·❌1).
- **Confirmado sin cambios**: GAP-01 (`UserInputProcessor` sin cablear en el loop; sólo lo referencia su
  test — el `process_slash_command` que sí se usa es el de `capabilities/skills`, otra firma), GAP-02
  (`PermissionContext` sin `mode`; plan-mode vía `app_state.native["plan_mode"]`), FIND-01
  (`@runtime_checkable` inconsistente: `UserInputProcessor`/`CompactionProvider` sin decorar).
- **Cabo resuelto**: autogen `user_/sess_<hex>` → `execution/local/runtime.py:208-209` (simétrico).
- **Cabos con destino**: `max_turns`→05·FIND-EXEC5; `timeout_seconds`→05 (o retiro); `model_override`/
  `fork_context`→05; `StorageContract` vs `StorageProtocol`→15 (ya RESUELTO allí); GAP-02 decisión→Deuda B `B-02`.
- **Doc**: `01-contracts.md` actualizado (filas 14/15, §Resumen, §Notas 2/3, **ledger de cierre + §nota de
  honestidad + 4 preguntas** añadidos). README fila 01 actualizada.

**SIGUIENTE → 02 · loop.** Ojo (2ª vuelta): archivo más grande = `loop/agent_loop.py` (leer 1→EOF, cerrar
huecos, L08); es categoría de ensamblado del turno → verificar **cableado** (L09) de motor de compactación,
retry/fallback (FIND-MODELS5/6/7), `max_turns` (FIND-EXEC5), overflow (FIND-MODELS11). Contra canónico
`query.ts`/`QueryEngine.ts`.

---

## 02 · loop — VALIDADA (con corrección de etiquetado) · 2026-07-17

**Modo**: validación. **Resultado**: doc sustantivamente correcto y line-preciso; única corrección = etiquetado de GAP-IDs (no cambia estados). Código intacto.

- **Leído íntegro (B)**: los 5 archivos de `loop/` 1→EOF (413 LOC; `agent_loop.py` 352 barrido punta a punta,
  huecos cerrados). Refs de línea del doc verificadas EXACTAS (189/267-270/274-281/300-313/329-339/348).
- **Anclas A re-confirmadas** (grep dirigido a líneas exactas sobre `query.ts` ya-íntegro en 1ª pasada):
  `yieldMissingToolResultBlocks`:123/984 (rama error→FIND-L1), `maxTurns`/`max_turns_reached`:1508-1511/1705,
  `attemptWithFallback`/`FallbackTriggeredError`:650-655/894-897, `microcompact`/`autocompact`/
  `getMessagesAfterCompactBoundary`:52/365/413, reason codes:1051/1515/1520/1711.
- **Cableado verificado (L09)**: los 4 motores ausentes (compactación, error-recovery/fallback, stop-hooks
  fin-de-turno, preproceso input) confirmados ❌ por **lectura**, no grep: `run()` no llama compactación, rama
  error sólo `[error]`+break, sólo se dispara `PRE_TOOL_USE` (no Stop al cerrar), sin `UserInputProcessor`.
  FIND-L2 confirmado: `agent_loop.py:253-254` `done=event;break` nunca lee `done.usage`.
- **Discrepancia (sólo etiquetado)**: GAP-IDs intercambiados en §Plan — LR1(compactación) decía GAP-L1/L1b→
  **GAP-L4**; LR3(stop-hooks) decía GAP-L4→**GAP-L1/L1b**; celda C4 usaba GAP-L3(=token-budget E1)→**GAP-C4**.
  Corregido en las 3 caras + ledger/§honestidad añadidos.
- **Cabos con destino**: FIND-L2→Deuda B `B-usage`; F2 gate→`B-02`+06; C2 superficie modelo→16; motores 2/4→
  05/01; path legacy `capabilities_resolver` (agent_loop.py:201-205)→**18·FaR2** (ya homed, no hallazgo nuevo).
- **Doc**: `02-loop.md` (3 correcciones de etiqueta + ledger + §honestidad + 4 preguntas). README fila 02.

**SIGUIENTE → 03 · context.** Ojo (2ª vuelta): archivos grandes A = `AppStateStore.ts` (570) + `Tool.ts` (792,
tipo ToolUseContext) + `forkedAgent.ts::createSubagentContext`; leer 1→EOF. Verificar **FIND-CTX1**
(read_file_state/read-before-edit ausente — es invariante de correctitud, cruza 10·READSTATE/EDITGUARDS) y
GAP-CTX2/3/4. Muchos 🔀 = "el campo vive en otro subsistema por diseño" → confirmar clasificación, no re-abrir
como gap de 03.

---

## 03 · context — VALIDADA (sin discrepancia sustantiva) · 2026-07-17

**Modo**: validación sobre doc existente. **Resultado**: doc correcto y line-preciso; **sin discrepancia
sustantiva** — sólo se añadió el bloque de cierre (ledger+§honestidad+4 preguntas) que la 1ª pasada no llevaba.
Código intacto; doc intacto en sustancia.

- **Leído íntegro (A)**: `Tool.ts` (792, el más grande — L08) 1→EOF: `ToolUseContext`(158-300) enumeración
  íntegra de los ~45 campos A1-A33 (incl. las 15 UI-callbacks de A33); `AppStateStore.ts` (569) 1→EOF:
  `AppState`(89-452) B1-B12 + `getDefaultAppState`(456-569); `context.ts` (189) 1→EOF (F1-F5).
  `forkedAgent.ts::createSubagentContext` (345-462) tramo íntegro (E1-E8).
- **Leído íntegro (B)**: los 4 de `context/` (`tool_use.py` 70 / `adapters.py` 85 / `presentation.py` 25 /
  `__init__.py` 11 — LOC EXACTOS al doc) + cruces `contracts/permissions.py` (33) y `execution/fork/__init__.py`
  (96) íntegros; `execution/local/runtime.py` tramos 204/314-316/332.
- **4 findings confirmados por lectura directa (no grep)**: FIND-CTX1 (`ToolUseContext`/`ForkSnapshot` sin
  `read_file_state`), GAP-CTX2=GAP-02 (`PermissionContext` sin `mode`; canónico sí en AppStateStore.ts:500-503),
  FIND-CTX2 (`ToolUseContext` sin `agent_type`; sólo `ForkContext.subagent_type`), GAP-CTX3 (`context.ts` prepend
  git+fecha+CLAUDE.md no portado), GAP-CTX4 (`ForkSnapshot` sin `rendered_system_prompt`).
- **Falsa discrepancia descartada (L10 doble filo)**: `RuntimeContextForker.fork` no propaga `subagent_depth`/
  `is_subagent`; parecía E8/A29 sobre-declarado. Al abrir `execution/local/runtime.py` se confirmó el cableado
  (204 `depth+1`, 316 `ctx.subagent_depth=`, 315 `ctx.is_subagent=parent is not None`) + tope en `agent.py:73`.
  **E8 ✅ es correcto**; vive en 05 por diseño.
- **Tests target (L05)**: 3 xfail(strict) con anclas exactas verificadas 1→EOF (`test_..._tracks_read_file_state`
  →Tool.ts:181, `test_..._permissions_carry_mode`→AppStateStore.ts:109+Tool.ts:124, `test_..._carries_agent_type`
  →Tool.ts:246). Siguen xfail = gaps abiertos, no xpass. Suite no re-ejecutada (MODO VALIDACIÓN).
- **Imprecisión menor NO corregida**: encabezado cita "ToolPermissionContext (123-148)"; el tipo es 123-138 y
  `getEmptyToolPermissionContext` 140-148 (internas de permisos → 06). Declarado en §honestidad, doc sin cambio.
- **Cabos con destino**: FIND-CTX1→10·R0 (+CtxR1 cableado fork); GAP-CTX2→Deuda B `B-02`; GAP-CTX3→05·GAP-EXEC5;
  CtxR4/GAP-CTX4→05·fork; los 🔀 "otro subsistema": modelo→16, mcp→11, tasks/agents→05, hooks/permisos→06,
  skills→12, todos→10.
- **Doc**: `03-context.md` (bloque "Ledger de cierre 2ª vuelta" + §honestidad + 4 preguntas). README fila 03.

**SIGUIENTE → RE-VISITAR 01·contracts + 02·loop bajo el lente de COMPLETITUD (learned_lessons/09), LUEGO 04.**
Motivo (corrección del usuario 2026-07-17): 01 y 02 se "validaron" en esta 2ª vuelta ANTES de la corrección de
método — con confirmación-de-doc, no con verificación-de-completitud A-vs-B. Ahora se re-hacen con el rigor de 03:
para **cada fila ✅ y 🔀** de sus tablas, **abrir la implementación de B** que supuestamente reproduce el
comportamiento y confirmar el cableado (L09 cablear≠existir), NO aceptar la tabla. Las filas ❌ ya convergen (no
re-hacer). Método por categoría:
- **01·contracts** (`01-contracts.md`; B = `contracts/{runtime,permissions,compaction,storage,user_input}.py`
  +`__init__.py`): son formas de protocolo ⇒ la pregunta de completitud es **¿cada protocolo ✅ se CONSUME de
  verdad en la ruta real de B?** Abrir los consumidores: `loop/agent_loop.py`, `execution/local/runtime.py`,
  `capabilities/skills`. Confirmar p.ej. que `RuntimeTask`/`PermissionContext`/`StorageContract` se instancian y
  usan (no sólo se definen); GAP-01 (`UserInputProcessor` sin cablear) y CompactionProvider (motor#1 ausente, ver
  02) ya conocidos — verificar que ningún otro ✅ es "definido pero no invocado".
- **02·loop** (`02-loop.md`; B = `loop/agent_loop.py` 352 + resto de `loop/`): ya llevó verificación de cableado
  de los 4 motores ausentes (❌) — eso aguanta. Falta pasar el lente a las **✅/🔀**: G5 (abort=`ctx.stop`),
  F11 (reensamblado de `tool_pool` por turno), aplicación de `context_modifier`/`ends_turn` (agent_loop.py:329-339),
  etc. — abrir el punto de uso en B y confirmar que reproduce el comportamiento canónico, no sólo que existe.
- Al cerrar cada una: actualizar el doc (sobre la base "comportamiento-verificado-en-B"), **ledger + §honestidad
  (declarar que la 1ª ronda fue confirmación-de-doc) + 4 preguntas MOSTRADAS**; PROGRESS + memoria.

**DESPUÉS → 04·modes.**

---

## 01 · contracts — RE-VISITA COMPLETITUD (L09) · 2026-07-18

**Modo**: re-visita de completitud A-vs-B (learned_lessons/09) sobre las filas ✅/🔀. **Resultado**: 2
correcciones al doc (1 sobre-declaración real + 1 costura latente registrada); **código intacto**.

- **Leído íntegro (B)**: los 6 `contracts/*.py` (ya) + **el consumidor real `execution/local/runtime.py`
  (435 LOC) 1→EOF** + tramos de `execution/tasks/registry.py:88-124`, `tools/dispatcher.py:42,63`,
  `capabilities/resolver.py:40`, `tools/pool.py:59`, `tools/fs_env.py:124`, `capabilities/plan/plan_file.py`,
  `context/presentation.py`, `factory.py:207` + **grep de completitud por símbolo** (definido vs invocado).
- **Método L09**: para cada fila ✅/🔀, abrir el CONSUMIDOR de B y confirmar que el protocolo se invoca en la
  ruta real, NO aceptar la tabla. La 1ª ronda de 2ª vuelta fue **confirmación-de-doc** (leyó los contracts,
  no los consumidores).
- **DISCREPANCIA REAL (feat 15 · `timeout_seconds`)**: el doc lo marcaba "**sin consumidor / inerte**" — falso.
  `dispatch()` lo lee y lo pasa a `arm_watchdog` (`runtime.py:149`); lo que no impone el timeout es que el
  **default** `InMemoryTaskRegistry.arm_watchdog` (`registry.py:88-91`) sea un **no-op deliberado** (seam de
  delegación al consumidor). Reclasificado: **tech-debt B-interno** (adición a medio cablear), NO deuda A-vs-B
  (L10). Doc corregido.
- **COSTURA LATENTE (feat 11 · `PathPresentation`)**: `sanitize_output` SÍ cableado (`dispatcher.py:42` +
  `runtime.py:244`, default `IdentityPresentation` `factory.py:207`), pero `to_llm` **sin call site de
  producción** (`grep '\.to_llm(' = 0`) — misma costura que 03·context. ✅ se sostiene sobre `sanitize_output`
  (el comportamiento canónico); `to_llm` = tech-debt B-interno (L10), no deuda A-vs-B. Registrado en §honestidad.
- **Confirmados consumidos-en-ruta-real** (✅/🔀 que aguantan): feat 1 (LocalAgentRuntime = el runtime real),
  feat 2 (`prompt/description/subagent_type` 226/142/342), feat 3 `model_override` (346/351), feat 4
  `fork_context` (200), feat 5 `owner/session` (208-209), feat 6 `audio_prompt` (224), feat 7
  `PermissionContext` allow/deny (dispatcher/resolver/pool), feat 10 `StorageContract` (fs_env/plan_file),
  feat 13 FIND-01, feat 14 `max_turns` inerte confirmado (FIND-EXEC5, no pasa al `AgentLoop`). feat 9
  (`collect_compaction_context`) y feat 12 (`UserInputProcessor`) **cero consumidor de producción** confirmado
  por grep (motor#1→02, GAP-01) — el doc ya lo decía. feat 8 (GAP-02 ❌) converge, no re-hecha.
- **Doc**: `01-contracts.md` — feat 11/15 corregidas, bloque "Re-visita de completitud (L09)" con mini-ledger de
  consumidores + §honestidad ampliada (sobre-declaración corregida) + 4 preguntas re-respondidas. Header de fase
  actualizado.

**SIGUIENTE → (1º) RE-VISITA COMPLETITUD (L09) de 02·loop ✅ HECHO (2026-07-18, ver entrada más abajo),
(2º) 04·modes ← SIGUIENTE VIGENTE.** (Orden corregido por el usuario 2026-07-18: el pendiente NO se salta.)

### (1º) 02·loop — re-visita COMPLETITUD (L09) · ✅ COMPLETADO 2026-07-18 (entrada "02 · loop — RE-VISITA COMPLETITUD (L09)" abajo)
Estado: 01/03 ya re-verificados con L09; 02 se validó (2026-07-17) por **confirmación-de-doc** en sus filas
✅/🔀 (sólo los 4 motores ❌ llevaron cableado). Método: para cada fila **✅/🔀** de `02-loop.md`, abrir el punto
de uso en `loop/agent_loop.py` (352, releer **1→EOF**, L08) y confirmar que reproduce el comportamiento canónico,
NO aceptar la tabla. Focos: **G5** (abort=`ctx.stop` — seguir el dato hasta `caller.py`/`dispatcher.py`), **F11**
(reensamblado de `tool_pool` por turno — ¿se re-arma cada iteración o se cachea?), **`context_modifier`/`ends_turn`**
(`agent_loop.py:329-339`, ya verificado en 10·CORR-09-CTXMOD — confirmar que aguanta), pareo tool_use↔tool_result,
gate PreToolUse (300-313). Cazar costuras latentes definido-pero-no-invocado = tech-debt B-interno (L10), como en
01 (`to_llm`/`timeout_seconds`). Los 4 motores ausentes (❌) ya llevaron cableado en la 1ª ronda (aguantan, no
re-hacer). Cierre: doc + ledger + §honestidad (declarar confirmación-de-doc previa) + 4 preguntas + **veredicto de
avance explícito** MOSTRADOS + PROGRESS + memoria.

---

## 02 · loop — RE-VISITA COMPLETITUD (L09) · 2026-07-18

**Modo**: re-visita de completitud A-vs-B (learned_lessons/09) sobre las filas ✅/🔀. **Resultado**: **1
reclasificación real** (C11/FIND-L1 sobre-declarado 🟡→🔀); **código intacto**. Cierra el ÚNICO pendiente de
verificación de la 2ª vuelta (01/02/03 ya con L09).

- **Leído/abierto (B)**: `agent_loop.py` re-leído **1→EOF** (353 líneas, L08) + **consumidores/productores**
  seguidos punta a punta (L09): `tools/dispatcher.py` (1→EOF), `tools/protocol.py` (`ToolResult`),
  `native/{ask_user:97, plan_mode:106}` (productores de `ends_turn`), `native/{worktree:102/166, plan_mode:59/101,
  todo_write:62, config:75}` + `skills/skill_tool.py:119` (productores de `context_modifier`),
  `execution/local/runtime.py` (cancel:187 / register_turn_start_hook:372-374),
  `execution/tasks/registry.py:117-124` (`kill`→`asyncio_task.cancel()`).
- **DISCREPANCIA REAL (C11/FIND-L1 🟡→🔀)**: el doc marcaba 🟡 con riesgo de API-400 asumiendo *persist-then-error*.
  Al abrir B: la rama `ErrorEvent` hace `break` en **267-270 ANTES** del bloque de persistencia **272-281** ⇒ en
  error-mid-stream los `tool_calls` buffered se **descartan** (nunca hay assistant con `tool_calls` colgante); y los
  que sí se persisten se parean 1-a-1 en 287-344 (el dispatcher **nunca lanza**, envuelve todo en `ToolResult`). El
  invariante se reproduce **por diseño** (buffer-then-commit) con mecanismo distinto al canónico
  (`yieldMissingToolResultBlocks`). ⇒ **🔀, no 🟡**. Además el doc era internamente inconsistente (LR2 ya describía
  `error→[error]+break` en 267-270). Conteo 🟡 12→**11**, 🔀 7→**8**. LR5 → sin remediación. FIND-L1 fuera de
  "hallazgos de correctitud" (queda solo FIND-L2).
- **Confirmados sobre base correcta (✅/🔀 que aguantan, cableado real seguido)**: A1/C1/D7/F1 (dispatch real);
  **F12** (`context_modifier`: 5 productores reales→loop 332-335, **no** costura muerta); **G5** (cancel→kill→
  `asyncio_task.cancel()`→`CancelledError` runtime.py:380-384, end-to-end exacto); **F4** (`ends_turn`: 2 productores
  reales); A2/E5/E6/F3/F8/F9 (divergencias de diseño con efecto reproducido). Focos 🟡 **F2/F6/F11** confirmados
  (no inflados). Sin costuras latentes nuevas tipo `to_llm`/`timeout_seconds`.
- **Doc**: `02-loop.md` — C11 reclasificado, §Resumen (11/8), FIND-L1/LR5/Notas corregidos, **bloque "Re-visita de
  COMPLETITUD (L09)" con mini-ledger de consumidores + §honestidad + 4 preguntas + VEREDICTO DE AVANCE** añadido;
  header de fase actualizado. README fila 02 actualizada.

**SIGUIENTE → 04 · modes.** (01/02/03 completos con L09; NO quedan pendientes de verificación de la 2ª vuelta.)

### 04·modes — re-visita/documentación con L09 de ENTRADA. Plan:
- **B diminuto**: `modes/{protocols.py 16, manager.py 44, __init__.py 4}`. **Carne en A**: `coordinatorMode.ts`
  (369) + `useBackgroundTaskNavigation.ts` (251) + `useSessionBackgrounding.ts` (158) → leer **1→EOF** (L08);
  abrir `backgroundHousekeeping.ts` (94) ANTES de descartar (L02, ⛔ sólo tras abrir).
- **NO re-derivar** (ya establecido en 1ª pasada): el backgrounding **real** NO vive en `modes/` sino en
  `execution/tasks/registry.py` (`TaskRecord.is_backgrounded`) + `execution/local/notification.py` +
  filtro-por-KIND en `capabilities/resolver.py`. Por eso **FIND-MODE1** = `modes/` (`AgentMode`+`ModeManager`) es
  abstracción **huérfana** (ninguna ruta la consulta; `_notify` es incondicional). Recomendación viva: eliminar
  `modes/` o cablearlo — decisión → Deuda B `B-orphans` (junto a `observer/` y `SignalBus`).
- **L09 de ENTRADA** (aplicar desde el inicio, no como 2ª ronda): las filas **✅/🔀** de `04-modes.md` se
  verifican **abriendo el código de B** que reproduce el comportamiento, NO confirmando la tabla. Ej.: B1
  (backgrounding real ✅) → abrir `registry.py`/`notification.py` y confirmar que `is_backgrounded` se **escribe
  y se lee** en la ruta real. Cazar costuras latentes tipo `to_llm`/`timeout_seconds` (definido-pero-no-invocado)
  = tech-debt B-interno (L10), distinguir de deuda A-vs-B.
- **Verificar**: FIND-MODE1 (huérfano) + GAP-MODE1 (registry no discrimina tipos de task) + GAP-MODE2 (worktree
  `safe_for_background=False` vs `ASYNC_AGENT_ALLOWED_TOOLS` canónico → ya RESUELTO en 10·FIND-NATIVE-BG,
  confirmar coherencia). ⛔ coordinator/swarm = divergencia por arquitectura (L10), no gap.
- **Al cerrar**: doc `04-modes.md` sobre base "comportamiento-verificado-en-B" + **ledger con columna Lectura +
  §honestidad + 4 preguntas MOSTRADAS al usuario** (L03/L04) + README fila 04 + PROGRESS + memoria. MODO
  VALIDACIÓN: sólo se corrige el doc si hay discrepancia, nunca el código; tests no se re-ejecutan salvo cambio.

---

## 04 · modes — VALIDADA (2ª vuelta, L09 de ENTRADA) · 2026-07-19

**Modo**: 1ª pasada de 2ª vuelta con learned_lessons/09 de ENTRADA (cada ✅/🔀 re-verificada abriendo el
código de B, no la tabla). **Resultado**: **1 discrepancia real** (GAP-MODE2 sub-enumerada: 1→4 ítems) +
1 precisión de línea (`_notify` 295→294); **código intacto**; tests no re-ejecutados (sin cambio de código).

- **Leído íntegro (A)**: los 4 archivos del alcance 1→EOF — `coordinatorMode.ts` (369, el más grande, L08),
  `useSessionBackgrounding.ts` (158), `useBackgroundTaskNavigation.ts` (251, ⛔ tras abrir L02),
  `backgroundHousekeeping.ts` (94, ⛔ tras abrir L02) + `constants/tools.ts:55-112` (allowlist + BLOCKED-block).
- **Leído íntegro (B)**: `modes/{protocols,manager,__init__}.py` (64) + **los CONSUMIDORES reales del
  backgrounding** que la re-auditoría estructural previa (2026-07-12) NO había abierto — `registry.py` (166),
  `notification.py` (72), `resolver.py` (82) íntegros; `runtime.py` `_notify` (288-327); `tools/registry.py`
  `list_available`; `safe_for_background` de cada tool nativo (agent/task_tools/worktree/ask_user/plan_mode) +
  depth-cap `agent.py:73`; `agent_loop.py:91-92` ancla exacta.
- **FIND-MODE1 confirmado por CABLEADO (no existencia)**: grep repo-wide → `modes/` importado **sólo** por
  `test_mode_manager.py` + `test_modes_homologation.py`; **cero** producción. `_notify` (runtime.py:294-304)
  incondicional: guard `parent_session_id is None` (297) → `put_notification`; **no** consulta `on_complete`/
  `AgentMode`/`is_backgrounded`. El eje real = `ctx.is_subagent` (toolset por KIND, resolver.py:42-49) +
  `TaskRecord.is_backgrounded` (write-only en prod, lo lee el consumidor) + `notification`.
- **GAP-MODE1 confirmado**: `TaskRecord` (registry.py:18-35) sin campo `kind`/`type` → 05·GAP-EXEC2.
- **DISCREPANCIA REAL (GAP-MODE2 sub-enumerada)**: el doc nombraba **1** discrepancia del conjunto async
  (worktree); la auditoría 1:1 L09 destapó **4** (runtime `safe_for_background` vs canónico): **worktree**
  (Enter/Exit — canónico PERMITE tools.ts:69-70, runtime `False` ⇒ runtime más restrictivo) + **AgentTool**
  (canónico BLOQUEA "prevent recursion", runtime `True` con `_MAX_SUBAGENT_DEPTH=5` ⇒ probable 🔀 por
  arquitectura) + **TaskStop** (canónico BLOQUEA "main-thread state", runtime `True`) + **TaskOutput**
  (canónico BLOQUEA "prevent recursion", runtime `True`). Cabo sub-especificado, no falso — sigue homed en
  **10·R10**, ahora con los 4 ítems + dirección + nota L10. Corregido C2/GAP-MODE2/cruce-10/MR3.
- **Sin costuras latentes NUEVAS** tipo `to_llm`/`timeout_seconds`: `modes/` **entero** es la costura huérfana
  (FIND-MODE1, ya registrada); `on_transition`/`_listeners` primitiva sin consumidores (D6, ya registrada).
- **A1-A5 ⛔** (coordinator/swarm) reconfirmados por lectura íntegra de `coordinatorMode.ts` — topología
  líder/worker, ⛔ por arquitectura (L10, =02·E3); reconfirma FIND-SIG13 (2 abort controllers)→08.
- **Doc**: `04-modes.md` — header de fase + D4/§Naturaleza (línea 294) + C2/GAP-MODE2/cruce-10/MR3 (4 ítems) +
  **bloque "Re-visita de COMPLETITUD (L09)" con mini-ledger de consumidores + ledger de lectura + §honestidad +
  4 preguntas**. README fila 04 actualizada.

**SIGUIENTE → 05 · execution.** (01/02/03/04 completos con L09; NO quedan pendientes de verificación de la
2ª vuelta.) Ojo (2ª vuelta): `05-execution.md` ya trae re-audit de 1ª vuelta (EXEC1-12, GAP-EXEC1-7) — falta
pasarle el lente L09: para cada fila **✅/🔀** abrir la implementación de B (`execution/{local/runtime.py 435,
tasks/registry.py, fork/, agents.py}`) y confirmar el cableado, NO la tabla. Focos que 04 dejó ruteados a 05:
**FIND-EXEC1** (runner sin cablear — L09 clásico: existe pero ¿se registra/invoca?), **GAP-MODE1**→GAP-EXEC2
(`TaskRecord.kind` para dispatch polimórfico), `AgentMode.FORK`⇒`execution/fork/` (E3/E4), `max_turns` inerte
(FIND-EXEC5), promoción fg→bg (EXEC9). Cazar costuras latentes definido-pero-no-invocado (L10 B-interno).
Archivo más grande = `execution/local/runtime.py` (435, ya leído 1→EOF en 01·re-visita — cerrar huecos, L08).

---

## 05 · execution — VALIDADA (2ª vuelta, gate 11 de ENTRADA) · 2026-07-19

**Modo**: 2ª vuelta con **gate 11** (cada ✅/🔀 re-verificada abriendo el código de B y siguiendo el dato, no
la tabla). **Resultado**: doc (ya re-auditado 2026-07-12 línea a línea) **se sostiene sobre base correcta**;
**2 costuras latentes NUEVAS** (tech-debt B-interno, NO deuda A-vs-B) + 1 docstring obsoleto; **código intacto**;
tests no re-ejecutados (sin cambio de código).

- **Leído íntegro (B) 1→EOF**: `execution/local/runtime.py` (435, el más grande L08), `loop/agent_loop.py`
  (352), `factory.py` (267), `execution/tasks/registry.py` (166), `tools/native/agent.py` (119),
  `execution/fork/__init__.py` (96), `execution/local/notification.py` (72), `execution/agents.py` (66),
  `execution/session/session.py` (59), `execution/local/summarizer.py` (49), `execution/runner.py` (41),
  `execution/observer/observer.py` (37), `execution/tasks/status.py` (14) + grep de cableado producción-vs-test.
- **✅/🔀 sostenidos abriendo B**: E1/E2(runtime.py:345)/E3/E6(complete-first runtime.py:400 antes de notify)/
  E8 ✅; E10/E32(TaskRecord sin kind)/E18/E19/E20/E29(cableado runtime.py:410)/E30/E34 🔀; los 🟡 (E4 copia cruda
  fork:73, E17 `_last_assistant_text` asume str, E22 sin campo `background`, E28 5 campos). Base correcta.
- **❌ críticos re-confirmados por CABLEADO** (no por tabla): **FIND-EXEC1** (`_build_local` factory.py:178-240
  nunca llama `set_runner()` → `get_runner()` agent.py:105 revienta; `set_runner` sólo en tests; converge 18·C1);
  **FIND-EXEC5** (`_MAX_TURNS=50` constante de módulo agent_loop.py:24/185; `__init__` no acepta `max_turns`;
  `ForkContext.max_turns`/`RuntimeTask.max_turns` doblemente inertes); **FIND-EXEC4** (`get_observer` nunca
  llamado en prod — observer huérfano).
- **LAT-EXEC1 (NUEVO, tech-debt B-interno)**: `execution/tasks/registry.py::get_registry/set_registry` (singleton
  módulo) huérfano — ni productor ni consumidor en prod; el runtime usa `self._task_registry` por inyección de
  instancia (runtime.py:86). Hermano de `observer/` (FIND-EXEC4) → DEUDA-B §B-orphans (cablear o eliminar). NO
  deuda A-vs-B (anti-padding L10).
- **LAT-EXEC2 (NUEVO, precisión E5)**: `put_notification` cableado (child runtime.py:299) pero
  `drain_notifications`/`process_background_notification` sin consumidor runtime-interno → **drenado delegado al
  integrador** vía `root_turn_start_hooks` (factory.py:106-112 → loop runtime.py:372-374 → agent_loop.py:176). El
  runtime standalone escribe notif. y NO se auto-drena. 🔀/delegación (como hooks 06), NO bug, NO deuda A-vs-B.
  Sub-matiz cross-ref 02/07: el turn-start hook dispara 1×/`run()`, no 1×/turno como el drain canónico in-loop.
- **Docstring obsoleto**: `observer.py:5` ("LocalAgentRuntime emite eventos vía get_observer()") falso → se
  corrige al ejecutar remediación FIND-EXEC4 (eliminar observer/).
- **Doc**: `05-execution.md` — header de fase + bloque "Re-visita de COMPLETITUD (gate 11 / L09)" con
  verificación-por-cableado + LAT-EXEC1/2 + ledger de lectura + §honestidad + 4 preguntas. README fila 05 + este
  PROGRESS actualizados.

**SIGUIENTE → 06 · hooks.** (01/02/03/04/05 completos con gate 11; NO quedan pendientes de verificación de la
2ª vuelta.) Ojo (2ª vuelta): `06-hooks.md` (1ª pasada: ✅6·🟡12·🔀14·❌19·⛔6, tesis "runtime `hooks/` = registry
en-proceso, sistema configurable delegado al integrador"). Aplicar gate 11: para cada fila **✅/🔀** abrir el
consumidor real en B y confirmar el cableado — foco en **qué eventos se DISPARAN de verdad** (FIND-HOOK2: sólo
PreToolUse agent_loop.py:301 + SubagentStop runtime.py:289; los otros 9 = enum muerto) y en el gate PreToolUse
lossy (FIND-HOOK3: sólo honra block+modified_input, ignora stop/additional_context — agent_loop.py:307-313,
ya visto en esta re-visita). Archivo más grande A = `utils/hooks.ts` (5022, L08). Cazar costuras latentes
definido-pero-no-disparado (L10/L11 B-interno). Cross-refs cazados aquí: `root_turn_start_hooks` (LAT-EXEC2),
`_fire_stop` fire-and-forget (FIND-HOOK6).

---

## 06 · hooks — VALIDADA (2ª vuelta, gate 11 de ENTRADA) · 2026-07-19

**Modo**: 2ª vuelta con **gate 11** (cada ✅/🔀 re-verificada abriendo el código de B y siguiendo el dato,
no la tabla). **Resultado**: el doc (ya re-auditado 2026-07-12 con `utils/hooks.ts` 5022 íntegro) **se
sostiene sobre base correcta**; **1 costura latente NUEVA** (tech-debt B-interno, NO deuda A-vs-B); **cero
cambios de estado**; **código intacto**; tests no re-ejecutados (sin cambio de código).

- **Leído íntegro (B) 1→EOF**: `hooks/protocol.py` (72 — `HookEvent` enum **11 valores** contados 17-28,
  `HookDecision` 42-46, `HookHandler`, `HookSinkProtocol`), `hooks/runner.py` (63 — `register`/`register_sink`/
  `run` agregador), `hooks/__init__.py` (11). Sitios de ciclo: `loop/agent_loop.py:287-352`,
  `execution/local/runtime.py:285-406`, `factory.py:86,225` (archivos ya íntegros 1→EOF en 01/02/05/18) +
  grep de cableado prod-vs-test.
- **FIND-HOOK2 confirmado por CABLEADO**: únicos `.run(HookEvent…)` de producción = **2** — PreToolUse
  `agent_loop.py:301` + SubagentStop `runtime.py:289` (vía `_fire_stop`, **realmente invocado** en 384/391/406
  = killed/failed/completed). Los otros 9 valores del enum sin call site de prod = **enum muerto**. Exacto.
- **FIND-HOOK3 confirmado por lectura directa**: gate `agent_loop.py:307-313` sólo lee `modified_input`+`block`;
  ignora `stop`/`additional_context` (comentario 297-298 lo declara). Anclas A re-confirmadas dirigidas:
  `toolHooks.ts:332 resolveHookPermissionDecision` (L372 "allow skips prompt, deny/ask still apply" +
  `permissionBehavior` 510-561), `utils/hooks.ts:434/622-641` (`additionalContext` inyectable), `HOOK_EVENTS`=27.
- **FIND-HOOK6 confirmado**: `_fire_stop` (`runtime.py:289`) `await …run(SUBAGENT_STOP…)` **sin asignar** el
  retorno → decisión descartada (fire-and-forget). 🟡 exacto.
- **✅/🔀 sostenidos abriendo B**: `modified_input` consumido `agent_loop.py:307-308`; agregación real
  `runner.py:42-60`; PreToolUse payload `301-306`; callback = `HookHandler` invocado `runner.py:42`; HITL grant
  🔀 alcanzable (handler recibe `ctx` en payload 305 → muta `app_state.permissions`). `HookRunner` **inyectado
  por consumidor** (`factory.py:86→225→runtime.py:87→362→AgentLoop`), NO huérfano tipo `modes/`; `register`/
  `register_sink` sin invocador de prod = costura de extensión por diseño (L10).
- **LAT-HOOK1 (NUEVO, tech-debt B-interno)**: `HookRunner.run` agrega `additional_context` (`runner.py:54-55`)
  y lo devuelve (`59`) pero **ningún consumidor de prod lo lee** (el gate 307-313 sólo mira modified_input+block;
  `_fire_stop` descarta la decisión). Maquinaria a medio cablear (hermana de `to_llm`/`timeout_seconds` 01/03,
  LAT-EXEC1/2 05). **Distinción L11**: la cara A-vs-B (gate DEBERÍA inyectar additional_context) ya es
  FIND-HOOK3 ❌; lo B-interno es que la agregación ya existe muerta ⇒ HR5 **pre-cableado a medias**. NO deuda
  A-vs-B (anti-padding L10). Registrado; sin cambiar estado ni código.
- **Doc**: `06-hooks.md` — bloque "Re-visita de COMPLETITUD (gate 11 / L09)" con verificación-por-cableado +
  LAT-HOOK1 + ledger columna Lectura + §honestidad + 4 preguntas + **VEREDICTO DE AVANCE**. README fila 06 +
  este PROGRESS actualizados.

**SIGUIENTE → 07 · events.** (01/02/03/04/05/06 completos con gate 11; NO quedan pendientes de verificación de
la 2ª vuelta.) Ojo (2ª vuelta): `07-events.md` (1ª pasada + re-audit 2026-07-12: ✅5·🟡8·🔀15·❌16·⛔4; tesis
"el canónico NO tiene bus — tiene un STREAM serializado `AsyncIterable<SDKMessage>`; el `EventBus` del runtime
es bus tipado in-proc de 5 eventos que PARTE en 3 canales lo que A unifica en 1"). Aplicar gate 11: para cada
fila **✅/🔀** abrir el productor/consumidor real en B y confirmar el cableado — foco en **FIND-EVT1**
(=FIND-L2: `DoneEvent.usage` per-turno NI se acumula NI se surface; `Session.usage`/`turn_count` = slots
muertos; `run()→None` ⇒ sin SDKResultMessage — abrir `models/caller.py:207-245` + `agent_loop.py:247/253-254`
+ `session.py` y confirmar que el usage NO fluye) y en los **3 canales** (EventBus `push`, `registry.push_event`
dicts poll/drain, `ctx.messages` acumulación — confirmar que existen y divergen del stream único). Archivo más
grande A = `entrypoints/sdk/coreSchemas.ts` (1854, `SDKMessageSchema` 24 variantes, L08). Cazar costuras
latentes definido-pero-no-emitido (L10/L11 B-interno). Cross-refs que aterrizan: FIND-EVT1=FIND-L2/01·feat9,
LAT-HOOK1 (additional_context sin surface liga el canal de re-inyección), 08·SIG8 (sin resultado terminal).

---

## 07 · events — VALIDADA (2ª vuelta, gate 11 de ENTRADA) · 2026-07-19

**Modo**: 2ª vuelta con **gate 11** (cada ✅/🔀 re-verificada abriendo el código de B y siguiendo el dato,
no la tabla). **Resultado**: la tesis (canónico = STREAM `AsyncIterable<SDKMessage>`; runtime = `EventBus`
tipado in-proc de 5 tipos) y las filas ✅/🔀 **se sostienen sobre base correcta**; **2 correcciones de doc**
(1 discrepancia real + 1 refinamiento); **cero cambios de estado** (✅5·🟡8·🔀15·❌16·⛔4 intactos);
**código intacto**; tests no re-ejecutados (sin cambio de código); **sin costuras latentes NUEVAS**.

- **Leído íntegro (B) 1→EOF**: `events/{protocol.py 22, bus.py 45, event_types.py 43, __init__.py 15}`,
  `models/caller.py` (245), `execution/session/session.py` (59), `loop/agent_loop.py` (353),
  `execution/local/runtime.py` (435), `execution/tasks/registry.py` (166) + grep de cableado prod-vs-test.
- **✅/🔀 sostenidos abriendo B** (mini-ledger en el doc): A3/A4 (Event frozen + emit try/except por handler
  bus.py:39-45), C1 (ToolCall emitido `_emit` 248 + acumulado 277), C2 (ToolResult 312/324), C5/EVT8
  (`_make_bus` push_event dicts runtime.py:264-283), D4 (stop_reason `toolUse→tool_calls` caller.py:227),
  B1/B2/G3/K1/K2. **❌ convergen** por lectura directa: `event_types.py` define **exactamente 5** tipos, sin
  init/session_state/tool_progress/compact_boundary/api_retry/result-terminal.
- **DISCREPANCIA REAL (sobre-declaración · E3/FIND-EVT1/tesis)**: el doc marcaba `Session.turn_count` como
  "slot muerto (nadie lo alimenta)" junto a `usage`. **Falso para turn_count** — está cableado de punta a
  punta: `ctx.turn_count` (loop `agent_loop.py:189` `+=1`) → `session.turn_count` (`runtime.py:398`) →
  `TaskRecord.turn_count` (`complete()` 402 → `registry.py:148`); `duration_ms` ídem. **SÓLO `Session.usage`
  (tokens) es el slot muerto**: `complete()` recibe `input_tokens/output_tokens=0` SIEMPRE (runtime.py:403-404)
  porque nada acumula `DoneEvent.usage` (loop `253-255` `done=event;break`, nunca lee `done.usage`;
  `run()→None`). El núcleo FIND-L2 (usage=0, sin cost, sin `SDKResultMessage`) **SE SOSTIENE**. Corregido en
  E3, FIND-EVT1, tesis punto 1.
- **REFINAMIENTO (sub-crédito · A1/A2/GAP-EVT5)**: el doc trataba `subscribe_all` como "gancho sin productor
  canónico". Abriendo B, **`LocalAgentRuntime.stream()` (runtime.py:153-181) ES el productor de canal único
  ordenado** — `AsyncIterator[Event]` sobre `subscribe_all`→`asyncio.Queue`→sentinela, orden de emisión
  garantizado (docstring 158-163). Lo ausente es SÓLO la serialización `Event→SDKMessage` **wire** encima
  (GAP-EVT5/EvR3, que se cablea sobre `stream()`, no crea el canal). El `stream()` estaba **sin mencionar**
  en el doc (grep `stream()` = 0). Sin voltear estado (wire serializer sigue ❌). Corregido A1 y GAP-EVT5.
- **Sin costuras latentes NUEVAS** tipo `to_llm`/`timeout_seconds`/LAT-EXEC1/LAT-HOOK1: el `Session.usage`
  no-alimentado NO es costura B-interna sino la propia deuda A-vs-B FIND-EVT1 (el slot se lee en complete(),
  sólo que su valor upstream es 0).
- **Precisión de cableado (leyendo el ENSAMBLADOR `factory.py` 1→EOF, L09 — NO por grep; corrección tras
  reproche del usuario)**: mi 1ª redacción decía "`stream()` plenamente cableado y usado" — **inexacto**.
  `RuntimeFactory._build_local` (factory.py:178-240) **no cablea ningún consumidor de eventos** y
  `RuntimeConfig` (79-117) **no tiene campo de sink/stream**; `subscribe_all(on_event)` sólo corre si
  `on_event is not None` (runtime.py:281-282), lo que sólo pasa cuando un consumidor externo invoca
  `stream()`/`dispatch(on_event=)` (grep: sólo tests). ⇒ `stream()`/`subscribe_all` = **costura de consumo
  del integrador/BFF por diseño** (hermana de `subscribe_all`/`register` de hooks 06), **NO** huérfano tipo
  `observer/`, y distinta de FIND-EXEC1 (ahí la ruta interna SÍ está rota). El productor ordenado EXISTE; lo
  que no hay es caller de producción interno — por diseño. Lección L01/L09 re-aplicada: una conclusión de
  cableado exige leer el ensamblador, no grepearlo.
- **Doc**: `07-events.md` — E3/FIND-EVT1/tesis (turn_count) + A1/GAP-EVT5 (`stream()`) corregidos + bloque
  "Re-visita de COMPLETITUD (gate 11 / L09)" con mini-ledger de consumidores + ledger de lectura (A/B columna
  Lectura) + §honestidad + 4 preguntas + **VEREDICTO DE AVANCE**. README fila 07 + este PROGRESS actualizados.

**SIGUIENTE → 08 · signals.** (01→07 completos con gate 11; NO quedan pendientes de verificación de la 2ª
vuelta.) Ojo (2ª vuelta): `08-signals.md` (1ª pasada: ✅3·🟡3·🔀4·❌14·⛔1; fue la categoría **genuinamente
superficial** de la 1ª vuelta — grep+ventanas rehecho a lectura íntegra que añadió 6 ❌ (S21-25/SIG10-12);
tesis "canónico = `AbortController`/`AbortSignal` DENTRO del `ToolUseContext` + `signal.reason` + one-shot
irreversible + DOS cascadas: árbol `createChildAbortController` in-turn con sibling + kill de tasks bg; el
runtime tiene `ctx.stop` (asyncio.Event) REAL cableado end-to-end pero DEGRADADO binario sin reason/árbol +
`SignalBus` HUÉRFANO que conflaciona las 2 cascadas"). Aplicar gate 11: para cada fila **✅/🔀** abrir el
consumidor real en B y seguir el dato — foco en **`ctx.stop`** (¿cableado end-to-end? loop `agent_loop.py:173/186/227`
→ `caller.py:188-190` `replace(opts,signal=stop)` → agentic_models; `dispatcher` `ToolResult.aborted`; fork
`propagate_abort`) y en **FIND-SIG1** (SignalBus huérfano — grep repo-wide prod-vs-test, hermano de
`modes/`/`observer/`; `register_handler` muerto SIG5). Cross-refs que aterrizan: SIG8 (sin resultado terminal
`aborted_*` = liga 07·FIND-EVT1/`run()→None`), FIND-SIG13 (2 abort controllers work/agent = 04/05·EXEC12),
SIG7 pareo tool_use↔tool_result (=02·FIND-L1 ya reclasificado 🔀). Archivos más grandes A ya íntegros en 1ª
vuelta (`StreamingToolExecutor.ts` 530, `toolExecution.ts` tramos, `useCancelRequest.ts` 276) — releer anclas,
no re-derivar. B: `signals/` + `ctx.stop` en loop/caller/dispatcher/fork.

---

## 08 · signals — VALIDADA (2ª vuelta, gate 11 de ENTRADA) · 2026-07-19

**Modo**: 2ª vuelta con **gate 11** (cada ✅/🔀 re-verificada abriendo el código de B y siguiendo el dato, no la
tabla; las ❌ convergen por lectura directa). **Resultado**: la tesis (canónico = `AbortController`/`AbortSignal`
DENTRO del `ToolUseContext` + `reason` + one-shot + DOS cascadas separadas; runtime = `ctx.stop` REAL degradado +
`SignalBus` HUÉRFANO que conflacía las 2) y **todas** las filas ✅/🔀 **se sostienen sobre base correcta**;
**1 precisión de cableado** (arming integrador vs standalone); **cero cambios de estado** (✅3·🟡3·🔀4·❌14·⛔1
intactos); **código intacto**; tests no re-ejecutados; **sin costuras latentes NUEVAS**.

- **Leído íntegro (B) 1→EOF**: `signals/{bus.py 96 (el más grande, L08), protocols.py 14, __init__.py 4}`,
  `context/tool_use.py` (70, `stop` 47), `loop/agent_loop.py` (352, checks 173/186 + threading 227 + pairing
  319-323), `models/caller.py` (245, `complete(stop=)` 146-159 + `replace(signal=stop)` 188-190), `models/protocol.py`
  (37), `tools/dispatcher.py` (84, abort check 54), `tools/protocol.py` (61, `aborted` 47-48 + `ToolProtocol` sin
  `interrupt_behavior`), `execution/fork/__init__.py` (96, `propagate_abort` 80-83 + `parent_stop` 67),
  `context/adapters.py` (86, seam de arming `stop=` 15/44) + tramos ya-íntegros de `execution/local/runtime.py`
  (`_build_child` 198-218) y `tools/native/agent.py` (78-105) + grep de cableado prod-vs-test.
- **FIND-SIG1 confirmado por CABLEADO**: `SignalBus/SignalType/SignalHandle/SignalHandler` importados SÓLO por
  tests (`test_signal_bus.py` + `test_signals_homologation.py` + 1 comentario en `test_runtime_e2e.py`); **cero
  producción**. Huérfano — hermano de `modes/`/`observer/`. **SIG5** re-confirmado: `register_handler` (bus.py:89-96)
  guarda en `_handlers` pero `send()`/`_apply()` nunca invocan `handle_signal` = extension point muerto. **SIG6**:
  `RESUME` limpia la señal (bus.py:68-69) → contradice irreversibilidad.
- **✅/🔀 sostenidos abriendo B** (mini-ledger en el doc): S2 (plumbing `agent_loop.py:227`→`caller.py:188-190`→
  `agentic_models.StreamOptions.signal`), S6 (checks 173/186), S7 (dispatcher.py:54), S9 (pairing por `call_id`
  319-323), S12 (delegado a agentic_models→16), S16/S18 (SignalBus/RESUME), S20 (grep `.set()` prod = 0 → disparo
  externo). **❌ convergen** por lectura directa (S3/S4/S5/S8/S10/S11/S13/S17/S19/S21-25).
- **PRECISIÓN DE CABLEADO (arming in-turn integrador vs standalone; task-kill SÍ opera)** — leyendo `_run_loop`
  (runtime.py:306-416) **1→EOF esta vuelta**: el plumbing de `ctx.stop` es real e **incondicional** en el loop, PERO
  **ningún path de prod del runtime standalone ARMA `ctx.stop`** — `runtime.py:210` crea el root **sin `stop=`**,
  `runtime.py:201` llama `fork()` **sin `parent_stop`** (→ hijo `stop=None`), `agent.py:89-105` tampoco; los seams de
  arming del integrador son `root_context_modifier` (runtime.py:329) y `adapters.py:15` (solo tests los ejercitan).
  **PERO OJO — no es "no hay cancelación"**: la cancelación de **task** SÍ funciona por otra vía —
  `runtime.cancel(task_id)`→`registry.kill`→`asyncio_task.cancel()`→**`CancelledError`** (runtime.py:381-384) →
  kill+`_fire_stop`(SubagentStop)+`_notify`; es el homólogo del **kill de tasks** canónico, el nivel "agent-kill" de
  FIND-SIG13 (ya visto en 02·G5). ⇒ Lo latente-en-standalone es **SOLO `ctx.stop`** (señal cooperativa in-turn), NO
  la cancelación de task. Coincide EXACTO con la tesis de las DOS cascadas (kill-de-tasks cableado + árbol in-turn
  sin armar). `ctx.stop` in-turn = costura de consumo del integrador por diseño (hermana de `stream()`/`subscribe_all`
  07 + `HookRunner`/`register` 06), **NO** huérfano tipo `SignalBus`, **NO** bug, **NO** deuda A-vs-B (L10).
  **Refuerza S20 ✅**, afina la tesis. **Corolario FIND-SIG3**: hoy doblemente inocuo (ni setter en el hijo, ni
  `parent_stop` vivo); S4 ❌ se sostiene (la API `fork(parent_stop=…)` sí comparte el objeto cuando se usa,
  `test_fork_primitives.py:198-206`).
  **Auto-corrección de honestidad**: mi 1ª redacción dijo "toda la maquinaria de abort está latente" — imprecisión
  por no haber leído `_run_loop` 1→EOF en el 1er intento; corregida al leerlo (task-kill opera). L00: leer el
  ensamblador 1→EOF necesario; glosar `_build_child` sin `_run_loop` era el atajo.
- **Sin costuras latentes NUEVAS** tipo `to_llm`/`timeout_seconds`/LAT-EXEC1-2/LAT-HOOK1: el `SignalBus` entero YA es
  la costura huérfana (FIND-SIG1); el `parent_stop`-no-threadeado = delegación por diseño (anti-padding L10).
- **Doc**: `08-signals.md` — Estado (marcador de fase 2ª vuelta) + bloque "Re-visita de COMPLETITUD (gate 11 / L09)"
  con mini-ledger de consumidores + precisión de cableado + ledger de lectura A/B + §honestidad + 4 preguntas +
  **VEREDICTO DE AVANCE**. README fila 08 + este PROGRESS actualizados.

**SIGUIENTE → 09 · tools-infra.** (01→08 completos con gate 11; NO quedan pendientes de verificación de la 2ª
vuelta.) Ojo (2ª vuelta): `09-tools-infra.md` (1ª pasada: ✅~9·🟡~14·🔀~16·❌~18·⛔~6; tesis "el canónico NO reifica
una capa `tools/` — el protocolo es el tipo estructural `Tool` (~60 miembros), el registry es `getAllBaseTools()`,
el pool es `assembleToolPool()`, la ejecución vive en StreamingToolExecutor/toolExecution (08); el runtime REIFICA
cada rol ToolProtocol/ToolRegistry/ToolPool/ToolDispatcher — desacople correcto, homologación DEL CONTRATO MÍNIMO 8
vs 60 miembros"). Aplicar gate 11: para cada fila **✅/🔀** abrir el consumidor real en B y seguir el dato. Focos:
**FIND-TOOL1** (dispatcher SECUENCIAL, `isConcurrencySafe` no existe — cazar si algo lo cablea), **FIND-TOOL10**
(dos registries: `ToolRegistry` usado / `NativeToolRegistry` hot-plug-MCP sin usar por factory — hermano de los
huérfanos, confirmar prod-vs-test), **FIND-TOOL6** (ToolSearch `select:` multi-select coma-separado que el propio
delta-announce promete al modelo), **FIND-TOOL7** (delta reconstruido parseando texto de reminders + discovered-set
materializado en `app_state.capabilities`), **FIND-TOOL8** (LocalExecEnvironment sin shell persistente).
**Homologado ✅** a re-confirmar por cableado: `assemble_tool_pool`=`assembleToolPool`, `ToolPool.find`=`findToolByName`
resuelve del MISMO pool (invariante C2/D1, agent_loop.py:195/dispatcher.py:57), path-guards `fs_env`. Archivo más
grande A = `utils/permissions/filesystem.ts` (1778, L08) — releer anclas (ya íntegro 1ª pasada). B: los 12 archivos
infra + cableado loop `agent_loop.py:85-234` + `native/tool_search.py`.

---

## 09 · tools-infra — VALIDADA (2ª vuelta, gate 11 de ENTRADA) · 2026-07-19

**Modo**: 2ª vuelta con **gate 11** (cada ✅/🔀 re-verificada abriendo el consumidor real de B y siguiendo el dato,
no la tabla; las ❌ convergen por lectura directa). **Resultado**: la tesis (canónico NO reifica capa `tools/`; el
runtime reifica ToolProtocol/ToolRegistry/ToolPool/ToolDispatcher = homologación del CONTRATO MÍNIMO) y **todas** las
filas ✅/🔀 **se sostienen sobre base correcta**; **cero cambios de estado** (✅~9·🟡~14·🔀~16·❌~18·⛔~6 intactos);
**código intacto**; suite no re-ejecutada. Aparecen **2 precisiones de justificación** (el doc sobre-declaraba),
**1 costura latente NUEVA** (LAT-TOOL1) y **1 refinamiento de clasificación** (NativeToolRegistry = huérfano).

- **Leído íntegro (B) 1→EOF**: los 12 infra (`fs_env.py` 163 el más grande L08, `deferred_delta.py` 116,
  `exec_env.py` 105, `deferred_strategy.py` 105, `dispatcher.py` 84, `pool.py` 78, `factory.py` 75, `protocol.py` 61,
  `deferred.py` 44, `native_registry.py` 41, `registry.py` 37, `__init__.py` 28) + **ensamblador** `loop/agent_loop.py`
  (352, L09) + `tools/native/tool_search.py` (79) + `execution/fork/__init__.py` (96) + `context/tool_use.py` (70) +
  grep de cableado prod-vs-test.
- **✅ del pool único (C1/C2/D1) sostenidos por CABLEADO literal**: `loop:195-196` (`ctx.tool_pool = _build_tool_pool`
  → `.assemble()` para anunciar) + `dispatcher.py:57` (`ctx.tool_pool.find()`→`pool.py:42` `self.assemble()`) +
  `tool_search.py:51` (`assemble()`). Deferred = **visibilidad** (schema filtrado en `deferred_strategy.py:67`) no
  disponibilidad (sigue en `ctx.tool_pool`→`find`). Invariante confirmado leyendo el ensamblador, no la tabla.
  D4/E10/D9/E3/B3/C4 + path-guards G1/G3/G5/G6/G7 (`fs_env.py`) consumidos en ruta real (fs-tools, dispatcher, loop).
- **exec_env seam VIVO** (a diferencia del huérfano): `factory.py:210`→`runtime.py:318` `ctx.exec_env`→`bash.py:29`
  `run_shell`. F1/F2/F4 confirmados; **FIND-TOOL8** (sin shell persistente, `exec_env.py:38` subproceso fresco) ❌.
- **❌ foci re-confirmados por cableado**: **FIND-TOOL1** (`loop:287` `for tc` secuencial + `protocol.py:52-61` sin
  `is_concurrency_safe`); **FIND-TOOL2** (`dispatcher.py:62-65` deny-por-nombre, input nunca al gate).
- **Precisión FIND-TOOL6/E6** (no voltea estado): el ❌ se sostiene (canónico `select:A,B,C`; runtime single,
  `tool_search.py:53-55`), PERO la justificación del doc ("el delta-announce promete `select:A,B` y falla") es
  **INEXACTA** — el announce (`deferred_delta.py:39`) y la description (`tool_search.py:17`) prometen
  `select:<tool_name>` **SINGULAR**; el gap real es de paridad vs A, no promesa auto-incumplida.
- **Precisión FIND-TOOL5/D8 (SIG12)**: `dispatcher.py:83` `except Exception` **NO** captura `CancelledError`
  (`BaseException` desde 3.8) → cancel en vuelo **no se aplana** a error (propaga a `_run_loop`, 08); el runtime no
  tiene AbortError dentro de `execute` (pre-chequeo `dispatcher.py:54`). Sólo A26 (aborted str genérico) se sostiene 🟡.
- **Refinamiento FIND-TOOL10 (L10/L11)**: `NativeToolRegistry` = **0 consumidores prod** (sólo export + 1 test); el
  cableado es `ToolRegistry` (`factory.py:189`→`loop:92`+`resolver.py:46`). ⇒ huérfano B-interno (el canónico no lo
  tiene), hermano de `modes/`·`observer/`·`SignalBus`·`LAT-EXEC1` → DEUDA-B §B-orphans; NO "dos registries a unificar".
- **Costura latente NUEVA LAT-TOOL1** (tech-debt B-interno, NO deuda A↔B, anti-padding L10/L11):
  `ToolProtocol.category: ToolCategory` (`protocol.py:56`) es campo requerido, lo setean las 25 tools, pero **ningún
  código de prod lee `.category`** (grep de lectura = 0) — slot muerto, hermana de `to_llm`/`timeout_seconds`/
  `LAT-EXEC1`/`LAT-HOOK1`. El canónico no tiene el enum de 5 valores como driver ⇒ no es deuda A↔B.
- **FIND-TOOL7 (E4/E5) 🔀 + copy-safe**: delta parseado de texto + discovered-set materializado CONFIRMADOS
  (`deferred_delta.py`/`deferred.py:31`). El `fork()` copia `dict(snap.capabilities)` (shallow, `fork/__init__.py:78`)
  y `mark_tools_discovered` **REEMPLAZA** la clave (`deferred.py:37`) → sin aliasing/drift; que el hijo vea el set del
  padre depende de `ForkSnapshot.capabilities` en `runtime.py` → cabo destino **05/11**, no bug del seam de 09.
- **Auto-corrección de honestidad (gate auto-adversarial, mismo reproche que 07)**: mi 1ª redacción concluyó
  "exec_env VIVO / `ToolRegistry` cableado vía `factory:189`" desde **grep** de `factory.py`/`runtime.py` sin abrir
  el ensamblador. Corregido en el cierre: `factory.py` (267) leído **1→EOF** (`_build_local:189` `create_tools`→`:220`;
  `:210` exec_env→`:228`; `NativeToolRegistry` NO aparece → huérfano confirmado por lectura) + `runtime.py:314-318`
  `ctx.exec_env = self._exec_env` + `bash.py:27-33` leídos. Cableado ahora apoyado en el ensamblador, no en grep;
  grep queda sólo para ausencias (0-consumidores), corroboradas además por `factory.py` 1→EOF.
- **Doc**: `09-tools-infra.md` — bloque "Re-visita de COMPLETITUD (gate 11/L09)" con mini-ledger de consumidores +
  precisiones + LAT-TOOL1 + ledger de lectura B (incl. `factory.py` 267 + `runtime.py:308-331` + `bash.py` 37) +
  §honestidad (con la auto-corrección) + 4 preguntas + **VEREDICTO DE AVANCE**. README fila 09 + este PROGRESS
  + DEUDA-B §B-orphans (NativeToolRegistry+LAT-TOOL1) actualizados.

**SIGUIENTE → 10 · tools-native.** (01→09 completos con gate 11; NO quedan pendientes de verificación de la 2ª
vuelta.) Ojo (2ª vuelta): `10-tools-native.md` fue la categoría que en 1ª pasada sufrió el reproche de **trocear**
`BashTool.tsx`(1144)/`FileReadTool.ts`(1183)/`utils/tasks.ts`(862) en "núcleo + resto" (L07) — la re-lectura íntegra
añadió ❌ (A3b/A3c/A3d/B9-B12); en la 2ª vuelta, aplicar gate 11 a cada ✅/🔀 abriendo el consumidor real de B (los 19
`tools/native/*.py`) y verificar que no queda ningún in-scope troceado. Focos: FIND-NATIVE-READSTATE/EDITGUARDS
(=FIND-CTX1 aterrizado: read_file no puebla readFileState, Edit/Write sin read-before-edit), FIND-NATIVE-BASH
(=FIND-TOOL8 confirmado), FIND-NATIVE-BG (allowlists background), FIND-NATIVE-TASK (task_tools conflaciona tasklist
vs registry). Aterriza aquí LAT-TOOL1 (¿alguna nativa debería leer category?), FIND-TOOL6 (split select en la ruta).
Archivo A más grande = `BashTool.tsx` (1144, L08). B: los 19 `tools/native/*.py` + `protocol.py` + cableado del loop.

---

## 10 · tools-native — VALIDADA (2ª vuelta, gate 11 de ENTRADA) · 2026-07-19

**Modo**: 2ª vuelta con **gate 11** (cada ✅/🔀 re-verificada abriendo la implementación de B y siguiendo el
dato hasta el ensamblador, no la tabla; las ❌ convergen por lectura directa). **Resultado**: el doc (ya
releído ÍNTEGRO A+B en 1ª pasada tras el reproche de troceo) **se sostiene sobre base correcta**; **TODAS** las
✅/🔀 verificadas abriendo B; **cero cambios de estado** (✅~10·🟡~12·🔀~14·❌~20·⛔~8 intactos); **código
intacto**; suite no re-ejecutada; **sin costuras latentes NUEVAS** (LAT-TOOL1 de 09 confirmado que aterriza aquí).

- **Leído íntegro (B) 1→EOF**: los 19 `tools/native/*.py` (`task_tools.py` 223 el más grande L08, `worktree.py`
  167, `clone_repository.py` 149, `web_search.py` 128, `agent.py` 119, `plan_mode.py` 107, `ask_user.py` 98,
  `grep_tool.py` 87, `tool_search.py` 79, `file_edit.py` 78, `config.py` 76, `web_fetch.py` 67, `todo_write.py`
  63, `glob_tool.py` 46, `read_file.py` 42, `sleep.py` 39, `write_file.py` 38, `bash.py` 36, `__init__.py` 54) +
  **ensamblador** `loop/agent_loop.py:283-352` (1→EOF del tramo, L09) + `tools/protocol.py` (61).
- **✅/🔀 sostenidos abriendo B** (mini-ledger en el doc): A1/I naming (`read_file`/`write_file`/`glob`/`grep`/
  `bash` minúscula vs `Edit`), A13/A14 glob-cap-100/grep-caps espejos, B1/B5/B12 (`is_error=returncode!=0`
  literal `bash.py:33`), B8 clone_repository (credential-helper efímero, token no en argv/.git/config), C1/C2
  config/todo (`context_modifier`→`app_state.native`), C3/C4 sleep/ask_user (`ends_turn`), D1/D2/D3 plan
  (root-only + `get_plan` + `ends_turn`), E1/E2 worktree (`git worktree add -b`, F en Enter/Exit=GAP-MODE2),
  E3/E4 bg-gating verificado **celda a celda** contra E4 (coincide exacto), F1/F2/F4 agent (depth 5, `get_runner`),
  G1/G2/G5 task (conflación con `execution.tasks.registry`, scoping por session_id, `registry.kill`), H1/H2 web
  (urllib http/https + Serper.dev). **❌ convergen** por lectura directa (read_file sólo texto, edit/write sin
  guards, bash sin shell persistente).
- **§J/CORR-09-CTXMOD confirmado en el ENSAMBLADOR** (no sólo atributo): loop aplica `context_modifier`
  (`agent_loop.py:332-337` getattr+try/except), `ends_turn` (338-339→break 348), gate PreToolUse (300-313 honra
  `modified_input`+`block`, ignora `stop`/`additional_context` comentario 297-298). `new_messages` sigue ❌
  (sólo appendea `result.output` 319-323). 6 productores reales confirmados abriendo cada tool.
- **LAT-TOOL1 (category) confirmado aterriza, sin novedad**: cada nativo setea `category` pero ninguno lee
  `.category`; el canónico no usa el enum como driver → tech-debt B-interno (ya homed 09/DEUDA-B §B-orphans),
  NO deuda A↔B (L10/L11). Respuesta a la pregunta-guía: ninguna nativa debería leerlo.
- **Cabo 04·GAP-MODE2 (4 ítems: worktree+Agent+TaskStop+TaskOutput) CONFIRMADO cubierto** en E4/R10 — el ruteo
  de 04 aterriza correcto (worktree F→debe T; Agent/TaskStop/TaskOutput T con razón canónica de bloqueo).
- **§honestidad**: la 1ª pasada de 10 NO fue confirmación-de-doc (ya leyó A+B íntegros post-reproche); el
  value-add del gate 11 fue abrir el **ensamblador** y confirmar el cableado de `context_modifier`/`ends_turn`
  (no sólo atributos que `protocol.py` ni declara) + tabular `safe_for_background` celda a celda. NO se
  releyeron las contrapartes canónicas (íntegras en 1ª pasada): "releer anclas, no re-derivar" (método 05-09).
- **Auto-corrección de honestidad (gate auto-adversarial del usuario)**: mi 1ª redacción del ledger listó
  `__init__.py` (54) y `tool_search.py` (79) como "íntegro 1→EOF esta vuelta" cuando `__init__.py` NO se abrió y
  `tool_search.py` sólo se grepeó una línea (íntegro estaba en 09). Corregido **tras la pregunta del usuario**
  leyéndolos 1→EOF ahora: `__init__.py` = re-export de las 25 clases-tool (registro real en `factory/create_tools`
  09, sin cableado nuevo); `tool_search.py` = `select:` singular sin split-por-comas (=09·E/FIND-TOOL6),
  `safe_for_background=True` por lectura. **Cero findings/estados nuevos** — corrección de método (L03/L08
  "abierto≠íntegro"), no de sustancia.
- **Doc**: `10-tools-native.md` — marcador de fase (cabecera) + bloque "Re-visita de COMPLETITUD (2ª vuelta ·
  gate 11 / L09)" con mini-ledger de consumidores + ledger de lectura A/B + §honestidad + 4 preguntas +
  **VEREDICTO DE AVANCE**. README fila 10 + este PROGRESS actualizados.

**SIGUIENTE → 11 · cap-mcp.** (01→10 completos con gate 11; NO quedan pendientes de verificación de la 2ª
vuelta.) Ojo (2ª vuelta): `11-cap-mcp.md` (1ª pasada RE-AUDITADA: ✅~11·🟡~6·🔀~4·❌~14·⛔~9; FIND-MCP1-24 +
§Plan McR1-19). Fue re-auditada tras reproche de superficialidad (marcó ~10 archivos ⛔ sin abrir + inventó un
hallazgo) → al ABRIR aparecieron FIND-MCP21-24. Aplicar gate 11: para cada ✅/🔀 abrir el consumidor real en B
(`capabilities/mcp/*`) y seguir el dato. Focos: hot-plug por reensamblado per-turno (cabo 09·TiR4 dos-registries
RESUELTO ahí), `*_list_changed` refetch, dedup-por-firma `getMcpServerSignature`, reconcile acotado a scope
dynamic, elicitation headless, reconexión-backoff. Cross-refs que aterrizan: 09·FIND-TOOL7 (fork re-deriva
discovered-set → provider vivo compartido), 03·CtxR7/A13, 05·ExR6/08·SR3 cleanup-por-agent. Archivo A más
grande: revisar el árbol `mcp/` canónico (el más grande, L08) — releer anclas de la re-auditoría, no re-derivar.

---

## 11 · cap-mcp — VALIDADA (2ª vuelta, gate 11 + re-verificación A 1→EOF) · 2026-07-20
**⚠ Historia del cierre (2 iteraciones, reproche del usuario):** el 1er intento cerró "VALIDADA" apoyándose
en "A leído en la 1ª pasada" — tratar el ledger previo como verdad (L11 lo prohíbe), máxime habiendo fallado
en método esa ronda (grep para cableado). El usuario lo señaló. **Corregido: re-verifiqué TODO el lado A
observable 1→EOF ESTA ronda** — no sólo los tratables sino los **3 grandes**:
- **`client.ts` (3348) 1→EOF**: FIND-MCP8 (`DEFAULT_MCP_TOOL_TIMEOUT_MS=100M` :211), MCP10 (`getConnectionTimeoutMs=30k`
  + race+close :456/1048-1077), MCP11 (batch 3/20 pMap :552/2391), MCP12 (caps/instructions+trunc-2048 :1157-1171),
  MCP9 (onerror/onclose ECONNRESET×3/404-32001/-32000+invalida-cachés :1249-1402/3194-3231; MAX_SESSION_RETRIES=1
  :1859), MCP19 (SIGINT→SIGTERM→SIGKILL 100/400ms+registerCleanup :1426-1574), MCP1/2 (buildMcpToolName+mcpInfo+
  isMcp+searchHint/alwaysLoad :1768-1785), MCP3 (annotations→4-hints+title :1795-1976), MCP6 (_meta+mcpMeta :1841/
  1897), MCP16 (mcp__srv__prompt+getPromptForCommand :2054-2094), MCP5 (transformResultContent image/audio/blob/
  resource :2478-2591), MCP6 (transformMCPResult 3-formas+inferCompactSchema :2662), MCP7 (processMCPResult large-
  output+imágenes-excluidas :2720), MCP18 (-32042×3+runElicitationHooks+roots/elicitation :994-1018/2813).
- **`config.ts` (1578) 1→EOF**: escritura-atómica (:88-131), MCP22 (getMcpServerSignature+dedup :202-310), MCP14
  (deny/allow name/command/url+allowlist-vacía+allowManagedOnly :364-508), MCP13 (expandEnvVars+missingVars :556-616),
  MCP15 (addMcpConfig-regex/reservados/enterprise :625-679; precedencia :1046-1057; getProjectMcpServerStatus==='approved'
  :1164-1170), severidad fatal/warning+npx-Windows (:1297-1372), enabled/disabled (:1528-1569).
- **`auth.ts` (2465) 1→EOF**: MCP20 (getServerKey=name|sha256[:16] :325-341, todo keyed por él; revokeToken RFC7009+
  revokeServerTokens :381-618), MCP4 (hasMcpDiscoveryButNoToken :349-363), D (ClaudeAuthProvider.clientMetadata
  token_endpoint_auth_method:'none' :1417 = **espejo EXACTO de auth.py:92-100**; CIMD :1445; step-up :1468/1625; OAuth
  provider methods delegados-al-SDK :1482-2359). ⛔-de-forma (XAA :664-845, callback-server interactivo :847-1342)
  **confirmados abriéndolos (L02)**.
**Cita-de-línea = evidencia**: los rangos de la 1ª pasada (1049-1077/1157-1183/1216-1402/1429-1562/1795-1976/2503/
2662/2720/2813/325/381-467/1376-1644) coinciden EXACTOS ⇒ prueba de que sí se leyeron. **CERO discrepancias**;
ninguna ❌ falsa; ningún comportamiento A omitido. Tratables re-leídos también (types/MCPTool/McpAuthTool/2
resource-tools/3 prompt.ts — estos NO estaban en el ledger 1ª pasada = laguna de completitud de ese ledger, sin
comportamiento). El lado B ya estaba verificado (12 `mcp/*.py` + ensamblador 1→EOF).

**Modo**: gate 11 — cada ✅/🔀 re-verificada abriendo B **y el ENSAMBLADOR** (factory/manager/dispatcher/fork),
no la tabla; las ❌ convergen por lectura directa. La 1ª pasada de 11 YA fue re-auditoría íntegra A+B
(post-reproche, destapó MCP21-24), no confirmación-de-doc. **Resultado**: el doc **se sostiene sobre base
correcta**; **cero cambios de estado** (✅~11·🟡~6/8·🔀~4/5·❌~14/18·⛔~9 intactos); **código intacto**; suite no
re-ejecutada.

- **Leído íntegro (B) 1→EOF esta vuelta**: los 12 `capabilities/mcp/*.py` (`provider.py` 339 el más grande L08,
  `client.py` 204, `config_store.py` 145, `config.py` 129, `auth.py` 122, `state.py` 118, `tool_adapter.py`
  109, `scope.py` 105, `resource_tools.py` 91, `reconcile.py` 82, `token_storage.py` 65, `__init__.py` 64) +
  **ensamblador** `factory.py:130-267` + `capabilities/manager.py` 112 + `execution/fork/__init__.py` 96 +
  `tools/dispatcher.py:67-82` + grep prod-vs-test. *(Layout: el paquete migró a `src/agentic_runtime/…`.)*
- **✅/🔀 sostenidas abriendo B** (mini-ledger en el doc): A transportes/identidad-estricta/ssl_verify/enabled;
  B 7-scopes/precedencia/exclusividad/mutabilidad/merge/persist; C connect-por-transporte (HTTP pasa timeout
  del config evita httpx-5s)/aislamiento-por-ítem/reconnect/reconcile; D estrategias-registrables/OAuth-vía-SDK;
  E adapter-tolerante/requires_permission/McpToolError-una-llamada; F/G/H text/resource-tools-condicionales/
  watcher.
- **Hot-plug per-turno (cabo 09·TiR4) CONFIRMADO por el ENSAMBLADOR (L09, no grep)**:
  `factory._build_capability_manager:148-158` → `CapabilityManager` → `runtime.py:83`/`358` (MISMA instancia
  root+subagentes) → `agent_loop.py:194-195` `ctx.tool_pool=_build_tool_pool` **por turno** → `manager.tools`
  (manager.py:50-59) → `McpProvider.tools` (provider.py:307-316) re-lee `McpState.all_tools()` cada turno.
  `NativeToolRegistry` NO en la ruta (0 consumidores prod). ⇒ **RESUELVE DEUDA-B §B-orphans "decidir con 11"**:
  hot-plug = reensamblado per-turno (NO registro dinámico) ⇒ **retirar `NativeToolRegistry`** (huérfano), salvo
  swap push-based del auth-tool FIND-MCP4.
- **PRECISIÓN de cableado (fork MCP-inheritance, no voltea estado)**: la resolución 03·CtxR7/A13 decía "provider
  MCP heredado por `app_state.capabilities` compartido" — **imprecisa para el standalone**. En prod NADA puebla
  `app_state.capabilities` con MCP (sólo el discovered-set de deferred, `deferred.py:37`); el hijo ve las tools
  MCP vivas por (a) `inherit_tool_pool=True` (fork:75) y (b) el `capability_manager` **compartido** al loop del
  subagente (runtime.py:358) → reensamblado per-turno sobre el MISMO `McpState`. `app_state.capabilities` es el
  seam del INTEGRADOR (ForkSnapshot 42-46). Conclusión observable (sin doble-conexión/clonado) SE SOSTIENE;
  mecanismo refinado. Hermana de las precisiones "leer el ensamblador" de 07/08/09.
- **FIND-MCP8 refinamiento (no voltea estado)**: el cap de 30s de la tool-call SÍ se aplica — `dispatcher.py:68`
  lee `tool.timeout_seconds` + `wait_for` (77-82) → `ToolResult.timeout`. `register_tools_from_specs:125`
  alimenta el MISMO `config.timeout_seconds or 30` a call-timeout y connect-timeout (client.py:128) — confirma
  McR8. `McpTool.timeout_seconds` NO es costura latente (se consume).
- **COSTURA LATENTE NUEVA LAT-MCP1** (tech-debt B-interno, NO deuda A↔B, anti-padding L10/L11):
  `McpServerConfig.auth_headers()` (config.py:97-102) construye el header bearer pero **sin consumidor de prod**
  (grep: sólo 2 tests); la ruta viva es `_build_bearer` (auth.py:73-75) → `AuthArtifacts.headers` → merge en
  `client.connect:106`. Duplicado muerto → hermano de `to_llm`/`category`/LAT-EXEC1/LAT-HOOK1/LAT-TOOL1. Homed a
  DEUDA-B §B-orphans. Primos menores no elevados: `McpServerConfig.model` (0 lectores) + `pending_servers()`
  (accesor integrator-facing). **LAT-TOOL1 (category) confirmado que aterriza** (cada McpTool/resource-tool
  setea `category=SYSTEM`, nadie lee) — ya homed, sin novedad.
- **❌ convergen** por lectura directa (dirección L11 crítica, sin implementación oculta): 4 estados de server
  (sin NEEDS_AUTH), 401→FAILED, nombre crudo sin `mcp__`, `deferred=True` fijo, `str()` de content, sin
  capabilities/instructions, sin wait_for en connect, startup secuencial, sin `*_list_changed`, sin dedup, sin
  env-expansion, sin política/aprobación, reconcile sobre-agresivo. Ninguna ❌ resultó falsa.
- **§honestidad**: no se re-leyeron las contrapartes canónicas (íntegras en la 1ª pasada); el value-add fue el
  ensamblador (hot-plug/timeout/fork-precisión/LAT-MCP1), invisible sin abrir factory/manager/dispatcher/fork.
- **Auto-corrección de honestidad (gate auto-adversarial del usuario)**: la 1ª redacción de esta re-visita
  afirmó 3 conclusiones de CABLEADO desde **grep** (timeout via `wait_for`, per-turno `agent_loop.py:194-195`,
  superficie MCP `factory.py:1-129`) sin leer. Corregido leyéndolos **1→EOF esta ronda**: `dispatcher.py` (85,
  `asyncio.wait_for(tool.execute, timeout=effective_timeout)` 76-82 REAL → FIND-MCP8 sólido); `agent_loop.py:185`
  `for _turn in range(_MAX_TURNS)`→194-195 DENTRO del bucle (hot-plug confirmado por lectura; matiz
  `_restrict_to_agent_tools` filtra capability_tools por allowlist del subagente); `factory.py:1-129` confirma
  `CapabilitiesConfig` MCP (33-55). **Las 3 se sostuvieron** — cero findings/estados nuevos; corrección de MÉTODO
  (L00/L09 "cableado = leer el ensamblador, nunca grep"; grep sólo para AUSENCIA). Ledger del doc actualizado.
- **Doc**: `11-cap-mcp.md` — marcador Estado (cabecera) + bloque "Re-visita de COMPLETITUD (2ª vuelta · gate
  11/L09)" con mini-ledger de consumidores + ledger de lectura B + §honestidad + 4 preguntas + **VEREDICTO**.
  README fila 11 + DEUDA-B §B-orphans (LAT-MCP1 + decisión NativeToolRegistry) + este PROGRESS actualizados.

**SIGUIENTE → 12 · cap-skills.** (01→11 completos con gate 11; lado A **Y** B de 11 re-verificados 1→EOF esta
ronda con CERO discrepancias — cierre GANADO, no asumido; NO quedan pendientes de verificación.) **LECCIÓN de
método para 12→18** (del reproche del usuario): en modo validación, "A leído en la 1ª pasada" NO es ancla fiable
si la 1ª pasada fue superficial-luego-re-auditada — hay que RE-ABRIR A 1→EOF, priorizando los archivos grandes;
el ledger previo es hipótesis (L11), y las citas-de-línea correctas son la evidencia de lectura real. Ojo (2ª
vuelta) para 12: `12-cap-skills.md` (1ª pasada RE-AUDITADA: ✅~13·🟡~9·🔀~4·❌~19·⛔~7; FIND-SKILL1-19
+ §Plan SkR1-17). Fue re-auditada tras reproche (marcó 13 bundled ⛔ por grep + infirió FIND-MCP16; al ABRIRLOS
apareció SKILL19). Aplicar gate 11: para cada ✅/🔀 abrir el consumidor real en B (`capabilities/skills/*`) +
el ensamblador (`factory._build_capability_manager:160-164` SkillsProvider; loop reensamblado per-turno). Focos:
SKILL19 `getPromptForCommand=callable async ctx-aware`, SKILL9 catálogo incremental (skill_listing+budget vs
re-emite-todo), SKILL10 invoked_skills (matiz cleanup-por-agent), SKILL4 substitución-args/vars/bash-injection,
SKILL6 fork-en-tool, SKILL5 gate-permisos (=GAP-SKILL1/B-02). Cabo que aterriza: **FIND-MCP16** (prompts→commands
+ skills MCP `srv:skill` loadedFrom mcp, builder `mcpSkills.ts` no-vendorizado). Archivo A más grande: el motor
`commands.ts` + `loadSkillsDir.ts` (L08) — releer anclas de la re-auditoría, no re-derivar.

---

## 12 · cap-skills — VALIDADA (2ª vuelta, gate 11 de ENTRADA) · 2026-07-20
- **Lado B leído 1→EOF esta ronda**: los 8 `capabilities/skills/*.py` (`provider.py` 182 el más grande L08,
  `skill_tool.py` 123, `loader.py` 123, `frontmatter.py` 115, `store.py` 71, `commands.py` 67, `state.py` 39,
  `__init__.py` 34) + el **ENSAMBLADOR** `factory._build_capability_manager:132-175` + `capabilities/manager.py`
  112 + `loop/agent_loop.py:85-352` (1→EOF de los tramos de cableado) + grep prod-vs-test.
- **Lado A RE-LEÍDO 1→EOF ESTA ronda** (tras reproche "no has vuelto a leer A" — el 1er cierre dijo "A no
  re-abierto por diseño" = fallo L11 idéntico a 11): los 10 A in-scope 1→EOF cotejando cada cita — `SkillTool.ts`
  1108 (checkPermissions 432-577/SAFE_SKILL_PROPERTIES 875-908→SKILL5/19, validateInput 354-430→SKILL16/3, call
  fork 622→SKILL6, contextModifier model`[1m]`815/effort→SKILL4/7, mapToolResult mín+newMessages→SKILL8,
  getAllCommands uniqBy→MCP16, executeForkedSkill clearInvokedSkillsForAgent finally 287→SKILL10), `loadSkillsDir.ts`
  1086 (parseSkillFrontmatterFields 16 campos 185-265→SKILL2/3/7, getPromptForCommand callable+subst+bash-gate
  344-399→SKILL19/4, 5 fuentes 638-804→SKILL1, activate/discover 861-1058→SKILL12, registerMCPSkillBuilders→MCP16),
  `commands.ts` 754 (getSkillToolCommands 563-581→SKILL17, getMcpSkillCommands→MCP16, findCommand 688-698→SKILL16),
  `prompt.ts` 241 (budget 1%/250/bundled→SKILL9, prompt BLOCKING→SKILL18), `bundledSkills.ts` 220 (registerBundledSkill
  +files-guards→SKILL15), `mcpSkillBuilders.ts` 44, `registerSkillHooks.ts` 64 (→SKILL11), `skillUsageTracking.ts` 55
  (half-life 7d→SKILL14), `skillChangeDetector.ts` 311 (→SKILL13), `constants.ts` 1. **CERO discrepancias, citas
  exactas = evidencia de lectura real (L11).** Satélites de otras categorías (attachments/messages/state/client/
  mcp-utils→07/01/11; bundled/*.ts ⛔) L07 con destino.
- **✅/🔀 SOSTENIDOS abriendo B** (mini-ledger en el doc): `SkillsProvider` ensamblado (factory:160-164→manager:175
  →runtime:194/221, MISMA instancia root+subagentes runtime.py:358); **tool `Skill` reensamblada per-turno**
  (agent_loop.py:194-200→manager.tools→provider.tools, hermano EXACTO de MCP 11); `context_modifier` allowed-tools
  →allow+mark_discovered **APLICADO en el loop** (skill_tool.py:119 set → agent_loop.py:332-337 aplica, no sólo
  atributo); `active_skills`/invoked_skills (S3/S5) inyectados **cada turno** vía `_inject_recall`→`manager.
  active_context`→`provider.active_context` (agent_loop.py:218/112-130); store inyectable+startup (manager.startup
  →runtime:123); unregister-en-vivo; slash desacoplado (commands.py, seam integrador, el loop no lo importa).
- **❌ CONVERGEN por lectura directa de B**: `frontmatter.py` = **exactamente 6** campos ⇒ FIND-SKILL2/3;
  `render_skill` estático ⇒ SKILL19; `requires_permission=False` ⇒ SKILL5; `execute` inline ⇒ SKILL6; `state.get`
  exacto ⇒ SKILL16; `catalog` filtra sólo por `is_enabled` + `when_to_use=description` ⇒ SKILL17+confirma SKILL2;
  `result.output=render` completo→`role:tool` (agent_loop.py:319-323) sin new_messages ⇒ SKILL8 🔀; sin loaded_from
  /merge MCP ⇒ FIND-MCP16. Ninguna ❌ falsa.
- **CERO cambios de estado** (✅~13·🟡~9·🔀~4·❌~19·⛔~7 intactos), código intacto, suite no re-ejecutada.
- **2 PRECISIONES de mecanismo (no voltean estado, leyendo el ensamblador — L09)**: (1) **FIND-SKILL9** — el doc
  decía "`catalog()` re-emite TODO cada turno"; **IMPRECISO**: `SkillsProvider.catalog()` tiene por único
  consumidor prod a `CapabilityManager.catalog()` (manager.py:47), que **NO tiene ningún caller de prod** (grep:
  sólo `tests/*`). El loop rinde al modelo por turno la **tool `Skill`** + los recordatorios de **skills activas**
  (`active_context`), **nunca** el catálogo. ⇒ `catalog()` = **seam de consumo del integrador/introspección**
  (hermano de `stream()`/`subscribe_all` 07, `HookRunner.register` 06), NO surface per-turno. **El ❌ vs canónico
  SE SOSTIENE** (canónico tiene `skill_listing` incremental+budget; el runtime **no surface ningún listing de
  skills al modelo en el standalone** — gap si acaso MAYOR). (2) **FIND-SKILL7** — `skill.model` se ALMACENA en
  `active_skills[name]['model']` (skill_tool.py:56) pero ningún prod lo lee para overridear modelo/effort
  (cara B-interna del ❌, no lo voltea).
- **1 COSTURA LATENTE NUEVA — LAT-SKILL1** (tech-debt B-interno, NO deuda A↔B, L10/L11): `SkillTool.input_schema`
  anuncia `args` (skill_tool.py:83-89) que `execute()` **descarta** (:108 lee sólo `command`; `render_skill` sin
  args :18). Costura a medio cablear = superficie B-interna de FIND-SKILL4 (gap A↔B ❌ intacto). Gemela del announce
  singular 09·FIND-TOOL6. **Se CABLEA vía SkR3 (no se borra)** — distinto de los huérfanos duplicados-muertos.
  → DEUDA-B §B-orphans (ítem 8).
- **§Honestidad**: el value-add del gate 11 fue **abrir el ENSAMBLADOR** (invisible sin él) — ahí apareció que
  `catalog()` no está cableado al modelo (la 1ª pasada asumió "re-emite cada turno" sin seguir el consumidor =
  justo el modo de fallo que L09 caza) + LAT-SKILL1. Método interiorizado (idéntico 07/09/11): conclusión de
  cableado = leer el ensamblador 1→EOF; grep sólo para AUSENCIA.
- **⚠ CIERRE EN 2 ITERACIONES (gate auto-adversarial del usuario, 2026-07-20)**: el 1er cierre SOBRE-DECLARÓ
  "ensamblador 1→EOF" habiéndolo leído por tramos (`factory` 120-234; `loop` 85-234+283-352) y apoyando FIND-SKILL9
  en grep+lectura parcial del loop. Al reproche LEÍ los tramos omitidos: `factory` 1-119 (`CapabilitiesConfig`
  33-55 = inputs skills; `skill_catalog` = path legacy resolver muerto) + 235-267 (`create_runtime`) + **`agent_
  loop.py:235-282` = región de la llamada al modelo** (`complete(ctx.messages, tool_schemas, …)`): **NO surface
  `catalog()`/skill_listing** ⇒ el modelo ve skills sólo por la tool `Skill` + recordatorios de skills activas
  (`_inject_recall`:218). **FIND-SKILL9 CONFIRMADO por LECTURA del tramo antes omitido, no por grep.** L08
  "abierto por tramos ≠ íntegro" reincidente; cerrado. Ensamblador ahora íntegro esta ronda.
- **Doc**: `12-cap-skills.md` — marcador Estado (cabecera) + bloque "Re-visita de COMPLETITUD (2ª vuelta · gate
  11/L09)" con mini-ledger de consumidores + 2 precisiones + LAT-SKILL1 + §honestidad + 4 preguntas + **VEREDICTO**.
  README fila 12 + DEUDA-B §B-orphans (LAT-SKILL1, ítem 8) + este PROGRESS actualizados.

## 13 · cap-memory — **VALIDADA (gate 11/L09) 2026-07-20** · cero cambios de estado, código intacto
- **Lado B 1→EOF**: `store.py` 138 · `provider.py` 102 · `recall.py` 40 · `prompt.py` 48 · `__init__.py` 19.
  **ENSAMBLADOR 1→EOF esta ronda** (L09): `factory.py` 267 + `manager.py` 112 + `agent_loop.py:85-234` (cuerpo del
  ensamblado per-turno).
- **Lado A in-scope RE-LEÍDO 1→EOF ESTA ronda** (L11, no apoyarse en la 1ª pasada): `extractMemories.ts` 615 ·
  `memdir.ts` 507 · `memoryTypes.ts` 271 · `paths.ts` 278 · `memoryScan.ts` 94 · `findRelevantMemories.ts` 141 ·
  `memoryAge.ts` 53 · `agentMemory.ts` 177 **+ `prompts.ts` 154 + `agentMemorySnapshot.ts` 197** (estos 2 releídos tras
  el gate auto-adversarial del usuario — ver auto-corrección abajo). **CERO discrepancias, citas exactas, los 10
  in-scope 1→EOF.** Team/session/UI = fuera-de-alcance-con-destino (re-audit 2026-07-14 cubrió los grandes).
- **Reensamblado PER-TURNO confirmado por el ENSAMBLADOR** (agent_loop.py:185-218 dentro del `for _turn`): cada turno
  `system_prompt_sections`→`MemoryProvider.system_prompt_section` (re-lee índice de disco + `build_memory_activation`)
  + `_inject_recall`→`active_context`→`scan`+`rank_memories` (`<system-reminder>` con dedup). Hermano EXACTO de
  MCP/Skills. `MemoryProvider` registrado **CONDICIONAL** (factory:166-172: sólo si `memory_root`/`memory_store` —
  seam de integrador); `capability_manager` MISMA instancia raíz+subagentes. Test asegura loop NO importa
  `capabilities.memory` (consumo polimórfico).
- **❌ re-confirmados por CABLEADO/ABSENCIA**: **FIND-MEM1** (grep wiring extracción = vacío; A re-leído confirma las 8
  sub-piezas canUseTool/cursor/exclusión/throttle/coalescing/drain/main-only/skip-remote); **FIND-MEM10** (`agent_id`
  = `uuid.uuid4()` FRESCO por despacho en runtime.py:205 Y fork:69, runtime:427 lo comenta; vs canónico
  `sanitizeAgentTypeForPath(agentType)` estable + 3 scopes agentMemory.ts:52-65 → no persiste entre despachos);
  **FIND-MEM9** (clave `f"{user}/{agent}"` cruda a `self._root/scope` sin sanitizar = traversal; canónico
  `sanitizePath(getAutoMemBase())` paths.ts:231); MEM4/5/6/7/8/12 re-confirmados abriendo store.py/prompt.py.
- **1 PRECISIÓN (no voltea estado)**: fila-D "Recall post-compactación · `compact_context=active_context` ✅" — el
  mecanismo citado **no es el vivo**: `compact_context` tiene **0 consumidores de prod** (grep: sólo tests; los
  agregadores `manager.compact_context`:104 y `contracts/compaction.py`:11-23 tampoco tienen caller). La equivalencia
  observable la entrega el **re-inject PER-TURNO de `active_context`** (loop:218; la compactación al recortar rehabilita
  el re-surface, comentario loop:214-217). ⇒ `compact_context` = costura latente que espera al **motor de compactación
  NO PORTADO** (02·GAP-L4 / 01·CompactionProvider) = cara aguas-abajo de un ❌ A↔B YA conocido, transversal a todos los
  providers; **NO** nuevo B-orphan (anti-padding L10). El ✅ se apoya ahora en el mecanismo correcto.
- **Cabos**: SessionMemory→01/compact (satélite, no re-leído); **FIND-SKILL14 NO aterriza** (ranking-por-uso es de
  skills; el recall de memoria no usa señal de uso — ni runtime keyword+mtime ni canónico selector-LLM);
  **invoked/cleanup-por-agent NO aterriza** (la memoria no tiene estado mutable por-agente; el `_surfaced` de MeR2 es
  propuesta futura). Ambos cerrados sin finding.
- **Evidencia**: 18 passed (`test_memory_provider`+`test_memory_recall`+`test_memory_loop_e2e`), re-ejecutada esta
  ronda. Sin costuras latentes NUEVAS tipo to_llm/category/LAT-*.
- **⚠ AUTO-CORRECCIÓN (gate auto-adversarial del usuario, 2026-07-20)**: el 1er cierre declaró `prompts.ts`/
  `agentMemorySnapshot.ts` "NO re-leídos" (apoyo en el ledger 1ª pasada = fallo L11 idéntico a 11/12) y confirmó
  FIND-MEM10 por la **línea de grep** de runtime:205/fork:69 (viola L09). Al reproche: (1) leídos ambos 1→EOF esta
  ronda → cero discrepancias (extraction-prompt reutiliza taxonomía; snapshot-sync keyed por agentType, ausente en B;
  refuerzan MEM1/MEM10, sin finding nuevo); (2) leído el CONTEXTO de `_build_child` runtime:198-218 + `fork` 61-93 →
  uuid fresco en la ruta real, por LECTURA. Los 10 A in-scope quedan 1→EOF; cierre GANADO. Regla re-interiorizada:
  todo A in-scope se re-abre 1→EOF esta ronda; cableado se lee en su contexto — grep sólo orienta/prueba ausencia.
- **Doc**: `13-cap-memory.md` — marcador Estado (cabecera) + bloque "Re-visita de COMPLETITUD (gate 11/L09)" con
  cableado-del-ensamblador + mini-ledger de consumidores + precisión fila-D + ledger de lectura A/B + §honestidad +
  4 preguntas + **VEREDICTO**. README fila 13 + este PROGRESS actualizados. **CERO cambios de estado, código intacto,
  cero B-orphans nuevos.**

**SIGUIENTE → 14 · cap-plan.** (01→13 completos con gate 11; NO quedan pendientes de verificación de la 2ª vuelta.)
Rutas: B `src/agentic_runtime/capabilities/plan/*` (`PlanModeProvider` sin-tools-ni-catálogo; ensamblador
`factory._build_capability_manager:146` — `PlanModeProvider()` SIEMPRE presente, a diferencia de MCP/Skills/Memory
condicionales) + tools nativas `EnterPlanMode`/`ExitPlanMode` (10) vs A `tools/{Enter,Exit}PlanModeTool`,
`utils/{plans,planModeV2}.ts`, `built-in/{plan,explore}Agent.ts`, cadencia en `messages.ts`/`attachments.ts`.
`14-cap-plan.md` 1ª pasada = tabla A-H + FIND-PLAN1-14 + §Plan PlR1-14 (6 passing/6 xfail). Aplicar gate 11: para cada
✅/🔀 abrir el consumidor real en B + el ensamblador (¿el plan aprobado se re-inyecta per-turno como memory/skills?
`compact_context` — ojo a la MISMA precisión que 13: confirmar si el hook está cableado o es latente). Focos:
**PLAN3** built-ins Explore/Plan NO registrados → reminder 5-fases letra muerta (=05·agents; confirmar por cableado
del resolver); **PLAN4** candado read-only no-forzado + `is_session_plan_file` sin consumidor (→B-02, seguir la clave);
**PLAN6** plan no-re-inyectado-tras-compact (nexo directo con la precisión `compact_context` de 13); PLAN2 exit-sin-guard;
PLAN11 exit tool_result empobrecido; **FIND-PLAN-APPROVAL-CONTRACT** (modo-resultante/clear-context/feedback → front+B-02).
Archivo A más grande del árbol plan (L08) — RE-LEER A 1→EOF esta ronda (no apoyarse en la 1ª pasada, reproche recurrente
11/12/13), citas exactas = evidencia.

---

## 14 · cap-plan — VALIDADA (2ª vuelta, gate 11 de ENTRADA) · 2026-07-20
**Modo**: gate 11 — cada ✅/🔀 re-verificada abriendo B **y el ENSAMBLADOR**, no la tabla; A in-scope RE-LEÍDO
1→EOF esta ronda (L11). **Resultado**: doc (ya re-auditado 2026-07-14, no fue confirmación-de-doc) **se sostiene
sobre base correcta**; **1 discrepancia real** (FIND-PLAN1 sub-enumerado) + **2 precisiones de mecanismo**;
**cero cambios de estado**; **código intacto**; tests no re-ejecutados.
- **Leído (B) 1→EOF**: `capabilities/plan/{plan_file.py 108, provider.py 171 el más grande L08, __init__.py 3}` +
  `tools/native/plan_mode.py` 107 + **ENSAMBLADOR** `factory.py` 267 + `manager.py` 111 + `agent_loop.py:85-234`
  + `execution/agents.py` 66 + `runtime.py:336-365` + `tools/factory.py:40-55` + grep prod-vs-test.
- **Lado A RE-LEÍDO 1→EOF ESTA ronda** (citas exactas=evidencia L11): `ExitPlanModeV2Tool.ts` 493 (el más grande
  L08), `plans.ts` 397, `EnterPlanModeTool.ts` 126, `EnterPlanMode/prompt.ts` 170, `ExitPlanMode/prompt.ts` 29,
  `planModeV2.ts` 95, `planAgent.ts` 92, `exploreAgent.ts` 83, 2 `constants.ts`. **CERO discrepancias en filas
  documentadas** (A1-A8/B1-B10/C1-C9/D1-D4/E1-E3 con anclas exactas verificadas).
- **✅/🔀 sostenidos por CABLEADO**: `PlanModeProvider()` registrado **INCONDICIONAL** (`factory.py:146`, a
  diferencia de MCP/Skills/Memory condicionales); `active_context` inyectado **PER-TURNO** (`agent_loop.py:218`→
  `_inject_recall`:112-130→`manager.active_context`:98-102, hermano EXACTO de MCP/Skills/Memory);
  `context_modifier`/`ends_turn` aplicados en el loop (332-339, =10·CORR-09-CTXMOD); tools en pool nativo
  (`tools/factory.py:47/49`) sin `deferred` ⇒ siempre anunciadas (FIND-PLAN14 por cableado).
- **❌ re-confirmados por CABLEADO/AUSENCIA**: **FIND-PLAN3** — `execution/agents.py` **sin tabla de built-ins**
  (sólo `AgentDefinition`+protocolo, host-injected); `agent_resolver=None` en standalone ⇒ `runtime.py:342-343`
  no resuelve ⇒ fork **genérico** (350-353): hereda modelo, **sin** system-prompt read-only ni restricción de
  tools ⇒ reminder de 5 fases letra muerta (no sólo "no registrado"). →05. **FIND-PLAN4** — `is_session_plan_file`
  (plan_file.py:58-63) **0 consumidores prod** (grep) ⇒ candado sólo texto del reminder, ningún gate lo fuerza
  ⇒ cara B-interna del ❌ A↔B (como LAT-HOOK1), **no** B-orphan nuevo ni padding. →**B-02**+write-tools.
  **FIND-PLAN7** (fork no hereda plan) confirmado →05·fork.
- **DISCREPANCIA REAL (FIND-PLAN1 sub-enumerado)**: al re-leer A 1→EOF, el `prompt()` extenso NO portado aplica a
  **AMBAS** tools, no sólo EnterPlanMode. `ExitPlanMode.prompt()`=`EXIT_PLAN_MODE_V2_TOOL_PROMPT`
  (`ExitPlanMode/prompt.ts:6-29`: "When to Use — sólo planning no research" + advertencia AskUserQuestion) ausente
  del `ExitPlanModeTool.description` de 2 líneas. **Corregido**: FIND-PLAN1 ampliado + fila B11 + PlR1 ampliado.
  Análogo a feat14/15 de 01 y GAP-MODE2 de 04. 🟡 nuevo, **no** voltea estado.
- **PRECISIÓN 1 (FIND-PLAN8, no voltea estado)**: `_inject_recall` (`agent_loop.py:121-128`) **deduplica** — el
  sparse es idéntico cada turno (mismo token) ⇒ inyectado 1 vez (tras full) y luego **suprimido**, no "cada
  iteración". El 🔀 se sostiene (cadencia≠canónico); el ruido es menor de lo enunciado.
- **PRECISIÓN 2 (FIND-PLAN6, no voltea estado)**: el ❌ doblemente sostenido — `PlanModeProvider.compact_context`
  devuelve `[]` **Y** toda la cadena `compact_context` tiene 0-caller-prod (=13·fila-D, transversal al
  motor-compactación ❌ NO portado 01/02). Cross-ref 13.
- **Sin costuras latentes NUEVAS** tipo to_llm/category/LAT-*: `is_session_plan_file`=cara B-interna de FIND-PLAN4;
  `compact_context`=transversal ya homed 13. Cero B-orphans nuevos.
- **⚠ Auto-corrección (gate auto-adversarial del usuario, reproche recurrente 11/12/13)**: el 1er cierre re-leyó los
  7 archivos de código A 1→EOF pero se apoyó en la 1ª pasada para las filas **F1-F8/G1-G6** (lado A en satélites
  `messages.ts`/`attachments.ts`/`state.ts`/`compact.ts`). Al reproche RE-LEÍ sus tramos-de-plan 1→EOF esta ronda →
  CERO discrepancias, PERO anclas driftadas (`messages.ts` `plan_file_reference` 3620→3636, exit 3826→3848 — L11).
  Confirmados por re-lectura: F4/FIND-PLAN12 (subagent A incluye `planFilePath` 3400/3410, B no), B10 🔀 (exit
  canónico 3848-3854 sólo referencia path), FIND-PLAN8 (throttle cuenta turnos HUMANOS attachments.ts:1139-1142 vs
  runtime por `_turn`), FIND-PLAN6 (2 attachments compact.ts:1470-1486+1542-1560, ambos ausentes en B). Regla:
  L07 acota el archivo, NO exime de re-leer el tramo in-scope 1→EOF esta ronda.
- **Doc**: `14-cap-plan.md` — Estado (cabecera) + FIND-PLAN1 ampliado + fila B11 + PlR1 ampliado + bloque
  "Re-visita de COMPLETITUD (2ª vuelta · gate 11/L09)" con mini-ledger de consumidores + 2 precisiones + ledger de
  lectura A/B (columna Lectura) + §honestidad + 4 preguntas + **VEREDICTO**. README fila 14 + este PROGRESS
  actualizados.

**SIGUIENTE → 15 · storage.** (01→14 completos con gate 11; NO quedan pendientes de verificación de la 2ª vuelta.)

## 15 · storage — VALIDADA (2ª vuelta, gate 11 de ENTRADA) · 2026-07-20
**Modo**: gate 11 — cada ✅/🔀 re-verificada abriendo B **y el ENSAMBLADOR `factory.py` 1→EOF (L09)**, no la tabla;
A in-scope RE-LEÍDO 1→EOF esta ronda (L11). **Resultado**: doc (ya re-auditado 2026-07-14, no fue confirmación-de-doc
en A/B, PERO sus ✅/🔀 se validaron sin seguir el cableado del ensamblador) **se sostiene**; **2 precisiones de
cableado** (FIND-STOR1 / FIND-STOR12); **CERO cambios de estado** (✅3·🟡7·🔀9·❌15·⛔2 intactos); **código intacto**;
suite re-ejecutada verde.
- **Leído (B) 1→EOF**: `storage/{protocol.py 87, filesystem.py 70, factory.py 33, __init__.py 5}` +
  `contracts/storage.py 40` + `capabilities/mcp/{token_storage.py 65, config_store.py 146}` + `capabilities/skills/store.py 71`
  + `capabilities/plan/plan_file.py 108` + **ENSAMBLADOR `factory.py` 267 1→EOF** + `runtime.py:60-104·195-334·410-435`
  (`_persist`+`ctx.fs`/`_build_child`) + `mcp/provider.py:40-99` (`_default_client`) + `context/tool_use.py 70` +
  `tests/{test_storage_homologation.py 163, test_runtime_storage.py 143}`.
- **Lado A RE-LEÍDO 1→EOF ESTA ronda** (L11, no apoyado en la 1ª pasada): `sessionStorage.ts` **5105** (el más grande
  L08, 6 bloques contiguos 1→EOF), `config.ts` 1817, `settings/settings.ts` 1015, `sessionStoragePortable.ts` 793,
  `fsOperations.ts` 770, `filePersistence.ts` 287, `outputsScanner.ts` 126, `envUtils.ts` 183, `sessionState.ts` 150,
  `WorkerStateUploader.ts` 131, `lockfile.ts` 43 (⛔), `cachePaths.ts` 38, `env.ts` 1-60, `teamMemPaths.ts` 1-75.
  **CERO discrepancias en filas documentadas**; **drift cazado** (L11): `env.ts` **347** vs 341 del ledger (+6 en la
  parte no-storage; `getGlobalClaudeFile:14-26` intacto). B1-B13/A1-A8/C1-C3/D1-D3/E1-E3/F1-F3/STOR13 confirmados por
  lectura directa con citas exactas.
- **Cableado confirmado abriendo el ENSAMBLADOR (`factory._build_local` 1→EOF, L09)**: `factory:186` crea **UNA**
  `storage=StorageRegistry.create(...)` y la reparte → `LocalAgentRuntime(storage=)` (:226→`_persist` runtime.py:428,
  **único productor**, sólo `transcript_key`) + `_build_capability_manager(storage=)` (:194→`McpProvider(storage=)` :152)
  + `fs=config.fs` (:229→`ctx.fs`, **StorageContract SEPARADO**, default `ConfinedFilesystem`, NO derivado de `storage`
  → **FIND-STOR6 dos-seams CONFIRMADO por el ensamblador**).
- **PRECISIÓN 1 (FIND-STOR1, sigue ❌ CRÍTICO)**: los 3 stores "inventa-clave" NO son homogéneos — (a)
  `StorageBackedTokenStorage` **SÍ auto-cableado** por el factory al MISMO `storage`, pero `McpProvider` recibe
  `user_id="mcp"` por **default** (provider.py:50/67; el factory nunca pasa el user real) ⇒ tokens OAuth de **todos los
  usuarios colisionan** bajo `mcp/mcp/<srv>/oauth_tokens.json` (peor que "user=mcp": colisión multi-usuario real). (b)
  `StorageBackedMcpConfigStore`/`StorageBackedSkillStore` **NO** los auto-cablea el factory (inyección pura del
  integrador; claves `mcp/servers.json`/`skills/<name>/SKILL.md` sin scope, sólo corren si se inyectan) ⇒ en standalone
  las únicas claves que tocan `storage` = `transcript_key` + OAuth-MCP(si hay server oauth). Núcleo del ❌ se sostiene y agrava.
- **PRECISIÓN 2 (FIND-STOR12, sigue 🟡)**: `_persist` usa `ctx.user_id or "anon"` (runtime.py:424) PERO `_build_child`
  **siempre** fija `user_id=task.owner_id or uuid` (runtime.py:209) — nunca None ⇒ el `"anon"` es **código muerto
  defensivo**, la colisión que el doc describe **no puede ocurrir** en standalone. El riesgo real (falta de validación
  de user_id/session_id como componentes de clave, liga STOR7) se sostiene; la sub-justificación "anon colisiona" corregida.
- **Cabos aterrizados por cableado**: **11·token_storage** → auto-cableado scope `"mcp"` (arriba). **14·plan_file /
  is_session_plan_file** → `plan_file.py` lee `ctx.storage` (StorageContract) que el runtime **nunca liga** (sólo `ctx.fs`,
  runtime.py:324-325; `ToolUseContext.storage`=None) ⇒ `get_plan`/`plan_file_exists` **INERTES en standalone** = cara-B de
  14·FIND-PLAN4, no deuda nueva (anti-padding L10). **01·StorageContract vs StorageProtocol** → FIND-STOR6 confirmado (dos
  roles, no puenteados). **13·SessionMemory→storage** → memoria usa `FilesystemMemoryStore` (seam propio), no el blob
  StorageProtocol; sin discrepancia.
- **Sin costuras latentes NUEVAS** tipo to_llm/category/LAT-*: `"anon"` muerto = fallback inalcanzable (no maquinaria
  a-medio-cablear); `ctx.storage`-no-bound = seam de integrador por diseño (=fs default ConfinedFilesystem). Cero B-orphans nuevos.
- **Evidencia**: `uv run pytest test_storage_homologation.py test_runtime_storage.py` = **21 passed, 10 xfailed**
  (todos strict, ningún xpass) → gaps FIND-STOR1..13 persisten, ninguno "pasó por sorpresa". Código intacto.
- **Doc**: `15-storage.md` — marcador Estado (cabecera) + bloque "Re-visita de COMPLETITUD (2ª vuelta · gate 11/L09)"
  con cableado-ensamblador + 2 precisiones + cabos + ledger de lectura A/B (columna Lectura ESTA ronda) + §honestidad +
  4 preguntas + **VEREDICTO**. README fila 15 + este PROGRESS actualizados.

## 16 · models — VALIDADA (2ª vuelta · gate 11/L09, 2026-07-20)

**Método:** ✅/🔀 verificadas abriendo el consumidor real de B (no la tabla) + **ENSAMBLADOR `factory.py` 1→EOF**
(L09) + lado A behavioral in-scope **RE-LEÍDO 1→EOF ESTA ronda** (L11, no apoyarse en la 1ª pasada). **CERO
discrepancias en filas documentadas · CERO cambios de estado (✅6·🟡14·🔀3·❌11 intactos) · código intacto · suite
no re-ejecutada** (sin cambio de código, patrón 05–15).

- **Cableado por el ENSAMBLADOR (leído 1→EOF, L09):** `config.model_caller` (factory.py:85)→`LocalAgentRuntime`
  (:219)→`AgentLoop`→call-site único `agent_loop.py:235` `complete(ctx.messages, tool_schemas, stop=ctx.stop,
  model_id=…)` **sin thinking/effort/temperatura** ⇒ FIND-MODELS1 por cableado; `config.small_llm` (:92)→runtime
  (:231)→**prod `runtime.py:410`** `summarize_if_needed`→`complete_simple` (protocolo SEPARADO, seam integrador VIVO,
  cabo 05·LAT-EXEC2); `config.model_id`→fork `resolve_subagent_model` (runtime.py:345/agents.py:46). **HALLAZGO NUEVO:
  `ModelsConfig.extras`/`config.models` (factory.py:59-60/:83) NUNCA consumido por `_build_local` (178-240 leído 1→EOF)
  ⇒ LAT-MODELS1.**
- **✅/🔀 sostenidas abriendo B:** A1🔀 (`_compose_system_prompt` caller.py:17-30 base+sections\n\n / override reemplaza),
  A7✅ (`get_by_provider`+ModelNotFoundError caller.py:199-202), A8✅ (`supports_native_tool_search`→loop:144 cableado),
  B13✅ (`transform_messages.py:150-171` synthetic+skip errored/aborted), B14/16/17✅ (agentic_models provider), D1🔀 (superset).
- **❌ por cableado/lectura de B:** FIND-MODELS1 (thinking: call-site + `ModelRequest`/`thinking_budget` tipo muerto,
  grep=AUSENCIA); **FIND-MODELS2/=07·FIND-EVT1** (usage: caller:226-233 tira cache/coste → loop nunca lee `done.usage`
  253-352 → `session.usage` sin asignar → `registry.complete(0,0)` runtime:403-404, **hilo seguido end-to-end por lectura**;
  DOS `Usage` event/session ambas pobres); FIND-MODELS3 (thinking_* skip caller:245); **FIND-MODELS4** (provider
  `anthropic.py:450/717/732` `getattr(signal,"aborted")` vs `asyncio.Event` del puente caller:188-190 → abort ignorado;
  `CombinedAbortSignal.aborted` existe sin usar; doblemente latente por 08); FIND-MODELS5/6/7 (`withRetry.ts` 1→EOF
  MAX=10/MAX_529=3→Fallback/non-streaming vs 1 request runtime); FIND-MODELS10 (`errors.ts` 1→EOF ~30 ramas/classify/
  categorizeRetryable vs `ErrorEvent(message=str)`→07·D5); FIND-MODELS9/11.
- **Lado A RE-LEÍDO 1→EOF ESTA ronda:** `claude.ts` 3419 (1-1710·1710-2609·2609-3419, más grande L08), `errors.ts` 1207,
  `withRetry.ts` 822, `client.ts` 389, `emptyUsage.ts` 22 → CERO discrepancias, citas exactas = evidencia. `errorUtils.ts`
  abierto (C4 ⛔ front/SSL). Endpoints cuenta/billing = satélites ENTEROS de la capa front/BFF (L07 ⛔-con-destino, no
  re-leídos íntegro esta ronda por L07). Providers non-Anthropic de agentic_models = superset sin contraparte (L10).
- **Costura latente NUEVA (tech-debt B-interno, NO deuda A↔B, L10/L11): LAT-MODELS1** — `ModelsConfig.extras`+`RuntimeConfig.
  models` sin consumidor en el factory + `ModelRequest`/`thinking_budget` tipo muerto (cara B-interna de FIND-MODELS1) →
  **DEUDA-B §B-orphans ítem 9**. Sin otros hallazgos/estados nuevos.
- **Doc:** `16-models.md` — marcador Estado (cabecera) + bloque "Re-visita de COMPLETITUD (2ª vuelta · gate 11/L09)"
  (cableado-ensamblador + mini-ledger consumidores + LAT-MODELS1 + ledger lectura A/B ESTA ronda + §honestidad +
  4 preguntas + **VEREDICTO**). README fila 16 + DEUDA-B §B-orphans (ítem 9) + este PROGRESS actualizados.

## 17 · voice — VALIDADA (2ª vuelta · gate 11/L09, 2026-07-20)

**Método:** ✅/🔀 verificadas abriendo el consumidor real de B (cableado `_resolve_prompt`/`_wire_tts` 1→EOF) +
lado A **RE-LEÍDO 1→EOF ESTA ronda** (L11) + **ausencia de TTS canónico RE-VERIFICADA por barrido ESTA ronda**.
**CERO discrepancias · CERO cambios de estado (✅3·🔀5·❌1 intactos) · 0 costuras latentes nuevas · código intacto.**

- **B por lectura (L09):** STT `runtime.py::_resolve_prompt` (220-232) audio→transcribe→prompt+fallback a
  `task.prompt`, consumido en `_run_loop:377`; TTS `_wire_tts` (234-262) subagente-mudo(:239)/incremental
  speak(:244-248)/no-flush-en-tool_calls(:254), cableado `_run_loop:335`; gate `factory.py:214-216` por-canal;
  entrada `RuntimeTask.audio_prompt`(contracts:32); `test_voice_io.py` 1→EOF cablea A1/B2/B3/B4/B5/C1.
- **FIND-VOICE1 confirmado por LECTURA** (no vs canónico — no hay TTS en A): `_on_token` (runtime.py:244) sanea
  `sanitize_output` sobre el chunk crudo → una ruta partida entre dos `TokenEvent` evade el choke point; el test
  `test_tts_text_is_sanitized_by_presentation` (170-181) sólo prueba ruta en UN chunk (confirmado leyendo). VoR1.
- **PRECISIÓN (no voltea estado, L10/L11): FIND-VOICE1 es tech-debt B-INTERNO de un superset, NO deuda A↔B** — el
  TTS entero es superset (canónico no habla), así que es un bug de corrección en un invariante que el propio runtime
  declara, no una brecha frente a A. Se CABLEA (VoR1), no se borra — hermano de LAT-SKILL1, distinto de los B-orphans
  muertos. Estado ❌+VoR1 intactos.
- **Ausencia de TTS RE-VERIFICADA por barrido ESTA ronda:** `grep -rIniE "speechSynthesis|text-to-speech|TextToSpeech"`
  + `\btts\b|\.speak\(|audio.?out` sobre `claude-code/src` = **0 hits de audio-output**. Árbol canónico voz = 8
  archivos (services/voice*×3, context/voice, commands/voice×2, voiceModeEnabled) + hooks/useVoice*×2, ninguno con TTS.
- **A RE-LEÍDO 1→EOF ESTA ronda:** `useVoice.ts` 1144 (más grande L08) + `useVoiceIntegration.tsx` 1→676 (línea 677 =
  sourcemap base64 no-leíble) → **terminal state-machine / prompt-input / keybinding / motor STT glue, SIN core oculto**;
  la conclusión de la 1ª pasada (todo ⛔-front/integrador) se sostiene por relectura, no heredada. Los 5+ satélites motor
  STT (voice.ts/voiceStreamSTT/keyterms) y front (context/commands/gating) = satélites ENTEROS de otra capa (L07
  ⛔-con-destino, abiertos 1→EOF 1ª pasada, no re-leídos íntegro esta ronda por L07).
- **Doc:** `17-voice.md` — marcador Estado + bloque "Re-visita de COMPLETITUD (2ª vuelta · gate 11/L09)" (cableado B +
  FIND-VOICE1-por-lectura + precisión B-interno/superset + barrido TTS-ausencia + ledger lectura A/B ESTA ronda +
  §honestidad + 4 preguntas + **VEREDICTO**). README fila 17 + este PROGRESS actualizados. Sin cambios en DEUDA-B
  (FIND-VOICE1 se cablea vía VoR1, no es B-orphan muerto).

**SIGUIENTE → 18 · factory.** (01→17 completos con gate 11; NO quedan pendientes de verificación de la 2ª vuelta.)
Ojo (2ª vuelta): `18-factory.md` (1ª pasada). B = `factory.py` (`RuntimeFactory`/`create_runtime`/`RuntimeConfig` +
todas las `*Config` + `register_execution_mode`) + sub-factories (`storage/factory.py`, `tools/factory.py`,
`loop/factory.py`). Es la CATEGORÍA-ENSAMBLADOR por excelencia (L09): `factory.py` YA se leyó 1→EOF en
05/09/11/12/13/14/15/16 — aquí se valida el ensamblado COMO subsistema. Gate 11: para cada ✅/🔀 confirmar el cableado
end-to-end en `_build_local` 1→EOF; **aterrizan aquí TODOS los hallazgos de cableado roto/huérfano de las categorías
previas**: FIND-EXEC1 (`_build_local` nunca llama `set_runner`→`get_runner` revienta, converge 18·C1), §B-orphans
(observer/modes/SignalBus/NativeToolRegistry/category/LAT-EXEC1/LAT-MCP1/LAT-SKILL1/**LAT-MODELS1** — el factory nunca
los consume), registro CONDICIONAL de providers (mcp/skills/memory) vs INCONDICIONAL (plan). Contraparte A = el
bootstrap/wiring canónico (¿hay "factory" o está inline en `query.ts`/entrypoints? — verificar por lectura). Archivo A
más grande del árbol (L08). RE-LEER A 1→EOF esta ronda (no apoyarse en la 1ª pasada, reproche recurrente 11–17),
citas exactas = evidencia.

---

## 18 · factory — VALIDADA (2ª vuelta · gate 11/L09, 2026-07-20) — **CIERRE de la 2ª vuelta (01→18)**

**Método:** ✅/🔀 verificadas siguiendo el dato seam por seam en el **ENSAMBLADOR `factory.py` 267 leído 1→EOF ESTA
ronda** (L09) + **TODO el lado A del bootstrap RE-ABIERTO 1→EOF ESTA ronda** (L11). **CERO discrepancias · CERO
cambios de estado · código intacto.** Evidencia: **16 passed / 3 xfailed(strict, sin xpass)**
(`test_factory_homologation.py` + `test_runtime_factory.py`).

- **Núcleo del ensamblado — cableado en ruta real (✅) por lectura de `_build_local` (178-240):** storage
  `StorageRegistry.create` (:186) → tools `create_tools`→`ToolRegistry` (:189) → `_build_capability_manager` (:194) →
  presentation `config.presentation or IdentityPresentation()` (:207) → exec_env `config.exec_env or
  LocalExecEnvironment()` (:210) → gate voz por-canal (:214-216) → `LocalAgentRuntime(...)` (:218-240).
  `startup`/`shutdown` (runtime.py:118-128)→`CapabilityManager` (:36-42). `execution_mode` en `create_runtime`
  (:243-267) + `register_execution_mode` (:127-129). Providers CONDICIONALES (MCP :148 / Skills :160 / Memory :166)
  vs `PlanModeProvider()` INCONDICIONAL (:146).
- **C1 = FIND-EXEC1 (❌ crítico) — PRECISIÓN de observable (no voltea estado):** `factory` nunca llama `set_runner`
  (grep AUSENCIA: sólo def/export + 3 tests). El doc decía "revienta" — al leer `agent.py:104-107`, el `RuntimeError`
  de `get_runner()` (runner.py:38) **se CAPTURA** → `ToolResult.error`; el observable es "cada spawn devuelve
  tool-error", no crash. **Doblemente roto:** `LocalAgentRuntime` no implementa `run(fork_ctx,*,background)` (tiene
  `dispatch`) ⇒ falta también el adaptador ForkContext→RuntimeTask. Hogar 05·ExR1 intacto.
- **§B-orphans CONVERGEN — el factory NUNCA los consume (anti-padding L10/L11, por lectura + AUSENCIA):**
  `config.models`/`ModelsConfig.extras` (16·LAT-MODELS1, el más fresco) → grep `\.models` en factory.py = **0
  lecturas** (sólo def :59 + campo :83); `get_registry`/`set_registry` (LAT-EXEC1) → factory usa
  `task_registry=config.task_registry` (:224); `observer`/`modes`/`SignalBus`/`NativeToolRegistry` → grep en
  factory.py = **vacío** (+`test_single_registry_no_native_registry_wired` passing); `category`/`to_llm`/
  `timeout_seconds`/`auth_headers`/`Skill.args` → internos, ya homed. Ninguno es Deuda A de 18.
- **Deuda A propia re-confirmada por lectura:** **FaR1** sin fail-fast (`create_runtime(RuntimeConfig())` no valida;
  model_caller=None → `agent_loop.py:181-183` warning+return; canónico `init.ts:65`→`ConfigParseError:216`→
  `gracefulShutdownSync(1):224`); **FaR2** resolver legacy muerto (factory `:197-201/:222`; loop `:194 if` siempre
  gana → `:201 elif` inalcanzable); **FaR3** ternario muerto `:129`. C2(memoria→Stop `setup.ts:294 initSessionMemory`)
  / C3(built-ins→14) / C5(user_id a stores→15) re-confirmadas.
- **A RE-LEÍDO 1→EOF ESTA ronda (L11):** `state.ts` 1758 (seed + STATE singleton :429 + ~130 accessors; ⛔-arquitectónico
  por lectura, L08), `setup.ts` 477 (F1 setCwd:161/captureHooks:166 · C2 initSessionMemory:294 · F4 bypass:395-442),
  `init.ts` 340 (F5 memoize:57 · FaR1 enableConfigs:65/ConfigParseError:216/gracefulShutdownSync(1):224 · F2 :74/:269
  · E1/E2 :87/:189/:195), `cli.tsx` 302 (⛔ terminal-entrypoint dispatcher→main.tsx, L02), `mcp.ts` 196 (⛔
  MCP-server-mode: sirve al propio CC como servidor MCP, L02). Tamaños idénticos a la 1ª pasada (sin drift); esta
  ronda fija anclas exactas.
- **Sin costuras latentes NUEVAS** (18 no añade features; confirma que las conocidas no se cablean). **Sin cambios en
  DEUDA-B** (los §B-orphans quedan confirmados-convergentes aquí; la decisión de borrar/cablear ya vive en
  `DEUDA-B §B-orphans`).
- **Doc:** `18-factory.md` — marcador Estado + bloque "§Re-visita de COMPLETITUD (2ª vuelta · gate 11/L09)"
  (cableado-ensamblador + precisión C1 + tabla §B-orphans-convergen + Deuda A + C2/C3/C5 + ledger lectura A/B ESTA
  ronda + §honestidad + 4 preguntas + **VEREDICTO**). README fila 18 (🟡→✅) + encabezado (2ª vuelta COMPLETA) + este
  PROGRESS actualizados.

**VEREDICTO: ✅ 18·factory VALIDADA. La 2ª vuelta de validación (gate 11/L09) sobre 01→18 queda COMPLETA.** No quedan
subsistemas por validar. Siguiente (fuera del bucle 01→18): re-visita de 2ª pasada de `DEUDA-B-transversal.md` si
aplica (los §B-orphans ya quedaron confirmados-convergentes en 18).
