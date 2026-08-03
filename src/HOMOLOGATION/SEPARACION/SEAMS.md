# SEAMS — firmas borrador de las costuras de la ESPINA (Filosofía B)

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/SEAMS.md`.
> **Ciclo A1.7** (síntesis de la espina). Fuente: §2.1 "Costuras que implica" de los 6 `SEPARACION/{01,16,07,02,05,09}.md`.
> Esquema/tiers: `00-LEGEND.md §2.2`. Gemelo de datos de `00-BLUEPRINT.md §2` (aquí las FIRMAS; allí el índice).
>
> **Naturaleza del doc.** Cada costura = una **interfaz que el base define y el integrador/battery rellena** (T2-COSTURA),
> o la **costura al motor de modelo** (T1-MOTOR). Las firmas son **BORRADOR**: destiladas de los call-sites/firmas ya
> abiertos en los ciclos A1.x (evidencia citada por costura), **a validar o corregir en el walking skeleton A2** (PLAN §4).
> No son la firma final; son el contrato de partida que A2 ejercita con un turno real.
>
> **Convención de estado por costura:** `existe-fiel` (cableada y homóloga) · `existe-enriquecer` (cableada pero la firma
> se queda corta) · `existe-sin-poblar` (declarada, ningún productor la invoca — DEUDA-B de cableado) · `ausente` (hay que
> crearla). El estado sale de la evidencia del ciclo de origen (L09: cableado ≠ existencia).
>
> **id opaco (transversal):** ninguna firma transporta `userId`/`sessionId` interpretados; los repos son **genéricos sobre
> una metadata que el integrador define** y el runtime lee **sólo el `.id` opaco** (LEGEND §2.4). Marcado `【id-opaco】`.
>
> > **Nota de aplicación (A-CIERRE.MCP 2026-07-30 — `AC-39`).** Este invariante **se estaba incumpliendo en una firma
> > publicada**, y el corpus llegó a tener **cuatro grafías del mismo cable**: `11·OI-MCP-A` ofrecía
> > `create_runtime(config.capabilities.mcp_user=…)` **o** `McpProvider(user_id=ctx.user_id)`, `DEUDA-A·ID-3` usaba
> > `scope=` y `00-INTEGRADORES §1.7·C5` fijaba `RuntimeHost.scope`. La segunda **nombra la identidad en el
> > parámetro** y es justo la que este invariante prohíbe — ofrecida al integrador en pie de igualdad con la
> > correcta. **Grafía única y vinculante: `RuntimeHost.scope`, token opaco.** Regla operativa: *toda firma nueva que
> > transporte identidad se contrasta contra esta nota y `00-LEGEND §2.4` **antes** de escribirse, y ningún par puede
> > publicar dos firmas alternativas sin decir cuál cumple el invariante.* El nombre del parámetro **es parte de la
> > costura**: cuatro nombres para un cable son cuatro implementaciones divergentes esperando a ocurrir.

---

> **ENMIENDA A3.CAT (2026-07-27).** Este doc se abrió **1→EOF** por primera vez desde A1.7, en el gate de cierre de
> `BATTERIES.md` (pendiente **V1**). Se aplican las 3 correcciones que `17·§2.7` le debía y se numeran las dos costuras
> de voz (**S30/S31**), cerrando el cabo 5 de `BATTERIES §4.5` que había quedado *sin número*. Cambios, todos trazables:
> (1) el índice decía **"(20)"** y listaba **27** filas (la L54 ya decía 27) → ahora **29**; (2) **S12** pasa de
> `existe-fiel` a **`existe-parcial`** — el propio §3·S12 dice *«`to_llm` sin call-site»*, y bajo la convención de estado
> de este encabezado un miembro que ningún productor invoca **no** es `existe-fiel`; (3) **S30/S31** registran dos
> protocolos que estaban **cableados y fuera del índice**. La numeración `S28`/`S29` está tomada por `Battery`/`compose()`
> y `RuntimeManifest` (borradores de `18·factory`), por eso la voz empieza en **S30**.

> **ENMIENDA A-CIERRE.MCP (2026-07-30).** Doc re-abierto **1→EOF** desde `A-CIERRE·P4″ §16` (par 11 · mcp,
> `EVIDENCIA.log:247`). Se numeran **siete costuras MCP** (`S32`-`S38`) que estaban **cableadas y fuera del índice**:
> `11·§2.1` declaraba **diez** costuras y **ninguna** tenía número `S`, la peor proporción de los once pares
> reconciliados (10·mem-remote: 5/12; 07·events: 1/7). *(De las diez, dos no son de 11 y ya estaban aquí:
> `CapabilityProvider` es home 12 y `ToolExecEnvironment` es `S15`; la décima, `cleanup_for_agent`, es el consumidor
> de `S23` y se registra como cable, no como costura nueva.)*
>
> **La exclusión ya no tenía base.** La cabecera `:4` limita las fuentes a los `§2.1` de `{01,16,07,02,05,09}` — pero
> **esta misma casa ya la rompió**: `A3.CAT` numeró `S30`/`S31` desde el **ciclo 17**, que tampoco era fuente. Una
> exclusión estructural incumplida una vez por precedente deja de justificar nada; la regla vigente es **si está
> cableada, se numera**, venga del par que venga. Se cierra así el defecto `AC-21` para el par 11 y se deja el mismo
> criterio escrito para 12·13·14·15·16·17·18.
>
> **Cambios, todos trazables:** (1) índice **29 → 36**; (2) altas `S32`-`S38` (`S28`/`S29` siguen tomadas por
> `Battery`/`compose()` y `RuntimeManifest`, borradores de `18·factory`); (3) `§S23` gana el cable inverso a
> `11·CG-MCP-20`; (4) `§S25` gana la resolución de su delegado `mcp_servers→11` (**huérfano hasta hoy**, y con el
> ancla canónica corregida a `initializeAgentMcpServers` el 2026-07-30 tras leer el canónico por excepción: 11 no lo
> tenía) y la advertencia sobre los otros cuatro delegados sin comprobar; (5) `【id-opaco】` `:16-17` gana la nota de
> aplicación que resuelve las **cuatro grafías** del mismo cable de identidad (`AC-39`).

## 0. Índice de costuras (27 de A1.7 + 2 de A3.CAT + 7 de A-CIERRE.MCP = 36)

| # | costura | tier | estado | origen (ciclo · findings) |
|---|---|---|---|---|
| S1 | `ModelCallerProtocol` | T1-MOTOR | existe-enriquecer | 16·A2/A3/A4/A5/B7-B11 · 02·C2/C3/C4 · 07·D4/D5/E1 · 05·E2/E18 |
| S2 | señal-de-abort (`AbortSignal`) | T1-MOTOR | existe-roto | 16·A6 · 07 · 08(coord) |
| S3 | `AuthProvider` (credencial/refresh) | T2-COSTURA | ausente | 16·D2/B17 |
| S4 | `AgentRuntime` (façade) | T2-COSTURA (+base default) | existe-fiel | 01·CTR-01 |
| S5 | `EventBus` + `stream()` (canal único ordenado) | T2-BASE-MECANISMO | existe-fiel | 07·A1/A2/A3/A4 |
| S6 | wire serializer `Event→SDKMessage` | T2-COSTURA (battery `wire`) | ausente | 07·GAP-EVT5/K4/F0/D1 |
| S7 | `on_progress` (tool-progress) | T2-COSTURA | ausente | 07·C3 · 09·D10 |
| S8 | `HookRunner` (fire points + hook-sink) | T2-COSTURA | existe-parcial | 02·D3/D5/E2/F2 · 07·I1 · 06 |
| S9 | `CompactionProvider` (+ trigger del loop) | T2-COSTURA | existe-sin-motor | 01·CTR-09 · 02·B6 · 07·H1 · 16·C2 |
| S10 | `RetryPolicy` / `with_retry` (+ fallback) | T2-COSTURA (+T1-MOTOR) | ausente | 16·B1/B2/B3 · 02·C4/C5/C7/D2 · 07·J3 |
| S11 | `UserInputProcessor` | T2-COSTURA | **existe-fiel** (`C4` 2026-07-31: cableado pre-turno; firma DIVERGE del borrador, ver §S11) | 01·CTR-12 · 02·G1/F8 |
| S12 | `PathPresentation` (sanitize choke) | T2-COSTURA (+base default) | **existe-parcial** (`C5` 2026-08-01 CORREGIDO ×2: `to_llm` cableada en **6** puntos ⇒ deja de estar sin poblar, pero `17·§2.7.1` prohíbe `existe-fiel` mientras el choke per-chunk siga roto y el default sea no-op) | 01·CTR-11 · 09·D9 · 17·§2.7.1 |
| S13 | `StorageContract` (roots + token→path) | T2-COSTURA | existe-fiel | 01·CTR-10 · 05·E7 · 09·G6 · 15 |
| S14 | `ConfinedFilesystem` (confinamiento) | T2-BASE + costura S13 | existe-fiel (`C6` 2026-08-01: G2→**G1**, corrida; `FIND-C6-1` PAGADO; `worktree.py` la esquivaba entera ⇒ cableada) | 09·G1-G8 |
| S15 | `ToolExecEnvironment` (backend shell) | T2-COSTURA (AÑADIDA) | existe-fiel — **ENRIQUECIDA 2026-08-01** con `run_argv(argv, *, cwd, timeout)` para cerrar el bypass de `worktree.py` (git corría en el host con bwrap inyectado) | 09·F1/F2/F3/F4 |
| S16 | `ToolProtocol` (contrato de tool) | T1-CONTRATO + costura | existe-enriquecer (`C5` 2026-08-01: `09·A24` DECLARADO, `FIND-TOOL4` pagado; siguen fuera los miembros de comportamiento) | 09·A1-A26 |
| S17 | `PermissionGate` (`check_permissions` per-input) | T2-COSTURA | existe-parcial | 09·A6-A9/D3/G8 · 02·F2 · 06 |
| S18 | `SubagentRunnerProtocol` | T2-COSTURA | **poblada por DI** (`C8` 2026-07-31: `FIND-EXEC1` PAGADO) | 05·E24 (FIND-EXEC1) |
| S19 | `TaskRegistryProtocol` (repo id-opaco) | T2-COSTURA | **camino único** (`C7` 2026-07-31; `TaskRecord` sin enriquecer, diferido) | 05·E9/E10/E32 |
| S20 | `SessionRepo` (repo id-opaco de sesión) | T3-INTEGRADOR / costura | existe-mímica | 05·E30 【id-opaco central】 |
| S21 | `NotificationSink` (drain/process) | T2-COSTURA | **put+drain+apply con call-site** (`C8` 2026-07-31: CORE-GAP `H-5` PAGADO) | 05·E5/E19 |
| S22 | `ForceAsyncPolicy` | T2-COSTURA | ausente | 05·E34 |
| S23 | `on_agent_teardown(agent_id)` (reaping) | T2-COSTURA | ausente | 05·E35 |
| S24 | `arm_watchdog` (timeout/watchdog) | T2-COSTURA | existe-noop | 01·CTR-15 · 05 · 16·B4 |
| S25 | `AgentDefinition` (contrato ampliado) | T1-CONTRATO + costura | existe-parcial | 05·E28/E22 |
| S26 | `DeferredToolStrategy` | T2-BASE-MECANISMO (+T1-MOTOR) | existe-fiel (`C5` 2026-08-01: verificada CORRIENDO — `E2b` visibilidad, `E2e` descubrimiento, `E2g` **las dos ramas** con modelo real; `FIND-E2G-1`/`-2` abiertos) | 09·E1-E10 |
| S27 | deps-DI seam (constructor) | T2-COSTURA (test) | existe-fiel | 02·E6 |
| S30 | `PromptSourceProtocol` (entrada no-textual, pre-loop) | T2-COSTURA (AÑADIDA A3.CAT) | existe-horneada | 17·C1/§2.7 · `BATTERIES §4.5` |
| S31 | `SpeechSink` (salida hablada sobre S5) | T2-COSTURA (AÑADIDA A3.CAT) | existe-horneada | 17·§2.7 · `BATTERIES §4.5` · K4 |
| S32 | `McpConfigStore` / `ScopedMcpConfigStore` (productores por scope) | T2-COSTURA (AÑADIDA A-CIERRE.MCP) | existe-fiel | 11·§2.1 · MCP-OK-10/11 |
| S33 | `McpConfigWatcher` (fuente externa de config) | T2-COSTURA (AÑADIDA A-CIERRE.MCP) | existe-fiel | 11·MCP-OK-24 · espejo 15·A5 |
| S34 | `register_auth_strategy` / `AuthDeps` | T2-COSTURA (AÑADIDA A-CIERRE.MCP) | existe-fiel | 11·MCP-OK-16/17/18 |
| S35 | `McpPolicy` (allow/deny name·command·url) | T2-COSTURA (AÑADIDA A-CIERRE.MCP) | **ausente** 【borde-seguridad】 | 11·FIND-MCP14 → CG-MCP-11 |
| S36 | `McpApprovalGate` (project approved/rejected/pending) | T2-COSTURA (AÑADIDA A-CIERRE.MCP) | **ausente** 【borde-seguridad】 | 11·FIND-MCP15 → CG-MCP-11 |
| S37 | `elicitation-hook` (elicitation/roots sin UI) | T2-COSTURA (AÑADIDA A-CIERRE.MCP) | ausente | 11·FIND-MCP18 → CG-MCP-18 |
| S38 | `trust-gate` del headersHelper (sobre `S15`) | T2-COSTURA (AÑADIDA A-CIERRE.MCP) | **ausente** 【borde-seguridad】 | 11·FIND-MCP24 → CG-MCP-15 |

> **Nota de las altas MCP.** Tres de las siete (`S35`·`S36`·`S38`) son **borde de seguridad** y estaban **fuera del
> índice**: un lector de este doc no veía que la admisión de servidores MCP, la aprobación de servidores de proyecto
> y el trust-gate del script de headers son decisiones **del integrador**, no del runtime. Es exactamente el daño que
> `c24/c29` mide: no que falte el número, sino que **la costura no existe para quien lee el rollup**. Las tres
> nacen `ausente` — el runtime hoy conecta sin política, sin aprobación y ejecuta el helper sin gate.

> El índice de `00-BLUEPRINT.md §2` es un extracto de las 5 costuras rectoras (model-caller, tool-contract,
> event/stream, dispatch, repo/scope); **aquí** están las 29 firmas completas. La numeración `S#` es de este doc,
> **y es compartida con los borradores `S28 Battery/compose()` y `S29 RuntimeManifest` de `18·factory`** (por eso la
> voz empieza en S30; S28/S29 no se re-listan aquí porque siguen **BORRADOR NO VALIDADO** → Fase C).

