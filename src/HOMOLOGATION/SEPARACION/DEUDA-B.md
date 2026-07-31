# DEUDA-B · clasificación por TIER + decisión borrar-vs-cablear (ciclo A3.DB)

> **Rollup transversal hermano de `DEUDA-A.md`.** Mientras `DEUDA-A.md` consolida los **CORE-GAP** (capacidad
> que el base/battery **debe** reproducir y hoy no reproduce), este doc consolida el **tier `DEUDA-B` del
> `00-LEGEND §2.2`**: *higiene interna del runtime* — huérfanos a **borrar** o costuras a-medio-cablear a
> **cablear**. No es deuda A↔B. Cerrado 2026-07-25.

---

## 0. Alcance, corpus y qué se hereda

### 0.1 Corpus — CON EL ESTADO DE EVIDENCIA CORREGIDO (2ª corrección, tras el gate del usuario)

> **⚠ CORRECCIÓN DE HONESTIDAD.** La 1ª redacción de este §0.1 titulaba *"Corpus abierto ESTE ciclo
> (post-compactación; re-abierto, no heredado)"*. **Eso es FALSO** y repite exactamente el defecto que
> `DEUDA-A §0.1` ya se había cazado. El ciclo A3.DB sufrió **una compactación de contexto**: la recolección
> de evidencia ocurrió ANTES, y la redacción del documento DESPUÉS. Salvo los 10 archivos listados en la
> tabla T1 de abajo, **el contenido de los demás me llegó por el RESUMEN de la compactación, no por mi
> propia lectura en contexto**. Por mi propia regla (*una lectura previa a una compactación no cuenta como
> "abierta este ciclo": o se re-abre, o se declara HEREDADA*), lo correcto es lo siguiente.
>
> **T1 · PRIMERA MANO 1→EOF, post-compactación (10 archivos, 475 líneas):** `storage/factory.py`1→33 ·
> `storage/protocol.py`1→87 · `events/protocol.py`1→23 · `events/bus.py`1→46 · `events/event_types.py`1→44 ·
> `models/protocol.py`1→37 · `execution/runner.py`1→41 · `tools/protocol.py`1→61 · `loop/factory.py`1→27 ·
> `capabilities/contracts.py`1→76.
> **T2 · POR TRAMO, post-compactación:** `execution/local/runtime.py:134-183` y `:234-308` ·
> `loop/agent_loop.py:206-255` · `capabilities/mcp/auth.py:30-74` · `models/caller.py:1-60`+firma por grep ·
> el censo de globales (3 pasadas de grep + apertura de cada hallazgo).
> **T3 · HEREDADO del tramo compactado** (leído en este ciclo, pero **no re-abierto** tras la compactación):
> el tracker `../DEUDA-B-transversal.md`1→332 · `00-LEGEND.md`1→159 · los **18 tramos §2.4** · y los
> **~13 archivos de código restantes** de la tabla siguiente (`factory.py`267 · `runtime.py`435 íntegro ·
> `agent_loop.py`352 íntegro · `dispatcher.py` · `resolver.py` · `signals/`×2 · `modes/`×2 ·
> `observer/`×3 · `tasks/registry.py` · `task_tools.py` · `notification.py` · `session/session.py` ·
> `hooks/runner.py` · `mcp/config.py` · `skill_tool.py` · `native_registry.py`).
>
> **Qué significa y qué no.** No invalida el ciclo: el trabajo se hizo, y los 10 de T1 —re-abiertos en el
> tramo de reparación— **confirmaron cada ancla que sostienen** (`ToolResult.__init__` con 6 campos ·
> `ToolProtocol.category` · `log_key` sin dueño · `CapabilityActivation` inerte · `create_loop` sobre
> `capabilities_resolver` · `_runner` global). Pero **T3 no puede presentarse como primera mano**, y las
> decisiones de **BORRAR** que dependen sólo de T3 —`modes/`, `observer/`, `signals/`, `native_registry`,
> `auth_headers()`— quedan **con evidencia heredada declarada**, no confirmada en contexto.
>
> **Omisión detectada al re-abrir `storage/protocol.py`:** §3.A·DB-16 enumera como hermanos de `log_key`
> sólo `config_key`/`meta_key`/`work_key`/`transcript_key`. **Son 6, no 4**: faltan `agent_md_key`(:57) y
> `ltm_key`(:61), igualmente sin consumidor de producción. No cambia la decisión sobre `log_key`, pero el
> inventario estaba incompleto.

> **✅ 3ª redacción (2026-07-26) — T3 RESUELTO, y ahora GENERADO, no recordado.** El tramo de
> re-verificación **A3.DB·RV** re-abrió 1→EOF, en contexto, **todo el conjunto T3**: el tracker
> `../DEUDA-B-transversal.md`1→332 · los tres ensambladores grandes (`factory.py`267 ·
> `execution/local/runtime.py`435 · `loop/agent_loop.py`352) · y los 11 archivos de código de los que
> dependen decisiones de BORRAR (`tasks/registry.py`166 · `task_tools.py`223 · `dispatcher.py`85 ·
> `resolver.py`82 · `skill_tool.py`123 · `notification.py`72 · `modes/protocols.py`16 ·
> `signals/protocols.py`14 · `observer/events.py`23 · `observer/__init__.py`11), **más** los 18 del tramo T1.
> ⇒ **ninguna decisión de BORRAR descansa ya en evidencia heredada.**
>
> Lo único que permanece **HEREDADO declarado**: `00-LEGEND.md`1→159 y los **18 tramos §2.4** de los docs de
> categoría (fuentes de las entradas DB-16..DB-28 de §2.b). No sostienen ninguna orden de borrado de código
> por sí solos.
>
> **Cambio de método, no sólo de contenido.** Este §0.1 ya **no se redacta de memoria**: se genera desde
> `SEPARACION/EVIDENCIA.log`, un registro *append-only* escrito **en el momento de leer**, con
> `archivo · rango · 1→EOF|tramo · qué ancla sostiene`. Razón: los dos fallos de honestidad de este ciclo
> no ocurrieron en las clasificaciones (que sobrevivieron intactas ambas veces) sino en el **estado de
> evidencia auto-reportado**, y la regla «declara HEREDADA lo leído antes de una compactación» es
> **inaplicable por introspección** — un hecho resumido se siente idéntico a un hecho leído. Un archivo en
> disco sobrevive a la compactación; el contexto no. Regla operativa: *si una lectura no está en
> `EVIDENCIA.log`, para efectos del gatekeeper no ocurrió.*

### 0.1b Corpus (inventario, con el tier de evidencia de §0.1 aplicado)

**Método (PASO 0):** las 11 lecciones + README de `~/.claude/skills/analisis-comparativo-ab/lecciones/`
1→EOF (12 archivos, ~547 líneas). El mirror `learned_lessons/` está RETIRADO.

**Fuente primaria:** `../DEUDA-B-transversal.md` **1→332 (ÍNTEGRO)**.

**Esquema y gate:** `00-LEGEND.md` 1→159 (TIER §2.2; gatekeeper §3.3 líneas 111-134).

**Hermanos:** `DEUDA-A.md` §4(b)/(c)/(f) + §5 (líneas 579-646) + §0.1b; `PLAN.md` §4-A3 (76-88) y §7 (102-132).

**Barrido §2.4 de las 18 categorías** (re-abierto ESTE ciclo tras la compactación, rangos exactos):
`01:61-66` · `02:148-152` · `03:154-159` · `04:129-137` · `05:152-158` · `06:248-255` · `07:121-128` ·
`08:245-283` · `09:182-185` · `10:238-256` · `11:235-257` · `12:229-266` · `13:226-238` · `14:275-292` ·
`15:186-194` · `16:140-146` · `17:352-360` (numerada §2.6) · `18:290-302`.

**Código del runtime abierto 1→EOF ESTE ciclo (18 archivos, 2.352 líneas)** — cada decisión de abajo se
apoya en uno de éstos, no en grep:

| archivo | L | qué prueba |
|---|---|---|
| `factory.py` | 267 | ensamblador raíz: ausencia de `set_runner`/`set_registry`/`set_observer`; `PlanModeProvider()` :146; `agent_resolver` :237; ternario muerto :129; `CapabilitiesResolver` :197-201,222 |
| `execution/local/runtime.py` | 435 | ensamblador de ejecución: `_run_loop` 306-416; `_persist` 418-432 (`"anon"` :424); `_wire_tts` 234-262; `_resolve_prompt` 220-232; `agent_resolver` 342-343 |
| `loop/agent_loop.py` | 352 | ensamblador de turno: rama viva :194-200 vs rama muerta :201-205; gate PreToolUse :300-313 (descarta `additional_context`); `context_modifier`/`ends_turn` por `getattr` :332/:338; literal `"tool_calls"` :348 |
| `tools/protocol.py` | 61 | `ToolResult.__init__` :21-36 declara SÓLO 6 campos; `ToolCategory` :10-19; `category` :56 |
| `tools/dispatcher.py` | 85 | gate deny-por-nombre :62-65; despacho **unitario** (no `dispatch_many`) |
| `capabilities/resolver.py` | 82 | el resolver legacy que muere |
| `capabilities/contracts.py` | 76 | `CapabilityActivation` :26-38 + export :72-76 |
| `loop/factory.py` | 27 | `create_loop` cablea exactamente la rama muerta |
| `loop/protocol.py` | 27 | `LoopProtocol`/`DrainableLoopProtocol` |
| `storage/protocol.py` | 87 | `log_key` :85-87 vs los 4 vivos |
| `signals/bus.py` + `signals/protocols.py` | 96+14 | `register_handler` :89-96 nunca invoca `handle_signal`; `RESUME` limpia la señal :68-69 |
| `modes/manager.py` + `modes/protocols.py` | 44+16 | `ModeManager` completo, sin productor |
| `execution/observer/{observer,events,__init__}.py` | 37+23+11 | `get_observer` sin call-site |
| `execution/tasks/registry.py` | 166 | global `_registry` :153-166 + `InMemoryTaskRegistry` vivo |
| `tools/native/task_tools.py` | 223 | consume el global en :29/54/113/187 |
| `execution/runner.py` | 41 | `SubagentRunnerProtocol` + global `_runner` :28-41 |
| `execution/local/notification.py` | 72 | global `_channel` :22 |
| `execution/session/session.py` | 59 | `Usage` (BaseModel, i/o) :16-18 |
| `events/event_types.py` | 43 | `Usage` (dataclass, i/o/thinking) :9-13 |
| `hooks/runner.py` | 63 | agrega `additional_context` :54-59 |
| `models/protocol.py` | 37 | `ModelRequest` :11-19 vs `complete(...)` :28-37 |
| `capabilities/mcp/config.py` | 129 | `auth_headers()` :97-102 |
| `capabilities/mcp/auth.py` | 123 | `_build_bearer` :73-75 = la ruta viva |
| `capabilities/mcp/client.py` | :80-139 | el merge real de headers :106 |
| `capabilities/skills/skill_tool.py` | 123 | schema anuncia `args` :88, `execute` :107-120 no lo lee |
| `tools/native/agent.py` | :80-119 | `get_runner()` :105 dentro de try/except → `ToolResult.error` |
| `tools/native_registry.py` | 41 | `NativeToolRegistry` completo |

*(Nota de honestidad: `client.py` y `agent.py` se abrieron por TRAMO, no 1→EOF — se declara así; sus
tramos son los que sostienen las afirmaciones LAT-MCP1 y B-runner-wiring respectivamente.)*

### 0.2 Lo que se hereda DECLARADO (no se re-abrió este ciclo)

Cabo 6 del enunciado: las 6 confirmaciones de primera mano de `DEUDA-A §0.1b` podían tomarse por cerradas.
**No hizo falta heredarlas: 5 de 6 se re-abrieron aquí** (`B-runner-wiring` por `factory.py`+`runner.py`+
`agent.py:105`; `B-dead-resolver` por `factory.py:197-201`+`agent_loop.py:194/201`; `B-dead-ternary` por
`factory.py:129`; `"anon"` por `runtime.py:209/424`; `B-global-registries` parcial). **La única HEREDADA es
`LAT-MODELS1`** en su mitad *"el factory nunca registra los `Model` extra en `agentic_models`"*: verifiqué
por lectura de `factory.py` 1→EOF que `_build_local` **no lee** `config.models` (ausencia), pero **no abrí
`agentic_models`** para comprobar qué haría ese registro. La ausencia en el ensamblador es de primera mano;
la contraparte, heredada de 16·§2.4.

**Delta honesto sobre `18·N4`:** N4 declara **6** almacenes globales de proceso. Verifiqué **4** de primera
mano (`_registry` registry.py:153 · `_runner` runner.py:28 · `_observer` observer.py:28 · `_channel`
notification.py:22 — los 3 primeros por `global`, el cuarto por mutación in-place). Los **2 restantes de la
lista de N4 NO los re-verifiqué**: no los afirmo ni los niego aquí.

---

## 1. Regla de clasificación (choque de nombres, resuelto)

El tracker llama **"Deuda B"** a *deuda transversal entre subsistemas*. El `00-LEGEND §2.2` llama
**`DEUDA-B`** a un **TIER**: *higiene interna del runtime* (huérfano a borrar / costura a medias a cablear).
**No son lo mismo.** El precedente lo fijó `07·§2.4` al recalificar `B-usage` de "Deuda B" → **CORE-GAP**,
dejando sólo `E4` como tier DEUDA-B puro. A3.DB aplica ese criterio a los 7 ítems:

> **Criterio:** si el ítem describe **capacidad que el canónico tiene y B no** → tier **CORE-GAP** (hogar
> `DEUDA-A.md`), **no se re-cuenta aquí** (L10 anti-padding). Sólo su **faceta B-interna** —maquinaria
> duplicada-muerta o cañería a medias— es tier DEUDA-B.

Resultado del corte: **de los 7 ítems del tracker, 6 son mayoritariamente CORE-GAP** y **1 (`B-orphans`) es
íntegramente tier DEUDA-B**. Las facetas B-internas de los otros 6 suman 8 entradas. Total tier DEUDA-B
clasificado: **21 entradas** (10 de `B-orphans` + 8 facetas + 3 nuevas del barrido §2.4 no listadas en el
tracker: `log_key`, `LAT-CAP1`, `create_loop`).

---

