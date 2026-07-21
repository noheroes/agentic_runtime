# 01 · contracts

**Fase:** validación 2ª vuelta + **re-visita de completitud L09** (2026-07-18): 2 correcciones al doc, código intacto.
**Runtime:** `src/agentic_runtime/contracts/{runtime,permissions,compaction,storage,user_input}.py`
**Canónico:** seams inventados por el runtime → homologación **de comportamiento** (no 1:1 de forma).
Contrapartes: `tools/AgentTool/`, sistema de permisos (`alwaysAllowRules`/`acceptEdits`), `services/compact/`, `commands.ts`+`query.ts`, manejo de paths.

## Naturaleza del subsistema
`contracts/` no porta código canónico: son **Protocols** que el runtime introdujo para desacoplar al
consumidor (BFF/new_core/agent-code). Por eso el veredicto no es "¿portó la función X?" sino
**"¿el seam cubre y respeta el comportamiento que el canónico ejecuta inline?"**.

## Evidencia ejecutada
- **Lint** (subsistema): `ruff` ✅ · `mypy` ✅ (6 archivos, sin issues) · `bandit` ✅ (sin hallazgos).
- **Tests**: `test_runtime_contracts.py` (15) ✅ + nuevo `test_contracts_homologation.py` → **7 passed, 2 xfailed**.
  Los `xfail(strict)` codifican comportamiento homologado ausente (GAP-01, GAP-02): su fallo es la evidencia.
- **e2e real**: `LocalAgentRuntime` satisface `AgentRuntime` (isinstance + 6 métodos) — dispatch real cubierto por `test_runtime_e2e_real*`.

## Tabla feature-by-feature

