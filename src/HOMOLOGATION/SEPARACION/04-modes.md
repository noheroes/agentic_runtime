# 04 · modes — SEPARACION (Filosofía B)

> Ruta base `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/04-modes.md`.
> Tracker de origen: `../04-modes.md` (288 LOC, leído ÍNTEGRO 1→EOF este ciclo). Esquema: `00-LEGEND.md §3`.
> PASO 0 (lecciones skill) ejecutado. Ensamblador re-abierto EN ESTE CICLO (L09/L11, NO heredado del gate de 2ª vuelta).

---

## 0. Tesis de separación (Filosofía B)

**"Modo" no es un concepto único** — el tracker lo abre en el hallazgo central: son **ejes ortogonales** que el
canónico mantiene separados y que el runtime `modes/` **colapsó indebidamente en un solo enum huérfano**. La
separación B parte de esa disección:

1. **Modo de sesión coordinator↔normal** (`coordinatorMode.ts`, gate `feature('COORDINATOR_MODE')`+env,
   experimental incluso en el canónico) = **topología líder/worker del swarm**. El runtime modela **subagentes
   anidables, NO teammates-pares** (grep=0). ⛔ N/A-core, ya resuelto en **02·E3**. Si algún integrador quiere swarm
   ⇒ subsistema T3 nuevo, no gap del base. → `00-INTEGRADORES.md` (capa hipotética, fuera de agentic_code/assistant hoy).
2. **Backgrounding por-task** (`isBackgrounded` mutable relativo al observador). El **comportamiento observable**
   (task desatendido corre, ~~notifica al terminar~~ **[⚠ el aviso NO llega hoy — CORE-GAP `H-5`, ver §2.6·I2:
   el canal se llena y nadie lo drena]**, se re-background/foreground) SÍ vive en el base — pero en
   `execution/tasks/registry.py` (`TaskRecord.is_backgrounded`) + `execution/local/notification.py`, **no en `modes/`**.
   La UI (Ctrl+B, sync a la vista, foregroundedTaskId) = CLI-ONLY/INTERFAZ → integrador.
3. **Fork** (snapshot/aislamiento) = **05·execution/fork**, no este subsistema.
4. **Filtro del toolset del agente desatendido** = por **KIND** (`ctx.is_subagent`), mecanismo **invertido** frente al
   canónico (flag por-tool `safe_for_background` vs allowlist central). Base mechanism, ya cableado.

**El subsistema `modes/` del runtime (`AgentMode{FOREGROUND,BACKGROUND,FORK}` + `ModeManager` + `ModeManagerProtocol`)
colapsa esos ejes en un enum por-task y NO está cableado a NADA** — es el gemelo exacto del `SignalBus` (08·DB-SIG-1)
y de `observer/` (05·FIND-EXEC4): **abstracción especulativa huérfana → DEUDA-B (borrar), hogar `B-orphans` → A3.DB**.
Verificado este ciclo (§3.2·Q3): cero productores en producción; `_notify` incondicional; el loop deriva el modo de
`is_subagent`; la factory usa `execution_mode` (backends), otro concepto.

**04 = categoría SIN battery y SIN CORE-GAP propio** (anti-padding L10). Los dos gaps reales (GAP-MODE1 discriminante
de tipo de task · GAP-MODE2 conjunto async 1:1) **cruzan a 05·GAP-EXEC2 y 10·R10** — no se re-desarrollan aquí; su
dueño es la categoría de destino. Lo propio de 04 es **el borrado del huérfano** (FIND-MODE1) + la **disección de ejes**.

### 0.1 DESAMBIGUACIÓN load-bearing — "permission modes" (GAP-02) NO es finding de 04

La memoria de retoma marcó **GAP-02 permission modes** (`default`/`plan`/`acceptEdits`/`bypassPermissions`) como
"corazón de 04". **Corrección honesta tras abrir el tracker (L07/L11):** el tracker `../04-modes.md` **NO cubre
permission-modes** — su alcance A-side es `coordinatorMode.ts` + `useSessionBackgrounding.ts` + `modes/` (=**AgentMode**,
el eje ejecución/backgrounding). El homónimo "permission mode" del canónico vive en `hooks/toolPermission/` y ya está
**homed fuera de 04**:
- **06·CG-HOOK-8** — `PermissionContext.mode` **ausente** (verificado este ciclo: `contracts/permissions.py` sin campo
  `mode`; sólo `always_allow_command`/`model_copy`). Hogar canónico `hooks/toolPermission/`.
  ⚠ **Puntero actualizado (`P4-04-I5`, consecuencia 7 — un puntero se degrada por quedar rancio):** desde el cierre
  de A3.DA el dueño de GAP-02 es el **keystone `K1 · PermissionContext.mode`** (`DEUDA-A §1.1:185`), **primero del
  orden de construcción** (`DEUDA-A:359`), con `06·CG-HOOK-8` como su faceta de hooks. La remisión «→ A3.DA
  (consolidación)» quedó consumida: A3.DA cerró y **produjo K1**. Leer «→ **K1**, faceta 06·CG-HOOK-8».
- **03·GAP-CTX2 / B2** — hack `app_state.native["plan_mode"]` (verificado: `agent_loop.py:293,330` + `capabilities/plan/`).
- **10·D1/B2** + **01·GAP-02/CTR-08**.

⇒ 04 **cruza** GAP-02 a **A3.DA** (consolidación) y a **06·CG-HOOK-8** (dueño), **NO lo re-cuenta** como finding 04
(no existe fila A-side en `../04-modes.md`). Arrastrarlo aquí sería trocear alcance ajeno (L07) e inflar el conteo (L10).

---

## 1.0 Criterio de aceptación — §Evidencia restituida (`P4-04-9`)

> **Agujero estructural del esquema, 4º par consecutivo.** El tracker `../04-modes.md:61-70` lleva un
> `## Evidencia ejecutada` que **no dejó rastro** en este documento: el destilado conservó las 23 fichas y perdió
> **entero** el criterio con que se comprueba si están homologadas. Idéntico a `P4-05-9`, `P4-02-16` y `P4-03-12`
> ⇒ **4 de 4 pares que tenían §Evidencia la han perdido**. Restituida aquí porque es lo único que, desde el código,
> detecta que este doc se ha quedado rancio — que es exactamente el defecto §2.6.

