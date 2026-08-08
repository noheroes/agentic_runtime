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
| 1 | `loop/` | 6 | 622 | 🟢 | **cable por cable, todos con efecto observable y control** (§4). Ya lo estaban por tests previos verificados como funcionales: `input_processor` (corte + reescritura + default identidad), anuncios de la estrategia diferida (+dedup entre iteraciones), `system_override`, `context_modifier` vía skills. Pagados en esta vuelta: `_drain_notifications` (5), filtro de pool por subagente **en ejecución**, filtro `background`, `model_options` (+control negativo), `[no dispatcher]`, excepción del modifier, ctx devuelto, dedup de recall **real**. Abiertos y nombrados: `H-L4` (fuera del radar). `FIND-LOOP-1` **pagado en la 10ª ventana** (§3): `_adoptar_ctx_modificado` repone el `tool_pool` del turno tras un fork y hace ruidosa la pérdida de los cables del integrador |
| 2 | `tools/native/` | 19 | 1891 | 🟢 | **Efecto observable de las 25 tools: YA pagado por `E10`** (cableado real, negativas, acreditado 7/7 — no se duplica). Pagado en la 9ª ventana: auditoría `H-L4` de sus dos ficheros de test y **8 xfail de FIRMA reescritos a CONDUCTA** (§5), 3 FORMA→CONDUCTA, `FIND-CFG-1` nuevo y
`FIND-TOOL5/SIG10` **pagado** con la causa localizada por contraste (§5.1). **Deuda de lectura PAGADA** (§5.2): los 19 módulos recorridos 1→EOF, y la lectura destapó **3 hallazgos nuevos** que la superficie de test no veía (`FIND-READ-1`, `FIND-READ-2`, `FIND-GLOB-1`). **10ª ventana: los tres PAGADOS**, más `FIND-GLOB-2` (nuevo: A pasa `--files`, B emitía directorios) y `FIND-NATIVE-READ/A3b` (numeración, cerrado de arrastre). El gate `E10` enrojeció con el contrato nuevo y se actualizó SIN relajarlo — sigue siendo igualdad exacta, ahora también sobre el formato. **`FIND-CFG-1` también pagado ⇒ el paquete queda sin hallazgos abiertos**; su fichero de test pasa de 13 passed / 11 xfailed a **14 / 10** |
| 3 | `tools/` | 11 | 916 | ⛔ | — |
| 4 | `execution/local/` | 4 | 681 | ⛔ | — |
| 5 | `execution/` (+fork, tasks, session, observer, context) | 14 | 604 | ⛔ | — |
| 6 | `capabilities/mcp/` | 12 | 1592 | ⛔ | — |
| 7 | `capabilities/skills/` | 9 | 1149 | 🟡 | **21ª ventana** (`VALIDACION § 2 sexies`): pagados `FIND-SKILL9/17` (el catálogo no llegaba al modelo por NINGUNA vía; A tiene **una**, no dos — premisa corregida), `-20` (identidad ← directorio), `-21` (`source`/`loaded_from` + first-wins con dedup por identidad real de fichero) y los cuatro `xfail` que XPASSaron al pagarse: `FIND-SKILL2`, `FIND-SKILL4` (= `LAT-SKILL1`, abierto por duplicado por mí y unificado), `FIND-SKILL17`, `FIND-SKILL18`. `INY-120..138` → **16 rojas + 3 VERDES que son el hallazgo** (guarda `skill_tool_available` sin medir, sidecar medido sólo en escritura + fixture multilínea que converge igual, guarda `errorCode`-4 sin ningún test, frontera del marco no observable). ⛔ **Abierto y NO pagado: `FIND-SKILL-22`** (A ejecuta el shell embebido en el markdown de la skill, con exención para las de MCP por no confiables — frontera de confianza que B no tiene dónde declarar). ⛔ **Deuda de LECTURA sin pagar**: los 9 módulos no se han recorrido 1→EOF, así que el paquete NO puede pasar a 🟢 (`D-07`) |
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
| `FIND-E11-1` | **CERRADO POR CONTRASTE (10ª ventana): estaba MAL ENUNCIADO y no hubo que tocar fuente.** Decía «no existe costura para restringir las tools del agente RAÍZ», y tenía dos mitades: (1) que `initial_allowed_tools` sea **aditivo** y no recorte nada es **fiel a A** —`createGetAppStateWithAllowedTools` (`forkedAgent.ts:147-171`) también suma sobre `alwaysAllowRules.command`—, o sea que el defecto estaba en mi andamio de `E11`, no en el sujeto; (2) lo que A sí tiene, el recorte por DENY **antes del anuncio** (`filterToolsByDenyRules` dentro de `getTools()`, `tools.ts:262-268`, literal *«before the model sees them — not just at call time»*, alimentado por `alwaysDenyRules: {cliArg: parsedDisallowedToolsCli}` en `permissionSetup.ts:983` y por `--base-tools`), **B lo tiene igual**: `assemble_tool_pool` filtra por `denied_names()` al ensamblar (`tools/pool.py:59-73`) y el integrador llega hasta ahí por `root_context_modifier` (`runtime.py:427-428`), que corre antes de que el loop construya el pool del turno (`agent_loop.py:350`) | `test_runtime_e2e.py::test_e2e_el_integrador_puede_recortar_el_catalogo_del_agente_raiz` — mide lo **ANUNCIADO** al caller (una tool que el modelo no ve no la puede elegir), con control positivo (el recorte es selectivo, no un catálogo vacío) y control negativo (sin el modifier, `echo` sí se anuncia) | ✅ cerrado — costura existente **y cableada**, probada corriendo sobre el runtime de `create_runtime()`. `L09` al revés: aquí sí estaba cableada y el hallazgo la daba por ausente |
| `FIND-E11-4` | descripción de B divergente de A | ✅ pagado + `test_description_es_la_que_A_manda_al_modelo` | ✅ |
| `FIND-C10-1` | `RuntimeFactory._modes` singleton mutable preexistente | `E8·e` lo congela y vigila | ✅ |
| `FIND-SEQ-1` | **MITIGADO POR `D-14` (10ª ventana).** El modelo emite las 2 calls dependientes en el MISMO turno rellenando el argumento con placeholder (`''` / `'__PENDING__'`); diagnosticado con el transcript entero, no supuesto: dos `tool_start` **consecutivos** antes de cualquier `tool_result`. **La parte del runtime está intacta y se comprobó**: despachó las dos, entregó el token REAL al historial y dio un turno más — el modelo elige reportar el `ERROR: token inválido` en vez de reintentar con el token que ya tiene delante. Nada en A serializa dependencias entre calls de un mismo turno (particionar por `is_concurrency_safe` es fan-out, no esto), y **ningún orden de ejecución arregla un argumento ya emitido**. **Hipótesis de «efecto de corrida pareada» MEDIDA Y DESCARTADA**: 4/4 en pareado + 5/5 solo + 3/3 = **12/12**, y en las 4 pareadas el token **CRUZÓ** (o sea se ejerció la rama de gate duro, no la de vigilancia) | `test_runtime_e2e_real.py::test_real_sequential_dependent_tools` **partido, no relajado**: gate DURO en lo del runtime (COMPLETED · ambas despachadas · ≥2 `tool_result` · **el token real en el transcript** · `turn_count>=2`) + rama de VIGILANCIA que sólo tolera la carencia con su FORMA exacta (placeholder Y canje rechazado); si el token cruza, el cierre pasa a gate duro (`final` en la respuesta + `turn_count>=3`). La rama tomada se IMPRIME en cada corrida | ✅ mitigado |
| `FIND-E2G-1` | **REPRODUCIDO Y ACOTADO, NO MITIGADO (10ª ventana)** — venía anotado como «intermitente y no reproducido»; **volvió, y la vigilancia hizo justo lo que se le pidió**. Marcador estable en TRES configuraciones distintas: **6/8 · 6/8 · 6/8 en la rama nativa, 24/24 en la simulada**, siempre el mismo caso (`archivos/nativa`). **TERCERA HIPÓTESIS MÍA, TAMBIÉN REFUTADA, y es la que más me costó ver:** dije que «la expansión server-side entrega un SUBCONJUNTO y nunca surte `grep`/`read_file`», y construí sobre eso un split `D-14` con un conjunto `resolutivas`. **Falso, y la medición de 12 rondas lo tumbó: la tolerancia que construí no se disparó NI UNA VEZ.** En los 3 fallos de 12 el modelo podía alcanzar `grep` y no lo hizo: eligió `glob`+`read_file`, leyó parte de los 6 ficheros y se rindió. **No es disponibilidad: es ELECCIÓN.** ⚠ **CORRECCIÓN A ESTE RENGLÓN (11ª ventana), y va antes que nada:** aquí escribí *«en la rama nativa **no se oculta nada** — las 24 se anuncian, `grep` incluida»* y *«el modelo tenía `grep` DELANTE»*, y **la premisa era FALSA**. Miré el CABLE DEL RUNTIME (B manda los 24 schemas, `anunciadas_1er_turno=24`) y di por hecho que el proveedor los pasaba tal cual. **No: el proveedor SÍ oculta los schemas de las diferidas** — medido, 24/24 (ver `GAP-TOOL4` y `SEAMS.md · S26`). Lo que el modelo tiene delante son los **NOMBRES**, y pide por nombre lo que quiere expandir (`tool_search_call.arguments = {"paths":[...]}`). La conclusión no se cae —seguía sin ser DISPONIBILIDAD: `grep` era alcanzable con un `paths:["grep"]`— pero cambia de base, y **refuerza `GAP-PROMPT-1` por partida doble**: si lo que gobierna la expansión es NOMBRE + DESCRIPCIÓN, un `bash` descrito en UNA línea (`tools/native/bash.py:14`) compite en desventaja contra el documento que A pone ahí. El split se RETIRÓ del test por codificar una teoría muerta. **DOS HIPÓTESIS MÍAS, LAS DOS REFUTADAS POR MEDICIÓN:** (1) confundidor de atrezo — el fixture decía «clave de sumario» con centinela `SUMARIO-…` y en castellano «clave» ES contraseña; se midió una ronda en que el modelo alcanzó `grep`+`read_file` y respondió «No puedo acceder ni revelar esa clave». Real, se quitó el atrezo… **y el marcador no se movió**; (2) que la culpa fuera la divergencia frente a A —A mantiene `ToolSearchTool` SIEMPRE que haya diferidas (`claude.ts:1163-1164`, literal *«Always include ToolSearchTool»*) y la rama nativa de B lo retira— **experimento sobre fuente, revertido por `sha256`: 6/8 IGUAL**, y en la ronda roja el modelo **llamó a `ToolSearch`** y aun así no pudo. ⇒ la divergencia es real pero **NO es la causa**, y por eso el contrato durable (`PLAN_DEFERRED_LOADING_PRIMITIVA.md` §2-3) **NO se tocó** | `E2g` **partido, no relajado**: la rama SIMULADA conserva el listón ENTERO (es la que espeja a A) y la parte del RUNTIME sigue en gate duro en las dos ramas (24 anuncios · `defer_loading` sobre el conjunto exacto · `ToolSearch` retirado). Sólo se tolera el caso nativo en que el modelo **no tocó ninguna tool RESOLUTIVA** (`grep`/`bash`/`read_file`; `glob` NO cuenta: lista nombres, no lee) — si tocó una y aun así no reportó el centinela, ROJO, que es la mitad que vigila. La rama ejercida se IMPRIME | ⛔ **ABIERTO — y lo digo tras haber escrito «mitigado» antes de tiempo en este mismo renglón.** La corrida de validación (8 rondas con el `D-14` ya puesto) dio **6/8 con las DOS rojas siendo la VIGILANCIA, no la tolerancia**: una por `CancelledError` (`FIND-E2G-2`, dejado en duro a propósito) y otra por «el centinela no llegó» **sin** que la tolerancia se activara — es decir el modelo **sí tocó una resolutiva** y aun así no reportó. ⇒ existe un **SEGUNDO modo de fallo que mi caracterización no cubre**, y la teoría del «subconjunto» explica unas rondas pero no todas. El split está bien construido justamente porque **se negó a absorberlo**; el hallazgo sigue abierto y `TRAMO 1` **no puede declararse cerrado** por esto. **CARRIL DE REMEDIACIÓN, indicado por el usuario y no contemplado por mí:** A está escrito para la familia **Claude** y B corre sobre **gpt-5.4-mini**; una divergencia de CONDUCTA DEL MODELO entre familias no se arregla en el runtime ni se contempla como carencia — se paga **a pico y pala en la capa de system prompt**. Eso cambia la disposición: esto no es «declarado y vigilado» sino **trabajo pendiente con lane conocida**. ⇒ **RECLASIFICADO A `GAP-PROMPT-1`** (fila siguiente), que es donde vive la deuda de verdad |
| `GAP-PROMPT-1` | **NUEVO (10ª ventana) — la deuda REAL detrás de `FIND-E2G-1`, y la única que esta prueba supo encontrar.** A **dirige la elección de tools desde la capa de prompt**: `getSimplePrompt()` en `BashTool/prompt.ts:280-290` emite *«File search: Use Glob (NOT find or ls)»* · *«Content search: Use Grep (NOT grep or rg)»* · *«Read files: Use Read (NOT cat/head/tail)»* · *«Edit files: Use Edit (NOT sed/awk)»* · *«Write files: Use Write»* · *«Communication: Output text directly»*, y además lista los comandos a evitar en Bash — con una rama que RETIRA la guía cuando el build lleva `find`/`grep` embebidos (`:276-277`), o sea que la guía es deliberada y condicional, no decorativa. **B no tiene NADA equivalente en producción**: `grep -rn "NOT find\|NOT cat\|Content search\|File search"` sobre todo `src/agentic_runtime` excluyendo tests → **cero**. **Medido, no razonado:** es exactamente lo que hace que el modelo fuerce bruta con `read_file` en vez de usar `grep`, y cuesta **3 fallos de 12 (25 %)** en `E2g`. **Encuadre del usuario, y es el correcto:** A está escrito para la familia Claude y B corre sobre gpt-5.4-mini; una divergencia de conducta entre familias **no se arregla en el runtime ni se contempla como carencia — se paga a pico y pala en la capa de system prompt**, que es justo la superficie que aquí falta | `E2g` lo deja VER: sin tolerancia, el caso cae ~25 % y el gate se pone rojo. Un split que lo absorbiera estaría tapando la deuda | 🟡 **PAGADO EN EL RUNTIME (16ª ventana), NO CERRADO.** Pagadas las **13 descripciones** que quedaban en one-liner, cada una contra el `prompt()`/`DESCRIPTION` canónico y con la rama correcta elegida a mano (`EnterPlanMode` → EXTERNAL, no Ant, por `:166-170`; `Agent` → no-coordinator con fork apagado). **La cifra heredada de «~25 %» estaba OBSOLETA y se corrigió midiendo**: era pre-`ba2ac47` (que ya había pagado 8 descripciones y **nunca se re-midió**). Baseline real en `b9c8ee3`: **4 rojas / 2 verdes de 6 rondas = 4 incumplimientos en 24 casos (16,7 %)**, y **los 4 en la MISMA celda**, `archivos/nativa`. **Mecanismo confirmado a nivel de CASO, no supuesto:** en los 4 fallos el modelo **sí recuperaba** las tools ocultas (`glob`/`read_file` salen en `elegidas`) — no era disponibilidad ni descubrimiento — y se desviaba a `TaskCreate`/`TaskList`/`TaskOutput`/`TodoWrite`/`Config`/`EnterPlanMode`, las de una línea, cerrando con respuesta **inventada** (`'12345'`), vacía, o «No pude determinarlo todavía». Post-pago: **6/6 verde**, y `grep` pasa a aparecer en la mayoría de rondas (baseline: en 2 de 6 y **jamás** en una roja). ⚠ **Lo que NO se puede afirmar y no se afirma:** el modelo **sigue** invocando `Task*`/`Agent`/`EnterPlanMode` en las rondas verdes — la desviación no desapareció, dejó de ser terminal; y 6/6 no es prueba de cierre para un fenómeno que en baseline era 1 de cada 6 casos. **Segundo atractor MEDIDO y NO pagado por esta vía:** en 2 de los 4 fallos el modelo llamó a `AskUserQuestion` y cerró el turno **vacío** — y esa descripción **ya estaba homologada desde `ba2ac47`**, así que ninguna descripción lo arregla. Es la mitad que el usuario anticipó (*«pero eso quizá no sea suficiente»*) y su carril es el system prompt del integrador, con incitadores **genéricos** — no un vertedero de descripciones por tool, que es divergencia (`L10`) |
| `FIND-TASK-1` | **NUEVO (16ª ventana), destapado al portar `TaskUpdateTool/prompt.ts`.** El `PROMPT` canónico (`:3-84`) es casi todo flujo de estados —`pending → in_progress → completed`, más `deleted`— sobre **8 campos actualizables** (`:35-43`). El `TaskUpdate` de B acepta **uno**: `description`. ⇒ **en B el modelo no tiene forma de marcar una tarea como completada**; el `status` lo mueve sólo el registry por la ejecución en background. Es carencia ESTRUCTURAL (la familia `Task*` de B es registro de trabajo asíncrono, la de A es lista de tareas que el agente gobierna) y **no se paga con una descripción**. Lo que sí se hizo: que la descripción **no mienta** sobre ello — portar el texto de A verbatim habría anunciado `status`/`owner`/`addBlockedBy` que el esquema descarta en silencio, que es la trampa exacta de `FIND-E11-3` | `test_task_update_no_promete_transiciones_de_estado` (INY-77 → roja) + el guard genérico `test_ninguna_descripcion_anuncia_parametros_que_su_esquema_no_acepta` | ⛔ **ABIERTO — carencia estructural, declarada y acotada, no disimulada** |
| `FIND-CFG-2` | **NUEVO (16ª ventana), destapado al portar `ConfigTool/prompt.ts`.** A **enumera** los ajustes configurables en el prompt (`## Configurable settings list`, `:59-66`, generado recorriendo `SUPPORTED_SETTINGS` en `:18-46`, más `generateModelSection()` en `:79-93` con las opciones de modelo). **B no tiene registro de ajustes**: su `execute` acepta cualquier clave y la guarda en `app_state.native["config"]`, así que no hay dominio que enumerar ni que validar. ⇒ el modelo **no puede saber qué claves existen ni qué valores admiten**. Mismo patrón que `FIND-AGENT-LIST-1` y `FIND-SKILL-20` pero un grado peor: allí B tiene el dato y no lo pone en ninguna lista que el modelo vea; aquí **B ni siquiera tiene el dato**. No se inventó una lista en la descripción: sería fabricar un dominio que la tool no valida | `test_config_no_inventa_un_dominio_de_ajustes` (INY-81 → roja) | ⛔ **ABIERTO — CORE-GAP con canónico citado** |
| `GAP-TOOL4` | **NUEVO (11ª ventana), destapado contestando la duda del usuario sobre si el diferido es nativo de gpt-5.4.** A difiere **nativas** por `shouldDefer: true` (`ToolSearchTool/prompt.ts:106`, tras las excepciones explícitas de `:62-105`) y el censo real son **25 directorios** de `claude-code/src/tools`. Cruzado contra el censo de 25 de B: **difieren en A y B no difiere NINGUNA (15)** = `AskUserQuestion`, `Config`, `EnterPlanMode`, `ExitPlanMode`, `EnterWorktree`, `ExitWorktree`, `TaskCreate`, `TaskGet`, `TaskList`, `TaskOutput`, `TaskStop`, `TaskUpdate`, `TodoWrite`, `WebFetch`, `WebSearch`; **no difieren en A (10)** = `Agent`, `bash`, `glob`, `grep`, `read_file`, `write_file`, `Edit`, `Sleep`, `clone_repository`, `ToolSearch`. **El reparto de A no es arbitrario: lo que NO difiere es exactamente el núcleo de exploración de ficheros que el modelo necesita en el turno 1** — es la misma tesis que `GAP-PROMPT-1`, vista desde el otro lado. **CORRECCIÓN DE TAMAÑO:** `SEAMS.md · S26` lo tenía anotado como «`WebFetch`/`WebSearch`», corto **por un factor de 7**, porque el conteo filtraba `--include=*.ts` y perdía los `.tsx` (`AskUserQuestionTool.tsx:113`, `TaskOutputTool.tsx:148`). **NO es `GAP-TOOL3`**: aquella es la *precedencia* de `isDeferredTool`, e implementarla no pone ni una sola nativa a diferir | `E2g` no lo ve: **fabrica** su sujeto nativo por monkeypatch sobre las clases de producción (`test_tramo1_gate.py:2357-2359`), cosa que el propio test declara en su cabecera (`:1753`). Sin esa fabricación, la rama nativa del gate no tendría nada que diferir | ⛔ **ABIERTO — CORE-GAP con canónico citado y tamaño medido** |
| `FIND-E2G-2` | diferido nombrado | — | ⛔ |
| `FIND-E2G-3` | **NUEVO (10ª ventana), destapado buscando el consumidor de la rama nativa.** `DeferredToolStrategy.owns_search_dispatch()` es miembro del contrato durable (`PLAN_DEFERRED_LOADING_PRIMITIVA.md` §2-3) y **NO TIENE UN SOLO CONSUMIDOR EN PRODUCCIÓN**: `grep -rn owns_search_dispatch` en TODO el repo devuelve 3 definiciones y **4 aserciones de test que sólo comprueban su valor de retorno** (`test_deferred_strategy.py:101,129`, `test_tools_infra_homologation.py:173,184`). **PREEXISTENTE, verificado por `git log -S`, no introducido en esta ventana**: método y aserciones entran juntos en `0b7de34` («primitiva DeferredToolStrategy con selección por capability») + `cce603f`. **CORRECCIÓN A MI PROPIO ENUNCIADO, hecha al mirar el contexto:** dije «4 tests acreditando una costura que no gobierna nada» y es exagerado — esos tests **NO son huecos**, aseveran conducta real (schemas, `defer_loading`, anuncios) y sólo REMATAN con esta línea. Lo decorativo es **la línea, no el test**, y el hallazgo es más estrecho: un miembro del contrato durable **sin consumidor en producción**, de modo que `L09` aplica al MÉTODO, no a la suite que lo roza. Quien decide de verdad si el modelo puede buscar es una sola cosa: que `ToolSearch` entre o no en `tool_schemas` (`deferred_strategy.py:87-88`) | **RESUELTO POR `D-08` Y PAGADO (11ª ventana): RETIRADO DEL CONTRATO Y DEL CÓDIGO.** Dos cortes del usuario, ambos correctos. El primero, *«¿por qué tantas vueltas si bastaría con mirar el canónico?»* — `D-08` literal, yo llevaba dos turnos deliberando sin abrir A. El segundo, *«no tiene sentido que digas que sólo aparece en… si usas `sed` y `grep`»* — **invalidó la acreditación del veredicto**, que estaba escrito sobre `grep` + ventanas `sed` (`D-05`: grep localiza, no dictamina). Acreditado ya con **4 ficheros leídos 1→EOF**: `utils/toolSearch.ts` (756) · `toolExecution.ts` (1745) · `ToolSearchTool.ts` (471) · `Tool.ts` (792). **La lectura corrigió el enunciado anterior por partida doble:** (a) el interruptor de A **NO es «la presencia de la tool»** —eso decía este renglón— sino `isToolSearchEnabled` (`utils/toolSearch.ts:385-473`), compuesto de CUATRO condiciones (`modelSupportsToolReference` ∧ `isToolSearchToolAvailable` ∧ `getToolSearchMode()` ∧ umbral `tst-auto`); la presencia es una de cuatro. (b) **la razón de fondo es estructural y mejor**: el `ToolSearch` de A es una tool **client-side y punto** (`ToolSearchTool.ts:328-434` filtra, puntúa y devuelve `tool_reference` EN LOCAL) ⇒ **A tiene UNA SOLA RAMA**, y «¿quién posee el despacho?» no es una pregunta que A pueda formularse. **No le falta a A el predicado: le falta el DILEMA.** B sí lo tiene y es genuino (medido: el proveedor Responses resuelve el search server-side), pero el predicado **no puede gobernar nada** porque es una segunda codificación de un hecho que `tool_schemas` ya expresa (la rama nativa retira `ToolSearch` de los schemas). Confirmado además que en las 1745 líneas de `toolExecution.ts` el único toque de diferido es `buildSchemaNotSentHint` (`:578-597`), y sólo para anexar texto a un error Zod. **CORRECCIÓN A MI PROPIA PROPUESTA:** propuse *cablearlo como guarda* contra una llamada alucinada a `ToolSearch` — era **inventarme una divergencia en vez de leer A**, y A hace lo CONTRARIO: es deliberadamente permisivo (`ToolSearchTool.ts:199-204`, `:374-375`, *«a harmless no-op that lets the model proceed without retry churn»*). **PAGO:** retiradas 3 definiciones + la del `Protocol` y las 4 aserciones de remate; la conducta sigue aserida por `prepare_turn` en los mismos tests, así que no se retira cobertura. `grep` residual → CERO. `ruff` 504 · `mypy` 138/54 · suite sin regresión. **VEREDICTO FUNCIONAL (11ª ventana, a petición expresa del usuario: *«no sólo resuelto y pagado, sino funcionalmente correcto»*):** la retirada sólo es correcta si el despacho REAL funciona en las DOS ramas, y el riesgo vive en la NATIVA (el runtime nunca descubre nada). Lo que había NO lo probaba: `test_deferred_strategy.py:132-156` asevera la FORMA de los schemas (`H-L4`). **Dos tests nuevos que miden EJECUCIÓN:** `test_native_branch_executes_deferred_tool_never_discovered` (rama nativa, `discovered_tool_names` vacío y `drew:` real en `ctx.messages`) y `test_simulated_branch_full_cycle_hidden_search_announced_executed` (ciclo entero en una corrida: oculta → ToolSearch con schema completo → anunciada → invocada → ejecutada). **Acreditados por efecto:** INY-45 (puerta de descubrimiento en `dispatcher.py`) → 2 rojas; INY-46 (la descubierta sigue oculta en simulada) → 3 rojas. **El dato decisivo: bajo INY-45 el ciclo simulado siguió VERDE** — el agujero de la rama nativa sólo lo caza el test nuevo. Revertido desde copia propia con `sha256 -c` OK; 14 passed; `ruff` 504 | ✅ **RESUELTO, PAGADO Y FUNCIONALMENTE ACREDITADO** |
| `FIND-C6-2` | **PAGADO (10ª ventana), y el contraste PARTIÓ el hallazgo en dos.** (a) Que `asyncio.wait_for` no pueda preemptar una corrutina que no cede **NO es deuda de homologación**: A tiene la misma propiedad (un solo event loop) y de hecho **ni siquiera tiene** cap genérico por tool — su único `timeout` es el de INPUT de `Bash` (`toolExecution.ts:1148-1149`), donde hay un subproceso genuinamente preemptable. (b) Lo que SÍ era deuda: `web_fetch.py:53` y `web_search.py:111` hacían `urlopen` **síncrono dentro de su `async def`**, o sea *eran* esa corrutina que no cede, hasta 20 s — congelando stream, subagentes y notificaciones, y dejando sin efecto el cap. A no lo tiene porque su E/S de red es asíncrona de raíz y honra `signal` + `FETCH_TIMEOUT_MS` (`WebFetchTool/utils.ts:262-282`). **Arreglo: `asyncio.to_thread`** en las dos, con la descarga extraída a una función NO-corrutina para que reintroducir el bloqueo se vea en el diff. Repone la verdad de `11-cap-mcp.md:656-658` | `test_tool_dispatcher.py`: `test_una_corrutina_que_no_cede_no_se_puede_acotar_y_esto_esta_medido` (el límite estructural, aseverado con su signo + control positivo con tool que cede) · `..._las_tools_de_red_no_bloquean_el_event_loop_y_el_cap_las_acota` (servidor HTTP **real** lento + LATIDO concurrente) · `test_web_search_tampoco_bloquea_el_event_loop` | ✅ pagado — INY-60..61 → 2 rojas / 0 falsos negativos. **Y su `xfail` anterior ACREDITABA EN FALSO (`H-L4`)**: reventaba en `ToolUseContext(...)` con `ValidationError: session_id Field required`, nunca llegó a `dispatch` ni midió timeout alguno, y el `strict` tampoco habría enrojecido al pagarse el gap. **Declarado y NO pagado**: cortar la petición EN VUELO por `ctx.stop` — exige un signal esperable, y `AbortController` es no-esperable **por diseño documentado** (`abort.py:47-49`); es cambio de `contracts/abort.py`, fuera de `tools/` |
| `FIND-CFG-1` | **NUEVO (9ª ventana), resuelto contra el canónico por `D-08` antes de tocar nada.** La rama GET de `Config` **escribe**: `ctx.app_state.native.setdefault("config", {})` corre antes de bifurcar (`config.py:44`), así que una simple lectura deja la clave creada en el estado de la sesión. A tiene el GET como lectura pura —`call()` sólo llama a `getValue()`, que lee de `getGlobalConfig()`/`getInitialSettings()` (`ConfigTool.ts:136-144`)— **y lo DECLARA**: `isReadOnly(input) { return input.value === undefined }` (`:90-92`). Medido: el GET deja `{'config': {}}`. **PAGADO (10ª ventana)**, y el arreglo es de UNA línea porque el contraste ya había localizado la causa exacta: `.setdefault(_CONFIG_KEY, {})` → `.get(_CONFIG_KEY) or {}`. La rama SET no cambia: sigue escribiendo **sólo** por su `context_modifier`, que es el único punto donde el runtime admite mutación de contexto desde una tool — igual que en A, donde `isReadOnly` distingue las dos ramas | `test_tools_native_homologation.py::test_config_get_does_not_write_state` (xfail retirado; incluye control positivo de que el SET sólo actúa por su `context_modifier`) | ✅ pagado — INY-57..59 → 3 rojas / 0 falsos negativos (GET con `setdefault` · SET mutando fuera del modifier · modifier sin efecto) |
| `FIND-LOOP-1` | **PAGADO (10ª ventana).** El loop acepta que un `context_modifier` devuelva OTRO ctx (`ctx = modifier(ctx) or ctx`), pero `ctx.tool_pool` es estado DEL TURNO: un modifier que forkaba sin arrastrarlo dejaba al dispatcher con el pool vacío y **las tool calls restantes del mismo turno fallaban en silencio** («no encontrado en el tool pool»), indistinguibles de un resultado de tool normal. **Contraste (`D-08`, los 4 sitios de A leídos):** `toolOrchestration.ts:42-60` (concurrente) · `:140-141` (serie) · `StreamingToolExecutor.ts:391-394` · `toolExecution.ts:1400/1467` aplican todos `currentContext = modifier(currentContext)` — **modelo idéntico al de B**. La divergencia no está en cómo se aplica sino en que el único modifier real de A deriva por **spread** (`SkillTool.ts:773-800`), lo que hace la pérdida de campos **estructuralmente imposible**; en B el ctx es un modelo con `default_factory` en casi todo, así que el fork parcial es válido **y mudo** | `test_agent_loop.py::test_FIND_LOOP_1_un_fork_ingenuo_del_ctx_no_mata_las_tool_calls_restantes` + `…_deja_de_ser_silencioso` (ambos nacieron **rojos** con el arreglo fuera) | ✅ pagado — `_adoptar_ctx_modificado` repone `tool_pool` (único campo del ctx que el loop escribe: `agent_loop.py:292`, verificado por grep exhaustivo de asignaciones) y **avisa** de los demás cables perdidos (`stop`/`event_queue`/`storage`/`fs`/`exec_env`), que el loop no posee y por tanto no inventa |
| `FIND-READ-1` | **PAGADO (10ª ventana).** `read_file.py:38` hacía `limit = input.get("limit", len(lines))`: sin `limit` explícito el fichero entero entraba al contexto. A aplica `maxSizeBytes` 256 KB sobre el tamaño TOTAL y **lanza** en vez de truncar — probaron truncar (#21841) y lo revirtieron porque el throw cuesta ~100 B y truncar costaba 25 K tokens (`limits.ts:1-14`). **El contraste corrigió mi hallazgo:** el cap **sólo rige la lectura sin `limit`** (`FileReadTool.ts:1023` pasa `limit === undefined ? maxSizeBytes : undefined`), porque pedir un rango acotado es justo lo que el error recomienda; sin ese matiz el arreglo habría sido MÁS SEVERO que el canónico | `test_read_file_refuses_a_file_over_the_canonical_size_cap` — ahora asevera también que el mensaje nombra `offset`/`limit` y que un `limit` explícito EXIME del cap | ✅ pagado. **Declarado y NO pagado**: el segundo tope de A, `maxTokens` 25 000, exige un tokenizador del proveedor — no se finge con una heurística de bytes |
| `FIND-READ-2` | **PAGADO (10ª ventana).** (a) `offset` era **0-indexado** en B y es **1-indexado** en A (`FileReadTool.ts:497`) ⇒ off-by-one silencioso en la tool con la que el modelo cita código; (b) B emitía las líneas desnudas, A devuelve `addLineNumbers` (`:726`, formato ancho 6 + `→`). **El contraste añadió una regla que yo no tenía:** en A `offset` 0 y 1 nombran la MISMA primera línea (`:1020`, `offset === 0 ? 0 : offset - 1`), así que un llamante con la grafía vieja no se desplaza | `test_read_file_offset_is_one_indexed_and_output_is_numbered` **reforzado**: la versión anterior aseveraba `"1" in primera_línea`, que habría pasado con la salida desnuda si el texto contenía un 1 — acreditaba en falso (`H-L4`). Ahora compara el formato exacto y que una lectura desplazada abre con el número de línea REAL | ✅ pagado. Arrastró un cuarto xfail que no estaba en el pool, `FIND-NATIVE-READ/A3b` (numeración), que apareció solo como XPASS estricto |
| `FIND-GLOB-1` | **PAGADO (10ª ventana).** B ordenaba **alfabéticamente** (`glob_tool.py:40`); A ordena por **mtime** (`utils/glob.ts:98-104`, `--sort=modified`) y recorta DESPUÉS (`:127`), y `GlobTool.ts:154-170` **no reordena**, luego ese es el orden que ve el modelo. **Con un cap, el orden es SELECCIÓN**: decide cuáles 100 de 130 llegan al contexto. Dirección verificada **empíricamente contra `rg` real**, no sólo por el comentario: `--sort=modified` es ASCENDENTE (oldest first) | `test_glob_orders_by_mtime_not_alphabetically` — asevera la **secuencia completa**, no sólo el primero, y `zzz` está sembrado en la posición alfabética contraria para que los dos órdenes sean inversos | ✅ pagado |
| `FIND-GLOB-2` | **NUEVO Y PAGADO (10ª ventana), destapado leyendo el canónico para pagar `FIND-GLOB-1`.** A pasa `--files` a ripgrep (`utils/glob.ts:98`): lista **ficheros**. B hacía `base.glob(pattern)` a secas, que casa igual un **directorio** cuyo nombre encaje en el patrón. **Medido antes de levantarlo**: un dir `carpeta.txt` salía como resultado de `*.txt`, y el modelo recibe una ruta que no puede leer | `test_glob_lists_files_only_not_directories` | ✅ pagado |
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

> **10ª ventana:** el contraste que este párrafo dejaba pendiente YA está hecho y documentado en las
> filas de hallazgos, así que los cuatro (`FIND-READ-1`, `FIND-READ-2`, `FIND-GLOB-1`, `FIND-CFG-1`)
> están **pagados** y sus `xfail` retirados. Dejarlos declarados una segunda vez habría sido
> `declaración-como-pago`.

### Corrección de inventario (2026-08-02)

Declaré como hueco que «`ends_turn` se asevera como flag y nunca que el loop cierre el turno
por ese flag». **Falso como fue enunciado**: `test_agent_loop.py:234` y
`test_loop_homologation.py:261` ya aseveraban el efecto de loop. El hueco real era más fino y
es el que se pagó: **ninguno de los dos tenía control positivo** — ambos medían «el modelo se
llamó 1 vez», luego un loop roto que cortara SIEMPRE tras ejecutar tools los dejaba verdes; la
frase «sin ends_turn se re-llamaría (2)» vivía en un **comentario**, no en una aserción.

### 11ª ventana (2026-08-03) — mecanismos de tools: ToolSearch, WebFetch, search hint

| Renglón | Estado |
|---|---|
| `GAP-TOOLSEARCH-1` — lenguaje de consulta de ToolSearch | ✅ **PAGADO** — nombre exacto, `mcp__`, `+requerido`, scoring 12/10·6/5·+4 hint·+2 desc, `select:` multi con éxito parcial, dedupe y caída al set completo. `FIND-TOOL6/E6` XPASSó y su `xfail` se retiró. 9 tests nuevos |
| `GAP-WEBFETCH-1` — mecanismo de WebFetch | ✅ **PAGADO** salvo el paso de modelo secundario: validación de URL, subida incondicional a `https:`, política de redirects (`MAX_REDIRECTS=10` + host permitido), markdown sólo para `text/html`, truncado a 100 000, `prompt` requerido. 9 tests nuevos |
| `GAP-WEBFETCH-2` — `applyPromptToMarkdown`→`queryHaiku` | ⚠ **CARENCIA DECLARADA Y RAZONADA** — fija un modelo, y elegir modelo es política del integrador (Filosofía B). Exige costura inyectada, no se simula |
| search hint (`Tool.ts:373-378`) | ✅ **CABLEADO** — scoring por `getattr` (sin tocar el contrato T1), atributo en las 8 nativas con contraparte, y `_meta` del server con colapso de espacios. Clave `_meta` **neutra de vendor**; el dialecto namespaced lo aporta el integrador. INY-57..61 → 5 rojas |
| `FIND-E7F-2` **NUEVO** — el barrido de costura medía UNA API | ✅ **PAGADO** — pinchaba sólo `urlopen`; al pasar WebFetch a `build_opener().open()` el barrido dejó de ver un escape que **seguía ahí** y lo dio por pagado. Ahora pincha `socket.socket.connect`: capacidad, no API |
| `E10`/`WebFetch` | ✅ **REFORZADO** — servidor local a **TLS real** (la tool sube `http:`→`https:` sola, así que se mide eso) y aserción de que la salida es markdown, no html crudo. Sin desactivar verificación en ningún punto |

**Falsos negativos propios cazados por inyección VERDE** (la inyección que pasa **es** el hallazgo):
**INY-49**, el test del nombre desnudo usaba una tool ya diferida y nunca ejercitaba la caída al set
completo; **INY-56**, el test de markdown llamaba al conversor directo y no probaba que `execute` lo
use — `L09` en estado puro. Los dos pagados con test E2E nuevo y re-inyección roja.

**Neutralidad de vendor** (instrucción del usuario, 2026-08-03): las **citas** del canónico en
comentarios se quedan —son el registro de homologación—, pero los strings, claves, rutas y defaults
**propios** del runtime van neutros. Corregidos `config.py` (search hint), `models/caller.py:120`
(id de modelo en el ejemplo) y la clave `_meta` del hint. `.claude/`/`CLAUDE.md` ya estaban limpios en
producción. **Sin tocar y en la mesa del usuario**: `McpScope.CLAUDEAI` es procedencia de config que
llega del integrador y está homologada con tests — renombrarla rompe compatibilidad de wire.
