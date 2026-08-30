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
| 2 | Fallback de `BashTool` (`TRAMO-1.md:183`) | conducta | ✅ **PAGADO** (13ª ventana) — más ancho que la ficha: el fallback estaba en **dos** sitios de producción |
| 3 | Remediación de `FIND-TS-1` / `TS-3` / `TS-4` | deuda ya declarada | ⛔ abierto |
| 4 | `GAP-TOOL4` | deuda ya declarada | ✅ **PAGADO** (`D-19`) — 15 nativas diferidas como A; marcador antes/después de 14 sesiones con `AGENTIC_CODE_GPT5_HINTS=0` |
| 5 | `GAP-PROMPT-1` — **reenunciado por `D-20`**: no «descripciones sin homologar» sino descripciones que **no guían la elección** con gpt-5.x (P4). Partido por el dogma: la guía que nombra una tool va a su `description`; el segundo atractor (cierre en vacío tras `AskUserQuestion`) al prompt sólo como incitador **genérico** | superficie del modelo | ⛔ abierto — cierra con conducta medida, no con paridad textual |
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

**Detalle del #2 — remediación desarrollada (`L05`, seis campos).** La ficha nombraba `bash.py:27`; el
fallback vivía en **dos** sitios de producción, y el segundo (`worktree.py:64`) en un módulo cuya
cabecera declara haber cerrado justo este bypass un nivel más abajo (`S15`: git por `run_argv` y no por
`create_subprocess_exec`). Lo DICTA el canónico (`D-08`, `sandbox-adapter.ts` 1→EOF): `wrapWithSandbox`
**lanza** en vez de degradar (`:704-717`), `isSandboxRequired` lee `failIfUnavailable` (`:479-485`) y el
fix de #34044 (`:549-560`) llama a la degradación silenciosa **«a security footgun»**.

| Campo | Contenido |
|---|---|
| **Comportamiento** | Con `ctx.exec_env` sin poblar, las tools que corren comandos **no ejecutan**: devuelven `is_error` limpio diciendo por qué. El default sigue existiendo, pero sólo en el ensamblador. |
| **Seam** | `S15 ToolExecEnvironment`. `None` = costura sin poblar, igual que `runner=None` (`S18`) y `scope=None` — precedentes del propio B, no invención. |
| **Firma** | `require_exec_env(ctx) -> ToolExecEnvironment` + `ExecEnvironmentUnavailable(RuntimeError)` en `tools/exec_env.py`. Punto único: una tool nueva que corra comandos pasa por ahí o revienta. |
| **Cableado** | `bash.py` comprueba ANTES de resolver el cwd (para que el motivo que sale sea el real); `worktree.py::_run` **lanza** y las dos tools guardan arriba —`ExitWorktree` **sólo** en la rama `remove`, porque `keep` no ejecuta nada—. `exec_env` sigue SIN `default_factory` en `tool_use.py`, a diferencia de `fs`/`presentation`, cuyos defaults sí son seguros. |
| **Orden** | contrato (`exec_env`) → choke (`require_exec_env`) → tools (`bash`, `worktree`) → comentario de contrato (`tool_use`) → detector en consumidor. |
| **Prueba** | Detector en `agentic_code` que nace ROJO (`test_a_broken_exec_cable_stops_the_command_instead_of_running_it_on_the_host`): con el cable roto tras componer, el `touch` **no deja fichero**. Medido por EFECTO, no por mensaje. |
| **Acreditación** | `INY-59..64`. **Dos salieron VERDES y ESO fue el hallazgo**: `60` (fallback dentro de `_run`) y `62` (guarda de `ExitWorktree(remove)`) no ponían roja ninguna prueba ⇒ dos tests que faltaban, escritos y nacidos rojos. El resto: `59` fallback en `bash` (2 rojas: runtime + consumidor) · `61` sin guarda en `EnterWorktree` (1) · `63` `default_factory` en el contrato (4) · `64` sin default en el ensamblador (1, el control positivo). |
| **`H-L4` saldadas de paso** | `test_bash_defaults_to_local_when_no_env` aseveraba `is_error is False` — **consagraba** la divergencia; reescrito. Y `_ctx()` de `test_tools_native_homologation.py` corría bash/worktree **en el host** por el fallback, es decir acreditaba conducta por un camino que producción nunca toma: ahora inyecta `LocalExecEnvironment()` explícito. |
| **Descartado por lectura, no por grep (`L10`)** | El `create_subprocess_exec` directo de `clone_repository.py:131` es **divergencia declarada** en su propia cabecera (`:11-13`: el clone corre FUERA del sandbox, con red). No se toca. |

**Detalle de `FIND-DEFER-1` — pagado en la misma ventana** (era la deuda que destapaban los
adversariales del fichero de test reescrito, y dejarlo abierto habría dejado 6 tests rojos o, peor, 6
tests debilitados). La defensa va donde A la pone: el **INGRESO**. `buildMcpToolName` sanea el nombre de
la tool con `normalizeNameForMCP` (`mcpStringUtils.ts:70-72`, `normalization.ts:17-23`) y conserva el
original en `mcpInfo.toolName` para la llamada real (`client.ts:1767-1773`). B ahora hace lo mismo:
`build_mcp_tool` expone `name` saneado y guarda `remote_name` crudo, con el que `execute` llama al
server. La propiedad que se mide es la **CONVERGENCIA** del delta (anunciar y recomputar ⇒ `None`), no
el texto. **6 tests nacidos rojos.** Sigue en pie que el mecanismo de B (re-parsear el texto rendido)
diverge del attachment estructurado de A: eso es forma, y se paga —si se paga— con el `MessageEvent`
del #10, no aquí.

**Detalle de `FIND-DEFER-2` — remediación desarrollada (`L05`, seis campos).** El canónico capa en
**dos** sitios, y sólo uno tiene homólogo en B: las `instructions` del server (`client.ts:1160-1171`) y
la descripción de cada tool MCP (`:1789-1794`). Lo DICTA su propio comentario (`:213-217`): «OpenAPI-
generated MCP servers have been observed dumping 15-60KB of endpoint docs into tool.description».

| Campo | Contenido |
|---|---|
| **Comportamiento** | El texto que un tercero escribe y que llega al MODELO está acotado a 2048 ch + sufijo, por **todas** las vías: schema anunciado, resultado de `ToolSearch` y schema del resolver. El original no se pierde. |
| **Seam** | El constructor de `McpTool`. A capa dentro de un **accessor** (`prompt()`), y por eso ningún consumidor lo esquiva; B no tiene accessor —`description` es un atributo que cada consumidor lee directo—, así que el único punto equivalente por el que pasa TODO es el constructor. En `build_mcp_tool` sería esquivable instanciando a mano (`INY-71`, roja). |
| **Firma** | `MAX_MCP_DESCRIPTION_LENGTH = 2048` y `cap_mcp_description(text) -> str` en `capabilities/mcp/tool_adapter.py`, reexportados. Nuevo atributo `McpTool.raw_description` = el texto íntegro, homólogo del `description()` de A (`:1786-1788`). |
| **Cableado** | `self.description = cap_mcp_description(description)`; `raw_description` guarda el original. Sufijo literal del canónico, `… [truncated]`. |
| **Orden** | canónico (los dos sitios de cap) → medida por conducta de las 3 vías → constante+función → constructor → server de prueba → detector. |
| **Prueba** | El volumen entra por un **transporte real**: `dump_docs` declara 60 005 ch en el propio `_mcp_echo_server.py` (FastMCP, Streamable HTTP) y el E2E asevera que lo registrado está capado y marcado, con `raw_description` intacta — sin esa segunda aserción el test pasaría por no haber dump. Más 6 de conducta por vía y por borde. |
| **Acreditación** | **8 inyecciones, 8 rojas, 0 falsos positivos** (`INY-65..72`): `65` sin cap (5 unit + E2E) · `66` sin sufijo · `67` el cap movido al serializador común — la que caza la divergencia **por exceso** · `68` sufijo siempre · `69` `raw_description` pisada · `70` off-by-one en el borde exacto · `71` cap en `build_mcp_tool` (esquivable) · `72` `ToolSearch` devolviendo la cruda. Revertido desde copia propia verificada por `sha256`; jamás `git checkout`. |
| **Contraprueba, no relleno (`L10`)** | Las descripciones **nativas** NO se capan, y hay un test que se pone rojo si alguien lo cambia (`INY-67`). En A el cap vive en el `prompt()` de la tool MCP y no en el serializador común (`api.ts:171`), y por eso `Agent` pasa con sus 16,6 KB. Capar las nativas sería divergencia por exceso. Tampoco se capa `searchHint`: A tampoco lo capa. |
| **Lo que NO se pagó, dicho** | El **segundo** sitio de cap del canónico, las `instructions` del server, no tiene homólogo porque B **no las ingiere en absoluto**. No es un olvido de esta ficha: ya está declarado como `FIND-MCP12` con un `xfail(strict)` vivo (`test_cap_mcp_homologation.py:266-269`) y destino en `11-cap-mcp.md`. Se dice, no se disfraza. |
| **Límite del método `D-15`, dicho** | Aquí **no hay detector en `agentic_code`**: el integrador no tiene cableado MCP alguno (sólo `permissions.py` lo menciona). La evidencia más fuerte disponible no es el consumidor sino un server MCP **real** emitiendo el volumen extremo de punta a punta. No se fabricó un consumidor de coartada para poder decir que lo hay. |

---

## 2 bis · El cable MCP de `agentic_code` (15ª ventana) — pago del límite declarado del método

La 14ª ventana cerró `FIND-DEFER-2` diciendo un límite y no disfrazándolo: **«no hay detector en
`agentic_code` porque el integrador no tiene cableado MCP alguno»** (`:154`). Ese límite no es una nota
al pie: mientras exista, toda la pata MCP sólo puede acreditarse con la suite propia del runtime, que
es exactamente lo que `D-15` declara insuficiente. El encargo de esta ventana, fijado por el usuario
antes del siguiente enunciado, fue cerrarlo.

**Reparto dictado por el propio contrato del runtime, no por gusto.** `McpConfigStore` dice con todas
las letras «el runtime define este contrato; el integrador provee la implementación»: el runtime trae
precedencia por scope, exclusividad de `enterprise`, gate de mutabilidad, conexión y `reconcile()`;
*de dónde salen* los servers es del integrador. Se respeta el encuadre vinculante — el núcleo se
mantiene GENÉRICO y el integrador se adapta a él —: en `agentic_runtime` sólo entran dos cosas, y
ninguna es MCP-específica de producto.