- **Lint** (`modes/` + `test_modes_homologation.py`): `ruff` ✅ · `mypy` ✅ (3 archivos) · `bandit` ✅ (0 hallazgos).
- **Tests, con su reparto de intención** (el nombre importa: cada uno fija un eje distinto):
  - `test_mode_manager.py` — **9 passed**: unit del `ModeManager` **huérfano** (ejercita en aislamiento lo que
    ninguna ruta consulta). ⇒ **se retiran con `DB-01`**.
  - `test_modes_background.py` — **4 passed**: la ruta **REAL** (filtro por KIND + `is_backgrounded` mutable
    ortogonal al toolset). ⇒ **sobreviven al borrado**; son la cobertura de B1/C3.
  - `test_modes_homologation.py` — **2 passed + 1 xfailed**.
- **`xfail(strict)`** = **`test_mode_manager_gates_notification`** (FIND-MODE1: `ModeManager` no cableado a la ruta
  de notificación de `LocalAgentRuntime`). Es el **único mecanismo del corpus que detecta desde el código** que la
  decisión de modo no gobierna nada; si pasara «por sorpresa», el gap se habría cerrado sin actualizar el doc.
- **Guards de Fase B** (ya anclados): `test_no_orphan_modemanager_in_real_path` (§2.4) · `test_task_record_has_kind`
  (§2.3, dueño 05).
- **Suite global tras 04:** **561 passed · 3 skipped · 11 xfailed** (era 559·3·10 tras 03 ⇒ +2 passed, +1 xfailed,
  **sin regresiones**).

---

## 1. Tabla por finding (grid del tracker · A1-A5 · B1-B8 · C1-C3 · D1-D7 = **23 filas**)

> Los 3 findings-resumen del tracker (`FIND-MODE1`, `GAP-MODE1`, `GAP-MODE2`) = **capa de remediación** que reafirma
> celdas del grid (FIND-MODE1→D3-D7/D4 · GAP-MODE1→B8 · GAP-MODE2→C2); **no se re-cuentan** (patrón 06/10). `FIND-SIG13`
> (2 abort controllers, cazado por la re-lectura del descartado `useBackgroundTaskNavigation.ts`) ya está **homed en 08**.

### A · Modo de sesión coordinator↔normal (`coordinatorMode.ts`, íntegro) — swarm
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| A1 | `isCoordinatorMode()` gate feature+env | cáscara/producto | T3-INTEGRADOR | `00-INTEGRADORES` (swarm hipotético) | — | ⛔ N/A-core =02·E3; runtime no modela teammates-pares; si se adopta ⇒ subsistema T3 nuevo, no gap |
| A2 | `matchSessionMode(stored)` reconcilia modo al reanudar | cáscara/producto | T3-INTEGRADOR | `00-INTEGRADORES` (swarm) | persistencia (id opaco+repo) | ⛔ N/A-core; persistencia+reconcil del modo de sesión, depende de A1. **`P4-04-1` (mecanismo restituido):** reconciliar = **flip del env** + emitir el evento `tengu_coordinator_mode_switched`. El destilado conservaba el disparador («reconcilia») y perdía los dos efectos observables ⇒ un integrador que adopte swarm no sabría **qué hace** la reconciliación |
| A3 | `getCoordinatorUserContext(mcpClients, scratchpadDir)` inyecta tools/MCP/scratchpad de workers | cáscara/producto | T3-INTEGRADOR | `00-INTEGRADORES` (swarm) | — | ⛔ N/A-core; prompt de coordinación; env `CLAUDE_CODE_SIMPLE` reduce toolset del worker. **`P4-04-2` (firma + nexo restituidos):** la firma toma `(mcpClients, scratchpadDir)` — el prompt de workers **no se genera solo**, consume el estado MCP y el scratchpad; y **el listado de tools que anuncia = `ASYNC_AGENT_ALLOWED_TOOLS`, el mismo de C1** ⇒ A y C no son ejes independientes: el prompt del coordinador **enumera la allowlist async** |
| A4 | `getCoordinatorSystemPrompt()` system prompt del líder | cáscara/producto | T3-INTEGRADOR | `00-INTEGRADORES` (swarm) | — | ⛔ N/A-core; define el XML `<task-notification>` (146-160) = contraparte del canal de notif 05/07 |
| A5 | `INTERNAL_WORKER_TOOLS` (TeamCreate/Delete/SendMessage/SyntheticOutput ocultas) | cáscara/producto | T3-INTEGRADOR | `00-INTEGRADORES` (swarm) + 10 | — | ⛔ N/A-core =02·E3 + 10·tools-native (candidatas ⛔) |

