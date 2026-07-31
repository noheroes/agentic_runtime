# 08 · signals — SEPARACION (Filosofía B)

> Ruta base `/home/noheroes/python`. Formato = `00-LEGEND.md §3` (plantilla ejercida por `03-context.md`/
> `06-hooks.md`/`10-tools-native.md`).
> Fuente = tracker `../08-signals.md` (441 líneas, leído íntegro 1→441: contrapartes A+B · tesis "dos cascadas" ·
> tabla S1-S25 · §Hallazgos FIND-SIG1-13 · §Gaps GAP-SIG1-3 · cabos · estado · §Plan SR1-SR5 · re-visita
> gate-11 con mini-ledger+precisión-de-cableado+ledger-de-lectura+4-preguntas+VEREDICTO) + **re-apertura EN ESTE
> CICLO** del ensamblador real de B (L09/L11: los ✅/🔀 del gate-11 del tracker NO se heredan como evidencia —
> se re-abren aquí contra el runtime vivo).
>
> ⚠ **REVISADO EN `A-CIERRE·P4″` (2026-07-29) — ver `A-CIERRE-P4.md §14`.** Dos cambios de estado
> (**`S2 ✅→❌`**, **`S12 🔀→❌`** ⇒ finding nuevo `CG-SIG-10`), el alcance de `DB-SIG-1..3` corregido a nivel de
> símbolo por `R-1`/`RV-6` (**`SignalType` SOBREVIVE**) con la precondición `DB-h2`, la columna canónica restituida
> (`§0.1`), y el **veredicto `§3.4` reescrito** de `✅ NADA PENDIENTE` a **`⛔ RECONCILIADO, NO CERRADO`**.
> Saldo del segundo salto: 26/26 fichas · CONSERVADA 10 · **ENRIQUECIDA 11** · COMPRIMIDA-CON-PÉRDIDA 5 ·
> INVENTADA 0 · PERDIDA de fila 0 · 16 pérdidas numeradas `P4-08-1..16`.

## 0. Tesis de separación (Filosofía B)

El canónico **NO tiene un `SignalBus`**. Su primitiva de cancelación es el **`AbortController`/`AbortSignal` nativo,
que vive DENTRO del `ToolUseContext`** (`abortController`) y se threadea por TODO el core. La señal lleva **`reason`**
(`'interrupt'`/`'sibling_error'`/`'streaming_fallback'`/user) que gobierna el comportamiento posterior, y es
**one-shot irreversible**. Hay **DOS cascadas distintas, no una** (matiz que la lectura íntegra del tracker reveló):
1. **Árbol de `AbortController`** (`createChildAbortController`) — tools/subquery del **mismo turno**, direccionalidad
   estricta (padre→hijo sí; hijo→padre NO salvo el bubble de rechazo de permiso), con nivel intermedio
   `siblingAbortController` (Bash mata hermanos sin terminar el turno).
2. **Kill de tasks** (`killAllRunningAgentTasks`+`emitTaskTerminatedSdk`) — **agentes en background** (hijos de OTRO
   turno/sesión), por el registry de tasks, NO por el árbol de controllers.

El runtime tiene **DOS mecanismos paralelos y desconectados**: (a) **`ctx.stop` (`asyncio.Event`)** — el REAL,
cableado end-to-end (loop→caller→`agentic_models.signal`; dispatcher; fork), homologación de facto del
`AbortController` pero **degradada** (binaria, sin `reason`, sin árbol direccional, sin `interruptBehavior`); y
(b) **`SignalBus`/`SignalType`/`SignalHandle`/`SignalHandler`** — **HUÉRFANO**: implementa un árbol de cascada
`ABORT/PAUSE/RESUME`+`send(cascade=True)` que **ninguna ruta consulta** (sólo sus tests), y encima **conflaciona las
dos cascadas** que el canónico separa a propósito. Tercer huérfano del patrón `modes/`/`observer/` (FIND-MODE1/EXEC4).

**Bajo Filosofía B, la homologación de 08 NO produce battery** (contraste con 10 battery-intensa / 06 battery+seam):
la cancelación es una **primitiva del base**, no un paquete opcional. Reparto por ejes:
- **T1-CONTRATO** — lo que cruza el seam: el `reason` (enum de abort) · el `aborted` result rico (reason+tool_use_id+
  mensaje sintético) · `interrupt_behavior` en `ToolProtocol` · el resultado terminal tipado `{reason:'aborted_*'}`.
- **T1-MOTOR** — el corte de la llamada al modelo (`StreamOptions.signal`→fetch/stream, `APIUserAbortError`) →
  delegado a `agentic_models` (verificación fina en 16).
- **T2-BASE-MECANISMO** — el runtime OWNS: los checks de abort en el loop/dispatcher, el threading de la señal, el
  árbol direccional de derivación, `interrupt()` público, la señal de "turno interrumpible", los dos niveles
  turno/agente. **La reconciliación de los dos mecanismos en UNA primitiva (`AbortScope`)** es el corazón de 08.
- **T2-COSTURA** — `on_abort(callback)` (cleanup/lock-release en abort mid-turn, que 11·mcp rellena).
- **T3-INTEGRADOR / CLI-ONLY-INTERFAZ** — el **disparo** del abort (keybinding Ctrl+C/Escape, escalera de prioridad,
  `killAgents`) y el **arming** de la primitiva in-turn (el standalone no la puebla). Correcto y ✅ de comportamiento:
  igual que el `abortController` canónico lo arma la UI (`useCancelRequest`), NO el core.
- **DEUDA-B (borrar)** — la maquinaria del `SignalBus` (`_Node`/`SignalHandle`/`SignalBus`/`register_handler`/
  `SignalHandler`) + la semántica `RESUME`-limpia-señal. ⚠ **A nivel de SÍMBOLO, no de paquete: `SignalType`
  SOBREVIVE** y se reubica al vocabulario `T1` (`RV-6`/`R-1`, ver `§2.4`), con la precondición `DB-h2`.

**La homologación de 08 es del SEAM de cancelación:** (a) reconciliar los dos mecanismos del runtime en UNO
(`AbortScope`: `ctx.stop` crecido a reason + árbol direccional + `interrupt_behavior` + `interrupt()` + dos niveles +
`on_abort`), (b) dejar la cascada de background donde ya vive de facto y **funciona** (el registry, kill vía
`CancelledError`), y (c) **borrar** el `SignalBus` huérfano (no fabricar un tercer canal que unifique lo que el
canónico separa). El grueso de `AbortScope` está pre-anotado en `../DEUDA-B-transversal.md §B-signals`; aquí se
re-clasifica bajo los ejes B (buena parte NO es "DEUDA-B" de tier sino **CORE-GAP A↔B**: el canónico tiene esos
comportamientos y el runtime no) y se ancla seam+cableado+prueba en-ciclo.

Convención de destino (como 03/06/10): `→NN` = homed en otra categoría con destino nombrado (L07); `AbortScope` =
la primitiva unificada (módulo base + contratos); `INTEGRADOR` = `00-INTEGRADORES.md`; `⛔-nombrado` = fuera de MVP
con satélite nombrado; `SRn` = entrada del §Plan del tracker (target codificado por xfail existente).

**Disciplina de prefijos (`A-CIERRE·P4″·c25`, molde `BATTERIES §2.1·B06`).** Las `S1..S25` de este documento son
**filas del grid del tracker 08** y NO son las `S1..S31` de `SEAMS.md` (costuras). Colisionan de hecho en tres
puntos: `08·S2` (propagación al modelo) vs `SEAMS·S2` (la señal de abort) · `08·S16` (`SignalBus`) vs `SEAMS·S16`
(`ToolProtocol`) · `08·S4` (árbol de controllers) vs `SEAMS·S4` (skeleton del runtime, cuyo `A2.5` remite **a
este documento**). Regla: al citar desde fuera se escribe **`08·Sn`** o **`SEAMS·Sn`**; **nunca se renumera**
(renumerar rompe todas las remisiones ya escritas aguas arriba).

### 0.1 Contrapartes canónicas (columna A — restituida por `A-CIERRE·P4″·P4-08-12`)

El destilado había perdido ≈87 % de la columna canónica (11 archivos con LOC y ≳30 anclas `.ts:línea` → 4 anclas,
cero LOC). En este par la pérdida **no fue documental**: `S2` es una fila cuya verdad se decide en la frontera
entre B y `agentic_models`, y sin la columna A no se ve dónde termina el cable. Se restituye:

| archivo canónico | LOC | qué aporta a 08 |
|---|---|---|
| `utils/abortController.ts` | 99 | `createAbortController(maxListeners)` · `createChildAbortController(parent)`: padre→hijo propaga, hijo→padre **NO**, WeakRef GC-safe, fast-path si el padre ya abortó (base de `CG-SIG-2`) |
| `services/tools/StreamingToolExecutor.ts` | 530 | `siblingAbortController` (:59, sólo Bash lo aborta :359-362) · `toolAbortController` per-tool (:301) con bubble condicionado (:307-315) · `getAbortReason` (:210-231) tres razones · `createSyntheticErrorMessage` (:153-205) tres mensajes · `updateInterruptibleState` (:254-260) · **`ToolStatus` + `isConcurrencySafe`** (→09) |
| `hooks/useCancelRequest.ts` | 276 | escalera de disparo (:87-122) · Ctrl+C vs Escape · `chat:killAgents` doble pulsación 3 s (:225-266) · `killAllAgentsAndNotify` (:172-195) = análogo conductual REAL de `send(cascade=True)` para background |
| `Task.ts` | 125 | `TaskContext.abortController` **uno POR task** (:39) · `totalPausedMs` (:53) = la pausa vive en el lifecycle · *"abortController were dead weight"* para kill (:71) |
| `services/tools/toolExecution.ts` | 1745 | tramos abort 400-469 / 1615-1714: check pre-exec (:415) · `CANCEL_MESSAGE`+`withMemoryCorrectionHint` (:443-452) · `isInterrupt = error instanceof AbortError` (:1694) pasado a `runPostToolUseFailureHooks` (:1700-1707) · `AbortError` no loguea (:1631) |
| `Tool.ts` | 792 | `ToolUseContext.abortController` (:180) · `signal: AbortSignal` en `call` (:201) · `interruptBehavior?(): 'cancel'\|'block'` (:416) |
| `QueryEngine.ts` | 1295 | `interrupt(): void { this.abortController.abort() }` (:1157-1159) — el espejo de `CG-SIG-7` |
| `query.ts` | 1729 | checks pre-modelo (:1015) y post-tools (:1485) · `signal.reason !== 'interrupt'` (:1046,:1501) gatea `createUserInterruptionMessage` · retornos `{reason:'aborted_streaming'\|'aborted_tools'}` |
| `services/tools/toolHooks.ts` | 650 | `signal` propagado a hooks (:63,:220,:472,:582) — el espejo de `GAP-SIG2` |
| `services/api/claude.ts` | 3419 | `signal`→fetch/stream · `APIUserAbortError` (:114,:744-745,:876,:2434-2453,:2738,:2796) · `stream.controller.abort()` en cleanup (:2906-2907) — **la contraparte exacta de `S2`/`S12`, y la que prueba que el canónico SÍ corta** |
| `useBackgroundTaskNavigation.ts` | — | :156-158 Escape sobre teammate running → **aborta el turno, NO mata** (base de `CG-SIG-9`) |

---

## 1. Tabla por finding (grid del tracker S1-S25 · 25 filas + SIG13 · 1 = 26)

Columnas: `resumen` · `núcleo|cáscara` · TIER · destino · `est.` (estado del tracker) · acción. Unidad atómica =
**fila de la tabla feature-by-feature del tracker** (espejo de la decisión de conteo de 06/10: la fila del tracker
es la unidad; los `FIND-SIG*`/`GAP-SIG*`/`SR*` son la capa de **remediación/resumen** que aterriza sobre estas
filas — referenciada en `acción`, no re-contada). `S15` doble-marca 🔀/❌ en el tracker → contada **1 vez** (🔀,
como el recuento del tracker). **SIG13** (dos niveles de abort) NO tiene fila-S en la tabla del tracker (surgió en
la re-auditoría de 04·modes) → se coloca explícito como fila extra (no plegado, L07).