## 2. Ledger maestro — una fila por CADA entrada del tracker `../DEUDA-B-transversal.md`

**Denominador — CORREGIDO en el tramo RV (tracker abierto 1→EOF, `EVIDENCIA.log` línea 1):** 7 ítems de §.
`B-orphans` desagrega **10** sub-ítems numerados (:71-132) y `B-signals` desagrega **2** sub-ítems
explícitamente rotulados «Sub-ítem» (**SIG9** cleanup/liberación de recursos :204-209 · **SIG13** dos niveles
de abort `work`/`agent` :210-215). ⇒ hojas reales = 6 + 10 + 2 = **18**. La tabla de abajo tiene **16 filas**
(1 + 10 + 5) y declaraba «17»: **el 17 era un error aritmético** y **SIG9/SIG13 nunca recibieron fila**.
Ambos van dentro de la remisión CORE-GAP de la fila 3 (`B-signals`→`AbortScope`, `DEUDA-A:297`) — el destino
no cambia — pero **no estaban nombrados**, y un sub-ítem sin nombre es un sub-ítem que Fase B no implementa.
Filas SIG9/SIG13 añadidas abajo.

| # | ID tracker | TIER real | destino | cara | evidencia | detalle | nota-identidad |
|---|---|---|---|---|---|---|---|
| 1 | **B-02** | **CORE-GAP** (=GAP-02/K1) | `DEUDA-A.md` K1 · residual → **DB-19** | base | `dispatcher.py:62-65` 1→EOF · `factory.py:146` 1→EOF | N/A (tier remitido) | K1 |
| 2.1 | `modes/ModeManager` (FIND-MODE1) | DEUDA-B | **BORRAR** → DB-01 | base | `modes/manager.py`+`protocols.py` 1→EOF · `agent_loop.py:91` | sí | — |
| 2.2 | `execution/observer/` (FIND-EXEC4) | DEUDA-B | **BORRAR** → DB-02 | base | `observer/` 3 arch. 1→EOF · `runtime.py:306-416` 1→EOF (ausencia) | sí | — |
| 2.3 | `SignalBus` (FIND-SIG1) | DEUDA-B | **BORRAR** → DB-03 | base | `signals/bus.py`+`protocols.py` 1→EOF | sí | — |
| 2.4 | `tasks.get/set_registry` (LAT-EXEC1) | DEUDA-B **(defecto activo)** | **CABLEAR→BORRAR** → DB-04 | base | `registry.py:153-166` + `task_tools.py:29/54/113/187` + `runtime.py:86` + `factory.py` 1→EOF | sí | — |
| 2.5 | `NativeToolRegistry` (FIND-TOOL10) | DEUDA-B | **BORRAR** → DB-05 | base | `native_registry.py` 1→EOF · `factory.py:189` · `agent_loop.py:194-195` | sí | — |
| 2.6 | `ToolProtocol.category` (LAT-TOOL1) | DEUDA-B | **BORRAR** → DB-06 | base | `tools/protocol.py:10-19,56` 1→EOF · 0 lectores | sí | — |
| 2.7 | `HookRunner additional_context` (LAT-HOOK1) | DEUDA-B | **CABLEAR** → DB-07 | base | `hooks/runner.py:54-59` 1→EOF · `agent_loop.py:297-313` 1→EOF | sí (6 campos) | — |
| 2.8 | `McpServerConfig.auth_headers()` (LAT-MCP1) | DEUDA-B | **BORRAR** → DB-08 | base | `config.py:97-102` · `auth.py:73-75` 1→EOF · `client.py:106` | sí | — |
| 2.9 | `SkillTool.input_schema.args` (LAT-SKILL1) | DEUDA-B | **CABLEAR** → DB-09 | base | `skill_tool.py:88` vs `:107-120` 1→EOF | sí (6 campos) | — |
| 2.10 | `ModelsConfig.extras`/`ModelRequest` (LAT-MODELS1) | DEUDA-B | **BORRAR (a) · CABLEAR (b)** → DB-10 | base | `factory.py:59-60,83` 1→EOF · `models/protocol.py` 1→EOF · `agent_loop.py:235-239` | sí | — |
| 3 | **B-signals** | **CORE-GAP** (AbortScope, =`DEUDA-A:297`) | `DEUDA-A.md` · residual → **DB-03/DB-11/DB-12** | base | `signals/` 1→EOF · `agent_loop.py:173/186` | N/A (tier remitido) | — |
| 4 | **B-new_messages** | **CORE-GAP** (=K5) | `DEUDA-A.md` K5 · residual → **DB-13** | base | `tools/protocol.py:21-36` 1→EOF · `agent_loop.py:319-344` | N/A (tier remitido) | K5 |
| 5 | **B-concurrency** | **CORE-GAP** (=`DEUDA-A:330`) | `DEUDA-A.md` · residual **0** | base | `dispatcher.py` 1→EOF (sin `dispatch_many`) · `agent_loop.py:287` (bucle serial) | N/A (tier remitido) | — |
| 6 | **B-usage** | **CORE-GAP** (tier ya corregido en 07·§2.4) | `DEUDA-A.md` · residual → **DB-14/DB-15** | base | `events/event_types.py:9-13` + `session/session.py:16-18` 1→EOF · `runtime.py:403-404` | N/A (tier remitido) | — |
| 7 | **B-structured-output** | **CORE-GAP** (=K5) | `DEUDA-A.md` K5 · residual **0** | base | `tools/protocol.py:21-36` 1→EOF | N/A (tier remitido) | K5 |
| 3.1 | **SIG9** cleanup al abortar mid-turn (tracker :204-209) | **CORE-GAP** (sub de B-signals) | `DEUDA-A.md` con `AbortScope` — `on_abort(cb)` LIFO; 11·mcp registra su release | base | tracker 1→EOF · `dispatcher.py:54` 1→EOF (abort sin cleanup) | N/A (tier remitido) | — |
| 3.2 | **SIG13** dos niveles de abort `work`/`agent` (tracker :210-215) | **CORE-GAP** (sub de B-signals) | `DEUDA-A.md` con `AbortScope` — `interrupt(level=…)`; habilita 05·EXEC12 | base | tracker 1→EOF · `runtime.py:187-188` (`cancel`→`kill`, un solo nivel) 1→EOF | N/A (tier remitido) | — |

**Reconciliación (corregida en RV):** entradas hoja del tracker = **18**; colocadas = **18** (16 filas
originales + SIG9 + SIG13); sin colocar = **0**. *(La cifra «17=17=0» de la 1ª redacción era falsa por
partida doble: sobrecontaba en 1 y omitía 2.)*

### 2.b Entradas tier DEUDA-B **no listadas en el tracker**, recogidas del barrido §2.4

| # | origen | destino |
|---|---|---|
| DB-16 | `15·§2.4` `StorageKeys.log_key` slot muerto | **BORRAR** |
| DB-17 | `12·§2.4` `LAT-CAP1` `CapabilityActivation` inerte | **BORRAR** |
| DB-18 | `18·§2.4` `B-create-loop` (+`B-dead-resolver`) | **CABLEAR (create_loop) + BORRAR (resolver)** |
| DB-19 | `01·CTR-08`/`02·F2`/`03·B2`/`09` hack `app_state.native["plan_mode"]` | **BORRAR (secuenciado tras K1)** |
| DB-20 | `18·§2.4` `B-untyped-composition` (21 slots `Any`) | **CABLEAR** |
| DB-21 | `18·§2.4` `B-dead-ternary` `factory.py:129` | **BORRAR** |
| DB-22 | `18·§2.4` `B-unreachable-knobs` (`default_timeout`/`deferred_strategy`/`tool_dispatcher`) | **CABLEAR (exponer)** |
| DB-23 | `18·§2.4` `B-global-registries` (umbrella) | **política — ver §3.C** |
| DB-24 | `17·§2.6` superficie de voz en el base (3 filas) | **BORRAR (al extraer battery)** |
| DB-25 | `17·§2.6` literal `stop_reason=="tool_calls"` duplicado | **CABLEAR (vocabulario T1)** |
| DB-26 | `15·§2.4` `"anon"` inalcanzable `runtime.py:424` | **BORRAR (secuenciado tras H-1)** |
| DB-27 | `05·§2.4` `B-runner-wiring` (S18/C1) | **CABLEAR (crítico)** |
| DB-29 | **(RV)** canal de notificación background sin drenador en el base — `notification.py:45-72` | **CORE-GAP — ver §9·RV-7** |
| DB-30 | **(RV)** `_MAX_TURNS = 50` hardcodeado `agent_loop.py:24` | **CABLEAR (se pliega en DB-22)** |
| DB-28 | `11` `McpState.pending_servers()` accesor sin lector de prod (tracker :102-103, no listado antes — RV-3) · `01·CTR-13` `@runtime_checkable` inconsistente · `01·CTR-15` `arm_watchdog` no-op · `01·CTR-11`/`03·D2` `to_llm` sin call-site · `03·C3` `apply_context_modifier_compat` · `03·A+` autogen `user_/sess_` · `10·G1` conflación tasklist↔registry · `11` `McpServerConfig.model` | **menores — ver §3.D** |

*(No se re-cuentan, por L10, las 4 caras aguas-abajo que `DEUDA-A §4(c)` ya excluyó: `compact_context()==[]`
×4 · `is_session_plan_file` · `EXPLORE/PLAN_AGENT_TYPE` · la mitad A↔B de `LAT-HOOK1`/`to_llm`.
Tampoco se inventa deuda para `04`, `13` y `14`, que cerraron con **CERO** DEUDA-B propia.)*

---

## 3. Inventario clasificado: BORRAR vs CABLEAR

### 3.A — BORRAR (duplicados-muertos: existe un mecanismo real que ya da el comportamiento)

> **⚙ R-1 · auditoría RV-6 a nivel de símbolo — COMPLETADA (2026-07-28, pasada `A-CIERRE`).**
> `§8` cerró este documento diciendo: *«aplicado ya a DB-01; queda por auditar con ese criterio el resto de
> las entradas BORRAR»*. Eso es lo que hace este tramo. **Ninguna entrada BORRAR queda escrita a nivel de
> archivo/módulo:** cada una lleva ahora un bloque `⚙ RV-6` con (a) los símbolos que **MUEREN**, (b) los
> símbolos que **SOBREVIVEN** al borrado y por qué, y (c) el **colateral** (exports a retirar, tests a
> re-apuntar, call-sites). Sin ese bloque, Fase B ejecutaría "borrar X entero" y destruiría vivo lo que
> comparte archivo con el muerto — el defecto que RV-6 nació para cerrar (`AgentMode` en DB-01).
> **Insumo:** los 16 archivos objeto se abrieron 1→EOF en esta pasada (registrados en `EVIDENCIA.log`);
> `grep` se usó **sólo como localizador** de call-sites (D-05·3), nunca como fuente de veredicto.
> **Resultado global: 2 entradas cambian de alcance (DB-03, DB-24), 3 ganan colateral no declarado
> (DB-06, DB-10, DB-16), 1 gana precondición dura (DB-26); las 5 restantes se confirman tal cual.**

**DB-01 · `modes/` entero** (`manager.py` 44 + `protocols.py` 16 + `__init__.py` 4).
`ModeManager`/`AgentMode`/`ModeManagerProtocol`/`on_transition`. **0 productores de producción**
(verificado: importado sólo por `test_mode_manager.py` 9 tests + `test_modes_homologation.py` xfail).
El eje real ya vive repartido: KIND por `ctx.is_subagent` (`agent_loop.py:91` usa los strings crudos
`"background"`/`"foreground"`, **no** `AgentMode`), backgrounding por `TaskRecord.is_backgrounded`
(`registry.py:26`), fork por `ForkPolicy`. **Impacto:** borra `agentic_runtime/modes/` + su export; los 2
tests se retiran, se deja el guard `test_no_orphan_modemanager_in_real_path`.
**⚠ ALCANCE CORREGIDO (RV-6, tramo de re-verificación — `modes/protocols.py` 1→EOF):** "borrar `modes/`
entero" estaba **mal alcanzado**. El archivo contiene DOS cosas de tier distinto: `ModeManagerProtocol`
(:11-16) = maquinaria huérfana ⇒ borrar; y **`AgentMode`** (:5-8, `FOREGROUND/BACKGROUND/FORK`) =
**vocabulario T1 legítimo**, que es justamente el tipo que `agent_loop.py:91` debería estar usando en vez
de los strings crudos con los que hoy llama a `list_available(mode=…)`. Borrarlo entero **fija los strings
crudos para siempre** y contradice a DB-25, que pide exactamente lo contrario para `stop_reason`.
⇒ **BORRAR `ModeManager` + `ModeManagerProtocol`; CONSERVAR `AgentMode`, reubicado al módulo de
vocabulario T1 junto al `stop_reason` de DB-25, y cablear `agent_loop.py:91` a él.** Misma especie de
defecto que la regla DB-23 mal formulada: una orden de borrado que, aplicada literal en Fase B, destruye
algo vivo.
**⚠ No confundir:** el `PermissionMode` (default/acceptEdits/plan/bypass) de **K1/GAP-02** es OTRO eje y su
hogar es `PermissionContext.mode` en `contracts` — borrar `modes/` **no** le quita hogar.