---

## 1. T1-MOTOR — costura al motor de modelo (`agentic_models`)

### S1 · `ModelCallerProtocol` — LA costura central
- **tier:** T1-MOTOR. **estado:** `existe-enriquecer` (el grueso del trabajo de la espina).
- **productor (invoca):** el base loop — `AgentLoop.run` en `agent_loop.py:235` (`complete(...)`).
- **consumidor (implementa):** bridge `AgenticModelsCaller` (**battery por defecto**, `caller.py`) **o** un caller del
  integrador complejo que embeba el motor y lo dirija por eventos (openclaw-like).
- **firma HOY** (`protocol.py:28-37`, demasiado delgada): `complete(messages, tools, *, stop, model_id) -> AsyncIterator[Event]`
  (+ `system_sections`/`system_override` condicionales, `agent_loop.py:227-234`).
- **firma BORRADOR enriquecida** (targets 16·MoR1/MoR2, 02·C2, 05·E2):
  ```python
  class ModelCallerProtocol(Protocol):
      async def complete(
          self,
          messages: list[Message],
          tools: list[ToolSchema],
          *,
          model_id: str,                     # 16·A7 resuelto (provider,id); 02·C3 por-turno
          stop: AbortSignal,                 # S2 — NO asyncio.Event (16·A6)
          system_sections: list[SystemSection] | None = None,
          system_override: str | None = None,
          thinking: ThinkingConfig | None = None,   # 16·A2/B7 (hoy no puebla)
          effort: Effort | None = None,             # 16·A2/B5
          temperature: float | None = None,         # 16·B8
          max_tokens: int | None = None,            # 16·B9 (política de cap → battery)
          output_format: OutputFormat | None = None,# 16·B11 structured (sin MoR en tracker)
          tool_choice: ToolChoice | None = None,    # 16·B10
          metadata: Mapping[str, str] | None = None,# 16·B10 【id-opaco】 (user_id/affinity)
      ) -> AsyncIterator[Event]: ...
      def supports_native_tool_search(self) -> bool: ...   # 16·A8 (caller.py:131-144, cableado agent_loop.py:144-146)
  ```
- **eventos de retorno (T1-CONTRATO, def. en 07):** `TokenEvent`(+`kind` thinking), `ThinkingEvent` (16·A4 — hoy skip
  `caller.py:245`), `ToolCallEvent`, `DoneEvent`(`Usage` con cache/coste — hoy `thinking_tokens=0` `caller.py:228-232`),
  `ErrorEvent(category)` (16·C1 — hoy `ErrorEvent(message=str)` `caller.py:236-242`).
- **validación A2 (A2.2 motor) — HECHA ✅:** turno real texto-solo corrido (`skeleton/_motor.py`, `claude-haiku-4-5`,
  exit 0; texto + `Usage` reales). **Validado passthrough:** `system_override`/`temperature`/`max_tokens`/`metadata`
  (sólo `user_id`)/`stop`→`signal`, y `Usage` con cache/coste (provider los puebla, anthropic.py:606-611). **CORRECCIÓN:**
  `thinking`/`effort`/`tool_choice` **NO** viajan por `StreamOptions` (duck-typing / `stream_simple(reasoning)`,
  anthropic.py:751-792) ⇒ **bridge-traducidos, no passthrough**; `Usage` NO lleva `thinking_tokens`. **HALLAZGOS**: (1) rama
  oauth de `agentic_models` rota con anthropic-sdk 0.109.1 (emite `x-api-key: dummy`) → workaround `options.client`
  pre-construido; (2) TLS MITM del dev-box (shim aislado en `_motor`). Detalle: `skeleton/README.md` cierre A2.2 → consolidar
  en `SKELETON-REPORT.md` (A2.5) + deuda Fase D.
- **cabo:** el mapeo de `stop_reason` (16·A5/C3, refusal→policy) y betas dinámicos (16·B5) viven en el bridge, no en la firma.

### S2 · señal-de-abort (`AbortSignal`)
- **tier:** T1-MOTOR. **estado:** `existe-roto` (16·A6: se pasa `asyncio.Event`, el provider chequea `.aborted` que Event no tiene ⇒ abort ignorado).
- **productor:** el bridge envuelve `ctx.stop` antes de `complete()`. **consumidor:** el provider del motor (`signal.aborted`).
- **firma BORRADOR:**
  ```python
  class AbortSignal(Protocol):
      @property
      def aborted(self) -> bool: ...
      def reason(self) -> AbortReason | None: ...   # liga 08·SIG13 (turno vs agente)
  # bridge: CombinedAbortSignal(ctx.stop: asyncio.Event) -> AbortSignal
  ```
- **coordinación:** doblemente latente — en standalone `ctx.stop` **nunca se ARMA** (→08·signals). La separación
  abort-de-turno / abort-de-agente (05·E36/FIND-SIG13) refina `reason()`.
- **validación A2:** no crítico para A2.2 (turno feliz); se ejercita cuando entre 08.

### S3 · `AuthProvider` (credencial + refresh pre-request)
- **tier:** T2-COSTURA (auth-provider seam) + credencial = T3-INTEGRADOR. **estado:** `ausente` (16·D2: `oauth/anthropic.refresh` existe pero no auto-invocado).
- **productor:** el bridge pre-request. **consumidor:** el integrador (provee credencial fresca / refresca por-usuario).
- **firma BORRADOR:**
  ```python
  class AuthProvider(Protocol):
      async def credential(self) -> Credential: ...   # api_key | sk-ant-oat; refresca si caduca
  ```
- **AMPLIACIÓN A2.2 (ganada corriendo un turno OAuth real):** la costura auth es credencial **+ modo de construcción del
  cliente del motor**. Bajo OAuth-CC con anthropic-sdk 0.109.1 no basta pasar `api_key` (rama oauth de `agentic_models`
  filtra `x-api-key: dummy` ⇒ 401): el integrador construye un **cliente pre-construido** `AsyncAnthropic(auth_token=…)`
  sin api_key + betas `claude-code-20250219,oauth-2025-04-20` + inyecta la identidad CC en el system-prompt, y lo pasa por
  `options.client`. Consecuencia: `options.client` ⇒ `is_oauth=False` ⇒ **se desactiva `_to_cc_name`** (mapeo de nombres
  de tool, anthropic.py:200/248) → cabo para 09/A2.3. El bridge acepta `api_key | client`. Detalle desarrollado (6 campos)
  en `00-INTEGRADORES §1.2` (refinamiento A2.2). Arreglo de raíz de la rama oauth = **Fase D** (`agentic_models`).
- **validación A2:** el turno real de A2.2 **sí** ejercitó auth OAuth (no estático) por necesidad del dev-box; el diseño de
  la costura `AuthProvider`/refresh formal se cablea en Fase E/F.

---

## 2. T2-BASE-MECANISMO — costuras que el base POSEE (firma fija, no rellenable por el integrador)

> Estas no son "rellenables" por el integrador; son el mecanismo del base. Se listan porque son el **contrato interno**
> que las batteries y el loop consumen. Firma = la del base.

### S5 · `EventBus` + `stream()` (canal único ordenado)
- **estado:** `existe-fiel` (07·A1-A4, verificado `runtime.py:153-181`, `bus.py:26-45`). **NO se re-construye.**
- **firma BORRADOR:**
  ```python
  class EventBus:                                   # bus.py (base)
      def subscribe(self, event_type: type[E], handler: Callable[[E], None]) -> Unsubscribe: ...
      def subscribe_all(self, handler: Callable[[Event], None]) -> Unsubscribe: ...
      def emit(self, event: Event) -> None: ...     # try/except por-handler (07·A4)
  class LocalAgentRuntime:
      async def stream(self, task: RuntimeTask) -> AsyncIterator[Event]: ...  # orden total (07·A2)
  ```
- **productor:** caller/loop/runtime (`emit`). **consumidor:** integrador vía `subscribe_all`/`async for` (→S6 wire).

### S14 · `ConfinedFilesystem` (mecanismo de confinamiento)
- **estado:** `existe-fiel` (09·G1/G3/G5 byte-idénticos; G2/G4 omiten normalización macOS = menor).
- **firma:** `resolve(token, *, for_write: bool) -> HostPath` (`fs_env.py:144`), sobre `roots`/`write_roots` + `StorageContract` (S13).
- **nota:** el **mecanismo** (traversal/symlink/allow-set) es base; la **política** (roots, token→path, safety-fs G8) es del integrador (→S13/S17).
- **estado tras `C6` (2026-08-01):** grado **G2 → G1** (corrida, no sólo leída) — y correrla encontró **`FIND-C6-1`, PAGADO
  en la misma ventana**: `resolve()` validaba el path **expandido** y devolvía `Path(host)` **sin expandir**, así que un token
  RELATIVO pasaba el gate (expandido contra `roots[0]`) y la tool lo abría contra el **cwd del proceso** — `write_file` con
  `path="notas.txt"` escribía en `cwd()/notas.txt` con `is_error=False`. Medido con sonda, no razonado. Hoy devuelve
  `Path(expand_path(...))`: lo autorizado y lo usado son el MISMO path. Expansión **léxica** a propósito (la forma con symlinks
  resueltos es para el CHEQUEO, no para la E/S — mismo reparto que el canónico). Acreditado por `E7a` (traversal · absoluto-fuera
  · symlink-que-apunta-fuera · roots asimétricos read/write · la regresión relativa) y por la negativa E2E real `E7c`.
