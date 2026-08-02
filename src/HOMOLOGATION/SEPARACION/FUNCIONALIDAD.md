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
| 1 | `loop/` | 6 | 622 | 🟡 | pagados `ends_turn`, `H-L1`, `H-L2`, `H-L3` (§4). Sin auditar aún: `_drain_notifications`, `input_processor`, anuncios de la estrategia diferida, dedup de recall, filtro de pool por subagente, `model_options`, `system_override`, `context_modifier` (y su excepción), rama «[no dispatcher]». Abierto: `H-L4` |
| 2 | `tools/native/` | 19 | 1891 | ⛔ | — |
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

### Corrección de inventario (2026-08-02)

Declaré como hueco que «`ends_turn` se asevera como flag y nunca que el loop cierre el turno
por ese flag». **Falso como fue enunciado**: `test_agent_loop.py:234` y
`test_loop_homologation.py:261` ya aseveraban el efecto de loop. El hueco real era más fino y
es el que se pagó: **ninguno de los dos tenía control positivo** — ambos medían «el modelo se
llamó 1 vez», luego un loop roto que cortara SIEMPRE tras ejecutar tools los dejaba verdes; la
frase «sin ends_turn se re-llamaría (2)» vivía en un **comentario**, no en una aserción.