| Campo | Contenido |
|---|---|
| **Comportamiento** | `agentic_code` produce los cuatro scopes de A: `project` (`.mcp.json` recorrido desde la RAÍZ hacia el cwd, el más cercano gana, `config.ts:917-955`) **filtrado por aprobación** (`config.ts:1167`), `user`, `local` (+ `disabledMcpServers`) y `enterprise` (`managed-mcp.json`, sólo lectura, `config.ts:705-709`). Variables expandidas como `envExpansion.ts:16-32`. El runtime conecta, publica las tools como DIFERIDAS y el modelo llega a ellas por `ToolSearch`. |
| **Seam** | `CapabilitiesConfig(mcp_config_store=…)` en `composition.py` — la costura pública que ya existía y que nadie cableaba. Sin esa línea el `McpProvider` **ni se construye** (`factory.py:177`) y todo el MCP del runtime queda inalcanzable desde el producto: `cablear ≠ existir` (`L09`) en su forma más literal. |
| **Firma** | Integrador: `agentic_code/mcp_config.py` (nuevo) — `build_mcp_config_store(settings, identity, *, approvals)`, `ProjectServerStore`, `JsonFileServerStore`, `ServerApprovals`, `expand_env_vars*`, `discover_project_files`. Runtime: **una** propiedad pública nueva, `LocalRuntime.capabilities` — devuelve el `CapabilityManager`, no MCP; genérica por construcción. |
| **Cableado** | `cli.py` construye UN `ServerApprovals` y lo comparte entre el store y el REPL (si fueran dos objetos, aprobar en el REPL no cambiaría lo que el store lee). `repl.py` gana `/mcp`, `/mcp approve <n>`, `/mcp deny <n>`, que tras decidir llama a `provider.reconcile()`: el server se conecta **sin reiniciar**. El gate de aprobación no es un cable muerto: tiene superficie humana. |
| **Orden** | contrato leído → sourcing del integrador (`mcp_config.py`) → cable (`composition.py`) → superficie (`cli.py`, `repl.py`) → accessor genérico en el runtime → detectores. |
| **Prueba** | 6 detectores E2E con un server MCP **real** de terceros por stdio (`tests/_mcp_echo_server.py`, SDK `mcp` 2.0.0 instalado en el venv del integrador) + 9 tests de sourcing. Ninguno usa dobles del runtime. |
| **Acreditación** | **13 inyecciones, 13 rojas, 0 falsos positivos.** Runtime `INY-73..76`; integrador `INY-77..85`: sin `capabilities=` en `composition` · gate de aprobación quitado · recorrido de `.mcp.json` invertido · `headers` sin expandir · `_apply_disabled` neutralizado · validación de nombre quitada · productor `PROJECT` quitado · `/mcp approve` sin `reconcile` · accessor del runtime quitado. Anunciadas ANTES de tocar fuente; revertidas desde copia propia verificada por `sha256 -c` en `mktemp -d`; jamás `git checkout`. |
| **Lo que NO se cableó, dicho** | (a) El **watcher** de config (`mcp_config_watcher`): el runtime lo soporta, el integrador no lo pasa — hoy la reconciliación es explícita por `/mcp`, no por inotify. (b) Los handlers **OAuth** interactivos para servers remotos: sólo se cablearon stdio/HTTP sin flujo de autorización. Ninguna de las dos se disfraza de cableado. |

### Cosecha del cable: tres defectos del RUNTIME que su propia suite no podía ver

Este es el rendimiento de `D-15` y la razón de haberlo hecho antes del siguiente enunciado. Los tres se
midieron **por conducta contra el server real, antes de escribir una línea de arreglo**.

| ID | Hallazgo | Estado |
|---|---|---|
| `FIND-MCP-SDK-1` | El cliente lee los campos del SDK **por una sola grafía**. `mcp.types` genera alias camelCase, pero el atributo Python cambió de major: 1.x expone `inputSchema`/`isError`/`mimeType`, 2.x expone `input_schema`/`is_error`/`mime_type`. Con el SDK 2.x, **toda** tool MCP llegaba al modelo con `inputSchema` VACÍO: el modelo ve la tool y no puede llamarla con argumentos. La suite del runtime corría con 1.27.2 y estaba **verde y ciega** — sólo un consumidor con otro venv podía verlo | ✅ **PAGADO** — helper `_read(obj, *names)` tolerante a ambas grafías, aplicado a los tres campos |
| `FIND-MCP-ERR-1` | Un resultado con `isError=True` se entregaba al modelo **como respuesta correcta**: `call` sólo miraba la grafía 1.x, así que bajo 2.x el fallo del server remoto se convertía en output válido. Es la familia de `L10` invertida: no es divergencia de forma, es un error silencioso que el modelo consume como dato bueno | ✅ **PAGADO** — `McpToolError`, con detector que exige el mensaje del PROPIO server, no un genérico |
| `FIND-MCP-META-1` | El `_meta` del server **nunca salía del cliente**: el adaptador leía `searchHint` de un campo que el cliente no poblaba jamás. Cable muerto con las dos grafías del SDK, no un problema de versión — el `searchHint` que A usa para que `ToolSearch` encuentre la tool no existía en producción | ✅ **PAGADO** — `_meta` reenviado desde `list_tools` |

**Error de método mío, dicho.** Dos detectores fallaron en la primera corrida y **uno de ellos venía
pasando por la razón equivocada**: `dangerously_skip_permissions=True` en `Settings` no hace nada sin
un `PermissionPolicy` —el bypass lo implementa la política—, así que toda tool MCP moría en el hook de
permisos y el `"✗ always_fails"` que yo leía como «el server falló» era **permiso denegado**. Corregido
el arnés (`permission_policy=` en el helper) y **reforzada** la aserción para exigir el texto del
server. Un verde por el motivo equivocado es exactamente lo que `L03` llama ledger deshonesto.

---

## 2 ter · La re-medida del `E2g` con el prompt de PRODUCTO (17ª ventana)

La 16ª ventana midió el residuo del `E2g` **sin** el prompt del producto y lo dejó como pendiente de
verificación abierto. El encargo de ésta fue re-medirlo con `operational_system_prompt()` de
`agentic_code` puesto, ≥6 rondas, y **prohibido decidir el criterio de cierre antes de tener el dato**.

**Premisa del encargo, corregida (`L01`).** La línea 329 concluyó de un `grep system_prompt` sobre
`test_tramo1_gate.py` que «el gate corre sin ningún system prompt». Es falso: `:2384` hace
`inner = _build_caller(_E2G_SYSTEM)`, **posicional**, a través de un import aliaseado (`:76`) cuya firma
vive en `_azure_real.py:build_caller(system_prompt, options=None)`. El grep no lo vio porque el nombre
no aparece en el fichero. El experimento no fue «desnudo vs vestido» sino **`_E2G_SYSTEM` solo vs
`_E2G_SYSTEM` + invariantes del producto**, que es la ruta real de un usuario con prompt custom.

**Instrumento.** Plugin de pytest de MEDICIÓN, fuera del árbol, que **no toca el fuente del gate**:
importa la función REAL del integrador (no copia el texto, `D-15`) y cuelga `on_payload` para
**probar el cableado** en vez de suponerlo — se asevera que todos los payloads que salen hacia Azure
llevan `<completion-policy>`. Si no viajara, la medición sale roja ahí, no en silencio (`L09`).

**Dato: 2 incumplimientos en 32 casos (6,3 %), la misma cifra de cabecera que sin el prompt de
producto.** Pero abrir las dos rojas es lo que separó incitación de defecto:

| Ronda | Semilla | Síntoma | Naturaleza |
|---|---|---|---|
| 3 | `1780649320` | `elegidas=['AskUserQuestion','glob']`, `respuesta=''` | residuo de INCITACIÓN — el `<completion-policy>` no lo corrige |
| 6 | `986409977` | «la tarea fue CANCELADA esperando el stream», `TaskStop` entre las elegidas, `respuesta=''` | **defecto de B**, no del modelo → `FIND-TASK-SELF-1` |

⇒ el residuo de incitación real es **1 de 32 (3,1 %)**, no 2. Con n=32, 2/32 frente a 2/32 significa
«sin diferencia medible a este tamaño», **no** «sin efecto»: la muestra no distingue 6 % de 3 %, y eso
se dice en vez de redondearlo a una conclusión.

### `FIND-TASK-SELF-1` — el modelo podía detener su propio turno ✅ PAGADO

**A tiene DOS registros; B los fusionó en uno.** `TaskStopTool.ts` valida contra `appState.tasks[id]`
con `status === 'running'`, y ahí sólo viven tareas de FONDO (shells, agentes async, sesiones remotas);
el turno principal **no es una entrada de ese registro**. `TaskList/Get/Update` de A leen la otra
estructura, la lista por sesión. B tiene un único `InMemoryTaskRegistry` donde la tarea raíz también
vive, con `owner_session_id == ctx.session_id` (`runtime.py:192-194`, `:292-293`) ⇒ `list_for`
(`registry.py:106`) se la sirve al modelo y `_scoped_get` la resuelve por id, así que `TaskStop` la
mata con `asyncio_task.cancel()` (`registry.py:118-125`).

**Medido antes de arreglar**, con sonda de conducta sobre el runtime ensamblado por `create_runtime`
(caller guionizado, sin red): `TaskList` devolvió la propia raíz, `TaskStop` apuntó a ella, y con el
turno final esperando al stream el resultado fue `status=KILLED`, `result=None`. Segundo modo
destapado por la variante rápida: si la cancelación llega tarde, **el registry dice `COMPLETED` con
resultado mientras quien espera la tarea recibe `CancelledError`** — estado incoherente.

**Pago:** guarda `_is_own_task(task_id, ctx)` sobre `ctx.task_id` (el cable que pobló `FIND-STREAM-1`),
aplicada en `_scoped_get` (cubre `Get`/`Update`/`Stop`/`Output`) y en el filtro de `TaskList`.
**Alcance declarado, no disimulado:** es una guarda, no la topología de A; la separación de los dos
registros es más ancha y queda con `FIND-TASK-1`, que es la misma raíz.

**Prueba:** 7 tests nacidos rojos en `test_task_self_stop_guard.py` — 4 de unidad parametrizados sobre
las cuatro tools direccionables, uno de listado, uno E2E que reproduce la RONDA 6 (el modelo LEE el id
de `TaskList`, no lo inventa) y **un control positivo** que impide que la guarda degenere en «`TaskStop`
no para nada». **Acreditación `INY-51..55` → 5 rojas / 0 falsos positivos**: guarda neutralizada · sólo
en `_scoped_get` · sólo en `TaskList` · cable equivocado (`agent_id` por `task_id`) · comparación laxa.
Dicho: bajo `INY-53` el E2E **sobrevivió** y sólo cayeron los 4 de unidad — el E2E no cubre esa vía por
sí solo, y por eso hacen falta los dos niveles.

### Incitadores extendidos en el registro que ya existía (`agentic_code`, genéricos, `L10`)

Para el residuo que sí es de incitación se extendió `operational_system_prompt()` con dos bloques más,
**sin nombrar ninguna tool**: `<tool-availability>` (la lista visible puede no ser la completa; algunas
se cargan al buscarlas y otras aparecen a mitad de conversación) y `<answer-policy>` (terminar siempre
con el dato o con el bloqueo concreto; devolver la pregunta al usuario sólo si el trabajo no puede
continuar sin su decisión). Es cierto en producción: el diferimiento lo decide `is_deferred_tool()`
sobre el pool (`deferred_strategy.py:58,92`), no una configuración del banco de pruebas.

---

## 2 quater · `FIND-POOL-1` — al pool le faltaba el predicado de PUBLICACIÓN ✅ PAGADO (18ª ventana)

**Es el mismo hallazgo que `FIND-POOL-1` de la §3, redescubierto por otra vía.** Lo abrí como
`FIND-TOOL-ENABLED-1` desde las rojas del `E2g` sin caer en que el barrido EOF de la 10ª ventana ya lo
había cazado leyendo el canónico. Se unifican bajo `FIND-POOL-1`: dos IDs para un defecto inflarían el
ledger y romperían la trazabilidad. Que un mismo defecto salga por dos instrumentos independientes
—lectura del canónico y medición con el modelo real— es la confirmación cruzada que `D-15` busca.

**El defecto.** A tiene DOS filtros en el ensamblado del pool (`tools.ts:311-326`): deny —lo que el
usuario prohibió— e `isEnabled()` —lo que el host no puede sostener—. B sólo tenía el primero.
`isEnabled` no figuraba siquiera en la lista de miembros diferidos del contrato
(`contracts/tools.py:3-6`): **omisión no declarada**, que es peor que una deuda.

A escribe la razón, y es literalmente el síntoma que medí:
> *«When --channels is active, ExitPlanMode is disabled (its approval dialog needs the terminal).
> Disable entry too so plan mode isn't a trap the model can enter but never leave.»*
> (`EnterPlanModeTool.ts:56-67`)

