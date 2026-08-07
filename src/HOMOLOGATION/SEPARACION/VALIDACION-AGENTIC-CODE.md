# VALIDACIÓN POR CONSUMIDOR REAL — `agentic_code` sobre `agentic_runtime`

> **Qué es esto.** El método de trabajo decidido por el usuario el **2026-08-06** (`DECISIONES.md · D-15`)
> y el **listado de problemas confirmados** que produjo su primera aplicación. Este fichero es de ESTADO,
> no de log (`D-09`): una viñeta es una línea, y lo que se paga se marca aquí mismo.

---

## 1 · El método

`agentic_runtime` es una librería sin usuarios. Una suite propia sólo puede probar lo que su autor
**pensó** probar, y el barrido EOF del canónico (10ª ventana) demostró el patrón de fallo dominante:
**el runtime tiene el dato cargado y no lo pone en ninguna lista que el modelo vea**. Ninguna de esas
omisiones la vio un test verde; las vio un consumidor.

El ciclo, en cuatro pasos:

1. **Ejercitar** una capacidad de `agentic_runtime` **desde `agentic_code`**, como integrador real.
2. **Leer qué está implementado en `agentic_code`** — la asimetría entre lo que el integrador necesita
   escribir y lo que el runtime le da es, ella misma, la medida del hueco.
3. **Conforme se activan más capacidades en `agentic_runtime`, implementar más capacidades en
   `agentic_code`** — los dos repos avanzan acoplados, y el integrador es la puerta.
4. **Validar la operación contra los `.jsonl`** de sesión que `agentic_code` deja: la traza real de
   mensajes, tool calls, anuncios y resultados. Es evidencia de EJECUCIÓN, no de lectura.

**Por qué los `.jsonl` mandan.** Una aserción sobre firma acredita en falso (`H-L4`); un `.jsonl` es
lo que el modelo REALMENTE recibió y lo que REALMENTE devolvió. Contra él se comprueba lo que ningún
test unitario alcanza: si el anuncio de diferidas converge, si el listado de skills llegó, si el
`system-reminder` se repite turno tras turno, si una tool anunciada era invocable.

**Lo que este método NO es.** No sustituye al contraste contra el canónico. Sigue vigente el encuadre
del usuario: *ante conducta divergente, contraste contra canónico > «arreglar» lo que no sabes si es
genuino* (`D-08`). `agentic_code` DETECTA; el canónico DICTA.

---

## 2 · Listado de problemas confirmados (orden de evidencia del usuario)

Producido por el usuario ejercitando `agentic_code` contra el runtime. **Este es el orden de ataque.**

| # | Problema | Clase | Estado |
|---|---|---|---|
| 1 | `run_shell` sin `cwd` | defecto de **CONTRATO** | ✅ **PAGADO** (11ª ventana) — 6 inyecciones rojas, `preventCwdChanges` incluido |
| 2 | Fallback de `BashTool` (`TRAMO-1.md:183`) | conducta | ⛔ abierto |
| 3 | Remediación de `FIND-TS-1` / `TS-3` / `TS-4` | deuda ya declarada | ⛔ abierto |
| 4 | `GAP-TOOL4` | deuda ya declarada | ⛔ abierto |
| 5 | `GAP-PROMPT-1` — 15 de 25 descripciones sin homologar | superficie del modelo | ⛔ abierto |
| 6 | `FIND-E2G-2` | deuda ya declarada | ⛔ abierto |
| 7 | Abort de `WebFetch` no esperable | conducta | ⛔ abierto |
| 8 | `RuntimeFactory._modes` singleton (`factory.py:152`) | estructural | ⛔ abierto |
| 9 | Motor de permisos parcial | capacidad | ⛔ abierto |
| 10 | Stream público insuficiente para reproducir la observabilidad canónica | **observabilidad** | ✅ **PAGADO** (12ª ventana) junto con `FIND-STREAM-1` — 8 inyecciones rojas |

**Detalle del #5** — las 15 descripciones que no están homologadas contra el canónico:
`Agent` (16.6 KB en A), `TodoWrite` (9.5 KB), `EnterPlanMode` (7.7 KB), `Config`, `ExitPlanMode`,
los 6 `Task*`, los 2 `Worktree*`, `clone_repository`.