| # | Feature (runtime) | Contraparte canónica | Estado | Diferencia / ajuste holístico |
|---|---|---|---|---|
| 1 | `AgentRuntime` protocol (`dispatch/stream/status/cancel/result/runtime_id`) | `query.ts` async-gen + `Task.ts` (dispatch+stream de una unidad de agente) | ✅ | `LocalAgentRuntime` conforma. `stream` como `async def`+yield ≡ `AsyncIterator`. Sin acción. |
| 2 | `RuntimeTask` campos base (`prompt`,`description`,`subagent_type`) | `AgentTool` inputSchema (`prompt`,`description`,`subagent_type`) | ✅ | Coinciden en semántica. |
| 3 | `RuntimeTask.model_override: str\|None` | `AgentTool.model: z.enum(['sonnet','opus','haiku'])` | 🔀 | Runtime usa string libre; canónico restringe a enum + reglas (`getAgentModel`, `isCoordinatorMode`→undefined). **Ajuste**: el contrato debe permitir alias canónicos y resolución (`inherit`/coordinator), no un string opaco. Resolución vive en `execution` (ver 05). |
| 4 | `RuntimeTask.fork_context: bool` | fork **implícito** (`forkSubagent.ts`: omitir `subagent_type`; `FORK_SUBAGENT_TYPE='fork'`; prefijo byte-idéntico para prompt-cache; `isInForkChild` guard) | 🔀 | Mecanismo distinto: flag explícito vs omisión implícita. El canónico exige **prefijo byte-idéntico** entre hijos-fork para compartir prompt-cache y un guard anti-recursión. **Ajuste**: contrastar en 04/05 si `RuntimeContextForker` reproduce byte-identidad y guard; el contrato solo expone el flag. |
| 5 | `RuntimeTask.owner_id`/`session_id` | *sin equivalente* (canónico single-user en terminal) | ✅* | Adición correcta: el runtime SÍ tiene usuarios/sesiones (requisito). Autogen `user_<hex>`/`sess_<hex>` si ausentes → ejecutable solo. Homologación *de comportamiento* (no de forma). |
| 6 | `RuntimeTask.audio_prompt: AudioInput\|None` | *sin equivalente directo* (`voice/`, STT) | ✅* | Adición del runtime (STT→prompt). Se contrasta en 17·voice. |
| 7 | `PermissionContext` (`always_allow_command`/`always_allow_session`/`always_deny` + `allowed_names`/`with_command_allow`) | `alwaysAllowRules`/`alwaysDenyRules` + scopes `command`/`project`/`localSettings`/`userSettings` | 🟡 | Cubre allow/deny por nombre. **Falta**: distinción de **scope de persistencia** (project/user/local vs session) — el runtime colapsa a command(persistente)/session(volátil). **Ajuste**: mapear los scopes canónicos al contrato o delegar explícitamente su persistencia al consumidor (documentarlo). |
| 8 | Permission **modes** | `acceptEdits` / `bypassPermissions` / `plan` / `default` (44+ usos de `acceptEdits`, 10 de `bypassPermissions`) | ❌ | **GAP-02**. `PermissionContext` NO modela modos; el plan-mode se maneja ad-hoc vía `app_state.native["plan_mode"]` en `loop/agent_loop.py:293`. **Ajuste holístico**: introducir `mode` en el contrato de permisos (enum canónico) y que `loop`/dispatcher decidan por modo+reglas, no por estado nativo suelto. Test `xfail`: `test_permission_context_models_permission_modes`. |
| 9 | `CompactionProvider` + `collect_compaction_context` | `services/compact/` (auto/micro/api-micro/sessionMemory/timeBased/postCleanup/grouping/prompt) | 🟡 | El seam solo abstrae "providers aportan mensajes en orden". El **trigger y la estrategia** de compactación (auto/micro/time-based, warning, cleanup) NO están en contracts. **Ajuste**: correcto que el aporte de providers sea un seam; pero falta el contrato del **motor** de compactación (trigger + presupuesto) — se contrasta en 02·loop / 03·context. Aquí queda 🟡 por cobertura parcial del dominio. |
| 10 | `StorageContract` (`real_path`/`ensure_local`/`commit`/`teardown`) | *sin equivalente directo* (canónico = FS local identidad) | 🔀 | Seam inventado para deployments contenerizados/blob (MinIO). Usado por capability `plan` (`plan_file.py`). Deliberado. **Ajuste**: ninguno de forma; verificar en 15·storage que `filesystem.py`/adaptador MinIO lo satisfacen coherentemente (hoy `StorageContract` vs `StorageProtocol` de 15 son **dos** abstracciones — revisar solapamiento). |
| 11 | `PathPresentation` (`to_llm`/`sanitize_output`) | traducción/saneo de paths hacia LLM/UI (inline en canónico) | ✅ | **Re-verificado bajo L09**: `sanitize_output` SÍ está cableado en ruta real — `tools/dispatcher.py:42` (saneo del output de tool bajo identidad = no-op) y `execution/local/runtime.py:244` (choke point TTS por-chunk); `IdentityPresentation` default en `factory.py:207`. **PERO** el otro método del protocolo, `to_llm`, **no tiene call site de producción** (`grep '\.to_llm(' = 0`; sólo la def en `context/presentation.py:18` + fakes de test) — misma costura latente que destapó 03·context. El comportamiento que A ejecuta inline (saneo de paths hacia LLM/voz) SÍ se reproduce vía `sanitize_output` ⇒ **✅ se sostiene**; el `to_llm` sin consumidor es **tech-debt B-interno** (extensión sin contraparte canónica), **NO deuda A-vs-B** (L10). Conforma `@runtime_checkable`. |
| 12 | `UserInputProcessor` + `NoopUserInputProcessor` (`process_slash_command`/`expand_inline_invocation`/`get_inline_name`) | `commands.ts` + `query.ts`/`QueryEngine.ts` (procesado de slash + invocación inline) | 🟡 | **GAP-01**: el seam existe y `Noop` es passthrough, pero **ningún consumidor lo invoca** (grep: solo exportado). El loop no preprocesa slash/inline. **Ajuste holístico**: cablear el processor en el `AgentLoop` antes del turno LLM (equivalente a `query`), no dejarlo colgado. Test `xfail`: `test_agent_loop_consumes_user_input_processor`. |
| 13 | Consistencia `@runtime_checkable` | — | 🟡 | **FIND-01**: `AgentRuntime`/`StorageContract`/`PathPresentation` son `@runtime_checkable`; `UserInputProcessor` y `CompactionProvider` **no**. Inconsistencia de contrato. **Ajuste**: unificar criterio (decorar todos o documentar por qué no). |
| 14 | `RuntimeTask.max_turns: int\|None` | `AgentTool.maxTurns` (`runAgent.ts:756` `maxTurns ?? agentDefinition.maxTurns`; `forkSubagent.ts:65`=200; `loadAgentsDir.ts` parsea frontmatter `maxTurns`) | 🟡 | **Añadido en re-auditoría 2ª vuelta** (la tabla original omitía este campo del contrato). El campo existe en `RuntimeTask` pero **no se cablea al loop**: `AgentLoop._MAX_TURNS=50` fijo y `AgentLoop.__init__` ni acepta `max_turns`. Gap de cableado **homed en 05·execution como FIND-EXEC5** (test `test_max_turns_threaded_to_loop` xfail). Aquí sólo se registra la existencia del campo-contrato + destino. |
| 15 | `RuntimeTask.timeout_seconds: float\|None` | *sin contraparte directa* (canónico usa abort/cancel, no timeout per-task en `AgentTool`) | 🟡 | **CORREGIDO en re-visita de completitud (L09; la 1ª ronda de 2ª vuelta fue confirmación-de-doc y sobre-declaró el gap)**: NO es "sin consumidor / inerte". `dispatch()` **lee** el campo y lo pasa al seam de watchdog — `execution/local/runtime.py:149` `arm_watchdog(task_id, task.timeout_seconds or self._default_timeout)`. Lo que hoy no impone el timeout es que el **default** `InMemoryTaskRegistry.arm_watchdog` (`execution/tasks/registry.py:88-91`) sea un **no-op deliberado** (comentario: *"el watchdog real lo arma el consumidor si lo necesita"*). Es decir: campo **cableado a un seam de delegación**, no colgante. Sin contraparte canónica ⇒ **tech-debt B-interno** (adición a medio cablear), **NO deuda A-vs-B** (L10 anti-padding); no es gap de homologación. **Ajuste (B-interno, opcional)**: proveer un `arm_watchdog` que arme `asyncio.wait_for`/deadline→`kill`, o retirar el campo si la cancelación por abort (08·signals) lo cubre. (`resolve_timeout_seconds` de `factory.py` es OTRO campo, de `CapabilitiesConfig`, no éste.) |