**Medido tres veces en el `E2g`, con dos tools distintas**, y las tres son la misma forma —una tool que
cede el turno esperando a un humano, publicada en un host que no tiene humano—:

| Semilla | Síntoma |
|---|---|
| `1780649320` | `elegidas=['AskUserQuestion','glob']`, `respuesta=''` |
| `29525785` | el modelo entró en plan mode y se declaró bloqueado |
| `1561952726` | ídem |

⇒ **3 de las 4 rojas residuales del `E2g` eran UN defecto de B, no incitación.** El cuadro que las
contaba como ruido del modelo estaba mal, y la reclasificación es el resultado, no una excusa.

**Pago.** `tool_is_enabled()` en el contrato (helper, no miembro del `Protocol`: declararlo requerido en
un `runtime_checkable` estructural rompería el `isinstance` de toda tool de terceros — que es lo
contrario de un *default*, y A lo tipa requerido pero lo lista en `DefaultableToolKeys` y lo rellena en
`buildTool`, `Tool.ts:403,708,749,758`). Filtro aplicado en `assemble_tool_pool` **al final, tras deny y
dedup**, orden que es parte de la costura: una capability NO puede ocupar el hueco de una nativa
apagada. Eje nuevo `ToolsConfig.interactive`, default `False`, mismo criterio que los handlers OAuth de
`CapabilitiesConfig` — el runtime headless no abre navegador.

**Prueba:** 13 tests nacidos rojos en `test_tool_enablement.py`. La ronda de reversión con el estado
previo íntegro sólo da `ImportError` —señal gruesa—, así que se midió además una ronda **quirúrgica**
que deja el arreglo puesto salvo el filtro del pool: 7 rojos por `AssertionError`, conducta y no firma.
Se descartan explícitamente dos rondas intermedias que enrojecían por `TypeError` en cadena: eso es
`H-L4` y no acredita nada.

**`INY-73..80` → 8 rojas / 0 falsos positivos**, y **dos de ellas nacieron VERDES, que es el hallazgo**:

- `INY-76` (estrechar el helper a «sólo callable»): verde porque el fake siempre adjunta una lambda. La
  docstring prometía aceptar también un atributo booleano —la grafía más natural en Python para una
  tool de terceros— y **nadie lo medía**. Declaración sin prueba.
- `INY-79` (invertir el default de `ToolsConfig.interactive`): verde porque todos los tests pasaban
  `interactive=` explícito. El **default** es justo la costura del caso real —un integrador que no
  configuró nada— y era la única sin vigilar.

Ambas carencias son mías, se pagaron con dos tests más, y las inyecciones re-corridas ya enrojecen.

**Radio de explosión, atendido y no disimulado.** El arreglo puso en rojo `E2c`, `E2d` y `E11`, que
codificaban la premisa vieja «el censo entero se anuncia siempre». Ninguno se relajó:

- `E2c` gana una **rama C** con el mismo tratamiento que ya se le había dado a `ToolSearch`: el censo
  se anuncia entero **si y sólo si** el host sostiene las de puerta única, y se asevera que la
  diferencia entre los dos hosts es *exactamente* ese conjunto. Es más fuerte que la premisa vieja.
- `E2d` declara `interactive=True` porque mide selección **contra el censo íntegro como distractor**:
  dejarlo headless le quitaría 3 opciones al modelo y ablandaría la prueba en silencio, quedándose
  verde mientras mide algo más fácil que lo enunciado.
- `E11` declara `interactive=True` porque `AskUserQuestion` está en `_E11_OBJETIVO`: en headless la
  tool no se anuncia y el gate mediría una tool **ausente** en vez de una **no elegida** — dos cosas
  distintas con el mismo rojo. Se corrigió además la nota de `_E11_CARENCIA` que decía «mecánicamente
  cierta en un runtime headless» y habría quedado engañosa.

**El radio de explosión estaba INCOMPLETO, y lo destapó la 19ª ventana: el propio `E2g`.** La suite
completa salió `1 failed, 888 passed`, y el rojo era `E2g` fallando en **12,84 s** —antes de llamar al
modelo— en la aserción de montaje `test_tramo1_gate.py:2497`:
`AssertionError: [web/nativa] diferidas sin 'defer_loading' en el cable: ['EnterPlanMode']`.

Causa: los **señuelos** del montaje se sorteaban sobre `_NATIVE_CENSUS` crudo
(`rnd.sample(sorted(_NATIVE_CENSUS - sc["hide"] - {"ToolSearch"}), …)`), que sigue listando —con
razón— las tres de puerta única. Desde el pago de `FIND-POOL-1` esas tres no se publican en un host
headless, así que toda semilla cuyo `sample` tocara una de ellas exigía verla marcada `defer_loading`
en un anuncio donde ya no está. No es fallo del modelo ni del runtime: es el **banco de pruebas
arrastrando la premisa vieja**, exactamente el mismo error que en `E2c`/`E2d`/`E11`, en el único
escenario que la revisión de aquella ventana no repasó.

**Por qué una corrida verde no lo vio, dicho sin adornos:** la semilla es aleatoria salvo que se fije
`GATE_E2G_SEED` (`:2378`), de modo que el defecto es **intermitente por construcción** y el verde
único con que se cerró la 18ª ventana no prueba lo que parecía probar. Un gate con montaje aleatorio
exige que el *invariante del montaje*, no la corrida, sea lo que se acredita.

**Arreglo (19ª ventana).** El universo de señuelos pasa a derivarse de lo que el pool **publica**
—`{t.name for t in create_tools().all_tools() if tool_is_enabled(t)}`— y no del censo. Una tool que
el host no publica no es señuelo: no llega al anuncio, así que ni oculta nada en la rama simulada ni
puede aparecer diferida en la nativa. `_NATIVE_CENSUS` **no se estrecha** (lo aseveran `:1353`,
`:1617`, `:1763` como censo de registro), y se añade una guarda que exige
`_NATIVE_CENSUS - publicables == _PUERTA_UNICA`: si mañana se apaga otra cosa, el gate se pone rojo y
obliga a mirarlo en vez de dejar que el universo de señuelos se encoja en silencio. Que el arreglo sea
correcto **para toda semilla** es una propiedad estructural, no un muestreo:
`publicables ∩ _PUERTA_UNICA = ∅`, y ambos `sc["hide"]` (`:2344`, `:2356`) están dentro de
`publicables`. Verificado además con corrida real (`GATE_E2G_SEED=4294967291` → passed en 37,57 s).

**`FIND-CODE-HITL-1` (nuevo, desde el consumidor real).** `agentic_code` **no resuelve ninguna** tool de
puerta única: `driver.py` (leído 1→EOF) se autodescribe como «driver headless compartido», es el mismo
para el REPL y para `--print`, y ni detecta el `tool_call` de `AskUserQuestion`/`ExitPlanMode` en el
stream ni reinyecta la respuesta del usuario en el turno siguiente. ⇒ el default headless es el
correcto **en los dos modos**, y lo que se cablea es una declaración escrita en `composition.py` para
que nadie lo «arregle» poniendo `True` sin la capa (`L09`). El día que el REPL implemente el HITL, ése
es el punto exacto que cambia.

**Deuda cero neta por diff**, medida contra el árbol sin el arreglo, no contra una cifra recordada:
`ruff` 510 → 510 (los 2 `RUF012` que introduje se limpiaron con `ClassVar`), `mypy --strict` 135/52.

**No pagado y dicho — `FIND-PLAN-FILE-1`, y ES LO SIGUIENTE, no un ítem más de la cola:** el apagado
headless saca a plan mode de la medición, pero **no cablea el plan-file**. Hasta hoy era latente porque
`ExitPlanMode` era inalcanzable en la práctica; con `ToolsConfig.interactive` **basta que un host declare
`True` para que pase a fallo ACTIVO**, y su habilitador es `FIND-CODE-HITL-1`, que va antes o a la vez. Con un host interactivo, `provider.py:41` sigue ordenando escribir en
`/plans/plan.md` y `is_session_plan_file` (`plan_file.py:58-63`) no tiene consumidor fuera de tests en
ninguno de los dos repos. Queda abierto y nombrado, no cerrado por efecto lateral.

---

## 2 quinquies · `FIND-PLAN-FILE-1` + `FIND-CODE-HITL-1` — diagnóstico (19ª ventana)

Los dos ítems que la 18ª ventana abrió. Se atacan juntos porque **`ExitPlanMode` es una de las dos
tools de puerta única**: la capa HITL sin plan-file publica una tool que no puede funcionar, y el
plan-file sin HITL no tiene quién apruebe. El orden real de pago es **plan-file → HITL → `interactive`**,
y se dice por escrito porque no es el orden en que vienen enunciados en el encargo.

### `FIND-PLAN-FILE-1` — no es «falta un consumidor»: son TRES cortes independientes

Enunciado hasta hoy: «`is_session_plan_file` no tiene consumidor fuera de tests». Al leer el camino
entero 1→EOF resulta ser el **tercero** de tres cortes, y los dos primeros son más graves porque
dejan la tool muerta aunque el tercero se pague.

1. **`ctx.storage` NUNCA se puebla en producción.** `execution/local/runtime.py:426-439` threadea al
   ctx `presentation`, `exec_env`, `git_credentials`, `runner`, `task_registry` y `fs` — **`storage`
   no está en esa lista**. `LocalAgentRuntime._storage` existe (`:107`) y se usa en un solo sitio,
   `:578`, para subir el transcript. El único constructor de ctx que acepta `storage=`
   (`context/adapters.py:12-49`) **no lo llama nadie en `src/`** (censo hecho: sólo `__init__.py` lo
   re-exporta y tests lo usan). ⇒ `plan_file_exists()` devuelve `False` **siempre** y `get_plan()`
   devuelve `None` **siempre** ⇒ `ExitPlanMode.execute` cae invariablemente en su rama de error
   («No plan found at /plans/plan.md»), **aun con host interactivo y aun con el plan escrito**.
   Es el patrón `S18`/`S19` ya pagado para `runner`/`task_registry`: el cable existe en el TIPO y no
   existe en la EJECUCIÓN.
2. **Desajuste de protocolo — dos `Storage*` distintos.** `plan_file.py:75,91` llama `real_path()` y
   `await ensure_local()`, que son `StorageContract` (`contracts/storage.py:22-30`). Lo que
   `factory.py:237` construye es `StorageRegistry.create("filesystem")` → `FilesystemStorage`, que
   implementa `StorageProtocol` (`upload/download/presign/delete/exists/list_prefix`,
   `storage/protocol.py:9-17`) y **no tiene ninguno de los dos métodos**. Consecuencia medible si
   alguien «arregla» el corte 1 enchufando ese objeto: `plan_file_exists` se traga el `AttributeError`
   (`except Exception` → `False`, silencioso) y `get_plan` lo deja **escapar** (`except OSError` no lo
   atrapa) ⇒ `ExitPlanMode` revienta en vez de errar. Y **no hay ningún campo en `RuntimeConfig`** por
   el que un integrador pueda inyectar un `StorageContract`: el único hueco es el parámetro `storage=`
   de `ConfinedFilesystem` (`tools/fs_env.py:121-132`), que no llega al ctx.
3. **Confinamiento: el modelo no puede obedecer la instrucción que el propio runtime le da.**
   `capabilities/plan/provider.py:40-42` le ordena escribir el plan en `/plans/plan.md` con
   `write_file`. `write_file` resuelve por `ctx.fs.resolve(token, for_write=True)`; con `storage=None`
   el token se toma como path host y se confina contra `write_roots=[cwd]` (`composition.py:127-130`)
   ⇒ **`PathOutsideWorkspace`**. El plan-file está fuera del workspace por construcción.