- **corrección (barrido de las 18 tools, misma fecha): el estado `existe-fiel` era de la COSTURA, no del cableado.** Había una
  tool que no pasaba por ella: `worktree.py` componía el destino a mano (`Path(git_root).parent / ".worktrees/<name>"`) y
  no lo pasaba por `resolve()` **en ningún momento** — sin allow-set y, encima, **fuera** del write-root por construcción
  (hermano del git root). Hoy va por `ctx.fs.resolve(str(ctx.fs.write_root / ".worktrees/<name>"), for_write=True)`, lo que
  obliga a una **divergencia declarada**: el worktree se crea DENTRO del write-root, no como hermano. Con la ubicación
  anterior el confinamiento era literalmente inexpresable. Acreditado en `E7e`.
  `PathOutsideWorkspace` se devuelve al modelo con `str(exc)` en 6 sitios y su mensaje repite **sólo el token del modelo**,
  no los roots — comprobado, no supuesto: no es un séptimo punto de emisión.
- **⚠ la frase «ningún otro de los 18 módulos esquiva `S14`» que ocupaba este sitio era grep, no medición** — el usuario la paró.
  Sustituida por `E7f`, que **ejecuta las 25 tools** con `asyncio.create_subprocess_exec/_shell` y `urllib.request.urlopen`
  prohibidos y un `exec_env` espía no-delegante. **Medido: 23 de 25 pasan por la costura; se escapan exactamente 2** —
  `WebFetch` y `WebSearch`, ambas `red-directa` (`urllib.request.urlopen` en el proceso del runtime, sobre la red del host, con
  la URL elegida por el **modelo** y sin guarda de SSRF: `169.254.169.254`, `127.0.0.1:*`). `clone_repository` **no** se escapa.
  Es la misma forma que tenía `worktree.py` con git: con un `BwrapExecEnvironment` (`--unshare-all`) `bash` queda aislado y estas
  dos siguen saliendo a Internet. **No se paga aquí y no es `declaración-como-pago`:** el canónico ubica la política de red en las
  reglas `WebFetch(domain:*)` que el sandbox-adapter deriva a `allowedDomains` (`09·F3`), y `09·F3` + `S17` están **arriba de la
  línea** (`TRAMO-1 §3·C`), con `C6` excluyéndolas por su nombre — diferidas ANTES de que el barrido las encontrara. Lo que sí se
  paga: queda medido, acotado a dos, y la lista blanca es **exacta** (`==`), así que un escape nuevo la pone roja **y pagar uno de
  los declarados también**, lo que obliga a tocar el tracker.

### S26 · `DeferredToolStrategy`
- **estado:** `existe-fiel` (09·E2/E3/E10; Simulada client-side + Nativa `defer_loading` server-side).
- **firma BORRADOR:**
  ```python
  class DeferredToolStrategy(Protocol):
      def owns_search_dispatch(self) -> bool: ...          # Simulada True / Nativa False
      def filter_announced(self, pool: ToolPool, discovered: set[str]) -> list[ToolSchema]: ...
      def should_defer_turn(self, pool: ToolPool, model_id: str) -> bool: ...  # 09·E9 auto-mode → 16
  ```
- **productor:** `AgentLoop._resolve_deferred_strategy` (`agent_loop.py:132-150`), elige por `supports_native_tool_search` (S1).
- **cabo:** delta tipado (09·E4), multi-select (E6), keyword-quality (E7), precedencia (E1) = mejoras del base; auto-mode umbral →16.
- **estado tras `C5` (2026-08-01):** `existe-fiel` **verificado corriendo**, no por lectura. `E2b` acredita el invariante que
  importa: **`deferred` es VISIBILIDAD, no disponibilidad** — una tool diferida NO aparece en el anuncio al modelo (con control
  positivo: `"bash"` sí aparece, para que el verde no sea trivial) y aun así se **despacha con éxito** por un `ToolDispatcher`
  real **sobre el mismo `ctx`**, porque anuncio y ejecución resuelven del MISMO objeto (invariante de pool único). El atributo
  `deferred` NO se cuenta como defecto (`L10`): es mímica fiel del `shouldDefer` opcional de A con default seguro, y sus setters
  lo declaran como atributo normal de clase — sin monkeypatch y sin `type: ignore`, al contrario que `context_modifier`.

> **Otros mecanismos base** (firma = base, no costura rellenable): `AgentLoop` (esqueleto del turno, 02·A1/C1/F1), `ToolPool`
> (assemble/find, invariante pool-único, 09·C1-C4/D1), `ToolDispatcher` (dispatch+timeout, 09·D1/D5), `fork` (snapshot/policy/
> filtrado/guard, 05·E3/E4/E12/E13/E14), `TaskStatus` (05·E1), ciclo de vida `_run_loop` (05·E6 complete-first).

---

## 3. T2-COSTURA — interfaces que el integrador/battery rellena

### S4 · `AgentRuntime` (façade de ejecución) — ✅ VALIDADA (dispatch/status/result) en A2.5
- **estado:** `existe-fiel` (base envía `LocalAgentRuntime` default; el integrador complejo puede implementar la suya).
- **fuente mímica 1→EOF (2026-07-23, `execution/local/runtime.py` 435 LOC):** la façade real = `dispatch`(L134, async, `register`→`ensure_future(_run_loop)`→devuelve `task_id` **inmediatamente**) · `stream`(L153, azúcar sobre dispatch+queue+sentinel) · `status`(L183, lee `registry.get(id).status`) · `cancel`(L187, `registry.kill`) · `result`(L190, `registry.get(id).result`) · `runtime_id`(L110). Coherencia vía el **registry keyed-by-task_id**, no un dict interno.
- **validación A2.5 (skeleton):** `dispatch`→`status`(COMPLETED)/`result`(no-None) coherentes bajo el MISMO `task_id`. **Matiz honesto:** el id-mismatch que corregí era de **mi propio stub A2.1** (guardaba result bajo id distinto), NO un finding de la mímica (que usa el registry). Divergencia de mi skeleton: mi `dispatch` corre a COMPLETIÓN (sin async task real) ⇒ NO ejercita el ciclo PENDING/RUNNING de la mímica (background real → S22/Fase F). `cancel`/`runtime_id` NO realizados en el skeleton (cancel→08·signals); `on_event` kwarg NO añadido (el `stream` ya emite el canal). Diferidos honestos, no fallos de costura.
- **productor:** el consumidor/integrador (`dispatch`/`stream`/`status`/`cancel`/`result`). **consumidor:** base default o integrador.
- **firma BORRADOR** (01·CTR-01):
  ```python
  class AgentRuntime(Protocol):
      async def dispatch(self, task: RuntimeTask, *, on_event: EventSink | None = None) -> str: ...  # task_id
      def stream(self, task: RuntimeTask) -> AsyncIterator[Event]: ...
      def status(self, task_id: str) -> TaskStatus: ...
      async def cancel(self, task_id: str) -> None: ...
      def result(self, task_id: str) -> ResultEvent | None: ...
  ```
- **ENRIQUECIMIENTO DECLARADO (`C8`, 2026-07-31) — `join(task_id) -> str | None`.** Un spawn en *foreground* es, por definición, el padre BLOQUEANDO en el hijo; con sólo `dispatch`/`status`/`result` la única forma de esperar era hurgar en el `asyncio_task` del registry, es decir **romper la costura por dentro** desde `S18`. `LocalAgentRuntime.join` espera la task y devuelve su `result`. Es adición, no cambio: ningún consumidor previo la necesita, y `S22 ForceAsyncPolicy` (quién decide fondo vs primer plano) sigue **ausente** y bajo la línea de corte.

### S6 · wire serializer `Event→SDKMessage` (battery `wire`)
- **estado:** `ausente` (07·GAP-EVT5; el factory no lo cablea, `factory.py:178-240`). **Costura de consumo externa por diseño** (NO huérfano).
- **productor:** el integrador con transporte fuera-de-proceso (BFF-SSE/REPL), suscrito a `subscribe_all`. **consumidor:** BFF/REPL cliente (`K4 convertSDKMessage` = el espejo).
- **firma BORRADOR:** `to_sdk_message(event: Event) -> dict` (24 variantes); produce también `init` (F0), `result` terminal (D1), `session_state` (F1).
- **validación A2:** A2.5 (integrador) puede consumir directo por `async for` sin wire; el wire se valida en Fase F (BFF).

### S7 · `on_progress` (tool-progress heartbeat)
- **estado:** `ausente` (07·C3/EVT6, 09·D10). **productor:** dispatcher/tool durante ejecución. **consumidor:** `EventBus` (`ToolProgressEvent`).
- **firma BORRADOR:** `on_progress: Callable[[ToolProgress], None]` pasado a `tool.execute`; requiere `run_shell` generador/callback (→10·Bash).

### S8 · `HookRunner` (fire points + hook-sink)
- **estado:** `existe-parcial` (cablea `PRE_TOOL_USE` `agent_loop.py:300-306`; faltan `STOP`/`SUBAGENT_STOP`(main)/`POST_TOOL_USE`/post-sampling).
- **productor:** el loop en las fronteras del turno (02·D3/D5/E2/F2). **consumidor:** el integrador registra hooks; el `HookRunner` emite progreso al `EventBus` (07·I1).
- **firma BORRADOR:**
  ```python
  class HookRunner(Protocol):
      async def run(self, event: HookEvent, payload: HookPayload, ctx: ToolUseContext) -> HookOutcome: ...
      # HookEvent: PRE_TOOL_USE(vivo) · POST_TOOL_USE · STOP · SUBAGENT_STOP · POST_SAMPLING (fire points ausentes)
      # HookOutcome: block | modified_input | prevent_continuation | passthrough
  ```
- **cabo:** el detalle de fire points + shape `Hook*Event` se desarrolla en **06·hooks** (A3); aquí se fija el punto y la firma.

### S9 · `CompactionProvider` (+ trigger del loop)
- **estado:** `existe-sin-motor` (el seam de aporte de providers existe, 01·CTR-09; **falta EL MOTOR**, 02·B6/GAP-L4).
- **productor:** el **loop** invoca el **trigger** (`should_compact`/`compact`, LR1 = base-mecanismo, `agent_loop.py:189`); el **motor** (battery) invoca `collect_compaction_context`. **consumidor:** providers concretos (battery/integrador).
- **firma BORRADOR:**
  ```python
  class CompactionProvider(Protocol):
      def collect_compaction_context(self, ctx: ToolUseContext) -> list[Message]: ...
  # motor (battery compaction): should_compact(ctx, usage) -> bool ; compact(ctx) -> CompactBoundary
  ```
- **emite:** `CompactBoundaryEvent` (07·H1). **consumidor de trigger:** overflow del motor (16·C2, `is_context_overflow`).
- **cabo:** el motor completo (trigger/microcompact/snip/collapse/budget) es la **battery `compaction`**, hogar 02·loop.

### S10 · `RetryPolicy` / `with_retry` (+ fallback de modelo)
- **estado:** `ausente` (16·B1-B3, 02·C4). **NO va en `agentic_models`** (lib de una request por diseño): es battery en el loop.
- **productor:** el loop envuelve `complete()` (`_attempt_with_fallback`, LR2). **consumidor:** **battery `resilience`** + config del integrador/caller.
- **firma BORRADOR:**
  ```python
  class RetryPolicy(Protocol):
      async def with_retry(
          self, call: Callable[[], AsyncIterator[Event]], *, fallback_model: str | None
      ) -> AsyncIterator[Event]: ...   # 10× backoff+jitter+retry-after ; 529→fallback ; streaming→non-streaming ; idle-watchdog
  ```
- **emite:** `ApiRetryEvent` (07·J3). **descarta parciales** al reintentar (respeta 02·C11 buffer-then-commit).