**Detalle del #1 — remediación desarrollada (`L05`, seis campos).** Medido en consumidor: con el
workspace en `/tmp/repro-cwd-…/workspace`, `bash pwd` devolvió `/home/noheroes/python/agentic_code`
(el cwd del PROCESO) con `is_error=False`. Es `FIND-C6-1` una capa más arriba: se autoriza una cosa
—`read_file`/`write_file` confinados, prompt declarando el workspace «autoritativo»— y se ejecuta en
otra. **Corrección al corpus (`D-08`, leído `Shell.ts` 1→EOF):** `FIND-TOOL8` / `09·F2:155` /
`10·B2:112` afirman que A mantiene *un shell vivo*; A **spawnea un shell nuevo por comando**
(`Shell.ts:179`). El env persiste por el snapshot sourceado y el cwd por la relectura de un fichero
temporal — no por un proceso vivo.

| Campo | Contenido |
|---|---|
| **Comportamiento** | El comando corre en el cwd que el integrador declaró, no en el del proceso host; un `cd` persiste **entre comandos del turno** vía relectura de `pwd -P` (A: `bashProvider.ts:186`, `Shell.ts:385-421`), y si el cwd desapareció se recupera al workspace o se falla con mensaje (A: `Shell.ts:220-238`). |
| **Seam** | `ToolExecEnvironment` (`ctx.exec_env`) + un cable nuevo `ctx.cwd`. **No** se compone estado en el runtime: `ctx.cwd` es cable, y la persistencia ENTRE TURNOS es del integrador por `root_context_modifier` (`_open_session` da `Session` fresca por turno, `S20`). |
| **Firma** | `run_shell(command, *, cwd: str \| None = None, timeout: float)` — simetría con `run_argv`; `ShellResult` gana `cwd: str \| None = None` (`None` = el backend no lo rastrea). |
| **Cableado** | `BashTool.execute` resuelve `ctx.cwd or str(ctx.fs.write_root)`, aplica la recuperación de A, pasa `cwd=` y **escribe de vuelta** `ShellResult.cwd` en `ctx.cwd` (el dispatcher entrega el ctx VIVO, `dispatcher.py:79`). `agentic_code` cablea el workspace en `composition.py`. |
| **Orden** | Contrato (`exec_env`) → cable (`tool_use`) → tool (`bash`) → integrador (`composition`) → detector. |
| **Prueba** | Detector en `agentic_code` que nace ROJO: `bash pwd` == workspace declarado, con el proceso corriendo FUERA de él. Más el par host/sandbox en la suite del runtime. |
| **Acreditación** | 6 inyecciones, 6 rojas y cada una donde tocaba: `INY-45` `BashTool` no pasa `cwd` (2 rojas) · `INY-46` el spawn ignora `cwd=` (2) · `INY-47` sin escritura de vuelta (1, sólo la del `cd`) · `INY-48` el integrador no transporta (1, sólo la de entre-turnos) · `INY-49` sin `eval` (1, sólo la de precedencia) · `INY-50` el escape `!` no publica su `cd` (1). Además el xfail `test_bash_persistent_shell` se puso ROJO por **XPASS(strict)** al pagar la deuda —la señal funcionando— y se reescribió a conducta. |
| **Efecto lateral pagado, no declarado** | Hacer persistir el `cwd` activó `preventCwdChanges` (B11): A gatea la escritura para no-main-thread, y sin esa guarda el arreglo habría abierto un agujero que el canónico cierra. Implementado (`ctx.is_subagent`) y con test propio. |
| **Carencia declarada** | `BwrapExecEnvironment` honra el `cwd` pero **no lo rastrea** (`ShellResult.cwd=None`): el fichero temporal del host no existe dentro del sandbox y el `pwd` de dentro es un path INTERNO (`/workspace/…`) que no es asignable a `ctx.cwd`. Bajo bwrap un `cd` no persiste entre comandos. Declarado, no oculto. |

**Detalle del #10 + `FIND-STREAM-1` — remediación desarrollada (`L05`, seis campos).** Se pagan
JUNTOS: son el mismo seam, el stream público. Medido en consumidor sobre `.jsonl` real: los 5 campos
de identidad llegan vacíos en **`ToolCallEvent`, `DoneEvent` y `ToolResultEvent`** — universal, no
sólo el último; y `agentic_code` se ve obligado a fabricarse `seq`/`timestamp`/`session_id` propios
(`capture.py:116-124`) más un segundo contador `_source_sequence` (`:39`, `:75`), que es la asimetría
del paso 2 del método hecha código. Agravante de rótulo: `contracts/events.py:41-43` afirma «el
runtime los puebla y no los lee» — la primera mitad es falsa.