**Qué dicta el canónico (`D-08`, leído, no razonado).** `isSessionPlanFile` (`filesystem.ts:245`)
tiene **dos** consumidores de producción y los dos están en la capa de PERMISOS:
`checkEditableInternalPath` (`:1488`, `'Plan files for current session are allowed for writing'`) y su
gemelo de lectura (`:1645`, `…allowed for reading`). Es una **exención del chequeo de
workspace/permisos**, no de un «candado de plan mode» — el docstring de `plan_file.py:58-63` lo
nombra mal. Su homólogo exacto en B es `ConfinedFilesystem.resolve`, que es donde vive ese chequeo.
Eso lo vuelve **mecanismo del runtime**, no política del integrador.

**Lo que NO es hueco del runtime, y se dice para no inflar la deuda (`L10`).** `app_state.native` es
per-ctx y no se persiste entre turnos, luego `plan_mode` no sobrevive al turno. Eso **no** es un
defecto: `runtime.py:442` designa por escrito `root_context_modifier` como la costura donde el
consumidor siembra `app_state.native`. Persistir el flag es trabajo del integrador, y `agentic_code`
no lo hace hoy (`author_root_context` sólo siembra permisos y cwd).

### `FIND-PLAN-FILE-1` — remediación desarrollada (`L05`)

- **comportamiento** · Con host interactivo: el modelo escribe el plan en el token que el reminder le
  dicta, `ExitPlanMode` lo lee y lo presenta. Sin host interactivo nada cambia (las tools siguen
  despublicadas por `is_enabled`).
- **seam** · (a) nuevo campo `RuntimeConfig.storage_contract: StorageContract | None`, threadeado a
  `ctx.storage` en el mismo bloque que `ctx.fs` (`runtime.py:426-439`) y al fork; (b)
  `ConfinedFilesystem.resolve` consume `is_session_plan_file(token)` para eximir el plan-file del
  allow-set, espejo de `checkEditableInternalPath`/`checkReadableInternalPath`.
- **firma** · `RuntimeConfig(storage_contract=…)`; `ConfinedFilesystem.resolve` sin cambio de firma
  (la exención es interna, para que ningún consumidor la esquive — mismo criterio que el cap de
  `FIND-DEFER-2`).
- **cableado** · `factory._build_local` pasa `config.storage_contract` a `LocalAgentRuntime`, que lo
  asigna al ctx raíz **antes** del `root_context_modifier`; el `ForkSnapshot` lo hereda por el mismo
  camino que `fs`. En `agentic_code`: `WorkspaceStorage` (implementación de `StorageContract` que
  mapea `/plans/<n>.md` → `<state_dir>/projects/<key>/plans/<n>.md`) inyectada a la vez en
  `ConfinedFilesystem(storage=…)` y en `storage_contract`, más la persistencia de `plan_mode` en
  `author_root_context`.
- **orden** · Antes que el HITL: `ExitPlanMode` no es publicable mientras esto no funcione.
- **prueba** · Tests nacidos ROJOS en los dos repos: (1) `ctx.storage` poblado en el ctx raíz REAL
  que produce el runtime (no uno de test); (2) `get_plan` devuelve el plan escrito por `write_file`
  en el token del reminder — el ciclo COMPLETO, que es el único que caza los tres cortes a la vez;
  (3) `write_file` sobre `/plans/plan.md` no levanta `PathOutsideWorkspace`; (4) un token que NO es
  plan-file sigue confinado (control negativo, sin el cual la exención sería un agujero).

### `FIND-CODE-HITL-1` — remediación desarrollada (`L05`)

Mecánica establecida por lectura, no supuesta: el loop deja en el historial el `assistant` con
`tool_calls` y el `tool` placeholder (`agent_loop.py:596-613`), rompe con `LoopEndReason.ENDS_TURN`, y
`runtime.py:523` hace `session.messages = list(ctx.messages)` ⇒ **el par tool_call/placeholder SÍ se
persiste** y `ConversationState.reload()` lo ve. Ahí es donde entra la respuesta real.

- **comportamiento** · Turno que cierra con `AskUserQuestion`/`ExitPlanMode` ⇒ el REPL presenta las
  preguntas (o el plan), lee al humano por `self.reader`, y el turno siguiente arranca con el
  tool_result REAL en lugar del placeholder.
- **seam** · Detección: `RunResult.stream.tool_uses` (`streaming.py:151-160` ya modela `call_id`,
  `name`, `tool_input`). Reinyección: `ConversationState`, que es quien posee los mensajes que
  `inject()` mete en cada ctx raíz.
- **firma** · Módulo nuevo `agentic_code/hitl.py`: `pending_interaction(snapshot) -> Pending | None`,
  `resolve(pending, reader) -> Resolution(tool_result, user_message)`;
  `ConversationState.replace_tool_result(call_id, content)`.
- **cableado** · `repl._execute` tras `dispatch_prompt`; `composition.py` pasa a
  `ToolsConfig.interactive=True` **sólo al final**, cuando lo anterior está verde.
- **texto** · Lo DICTA el canónico, no yo: `User has answered your questions: "<q>"="<a>"…. You can
  now continue with the user's answers in mind.` (`AskUserQuestionTool.tsx:222-244`);
  `User has approved your plan. You can now start coding…` / `User has approved exiting plan mode.
  You can now proceed.` (`ExitPlanModeV2Tool.ts`); rechazo: `REJECT_MESSAGE` /
  `REJECT_MESSAGE_WITH_REASON_PREFIX` (`utils/messages.ts:212-215`).
- **divergencia declarada** · El turno de continuación necesita un mensaje de usuario porque el loop
  lo appendea siempre (`agent_loop.py:388`). Se usa **lo que el humano tecleó**, nunca un texto
  inventado ni uno vacío: A no necesita ese mensaje porque resuelve dentro del mismo turno vía
  `checkPermissions → behavior:'ask'`, capa que en B es `GAP-02`/`K1`.
- **prueba** · Tests nacidos rojos: detección del pending; wording exacto de los cuatro desenlaces
  (respuesta / plan aprobado / plan aprobado sin plan / rechazo con y sin razón); reemplazo del
  placeholder por `call_id` (y control negativo: un `call_id` que no existe no toca nada); y un E2E
  de REPL con `reader` guionizado que verifica que el turno siguiente lleva el tool_result real.

**Hallazgo adicional a confirmar, NO aseverado.** En A, `ExitPlanModeV2Tool.call()` —que es quien
restaura el modo— corre **después** de la aprobación (`checkPermissions → behavior:'ask'`), luego un
plan rechazado deja plan mode intacto. En B, `ExitPlanModeTool.execute` (`plan_mode.py:252-259`) hace
`pop(_PLAN_MODE_KEY)` y arma `_PLAN_EXIT_PENDING_KEY` **antes de que nadie decida**. Con la capa HITL
en pie eso es medible: se mide y se resuelve entonces, no ahora.

### `FIND-PLAN-FILE-1` + `FIND-CODE-HITL-1` — ✅ PAGADOS (19ª ventana)

**Lo pagado.** `FIND-PLAN-FILE-1`, lado runtime: los tres cortes atados, con `storage_contract` como
costura y **el mismo objeto** en `ctx.fs` y en `ctx.storage` —dos traducciones distintas del mismo
token serían un plan que se escribe en un sitio y se lee en otro, que era el estado—. 5 tests nacidos
rojos, `INY-81..85` → 5 rojas. `FIND-CODE-HITL-1`, lado integrador: módulo `agentic_code/hitl.py`
(detección + los literales de A con cita), `repl._resolve_single_door_tools` con la respuesta
entregada por un `asyncio.Future` —el bucle de `run()` es el ÚNICO lector de stdin y abrir un segundo
consumidor los habría puesto a competir—, `PlanModeState.rearm()` para el plan rechazado, y
`ToolsConfig.interactive = not args.print_mode`: **lo decide el MODO, no el paquete**, porque el
driver es el mismo para el REPL y para `--print` y la diferencia está en si hay una persona.

**El hallazgo anotado arriba queda CONFIRMADO y resuelto**: B sale de plan mode antes de que nadie
decida, y como el ciclo aquí es multi-turno el runtime no puede conocer el desenlace ⇒ re-armar es
del INTEGRADOR, que es quien tiene la decisión. El runtime lleva el cable; el consumidor decide. Se
resuelve sin tocar el núcleo, según el encuadre vinculante.

**Honestidad sobre el orden de la prueba.** El lado runtime fue test-first de verdad. El lado
integrador (`hitl.py`, el cableado de `repl.py`/`composition.py`) **se escribió ANTES que sus tests**;
se dice porque cambia el grado probatorio. Lo que lo compensa es la ronda de reversión, que es lo
único que acredita que esos tests midan algo: **`INY-94..100` → 7 rojas / 0 falsos positivos**,
reversión desde copia propia verificada por `sha256 -c` (nunca `git checkout`).

### Superficie de terminal: foco y color (19ª ventana, encargo del usuario)

Contraste de la TUI contra el canónico, fuera del ledger de homologación del runtime pero con el
mismo método. `theme.py` nuevo porta la paleta SEMÁNTICA de `utils/theme.ts` con RGB explícito, por
la razón que A documenta (`:107-110`): el `red` de un terminal lo define el usuario. Tres cosas que
el contraste destapó, ninguna visible para la suite anterior:

1. **El foco no volvía al editor.** `on_mount` lo enfocaba UNA vez, al arrancar; abrir un deck o
   cerrar el modal de permiso dejaba las teclas sin destino. Pagado con `on_turn_end` en
   `TextualPresentation` (lo disparan los tres desenlaces, incluidos cancelado y fallido) + `Esc`
   como salida del transcript.
2. **El régimen no se veía en ninguna parte.** En A toda la superficie de plan mode va con
   `borderColor="planMode"` y `PERMISSION_MODE_CONFIG` da símbolo y color por modo. Pagado con el
   indicador en la barra (`⏸ Plan` / `⏵⏵ Bypass`) y las reglas del editor teñidas por régimen.
3. **Colores ANSI del terminal en toda la superficie**, incluido `CANCELLED` compartiendo amarillo
   con «en curso». Pagado y **vigilado**: hay un test que enrojece si vuelve a entrar un `"bold red"`.

`INY-86..93` → **8 rojas / 0 falsos positivos**. Carencia declarada y NO pagada: un solo tema fijo
(A resuelve `auto`/claro/oscuro/daltónico y tiene variantes ANSI); fabricar los seis sin selector
sería cableado que parece existir (`L09`). Guion manual `PRUEBAS-MANUALES.md § J1–J4`.

---

## 2 sexies · La pata de skills — `FIND-SKILL9/17`, `-20`, `-21` y `FIND-SKILL2/4/17/18` (21ª ventana)

Todo lo de esta sección es el **mismo patrón único** que el barrido EOF tipificó: *B tiene el dato
cargado y no lo pone en ninguna lista que el modelo vea*. `SkillsProvider.catalog()` existía, estaba
probado, y **no lo consumía nadie en producción**: el único `.catalog(` fuera de `capabilities/`
vivía en ficheros de test. El único camino por el que un nombre de skill alcanzaba al modelo era el
mensaje de **ERROR** de `skill_tool.py` — o sea, el modelo sólo podía aprender el catálogo
**fallando primero**, y para fallar tenía que haber adivinado un nombre.

**Corrección de premisa, dicha primero.** El encargo (y esta misma tabla) repetía que A tiene «dos
vías» para el listado. Es **falso** y lo desmiente el fuente: `SkillTool.getPrompt` no lleva
listado alguno y `getSessionSpecificGuidanceSection` sólo aporta una viñeta de guía. A tiene **una**
vía real, el attachment `skill_listing`. La premisa vieja habría hecho fabricar una segunda entrega
que en A no existe.

