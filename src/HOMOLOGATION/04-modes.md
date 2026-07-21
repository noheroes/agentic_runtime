# 04 · modes

**Fase:** VALIDADA en 2ª vuelta con learned_lessons/09 de ENTRADA · 2026-07-19 (ver §Re-visita de
COMPLETITUD al final). Discrepancia: GAP-MODE2 sub-enumerada (1→4 ítems) + precisión de línea; **código
intacto**. Documentación 1ª pasada previa: sin ajustes al código del runtime.
**Runtime:** `src/agentic_runtime/modes/{protocols.py (16 LOC), manager.py (44), __init__.py (4)}`
**Contrapartes canónicas (leídas ÍNTEGRAS, no por hitos):**
- `coordinator/coordinatorMode.ts` (369 LOC) — modo de **sesión** coordinator/normal: `isCoordinatorMode`
  (gate `feature('COORDINATOR_MODE')` + env `CLAUDE_CODE_COORDINATOR_MODE`), `matchSessionMode` (reconcilia
  el modo al reanudar sesión), `getCoordinatorUserContext`/`getCoordinatorSystemPrompt` (prompt de líder).
- `hooks/useSessionBackgrounding.ts` (158) — **backgrounding** de la sesión (Ctrl+B): flip `isBackgrounded`
  del task, `foregroundedTaskId`, sync de mensajes/loading del task foregrounded al view principal.
- `hooks/toolPermission/handlers/coordinatorHandler.ts` (65) — flujo de permisos del worker coordinator
  (hooks → classifier → cae al diálogo). Cruza con 06·hooks.
- `hooks/useBackgroundTaskNavigation.ts` (251) — navegación Shift+↑/↓ entre líder/teammates, kill/view.
- `utils/backgroundHousekeeping.ts` (94) — mantenimiento periódico de sesión (cleanup, auto-update,
  extractMemories, autoDream). No es "modo" — se lee para descartarlo del alcance.

**Contexto ya establecido (no se re-deriva):** el eje **backgrounding real** del runtime NO vive en
`modes/` sino en `execution/tasks/registry.py` (`TaskRecord.is_backgrounded`, mutable, relativo al
observador) + `execution/local/notification.py` (canal `<task-notification>`) + el **filtro por KIND**
del toolset (`capabilities/resolver.py` + `tools/registry.list_available(mode=…)`). Todo esto se
documentó/verificó en **03·context (E, B3)** y `test_modes_background.py`. Aquí se contrasta el
**subsistema `modes/`** contra el canónico y se resuelve su relación con esos ejes.

## Naturaleza del subsistema — el hallazgo central

En el canónico **"modo" no es un concepto único**: son **tres ejes ortogonales**, cada uno con su
mecanismo y su alcance:

1. **Modo de sesión** coordinator↔normal (`coordinatorMode.ts`). Gateado tras `feature('COORDINATOR_MODE')`
   + env — **experimental incluso en el canónico**. Es la topología líder/worker del swarm ⇒ ya marcada
   **⛔ N/A core** en **02·E3** (`utils/swarm`, `SendMessageTool`, `TeamCreate/Delete`). El runtime modela
   subagentes, no teammates-pares (grep=0).
2. **Backgrounding** por-task (`useSessionBackgrounding.ts`): `isBackgrounded` (flag mutable relativo al
   observador) + `foregroundedTaskId` (qué task async se está mirando ahora) + Ctrl+B + sync de mensajes.
   La UI (Ctrl+B, sync a la vista) es **⛔ terminal**; el **comportamiento observable** (un task corre
   desatendido, notifica al terminar, se puede re-background/foreground) **sí** vive en el runtime — pero
   en `execution` (registry) + `notification`, **no en `modes/`**.
3. **Fork** (snapshot/aislamiento). Existe en el canónico (`createSubagentContext`, `ForkSnapshot`) y en el
   runtime (`execution/fork/`). Pertenece a **05·execution/fork**, no a este subsistema.