### B · Backgrounding por-task (`useSessionBackgrounding.ts`, íntegro)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| B1 | `task.isBackgrounded` flag mutable por-task, relativo al observador | núcleo | T2-BASE-MECANISMO | `execution/tasks/registry` (`TaskRecord.is_backgrounded`) | ejecución (id opaco+repo) | ✅ espejo directo; mutable, NO re-filtra toolset; verificado §3.2·Q3. **`P4-04-3` (el hecho load-bearing restituido, tracker `:235`):** el flag **se ESCRIBE (`set_backgrounded`) y NUNCA SE LEE en producción** — 0 lectores en el base; el único lector concebible es el integrador que proyecta la vista (OI-MODE-B). Sin este dato, Fase B implementa un flag creyendo que algo del base lo consume. Cobertura: `test_modes_background.py` (4 tests) |
| B2 | `foregroundedTaskId` — qué task async se mira ahora | cáscara-CLI | CLI-ONLY/INTERFAZ | `00-INTEGRADORES` (must-be view) | — | ⛔ concepto de vista; dato existe (`list_for`+eventos), la selección la hace el integrador |
| B3 | Ctrl+B → `handleBackgroundSession()` — **dos comportamientos en un gesto** | cáscara-CLI | CLI-ONLY/INTERFAZ | `00-INTEGRADORES` (disparo) | — | ⛔ keybinding; el *acto* = `set_backgrounded(id,True)`; el disparo (tecla/API) es del integrador. **`P4-04-4` (la disyunción restituida):** el mismo gesto hace **una de dos cosas según el estado de la vista** — (a) si NO hay task foregrounded, manda a background **la query actual**; (b) si lo hay, **re-backgroundea el foregrounded**. Es un requisito de OI-MODE-A, no un detalle: un integrador que implemente sólo (a) deja al usuario sin salida de la vista foreground |
| B4 | Re-background: flip `isBackgrounded=true` + limpiar messages/abort del view | núcleo+cáscara | T2-BASE-MECANISMO + INTERFAZ | `registry.set_backgrounded` (base) · view-clear (integrador) | ejecución | 🔀 base hace sólo el flip de estado; limpiar el *view* es del consumidor (no hay view compartido). **`P4-04-5` (invariante restituido, =03·B3):** `set_backgrounded` **no toca `ctx`** (`registry.py:107-110` escribe **sólo** `rec.is_backgrounded`) — el re-background NO invalida el contexto del task en curso |
| B5 | Foreground: sync messages/loading/abort del task al REPL único | cáscara-CLI | CLI-ONLY/INTERFAZ | `00-INTEGRADORES` (must-be view) | — | ⛔ multiplexado React/ink; base emite eventos por task, el consumidor los proyecta (=02·D4) |
| B6 | Task abortado mientras foregrounded → clear+re-background | núcleo+cáscara | T2-BASE-MECANISMO + INTERFAZ | `registry.kill` (base) · transición-vista (integrador) | ejecución | 🔀 base marca KILLED; la transición de vista es del consumidor. **`P4-04-6` (invariante restituido):** `kill` deja **`is_backgrounded` INTACTO** (`registry.py:117-124`: cancela el `asyncio_task` y pone `status=KILLED`, **no** toca el flag) ⇒ matar y observar son ortogonales, y el canónico *re-backgroundea* precisamente porque el flag sobrevive al kill |
| B7 | Task completado mientras foregrounded → restaurar a background + notif | núcleo+cáscara | T2-BASE-MECANISMO + INTERFAZ | `registry.complete`+`notification` (base) · re-proyección (integrador) | ejecución | 🔀 completar **encola** `<task-notification>`; "restaurar a background" = re-proyección del consumidor. ⚠ **VEREDICTO INVERTIDO AGUAS ABAJO — §2.6·I2:** el `put` existe (`runtime.py:294-304`, gateado por `parent_session_id`:408) pero **NADIE DRENA** ⇒ el aviso no llega. CORE-GAP `H-5`/`AC-07` |
| B8 | `foregroundedTask.type !== 'local_agent'` → limpiar foreground | núcleo | **CORE-GAP** | **05·GAP-EXEC2** (`TaskRecord.kind`) | ejecución | 🟡 **GAP-MODE1**: registry sin discriminante `kind`; si se porta bash-background como task ⇒ necesita `type`; cruza 10·bash+05 |

### C · Filtro del toolset del agente desatendido (allowlist vs flag por-tool)
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| C1 | `ASYNC_AGENT_ALLOWED_TOOLS` (allowlist central) vs `safe_for_background` por-tool | núcleo | T1-CONTRATO + T2-BASE | `ToolProtocol.safe_for_background` (09/10) · `registry.list_available(mode=)` (09) | — | 🔀 misma intención, mecanismo **invertido**; la aptitud viaja con la tool; verificar conjunto→C2. **`P4-04-7` (enumeración restituida, `constants/tools.ts:55-102`):** el Set canónico es **nominal y cerrado** — `Read` · `Grep` · `Glob` · `Web*` · `Todo` · `Shell` · `Edit` · `Write` · `Notebook` · `Skill` · `Synthetic` · `ToolSearch` · `Worktree`. Sin la lista, C2 (reconciliación 1:1) no tiene contra qué reconciliar. ⚠ **VEREDICTO INVERTIDO — §2.6·I3:** «la aptitud viaja con la tool» se registró como *ventaja* del runtime; `10·E3` (`FIND-NATIVE-BG`) la recalificó a **CORE-GAP-restrictividad** y decidió **sustituir el bool por DOS `frozenset[str]` nombradas** ⇒ el mecanismo invertido **se revierte al del canónico** |
| C2 | Conjunto concreto permitido a un async-agent (1:1) | núcleo | ~~CORE-GAP~~ **CERRADO en 10** | **10·E2/E4** (era `10·R10`) | — | 🟡 **GAP-MODE2**: 4 discrepancias. **`P4-04-8` (las 8 anclas + los motivos canónicos restituidos):** ① **worktree** — canónico lo **PERMITE** (`tools.ts:69-70`), runtime `False` (`worktree.py:61,129`) ⇒ *más restrictivo*; ② **AgentTool** — canónico **BLOQUEA** *«prevent recursion»* (`tools.ts:92`), runtime `True` (`agent.py:60`) con tope `_MAX_SUBAGENT_DEPTH=5` (`agent.py:73`) ⇒ *más permisivo, acota por profundidad no por exclusión*; ③ **TaskStop** — canónico **BLOQUEA** *«requires main-thread task state»* (`tools.ts:95`), runtime `True` (`task_tools.py:178`); ④ **TaskOutput** — canónico **BLOQUEA** *«prevent recursion»* (`tools.ts:93`), runtime `True` (`task_tools.py:210`). Mecánica del filtro: `registry.py:32-33`. Coincidentes por diseño en ambos lados: `ask_user`/`plan_mode` (`False`). ⚠ **ESTADO INVERTIDO — §2.6·I4:** `10·E2` lo declara **`GAP-TOOL2`=`GAP-MODE2` RESUELTO** y `10·E4` da el cabo **cubierto** ⇒ esta fila ya no es un pendiente de 04 |
| C3 | Gate por KIND (subagente=unattended) ⟂ `isBackgrounded` | núcleo | T2-BASE-MECANISMO | `capabilities/resolver` | — | ✅ ejes ortogonales; resolver filtra por `ctx.is_subagent`, el flag mutable NO re-filtra; verificado §3.2·Q3 (resolver.py:39-49) |