**Corrección de inventario, mía.** Abrí `LAT-SKILL1` como latente nuevo. No lo era: es
`FIND-SKILL4`, que llevaba abierto desde el censo con su `xfail(strict)` puesto. Es la **segunda
vez** que abro por duplicado algo ya censado (la primera fue `FIND-TOOL-ENABLED-1` sobre
`FIND-POOL-1`, 18ª ventana). Se unifican bajo `FIND-SKILL4`; el ID `LAT-SKILL1` se conserva en la
tabla sólo porque los tests y los commits ya lo citan.

### Los tres `xfail` que acreditaban en falso, y el que rotulaba de más

Al pagarse, cuatro `xfail(strict)` se pusieron rojos por **XPASS** — la señal funcionando. Uno de
ellos, el de `FIND-SKILL4`, **rotulaba `${CLAUDE_SKILL_DIR}` en su `reason` y no lo aseveraba en
ninguna línea**: retirarlo por XPASS habría dado por pagadas unas variables que B no sustituía en
ningún sitio. Es `H-L4` en su forma más silenciosa —el rótulo cubriendo más superficie que la
aserción— y por eso las dos variables (`${CLAUDE_SKILL_DIR}`, `${CLAUDE_SESSION_ID}`,
`loadSkillsDir.ts:356-369`) se pagaron también, con su guarda de `base_dir` incluida.

Un quinto xfail, `test_skill_listing_incremental_per_agent`, aseveraba una **FIRMA** (`prov.skill_listing(ctx)`,
un método del provider) y seguía rojo **por el nombre** mientras la capacidad ya existía por otra
costura. Un xfail así miente en las dos direcciones: rojo cuando está pagado, y verde en cuanto
alguien añada el método aunque no anuncie nada. Reescrito a conducta sobre el eje que ningún otro
test medía: el **scope por agente**.

### Acreditación — `INY-120..138`

**19 inyecciones válidas: 15 rojas a la primera, y CUATRO que nacieron VERDES — que son el hallazgo.**
(`INY-121`, `INY-122`, `INY-130`, `INY-135b`. La cifra se corrige aquí: la primera redacción decía
TRES y la tabla de abajo ya listaba cuatro — el recuento correcto es el de la tabla.)

| # | Inyección | Resultado |
|---|---|---|
| `INY-121` | se arranca la guarda `skill_tool_available` | **VERDE** ⇒ el test montaba un provider con TODAS las skills deshabilitadas: sin tool **y sin catálogo**, el delta salía `None` por «nada que anunciar», no por la guarda. Remontado con catálogo LLENO y la tool fuera del pool (subagente restringido, el caso real) + control positivo ⇒ `INY-121b` roja |
| `INY-122` | el delta se reconstruye RE-PARSEANDO el texto rendido | **VERDE** ⇒ **dos** tests débiles a la vez: el del sidecar aseveraba que se ESCRIBE, y el defecto está en la LECTURA (mitades independientes); y el de la descripción multilínea usaba `"linea1\nlinea2"`, con la que el re-parseo **converge igual** porque sólo la primera línea empieza por `- `. El caso adversarial de verdad es una descripción con una **viñeta**. Corregidos los dos ⇒ `INY-122b` → 2 rojas |
| `INY-130` | se arranca la guarda `errorCode`-4 de `SkillTool.execute` | **VERDE** ⇒ sólo estaba acreditado el filtro del LISTADO. Filtrar el listado no basta —lo dice el propio comentario del fuente—: el modelo puede nombrar la skill igual. Test nuevo con los dos ejes (cerrada al modelo, abierta al usuario) ⇒ `INY-130b` roja |
| `INY-135b` | la sustitución alcanza también el MARCO del runtime | **VERDE** ⇒ el marco no contiene placeholders, así que sustituir de más es **idempotente y no se nota**. La frontera sólo es observable por la rama de apéndice: aplicada al todo, apendiza dos veces y **detrás de la coleta**. Aserción reescrita a eso ⇒ `INY-135c` roja |

Rojas a la primera: `120` (el loop deja de anunciar) · `123` (sin caída a sólo-nombres) · `124`
(las bundled pierden la exención del recorte) · `125` (sin re-anuncio íntegro tras una baja) ·
`126` (`when_to_use` no se concatena) · `127` (sin tope de 250) · `128` (`disable-model-invocation`
deja de filtrar el catálogo) · `129` (`when_to_use` vuelve a duplicar la `description`) · `131` (el
frontmatter recupera la identidad) · `132` (los args se vuelven a tirar) · `133` (se sustituye
`${CLAUDE_SKILL_DIR}` sin `base_dir`) · `134` (la tool no pasa el `session_id`) · `136` (last-wins) ·
`137` (sin dedup por identidad real de fichero) · `138` (el slash command tira sus args).

`INY-135` se **descarta y se dice**: la inyección era sintácticamente inválida y murió en
colección. Un error de colección no acredita nada — no distingue «el test ve el defecto» de «el
fichero no importa».

Reversión desde copia propia con `sha256sum -c` → **7 OK** en cada ronda
(`agent_loop · skill_listing_delta · provider · skill_tool · state · loader · commands`).

---

## 3 · Cosecha del barrido EOF (10ª ventana) — entra en la misma cola

Hallazgos del barrido del canónico sobre las LISTAS de tools (nativas, MCP diferidas, skills). No los
produjo `agentic_code`, pero son de la misma familia y se atacan con el mismo instrumento.

| ID | Hallazgo | Estado |
|---|---|---|
| `FIND-DEFER-1` | El delta de diferidas se reconstruye RE-PARSEANDO el texto rendido; un `\n` en el nombre anuncia una tool inexistente, pierde la real y **el delta no converge nunca** | ✅ **PAGADO** (13ª ventana) — saneado en el INGRESO como A, `remote_name` para el transporte; 6 tests nacidos rojos |
| `FIND-DEFER-2` | Sin cap de descripción de terceros (60 000 ch medidos vs `MAX_MCP_DESCRIPTION_LENGTH = 2048` de A) | ✅ **PAGADO** (14ª ventana) — cap en el constructor de `McpTool`, el único punto que ningún consumidor esquiva; 7 tests nacidos rojos, `INY-65..72` |
| `FIND-AGENT-LIST-1` | Al modelo no le llega **ningún listado de subagentes**; `AgentDefinition.description` es campo muerto y `AgentDefinitionResolver` **no tiene enumeración** | ✅ **PAGADO** (21ª ventana) — enumeración + listado por el loop; `INY-109..119` → 11 rojas |
| `FIND-SKILL9/17` | Al modelo **no le llega ningún listado de skills**. ⚠ **Corrección de premisa**: NO son «dos vías». `SkillTool.getPrompt` no lleva listado y `getSessionSpecificGuidanceSection` sólo lleva una viñeta de guía; A tiene UNA vía real, el attachment `skill_listing` incremental | ✅ **PAGADO** (21ª ventana) — `capabilities/skill_listing_delta.py` + `AgentLoop._announce_skill_listing`, con las 3 ramas de presupuesto y sidecar estructurado; `INY-120..127` |
| `FIND-SKILL-20` | El frontmatter PISA la identidad de la skill (A: siempre el nombre del directorio) | ✅ **PAGADO** (21ª ventana) — identidad ← directorio, `name:` a `display_name`/`user_facing_name`; `INY-131` |
| `FIND-SKILL-21` | Sin dimensión de fuente ni precedencia; `last-wins` donde A tiene `first-wins` por identidad de fichero real | ✅ **PAGADO** (21ª ventana) — `source`/`loaded_from` passthrough opaco, `add_skills` first-wins + dedup por identidad real de fichero; `INY-136`/`INY-137` |
| `FIND-SKILL2` · `FIND-SKILL4` · `FIND-SKILL17` · `FIND-SKILL18` | `when_to_use` fundido con `description` · sin sustitución de argumentos ni variables · `catalog` sin filtro de `disable-model-invocation` · descripción de la tool sin BLOCKING REQUIREMENT | ✅ **PAGADOS** (21ª ventana) — sus `xfail(strict)` se pusieron rojos por **XPASS** al pagarse. ⚠ El de `FIND-SKILL4` **rotulaba `${CLAUDE_SKILL_DIR}` y no lo aseveraba**: retirarlo por XPASS habría acreditado en falso unas variables que B no sustituía en ningún sitio (`H-L4`) — se pagaron también |
| `LAT-SKILL1` | `SkillTool.input_schema` anuncia `args` y la descripción homologada pone un ejemplo con args; `execute()` los **descartaba en silencio**, igual por la vía del slash command. Un `$ARGUMENTS` de una skill escrita para A se quedaba LITERAL, sin error y sin señal. ⚠ **No era latente nuevo: es `FIND-SKILL4`**, que ya estaba abierto — lo abrí por duplicado y se unifican | ✅ **PAGADO** (21ª ventana) — `capabilities/skills/arguments.py` espejo de `argumentSubstitution.ts`; 30 tests; `INY-132..135c`, `INY-138` |
| `FIND-E2G-3` **NUEVO** (21ª ventana) | El `E2g` exige el centinela ENTERO (`PADRON-55B48CEFB2`) en la respuesta. Medida una corrida en la que el modelo alcanzó la tool oculta y respondió **`55B48CEFB2`** — los 10 hex inadivinables, o sea la propiedad bajo prueba SÍ se cumplió— y el caso salió rojo por el prefijo literal, que es decoración. Mismo modo de fallo que el confundidor de la «clave» ya documentado en el fuente: rojo por algo que no es la propiedad. Arreglo indicado, **por atrezo y no por listón** (precedente del propio fichero): centinela de UN solo token sin guion, para que citar «el código» obligue a citarlo entero | ⛔ **abierto, NO pagado y dicho.** Fuera del encargo, y el diagnóstico se apoya en **una** observación: cambiar un gate ajeno con n=1 tiene la forma exacta de bajar el listón. Se nombra con su evidencia para que lo pague quien toque `E2g` |
| `FIND-CODE-SKILL-1` **NUEVO** (21ª ventana, a indicación del usuario) | **El consumidor real no consume NADA de lo que esta ventana pagó.** `agentic_code` tiene CERO referencias a skills y CERO al listado de subagentes: `composition.py:205` construye `CapabilitiesConfig(mcp_config_store=mcp_store)` y deja sin poblar `skill_dirs` y `skill_store` (`factory.py:46,55`), que el runtime ya expone; el REPL no llama a `process_slash_command`, así que `/<skill>` no existe para el usuario; y no hay ninguna raíz de subagentes declarada, luego la enumeración nueva del `AgentDefinitionResolver` no tiene qué enumerar. **No es un fleco de integración: es `L09` aplicado a mi propio trabajo** —cablear ≠ existir— y rompe la premisa del método `D-15`, porque el consumidor es el que DETECTA: sin este cableado, toda la pata de skills y la de subagentes están acreditadas SÓLO con tests del propio sujeto, sin un solo `.jsonl` de operación real que las ejercite. El pago del runtime es correcto y genérico (el encuadre vinculante se respeta: el núcleo no se adapta al integrador); lo que falta es el lado del integrador | ⛔ **abierto, NO pagado.** Lo señaló el usuario al cierre de la ventana; entra en el encargo de la siguiente, POR DELANTE de `FIND-SKILL-22`, porque hasta que exista no hay detector para lo ya pagado |
| `FIND-SKILL-22` **NUEVO** (21ª ventana) | `getPromptForCommand` cierra ejecutando los comandos de shell EMBEBIDOS en el markdown de la skill (`` !`…` ``, `loadSkillsDir.ts:374-396`), con las `allowedTools` de la skill injertadas como reglas de permiso, y **exentando a las de MCP porque son remotas y no confiables**. B no ejecuta nada: el `` !`…` `` se queda literal. No es sólo una capacidad ausente — es una **frontera de confianza** que B no tiene dónde declarar el día que la implemente | ⛔ **abierto, NO pagado y dicho.** Fuera del encargo de la ventana (`L07`: fuera-de-alcance ≠ trocear). Se nombra al descubrirlo, no se difiere en silencio |
| `FIND-STREAM-1` | **Los 5 campos de identidad del evento llegan VACÍOS al `.jsonl`**: `task_id: ""`, `agent_id: ""`, `session_id: ""`, `seq: 0`, `ts: 0.0`. **Ampliado en la 12ª ventana: es UNIVERSAL** (medido en `ToolCallEvent`, `DoneEvent` y `ToolResultEvent`), no sólo el último; ningún sitio de producción de `src/` poblaba identidad. Sin `seq`/`ts` no se ordena ni se fecha una traza, y sin `task_id`/`agent_id` no se separa agente de subagente. Se pagó con el **#10** (mismo seam) | ✅ **PAGADO** (12ª ventana) |
| `FIND-POOL-1` | Sin predicado de enablement por tool (`Tool.isEnabled()`); el integrador ha de negar POR NOMBRE, mezclando política con disponibilidad | ✅ **PAGADO** (18ª ventana) — ver **§ 2 quater**. Absorbe el `FIND-TOOL-ENABLED-1` que abrí por duplicado desde el `E2g`; 13 tests nacidos rojos, `INY-73..80` |
| `FIND-CODE-HITL-1` | `agentic_code` no resuelve ninguna tool de puerta única: el mismo driver headless sirve al REPL y a `--print`, sin detección del `tool_call` ni reinyección de la respuesta | ✅ **PAGADO** (19ª ventana) — `hitl.py` + `repl._resolve_single_door_tools`; `interactive` lo decide el MODO (`not --print`); `INY-94..100` → 7 rojas. Escrito antes que sus tests, dicho |
| `FIND-PLAN-FILE-1` | El plan-file no está cableado: `provider.py:41` ordena escribir en `/plans/plan.md` y `is_session_plan_file` no tiene consumidor fuera de tests en ninguno de los dos repos | ✅ **PAGADO** (19ª ventana) — `storage_contract`, el MISMO objeto en `ctx.fs` y `ctx.storage`; 5 tests nacidos rojos, `INY-81..85` |