**Corrección al enunciado del #10 (`D-08`, leído el canónico 1→EOF).** El enunciado previo pedía
«emitir el `TurnToolPlan`». El canónico **no tiene evento de plan**: `query.ts` rinde los MISMOS
`Message` que se persisten, y cada anuncio (`deferred_tools_delta`, `skill_listing`,
`agent_listing_delta`, memoria, recall) es un `AttachmentMessage` **yieldado al stream público**
(`:1588`, `:1610`, `:1624`), con un marcador de turno `{type:'stream_request_start'}` por iteración
(`:337`). La propiedad canónica es **el stream público lleva lo mismo que la historia**, no «hay un
canal aparte para el plan». Se implementa esa propiedad, no la formulación vieja.

| Campo | Contenido |
|---|---|
| **Comportamiento** | (a) Todo evento sale del runtime con sus 5 campos poblados; (b) todo mensaje que el loop añade a `ctx.messages` viaja también por el stream; (c) el turno tiene frontera observable y el plan de tools viaja como DATO (nombres anunciados / diferidos), no como texto a re-parsear — `FIND-DEFER-1` demuestra que re-parsear el texto rendido es la enfermedad, no el remedio. |
| **Seam** | **Sumidero único**, espejo de `insertMessageChain`: `AgentLoop._emit` (`agent_loop.py:246-248`) es el choke point por el que pasa TODO evento sin excepción. Sella ahí, no en cada emisor — A no le pide a ninguna factoría que recuerde los campos de sesión. |
| **Firma** | `Event` no cambia (los 5 campos ya existen). Añade `contracts/events.py`: `MessageEvent(role, content)` y `TurnStartEvent(turn, tool_names, deferred_names)`. Nombres genéricos de framework, no conveniencias del integrador. |
| **Cableado** | `_emit` reemplaza por `dataclasses.replace(...)` **incondicionalmente** (`ts`, `seq` del contador del sumidero, y `task_id`/`agent_id`/`session_id` de `ctx`). El re-sellado incondicional es dictado, no gusto: `sessionStorage.ts:1049-1056` documenta que sellar «sólo si falta» reintroduce el bug de identidad cruzada. El loop emite `TurnStartEvent` en `:352` y un `MessageEvent` por cada `ctx.messages.append` (anuncios `:354`, asistente `:463`, tool `:501`, recall). |
| **Orden** | contrato (`events.py`) → sumidero (`_emit`) → emisiones del loop → integrador (`capture.py` deja de fabricar identidad) → detector. |
| **Prueba** | Detector en `agentic_code` que nace ROJO: en un `.jsonl` real, `seq` estrictamente creciente, `ts` no nulo, `session_id` == el de la sesión, y el anuncio de diferidas presente como evento (no sólo dentro del prompt). Más el par en la suite del runtime. |
| **Divergencia declarada, no deuda (`L10`)** | A **no tiene `seq`** en 5105 L: ordena por lista enlazada `parentUuid` con desempate `timestamp` ISO. B declara `seq` y es primitiva legítima de un bus de eventos; lo que se paga no es la forma sino la propiedad —que el consumidor ordene y atribuya sin contabilidad propia—. Segunda divergencia declarada: A sella `timestamp` en la FÁBRICA y B lo sella en el SUMIDERO, porque B no tiene capa de factorías y exigirlo a cada provider es justo lo que A evita. |
| **Acreditación** | **8 inyecciones, 8 rojas, 0 falsos positivos** (`INY-51..58`), cada una donde tocaba: `51` sellado condicional en vez de incondicional (1 roja — la del re-sellado, la única que puede verlo) · `52` sin `ts` (2 rt + 1 ac) · `53` sin incrementar `seq` (2 rt + 1 ac) · `54` `_append` que añade a la historia y no emite (8 rt + 2 ac — la más ancha, que es lo esperable: es la propiedad central) · `55` sin `TurnStartEvent` (4 rt + 2 ac) · `56` `deferred_names=()` (1 rt) · `57` anuncios por `ctx.messages.append` crudo (1 rt) · `58` el integrador vuelve a fabricarse el contador (2 ac). Revertido desde copia propia verificada por `sha256` entre inyección e inyección; jamás `git checkout`. |
| **Cable nuevo** | `ToolUseContext.task_id` (`""` por defecto), poblado en `_run_loop` con el handle que acuña el registry. Es TRANSPORTE, no composición (`D-11`): el loop lo copia, no lo deriva. `extra="forbid"` hace que una grafía vieja reviente en vez de descartarse en silencio. |
| **Lo que NO emite `MessageEvent`, dicho** | Los dos `ctx.messages.append` de resultado de tool (dispatch real y denegación del gate). No es un hueco: ya viajan como `ToolResultEvent`, que además lleva `call_id` e `is_error`. Duplicarlos sería ruido. Está aseverado en el orden total exacto del canal, no narrado. |