### D · `modes/` del runtime — `AgentMode`+`ModeManager` (la abstracción huérfana) → DEUDA-B borrar
| ID | resumen | núcleo\|cáscara | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| D1 | `AgentMode.FOREGROUND/BACKGROUND` | núcleo | ~~DEUDA-B~~ **T1-VOCABULARIO** | ~~borrar~~ **CONSERVAR + reubicar** (`RV-6`/`DB-01`) | — | ⚠ **VEREDICTO INVERTIDO — §2.6·I1.** Decía «borrar»; `DEUDA-B §3.A·DB-01` lo corrigió: `AgentMode` es **vocabulario T1 vivo**, es un `str, Enum` cuyos valores son **literalmente** `"foreground"`/`"background"` (`protocols.py:5-8`, abierto 1→EOF) = **exactamente** los strings crudos con que `agent_loop.py:91` llama a `list_available(mode=…)`. Borrarlo **fija los strings crudos para siempre** y contradice a `DB-25` (`stop_reason`). ⇒ **CONSERVAR, reubicar al módulo de vocabulario T1 junto a `stop_reason`, y cablear `agent_loop.py:91` a él.** La duplicación con `is_backgrounded` (B1) **no** es real: son ejes distintos (KIND del turno vs flag del observador) |
| D2 | `AgentMode.FORK` | núcleo | **ABIERTO** (miembro, no archivo) | **`AC-09`** (auditoría símbolo-a-símbolo, P3) | — | 🔀 mezcla eje de aislamiento con notif; el fork real vive en `execution/fork/` (`ForkPolicy`, `fork/__init__.py:21` — verificado). ⚠ **`P4-04-N` — `RV-6` resolvió el ARCHIVO, no el MIEMBRO.** `RV-6` conserva `AgentMode` **entero** («`FOREGROUND/BACKGROUND/FORK`») sin pronunciarse sobre `FORK`; pero el único consumidor del enum es `list_available(mode=…)`, que **sólo compara contra `"background"`** (`tools/registry.py`, abierto) ⇒ si `AgentMode` pasa a ser el vocabulario T1 del gating de toolset, **`FORK` queda como miembro que nadie puede pasar**. El argumento de D2 (mezcla de ejes ortogonales) **sigue en pie dentro del enum conservado**. Decide `AC-09`, que es exactamente la auditoría símbolo-a-símbolo — **no lo cierra `RV-6`** |
| D3 | `ModeManager.register/get_mode/set_mode/unregister` | núcleo | DEUDA-B | **borrar** | — | ❌ huérfano; grep: sólo 2 tests; ni loop/runtime/resolver/factory lo instancian (§3.2·Q3) |
| D4 | `ModeManager.on_complete(id)`→notificar-si-BACKGROUND | núcleo | DEUDA-B | **borrar** | — | ❌ **FIND-MODE1**: `_notify` (runtime.py:294-304) es **incondicional**, cero consulta a `on_complete`; verificado §3.2·Q3 |
| D5 | `set_mode` bloquea transición si FORK (inmutable) | núcleo | DEUDA-B | **borrar** (con enum) | — | 🔀 invariante razonable pero protege un enum que nadie usa; sobra si FORK sale |
| D6 | `on_transition(callback)` — listeners de cambio de modo | núcleo | DEUDA-B | **borrar** | — | ❌ primitiva de extensión sin consumidores (manager.py:42); especulativa |
| D7 | `ModeManagerProtocol` (Protocol) | núcleo | DEUDA-B | **borrar** | — | ❌ contrato de un subsistema no cableado |

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica (nombre · productor invoca · consumidor implementa)
**04 no introduce ninguna costura NUEVA** — los ejes reales viven en costuras ya homed en 05/09/10 (L07: no se
re-hospedan aquí, se referencian):
- `TaskRegistryProtocol` (T2-COSTURA, home **05**) — `is_backgrounded`/`set_backgrounded`/`kill`/`complete`/`list_for`.
  Productor: `LocalAgentRuntime` + tool `agent`/bash-bg. Consumidor: `InMemoryTaskRegistry` (default base) o el del integrador.
  Verificado cableado este ciclo: registry.py:107-110 (write flag), 117-124 (kill), 133-150 (complete).
- `ToolProtocol.safe_for_background` (T1-CONTRATO, home **09/10**) — flag por-tool que reemplaza el allowlist central (C1).
- `list_available(mode="background")` (T2-BASE, home **09**) — tools/registry.py:25-34 filtra por el flag. Verificado.
- Canal `BackgroundNotification` (home **05/07**) — ⚠ **CORREGIDO (`§2.6·I2`, consecuencia 16):** la costura es
  **`put` SÍ / `drain` INEXISTENTE**, no «put/drain/process». `put_notification` tiene productor real
  (`runtime.py:299`); `drain_notifications`/`process_background_notification` (`notification.py:45,49`) tienen
  **0 callers de producción** — verificado con el árbol abierto: las únicas ocurrencias fuera de su definición son
  **re-exports** en `__init__.py:12,37-38` y `execution/__init__.py:3,15,17`, que son *exportaciones, no invocaciones*.
  `SEAMS §S21` lo tabula como `existe-put-sin-drain` y `SEAMS:517` retira al integrador como drenador. El
  `<task-notification>` XML se define canónicamente en `getCoordinatorSystemPrompt` (A4). ⇒ **CORE-GAP `H-5` → `AC-07`**.

### 2.2 Batteries que alimenta
**NINGUNA.** Como 08·signals: el backgrounding y la derivación de modo son **primitivas/mecanismo del base**, no
paquete opcional; el coordinator/swarm es **producto de un integrador hipotético**, no battery. Inventar una battery
aquí sería padding (L10). El contraste con 10 (battery-intensa) / 06 (battery+seam) es deliberado.

### 2.3 CORE-GAPs (brechas A↔B reales → rollup `DEUDA-A.md`)
**04 NO tiene CORE-GAP propio.** Los dos gaps reales cruzan a su categoría-dueña (se anclan aquí, se desarrollan allá):
- **GAP-MODE1** (B8) — `TaskRecord` sin discriminante `kind`/`type` (`local_agent`/`local_bash`/`teammate`); el canónico
  usa `TaskType`(×7) para dispatch polimórfico de kill/lifecycle. **Dueño: 05·GAP-EXEC2.** Seam/firma (referencia, no
  re-desarrollo): `TaskRecord` gana `kind: TaskKind = "local_agent"`; `register(...,kind=)`; `kill`/lifecycle consultan
  `kind`. Dimensión `teammate` queda ⛔ (swarm). Test: `test_task_record_has_kind`.
