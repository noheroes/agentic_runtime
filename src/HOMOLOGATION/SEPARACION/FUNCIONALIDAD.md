# FUNCIONALIDAD — auditoría de cobertura FUNCIONAL de la superficie cerrada por commit

> Artefacto de **ESTADO** (`D-09`): una viñeta = una línea; el log de ventanas vive en
> `PROGRESS.md`, no aquí. Abierto por encargo del usuario (2026-08-02):
> *«completemos todos los test funcionales para que aquello que esta cerrado por commit lo
> este completamente probado … "TODO" sin excepción, sin atajos, sin postergaciones»* y, a
> continuación, *«y luego los tests funcionales de lo que ahora esta abierto antes de seguir
> avanzando, con el mismo rigor … nada de esconder problemas "bajo la alfombra"»*.

## 1. Criterio — qué cuenta como test FUNCIONAL

Un test es **funcional** si su aserción es sobre un **efecto observable** producido por el
sujeto **realmente cableado**. No lo es si asevera:

| Categoría | Qué asevera | Cuenta |
|---|---|---|
| **funcional** | efecto: estado mutado, fichero escrito, turno cerrado, permiso denegado, mensaje que llega al modelo | ✅ |
| **forma / operativo** | nombres, claves de schema, flags, constantes, presencia de atributo | ❌ |
| **estructural** | grafo de imports, estado de clase, introspección | ❌ (necesario, no suficiente) |

Tres exigencias adicionales, sin las cuales un test funcional **no acredita**:

1. **Control positivo / negativo.** Si el test pasaría igual con el cable roto en el sentido
   contrario, no discrimina. Regla: *toda señal booleana necesita su gemelo sin la señal.*
2. **Cableado real, no stub del sujeto.** El stub es lícito en la frontera (modelo, red); nunca
   en el sujeto que se mide (`L09`: cablear ≠ existir).
3. **Acreditación por violación inyectada** (`D-12·b`). Verde a la primera = **no acreditado**.
   Se anuncia, se muta el fuente, se captura la corrida ENTERA a fichero, se revierte desde
   copia propia verificada por `sha256`. Nunca `git checkout`.

**Prohibido** para cerrar una fila: retocar el enunciado/prompt para que pase, mover el caso
fuera de alcance, relajar un umbral, o declarar la deuda en vez de pagarla (`D-07`).

## 2. UNIVERSO VALORABLE (`D-13`, 2026-08-02)

> El usuario acotó el alcance: *«todos los tests antiguos que no has modificado explícitamente
> producto de la refactorización prueban funcionalidades de la versión parcial de
> agentic_runtime, arrastrarlas no aportan nada … las demás salen del radar momentáneamente»*.

**Dentro del radar** = la superficie que la refactorización del TRAMO 1 tocó (`C1..C10` + el gate
`E1..E11`), **más** los tests que no se tocaron pero **operan sobre esa superficie** — ésos son
deuda del tramo y hay que revisarlos y actualizarlos, no heredarlos.

**Fuera del radar** = el resto de la suite. No se borra, no se cuenta, y se reincorpora cuando el
avance de la refactorización lo requiera. La métrica de cierre **deja de ser** el total de la
suite y pasa a ser la cobertura funcional de la superficie del tramo.

Censo total (referencia, no métrica): **131 módulos fuente**, ~11.000 líneas, 26 paquetes.
Veredicto por paquete; ✅ = todo comportamiento con prueba de efecto + control; 🟡 = parcial
(huecos nombrados); ⛔ = sin auditar; ⬜ = **fuera del radar** por `D-13`.