### A · La primitiva REAL (`ctx.stop`) — cableada pero degradada
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | acción |
|---|---|---|---|---|---|---|
| **S1** | primitiva de cancelación en el ctx (`abortController`→`ctx.stop: asyncio.Event`) | núcleo | T2-BASE-MECANISMO | `AbortScope` (crece de `context/tool_use.py:47`) | 🟡 | keystone: `ctx.stop` binario sin reason (verificado `tool_use.py:47`); crece a `AbortScope` (CG-SIG-1..). **Columna A restituida:** el canónico tiene **un controller POR task** (`Task.ts:39`) y anota que *"abortController were dead weight"* para el kill (`Task.ts:71`, que usa sólo `setAppState`) — es el argumento canónico de por qué el nivel *work* y el nivel *agent* son distintos (`CG-SIG-9`) |
| **S2** | propagación a la llamada al modelo (`signal`→fetch/stream) | núcleo | **T1-MOTOR** | seam motor (loop→caller→`agentic_models`) — dueño compartido 08↔16 | ~~✅~~ **❌** | **CG-SIG-10** — ⚠ **ESTADO CORREGIDO en `A-CIERRE·P4″` (era `✅`).** La tubería existe (`agent_loop.py:227`+`caller.py:188-190`) pero entrega un **`asyncio.Event`** en `StreamOptions.signal` y **los 8 providers gatean el corte en `getattr(signal,"aborted",False)`** ⇒ el abort **se ignora silenciosamente en todos**. Seam **roto en el tipo del contrato**, no "pendiente de verificación fina" |
| **S6** | check pre-modelo de abort (turno) | núcleo | T2-BASE-MECANISMO | loop (`AbortScope.work` check) | ✅ | homologa `query.ts:1015` a nivel turno (verificado `agent_loop.py:173`/`186`) |
| **S7** | check pre/post ejecución de tool | núcleo | T2-BASE-MECANISMO | dispatcher (`AbortScope` check) | 🟡 | corta pre-exec (verificado `dispatcher.py:54-55`); falta cascada en-vuelo (S8) |
| **S20** | ownership: nadie setea abort internamente (lo dispara usuario/integrador) | integrador | **T3-INTEGRADOR** | INTEGRADOR (OI-SIG-A/B) | ✅ | correcto: disparo 100% externo (verificado en-ciclo: `.set()` en prod = 0) |

### B · Los tres ejes ausentes (reason · árbol direccional · interrupt_behavior)
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | acción |
|---|---|---|---|---|---|---|
| **S3** | abort **reason** (`signal.reason`: interrupt/sibling_error/user) | núcleo | **T1-CONTRATO** (reason enum) + T2-BASE | `AbortScope.reason` | ❌ | **CG-SIG-1** (FIND-SIG2): `asyncio.Event` binario sin reason → no distingue submit-interrupt de user |
| **S4** | árbol de controllers con direccionalidad (`createChildAbortController`) | núcleo | T2-BASE-MECANISMO | `AbortScope` derivación child (fork) | ❌ | **CG-SIG-2** (FIND-SIG3): `fork:80-83` comparte el MISMO Event → hijo abortaría al padre (verificado en-ciclo) |
| **S5** | `interruptBehavior()` per-tool (`cancel`/`block`) | núcleo | **T1-CONTRATO** (`ToolProtocol`, home 09) | `ToolProtocol.interrupt_behavior` (→09) + consulta aquí | ❌ | **CG-SIG-3** (FIND-SIG4): `protocol.py:51-61` sin el campo (verificado); el runtime aborta toda tool indiscriminadamente |
| **S8** | cancelación de tools EN VUELO (sibling/per-tool child, `sibling_error` sólo Bash, bubble permiso) | núcleo | T2-BASE-MECANISMO | `AbortScope` (nivel sibling/tool) | ❌ | **CG-SIG-4** (FIND-SIG3b): dispatcher no aborta subprocesos ya lanzados ni cascada Bash→hermanos |