- **GAP-MODE2** (C2) — conjunto async-agent 1:1, **4 discrepancias** concretas con sus 8 anclas (ver C1/C2 tras
  `P4-04-7`/`P4-04-8`). ~~Dueño: 10·R10~~ ⚠ **CERRADO AGUAS ABAJO (§2.6·I4):** `10·E2` lo declara
  **`GAP-TOOL2`=`GAP-MODE2` RESUELTO** y `10·E4` da el cabo **cubierto** tras la reconciliación celda a celda.
  Lo que **sigue abierto** no es el conjunto sino el **modelo**: `10·E3`/`FIND-NATIVE-BG` sustituye el bool
  `safe_for_background` por **dos `frozenset[str]` nombradas** (`ASYNC_AGENT_ALLOWED_TOOLS` /
  `IN_PROCESS_TEAMMATE_ALLOWED_TOOLS`) — lo que **invierte C1** (§2.6·I3). Nota L10 (sostenida): AgentTool
  probable 🔀 por arquitectura (subagentes anidables con tope `_MAX_SUBAGENT_DEPTH=5` vs exclusión total); decide 10.
- **GAP-02 permission modes** — **NO es 04** (§0.1). Cruza al keystone **`K1 · PermissionContext.mode`**
  (`DEUDA-A §1.1:185`, **primero del orden de construcción** `:359`), faceta **06·CG-HOOK-8**. ~~+ A3.DA~~ — A3.DA
  cerró y **produjo K1**; la remisión a «consolidación» quedó consumida (§0.1, `P4-04-I5`).

### 2.4 DEUDA-B (higiene interna del runtime — L10, NO A↔B)
> ⚠ **ALCANCE CORREGIDO POR `RV-6` (§2.6·I1) — leer ANTES del párrafo siguiente.** La orden «borrar `modes/`
> entero» que este §2.4 emitió es **la orden que originó la regla `RV-6`**: *una decisión de BORRAR se escribe a
> nivel de **SÍMBOLO**, nunca de módulo, y siempre con la lista explícita de lo que **SOBREVIVE***. Aplicada
> literal en Fase B, habría destruido `AgentMode`, vocabulario T1 vivo. **Reparto correcto:**
> **BORRAR** → `ModeManager` (`manager.py` 44 L completo) · `ModeManagerProtocol` (`protocols.py:11-16`) ·
> `on_transition`/`_listeners` (`manager.py:42-44`) · el export del paquete.
> **SOBREVIVE** → **`AgentMode`** (`protocols.py:5-8`), reubicado al módulo de vocabulario T1 junto al
> `stop_reason` de `DB-25`, con `agent_loop.py:91` cableado a él. Miembro `FORK` = **abierto**, decide `AC-09`.
> 04 es el **precedente citado por `A-CIERRE-LEDGER·AC-09`** para auditar las 37 entradas BORRAR restantes.

- **FIND-MODE1 / D3-D7 — borrar la maquinaria de `modes/`** (`ModeManager` + `ModeManagerProtocol` +
  `on_transition`/`_listeners`; **NO** `AgentMode`). Huérfano confirmado este ciclo (§3.2·Q3): 0 productores en producción, importado sólo
  por `test_mode_manager.py` (9 tests) + `test_modes_homologation.py` (xfail FIND-MODE1). Gemelo de `SignalBus`
  (08·DB-SIG-1) y `observer/` (05·FIND-EXEC4) ⇒ **mismo criterio, mismo hogar: `B-orphans` en
  `../DEUDA-B-transversal.md` → clasificación en A3.DB.** El eje real ya es `is_subagent` (toolset por KIND) +
  `TaskRecord.is_backgrounded` (observador) + `notification`. Guard anti-regresión:
  `test_no_orphan_modemanager_in_real_path` (ninguna ruta de producción instancia `ModeManager`).

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05/§1.1)
**Must-be universal (CONTRATO BASE COMÚN — obligación de TODO integrador con vista):**
- **OI-MODE-A · Disparo del backgrounding.** Capacidad observable: un acto de UI/API **promueve** un task a background.
  Costura que rellena: `registry.set_backgrounded(id, True)` (base lo expone). Firma en integrador: gesto→llamada.
  Realización: agentic_code = Ctrl+B en el REPL; agentic_assistant = endpoint BFF/evento front. Criterio: tras el acto,
  `TaskRecord.is_backgrounded==True` y el task sigue corriendo desatendido. (B3.)
- **OI-MODE-B · Multiplexado/proyección de la vista** ("cuál de mis tasks background observo ahora" = `foregroundedTaskId`).
  Capacidad: el integrador elige UN task a proyectar entre los `registry.list_for(session)` y sincroniza sus
  messages/loading/abort. Costura: `list_for` + stream de eventos por task (base los emite; no hay view compartido en el
  base — B4/B6/B7 view-side son del consumidor). Realización: terminal = sync al REPL único (React/ink); front =
  proyección selectiva en el BFF. Criterio: el integrador puede foreground-uno sin que el base conozca "la vista". (B2/B5/B4/B6/B7.)

**Específico (capa secundaria — NO agentic_code/agentic_assistant hoy):**
- **A1-A5 · Topología swarm coordinator/worker** (T3-INTEGRADOR). Capacidad: modo-sesión líder + workers-pares +
  tools internas del swarm (`TeamCreate`/`SendMessage`/`SyntheticOutput`) + persistencia/reconciliación del modo +
  system/user-prompt de coordinación. Costura: subsistema T3 nuevo (no existe en el base ni se planea). Realización:
  ⛔ N/A hoy — experimental incluso en el canónico (gate `feature('COORDINATOR_MODE')`); =02·E3. Se documenta por
  **completitud de capacidad**: si un futuro integrador adopta swarm, esto es su blueprint de arranque, no un gap del base.

### 2.6 Veredictos invertidos aguas abajo (`A-CIERRE-P4 §11` · patrón 4 severo)

**Ninguna de estas 5 se caza comparando las dos caras del par: tracker y destilado COINCIDEN.** Las fichas eran
**fieles a su origen** y son **falsas hoy** porque un rollup posterior invirtió el veredicto sin volver a tocar
este documento. Se cazan **sólo** cruzando cada ficha contra `DEUDA-A`/`DEUDA-B`/`BATTERIES`/`SEAMS`/`P0`/`P1`.

