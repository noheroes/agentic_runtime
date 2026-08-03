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

### C5 · Tools: `ToolProtocol` + `ToolPool` + `ToolDispatcher` + `S26` 【G1】 · **estado 2026-08-01: ✅ implementada — `FIND-TOOL4/A24` PAGADO** (`ToolResult` declara `context_modifier` y `ends_turn`; los 9 monkeypatches con `type: ignore[attr-defined]` retirados; el loop lee los miembros declarados; `to_llm` CABLEADO. Acreditada por `E2` + `E2·b` reales) · **estado 2026-08-01 (6ª ventana): la capa POR TOOL queda acreditada — `E10` (efecto de las 25, con violación inyectada 7/7) + `E11` (conducción de las 11 que faltaban)**
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
- **⚠ NUEVO, medido, ABIERTO y VIGILADO POR EL GATE (`FIND-E2G-1`) — no diferido:** el tool-search **server-side** (rama nativa de `S26`, la que el `gpt-5` de Azure toma en producción) se mostró **menos solvente** que el `ToolSearch` client-side del runtime: 2 fallos en las 6 primeras corridas del caso `archivos` —el modelo tiró de `AskUserQuestion` y devolvió vacío— frente a 6 de 6 en la simulada. La primera versión de `E2g` sólo lo imprimía; ese colchón está **retirado** y la rama nativa **se asevera** — es la que el runtime **elige** por catálogo (`agent_loop.py:168-186`), no una variable ajena. Van **12 de 12** en verde con el listón puesto: **no está arreglado**, es intermitente, y si vuelve pone el gate **rojo**. **VOLVIÓ Y COBRÓ (2026-08-01):** la suite completa dio **`1 failed, 703 passed`** — *«SOLVENCIA CON ToolSearch: 1 incumplimientos en 4 casos»*, con `RuntimeError: Event loop is closed` en teardown (firma de `FIND-E2G-2`). **No se tocó el test.** Re-corridas: `E2g` solo verde · gate file **26 passed** · suite **704 passed / 0 failed** ⇒ **1 roja de 2 corridas de suite completa**. El caso concreto **no está identificado**: la corrida roja se lanzó con `| tail -6` y el mensaje se perdió (error de método propio: capturar **entera a fichero**). ⇒ el gate es 26 verdes **cuando `E2g` no cae**, no 26 verdes y ya. **6ª ventana (2026-08-01): NO CAZADO.** Suite completa lanzada **capturada entera a fichero** (método ya fijado) ⇒ **706 passed / 0 failed**, `E2g` **no cayó** ⇒ el marcador pasa a **1 roja de 3 corridas de suite**. Sigue **ABIERTO**: una corrida verde no arregla un intermitente, y el gate lo sigue vigilando.
- ✅ **`FIND-E7F-1` PAGADO Y RE-MEDIDO (2026-08-01, 6ª ventana).** La tabla `_tool_inputs` se corrigió contra el
  `input_schema` **de cada tool** (no contra una copia en el test) y el barrido se **re-midió**, no se heredó.
  Resultado real, distinto del firmado: **se escapan 3, no 2** — el tercero es **`clone_repository`
  (`subproceso-directo`)**, que antes ni cruzaba la puerta y por eso no aparecía en el mapa; y **22 de 25 pasan
  por la costura**, no 23. Añadida la guarda `_assert_input_matches_schema` en **las dos direcciones** (falta un
  `required` ⇒ la tool vuelve temprano y no mide nada; sobra una clave no declarada ⇒ la entrada es ficción que el
  modelo real nunca mandaría), y el `except Exception` ya no puede tragarse un `KeyError` de entrada mal formada.
  Aparecieron además dos entradas falsas que **nadie había nombrado** (`TaskCreate` mandaba `prompt`, `TaskUpdate`
  mandaba `status`; ninguna existe en sus schemas): cruzaban —las tools leen con `.get(…, default)`— pero eran
  igual de falsas. **La cifra vieja se dice, no se sobrescribe en silencio.**