**El runtime `modes/` (AgentMode {FOREGROUND, BACKGROUND, FORK} + ModeManager) colapsa esos tres ejes en
un solo enum por-task, y — el punto clave — no está cableado a nada.** El loop, el `LocalAgentRuntime`, el
resolver de capabilities y la factory **nunca consultan `ModeManager`**. Las rutas reales derivan su
propia noción de modo:
- El **loop** deriva `mode = "background" if ctx.is_subagent else "foreground"` (agent_loop.py:91) como
  string local para filtrar el toolset — no lee `AgentMode`.
- El **resolver** filtra por `ctx.is_subagent` (KIND), no por `is_backgrounded` ni por `AgentMode`.
- La **notificación al completar** del `LocalAgentRuntime` es **incondicional** (`_notify` def en
  runtime.py:294, gateada sólo por `parent_session_id is None` → early-return en 297, body 299-304) —
  **no** consulta `ModeManager.on_complete` ni `is_backgrounded`.

⇒ `modes/` es una **abstracción especulativa huérfana**: probada en aislamiento (`test_mode_manager.py`,
9 tests) pero desconectada del sistema. Ver **FIND-MODE1**.

> Nota de naming: la `factory.create_runtime(execution_mode=…)` (factory.py:246-268) y `RuntimeFactory._modes`
> son **otro concepto** — el registro de *backends de ejecución* (local/remote/tmux/kubernetes/lambda), no
> el `AgentMode` de un task. No confundir. Contraparte canónica: `bootstrap`/`entrypoints` ⇒ **18·factory**.

## Evidencia ejecutada
- **Lint** (`modes/` + `test_modes_homologation.py`): `ruff` ✅ (All checks passed) · `mypy` ✅ (Success,
  3 archivos) · `bandit` ✅ (0 hallazgos).
- **Tests**: `test_mode_manager.py` (9 passed — unit del ModeManager huérfano) + `test_modes_background.py`
  (4 passed — la ruta **real**: filtro por KIND + `is_backgrounded` mutable ortogonal al toolset) +
  `test_modes_homologation.py` (2 passed + 1 xfailed).
- **xfail(strict)** nuevo como evidencia de gap: **FIND-MODE1** (`test_mode_manager_gates_notification`:
  `ModeManager` no cableado a la ruta de notificación de `LocalAgentRuntime`).
- **Suite global tras 04: 561 passed · 3 skipped · 11 xfailed** (era 559 · 3 · 10 tras 03 ⇒ +2 passed,
  +1 xfailed, **sin regresiones**).

## Tabla feature-by-feature

### A · Modo de sesión coordinator↔normal (`coordinatorMode.ts`, íntegro)
| # | Feature canónica | Runtime | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| A1 | `isCoordinatorMode()` (gate `feature('COORDINATOR_MODE')` + env) | — | ⛔ | Topología líder/worker del swarm. Experimental en el canónico. = **02·E3** (RESUELTO ⛔). El runtime modela subagentes, no teammates-pares. Si se adopta ⇒ subsistema nuevo, no gap. |
| A2 | `matchSessionMode(stored)` — reconcilia modo al reanudar sesión (flip env, log `tengu_coordinator_mode_switched`) | — | ⛔ | Persistencia del modo de sesión + reconciliación. Depende de A1. |
| A3 | `getCoordinatorUserContext(mcpClients, scratchpadDir)` — inyecta "workers tienen estas tools/MCP/scratchpad" al user-context | — | ⛔ | Prompt de coordinación. Depende de A1. Nota: el listado de tools del worker = `ASYNC_AGENT_ALLOWED_TOOLS` (ver C). |
| A4 | `getCoordinatorSystemPrompt()` — system prompt completo del líder | — | ⛔ | System prompt del rol coordinator. Depende de A1. |
| A5 | `INTERNAL_WORKER_TOOLS` (TeamCreate/Delete/SendMessage/SyntheticOutput ocultas del anuncio a workers) | — | ⛔ | Tools internas del swarm. = 02·E3 + 10·tools-native (candidatas ⛔). |

