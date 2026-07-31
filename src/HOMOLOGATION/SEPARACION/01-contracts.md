# 01 · contracts — SEPARACION (Filosofía B)

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/01-contracts.md`.
> **Ciclo A1.1** del PLAN §4. Fuente: tracker `../01-contracts.md` (15 findings, leído íntegro 1→198).
> Esquema: `00-LEGEND.md`. Re-clasifica cada finding de fidelidad-de-capacidades bajo B (base↔costuras↔batteries↔integrador).
> **No es otra tabla de deuda:** es el reparto de los contratos de la espina en sus destinos de construcción.

## Naturaleza de la categoría
`contracts/` **no porta código canónico**: son los **Protocols/DTOs** que el runtime introdujo para desacoplar al
consumidor. Bajo B, esta categoría es la **más "T1"** de la espina: aquí viven los **shapes invariantes** (la unidad
de trabajo `RuntimeTask`, el evento/stream que produce `AgentRuntime`, el `PermissionContext`) y las **costuras de
política** que el base define y el integrador/battery rellena. El eje de la re-clasificación: separar el **shape**
(T1, va al paquete de contratos) de la **política/motor** que ese shape mueve (costura, battery o integrador).

---

## 1. Tabla por finding

| ID | resumen (comportamiento observable) | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **CTR-01** `AgentRuntime` | façade dispatch/stream/status/cancel/result de una unidad de agente | núcleo | **T2-COSTURA** (+ default base `LocalAgentRuntime` = T2-BASE-MECANISMO) | interfaz **`AgentRuntime`** (paquete contratos) + base envía default `LocalAgentRuntime` | — | extraer la interfaz-façade al paquete de contratos; el base publica `LocalAgentRuntime` como mecanismo por defecto; el integrador complejo puede implementar la suya |
| **CTR-02** `RuntimeTask` base | unidad de trabajo `prompt`/`description`/`subagent_type` | núcleo | **T1-CONTRATO** | paquete contratos (`RuntimeTask` DTO) | — | extraer el DTO al paquete de contratos como shape invariante de entrada |
| **CTR-03** `model_override` 🔀 | selección de modelo por task | núcleo | **T1-CONTRATO** (el campo) | paquete contratos (campo) + **resolución→05·execution** | — | **shape del campo:** el canónico NO es string libre — `AgentTool.model: z.enum(['sonnet','opus','haiku'])` **+ el sentinel `inherit`** (restituido de tracker `:25` por `A-CIERRE-P4 §7·P4-01-2`; el corpus lo había perdido entero). El contrato debe decidir enum-cerrado+alias vs string opaco. **La resolución NO está pendiente: `05·E2` la da ✅ homologada y cableada** (`getAgentModel` ≡ `agents.py:46-58`, precedencia override>agente>herencia, `runtime.py:345`). `isCoordinatorMode`→undefined es legítimamente **⛔** (`04·A1`: topología de swarm, experimental) |
| **CTR-04** `fork_context` 🔀 | derivar contexto hijo (fork) compartiendo prefijo | núcleo | **T1-CONTRATO** (el flag) | paquete contratos (flag) + **mecanismo byte-idéntico→05** | eje **ejecución** (run efímero/fork) | el contrato expone el bool (`ForkPolicy(inherit_messages=...)`, runtime.py:200). **Mecanismo canónico restituido** (tracker `:26`, `A-CIERRE-P4 §7·P4-01-3`): el fork NO se pide con un flag — es **implícito por omisión de `subagent_type`**, con el sentinel **`FORK_SUBAGENT_TYPE='fork'`** (`forkSubagent.ts`). ⇒ decisión de shape T1 pendiente: flag explícito (hoy) vs valor centinela del propio `subagent_type`. Byte-identidad + guard anti-recursión → `05·E13`/`E14` (allí sí conservados) |
| **CTR-05** `owner_id`/`session_id` ✅\*→**CORE-GAP** | atribución de usuario/sesión sobre la unidad de trabajo | núcleo (transporta id opaco) | **T3-INTEGRADOR** + **T2-COSTURA (repo)** | integrador (atribuye) + costura **repo id-opaco**; **consolida en transversal (A3.DA)** | eje **persistencia+ejecución** · patrón **id opaco + repo** | **ripear** el autogen `user_<hex>`/`sess_<hex>` (runtime.py:208-209 = mímica de single-user): el contrato transporta un id opaco **sin interpretar**; el integrador atribuye y provee el repo. **⚠ CAMBIO DE ESTADO DECLARADO** (`A-CIERRE-P4 §7·P4-01-4`): el tracker `:27` lo daba **✅\* «adición correcta»**; esta ficha lo endureció a mímica-a-ripear **sin evidencia nueva al escribirla**. Corroborado **a posteriori y de primera mano** por `DEUDA-A §0.1b·H-1` + `ID-1`: `MemoryProvider._scope` keya por `f"{user_id}/{agent}"` (`provider.py:61-63`) y el autogen da un uuid nuevo **por dispatch** ⇒ la memoria se escribe en un directorio distinto cada vez. El endurecimiento **se sostiene**; lo que faltaba era declararlo |
| **CTR-06** `audio_prompt` ✅\* | entrada de voz → prompt (STT) | núcleo (el campo) | **T1-CONTRATO** (shape `AudioInput` opcional) + **BATTERY voice** | paquete contratos (campo opcional) + battery **voice** (17) | — | el shape `AudioInput` es campo opcional del contrato; el procesamiento STT es battery voice (se diseña en 17) |
| **CTR-07** `PermissionContext` allow/deny 🟡 | reglas allow/deny por nombre + scope de persistencia | núcleo (el shape) | **T1-CONTRATO** (shape) + **T3-INTEGRADOR** (scope de persistencia) | paquete contratos (`PermissionContext`) + integrador (persistencia por-scope, CR4) | eje **persistencia** (scope de reglas) | el shape queda en contratos; la distinción de scope se **delega documentadamente** al integrador (opera sobre el conjunto resuelto). **Vocabulario canónico restituido** (tracker `:29`/`:181`, `A-CIERRE-P4 §7·P4-01-5` — tenía **0 ocurrencias en los 18 `SEPARACION/NN-*.md`**): fuentes `alwaysAllowRules`/`alwaysDenyRules` con **cuatro** scopes nominales — **`command`** · **`project`** · **`localSettings`** · **`userSettings`**. Estado actual de B: los colapsa a **dos** — `command`(persistente)/`session`(volátil). Son 4→2, no 3 |
| **CTR-08** Permission **modes** ❌ **GAP-02** | modo `default`/`acceptEdits`/`plan`/`bypassPermissions` gobierna el gate | núcleo | **T1-CONTRATO** (campo `mode` faltante) + **DEUDA-B** (hack `native["plan_mode"]`) | paquete contratos (añadir `PermissionMode`+`mode`) + gate del dispatcher (base) + DEUDA-B (ripear hack) | — | **CORE-GAP**: el contrato NO modela `mode`; añadir enum+campo y que el gate decida por modo+reglas, no por `app_state.native` (loop/agent_loop.py:293). **Shape completo de CR1 traído del tracker `:150-152`** (estaba tras el puntero «CR1»): `mode: PermissionMode = "default"` **+ `additional_working_directories: list[str]`** (lo consume el gate de fs) **+ `pre_plan_mode: PermissionMode\|None`** (restaurar al salir de plan). Los **tres** campos, no sólo `mode` |
| **CTR-09** `CompactionProvider` 🟡 | providers aportan mensajes al contexto de compactación | núcleo | **T2-COSTURA** (provider seam, correcto) + **BATTERY compaction** (motor ausente) | interfaz **`CompactionProvider`** + battery **compaction** (motor→02) | eje **persistencia** (scope de compactación = sesión) | el aporte de providers es seam correcto; el **motor** (trigger/estrategia/presupuesto) es **CORE-GAP** homed en 02·loop. **Superficie canónica restituida** (tracker `:31`, `A-CIERRE-P4 §7·P4-01-6`): `services/compact/` son **8** sub-servicios — `auto` · `micro` · **`api-micro`** · `sessionMemory` · **`timeBased`** · **`postCleanup`** · **`grouping`** · **`prompt`**. Sólo 3 tienen contraparte en el corpus (`auto`≈02·B6, `micro`≈02·B4, `sessionMemory`→13). Los **5 en negrita = candidatos DR-2** (0 ocurrencias en los 18 trackers **y** en los 18 SEPARACION) ⇒ **P6″**, no P4″ |
| **CTR-10** `StorageContract` 🔀 | abstracción de FS/blob para deployments contenerizados | núcleo | **T2-COSTURA** | interfaz **`StorageContract`** (unificar con `StorageProtocol`→15) | eje **persistencia** | costura correcta (consumida por plan_file + fs_env.py:124); resolver el solapamiento con `StorageProtocol` de 15 al documentar 15 |
| **CTR-11** `PathPresentation` ✅ | saneo de paths hacia LLM/voz (no filtrar rutas reales del contenedor) | núcleo | **T2-COSTURA** (presentation seam, default base `IdentityPresentation`) + **DEUDA-B** (`to_llm` latente) | interfaz **`PathPresentation`** + DEUDA-B (`to_llm` sin call site) | — | `sanitize_output` cableado (dispatcher.py:42) = comportamiento núcleo ✅; `to_llm` sin consumidor de producción → **DEUDA-B** (cablear o borrar), NO deuda A↔B (L10) |
| **CTR-12** `UserInputProcessor` 🟡 **GAP-01** | preprocesar slash-commands / inline-invocations antes del turno LLM | núcleo | **T2-COSTURA** (seam) + **T2-BASE-MECANISMO** (cabling gap en el loop) + **BATTERY commands** | interfaz **`UserInputProcessor`** + **cablear en el loop base** (CR2) + battery **commands** (12) | — (arg `session` roza identidad) | **CORE-GAP**: el seam existe pero ningún consumidor lo invoca (grep: sólo exportado); el canónico (`commands.ts` + `query.ts`/`QueryEngine.ts`) sí preprocesa → el **loop base debe invocar el seam**; el contenido (comandos) es battery/integrador. **Punto y secuencia de cableado traídos del tracker `:161-167`** (estaban tras el puntero «CR2»): en `run()`, **tras `_run_turn_start_hooks()` y ANTES del `messages.append({"role":"user"…})` — `agent_loop.py:176-179`**; orden `expand_inline_invocation` → `get_inline_name` (resolver) → `process_slash_command(...)` (firma 5-arg: texto, registry, session, `ctx.stop`, `ctx.event_queue`) → **si devuelve resultado terminal, cortar el turno sin ir al modelo**; default `Noop` = passthrough. **⚠ Firma rancia contra `08·SR1` (`A-CIERRE-P4 §14.8`):** el 4º argumento se escribió como **`ctx.stop`**, y `08·SR1` **crece `ctx.stop` a `ctx.abort: AbortScope`** (reason + árbol + `interrupt()`). Al ejecutar CR2 el parámetro es **`ctx.abort`**, no `ctx.stop`; y el orden importa — **SR1 antes que CR2**, o CR2 nace escrito contra un tipo que va a desaparecer |
| **CTR-13** `@runtime_checkable` 🟡 **FIND-01** | conformidad `isinstance` de los Protocols | núcleo | **DEUDA-B** | DEUDA-B (decorar consistente) | — | higiene interna: `UserInputProcessor`/`CompactionProvider` sin decorar; unificar criterio (CR3). NO deuda A↔B |
| **CTR-14** `max_turns` 🟡 | tope de turnos por task | núcleo | **T1-CONTRATO** (el campo) + **cabling gap→05 (FIND-EXEC5)** | paquete contratos (campo) + **cablear→05** | — | el campo existe pero **no** se pasa al `AgentLoop(...)` (runtime.py:355-366; `_MAX_TURNS=50` fijo) → **CORE-GAP** homed en 05·execution·`E16`. **Default del hijo-fork restituido** (tracker `:36` y tracker `05:51`, `A-CIERRE-P4 §7·P4-01-7`): `forkSubagent.ts:65` fija **`maxTurns: 200`** para el fork — ausente en SEPARACION/01 **y** en `05·E16`, corregido en **los dos sitios**. La precedencia `maxTurns ?? agentDefinition.maxTurns` y el frontmatter de `loadAgentsDir` sí sobreviven (`05·E16`/`E28`) |
| **CTR-15** `timeout_seconds` 🟡 | límite de vida por task | núcleo | **T1-CONTRATO** (campo) + **T2-COSTURA** (`arm_watchdog`) + **DEUDA-B** (default no-op) | paquete contratos (campo) + costura **`arm_watchdog`** (execution/tasks) + DEUDA-B | eje **ejecución** (vida del task) | campo **cableado** al seam (`arm_watchdog(task.timeout_seconds…)`, runtime.py:149) cuyo default `InMemoryTaskRegistry.arm_watchdog` es **no-op deliberado** → **DEUDA-B** (completar o retirar); sin contraparte canónica ⇒ NO deuda A↔B (L10). **⚠ RAMA CERRADA (`A-CIERRE-P4 §14.8`, 2026-07-29, `CAT-h10`): se COMPLETA, no se retira.** La disyuntiva se dejó abierta en `§2.4` con la condición *«…o retirar el campo si 08·signals cubre la cancelación»*; **08·signals NO la cubre**: el `AbortScope` de `08·SR1` modela la cancelación **por SEÑAL** (alguien decide parar), no el **deadline por TIEMPO** (nadie decide; vence un plazo). Son dos disparadores distintos sobre el mismo efecto. Corroborado desde la propia `§1.1` de este doc — *«el canónico cancela por abort, no por timeout per-task»* ⇒ `arm_watchdog` es **extensión de B sin contraparte**, y una extensión no se justifica por otra costura que no la implementa. **Forma — ⚠ CORREGIDA CONTRA EL CANÓNICO 2026-07-29 (`A-CIERRE-P4 §14.9`).** La 1ª redacción decía *«entra por la misma puerta que el abort, con `reason='timeout'` como **cuarta razón del enum**»*: la mitad sobrevive y la mitad no. **Sobrevive** que el vencimiento entra por la misma puerta (no hay mecanismo de deadline paralelo) ⇒ `arm_watchdog` **se completa**. **Cae** el mecanismo: el canónico **compone la fuente DENTRO de la señal** —`createCombinedAbortSignal(signal, {timeoutMs})`, `utils/combinedAbortSignal.ts` 1→47— en vez de que un watchdog externo llame a `interrupt()`; y **no tiene enum de razones**: `.abort(reason)` toma valor abierto (`'interrupt'`, `'sibling_error'`, `DOMException TimeoutError`). ⇒ firma para B del tipo `combine(scope, timeout_s=...) -> (scope_hijo, cleanup)`, con **`cleanup` obligatorio** (el propio canónico explica por qué: `AbortSignal.timeout` acumula ~2,4 KB/llamada bajo Bun hasta vencer). Pendiente de escribirse en `SEAMS §S24` en **esta** forma |

---

## 1.1 Anclas canónicas — columna que la destilación había borrado entera

> **Hallazgo sistémico `P4-01-1`.** El tracker cita **11 referencias a archivos/símbolos canónicos**; esta ficha
> conservaba **0**. No es un descuido de una celda: la tabla de §1 **no tiene columna de contraparte canónica**,
> así que la referencia se cayó por construcción, para las 15 fichas a la vez. Medido sobre los 18 pares, la
> retención de citas `*.ts` es **1130 → 105 (≈9 %)**, y **tres pares quedan en cero: 01, 05 y 07**.
>
> **Consecuencia bajo la regla del 7º campo** (*ninguna unidad entra en Fase B sin ancla canónica*): el ancla no
> hay que ir a buscarla al canónico — **está en el tracker**, que es lo que `D-01` afirmaba y esto confirma con
> número. Restituirla es P4″; **tabularla como comportamientos (`D-02`) sigue siendo P6″/T-A**: lo de abajo son
> **punteros, no anclas acreditadas**.

| ficha | contraparte canónica (del tracker) |
|---|---|
| CTR-01 | `query.ts` (async-gen del turno) + `Task.ts` (dispatch+stream de una unidad de agente) |
| CTR-02 | `AgentTool` inputSchema (`prompt`/`description`/`subagent_type`) |
| CTR-03 | `AgentTool.model: z.enum(['sonnet','opus','haiku'])` + `getAgentModel` + sentinel `inherit` (+`isCoordinatorMode`→undefined, **⛔** por `04·A1`) |
| CTR-04 | `forkSubagent.ts` — fork implícito por omisión de `subagent_type`; `FORK_SUBAGENT_TYPE='fork'`; `isInForkChild` |
| CTR-05 | *(sin contraparte: el canónico es single-user en terminal)* |
| CTR-06 | *(sin contraparte directa: `voice/`, STT → 17)* |
| CTR-07 | `alwaysAllowRules`/`alwaysDenyRules` + scopes `command`/`project`/`localSettings`/`userSettings` |
| CTR-08 | `acceptEdits` (44+ usos) · `bypassPermissions` (10) · `plan` · `default` |
| CTR-09 | `services/compact/` — `auto`·`micro`·`api-micro`·`sessionMemory`·`timeBased`·`postCleanup`·`grouping`·`prompt` |
| CTR-10 | *(sin contraparte: el canónico es FS local por identidad)* |
| CTR-11 | traducción/saneo de paths hacia LLM/UI — **inline** en el canónico, sin módulo propio |
| CTR-12 | `commands.ts` + `query.ts`/`QueryEngine.ts` |
| CTR-13 | *(sin contraparte: higiene de Protocols, invención de B)* |
| CTR-14 | `runAgent.ts:756` (`maxTurns ?? agentDefinition.maxTurns`) · `forkSubagent.ts:65` (=200) · `loadAgentsDir.ts` (frontmatter) |
| CTR-15 | ⚠ **CORREGIDO 2026-07-29** (`A-CIERRE-P4 §14.9`, `CAT-h10`). Decía *«sin contraparte: el canónico cancela por abort, no por timeout per-task»* y es **verdad a medias**: cierto que no hay campo `timeout_seconds` **per-task**, **falso** que el canónico no convierta tiempo en abort. **Contraparte real: `utils/combinedAbortSignal.ts` (`createCombinedAbortSignal(signal, {signalB?, timeoutMs?})`)** — funde señal + deadline en **una sola** `AbortSignal` con `setTimeout`, y devuelve `cleanup()` obligatorio. Consumidores: `hooks.ts:2149,2196,3089,3281,4758` · `execPromptHook.ts:59` · `execAgentHook.ts:80` · `execHttpHook.ts:151` · `print.ts:4189`; variante MCP `mcp/client.ts:519` (`DOMException('...','TimeoutError')`). El corte es **por operación**, no per-task |

**Pruebas que ya codifican los targets** (el 6º campo de L05, también perdido en la destilación; existen hoy
como `xfail(strict)` en `test_contracts_homologation.py`): `test_permission_context_models_permission_modes`
(CTR-08) · `test_agent_loop_consumes_user_input_processor` (CTR-12) · `test_max_turns_threaded_to_loop`
(CTR-14, home 05) · `test_all_contract_protocols_runtime_checkable` (CTR-13, a crear).

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica (nombre · productor invoca · consumidor implementa)
- **`AgentRuntime`** (T2-COSTURA, façade de ejecución) — productor: consumidor/integrador (`dispatch`/`stream`) · consumidor: base `LocalAgentRuntime` (default) **o** integrador complejo (impl propia). *Su `stream()` produce eventos cuyo shape es T1-CONTRATO → definido en 07·events.*
- **`CompactionProvider`** (T2-COSTURA) — productor: motor de compactación (battery) vía `collect_compaction_context` · consumidor: providers concretos (battery/integrador).
- **`StorageContract`** (T2-COSTURA) — productor: `plan_file` + `fs_env.py:124` (`real_path`/`ensure_local`/`commit`) · consumidor: integrador (FS local degenerado / adaptador MinIO). *Solape con `StorageProtocol` (15) → unificar en 15.*
- **`PathPresentation`** (T2-COSTURA) — productor: `tools/dispatcher.py:42` + `runtime.py:244` (`sanitize_output`) · consumidor: base default `IdentityPresentation` / integrador.
- **`UserInputProcessor`** (T2-COSTURA, **hoy sin productor** = GAP-01) — productor (a cablear): `AgentLoop` antes del turno LLM · consumidor: battery commands / integrador.
- **`arm_watchdog`** (T2-COSTURA en execution/tasks) — productor: `dispatch()` (runtime.py:149) · consumidor: base default no-op / integrador con watchdog real.
- **repo id-opaco de identidad/sesión** (T2-COSTURA transversal, SEAM-DE-IDENTIDAD) — productor: runtime (lee sólo `.id`) · consumidor: integrador (atribuye + metadata). *Consolidación en A3.DA, no aquí.*

### 2.2 Batteries que alimenta (nombre · alcance)
- **compaction** — motor de compactación (trigger/estrategia/presupuesto) que consume `CompactionProvider`. Origen del **motor** en 02·loop; el seam nace aquí.
- **voice** — STT `AudioInput`→prompt (17). El shape entra por el contrato; el procesamiento es battery.
- **commands** — slash-commands / inline-invocations que rellenan `UserInputProcessor` (12·skills).

### 2.3 CORE-GAPs (brechas A↔B reales → rollup `DEUDA-A.md`)
- **CTR-08 / GAP-02** — el contrato de permisos no modela `mode`; la decisión de plan-mode vive suelta en `app_state.native`. Brecha de contrato + mecanismo de gate. *(Real: el canónico gobierna por modo en 44+/10 usos.)*
- **CTR-12 / GAP-01** — `UserInputProcessor` no invocado por el loop; el canónico `query` sí preprocesa slash/inline. Brecha de **cableado** (L09: existir≠cablear).
- **CTR-14 / FIND-EXEC5** — `max_turns` no llega al loop (homed en 05·execution; se registra aquí el origen-contrato).
- **CTR-09 (motor)** — motor de compactación ausente (homed en 02·loop; el seam de providers sí existe).

### 2.3b Cambios de estado respecto del tracker (declarados — `A-CIERRE-P4 §7`)

Un veredicto que cambia entre el tracker y esta ficha **se declara aquí con su evidencia**; si no, es
endurecimiento indistinguible de una invención (la especie de `09·E5`).

- **CTR-05 · ✅\* «adición correcta» (tracker `:27`) → CORE-GAP «mímica a ripear».** Al escribirse, esta ficha
  no aportó evidencia nueva: reinterpretó el mismo `runtime.py:208-209` que el tracker había aprobado.
  **Corroborado después y de primera mano** en `DEUDA-A §0.1b·H-1`/`ID-1` (`MemoryProvider._scope` keya por
  `f"{user_id}/{agent}"`, `provider.py:61-63`; uuid nuevo por dispatch ⇒ la memoria del agente principal se
  escribe en un directorio distinto cada vez). **El endurecimiento se sostiene por sus consecuencias
  verificadas, no por el razonamiento que lo produjo.** Contra-ejemplo útil de `09·E5`: endurecer no es *per se*
  inventar — la diferencia es si alguien abrió el archivo.

### 2.4 DEUDA-B (higiene interna del runtime, NO A↔B — L10)
- **CTR-13 / FIND-01** — `@runtime_checkable` inconsistente → decorar.
- **CTR-15** — default `arm_watchdog` no-op → **completar** (`asyncio.wait_for`/deadline→kill). ~~o retirar el campo si 08·signals cubre la cancelación~~ — **rama descartada con evidencia** (`A-CIERRE-P4 §14.8`): 08 cubre cancelación **por señal**, no **deadline por tiempo**; el vencimiento entra por la misma puerta del `AbortScope` con `reason='timeout'`. Ver la celda `CTR-15` de §1.
- **CTR-11** — `to_llm` sin call site de producción → cablear o borrar.
- **CTR-08 (parte hack)** — ripear `app_state.native["plan_mode"]` cuando `mode` entre al contrato.

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05; vertido formal en A1.7)
Con **capacidad observable · origen (costura del base) · firma que consume · cableado en el integrador · orden · criterio de aceptación**:

- **OI-1 · Atribuir identidad/sesión** *(contrato base común §1.1)* — **capacidad:** todo integrador atribuye usuario/sesión al id opaco y provee el repo genérico. **origen:** CTR-05 (costura repo id-opaco). **firma:** `RuntimeTask.owner_id/session_id` opacos + repo `create/open/list/delete/fork` sobre metadata propia. **cableado:** el integrador setea los ids antes de `dispatch`; implementa el repo. **orden:** prerrequisito de persistencia (OI-3). **aceptación:** degenerado corre con defaults minimal (cero ceremonia); complejo particiona por tenant sin que el runtime vea el grafo. *(realización: §2.1 degenerada vs §2.2 multi-tenant)*
- **OI-2 · Poblar la façade `AgentRuntime`** *(§1.2)* — **capacidad:** despachar/stremear un turno. **origen:** CTR-01. **firma:** `AgentRuntime`. **cableado:** degenerado usa `LocalAgentRuntime`; complejo puede implementar la propia. **aceptación:** un turno end-to-end (validado en A2). 
- **OI-3 · Proveer `StorageContract`** *(§1.3 persistencia)* — **capacidad:** resolver rutas/persistir artefactos (plan, fs). **origen:** CTR-10. **firma:** `StorageContract`. **cableado:** FS local (degenerado) / MinIO (complejo). **aceptación:** plan_file/fs_env operan sobre el adaptador.
- **OI-4 · Política de permisos por-scope + por-modo** *(§1.6 política/gates)* — **capacidad:** persistir reglas en los **cuatro** scopes canónicos (`command` · `project` · `localSettings` · `userSettings`) y decidir por `mode`. **origen:** CTR-07 (scope) + CTR-08 (modo, cuyo **campo** es base pero cuya **política** es integrador/battery). **firma:** `PermissionContext` (mode + `additional_working_directories` + reglas resueltas). **cableado:** el integrador persiste por scope y setea el modo (p.ej. `EnterPlanMode`, guardando `pre_plan_mode` para restaurar al salir); el gate del base lee el conjunto resuelto. **aceptación (subida por `A-CIERRE-P4 §7·P4-01-5`):** los cuatro scopes se distinguen — una regla de scope `project` sobrevive entre sesiones del mismo proyecto, una de `userSettings` sobrevive entre proyectos, una de `command` sobrevive a la sesión, y una de `session` **no** sobrevive. Un integrador que colapse los 4 a 2 (lo que hace B hoy) **no** pasa.
- **OI-5 · Rellenar `UserInputProcessor`** *(§1.5 composición)* — **capacidad:** slash/inline reales. **origen:** CTR-12. **firma:** `UserInputProcessor`. **cableado:** battery commands (12) o processor propio; el loop base ya invoca el seam (tras CR2). **aceptación:** un slash-command corta el turno sin ir al modelo.

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor (lema de la etapa):**
> De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda; ninguna categoría
> se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar —o colocado sin
> abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — una fila por finding

| ID | TIER | destino | cara | evidencia | detalle | nota-identidad |
|---|---|---|---|---|---|---|
| CTR-01 | T2-COSTURA (+base default) | interfaz `AgentRuntime` | ambas | tracker-leído + ensamblador `runtime.py:140-169` (dispatch/stream) abierto | sí (§2.1 + OI-2) | — |
| CTR-02 | T1-CONTRATO | paquete contratos | base | tracker-leído | sí (§1) | — |
| CTR-03 | T1-CONTRATO | contratos + 05 | base | tracker-leído + ensamblador `runtime.py:346/351` abierto | sí (→05) | — |
| CTR-04 | T1-CONTRATO | contratos + 05 | base | tracker-leído + ensamblador `runtime.py:200` abierto | sí (→05) | eje ejecución |
| CTR-05 | T3-INTEGRADOR + T2-COSTURA | integrador + repo (transversal) | ambas | tracker-leído + ensamblador `runtime.py:208-209` abierto (autogen) | sí (OI-1) | **persist+ejec · id opaco+repo** |
| CTR-06 | T1-CONTRATO + BATTERY voice | contratos + battery voice(17) | ambas | tracker-leído | sí (→17) | — |
| CTR-07 | T1-CONTRATO + T3-INTEGRADOR | contratos + integrador (CR4) | ambas | tracker-leído | sí (OI-4) | eje persistencia |
| CTR-08 | T1-CONTRATO + DEUDA-B | contratos + gate base + DEUDA-B | ambas | tracker-leído | sí (CR1/OI-4) | — |
| CTR-09 | T2-COSTURA + BATTERY compaction | interfaz + battery(→02) | base | tracker-leído (motor sin consumidor confirmado por grep en tracker L09) | sí (→02) | eje persistencia |
| CTR-10 | T2-COSTURA | interfaz `StorageContract` (→15) | ambas | tracker-leído + ensamblador `fs_env.py:124` abierto | sí (OI-3/→15) | eje persistencia |
| CTR-11 | T2-COSTURA + DEUDA-B | interfaz + DEUDA-B(`to_llm`) | base | tracker-leído + ensamblador `dispatcher.py:42` + `runtime.py:241,244` abiertos (2 anclajes `sanitize_output`) | sí (§2.4) | — |
| CTR-12 | T2-COSTURA + T2-BASE-MECANISMO + BATTERY | interfaz + cablear loop(CR2) + battery(12) | ambas | tracker-leído (uncabled confirmado por grep en tracker L09) | sí (CR2/OI-5) | — |
| CTR-13 | DEUDA-B | DEUDA-B (decorar) | base | tracker-leído | N/A (DEUDA-B) | — |
| CTR-14 | T1-CONTRATO + cabling→05 | contratos + 05 | base | tracker-leído + ensamblador `runtime.py:355-366` abierto (no pasa max_turns) | sí (→05) | — |
| CTR-15 | T1-CONTRATO + T2-COSTURA + DEUDA-B | contratos + costura watchdog + DEUDA-B | base | tracker-leído + ensamblador `runtime.py:149` (llamada) + `registry.py:88-91` (default `pass` no-op) abiertos | sí (§2.4) | eje ejecución |

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../01-contracts.md`?** — **Sí**, líneas 1→198 (incl. tabla, re-visita L09, ledger de cierre, §remediación).
2. **¿Reconcilia el conteo?** — findings en `../01-contracts.md` = **15** (feats 1-15); colocados = **15**; sin colocar = **0**. ✅
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador (sin grep)?** — **Sí, re-abierto en ESTE ciclo:** CTR-01 `runtime.py:140-169`; CTR-03 `:346/351`; CTR-04 `:200`; CTR-05 `:208-209`; CTR-14 `:355-366`; CTR-15 `:149`; CTR-10 `fs_env.py:124`; CTR-11 `dispatcher.py:42`. Los **ausentes-de-consumidor** (CTR-09 motor, CTR-12 uncabled) se apoyan en el grep-completo de la re-visita L09 del tracker (símbolo definido-vs-invocado) — es una **ausencia**, no una afirmación de cableado (Q3 aplica a afirmar cableado, no a probar su ausencia).
4. **¿La cara integrador quedó al MISMO detalle que la base?** — **Sí**: §2.5 desarrolla 5 obligaciones (OI-1…OI-5) con los 6 campos L05; ningún finding cerrado con "→ integrador" a secas.
5. **¿Doble filo (L10)?** — **Sí**: ningún ❌ disfrazado de 🔀 (CTR-08 se mantiene ❌/CORE-GAP; CTR-12 CORE-GAP de cableado). Ninguna deuda inflada: CTR-11/CTR-13/CTR-15 clasificados **DEUDA-B interna**, NO deuda A↔B (extensiones sin contraparte canónica).