- **⛔ (histórico, ya pagado — se conserva porque es el enunciado del defecto) `FIND-E7F-1` — el «barrido corriendo de las 25» NO corrió 4 de ellas (2026-08-01, SÉPTIMA CORRECCIÓN).** `_tool_inputs` les pasa claves que no son las de su schema: `read_file`/`write_file` reciben `file_path` y declaran `path` ⇒ `KeyError` **tragado por el `except Exception`** (comprobado corriendo: `salida.txt` no se crea); `clone_repository` recibe `url`/`destination` y declara `repository`/`directory` ⇒ error temprano; `Config` recibe `{}` ⇒ sólo rama de error. Dos consecuencias: el barrido estaba **verde con 4 de 25 sin cruzar la puerta**, y **el número firmado «23 de 25 pasan por la costura» NO VALE** — `_ESCAPES_DECLARADOS` se **re-mide**, no se hereda.
- ✅ **LA AUDITORÍA DE LA CAPA POR TOOL, PAGADA ENTERA (2026-08-01, 6ª ventana) — `E10` (efecto) + `E11` (conducción).**
  - **`E10` — las 25 aseveran EFECTO, con cableado real y 25/25 en verde.** No `is_error`: el efecto. `Edit`
    **edita** (y tiene **tres negativas**: `old_string` ausente, `old_string` ambiguo, ruta relativa — cada una
    aseverando que el fichero queda **byte a byte idéntico**); `clone_repository` clona de un **servidor git-https
    real** levantado en `127.0.0.1` con certificado propio (su `_normalize` fuerza `https://` sea cual sea el
    esquema de entrada, así que un `file://` o un `http://` no habrían probado el camino de producción); `WebFetch`
    trae de un `ThreadingHTTPServer` real; `Sleep` corre con duración **medible**, no con `0`; las seis `Task*` van
    contra un `InMemoryTaskRegistry` real; `Config`(set) se asevera **aplicando el `context_modifier`** como hace el
    dispatcher, no leyendo el JSON de salida. Cierra con `assert set(comprobadas) == _NATIVE_CENSUS` y el nombre se
    marca **antes** de correr el caso, para que una excepción no pueda sacar una tool del censo en silencio.
  - **⚠ `E10` salió verde 25/25 a la primera, y eso se trató como bandera roja, no como éxito.** Un test nuevo que
    nunca ha estado rojo no ha demostrado que pueda ponerse rojo (`L09`). Acreditado con **violación inyectada** —
    anunciada antes de tocar el fuente, revertida desde copia propia verificada por `sha256sum -c`: **7 inyecciones
    en 6 ficheros → 7 rojas, 0 falsos positivos, las 18 restantes intactas en verde**.
  - **`E11` — el modelo CONDUCE las 11 que ninguna corrida medida había invocado**, 11/11, con el censo entero
    delante y enunciados por objetivo (no por nombre de herramienta), salvo un escenario **declarado como dirigido**
    (régimen `E2d`) porque `TaskOutput` y `TaskGet` son **redundantes por diseño** —`TaskGet` también devuelve
    `result`— y **ningún enunciado por objetivo los discrimina**. Se declara en vez de disfrazarse.
  - **✅ VEREDICTO PENDIENTE, EMITIDO: `EnterPlanMode`/`ExitPlanMode` SÍ tienen prueba funcional, con negativa.**
    Los dos ficheros abiertos **1→EOF** (`test_plan_mode_binding.py` 157 L · `test_cap_plan_homologation.py` 188 L).
    `EnterPlanMode`: `test_enter_root_ok_subagent_blocked` asevera el **efecto** (`_PLAN_MODE_KEY is True` tras
    aplicar el `context_modifier`) **+ negativa** (subagente ⇒ `is_error` con «subagent» en el mensaje).
    `ExitPlanMode`: lee el plan **de disco**, arma el one-shot, sale de plan mode y **cierra el turno**; el provider
    lo rinde **una vez** y luego calla **+ negativa de efecto**: sin plan-file es error **y no sale de plan mode**
    (el estado se asevera intacto). Ambas re-aseveradas por `E10` con un `StorageContract` real haciendo E/S real
    (el runtime no trae ninguno). **Límite honesto:** el storage de esos dos ficheros es un doble de test —hace E/S
    real en un tmpdir, pero es un doble—; y los gaps conocidos siguen fijados como `xfail(strict=True)`
    (`FIND-PLAN1/2/3/5/6/12`), entre ellos **`FIND-PLAN2`: `ExitPlanMode` no tiene guard de plan-mode activo**.
  - ⇒ **queda cerrada la lista de «sin ninguna prueba» y la de «sin veredicto»**: las 25 tienen hoy aserción de
    efecto, y 25 de 25 han sido conducidas por un modelo real en alguna corrida medida (14 por `E2g`, 11 por `E11`).