**DB-02 · `execution/observer/`** (3 archivos, 71 L). `get_observer`/`set_observer`/`SubagentStarted`/
`SubagentStopped`. Leí `_run_loop` 1→EOF (306-416): **nunca** llama `get_observer()`. Su payload ya viaja
por dos rutas vivas: `_task_registry.push_event` (`_make_bus` 264-283) + `_task_registry.complete(...,
duration_ms, turn_count, input_tokens, output_tokens)` (:400-405) + `_fire_stop` → `HookEvent.SUBAGENT_STOP`
(:285-292). **Nada se pierde.** Si se quiere un observer tipado, que sea **suscriptor del EventBus**.
**⚙ RV-6 · CONFIRMADA SIN CAMBIO DE ALCANCE — la única entrada con CERO supervivientes.**
*MUEREN (los 7 símbolos + el paquete):* `ExecutionObserverProtocol` (`observer.py:15-18`), `NoopObserver`
(:20-26), el global `_observer` (:28), `set_observer` (:31-33), `get_observer` (:36-37), `SubagentStarted`
(`events.py:6-11`), `SubagentStopped` (:14-23), y los 3 `__init__`/`__all__` del paquete.
*SOBREVIVEN: **ninguno**.* Verificado **campo por campo** contra `TaskRecord`
(`execution/tasks/registry.py:16-35`), que es el registro de la ruta viva:
`SubagentStopped(task_id·description·status·result·duration_ms·turn_count·input_tokens·output_tokens)` →
los **8** tienen homónimo exacto en `TaskRecord` (:18,19,23,27,30,31,32,33) y los 4 numéricos los puebla
`complete(...)` (`:133-150`, llamada desde `runtime.py:400-405`).
`SubagentStarted(task_id·description·foreground·model_override)` → `task_id`/`description` en `TaskRecord`;
`foreground` = eje inverso de `TaskRecord.is_backgrounded` (:26); **`model_override` NO está en
`TaskRecord`, pero sí está vivo** en `RuntimeTask.model_override` (`contracts/runtime.py:21`), consumido en
`runtime.py:346,351` vía `resolve_subagent_model` (`execution/agents.py:47-55`) ⇒ es duplicado, no
vocabulario huérfano. **Ningún dato queda sin hogar.**
*Colateral:* `execution/__init__.py` (1→EOF, 21 L) **no re-exporta** el paquete ⇒ el radio de explosión es
el directorio + un solo test: el xfail `test_execution_homologation.py:186,195` (`FIND-EXEC4`), que se
**retira** (no se re-apunta: no hay comportamiento que preservar).
*Nota de método (RV-5):* el docstring `observer.py:4-5` afirma que «`LocalAgentRuntime` emite eventos vía
`get_observer()`». **Es falso** — `_run_loop` (306-416) leído 1→EOF nunca lo llama. Se borra con el archivo,
pero queda registrado: es exactamente el tipo de docstring que hizo sobrevivir 18 ciclos a los huérfanos.

**DB-03 · `signals/` entero** (`bus.py` 96 + `protocols.py` 14 + `__init__.py` 4). Huérfano
(0 producción). Absorbe **DB-SIG-2** (`register_handler` :89-96 guarda handlers que `send`/`_apply` nunca
invocan → punto de extensión muerto, cae con el bus) y **DB-SIG-3** (`RESUME` limpia la señal :68-69,
contradiciendo la irreversibilidad one-shot del abort).
**⚠ Secuenciación honesta:** borrar el módulo **NO entrega** el árbol de cascada — ése es CORE-GAP
(`DEUDA-A:297`, `AbortScope`). Y `SignalType.PAUSE/RESUME` es hoy la **única traza nominal** de pausa/reanudación
en el runtime; **H-3 (`resume` no existe, CORE-GAP nuevo, hogar 05)** aún no tiene cableado desarrollado.
⇒ **DB-03 se ejecuta DESPUÉS de que H-3 tenga hogar escrito**, o el vocabulario desaparece sin sustituto.
**⚙ RV-6 · ⚠ ALCANCE CORREGIDO — misma especie exacta que DB-01. La secuenciación NO bastaba.**
Lo escrito arriba sólo **aplaza** el borrado tras H-3; no dice qué se salva. Abierto `signals/protocols.py`
1→EOF (14 L) queda claro que el archivo, igual que `modes/protocols.py`, contiene **dos cosas de tier
distinto**: `SignalHandler` (:11-14) = maquinaria del punto de extensión muerto ⇒ muere; y **`SignalType`
(:5-8, `ABORT`/`PAUSE`/`RESUME`) = vocabulario T1 legítimo** ⇒ **CONSERVAR**.
*MUEREN:* `_Node` (`bus.py:11-14`), `SignalHandle` (:17-27), `SignalBus` (:29-87, con `register`/
`unregister`/`get_signal`/`send`/`_apply`/`_children`), `register_handler` (:89-96, DB-SIG-2: guarda
handlers que `send`/`_apply` nunca invocan), la semántica `RESUME`-limpia-señal (:68-69, DB-SIG-3),
`SignalHandler` (`protocols.py:11-14`) y el `__init__.py` del paquete.
*SOBREVIVE:* **`SignalType`**, reubicado al **mismo módulo de vocabulario T1** al que DB-01 manda `AgentMode`
y DB-25 manda `stop_reason`. Justificación positiva, no por defecto: (a) `ABORT` — la ruta viva de aborto es
`runtime.cancel()` (:187) → `registry.kill()` → `TaskStatus.KILLED`, que es vocabulario **de tarea**, no de
señal; el árbol de cascada sigue siendo CORE-GAP (`DEUDA-A:297`, `AbortScope`) y necesitará este tipo.
(b) **`PAUSE`/`RESUME` no tienen NINGÚN homónimo vivo** en el runtime — ni en `TaskStatus`, ni en
`stop_reason` (hoy `str` crudo, `events/event_types.py:37` + `models/caller.py:227`), ni en `HookEvent`.
Borrarlos deja a H-3 (`resume`, CORE-GAP, hogar 05) **sin una sola palabra que reusar** y fija el patrón de
strings crudos que DB-25 pide revertir. Es literalmente el argumento de DB-01, verbatim, sobre otro enum.
*Colateral:* `signals/__init__.py:4` pasa de 4 a 1 símbolo exportado; `test_signal_bus.py` (13 tests) se
retira entero; `test_signals_homologation.py` conserva sólo lo que hable de `SignalType`, y sus xfails
`FIND-SIG1` (:63) y `FIND-SIG5` (:148) se retiran porque su sujeto (`SignalBus`) deja de existir — **no** se
convierten en tests verdes. `test_runtime_e2e.py:9` es una nota de alcance en docstring: reescribir.

**DB-05 · `NativeToolRegistry`** (`native_registry.py` 41). 0 consumidores de producción; el registry vivo
es `ToolRegistry` (`factory.py:189` → `runtime._tool_registry` → `agent_loop.py:92`). El hot-plug MCP es por
**reensamblado del pool por turno** (`agent_loop.py:194-195`), no por registro dinámico. **Impacto de API
pública:** hay que retirar 2 exports — `agentic_runtime/__init__.py:14,26` y `tools/__init__.py:9,17`.
**Excepción viva:** si `CG-MCP-7` implementa el swap push-based, `unregister_by_prefix` (:34-38) sería su
seam; mientras no, huérfano.
**⚙ RV-6 · CONFIRMADA SIN CAMBIO DE ALCANCE.** `native_registry.py` abierto 1→EOF (41 L): el archivo
contiene **una sola clase y nada más**, así que aquí "borrar el archivo" y "borrar los símbolos" coinciden —
pero se escribe a nivel de símbolo igual, por regla.
*MUEREN:* `NativeToolRegistry` (:6-39) con sus 6 métodos `register`/`get`/`list_tools`/`names`/`unregister`/
`unregister_by_prefix` (:34-38), y `__all__` (:41).
*SOBREVIVEN: **ninguno dentro del archivo**.* No hay vocabulario T1 mezclado: no declara enums, protocolos
ni dataclasses — sólo maquinaria. (Contraste deliberado con DB-01/DB-03, donde sí lo había.)
*Colateral (ya declarado arriba, verificado exacto):* `agentic_runtime/__init__.py:14` (import) y `:26`
(`__all__`); `tools/__init__.py:9` (import) y `:17` (`__all__`). **Único consumidor de test:**
`test_runtime_contracts.py:9,48,55` — se retiran esas 3 líneas, incluida la única prueba de
`unregister_by_prefix` (:55). **Cero referencias fuera de esas 4+3.**
*Cabo abierto que esta auditoría NO cierra:* si `CG-MCP-7` (swap push-based) se implementa, tendrá que
**re-crear** `unregister_by_prefix` sobre `ToolRegistry`, no resucitar esta clase. Queda anotado en la
remediación de `CG-MCP-7`, no como excepción al borrado.

**DB-06 · `ToolProtocol.category` + `ToolCategory`** (`tools/protocol.py:10-19,56`). Campo **requerido** que
las 25 nativas + `McpTool` + resource-tools + `SkillTool` setean y que **ningún código de producción lee**.
Ruling de `09·§2.4` + `10·§2.4`, que ratifico: el canónico **no** usa este enum como driver (sus
`isReadOnly`/`isDestructive` sí-consumidos son otra cosa, ya ❌ en A6/A7) ⇒ **borrar el campo**, no
inventarle consumidor. *(Registro de honestidad: mi primera inclinación fue "cablearlo contra el
announcement diferido"; abrir 09/10·§2.4 la desmontó — no hay contraparte canónica que lo justifique.
Cablearlo habría sido mímica inventada.)*
**⚙ RV-6 · CONFIRMADA EN EL VEREDICTO, PERO CON COLATERAL NO DECLARADO — el radio de explosión más grande
de las 12 entradas BORRAR.** `tools/protocol.py` abierto 1→EOF (61 L).
*MUEREN:* el enum `ToolCategory` (:10-15, valores `FILE`/`SYSTEM`/`NETWORK`/`UTILITY`/`BACKGROUND`) y el
campo requerido `ToolProtocol.category: ToolCategory` (:56).
*SOBREVIVE **todo lo demás del archivo**, y hay que decirlo porque el archivo es compartido:* `ToolResult`
(:18-53) íntegro — su `__init__` de 6 campos (:21-36) y los constructores `error`/`timeout`/`aborted`
(:38-48, este último es la ruta viva de `dispatcher.py:55`) — y `ToolProtocol` (:55-61) **menos** la línea
:56. Borrar el archivo o la clase sería catastrófico: `ToolResult` es el tipo de retorno de **toda** tool.
*Colateral NO declarado en la redacción original (3 frentes):*
1. **El export.** `ToolCategory` se re-exporta en `tools/__init__.py:11` (import) y `:19` (`__all__`). La
   entrada sólo hablaba de "borrar el campo y el enum"; hay que retirar el export o el paquete rompe.
2. **Los ~25 productores.** No basta con borrar el campo: hay que retirar la línea `category = …` y su
   import en cada implementación. Censadas por localizador: 18 nativas (`sleep`·`tool_search`·`bash`·
   `todo_write`·`glob_tool`·`ask_user`·`file_edit`·`web_search`·`config`·`clone_repository`·`grep_tool`·
   `plan_mode`×2·`worktree`×2·`agent`·`web_fetch`·`read_file`·`task_tools`), más
   `capabilities/mcp/resource_tools.py:6,31,63`, `capabilities/mcp/tool_adapter.py:6,27` y
   `capabilities/skills/skill_tool.py:6,91`.
3. **Un consumidor fuera de `tests/`.** `scripts/e2e_runtime_test.py:37,46` — es un **script ejecutable**,
   no un test; se rompe igual y no lo cubre la retirada de tests.
*Tests a re-apuntar (24 archivos):* `test_runtime_e2e_real_complex`·`test_runtime_e2e_real`·
`test_modes_background`·`test_hooks_homologation`·`test_deferred_strategy`·`test_runtime_factory`·
`test_root_context_modifier`·`test_capability_wiring`·`test_deferred_loading`·`test_deferred_delta`·
`test_mcp_provider`·`test_tool_dispatcher`·`test_subagent_application`·`test_runtime_contracts`·
`test_path_presentation`·`test_capability_manager`·`test_runtime_e2e`·`test_pre_tool_use_hook`·
`test_events_homologation`·`test_capabilities_resolver`·`test_runtime_v2`·`test_loop_homologation`·
`test_agent_loop`·`test_tools_infra_homologation`. En todos el uso es idéntico (`category = ToolCategory.X`
en una tool de fixture) ⇒ retirada mecánica, pero **no es "borrar una línea"**: es la entrada más cara de
ejecutar de las 12, y conviene saberlo antes de Fase B, no durante.

**DB-08 · `McpServerConfig.auth_headers()`** (`config.py:97-102`). Duplicado muerto: la ruta viva del bearer
es `build_auth` → `_build_bearer` (`auth.py:73-75`) → `AuthArtifacts.headers` → merge en
`client.connect` (`client.py:106`). Además **diverge**: `auth_headers()` ignora `oauth` por completo
(que `_build_oauth` sí resuelve, `auth.py:78-108`) ⇒ segunda fuente de verdad, ya incorrecta.
**Impacto:** re-apuntar `test_cap_mcp_homologation.py:68-71` y `test_mcp_config_contract.py:60-75` a
`build_auth`/`_build_bearer`.
**⚙ RV-6 · CONFIRMADA SIN CAMBIO DE ALCANCE.** `capabilities/mcp/config.py` abierto 1→EOF (129 L) y
`capabilities/mcp/auth.py` 1→EOF (122 L).
*MUERE: **un solo método**,* `McpServerConfig.auth_headers()` (:97-102). Nada más.
*SOBREVIVE **todo el resto de `config.py`**, y se enumera porque la entrada nombra la clase y podría leerse
como "borrar la config":* `McpServerConfig` con todos sus campos —incluido `model: str | None` (:49), que es
**DB-28** y tiene su propio destino, no éste—, `_validate_identity_and_auth`, `resolved_transport()`,
`parse_server_config` y `load_server_configs`. **Se borra un método, no una clase.**
*Sobrevive también toda la ruta viva sustituta*, que es la que hace el trabajo: `AuthArtifacts`, `AuthDeps`,
`AuthBuilder`, el registry `_STRATEGIES` (`auth.py:42`, **CONSERVAR** por la regla DB-23 corregida de §7.1:
registry de extensión poblado en import-time, no estado de sesión), `register_auth_strategy`,
`available_auth_strategies`, `build_auth`, `_build_none`, `_build_bearer` (:73-75) y `_build_oauth`
(:78-108) — este último es justo lo que `auth_headers()` ignora y por lo que es una segunda fuente de verdad
**ya incorrecta**, no meramente redundante.
*Colateral:* además de los 2 tests ya declarados (verificados exactos: `test_cap_mcp_homologation.py:71` y
`test_mcp_config_contract.py:60,69,75`), existe una **tercera** ocurrencia:
`SEPARACION/skeleton/bridge.py:153`, que la menciona **en un comentario** describiendo un fallo 401. Es
documentación, no cableado ⇒ no rompe, pero hay que actualizar el comentario o quedará citando un método
inexistente. **Cero referencias de producción.**