| # | ficha | decía | dice hoy la evidencia |
|---|---|---|---|
| **I1** | `D1`/`D2`/`§2.4` | «**borrar `modes/` entero**», `AgentMode` incluido | **FALSO.** `DEUDA-B §3.A·DB-01` + **`RV-6`**: `AgentMode` (`protocols.py:5-8`) es **vocabulario T1 vivo** — `str, Enum` con valores `"foreground"`/`"background"`, *los mismos strings crudos* que `agent_loop.py:91` pasa a `list_available(mode=…)`. Borrarlo **fija los strings para siempre** y contradice `DB-25`. ⇒ **BORRAR `ModeManager`+`ModeManagerProtocol`+`on_transition`; CONSERVAR `AgentMode`.** Esta ficha es **el precedente que originó la regla `RV-6`** y el que `A-CIERRE-LEDGER·AC-09` (P3) cita para auditar las **37** entradas BORRAR restantes — y aun así **04 nunca se actualizó** |
| **I2** | `B7`/`§0·2`/`§2.1` | 🔀 «completar **notifica** al padre»; costura `put/drain/process` | **CORE-GAP `H-5`/`AC-07`.** El `put` existe (`runtime.py:294-304`, gate `:408`); `drain_notifications`/`process_background_notification` (`notification.py:45,49`) tienen **0 callers de producción** — sus únicas ocurrencias fuera de la definición son **re-exports** (`__init__.py:12,37-38`, `execution/__init__.py:3,15,17`), que **no son invocaciones**. `SEAMS §S21` = `existe-put-sin-drain`; `SEAMS:517` **retira al integrador** como drenador. Concuerda con `05·§2.6·R1`, `02·§9.3·I1` y `03·§2.6·I1` |
| **I3** | `C1`/`§2.1` | 🔀 mecanismo invertido = **ventaja** del runtime («la aptitud viaja con la tool») | **CORE-GAP-restrictividad.** `10·E3` (`FIND-NATIVE-BG`) recalifica y decide **sustituir el bool `safe_for_background` por DOS `frozenset[str]` nombradas** (`ASYNC_AGENT_ALLOWED_TOOLS`/`IN_PROCESS_TEAMMATE_ALLOWED_TOOLS`) ⇒ el modelo **se revierte al del canónico**. La costura T1 que §2.1 declara (`ToolProtocol.safe_for_background`) **desaparece** en Fase B |
| **I4** | `C2`/`§2.3` | 🟡 pendiente, «dueño **10·R10**» | **RESUELTO.** `10·E2` rotula `GAP-TOOL2`=`GAP-MODE2` **RESUELTO**; `10·E4` da el cabo *«04·GAP-MODE2 (worktree+Agent+TaskStop+TaskOutput) **cubierto**»* tras la reconciliación celda a celda. 04 arrastraba como abierto un cabo cerrado |
| **I5** | `§0.1`/`§2.3` | GAP-02 → «**06·CG-HOOK-8** (dueño) + **A3.DA** (consolidación)» | **Puntero rancio** (consecuencia 7). A3.DA **cerró y produjo** el keystone **`K1 · PermissionContext.mode`** (`DEUDA-A §1.1:185`), **primero del orden de construcción** (`:359`); `06·CG-HOOK-8` pasa a ser su **faceta**, no el dueño. Remitir a «A3.DA» hoy remite a una fase consumida |

**Tasa: 5/23 = 21,7 %** — más del **doble** de la tasa acumulada (`05` 11 % · `02` 8,3 % · `03` 9,4 % ⇒ ~9-10 %).
**No es ruido, y el mecanismo es legible:** 04 es la categoría **más delegadora del corpus** — no posee ninguna
battery, ningún CORE-GAP propio, y **17 de sus 23 fichas apuntan a un dueño ajeno** (05·GAP-EXEC2 · 10·R10 ·
06/K1 · A3.DB · 00-INTEGRADORES). Una ficha que delega **no controla su propio veredicto**: se invierte cuando su
dueño decide, y nadie vuelve a avisar al remitente. ⇒ **consecuencia 18** (`A-CIERRE-P4 §11.6`).