| # | Paquete | Módulos | Líneas | Veredicto | Huecos nombrados |
|---|---|---|---|---|---|
| 1 | `loop/` | 6 | 622 | 🟢 | **cable por cable, todos con efecto observable y control** (§4). Ya lo estaban por tests previos verificados como funcionales: `input_processor` (corte + reescritura + default identidad), anuncios de la estrategia diferida (+dedup entre iteraciones), `system_override`, `context_modifier` vía skills. Pagados en esta vuelta: `_drain_notifications` (5), filtro de pool por subagente **en ejecución**, filtro `background`, `model_options` (+control negativo), `[no dispatcher]`, excepción del modifier, ctx devuelto, dedup de recall **real**. Abiertos y nombrados: `H-L4` (fuera del radar), `FIND-LOOP-1` (§3) |
| 2 | `tools/native/` | 19 | 1891 | 🟢 | **Efecto observable de las 25 tools: YA pagado por `E10`** (cableado real, negativas, acreditado 7/7 — no se duplica). Pagado en la 9ª ventana: auditoría `H-L4` de sus dos ficheros de test y **8 xfail de FIRMA reescritos a CONDUCTA** (§5), 3 FORMA→CONDUCTA, `FIND-CFG-1` nuevo y
`FIND-TOOL5/SIG10` **pagado** con la causa localizada por contraste (§5.1). **Deuda de lectura PAGADA** (§5.2): los 19 módulos recorridos 1→EOF, y la lectura destapó **3 hallazgos nuevos** que la superficie de test no veía (`FIND-READ-1`, `FIND-READ-2`, `FIND-GLOB-1`) |
| 3 | `tools/` | 11 | 916 | ⛔ | — |
| 4 | `execution/local/` | 4 | 681 | ⛔ | — |
| 5 | `execution/` (+fork, tasks, session, observer, context) | 14 | 604 | ⛔ | — |
| 6 | `capabilities/mcp/` | 12 | 1592 | ⛔ | — |
| 7 | `capabilities/skills/` | 8 | 760 | ⛔ | — |
| 8 | `capabilities/memory/` | 5 | 361 | ⛔ | — |
| 9 | `capabilities/plan/` | 3 | 282 | ⛔ | — |
| 10 | `capabilities/` | 5 | 309 | ⛔ | — |
| 11 | `contracts/` | 15 | 1011 | ⛔ | — |
| 12 | `models/` | 3 | 517 | ⛔ | — |
| 13 | `context/` | 4 | 234 | ⛔ | — |
| 14 | `storage/` | 4 | 203 | ⛔ | — |
| 15 | `scripts/` | 1 | 161 | ⛔ | — |
| 16 | `hooks/` | 3 | 146 | ⛔ | — |
| 17 | `execution/fork/` | 1 | 116 | ⛔ | — |
| 18 | `signals/` | 3 | 114 | ⛔ | — |
| 19 | `events/` | 4 | 100 | ⛔ | — |
| 20 | raíz (`factory.py`, `runtime.py`) | 2 | 366 | ⛔ | — |
| 21 | `modes/` | 3 | 64 | ⛔ | — |
| 22 | `voice/` | 2 | 52 | ⛔ | — |

**Orden de ataque** (por carga funcional, no alfabético): 1 → 2 → 3 → 4 → 5 → 6..10 → 11..22.

## 3. FASE 2 — lo que está ABIERTO (encargo 2)

Un hallazgo abierto **sin test que lo fije** es exactamente la alfombra. Cada uno necesita una
prueba que asevere el comportamiento **tal como hoy es** (xfail estricto si el defecto es del
sujeto; marcador medido si es no-determinista), de modo que el día que cambie, el test hable.