### S11 · `UserInputProcessor`
- **estado:** `existe-sin-poblar` (01·CTR-12/GAP-01: exportado, **ningún consumidor lo invoca**; el canónico `query` sí preprocesa).
- **productor (a cablear):** el `AgentLoop` **pre-turno** (01·CR2 — el CORE-GAP es este cableado). **consumidor:** battery `commands` (12) / processor del integrador.
- **firma BORRADOR:** `async def process(self, input: UserInput, ctx: ToolUseContext) -> ProcessedInput | ShortCircuit` (un slash-command corta el turno sin ir al modelo).
- **validación A2:** A2.1 stub (passthrough); el cableado real del loop se valida cuando entre la battery commands (A3·12).
- **⚠ DIVERGENCIA DECLARADA, resuelta por `D-08` leyendo el canónico (`C4`, 2026-07-31):** la firma vigente **no** es
  la unión `ProcessedInput | ShortCircuit` de este borrador, sino **un único resultado con booleano**:
  `async def process(self, prompt: str, ctx: ToolContext) -> ProcessedInput`, con
  `ProcessedInput(prompt, short_circuit=False, result_text=None)`. Tres fuentes independientes coinciden y el borrador
  es la única que discrepa: (1) el canónico `utils/processUserInput/processUserInput.ts` (605 L, leído 1→EOF) devuelve
  **siempre** `ProcessUserInputBaseResult` con `shouldQuery: boolean` —los caminos de corte (`:439-448` comando
  bridge-unsafe, `:198-208` hook bloqueante) devuelven `shouldQuery:false` **con los mensajes ya poblados**—;
  (2) el walking skeleton A2 lo validó **corriendo** con esa forma (`skeleton/seams.py:83-99`, grado G1);
  (3) `TRAMO-1 §C4`. Motivo de fondo: la unión obligaría al loop a ramificar el tipo ANTES de escribir el historial, y
  el canónico hace lo contrario —empuja los mensajes en los **dos** caminos (`QueryEngine.ts:431`) y sólo después mira
  `shouldQuery` (`:556`)—, de modo que un slash-command resuelto **no borra de la conversación que el usuario lo
  escribió**. Mimarlo con una unión habría perdido ese orden.
- **⚠ diferidos ENTEROS y nombrados (`L07`), no troceados:** el canónico devuelve además `allowedTools`/`model`/
  `effort`/`nextInput`/`submitNextInput`. Son **política del integrador**, van con la battery `commands` (bajo la
  línea de corte, `TRAMO-1 §3·B`) y **no** se han añadido a medias al contrato.
- **estado tras `C4`:** `existe-fiel` — cableado **pre-turno** en `agent_loop.py:211` por constructor (`S27`),
  poblado desde `RuntimeConfig.input_processor` → `LocalAgentRuntime` → `AgentLoop`, default
  `NoopUserInputProcessor` (identidad exacta) y Protocol `@runtime_checkable` (paga `FIND-01` para esta costura).
  Acreditado con violación inyectada: descablear el `process()` pone rojos los dos tests de comportamiento.

### S12 · `PathPresentation` (sanitize choke)
- **estado:** **`existe-parcial`** (corregido por A3.CAT; antes `existe-fiel`, que contradecía la línea siguiente de este
  mismo bloque). `sanitize_output` **sí** cableado (`dispatcher.py:42` + `runtime.py:244`); **`to_llm` sin call-site** ⇒
  bajo la convención del encabezado, un miembro sin productor es `existe-sin-poblar` ⇒ la costura, en conjunto, es
  **parcial**. Añade la corrección de `17·§2.7.1`: el saneo per-chunk de la salida hablada **rompe secuencias a caballo
  entre chunks** (`CG-V4`/`FIND-VOICE1`, `tests/test_voice_homologation.py:54-78` `xfail(strict=True)`) ⇒ al extraer la
  battery de voz, el saneo pasa a método de **S31** (`BATTERIES §4.5`).
- **productor:** `tools/dispatcher.py:42` (todo `output` pasa antes de `ctx.messages` Y EventBus, 09·D9). **consumidor:** base default `IdentityPresentation` (no-op bajo identidad) / integrador.
- **firma BORRADOR:** `sanitize_output(text: str) -> str` (+ `to_llm(path)->str` latente, cablear o borrar). 【id-opaco: no filtrar rutas reales del contenedor】.
- **estado tras `C5` (2026-08-01) — ENTRADA CORREGIDA EN LA MISMA VENTANA, ver §nota al final:** sigue **`existe-parcial`**.
  `to_llm` deja de estar **sin poblar** (ya tiene productor real), pero eso NO promueve la costura a `existe-fiel`: `17·§2.7.1`
  dice por escrito que S12 **está sobre-declarada** mientras `runtime.py:244` sanee **per-chunk** (`CG-V4`/`FIND-VOICE1`) y el
  default `IdentityPresentation` sea **no-op** (invariante vacuo salvo inyección → `OI-VOICE-2`). Eso sigue igual hoy.
- **la disyuntiva «cablear o borrar» se resuelve CABLEAR, con el motivo correcto.** `01·CTR-11` ya tenía clasificado `to_llm`
  como **extensión de B sin contraparte canónica**, DEUDA-B **interna**, NO deuda A↔B (`L10`) — verificado ahora leyendo el
  anclaje, y confirmado por grep exhaustivo en `claude-code/src` (`toLlm`/`PathPresentation`/`fakePath` = **cero**). `09·D9`
  habla **sólo** de `sanitize_output`; `to_llm` no aparece en él. Los consumidores son los integradores **`agentic_code` y
  `agentic_assistant`, planificados para después de esta refactorización**: la costura se cablea por el mismo criterio que
  `subagent_runner_factory=lambda _rt: None` — productor poblado, consumidor **vacío por diseño** hasta que existan.
- **SEIS puntos de emisión de ruta HOST, no cuatro (y menos tres):** `tools/native/write_file.py:38`, `glob_tool.py:40`,
  `grep_tool.py:68` (una vez por archivo, no por línea), **`clone_repository.py:149`** y **`worktree.py:138` + `:211`**.
  Los dos de `worktree` aparecieron en el barrido POSTERIOR, cuando el usuario señaló que sólo se habían ajustado 8 de las
  18 tools: interpolaban la ruta host cruda (`f"Created worktree at {worktree_path}…"`, `f"…Path: {path}"`) y además la
  tool esquivaba `S14` (destino compuesto a mano, sin allow-set) y `S15` (git por `create_subprocess_exec` directo).
  Acreditados por `E7e` con DOS violaciones inyectadas (quitar `to_llm` ⇒ rojo con la ruta host literal; devolver `_run` al
  subproceso directo ⇒ rojo con la costura vacía, `seen == []`); revert desde copia propia verificado con `sha256 -c`.
  **Recuento firmado dos veces y equivocado las dos** (3, luego 4): el barrido por ejes —quién resuelve, quién ejecuta,
  quién emite— sólo se hizo entero a la tercera. El de `clone_repository` es el que peor pinta tiene:
  el path host absoluto viaja en el `argv` de `git clone`, así que **git lo imprime** (`Cloning into '/ruta/host/…'`) y ese
  stdout se devuelve al modelo — la ruta no la escribe el runtime, luego `to_llm(Path)` no bastaba. Se traduce por el string
  **literal** que se le pasó a git (exacto, no heurístico), y NO se deja a `sanitize_output`, que es una red de regex con
  pérdidas. Acreditado por `E7d` con violación inyectada (quitar el `.replace` ⇒ rojo con la ruta host en el payload; revert
  desde copia propia verificado con `sha256 -c`). NO se cablea en `read_file` (no emite ruta) ni en `file_edit` (devuelve el
  string de entrada tal cual).
- **§nota de honestidad.** La primera versión de esta entrada (commit `724bc90`) decía «`existe-parcial` → `existe-fiel`» y
  justificaba el cableado en que `new_core/.../path_presentation.py` era «el integrador containerizado» que quedaría huérfano.
  **Las dos cosas eran falsas**: `new_core`/`agent_core` es un proyecto **muerto** (última actividad 2026-07-10) y no se
  retoma, y `17·§2.7.1` prohibía `existe-fiel` por escrito. El error de método fue no aplicarle a `to_llm` la misma prueba que
  sí le apliqué a `ends_turn` (sin homólogo en A ⇒ carga de la prueba invertida): me paré en «un integrador lo implementa» sin
  comprobar si ese integrador existía. Los tres anclajes (`01·CTR-11`, `09·D9`, `17·§2.7.1`) estaban **sin abrir** cuando
  firmé aquello; ahora están leídos y son la fuente de esta entrada.

### S13 · `StorageContract` (roots + traducción token→path)
- **estado:** `existe-fiel` (consumido por plan_file + `fs_env.py:124` + `_persist` de execution). **Unificar con `StorageProtocol` de 15.**
- **productor:** fs-tools/`ConfinedFilesystem` (S14), plan_file, `_persist`. **consumidor:** el integrador (FS local degenerado / adaptador MinIO). 【id-opaco: clave = repo genérico sobre metadata del integrador】.
- **firma BORRADOR:**
  ```python
  class StorageContract(Protocol):
      def real_path(self, token: str, *, for_write: bool) -> HostPath: ...   # token opaco → path host
      async def ensure_local(self, token: str) -> HostPath: ...
      async def commit(self, token: str) -> None: ...
  ```
- **cabo:** solape con `StorageProtocol` (15) → resolver al documentar 15; transcript/metadata de subagente (05·E7) usan la misma costura.

### S15 · `ToolExecEnvironment` (backend de shell inyectable)
- **estado:** `existe-fiel` (costura AÑADIDA sin contraparte canónica; seam VIVO `bash.py:27` ← `factory` → `ctx.exec_env`).
- **productor:** `BashTool.execute` (`exec_env.run_shell`). **consumidor:** `LocalExecEnvironment` (default, subproceso fresco) / integrador (bwrap/remoto/sandbox real).
- **firma BORRADOR:**
  ```python
  class ToolExecEnvironment(Protocol):
      async def run_shell(self, command: str, *, timeout: float | None = None) -> ShellResult: ...
  # ShellResult: output(combinado) + returncode — enriquecer con stdout/stderr/interrupted/background_task_id (09·F4 → 10)
  ```
- **cabo:** shell persistente (09·F2 → 10·R8), política de sandbox (09·F3 → integrador OI-20).
- **estado tras el barrido de las 18 tools (2026-08-01): ENRIQUECIDA con `run_argv(argv, *, cwd, timeout)`.** La costura
  sólo cubría `bash`; `worktree.py` lanzaba git con `asyncio.create_subprocess_exec` **directo**, así que con un
  `BwrapExecEnvironment` inyectado `bash` quedaba aislado y `EnterWorktree` corría git **en el host**. `E7b` no lo cazaba
  porque sólo acreditaba `bash`. Enriquecimiento declarado, mismo patrón con que `S4` ganó `join(task_id)` y `S18` pasó a
  `SubagentSpec`. Es `run_argv` y **no** `run_shell` a propósito: el argv lleva un nombre de rama que viene del MODELO, y
  serializarlo a string de shell cambiaría una fuga de ruta por una **inyección de comandos**. `BwrapExecEnvironment`
  **traduce** el `cwd` host → `/workspace/…` y **rechaza** un `cwd` fuera del montaje en vez de ignorarlo (ignorarlo es el
  modo de fallo «autorizar una cosa y ejecutar otra» de `FIND-C6-1`). Segundo productor: `worktree.py:_run`.
  **Cabo declarado y NO pagado (`L07`):** `run_argv` traduce el `cwd`, **no** los paths que viajan dentro del `argv`.
  `worktree.py` lo esquiva pasando paths **relativos** al `cwd`; cualquier tool futura que necesite un path absoluto en el
  argv bajo bwrap necesitará un `to_exec_env(path)` en la costura, que hoy no existe.

### S16 · `ToolProtocol` (contrato de tool)
- **estado:** `existe-enriquecer` (8 miembros; faltan miembros de **comportamiento**, no de render).
- **productor:** `create_tools`/`registry.register` (batteries/MCP/skills registran). **consumidor:** cada tool concreta + adaptador MCP (11) + integrador (extras).
- **firma BORRADOR** (mínimo + campos a crecer):
  ```python
  class ToolProtocol(Protocol):
      name: str
      input_schema: dict                       # JSON-Schema (validado por agentic_models)
      def description(self, input: dict | None = None) -> str: ...   # 09·A2 (hoy str fijo)
      async def execute(self, input: dict, ctx: ToolUseContext) -> ToolResult: ...
      # A CRECER (comportamiento): is_concurrency_safe(input) 09·A3 · interrupt_behavior 09·A4 ·
      #   is_read_only/is_destructive/check_permissions(input,ctx) 09·A6/A7/A8 (→S17) · validate_input 09·A9 ·
      #   aliases 09·A11 · search_hint 09·A12 · output_schema 09·A15
  # ToolResult: output:str + is_error/is_timeout/is_aborted + metadata
  #   A CRECER: new_messages 09·A23 · context_modifier(ctx) 09·A24 (ya aplicado agent_loop.py:332-337, declarar) · structured 09·A22 · mcp_meta 09·A25
  ```