**Dos `H-L4` — ✅ SALDADAS (13ª ventana).** `test_deferred_delta.py` se **reescribió** entero: el test que
consagraba el reparseo (`:43-47`) pasó a medir la conducta («la misma tool no se anuncia dos veces») y
el fichero ganó 6 casos adversariales sobre nombres escritos por terceros, más un test que ata el
helper de los tests puros a lo que el loop escribe de verdad —para que el fichero no pueda quedarse
verde midiendo un formato que ya nadie produce—. 15 tests, de 9 que había.

**Orden 2 arrastrado** (hallazgos de ventanas previas, sin tocar): `FIND-READ-1`, `FIND-READ-2`,
`FIND-GLOB-1`, `FIND-CFG-1`, `FIND-LOOP-1`, `FIND-E11-1`, `FIND-C10-1`, `FIND-SEQ-1`, `FIND-E2G-1`,
`FIND-E2G-2`, `FIND-C6-2`.

---

## 4 · Bajo la línea, sin tocar

`A-CIERRE` P4″ 12–18 · ledger 39 abiertos · `O-18`/`R-1b` · `R-6`/`O-16` · `ID-4`/`K3` · `H-3`.
Diferidos nombrados: `SERPER_API_KEY` del entorno vs `ctx.git_credentials` · `ForkSnapshot` no
transporta el confinamiento · `run_argv` no traduce paths DENTRO del argv.

---

## § 4 · CABLEADO PENDIENTE EN `agentic_code` — inventario completo (21ª ventana)

**Por qué este inventario existe.** El usuario fijó como puerta lo que `D-15` ya decía en su paso (3):
lo que se cierra en `agentic_runtime` o `agentic_models` **se cablea en `agentic_code` antes de
declararlo cerrado**, porque una prueba manual real vale más que sólo pruebas sintéticas. Yo lo
incumplí varias ventanas; `FIND-CODE-SKILL-1` era su residuo visible, y este inventario es el residuo
COMPLETO. **Se ataca ENTERO antes de seguir con el resto del TRAMO.**

**Método, para que la lista no sea de memoria:** `composition.py` leído 1→EOF (207 L) y cruzado campo
a campo contra `RuntimeConfig`/`CapabilitiesConfig` (`factory.py:21-160`), más `grep` por nombre de
costura en `agentic_code/src`. **Lo verificado es «la costura viene vacía»** — eso es firme y medido.
Lo que NO está verificado para todos los ítems es si el hueco es DEUDA o **divergencia deliberada**
(`L10`): eso exige abrir cada capacidad, y se marca como tal en vez de darse por hecho.

**Lo que se pobla hoy (12 costuras)** y por tanto NO está en la lista: `model_caller`, `hook_runner`,
`model_id`, `storage`, `scope`, `fs`, `storage_contract`, `exec_env`, `initial_allowed_tools`,
`tools.interactive`, `root_context_modifier`, `capabilities.mcp_config_store`.

### Bloque A — lo que la 21ª pagó y nadie consume (`FIND-CODE-SKILL-1`)

| # | Costura vacía | Qué queda inalcanzable | Evidencia |
|---|---|---|---|
| A1 | `CapabilitiesConfig.skill_dirs` · `skill_store` | El `SkillsProvider` **ni se construye** (`factory.py:222` lo condiciona a uno de los dos). Toda la pata de skills de la 21ª —listado, identidad, precedencia, argumentos, variables— es inalcanzable desde el producto | `composition.py:205` pasa sólo `mcp_config_store`; grep `skill_dirs\|skill_store` en `agentic_code/src` = **0** |
| A2 | `RuntimeConfig.input_processor` (`S11`) | `/<skill>` no existe para el usuario. **Corrijo lo que dije antes:** el sitio no es «que el REPL llame a `process_slash_command`», es esta costura, que el propio contrato designa para «slash-commands resueltos localmente» (`factory.py:91-93`) | grep `input_processor` = **0** |
| A3 | `RuntimeConfig.agent_resolver` | La enumeración de subagentes que se acaba de añadir al `AgentDefinitionResolver` **no tiene qué enumerar**, y `AgentDefinition.description` vuelve a ser campo muerto de facto | grep `agent_resolver` = **0** |

### Bloque B — capacidades de ventanas anteriores, pagadas y sin consumidor

| # | Costura vacía | Qué queda inalcanzable | Clasificación |
|---|---|---|---|
| B1 | `CapabilitiesConfig.memory_root` · `memory_store` | El `MemoryProvider` **no se registra nunca** (`factory.py:227`): el producto no tiene memoria de agente. Es la auto-memoria (memdir), **no** el fichero de proyecto — ése es `FIND-CODE-MEM-1`, § 4 ter, y se paga junto con éste | ❌ deuda, salvo prueba en contra |
| B2 | `mcp_oauth_redirect_handler` · `mcp_oauth_callback_handler` | **Todo server MCP con OAuth es inalcanzable desde el producto.** Y el contrato dice por qué duele aquí: «el runtime headless no abre navegador» (`factory.py:60-62`) — `agentic_code` es justamente quien tiene persona y navegador delante | ❌ deuda |
| B3 | `mcp_config_watcher` | Vector 2 de recarga dinámica muerto. El contrato **NOMBRA a este integrador** como su implementador: «`agentic_code`: inotify» (`factory.py:51-54`). Campo designado por escrito y vacío | ❌ deuda |
| B4 | `task_registry` (`S19`) **+** `root_turn_start_hooks` | Van en PAREJA: sin registry no hay tareas en background, y sin los hooks de turn-start no se drenan sus notificaciones (`factory.py:129-135` lo dice: el consumidor no alcanza el loop, así que las inyecta ahí). Cablear uno solo deja el ciclo a medias | ❌ deuda, y **acoplada** |
| B5 | `model_options` | ✅ **CABLEADO (22ª ventana)** — `--effort` / `--thinking` / `--capture-payloads`, round-trip de razonamiento y presentación del pensamiento. Ver § 4 quater. `temperature`, `max_tokens`, `metadata` los transporta el puente y **nadie los pide**: declarados, no cableados. `tool_choice` y `output_format` **no tienen representación** en agentic_models 0.2.0 y el puente los rechaza | ✅ pagado, con residuo declarado |
| B6 | `presentation` (`PathPresentation`) | Sin presentación de paths inyectada, el default identidad — a verificar contra qué hace A al citar rutas al modelo | 🟡 abrir antes de rotular |
| B7 | `git_credentials` | `clone_repository` sin auth. **Ya estaba nombrado como diferido** en ventanas anteriores (`SERPER_API_KEY` del entorno vs `ctx.git_credentials`) | ❌ deuda, ya nombrada |
| B8 | `small_llm` | Sin modelo pequeño inyectado; a determinar qué lo consume en el runtime | 🟡 abrir antes de rotular |
| B9 | `voice` (`stt` / `tts`) | Sin I/O por voz | 🟡 **candidato a divergencia deliberada** (`L10`) para un producto de terminal — se decide y se ESCRIBE, no se deja en blanco |

### Lo que NO es deuda, y se dice para que nadie lo cuente como hueco

`session_repo` (opcional por diseño: el runtime usa su `Session` nativa), `subagent_runner_factory`
(`None` = `LocalSubagentRunner`, que es el default correcto — y su comentario recuerda que ahí vivió
`FIND-EXEC1`), `notification_sink` (`None` = canal en-proceso), `skill_catalog`,
`resolve_timeout_seconds`, `background_result_max_chars`, `extra_providers`. **Siete costuras vacías
A PROPÓSITO**, con default correcto.

### § 4 bis · Pre-encargo de la 22ª — el server MCP `obsidian` daba error ✅ PAGADO

Sin esto no hay detector `D-15` para NINGUNA superficie MCP, así que va por delante del bloque.

**Lo que era, medido y no supuesto:** `httpx.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED]
self-signed certificate` contra `https://127.0.0.1:5583/mcp/` (plugin Local REST API de Obsidian,
cert autofirmado). Pagado en TRES piezas, dos de ellas defectos del runtime que su suite no veía:

1. **Material de confianza TLS ausente por completo** → `agentic_runtime/tls.py` nuevo, homólogo de
   `utils/caCerts.ts`. La diferencia que dicta el diseño y que el canónico escribe: `NODE_EXTRA_CA_CERTS`
   **añade**, mientras `SSL_CERT_FILE`/`SSL_CERT_DIR` de Python **reemplazan** el almacén — de ahí que
   `default_ssl_context()` construya sobre la base (`httpx.create_ssl_context`) y **sume** la CA extra,
   igual que el comentario de A («setting `ca` … replaces the default certificate store, so we must
   always include base CAs»). Cableado a TODA la salida TLS del runtime: MCP http, MCP sse, `WebFetch`
   y `WebSearch`. El *sourcing* de la ruta se queda FUERA del runtime a propósito, exactamente como A
   lo parte entre `caCerts.ts` (sólo `process.env`) y `caCertsConfig.ts` (importado sólo por `init.ts`).
2. **`FIND-MCP-HTTPX-FLAVOR-1`** — el cliente HTTP se construía con el `httpx` del entorno, no con el
   del SDK. En `mcp` 2.x el SDK usa `httpx2` y sólo su `AsyncClient` tiene `.sse`; el módulo se lee
   ahora del propio SDK (`_sdk_httpx()`), no se supone.
3. **`FIND-MCP-TIMEOUT-1`** — el timeout iba PLANO al transporte, con lo que el `read` cortaba el GET
   servidor→cliente del canal SSE. Ahora `Timeout(request, read=SSE_READ_TIMEOUT_SECONDS)`.