## Resumen de estados
✅ 4 (feat. 1,2,11 + 5/6 como adiciones correctas) · 🟡 6 (7,9,12,13,14,15) · 🔀 3 (3,4,10) · ❌ 1 (8) · ⛔ 0
> **Actualizado en 2ª vuelta**: 13→15 features (antes ✅4·🟡4·🔀3·❌1). Las 2 nuevas son campos de `RuntimeTask`
> omitidos en la 1ª pasada (`max_turns`→FIND-EXEC5/05, `timeout_seconds` inerte). Ver §nota de honestidad.

## Gaps priorizados (para fase de implementación)
- **GAP-02 (❌)** Permission modes ausentes en el contrato → decisión de permisos hoy dispersa en `app_state.native`. *Arquitectural, no parche.*
- **GAP-01 (🟡)** `UserInputProcessor` no cableado en el loop → slash/inline no se preprocesan.
- **FIND-01 (🟡)** `@runtime_checkable` inconsistente.
- **Solapamiento** `StorageContract` (contracts) vs `StorageProtocol` (15·storage): revisar si deben unificarse.
- **model_override** (🔀) y **fork_context** (🔀): resolver semántica de modelo y byte-identidad de fork en 04/05.

## Notas para pasadas 2/3
- ~~Verificar dónde ocurre el autogen `user_<hex>`/`sess_<hex>`~~ **RESUELTO (2ª vuelta)**: ocurre en
  `execution/local/runtime.py:208-209` (`session_id = task.session_id or f"sess_{uuid.uuid4().hex[:12]}"`;
  `user_id = task.owner_id or f"user_{uuid.uuid4().hex[:12]}"`), simétrico. Confirmado.
