# 00 · BLUEPRINT — mapa de descomposición base ↔ costuras ↔ batteries ↔ integradores

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/00-BLUEPRINT.md`.
> **ESTADO: SKELETON (creado en A0).** Las secciones están **VACÍAS a propósito**: se rellenan incrementalmente.
> - La **espina** (base + costuras + batteries del núcleo) se consolida en **A1.7** desde `SEPARACION/01,16,07,02,05,09`.
> - Las firmas borrador de costuras se destilan en **A1.7 → `SEAMS.md`** y se **validan/corrigen** en el walking skeleton **A2**.
> - El **resto** (batteries de capabilities + deudas) se añade en **A3**.
> - El blueprint **FINAL** (todo cableado end-to-end + plan de construcción B–F) se cierra en **A-CIERRE**.
> - **Todo lo que converge en A-CIERRE está inventariado en `A-CIERRE-LEDGER.md`** (2026-07-27): 64 ocurrencias → 40 descartadas nombradas + **18 ítems `AC-01..AC-18`** con origen `archivo:línea`, tamaño y pasada; **10 pasadas P0..P9**, forzadas por los 18 `NN-*.md` = **6531 L ≈ 795 KB**. Este documento es uno de los que **AC-10 reescribe entero** (su lectura íntegra actual es HEREDADA pre-compactación).
>
> Esquema de clasificación: ver `00-LEGEND.md`. Filosofía: memoria **architecture-layers** (B = base framework + batteries).
> **No escribir aquí conclusiones no destiladas de un ciclo NN** — este mapa es agregador, no fuente primaria (evita superficialidad heredada, L00).

---

## 0. Leyenda de estado de llenado
`⬜ vacío (skeleton)` · `🟨 parcial (algún ciclo aportó)` · `✅ consolidado (ciclo de síntesis cerrado)`.
Cada sección lleva su marcador y **de qué ciclo** proviene su contenido.

> **Estado global tras A1.7 (2026-07-21):** la **ESPINA** (§1 base + §2 costuras + §3 batteries) queda **✅ consolidada
> desde los 6 `SEPARACION/{01,16,07,02,05,09}.md`**. §1.4 (base del resto), §2.1 (rollup identidad) y el catálogo formal
> siguen ⬜ (A3/A-CIERRE). Las **firmas** de las costuras viven en **`SEAMS.md`** (creado en A1.7); aquí, el índice.

---

## 1. BASE FRAMEWORK — módulos del núcleo `agentic_runtime`
> Módulos que el base **posee** (T2-BASE-MECANISMO) + contratos T1 que mueve. Mecanismo, no política.
> **Estado: ✅ espina consolidada (A1.7)** · §1.4 ⬜ (A3).

### 1.1 Contratos (T1-CONTRATO) — paquete `contratos` — ✅ A1.1/A1.3/A1.6/A1.5
> Shapes invariantes donde enchufan AMBOS integradores. Reimplementarlos forkea el ecosistema.

- **Entrada / unidad de trabajo:** `RuntimeTask` (`prompt`/`description`/`subagent_type`, 01·CTR-02) + campos
  `model_override` (01·CTR-03), `fork_context`/`ForkPolicy` (01·CTR-04), `max_turns` (01·CTR-14), `timeout_seconds`
  (01·CTR-15), `audio_prompt`/`AudioInput` opcional (01·CTR-06); `owner_id`/`session_id` = **ids opacos** (01·CTR-05).
- **Permisos:** `PermissionContext` (allow/deny + `mode`, 01·CTR-07/CTR-08) + enum `PermissionMode`
  (`default`/`acceptEdits`/`plan`/`bypass`) — **CORE-GAP: el `mode` falta en el contrato** (GAP-02).
- **Eventos / stream (07·events):** `Event` frozen extensible (07·A3) + la taxonomía: `TokenEvent`(+`kind`),
  `ThinkingEvent` (07·B1/16·A4), `ToolCallEvent`, `ToolResultEvent`, `ToolProgressEvent` (07·C3), `DoneEvent`,
  `ResultEvent` terminal (07·D1/D2, **ausente**), `ErrorEvent(code)` (07·D5), `Usage`=ModelUsage rico
  (07·E1, cache/coste/thinking — **empobrecido hoy**), `InitEvent` (07·F0), `SessionStateEvent` (07·F1),
  `StatusEvent` (07·F2), `TaskStartedEvent` (07·G1), `CompactBoundaryEvent` (07·H1), `ApiRetryEvent` (07·J3),
  `Hook*Event` (07·I1). **Un solo `Usage` canónico** (unificar los dos divergentes, 07·E4 DEUDA-B).
- **Tool (09·tools):** `ToolProtocol` (schema+result mínimo) + `ToolResult` + `ToolCategory` (09·A1/A22) — miembros de
  **comportamiento** a crecer (concurrency/interrupt/permisos/validate/new_messages/output_schema/searchHint/aliases).
- **Ejecución (05):** `AgentDefinition` ampliado (campos de ejecución, 05·E28) + `TaskType`/`TaskRecord` enriquecido
  (05·E9/E32) + shape de trailer de resultado/`<task-notification>` (05·E18/E19 → converge 07).

### 1.2 Costura de motor (T1-MOTOR) — hacia `agentic_models` — ✅ A1.2
> El motor **ya vive separado** (`agentic_models`, port de `pi/ai`, ~30 providers = superset 🔀, NO deuda). El reparto B
> **no lo re-homa**: lo confirma como el motor y **enriquece la costura** que lo llama.
- **`ModelCallerProtocol`** (`caller.py`/`protocol.py`) = **la costura central** → firma `SEAMS.md §S1`. El **hallazgo raíz de
  la espina**: la costura es **demasiado delgada** (`complete()` no transporta thinking/effort/temperature/max_tokens/
  output_format/tool_choice; degrada `Usage`, descarta `thinking`, colapsa el error a str). El motor **ya trae la
  maquinaria**; falta enriquecer la costura para que el base la pida y la reciba (16·MoR1-8).
- Costuras auxiliares del motor: señal-de-abort (`SEAMS §S2`, hoy roto), `AuthProvider` (`§S3`). La **resiliencia**
  (retry/fallback/watchdog) **NO es del motor** (lib de una request) → battery `resilience` compuesta en el loop (§3).

### 1.3 Mecanismo de orquestación (T2-BASE-MECANISMO) — ✅ A1.3/A1.4/A1.5/A1.6
> Lo que el base **posee**: esqueleto, no política. El canónico lo fusiona en `query.ts` (1729 LOC); B lo des-fusiona en
> un loop delgado que **invoca costuras** y compone **batteries**.

- **`events/`** (07): `Event` + `EventBus` (`bus.py`, subscribe/subscribe_all/emit-try-except) + `stream()` productor de
  **canal único ordenado** (`runtime.py:153-181`, YA existe). Split de 3 canales (bus in-proc · `push_event` poll
  per-task · `ctx.messages` acumulación) = divergencia por-diseño para subagentes. `SEAMS §S5`.
- **`loop/`** (02): `AgentLoop` = **el mecanismo del turno** (prompt→pool→`complete()`→consumir stream→persistir
  assistant→dispatch con gate+context_modifier/ends_turn→decidir continuar). Esqueleto **homólogo fiel**; lo AUSENTE
  son **4 motores** que el loop **dispara** (compactación, budget, commands = batteries; error-recovery = base-mecanismo
  resiliente). Introducir `LoopOutcome`/reason-codes (02·A4) + `max_turns` configurable (02·A5, cabling→05).
- **`tools/`** (09): `ToolPool` (assemble/find, **invariante del pool único** = anuncio y ejecución resuelven del MISMO
  objeto ⇒ deferred = visibilidad, no disponibilidad) + `ToolDispatcher` (resolución+schema-validate+timeout-global) +
  `DeferredToolStrategy` (Simulada client-side / Nativa `defer_loading` server-side) + `ConfinedFilesystem`
  (confinamiento homologado: traversal/symlink/allow-set). `SEAMS §S14/§S26`.
- **`execution/`** (05): `LocalAgentRuntime` = ciclo de vida de subagente (spawn→stream→**complete-first**→summarize→
  notify→persist) + **`fork`** (snapshot inmutable/policy/filtrado de invariantes/guard de recursión/prefijo
  byte-idéntico) + `tasks/` (`TaskStatus` + registro). Des-fusionado **correcto de forma**; cableado **a medias**
  (el seam runner sin poblar — DEUDA-B crítico `B-runner-wiring`) + hereda **mímica de identidad** (→§2.1).

### 1.4 Módulos base del resto
_(pendiente A3: context · tools-native · hooks · signals · modes · storage · memory · skills · mcp · plan · voice · factory → consolidar A-CIERRE)_

---

## 2. COSTURAS (SEAMS) — interfaces que el integrador/battery rellena — ✅ espina (A1.7)
> T2-COSTURA + T1-MOTOR. **Firmas borrador completas (27) en `SEAMS.md`.** Aquí el índice rector (5 costuras del PLAN §3
> "model-caller, tool-contract, event/stream, dispatch, repo/scope") + el resto de la espina. Estado por `SEAMS §0`.

| costura (SEAMS) | tier | productor (invoca) | consumidor (implementa) | estado |
|---|---|---|---|---|
| **S1 model-caller** `ModelCallerProtocol` | T1-MOTOR | loop `agent_loop.py:235` | bridge `AgenticModelsCaller` / integrador | existe-enriquecer |
| **S16 tool-contract** `ToolProtocol` | T1-CONTRATO+costura | `create_tools`/`register` | tools/MCP/skills/integrador | existe-enriquecer |
| **S5 event/stream** `EventBus`+`stream()` | T2-BASE | caller/loop/runtime (`emit`) | integrador (`subscribe_all`) | existe-fiel |
| **S6 wire-sink** `Event→SDKMessage` | T2-COSTURA (battery) | integrador (`subscribe_all(ser)`) | BFF/REPL | ausente |
| **(dispatch)** `ToolDispatcher`+`ToolPool` | T2-BASE | loop `_build_tool_pool` | base | existe-fiel |
| **S19/S20 repo/scope** `TaskRegistry`/`SessionRepo` | T2-COSTURA/T3 | runtime/driver | integrador (id-opaco+repo) | existe-mímica |
| S2 abort · S3 auth | T1-MOTOR/costura | bridge | provider/integrador | roto/ausente |
| S4 `AgentRuntime` façade | T2-COSTURA | integrador | `LocalAgentRuntime`/integrador | existe-fiel |
| S7 `on_progress` · S8 `HookRunner` | T2-COSTURA | dispatcher / loop | EventBus / integrador (06) | ausente/parcial |
| S9 `CompactionProvider` · S10 `RetryPolicy` | T2-COSTURA | loop | battery compaction/resilience | sin-motor/ausente |
| S11 `UserInputProcessor` · S12 `PathPresentation` | T2-COSTURA | loop / dispatcher | battery commands / integrador | sin-poblar/fiel |
| S13 `StorageContract` · S14 `ConfinedFilesystem` | T2-COSTURA/base | fs-tools/plan/`_persist` | integrador (FS/MinIO) | fiel |
| S15 `ToolExecEnvironment` | T2-COSTURA | `bash.py:27` | `LocalExecEnvironment`/integrador | fiel |
| S17 `PermissionGate` | T2-COSTURA | loop `PRE_TOOL_USE` | integrador (política) | parcial-vivo |
| S18 `SubagentRunnerProtocol` | T2-COSTURA | `AgentTool` `agent.py:105` | `LocalAgentRuntime` vía adaptador | **sin-poblar (crítico)** |
| S21 `NotificationSink` · S22 `ForceAsyncPolicy` | T2-COSTURA | child / dispatch | integrador | put-sin-drain/ausente |
| S23 `on_agent_teardown` · S24 `arm_watchdog` | T2-COSTURA | `_run_loop` / `dispatch` | 10/11/12 / integrador | ausente/noop |
| S25 `AgentDefinition` · S26 `DeferredToolStrategy` · S27 deps-DI | contrato/base | resolver / loop | integrador / base | parcial/fiel |

### 2.1 SEAM-DE-IDENTIDAD/SESIÓN (transversal) — 🟨 tocado por la espina, consolida A3.DA
> Patrón **id opaco + repo genérico** por subsistema stateful. Ningún objeto global de identidad en el runtime.
> **Nido central = `SessionRepo` (05·E30, `SEAMS §S20`).** Touchpoints ya identificados en la espina (nota-identidad):
> `SessionRepo` (05·E30) · `TaskRegistry` repo (05·E9) · scoping notif/transcript (05·E5/E7, clave repo genérico) ·
> ids opacos de ejecución (05·E3/E8/E33/E35/E36) · resume (05·E26) · `metadata.user_id` del model-call (16·B10) ·
> `StorageContract` token→path (09·G6) · discovered-set por `agent_id` (09·E5) · `session_id`/`uuid` del wire (07·B3) ·
> índice de sesiones `SDKSessionInfo` (07·K5→15). **Mímica a ripear:** `_build_child` autogenera `sess_…`/`user_…`
> (05·`_build_child:205-218`; 01·CTR-05 `runtime.py:208-209`). **Se consolidan en el rollup transversal (`DEUDA-A.md`,
> A3.DA), no aquí** (no se resuelve categoría a categoría).
>
> **Cotejo 1:1 tras A3.DA (`DEUDA-A.md §2.8`, verificado contra código):** 9 de estos 11 quedan con cableado
> desarrollado en ID-1..ID-7. **Los 2 que NO:** (5) **`resume`** — `00-INTEGRADORES §1.3` declara la firma
> `LocalAgentRuntime.resume(agent_id, message)` y **ese método no existe** (`execution/local/runtime.py` leído
> 1→EOF) ⇒ **CORE-GAP nuevo, hogar `05·execution`**; (8) **discovered-set `09·E5`** — comparte el `agent_id`
> inestable con la memoria, pero ID-5 sólo cablea la clave de memoria ⇒ **extender el cableado de ID-5**.

---

## 3. BATTERIES — paquetes estándar OPCIONALES (derivados del canónico) — ✅ espina (A1.7) + ✅ **A3.CAT**
> Cada battery: nombre · alcance · costura(s) por las que se compone · origen. Se **compone o sustituye, nunca
> sobreescribe**. Catálogo formal = **`BATTERIES.md`** (A3.CAT); aquí, las que **emergen de la espina** + punteros a las de A3.
>
> **✅ A3.CAT (2026-07-26) — `BATTERIES.md` es ahora la fuente de verdad del catálogo.** Esta tabla queda como la
> **vista de espina** (11 filas); el catálogo completo son **33 unidades de composición** en 6 bloques (estrategia ·
> subagente · capabilities · persistencia · tools nativas · helper). Veredicto: **ninguna battery es obligatoria**;
> lo obligatorio es que el integrador declare su **perfil** (`BATTERIES.md §1`, 3 perfiles). La nota "NO son
> batteries" de abajo se amplía en **`BATTERIES.md §5`** (13 exclusiones con su razón y su dueño).

| battery | alcance | costura de composición | origen (espina) |
|---|---|---|---|
| **compaction** | motor de compactación/presupuesto de contexto: trigger por umbral + microcompact/snip/collapse + tool-result-budget + boundary/vista + PTL-recovery + cache-edits; emite `CompactBoundaryEvent` | S9 `CompactionProvider` + trigger del loop | 02·B1-B9/C9/D1 · 01·CTR-09 · 07·H1 · 16·C2 |
| **resilience** | retry/backoff+jitter/retry-after + 529→fallback-de-modelo + streaming→non-streaming + idle-watchdog; emite `ApiRetryEvent` | S10 `RetryPolicy`/`with_retry` (en el loop) | 16·B1-B4 · 02·C4/C5/C7/D2 · 07·J3 |
| **caching** | estrategia rica de `cache_control` (TTL-elegibilidad/scope/skip-write/cache_edits + split de bloques cache-scoped del system prompt) | envuelve la maquinaria wire del motor | 16·A1/B6 |
| **budget** | token-budget auto-continue +500k con nudge/diminishing-returns + cost-cap por request | consume usage-accounting (S1) + coste/modelo (16) | 02·E1/D6/B9 · G2 |
| **commands** | drain de comandos encolados + lifecycle + preproceso slash/inline | S11 `UserInputProcessor` | 01·CTR-12 · 02·G1/F8/F14 · 07·J6 (cross 12) |
| **wire** | serializador `Event→SDKMessage` (24 variantes) + `SessionInfo` sobre `stream()`; produce init/result/session_state al wire | S6 wire (subscribe_all) | 07·GAP-EVT5/K4/K5 |
| **structured-output** | `SyntheticOutputTool` + `jsonSchema` con reintentos; endpoints tipados del BFF | S16 `output_schema` + driver (05) | 02·G3 · 09·A15/A22 |
| **voice** | STT `AudioInput`→prompt **+ TTS `SpeechSink` de salida** (alcance AMPLIADO por 17: la espina A1.7 sólo vio la entrada; `17·CG-V1` mostró que **ambos** canales están horneados en `LocalAgentRuntime`) | shape opcional del contrato + `EventEnvelope` (K4) para la salida | 01·CTR-06 · **17·CG-V1/V2/V3/V4** |
| **result-summary** | condensación **final-only** del resultado del subagente antes de inyectarlo al padre (cableado `runtime.py:410`) | componible en el ciclo de vida | 05·E29 |
| **handoff-classifier** | classifier de seguridad del output del subagente (feature-gated) | hook de política / battery seguridad | 05·E27 |
| **background-agents** | post_turn_summary (status_category/needs_action/artifact_urls) | battery → 05/13 | 07·F3 |
| _(alimentadas, hogar A3):_ **memory** (13, prefetch/extract 02·E2/F9) · **skills** (12, discovery-prefetch 02·F10) · **attachments** (03/13, 02·F7) · **mcp** (11, 07·J5) · **plan** (14) | | | |

> **NO son batteries** (son base-mecanismo/costura): ensamblado/dispatch/deferral/confinamiento (09), el esqueleto del
> loop y el error-recovery resiliente (02·C4/C5/C7/D2), el ciclo de vida/fork/reaping (05). Sólo la **estrategia**
> (compactación, condensación, caché, budget, resiliencia) y las **tools concretas** son componibles. `tool-builder`
> (09·A21) = helper opcional. `ToolSearch` = **infra base**, NO battery (necesaria para el mecanismo de deferral).

---

## 4. INTEGRADORES — productos sobre el base (validación viva de B)
> **La guía de implementación detallada de los integradores vive en su gemelo `00-INTEGRADORES.md`** (lado
> implementador; secuencia `agentic_code` → `agentic_assistant`; Fases E–F). Esta sección es sólo el índice/puntero.
> No se construyen en Fase A; se listan para saber **qué costura consume cada uno** (los dos extremos del espectro).
> **Estado: ⬜ vacío (referencia → detalle en `00-INTEGRADORES.md`).**

### 4.1 `agentic_code` (CLc-like — integrador FINO/degenerado) — 🟨 sembrado A1.7
> Compone muchas batteries; consumidor natural de las capacidades estilo asistente-de-programación. NO es Claude Code.
> **Realización DEGENERADA del contrato base común** (detalle en `00-INTEGRADORES.md §2.1`, vertido A1.7): identidad
> single-session scope-por-cwd (defaults minimal, cero ceremonia); `SessionRepo`/`TaskRegistry` default; caller = bridge
> `AgenticModelsCaller`; interfaz = terminal (render + `claude ps` + prompt de aprobación); force-async **off**; sin
> billing/multi-tenant. Consume: S1/S4/S5/S13/S15/S16/S18 + política de permisos terminal (S17).
_(costuras que consume: perfil sembrado en A1.7; se cierra en A2.5 y A-CIERRE)_

### 4.2 `agentic_assistant` (openclaw-like — integrador COMPLEJO)
> Multi-canal/multi-tenant; **posee** su orquestación y compone selectivamente. NO es openclaw.
> Consume el runtime por el **protocolo message/tool/event/stream + motor** (no necesariamente los repo-seams). NO es openclaw.
_(costuras que consume: pendiente — se perfila en A-CIERRE / Fase F)_

---

## 5. CORE-GAPs y deudas (punteros)
> No se desarrollan aquí; punteros a los docs de rollup.
- **DEUDA-A** (CORE-GAPs consolidados, brechas A↔B reales) → `DEUDA-A.md` (A3.DA). **Estado: ✅ 2026-07-25** —
  ≈152 entradas de las 18 §2.3, ordenadas keystone-first (**K1** modos de permiso/GAP-02 · **K2** hilo de
  identidad · **K3** guard-path · **K4** sobre del evento · **K5** `ToolResult` · **K6** compactación · **K7**
  fork/runner · **K8** fail-fast) + el hilo de identidad desarrollado (ID-1..ID-7, 6 campos L05) + §4 lo que NO es
  DEUDA-A (RB-1..6, DEUDA-B, caras-aguas-abajo, 🔀, ⛔). **+ tramo de re-verificación** (3 docs 1→EOF + 11
  archivos de código; ~20 anclas contrastadas, todas exactas): **4 hallazgos nuevos** — **H-1** el autogen de
  `user_id` rompe el scope persistente de la memoria · **H-2** el guard-path debe cubrir el segmento absoluto ·
  **H-3** `LocalAgentRuntime.resume` **no existe** (CORE-GAP nuevo, hogar 05) · **H-4** el discovered-set `09·E5`
  no queda cableado por ID-5.
- **DEUDA-B** (higiene interna del runtime: borrar/cablear) → `DEUDA-B.md` (A3.DB), desde `../DEUDA-B-transversal.md`.
  **Estado: ✅ 2026-07-25 (A3.DB) + tramo de re-verificación `A3.DB·RV` ✅ 2026-07-26.** *(Este puntero decía ⬜ hasta
  A3.CAT: estado rancio, corregido — `BATTERIES.md §6·CAT-h4`.)* 6 de 7 ítems del tracker **recalificados a
  CORE-GAP** (sólo `B-orphans` es DEUDA-B pura); reparto final **12 BORRAR / 12 CABLEAR**; conteo **18=18=0**; los
  globales son **7 en 3 clases** y el corte es *«¿dos tenants se ven?»*, no *«¿es mutable?»*. Remedio estructural
  permanente nacido aquí: **`EVIDENCIA.log`** (append-only, una línea por lectura escrita AL LEER). Reglas duras:
  **BORRAR se escribe a nivel de SÍMBOLO, nunca de módulo** (RV-6) · **un docstring no es evidencia de cableado**
  (RV-5). Hallazgo `RV-7` = **H-5** (canal de notificación background sin drenador) → se incorpora en A-CIERRE.
  **`DEUDA-B.md` NO tiene addenda de ítems nuevos:** A3.CAT intentó abrir `CAT-DB-1` y lo **retractó** en su propio
  gate (`DEUDA-B.md §10` + `BATTERIES.md §6·CAT-h7`) — `§4·cabo 7` ya había fallado que el `:146` es **decisión de
  composición, no deuda**. El reparto 12/12 y el conteo 18=18=0 quedan intactos.
- **BATTERIES** (catálogo de paquetes componibles) → `BATTERIES.md` (A3.CAT). **Estado: producto ✅ / verificación
  parcial 2026-07-27** — 33 unidades + 13 exclusiones razonadas, 5 cabos resueltos, **11 hallazgos** (CAT-h1..h11),
  reconciliación **item-level 34 = 33 + 1 = 0 sin colocar**. **V1 y V4 CERRADOS en el gate** abriendo `SEAMS.md`
  (436) y `DEUDA-A.md` (647) **1→EOF** ⇒ **el contenido del catálogo ya no tiene pendientes que puedan cambiarlo**;
  quedan **V2/V3/V4'/V5/V7 (procedencia)** y **V6 (doble filo: 10 de 33 con cara-base vacía por ausencia)**.
  **Producto del cierre de V1:** las costuras de voz quedan numeradas **S30 `PromptSourceProtocol`** (entrada,
  pre-loop) y **S31 `SpeechSink`** (salida, sobre S5, detrás de K4) en `SEAMS.md`, con S12 corregida a
  `existe-parcial` y el índice a **29**.
- ⚠ **Corrección pendiente en `DEUDA-A.md` (CAT-h10):** su `§1.1·K4` y su `§2·ID-6` siguen diciendo
  **`EventEnvelope`**, forma que **`DEUDA-B §7.2` descartó** con razón verificada (`bus.py:40` despacha por
  `type(event)` ⇒ envolver rompe el despacho tipado). La forma vigente es **campos de identidad en el `Event`
  BASE**. **A-CIERRE lo aplica en `DEUDA-A`**, que es donde se lee.

---

## 6. Trazabilidad de llenado (bitácora del skeleton)
| sección | se llena en | fuente | estado |
|---|---|---|---|
| 1.1 contratos | A1.7 | 01·contracts | ✅ A1.7 |
| 1.2 costura motor | A1.7 | 16·models | ✅ A1.7 |
| 1.3 mecanismo | A1.7 | 07·events, 02·loop, 05·execution, 09·tools-infra | ✅ A1.7 |
| 1.4 base resto | A-CIERRE | A3.* | ⬜ |
| 2 costuras (índice) | A1.7 (+ `SEAMS.md`) | espina | ✅ A1.7 (27 firmas en `SEAMS.md`) |
| 2.1 seam identidad | A3.DA | transversal | 🟨 A3.DA (`DEUDA-A.md §2`, ID-1..ID-7 con 6 campos). **9/11 touchpoints con cableado desarrollado**; faltan **H-3** (`resume` **no existe** en `LocalAgentRuntime` — CORE-GAP nuevo, hogar 05) y **H-4** (discovered-set `09·E5` no cableado por ID-5). ✅ al cerrarlos en A-CIERRE |
| 3 batteries (índice) | A3.CAT (+ `BATTERIES.md`) | todas | ✅ **A3.CAT** — **33 unidades** en 6 bloques; **ninguna obligatoria**, 3 perfiles; 5 cabos resueltos (persistence=**4 unidades/1 distribución** · skills+mcp_skills=**2** por el criterio ejecutable de OI-FAC-1 · plan=**battery opcional** · voz: salida=**S31 sobre S5+K4**, entrada=**S30**); **13 exclusiones** razonadas en `§5`; `battery_builtin_agents` **eliminado** (anti-padding). **Gate (2026-07-27):** `SEAMS.md` y `DEUDA-A.md` abiertos **1→EOF** ⇒ voz numerada **S30/S31**, S12→`existe-parcial`, índice de costuras **29**; reconciliación item-level **34=33+1=0**; **11 hallazgos** (CAT-h1..h11). Límite que queda: **10 de 33 con cara-base vacía por ausencia** (mímica, no des-fusión) y S28/S29 sin validar |
| 4 integradores | A-CIERRE | A2.5 + diseño B–F | 🟨 agentic_code degenerado (A1.7) + perfiles de composición propuestos (`BATTERIES.md §1`, **no validados contra integrador vivo**) |
| 5 deudas | A3.DA / A3.DB / A3.CAT | rollups | 🟨 `DEUDA-A.md` ✅ A3.DA (8 keystones K1-K8 + hilo ID-1..ID-7) **+ H-5 post-cierre**; `DEUDA-B.md` ✅ A3.DB **+ `A3.DB·RV`** **+ CAT-h3 post-cierre**; `BATTERIES.md` ✅ A3.CAT. Pendiente en A-CIERRE: **CAT-h1** (`resume` figura como battery en `05·§2.2` y es CORE-GAP) y **CAT-h2** (`DEUDA-A §1.2(b)` archiva los ítems de 09 bajo BATTERY siendo base-mecanismo) |