### B · Backgrounding por-task (`useSessionBackgrounding.ts`, íntegro)
| # | Feature canónica | Runtime | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| B1 | `task.isBackgrounded` (flag mutable por-task, relativo al observador) | `TaskRecord.is_backgrounded` + `registry.set_backgrounded()` | ✅ | Espejo directo. Mutable, no re-filtra el toolset (por KIND). Verificado en `test_modes_background.py`. Ver 03·B3. |
| B2 | `foregroundedTaskId` (qué task async se está mirando en el view principal) | — | ⛔ | Concepto **de vista**: "cuál de mis tasks background estoy observando ahora". Sin terminal no hay "view único" que multiplexar. El runtime expone TODOS los tasks vía `registry.list_for(session)`; el consumidor (BFF) elige cuál proyectar. Homologación *de comportamiento*: el dato para foreground-uno existe (`list_for` + eventos), la selección es del integrador. |
| B3 | Ctrl+B → `handleBackgroundSession()` (background la query actual / re-background el foregrounded) | — | ⛔ | Keybinding de terminal. El *acto* de promover a background = `set_backgrounded(id, True)`; el disparo (tecla) es UI. |
| B4 | Re-background: flip `isBackgrounded=true`, limpiar messages/abort del view | `set_backgrounded(id, True)` | 🔀 | El runtime hace sólo el flip de estado; limpiar messages/abort del *view* es del consumidor (no hay view compartido). El registry no toca `ctx` (verificado B3 de 03). |
| B5 | Foreground: sync `foregroundedTask.messages` → `setMessages`, `status==='running'`→`setIsLoading`, adoptar `abortController` del task | — | ⛔ | Multiplexado de messages/loading/abort de un task async al REPL único. Puro React/ink. El runtime emite eventos por task; el consumidor los proyecta (D4 de 02). |
| B6 | Task abortado mientras foregrounded → clear foreground, re-background | `registry.kill()` (status→KILLED) + `is_backgrounded` intacto | 🔀 | El runtime marca KILLED en el registry; la transición de vista es del consumidor. |
| B7 | Task completado mientras foregrounded → restaurar a background, clear view | `registry.complete()` + notificación por canal | 🔀 | Completar dispara `<task-notification>` (notification.py); "restaurar a background" es re-proyección del consumidor. |
| B8 | `foregroundedTask.type !== 'local_agent'` → limpiar foreground | `TaskRecord` sin discriminante `type` (local_agent/local_bash/teammate) | 🟡 | El canónico distingue tipos de task en el mismo mapa `tasks`; el runtime sólo modela el agent-task (bash background y teammates no son tasks del registry). **GAP-MODE1**: si el runtime porta bash-background como task, necesitará un discriminante. Cruza con 10·bash + 05. |

### C · Filtro del toolset del agente desatendido (allowlist vs flag por-tool)
| # | Feature canónica | Runtime | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| C1 | `ASYNC_AGENT_ALLOWED_TOOLS` (Set allowlist: Read/Grep/Glob/Web*/Todo/Shell/Edit/Write/Notebook/Skill/Synthetic/ToolSearch/Worktree) | por-tool `safe_for_background: bool` + `registry.list_available(mode="background")` | 🔀 | **Misma intención, mecanismo invertido.** Canónico: allowlist central que enumera qué entra. Runtime: cada tool declara su propia aptitud; el registry filtra. Ventaja runtime: la aptitud viaja con la tool (no hay lista central a mantener al añadir tools). Verificar que el *conjunto resultante* coincide (ver C2). |
| C2 | Conjunto concreto permitido a un async-agent | subagente ve sólo `safe_for_background=True` | 🟡 | **Homologación de conjunto pendiente de auditar 1:1 en 10·tools-native.** Re-verificado L09 (2026-07-19) abriendo `constants/tools.ts:55-102` (allowlist + bloque `BLOCKED FOR ASYNC AGENTS`) contra `safe_for_background` de cada tool nativo del runtime: la discrepancia **NO se limita a worktree** — ver **GAP-MODE2** para la enumeración concreta (worktree, AgentTool, TaskStop, TaskOutput). **Ajuste**: reconciliar los 4 en 10·R10. |
| C3 | Gate por KIND (subagente=unattended) independiente de `isBackgrounded` | resolver filtra por `ctx.is_subagent`, no por `is_backgrounded` | ✅ | Los dos ejes son ortogonales y así se implementan: KIND fija el toolset, el flag mutable no re-filtra. = 03·B3. Verificado. |