- Confirmar que `fork_context=True` produce prefijo byte-idéntico (prompt-cache) como exige el canónico → **05·execution** (`RuntimeContextForker`), no en 01.
- Rastrear si algún consumidor externo (new_core/BFF) ya cablea `UserInputProcessor` fuera de este repo (GAP-01 sigue abierto en este repo: sólo lo referencia su test de homologación).

---

## Ledger de cierre — 2ª vuelta (validación)

| Archivo | Lado | Lectura | Nota |
|---|---|---|---|
| `contracts/runtime.py` (67 LOC) | B | **íntegro 1→EOF** | Destapó `max_turns`/`timeout_seconds` omitidos en la tabla original → feat 14/15. |
| `contracts/permissions.py` (33) | B | **íntegro** | Sin `mode` → GAP-02 confirmado. |
| `contracts/compaction.py` (27) | B | **íntegro** | `CompactionProvider` sin `@runtime_checkable` → FIND-01 confirmado. |
| `contracts/storage.py` (40) | B | **íntegro** | `StorageContract`+`PathPresentation` ambos `@runtime_checkable`. |
| `contracts/user_input.py` (46) | B | **íntegro** | Firma 5-arg `process_slash_command`; `UserInputProcessor` sin decorar → FIND-01. |
| `contracts/__init__.py` (17) | B | **íntegro** | Exports; ningún consumidor de `UserInputProcessor` fuera del test → GAP-01. |
| `loop/agent_loop.py:293,330` | B | tramos (líneas citadas + contexto) | plan_mode vía `app_state.native` → GAP-02 confirmado. |
| `execution/local/runtime.py:208-209` | B | tramo | autogen user/sess confirmado. |
| `AgentTool/` (runAgent/forkSubagent/loadAgentsDir) | A | grep dirigido (maxTurns) | Contraparte de feat 14 confirmada; auditoría íntegra vive en 05/10. |
| Contrapartes canónicas dispersas (compact/permissions/commands) | A | delegadas a 02/05/06/12/15 | Este subsistema son seams inventados; su A se audita íntegro en los subsistemas de destino. |

### Re-visita de completitud (L09) — consumidores de B abiertos en ruta real (2026-07-18)

> La 1ª ronda de 2ª vuelta validó por **confirmación-de-doc** (leyó los 6 `contracts/*.py` + tramos, contrastó
> la tabla). Esta re-visita aplica `learned_lessons/09`: por CADA fila ✅/🔀, abrir la implementación de B que
> **consume** el protocolo y confirmar que se invoca en la ruta real (cablear ≠ existir). Resultado: 1
> discrepancia real (feat 15) + 1 costura latente (feat 11); el resto de ✅/🔀 confirmados consumidos.