- **estado tras `C5` (2026-08-01): `09·A24` DECLARADO — `FIND-TOOL4` PAGADO.** `ToolResult` declara ahora **dos** miembros que
  antes se **inyectaban por monkeypatch** con `type: ignore[attr-defined]` desde **9 call-sites** y se leían por `getattr` en el
  loop: portantes en producción pero invisibles para cualquier tercero que implemente el contrato. Los 9 monkeypatch están
  RETIRADOS (`plan_mode.py` ×3, `worktree.py` ×2, `todo_write.py`, `config.py`, `ask_user.py`, `skills/skill_tool.py`) y hoy son
  kwargs del constructor; `agent_loop.py:453-465` los lee como miembros.
  - `context_modifier: Callable[[Any], Any] | None = None` — grafía exacta de `Tool.ts:330` (`contextModifier?`, **opcional**,
    leído 1→EOF). A lo honra *sólo* para tools no concurrency-safe; el tramo 1 corre en **serie**, así que aquí se honra sin
    condición: correcto-para-serie y **declarado** — cuando entre la concurrencia, este es el punto que vuelve a abrirse. El tipo
    es `Any` **a propósito**: `contracts/` no puede nombrar el `ToolUseContext` del base (invariante que `test_contracts_invariant`
    vigila **incluso bajo `TYPE_CHECKING`** — el intento de importarlo así puso el test en rojo). El alias preciso vive en el base.
  - `ends_turn: bool = False` — **NO tiene homólogo canónico**: `endsTurn` no existe en A (grep = cero). Es **extensión declarada
    de B**, no des-fusión acreditada: A cede el turno bloqueando en `checkPermissions → behavior:'ask' + updatedInput` (verificado
    1→EOF en `AskUserQuestionTool.tsx` 266 L, cuyo `call()` devuelve **sólo** `data`), y esa capa es `GAP-02`/`K1`, **por encima de
    la línea de corte**. Queda atada a ella: cuando `check_permissions` entre, `ends_turn` se re-examina contra ella y no antes.
    Se corrigió además el comentario de `plan_mode.py` que lo vendía como espejo de `requiresUserInteraction()`.
- ✅ **RETIRADO el doble-camino (2026-08-01, TERCERA CORRECCIÓN).** `NativeToolRegistry` (tercer registro junto a `ToolRegistry` y
  `ToolPool`, cero call-sites de producción) **borrado**, no diferido — decisión cerrada leyendo (`09·TiR4` → `11:645-655`: el
  hot-plug MCP es reensamblado del pool por turno, no registro dinámico; su única condición de supervivencia, el swap push-based de
  `FIND-MCP4`/`McR2`, verificada **ausente en el código**). Retirado también del `__all__` **raíz**: en la superficie pública era la
  forma de `FIND-EXEC1` pre-empaquetada para integradores. Test **invertido**, no borrado ⇒ reintroducirlo se pone rojo. Con él cayó
  `ToolRegistry.list_available(permission_ctx=…)` (parámetro muerto: insinuaba un segundo sitio donde se filtra por permisos, cuando
  el gate vive aguas abajo — `assemble_tool_pool` + `resolver.py:40` `denied_names()`).
- **acreditación del DESCUBRIMIENTO y de la SOLVENCIA (2026-08-01, cuarta corrección):** `E2c`/`E2b` sólo acreditaban
  que el mecanismo sabe **esconder**. `E2e` cierra la ida y vuelta sin modelo: `ToolSearch(select:…)` por el dispatcher
  real ⇒ la descubierta pasa a anunciarse en el turno siguiente **y sólo ella** (el descubrimiento es por tool, no un
  interruptor global), con el **schema completo** en el resultado — sin él «descubierta» sería una etiqueta: el modelo
  sabría el nombre y no cómo llamarla. `E2f` mide la **solvencia**: enunciado de OBJETIVO (no de herramienta),
  centinelas `uuid4` por corrida y escenarios barajados, así que un acierto no puede venir del conocimiento paramétrico
  ni de una corrida anterior. Acreditado con **violación inyectada** (SERP con un código distinto ⇒ rojo), que además
  midió que con 24 tools delante el modelo **sí elige `WebSearch`** y **se niega a fabricar** el dato que no cuadra.
- **acreditación de la SOLVENCIA CON `ToolSearch` (2026-08-01, `E2g`) — y la rama que de verdad se toma:** `E2e` guionaba la
  llamada a `ToolSearch` con un caller de mentira y `E2f` corre con las 24 anunciadas, así que **ningún test tenía al modelo
  decidiendo buscar**. `E2g` lo cierra: se difiere el **conjunto entero** de tools capaces de resolver el objetivo (diferir una
  sola dejaría resolver por la alternativa sin tocar `ToolSearch`) más **2–3 señuelos aleatorios** del censo, para que el search
  tenga que **discriminar**. Al escribirlo salió un hallazgo que cambió el diseño: **`agent_loop.py:168-186` elige la estrategia
  por capability del provider**, y el `gpt-5` de Azure declara `native_tool_search=True` (`caller.py:151`) ⇒ toma
  `NativeDeferredStrategy`, que anuncia **todas** con `defer_loading=True` y **retira `ToolSearch`**
  (`deferred_strategy.py:87-88`) — es decir, la rama que el runtime usa en producción con este modelo **no era la que se estaba
  probando**. `E2g` corre **las dos, aseverando las dos**: la simulada se selecciona por su **entrada documentada** (un caller que declara
  `supports_native_tool_search() → False`, caso real de todo provider de terceros) con `complete` delegado **intacto** en el
  Azure real, sin parchear la estrategia. Acreditado con **violación inyectada** (`mark_tools_discovered` deja de marcar ⇒ rojo),
  que midió el eslabón exacto: el modelo **sí llama a `ToolSearch` por su cuenta** y, rota la disponibilidad de la descubierta,
  **se niega a fabricar** el dato.
- **⚠ `FIND-E2G-1`, medido, ABIERTO y vigilado por el gate (no diferido):** el tool-search **server-side** de esta deployment se
  mostró **menos solvente** que el `ToolSearch` client-side del runtime: en las 6 primeras corridas el caso `archivos/nativa`
  falló **2** (con `grep`/`bash`/`read_file` diferidas server-side el modelo tiró de `AskUserQuestion` y devolvió respuesta
  vacía) mientras la simulada resolvía **6 de 6**. La primera versión de `E2g` sólo lo **imprimía** — un colchón, retirado: la
  rama nativa **no es ajena al runtime**, es la que el runtime **elige** cuando el catálogo declara `native_tool_search=True`
  (`agent_loop.py:168-186`, `caller.py:151`), así que su solvencia es consecuencia de una decisión del sujeto y **se asevera**.
  Con el listón en las dos ramas van **12 de 12** en verde: **no está arreglado**, es intermitente y no se ha reproducido, pero
  ahora es load-bearing — si vuelve, el gate se pone rojo. Además se exige lo que el runtime posee sin discusión:
  `defer_loading=True` en el cable y `ToolSearch` client-side retirado, con `openai_responses_shared.py:225,231-232` **leído**
  (emite el flag y añade `{"type":"tool_search","execution":"server"}`).
- **⚠ falso positivo en la instrumentación de los tests, PAGADO (2026-08-01):** `E2d`/`E2f`/`E2g` contaban lo elegido con un
  substring sobre el historial serializado. El **resultado de `ToolSearch` transporta los nombres de sus coincidencias** —los
  señuelos incluidos— así que menciones contaban como invocaciones y `selected & must_use` podía cumplirse **sin que el modelo
  llamara a nada**. Sustituido por `_invoked_tool_names`, que lee `msg["tool_calls"][*]["function"]["name"]` (`agent_loop.py:401-403`).
  Medido con el contador honesto: unión de **14 de las 25** tools del censo invocadas por el modelo; las 11 restantes
  (`AskUserQuestion`, `Config`, `Edit`, `EnterWorktree`, `ExitWorktree`, `TaskList`, `TaskOutput`, `TaskStop`, `TodoWrite`,
  `WebFetch`, `clone_repository`) están **anunciadas y barridas**, pero **ninguna corrida medida las condujo**.
- **⚠ `FIND-E2G-2`, medido, NO atribuido y nombrado (`L07`):** 1 de 6 corridas murió con `CancelledError` **esperando el stream del
  modelo** (`event_stream.py:55` ← `caller.py:286` ← `agent_loop.py:348`). **Nada del runtime cancela**: `arm_watchdog` es un
  **no-op** (`registry.py:89-92`) y el default es 300 s, pero murió a ~100 s. `E2g` ya no revienta con un error opaco de asyncio:
  captura el `CancelledError` —legítimo, porque `await` sobre una tarea **ajena** cancelada lo relanza en quien espera sin
  cancelarlo a él— y lo reporta como fallo del caso **con las tools que el modelo había elegido antes de morir**.
- **⚠ `S26` no tiene sujeto nativo en producción:** **ninguna** tool nativa marca `deferred` (`grep -c "deferred = True"
  tools/native/*.py` = **cero**). El único sujeto real es MCP (`capabilities/mcp/tool_adapter.py:30`, a mano), tal como
  `09·E1` anticipaba. Lo que difiere `WebFetch`/`WebSearch` en el canónico es `shouldDefer` dentro de la precedencia de
  `isDeferredTool` (`prompt.ts:62`) = `GAP-TOOL3`/`09·TiR5`, **no implementada** ⇒ `E2e` **configura** el runtime como
  el canónico lo configura y lo declara en su cabecera, en vez de fingir que el sujeto ya existía.
- **acreditación del censo (2026-08-01):** `E2c`×2 congela el censo **en literal** —25 tools en **18 módulos**— y lo asevera contra
  `create_tools()`; el anuncio se prueba en **sus dos ramas** (24 siempre · `ToolSearch` **sii** hay una diferida en el pool, tal como
  `deferred_strategy.py:64-66` espeja al canónico; esta rama puso el test ROJO en su primera corrida y la aserción equivocada era la
  mía). `E2d` prueba la **selección por el modelo** con el censo entero anunciado, separando ANUNCIADO (`calls[*].tools`) de ELEGIDO
  (`calls[*].messages`). Añadir una tool sin barrerla pone `E7f` en rojo.
- **✅ `FIND-C6-2` PAGADO (10ª ventana):** que `asyncio.wait_for` no acote a una corrutina que no cede **no es deuda** (A tiene la misma
  propiedad y ni siquiera tiene cap genérico por tool); la deuda era que `web_fetch`/`web_search` **fueran** esa corrutina, con `urlopen`
  síncrono dentro de su `async def`. Arreglado con `asyncio.to_thread` en ambas ⇒ el cap vuelve a valer lo que promete y el loop deja de
  congelarse. Su `xfail` anterior acreditaba **en falso** (`H-L4`): reventaba en `ToolUseContext(...)` antes de llegar a `dispatch`.

### S17 · `PermissionGate` (`check_permissions` por-input + modos)
- **estado:** `existe-parcial` (el gate del dispatcher es deny-por-nombre `dispatcher.py:62-65`; el **seam input-aware VIVE** en `PRE_TOOL_USE` `agent_loop.py:300-313` honrando `block`/`modified_input`; falta `check_permissions` per-tool + modos).
- **productor:** el loop dispara `PRE_TOOL_USE(tool_name, tool_input, call_id, ctx)`; el dispatcher chequea. **consumidor:** el **integrador** provee la política (modos `default`/`acceptEdits`/`plan`/`bypass`, deny/allow rules, ask/HITL, suggestions).
- **firma BORRADOR:**
  ```python
  # per-tool (crece en S16): def check_permissions(self, input, ctx) -> PermissionDecision  # allow|ask|deny + updated_input + suggestions
  # gate del loop (política del integrador vía hook PRE_TOOL_USE, S8):
  class PermissionContext:   # 01·CTR-07/CTR-08 — T1-CONTRATO
      mode: PermissionMode   # default|acceptEdits|plan|bypassPermissions (01·CTR-08, hoy hack app_state.native["plan_mode"])
      rules: ResolvedRules   # allow/deny resueltas (scope de persistencia = integrador)
  ```