### D · `modes/` del runtime — `AgentMode` + `ModeManager` (la abstracción huérfana)
| # | Símbolo runtime | ¿Contraparte canónica? | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| D1 | `AgentMode.FOREGROUND / BACKGROUND` | eje B (backgrounding por-task) | 🔀 | El canónico modela esto como `isBackgrounded: bool` **en el task**, no como enum en un manager aparte. El runtime ya tiene el bool en `TaskRecord` (B1) — este enum lo **duplica**. |
| D2 | `AgentMode.FORK` | eje fork (05·execution/fork, `ForkSnapshot`) | 🔀 | Fork no es un "modo de notificación" — es un modo de *aislamiento de contexto*. Meterlo en el mismo enum que FG/BG mezcla ejes ortogonales. El fork real vive en `execution/fork/`. **Ajuste**: sacar FORK del enum o documentar que aquí es sólo un marcador de inmutabilidad. |
| D3 | `ModeManager.register/get_mode/set_mode/unregister` | — (nada lo llama en la ruta real) | ❌ | **Huérfano.** grep: sólo `test_mode_manager.py`. Ni loop, ni `LocalAgentRuntime`, ni resolver, ni factory lo instancian. |
| D4 | `ModeManager.on_complete(id)` → `True` si BACKGROUND (¿notificar al completar?) | notificación real = `LocalAgentRuntime._notify` **incondicional** (runtime.py:294-304) | ❌ | **FIND-MODE1.** La decisión "¿notifico al terminar?" que `on_complete` promete tomar, en la ruta real **no se consulta**: `_notify` siempre encola `<task-notification>` si hay `parent_session_id`. El `ModeManager` no gobierna nada. **Re-verificado L09 (2026-07-19)**: cableado seguido punta a punta — `_notify` sólo guarda `parent_session_id is None` (297) y llama `put_notification`; grep confirma que `modes/` lo importan sólo 2 tests, cero producción. |
| D5 | `set_mode` bloquea transición si FORK (inmutable) | — | 🔀 | Invariante razonable (un fork no se "des-forkea"), pero protege un enum que nadie usa. Si FORK sale del enum (D2), esto sobra. |
| D6 | `on_transition(callback)` — listeners ante cambio de modo | — | ❌ | Primitiva de extensión sin consumidores. Especulativa. |
| D7 | `ModeManagerProtocol` (Protocol) | — | ❌ | Contrato de un subsistema no cableado. |

## Hallazgos

- **FIND-MODE1 (arquitectura / código muerto).** `modes/` (`AgentMode` + `ModeManager` +
  `ModeManagerProtocol`) es una abstracción **huérfana**: 9 tests unitarios la ejercen en aislamiento, pero
  **ninguna ruta de ejecución la consulta**. La decisión que `on_complete` promete (notificar al completar
  sólo si BACKGROUND) la toma en realidad `LocalAgentRuntime._notify` de forma **incondicional**
  (runtime.py:295), sin mirar el manager. El eje backgrounding real es `TaskRecord.is_backgrounded`; el
  eje toolset es `ctx.is_subagent`. **Ajuste (dos caminos, decisión del integrador):**
  (a) **cablear** — `LocalAgentRuntime` consulta `ModeManager.on_complete(task_id)` antes de `_notify`, y
  algo puebla el manager al lanzar el task; o (b) **eliminar** `modes/` y dejar que `is_backgrounded` +
  `is_subagent` + `notification` sean la única representación (recomendado: elimina duplicación de ejes).
  xfail `test_mode_manager_gates_notification`.

- **GAP-MODE1 (B8).** El runtime no discrimina *tipos* de background task (`local_agent` vs `local_bash`
  vs teammate) — el registry sólo modela el agent-task. Si se porta bash-background como task
  observable, `TaskRecord` necesitará un discriminante `type`. Cruza con 10·bash + 05.

