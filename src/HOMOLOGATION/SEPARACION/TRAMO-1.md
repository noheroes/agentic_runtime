# TRAMO 1 — guion de refactorización de `agentic_runtime` (Fase B, primer tramo)

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/TRAMO-1.md`.
> **Naturaleza: artefacto de ESTADO + guion ejecutable (`D-09`).** Una línea por capacidad. El log del tramo
> va a `PROGRESS.md` y a `EVIDENCIA.log`, **nunca aquí**.
>
> **Qué decide este documento:** qué capacidades se refactorizan AHORA, dónde está la **LÍNEA DE CORTE**, y
> qué prueba E2E real cierra el tramo. Lo que queda por encima de la línea es el **nuevo top** del trabajo
> restante y se reconcilia después, en tramos cortos.
>
> **Lecturas que lo sostienen (1→EOF en la ventana que lo escribió, 2026-07-30):** las 12 lecciones (547 L,
> `EVIDENCIA.log:255`) · `SEAMS.md` (607) · `00-BLUEPRINT.md` (229) · `SKELETON-REPORT.md` (138) ·
> `PLAN.md` (111) · `DECISIONES.md` (261) · `models/protocol.py:17,33` (verificación puntual de C2).

---

## 0. El criterio de corte, dicho antes que la lista

La línea **no** se traza por número de ciclo (`NN`) ni por porcentaje de avance. Se traza por **grado
probatorio**, porque es lo único que el corpus discrimina de forma mecánica:

| grado | qué es | reaperturas registradas |
|---|---|---|
| **G1 — validado CORRIENDO** | las 12 costuras que el walking skeleton A2 ejerció con turnos reales (`SKELETON-REPORT §1`) | **cero** en 255 entradas de `EVIDENCIA.log`. Cuando skeleton y documento discreparon, **el documento se corrigió** (`ForkContext→SubagentSpec`, singleton→DI, `05·LAT-EXEC1` incorrecto) |
| **G2 — leído 1→EOF en la ventana que lo escribió** | mecanismos `existe-fiel` acreditados abriendo la fuente (`09·G1-G8`, `05` façade, `07·A1-A4`) | bajas y siempre por lectura, no por razonamiento |
| **G3 — inferido, heredado, o resuelto por `grep`/tramos** | todo lo demás | **es exactamente el conjunto que se ha reabierto**: `R-1` (4 de 11 entradas BORRAR habrían destruido código vivo), `CG-MCP-21`, `CAT-h10`, `05·LAT-EXEC1`, `08·S12` |

**Regla del tramo 1: entra G1, entra G2 marcado como tal, no entra G3.** Una capacidad G2 dentro del tramo
declara su grado en su ficha y **la E2E del tramo es lo que la promueve a G1** — ese es el propósito del gate,
no un trámite.

**Y una excepción razonada, la única:** entra una capacidad G3 —**C9, el hilo de identidad**— porque es la
única transversal cuyo aplazamiento **encarece el resto de forma no lineal** (§4·riesgo 3).

---

## 1. Alcance del tramo 1, en una frase

> **Un turno agéntico real, padre → subagente, corriendo sobre costuras exteriorizadas, con identidad opaca
> y un único punto de composición.**

Eso es *exactamente* lo que el walking skeleton A2 ya demostró que aguanta. El tramo 1 no inventa: **promueve
el skeleton a runtime**, sustituyendo la mímica por el diseño de Filosofía B.

Fuera del tramo queda toda **política** (permisos, hooks, modos), toda **estrategia** (las batteries) y todo
**subsistema de capability** (mcp, skills, memoria, plan, voz, storage rico). Ninguno se trocea: se difieren
**enteros y nombrados** (§3), como exige `L07`.

---

## 2. Las 10 capacidades del tramo, con los 6 campos de `L05`

> `comportamiento · costura · firma · cableado · orden · prueba`. Sin los 6 campos no es guion, es lista de
> deseos (`L05`, modo de fallo: *«ajuste: portar Y»*).

### C1 · Contratos T1 del turno — paquete `contracts` 【G2】 · **estado 2026-07-31: 🟢 implementada y corrida** (prueba con violación inyectada; su promoción formal la firma `E1`/`E8`)
- **comportamiento:** existe un paquete de shapes invariantes que **no importa nada del base**; reimplementarlos forkea el ecosistema.
- **costura:** ninguna — *es* T1. Fuente: `00-BLUEPRINT §1.1`.
- **firma:** `RuntimeTask` (prompt/description/subagent_type/model_override/fork_context/max_turns/timeout_seconds/audio_prompt; `owner_id`/`session_id` **opacos**) · `Event` base **con campos de identidad** (`task_id`/`agent_id`/`session_id`/`seq`/`ts`) + los 5 subtipos · `Usage` **único** (unificar los dos divergentes, `07·E4`) · `ToolProtocol`/`ToolResult`/`ToolCategory` mínimos · `PermissionContext` **con `mode`** (`GAP-02`) · `AgentDefinition` con los campos de ejecución (`05·E28`).
- **cableado:** nadie. Es la hoja del grafo de dependencias; todo lo demás la importa.
- **orden:** **primero**. Bloquea C2..C10.
- **prueba:** `mypy --strict` sobre el paquete + test que importe `contracts` con el base **ausente del path** (si falla, el contrato no es invariante).
- **⚠ decisión declarada:** `Event` lleva **campos de identidad en la base**, **NO** `EventEnvelope` — `bus.py:40` despacha por `type(event)` y envolver rompe el despacho tipado (`A3.DB §7.2`, forma vigente de **K4**). `PermissionContext.mode` se **define** aquí y su motor queda fuera (§3); mientras tanto el default es `default`, **nunca** `bypass`.

### C2 · S1 model-caller enriquecida + S2 `AbortSignal` 【G1】
- **comportamiento:** el base pide al motor todo lo que el motor sabe hacer, y **puede abortar de verdad**.
- **costura:** `S1` `ModelCallerProtocol` (T1-MOTOR, *la costura central*) + `S2` `AbortSignal`.
- **firma:** la de `SEAMS §S1` (añade `thinking`/`effort`/`temperature`/`max_tokens`/`output_format`/`tool_choice`/`metadata`) + `supports_native_tool_search()`. `stop: AbortSignal` con `.aborted`/`.reason()`, **no `asyncio.Event`**.
- **cableado:** `AgentLoop.run` → `complete()` (`agent_loop.py:235`); el bridge `AgenticModelsCaller` traduce. Punto de composición: `factory` (`model_caller=config.model_caller`) — el slot `ModelsConfig` es **muerto** (`LAT-MODELS1`), se retira.
- **orden:** tras C1. Bloquea C4.
- **prueba:** **turno real texto-solo** con `on_payload` verificando qué llega al cable (ya corrido en A2.2) + test de que `stop.aborted=True` **corta el stream**.
- **⚠ defecto verificado en esta ventana:** `models/protocol.py:17` y `:33` tipan `stop: Optional[asyncio.Event]` y los providers consultan `getattr(signal,"aborted",False)` ⇒ **el abort se ignora silenciosamente hoy**. Es un cambio de **tipo del contrato**: por eso vive en el tramo 1 y no puede diferirse.
- **⚠ límite honesto:** `thinking`/`effort`/`tool_choice` **no** son passthrough — los **traduce el bridge** (`stream_simple(reasoning=…)`); `Usage` no lleva `thinking_tokens`. Corregido en A2.2 corriendo, no supuesto.
- **estado 2026-07-31: ✅ acreditada por `E1`+`E5` corriendo** — defecto `protocol.py:17,33` pagado (`AbortSignal` en toda la cadena + `AbortController` concreto), `S1` enriquecida y **poblada** vía `RuntimeConfig.model_options`, `ModelsConfig` retirado; medido en la wheel: `tool_choice`/`output_format` inexpresables en `agentic_models 0.2.0` ⇒ el puente **levanta** `UnsupportedModelOptionError`, y sólo `anthropic` corta dentro del SSE ⇒ el corte a mitad es del runtime; **diferidos nombrados:** controller vivo padre→hijo, `Usage` (cache/coste), puente bus↔`ctx.stop` (`08·signals`).

### C3 · S5 `EventBus` + `stream()` — canal único ordenado 【G1】 · **estado 2026-07-31: ✅ verificada** (`test_events_homologation.py::test_c3_*`: orden total exacto en los 3 emisores por las DOS vías de suscripción + handler que revienta sin tumbar el canal). **Hallazgo:** el orden real **no** es `Init→…→Result` — no existen `InitEvent`/`ResultEvent` y `Done` precede a los `ToolResultEvent` del turno (coherente con el canónico, no con esta ficha); aseverado en el test. «Los 3 runners» no está definido en el corpus: se lee como los 3 **emisores** (caller/loop/runtime), declarado en el test
- **comportamiento:** un solo canal ordenado `Init→…→Result`; un handler que revienta no tumba a los demás.
- **costura:** `S5` (T2-BASE-MECANISMO — el base la **posee**, no es rellenable).
- **firma:** `subscribe(type,handler)` / `subscribe_all(handler)` / `emit(event)` con try-except por handler; `stream(task) -> AsyncIterator[Event]`.
- **cableado:** caller/loop/runtime emiten; el integrador consume por `async for` o `subscribe_all`. **No se reconstruye** — ya es `existe-fiel` (`runtime.py:153-181`, `bus.py:26-45`).
- **orden:** tras C1, en paralelo a C2.
- **prueba:** orden total del canal en los 3 runners + test de handler que lanza.

### C4 · `AgentLoop` — el mecanismo del turno, sin motores 【G1】
- **comportamiento:** prompt → pool → `complete()` → consumir stream → persistir assistant → dispatch con gate y `context_modifier`/`ends_turn` → decidir continuar. Con `LoopOutcome`/reason-codes (`02·A4`) y `max_turns` efectivo (`02·A5`, hoy inerte).
- **costura:** `S11` `UserInputProcessor` **cableado pre-turno** (hoy exportado y sin consumidor, `01·CTR-12`/`GAP-01`) + `S27` deps-DI por constructor.
- **firma:** `AgentLoop(caller, pool, dispatcher, input_processor, …)` — **todo por constructor**.
- **cableado:** el loop invoca `process()` **antes** del turno y honra el `ShortCircuit`.
- **orden:** tras C2 y C3.
- **prueba:** turno real con tool; test de short-circuit (el processor corta y **no** se llama al modelo); test de `max_turns`.
- **estado 2026-07-31: ✅ implementada y acreditada con violación inyectada** — `S11` cableado **pre-turno** (`agent_loop.py:211`, paga `GAP-01`/`01·CTR-12`) con el orden del canónico (el mensaje del usuario entra al historial en los DOS caminos, corte incluido: `QueryEngine.ts:431` antes de `:556`); firma **divergente del borrador `SEAMS §S11`**, resuelta por `D-08` leyendo `processUserInput.ts` 1→EOF (resultado único con booleano, no unión) y registrada en `SEAMS.md`; `S27` deps-DI por constructor hasta `RuntimeConfig.input_processor`; `LoopOutcome`/`LoopEndReason` con 5 reason-codes espejo del canónico (`query.ts:1705` etc.) + 4 declarados del runtime, `run() -> LoopOutcome` (paga `02·A4`/`FIND-L2` parcial); `max_turns` **efectivo** por constructor y por TAREA (`task.max_turns`, paga `02·A5`/`05·FIND-EXEC5`). **Deuda pagada de paso:** el `try:` de `_run_loop` abre en `_build_child` (defecto que encontró `E6`) ⇒ el registry va a `FAILED`, no se queda `RUNNING`. **Dos xfail de grado `grep` retirados** (aseveraban `inspect.signature`, el modo de fallo de `L09`) y sustituidos por tests de comportamiento.
- **⚠ los 4 motores que el loop dispara quedan FUERA** (compactación · budget · commands · error-recovery). El loop expone el **punto de disparo** y el base corre sin ellos. `S9` se cablea como **seam de composición** (validado en A2.4: 0 boundaries sin battery, ≥1 con battery inyectada), **no** como motor.

### C5 · Tools: `ToolProtocol` + `ToolPool` + `ToolDispatcher` + `S26` 【G1】 · **estado 2026-08-01: ✅ implementada — `FIND-TOOL4/A24` PAGADO** (`ToolResult` declara `context_modifier` y `ends_turn`; los 9 monkeypatches con `type: ignore[attr-defined]` retirados; el loop lee los miembros declarados; `to_llm` CABLEADO. Acreditada por `E2` + `E2·b` reales)
- **comportamiento:** el modelo llama una tool, el dispatcher resuelve/valida schema/aplica timeout, el resultado se aplana y el turno re-entra. **Invariante del pool único**: anuncio y ejecución resuelven del MISMO objeto ⇒ *deferred = visibilidad, no disponibilidad*.
- **costura:** `S16` `ToolProtocol` · `S26` `DeferredToolStrategy` · `S12` `PathPresentation` (choke de saneo, `dispatcher.py:42`).
- **firma:** `SEAMS §S16` mínimo (`name`/`input_schema`/`description(input)`/`execute`) + `ToolResult(output, is_error, is_timeout, is_aborted, metadata, context_modifier)`.
- **cableado:** `create_tools`/`registry.register`; `_resolve_deferred_strategy` elige por `supports_native_tool_search` (C2).
- **orden:** tras C4.
- **prueba:** turno real donde el modelo llama la tool y el resultado se aplana (corrido en A2.3) + test del invariante del pool único.
- **⚠ los miembros de *comportamiento* de `S16` quedan FUERA** (`check_permissions`/`validate_input`/`output_schema`/`is_concurrency_safe`/`interrupt_behavior`) — van con `04·modes`/`06·hooks`/`09` en el tramo 2. **Y `is_concurrency_safe` no es cosmético:** el canónico particiona por él el fan-out (default **diez**, `CG-TOOL-CONC`) ⇒ el tramo 1 corre **serie**, declarado, no fingido.
- **`to_llm` de `S12`: RESUELTO → se CABLEA.** El dilema se cerró leyendo, no razonando: `to_llm` no era un miembro muerto sino `existe-parcial` de verdad — `new_core` lo **implementa** (`FakePathPresentation.to_llm`) y lo prueba (`test_presentation_to_llm_hides_host_path`), pero **cero invocaciones en producción en todo el árbol** (`grep '\.to_llm('` = 1 sola, y es ese test). Borrarlo habría dejado huérfano al integrador contenedorizado. Cableado en los **tres** emisores de ruta HOST — `write_file.py` (ruta escrita), `glob_tool.py` (cada match), `grep_tool.py` (una vez por archivo, no por línea). **No** se cablea en `read_file` (no emite ruta) ni en `file_edit` (devuelve el string de ENTRADA, ya en términos del modelo). Reparto homologado: `to_llm` = traducción *forward* exacta en el punto de emisión; `sanitize_output` = red de seguridad regex en el choke del dispatcher, y por tanto **perdible** (`FIND-VOICE1` ya probó que la red se escapa). Además `ctx.presentation` gana su **default seguro** (`IdentityPresentation`, simétrico al de `ctx.fs`): era `None` y cada consumidor repetía el fallback por su cuenta.
- **`ends_turn` — divergencia DECLARADA, no espejo (`L10`).** `endsTurn` **no existe en A**: `AskUserQuestionTool.call()` devuelve sólo `{data:…}` (leído 1→EOF) y las respuestas vuelven **en el mismo turno** por `checkPermissions → behavior:'ask' + updatedInput`. Esa capa de interacción es `GAP-02`/`K1`, **por encima de la línea de corte**; hasta que entre, B necesita un cable para ceder el turno. Queda declarado en el docstring de `ToolResult` y en `ask_user.py`, con la instrucción de **re-examinarlo contra `check_permissions`** cuando esa capa aterrice. La nota de `plan_mode.py` que lo llamaba «espejo de `requiresUserInteraction()->true`» **sobre-afirmaba** y está corregida: `requiresUserInteraction()` existe en A pero no cierra el turno.
- **⚠ el `xfail(strict=True)` de `FIND-TOOL4/A24` pedía lo que el canónico NO hace.** Su aserción era `hasattr(r,'context_modifier') and r.context_modifier is not None` sobre un resultado **desnudo**; `Tool.ts:330` declara `contextModifier?` **opcional**. Reescrito contra el canónico (`L11`: se valida A↔B, no la doc): el miembro existe, defaultea a `None`, y transporta+aplica el modifier cuando la tool lo produce.
- ✅ **PAGADO (2026-08-01, TERCERA CORRECCIÓN — dejó de ser diferido a instancia del usuario: «postergar `NativeToolRegistry`, que es parte de la funcionalidad siendo revisada, hace que el apartado tools nativas no pueda cerrarse»).** `NativeToolRegistry` **RETIRADO**, no diferido. La decisión se cerró **leyendo** (`D-08`), no razonando: `09·TiR4` la condicionaba a una verificación en `11` que **ya estaba hecha** — `11-cap-mcp.md:645-655`, por el ensamblador: el hot-plug MCP es **reensamblado del pool por turno** (`agent_loop.py:194-195` → `McpProvider.tools()` re-lee `McpState`), no registro dinámico ⇒ veredicto literal «retirar `NativeToolRegistry`; sólo se mantendría si se implementa el swap push-based del auth-tool de `FIND-MCP4`(`McR2`)». Condición verificada **en el código**: cero `unregister`/`swap` en `capabilities/mcp/`. Borrado el módulo (41 L) y el export **de `tools/__init__.py` y del `__all__` raíz** — estar en la superficie pública era lo que lo hacía peor que un huérfano privado: la forma de `FIND-EXEC1` pre-empaquetada para integradores. El test que lo ejercitaba **no se borró: se invirtió** (`test_there_is_exactly_one_tool_registry`) ⇒ reintroducirlo se pone rojo. Con él cayó `ToolRegistry.list_available(permission_ctx=…)`, parámetro muerto que insinuaba un segundo sitio donde se filtra por permisos (el gate vive aguas abajo: `assemble_tool_pool` + `resolver.py:40`).
- **⚠ NUEVO, medido, NO pagado y nombrado (`FIND-C6-2`, `L07`):** el timeout del dispatcher **no acota a una tool que bloquea el event loop**. `dispatcher.py:76` confía el cap a `asyncio.wait_for`, que no puede preemptar una llamada síncrona: cap 0,30 s → transcurrido **2,00 s**, y el resultado vuelve como **ÉXITO**, no como `ToolResult.timeout`. Falsifica lo firmado en `11-cap-mcp.md:656-658`. Instancias vivas: `web_fetch`/`web_search` (urlopen síncrono, hasta 20 s), durante las cuales `ctx.stop` tampoco surte efecto (el abort sólo se **pre**-chequea, `dispatcher.py:54`) y, con un solo event loop, se congelan stream, subagentes y notificaciones. Fijado como `xfail(strict=True)`: si alguien lo paga, se pone **rojo** y obliga a tocar el tracker. El arreglo es `10·tools-native` más allá de las 2 tools de `C6` ⇒ **arriba de la línea**.
- **⚠ `deferred` NO es defecto.** `ToolProtocol` no lo declara y `is_deferred_tool` lo lee con `getattr(tool,'deferred',False)`, pero eso es mímica **fiel** de un miembro opcional (`shouldDefer` en A) con default seguro, y quien lo pone (`capabilities/contracts.py:23`, `mcp/tool_adapter.py:30`) lo declara como atributo normal — no hay monkeypatch ni `type: ignore`. Distinto de `context_modifier`, que sí era una mentira al sistema de tipos.

### C6 · Entorno de ejecución y confinamiento 【G2 → **G1**】 · **estado 2026-08-01: ✅ promovida corriendo — `FIND-C6-1` PAGADO** (acreditada por `E7`×3, con negativa E2E real)
- **comportamiento:** una tool real (`Bash` y una de FS) corre contra un backend **inyectable** y no puede salir de sus raíces.
- **costura:** `S15` `ToolExecEnvironment` · `S14` `ConfinedFilesystem` (mecanismo base) · `S13` `StorageContract` (política del integrador).
- **firma:** `run_shell(command,*,timeout) -> ShellResult` · `resolve(token,*,for_write) -> HostPath` · `real_path/ensure_local/commit`.
- **cableado:** `bash.py:27` ← `factory` → `ctx.exec_env`; `fs_env.py:124`.
- **orden:** tras C5.
- **prueba:** **la que promueve G2→G1**: traversal, symlink y allow-set rechazados con test negativo; `run_shell` contra un backend fake **y** contra el local.
- **⚠ `FIND-C6-1` — el confinamiento tenía una fuga, y la encontró CORRERLO.** `ConfinedFilesystem.resolve()` validaba el path **expandido** contra el allow-set y devolvía `Path(host)` **sin expandir**. Un token RELATIVO pasaba el gate (expandido contra `roots[0]`) y la tool lo abría contra el **cwd del proceso**: `write_file(path="notas.txt")` devolvía `is_error=False` y el archivo caía **fuera del workspace**. Medido, no razonado — probe ejecutado en esta ventana, con el archivo apareciendo en `cwd()` y no en el root. Contradecía además el docstring del propio módulo (`:113`, «los tokens relativos se expanden contra el primer root»). Pagado: `resolve` devuelve el path expandido, que es el que se acaba de autorizar; lexical a propósito (la forma con symlinks resueltos es para el CHEQUEO, no para la E/S — mismo reparto que el canónico). Para un token absoluto es un no-op. Regresión aseverada en `E7·a`. **Esto es exactamente por qué `G2` no es `G1`: la ficha decía `existe-fiel por lectura` y la lectura no vio la fuga.**
- **⚠ NO pagado, nombrado:** `bash.py:27` hace `getattr(ctx,'exec_env',None) or LocalExecEnvironment()`. En producción `ctx.exec_env` va siempre poblado (el runtime lo threadea sin condición), así que el fallback está muerto — pero es la misma forma que enmascaraba `FIND-EXEC1`: si el cable se rompiera, `bash` seguiría corriendo **en el host** y nadie lo notaría. `E7·b` cubre hoy el caso cableado; retirar el fallback es cambio de contrato de la tool y se difiere nombrado.
- **⚠ grado y razón de estar dentro:** `existe-fiel` por lectura (`09·G1-G8`), **no corrido**. Está dentro porque sin una tool real la E2E del tramo es un juguete (`add_numbers`). Quedan fuera: shell persistente (`09·F2`), política de sandbox (`09·F3`) y `safety-fs` (`09·G8`).

### C7 · Façade `AgentRuntime` + registro de tasks 【G1】 · **estado 2026-07-31: ✅ implementada** (doble-camino cerrado: `_registry`/`set_registry`/`get_registry` **retirados**; `task_tools.py` lee `ctx.task_registry`; `S4` gana `join(task_id)` como enriquecimiento declarado, ver `SEAMS §S4`)
- **comportamiento:** `dispatch` devuelve `task_id` inmediatamente; `status`/`result` son coherentes bajo ese mismo id.
- **costura:** `S4` `AgentRuntime` · `S19` `TaskRegistryProtocol` · `S24` `arm_watchdog` (default no-op **declarado**).
- **firma:** `SEAMS §S4` y `§S19`.
- **cableado:** **un solo camino**: el registry se **inyecta** al `LocalAgentRuntime` y se threadea al `ctx`. Se **elimina el doble-camino** `get_registry()` global de `task_tools.py:29/54/113/187` (aprendizaje A2 nº2).
- **orden:** tras C4.
- **prueba:** `dispatch`→`status`=COMPLETED→`result` no-None bajo el MISMO id (corrido en A2.5) + test de que no queda **ningún** `get_registry()` global.
- **⚠ fuera:** el `TaskRecord` rico (`type`/`notified`/`output_file`/`pending_messages`) y el watchdog real → tramo 2/Fase F. `05·LAT-EXEC1` del tracker **es incorrecto** y no debe guiar este cableado (`SKELETON-REPORT §5·pregunta 4`).

### C8 · Subagentes: runner por DI + canal de notificación con drenador 【G1 + un CORE-GAP】 · **estado 2026-07-31: ✅ implementada — `FIND-EXEC1` y `H-5` PAGADOS** (runner por factory inyectada → `ctx.runner`; global retirado; drenaje como paso propio del `AgentLoop` con `apply_notification` sobre el historial vivo, sólo en la raíz; acreditada por `E3` y `E9` reales)
- **comportamiento:** el padre delega, el hijo corre de verdad, el resultado vuelve **aplanado y citado**, y el padre **se entera** de que un hijo background terminó.
- **costura:** `S18` `SubagentRunnerProtocol` · `S21` `NotificationSink`.
- **firma:** `run(spec: SubagentSpec, *, background: bool)` — **`SubagentSpec` frozen mínimo, NO `ForkContext`** (corregido corriendo) · `drain(scope) -> list[Notification]` · **`apply_notification(messages, n)`**.
- **cableado:** el runner se **inyecta por constructor** y `AgentTool` lee `ctx.runner` — se **retira** `set_runner/get_runner` global (`execution/runner.py`). El drain lo hace **el propio `AgentLoop`** antes de componer el turno.
- **orden:** tras C7. **La última pieza antes de la E2E.**
- **prueba:** turno real padre→subagente **+ la prueba NEGATIVA**: un runtime con `runner=None` hace que `AgentTool` devuelva `is_error` ⇒ la costura es *load-bearing*. Sin la negativa, el verde no prueba nada (`L09`).
- **⚠ CORE-GAP `H-5`, se paga aquí:** hoy el base **escribe** notificaciones (`runtime.py:299`) y **nadie las drena** — `process_background_notification` se declara «genérico del runtime» y no tiene call-site; su docstring afirma un drenado que no ocurre. **Y aunque se cableara no funcionaría**: hace `session.messages.append(...)` mientras `runtime.py:397` reasigna `session.messages = list(ctx.messages)` ⇒ el XML se descarta en silencio. Por eso la firma pasa a `apply_notification(messages, n)` **sobre el historial vivo**. Los 7 tests que hoy pasan verifican **la función**, no el comportamiento.
- **⚠ fuera:** el *fork* de historial (aquí sólo *spawn* con prompt propio) y `background=True` (`S22`) — **declarados, no fingidos**.

### C9 · Hilo de identidad: id opaco + repo genérico 【G3 — la excepción razonada】
- **comportamiento:** el runtime **nunca** interpreta `userId`/`sessionId`; lee sólo `.id` opaco. El integrador posee la identidad y scopea por su metadata.
- **costura:** `S20` `SessionRepo[TMetadata]` + `RuntimeSessionProtocol` (`id` opaco).
- **firma:** `SEAMS §S20`. Grafía **única y vinculante** de todo cable de identidad: **`RuntimeHost.scope`, token opaco** — el corpus llegó a tener **cuatro grafías** del mismo cable (`AC-39`) y el nombre del parámetro **es parte de la costura**.
- **cableado:** ripear la mímica `_build_child` (autogenera `sess_…`/`user_…`) y los touchpoints `ID-1..ID-7`.
- **orden:** **transversal — se hace CON C1..C8, no después.**
- **prueba:** turno completo **sin `user_id`** + *probe* que asegura que ningún `user_id` llega al seam del modelo (corrido en A2.4).
- **⚠ por qué entra siendo G3:** es la única capacidad cuyo aplazamiento **cambia la firma de todas las demás**. Refactorizar C1..C8 con la mímica dentro y ripearla en el tramo 2 significa **reabrir las diez fichas**. Es la aplicación literal de `L00`: *si no lo hago ahora, ¿tendré que hacerlo después?* → sí → no hay ahorro.
- **estado 2026-07-31: ✅ acreditada por `E6` corriendo, promovida G3→G1** — turno real sin `user_id` + probe en `S1` + negativa + guardia de grafía `AC-39`/`D-11`; **defecto encontrado por la prueba y PAGADO con `C4` (2026-07-31, 2ª ventana):** `runtime.py:358` llamaba a `_build_child` fuera del `try:`; ahora el `try:` abre ahí ⇒ identidad/sesión/bus/resolver/prompt fallan a `FAILED` **registrado**, con hooks y aviso, y la negativa de `E6` asevera `status is FAILED` + el motivo (antes sólo podía decir `!= COMPLETED`). Acreditado con violación inyectada.
- **⚠ límites declarados:** de los 11 touchpoints, **9** tienen cableado desarrollado. Los 2 que no: **`H-3`** (`LocalAgentRuntime.resume` **no existe**, aunque `00-INTEGRADORES §1.3` publica su firma) → **fuera del tramo, unidad nombrada**; **`H-4`** (discovered-set `09·E5` comparte el `agent_id` inestable y `ID-5` sólo cablea la clave de memoria) → **dentro**, porque toca C5.

### C10 · El ensamblador único `create_runtime` 【G1 — la costura que sostiene a las demás】
- **comportamiento:** existe **un solo** punto de composición; todo lo demás recibe sus dependencias por constructor.
- **costura:** todas. *«El ensamblador es la costura»* (aprendizaje A2 nº1).
- **firma:** `create_runtime(config) -> AgentRuntime`, con `build_child` como **fábrica** inyectada (no un import) — el mismo runner sirve al integrador degenerado y al complejo.
- **cableado:** él **es** el cableado. Prohibido cualquier singleton mutable nuevo.
- **orden:** se escribe con C1 y se cierra con C8.
- **prueba:** el turno E2E lo ejercita por construcción **+** test de aislamiento: una battery importada **sólo** por su compositor; `ctx.runner is None` ⇒ el spawn falla limpio. *El aislamiento se prueba con aserciones, no con prosa* (aprendizaje A2 nº4).

---

## 3. LÍNEA DE CORTE — el nuevo top

> Todo lo de abajo está **fuera del tramo 1**, **entero y nombrado** (`L07`: ninguna unidad se trocea en
> «núcleo aquí + resto a ningún sitio»). Esto **es** el backlog del trabajo restante, y de aquí salen los
> tramos 2..n.

**A · Subsistemas de capability (unidades enteras, con su ciclo dueño)**
`03·context` · `04·modes` · `06·hooks` · `08·signals` · `10·tools-native` (más allá de las 2 tools de C6) ·
`11·mcp` · `12·skills` · `13·memory` · `14·plan` · `15·storage` (rico) · `17·voice` · `18·factory` (manifest).

**B · Batteries (ninguna es obligatoria; `BATTERIES.md` = catálogo, 33 unidades / 6 bloques / 3 perfiles)**
compaction · resilience · caching · budget · commands · wire · structured-output · voice · result-summary ·
handoff-classifier · background-agents.

**C · Costuras no ejercidas por el tramo**
`S3` auth · `S6` wire · `S7` on_progress · `S8` fire-points STOP/POST · `S10` retry · `S17` PermissionGate ·
`S22` force-async · `S23` teardown/reaping · `S25` delegados · `S28`/`S29` (borradores no validados) ·
`S30`/`S31` voz (**`existe-horneada`**: funcionan *porque* no son costura; exteriorizarlas exige **K4**) ·
`S32`–`S38` mcp — de las cuales **`S35`/`S36`/`S38` son 【borde-seguridad】 y nacen `ausente`**.

**D · Deuda documental (el ledger, que NO bloquea el tramo 1 — ver `D-10`)**
7 pares de `P4″` (12·13·14·15·16·17·18) · **39 ítems abiertos** del `A-CIERRE-LEDGER` ·
`O-18`/`R-1b` (12 entradas CABLEAR sin auditar a nivel de símbolo) · `AC-32` (barrido `D-08` sobre los 9 pares
cerrados antes de la regla) · `AC-31` · `BATTERIES` `V2`/`V3`/`V6`/`V7` · `BLUEPRINT §1.4` y `§4` ·
`R-6`/`O-16` (`A-CIERRE-P1.md`, 309 L, nunca abierto 1→EOF).

**E · CORE-GAPs nombrados que quedan arriba**
`H-3` (`resume` inexistente) · `K1` motor de modos de permiso · `K3` guard-path · `K6` compactación ·
`K8` fail-fast · `CG-TOOL-CONC` (fan-out diez + partición por `is_concurrency_safe`).

---

## 4. Gate de fin de tramo — E2E **reales**, no unitarias

El tramo 1 se declara terminado cuando **todas** estas pasan, corriendo:

| # | prueba | qué acredita | estado 2026-07-31 | por qué no basta con menos |
|---|---|---|---|---|
| E1 | turno real texto-solo, con verificación **en el cable** de qué llegó al proveedor | C1·C2·C3 | 🟢 2 tests | un mock no distingue passthrough de traducción-en-el-bridge |
| E2 | turno real con **tool nativa real** (bash + fs), resultado aplanado, re-entrada **+ censo, anuncio, descubrimiento y SOLVENCIA del modelo sobre las 18 tools nativas** | C4·C5·C6 | 🟢 7 tests (turno real `bash`+`write_file` · invariante del **pool único** · `E2c`×2: censo congelado en literal == `create_tools()` (25 tools / 18 módulos) y anuncio en **sus dos ramas** · `E2d`: el modelo elige por nombre del censo entero · `E2e`: `ToolSearch` **descubre** una diferida y **sólo ésa** pasa a anunciarse, con schema invocable · **`E2f`: SOLVENCIA** — enunciado de OBJETIVO (no de herramienta), centinelas `uuid4` por corrida, escenarios barajados, acreditado con violación inyectada) | `add_numbers` no ejercita confinamiento; con 2 tools anunciadas «seleccionar» sale por descarte; y un mecanismo de diferidas que sólo sabe ESCONDER no está acreditado |
| E3 | turno real **padre→subagente**, resultado citado por el padre | C7·C8·C10 | ✅ **en verde** | es el único camino que cruza las 10 capacidades |
| E4 | **NEGATIVA**: runtime sin cablear (`runner=None`) ⇒ `is_error` limpio, no excepción | que las costuras son *load-bearing* | 🟢 4 tests (control positivo · negativa de costura · `FIND-EXEC1` aseverado · negativa **E2E real**), acreditada con violación inyectada | sin ella, verde ≠ cableado (`L09`) |
| E5 | **abort real**: `stop.aborted=True` corta el stream a mitad | C2 / `S2` | 🟢 1 test | hoy el abort se ignora en silencio |
| E6 | **sin identidad**: turno completo sin `user_id`; probe de que ninguno llega al seam del modelo | C9 | 🟢 3 tests | es la prueba de que Filosofía B se cumple |
| E7 | **confinamiento**: traversal/symlink/allow-set rechazados **+ barrido de no-escape sobre las 25 tools** | C6 | 🟢 6 tests (mecanismo: traversal · symlink · allow-set r/w asimétrico · regresión `FIND-C6-1` · costura `S15` load-bearing · **negativa E2E real** con control positivo · `E7f`: las 25 ejecutadas con `subprocess`/`urlopen` prohibidos y `exec_env` espía ⇒ **23 pasan por la costura, se escapan exactamente 2**, lista blanca `==`) | promueve C6 de G2 a G1; y sin `E7f` el «no se escapa ninguna» era grep, no medición |
| E8 | **aislamiento**: battery importada sólo por su compositor; el base no la conoce | C10 | ⛔ sin escribir | el agnosticismo se asevera, no se narra |
| E9 | **notificación**: el padre recibe y **aplica** al historial vivo la notificación de un hijo | C8 / `H-5` | ✅ **en verde** | los 7 tests actuales verifican la función, no el comportamiento |

**Estado del gate — MEDICIÓN VIGENTE (2026-08-01, 5ª ventana, tras la CUARTA CORRECCIÓN):**
`-m gate_tramo1` = **25 passed, 0 skipped, en una sola corrida** (`E1`×2 · `E2`×**7** · `E3`×1 · `E4`×4 ·
`E5`×1 · `E6`×3 · `E7`×**6** · `E9`×1). **8 de 9 — falta sólo `E8`. El tramo NO está cerrado.**
Deuda de cierre re-medida entera (nada heredado): `mypy --strict` **138 err / 54 f** (−1/−1 respecto de la
firma anterior: exactamente el huérfano `native_registry.py` retirado) · `ruff` **505** — las dos piezas de la
cuarta corrección añadieron **cero deuda neta** (6 brutas pagadas enteras, 4 de ellas `B023`, un olor real) ·
suite **703 passed / 2 skipped / 112 xfailed / 0 failed**.

> ⚠ Las cifras que este bloque publicaba antes (**17 passed**, `ruff` 502, suite 695/3/111) eran de **mitad de
> ventana**: se escribieron cuando el gate iba por 17 y la ventana cerró en 19 sin volver aquí. No se sobrescriben
> en silencio — se dicen. La secuencia real de la ventana fue **17 → 19 → 23 → 25**.

El delta cuadra entero contra la medición firmada anterior (19 passed · 697/2/111 · ruff 503 · mypy 139/55):
**+6 passed** = `E2c`×2, `E7f`, `E2d`, `E2e`, `E2f`; **+1 xfailed** = `FIND-C6-2` (el timeout que no acota a
una tool bloqueante); el test invertido del registry sustituye al que lo ejercitaba, sin mover el conteo. `ruff` **+2**
netos: +4 brutos, 2 pagados con `noqa` razonado (`ASYNC251`, `BLE001`) y 2 `RUF012` calcados del idioma de su
propio fichero. Ningún `xfail` estricto pasó en silencio (cero `XPASS`).

✅ **`FIND-EXEC1` PAGADO (`C8`, 4ª ventana).** `create_runtime` puebla `S18` por factory inyectada y `_run_loop` lo
threadea a `ctx.runner`; el global `set_runner`/`get_runner` está retirado. La pieza 3 de `E4` —escrita con su
muerte anunciada— se puso roja al pagarlo y está **reescrita al revés**: hoy asevera que el ensamblador SÍ cablea y
que la costura LLEGA al `ctx` (testigo `S11` dentro del turno, no `hasattr`). El caso «sin cablear» de la negativa
se construye ahora **a propósito** (`subagent_runner_factory=lambda _rt: None`).

**Regla dura del gate:** «100 % del tramo probado y operativo» significa **E1–E9 en verde a la vez, en una sola
corrida**, con `mypy --strict` y lint limpios. Una prueba verde con la costura sin cablear es el modo de fallo
que `L09` documenta como el más caro: *el catálogo verde da falsa confianza*.

---

## 5. Qué se descarta al cerrar el tramo, y qué NO

**Se descarta** (deja de ser trabajo pendiente): la deuda de reconciliación documental **de las unidades que
quedaron dentro de la línea** — sus fichas ya no se releen, porque la E2E las acredita mejor que cualquier
lectura.

**NO se descarta, y conviene decirlo antes de que alguien lo intente:** los **18 trackers de fase 1**
(`HOMOLOGATION/NN-*.md`, 6531 L). Son el único sitio donde vive la **enumeración de comportamientos del
canónico**, y los tramos 2..n se anclan contra ellos (`D-01`, `D-02`). Descartarlos al cerrar el tramo 1
obligaría a releer el canónico entero — el escenario que `D-01` documenta como ya evitado una vez.

---

## 6. Ciclo de los tramos siguientes (el patrón que se repite hasta el final)

1. **Elegir la unidad entera** del §3 (una, nombrada).
2. **Reconciliar su par `P4″`** — sólo el suyo: es un tramo corto, no la pasada completa.
3. **Escribir sus capacidades con los 6 campos de `L05`**, contra el tracker (canónico por excepción, `D-01`).
4. **Refactorizar + E2E real** de esa unidad, **más la re-corrida de E1–E9** (no-regresión del tramo anterior).
5. **Bajar la línea de corte** un escalón y actualizar `§3`.

**El universo de ajuste documental se reduce en cada vuelta**, porque cada unidad cerrada sale del §3 y sus
fichas dejan de necesitar reconciliación. Ese es el mecanismo por el que este plan converge y el anterior
—«Fase B no abre hasta que el ledger esté en 0»— no convergía.