- **cabo:** el algoritmo `agentGetAppState` (override permMode hijo, scoping `allowedTools` anti-fuga) → 05·E20/02·F2; ripear hack `plan_mode` = DEUDA-B `B-02`; safety-fs (09·G8) → 10·R3. Hogar del desarrollo = **06·hooks** (A3).

### S18 · `SubagentRunnerProtocol` — ✅ VALIDADA-CORREGIDA en A2.5 · **PAGADA en `C8` (2026-07-31)**
- **estado (2026-07-31):** ✅ **poblada por DI**. `FIND-EXEC1` cerrado: `RuntimeConfig.subagent_runner_factory` → `LocalAgentRuntime(runner_factory=…)` → `self._runner` → `ctx.runner` (threadeado en `_run_loop`, punto único por el que pasan raíz y fork) → `AgentTool` lee `ctx.runner`. El global `_runner`/`set_runner`/`get_runner` está **retirado del código**. Se inyecta una **factory** `(runtime) -> runner`, no el runner ya construido, porque el runner tiene que despachar EN el runtime que lo posee: un cableado en dos tiempos es exactamente lo que un ensamblador puede olvidar, que es el modo de fallo de `FIND-EXEC1`. `subagent_runner_factory=lambda _rt: None` deja la costura vacía **a propósito** (distinto de olvidarla) y `AgentTool` devuelve `is_error` limpio.
- **DIVERGENCIA DECLARADA (`L10`) frente al `SubagentSpec` mínimo de A2.5:** el spec lleva además `parent_snapshot: ForkSnapshot | None` e `inherit_messages: bool`. El skeleton no ejercitaba el fork-de-historial ni la herencia de permisos/tool_pool/capabilities, pero la mímica sí las tiene, y sin el snapshot el hijo no puede heredar `scope`/permisos/`capabilities` del padre: sería el runtime COMPONIENDO identidad (`D-11`), no transportándola. `background=True` **ya no lanza `NotImplementedError`**: el `dispatch` es genuinamente fire-and-forget y `run` devuelve el `task_id` (acreditado por `E9`). `S22 ForceAsyncPolicy` —quién DECIDE el fondo— sigue **ausente** y bajo la línea de corte: no se simula.
- **estado histórico:** `existe-sin-poblar` (05·E24/FIND-EXEC1: `set_runner` sólo en test; `get_runner()` lanza `RuntimeError` en **todo** spawn — el **crítico de cableado** de la espina, pero DEUDA-B, no gap A↔B).
- **productor:** `AgentTool.execute` (`agent.py:105` `get_runner().run`). **consumidor:** `LocalAgentRuntime.dispatch` vía adaptador.
- **firma BORRADOR** (a reconciliar en A2):
  ```python
  class SubagentRunnerProtocol(Protocol):
      async def run(self, fork_ctx: ForkContext, *, background: bool) -> str | None: ...
  # adaptador: ForkContext → RuntimeTask ; cablear set_runner en factory.create_runtime (18·C1)
  ```
- **validación A2 (A2.5, turno real end-to-end padre→subagente · `skeleton._integrador`):** la costura AGUANTA en efecto (adaptador `SubagentSpec`→`RuntimeTask`, poblado por el factory), pero el **MECANISMO se CORRIGIÓ** (🔀, no bug; ver `SKELETON-REPORT.md` §S18):
  - **`fork_ctx: ForkContext` → `spec: SubagentSpec`** (dataclass frozen mínimo: prompt/subagent_type/model_override/parent_session_id opaco). El "fork" (hijo hereda historial completo) NO se ejercita en A2.5 — sólo el spawn con prompt propio; el fork-de-historial → Fase C/F.
  - **`set_runner/get_runner` (singleton GLOBAL) → deps-DI (S27)**: **VERIFICADO POR FUENTE 1→EOF (2026-07-23)**: `execution/runner.py` (`_runner` global L28, `get_runner()` lanza `RuntimeError` si `None` L36-41, `set_runner` lo puebla L31-33) · `tools/native/agent.py:105` (productor: `get_runner().run(fork_ctx, background=…)`) · **`factory.py` L178-240 `_build_local` leído íntegro: ensambla `LocalAgentRuntime` con TODAS las deps inyectadas y NO llama `set_runner` ni construye runner alguno** ⇒ el seam está genuinamente roto (FIND-EXEC1 confirmado por el ensamblador, no por grep). El fix: el runner se inyecta al `LocalAgentRuntime` por constructor y éste lo threadea al `ctx`; `AgentTool.execute` lee `ctx.runner`. **Retirar la nota "cablear `set_runner` en factory" — el patrón correcto es DI.** **CORRECCIÓN a una afirmación previa mía:** este fix elimina la fragilidad del **global del runner (S18)**, NO el "doble-camino" del **registry (S19)** — dos globals distintos; el skeleton A2.5 no tiene TaskRegistry, no toca S19.
  - **carga probada (L09):** prueba NEGATIVA en `_integrador` — un runtime SIN el cableado del factory (`runner=None`) hace que `AgentTool` devuelva `is_error` ("not wired") ⇒ la costura es load-bearing; el turno real prueba que el factory SÍ la puebla (padre delegó → subagente real sumó 42 → aplanado y citado).
  - **`background`:** el camino fire-and-forget NO se ejercita (declarado; `LocalSubagentRunner.run(background=True)` lanza `NotImplementedError` apuntando a S22 force-async + daemon del integrador, Fase F). L09-inverso: no se finge camino muerto.

### S19 · `TaskRegistryProtocol` (repo genérico id-opaco) · **DOBLE CAMINO CERRADO en `C7` (2026-07-31)**
- **estado (2026-07-31):** ✅ **camino único**. `registry.py` ya no tiene `_registry`/`set_registry`/`get_registry`; las tools nativas leen `ctx.task_registry`, threadeado por `_run_loop` desde la instancia que el runtime posee. Ya no pueden divergir porque ya no hay dos. `TaskRecord` sigue SIN enriquecer (`type/kind`, `notified`, `output_file/offset`, `pending_messages`): diferido entero y nombrado (`L07`).
- **estado histórico:** `existe-doble-camino` (05·`B-registry-dual-path`: `LocalAgentRuntime` usa instancia inyectada `runtime.py:63/86`; las tools nativas usan el global `get_registry()` `task_tools.py:29/54/113/187` — pueden divergir).
- **productor:** `LocalAgentRuntime` (register/get/kill/complete) + tools nativas. **consumidor:** `InMemoryTaskRegistry` (default) o repo del integrador. 【id-opaco: reifica `.id` de la task; el scoping (`session_id`) es metadata del repo — patrón pi `SessionRepo`】.
- **firma BORRADOR:**
  ```python
  class TaskRegistryProtocol(Protocol):
      def register(self, record: TaskRecord) -> None: ...
      def get(self, task_id: str) -> TaskRecord | None: ...
      def list(self, *, scope: Mapping | None = None) -> list[TaskRecord]: ...   # scope = metadata del integrador
      async def kill(self, task_id: str) -> None: ...            # 05·E10 + StopTaskError codes
      def get_by_type(self, task_type: TaskType) -> ...          # 05·E32 dispatch polimórfico (falta kind/type)
      def arm_watchdog(self, task_id: str, timeout: float | None) -> None: ...   # S24 (default no-op)
  # TaskRecord A CRECER: type/kind (E32) · notified (GAP-EXEC1) · output_file/output_offset (E9) · pending_messages (E36)
  ```
- **cabo:** unificar el doble camino (DEUDA-B); enriquecer `TaskRecord` (05·E9).

### S20 · `SessionRepo` (repo genérico id-opaco de sesión) — 【NIDO DEL HILO TRANSVERSAL DE IDENTIDAD】
- **estado:** `existe-mímica` (05·E30: `Session`/`Usage`/`SessionMetadata` reifican identidad single-user; el `_build_child` autogenera `session_id or "sess_…"`/`owner_id or "user_…"` = mímica a ripear).
- **productor:** el driver de sesión (`LocalAgentRuntime`). **consumidor:** el integrador (degenerado = default single-session scope-por-cwd; complejo = repo multi-tenant sobre MinIO). **El runtime lee sólo `session.id` opaco.**
- **firma BORRADOR:**
  ```python
  class SessionRepo(Protocol[TMetadata]):        # genérico sobre la metadata del integrador
      def create(self, metadata: TMetadata) -> SessionId: ...
      def open(self, session_id: SessionId) -> SessionHandle: ...
      def list(self, query: TMetadata) -> list[SessionInfo]: ...   # 07·K5 SDKSessionInfo (índice → 15)
      def delete(self, session_id: SessionId) -> None: ...
      def fork(self, session_id: SessionId) -> SessionId: ...
  class RuntimeSessionProtocol(Protocol):        # lo que el runtime SÍ lee
      @property
      def id(self) -> str: ...                   # OPACO — nunca userId/sessionId interpretado
  ```
- **validación A2:** A2.4/A2.5 corren un turno **sin conocer userId**; el integrador lista/scopea por su metadata. **Funda el rollup transversal DEUDA-A** (consolidación en A3.DA — no se resuelve categoría a categoría).

### S21 · `NotificationSink` (drain/process del canal `<task-notification>`) — ✅ VALIDADA (put+drain) en A2.5 · **CORE-GAP `H-5` PAGADO en `C8` (2026-07-31)**
- **estado (2026-07-31):** ✅ **put + drain + apply, con call-site**. El drenaje es un **paso propio del `AgentLoop`** (`_drain_notifications`), como prescribía `AC-h3`: corre en `run()` tras los turn-start hooks y **antes** del mensaje del usuario y de `_inject_recall`, porque son hechos ya ocurridos. Frecuencia: una por `run()` = una por prompt de usuario = la del canónico (`query.ts:1631-1633`).
  - `contracts/notifications.py` (nuevo): `BackgroundNotification`, `NotificationSink` (`put`/`drain`), `render_notification` y **`apply_notification(messages, n)`** — la firma que `AC-07` prescribió en sustitución de `process_background_notification(session, n)`, que escribía sobre `session.messages` (sumidero de copia que `_run_loop` reasigna) y por eso **descartaba el XML en silencio** (`AC-h5`). `process_background_notification` está **retirada**; los 7 tests que verificaban la función se reescribieron contra `apply_notification`.
  - El contrato vive en `contracts` (hoja del grafo) para que el loop no importe `execution.local`; el canal concreto y `InProcessNotificationSink` siguen en `execution/local/notification.py`, y `LocalAgentRuntime` lo inyecta por defecto (`RuntimeConfig.notification_sink` para sustituirlo).
  - **DEFECTO ENCONTRADO Y PAGADO EN LA MISMA VENTANA:** el fork hereda `session_id` **y** `scope` del padre, así que la clave del canal `(scope, session_id)` es **la misma** para padre e hijo ⇒ con el drenaje incondicional un subagente se comía la notificación de su hermano y el padre no se enteraba nunca. `_drain_notifications` sólo drena en la RAÍZ (`not ctx.is_subagent`); en el canónico las notificaciones entran por el input del usuario, que sólo la raíz tiene.
  - **acreditado por `E9`** (gate del tramo, E2E real): hijo de fondo real → `_notify` → canal → drenaje del turno siguiente del padre → `<task-notification>` **en el cable del modelo** → el padre cita el código; y el canal queda vacío tras aplicarla. Lo que `E9` NO deja al modelo es la **decisión** de lanzar en fondo (se pide por la costura): declarado, no disimulado. `TaskRecord.notified` sigue sin existir ⇒ la de-duplicación es «drenar consume», no una marca en el registro: diferido nombrado.