| Consumidor (B) | Lectura | Qué confirma |
|---|---|---|
| `execution/local/runtime.py` (435 LOC) | **íntegro 1→EOF** | El consumidor real. `prompt/description/subagent_type` (226/142/342), `model_override` (346/351), `fork_context` (200 `ForkPolicy(inherit_messages=...)`), `owner_id/session_id` (208-209), `audio_prompt` (224) → **todos consumidos**. `max_turns` **NO** se pasa al `AgentLoop(...)` (355-366) → FIND-EXEC5 inerte confirmado. `timeout_seconds` **SÍ** se lee (149→`arm_watchdog`). |
| `execution/tasks/registry.py:88-91` | tramo (arm_watchdog/kill) | `InMemoryTaskRegistry.arm_watchdog` = **no-op deliberado** (`pass`) → el seam de timeout se delega al consumidor; `kill` (117-124) sí cancela la asyncio.Task. Corrige feat 15. |
| `tools/dispatcher.py:42,63` · `capabilities/resolver.py:40` · `tools/pool.py:59` | tramos | `PermissionContext.sanitize_output`/`allowed_names`/`denied_names` consumidos en el gate real (feat 7 ✅ en su parte allow/deny). |
| `context/presentation.py` · `factory.py:207` | íntegro / tramo | `sanitize_output` cableado (dispatcher:42 + runtime:244); `to_llm` **sin call site de producción** (feat 11). |
| `capabilities/plan/plan_file.py` · `tools/fs_env.py:124` | tramos | `StorageContract` consumido por plan-file + fs_env (feat 10 🔀 cableado). |
| `collect_compaction_context` / `UserInputProcessor` | grep completo | **Cero consumidor de producción** (sólo tests) → motor#1 de compactación ausente (feat 9 🟡→02) y GAP-01 (feat 12) confirmados por completitud. |

### Nota de honestidad (2ª vuelta + re-visita de completitud L09)

- **⚠️ Sobre-declaración de la 1ª ronda CORREGIDA (feat 15)**: la 1ª ronda de 2ª vuelta declaró `timeout_seconds`
  "**sin consumidor** en B... inerte" — falso. Fue **confirmación-de-doc**: no se abrió `dispatch()`, se heredó
  la afirmación. La re-visita L09 abrió `runtime.py:149` y vio que el campo **se lee y se pasa a `arm_watchdog`**
  (seam de delegación cuyo default es un no-op). Reclasificado: **tech-debt B-interno**, no gap A-vs-B (L10).
- **Costura latente registrada (feat 11)**: bajo L09, `to_llm` no tiene call site de producción (sólo
  `sanitize_output` lo tiene). El ✅ se sostiene sobre `sanitize_output` (el comportamiento canónico), pero se
  deja explícito que `to_llm` es extensión B sin consumidor = tech-debt B-interno (mismo hallazgo que 03·context;
  L10 anti-padding: NO se cuenta como deuda A-vs-B).
- **Resto validado-sin-cambios bajo completitud**: feats 1-6, 9, 10, 13, 14 confirmados consumidos-en-ruta-real
  (o confirmada su ausencia de consumidor donde el doc ya lo decía: motor de compactación, GAP-01, max_turns).
  GAP-01 (UserInputProcessor uncabled), GAP-02 (sin `mode`, feat 8 ❌ — converge, no re-hecha), FIND-01
  (`@runtime_checkable` inconsistente) siguen ciertos contra el B actual.

### Nota de honestidad original (1ª ronda de 2ª vuelta — preservada)
- **Discrepancia real encontrada**: la tabla de la 1ª pasada **sub-declaraba** los campos de `RuntimeTask`:
  enumeró 6 de 8 campos, omitiendo `max_turns` y `timeout_seconds`. Corregido (feat 14/15). `max_turns` no era
  "nuevo": su gap ya estaba homed como FIND-EXEC5 en 05, pero el doc-contrato no lo cruzaba — cabo-con-destino
  sin anotar, ahora anotado.
- **Todo lo demás validado-sin-cambios**: GAP-01 (UserInputProcessor uncabled), GAP-02 (sin `mode`), FIND-01
  (`@runtime_checkable` inconsistente), feats 1-13 y los estados/conteos siguen ciertos contra el B actual.