| Hallazgo | Qué es | Test que lo fija | Estado |
|---|---|---|---|
| `FIND-E11-2` | el modelo no conduce `AskUserQuestion` (0/10 con sujeto homologado) | `D-14`: carencia declarada + puerta dura sobre anuncio/schema + `test_e11_vigila_carencias_declaradas` (xfail estricto que enrojece por XPASS si el modelo la conduce) | ✅ mitigado |
| `FIND-E11-1` | (ver ledger) | — | ⛔ |
| `FIND-E11-4` | descripción de B divergente de A | ✅ pagado + `test_description_es_la_que_A_manda_al_modelo` | ✅ |
| `FIND-C10-1` | `RuntimeFactory._modes` singleton mutable preexistente | `E8·e` lo congela y vigila | ✅ |
| `FIND-SEQ-1` | modelo emite 2 calls dependientes en el mismo turno (2/6) | marcador medido + transcript | ⛔ |
| `FIND-E2G-1` | cayó 1 de 4 inyecciones | falta la prueba que discrimine las otras 3 | ⛔ |
| `FIND-E2G-2` | diferido nombrado | — | ⛔ |
| `FIND-C6-2` | diferido nombrado | — | ⛔ |
| `FIND-CFG-1` | **NUEVO (9ª ventana), resuelto contra el canónico por `D-08` antes de tocar nada.** La rama GET de `Config` **escribe**: `ctx.app_state.native.setdefault("config", {})` corre antes de bifurcar (`config.py:44`), así que una simple lectura deja la clave creada en el estado de la sesión. A tiene el GET como lectura pura —`call()` sólo llama a `getValue()`, que lee de `getGlobalConfig()`/`getInitialSettings()` (`ConfigTool.ts:136-144`)— **y lo DECLARA**: `isReadOnly(input) { return input.value === undefined }` (`:90-92`). Medido: el GET deja `{'config': {}}` | `test_tools_native_homologation.py::test_config_get_does_not_write_state` (xfail estricto; incluye control positivo de que el SET sólo actúa por su `context_modifier`) | ⛔ abierto — **fuente NO tocado a propósito**: contrastar contra el canónico y dejar el rojo como evidencia, no «arreglar» por impulso |
| `FIND-LOOP-1` | **NUEVO, cazado escribiendo la prueba (nació roja).** El loop acepta que un `context_modifier` devuelva OTRO ctx (`ctx = modifier(ctx) or ctx`), pero `ctx.tool_pool` es estado DEL TURNO: un modifier que forka sin arrastrarlo deja al dispatcher con el pool vacío y **las tool calls restantes del mismo turno fallan en silencio** («no encontrado en el tool pool»), indistinguibles de un resultado de tool normal | `test_agent_loop.py::test_FIND_LOOP_1_un_fork_ingenuo_del_ctx_mata_las_tool_calls_restantes` — asevera la conducta REAL, no la deseable | ⛔ abierto |
| `FIND-READ-1` | **NUEVO (9ª ventana), destapado por la LECTURA, no por el test.** `read_file` no tiene **ningún** cap: `read_file.py:38` hace `limit = input.get("limit", len(lines))`, así que sin `limit` explícito el fichero entero entra al contexto. A aplica **dos** topes y **lanza** en desbordamiento: `maxSizeBytes` 256 KB sobre el tamaño total y `maxTokens` 25 000 sobre la salida (`FileReadTool/limits.ts:1-18`), y la cabecera documenta que probaron truncar (#21841, mar-2026) y lo **revirtieron** porque el throw cuesta ~100 B de error y truncar costaba 25 K tokens. CORE-GAP: la protección existe en el hermano (`grep_tool.py:12-15` sí la documenta y la aplica). Medido: 300 000 B salieron enteros | `test_tools_native_homologation.py::test_read_file_refuses_a_file_over_the_canonical_size_cap` (xfail estricto, con control positivo de que un fichero pequeño sigue leyéndose entero) | ⛔ abierto — **fuente no tocado**: contraste primero |
| `FIND-READ-2` | **NUEVO (9ª ventana).** Dos mitades del mismo contrato: (a) `offset` es **0-indexado** en B (`read_file.py:37-39`, índice de lista Python) y **1-indexado** en A (`FileReadTool.ts:497`, `{ offset = 1 }`) ⇒ **off-by-one silencioso** en la tool con la que el modelo cita código; (b) B emite las líneas desnudas, A devuelve `addLineNumbers(file)` (`:726`) ⇒ sin numeración no se puede referenciar `fichero:línea` sin contar a mano. Medido: `offset=1` devolvió `'dos'` donde A da `'uno'` | `test_tools_native_homologation.py::test_read_file_offset_is_one_indexed_and_output_is_numbered` (xfail estricto) | ⛔ abierto |
| `FIND-GLOB-1` | **NUEVO (9ª ventana).** B ordena **alfabéticamente** (`glob_tool.py:40`, `sorted(...)`); A ordena por **mtime** con `--sort=modified` y el comentario explícito «oldest first» (`utils/glob.ts:94-104`), y recorta DESPUÉS (`:127`). **El orden no es presentación cuando hay cap: es selección** — con el cap de 100 que ambos comparten, el orden decide *cuáles* 100 de 130 ve el modelo. Medido con mtimes sembrados (no dependiente del disco): B dio `aaa·mmm·zzz`, A daría `zzz` primero | `test_tools_native_homologation.py::test_glob_orders_by_mtime_not_alphabetically` (xfail estricto, con control positivo de que los 3 salen) | ⛔ abierto |
| `FIND-TOOL5/SIG10` | **PAGADO (9ª ventana).** Mi diagnóstico previo («la señal de abort es binaria») era **falso**: `AbortController` deriva `aborted` de `AbortReason` para cerrar `SIG2`. La causa real era de una línea — `dispatcher.py:54-55` devolvía `ToolResult.aborted(tool_name)` tirando el `ctx.stop.reason()` disponible en la línea anterior, dejando dos cortes de causa distinta indistinguibles. A trata `signal.reason` como dato de primera clase (`StreamingToolExecutor.ts:213-229`) ⇒ CORE-GAP | `test_tools_infra_homologation.py::test_abort_reason_reaches_the_result` (ya no xfail) | ✅ pagado — `reason` viaja al resultado **y al `output`**. `interrupt_behavior` **sigue abierto y aparte**: `contracts/tools.py:3-6` lo declara fuera del tramo 1 |

## 4. Registro de capacidades funcionales pagadas en esta obra

| Fecha | Capacidad | Test(s) | Acreditación |
|---|---|---|---|
| 2026-08-02 | `ends_turn` cierra el turno **y sin la señal el loop re-entra** | `test_agent_loop.py::test_tool_ends_turn_no_reinvoca_al_modelo` + `::test_tool_sin_la_senal_el_loop_reentra` | INY-12 (quita `_ends_turn or` de la condición) → 1 roja; INY-13 (`_ends_turn` incondicional) → roja el control positivo. 2 inyecciones → 2 rojas, 0 falsos positivos |
| 2026-08-02 | `H-L1` · **abort a mitad de stream**: corta al detectar la señal por evento, cierra el generador (`aclose`), no acumula lo posterior, no registra el turno parcial, no despacha sus tool calls | `test_agent_loop.py::test_abort_a_mitad_de_stream_corta_sin_registrar_ni_despachar` + control positivo `::test_sin_abort_el_mismo_stream_se_consume_entero` | INY-14 (borra el chequeo dentro del `async for`) → roja; INY-15 (no llama `aclose`) → roja; INY-16 (`break` → `pass`: registra y despacha lo abortado) → roja. 3 inyecciones → 3 rojas |
| 2026-08-02 | `H-L2` · el error del modelo entra al historial, nombra el outcome y viaja en `detail` | `test_agent_loop.py::test_loop_handles_error_event` (antes: **cero aserciones**) | INY-17 (quita el `append` de `[error: …]`) → 1 roja, **y sólo ese test la caza**: antes de este trabajo el runtime podía dejar de registrar el error del modelo con la suite entera en verde |
| 2026-08-02 | `H-L3` · reason-codes de corte aseverados: `ABORTED_PRE_RUN`, `ABORTED_TOOLS`, `MAX_TURNS` (+`detail`), y la property `LoopOutcome.aborted` en los cinco casos | `test_agent_loop.py::test_abort_pre_run_y_su_reason` + refuerzo de `test_loop_homologation.py::test_loop_abort_between_turns_stops_reprompt` y `::test_loop_max_turns_ceiling_bounds_runaway` | INY-18 (ambos reason-codes → `COMPLETED`) → 3 rojas (las dos reforzadas + `test_loop_accepts_configurable_max_turns`), 0 falsos positivos |

**Acreditación acumulada de la obra funcional: 7 inyecciones (INY-12..18) → 7 rojas, 0 falsos
positivos.** `ruff` sobre `test_agent_loop.py`: 4 errores **preexistentes**, sin variación (deuda
cero neta). Corridas capturadas enteras en `/tmp/iny_endsturn_OJQp/iny1{2..8}.log`.

| 2026-08-02 | `D-14` · `E11` mitigado: la carencia del modelo deja de bloquear, pero el anuncio y el schema homologado pasan a ser **puerta dura** (antes no se exigían) y la carencia queda vigilada en ambos sentidos | `test_tramo1_gate.py::test_e11_…` + `::test_e11_vigila_carencias_declaradas` | INY-19 (mutar la `description` del sujeto) → **VERDE = falso negativo cazado**: la comparación anuncio↔sujeto es tautológica ante una mutación del sujeto; INY-19b → roja en `test_ask_user.py` (ahí vive la fidelidad a A); INY-20 (el runtime trunca la description al anunciar) → **roja**; INY-21 (forzar «el modelo sí la condujo») → **roja por XPASS estricto** |
| 2026-08-02 | `H-L4` pagado en los xfail del loop tocados: `GAP-L3` y `GAP-L4` pasan de FIRMA a COMPORTAMIENTO | `test_loop_recupera_con_modelo_de_fallback`, `test_loop_compacta_el_historial_al_exceder_el_presupuesto` | fallan ahora por el gap real y medido (`intentos=['primario']`, `61 mensajes sin compactar`), no por `inspect.signature` |

**Estado del gate tras `D-14`: `33 passed / 1 xfailed / 0 failed` en UNA corrida** (2026-08-02,
`GATE_E11_SEED=14329873`), con `E11` conduciendo 10 de 11 y la 11ª declarada, medida y vigilada.

| 2026-08-02 | **`S21`/`H-5` · el CABLE del drenaje**: el loop drena, el XML llega **al modelo**, va **antes** del prompt del usuario, **sólo la raíz** drena (y la notificación del hermano sobrevive al turno del hijo), la clave es el par `(scope, session_id)`, se drena **una vez por `run()`** y sin canal inyectado no se toca el canal global | `test_background_notification_channel.py::test_el_loop_drena_el_canal_y_el_XML_llega_al_MODELO`, `::test_el_drenaje_va_ANTES_del_mensaje_del_usuario`, `::test_un_SUBAGENTE_no_drena_…`, `::test_el_loop_drena_con_la_clave_del_ctx_no_con_otra` (+control positivo), `::test_se_drena_una_vez_por_run_no_una_por_turno`, `::test_sin_canal_inyectado_…` | INY-24 (no drena) → 5 rojas; INY-25 (drenar DESPUÉS del prompt) → 1 roja, justo la del orden; INY-26 (quitar `or ctx.is_subagent`) → 1 roja; INY-27 (clave con scope `""`) → 5 rojas; INY-33 (`apply_notification` sobre una copia) → 11 rojas |
| 2026-08-02 | **filtro de pool por subagente en la EJECUCIÓN**, no sólo en el anuncio; y filtro `background` (`safe_for_background`) en ambos extremos | `test_subagent_application.py::test_la_restriccion_corta_tambien_la_EJECUCION_no_solo_el_anuncio` (+control positivo), `::test_subagente_unattended_solo_recibe_tools_safe_for_background` (+control positivo) | INY-22 (`_restrict_to_agent_tools` no filtra) → 3 rojas; INY-23 (`mode` siempre `foreground`) → 1 roja |
| 2026-08-02 | `S1` · `model_options` viajan al caller **y lo no pedido NO viaja como `None` explícito** (la promesa de robustez ante callers de terceros) | `test_agent_loop.py::test_model_options_llegan_al_caller_como_kwargs`, `::test_lo_no_pedido_NO_viaja_como_None_explicito` | INY-28 (no transportar opciones) → 2 rojas; INY-29 (`as_kwargs` devuelve los `None`) → 17 rojas — el reventón masivo **es** la medida de para qué existe el contrato |
| 2026-08-02 | rama `[no dispatcher]`: la tool call se contesta igual, con `tool_call_id`, para no dejar una llamada colgando en el turno siguiente | `test_agent_loop.py::test_sin_dispatcher_la_tool_call_se_contesta_y_el_turno_sigue` | INY-30 (`continue` sin `append`) → 1 roja |
| 2026-08-02 | `context_modifier` del `ToolResult`: la excepción se traga **a propósito** (el trabajo ya hecho se conserva) y el ctx devuelto es el que ve la tool siguiente | `test_agent_loop.py::test_un_modifier_que_revienta_no_tumba_el_turno`, `::test_el_ctx_que_el_modifier_devuelve_es_el_que_ve_la_tool_siguiente`, `::test_si_el_modifier_devuelve_OTRO_ctx_…` (+control negativo) | INY-31 (propagar la excepción) → 1 roja; INY-32 (`modifier(ctx)` tirando el retorno) → 2 rojas |
| 2026-08-02 | dedup de recall **entre turnos reales** | `test_capability_systemprompt_and_recall.py::test_recall_deduped_across_turns` (reescrito: antes corría UN turno y pre-sembraba el mensaje a mano) | INY-34 (quitar el `if rendered in existing: continue`) → 2 rojas |

**Acreditación de esta vuelta: INY-22..34 (13 inyecciones) → 13 rojas, 0 falsos positivos.** Cada
una anunciada antes de tocar el fuente y revertida desde copia propia con `sha256sum -c` en verde
(`loop/agent_loop.py`, `models/protocol.py`, `contracts/notifications.py`). Corridas capturadas
enteras en `$SCRATCH/iny-2{2..9}.log`, `iny-3{0..4}.log`. Deuda **cero neta**: `ruff` 505 ·
`mypy --strict` 138/54 · suite sin gate **701 passed / 0 failed / 3 skipped / 112 xfailed**.

### Tests no tocados que operaban sobre superficie modificada (encargo 3)

Revisados uno a uno; el veredicto **no** fue «casi todos valían»:

- `test_background_notification_channel.py` — `test_apply_operates_on_the_live_history_not_on_a_session`
  aseveraba `params[0] == "messages"`: **patrón `H-L4`**, forma disfrazada de conducta. Reescrito a
  identidad de objeto + mutación in-place. Los dos `test_run_loop_does_not_…` son estructurales
  (`inspect.signature` / `inspect.getsource` con `in`): se conservan como guarda barata, pero
  quedan rotulados como **necesarios-no-suficientes**, y su contraparte funcional es el bloque de
  drenaje nuevo. Que este fichero pasara entero mientras el cable del loop no lo probaba nadie es
  el ejemplo vivo de `L09`.
- `test_subagent_application.py` — funcional, con controles, pero medía **sólo el anuncio** de una
  restricción cuyo docstring promete anuncio **y** ejecución. La mitad que faltaba es justo la que
  sostiene el candado.
- `test_capability_systemprompt_and_recall.py` — funcional; su `test_recall_deduped_across_turns`
  se llamaba «across turns» y corría un turno. Reescrito.
- `test_deferred_delta.py`, `test_deferred_strategy.py`, `test_deferred_loading.py`,
  `test_skill_invocation.py`, `test_loop_homologation.py` (`S11`), `test_root_context_modifier.py`,
  `test_caller_system_override.py` — verificados **funcionales y suficientes** para su cable; no se
  tocan.

### `H-L4` — pagado en el radar, abierto fuera de él

Los dos xfail de gap del loop (`GAP-L3` fallback model, `GAP-L4` compaction engine) aseveran
**la FIRMA**, no el comportamiento: `assert "fallback_model" in inspect.signature(...).parameters`.
El día que alguien añada el parámetro sin implementar nada, el xfail pasa a **XPASS y acredita
como pagado un gap que no lo está**. Un gap se fija por su comportamiento ausente (un
`ErrorEvent` debe provocar reintento con otro modelo), no por su parámetro ausente. Pendiente
**Pagado** en los dos xfail del loop (que están en el radar). El mismo patrón queda **por auditar
en los otros xfail de la suite**, que por `D-13` están fuera del radar hasta que su superficie
entre en un tramo.

**Un hallazgo colateral, dicho porque casi cuela:** al reescribir `GAP-L3` el test usaba
`ErrorEvent` sin importarlo en ese fichero. El xfail seguía «pasando» — pero por `NameError`, no
por el gap. Un xfail estricto no distingue *«falla por lo que dice el reason»* de *«falla por un
error tonto»*; lo cazó `ruff F821`, no pytest. Los dos xfail reescritos se verificaron con
`--runxfail` para leer el fallo real.

## 5. `tools/native/` — 9ª ventana (2026-08-02)

**Corrección de premisa, dicha primero.** La retoma daba `tools/native/` por ⛔ sin pagar. Leído
el gate 1→EOF (4299 L), eso era **falso**: `E10` ya es una matriz funcional de las **25** tools con
efecto observable, cableado real y negativas, acreditada con 7 inyecciones → 7 rojas. Duplicarla
habría sido volumen, no grado. El trabajo realmente impagado era otro y es el que se hizo.

### `H-L4` — la auditoría que el tramo anterior dejó fuera del radar

Auditados uno a uno los 11 `xfail` de `test_tools_native_homologation.py` y los 6 de
`test_tools_infra_homologation.py`. **Ocho acreditaban en falso** y se reescribieron a CONDUCTA.
Tres de los de `infra` eran **peores que FIRMA**: aseveraban sobre `_FakeTool`, el **doble** del
propio fichero — añadirle un método al doble los habría puesto XPASS **sin que el runtime cambiara
una línea**.

| xfail | Aseveraba (FIRMA) | Ahora asevera (CONDUCTA) | Fallo real medido |
|---|---|---|---|
| `test_fs_shell_tools_…` | `BashTool.name == "Bash"` | el **registry de producción** resuelve el nombre | `resolve('Bash')` → `None` |
| `test_edit_replace_all_…` | `"replace_all" in input_schema` | las 3 ocurrencias reemplazadas **en disco** | error de ambigüedad, fichero intacto |
| `test_worktree_offered_…` | `safe_for_background is True` | el filtro REAL `list_available(mode="background")` | 20 tools ofrecidas, sin `EnterWorktree` |
| `test_task_update_transitions_…` | `"status" in input_schema` | `TaskGet` devuelve el status pedido | pidió `completed`, devuelve `pending` |
| `test_dispatcher_honours_block_…` | `t.interrupt_behavior()` **sobre el doble** | el dispatcher respeta `block` ante un abort | canceló la tool `block` igual |
| `test_concurrency_safe_…_parallel` | `isinstance(t.is_concurrency_safe, …)` **sobre el doble** | dos tools del turno **se solapan** | **0,40 s medidos** vs 0,35 (serie) |
| `test_new_messages_…_conversation` | `isinstance(r.new_messages, list)` | los mensajes **llegan a `ctx.messages`** | no llegan |
| `test_abort_reason_…` | `getattr(r,"reason",…)` | el motivo viaja en lo que el modelo **lee** | `'aborted: Bash'` genérico → **PAGADO, ver §5.1** |

Siete siguen **rojos y por el mismo gap**: se invirtió el sujeto de la aserción, no se relajó el
listón. Verificados con `--runxfail` para leer el fallo real (un xfail no distingue «falla por el
gap» de «falla por un typo»). El octavo (`test_abort_reason_…`) dejó de ser xfail porque el gap se
**pagó**: §5.1.

### 5.1 `FIND-TOOL5/SIG10` — PAGADO, con la causa localizada por contraste

**Mi diagnóstico era falso y se corrige aquí.** Dije que el gap era «la señal de abort es
binaria». `contracts/abort.py` define `AbortReason` y `AbortController` **deriva `aborted` de la
razón** precisamente para cerrar `SIG2`: la señal lleva el motivo desde que ese contrato existe.
El gap real estaba un eslabón más abajo y era de **una línea** — `dispatcher.py:54-55` consultaba
`ctx.stop.aborted` y devolvía `ToolResult.aborted(tool_name)` **tirando el `ctx.stop.reason()` que
tenía disponible en la línea anterior**.

Contraste (`D-08`, leído en A): `signal.reason` es dato de primera clase — se fija al abortar
(`abort('interrupt')` · `abort('sibling_error')` · `abort('user-cancel')` · `abort('background')`)
y se lee para decidir qué se cancela y con qué motivo (`StreamingToolExecutor.ts:213-229`:
`streaming_fallback` · `sibling_error` · `user_interrupted` · `null`). Perder la razón en el
resultado es **CORE-GAP, no divergencia** (`L10` no aplica: no hay nada que acreditar como mejora).

**Ajuste aplicado**: `ToolResult` acepta `reason`, `ToolResult.aborted()` la propaga al campo y al
`output`, y el dispatcher deja de tirarla. **`interrupt_behavior` NO se ajustó**: `contracts/tools.py:3-6`
lo declara **fuera del tramo 1** y el contraste no autoriza a colarlo por la puerta de atrás — su
xfail (`test_dispatcher_honours_block_…`) sigue rojo y sigue siendo deuda declarada. Los dos gaps
son distintos y se pagan por separado.

| Fecha | Capacidad | Test | Acreditación |
|---|---|---|---|
| 2026-08-02 | la razón del corte sobrevive señal→resultado→`output` | `test_abort_reason_reaches_the_result` | **INY-43′ y INY-44″ → 2 rojas.** 43′ = el dispatcher tira `reason` · 44″ = la razón se guarda pero no llega al `output` |

⚠ **Un falso negativo mío, cazado por la propia inyección y dicho aquí.** La primera pasada de
INY-44′ salió **verde**: el test comparaba la tupla `(reason, output)` de dos cortes, y basta con
que difiera el `reason` para que la tupla difiera — vaciar el `output` no lo ponía en rojo, pese a
que el `output` es lo único que el modelo lee. Se separaron las aserciones (campo por un lado,
`output` por otro, más pertenencia del literal de cada razón) y se repitió la inyección: roja.
Sin la inyección, esa aserción habría quedado acreditando en falso, que es exactamente `H-L4`.

⚠ **Un error de método mío, también dicho.** El backup con el que revertí la primera ronda era del
estado **pre-arreglo**, así que la reversión **borró el arreglo** en vez de restaurarlo, y el
`sha256sum -c` en verde confirmaba el estado equivocado. La ronda entera se descartó y se repitió
con backup del estado **arreglado** (`fix9b`). Lección: la copia de reversión debe ser del estado
que se quiere conservar, no del que había cuando se empezó a mirar.

### FORMA → CONDUCTA en los que ya pasaban

`Edit.name` → resolución por el registry de producción · `DEFAULT_GLOB_LIMIT` → **130 ficheros
sembrados, 100 salen + aviso de truncado**, con control positivo por debajo del cap ·
`_validate_slug` (llamada directa a una función privada, unidad, no conducta) → rechazo por
`execute()`, con control positivo que distingue «murió por el slug» de «murió por no haber repo».
`DEFAULT_HEAD_LIMIT == 250` se **conserva como FIRMA declarada**: el cap de grep se ejerce en
`E10`, y resembrar 250 líneas aquí no añade grado, sólo tiempo.

| Fecha | Capacidad | Test(s) | Acreditación |
|---|---|---|---|
| 2026-08-02 | los 8 tests **que pasan** de `test_tools_native_homologation.py` | (los del fichero) | **INY-35..42 (8 inyecciones) → 8 rojas, 0 falsos positivos.** Cada inyección tumbó **exactamente** su test dejando los otros 7 verdes: sin acoplamiento espurio. Nombre canónico de `Edit`, cap de glob, cap de grep, `context_modifier` de `TodoWrite`, `ends_turn` de `AskUserQuestion`, guarda root-only de `EnterPlanMode`, consulta del slug en `worktree`, `minItems` del cuestionario |

Anunciadas antes de tocar el fuente y revertidas desde copia propia: `sha256sum -c` → **7 OK**
(`file_edit · glob_tool · grep_tool · todo_write · ask_user · plan_mode · worktree`).
Deuda **cero neta**: `mypy --strict` **138/54** (idéntico a la base) · `ruff` **sin hallazgos en
los dos ficheros tocados** · suite **735 passed / 3 skipped / 114 xfailed / 0 failed**, y tras el
arreglo de §5.1 **736 passed / 3 skipped / 113 xfailed / 0 failed** (el xfail pagado pasa a passed,
cuadra exacto) con `mypy --strict` **138/54** sin cambio.

✅ **`ruff` 505 — pendiente RESUELTO al cierre de la ventana, y el error era mío.** Dije que no
reproducía la cifra base; la causa no era la falta de `[tool.ruff]` sino que yo estaba corriendo el
binario del venv de **otro** proyecto (`packages_openclaw`, ruff 0.15.5 → 11 hallazgos) en vez del
comando **documentado en el propio `pyproject.toml:45`**: `uvx ruff check src/agentic_runtime`.
Con él salen **506**, o sea **+1 sobre la base**. Aislado montando un worktree en el commit de
cierre de la 8ª ventana (`f15ab3d`) y difando por fichero+regla: da **505 exactos**, y el +1 era un
`I001` (bloque de imports sin ordenar) **introducido por mí** en `test_tools_infra_homologation.py`.
Corregido ⇒ **505**, idéntico a la base. Lección: «no reproduzco la cifra» era, de hecho, «no estoy
corriendo el comando que el repo documenta» — el pendiente había que cerrarlo, no heredarlo.

### 5.2 Deuda de LECTURA pagada — los 19 módulos 1→EOF, y lo que sólo se ve leyendo

`D-07`: una deuda de lectura se paga o el ciclo no cierra. Recorridos 1→EOF los 19 módulos
(1891 L): `__init__` · `bash` · `sleep` · `write_file` · `read_file` · `glob_tool` · `grep_tool` ·
`todo_write` · `tool_search` · `web_fetch` · `plan_mode` · `agent` · `web_search` ·
`clone_repository` · `ask_user` · `worktree` (+ `config` · `file_edit` · `task_tools`, leídos antes
en esta misma ventana). Con esto el paquete pasa 🟡→**🟢**.

**`L08` confirmado en la práctica, no citado**: la superficie de test estaba en verde y aun así la
lectura destapó **tres hallazgos** que ningún test miraba, y ninguno está en los ficheros grandes —
salen de `read_file.py` (42 L) y `glob_tool.py` (47 L), dos de los **más pequeños** del censo. Es
exactamente el modo de fallo que `L02` tipifica: la superficialidad migra a los satélites.

Confirmados en fuente (ya tenían test, ahora tienen la línea): `bash.py:13` `name = "bash"` en
minúscula frente al `Bash` canónico · `tool_search.py:53-55` el `select:` toma **un** nombre, sin
coma-separado (`FIND-TOOL6/E6`) · `web_search.py:74` la credencial sale de `os.getenv("SERPER_API_KEY")`
y no del `ctx`, a diferencia de `ctx.git_credentials` en `clone_repository.py:116` — el diferido ya
nombrado, ahora con la asimetría localizada entre dos módulos hermanos.

Los tres hallazgos nuevos se dejan **rojos y con el fuente sin tocar**, misma regla que `FIND-CFG-1`:
contraste contra el canónico primero, el rojo es la evidencia. Verificados con `--runxfail` para leer
el fallo real, y los tres llevan control positivo que pasa antes de la aserción que falla.

### Corrección de inventario (2026-08-02)

Declaré como hueco que «`ends_turn` se asevera como flag y nunca que el loop cierre el turno
por ese flag». **Falso como fue enunciado**: `test_agent_loop.py:234` y
`test_loop_homologation.py:261` ya aseveraban el efecto de loop. El hueco real era más fino y
es el que se pagó: **ninguno de los dos tenía control positivo** — ambos medían «el modelo se
llamó 1 vez», luego un loop roto que cortara SIEMPRE tras ejecutar tools los dejaba verdes; la
frase «sin ends_turn se re-llamaría (2)» vivía en un **comentario**, no en una aserción.