**DB-10(a) · `ModelsConfig.extras` + `RuntimeConfig.models`** (`factory.py:59-60,83`). Declarados y
**nunca consumidos** por `_build_local` (leído 1→EOF: no aparece `config.models`). El integrador arma su
`model_caller` ya con su `Model`. → **borrar** ambos.
**⚙ RV-6 · CONFIRMADA, CON UNA CONSECUENCIA NO ESCRITA: no muere un campo, muere la dataclass entera.**
`factory.py` abierto 1→EOF (267 L).
*MUEREN (a):* `ModelsConfig` (:58-60) **completa** — porque `extras` (:60) es su **único** campo, borrarlo
la deja vacía ⇒ no queda "una dataclass con menos campos", queda una dataclass sin razón de ser; y
`RuntimeConfig.models` (:83). La redacción "borrar ambos" ya lo implicaba, pero no lo decía, y en Fase B la
diferencia entre "quitar un campo" y "quitar un tipo del módulo" es real.
*SOBREVIVEN:* las otras 4 config-dataclasses de `factory.py` (`StorageConfig`, `ToolsConfig`,
`CapabilitiesConfig`, `VoiceConfig` —ésta con su propio destino en DB-24—) y los 21 slots `Any` de
`RuntimeConfig` (:85-117). **Ninguna otra línea de `RuntimeConfig` se toca.**
*Colateral:* **cero.** Censo por localizador: `ModelsConfig` aparece **sólo** en `factory.py:59` (def) y
`:83` (uso) — ni un test, ni un integrador, ni un script. Es la entrada más limpia de las 12.
**DB-10(b) · `ModelRequest`** (`models/protocol.py:11-18`) — resuelta en **§7.3** («BORRAR ahora», al revés
de lo que se había remitido). Su auditoría RV-6, que §3.A no tenía:
*MUERE:* la dataclass `ModelRequest` (:11-18) entera, incluido el campo `thinking_budget` (:18) que el motor
no soporta y que era la única razón para conservarla "por si acaso".
*SOBREVIVE:* **`ModelCallerProtocol` (:28-37)** — el superviviente del archivo, y el que de verdad se usa:
su `complete(...)` lleva `system_sections`/`system_override`, que es la firma viva. `models/protocol.py`
**no se borra**: se le quita la dataclass.
*Colateral:* retirar el export en `models/__init__.py:1` (import) y `:4` (`__all__`) — el `__all__` pasa de
3 a 2 símbolos; y `test_model_caller_protocol.py:5,14,20` (2 de sus tests son de `ModelRequest`: "es frozen"
y el de construcción) se retiran, conservando los de `ModelCallerProtocol`. El docstring del archivo de test
(:1) nombra ambos: reescribir.

**DB-16 · `StorageKeys.log_key`** (`storage/protocol.py:85-87`). **0 referencias en todo el paquete** (la
única ocurrencia es su propia def). Sus hermanos `config_key`/`meta_key`/`work_key`/`transcript_key` tienen
dueño (los 3 primeros los cablea `CG-STOR-1`; el cuarto lo consume `runtime.py:428`); `log_key` no tiene
ninguno. **Cablearlo exigiría inventar una capacidad "log durable por agente" que la lectura del canónico no
respalda ⇒ scope creep (L07).** → **borrar**.
**⚙ RV-6 · CONFIRMADA, PERO LA FRASE SOBRE LOS HERMANOS ERA IMPRECISA — y la imprecisión es peligrosa aquí,
porque `StorageKeys` es una clase de la que se borra UN método.** `storage/protocol.py` abierto 1→EOF (87 L).
*MUERE:* `StorageKeys.log_key` (:85-87). **Un método estático. Nada más.**
*SOBREVIVEN — enumerados uno a uno, porque comparten clase con el muerto:* `StorageProtocol`,
`StorageKeys._agent_base`, `config_key` (:53), **`agent_md_key` (:57)**, **`ltm_key` (:61)**,
`transcript_key` (:68), `meta_key` (:72), `work_key` (:79). **Los 7 se conservan.**
*Corrección de la redacción original:* decía «sus hermanos `config_key`/`meta_key`/`work_key`/
`transcript_key` tienen dueño». Verificado por censo + apertura: **sólo `transcript_key` tiene consumidor de
producción** (`runtime.py:428`). Los otros tres **no** lo tienen hoy; lo que tienen es **destino declarado**
(`CG-STOR-1`, y los xfails `StR3`/`StR4` de `test_storage_homologation.py:112,116-118`). La distinción
importa: "tener dueño" y "tener destino" no son lo mismo, y sólo lo segundo es cierto.
*Y el punto que esta auditoría existe para fijar:* **`agent_md_key` y `ltm_key` no aparecían en ninguna de
las dos listas** — ni entre los muertos ni entre los hermanos con dueño. Están exactamente en la misma
situación fáctica que `log_key` (**0 consumidores de producción**; su única referencia externa es
`test_runtime_storage.py:133-134`). La diferencia que los salva es que **sí tienen destino nombrado**: el
xfail `test_storage_homologation.py:116` los cita literalmente (*«sin persistencia de config
(`config_key`/`agent_md`/`ltm` muertos)»*) bajo `StR4`. ⇒ **Quedan declarados SUPERVIVIENTES con destino
`StR4`/`CG-STOR-1`.** Sin esta línea, Fase B los habría borrado por el mismo argumento que a `log_key`
—"0 referencias"— y habría matado la persistencia de `AGENT.md` y de memoria a largo plazo.
*Hallazgo lateral (no de esta entrada, se remite):* `test_storage_homologation.py:97,100` asevera
`StorageKeys.mcp_config_key`, que **no existe** en `storage/protocol.py`. Es una brecha del lado CABLEAR,
no del BORRAR; se anota para `CG-STOR-1` y no se resuelve aquí (L07: no trocear, pero tampoco absorber lo
que pertenece a otra entrada).

**DB-17 · `CapabilityActivation`** (`capabilities/contracts.py:26-38`, export `:72-76` +
`capabilities/__init__.py:1,8`). BaseModel con 5 campos, **sin productor ni consumidor**. Verificado que
cada uno de sus campos ya lo entrega un mecanismo vivo y distinto: `tools_to_enable`+`permission_rules`+
`active_state` → `context_modifier` (`skill_tool.py:38-66`); `messages_to_append` → `active_context()` +
`_inject_recall` (`agent_loop.py:112-130,218`); `refresh_tool_pool` → `build_tool_pool` per-turno
(`agent_loop.py:194-195`). **Cabo 5 resuelto: BORRAR.** Razón desarrollada: `12·§2.4` dejó la decisión
abierta entre «shape de retorno de `activate()`» y «superseded por `ToolResult.new_messages` (CG-SKILL-5)».
La resolución es la segunda: **K5 tipa `ToolResult` con `new_messages`/`structured`/`context_modifier`/
`ends_turn`**, y ése es el canal por el que una capability altera el turno. Mantener además un
`CapabilityActivation` sería **el mismo modo de fallo que ya sufre 08 con dos cascadas**: dos mecanismos
paralelos que divergen. Si Fase C reifica un `activate()` tipado, se re-introduce entonces, con productor.
**⚙ RV-6 · CONFIRMADA SIN CAMBIO DE ALCANCE.** `capabilities/contracts.py` abierto 1→EOF (76 L) y
`capabilities/__init__.py` 1→EOF (15 L).
*MUERE:* el `BaseModel` `CapabilityActivation` (:26-38) con sus 5 campos.
*SOBREVIVEN — se enumeran porque el archivo es el contrato del subsistema entero:* `CapabilitySummary`
(:10-24) y `CapabilityProvider` (:41-70). `contracts.py` **no se borra**; pierde una clase de tres.
*Colateral:* retirar `contracts.py:73` (`__all__`, que pasa de 3 a 2) y `capabilities/__init__.py:1`
(import) + `:8` (`__all__`). **Cero consumidores adicionales:** el censo no encuentra ni un test, ni un
integrador, ni una llamada — las **4** ocurrencias del símbolo en todo el corpus son su `class`, su
`__all__` y los dos del `__init__`. Es, junto a DB-10(a), la entrada de radio mínimo.
*Sin superviviente que rescatar:* a diferencia de DB-01/DB-03, aquí **no hay vocabulario T1 atrapado** — los
5 campos no son un enum ni un tipo nominal, son un *shape* de retorno, y su sustituto (`ToolResult` tipado
con `new_messages`/`structured`/`context_modifier`/`ends_turn`, K5) es el que aporta el vocabulario.

**DB-21 · ternario muerto** `factory.py:129` `cls._modes[name] = name if False else runtime_cls` → `= runtime_cls`.
**⚙ RV-6 · CONFIRMADA SIN CAMBIO DE ALCANCE — pero la auditoría era obligatoria, no una formalidad.**
La entrada dice "borrar el ternario"; leído `factory.py:124-129` 1→EOF, el ternario está **dentro** de
`register_execution_mode`, que es el punto de extensión del registry `_modes`.
*MUERE:* la sub-expresión `name if False else` de la línea :129. **Media línea.**
*SOBREVIVEN — y ésta es la razón de escribirlo:* `RuntimeFactory._modes` (:125) y
`register_execution_mode` (:127-129) **enteros**. `_modes` es exactamente uno de los **7 globales**
censados en §7.1 y está clasificado **CONSERVAR** por la regla DB-23 corregida (registry de extensión
`nombre → clase` poblado en import-time; **no** es estado de sesión ni de tenant). Una entrada BORRAR que
menciona `cls._modes[…]` sin decir esto es precisamente el tipo de texto que, aplicado literal, se lleva por
delante el registry junto con el ternario.
*Colateral:* **cero.** No hay export, ni test, ni consumidor que dependa de la forma de la expresión.

**DB-24 · superficie de voz en el base** (`17·§2.6`): `VoiceConfig.stt_enabled`/`tts_enabled`
(`factory.py:74-75`), `RuntimeConfig.voice` (:84) + gate (:212-216) + paso (:238-239),
`LocalAgentRuntime(stt=,tts=)` (`runtime.py:76-77,106-107`) y sus consumidores `_resolve_prompt` (:220-232)
y `_wire_tts` (:234-262). No componer la battery **es** el gate ⇒ los flags son redundantes.
→ **borrar del base al extraer `battery_voice`** (Fase C). Secuenciado, no antes.
**⚙ RV-6 · ⚠ ALCANCE AMPLIADO POR EL LADO DE LOS SUPERVIVIENTES — la entrada nombraba lo que muere pero
callaba el archivo completo que NO puede morir con ello.** Abierto en esta pasada `voice/protocol.py` 1→EOF
(58 L) y `voice/__init__.py` 1→EOF (6 L) — que **no estaban citados en ninguna parte de DEUDA-B**.
*MUEREN (del base, al extraer la battery):* `VoiceConfig.stt_enabled`/`tts_enabled` (`factory.py:74-75`),
`RuntimeConfig.voice` (:84) y —por el mismo argumento que DB-10(a)— la dataclass `VoiceConfig` (:63-75)
**entera**, cuyos otros dos campos `stt`/`tts` (:72-73) se mudan a la config de la battery, no se conservan
en el base; el gate de voz de `_build_local` (:212-216) y el paso `stt=stt, tts=tts` (:238-239); los
parámetros `LocalAgentRuntime(stt=, tts=)` (`runtime.py:76-77` → `:106-107`) y sus dos consumidores
`_resolve_prompt` (:220-232) y `_wire_tts` (:234-262).
*SOBREVIVE ÍNTEGRO — y se muda, no se borra — `agentic_runtime/voice/`:* `AudioInput` (`protocol.py:21-31`,
con `data`/`mime_type`/`sample_rate`/`metadata`), `SpeechToTextProtocol` (:34-41, `transcribe`) y
`TextToSpeechProtocol` (:44-55, `speak` + `flush`), más el `__init__.py` que los exporta. **Son vocabulario
T1 puro: tres tipos nominales, cero maquinaria, cero estado.** Son exactamente la superficie que
`battery_voice` necesita para que el integrador inyecte su motor, y el propio docstring del módulo (:3-10)
la describe como «primitivas y plomería; el motor real lo inyecta el integrador» — coherente con Filosofía B.
Borrar "la superficie de voz del base" sin esta salvedad dejaría a la battery sin protocolo que implementar.
⇒ **DB-24 borra la CONFIGURACIÓN y el CABLEADO de voz del base; NO borra las PRIMITIVAS.**
*Colateral:* `test_voice_io.py` (7 usos de `VoiceConfig`: :22,103,118,133,150,163,177) y
`test_factory_homologation.py:17,143,149` migran a la battery; `test_voice_homologation.py` tiene por sujeto
declarado (`:2`) justamente `_resolve_prompt`/`_wire_tts`/el gate ⇒ migra entero con ellos.

**DB-26 · `"anon"` inalcanzable** (`runtime.py:424`). `_build_child:209` **siempre** fija
`user_id = task.owner_id or f"user_{uuid}"` ⇒ la rama nunca corre. **Pero borrarlo aislado no cambia nada:**
el defecto real es el autogen mismo (**H-1**, memoria rota por identidad autogenerada, CORE-GAP en
`DEUDA-A`) y `03·A+` pide ripearlo. ⇒ **se ejecuta DENTRO de la remediación de H-1**, no como barrido suelto.
**⚙ RV-6 · CONFIRMADA, Y CON UNA PRECONDICIÓN DURA QUE NO ESTABA ESCRITA: ejecutarla ANTES que H-1 rompe la
persistencia.** `_persist` abierto 1→EOF (`runtime.py:418-432`).
*MUERE:* el fallback `or "anon"` de la línea :424. **Media línea**, igual que DB-21.
*SOBREVIVEN:* `_persist` entero (:418-432) —el guard `if self._storage is None` (:419-420), la resolución
`agent_id` (:427), la llamada `StorageKeys.transcript_key(...)` (:428, **el único consumidor de producción
de `StorageKeys`**, ver DB-16) y el `try/except` de :429-432— y `_build_child` (:205-218) salvo lo que
H-1 decida sobre :209.
*Precondición dura (hallazgo de esta auditoría):* tras el borrado, la línea queda `user_id = ctx.user_id`, y
`ctx.user_id` es opcional. Hoy la rama `"anon"` es inalcanzable **sólo porque** `_build_child:209` fija
siempre `task.owner_id or f"user_{uuid…}"`. Si Fase B aplica DB-26 **antes** de que H-1 retire ese autogen
—o si H-1 lo retira sin sustituto síncrono— `user_id` puede llegar `None` y la clave persistida pasa a ser
`"None/<session>/session.json"`: no falla ruidosamente, **persiste bajo un usuario inexistente**. Es un modo
de fallo silencioso, peor que el `"anon"` que se pretende eliminar.
⇒ **DB-26 no es "barrer una rama muerta": es el ÚLTIMO paso de la remediación de H-1**, y sólo es legítimo
cuando H-1 garantice que `ctx.user_id` no puede ser `None` en `_persist`. Anotado como orden, no como
preferencia.
*Colateral:* cero exports, cero tests que aserten `"anon"`.