**Lo que NO cambia (anti-padding, L10):** `FIND-MODE1` **se sostiene** — `ModeManager` sigue siendo huérfano y su
borrado sigue decidido; lo que `RV-6` corrigió es el **alcance**, no el veredicto. `B8`/`GAP-MODE1` **se sostiene**
como CORE-GAP y su dueño `05·E32` lo ha **enriquecido** (los 7 `TaskType` + `generateTaskId` = prefijo-por-tipo,
restituidos allí por `P4-05-4`). Las 5 fichas ⛔ del swarm (A1-A5) **no se han movido**.

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor:** De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda;
ninguna categoría se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar
—o colocado sin abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — una fila por finding (23 = grid A1-A5·5 + B1-B8·8 + C1-C3·3 + D1-D7·7)
| ID | TIER | destino | cara | evidencia | detalle | nota-id |
|---|---|---|---|---|---|---|
| A1 | T3-INTEGRADOR | 00-INTEGRADORES (swarm) | integrador | tracker-leído + `coordinatorMode.ts` 369 íntegro (2ª vuelta) | sí (§2.5) | — |
| A2 | T3-INTEGRADOR | 00-INTEGRADORES (swarm) | integrador | tracker-leído | sí (§2.5) | persistencia |
| A3 | T3-INTEGRADOR | 00-INTEGRADORES (swarm) | integrador | tracker-leído | sí (§2.5) | — |
| A4 | T3-INTEGRADOR | 00-INTEGRADORES (swarm) | integrador | tracker-leído | sí (§2.5) | — |
| A5 | T3-INTEGRADOR | 00-INTEGRADORES + 10 | integrador | tracker-leído | sí (§2.5) | — |
| B1 | T2-BASE-MECANISMO | execution/tasks/registry | base | `registry.py:24-26,107-110` abierto | sí (6c ref 05) | ejecución |
| B2 | CLI-ONLY/INTERFAZ | 00-INTEGRADORES (view) | integrador | tracker-leído; dato=`list_for` (registry.py:99-105) abierto | sí (§2.5 OI-B) | — |
| B3 | CLI-ONLY/INTERFAZ | 00-INTEGRADORES (disparo) | integrador | `registry.py:107-110` (`set_backgrounded`) abierto | sí (§2.5 OI-A) | — |
| B4 | T2-BASE + INTERFAZ | registry (base) · view (integ) | ambas | `registry.py:107-110` abierto | sí (§2.5) | ejecución |
| B5 | CLI-ONLY/INTERFAZ | 00-INTEGRADORES (view) | integrador | tracker-leído | sí (§2.5 OI-B) | — |
| B6 | T2-BASE + INTERFAZ | registry.kill · view | ambas | `registry.py:117-124` abierto | sí (§2.5) | ejecución |
| B7 | T2-BASE + INTERFAZ | registry.complete+notif · view | ambas | `registry.py:133-150` + `notification.py:36-68` abierto | sí (§2.5) | ejecución |
| B8 | CORE-GAP | 05·GAP-EXEC2 | base | `registry.py:16-35` (`TaskRecord` sin `kind`) 1→EOF + `runtime.py:141-143` (`register` sin kind) 1→EOF | sí (§2.3, dueño 05) | ejecución |
| C1 | T1-CONTRATO+T2-BASE | ToolProtocol.safe_for_background · list_available | base | `tools/registry.py:25-34` 1→EOF | sí (§2.1) | — |
| C2 | CORE-GAP | 10·R10 | base | tracker-leído (4 ítems, 2ª vuelta L09) | sí (§2.3, dueño 10) | — |
| C3 | T2-BASE-MECANISMO | capabilities/resolver | base | `resolver.py:39-49` 1→EOF (filtra por `is_subagent`) + `agent_loop.py:91` 1→EOF | sí (§2.1) | — |
| D1 | DEUDA-B | borrar (B-orphans) | base | `protocols.py:5-8` + `registry.py:24-26` 1→EOF | N/A (DEUDA-B) | — |
| D2 | DEUDA-B | borrar (fork→05) | base | `protocols.py:5-8` 1→EOF | N/A (DEUDA-B) | — |
| D3 | DEUDA-B | borrar | base | `manager.py:16-32` 1→EOF + ensamblador `factory.py`/`runtime.py`/`agent_loop.py` 1→EOF (cero ref) + grep prod=0 | N/A (DEUDA-B) | — |
| D4 | DEUDA-B | borrar (FIND-MODE1) | base | `manager.py:34-36` + `runtime.py` 1→435 EOF (`_notify` 294-304 incondicional, 3 paths, gate 408=KIND) | N/A (DEUDA-B) | — |
| D5 | DEUDA-B | borrar (con enum) | base | `manager.py:25-32` abierto | N/A (DEUDA-B) | — |
| D6 | DEUDA-B | borrar | base | `manager.py:42-44` abierto | N/A (DEUDA-B) | — |
| D7 | DEUDA-B | borrar | base | `protocols.py:11-16` abierto | N/A (DEUDA-B) | — |

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../04-modes.md`?** → **Sí**, 1→EOF (288 LOC): §Naturaleza, tablas A/B/C/D, §Hallazgos,
   §Cruces, §Descartados, §Re-auditoría 2026-07-12, §Plan MR1-MR3, §Re-visita COMPLETITUD L09 + 4 preguntas.
2. **¿Reconcilia el conteo?** findings en `../04-modes.md` (grid) = **23**; colocados = **23**; sin colocar = **0**.
   (A1-A5·5 + B1-B8·8 + C1-C3·3 + D1-D7·7 = 23. `FIND-MODE1`/`GAP-MODE1`/`GAP-MODE2` = capa remediación que restate
   D3-D7·D4/B8/C2, no se re-cuentan; `FIND-SIG13` homed en 08; permission-modes/GAP-02 homed en 06 §0.1 — no es fila 04.)
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador (sin grep)?** → Tramos abiertos EN ESTE CICLO:
   - **B1/C3 ✅**: `registry.py:16-35` (`TaskRecord.is_backgrounded` def), `:107-110` (`set_backgrounded` write) ·
     `resolver.py:39-49` (filtra por `ctx.is_subagent`, no por el flag) ✅.
   - **C1 🔀**: `tools/registry.py:25-34` (`list_available(mode="background")` filtra `safe_for_background`) ✅.
   - **B4/B6/B7 🔀**: `registry.py:107-110/117-124/133-150` + `notification.py:36-68` (put/process XML) ✅.
   - **D1-D7 (🔀/❌) huérfano** (afirmación NEGATIVA, la load-bearing): `modes/manager.py` 1→44 íntegro +
     `protocols.py` 1→16 íntegro + `__init__.py`; **`runtime.py` 1→435 ÍNTEGRO** (`_notify` 294-304 incondicional:
     sólo guard `parent_session_id is None`, invocado en los 3 paths killed:385/failed:392/completed:413, cero
     `on_complete`/`AgentMode`/`is_backgrounded`; notif-al-completar gateada por `parent_session_id is not None`:408 =
     KIND, no por el flag → refuerza FIND-MODE1; cero import/referencia a `modes/` en las 435 líneas); **`agent_loop.py`
     1→352 ÍNTEGRO** (`mode = "background" if ctx.is_subagent`:91; cero referencia a AgentMode en todo el loop);
     **`factory.py` 1→267 ÍNTEGRO** (`_build_local` 178-240 ensambla `LocalAgentRuntime` SIN referenciar `modes/`;
     `execution_mode` 243-267 = backends local/remote/tmux/k8s/lambda, NO AgentMode). **grep productores
     `ModeManager`/`AgentMode` en prod = 0** (corrobora AUSENCIA; sólo 2 tests + falsos positivos substring
     `getAgentModel`; `test_runtime_e2e.py:9` declara `ModeManager` fuera de alcance). ✅ orfandad confirmada por
     lectura del ENSAMBLADOR 1→EOF (no sólo grep) — L08/L09.
   - **§0.1**: `contracts/permissions.py` 1→33 ÍNTEGRO — sin campo `mode` (sólo `always_allow_command`/`_session`/
     `always_deny` + `allowed/denied_names`/`with_command_allow`) + `agent_loop.py:293,330` hack `native["plan_mode"]` ✅.
4. **¿La cara integrador quedó al MISMO detalle que la base?** → **Sí.** OI-MODE-A (disparo) + OI-MODE-B (multiplexado
   de vista) desarrollados con capacidad·costura·firma·realización·criterio (§2.5); A1-A5 swarm con blueprint de
   arranque. Ningún "→ integrador" a secas.
5. **¿Doble filo (L10)?** → **Sí, calibrado.** (a) Ningún ❌ disfrazado de 🔀: `modes/` es DEUDA-B honesto (borrar), no
   se maquilló de "divergencia". (b) Sin deuda inflada: A1-A5 swarm = ⛔ N/A-core (no ❌×5); B2/B3/B5 = CLI-ONLY (no
   gaps del base); permission-modes NO se arrastró a 04 (§0.1, evita padding + trocear alcance ajeno). Sin battery
   inventada. Los dos CORE-GAP reales se anclan pero su remediación es del dueño (05/10), no re-contada aquí.

### 3.3 §Honestidad
- **Auto-corrección de honestidad (gate auto-adversarial del usuario "¿EoF en todos?"):** la **1ª pasada NO hizo EOF
  en los ensambladores** — `runtime.py` (435) leído sólo por tramo `sed 283-335`; `agent_loop.py` (352), `factory.py`
  (267) y `contracts/permissions.py` (33) leídos **sólo por grep**, ni siquiera abiertos con Read. Esto viola L08
  (la omisión se esconde en el archivo más grande) y L09 (el ensamblador se lee 1→EOF, no por tramos) — y contradice
  la propia regla que escribí en la memoria SIGUIENTE ("el loop/caller/runtime/factory se leen 1→EOF"). **Subsanado:**
  leídos 1→EOF `runtime.py` 1→435, `agent_loop.py` 1→352, `factory.py` 1→267, `contracts/permissions.py` 1→33.
  **Resultado: CERO cambios de clasificación** — pero eso sólo se sabe tras leerlos (a diferencia de 08, donde el EOF
  SÍ destapó LAT-SIG1). Refinamiento honesto que apareció con el EOF de `runtime.py`: la notif-al-completar está gateada
  por `parent_session_id is not None` (408) = KIND, no por `is_backgrounded` → refuerza FIND-MODE1 (el gate real es
  KIND, `ModeManager` no gobierna). La orfandad de `modes/` queda ahora verificada **por lectura del ensamblador 1→EOF**
  (`_build_local` 178-240 no referencia `modes/`), no sólo por grep-de-ausencia.
- **Leídos 1→EOF EN ESTE CICLO** (L09/L11): `modes/*` (44+16+4), `registry.py` (166), `resolver.py` (82),
  `tools/registry.py` (37), `notification.py` (72), `runtime.py` (435), `agent_loop.py` (352), `factory.py` (267),
  `contracts/permissions.py` (33) + grep de productores (prueba AUSENCIA). **NO heredé** los ✅/🔀 de la re-visita L09
  2026-07-19 del tracker como evidencia-de-este-ciclo — los volví a seguir punta a punta.
- **Corrección de la memoria de retoma** (no defensiva): la nota SIGUIENTE afirmaba "GAP-02 permission modes = corazón
  de 04". Tras abrir el tracker, es **falso por ambigüedad del término**: 04 = AgentMode (ejecución/backgrounding);
  permission-modes = `hooks/toolPermission/`, homed en 06/03/10. Lo dejo explícito en §0.1 en vez de forzar un finding
  inexistente. FIND-MODE1 (`modes/` huérfano) SÍ es hermano de SignalBus/observer como decía la memoria — eso se sostiene.
- **Lo NO verificado (honesto):** la clasificación final de GAP-MODE2·AgentTool (🔀 vs ❌) la decide **10·R10**, no 04
  (aquí sólo se ancla la dirección de cada discrepancia). El discriminante `kind` de GAP-MODE1 se **diseña en
  05·GAP-EXEC2**, no aquí. El borrado efectivo de `modes/` se **ejecuta en A3.DB/Fase B** (aquí sólo se decide + ancla
  el guard). No re-ejecuté la suite (sin cambio de código este ciclo — es fase de diseño, PLAN §1.6).
- **Naming trap re-confirmada** (factory.py:129 `name if False else runtime_cls` = ternario muerto, cosmético) →
  pertenece a **18·factory**, no a 04; se nombra para no fingir que no se vio, no se remedia aquí.

### 3.4 VEREDICTO
**✅ NADA PENDIENTE → A3·15·storage.**
Conteo 23=23=0. Las 5 preguntas: sí honestas (Q3 con tramos abiertos este ciclo; Q5 doble-filo calibrado). Sin
pendiente de verificación de 04: FIND-MODE1 (borrar) anclado a A3.DB·`B-orphans`; GAP-MODE1→05·GAP-EXEC2;
GAP-MODE2→10·R10; GAP-02→06·CG-HOOK-8+A3.DA — todos **destinos concretos nombrados** (L07), no "ningún sitio".

> ⚠ **El veredicto de arriba es el del ciclo A3 (histórico) y NO sobrevive intacto a `A-CIERRE·P4″`.** Ver **§2.6**:
> **5 de sus 23 fichas (21,7 %) tienen el veredicto invertido aguas abajo** — `AgentMode` NO se borra (`RV-6`),
> la notificación background NO llega (`H-5`), el modelo `safe_for_background` se revierte (`10·E3`), `GAP-MODE2`
> ya está cerrado en 10, y el puntero de GAP-02 es rancio (hoy `K1`). Además se restituyeron **8 pérdidas de
> compresión** (`P4-04-1..8`) y la **§Evidencia entera** (`P4-04-9`, §1.0). El documento **actualizado** es el que
> entra en Fase B; el §3.4 original se conserva sólo como registro de lo que se creyó al cerrar A3.

### 3.5 Corrección de higiene (`P4-04-10`)

El archivo terminaba con basura `</content></invoke>` — **fuga de escritura de la sesión original**, exactamente
el mismo defecto que el tracker `../04-modes.md` documenta haber corregido en su §Re-auditoría 2026-07-12 (*«el
fichero tenía basura `</content></invoke>` al final»*). **La fuga se reprodujo en el destilado**: se corrigió en la
capa de origen y volvió a aparecer en la capa derivada. Eliminada aquí.