- **GAP-MODE2 (C2).** El *conjunto* de tools que ve un agente desatendido no está auditado 1:1 contra
  `ASYNC_AGENT_ALLOWED_TOOLS` + el bloque `BLOCKED FOR ASYNC AGENTS`. **Re-visita L09 (2026-07-19)**: abrir
  el canónico (`constants/tools.ts:55-102`) y `safe_for_background` de cada tool del runtime destapa que la
  discrepancia **NO es sólo worktree** — son **4 ítems concretos** (runtime `safe_for_background` vs canónico):
  1. **worktree** (Enter/Exit): canónico lo **PERMITE** a workers (`ASYNC_AGENT_ALLOWED_TOOLS`, tools.ts:69-70);
     runtime `False` (worktree.py:61,129). Runtime **más restrictivo**.
  2. **AgentTool**: canónico lo **BLOQUEA** ("prevent recursion", tools.ts:92); runtime `True` (agent.py:60)
     con tope de anidamiento `_MAX_SUBAGENT_DEPTH=5` (agent.py:73). Runtime **más permisivo**; la recursión se
     acota por profundidad, no por exclusión ⇒ probable **🔀 por arquitectura** (el runtime modela subagentes
     anidables, no swarm líder/worker) — la clasificación final la decide 10.
  3. **TaskStop**: canónico lo **BLOQUEA** ("requires main-thread task state", tools.ts:95); runtime `True`
     (task_tools.py:178). Runtime **más permisivo**.
  4. **TaskOutput**: canónico lo **BLOQUEA** ("prevent recursion", tools.ts:93); runtime `True`
     (task_tools.py:210). Runtime **más permisivo**.
  Reconciliar los **4** en **10·tools-native (R10)**, no sólo worktree. (La mecánica `list_available(mode=
  "background")` filtra por `safe_for_background`, registry.py:32-33 — verificado; lo pendiente es el *conjunto*.)

## Cruces con otros subsistemas
- **02·E3** (coordinator/swarm ⛔): A1-A5 son la misma topología ya resuelta como ⛔.
- **03·context (E, B3)**: el eje backgrounding real (is_backgrounded mutable + KIND) ya documentado allí.
- **05·execution**: `AgentMode.FORK` ⇒ `execution/fork/`; la notificación incondicional (`_notify`) y el
  registry viven en `execution`; GAP-MODE1 (discriminante de task type).
- **10·tools-native**: GAP-MODE2 — reconciliar `safe_for_background` con `ASYNC_AGENT_ALLOWED_TOOLS` +
  `BLOCKED FOR ASYNC AGENTS`. Conjunto 1:1 con **4 discrepancias concretas** (L09 2026-07-19): worktree
  (runtime más restrictivo), AgentTool/TaskStop/TaskOutput (runtime más permisivo). Ya excluidos por diseño y
  coincidentes con el canónico: `ask_user`/`plan_mode` (`safe_for_background=False` en ambos lados).
- **18·factory**: `execution_mode` (backends local/remote) — no confundir con `AgentMode`.

## Descartados del alcance (leídos para confirmarlo)
- `utils/backgroundHousekeeping.ts` — mantenimiento periódico de sesión (cleanup de versiones/mensajes,
  auto-update de plugins, `extractMemories`, `autoDream`). No es "modo": es housekeeping. `extractMemories`
  ⇒ **13·memory**; el resto ⛔ (instalador/plugins/analytics de terminal).
- `hooks/useBackgroundTaskNavigation.ts` — navegación Shift+↑/↓ líder/teammates, `f`/`k`/Enter, kill de
  teammate. Puro ink/teclado + swarm ⇒ **⛔** (= 02·E3).
- `hooks/toolPermission/handlers/coordinatorHandler.ts` — flujo de permisos del worker coordinator
  (hooks→classifier→diálogo). Depende de A1 (⛔) y su mecánica de permisos pertenece a **06·hooks**.