### 3.B — CABLEAR (costuras a medias: la mitad existe muerta; completarla ES la remediación)

**DB-04 · `B-registry-dual-path` — el más severo de este rollup.** *(Corrección del tracker: su ítem 2.4
declara `get/set_registry` «ni productor ni consumidor en producción». **Falso**, y `05·§2.4` ya lo corrigió.)*
- **comportamiento:** hoy `task_tools.py` resuelve el registry por el **global** (`get_registry()` en
  `:29/54/113/187`) mientras `LocalAgentRuntime` usa su **instancia** (`runtime.py:86`, inyectada o
  `InMemoryTaskRegistry()` propio). `factory.py` (1→EOF) **nunca llama `set_registry`** ⇒ en un runtime
  ensamblado por `create_runtime`, **toda** invocación de `TaskCreate/Get/List/Update/Stop/Output` levanta
  `RuntimeError("TaskRegistry not initialized…")` (`registry.py:161-166`) → `ToolResult.error` por el
  `except` genérico del dispatcher (`dispatcher.py:83-84`). Y si el integrador **sí** llama `set_registry`
  con otro objeto, quedan **dos registries divergentes**: las tools ven tareas que el runtime no tiene.
- **seam:** el registry viaja por el **ctx**, como ya viajan `presentation`/`exec_env`/`fs`/`git_credentials`
  (`runtime.py:317-325`). Nuevo slot `ctx.task_registry: TaskRegistryProtocol`.
- **firma:** `ToolUseContext.task_registry: TaskRegistryProtocol | None = None`; las 6 Task* tools pasan de
  `get_registry()` a `ctx.task_registry`; `_scoped_get(task_id, ctx)` ya recibe el ctx.
- **cableado:** `LocalAgentRuntime._run_loop`, junto a las otras asignaciones de ctx (:317-325):
  `ctx.task_registry = self._task_registry`. Se retiran el global `_registry` + `get_registry`/`set_registry`
  (`registry.py:153-166`) y su export (`execution/tasks/__init__.py:2,8,9`). `TaskRecord`/
  `InMemoryTaskRegistry`/`TaskRegistryProtocol` **se conservan** (vivos).
- **orden:** temprano; es prerrequisito de que las Task* tools funcionen en absoluto. Cae dentro de
  DB-23 (des-globalización) y comparte patrón con DB-27.
- **prueba:** `test_task_tools_use_runtime_registry` (crear vía `TaskCreate` y verlo en
  `runtime.status(task_id)`) + `test_no_global_task_registry`.

**DB-07 · `LAT-HOOK1` — `additional_context` agregado y descartado.**
- **comportamiento:** `HookRunner.run` agrega el `additional_context` de todos los handlers y lo devuelve
  unido (`runner.py:54-59`); el único consumidor de decisión (`agent_loop.py:300-313`) sólo honra
  `modified_input`+`block` — y el propio comentario del loop (:297-298) lo admite: *«`stop`/
  `additional_context` no se consumen en este punto»*. `_fire_stop` descarta la `HookDecision` entera.
- **seam:** el gate PreToolUse del loop consume la decisión completa.
- **firma:** sin cambio de tipo (`HookDecision` ya lleva el campo, `hooks/protocol.py:46`).
- **cableado:** en `agent_loop.py`, tras :306 y antes del dispatch: si `decision.additional_context` →
  `ctx.messages.append({"role":"user","content": _as_reminder(decision.additional_context)})`, reusando el
  helper ya existente (:27-33). Es exactamente la **parte (a) de CG-HOOK-5**.
- **orden:** con HR5. **Anti-padding:** la *decisión rica* (`behavior` allow/ask/deny, `stop`) es CORE-GAP
  CG-HOOK-4/5 en `DEUDA-A` y **no** se re-cuenta aquí; sólo la cañería a medias.
- **prueba:** `test_pretooluse_additional_context_injected` (hoy `xfail(strict)` en
  `test_hooks_homologation.py:212-215` → debe pasar a verde).

**DB-09 · `LAT-SKILL1` — `args` anunciado y descartado.**
- **comportamiento:** `SkillTool.input_schema` promete `args` (`skill_tool.py:88`) y `execute` lee sólo
  `command` (:108); `render_skill(skill)` (:18-35) no acepta args ⇒ la tool incumple **su propio** schema.
- **seam / firma:** `render_skill(skill, args: str = "", ctx=None)`.
- **cableado:** `execute` pasa `input.get("args","")` a `render_skill`; la substitución `$ARGS`/`$1..$N`
  entra con **CG-SKILL-2/SkR3**.
- **orden:** con SkR3. **Anti-padding:** el gap A↔B (sin substitución/vars/bash-injection, FIND-SKILL4) se
  sostiene ❌ en `DEUDA-A`; aquí sólo la inconsistencia announce↔execute.
- **prueba:** `test_skill_tool_passes_args_to_render`.

**DB-10(b) · `ModelRequest`** (`models/protocol.py:11-19`). Tipo frozen con `stop` (=LAT-SIG1) y
`thinking_budget`, **nunca construido**: el loop llama `complete(messages, tools, **kwargs)` directo
(`agent_loop.py:235-239`), armando los kwargs **condicionalmente** «por robustez ante callers de terceros»
(:224-234) — precisamente el olor que un request tipado elimina. **Decisión: CABLEAR, con la forma remitida
al diseño del seam T1-MOTOR (Fase B)**, junto a K8. Alternativa explícita si ese diseño la rechaza: borrar
la clase y sus tests. No la resuelvo aquí porque **es una decisión de contrato de motor, no de higiene**, y
resolverla en A3.DB sería decidir el seam por la puerta de atrás.
**⚠ ESTE PÁRRAFO ESTÁ SUPERSEDIDO.** `§7.3` lo revirtió («**BORRAR ahora**», al revés de lo remitido) y el
reparto final `12/12` cuenta `DB-10(b)` **en `§3.A`**, no aquí. Se conserva el texto por trazabilidad de la
decisión, pero **la orden vigente y su auditoría `⚙ RV-6` están en `§3.A`, bajo `DB-10`.** (Detectado en
`R-1`, 2026-07-28: la entrada aparecía en las dos listas con veredictos opuestos.)

**DB-13 · `context_modifier`/`ends_turn` no declarados en `ToolResult`.** **Cabo 1 resuelto.**
`ToolResult.__init__` (`tools/protocol.py:21-36`, leído 1→EOF) declara **sólo** `tool_name/output/is_error/
is_timeout/is_aborted/metadata`. Los dos campos se cuelgan por atributo dinámico
(`skill_tool.py:119` con `# type: ignore[attr-defined]`, `config.py:75`, `ask_user.py:97`) y se leen por
`getattr` (`agent_loop.py:332,338`). **Tier: DEUDA-B** — el mecanismo **funciona**, sólo está sin tipar.
Se distingue de `new_messages`/`structured`, que **no existen** = CORE-GAP K5.
→ **cablear: declararlos como campos tipados**, en la misma pasada que K5 tipa los otros dos.

**DB-14 · `E4` dos `Usage` divergentes.** `events/event_types.py:9-13` (dataclass: input/output/thinking) ≠
`execution/session/session.py:16-18` (BaseModel: input/output). → unificar en **un** `Usage` con el shape
objetivo de K-usage (5 campos + `__add__`). Higiene, pero la unificación apunta al shape canónico.

**DB-15 · `E3`-faceta: `session.usage` cableado a medias.** El slot existe (`session.py:42`) y se **lee**
(`runtime.py:403-404` lo vuelca a `complete(...)`), pero **nadie lo escribe** ⇒ todo transcript persiste
`input_tokens=0/output_tokens=0`. La *capacidad ausente* (acumular `DoneEvent.usage`) es CORE-GAP; la
*faceta seam-a-medias* es ésta. Se cierra con el mismo commit.

**DB-18 · `B-create-loop` + `B-dead-resolver` — decisión CONJUNTA. Cabo 4 resuelto.**
`create_loop` (`loop/factory.py` 1→EOF, 27 L) construye un `AgentLoop` pasándole `capabilities_resolver` y
**no** `tool_registry`/`capability_manager` ⇒ cae siempre en la rama `elif` (`agent_loop.py:201-205`), que
sólo **anuncia** schemas: el dispatcher resuelve de `ctx.tool_pool` (`dispatcher.py:57`), que en esa rama
queda vacío ⇒ **un loop que anuncia tools que no puede ejecutar**. A su vez esa rama es **inalcanzable desde
el ensamblador real**, porque `_build_local` siempre pasa ambos (`factory.py:189,194,221-222`) y el `if`
:194 siempre gana.
- **decisión:** **CABLEAR `create_loop`** (re-firmarlo sobre `tool_registry`/`capability_manager`/
  `tool_dispatcher`/`hook_runner`/`event_bus`) y **BORRAR** después `CapabilitiesResolver` + la rama `elif`
  + los parámetros `capabilities_resolver` de ambos `__init__` + `CapabilitiesConfig.skill_catalog` y
  `resolve_timeout_seconds` (que sólo lo alimentan, `factory.py:197-201`).
- **por qué no borrar `create_loop` también:** bajo Filosofía B el `loop/` es superficie de framework — un
  integrador que componga su propio modo de ejecución debe poder construir un loop **sin** importar
  `LocalAgentRuntime`. Hoy ese helper público entrega un loop roto; eso es peor que no tenerlo.
- **orden obligatorio:** re-firmar `create_loop` **antes** de borrar el resolver (⚠ N1 de 18: borrarlo
  primero rompe el helper). **prueba:** `test_create_loop_executes_tools`.

**DB-19 · hack `app_state.native["plan_mode"]`.** El loop documenta (`agent_loop.py:293-296`) que la
POLÍTICA vive en el hook del integrador, que lee `app_state.native["plan_mode"]`. Es **contrato con el
integrador**, no un hack lateral — pero es un canal **no tipado** que existe porque `PermissionContext` no
tiene `mode`. → **ripear cuando K1 (`PermissionMode`) entre al contrato**; el gate decidirá por modo+reglas.
**Cabo 7 resuelto:** el registro **incondicional** de `PlanModeProvider()` (`factory.py:146`, leído) **NO**
es un hack — es decisión de composición y va a **A3.CAT**, no aquí.

**DB-20 · `B-untyped-composition`.** 21 slots `Any` + 3 retornos `Any` en `factory.py:34-117,132,178,247`
(verifiqué la superficie 1→EOF: `model_caller`, `hook_runner`, `task_registry`, `presentation`, `exec_env`,
`fs`, `git_credentials`, `small_llm`, `agent_resolver`, `root_context_modifier`, `root_turn_start_hooks`,
`stt`, `tts`, `mcp_config_store`, `mcp_config_watcher`, `skill_store`, `memory_store`, `skill_catalog`,
`mcp_oauth_*`…). → tipar contra los Protocols que **ya existen**. **Anti-padding:** el *fail-fast* de
`create_runtime` es **K8** en `DEUDA-A`; aquí sólo las anotaciones.

**DB-22 · `B-unreachable-knobs`.** `LocalAgentRuntime.default_timeout` (`runtime.py:79`) y
`AgentLoop.deferred_strategy` (`agent_loop.py:62,78-82`) no son alcanzables desde `RuntimeConfig`;
`tool_dispatcher` se construye fijo (`factory.py:204`, sin `timeout_override`). → exponerlos en
`RuntimeConfig` o retirarlos. Son *knobs*, no capacidad ausente ⇒ tier DEUDA-B.

**DB-25 · literal `stop_reason == "tool_calls"`** duplicado en `agent_loop.py:348` y `runtime.py:254`.
El vocabulario de `stop_reason` es **T1-CONTRATO**; hoy es string mágico en dos capas. → fijarlo como
enum/constante del contrato **antes** de que una battery externa dependa del literal.

**DB-27 · `B-runner-wiring` (S18/C1) — el crítico funcional.** Verificado de primera mano ESTE ciclo:
`factory._build_local` (`factory.py:178-240`, 1→EOF) **nunca llama `set_runner()`**; `agent.py:105` llama
`get_runner()` dentro de un `try/except` que devuelve `ToolResult.error(f"Subagent failed: {e}")`; el global
`_runner` (`runner.py:28-41`) arranca en `None` y lanza `RuntimeError`. ⇒ **en un runtime ensamblado por
`create_runtime`, TODO spawn de subagente falla.** El seam existe y está **sin poblar** ⇒ tier DEUDA-B
(L09: existir ≠ estar cableado), no gap A↔B.
- **cableado:** el factory construye `LocalSubagentRunner(build_child=…)` y lo **inyecta** (`ctx.runner`),
  **no** por `set_runner` — mismo criterio de des-globalización que DB-04 (patrón fijado por A2.5).
- **prueba:** `test_spawn_subagent_e2e` sobre un runtime de `create_runtime`.
- **Cabo 8 resuelto:** `agent_resolver` **SÍ** está cableado (`factory.py:117` → `:237` →
  `runtime.py:78,104` → `_run_loop:342-343`, los tres tramos abiertos 1→EOF) ⇒ **no** se marca como seam
  sin poblar. El único `existe-sin-poblar` crítico es el **runner**.

### 3.C — DB-23 · `B-global-registries`: política, no ítem suelto

**No se cuenta aparte** (evitar doble conteo): sus instancias verificadas son DB-02 (`_observer`, borrar),
DB-04 (`_registry`, cablear vía ctx) y DB-27 (`_runner`, inyectar). Queda como **regla de arquitectura**:

> El base framework **no** posee estado global mutable de proceso. Todo registry/canal viaja por inyección
> o por el `ctx`. Motivo Filosofía B: el integrador complejo (`agentic_assistant`) es **multi-tenant** —
> un singleton de módulo mezcla sesiones de usuarios distintos en el mismo proceso.