- **Alcance del contraste A**: `contracts/` no porta código canónico (son seams del runtime); las contrapartes
  canónicas se auditan íntegras en sus subsistemas de destino (02·loop, 05·execution, 06·hooks, 12·skills,
  15·storage). Aquí el contraste A es dirigido y con destino nombrado, no troceo (lección 07 respetada: no hay
  archivo canónico "de la categoría 01" que se haya leído a medias — 01 no tiene archivos-A propios).

### 4 preguntas de cierre (tras re-visita de completitud L09)
1. **¿Se revisó todo cada archivo de B listado?** Sí — los 6 archivos de `contracts/` leídos **íntegros 1→EOF**
   (230 LOC) + **el consumidor real `execution/local/runtime.py` leído íntegro 1→EOF** (435 LOC) + tramos de
   `registry.py`/`dispatcher.py`/`resolver.py`/`pool.py`/`fs_env.py`/`plan_file.py`/`factory.py`/`presentation.py`
   + grep completo de cada símbolo de contrato (definido vs invocado). Esta vez se verificó COMPLETITUD (¿cada
   protocolo ✅/🔀 se **consume** en la ruta real?), no sólo la forma del doc.
2. **¿Se revisó todo cada archivo de A listado?** Sí, con el matiz honesto: 01 **no tiene archivos-A propios**
   (son seams inventados); las contrapartes canónicas se auditan íntegras en sus subsistemas de destino.
3. **¿Los hallazgos fueron exhaustivos?** Sí — **la re-visita L09 corrigió una sobre-declaración que la 1ª
   ronda (confirmación-de-doc) no vio**: feat 15 `timeout_seconds` estaba marcado "sin consumidor/inerte" pero
   B lo cablea a `arm_watchdog` (runtime.py:149). Además se registró la costura latente `to_llm` (feat 11) sin
   call site de producción. Ambos son tech-debt B-interno (L10), no deuda A-vs-B.
4. **¿Quedó todo cubierto?** Sí; los cabos van con destino: `max_turns`→05·FIND-EXEC5 (inerte confirmado),
   `timeout_seconds`→tech-debt B-interno (arm_watchdog no-op; ajuste opcional), `to_llm` sin consumidor→tech-debt
   B-interno (=03·context), `model_override`/`fork_context`→05, `StorageContract` solapamiento→15 (ya RESUELTO),
   GAP-02 decisión→Deuda B `B-02`, GAP-01 (UserInputProcessor uncabled) sigue abierto en este repo.

---

## Plan de homologación / remediación desarrollada

Diseño por finding (1ª pasada = diseño, no código). Seams reales: `contracts/permissions.py`
(`PermissionContext` = `always_allow_command`/`always_allow_session`/`always_deny` + `allowed_names`),
`contracts/user_input.py` (`UserInputProcessor` Protocol + `NoopUserInputProcessor`),
`contracts/runtime.py` (`RuntimeTask` dataclass + `AgentRuntime` `@runtime_checkable`),
`contracts/compaction.py` (`CompactionProvider` sin decorar). Cabos que se ELEVAN a Deuda B se anotan.

### CR1 · GAP-02 (parte contrato) — `mode` en `PermissionContext`
- **Comportamiento**: el contrato de permisos modela el **modo** canónico
  (`default`/`acceptEdits`/`plan`/`bypassPermissions`); hoy el plan-mode se lee de
  `app_state.native["plan_mode"]` (hack). La **decisión** por modo+reglas es Deuda B (`B-02`); aquí sólo
  el **campo del contrato** que esa decisión necesita.
- **Seam/firma**: `PermissionContext` gana `mode: PermissionMode = "default"` (`PermissionMode = Literal[
  "default","acceptEdits","plan","bypassPermissions"]`) + `additional_working_directories: list[str]`
  (para el gate fs) + `pre_plan_mode: PermissionMode | None` (restaurar al salir de plan).