- **estado histórico:** `existe-put-sin-drain` (05·E5/LAT-EXEC2: el runtime **escribe** `put_notification` `runtime.py:299` pero **no se auto-drena**) — ~~delegación al integrador, 🔀, no bug~~.
- **⚠ TIER CORREGIDO en A-CIERRE·P0 (AC-h3, `SEAMS.md` abierto 1→EOF 2026-07-27).** El «🔀, no bug» quedó
  **refutado** por `DEUDA-B §9·RV-7` (= `DB-29`, CORE-GAP **`H-5`**, con `notification.py` y `agent_loop.py`
  abiertos 1→EOF): (a) el base **ya trae escrita la lógica genérica** (`process_background_notification`
  `:49-72` se declara a sí misma «comportamiento genérico del runtime») y **nadie la llama** — maquinaria
  completa sin su call-site es **capacidad ausente**, no delegación; (b) el docstring `notification.py:5`
  afirma *«el loop padre drena el canal al inicio de cada turno»*, lo cual es **falso** (`RV-5`: docstring ≠
  cableado); (c) consecuencia funcional dura — **el padre nunca se entera de que su subagente background
  terminó**; y de recurso — `_channel` es un `defaultdict(list)` de proceso que **sólo crece**.
  ⇒ estado real **`existe-put-sin-drain` = CORE-GAP `H-5`**, no 🔀. La remediación con los 6 campos se
  desarrolla en **A-CIERRE·P1 (AC-07)**; el seam de cableado recomendado **no** es `root_turn_start_hooks`
  ~~(que dispara **una vez por `run()`**, no por turno — el propio *cabo cross 02/07* de abajo ya lo decía)~~
  sino un paso propio del `AgentLoop` antes de componer el turno, porque el orden respecto de
  `_inject_recall` es observable.
  ⚠ **RAZÓN CORREGIDA en A-CIERRE·P1** (auto-corrección: el hecho de P0 era cierto, la inferencia era floja).
  Que `_run_turn_start_hooks` dispare **una vez por `run()`** (`agent_loop.py:176`, antes del bucle
  `for _turn in range(_MAX_TURNS)` de `:185`) **no descalifica el seam**: en el runtime un `run()` = **un prompt
  de usuario**, y el canónico drena **por prompt de usuario**, no por turno de modelo (`query.ts:1631-1633`, las
  notificaciones entran como *attachment* junto al input) ⇒ **la frecuencia coincide**.
  **La razón real, y es más fuerte: el hook está SUB-PARAMETRIZADO.** `_root_turn_start_hooks(task)`
  (`runtime.py:373`) recibe `task` y devuelve corrutinas **de cero argumentos** (`agent_loop.py:160`,
  `Callable[[], Coroutine[Any, Any, None]]`). Con `task` el integrador **sí puede drenar** (tiene
  `session_id`/`owner_id`), pero **no puede aplicar** lo drenado: `process_background_notification(session, n)`
  exige el `Session`, que se construye **dentro** de `_run_loop` (`runtime.py:331`) y **no se expone por ningún
  accesor**; y el hook tampoco recibe el `ctx` para tocar `ctx.messages`. **La delegación al integrador no está
  incompleta: es imposible.**
  ⚠⚠ **Y hay un segundo defecto, `AC-h5`:** aunque se cableara, `process_background_notification` **no podría
  funcionar** — hace `session.messages.append(...)` (`notification.py:68`) mientras `runtime.py:397` reasigna
  `session.messages = list(ctx.messages)` al terminar el loop ⇒ **el XML inyectado se descarta en silencio**. El
  `Session` del runtime no es el historial vivo, es un **sumidero de copia**. Por eso `AC-07` **retira** esa
  firma en favor de `apply_notification(messages, n)` sobre el historial vivo. Los 7 tests que hoy pasan
  (`tests/test_background_notification_channel.py:99-141`) verifican **la función**, no el comportamiento.
- **fuente mímica 1→EOF (2026-07-23):** `local/notification.py` (72 LOC) — canal global `_channel` scopeado por `(user_id, session_id)` L22; `put_notification` L36, `drain_notifications` L45, `process_background_notification` L49 (produce el XML `<task-notification>` + append al historial del padre). `execution/local/runtime.py` (1→EOF): `_notify`→`put_notification` cableado L294-304, invocado en las 3 ramas terminales (completed L413 / failed L392 / killed L385), gated por `parent_session_id`; **`drain_notifications` NO aparece en las 435 líneas** ⇒ el runtime escribe y NO se auto-drena — el drain lo hace el integrador vía `root_turn_start_hooks` (L372-374). LAT-EXEC2 confirmado por fuente.
- **validación A2.5:** el par COMPLETO put/drain probado — el `LocalSubagentRunner` (child) hace `put(Notification)` al completar; el integrador (`_integrador`) `drain()` tras el turno y recupera el resultado del subagente. **Shape reducido** (task_id/status/summary/result); `scope` declarado pero no filtra aún (Notification no lleva metadata scopeable → **05·E19**; *corregido en A-CIERRE·P4″ (`I4`): decía `07·E19`, un ID que **no existe** — el grid de 07 llega hasta `E5`. El dueño es 05, como ya lo dice la firma BORRADOR dos líneas más abajo*). Auto-drain in-loop (una vez por turno, no por `run()`) → sigue anclado en 07·events, NO se realizó aquí.
- **productor:** el child escribe (`put_notification`). **consumidor:** el integrador drena vía `root_turn_start_hooks` (`factory.py:106-112`→`runtime.py:372-374`→`agent_loop.py:176`) y presenta al padre/usuario.
- **firma BORRADOR:** `def drain(self, scope) -> list[Notification]` + shape XML `<task-notification>` (task-id/tool-use-id/output-file/status/summary/result/`<usage>`/worktree, 05·E19 → 07). 【id-opaco: scoped por metadata del repo】.
- **cabo cross 02/07:** el hook de turn-start se dispara **una vez por `run()`**, no una por turno como el drain canónico in-loop → ancla en 07·events, no aquí.

### S22 · `ForceAsyncPolicy`
- **estado:** `ausente` (05·E34: async sólo por `run_in_background` `agent.py:65`; falta `assistant_force_async`).
- **productor:** `AgentTool`/`dispatch` consulta. **consumidor:** el integrador fija la política (muy relevante a `agentic_assistant`: un subagente sync atasca el `inputQueue` del daemon).
- **firma BORRADOR:** `def force_async(self, task: RuntimeTask, ctx: ToolUseContext) -> bool` en `ctx.force_async_policy`/`RuntimeConfig` (NO flag por-call).

### S23 · `on_agent_teardown(agent_id)` (reaping de recursos hijos)
- **estado:** `ausente` (05·E35/FIND-EXEC11: `_run_loop` sin `finally` ni reaping ⇒ bash-bg zombies, leak de `todos[agentId]`, hooks/mcp del agente).
- **productor:** `_run_loop` `finally`. **consumidor:** 10 (bash-bg)/11 (mcp)/12 (skills) reap-ean lo suyo por `agent_id`. 【id-opaco: reaping por `agent_id`】.
- **firma BORRADOR:** `async def on_agent_teardown(self, agent_id: str) -> None` (cadena de callbacks registrados por battery/subsistema).
- **consumidores registrados (A-CIERRE.MCP 2026-07-30):** **`11·CG-MCP-20`** (`cleanup_for_agent(agent_id)` → clients stdio/http del agente, tokens en vuelo, tareas de reconnect; wiring en 05·ExR6/GAP-EXEC4 + 08·CG-SIG-8). *La sustancia ya estaba en 11 desde A3; lo que faltaba era el cable nominal en **las dos** direcciones — `§S23` no nombraba a `CG-MCP-20` y `11` no nombraba a `S23`, de modo que ni el auditor de 05 ni el de 11 podían ver que la costura tenía dueño. Los consumidores 10 (bash-bg) y 12 (skills) **siguen sin cable nominal**: comprobar al reconciliar esos pares.*

### S24 · `arm_watchdog` (timeout/watchdog de task)
- **estado:** `existe-noop` (01·CTR-15/05: `dispatch` llama `arm_watchdog(task_id, task.timeout_seconds or default)` `runtime.py:149`, pero el default `InMemoryTaskRegistry.arm_watchdog` es `pass` no-op `registry.py:88-91` ⇒ standalone **no** aplica timeout).
- **productor:** `dispatch()`. **consumidor:** base default no-op / integrador con watchdog real. Adyacente a 05·E33 (promoción fg→bg puede montar sobre el mismo timer). DEUDA-B, NO deuda A↔B.
- **firma:** parte de `TaskRegistryProtocol` (S19). **cabo:** completar (`asyncio.wait_for`/deadline→kill) o retirar si 08·signals cubre la cancelación.

### S25 · `AgentDefinition` (contrato ampliado)
- **estado:** `existe-parcial` (05·E28/GAP-EXEC4: 5 campos; faltan los de **ejecución**).
- **productor:** el resolver del integrador (`loadAgentsDir`). **consumidor:** el runner threadea los campos de ejecución.
- **firma BORRADOR** (reparto de campos, 05·§AgentDefinition):
  ```python
  @dataclass(frozen=True)
  class AgentDefinition:                 # campos de EJECUCIÓN (contrato + base consume)
      system_prompt: str
      model: str | InheritSentinel
      max_turns: int | None = None       # 05·E16 (= RuntimeTask.max_turns 01·CTR-14; hoy inerte)
      background: bool = False           # 05·E22 force-async (→S22)
      disallowed_tools: frozenset[str] = frozenset()   # 05 denylist (hoy sólo allowlist)
      permission_mode: PermissionMode | None = None    # 05·E20 (→S17)
      # DELEGADOS: mcp_servers→11 · skills/hooks→12/06 · effort→16 · memory→13 · isolation→10/18
      # initialPrompt = persona de SESIÓN → integrador/entrypoint, NO subagente (corrección re-audit)
      # color/filename/baseDir = CLI-ONLY → integrador
  ```
- **⚠ ESTADO DE LOS DELEGADOS (A-CIERRE.MCP 2026-07-30) — la línea `# DELEGADOS` reparte seis campos y en los dos
  únicos pares auditados hasta hoy el dueño nombrado NO los tenía:**

  | delegado | dueño nombrado | comprobado en | resultado |
  |---|---|---|---|
  | `isolation` | 10/18 | `A-CIERRE·P4″ §15` (par 10) | ❌ **huérfano** — 10 no tenía las fichas |
  | `mcp_servers` | 11 | `A-CIERRE·P4″ §16` (par 11) | ❌ **huérfano** — 0 ocurrencias en 11; **RESUELTO**: 11 lo reclama como **`CG-MCP-21`**, contraparte canónica **`runAgent.ts:95-218 initializeAgentMcpServers`** (leída 1→EOF el 2026-07-30). ⚠ **El ancla se corrigió**: se escribió primero `extractAgentMcpServers`, que es la ruta de PANTALLA del `/mcp` y **descarta las referencias por string** (`utils.ts:483`) que la ruta real sí conecta ⇒ **una costura se ancla a la función que EJECUTA, no a la que MUESTRA** |
  | `skills`/`hooks` | 12/06 | — | ⬜ sin comprobar |
  | `effort` | 16 | — | ⬜ sin comprobar |
  | `memory` | 13 | — | ⬜ sin comprobar |

  **Dos de dos fallaron.** El estado `existe-parcial` de esta costura descansa en que los campos que faltan están
  *repartidos*; si alguno de los cuatro restantes aparece también huérfano, el reparto es nominal y **`S25` no está
  parcialmente implementada sino sin cablear**, y este estado habrá que corregirlo. Comprobar al reconciliar los
  pares 12, 13 y 16 — **no dar por bueno el reparto por estar escrito aquí** (`L09: cablear ≠ existir`).

### S27 · deps-DI seam (constructor)
- **estado:** `existe-fiel` (02·E6: DI por constructor `agent_loop.py:49-63`). No es costura de producto; es el seam para **inyectar los motores** (compaction/budget) **en tests**.
- **uso:** al portar las batteries, reusar este seam para inyectar sus motores fake en tests (A2 y Fase C).

### S30 · `PromptSourceProtocol` (resolución de entrada NO textual, **pre-loop**) — AÑADIDA por A3.CAT
- **tier:** T2-COSTURA. **estado:** `existe-horneada` — el mecanismo **está vivo pero no es costura**: vive dentro del
  base como `LocalAgentRuntime._resolve_prompt` (`runtime.py:220-232`), alimentado por el gate de voz del ensamblador
  (`factory.py:212-216`, `config.voice` → `stt`) y pasado por constructor (`LocalAgentRuntime(stt=…)`).