**Corrección de premisa MÍA, y la cazó `mypy`:** yo había afirmado que `mcp 1.27.2` no tenía el
parámetro `http_client` y que en el rango declarado convivían DOS firmas, y monté una bifurcación por
`inspect.signature`. Descargado `mcp==1.26.0` (el suelo declarado) se ve que `streamable_http_client`
YA lo tiene ahí; la firma vieja (`headers=`/`timeout=`/`auth=`) es de `streamablehttp_client` **sin
guion bajo**, que es otra función y está DEPRECADA. La bifurcación era código muerto en TODO el rango
⇒ eliminada junto con su test, que acreditaba una rama inexistente.

**`FIND-CODE-MCP-ALLOW-1` (integrador)** — `cli.py::_tool_names` DESCARTABA lo que no estuviera en el
censo de nativas. Como las tools MCP se descubren mucho después de parsear la línea de comandos, eso
dejaba **toda** la superficie MCP fuera de `--allowed-tool`, o sea inalcanzable en `--print`, que es
headless. El canónico no valida nada ahí: `parseToolListFromCLI` (`permissionSetup.ts:813-860`) sólo
trocea respetando paréntesis, y `mcp__server__tool` es forma esperada. Ahora se ACEPTA y se avisa.
`INY-156..158` → **3 rojas**.

**Hipótesis MÍA REFUTADA por medición, y se dice porque llegó a escribirse en el fuente.** Había
declarado un síntoma —«con `--allowed-tool` o con `--dangerously-skip-permissions` las tools MCP
desaparecen del pool»— a partir de la conducta del modelo. Medido con un espía en la costura
`complete`, el array de tools que llega al modelo es **IDÉNTICO en los tres casos** (24 tools; las MCP
en ninguno) y `vault_list` viaja por la vía DIFERIDA, en los mensajes, no en el array. Lo que variaba
era el MODELO, que unas veces hace `ToolSearch` y otras contesta «no tengo tool». La deferencia es
**fiel a A**, que lo dicta sin condición: *«MCP tools are always deferred (workflow-specific)»*
(`ToolSearchTool/prompt.ts:67-68`). En consecuencia, `FIND-RT-SEED-1` **pierde su evidencia**: el
`ctx` de `_prepare_context` nace con el `PermissionContext` por defecto vacío, así que sumar y
sustituir dan lo mismo. Se conserva el cambio por ser la primitiva correcta y **se declara NO
acreditado** en el propio fuente, en vez de dejar en pie un comentario que afirmaba una medición falsa.

**Abierto, NOMBRADO y no pagado (`L07`) — `FIND-MCP-ALWAYSLOAD-1`:** el canónico comprueba
`tool.alwaysLoad === true` **antes** que `isMcp` (`prompt.ts:63-68`), o sea que un server puede pedir
por `_meta['anthropic/alwaysLoad']` que su tool salga con esquema completo en el prompt inicial. B lee
ese `_meta` —lo tiene cargado en `client.py:242`— pero **sólo consume la clave del `searchHint`**. Es
otra vez el patrón del barrido EOF: el dato está y no llega a ninguna lista que el modelo vea.

**Abierto, NOMBRADO y no pagado — `FIND-MCP-NAME-1`, y lo destapó la traza real:** el anuncio de
diferidas que recibe el modelo lista `vault_list`, `search_query`, `open_file`… **sin prefijo de
server**. A compone `buildMcpToolName(client.name, tool.name)` → `mcp__<server>__<tool>` y sólo usa el
nombre desnudo en un caso estrechísimo (server de tipo `sdk` **y** `CLAUDE_AGENT_SDK_MCP_NO_PREFIX`,
`client.ts:1760-1773`); B llama a `normalize_mcp_tool_name(name)` a secas (`tool_adapter.py:187`). No
es cosmético y tiene tres consecuencias medibles: dos servers que publiquen `search` COLISIONAN entre
sí y contra las nativas (y el dedup de `assemble_tool_pool` es «native wins», así que la MCP
desaparece en silencio); `--allowed-tool mcp__obsidian__vault_list` —la forma que el canónico
documenta como esperada en `parseToolListFromCLI`— no casa con nada; y la comprobación de permisos
pierde el eje de servidor que A conserva aparte en `mcpInfo`. Se nombra y no se toca aquí: cambiar la
identidad de las tools MCP mueve pool, permisos y aprobaciones a la vez.

**Lo que NO se pudo cerrar con `.jsonl` y se dice en vez de rotularlo verde:** con el server ya
CONECTADO (15 tools, `vault_list` devolviendo el vault real por llamada directa), el modelo del
producto —Azure OpenAI responses— **no llega a llamar a `ToolSearch`** ni con instrucción explícita de
dos pasos; responde «no ejecutable» sin emitir una sola tool call (traza `20260808T*`, `DoneEvent` con
`stop_reason: stop` y cero `ToolCallEvent`). El pool, el anuncio de diferidas y el despacho están
medidos y correctos, así que esto es solvencia del MODELO y no defecto del sujeto — el mismo reparto
que `D-14` fijó para `E11`. Queda como carencia declarada del cierre `D-15` de esta pieza: la ruta
MCP está acreditada por medición directa, no por una traza en la que el modelo la use.

### Criterio de cierre del bloque

No es que compile ni que la suite siga verde: **es el `.jsonl` de sesión real** (`D-15`, paso 4). Un
cableado que no se puede ver operar en una traza no ha cerrado el ciclo, lo ha dejado en tres pasos.
Y el encuadre no se toca: se adapta el INTEGRADOR al núcleo, nunca al revés.

### § 4 ter · `FIND-CODE-MEM-1` — el fichero de memoria de proyecto (`AGENT.md`) ❌ ABIERTO, DIFERIDO

**Encargo del usuario, 22ª ventana, y su origen:** entró por un hallazgo lateral de la homologación
del system prompt. Al auditar frase a frase contra el canónico apareció que A dice «durable
instructions like **CLAUDE.md** files» (`prompts.ts:258`) y yo había cortado en «durable
instructions», porque `agentic_code` no tiene fichero de memoria. El usuario levantó que ese fichero
**es parte de la homologación** y que para este producto se llama **`AGENT.md`**, no `CLAUDE.md`.
Decisión suya al ver el alcance: **se documenta ahora y se implementa después del congelamiento del
TRAMO, cuando concluyan las pruebas de `agentic_code`.** No se toca código en esta ventana.

**La premisa con la que se abrió el tema era MÍA y era incorrecta.** Yo lo trataba como «una sección
más del system prompt». No lo es, y eso cambia dónde se paga:

| | Subsistema 1 — ficheros de memoria | Subsistema 2 — auto-memoria / memdir |
|---|---|---|
| Fuente en A | `utils/claudemd.ts` (1479 L) | `utils/memdir/` |
| Unidad | `CLAUDE.md` por directorio | un hecho por fichero + índice `MEMORY.md` |
| Cómo llega al modelo | **mensaje de usuario sintético** `isMeta: true` en `<system-reminder>`, antepuesto (`prependUserContext`, `utils/api.ts:449-473`) | sección del system prompt |
| Estado en el runtime | **NO EXISTE** | existe: `capabilities/memory/` |
| Estado en `agentic_code` | no existe | existe pero **sin cablear** (= `B1`) |

Lo que dicta A, leído (`claudemd.ts:1-25`, su propia cabecera):

- **Cuatro tipos en orden de carga**, de menor a mayor prioridad: managed (`/etc/claude-code/CLAUDE.md`)
  → user (`~/.claude/CLAUDE.md`) → project (`CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md`)
  → local (`CLAUDE.local.md`). *«Files are loaded in reverse order of priority»* — el último pesa más.
- **Descubrimiento caminando de cwd hacia la raíz**; más cerca del cwd ⇒ más prioridad.
- **Directiva `@include`**: `@path`, `@./rel`, `@~/home`, `@/abs`; sólo en nodos de texto hoja (no
  dentro de bloques de código), ciclos prevenidos, inexistentes ignorados en silencio.
- Cabecera fija al inyectar (`claudemd.ts:88-89`): *«Codebase and user instructions are shown below.
  Be sure to adhere to these instructions. IMPORTANT: These instructions OVERRIDE any default
  behavior and you MUST follow them exactly as written.»* Cada fichero se rinde como
  `Contents of <path> (<descripción por tipo>):` (`getClaudeMds`, `:1153-1195`).
- `MAX_MEMORY_CHARACTER_COUNT = 40000` (`:92`), recomendado, no duro.

**Dos consecuencias que NO son obvias y hay que respetar al pagarlo:**

1. **Sobrevive a `--system-prompt`.** En `queryContext.ts:61-72`, con `customSystemPrompt` definido el
   prompt por defecto se vacía pero **`getUserContext()` se sigue cargando**. Si esto se implementara
   como sección del prompt, un `--system-prompt` borraría la memoria del proyecto — divergencia
   silenciosa. Es meta-mensaje justamente por eso.
2. **Queda FUERA del prefijo cacheable**, a diferencia del memdir. Colocarlo en el bloque estático
   metería contenido volátil por proyecto en el prefijo (`prompts.ts:343-350`).

**Reparto, por el encuadre vinculante (núcleo genérico, el integrador se adapta):** el cargador va al
**runtime** —descubrimiento, jerarquía, orden, cap, e inyección como meta-mensaje— parametrizado por
**nombre(s) de fichero**; `agentic_code` declara `AGENT.md`. Codificar el nombre en el núcleo
obligaría al siguiente integrador a parchear el runtime, que es exactamente lo que `D-16` prohíbe.

**Deuda colateral que se cierra con esto:** `system_prompt.py` corta hoy en «durable instructions» y
lo declara en su docstring; al aterrizar `AGENT.md` la frase vuelve al literal de A con el nombre
sustituido, y la entrada correspondiente sale de `_ADAPTACIONES_DECLARADAS` en
`tests/test_system_prompt.py`. Lo mismo con `B1`: el encargo natural es cablear las **dos** memorias
en el mismo punto de composición, porque el memdir lleva ventanas pagado y sin consumidor real
(`FIND-CODE-SKILL-1` otra vez: cablear ≠ existir).

**Alcance a decidir cuando se retome** (se ofrecieron tres y el usuario difirió la elección): núcleo
(jerarquía + inyección) · núcleo + `@include` + cap · homologación completa de `claudemd.ts`
(reglas condicionales por glob, excludes, cachés, includes externos) — esta última es TRAMO propio,
no paso previo a probar.

---

### § 4 quater · `B5` — `model_options` cableado, y los tres cortes que había debajo (22ª ventana)

**Encargo del usuario, literal:** *«quiero que la implementación active las capacidades que hoy
no están conectadas y si el portado de PI no lo contenía implementes lo que falte para usar los
modos thinking y effort»*, más *«implementa hooks extras para que puedas capturar evidencias»* y
*«que ese hook pueda llevar por stream contenidos que sirvan para que el CLI… pueda mostrar estos
"pensamientos" junto con los spinners»*. El plan mínimo que yo había anunciado —cablear `--effort`
y declarar el resto— fue **rechazado por insuficiente**, y con razón: la costura estaba entera y
vacía, y llenarla sin mirar debajo habría dejado los tres cortes intactos.

**Lo que había debajo.** Tres hallazgos, uno por capa, todos con la misma forma —el parámetro
viaja, se acepta y se descarta **callando**—: `FIND-MODELS-BUDGET-1`, `FIND-MODELS-OFF-1` y
`FIND-RT-REASON-1`. El criterio con que se resuelven es `D-21`. Corrección de mi propio encuadre
inicial: supuse que el round-trip faltaba en `agentic_models`; leer
`openai_responses_shared.py:130-137` y `:368-379` probó que **PI lo implementa entero** y que los
tres cortes estaban en el runtime.

**Inyecciones.**