### C · Mensajes sintéticos & pairing en abort
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | acción |
|---|---|---|---|---|---|---|
| **S21** | **tres** mensajes sintéticos por tool abortada (`CANCEL`/`REJECT`/sibling) + `withMemoryCorrectionHint` | núcleo | **T1-CONTRATO** (`aborted` rico) | `ToolResult.aborted(reason,tool_use_id,...)` | ❌ | **CG-SIG-5** (FIND-SIG10): `protocol.py:47-48` = string plano `f"aborted: {name}"` (verificado); sin distinguir interrupción/rechazo/sibling ni hint |
| **S10** | mensaje de interrupción al usuario, gateado por `reason!=='interrupt'` | núcleo | **T1-CONTRATO** (reason gatea) | `AbortScope.reason` + render integrador (OI-SIG-C) | ❌ | **CG-SIG-5** (FIND-SIG2b): sin `createUserInterruptionMessage` ni distinción submit-interrupt; depende de S3 |
| **S9** | invariante `tool_use↔tool_result` en abort (`getRemainingResults`/`yieldMissing…`) | núcleo | T2-BASE-MECANISMO | **→02·LR5** (helper compartido FIND-L1) | 🟡 | homed 02: pairing se mantiene si el corte es a nivel dispatch (verificado `agent_loop.py:319-323`); mid-stream sin verificar (FIND-SIG7) |
| **S24** | `discard()` + razón `'streaming_fallback'` (abandonar tools del intento de streaming fallido) | núcleo | T2-BASE-MECANISMO | **→02** (motor#2 recuperación de streaming) | ❌ | homed 02: liga la recuperación de streaming (aún ❌ en 02); sin equivalente |

### D · Señal de interrumpibilidad & resultado terminal
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | acción |
|---|---|---|---|---|---|---|
| **S22** | `interruptBehavior==='cancel'` en todas las en-vuelo ⇒ turno interrumpible (`setHasInterruptibleToolInProgress`) | núcleo | T2-BASE-MECANISMO | `AbortScope`/ctx (deriva de S5) + expone en evento (→07·EVT7) | ❌ | **CG-SIG-6** (FIND-SIG11): el runtime no computa ni expone si el turno es interrumpible; Ctrl+C no puede gatearse |
| **S23** | tracking de tool_use IDs en vuelo (`setInProgressToolUseIDs`/`markToolUseAsComplete`) | núcleo | T2-BASE-MECANISMO | `AbortScope`/dispatcher (set de IDs vivos) | ❌ | **CG-SIG-6**: necesario para el pairing sintético (S9) y la señal S22 |
| **S11** | resultado terminal tipado (`{reason:'aborted_streaming'\|'aborted_tools'}`) | núcleo | **T1-CONTRATO** | **→07·EvR4** (`ResultEvent`/`SDKResultMessage`) + `B-usage` | ❌ | homed 07 (FIND-SIG8, liga 07·FIND-EVT1): `run()→None` no surface reason de abort aguas arriba (BFF/CCR) |
| **S12** | error de abort a nivel API (`APIUserAbortError`, `stream.controller.abort()` cleanup) | núcleo | **T1-MOTOR** | **CG-SIG-10** (dueño compartido 08↔16) | ~~🔀~~ **❌** | ⚠ **ESTADO CORREGIDO en `A-CIERRE·P4″` (era `🔀`).** No es delegación: **`16·FIND-MODELS4` ya dictaminó en contra** ("abort roto, tipo de señal equivocado", cf. `DEUDA-A §1.2(a)`; `SEAMS §S2` = `existe-roto`). No existe `APIUserAbortError` ni equivalente tipado, porque el provider **nunca aborta** (ver `S2`) |

### E · `interrupt()` público & disparo (integrador)
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | acción |
|---|---|---|---|---|---|---|
| **S13** | `interrupt()` público (`QueryEngine.interrupt`→abort) | núcleo | T2-BASE-MECANISMO | `AbortScope.interrupt()` + método en loop/runtime | ❌ | **CG-SIG-7** (GAP-SIG1): sin `interrupt()` público; hoy el integrador setea `ctx.stop` a mano |
| **S14** | disparo del abort (keybinding Ctrl+C/Escape, prioridad cancel-task-then-pop, `killAgents`) | integrador | **CLI-ONLY/INTERFAZ** + T3 | INTEGRADOR (OI-SIG-A) | ⛔ | `useCancelRequest.ts` = React/terminal; el **comportamiento** (quién dispara) es del integrador; el runtime expone el seam |

### F · `SignalBus` huérfano → DEUDA-B (borrar)
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | acción |
|---|---|---|---|---|---|---|
| **S16** | `SignalBus` árbol de cascada (`send(cascade=True)`, parent→children DFS) | núcleo | **DEUDA-B (borrar)** | borrar **a nivel de símbolo** (`RV-6`): mueren `_Node`/`SignalHandle`/`SignalBus`/`register_handler`/`SignalHandler`/`__init__.py` | 🔀 | **DB-SIG-1** (FIND-SIG1, `SR1`): HUÉRFANO (verificado en-ciclo: prod-refs=0, sólo tests) + conflaciona las dos cascadas. ⚠ **NO se borra `signals/` entero: `SignalType` SOBREVIVE** (ver `§2.4`) |
| **S17** | `SignalBus.register_handler` (handlers externos) | núcleo | **DEUDA-B (borrar)** | cae con el bus (`bus.py:89-96`) | ❌ | **DB-SIG-2** (FIND-SIG5, `SR1`): `bus.py:89-96` guarda en `_handlers` pero `send`/`_apply` **nunca invocan** `handle_signal` (verificado); extension point muerto |
| **S18** | `PAUSE`/`RESUME` | núcleo | **DEUDA-B (borrar la semántica, NO el enum)** | muere la semántica `RESUME`-limpia-señal (`bus.py:68-69`); **`SignalType` se REUBICA** al módulo de vocabulario `T1`; la pausa como lifecycle → **→04/05** (`totalPausedMs`) | 🔀 | **DB-SIG-3** (FIND-SIG6, `SR1`): `bus.py:68-69` `RESUME` limpia la señal → contradice la irreversibilidad del abort; mal ubicada. ⚠ **Precondición `DB-h2`**: no se ejecuta antes de que **H-3** tenga hogar (ver `§2.4`) |
| **S19** | cancelación en hooks (`signal` a Pre/PostToolUse hooks) | núcleo | T2-BASE-MECANISMO | **→06·hooks** (threadear `stop`/reason a `HookRunner.run`) | ❌ | homed 06 (GAP-SIG2): `agent_loop.py:301-306` payload de `PRE_TOOL_USE` sin `stop`/reason (verificado); hooks no abort-aware |

### G · Cabos de correctitud (cleanup · isInterrupt · dos niveles)
| ID | resumen | núcleo\|cáscara | TIER | destino | est. | acción |
|---|---|---|---|---|---|---|
| **S15** | cleanup on abort (computerUse ⛔; **MCP unhide + release de locks** = core) | núcleo (patrón) | **T2-COSTURA** (`AbortScope.on_abort`) + ⛔ (computerUse) | costura `on_abort` (base) + 11·mcp registra | 🔀/❌ | **CG-SIG-8** (FIND-SIG9/SR3): el patrón "liberar locks/recursos al abortar mid-turn" es core; computerUse UI = ⛔ |
| **S25** | `isInterrupt = error instanceof AbortError` a `PostToolUseFailure` hooks; `AbortError` no loguea error | núcleo | T2-BASE-MECANISMO | **→06·HR2** (el hook recibe `is_interrupt`) | ❌ | homed 06 (FIND-SIG12/GAP-SIG2): el runtime ni threadea `stop` a hooks ni distingue abort de error real |
| **SIG13** | dos niveles de abort (`currentWorkAbortController` corta el turno / `abortController` mata el agente) | núcleo | T2-BASE-MECANISMO | `AbortScope.work` + `AbortScope.agent` (liga 05·EXEC12) | ❌ | **CG-SIG-9** (SR4, de re-audit 04·modes): `ctx.stop` de UN nivel no distingue "para el turno" de "mata el agente"; el kill-de-task ya existe (registry, `CancelledError`). **Ancla canónica restituida:** `useBackgroundTaskNavigation.ts:156-158` (Escape sobre teammate running → **aborta el turno, NO mata**); liga `TaskStopTool`/`emitTaskTerminatedSdk('stopped')` |

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica (nombre · productor invoca · consumidor implementa)
- **`AbortScope`** (la primitiva unificada; **T2-BASE-MECANISMO + T1-CONTRATO del `reason`**; grueso en
  `../DEUDA-B-transversal.md §B-signals`) — productor: el loop/dispatcher consultan `abort.work.is_aborted()`, el
  integrador llama `abort.interrupt(level, reason)`; consumidor: la propia primitiva (crece de `ctx.stop`). Reemplaza
  **ambos** mecanismos del runtime (`ctx.stop` degradado + `SignalBus` huérfano). Ejes que absorbe: `reason` (S3),
  árbol child direccional (S4, espejo `createChildAbortController` + WeakRef GC-safe + fast-path padre-ya-abortado),
  `interrupt()` público (S13), dos niveles work/agent (SIG13), señal de interrumpibilidad (S22), tracking de IDs
  vivos (S23), `on_abort` (S15). **Hoy: ausente** (existe `ctx.stop` binario, cableado pero degradado).
- **`AbortScope.on_abort(callback)`** (**T2-COSTURA**, S15/CG-SIG-8) — productor: al `interrupt()`, el scope corre
  los callbacks en LIFO; consumidor: los subsistemas que toman recursos (11·mcp locks/hide, worktrees) registran un
  cleanup. Alternativa: `ctx.on_turn_cleanup` que el loop dispara en el path de abort.
- **`ToolProtocol.interrupt_behavior`** (**T1-CONTRATO**, S5/CG-SIG-3; home del protocolo = 09) — productor:
  `AbortScope` lo consulta antes de abortar una tool en vuelo; consumidor: cada tool lo declara (default `'block'`).
  El árbol in-turn NO aborta las `'block'` en interrupción de usuario.
- **seam T1-MOTOR de corte** (S2/S12) — ⚠ **`existe-roto`, corregido en `A-CIERRE·P4″`** (la redacción anterior
  decía "**cableado** … el consumidor corta fetch/stream y surface `APIUserAbortError`"; era falso).
  Productor: el caller hace `replace(opts, signal=stop)` (`caller.py:188-190`) **pasando un `asyncio.Event`**
  (`caller.py:151`/`:166` lo tipan así). Consumidor: **ningún provider de `agentic_models` lo consulta como Event**
  — los 8 gatean en `getattr(signal, "aborted", False)` y `asyncio.Event` **no tiene `.aborted`**, luego el
  `getattr` es `False` siempre. **Hay tubería y no hay señal.** Ver `CG-SIG-10` (`§2.3`) y `SEAMS §S2`
  (`existe-roto`) / `16·FIND-MODELS4`. La verificación en 16 **ya ocurrió y falló**: no queda nada que delegar.
- **cascada de background = registry de tasks** (**cableado y FUNCIONA** — verificado en-ciclo `runtime.py:381-387`)
  — el nivel "agent-kill": `runtime.cancel(task_id)`→`registry.kill`→`asyncio_task.cancel()`→`CancelledError`
  capturado→`kill`+`_fire_stop(SubagentStop)`+`_notify`. Homólogo de `killAllRunningAgentTasks`+`emitTaskTerminatedSdk`.
  **No hay que fabricarla** — ya existe (home 05). Es la cascada #2 del canónico.
- **seam de arming del ctx in-turn** (**cableado, no armado en standalone**) — `context/adapters.py:15/44`
  (`tool_use_context_from_session(*, stop=...)`→`ToolUseContext(stop=stop)`, verificado en-ciclo) y
  `runtime.py:329-330` (`root_context_modifier(ctx, task)`). Sólo el integrador (o los tests) arman `stop=Event()`.

### 2.2 Batteries que alimenta
**Ninguna.** 08 es una categoría **sin battery** (contraste declarado con 10 battery-intensa / 06 battery+seam): la
cancelación es una **primitiva del base** (T1-CONTRATO + T2-BASE-MECANISMO + T2-COSTURA), no un paquete estándar
opcional. Esto NO es un hueco del método: es la naturaleza de la categoría (el canónico tampoco tiene un "paquete de
señales" sustituible — el `AbortController` es nativo y no-opcional). Anti-padding (L10): no se inventa una battery
para llenar la casilla.

### 2.3 CORE-GAPs (brechas A↔B reales → rollup `DEUDA-A.md`)
El base **debe** reproducir el comportamiento observable y **hoy no** — remediación desarrollada (L05). El grueso de
`AbortScope` está pre-anotado en `../DEUDA-B-transversal.md §B-signals`; **la SEPARACION corrige su tier**: reason/
árbol/interrupt_behavior/interrupt()/niveles/interrumpibilidad son **CORE-GAP A↔B** (el canónico los tiene, el
runtime no), NO "DEUDA-B" (esa es sólo el borrado del huérfano, §2.4). Numeración `SRn` = §Plan del tracker.

**Rótulo agregado del tracker (restituido por `A-CIERRE·P4″·P4-08-7`):** `GAP-SIG3` (tracker `§Gaps`:220) es el
nombre que el tracker da a los **tres ejes juntos** — *"la primitiva de abort del runtime carece de `reason`, árbol
direccional e `interruptBehavior`: los tres ejes que el canónico expresa con `AbortController` +
`AbortSignal.reason` + `interruptBehavior()`"*. Aquí se **reparte** en `CG-SIG-1` (reason) · `CG-SIG-2` (árbol) ·
`CG-SIG-3` (`interrupt_behavior`); el rótulo se conserva porque es el índice por el que 09 y 16 entran a este
documento. `GAP-SIG1`→`CG-SIG-7` · `GAP-SIG2`→`S19`/`S25` (homed 06). Los tres `GAP-SIG*` quedan con sucesor
nombrado (la 1ª redacción citaba sólo dos).

- **CG-SIG-1 (SR2 · FIND-SIG2 · S3/S10)** — la primitiva única con `reason`.
  **comportamiento:** la señal de abort porta `reason` (enum: `interrupt`/`sibling_error`/`streaming_fallback`/`user`);
  el loop **omite** `createUserInterruptionMessage` cuando `reason=='interrupt'` (el mensaje de usuario encolado ya da
  contexto, espejo `query.ts:1046,1501`). **seam/firma:** `AbortScope` con `reason: AbortReason | None`; `ctx.stop`
  binario (`tool_use.py:47`) se reemplaza por `ctx.abort: AbortScope`. **cableado:** el integrador llama
  `abort.interrupt(reason=...)`; el loop lee `abort.reason` en el path de fin-por-abort. **orden:** raíz (todo lo demás
  cuelga). **prueba:** `test_abort_carries_reason` + `test_user_interrupt_skips_synthetic_message` (xfail SIG2 existente).
- **CG-SIG-2 (SR2 · FIND-SIG3 · S4)** — árbol child direccional.
  **comportamiento:** derivar un hijo del scope del padre con direccionalidad estricta (padre→hijo propaga; hijo→padre
  NO, salvo bubble explícito de rechazo de permiso), WeakRef GC-safe, fast-path si el padre ya abortó. **seam/firma:**
  `AbortScope.child() -> AbortScope`; reemplaza el `fork:80-83` que hoy comparte el MISMO `asyncio.Event`
  (verificado en-ciclo: `if propagate_abort: stop = parent_stop` → un `set()` del hijo abortaría al padre). **cableado:**
  `RuntimeContextForker.fork` deriva `child()` en vez de aliasar el Event; la tool Agent threadea el scope del padre.
  **orden:** tras CG-SIG-1. **prueba:** `test_child_abort_does_not_abort_parent` (xfail SIG3). **Nota (doble-inocuo hoy,
  verificado en-ciclo):** el peligro no se materializa aún — nadie setea `stop` en el hijo Y el fork ni recibe un
  `parent_stop` vivo (`runtime.py:201` llama `.fork(...)` sin `parent_stop`); el riesgo aparece cuando el integrador
  threadee un `parent_stop` real Y exista un setter en el hijo. El ❌ se sostiene: la **API** comparte el objeto cuando
  se usa.
- **CG-SIG-3 (SR2 · FIND-SIG4 · S5)** — `interrupt_behavior` per-tool.
  **comportamiento:** ante interrupción de usuario, NO abortar las tools `'block'` (sólo las `'cancel'`, espejo
  `StreamingToolExecutor:221-233`). **seam/firma:** `interrupt_behavior: Literal['cancel','block']` en `ToolProtocol`
  (default `'block'`; home del protocolo = 09) — hoy ausente (verificado `protocol.py:51-61`). `AbortScope` lo consulta
  antes de abortar cada tool en vuelo. **cableado:** el nivel tool del árbol (CG-SIG-4) consulta el campo. **orden:**
  junto a CG-SIG-4; coordina con 09 (dueño del protocolo). **prueba:** `test_block_tools_survive_user_interrupt` (xfail SIG4).
- **CG-SIG-4 (SR2 · FIND-SIG3b · S8)** — cancelación de tools EN VUELO.
  **comportamiento:** dos niveles intermedios espejo del canónico — `sibling` (un error de **Bash** aborta hermanos en
  vuelo con `sibling_error` SIN terminar el turno) y `tool` (per-tool child; su abort bubblea al scope del turno sólo
  si se cumplen **las TRES** condiciones de `StreamingToolExecutor:307-315` — `reason != 'sibling_error'` **AND** el
  padre **no estaba ya abortado** (evita el doble-abort) **AND** no hay `discard` — para que el rechazo de permiso
  (`PermissionContext.cancelAndAbort`) termine el turno; la condición existe por la **regresión #21056**
  (`ExitPlanMode`), no es teórica). **seam/firma:**
  `AbortScope` con sub-scopes `sibling()`/`tool()`; el dispatcher deriva un `tool()` por ejecución y cancela el
  subproceso real al abortar. **cableado:** el dispatcher (hoy `dispatcher.py:54-55` sólo corta pre-exec, verificado)
  deriva y propaga; Bash produce `sibling_error`. **orden:** tras CG-SIG-2/3. **prueba:**
  `test_bash_error_aborts_siblings_not_turn`, `test_inflight_tool_killed_on_abort`.
- **CG-SIG-5 (SR2 · FIND-SIG10/SIG2b · S21/S10)** — `aborted` result rico.
  **comportamiento:** tres mensajes sintéticos distintos por `tool_use_id`, todos con `withMemoryCorrectionHint`:
  `CANCEL_MESSAGE` (abort pre-exec), `REJECT_MESSAGE` (rechazo de permiso), "Cancelled: parallel tool call … errored"
  (sibling). Garantiza el pairing `tool_use↔tool_result` para cada tool abortada. **seam/firma:** `ToolResult.aborted`
  (hoy `f"aborted: {name}"` plano, verificado `protocol.py:47-48`) porta `reason` + `tool_use_id` + renderiza el mensaje
  correcto + `memory_correction_hint`. **cableado:** el dispatcher/`AbortScope` construye el result por reason; el loop
  lo parea (`agent_loop.py:319-323`). **orden:** tras CG-SIG-1 (necesita reason). **prueba:**
  `test_aborted_result_carries_reason_and_hint` (xfail SIG10).
- **CG-SIG-6 (SR2 · FIND-SIG11 · S22/S23)** — señal de "turno interrumpible" + tracking de IDs vivos.
  **comportamiento:** computar `has_interruptible_tool_in_progress` = TODAS las tools en vuelo son `interrupt_behavior=='cancel'`
  (espejo `setHasInterruptibleToolInProgress`) → gobierna si Ctrl+C puede interrumpir el turno; requiere un set de
  `tool_use` IDs en vuelo. **seam/firma:** `AbortScope`/dispatcher mantiene `in_progress_ids: set[str]` (marca al
  despachar, desmarca al completar) y deriva la señal; se expone en el ctx/evento. **cableado:** el dispatcher marca;
  la señal va al evento `session_state_changed` (**→07·FIND-EVT7**). **orden:** tras CG-SIG-3 (deriva de `interrupt_behavior`).
  **prueba:** `test_interruptible_signal_reflects_inflight_tools`.
- **CG-SIG-7 (SR1 · GAP-SIG1 · S13)** — `interrupt()` público. *(`SR1` lo contiene: el tracker :268 escribe
  `ctx.stop` crecido a `ctx.abort: AbortScope` con reason + árbol + **`interrupt()`**.)*
  **comportamiento:** un método `interrupt(level, reason)` en loop/runtime que dispara el abort (espejo
  `QueryEngine.interrupt`), en vez de que el integrador setee `ctx.stop` a mano. **seam/firma:**
  `AbortScope.interrupt(level='work'|'agent', reason=...)` + un método delegador en el runtime/loop. **cableado:** el
  integrador (o su transporte) lo llama; el loop chequea `abort.work.is_aborted()`. **orden:** tras CG-SIG-1/9.
  **prueba:** `test_public_interrupt_stops_turn`.
- **CG-SIG-8 (SR3 · FIND-SIG9 · S15)** — cleanup / liberación de recursos al abortar mid-turn.
  **comportamiento:** al abortar en medio de un turno, liberar recursos (MCP unhide + release de locks = core;
  `cleanupComputerUseAfterTurn` = ⛔ UI). Sin el gancho, un abort mid-turn deja locks MCP tomados / recursos colgando.
  **seam/firma:** `AbortScope.on_abort(callback)` (**T2-COSTURA**); al `interrupt()`, corre los callbacks en LIFO.
  **cableado:** 11·mcp registra su release; el loop/dispatcher lo dispara al detectar abort. **orden:** tras `AbortScope`
  y junto a 11. **prueba:** `test_abort_runs_cleanup_callbacks`. **Nota:** este finding NO estaba en el
  `§B-signals` original → **se añade allí** como sub-ítem (cerrando el hueco de la auditoría).
- **CG-SIG-9 (SR4 · SIG13)** — dos niveles de abort (work vs agent).
  **comportamiento:** `currentWorkAbortController` corta el TURNO pero el agente sigue vivo (puede recibir
  `SendMessage`-continue) vs `abortController` mata al agente. Un `ctx.stop` de UN nivel no lo modela → no se puede
  "interrumpir el trabajo actual sin matar al agente" (necesario para 05·EXEC12 pendingMessages + `TaskStop`).
  **seam/firma:** `AbortScope.work` (turno) + `AbortScope.agent` (vida); `interrupt(level=...)`. **cableado:** el loop
  chequea `abort.work.is_aborted()` (los checks `agent_loop.py:173/186` pasan a `abort.work`); el registry `kill` usa
  `abort.agent` — **el nivel agent-kill YA opera** (verificado en-ciclo `runtime.py:381-387` vía `CancelledError`), lo
  que falta es separar el nivel work. **orden:** junto a `AbortScope` + 05·EXEC12. **prueba:**
  `test_work_abort_keeps_agent_alive`. **Nota:** también se **añade** a `§B-signals` como sub-ítem.

- **CG-SIG-10 (S2/S12) — el seam de corte al modelo está ROTO EN EL TIPO** *(finding NUEVO de `A-CIERRE·P4″`;
  sustituye al `✅` de S2 y al `🔀` de S12; dueño compartido **08↔16**)*.
  **comportamiento:** un abort in-turn debe **cortar la llamada al modelo en vuelo** y surface un error tipado
  (`APIUserAbortError`, espejo `claude.ts:114/744-745/2434-2453` + `stream.controller.abort()` :2906-2907). **Hoy no
  corta:** `caller.py:151`/`:166` tipan `stop: Optional[asyncio.Event]` y `:188-190` lo entregan como
  `StreamOptions.signal`; **los 8 providers** gatean el corte en `getattr(signal, "aborted", False)`
  (`anthropic.py:450,717,732` · `openai_responses.py:238,254` · `openai_codex_responses.py:99,259,464,580,663,669,
  697,759,773` · `azure_openai_responses.py:213,229` · `amazon_bedrock.py:534,549` · `mistral.py:389,404` ·
  `faux.py:275,284,297,311,327`; `openai_completions.py:512` sólo lo usa para desactivar el timeout) y
  **`asyncio.Event` no expone `.aborted`** ⇒ el `getattr` es `False` en toda ejecución posible ⇒ **el abort se
  ignora silenciosamente en todos**. Ocurrencias de `is_set()` en `agentic_models` = **0** (censo por símbolo
  en-ciclo). El comentario `# asyncio.Event or AbortSignal equivalent` (`model_types.py:100`) **afirma lo que el
  código refuta** — `RV-5`: un comentario no es evidencia de cableado.
  **seam/firma — ⚠ RESUELTO CONTRA EL CANÓNICO, no elevado a 16 (`A-CIERRE·P4″`, 2ª vuelta 2026-07-29).** La
  redacción anterior planteaba *"dos opciones y hay que elegir en el par 16"*: (a) `Protocol` con `aborted`+`reason`
  (preferida) vs (b) providers gateando en `is_set()`. **No eran dos ramas defendibles: el canónico ya dicta (a),
  y se ha ido a leerlo.** Censo de primera mano en `claude-code/src`: el tipo es **`AbortSignal` nominal**, anotado
  como tal en toda firma que lo transporta (`claude.ts:721,764,829,1022,3251,3310` · `awaySummary.ts:31` ·
  `elicitationHandler.ts:34,217,267` · `toolUseSummaryGenerator.ts:34` · `mcp/client.ts:2830,2839,2847,3041`);
  se lee sincrónicamente por **`.aborted`** (**119** ocurrencias) y se escucha por **`addEventListener('abort')`**
  (**26**); lleva **`.reason`**, que se propaga a los hijos (`abortController.ts:35,76`) y se lee de vuelta
  (`StreamingToolExecutor.ts:308`). ⇒ **la rama (b) no es defendible**: `asyncio.Event` no tiene `reason`, no
  admite listener de abort ni propagación padre→hijo, y por tanto **no puede sostener `CG-SIG-1` (reason),
  `CG-SIG-7` (árbol) ni `CG-SIG-8` (`on_abort`)**. Se ejecuta (a) por `D-06·1`. **Y el defecto NO está en los
  providers:** su `getattr(signal, "aborted", False)` **mimetiza correctamente el canónico**; el productor
  (`caller.py`) es quien entrega el tipo equivocado. Lo que hay que arreglar es **quién produce**, no quién
  consume — lo contrario de lo que la nota «tocar 8 ficheros» insinuaba.
  **⚠ SEGUNDO DEFECTO, DESTAPADO POR LA MISMA LECTURA — `CG-SIG-11`.** Aun con el tipo correcto, `.aborted`
  **sondeado** entre eventos sólo corta **entre chunks**: no cierra la petición. El canónico **no sondea para
  cortar** — entrega la señal al **cliente HTTP**: `anthropic.beta.messages.create({...params, stream:true},
  { signal })` (`claude.ts:1826/1843`), y es el SDK quien aborta la conexión y lanza `APIUserAbortError`
  (`:2434`), que el canónico **desambigua re-leyendo `signal.aborted`**: si la señal NO estaba abortada, el
  `APIUserAbortError` venía del timeout interno del SDK y se re-lanza como `APIConnectionTimeoutError`
  (`:2438-2458`). ⇒ el trabajo de `CG-SIG-10` no termina en tipar el campo: **la señal debe llegar al cliente
  HTTP de cada provider** (`httpx`/SDK), y `S12` no es "verificación fina" sino esa entrega. Ver `CG-SIG-11`.
  **cableado:** `caller.py:188-190` deja de pasar el `Event` crudo y pasa el `AbortScope` (o su vista de sólo
  lectura); `model_types.py` tipa el campo con el `Protocol` en vez de `Any`; el `async for` de `caller.py:204-245`
  se envuelve para traducir el corte a resultado de abort tipado (liga `S11`→`07·EvR4`).
  **orden:** **bloquea a `CG-SIG-1..9`** en el eje de utilidad — sin este cable, `AbortScope` corta el loop pero
  no la petición HTTP en vuelo, que es el caso de uso real (Ctrl+C durante la generación). Coordinar con **16**.
  **prueba:** `test_abort_cuts_model_stream` (provider `faux`: setear el scope a mitad de stream y exigir que el
  generador termine) + `test_stream_options_signal_is_protocol_typed` (mypy/estructural: un `asyncio.Event` desnudo
  **no** debe satisfacer el tipo del campo — el test que habría cazado esto).
  **corroboración:** `SEAMS §S2` = `existe-roto` (`16·A6`) · `DEUDA-A §1.2(a)` = *"cruza `16·FIND-MODELS4` (abort
  roto, tipo de señal equivocado) y `05·E15` (kill ⇒ pérdida de trabajo)"*.

- **`CG-SIG-11` · La señal debe llegar al CLIENTE HTTP, no sólo al bucle del provider** *(abierto por la lectura
  del canónico, `A-CIERRE·P4″` 2ª vuelta; separable de `CG-SIG-10` porque sobrevive a arreglar el tipo)*
  **comportamiento:** abortar durante la generación **cierra la conexión**; no espera a que el servidor emita el
  siguiente chunk. El canónico lo consigue **sin sondear**: pasa el `AbortSignal` en las *request options* del SDK
  (`anthropic.beta.messages.create({...params, stream:true}, { signal })`, `claude.ts:1826/1843`; mismo patrón en
  `claude.ts:733,776,870,902,2558,2657` y en `fetch(url, {...init, signal})`, `mcp/auth.ts:206,229`). El sondeo de
  `.aborted` en el canónico sirve para **decidir y desambiguar**, no para cortar.
  **seam/firma:** `StreamOptions` necesita que el objeto de señal sea traducible al mecanismo de cancelación del
  cliente de cada provider (`httpx` ⇒ cancelar la `Response.aiter_*` / cerrar el stream; SDKs oficiales ⇒ su
  parámetro nativo). Candidato: que el provider registre `abort_scope.on_abort(cierra_el_stream)` (`CG-SIG-8`)
  en vez de consultar un booleano — **el `on_abort` deja de ser cosmético y pasa a ser el mecanismo**.
  **cableado:** dueño **16·models**, un punto por provider; `08` sólo aporta el scope con listener.
  **orden:** después de `CG-SIG-10` (tipo) y de `CG-SIG-8` (`on_abort`); **antes** de que `02·G5` pueda volver a ✅.
  **prueba:** `test_abort_closes_http_stream` — servidor lento que no emite más chunks; abortar debe resolver el
  `await` en vez de colgarse hasta el siguiente evento. Es el test que distingue `CG-SIG-11` de `CG-SIG-10`:
  con el tipo arreglado pero sin entrega al cliente, `test_abort_cuts_model_stream` (faux, chunks continuos)
  **pasa** y éste **no**.
  **corroboración:** `claude.ts:2438-2458` — el canónico distingue *abort de usuario* de *timeout interno del SDK*
  re-leyendo `signal.aborted`; esa desambiguación **sólo tiene sentido si el corte lo ejecuta el cliente HTTP**.

**CORE-GAPs que 08 detecta pero homea fuera** (destino nombrado, L07):
- **S9/SIG7 pairing `tool_use↔tool_result` en abort** (`SR5`) → **02·LR5** (familia FIND-L1: helper compartido de pairing).
- **S11/SIG8 resultado terminal `{reason:'aborted_*'}`** (`SR5`) → **07·EvR4** (`ResultEvent`/`SDKResultMessage` con
  subtype) + `B-usage` (liga 07·FIND-EVT1: sin él no hay señal de cancelación observable aguas arriba).
- **S25/SIG12 `isInterrupt` a `PostToolUseFailure`** (`SR5`) → **06·HR2** (el hook recibe `is_interrupt`).
- **S19/GAP-SIG2 `stop`/reason a los hooks** (`SR2`, vía la primitiva) → **06** (threadear a `HookRunner.run`; el
  payload actual no lo lleva, verificado `agent_loop.py:301-306`). Espejo canónico: `toolHooks.ts:63,220,472,582`.
- **S22 señal de interrumpibilidad al evento** (`SR2`) → **07·FIND-EVT7** (`session_state_changed`).
- **S24 `discard`/`streaming_fallback`** → **02** (motor#2 de recuperación de streaming, aún ❌).
- **`ToolStatus` (queued/executing/completed/yielded) + `isConcurrencySafe`** → **09·tools-infra·FIND-TOOL1**
  (*dispatcher SECUENCIAL, sin `isConcurrencySafe`*). Pieza del bloque `StreamingToolExecutor` (tracker :44) que
  **ni el tracker ni la 1ª redacción de este destilado colocaron**; homada aquí por `A-CIERRE·P4″·P4-08-8`. En el
  canónico gobierna qué tools corren en paralelo y cuáles en exclusiva, y por tanto **qué hay que abortar en vuelo**
  (liga `CG-SIG-4`): sin el estado por tool, el nivel `tool()` del árbol no tiene a quién cancelar.
- ~~**S12/`APIUserAbortError` corte HTTP fino** → 16·models~~ — ⚠ **RETIRADO de homed-fuera en `A-CIERRE·P4″`**:
  16 **ya dictaminó** (`FIND-MODELS4`) y el veredicto fue en contra. Un `🔀` no puede delegar en una categoría que
  ya resolvió el punto: eso no es homar con destino, es enterrar. Reconvertido en **`CG-SIG-10`** (arriba).

**Cabos ENTRANTES que aterrizan en 08** (restituidos por `A-CIERRE·P4″·P4-08-9/10`; los rollups los dirigen aquí y
la 1ª redacción no los acusaba de recibo):
- **`16·FIND-MODELS4`** (`DEUDA-A §1.2(a)`) — *abort roto, tipo de señal equivocado*. **Es el mismo hecho que
  `CG-SIG-10`**, visto desde la capa de modelos. Dueño compartido; no duplicar la remediación.
- **`05·E15`** (`DEUDA-A §1.2(a)`) — *kill ⇒ pérdida de trabajo*. Es el argumento material de `CG-SIG-9`: sin nivel
  *work*, la única forma de parar es matar, y matar pierde el turno.
- **`11·CG-MCP-20`** (`BATTERIES §2.3`) — el consumidor nominal de `AbortScope.on_abort` (`CG-SIG-8`). La remisión
  decía *"11·mcp registra su release"* **sin identificador**: sin él no es localizable desde el lado de 11.
- **`SEAMS §S24`** (watchdog/deadline) — `01·CTR-15 arm_watchdog` es **no-op** y su decisión está condicionada a
  este par: *"completar o retirar según lo cubra el `AbortScope`"*.
  ~~**Decisión que 08 debe emitir:** el `AbortScope` cubre la cancelación **por señal**, no el **deadline por
  tiempo**; un watchdog que arma un timeout y dispara `abort.interrupt(reason='timeout')` es un **productor** del
  scope, no un duplicado ⇒ `arm_watchdog` **se completa** (no se retira), con `reason='timeout'` como cuarta razón
  del enum de `CG-SIG-1`.~~
  ⚠ **DECISIÓN CORREGIDA CONTRA EL CANÓNICO (`A-CIERRE·P4″` 2ª vuelta, 2026-07-29).** La emití **razonando**
  (*"señal y deadline son disparadores distintos"*) en vez de **leyendo**, y el canónico la desmiente en su parte
  de mecanismo. Lo que el canónico hace: **`createCombinedAbortSignal(signal, { signalB?, timeoutMs? })`**
  (`utils/combinedAbortSignal.ts` 1→47) **funde señal + segunda señal + deadline en UNA sola `AbortSignal`**; el
  timeout es `setTimeout(abortCombined, timeoutMs)` y aborta **el mismo controller**. Consumidores reales: los
  **cinco** fire points de hooks con timeout por-hook (`hooks.ts:2149,2196,3089,3281,4758` ·
  `execPromptHook.ts:59` · `execAgentHook.ts:80` · `execHttpHook.ts:151`) y `print.ts:4189`. En MCP el mismo
  patrón con reason explícito: `c.abort(new DOMException('The operation timed out.','TimeoutError'))`
  (`mcp/client.ts:519`).
  **Qué de mi decisión sobrevive y qué no:**
  1. ✅ **Sobrevive:** el vencimiento **entra por la misma puerta que el abort** — no hay mecanismo de deadline
     paralelo. `arm_watchdog` **se completa, no se retira**.
  2. ❌ **Cae:** *"cuarta razón del **enum**"*. El canónico **no tiene enum de razones**: `.abort(reason)` toma un
     **valor abierto** —`'interrupt'` (`handlePromptSubmit.ts:331`, `print.ts:1861`), `'sibling_error'`
     (`StreamingToolExecutor.ts:362`), `DOMException TimeoutError` (`mcp/client.ts:519`)— que viaja en
     `signal.reason`. **Cerrar el vocabulario a un enum es una divergencia**, y si se adopta hay que declararla
     como tal (`L10`), no venderla como homologación. Esto **corrige `CG-SIG-1`**, que asume enum cerrado.
  3. ❌ **Cae:** la composición. El canónico **no** hace que un watchdog externo llame a `interrupt()` sobre el
     scope; **compone la fuente dentro de la señal** y devuelve un `cleanup()` que libera timer y listeners. La
     firma correcta para B es del tipo `combine(scope, timeout_s=...) -> (scope_hijo, cleanup)`, con el
     **`cleanup` obligatorio** — el propio canónico documenta por qué (`AbortSignal.timeout` acumula ~2,4 KB por
     llamada bajo Bun hasta que vence).
  4. ⚠ **Y cae mi «corroboración».** Cité `01·§1.1` (*"el canónico cancela por abort, no por timeout per-task"*)
     como apoyo independiente. Es **verdad a medias y la usé como si fuera entera**: cierto que no hay campo
     `timeout_seconds` **per-task**, falso que el canónico no convierta tiempo en abort — lo hace **por
     operación** (hook, request MCP). Corregido también en `01·§1.1` por `CAT-h10`.
  **⇒ Pendiente de EJECUCIÓN reformulado:** escribir en `SEAMS §S24` **esta** decisión (fusión en la señal +
  `cleanup`), no la anterior.
- **`SEAMS §S4·A2.5`** — *"`cancel`/`runtime_id` NO realizados en el skeleton (cancel→08·signals)"*. El `cancel` del
  skeleton es el **nivel agent** de `CG-SIG-9`, que en el runtime local **ya opera** (`runtime.py:381-387` vía
  `CancelledError`); lo que el skeleton debe exponer es `interrupt(level=...)` (`CG-SIG-7`), no un `cancel` nuevo.

### 2.4 DEUDA-B (higiene interna del runtime, NO A↔B — L10)
> ⚠ **ALCANCE CORREGIDO por `R-1`/`RV-6` (2026-07-28), bajado a este documento en `A-CIERRE·P4″` (`CAT-h10`).**
> La redacción anterior de `DB-SIG-1..3` ordenaba *"borrar `SignalBus`/`SignalType`/`SignalHandle`"* y *"borrar
> `signals/` entero"*. **Eso destruye un símbolo vivo.** `RV-6` prohíbe escribir una entrada BORRAR a nivel de
> fichero/módulo: se escribe a nivel de **símbolo**, con la lista de los que **SOBREVIVEN**. `R-1` cerró auditando
> las 12 entradas BORRAR de `DEUDA-B §3.A` y **4 de 11 (36 %)** habrían destruido código vivo o roto el paquete;
> ésta es la misma clase de defecto, replicada en un destilado que `R-1` no barrió.

- **DB-SIG-1 · retirar la maquinaria del `SignalBus` — a nivel de SÍMBOLO** (S16/FIND-SIG1, `SR1`) — abstracción
  **HUÉRFANA** (verificado en-ciclo: `SignalBus`/`SignalHandle`/`SignalHandler` referenciados SÓLO por
  `tests/test_signal_bus.py` + `tests/test_signals_homologation.py` + 1 comentario en `test_runtime_e2e.py`; **cero
  producción**) que además **conflaciona** las dos cascadas que el canónico separa.
  **MUEREN** (espejo exacto de `DEUDA-B §3.A·DB-03`): `_Node` (`bus.py:11-14`) · `SignalHandle` (`bus.py:17-27`) ·
  `SignalBus` (`bus.py:29-87`) · `register_handler` (`bus.py:89-96`, = DB-SIG-2) · la semántica
  `RESUME`-limpia-señal (`bus.py:68-69`, = DB-SIG-3) · `SignalHandler` (`protocols.py:11-14`) · el
  `signals/__init__.py` del paquete.
  **SOBREVIVE: `SignalType`** — se **reubica** al **mismo módulo de vocabulario `T1`** al que `DB-01` manda
  `AgentMode` y `DB-25` manda `stop_reason`. No es un rescate sentimental: `PAUSE`/`RESUME` es **la única traza
  nominal de pausa/reanudación en todo el runtime**, y borrarla antes de que exista su sustituto deja a `H-3` sin
  vocabulario (ver `DB-h2` abajo).
  **Colateral declarado** (`DEUDA-B §3.A·DB-03`): `signals/__init__.py` pasa de exportar 4 símbolos a **1**;
  `tests/test_signal_bus.py` (13 tests) **se retira entero**; los xfails `FIND-SIG1` (`test_signals_homologation.py:63`)
  y `FIND-SIG5` (`:148`) **se RETIRAN, NO se ponen en verde** — un xfail que codifica un gap que dejó de existir no
  «pasa»: deja de tener objeto; el docstring de `tests/test_runtime_e2e.py:9` se reescribe.
  Función legítima (árbol de cascada) **fusionada** en `AbortScope` (in-turn) + registry (background, ya existe).
  Tercer huérfano del patrón → **`B-orphans`** junto a `modes/`/`observer/`. NO deuda A↔B (el canónico tampoco tiene
  un SignalBus). **prueba:** `test_no_orphan_signalbus_in_real_path`.
- **DB-SIG-2 · `register_handler` muerto** (S17/FIND-SIG5, `SR1`) — `bus.py:89-96` guarda handlers en `_handlers` pero
  `send()`/`_apply()` **nunca invocan `handle_signal`** (verificado en-ciclo); el `SignalHandler` Protocol
  (`protocols.py:11-14`) no lo usa nadie. Extension point muerto → **cae con el bus** (DB-SIG-1). **xfail existente
  que lo codifica:** `FIND-SIG5` (`test_signals_homologation.py:148`) → se retira con el símbolo.
- **DB-SIG-3 · `PAUSE`/`RESUME` mal ubicado — muere la SEMÁNTICA, no el enum** (S18/FIND-SIG6, `SR1`) —
  `bus.py:68-69` `RESUME` limpia la señal (`node.signal = None`, verificado), lo que **contradice** la
  irreversibilidad one-shot del abort. La pausa SÍ existe en el canónico pero a nivel de **lifecycle de task**
  (`Task.ts:53 totalPausedMs`, contabilidad de backgrounding), NO como estado del abort. **Acción:** eliminar la
  rama `RESUME` del `send`/`_apply` (muere con el bus) y **reubicar `SignalType`** al módulo de vocabulario `T1`;
  si el runtime quiere pausa como capacidad, su hogar es **04/05** (lifecycle, con `totalPausedMs` como espejo).
  NO deuda A↔B. **xfail existente:** `FIND-SIG6` (`test_signals_homologation.py`) → se retira.
- **⚠ `DB-h2` · PRECONDICIÓN DE EJECUCIÓN de DB-SIG-1..3** (`DEUDA-B §5·DB-h2`, restituida aquí por
  `A-CIERRE·P4″·P4-08-3`) — *"borrar `signals/` tiene una precondición no escrita. `SignalType.PAUSE/RESUME` es la
  única traza nominal de pausa/reanudación, y **H-3** (`resume` no existe) sigue sin cableado desarrollado. Borrar
  antes de que H-3 tenga hogar elimina el vocabulario sin sustituto."*
  **`H-3`** (`DEUDA-A §H-3`): `00-INTEGRADORES §1.3` declara como firma que el integrador consume
  `LocalAgentRuntime.resume(agent_id, message)`; **verificado leyendo `execution/local/runtime.py` 1→EOF, ese método
  NO existe** — la superficie pública es `startup`/`shutdown`/`dispatch`/`stream`/`status`/`cancel`/`result`.
  ⇒ **ORDEN OBLIGATORIO:** (1) `H-3` recibe hogar y cableado desarrollado en `05·execution`; (2) `SignalType` se
  reubica al vocabulario `T1`; (3) **sólo entonces** se ejecutan DB-SIG-1/2/3. Invertir el orden es una pérdida de
  vocabulario sin sustituto, que es exactamente lo que `RV-6` existe para impedir.
- **LAT-SIG1 · `ModelRequest.stop` definido-no-consumido** (destapado por la lectura EOF de `models/protocol.py`, que
  el 1er intento por tramos había omitido) — `models/protocol.py:11-18` declara un `ModelRequest` frozen **con campo
  `stop: asyncio.Event`** (y `thinking_budget`), exportado en `models/__init__.py:1,4`, pero **ningún consumidor de
  producción lo construye**: el loop llama `complete(messages, tools, *, stop=ctx.stop, ...)` por kwarg
  (`agent_loop.py:235`), nunca arma un `ModelRequest`. Verificado en-ciclo por grep prod-vs-test: `ModelRequest`
  referenciado SÓLO por `models/__init__.py` (export) + `tests/test_model_caller_protocol.py`. Estructura
  **definido-no-consumido** con su `stop` inerte — hermana de `to_llm`/`LAT-EXEC1`/`LAT-HOOK1`.
  **Acción: BORRAR** — ⚠ **la binaria estaba ya cerrada aguas arriba y esta ficha la reabría** (corregido en
  `A-CIERRE·P4″·P4-08-11`, `D-06·1`: una binaria que la evidencia leída ya resuelve **se ejecuta**, no se eleva).
  `DEUDA-B §7.3`/`§3.A·DB-10(b)` decide **BORRAR ahora**, y con razón material: `ModelRequest` declara un
  `thinking_budget` que el motor **no soporta** y **le faltan** `system_sections`/`system_override` que el motor
  **sí usa** ⇒ "unificar el request en el tipo" no es una alternativa viable, sería reconstruirlo. **NO deuda A↔B**
  (extensión B sin contraparte canónica, anti-padding L10); DEUDA-B de higiene. La primitiva REAL de plumbing del
  abort al modelo es el kwarg `complete(*, stop=)` (`protocol.py:28-37` + `caller.py:146-159/188-190`), NO `ModelRequest`.
- **Nota anti-padding (L10):** el `parent_stop`-no-threadeado (`runtime.py:201`, `_build_child:210` sin `stop=`;
  `tools/native/agent.py:89-105` arma `ForkPolicy(propagate_abort=True)` + `ForkContext` **sin** `parent_stop`,
  verificado EOF en-ciclo) NO es huérfano ni deuda A↔B — es **delegación por diseño** (el `abortController` canónico
  también se arma externamente, UI `useCancelRequest`). Es la **costura de arming del integrador** (OI-SIG-B), no una
  cañería a medias. Verificado en-ciclo leyendo `_run_loop`/`agent.py`/`caller.py` 1→EOF: el kill-de-task SÍ opera; lo
  latente-en-standalone es SÓLO el `ctx.stop` in-turn.
- **Observación EOF (mecánica correcta, ⚠ PREMISA CORREGIDA en `A-CIERRE·P4″`):** `caller.py:204-245` (mapeo del
  stream) **no envuelve el `async for` en try/except de abort** → un corte de `agentic_models` por `signal`
  (`APIUserAbortError`) propagaría como Exception genérica hasta `runtime.py:388` (`fail`), NO por la rama
  `CancelledError` (381) ni como resultado de abort tipado.
  **Lo que esta observación daba por supuesto y es falso:** que el corte llega a producirse. **No llega** — el
  provider nunca aborta (`CG-SIG-10`), luego **no hay `APIUserAbortError` que envolver**. El documento estaba a una
  pregunta de distancia del defecto de `S2` —*¿y quién lanza esa excepción?*— y no la hizo. Se conserva la
  observación porque su mecánica sigue siendo válida **una vez `CG-SIG-10` esté reparado**: entonces sí hará falta
  el `try/except` para traducir el corte a resultado de abort tipado (liga S11→`07·EvR4`).

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05)
Con **capacidad observable · origen (costura del base) · firma que consume · cableado en el integrador · orden ·
criterio de aceptación**. El eje PRIMARIO = el **CONTRATO BASE COMÚN** (must-be de TODO integrador agéntico).

- **OI-SIG-A · Disparar el abort** *(contrato base común — must-be universal)* — **capacidad:** todo integrador DEBE
  proveer el disparo de cancelación (el runtime deliberadamente no lo dispara: S20 ✅). **origen:** S14/S13 (`useCancelRequest`
  + `interrupt()`). **firma:** el integrador llama `runtime.interrupt(task_id, level, reason)` / `abort.interrupt(...)`;
  implementa la **escalera de prioridad** (task activa→cancelar+vaciar cola de confirmación · idle con cola→pop ·
  fallback) y la distinción **Ctrl+C** (siempre cancela) vs **Escape** (cede a mode-exit/navegación). **cableado:**
  `agentic_code` = keybinding en terminal (espejo `handleCancel`, escalera + `killAgents` con doble-pulsación);
  `agentic_assistant` = botón/evento de cancel del front → SSE/websocket → `runtime.interrupt`. **orden:** tras
  CG-SIG-7 (`interrupt()` público). **aceptación:** Ctrl+C (o su análogo) corta el turno en vuelo; el runtime no conoce
  el medio del disparo.
- **OI-SIG-B · Armar la primitiva in-turn (`ctx.abort`)** *(contrato base común)* — **capacidad:** el standalone NO
  puebla `ctx.stop`/`ctx.abort` con un scope vivo; el integrador lo siembra para habilitar la cancelación cooperativa
  in-turn (el kill-de-task funciona sin ello). **origen:** precisión de cableado del tracker (arming) + seams verificados
  en-ciclo. **firma:** `context/adapters.py:tool_use_context_from_session(*, stop=...)` (→`ToolUseContext(stop=...)`,
  verificado `adapters.py:15/44`) y/o `root_context_modifier(ctx, task)` (`runtime.py:329-330`) siembran un `AbortScope`
  raíz; la tool Agent threadea `parent_stop`/scope al fork. **cableado:** `agentic_code` = arma un scope por REPL turn;
  `agentic_assistant` = arma un scope por request del bff y lo asocia al task_id para el cancel del front. **orden:**
  junto a `AbortScope`. **aceptación:** con el integrador armando el scope, un `abort.work` mid-turn detiene el loop
  cooperativamente (checks 173/186); sin armar, sólo opera el kill-de-task (ya funciona).
- **OI-SIG-C · Renderizar/entregar la interrupción al usuario** *(contrato base común, realización específica)* —
  **capacidad:** presentar el mensaje de interrupción (`createUserInterruptionMessage`, gateado por `reason!='interrupt'`)
  y las notificaciones de kill de agentes background (`killAllAgentsAndNotify`→notificación agregada al modelo).
  **origen:** S10 + el `_notify`/`NotificationSink` del kill (verificado `runtime.py:385-386/294-304`). **firma:** el
  integrador consume el `reason` del resultado terminal (S11→07) y las `BackgroundNotification` drenadas; renderiza al
  medio. **cableado:** `agentic_code` = mensaje en terminal; `agentic_assistant` = evento cancel por SSE + inbox de
  notificaciones. **orden:** tras S11 (07·EvR4). **aceptación:** un abort de usuario produce el mensaje correcto (o su
  omisión cuando `reason=='interrupt'`); un kill de agente background notifica al usuario.

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor (lema de la etapa):**
> De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda; ninguna categoría
> se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar —o colocado sin
> abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — una fila por finding (26 = grid S1-S25 · 25 + SIG13 · 1)

`ev.` = evidencia: `T`=tracker-leído · `E:archivo:L`=ensamblador abierto EN ESTE CICLO. `det.` = detalle L05: `sí`=6
campos en §2.3/§2.5 · `N/A`=DEUDA-B/homed-fuera/⛔.

| ID | TIER | destino | cara | ev. | det. | id-nota |
|---|---|---|---|---|---|---|
| S1 | T2-BASE-MECANISMO | `AbortScope` (de `tool_use.py:47`) | base | E:`tool_use.py:47` (`stop: asyncio.Event\|None`) | sí (CG-SIG-1) | ejecución (efímero: turno) |
| S2 | T1-MOTOR | **CG-SIG-10** (08↔16) | base | E:`caller.py:151,166,188-190` + **censo de los 8 providers de `agentic_models`** (`.aborted`; `is_set()`=0) | sí (CG-SIG-10) | ⚠ **✅→❌** (`A-CIERRE·P4″`) |
| S6 | T2-BASE-MECANISMO | loop (`abort.work`) | base | E:`agent_loop.py:173,186` | sí (✅) | — |
| S7 | T2-BASE-MECANISMO | dispatcher | base | E:`dispatcher.py:54-55` | sí (CG-SIG-4) | — |
| S20 | T3-INTEGRADOR | INTEGRADOR (OI-SIG-A/B) | integrador | E:grep `.set()` prod=0 (en-ciclo) | sí (OI-SIG-A) | ejecución |
| S3 | T1-CONTRATO+T2-BASE | `AbortScope.reason` | base | E:`tool_use.py:47` (Event sin reason) | sí (CG-SIG-1) | — |
| S4 | T2-BASE-MECANISMO | `AbortScope.child()` | base | E:`fork/__init__.py:80-83` (MISMO Event) | sí (CG-SIG-2) | ejecución (fork) |
| S5 | T1-CONTRATO (→09) | `ToolProtocol.interrupt_behavior` | base | E:`tools/protocol.py:51-61` (sin campo) | sí (CG-SIG-3) | — |
| S8 | T2-BASE-MECANISMO | `AbortScope` sibling/tool | base | E:`dispatcher.py:54-55` (sólo pre-exec) | sí (CG-SIG-4) | ejecución |
| S21 | T1-CONTRATO | `ToolResult.aborted` rico | base | E:`tools/protocol.py:47-48` (string plano) | sí (CG-SIG-5) | — |
| S10 | T1-CONTRATO | `AbortScope.reason`+render (OI-SIG-C) | base | E:`agent_loop.py`(sin user-interrupt-msg) | sí (CG-SIG-5) | — |
| S9 | T2-BASE-MECANISMO | →02·LR5 | base | E:`agent_loop.py:319-323` (pairing dispatch) | N/A (homed 02) | — |
| S24 | T2-BASE-MECANISMO | →02 (motor#2) | base | T | N/A (homed 02) | — |
| S22 | T2-BASE-MECANISMO | `AbortScope`+→07·EVT7 | base | T (deriva S5) | sí (CG-SIG-6) | — |
| S23 | T2-BASE-MECANISMO | dispatcher (IDs vivos) | base | E:`dispatcher.py` (sin tracking) | sí (CG-SIG-6) | ejecución |
| S11 | T1-CONTRATO | →07·EvR4 + `B-usage` | base | E:`runtime.py:380/394` (`run()→None`) | N/A (homed 07) | — |
| S12 | T1-MOTOR | **CG-SIG-10** (08↔16) | base | E:`model_types.py:100` (`signal: Any`, comentario RV-5) + censo de providers | sí (CG-SIG-10) | ⚠ **🔀→❌** — 16 ya dictaminó en contra (`FIND-MODELS4`); no era delegable |
| S13 | T2-BASE-MECANISMO | `AbortScope.interrupt()` | base | E:grep `interrupt(` runtime/loop=0 | sí (CG-SIG-7) | — |
| S14 | CLI-ONLY/INTERFAZ+T3 | INTEGRADOR (OI-SIG-A) | integrador | T (`useCancelRequest.ts` React) | sí (OI-SIG-A) | ejecución |
| S16 | DEUDA-B (borrar) | retirar **por símbolo** (`RV-6`) → `B-orphans`; `SignalType` sobrevive | base | E:grep prod-refs=0 (sólo tests, en-ciclo) | N/A (DEUDA-B) | ⚠ alcance corregido `R-1` |
| S17 | DEUDA-B (borrar) | cae con el bus | base | E:`bus.py:89-96` (`send` no invoca handle) | N/A (DEUDA-B) | — |
| S18 | DEUDA-B (borrar la semántica) | muere `RESUME`-limpia-señal; `SignalType` **se reubica** a vocabulario `T1`; pausa→04/05 | base | E:`bus.py:68-69` (`RESUME`→signal=None) | N/A (DEUDA-B) | ⚠ precondición `DB-h2` (tras `H-3`) |
| S19 | T2-BASE-MECANISMO | →06·hooks | base | E:`agent_loop.py:301-306` (payload sin stop) | N/A (homed 06) | — |
| S15 | T2-COSTURA+⛔ | `AbortScope.on_abort` + 11·mcp | base | T (SR3 nuevo) | sí (CG-SIG-8) | ejecución |
| S25 | T2-BASE-MECANISMO | →06·HR2 | base | T | N/A (homed 06) | — |
| SIG13 | T2-BASE-MECANISMO | `AbortScope.work`/`.agent` (05·EXEC12) | base | E:`runtime.py:381-387` (kill vía CancelledError) | sí (CG-SIG-9) | ejecución (turno vs vida) |

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../08-signals.md`?** — **Sí**, líneas 1→441 (cabecera + contrapartes leídas A+B + detalle
   `StreamingToolExecutor`/`useCancelRequest` + tesis arquitectural "dos cascadas" + tabla S1-S25 + recuento +
   §Hallazgos FIND-SIG1-13 + §Gaps GAP-SIG1-3 + cabos/relaciones + estado + §Plan SR1-SR5 + re-visita gate-11
   2026-07-19 con mini-ledger de consumidores + PRECISIÓN de cableado arming + ledger de lectura + §nota de honestidad
   + 4 preguntas + VEREDICTO).
2. **¿Reconcilia el conteo?** — findings en `../08-signals.md`: tabla feature-by-feature **S1-S25 = 25 filas** (`S15`
   doble-marca 🔀/❌ → contada **1**, igual que el recuento del tracker "25 filas; S15 contada 🔀") **+ SIG13** (finding
   de §Hallazgos sin fila-S, de la re-audit 04·modes) = **26 filas de ledger**; colocadas = **26**; sin colocar =
   **0**. Los `FIND-SIG1-13`/`GAP-SIG1-3` = capa de **resumen nombrado** sobre las filas-S; `SR1-SR5` = **remediación
   referenciada** (espejo de 06·HR/10·R) — no re-contados. ✅
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador (sin grep)?** — **Sí, re-abierto EN ESTE CICLO
   contra el runtime real** (no heredado del gate-11 del tracker):
   - ~~**✅ S2 (propagación al modelo)**~~ → ⚠ **❌, corregido en `A-CIERRE·P4″`.** La cadena que se siguió era
     `agent_loop.py:227` (`complete_kwargs={"stop": ctx.stop, ...}` **incondicional**) → `caller.py:188-190`
     (`if stop is not None: opts = replace(opts, signal=stop)`) → `agentic_models.StreamOptions.signal` — y **se
     paró ahí, en el punto de ENTREGA**. Al seguir un paso más, hasta el **consumidor**: los 8 providers gatean en
     `getattr(signal,"aborted",False)` y `caller.py:151/166` entrega un `asyncio.Event`, que no tiene `.aborted`
     ⇒ **el corte no ocurre nunca**. **Regla que este par deja escrita:** en una fila `T1-MOTOR`/`T1-CONTRATO` cuyo
     consumidor vive **en otro paquete**, el cableado termina en el CONSUMIDOR, no en el punto de entrega. Ver
     `CG-SIG-10`.
   - **✅ S6 (check pre-modelo)** → `agent_loop.py:173` (`return` pre-turno) + `:186` (`break` por turno), ambos
     `if ctx.stop and ctx.stop.is_set()`.
   - **🟡 S7 (check pre-exec tool)** → `dispatcher.py:54-55` (`if ctx.stop and ctx.stop.is_set(): return ToolResult.aborted(name)`).
   - **🟡 S9 (pairing)** → `agent_loop.py:319-323` (parea `role:"tool"` por `tool_call_id` 1-a-1 por cada tool).
   - ~~**🔀 S12 (corte API delegado)**~~ → ⚠ **❌, corregido en `A-CIERRE·P4″`.** Se marcó `🔀` "delegado, verificar
     en 16" **sin comprobar que 16 ya había verificado y fallado** (`FIND-MODELS4`, vía `DEUDA-A §1.2(a)`;
     `SEAMS §S2` = `existe-roto`). **Segunda regla del par:** un `🔀` no puede delegar en una categoría que ya
     dictaminó en contra — eso no es homar con destino, es enterrar.
   - **🔀 S16 (`SignalBus` huérfano)** → grep repo-wide EN ESTE CICLO: `SignalBus`/`SignalType`/`SignalHandle`/
     `SignalHandler` en prod = **0** (sólo `tests/test_signal_bus.py`, `tests/test_signals_homologation.py`, 1 comentario
     en `test_runtime_e2e.py`). FIND-SIG1 confirmado por cableado.
   - **🔀 S18 (`RESUME`)** → `bus.py:68-69` (`if signal == SignalType.RESUME: node.signal = None`).
   - **✅ S20 (nadie setea abort)** → grep `.set()`/`stop.set` en prod = **0**; el único `stop = asyncio.Event()` es
     `fork/__init__.py:83` (rama de aislamiento `propagate_abort=False`, Event fresco nunca `.set()`).
   - **kill-de-task (cascada background, opera)** → `runtime.py:381-387` (`except asyncio.CancelledError:` → `kill` +
     `_fire_stop` + `_notify` + `raise`); `runtime.py:187-188` (`cancel`→`registry.kill`).
   - **arming (integrador, no standalone)** → `adapters.py:15/44` (`stop=` seam) + `runtime.py:329-330`
     (`root_context_modifier`) + `runtime.py:201` (`.fork(...)` **sin** `parent_stop`) + `:210` (`ToolUseContext(...)`
     **sin** `stop=`).
   Las **ausencias** afirmadas (S3/S4/S5/S8/S10/S13/S21/S22/S23/S17/S19/S25) se confirmaron **leyendo la fuente** donde
   el campo/punto NO está: `tool_use.py:47` (Event binario sin reason), `fork:80-83` (MISMO Event, sin direccionalidad),
   `tools/protocol.py:47-61` (`aborted` string plano + `ToolProtocol` sin `interrupt_behavior`), `bus.py:89-96`
   (`register_handler` sin `handle_signal`), `agent_loop.py:301-306` (payload de hook sin `stop`/reason) — ausencia
   **leída en fuente**, no grep. Los homed-fuera puros (→02/06/07/16) van con destino nombrado y su cableado se verifica
   en su categoría-hogar (L07).
4. **¿La cara integrador quedó al MISMO detalle que la base?** — **Sí**: §2.5 desarrolla **3** obligaciones (OI-SIG-A
   disparar el abort · OI-SIG-B armar la primitiva in-turn · OI-SIG-C renderizar/entregar la interrupción) con los 6
   campos L05; ningún finding integrador (S14/S20) cerrado con "→ integrador" a secas. El eje PRIMARIO (contrato base
   común: TODO integrador DEBE disparar y armar la cancelación — el runtime deliberadamente no lo hace) está explícito.
5. **¿Doble filo (L10)?** — **Sí**. **No se infla deuda:** el `parent_stop`-no-threadeado NO se cuenta como
   huérfano/deuda A↔B — es **delegación de arming por diseño** (el `abortController` canónico también se arma en la UI);
   y 08 **no fabrica una battery** para llenar la casilla (la cancelación es primitiva del base, no paquete opcional).
   El borrado del `SignalBus` es **DEUDA-B interna** (huérfano sin contraparte A), NO deuda A↔B. **No se oculta deuda:**
   los ❌ reales del **seam de cancelación** (reason CG-SIG-1, árbol CG-SIG-2, interrupt_behavior CG-SIG-3, en-vuelo
   CG-SIG-4, sintéticos CG-SIG-5, interrumpible CG-SIG-6, interrupt() CG-SIG-7, cleanup CG-SIG-8, dos-niveles CG-SIG-9)
   se mantienen como CORE-GAP A↔B con remediación desarrollada — **NO disfrazados de 🔀** (el tracker marca S16/S18 🔀
   por ser "código presente pero divergente"; la SEPARACION los re-clasifica honestamente: S16/S18 = DEUDA-B-borrar,
   no CORE-GAP, porque su presencia es huérfana; los ejes ausentes S3/S4/S5/S8/… = ❌ CORE-GAP, no 🔀).

### 3.3 §Honestidad
- **CORRECCIÓN DE SOBRE-DECLARACIÓN (gate del usuario "¿EOF en todos?", L03/L04):** la **1ª pasada de este ciclo NO
  hizo EOF en todos los archivos** — declaración honesta antes de corregir. EOF real 1→EOF en la 1ª pasada: 9 archivos
  (`signals/bus.py` 96 · `protocols.py` 14 · `__init__.py` 4 · `context/tool_use.py` 70 · `fork/__init__.py` 96 ·
  **`runtime.py` 435, el más grande L08** · `dispatcher.py` 84 · `tools/protocol.py` 61 · `adapters.py` 85). **Leídos
  por TRAMOS (no EOF) en la 1ª pasada:** `agent_loop.py` (160-259 + 288-352; **saltados 1-159 y 260-287**, siendo 352
  el 2º archivo más grande y ensamblador — fallo L08/L09) · `caller.py` (140-199; saltados 1-139 y 200-245). **No
  abiertos en la 1ª pasada** (referenciados por el tracker): `models/protocol.py` · `tools/native/agent.py`.
- **HUECO CERRADO en-ciclo (2ª pasada, tras el gate):** se leyó a **EOF** lo que faltaba — `agent_loop.py` 1-159 +
  260-290 (completa 1→352) · `caller.py` 1-139 + 199-245 (completa 1→245) · `models/protocol.py` 1→37 ·
  `tools/native/agent.py` 1→119. **Reconciliación: CERO cambios de clasificación** en las 26 filas — los tramos
  omitidos confirmaron (no contradijeron) las clasificaciones: `agent_loop.py:1-159` no toca `ctx.stop` (init/pool/
  recall/deferred, sin lógica de abort); `260-287` = ensamblado de `tool_calls` POST-stream + dispatch serial `for tc`
  → **confirma S8/S23** (sin sibling/tool-child, sin tracking de IDs en vuelo) y **S9** (pairing sólo a nivel dispatch);
  `caller.py:1-139/200-245` = round-trip + mapeo de eventos, sin lógica de abort (el `reason` del `done` 224-227 es
  stop-reason del modelo, NO reason de abort → refuerza S3/S11). **HALLAZGO NUEVO que sólo la lectura EOF destapó:**
  **LAT-SIG1** (`ModelRequest.stop` definido-no-consumido, §2.4) — invisible a la lectura por tramos, es exactamente el
  tipo de omisión que L08 predice ("la superficialidad migra a los intersticios"). Es DEUDA-B B-interna (no altera el
  conteo de 26 findings-del-tracker; se registra como costura latente, espejo de LAT-HOOK1/LAT-EXEC1).
- **Ledger de lectura FINAL (post-cierre, todos EOF 1→fin):** `signals/bus.py` 1→96 · `signals/protocols.py` 1→14 ·
  `signals/__init__.py` 1→4 · `context/tool_use.py` 1→70 · `execution/fork/__init__.py` 1→96 ·
  `execution/local/runtime.py` 1→435 · `tools/dispatcher.py` 1→84 · `tools/protocol.py` 1→61 · `context/adapters.py`
  1→85 · **`loop/agent_loop.py` 1→352 íntegro** · **`models/caller.py` 1→245 íntegro** · `models/protocol.py` 1→37 ·
  `tools/native/agent.py` 1→119. + grep de completitud prod-vs-test (`SignalBus`=0 prod · `.set()`=0 prod · `.fork(`=
  sólo `runtime.py:201` sin `parent_stop` · `ModelRequest`=sólo export+test). Confirmaron FIND-SIG1/3/5/6 + arming +
  kill-de-task + LAT-SIG1 **por cableado**, no por la tabla del tracker.
- **Lo NO re-leído íntegro en-ciclo** (declarado, no presentado como leído): la contraparte canónica A
  (`utils/abortController.ts` 99, `StreamingToolExecutor.ts` 530, `useCancelRequest.ts` 276, `toolExecution.ts` tramos
  abort, `Task.ts`/`Tool.ts`/`query.ts`/`QueryEngine.ts` anclas) — su lectura íntegra ocurrió en la 1ª pasada + gate-11
  del tracker (2026-07-19); aquí la SEPARACION **re-clasifica findings ya destilados** bajo los ejes B, no re-audita A.
  Los sitios de ciclo homed-fuera (`02·LR5` pairing, `02` motor#2 streaming, `06·HR2` isInterrupt, `07·EvR4` resultado
  terminal, `16` corte HTTP) se **referencian** con destino; su cableado se verifica en su hogar (L07), no se re-abren aquí.
- **Recuento de estados tras la corrección de `A-CIERRE·P4″`** (declarado, porque cambia respecto al del tracker):
  el tracker daba `✅3 · 🟡3 · 🔀4 · ❌14 · ⛔1` = 25. Con `S2 ✅→❌` y `S12 🔀→❌` queda
  **`✅2` (S6·S20) · `🟡3` (S1·S7·S9) · `🔀3` (S16·S18·S15) · `❌16` · `⛔1` (S14) = 25**, +`SIG13` = **26**.
  Es el **único** cambio de estado del documento y **no** procede del segundo salto de destilación: procede de
  abrir el consumidor del seam en `agentic_models`, que ninguna de las dos caras había abierto.
- **Conteo de grid = decisión de método declarada:** unidad = fila de la tabla feature-by-feature del tracker (espejo
  de 06/10). `S15` (doble-marca 🔀/❌) se cuenta **1 vez** como el recuento del tracker. `SIG13` (finding de §Hallazgos
  sin fila-S, surgido de la re-audit de 04·modes) se coloca **explícito** (no plegado, L07: su único hogar es aquí) →
  26. Los `FIND-SIG*`/`GAP-SIG*`/`SR*` no se re-cuentan (capa de resumen/remediación).
- **Adjudicación de la discrepancia de conteo con el tracker (`c28`, `A-CIERRE·P4″`):** el ledger de lectura del
  tracker (:391) cuenta `context/adapters.py` = **86 L**; este documento cuenta **85**. Medido: `wc -l` = **85**
  ⇒ **el tracker está mal, este documento acierta**. Se nombra explícitamente porque una discrepancia de conteo sin
  adjudicar obliga al siguiente lector a re-medirla.
- **Evidencia de suite heredada del tracker (`§Estado`, restituida por `A-CIERRE·P4″·P4-08-6`)** — es la línea base
  contra la que Fase B medirá regresión: `test_signals_homologation.py` = **6 passed + 7 xfailed strict**, y los
  xfail codifican **SIG1 · SIG2 · SIG3 · SIG4 · SIG5 · SIG6 · SIG10**. Suite global **582 passed · 3 skipped ·
  40 xfailed**; lint verde (ruff/mypy/bandit). **Los siete xfails tienen destino declarado, no sólo los cuatro que
  la 1ª redacción citaba:** SIG2→`CG-SIG-1` · SIG3→`CG-SIG-2` · SIG4→`CG-SIG-3` · SIG10→`CG-SIG-5` (los cuatro **se
  ponen en verde** al remediar) · **SIG1→`DB-SIG-1` · SIG5→`DB-SIG-2` · SIG6→`DB-SIG-3` (los tres se RETIRAN, NO se
  ponen en verde** — su gap deja de existir, no se repara). La distinción es ejecutable y la 1ª redacción la perdía.
- **Re-clasificación de tier vs el tracker (transparente):** el tracker ancla el grueso de `AbortScope` en
  `DEUDA-B-transversal.md §B-signals` (nombre heredado pre-SEPARACION). Bajo la lente B, **la mayor parte NO es tier
  DEUDA-B sino CORE-GAP A↔B** (reason/árbol/interrupt_behavior/interrupt()/niveles/interrumpibilidad — el canónico los
  tiene, el runtime no); sólo el **borrado del huérfano** (`SignalBus`+`register_handler`+`PAUSE/RESUME`) es DEUDA-B de
  tier. Corregido aquí sin tocar el tracker (que sigue siendo la hipótesis de partida, L11).

### 3.4 VEREDICTO

> ⚠ **VEREDICTO REESCRITO en `A-CIERRE·P4″` (2026-07-29).** El anterior decía **`✅ NADA PENDIENTE → A3·04·modes`**
> y **era inválido por la propia `L04`** («Sin escotilla»: *si hay ≥1 pendiente de VERIFICACIÓN, el veredicto NO
> puede ser `✅ NADA PENDIENTE`*). Se conserva su argumento porque sigue siendo cierto **en lo que afirmaba** —el
> hueco de lectura de la 1ª pasada se cerró y las 26 filas se reconciliaron sin cambio de clasificación—; lo que
> **no** era cierto es la conclusión: cerrar el hueco de lectura **dentro** del paquete no bastaba, porque el
> defecto vivía **en la frontera del paquete**.

**⛔ RECONCILIADO, NO CERRADO.**

**Lo que sí queda cerrado y probado:** las 26 filas colocadas sin residuo (`§3.2·2`); las 9 remediaciones
`CG-SIG-1..9` con los 6 campos `L05` —desarrollo que el tracker explícitamente **no** hizo (`SR2`: *"aquí se
referencian; no se re-desarrollan"*)—; la cara de integrador `OI-SIG-A/B/C` creada de cero; `LAT-SIG1`; el hueco
de lectura de la 1ª pasada (`agent_loop.py` 1→352 y `caller.py` 1→245 íntegros).

**Pendientes de VERIFICACIÓN: CERO.**

> ⚠ **El único que quedaba se cerró leyendo el canónico, no elevándolo (`D-08`, 2026-07-29).** Decía: *«la forma
> del contrato de `CG-SIG-10` es binaria con dos ramas defendibles ⇒ `D-06·3`, la decide 16 como dueño del tipo».*
> **Era falso que hubiera dos ramas.** El canónico dicta una —`AbortSignal` nominal con `.aborted` (119 usos),
> `addEventListener('abort')` (26) y `.reason` propagable— y la rama (b) (`is_set()`) es **incapaz** de sostener
> `CG-SIG-1`/`CG-SIG-7`/`CG-SIG-8`. Ejecutado por `D-06·1`. La misma lectura destapó **`CG-SIG-11`** (la señal
> tiene que llegar al **cliente HTTP**, no al bucle del provider) y **refutó la decisión del watchdog** que este
> mismo documento había emitido razonando en vez de leyendo (ver `§2.3 · SEAMS §S24`). **Coste de la lectura: 6
> archivos del canónico.** Es la medida exacta de lo que valía la escotilla `D-06·3` que había abierto.

**Pendiente 2 — PAGADO el mismo día, no arrastrado (`D-07·1`).** Decía: *«el alcance real del daño de `CG-SIG-10`
sobre `01`/`02` no lo he verificado y no lo declaro verificado»*. Se abrieron **`SEPARACION/01-contracts.md`
1→164** y **`SEPARACION/02-loop.md` 1→318** íntegros. **Resultado: 4 celdas tocadas, 1 de ellas un `✅` falso.**

| doc | celda | antes | ahora | por qué |
|---|---|---|---|---|
| `02` | **`G5`** | **✅** «`interrupt()` ⇒ abort; vía cooperativa abierta» | **🟡** (`02·§2.6·I6`) | homologaba la **llamada**, no el **efecto**: el canónico aborta el HTTP en vuelo, B sólo corta en frontera de turno y entre tool calls |
| `02` | `F6` | 🟡 «el loop no re-chequea entre tools **ni mid-stream**» | 🟡 + **causa** | el mid-stream **no es alcanzable desde el loop**; listarlo junto al chequeo entre tools hacía parecer local un arreglo que vive en `16` |
| `01` | `CTR-15` | 🟡 con rama abierta «completar **o retirar si 08 cubre la cancelación**» | 🟡, **rama cerrada: COMPLETAR** | 08 cubre cancelación **por señal**, no **deadline por tiempo**. Corroborado por la propia `01·§1.1`: *«el canónico cancela por abort, no por timeout per-task»* |
| `01` | `CTR-12` | firma de CR2 con 4º arg **`ctx.stop`** | **`ctx.abort`** + orden `SR1 antes que CR2` | `08·SR1` hace desaparecer `ctx.stop`; CR2 nacía escrito contra un tipo muerto |

**Los dos hallazgos que la verificación produjo y que no estaban previstos:**
- **`02·G5` es el SEGUNDO fallo de `Q3` en ese mismo documento**, y por la punta **opuesta** a `F8`: en `F8` el
  tramo abierto probaba el punto de registro y no al productor; en `G5` prueba al **productor** y no al
  **consumidor efectivo**, que vive en otro paquete. Es el caso testigo de la **consecuencia 32**.
- **`02·I6` es de especie distinta a `I1..I5`:** a aquéllos los invirtió un **rollup**; a éste lo invierte **otro
  par**. La vigilancia de rancidez contra los 5 rollups **no cubre este vector** ⇒ **`AC-31`**.

**Pendientes de EJECUCIÓN con dueño ajeno (3):** `P4-08-8` (homar `ToolStatus`/`isConcurrencySafe` en el propio
`09·tools-infra`, aquí sólo queda la remisión) · la decisión de `SEAMS §S24` —en su **forma corregida**: el
deadline **se compone dentro de la señal** (`createCombinedAbortSignal`) y devuelve `cleanup` obligatorio; **no**
«cuarta razón de un enum»— hay que **escribirla en `SEAMS`**, no sólo aquí · `DB-h2` exige que `05·execution` dé
hogar a `H-3` **antes** de que DB-SIG-1..3 sea ejecutable.

**Deuda que esta 2ª vuelta abre sobre el propio 08 (declarada, no oculta):** `CG-SIG-1` fue escrito asumiendo un
**enum cerrado** de razones y el canónico usa **valor abierto**; queda **anotado** en `§2.3` pero `CG-SIG-1` **no
ha sido reescrito** — es remediación, no verificación, y su dueño es este mismo par en la pasada de ejecución.

**Cabos = remediación con destino nombrado** (no de verificación): `CG-SIG-1..9` → `AbortScope`/base/
`../DEUDA-B-transversal.md §B-signals` + A3.DA; `DB-SIG-1..3` → retirada **a nivel de símbolo** con `SignalType`
superviviente, **tras `H-3`**; `LAT-SIG1` → borrar `ModelRequest` (decisión ya tomada en `DEUDA-B §7.3`);
`OI-SIG-A..C` → `00-INTEGRADORES.md`; homed-fuera → `02·LR5`/`02·motor#2`/`06·HR2`/`07·EvR4`/`07·EVT7`/`09·FIND-TOOL1`.

**Nota para 04·modes:** liga directa — `CG-SIG-9` (dos niveles work/agent) cruza `05·EXEC12`; el `SignalBus`
huérfano es hermano de `modes/` huérfano (FIND-MODE1), que 04 debe resolver con el mismo criterio **y ahora con
`RV-6` delante** (a nivel de símbolo, nombrando lo que sobrevive); y `PermissionContext.mode` (GAP-02, ya anclado
en `06·CG-HOOK-8`) es el corazón de 04.