- **por qué NO es S11** (resuelve la vecindad que `17·§2.7` dejó abierta, y el cabo 5 de `BATTERIES §4.5`):
  S11 `UserInputProcessor` es **intra-turno**, su productor es el `AgentLoop` y su poder es **cortocircuitar** el turno
  (un slash-command). S30 es **pre-loop**: corre en `RuntimeTask` antes de que exista `AgentLoop`, consume `ctx` (`:228`)
  y su salida **es** el prompt del turno. Dos productores, dos ciclos de vida ⇒ **dos costuras, no una**.
- **productor:** `LocalAgentRuntime` al abrir la task. **consumidor:** battery `voice` (STT) o integrador (dictado,
  adjuntos, transcripción de otro medio).
- **firma BORRADOR:**
  ```python
  class PromptSourceProtocol(Protocol):
      async def resolve(self, task: RuntimeTask, vctx: VoiceCallContext) -> str: ...  # devuelve el prompt del turno
  # base default: TextPromptSource (identidad — devuelve task.prompt)
  ```
- **⚠ La firma NO copia la de hoy, y la razón importa.** Hoy `_resolve_prompt` llama `stt.transcribe(audio, ctx)`
  con el **`ToolUseContext` completo** (`runtime.py:228`) — es decir, entrega a un motor de terceros `user_id`,
  `session_id`, `messages` (la conversación entera), `tool_pool`, `app_state`, `storage`, `fs`, `git_credentials`.
  **`DEUDA-A ID-6(b)` lo tipifica como fuga y `00-LEGEND §2.4` lo prohíbe expresamente.** Extraer la costura
  copiando la firma actual **congelaría la fuga en un contrato público**, que es peor que tenerla horneada. Por eso
  S30 toma `VoiceCallContext` (`id` opaco + `metadata` + `stop`), la pieza que ID-6 ya diseñó. 【id-opaco】
- **cabo:** al extraerse la voz (B08), el base conserva **sólo** el default identidad; `VoiceConfig.stt_enabled`
  desaparece — *no componer la battery __es__ el gate* (17·C1).

### S31 · `SpeechSink` (salida hablada) — AÑADIDA por A3.CAT
- **tier:** T2-COSTURA. **estado:** `existe-horneada` — hoy `LocalAgentRuntime._wire_tts` (`runtime.py:234-262`) se
  suscribe él mismo a `TokenEvent`/`DoneEvent`. **NO necesita canal nuevo:** monta sobre **S5** (`EventBus.subscribe`),
  que ya es costura pública y viva ⇒ la asimetría con S30 es real y está en el diseño, no en la documentación.
- **productor:** el `EventBus` (S5). **consumidor:** battery `voice` (TTS) / integrador.
- **firma BORRADOR:**
  ```python
  class SpeechSink(Protocol):
      def attach(self, bus: EventBus) -> Unsubscribe: ...   # subscribe(TokenEvent) + subscribe(DoneEvent)
      def sanitize(self, text: str) -> str: ...             # absorbe el saneo de S12, con estado ENTRE chunks (CG-V4)
  ```
- **misma regla que S30:** `speak(text, ctx)`/`flush(ctx)` (`runtime.py:248/:257`) entregan hoy el `ToolUseContext`
  completo al motor ⇒ el contrato público toma **`VoiceCallContext`**, no `ctx` (`DEUDA-A ID-6(b)`).
- **dependencia dura:** el sink debe saber **de qué agente** es cada evento; hoy lo deduce de `ctx.is_subagent`
  (`runtime.py:239`), que sólo existe porque el wiring está dentro del runtime. Extraerlo **exige K4**, y K4 en su
  **forma vigente**: `A3.DB §7.2` cerró que **no** es un `EventEnvelope` que envuelva —`EventBus.emit` despacha por
  `type(event)` (`bus.py:40`), luego envolver rompe el despacho tipado— sino **campos de identidad en el `Event`
  BASE** (`task_id`/`agent_id`/`session_id`/`seq`/`ts`, viables porque los 5 subtipos tienen todos sus campos con
  default). ~~⚠ `DEUDA-A §1.1·K4` y `§2·ID-6` **siguen diciendo "envelope"**: están rancios~~ → **CORREGIDOS en
  A-CIERRE·P0 (AC-03)**: `DEUDA-A` declara ya la forma vigente en los **6** sitios donde la contradecía (`CAT-h10`
  descargado; el rótulo obsoleto de `DEUDA-B §4·cabo 2` retirado en el mismo paso, AC-04).
  ⇒ **la extracción de B08 no puede preceder a K4.**

---

## 4. Matriz productor → consumidor (resumen de cableado)

| costura | productor (invoca) | consumidor (implementa) | punto de cableado (ensamblador) |
|---|---|---|---|
| S1 model-caller | `AgentLoop` `agent_loop.py:235` | bridge `AgenticModelsCaller` / integrador | `factory.py:219` (`model_caller=config.model_caller`); NO `:83` = slot muerto `ModelsConfig`/LAT-MODELS1 |
| S4 AgentRuntime | integrador (`dispatch`/`stream`) | `LocalAgentRuntime` / integrador | `factory.create_runtime` |
| S5 EventBus/stream | caller/loop/runtime (`emit`) | integrador (`subscribe_all`/`async for`) | `runtime.py:153-181/264` |
| S6 wire | integrador (`subscribe_all(serializer)`) | BFF/REPL | **ausente** (factory no cablea) |
| S8 HookRunner | loop (fronteras del turno) | integrador (registra hooks) | `agent_loop.py:300-306` (sólo PRE_TOOL_USE) |
| S9 CompactionProvider | loop (trigger `agent_loop.py:189`) + motor battery | providers concretos | seam existe; **motor ausente** |
| S10 RetryPolicy | loop (envuelve `complete()`) | battery `resilience` | **ausente** |
| S11 UserInputProcessor | loop **pre-turno** `agent_loop.py:211` | battery `commands` / integrador | `factory.py:258` (`input_processor=config.input_processor`) → `LocalAgentRuntime` → `AgentLoop` (`C4`) |
| S12 PathPresentation | `dispatcher.py:42` (`sanitize_output`) + **6 puntos de `to_llm`**: `write_file.py:38`, `glob_tool.py:40`, `grep_tool.py:68`, `clone_repository.py:149`, `worktree.py:138`/`:211` | `IdentityPresentation` / integrador | cableado |
| S13 StorageContract | fs-tools/plan_file/`_persist` | integrador (FS/MinIO) | `fs_env.py:124` |
| S15 ToolExecEnvironment | `bash.py:27` (`run_shell`) + `worktree.py:_run` (`run_argv`) | `LocalExecEnvironment` / integrador | `factory.py:210→228`→`runtime.py:90/318` |
| S16 ToolProtocol | `create_tools`/`register` | tools/MCP/skills/integrador | `factory.py:41-67` |
| S17 PermissionGate | loop `PRE_TOOL_USE` + dispatcher | integrador (política) | `agent_loop.py:300-313` (vivo, parcial) |
| S18 SubagentRunner | `AgentTool` `agent.py:105` | `LocalAgentRuntime` vía adaptador | **sin poblar** (`set_runner` sólo test) → 18·C1 |
| S19 TaskRegistry | `LocalAgentRuntime` + tools nativas | `InMemoryTaskRegistry` / integrador | doble-camino (`runtime.py:63/86` vs `task_tools.py`) |
| S20 SessionRepo | driver de sesión | integrador | mímica (`_build_child` autogen) → A3.DA |
| S21 NotificationSink | child (`put_notification` `runtime.py:299`) | ~~integrador (drena)~~ → **el propio `AgentLoop`** (CORE-GAP `H-5`) | **put sí, drain INEXISTENTE** — no delegado (AC-h3/P0) → AC-07 |
| S24 arm_watchdog | `dispatch` `runtime.py:149` | integrador (watchdog real) | default no-op `registry.py:88-91` |
| S30 PromptSource | `LocalAgentRuntime` pre-loop `runtime.py:220-232` | battery `voice` (STT) / integrador | **horneado** en el base (`factory.py:212-216` → ctor `stt=`) — a exteriorizar |
| S31 SpeechSink | `EventBus` (S5) | battery `voice` (TTS) / integrador | **horneado** `runtime.py:234-262` (`_wire_tts`) — a exteriorizar, **tras K4** |
| S23 on_agent_teardown | `_run_loop` `finally` (05) | **11·`CG-MCP-20`** (`cleanup_for_agent`) · 10 bash-bg · 12 skills | costura `ausente`; **11 es el único consumidor con cable nominal** (A-CIERRE.MCP) — 10 y 12 sin comprobar |
| S32 McpConfigStore | `provider.startup/reconcile` invoca `load` | integrador registra productores por scope | `existe-fiel`; default `StorageBackedMcpConfigStore` |
| S33 McpConfigWatcher | `provider.startup` lo arranca | integrador (inotify / poll MinIO) | `existe-fiel`; espejo de `15·ConfigWatcher` |
| S34 register_auth_strategy / AuthDeps | `battery_mcp` auth | integrador inyecta redirect/callback/token-storage | `existe-fiel`; headless no abre browser |
| S35 McpPolicy | `battery_mcp` filtra **antes de conectar** | integrador provee las reglas | **`ausente`** — hoy se conecta a cualquier server declarado 【borde-seguridad】 |
| S36 McpApprovalGate | `battery_mcp` consulta `status(name,scope)` | integrador decide (auto-aprueba headless si lo habilita) | **`ausente`** — hoy `provider.py:228-245` conecta servers de proyecto **sin aprobar** 【borde-seguridad】 |
| S37 elicitation-hook | `battery_mcp` (capability `roots`+`elicitation`) | hook inyectado por el integrador | `ausente`; el diálogo interactivo es ⛔ (`11·MCP-NA-7`) |
| S38 trust-gate (headersHelper) | `battery_mcp` `client.connect` (http/sse) vía `S15` | integrador (workspace-trust) | **`ausente`** — el helper es **ejecución de script de terceros**: sin gate no debe correr 【borde-seguridad】 |

---

## 5. Estado para el walking skeleton A2 (qué costura valida qué ciclo)

- **A2.1 andamiaje:** stubs de S4/S5/S16/S11 (passthrough) + loop mínimo. Gate: typechecks.
- **A2.2 motor:** cablear **S1** (`ModelCallerProtocol`) → `agentic_models`; 1 turno real texto-solo. **La costura crítica a validar/corregir.**
- **A2.3 tools:** **S16** (`ToolProtocol`) + dispatch (S26/pool) + 1 tool nativa. Gate: el modelo llama la tool, resultado aplanado.
- **A2.4 battery:** componer 1 battery trivial vía **S9/S10** (composición); la battery se anuncia/consume sin que el base la conozca. **S20** (`SessionRepo`): el turno corre sin userId.
- **A2.5 integrador:** **S18** (`SubagentRunnerProtocol`, **crítico**) cableado en factory + **S4** + **S21**; turno end-to-end. Salida `SKELETON-REPORT.md`: veredicto de costuras (validadas o **corregidas**).

> **Costuras que A2 NO valida** (se difieren a A3/B–F): S2/S3 (abort/auth → 08/Fase E-F), S6 (wire → Fase F BFF),
> S7 (on_progress → 10·Bash), S8 fire-points STOP/POST (→06), S22/S23 (force-async/teardown → assistant/10-11-12),
> S24 (watchdog → integrador), S25 delegados (→11/12/13/06/16/10-18). Se listan aquí para que A2 no las dé por validadas (L09).
>
> **Añadido A3.CAT:** **S30/S31** tampoco las valida A2 — y con un matiz que no se puede omitir: no están `ausente`
> sino **`existe-horneada`**, es decir, el comportamiento funciona hoy *precisamente porque no es costura*. Su
> "validación" no es hacerlas andar (ya andan), sino **exteriorizarlas** sin perder comportamiento ⇒ **Fase C**, y S31
> **detrás de K4**. Declararlas validadas por el hecho de que la voz funciona sería el error inverso a L09.