| Capa | Qué se inyectó |
|---|---|
| `agentic_models` | `supports_thinking_budget(model)` — sonda de proveedor: qué APIs leen de verdad `thinking_budgets`. Conocimiento de proveedor, en la capa de proveedor (`C2`) |
| `agentic_runtime` | `ThinkingEvent` en el bus (contenido, firma, `final`, `model_id`); traducción de `effort`/`thinking` a `reasoning` con rechazo explícito de lo inexpresable; round-trip del razonamiento al rearmar el contexto, **filtrado por modelo**; persistencia de los bloques cerrados en el `AgentLoop`, colgados de un mensaje que ya existe |
| `agentic_code` | `--effort` (5 niveles) · `--thinking`/`--no-thinking` · `--capture-payloads`; `build_model_options`; `PayloadRecorder` sobre los hooks `on_payload`/`on_response` del motor; `ThinkingBlock` en el transcript y su widget; eco atenuado en `--print`; **el pensamiento en vivo junto al indicador de trabajo** de la barra de estado |

**Por qué hizo falta el grabador de payload.** El capture ordinario registra **eventos del
runtime** —lo que el motor devuelve—, no lo que se le pidió. Sin `PayloadRecorder`, «`--effort
high` viajó» es una afirmación sin prueba: una opción descartada por el camino produce
exactamente el mismo `.jsonl` que una que llegó. El grabador anota el `reasoning` real, el
`include`, y `reasoning_items_sent` —la cuenta de items de razonamiento devueltos—, que es la
**única prueba directa** del round-trip. Por defecto sólo la cabecera; el cuerpo entero con
`AGENTIC_CODE_CAPTURE_PAYLOADS_FULL` (el system prompt y la conversación ya están capturados y
duplicarlos multiplica el fichero por turno). Ninguno de los dos lleva la clave.

**Acreditación.** `test_model_options_reasoning.py` (13, runtime) + `test_reasoning_surface.py`
(16, integrador), verdes. Suites completas sin regresión: las 4 caídas de `agentic_code` y las de
`agentic_runtime` se verificaron **presentes en HEAD** extrayendo los tres repos con `git archive`
a un scratch y ejecutando con `PYTHONPATH` propio, con `__file__` comprobado — deuda cero neta por
diff. Al hacerlo salió un hallazgo de entorno: `agentic_runtime/.venv` tenía `agentic_models` como
copia congelada en `site-packages`, no editable; la suite del runtime llevaba midiendo contra una
copia vieja del proveedor. Reinstalado editable.

**Residuo declarado, no rotulado** (`declarar-no-es-pagar`): `temperature`, `max_tokens` y
`metadata` los transporta el puente y **nadie los pide** — una palanca que nadie mueve es
superficie sin conducta, y se cablearán cuando haya quien las mueva. `tool_choice` y
`output_format` **no tienen representación** en agentic_models 0.2.0 y el puente los rechaza por
`D-21`. **Criterio de cierre pendiente:** `D-15` — un `.jsonl` de sesión real con
`--capture-payloads` que muestre el `reasoning` que salió y `reasoning_items_sent > 0` en el
segundo request de un turno con tool calls.

### § 4 quinquies · El terminal del bucle, cableado en `agentic_code` (`D-65`, 2026-08-30)

`cablear-en-agentic-code-al-cerrar`: `FIND-RT-MAXTURNS-1` no se declara cerrado en el runtime sin
que el consumidor lo vea. Lo que se pobló, capa a capa:

| capa | fichero | qué consume |
|---|---|---|
| stream | `streaming.py` | `StreamSnapshot.end_reason` / `max_turns` / `turn_count`, reducidos desde `MaxTurnsEvent` |
| captura | `capture.py` | el adjunto canónico `{type:'max_turns_reached', maxTurns, turnCount}` y el `subtype` `error_max_turns` de la línea `result`, con `status: "completed"` |
| transcript | `transcript.py` | `MaxTurnsBlock`, espejo de `CompactionBlock`: cierra lo que estuviera en vuelo y no fabrica turno |
| render | `rendering.py` | la fila por `stderr`, nunca por `stdout` (lo que se canaliza es la respuesta) |
| TUI | `tui.py` | `MaxTurnsBlockWidget`, con el color de aviso del tema |

**El techo no necesitó superficie nueva:** `--max-turns` ya existía en `Settings` con default `None`
y validación `>= 1`; lo que faltaba era que `None` significara lo que dice.

---

## 2 septies · Observación E2E en vivo contra el modelo local (2026-08-29/30) — cinco cortes

**Método.** Sesión real de `agentic_code` contra `llama-server` + `unsloth/Qwen3.8-27B-GGUF:UD-IQ4_XS`,
`--provider local --capture-payloads`, encargo de escritura de módulos sobre `../prueba_agentic_code`.
Evidencia primaria: la captura de la sesión, 11,3 MB, en
`~/.local/state/agentic-code/streams/project-164ebd47edba77e91b212706/session-8b30548d-a246-442a-b609-5d06ffcbe2cf/20260829T210441-fde2e05cb186.jsonl`
— 17.124 registros, `{ThinkingEvent: 15866, TokenEvent: 860, ToolCallEvent: 67, ToolResultEvent: 67,
MessageEvent: 56, TurnStartEvent: 50, DoneEvent: 50, CompactionEvent: 2}`.

La captura escribe con `os.open`/`os.write`/`os.close` **por registro** (`capture.py:111-135`): nada
se bufferiza, luego un `kill -9` no pierde evidencia. Esto queda dicho porque en la ventana anterior
yo había advertido lo contrario.

---

### `FIND-RT-MAXTURNS-1` — el tope de vueltas para en seco, calla, y se registra como éxito ✅ **PAGADO** (`D-65`, 2026-08-30)

**Síntoma que reportó el usuario:** la sesión «se rompió» tras la segunda compactación, con el
indicador de trabajo colgado. El último texto del modelo fue coherente y anunciaba su siguiente
acción: *«scheduler.py was never created. Let me read the existing modules to get exact APIs before
writing the remaining pieces»*, tras leer cuatro ficheros dos veces.

**No hubo cuelgue.** El turno terminó. Terminó mintiendo.

Cadena, entera en fuente:

1. `agent_loop.py:373` — `for _turn in range(self._max_turns)` agota las 50 vueltas. La captura lo
   confirma con **50 `TurnStartEvent` y 50 `DoneEvent`** exactos.
2. `agent_loop.py:601-604` — sale por el `else` del `for`: `reason = LoopEndReason.MAX_TURNS`,
   `detail = "50"`, y **un `logger.warning`**, invisible en una TUI.
3. `execution/local/runtime.py:384` — `await loop.run(prompt, ctx)`: **el `LoopOutcome` se descarta**.
   Ni se asigna a una variable.
4. `runtime.py:407` — `self._task_registry.complete(...)` sin condición ⇒ `TaskStatus.COMPLETED`.
5. `runtime.py:403` + `:42-46` — `_last_assistant_text` devuelve `""`: el último mensaje de asistente
   sólo llevaba `tool_calls`.
6. `capture.py:90` — `subtype = "success"`. Y así está escrito en el registro `result` de la captura:
   `subtype=success status=completed stop=tool_calls anomalies=[]`.

Que ese registro exista **prueba que `driver.py:92-93` se ejecutó**: el turno se cerró de verdad y
`finish_turn` se pintó. El indicador colgado es un pie de página rancio, no un turno vivo. El daño
real es el otro: el agente se detuvo a mitad del trabajo, con cuatro resultados de herramienta
recién en la mano, sin decir nada.

**Contraste con A (`D-08`), `query.ts:1704-1712`:**

```ts
if (maxTurns && nextTurnCount > maxTurns) {
  yield createAttachmentMessage({ type: 'max_turns_reached', maxTurns, turnCount: nextTurnCount })
  return { reason: 'max_turns', turnCount: nextTurnCount }
}
```

Dos divergencias, y las dos condenan:

- **A avisa.** `yield` al mismo stream por el que viaja todo lo demás; el consumidor lo pinta. Lo
  repite en la rama de aborto (`:1506-1514`). B escribe a un logger que nadie lee.
- **A no impone tope.** `maxTurns?: number` (`:191`) y toda comprobación guardada por
  `if (maxTurns && …)`: sin valor, sin límite. B fuerza 50 siempre que `max_turns is None`, que es el
  defecto en toda la cadena: `agentic_code/settings.py:37` → `driver.py:61-68` →
  `contracts/runtime.py:23` → `agent_loop.py:153` (`else _MAX_TURNS`, `:74` = 50).

**Es la quinta vez que aparece la misma forma:** la capa de abajo calcula el material y no cruza al
consumidor. Aquí es literal — existe `loop/outcome.py` con el código `MAX_TURNS = "max_turns"`
anotado `# query.ts:1711`, un `detail`, y un docstring que dice que esa información «es la que
permite al integrador decidir si reintenta, si avisa, o si cierra». La línea que la recibe la tira.

**Inyección ejecutada (`D-65`), los cuatro puntos:**

| | dónde | qué se hizo |
|---|---|---|
| a | `execution/local/runtime.py:384` | el `LoopOutcome` se recoge y viaja al `TaskRecord`, que gana `end_reason` / `end_detail` |
| b | `agent_loop.py` | el `logger.warning` muere; la guarda del tope **emite `MaxTurnsEvent(max_turns, turn_count)` al bus** antes de romper, y el aviso llega hasta la TUI |
| c | `agent_loop.py:74`/`:153` | `_MAX_TURNS = 50` borrado; `self._max_turns = max_turns` a secas ⇒ `None` = sin límite, como A. El techo se pide con `--max-turns`, que ya existía en `Settings` |
| d | registro | **`TaskStatus.COMPLETED` se conserva**: el ciclo de vida no cambia porque la tarea no falló. El terminal viaja como DATO (`end_reason`, `MaxTurnsEvent`) y lo rotula el consumidor — `agentic_code` marca su línea `result` como `error_max_turns`, homólogo de `SDKResultErrorSchema` |

**Acreditación:** 7 casos en `agentic_code/tests/test_max_turns_wire.py`; 4 inyecciones → 4 rojas, 0
falsos positivos (INY-b enrojece **tres** capas, que es lo que acredita el cableado). `agentic_code`
286 → **293 passed**. Detalle completo en `DECISIONES.md · D-65`, con las dos divergencias declaradas
—aquí el aviso se pinta y en A es `NULL_RENDERING`; el `yield` de la rama de aborto no se porta—.

---

### La cola detrás, por orden (síntomas verificados en vivo; **citas por reverificar al abordarlas**)

- **`FIND-CODE-ESC-1`** — cancelación por ESC. Inyección de 5 puntos ya anunciada en ventana anterior.
- **`FIND-RT-COMPACT-EVT-1`** — la compactación no tiene evento de INICIO: la captura trae dos
  `CompactionEvent`, ambos de cierre. Durante la compactación la interfaz no dice nada, y ese silencio
  es lo que el usuario leyó como rotura.
- **`FIND-RT-TOOLINPUT-1`** — el input de herramienta no llega en stream. `caller.py:278-299` traduce
  `text_delta`/`thinking_delta`/`toolcall_end`/`done`/`error` y **descarta `toolcall_start` y
  `toolcall_delta`**. Consecuencia visible arriba: `streaming.py:166` fija `StreamMode.TOOL_INPUT`
  sólo al recibir la llamada **ya completa**, luego ese modo no describe nunca lo que nombra. La
  evidencia está asegurada: 67 `ToolCallEvent` en la captura y **cero** eventos de input parcial.
- **`FIND-CODE-TODO-1`** — TodoWrite. Antes de tocar su punto (c), **verificar si
  `RuntimeContextForker` comparte `app_state`**.

**Pendiente instrumental no resuelto:** `py-spy dump --pid <tui>` sigue sin poder ejecutarse
(`ptrace_scope=1`, `sudo` pide contraseña). Era lo único que explicaría del todo el pie de página
persistente; con la cadena de arriba probada, ha dejado de ser bloqueante.