El 4º global verificado, `_channel` (`notification.py:22`), está **scopeado por `(user_id, session_id)`**
(comentario :20-21) ⇒ no filtra entre usuarios, pero sigue siendo estado de proceso: mismo destino, menor
urgencia. Se aplica al extraer el canal de notificación.

### 3.D — DB-28 · menores heredados del barrido (una línea cada uno, sin inflar)

`01·CTR-13` `@runtime_checkable` inconsistente → decorar · `01·CTR-15` `arm_watchdog` no-op
(`registry.py:88-91`) → completar o retirar según cubra el AbortScope · `01·CTR-11`+`03·D2`
`PathPresentation.to_llm` sin call-site → cablear o borrar (slot pasivo, homed en 03) · `03·C3`
`apply_context_modifier_compat` andamiaje de migración → retirar el `except AttributeError` · `03·A+`
autogen `user_<hex>`/`sess_<hex>` (`runtime.py:208-209`) → **es H-1**, va con `DEUDA-A` · `10·G1` conflación
tasklist(TODO) ↔ registry-de-ejecución en `task_tools.py` → separar el store (su dimensión team/swarm sigue
⛔ por el corte del README) · `11` `McpServerConfig.model` (`config.py:49`) 0 lectores → cablear si
`battery_mcp_skills` usa modelo per-server, si no borrar. *(`McpState.pending_servers()` **no** entra:
`11·§2.4` lo clasificó como superficie de API integrator-facing, y lo respeto.)*

---

## 4. Los 8 cabos — resueltos uno por uno

| cabo | resolución |
|---|---|
| **1 · tier de `B-new_messages`** | **CORE-GAP K5** (la ausencia de `new_messages`/`structured`, ya en `DEUDA-A`). Residual tier DEUDA-B = **DB-13**: `context_modifier`/`ends_turn` existen y funcionan pero **no están declarados** en `ToolResult` → cablear (tiparlos) en la misma pasada de K5. |
| **2 · `07·B2` re-abierto por la objeción de 17 (K4)** | ~~REMITIDO a A-CIERRE~~ → **RESUELTO EN ESTE MISMO DOCUMENTO, `§7.2`** (tramo de cierre de los 3 pendientes; la remisión es del texto de la 1ª redacción y **quedó obsoleta al cerrarse §7**, como el propio `§7.4` registra). Veredicto: `07·B2` **no estaba equivocado, estaba condicionado a un seam que aún no existe**; se cierra como **CORE-GAP condicionado** y la forma queda decidida — **campos de identidad (`task_id`/`agent_id`/`session_id`/`seq`/`ts`) en el `Event` BASE, NO un `EventEnvelope` que envuelva** (`bus.py:40` despacha por `type(event)` ⇒ envolver rompe el despacho tipado). Sigue siendo entrada viva de `DEUDA-A` K4, **ya con forma**. ⚠ *Rótulo retirado en A-CIERRE·P0 (AC-04): dejarlo inducía a reabrir una decisión ya tomada.* |
| **3 · `log_key` borrar-vs-cablear** | **BORRAR** (DB-16). 0 referencias en todo el paquete; sin battery-dueño; cablearlo exigiría inventar una capacidad de log durable sin respaldo en la lectura del canónico (L07). |
| **4 · `B-dead-resolver` + `B-create-loop` (decisión conjunta)** | **CABLEAR `create_loop` PRIMERO, BORRAR el resolver DESPUÉS** (DB-18). El orden es obligatorio: borrar primero rompe el helper (⚠ N1 de 18). |
| **5 · `LAT-CAP1` cablear-vs-borrar** | **BORRAR** (DB-17). Sus 5 campos ya los sirven `context_modifier`, `active_context`+`_inject_recall` y el reensamblado per-turno; el canal tipado de activación será `ToolResult` extendido por K5. Mantener ambos reproduce el modo de fallo de las dos cascadas de 08. |
| **6 · las 6 confirmaciones de `DEUDA-A §0.1b`** | **5 de 6 re-abiertas ESTE ciclo** (no heredadas). La única **HEREDADA declarada** es la mitad de `LAT-MODELS1` relativa a qué haría el registro en `agentic_models` — ver §0.2. |
| **7 · `B-02` no es un hack lateral** | Confirmado leyendo `factory.py:146` 1→EOF: `PlanModeProvider()` se registra **incondicionalmente** ⇒ decisión de **composición** → **A3.CAT**, no deuda. Lo que sí queda como DEUDA-B es el canal **no tipado** `app_state.native["plan_mode"]` (DB-19), secuenciado tras K1. |
| **8 · contra-cabo `agent_resolver`** | Confirmado cableado extremo a extremo (`factory.py:117,237` → `runtime.py:78,104` → `_run_loop:342-343`). **No** se marca como costura sin poblar. El único `existe-sin-poblar` crítico es el **runner** (DB-27). |

---

## 5. Hallazgos de este ciclo (no estaban escritos así en ningún doc previo)

- **DB-h1 · `B-registry-dual-path` es un defecto ACTIVO, no una divergencia latente.** Los docs previos lo
  describían como «dos caminos de acceso ⇒ riesgo de divergencia». Al abrir `factory.py` 1→EOF junto a
  `registry.py:161-166`, el efecto real es más duro: **`create_runtime` nunca llama `set_registry`**, así
  que hoy las 6 Task* tools fallan **siempre** en un runtime de fábrica (`RuntimeError` → `ToolResult.error`).
  Es del mismo grado que `B-runner-wiring`, y no estaba marcado como tal.
- **DB-h2 · borrar `signals/` tiene una precondición no escrita.** `SignalType.PAUSE/RESUME` es la única
  traza nominal de pausa/reanudación, y **H-3** (`resume` no existe) sigue sin cableado desarrollado.
  Borrar antes de que H-3 tenga hogar elimina el vocabulario sin sustituto.
- **DB-h3 · `auth_headers()` no sólo está muerto: está incorrecto.** Ignora `oauth`, que la ruta viva sí
  resuelve (`auth.py:78-108`). Refuerza «borrar», no «cablear».
- **DB-h4 · delta sobre `18·N4`:** N4 afirma 6 globales; verifiqué 4. Los otros 2 no se re-verificaron
  (§0.2). No es una corrección — es un límite declarado de lo que este ciclo comprobó.

---

## 6. Orden de ejecución propuesto

1. **DB-27** (runner) y **DB-04** (registry) — hoy rompen funcionalidad real. Mismo patrón (des-globalizar
   por ctx/DI), misma tanda.
2. **DB-18** (`create_loop` primero, luego borrar resolver) + **DB-21** (ternario) — limpieza del ensamblador.
3. **DB-01 · DB-02 · DB-05 · DB-06 · DB-08 · DB-16 · DB-17** — barrido de duplicados-muertos (sin precondición).
4. **DB-13 + DB-14 + DB-15** — con la pasada de K5 (tipar `ToolResult`) y la de usage.
5. **DB-07 (HR5) · DB-09 (SkR3)** — con la remediación de su categoría.
6. **DB-20 · DB-22 · DB-25** — tipado y vocabulario, antes de que una battery externa dependa de la forma actual.
7. **DB-03** — sólo **después** de que H-3 tenga hogar (DB-h2).
8. **DB-19** (tras K1) · **DB-26** (dentro de H-1) · **DB-24** (al extraer `battery_voice`, Fase C).
9. **DB-23** política + **DB-28** menores — barrido de acompañamiento.

---

## 7. Cierre de los 3 pendientes (tramo añadido — instrucción del usuario: *"no podemos cerrar sin revisarlos"*)

La 1ª redacción cerró con `⛔` y 3 pendientes remitidos. El usuario objetó que un pendiente arrastrado
**es un error de ensamblaje diferido**. Se ejecutó el tramo. Los tres quedan resueltos **con evidencia
abierta**, y **dos de los tres cambian la conclusión anterior**.

### 7.1 · Censo de globales — COMPLETADO. **Son 7, no 6, y de 3 clases distintas**

Barrido exhaustivo en 3 pasadas sobre todo el paquete (sentencia `global` · asignación de contenedor mutable
a nivel de módulo · singleton anotado `= None` · atributo de clase mutable), excluyendo `tests/`:

| # | global | archivo:línea | clase | destino |
|---|---|---|---|---|
| 1 | `_registry` | `execution/tasks/registry.py:153` | **A · singleton de instancia** | DB-04 cablear por ctx |
| 2 | `_runner` | `execution/runner.py:28` | **A · singleton de instancia** | DB-27 inyectar |
| 3 | `_observer` | `execution/observer/observer.py:28` | **A · singleton de instancia** | DB-02 borrar |
| 4 | `_channel` | `execution/local/notification.py:22` | **B · acumulador de datos** | des-globalizar (menor) |
| 5 | `_STRATEGIES` | `capabilities/mcp/auth.py:42` | **C · registry de extensión** | **CONSERVAR** |
| 6 | `RuntimeFactory._modes` | `factory.py:125` | **C · registry de extensión** | **CONSERVAR** |
| 7 | `StorageRegistry._backends` | `storage/factory.py:17` | **C · registry de extensión** | **CONSERVAR** |

**El hallazgo no es el nº 7: es que la regla DB-23 que escribí en §3.C está MAL FORMULADA.** Decía
*"el base framework no posee estado global mutable de proceso"*. Aplicada literalmente **condena los 3
registries de extensión** (5, 6, 7), que son legítimos y load-bearing: mapean `nombre → clase/callable`,
se pueblan **en import-time** (`storage/factory.py:33` registra `filesystem`; `auth.py:67+` registra
`none`/`bearer`/`oauth`; `factory.py` registra los backends de ejecución) y **no contienen ni un byte de
estado por sesión ni por tenant**. Son el patrón de registry de plugins, y **borrarlos rompería el punto de
extensión que Filosofía B necesita** (un integrador registra su backend S3 sin tocar el runtime).

**Regla DB-23 corregida (ésta es la que va al blueprint):**

> El base framework no posee **estado global de sesión o de tenant**. Prohibido a nivel de módulo/clase:
> instancias de runtime, registries de tareas, runners, observers y cualquier acumulador de datos de
> usuario. Permitido: **registries de extensión `nombre → clase/callable` poblados en import-time**, que no
> guardan estado por sesión. El criterio de corte es *"¿dos tenants en el mismo proceso comparten esto y se
> ven?"* — no *"¿es mutable?"*.

Aplicando el criterio corregido: **clase A (1-3) = las 3 que ya tenían destino** — el censo **no destapa
ningún global peligroso nuevo**, y ésa era la pregunta real que quedaba abierta. **Clase B (4)**: `_channel`
acumula `BackgroundNotification` reales, pero está keyeado por `(user_id, session_id)`
(`notification.py:22`) ⇒ no filtra entre tenants; sigue siendo estado de proceso (se pierde al reiniciar y
no escala a multi-worker) ⇒ des-globalizar al extraer el canal de notificación, prioridad baja, **no
bloquea**. **Clase C (5-7): se conservan explícitamente**, y quedan anotadas como tales para que el barrido
de Fase B no las arrastre.

⇒ **Pendiente 1 CERRADO.** Resultado neto: el censo estaba incompleto **y** la regla estaba sobre-extendida;
lo segundo era el defecto grave, porque habría causado exactamente el error de ensamblaje que el usuario
temía — borrar en Fase B tres registries vivos por aplicar una regla mía mal escrita.

### 7.2 · `07·B2` / K4 — RESUELTO. **No es "envelope": son campos de identidad en el `Event` base**

Abierto 1→EOF el subsistema entero: `events/protocol.py`(23) · `events/bus.py`(46) ·
`events/event_types.py`(44), + los tramos de seam `runtime.py:134-181` (`dispatch`/`stream`) y `:264-283`
(`_make_bus`) y `:234-262` (`_wire_tts`).

**Hecho 1 — `Event` no tiene NINGÚN campo.** `protocol.py:9-11`: `@dataclass(frozen=True) class Event:` con
sólo un docstring. Cero identidad, cero timestamp, cero `task_id`.

**Hecho 2 — hoy sólo existen seams POR-DESPACHO.** Las dos únicas vías públicas de recibir eventos son
`dispatch(task, on_event=…)` (`:134-151`, devuelve `task_id`) y `stream(task)` (`:153-181`, azúcar sobre la
anterior). En ambas **el consumidor es quien despacha** ⇒ conoce el `task_id` por retorno y el `on_event` es
suyo, para esa task. **La conclusión de `07·B2` es correcta para los seams que existen hoy.**

**Hecho 3 — y aquí la objeción de 17 se confirma, por AUSENCIA.** El `EventBus` se crea **dentro** de
`_run_loop` (`_make_bus`, privado) y **no se expone por ningún accesor**. ⇒ hoy una battery **no puede
suscribirse** a los eventos de un runtime salvo siendo el despachador. El único sink in-proc que existe
(`_wire_tts`) lo cablea el propio runtime, con el `ctx` capturado en la clausura (`:241-248`) — por eso hoy
no le falta identidad. **Bajo Filosofía B ese seam de suscripción TIENE que existir** (telemetría,
persistencia de transcript, voz, cualquier battery observadora). En el instante en que exista, un handler
verá eventos de **todas** las tasks del proceso y `Event` no lleva de quién son.

⇒ **07·B2 no estaba equivocado: estaba condicionado a un seam que aún no existe.** Se cierra como
**CORE-GAP condicionado, con la forma decidida aquí:**

**Decisión de forma — campos en el base, NO un envelope que envuelva.** Razón técnica verificada, no
preferencia: `EventBus.emit` despacha por **`type(event)`** (`bus.py:40`, `self._handlers.get(type(event))`)
y `subscribe(TokenEvent, handler)` es la API tipada (`protocol.py:20`). Un `EventEnvelope` que *envuelva* al
evento colapsa todos los tipos en uno ⇒ **rompe el despacho por tipo y el tipado genérico del `subscribe`**,
que es lo mejor que tiene hoy el bus. Añadir los campos al `Event` base los hereda **todo** subtipo, sin
tocar `emit`, `subscribe` ni ningún handler existente.
**Viabilidad verificada:** `Event` es un frozen dataclass **sin campos**, y **los 5 subtipos tienen TODOS
sus campos con default** (`event_types.py:17-43`) ⇒ añadir campos con default al base **no rompe el orden de
dataclass** (base primero) ni ninguna construcción existente. Es un cambio compatible.
**Campos:** `task_id` · `agent_id` · `session_id` · `seq` (orden) · `ts`. `agent_id` es el mismo hilo de
ID-5/H-4, ⇒ **se cablea una vez y sirve a los tres**.