### 3.3 VEREDICTO

> **⚠ Revisado desde el par 08 — `A-CIERRE-P4 §14.8` (2026-07-29).** Dos celdas tocadas, **ninguna cambia de
> estado**: `CTR-15` cierra su rama abierta (**completar**, no retirar — 08 cubre señal, no deadline) y `CTR-12`
> corrige la firma de cableado de CR2 (`ctx.stop` → **`ctx.abort`**, con el orden `SR1 antes que CR2`). Registrado
> aquí y no sólo en 08 por `CAT-h10`. El «nada pendiente» de abajo **se sostiene**: lo que llegó del par 08 no
> abrió verificación en 01, la **cerró**.

**✅ NADA PENDIENTE → A1.2 (16·models).**
Los 15 findings repartidos con TIER+destino; 4 CORE-GAPs identificados para DEUDA-A (CTR-08, CTR-12, CTR-14→05, CTR-09→02); 4 DEUDA-B; 7 costuras nombradas con productor/consumidor; 5 obligaciones de integrador con detalle simétrico. Cabos con destino explícito (05·execution: CTR-03/04/14; 02·loop: CTR-09 motor; 15·storage: CTR-10; 17·voice: CTR-06; 12·skills: CTR-12; transversal A3.DA: CTR-05) — ninguno es pendiente de **verificación**.