- ✅ **`FIND-E11-1` — CERRADO POR CONTRASTE (10ª ventana), y el enunciado era MÍO y estaba MAL.** «No existe costura para restringir las tools del RAÍZ» es falso: `assemble_tool_pool` filtra por `denied_names()` **al ensamblar** (`tools/pool.py:59-73`) —espejo exacto de `filterToolsByDenyRules` dentro de `getTools()` (`tools.ts:262-268`, literal *«before the model sees them — not just at call time»*)— y el integrador llega hasta ahí por `root_context_modifier`, que corre sobre el ctx raíz (`runtime.py:427-428`) **antes** de que el loop construya el pool del turno (`agent_loop.py:350`). Probado CORRIENDO sobre `create_runtime()` midiendo lo **anunciado al caller**, con control positivo y negativo (`test_runtime_e2e.py::test_e2e_el_integrador_puede_recortar_el_catalogo_del_agente_raiz`). Y la otra mitad —que `initial_allowed_tools` sea aditivo— es **fiel a A** (`createGetAppStateWithAllowedTools`, `forkedAgent.ts:147-171`, suma sobre `alwaysAllowRules.command`): el defecto estaba en mi andamio, no en el sujeto. El párrafo original se conserva abajo porque el diagnóstico de por qué se levantó sigue siendo cierto:
  <br>~~**⚠ `FIND-E11-1` — ABIERTO, nombrado, NO pagado: no existe costura para restringir las tools del agente RAÍZ.**~~
  Encontrado corriendo: monté `E11` asumiendo que `initial_allowed_tools` recortaba el **anuncio**, y las 5 rojas de
  la primera corrida eran **de mi andamio**, no del sujeto. `runtime.py:295-298` lo usa como **allow-list de
  PERMISOS** (`PermissionContext.always_allow_command`), aditiva: no quita nada del catálogo. Para subagentes sí
  hay `agent_allowed_tools`; para la raíz, no. El andamio se **retiró entero** —el resultado medido (el modelo
  condujo las 11 **teniendo `bash` disponible**, que es la vía de escape más fácil) es más fuerte que el que habría
  dado un catálogo recortado—. El arreglo pertenece a `S17 PermissionGate`/`K1`, **arriba de la línea de corte**.
- **⚠ `FIND-E11-2` — ABIERTO y VIGILADO POR EL GATE: solvencia del modelo sobre `AskUserQuestion`.** En **2 de 4**
  corridas medidas el modelo **preguntó en prosa** en vez de conducir la tool. Verificado contra el canónico
  (`prompts.ts:350-380`, leído) que **no es déficit del montaje**: A sólo empuja `AskUserQuestion` en el caso de
  tool denegada. **Explícitamente NO se retocó el prompt ni el system prompt para que pasara** — eso es
  `no-debilitar-la-prueba`. Es intermitente; si vuelve, el gate se pone **rojo**.
- ✅ **`FIND-E11-3` — DEFECTO DEL SUJETO, encontrado por `E11` y PAGADO: `TaskList` tenía un parámetro que A no tiene.**
  El modelo leyó «Filter by status (…). Omit for all.» y llamó con `status="all"`; el campo era `string` libre **sin
  `enum`**, el filtro comparaba por igualdad, y un valor fuera de dominio devolvía `[]` — **indistinguible de «no hay
  tareas»**. El modelo respondió que la sesión no tenía trabajos, con **dos tareas sembradas delante**. Resuelto
  **leyendo el canónico** (`D-08`), no razonando: `TaskListTool.ts:13` es `z.strictObject({})`. Parámetro y filtro
  **retirados** (`L10`: una divergencia con A no es una mejora hasta que se demuestre) en vez de parcheados con un
  `enum`. Regresión clavada en `_e10_task_list`.