⇒ **Pendiente 2 CERRADO.** `K4` deja de llamarse "EventEnvelope" y pasa a **"identidad en el `Event` base"**;
sigue siendo CORE-GAP en `DEUDA-A`, pero ya con forma decidida y con la razón por la que la forma anterior
era la incorrecta.

### 7.3 · `ModelRequest` — RESUELTO, y al revés de lo que remití: **BORRAR ahora**

Abierto `models/protocol.py` 1→EOF y contrastado contra la implementación real
`models/caller.py` (`complete` :146-158, `_stream` :162-245).

**El dato que lo decide: `ModelRequest` ya ha DERIVADO del contrato vivo.**

| | `ModelRequest` (`protocol.py:11-18`) | `complete(...)` real (`protocol.py:28-37` = `caller.py:146-158`) |
|---|---|---|
| `messages`, `tools`, `model_id` | sí | sí |
| `stop` | sí | sí |
| `thinking_budget` | **sí** | **NO existe** (y `caller.py:231` emite `thinking_tokens=0` fijo) |
| `system_sections` | **NO** | sí |
| `system_override` | **NO** | sí |

Es decir: la clase declara un campo que el motor **no soporta** y le faltan **dos** que el motor sí usa —
justamente los dos que se añadieron después, con el comentario de "robustez ante callers de terceros"
(`agent_loop.py:224-234`) que motivaba el request tipado. **Un tipo muerto que ya divergió no es un seam
pendiente de cablear: es una segunda fuente de verdad, incorrecta, esperando a que alguien la crea.** Es el
mismo modo de fallo que `auth_headers()` (DB-h3), y se resuelve igual.

⇒ **BORRAR `ModelRequest` ahora** (+ sus referencias en tests). **Lo que NO se borra es el problema:**
la construcción condicional de kwargs en `agent_loop.py:227-239` sigue siendo el olor, y **Fase B / K8 puede
introducir un request tipado — pero diseñado desde la firma VIVA** (los 4 kwargs actuales + `metadata` de
ID-7 + `thinking_budget` sólo si el motor lo soporta), **no resucitando esta clase**. Queda escrito así para
que Fase B no la tome por un diseño ya hecho.

⇒ **Pendiente 3 CERRADO** — y mi remisión anterior era peor que una decisión: dejaba en pie una clase
que ya mentía sobre el contrato.

### 7.4 · Consecuencias sobre el resto del documento

- **§3.C (DB-23)**: la regla queda **sustituida** por la versión corregida de §7.1. Los 3 registries de
  extensión se marcan **CONSERVAR** en el catálogo, no "des-globalizar".
- **§3.B · DB-10(b)**: `ModelRequest` pasa de **CABLEAR-remitido** a **BORRAR** (§3.A lo hereda) ⇒ el
  reparto final es ~~**12 BORRAR / 11 CABLEAR**~~ → **12 BORRAR / 12 CABLEAR**.
  ⚠ **CORREGIDO en A-CIERRE·P0 (AC-h2, doc abierto 1→EOF 2026-07-27).** El «11» era un **error aritmético**,
  no texto pre-RV: mover `DB-10(b)` fuera de CABLEAR lleva la lista de **13 → 12**, no de 12 → 11 (se
  descontó dos veces). Recuento explícito, por si vuelve a discutirse:
  **BORRAR (12)** = DB-01 · DB-02 · DB-03 · DB-05 · DB-06 · DB-08 · **DB-10 (a+b, ya entera)** · DB-16 ·
  DB-17 · DB-21 · DB-24 · DB-26. **CABLEAR (12)** = DB-04 · DB-07 · DB-09 · DB-13 · DB-14 · DB-15 · DB-18 ·
  DB-19 · DB-20 · DB-22 · DB-25 · DB-27. Fuera del reparto por decisión ya escrita: DB-11/DB-12 (residuales
  sin ficha propia, dentro de la remisión CORE-GAP de `B-signals`), **DB-23** (política umbrella, §3.C, «no
  se cuenta aparte»), **DB-28** (menores), **DB-29** (CORE-GAP `H-5`), **DB-30** (se pliega en DB-22).
  ⇒ **24 fichas repartidas, 12/12.** La cifra buena era la de **§8** (`12 BORRAR / 12 CABLEAR`); ésta era la
  mala, y estaba **antes** en el documento, que es el orden peligroso.
- **§4 cabo 2**: pasa de "remitido a A-CIERRE" a **resuelto con forma decidida** (§7.2).
- **§6 orden**: se añade al paso 3 el borrado de `ModelRequest`; y al paso 1, que `agent_id` de K4/ID-5/H-4
  es **un solo cableado con tres consumidores**.

---

## 8. GATEKEEPER de cierre (`00-LEGEND §3.3`) — MOSTRADO

**Frase de rigor (lema de la etapa):**
> De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda; ninguna categoría
> se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar —o colocado sin
> abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

**Ledger:** §2 (**18 filas = las 18 entradas hoja del tracker**, tras la corrección del denominador en RV)
+ §2.b (**15** entradas adicionales: las 13 del barrido §2.4 + DB-29 y DB-30 del tramo RV).

**5 preguntas de cierre** (verbatim del `00-LEGEND §3.3`):

**1. ¿Se leyó ÍNTEGRO `../NN.md`? → sí + rango, o `⛔`.**
**Sí — ahora sí, y con registro.** `../DEUDA-B-transversal.md` **1→332**, re-abierto **en el tramo RV, en
contexto** (`EVIDENCIA.log`, 1ª línea). Es la lectura que permite responder Q2 de primera mano — y la que
destapó que el denominador estaba mal (ver Q2).
**Declarado HEREDADO, sin re-abrir:** `00-LEGEND.md`1→159 y los **18 tramos §2.4** de los docs de categoría.
Sostienen las entradas DB-16..DB-28 de §2.b (procedencia), **no** ninguna orden de borrado de código, que
en todos los casos descansa además sobre el archivo abierto 1→EOF.
*(La respuesta anterior a esta pregunta —«re-abierto ESTE ciclo … además `00-LEGEND` y los 18 tramos»—
era falsa en las dos mitades. Queda corregida aquí.)*

**2. ¿Reconcilia el conteo? findings en `../NN.md` = X; colocados = X; sin colocar = 0. Si ≠ 0 → `⛔`.**
findings = **18** entradas hoja (7 ítems de §; `B-orphans` desagrega **10** sub-ítems numerados y
`B-signals` desagrega **2** sub-ítems rotulados — **SIG9** :204-209 y **SIG13** :210-215);
colocados = **18**; **sin colocar = 0**.
**⚠ Esta cifra es una corrección.** La respuesta anterior decía «17 = 17 = 0» y era falsa por partida doble:
sobrecontaba en 1 (la tabla siempre tuvo 16 filas: 1 + 10 + 5) y omitía 2 (SIG9/SIG13 nunca tuvieron fila).
El destino no cambia —ambos caen dentro de la remisión CORE-GAP de `B-signals`→`AbortScope`— pero un
sub-ítem sin nombre es un sub-ítem que Fase B no implementa; por eso ahora tienen fila (3.1 y 3.2).
Desglose: 6 ítems recalificados a **CORE-GAP** con destino
`DEUDA-A.md` + sus 8 facetas B-internas retenidas aquí; `B-orphans` con sus 10 sub-ítems clasificados
individualmente (6 borrar · 3 cablear · 1 mixto). Añadidas 13 entradas del barrido §2.4 (§2.b) que el
tracker no listaba.

**3. ¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador (`archivo:L-R`), sin apoyarse en grep? → lista de tramos.**
Sí. Tramos de ensamblador abiertos 1→EOF ESTE ciclo, con lo que cada uno sostiene:
`factory.py` 1→267 (ausencia de `set_runner`/`set_registry`/`set_observer`; `:146` PlanModeProvider;
`:189,194,197-201,221-222` resolver+registries; `:237` agent_resolver; `:129` ternario) ·
`execution/local/runtime.py` 1→435 (`:86` registry por instancia; `:209/424` autogen y `"anon"`;
`:234-262` TTS; `:254` literal; `:306-416` `_run_loop` completo; `:342-343` agent_resolver;
`:400-405` métricas; sin `get_observer`) · `loop/agent_loop.py` 1→352 (`:91-92` strings de modo;
`:194-205` rama viva vs muerta; `:297-313` gate que descarta `additional_context`; `:332/338` getattr;
`:348` literal) · `loop/factory.py` 1→27 · `tools/dispatcher.py` 1→85 (`:57` resolución por pool;
`:62-65` gate) · `tools/protocol.py` 1→61 (`:21-36`) · `capabilities/mcp/auth.py` 1→123 +
`client.py:80-139` (`:106` merge real) · `capabilities/skills/skill_tool.py` 1→123 · `hooks/runner.py` 1→63
· `execution/tasks/registry.py` 1→166 + `tools/native/task_tools.py` 1→223 (dual-path) ·
`execution/runner.py` 1→41 + `tools/native/agent.py:80-119` (`:105` `get_runner`).
El grep sólo se usó para **negativos** (probar ausencia de consumidores) y para localizar líneas; ninguna
afirmación de *estar cableado* se apoya en él. **Declarado:** `client.py` y `agent.py` se abrieron por
tramo, no 1→EOF.
**Añadidos por el tramo §7** (4 archivos más, 1→EOF): `events/protocol.py`1→23 · `events/bus.py`1→46
(`:40` despacho por `type(event)` = la razón técnica de §7.2) · `events/event_types.py`1→44 (los 5 subtipos
con default) · `storage/factory.py`1→33 (`:17` `_backends`, `:33` registro import-time) + tramos
`runtime.py:134-181` (`dispatch`/`stream`) · `models/protocol.py`1→37 contrastado contra
`models/caller.py:146-158`+`:231`. El censo de globales de §7.1 **sí** es un barrido por grep — y eso es
legítimo porque su afirmación es de **ausencia/inventario**, no de cableado; cada uno de los 7 hallazgos se
confirmó abriendo su archivo.

**4. ¿La cara integrador quedó al MISMO detalle que la base? → sí; cualquier "→ integrador" a secas = `⛔`.**
Sí, con el alcance propio de este rollup. Las entradas con cara de integrador llevan su detalle:
**DB-19** (canal `app_state.native["plan_mode"]` = contrato con el integrador hoy no tipado; qué lo
sustituye: `PermissionContext.mode` de K1) · **DB-04/DB-27/DB-23** (el integrador deja de llamar
`set_registry`/`set_runner`: pasa a inyectar por `RuntimeConfig` → ctx; con el motivo multi-tenant
desarrollado) · **DB-24** (voz: qué se borra del base y adónde va — `battery_voice`, composición en Fase C)
· **DB-22** (knobs que el integrador debe poder alcanzar desde `RuntimeConfig`) · **DB-25** (por qué fijar
el vocabulario **antes** de que una battery externa dependa del literal). No hay ningún "→ integrador" a secas.

**5. ¿Doble filo (L10)? Ningún ❌ disfrazado de 🔀; ninguna deuda inflada con lo que es de otra capa. → sí, o nómbralo.**
Sí, y lo nombro en ambas direcciones:
- **contra inflar:** 6 de los 7 ítems del tracker **salen** de este rollup hacia `DEUDA-A` (son capacidad
  ausente, no higiene); las 4 caras aguas-abajo que `DEUDA-A §4(c)` excluyó **no** se re-cuentan;
  `04`, `13` y `14` conservan su **CERO** DEUDA-B propia; `McpState.pending_servers()` y
  `CapabilitySummary.deferred` se mantienen **fuera** (superficie de API / cosmético), respetando 11/12;
  el `parent_stop`-no-threadeado sigue siendo delegación por diseño (08), no deuda; `clone_repository` e
  `inherit_messages` siguen siendo extensión propia sin contraparte (10), no deuda; DB-23 se declara
  umbrella y **no** se cuenta aparte de DB-02/04/27.
- **contra disfrazar:** **DB-04** y **DB-27** se marcan como **defectos activos que rompen funcionalidad
  hoy** (Task* tools y todo spawn de subagente), no como "riesgo latente" — que es como los describían los
  docs previos. **DB-06** se resuelve **borrar** aunque mi inclinación inicial fue cablear: no hay
  contraparte canónica y cablearlo habría sido mímica inventada. **DB-03** no se presenta como si entregara
  la cascada: la cascada sigue siendo CORE-GAP.

**VEREDICTO (3ª redacción, tras el tramo RV):** `✅ NADA PENDIENTE` **de verificación** — con **dos
consecuencias tipadas** que salen de aquí hacia otros documentos (§9), y una advertencia de método.

> **Por qué ahora sí ✅.** El pendiente único era **evidencia no tenida**, y se ha tenido: el conjunto T3
> completo —tracker 1→332 + los 3 ensambladores grandes + los 11 archivos de código de los que dependen
> decisiones de BORRAR— está re-abierto 1→EOF **en contexto**, registrado línea a línea en
> `SEPARACION/EVIDENCIA.log`. **Ninguna orden de borrado descansa ya en una lectura que no pueda sostener.**
> Ninguna de las 5 preguntas queda en ⛔, luego la regla dura de L04 no prohíbe el ✅.