## Re-auditoría (2026-07-12)
Contrapartes reabiertas ÍNTEGRAS: `coordinatorMode.ts`(369), `useSessionBackgrounding.ts`(158),
`coordinatorHandler.ts`(65), `useBackgroundTaskNavigation.ts`(251), `backgroundHousekeeping.ts`(94). Resultado:
tablas A/B/C/D **verificadas exactas** contra el código (B1-B8 espejan `useSessionBackgrounding` línea a línea;
D1-D7 espejan `modes/manager.py`+`protocols.py`; FIND-MODE1 confirmado — solo los tests tocan `ModeManager`).
Matices menores añadidos (no cambian estados): env `CLAUDE_CODE_SIMPLE` reduce el toolset del worker a Bash/Read/Edit
(A3/A4); el formato `<task-notification>` XML se DEFINE canónicamente en `getCoordinatorSystemPrompt` (146-160) →
contraparte del canal de notificación de 05/07 (dentro de ⛔ swarm aquí). Defecto corregido: el fichero tenía basura
`</content></invoke>` al final (fuga de escritura de la sesión original). Sin cambios de estado; doc fiable.

**Cross-finding para 08·signals (lo cazó la re-lectura íntegra de un descartado)**: `useBackgroundTaskNavigation.ts:156-158`
revela que un task tiene DOS abort controllers — `currentWorkAbortController` (para el turno actual; el agente sigue
vivo → habilita SendMessage-continue) vs `abortController` (mata el agente). Granularidad de abort de dos niveles
(turno vs task) que el runtime (`ctx.stop`/`SignalType.ABORT` de un solo nivel) no modela → registrado como **FIND-SIG13**
en 08. Aunque el fichero es ⛔ (teammates), la distinción aplica a subagentes normales y liga con 05·GAP-EXEC3 (resume)
y con `TaskStopTool`/`emitTaskTerminatedSdk('stopped')`.

---

## Plan de homologación / remediación desarrollada

Diseño por finding. La mayor parte de 04 se resuelve por referencia (los ejes reales viven en 03/05/10);
lo propio de 04 es GAP-MODE1.

### MR1 · FIND-MODE1 — subsistema `modes/` huérfano → Deuda B (`B-orphans`)
- **Comportamiento/decisión**: `AgentMode{FG,BG,FORK}` + `ModeManager` colapsan en un enum tres ejes
  ortogonales (sesión coordinator/normal · backgrounding por-task · fork) y **ninguna ruta los consulta**
  (el loop deriva el modo de `ctx.is_subagent`, `agent_loop.py:91`; la notificación es incondicional en
  `LocalAgentRuntime._notify`). **Remediación = eliminar `modes/`** (hermano de `observer/` y `SignalBus`).
  El eje real ya es `is_subagent` (toolset por kind) + `TaskRecord.is_backgrounded` (observador) +
  `notification`. Desarrollado en **`DEUDA-B-transversal.md` §B-orphans** (decisión de borrado + guard
  anti-regresión). Aquí sólo se ancla la decisión.
- **Test**: `test_no_orphan_modemanager_in_real_path` (ninguna ruta de producción instancia `ModeManager`).

### MR2 · GAP-MODE1 — `TaskRecord` sin `type` (dispatch polimórfico de kill/lifecycle)
- **Comportamiento**: el registry no discrimina el KIND de task (`local_agent`/`local_bash`/`teammate`);
  el canónico usa `TaskType` (×7) para dispatch polimórfico (p.ej. `kill` distinto por tipo). Hoy
  `TaskRecord` (registry.py:17) no lo modela.
- **Seam/firma**: `TaskRecord` gana `kind: TaskKind = "local_agent"` (`TaskKind = Literal["local_agent",
  "local_bash","teammate"]`); `register(..., kind=...)`. `kill`/lifecycle consultan `kind`. La dimensión
  `teammate` queda ⛔ (swarm), pero el enum se porta para `local_agent`/`local_bash`.
- **Cableado**: `InMemoryTaskRegistry.register` acepta `kind`; `AgentTool`/`BashTool`-background lo setean.
  Liga 05·GAP-EXEC2. **Orden**: junto a 05. **Test**: `test_task_record_has_kind`.

