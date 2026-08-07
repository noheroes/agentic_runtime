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

## 3 · Cosecha del barrido EOF (10ª ventana) — entra en la misma cola

Hallazgos del barrido del canónico sobre las LISTAS de tools (nativas, MCP diferidas, skills). No los
produjo `agentic_code`, pero son de la misma familia y se atacan con el mismo instrumento.

| ID | Hallazgo | Estado |
|---|---|---|
| `FIND-DEFER-1` | El delta de diferidas se reconstruye RE-PARSEANDO el texto rendido; un `\n` en el nombre anuncia una tool inexistente, pierde la real y **el delta no converge nunca** | ✅ **PAGADO** (13ª ventana) — saneado en el INGRESO como A, `remote_name` para el transporte; 6 tests nacidos rojos |
| `FIND-DEFER-2` | Sin cap de descripción de terceros (60 000 ch medidos vs `MAX_MCP_DESCRIPTION_LENGTH = 2048` de A) | ✅ **PAGADO** (14ª ventana) — cap en el constructor de `McpTool`, el único punto que ningún consumidor esquiva; 7 tests nacidos rojos, `INY-65..72` |
| `FIND-AGENT-LIST-1` | Al modelo no le llega **ningún listado de subagentes**; `AgentDefinition.description` es campo muerto y `AgentDefinitionResolver` **no tiene enumeración** | ⛔ abierto |
| `FIND-SKILL9/17` | Reclasificado: al modelo **no le llega ningún listado de skills**, por ninguna de las **dos** vías de A (description de `Skill` + attachment `skill_listing` incremental) | ⛔ abierto — **primero de la pata de skills** |
| `FIND-SKILL-20` | El frontmatter PISA la identidad de la skill (A: siempre el nombre del directorio) | ⛔ abierto |
| `FIND-SKILL-21` | Sin dimensión de fuente ni precedencia; `last-wins` donde A tiene `first-wins` por identidad de fichero real | ⛔ abierto |
| `FIND-STREAM-1` | **Los 5 campos de identidad del evento llegan VACÍOS al `.jsonl`**: `task_id: ""`, `agent_id: ""`, `session_id: ""`, `seq: 0`, `ts: 0.0`. **Ampliado en la 12ª ventana: es UNIVERSAL** (medido en `ToolCallEvent`, `DoneEvent` y `ToolResultEvent`), no sólo el último; ningún sitio de producción de `src/` poblaba identidad. Sin `seq`/`ts` no se ordena ni se fecha una traza, y sin `task_id`/`agent_id` no se separa agente de subagente. Se pagó con el **#10** (mismo seam) | ✅ **PAGADO** (12ª ventana) |
| `FIND-POOL-1` | Sin predicado de enablement por tool (`Tool.isEnabled()`); el integrador ha de negar POR NOMBRE, mezclando política con disponibilidad | ⛔ abierto |

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