> **⚠ Advertencia honesta que acompaña al ✅ — la severidad NO decreció de forma monótona.**
> Yo mismo predije, al abrir el tramo, que aparecerían «1-3 desajustes más de la especie *inventario
> incompleto*» y que la señal a vigilar era la **severidad, no el número**. Aparecieron **10 hallazgos**
> (§9) y **dos de ellos cambian decisiones**, no sólo inventarios:
> - **RV-6** — «borrar `modes/` entero» habría borrado `AgentMode`, vocabulario T1 vivo. **Misma especie
>   exacta que el error de la regla DB-23**: una orden de borrado que, aplicada literal en Fase B, destruye
>   algo load-bearing. Es la **segunda** vez que este ciclo produce ese defecto.
> - **RV-7** — un **CORE-GAP nuevo** (`H-5`, canal de notificación background sin drenador) que obliga a
>   reabrir `DEUDA-A.md`, ya cerrado en A3.DA.
>
> Lectura correcta: el tramo de re-verificación **valió la pena y no fue redundante**, pero **no puedo
> afirmar convergencia**. Lo que sí puedo afirmar es que el modo de fallo cambió de sitio: los dos rounds
> anteriores fallaban en *evidencia auto-reportada* (ya remediado estructuralmente con `EVIDENCIA.log`);
> éste falla en **alcance de las órdenes de borrado** — un borrado escrito a nivel de *módulo* cuando el
> módulo contiene piezas de dos tiers. Contramedida propuesta para A-CIERRE, análoga y también
> estructural: **ninguna entrada BORRAR se escribe a nivel de archivo/módulo; se escribe a nivel de
> símbolo, y el propio §3.A lleva la lista de símbolos que SOBREVIVEN al borrado.** Sin esa lista, un
> borrado por nombre de carpeta vuelve a arrastrar vocabulario. Aplicado ya a DB-01; **queda por auditar
> con ese criterio el resto de las entradas BORRAR** — y eso es trabajo de A-CIERRE, no un pendiente de
> verificación de este ciclo.
>
> **⚙ CERRADO el 2026-07-28 (`A-CIERRE` · R-1 · `AC-09`).** Las 11 entradas BORRAR restantes están auditadas
> a nivel de símbolo; cada una lleva su bloque `⚙ RV-6` en `§3.A` (ver el encabezado de esa sección). Saldo:
> **2 correcciones de alcance** (DB-03 rescata `SignalType`; DB-24 rescata `voice/protocol.py` entero),
> **3 colaterales no declarados** (DB-06 el export + los ~25 productores + un script; DB-10 la dataclass
> entera y no un campo; DB-16 `agent_md_key`/`ltm_key` como supervivientes con destino), **1 precondición
> dura** (DB-26 sólo tras H-1, o persiste bajo `"None/…"`), **5 confirmadas sin cambio**. La contramedida
> RV-6 acertó: **4 de 11 entradas habrían destruido algo vivo o roto el paquete aplicadas literalmente.**

La 1ª redacción cerró `⛔` con 3 pendientes remitidos. El usuario objetó —con razón— que remitirlos es
diferir un error de ensamblaje. **Se ejecutó el tramo §7 y los 3 quedan cerrados con evidencia abierta:**

1. **Censo de globales — CERRADO** (§7.1). Son **7, no 6**, de 3 clases. Los 3 nuevos son **registries de
   extensión poblados en import-time** (`_STRATEGIES`, `RuntimeFactory._modes`, `StorageRegistry._backends`)
   y se **CONSERVAN**. Ningún global peligroso nuevo. **El defecto real que destapó el tramo no era el
   censo sino la regla: DB-23 estaba sobre-extendida y habría hecho borrar en Fase B tres puntos de
   extensión vivos.** Regla corregida en §7.1.
2. **`07·B2` / K4 — CERRADO con forma decidida** (§7.2). `07·B2` es correcto para los seams de hoy (ambos
   son por-despacho); la objeción de 17 se confirma **por ausencia** (el bus no se expone, y bajo B ese
   seam debe existir). Forma decidida por razón técnica verificada —`emit` despacha por `type(event)`
   (`bus.py:40`), luego un envelope que envuelva rompe el despacho por tipo—: **campos de identidad en el
   `Event` base**, viable porque los 5 subtipos tienen todos sus campos con default.
3. **`ModelRequest` — CERRADO: BORRAR** (§7.3), al revés de lo remitido. La clase **ya divergió** del
   contrato vivo (declara `thinking_budget`, que el motor no soporta; le faltan `system_sections` y
   `system_override`, que sí usa) ⇒ es una segunda fuente de verdad incorrecta, mismo modo de fallo que
   `auth_headers()`. Fase B podrá tipar el request **desde la firma viva**, no resucitando ésta.

**Corrección de fondo que este tramo deja escrita:** de los 3 "pendientes", **2 no eran cuestiones abiertas
sino decisiones que yo no había tomado**, y una de ellas (§7.1) encubría un error propio en una regla ya
escrita en el documento. Remitirlos habría trasladado ese error a Fase B, que es exactamente el fallo de
ensamblaje que la objeción del usuario anticipó.

**Reparto final: 12 BORRAR / 12 CABLEAR** (DB-30 se pliega en DB-22) **+ 1 CORE-GAP nuevo emitido**
(`H-5`/DB-29 → `DEUDA-A.md`). A3.DB **cerrado** con el tramo RV incluido. Siguiente: **A3.CAT**.

---

## 9. Tramo de re-verificación **A3.DB·RV** — hallazgos (2026-07-25/26)

Corpus re-abierto: ver `SEPARACION/EVIDENCIA.log`, bloque `A3.DB·RV` (14 lecturas, todas 1→EOF).
Lo que **no** cambió al re-abrir: **todas las anclas de código de §3.A/§3.B se confirmaron exactas**, y
ninguna clasificación BORRAR/CABLEAR se invirtió. Los hallazgos son de **alcance** e **inventario**.

| # | hallazgo | dónde | consecuencia |
|---|---|---|---|
| RV-1 | denominador «17» mal contado (la tabla siempre tuvo 16 filas) | §2 | conteo corregido a 18 |
| RV-2 | **SIG9** y **SIG13** son sub-ítems rotulados del tracker y nunca tuvieron fila | tracker :204-215 | filas 3.1/3.2 añadidas |
| RV-3 | `McpState.pending_servers()` no estaba en DB-28 | tracker :101-103 | añadido a DB-28 |
| RV-4 | §7.3 se presentó como reversión propia; **el tracker ya decidía borrar `ModelRequest`** | tracker :159-163 | mi aporte fue la **razón** (deriva probada contra la firma viva), no la decisión — corregida la atribución |
| **RV-5** | **patrón: docstrings que afirman un cableado inexistente, exactamente en los módulos huérfanos** | `observer/observer.py:5` · `tasks/registry.py:4-5` y `:66` · `local/notification.py:5` | ver abajo |
| **RV-6** | «borrar `modes/` entero» borraría **`AgentMode`**, vocabulario T1 vivo | `modes/protocols.py:5-8` vs `:11-16` | **DB-01 re-alcanzado** (§3.A) |
| **RV-7** | `drain_notifications`/`process_background_notification` **sin consumidor en el base** | `notification.py:45-72` | **CORE-GAP nuevo `H-5`** (DB-29) |
| RV-8 | DB-h1 refinado: el fallo de las 6 Task* tools es **silencioso** | `dispatcher.py:83-84` | el `except Exception` convierte el `RuntimeError` de `get_registry()` en un `ToolResult.error` que sólo ve el modelo — sin log, sin excepción, en **cada** llamada |
| RV-9 | `_MAX_TURNS = 50` hardcodeado | `agent_loop.py:24` | DB-30, se pliega en DB-22 |
| RV-10 | `Session._new_session_id()` es un 4º productor de identidad **latente, no activo** | `session/session.py:34-35` vs `runtime.py:331` | refina el hallazgo previo: `runtime.py` **siempre** pasa `session_id=ctx.session_id`, luego el `default_factory` nunca se ejerce hoy. Sigue siendo un 4º sitio de autogeneración a unificar en **H-1/ID-1**, pero **no** una fuente activa de identidades divergentes |

### RV-5 · el mecanismo por el que los huérfanos sobrevivieron 18 ciclos

No es un hallazgo de inventario: es **causal**. Los tres módulos huérfanos están **documentados como si
estuvieran cableados**, en su propio docstring de módulo:

- `execution/observer/observer.py:5` — *«LocalAgentRuntime emite eventos vía `get_observer()`»*. Abierto
  `runtime.py` 1→EOF: **nunca** lo llama.
- `execution/tasks/registry.py:4-5` — *«El exterior registra su implementación vía `set_registry()`.
  LocalAgentRuntime la obtiene vía `get_registry()` sin saber de dónde viene»*, y `:66` lo repite. Abierto
  `runtime.py` 1→EOF: `:86` toma el registry **por inyección de instancia**; `set_registry` no lo llama nadie.
- `execution/local/notification.py:5` — *«El loop padre drena el canal al inicio de cada turno»*. Abierto
  `agent_loop.py` 1→EOF: **no hay drenaje** (RV-7).

**Por qué importa para el método, no sólo para el código.** Una auditoría que lee un módulo y cree su
docstring concluye «cableado» sin abrir el ensamblador — que es **exactamente** lo que L09 (*cablear ≠
existir*) prohíbe, y explica por qué estos seams cruzaron 18 ciclos por categoría antes de caer en un
rollup transversal. **Regla que este ciclo deja escrita: en este esfuerzo, un docstring no es evidencia de
cableado; sólo lo es el ensamblador abierto.** Además, al borrar cada huérfano hay que borrar su docstring
mentiroso — si sobrevive en un módulo vecino, reintroduce la creencia.

### DB-29 / `H-5` · canal de notificación background sin drenador (CORE-GAP)

- **Comportamiento (hoy)**: un subagente que termina llama `put_notification` (`runtime.py:299` vía
  `_notify` :294-304) y su `BackgroundNotification` queda encolada en el global `_channel`
  (`notification.py:22`, keyeado por `(user_id, session_id)`). **Nadie la saca.** `drain_notifications`
  (:45-46) y `process_background_notification` (:49-72) sólo aparecen re-exportados en
  `agentic_runtime/__init__.py` y `execution/__init__.py`. Verificado **por ausencia** sobre los dos
  archivos que tendrían que consumirlos, ambos abiertos 1→EOF este tramo: `loop/agent_loop.py`352 y
  `execution/local/runtime.py`435.
- **Doble consecuencia**: (a) **funcional** — el padre **nunca se entera** de que su subagente background
  terminó; el `<task-notification>` que `process_background_notification` sabe construir (:62-68) no entra
  en ningún historial. (b) **de recurso** — `_channel` es un `defaultdict(list)` de proceso que **sólo
  crece**: cada task background deja una entrada permanente. En el integrador multi-tenant es acumulación
  no acotada por `(usuario, sesión)`.
- **Tier**: **CORE-GAP**, no DEUDA-B. Por mímica-default (la carga de la prueba está en quien afirme que es
  del integrador): el canónico **sí** drena en el padre al inicio de turno, y el base ya trae la lógica
  genérica escrita (`process_background_notification` se declara a sí misma «comportamiento genérico del
  runtime», :50). Maquinaria completa sin su llamada = capacidad ausente.
- **Seam**: no hace falta inventar uno — **existe**: `root_turn_start_hooks` (`runtime.py:372-374`,
  `RuntimeConfig`). La pregunta de diseño para Fase B es si el drenaje es (i) un hook de arranque de turno
  que el base **registra por defecto**, o (ii) un paso propio del `AgentLoop` antes de componer el turno.
  Recomendación: **(ii)** — el orden respecto de `_inject_recall` (`agent_loop.py:112-130`) es observable, y
  dejarlo a un hook del integrador reproduce el mismo modo de fallo que acaba de destaparse.
- **Firma**: `AgentLoop._drain_notifications(ctx) -> None` al inicio de cada turno, llamando
  `drain_notifications(ctx.user_id, ctx.session_id)` y por cada entrada
  `process_background_notification(session, n)`; requiere que el loop alcance la `Session` (hoy vive en
  `runtime._run_loop:331`, **no** en el loop) — **liga con K2/ID-1 y con H-3**.
- **Cableado**: `agent_loop.run`, antes de componer el primer mensaje del turno; `_channel` deja de ser
  global y pasa a instancia del runtime (cierra el ítem #4 del censo §7.1, hoy anotado «des-globalizar, no
  bloquea» — **ya no es menor**).
- **Orden**: **después** de que la `Session` sea alcanzable desde el loop (K2/ID-1) y en el mismo tramo que
  **H-3** (`resume`), con el que comparte hogar (05) y superficie.
- **Prueba**: `test_parent_receives_task_notification_next_turn` (un subagente que termina → el siguiente
  turno del padre contiene el bloque `<task-notification>`); `test_channel_drained_is_empty` (anti-fuga).
- **Cara integrador**: hoy el integrador **debe** llamar `drain_notifications` a mano y no hay nada que se
  lo diga salvo un docstring que afirma lo contrario; tras el cableado, no llama nada — recibe el mensaje en
  el historial y proyecta su UI escuchando eventos, que es lo que `:53-55` ya declara como el reparto.
- **Destino**: `DEUDA-A.md` como **`H-5`**, junto a H-1..H-4. **Consecuencia declarada: A3.DA queda con un
  hallazgo posterior a su cierre**; se incorpora en **A-CIERRE**, no se re-abre el ciclo.


---

## 10. Addenda post-cierre — intento de A3.CAT, **RETRACTADO por el propio A3.CAT** (2026-07-27)

> A3.CAT intentó abrir aquí un ítem `CAT-DB-1` («`PlanModeProvider()` se registra incondicionalmente en
> `factory.py:146` ⇒ DEUDA-B»). **Se retracta**: `DEUDA-B §4 · cabo 7` **ya había fallado el tier** —
> *«Confirmado leyendo `factory.py:146` 1→EOF: `PlanModeProvider()` se registra **incondicionalmente** ⇒ decisión
> de **composición** → **A3.CAT**, no deuda. Lo que sí queda como DEUDA-B es el canal **no tipado**
> `app_state.native["plan_mode"]` (DB-19), secuenciado tras K1.»*
>
> El fallo era correcto y A3.CAT lo contradijo **sin haber abierto §4**. Reparto correcto:
> - **la decisión** (`battery_plan` es battery **OPCIONAL**) es de A3.CAT → `BATTERIES.md §4.4`;
> - **la ejecución** (retirar el literal de `:146` y que `Battery.providers(host)` lo aporte) es **trabajo de
>   composición de Fase C**, no un ítem de higiene ⇒ **no entra en este ledger**;
> - lo que **sí** vive aquí sigue siendo **DB-19** (canal no tipado `app_state.native["plan_mode"]`, tras K1),
>   que es cosa distinta y ya estaba.
>
> **`DEUDA-B.md` NO gana ítems. El reparto 12 BORRAR / 12 CABLEAR y el conteo 18=18=0 quedan intactos.**
> Registrado como hallazgo **CAT-h7** en `BATTERIES.md §6`: *un rollup posterior no puede re-tierar lo que un
> rollup anterior ya falló sin abrir el tramo donde lo falló.*