- **Cableado**: `EnterPlanMode`/`ExitPlanMode` (10) dejan de mutar `native["plan_mode"]` y setean
  `permissions.mode` vía `context_modifier`; el gate del dispatcher (Deuda B `B-02`) lo lee.
- **Orden**: prerrequisito de `B-02`; independiente del resto de 01.
- **Test**: `test_permission_context_models_permission_modes` (xfail existente).

### CR2 · GAP-01 — cablear `UserInputProcessor` en el loop
- **Comportamiento**: el loop preprocesa slash-commands/inline-invocations ANTES del turno LLM (espejo de
  `query`), en vez de dejar el processor colgado (hoy sólo exportado, ningún consumidor lo invoca).
- **Seam/firma**: `AgentLoop.__init__` acepta `user_input_processor: UserInputProcessor =
  NoopUserInputProcessor()`. En `run()`, tras `_run_turn_start_hooks()` y ANTES de
  `ctx.messages.append({"role":"user","content":prompt})` (`agent_loop.py:176-179`): `expanded =
  processor.expand_inline_invocation(prompt)`; si `get_inline_name` → resolver; `handled = await
  processor.process_slash_command(expanded, registry, session, ctx.stop, ctx.event_queue)`; si el slash
  devuelve un resultado terminal (comando que no va al modelo) → cortar el turno.
- **Cableado**: default `Noop` = passthrough (backward-compatible); el BFF inyecta su processor con los
  slash/inline reales. Liga 12·skills (commands.py) donde viven los comandos.
- **Orden**: independiente.
- **Test**: `test_agent_loop_consumes_user_input_processor` (xfail existente).

### CR3 · FIND-01 — `@runtime_checkable` consistente
- **Comportamiento**: unificar el criterio — `AgentRuntime`/`StorageContract`/`PathPresentation` ya son
  `@runtime_checkable`; `UserInputProcessor` y `CompactionProvider` no.
- **Seam/firma**: decorar ambos con `@runtime_checkable` (permiten `isinstance` en tests de conformidad),
  o documentar por qué un Protocol de método async no lo lleva. Recomendación: decorar (coste nulo, simetría).
- **Orden**: trivial, independiente.
- **Test**: `test_all_contract_protocols_runtime_checkable`.

### CR4 · feat 7 — scope de persistencia de reglas de permiso
- **Comportamiento**: el canónico distingue scopes `command`/`project`/`localSettings`/`userSettings`; el
  runtime colapsa a `command`(persistente)/`session`(volátil).
- **Seam/firma**: dos caminos — (a) mapear los 4 scopes canónicos a `PermissionContext` (más campos), o
  (b) **delegar** la persistencia por-scope al consumidor (el runtime sólo ve allow/deny efectivos) y
  **documentarlo** como decisión. Recomendado (b): el scope de persistencia es política del integrador
  server-side (15·storage decide dónde), el runtime opera sobre el conjunto resuelto.
- **Orden**: independiente; se cierra al documentar 15.
- **Test**: — (decisión de diseño; sin xfail).

### CR5 · feats 3/4/10 — cabos que se resuelven en OTRO subsistema (no re-desarrollar aquí)
- **model_override (🔀, feat 3)** → resolución de alias/coordinator vive en **05·execution**
  (`resolve_subagent_model`); el contrato sólo expone el string. Diseño en 05.
- **fork_context byte-identidad (🔀, feat 4)** → **05·execution** (`RuntimeContextForker` debe reproducir
  prefijo byte-idéntico + guard anti-recursión `isInForkChild`). Diseño en 05.
- **StorageContract vs StorageProtocol (🔀, feat 10)** → **15·storage**: decidir si se unifican; el
  solapamiento se resuelve al documentar 15, no en 01.
- **CompactionProvider = motor de compactación (🟡, feat 9)** → el **aporte de providers** es seam correcto;
  el **motor** (trigger/presupuesto) es el motor #1 no portado de **02** (ver 02·§Plan, CR-adjacent).