- **⛔ (histórico, ya pagado — se conserva porque es el enunciado del hueco) AUDITORÍA DE LA CAPA POR TOOL — el hueco de método, dicho entero.** Las capacidades `E1`..`E9` aseveran **efecto** y aguantan (fichero en disco, corte de stream vs control, clave de persistencia, secreto fuera del allow-set, worktree con git real, uuid inadivinable). La capa **por tool** no: **con** prueba de que hace su trabajo = `bash`, `write_file`, `read_file`, `EnterWorktree`, `ExitWorktree`, `ToolSearch`, `WebSearch`, `Agent`, `grep`, `glob`, `TaskList`, `TodoWrite`; **sin ninguna** = `clone_repository`, `Edit`, `WebFetch`, `Sleep`, `TaskCreate`, `TaskGet`, `TaskUpdate`, `TaskOutput`, `TaskStop`, `AskUserQuestion`, `Config`(set); **sin veredicto** (ficheros no abiertos) = `EnterPlanMode`, `ExitPlanMode`. Nadie ha aseverado nunca que **`Edit` edite**; `clone_repository` y `WebFetch` sólo se han probado **fallando**; `Sleep` corrió con `duration: 0`. ⇒ **`C4`/`C5`/`C6` no pueden darse por cerradas por tool**: lo probado es el ensamblado y el no-escape, no la función.
- **⚠ DEFECTO DE MIS PROPIOS TESTS, encontrado al responder «¿cuántas de las 25 eligió el modelo?» y PAGADO (2026-08-01, SEXTA CORRECCIÓN).** `E2d`/`E2f`/`E2g` medían lo elegido con un **substring** sobre el historial serializado (`f'"{name}"' in json.dumps(messages)`). En `E2g` eso es insostenible: **el resultado de `ToolSearch` viaja en los mensajes con los nombres de sus coincidencias, señuelos incluidos** ⇒ una tool nunca llamada contaba como elegida (reportó 9 y 11 de 25, con `EnterPlanMode`/`TaskList` dentro). Lo grave no es el conteo: **la aserción `selected & must_use` podía satisfacerse con una MENCIÓN en un payload** en vez de con una invocación — un test aprobándose por el lado equivocado. Sustituido por `_invoked_tool_names`, que lee `msg["tool_calls"][*]["function"]["name"]`, lo que `agent_loop.py:401-403` escribe cuando el modelo pide una tool. Los tres tests siguen verdes **con el criterio más estricto**.
- **📊 Censo de conducción del modelo (4 corridas estructurales), dicho también como carencia:** `E2f` 4·5·4·5 tools distintas invocadas por corrida (unión **5**); `E2g` 5·7·5·**14** (unión **14 de las 25**: `Agent`, `EnterPlanMode`, `ExitPlanMode`, `Sleep`, `TaskCreate`, `TaskGet`, `TaskUpdate`, `ToolSearch`, `WebSearch`, `bash`, `glob`, `grep`, `read_file`, `write_file`). **Las 11 que ninguna corrida medida invocó:** `AskUserQuestion`, `Config`, `Edit`, `EnterWorktree`, `ExitWorktree`, `TaskList`, `TaskOutput`, `TaskStop`, `TodoWrite`, `WebFetch`, `clone_repository` — **anunciadas y barridas** sí (`E2c`, `E7f`), **conducidas por el modelo** no; es cobertura de escenarios y **falta**. ✅ **PAGADO en la 6ª ventana por `E11`: las 11 conducidas, 11 de 11** ⇒ la unión medida sube a **25 de 25**. Queda vivo un matiz que no se disfraza: la conducción de `AskUserQuestion` es **intermitente** (`FIND-E11-2`, 2 de 4). El censo es **25 tools en 18 módulos** (`E2c`: `assert len(modules) == 18`); el `print` que decía `11/25` era una etiqueta ambigua del conteo por corrida, **no** un recuento de tools nativas, y está reescrito.
- **⚠ NUEVO, medido, NO atribuido y nombrado (`FIND-E2G-2`, `L07`):** 1 de 6 corridas murió con `CancelledError` esperando el stream del modelo (`event_stream.py:55` ← `caller.py:286` ← `agent_loop.py:348`). **Nada del runtime cancela** (`arm_watchdog` es un no-op, `registry.py:89-92`; default 300 s y murió a ~100 s). Sin atribuir: puede ser del paquete `agentic_models` o del transporte. `E2g` lo captura y lo reporta con las tools elegidas antes de morir, en vez de reventar opaco ⇒ **arriba de la línea**.
- **✅ `FIND-C6-2` PAGADO (10ª ventana), y el contraste lo PARTIÓ EN DOS.** Como estaba escrito —«el timeout del dispatcher no acota a una tool que bloquea el event loop»— mezclaba un límite estructural con una deuda real. (a) **No es deuda:** `asyncio.wait_for` no puede preemptar una corrutina que nunca cede, y A tiene la misma propiedad; es más, A **ni siquiera tiene** cap genérico por tool — su único `timeout` es el de INPUT de `Bash` (`toolExecution.ts:1148-1149`), aplicado donde hay un subproceso genuinamente preemptable. El cap de `dispatcher.py:70` es **extensión de B**. (b) **Sí era deuda:** `web_fetch.py`/`web_search.py` hacían `urlopen` síncrono dentro de su propio `async def` ⇒ *eran* la corrutina que no cede, hasta 20 s, congelando stream, subagentes y notificaciones. A no lo tiene porque su E/S de red es asíncrona de raíz y honra `signal` + `FETCH_TIMEOUT_MS` (`WebFetchTool/utils.ts:262-282`). **Arreglo: `asyncio.to_thread` en las dos**, con la descarga extraída a función NO-corrutina para que reintroducir el bloqueo se vea en el diff; repone la verdad de `11-cap-mcp.md:656-658`. Acreditado INY-60..61 → 2 rojas. **Y el `xfail(strict=True)` que lo custodiaba ACREDITABA EN FALSO (`H-L4`)**: reventaba en `ToolUseContext(...)` con `ValidationError: session_id Field required` — nunca llegó a `dispatch` ni midió timeout alguno, y el `strict` tampoco habría enrojecido al pagarse el gap. **Declarado y NO pagado:** cortar la petición EN VUELO por `ctx.stop`, que exige un signal esperable; `AbortController` es no-esperable **por diseño documentado** (`abort.py:47-49`) ⇒ es cambio de `contracts/abort.py`, fuera de `tools/`.
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
- **estado 2026-08-02: ✅ acreditada por `E8` corriendo — 5 piezas, ninguna con `@_needs_azure`** (el gate ya no se puede acreditar con `E8` saltada): **`E8·a`** dirección del grafo de imports medida con `ast` sobre los fuentes de las dos partes (nunca grep, `D-05`), con **control positivo** (>150 módulos barridos + el conjunto EXACTO de importadores de `S11`) para que un barrido ciego no pase en vacío; **`E8·b`** intérprete limpio ⇒ importar el base no arrastra battery alguna y el `input_processor` por defecto es `None`; **`E8·c`** compuesta vs NO compuesta, dos ramas, con el corte de `/eco` observable y `caller.calls == []`; **`E8·d`** la negativa `ctx.runner is None` ⇒ `is_error` limpio sobre el ctx de **producción**; **`E8·e`** el estado mutable de clase **y de módulo** del ensamblador es **exactamente** el declarado. La battery vive en `batteries/e8_commands/`, **fuera de `src/`** (no se empaqueta). Acreditado con violación inyectada: **9 inyecciones → 9 rojas, 0 falsos positivos** (7 sobre `E8·a`–`E8·d`, 2 sobre `E8·e`), cada una anunciada antes de tocar el fuente, revertida desde copia propia y verificada con `sha256sum -c`.
- **⚠ hallazgos del ensamblador, medidos leyendo `factory.py` 1→EOF:** **`FIND-C10-1` ABIERTO y vigilado por `E8·e`** — `RuntimeFactory._modes` (`factory.py:152`) **es** un singleton mutable de clase, **preexistente**: la ficha prohíbe singleton **nuevo**, así que éste queda medido, nombrado y congelado en `_E8_SINGLETONS_DECLARADOS`; retirarlo exige mover el registro de modos a la config y **no** entra en el tramo. **`FIND-C10-2` PAGADO** — `factory.py:156` llevaba código muerto (`cls._modes[name] = name if False else runtime_cls`); ahora es la asignación directa.

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
| E2 | turno real con **tool nativa real** (bash + fs), resultado aplanado, re-entrada **+ censo, anuncio, descubrimiento y SOLVENCIA del modelo sobre las 18 tools nativas** | C4·C5·C6 | 🟢 8 tests (turno real `bash`+`write_file` · invariante del **pool único** · `E2c`×2: censo congelado en literal == `create_tools()` (25 tools / 18 módulos) y anuncio en **sus dos ramas** · `E2d`: el modelo elige por nombre del censo entero · `E2e`: `ToolSearch` **descubre** una diferida y **sólo ésa** pasa a anunciarse, con schema invocable · **`E2f`: SOLVENCIA** — enunciado de OBJETIVO (no de herramienta), centinelas `uuid4` por corrida, escenarios barajados, acreditado con violación inyectada · **`E2g`: SOLVENCIA CON `ToolSearch`** — lo capaz de resolver el objetivo va DIFERIDO y el modelo tiene que descubrirlo **él solo**, con señuelos aleatorios para que `ToolSearch` discrimine, en las **dos ramas** de `S26`: **las dos aseveradas**, con `FIND-E2G-1` vigilado por el propio gate) | `add_numbers` no ejercita confinamiento; con 2 tools anunciadas «seleccionar» sale por descarte; y un mecanismo de diferidas que sólo sabe ESCONDER no está acreditado |
| E3 | turno real **padre→subagente**, resultado citado por el padre | C7·C8·C10 | ✅ **en verde** | es el único camino que cruza las 10 capacidades |
| E4 | **NEGATIVA**: runtime sin cablear (`runner=None`) ⇒ `is_error` limpio, no excepción | que las costuras son *load-bearing* | 🟢 4 tests (control positivo · negativa de costura · `FIND-EXEC1` aseverado · negativa **E2E real**), acreditada con violación inyectada | sin ella, verde ≠ cableado (`L09`) |
| E5 | **abort real**: `stop.aborted=True` corta el stream a mitad | C2 / `S2` | 🟢 1 test | hoy el abort se ignora en silencio |
| E6 | **sin identidad**: turno completo sin `user_id`; probe de que ninguno llega al seam del modelo | C9 | 🟢 3 tests | es la prueba de que Filosofía B se cumple |
| E7 | **confinamiento**: traversal/symlink/allow-set rechazados **+ barrido de no-escape sobre las 25 tools** | C6 | 🟢 6 tests (mecanismo: traversal · symlink · allow-set r/w asimétrico · regresión `FIND-C6-1` · costura `S15` load-bearing · **negativa E2E real** con control positivo · `E7f` **RE-MEDIDO con las claves del schema** (`FIND-E7F-1` pagado): las 25 ejecutadas con `subprocess`/`urlopen` prohibidos y `exec_env` espía ⇒ **22 pasan por la costura, se escapan exactamente 3** (`WebFetch`/`WebSearch` red-directa, `clone_repository` subproceso-directo), lista blanca `==` + **guarda de schema** que impide que una entrada mal formada vuelva a pasar por barrido) | promueve C6 de G2 a G1; y sin `E7f` el «no se escapa ninguna» era grep, no medición |
| E8 | **aislamiento**: battery importada sólo por su compositor; el base no la conoce | C10 | 🟢 **5 tests** (`a` grafo de imports por `ast` con control positivo · `b` intérprete limpio · `c` compuesta vs no compuesta · `d` negativa `ctx.runner is None` · `e` estado mutable de clase y módulo del ensamblador == el declarado), **ninguno con `@_needs_azure`**, acreditado con **9 inyecciones → 9 rojas, 0 falsos positivos** | el agnosticismo se asevera, no se narra |
| E9 | **notificación**: el padre recibe y **aplica** al historial vivo la notificación de un hijo | C8 / `H-5` | ✅ **en verde** | los 7 tests actuales verifican la función, no el comportamiento |
| **E10** | **matriz funcional de las 25 tools**: cada una con **cableado real** (fs confinado real, `LocalExecEnvironment` real, `InMemoryTaskRegistry` real, git real, servidor HTTP en `127.0.0.1`, servidor git-https local con TLS propio) y aserción sobre su **EFECTO OBSERVABLE**, no sobre `is_error` | la capa **por tool** de C4·C5·C6 | 🟢 **1 test, 25/25 en verde**, cierra con `assert set(comprobadas) == _NATIVE_CENSUS` | paga el hueco de método de la SÉPTIMA CORRECCIÓN: aseverar **mecanismo** (que la tool arranca y vuelve sin error) no es aseverar **función** (que hace su trabajo). Nadie había aseverado nunca que **`Edit` editara** |
| **E11** | **conducción por el modelo** de las 11 que ninguna corrida medida había invocado: 11 escenarios reales con LLM, enunciados por OBJETIVO, con el censo entero delante | cobertura de conducción de C5 | 🟢 **1 test, `conducidas == _E11_OBJETIVO` (11/11)** | `E10` mide **efecto**, `E11` mide **conducción**: son dos preguntas distintas y por eso son dos tests. Una tool que funciona pero que el modelo nunca elige es cobertura que falta |