### MR3 · GAP-MODE2 / C2 — conjunto async 1:1 (4 discrepancias) → YA en 10·R10
- La reconciliación del conjunto permitido a un async-agent se desarrolla en **10·R10** (flip
  `safe_for_background` + modelo de dos allowlists). La re-visita L09 (2026-07-19) concretó **4 ítems** a
  reconciliar (no sólo worktree): **worktree** (runtime más restrictivo que el canónico) + **AgentTool /
  TaskStop / TaskOutput** (runtime más permisivo — el canónico los bloquea para async). No re-desarrollo el
  plan aquí; 10·R10 es el dueño. Nota L10: AgentTool es probable **🔀 por arquitectura** (subagentes
  anidables con tope de profundidad vs exclusión total del canónico), no un ❌ liso — decisión de 10.

---

## Re-visita de COMPLETITUD (L09) · 2026-07-19 — MODO VALIDACIÓN

**Modo**: 04 nunca se validó en la 2ª vuelta; esta es su **1ª pasada de 2ª vuelta**, hecha con
**learned_lessons/09 de ENTRADA** — cada fila ✅/🔀 se re-verificó **abriendo el código de B** que
reproduce el comportamiento y siguiendo el dato punta a punta, NO confirmando la tabla ni la re-auditoría
2026-07-12 (que fue verificación *estructural* — espejó `modes/manager.py`/`useSessionBackgrounding.ts`
línea a línea, pero NO abrió los CONSUMIDORES reales del backgrounding). **Resultado**: **1 discrepancia
real** (GAP-MODE2 sub-enumerada: 4 ítems, no 1) + 1 precisión de línea (`_notify` 295→294); **código
intacto**; tests **no re-ejecutados** (sin cambio de código).

### Mini-ledger de consumidores abiertos (L09 — seguir el dato, no el inventario)
| Fila(s) | Comportamiento canónico | Consumidor real de B abierto | Verificado |
|---|---|---|---|
| FIND-MODE1 / D3-D7 | notificar-si-BACKGROUND vía manager | `modes/*` (grep import) + `execution/local/runtime.py:294-304` | ✅ huérfano: `modes/` importado **sólo por 2 tests**; `_notify` incondicional (guard `parent_session_id is None`:297), cero consulta a `on_complete`/`AgentMode`/`is_backgrounded` |
| B1 / C3 | `isBackgrounded` mutable ⟂ toolset | `registry.py:26,107-110` (write) · `resolver.py:42-49` (read-side) | ✅ `is_backgrounded` se **escribe** vía `set_backgrounded` y **nunca se lee en producción**; el resolver filtra por `ctx.is_subagent` (KIND), no por el flag |
| B4 / B6 / B7 | flip / kill / complete+notify | `registry.py:107-110 / 117-124 / 133-150` + `notification.py` (put/drain/process) | ✅ flip sólo estado; `kill`→KILLED sin tocar flag; `complete`+`_notify`→`<task-notification>` |
| C1 | filtro del toolset background | `tools/registry.py:25-33` (`list_available(mode="background")`) + `safe_for_background` por-tool | ✅ mecanismo invertido (flag por-tool vs allowlist central) confirmado |
| GAP-MODE1 (B8 🟡) | discriminante `type` de task | `registry.py:18-35` (`TaskRecord`) | ✅ sin campo `kind`/`type` — gap real (→05·GAP-EXEC2) |
| A1-A5 (⛔) | coordinator/swarm | `coordinatorMode.ts` (369, íntegro) | ✅ topología líder/worker; ⛔ por arquitectura (L10, =02·E3) — el runtime no modela teammates-pares (grep=0) |
| Descartados | housekeeping / nav teclado | `backgroundHousekeeping.ts` (94) · `useBackgroundTaskNavigation.ts` (251), íntegros | ✅ ⛔ confirmado tras ABRIR (L02); reconfirma FIND-SIG13 (2 abort controllers, 157-158)→08 |