---

## 3 · Cosecha del barrido EOF (10ª ventana) — entra en la misma cola

Hallazgos del barrido del canónico sobre las LISTAS de tools (nativas, MCP diferidas, skills). No los
produjo `agentic_code`, pero son de la misma familia y se atacan con el mismo instrumento.

| ID | Hallazgo | Estado |
|---|---|---|
| `FIND-DEFER-1` | El delta de diferidas se reconstruye RE-PARSEANDO el texto rendido; un `\n` en el nombre anuncia una tool inexistente, pierde la real y **el delta no converge nunca** | ⛔ abierto |
| `FIND-DEFER-2` | Sin cap de descripción de terceros (60 000 ch medidos vs `MAX_MCP_DESCRIPTION_LENGTH = 2048` de A) | ⛔ abierto |
| `FIND-AGENT-LIST-1` | Al modelo no le llega **ningún listado de subagentes**; `AgentDefinition.description` es campo muerto y `AgentDefinitionResolver` **no tiene enumeración** | ⛔ abierto |
| `FIND-SKILL9/17` | Reclasificado: al modelo **no le llega ningún listado de skills**, por ninguna de las **dos** vías de A (description de `Skill` + attachment `skill_listing` incremental) | ⛔ abierto — **primero de la pata de skills** |
| `FIND-SKILL-20` | El frontmatter PISA la identidad de la skill (A: siempre el nombre del directorio) | ⛔ abierto |
| `FIND-SKILL-21` | Sin dimensión de fuente ni precedencia; `last-wins` donde A tiene `first-wins` por identidad de fichero real | ⛔ abierto |
| `FIND-STREAM-1` | **Los 5 campos de identidad del evento llegan VACÍOS al `.jsonl`**: `task_id: ""`, `agent_id: ""`, `session_id: ""`, `seq: 0`, `ts: 0.0`. **Ampliado en la 12ª ventana: es UNIVERSAL** (medido en `ToolCallEvent`, `DoneEvent` y `ToolResultEvent`), no sólo el último; ningún sitio de producción de `src/` poblaba identidad. Sin `seq`/`ts` no se ordena ni se fecha una traza, y sin `task_id`/`agent_id` no se separa agente de subagente. Se pagó con el **#10** (mismo seam) | ✅ **PAGADO** (12ª ventana) |
| `FIND-POOL-1` | Sin predicado de enablement por tool (`Tool.isEnabled()`); el integrador ha de negar POR NOMBRE, mezclando política con disponibilidad | ⛔ abierto |

**Dos `H-L4` a saldar al pagar lo anterior** — suites que acreditan la divergencia en vez de
detectarla: `test_deferred_delta.py:43-47` (consagra el reparseo de texto como mecanismo homologado) y
`test_deferred_delta.py` entero (190 L, **cero casos adversariales**). Se **reescriben**, no se amplían.

**Orden 2 arrastrado** (hallazgos de ventanas previas, sin tocar): `FIND-READ-1`, `FIND-READ-2`,
`FIND-GLOB-1`, `FIND-CFG-1`, `FIND-LOOP-1`, `FIND-E11-1`, `FIND-C10-1`, `FIND-SEQ-1`, `FIND-E2G-1`,
`FIND-E2G-2`, `FIND-C6-2`.

---

## 4 · Bajo la línea, sin tocar

`A-CIERRE` P4″ 12–18 · ledger 39 abiertos · `O-18`/`R-1b` · `R-6`/`O-16` · `ID-4`/`K3` · `H-3`.
Diferidos nombrados: `SERPER_API_KEY` del entorno vs `ctx.git_credentials` · `ForkSnapshot` no
transporta el confinamiento · `run_argv` no traduce paths DENTRO del argv.