**Estado del gate — MEDICIÓN VIGENTE (2026-08-02, 7ª ventana):**
Fichero del gate completo, **una sola corrida**, capturada entera a fichero: **32 passed / 1 failed** (150 s).
Con `E8` escrita, las **9 de 9** capacidades del gate **existen**; lo que falta es el **verde simultáneo**.
La única roja es **`E11 · preguntar-al-usuario`** — los otros 10 objetivos conducen — y es **`FIND-E11-2`**:
medido esta ventana en 10 corridas del escenario aislado, el modelo conduce `AskUserQuestion` **0 de 10** con
el sujeto homologado a A (**2 de 10** con la descripción que B tenía inventada, `FIND-E11-4`, ya pagada). La
tool iba anunciada 10 de 10 y, cuando la condujo, con argumentos válidos contra el schema ⇒ **no es montaje
ni schema: es solvencia del modelo**. Con el sujeto fiel deja de ser intermitente y pasa a **determinista**.
**⚠ Decisión de ALCANCE pendiente, no tomada aquí:** sacar `AskUserQuestion` de `_E11_OBJETIVO` sería el tell
«caso fuera» (`no-debilitar-la-prueba`); dejarla bloquea el cierre por algo que no es del runtime. Se deja
**medido y sin decidir**.
**⚠ `FIND-SEQ-1` NUEVO, medido, ABIERTO:** `test_real_sequential_dependent_tools` cayó **2 de 6 corridas**.
Cazado con transcript entero: el modelo emite las **dos** tool calls en el **mismo turno** rellenando el
argumento dependiente con un placeholder (`'__PENDING__'` / `''`); el runtime despachó las dos y devolvió
**ambos** resultados al historial —el token real cruzó—, pero el modelo **no se recuperó** del `ERROR: token
inválido` y cerró el turno con él. No-determinismo del modelo; **el test no se tocó**.
**`FIND-E2G-1`:** no cayó en ninguna de las corridas de suite de esta ventana ⇒ marcador **1 roja de 4**.
Sigue **ABIERTO**.
`ruff` **505** y `mypy --strict` **138 err / 54 f**: **deuda neta cero** (`ruff` subió a 506 por un `ISC004`
y se pagó entero). **El tramo NO está cerrado.**