### Ledger de lectura (columna Lectura real — L03)
| Archivo | LOC | Lectura |
|---|---|---|
| A `coordinator/coordinatorMode.ts` | 369 | íntegro 1→EOF (el más grande, L08) |
| A `hooks/useSessionBackgrounding.ts` | 158 | íntegro 1→EOF |
| A `hooks/useBackgroundTaskNavigation.ts` | 251 | íntegro 1→EOF (⛔ tras abrir, L02) |
| A `utils/backgroundHousekeeping.ts` | 94 | íntegro 1→EOF (⛔ tras abrir, L02) |
| A `constants/tools.ts` | 112 | tramos 55-112 (allowlist + BLOCKED-block, exacto) |
| B `modes/{protocols,manager,__init__}.py` | 64 | íntegros 1→EOF |
| B `execution/tasks/registry.py` | 166 | íntegro 1→EOF |
| B `execution/local/notification.py` | 72 | íntegro 1→EOF |
| B `capabilities/resolver.py` | 82 | íntegro 1→EOF |
| B `execution/local/runtime.py` | 435 | tramos `_notify` 288-327 (`_notify` + entrada de `_run_loop`); resto ya íntegro en 01·re-visita |
| B `tools/registry.py` | — | tramos 20-45 (`list_available`/`all_tools`) |
| B `tools/native/{agent,task_tools,worktree,ask_user,plan_mode}.py` | — | grep+tramos dirigidos a `safe_for_background` + depth-cap (agent.py:50-89) |
| B `loop/agent_loop.py:91-92` | — | ancla verificada exacta (`mode = "background" if ctx.is_subagent`) |

### §Nota de honestidad
- La **re-auditoría 2026-07-12** del doc fue **estructural** (tablas espejadas línea a línea contra el
  código), pero **NO** aplicó L09: no abrió los CONSUMIDORES del backgrounding (`registry`/`notification`/
  `resolver`) ni auditó el conjunto async 1:1. Esta re-visita L09 sí lo hizo. Las filas ✅/🔀 **se sostienen
  sobre la base correcta** (comportamiento-verificado-en-B), no sólo por espejo de tabla.
- **Sobre-declaración por defecto corregida**: GAP-MODE2 nombraba **1** discrepancia (worktree); la
  auditoría 1:1 del conjunto destapó **4** (worktree + AgentTool + TaskStop + TaskOutput). El cabo estaba
  *sub-especificado*, no falso — sigue homed en 10·R10, pero ahora enumera los 4 ítems con su dirección
  (runtime más/menos restrictivo) y su nota L10. No es deuda nueva de 04: es la reconciliación ya-ruteada,
  hecha honesta y completa.
- Precisión de línea: `_notify` está en runtime.py:**294** (no 295); corregido en §Naturaleza y D4.
- **Sin costuras latentes NUEVAS** tipo `to_llm`/`timeout_seconds`: el subsistema `modes/` **entero** ES la
  costura huérfana (FIND-MODE1, ya registrada); `on_transition`/`_listeners` (manager.py:42) es primitiva de
  extensión sin consumidores (D6 ❌, ya registrada). No apareció ninguna otra.

### Las 4 preguntas de cierre
1. **¿Se revisó todo cada archivo canónico (A)?** — **Sí.** Los 4 archivos A del alcance leídos 1→EOF
   (`coordinatorMode.ts` 369 · `useSessionBackgrounding.ts` 158 · `useBackgroundTaskNavigation.ts` 251 ·
   `backgroundHousekeeping.ts` 94) + `constants/tools.ts:55-112` para el conjunto async.
2. **¿Se revisó todo cada archivo runtime (B)?** — **Sí.** `modes/*` (64) íntegro + los CONSUMIDORES reales
   (`registry.py` 166 · `notification.py` 72 · `resolver.py` 82 íntegros; `runtime.py` `_notify`; `tools/
   registry.py` `list_available`; `safe_for_background` de cada tool nativo) — que es lo que la re-auditoría
   estructural previa NO había abierto.
3. **¿Los hallazgos fueron exhaustivos (no superficiales)?** — **Sí, y esta pasada mejoró la previa**:
   la auditoría 1:1 del conjunto async destapó 3 discrepancias que el doc no nombraba (AgentTool/TaskStop/
   TaskOutput), además de la de worktree.
4. **¿Quedó todo cubierto (nada pendiente)?** — **Sí.** FIND-MODE1 y GAP-MODE1 verificados por cableado;
   GAP-MODE2 (4 ítems) es un cabo con **destino concreto nombrado** (10·R10 — subsistema numerado, no
   "ningún sitio", L07). No queda **trabajo de verificación de 04** sin hacer (todas las ✅/🔀 re-verificadas
   en B con L09).
