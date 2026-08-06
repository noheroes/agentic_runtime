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
| 10 | Stream público insuficiente para reproducir la observabilidad canónica | **observabilidad** | ⛔ abierto |

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

**Detalle del #10** — es el que engancha con el barrido: el runtime **no emite el plan de tools del
turno**. `TurnToolPlan` (`deferred_strategy.py:34-39`) es interno, no viaja al stream público, y lo
único observable es `app_state.capabilities['discovered_tools']`. Un integrador **no puede
reconstruir** cuántas tools se anunciaron, cuáles iban diferidas ni cuántas quedaron fuera por
presupuesto — todo lo cual A sí contabiliza y expone (`analyzeContext.ts`). Sin esto, el paso 4 del
método (validar por `.jsonl`) es ciego para media superficie de tools: **conviene pagarlo temprano
aunque esté el último de la lista**, porque es el instrumento de medida del propio método.

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
| `FIND-STREAM-1` | **Los 5 campos de identidad del evento llegan VACÍOS al `.jsonl`**: `task_id: ""`, `agent_id: ""`, `session_id: ""`, `seq: 0`, `ts: 0.0` en todo `ToolResultEvent` medido. El `result` sí viaja. Con `seq`/`ts` a cero no se puede ordenar ni fechar una traza, y sin `task_id`/`agent_id` no se puede separar lo del agente de lo de un subagente — el paso 4 del método queda cojo justo donde más falta hace. Entra con el **#10** | ⛔ abierto — **NUEVO, 11ª ventana** |
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