**Estado del gate — medición anterior (2026-08-01, 6ª ventana):**
`-m gate_tramo1` = **27 passed, 0 skipped, en una sola corrida** (`E1`×2 · `E2`×8 · `E3`×1 · `E4`×4 ·
`E5`×1 · `E6`×3 · `E7`×6 · `E9`×1 · **`E10`×1** · **`E11`×1**; `E10`/`E11` sustituyen a un test que se
retiró, ver el delta). **8 de 9 de las capacidades `E1..E9` — falta sólo `E8`. El tramo NO está cerrado**,
y ahora además `C10` sigue ⛔.
Deuda de cierre re-medida entera (nada heredado): `mypy --strict` **138 err / 54 f** · `ruff` **505**
(alcance `src/agentic_runtime`, `pyproject.toml:45`) · suite **706 passed / 3 skipped / 112 xfailed /
0 failed** (`rc=0`, 434 s, capturada entera a fichero). **`E10` y `E11` añadieron cero deuda neta**: los
6 `ruff` brutos que introdujeron se pagaron enteros (505 → 511 → 505), y `mypy` no se movió.

> **Delta contra la firma anterior (26 passed · 704/3/112):** **+2 passed** = `E10`, `E11`; **+2 en la
> suite** por lo mismo. `ruff` y `mypy` **idénticos a la entrada** de la ventana.

**⚠ Método fijado esta ventana, tras haber perdido una roja:** las corridas de acreditación se capturan
**enteras a fichero**, nunca con `| tail`. La roja de `E2g` de la 5ª ventana se perdió por eso.

> El delta contra la firma anterior (25 passed · 703/2/112) cuadra entero: **+1 passed** = `E2g`; el skip extra
> es de entorno, no de código. La secuencia real de la ventana fue **17 → 19 → 23 → 25 → 26**.

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
