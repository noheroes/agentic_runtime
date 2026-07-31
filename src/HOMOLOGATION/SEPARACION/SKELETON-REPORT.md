# SKELETON-REPORT — veredicto de costuras del walking skeleton (Fase A2)

> Salida del ciclo **A2.5** (PLAN §4). Consolida qué costuras de `SEAMS.md` quedaron
> **validadas o corregidas** al ejercitarlas con TURNOS reales/canned en el spike
> `SEPARACION/skeleton/`. Es el cierre de Fase A2: las costuras que sobreviven aquí son las
> que Fase B construye "de verdad" sobre el runtime; las corregidas llevan su corrección ya
> vertida a `SEAMS.md`. **Evidencia = correr, no compilar** (PLAN §2).

## 0. Cómo se ejecuta la evidencia
```
cd agentic_runtime
MYPYPATH=src/HOMOLOGATION/SEPARACION .venv/bin/mypy --strict src/HOMOLOGATION/SEPARACION/skeleton   # 0 errores (17 archivos)
uvx ruff check src/HOMOLOGATION/SEPARACION/skeleton                                                  # All checks passed
PYTHONPATH=src/HOMOLOGATION/SEPARACION .venv/bin/python -m skeleton._smoke        # A2.1/A2.3 canned  · exit 0
PYTHONPATH=src/HOMOLOGATION/SEPARACION .venv/bin/python -m skeleton._motor        # A2.2 turno REAL   · exit 0
PYTHONPATH=src/HOMOLOGATION/SEPARACION .venv/bin/python -m skeleton._tools        # A2.3 turno REAL   · exit 0
PYTHONPATH=src/HOMOLOGATION/SEPARACION .venv/bin/python -m skeleton._battery      # A2.4 composición  · exit 0
PYTHONPATH=src/HOMOLOGATION/SEPARACION .venv/bin/python -m skeleton._integrador          # A2.5 OFFLINE (A∧B∧C) · exit 0
PYTHONPATH=src/HOMOLOGATION/SEPARACION .venv/bin/python -m skeleton._integrador --real    # A2.5 + turno REAL end-to-end
```
> **Nota de entorno (honestidad):** los turnos reales requieren (1) token OAuth de Claude Code
> (`~/.claude/.credentials.json`), (2) un **shim TLS** local (relaja `VERIFY_X509_STRICT` para el
> proxy MITM corporativo; aislado al runner, la costura `bridge.py` no lo conoce) y (3) el cliente
> OAuth por `options.client` (workaround de `anthropic-sdk 0.109.1`; arreglo de raíz → Fase D en
> `agentic_models`). `ruff` no está en el `.venv` de esta sesión → se corrió vía `uvx ruff`
> (mismo binario, entorno efímero). **Los turnos reales NO se re-corrieron con `SSL_CERT_FILE`
> sobreescrito** — hacerlo rompe la CA corporativa (visto y descartado en A2.5).

## 1. Tabla de veredictos (costuras EJERCITADAS por el skeleton)
| Costura | Ciclo | Veredicto | Evidencia (correr) |
|---|---|---|---|
| **S1** `ModelCallerProtocol` | A2.2 | ✅ **VALIDADA-CORREGIDA** | `_motor` turno real texto-solo; efecto-en-cable (`on_payload`) confirma temperature/max_tokens/metadata transmitidos |
| **S2** `AbortSignal` | A2.1/2.2 | 🟡 **shape corregido, trigger no ejercitado** | `.aborted` (no `asyncio.Event`); el abort real → 08·signals |
| **S4** `AgentRuntime` (façade) | A2.5 | ✅ **VALIDADA** (dispatch/status/result) | `_integrador` (C): `dispatch`→`status`=COMPLETED + `result` no-None bajo el MISMO id |
| **S5** `EventBus`/`stream` | A2.1 | ✅ **VALIDADA** | canal único ordenado Init→…→Result en todos los runners |
| **S9** `CompactionMotor` (battery) | A2.4 | ✅ **VALIDADA** (composición) | `_battery`: base agnóstico (0 boundary sin battery / ≥1 con battery inyectada) |
| **S11** `UserInputProcessor` | A2.1 | ✅ **VALIDADA** (cableado pre-turno) | el loop invoca `process` pre-turno; stub passthrough + rama short-circuit |
| **S16** `ToolProtocol` (+dispatch) | A2.3 | ✅ **VALIDADA** | `_tools` turno real: modelo llama `add_numbers`→dispatch aplana `42`→re-entra |
| **S18** `SubagentRunnerProtocol` | A2.5 | ✅ **VALIDADA-CORREGIDA** | `_integrador` REAL: padre delegó→subagente real sumó 42→aplanado+citado; NEGATIVA prueba carga |
| **S20** `SessionRepo` | A2.4 | ✅ **VALIDADA** (turno sin userId) | `_battery`: metadata rica→id opaco; probe asegura no-`user_id` al seam del modelo |
| **S21** `NotificationSink` | A2.5 | ✅ **VALIDADA** (put+drain) | `_integrador`: child publica `Notification`, integrador drena con el resultado |
| **S26** `DeferredToolStrategy` | A2.3 | ✅ **VALIDADA** (eager) | ramas Simulada/Nativa declaradas, no ejercitadas (L09-inverso) |
| **S27** deps-DI (constructor) | A2.1–2.5 | ✅ **VALIDADA** | todas las costuras inyectadas por constructor (caller/compaction/runner/notifier) |

## 2. Correcciones vertidas a `SEAMS.md` (costuras que NO aguantaron el borrador)
### §S18 — mecanismo corregido (🔀, no bug)
- **`ForkContext` → `SubagentSpec`** (dataclass frozen mínimo). El *fork* real (hijo hereda
  historial completo del padre) NO se ejercita en A2.5; sólo el *spawn* con prompt propio. El
  fork-de-historial es Fase C/F.
- **Singleton global `set_runner/get_runner` → deps-DI (S27).** El runner se inyecta al
  `LocalAgentRuntime` por constructor y se threadea al `ctx`; `AgentTool` lee `ctx.runner`. La nota
  del borrador "cablear `set_runner` en factory" queda **retirada** — el patrón correcto es DI, no un
  global mutable. **Verificado por fuente** (2026-07-23, `execution/runner.py` 1→EOF): `_runner` global,
  `get_runner()` lanza si `None`, productor `agent.py:105`.
  **⚠️ Corrección a mi propia afirmación previa:** este fix elimina la fragilidad del **global del
  RUNNER (S18)**, NO el "doble-camino" del **REGISTRY (S19)** — son dos globals distintos; el skeleton
  A2.5 no tiene TaskRegistry, luego no toca S19. Conflarlos fue un overreach. (El estado real de S19
  es además contestado: `task_tools.py:10,29/54/113/187` usa el `get_registry` de ejecución —
  contradice 05·LAT-EXEC1 que lo daba por `agentic_models`— pero confirmarlo como divergencia viva
  necesita `runtime.py:63/86`, no re-abierto aquí → cabo de S19/Fase F.)
- **Prueba de carga (L09).** El bug mímica (05·E24) era: la pieza existe pero el ensamblador nunca
  la cablea ⇒ `get_runner()` lanza en todo spawn. Reproducido y prevenido: la prueba NEGATIVA de
  `_integrador` construye un runtime SIN el cableado del factory (`runner=None`) y comprueba que
  `AgentTool` devuelve `is_error` ("not wired"); el turno REAL prueba que el factory SÍ lo puebla.
- **`background`:** declarado (`run(background=True)` lanza `NotImplementedError`→S22/Fase F), no
  ejercitado. No se finge camino muerto (L09-inverso).

### §S4 — id-mismatch corregido (en MI stub, no en la mímica)
- **Verificado por fuente** (`execution/local/runtime.py` 1→EOF, 2026-07-23): la façade real =
  `dispatch`(L134, devuelve `task_id` inmediatamente vía `ensure_future`)/`stream`/`status`(L183)/
  `cancel`(L187)/`result`(L190)/`runtime_id`(L110); la coherencia la da el **registry keyed-by-id**.
- El id-mismatch que corregí era de **mi propio stub A2.1** (`dispatch` guardaba el resultado bajo un
  `task_id` distinto del que devolvía ⇒ `result()` daba `None`), **NO** un finding de la mímica.
  Corregido: `stream(task, *, task_id=None)` acepta el id de `dispatch`. **Divergencia honesta de mi
  skeleton:** mi `dispatch` corre a completión (sin async task real) ⇒ no ejercita el ciclo
  PENDING/RUNNING de la mímica (background → S22/Fase F). `cancel`(→08) y `runtime_id`/`on_event` no añadidos.

### §S1 — (ya vertida en A2.2, se re-afirma aquí)
- `effort`/`thinking`/`tool_choice` NO son passthrough de `StreamOptions`: los **traduce el bridge**
  (`stream_simple(reasoning=…)`). `Usage` NO tiene `thinking_tokens`; sí `cache_read/cache_write/cost`.

## 3. Lo que Fase A2 NO validó (honesto — se difiere, con destino)
Estas costuras se DECLARARON en `SEAMS.md` para que A2 no las diera por validadas (L09), pero el
walking skeleton NO las ejerció; su hogar es A3/Fase B–F:
- **S2** abort *disparado* (sólo el shape) · **S3** `AuthProvider` (credencial/refresh) → 08 / Fase E-F.
- **S6** wire serializer `Event→SDKMessage` → Fase F (BFF-SSE). El integrador de A2.5 consume por
  `async for` directo, sin wire.
- **S7** `on_progress` (heartbeat de tool) → 10·Bash. · **S8** fire-points STOP/POST_TOOL_USE → 06·hooks.
- **S10** `RetryPolicy` (battery `resilience`) → **declarada-no-cableada** en A2.4 (mandato "1 battery"); Fase C.
- **S17** `PermissionGate` · miembros de comportamiento de S16 (check_permissions/validate_input/
  output_schema) → A3 (06/09).
- **S19** `TaskRegistry` *rico* (TaskRecord con type/notified/output_file/pending_messages) → Fase F.
- **S20** `open`/`fork`/`delete` del repo (sólo `create`/`get_metadata`/`list` ejercitados) → 15·storage.
- **S22** force-async · **S23** teardown/reaping · **S24** watchdog real · **S25** `AgentDefinition`
  campos de ejecución → assistant / 10-11-12-13-06.
- **S9** `collect_compaction_context` (provider-seam) · **fidelidad** de la compactación → battery Fase C.

## 4. Aprendizajes de arquitectura (para Fase B)
1. **El ensamblador es la costura.** El bug crítico de la espina (S18) no era una pieza ausente sino
   un cableado ausente. El `factory` clean-room lo hace imposible de olvidar porque el turno real lo
   ejercita; Fase B debe conservar **un solo** `create_runtime` como punto único de composición.
2. **DI > global.** Sustituir `set_runner/get_runner` global por inyección al `ctx` colapsa el
   doble-camino S18/S19 sin esfuerzo extra. Aplicar el mismo criterio al `TaskRegistry` (S19) en Fase B.
3. **El base compone, no hereda.** El runner recibe una FÁBRICA de runtime-hijo (`build_child`), no
   un import — el mismo runner sirve a integrador degenerado y complejo. Es el patrón a replicar para
   toda costura que el integrador rellene.
4. **Base agnóstico probado, no afirmado.** El aislamiento (battery importada sólo por su compositor;
   `ctx.runner is None`→spawn falla) se prueba con aserciones ejecutables, no con prosa.

## 5. Ledger de cierre A2.5 (con el PASE DE VERIFICACIÓN por fuente · 2026-07-23)
| Artefacto | Lectura | Estado |
|---|---|---|
| `../05-execution.md` (tracker) | **íntegro 1→510** | E24/FIND-EXEC1, E5/LAT-EXEC2 |
| `../01-contracts.md` (tracker) | **íntegro 1→198** | CTR-01/feat 1 (S4), autogen id opaco |
| mímica `execution/runner.py` | **íntegro 1→41** | S18: global + `get_runner` lanza |
| mímica `tools/native/agent.py` | **íntegro 1→119** | S18 productor L105 |
| mímica `factory.py` | **íntegro 1→267** | `_build_local` NO llama `set_runner` (seam roto) |
| mímica `execution/local/notification.py` | **íntegro 1→72** | S21 put/drain/process |
| mímica `execution/local/runtime.py` | **íntegro 1→435** | S4 façade + `_notify`→put; drain ausente; registry inyectado L86 |
| mímica `tools/native/task_tools.py` | **íntegro 1→224** | S19 usa el global de ejecución (contra LAT-EXEC1) |
| `skeleton/*.py` (13 existentes) + `runner.py`/`factory.py`/`_integrador.py` | íntegro 1→EOF / escritos+corridos | S18/S4/S21 cableadas y corridas |

**Puerta de cierre (4 preguntas) — tras el pase de verificación por fuente:**
1. ¿Se revisó A (los `../NN.md` + la mímica que las costuras citan)? **Sí AHORA** — `../05-execution.md` y `../01-contracts.md` 1→EOF + los 6 archivos de la mímica (runner/agent/factory/notification/runtime/task_tools) 1→EOF. **En el cierre inicial NO se habían abierto; se declaró leído sin serlo — retirado.**
2. ¿Se revisó B (el spike)? **Sí** — escrito y CORRIDO (mypy 0 / ruff 0 / offline A∧B∧C / turno real end-to-end).
3. ¿Cada ✅ que afirma cableado abrió el ensamblador (archivo:L-R), sin grep-como-sustituto? **Sí AHORA**: S18 (`runner.py:36-41`+`agent.py:105`+`factory.py:178-240`), S4 (`runtime.py:134-192`), S21 (`notification.py:36-49`+`runtime.py:294-304`, drain ausente en 435 líneas).
4. ¿Todo cubierto, con doble filo? **Sí** — el pase CORRIGIÓ 2 afirmaciones MÍAS: (a) "elimina doble-camino S19" (falso: dos globals; el skeleton no toca S19); (b) "S4 id-mismatch" era de mi stub, no de la mímica. Y destapó que **05·LAT-EXEC1 del tracker es incorrecto** (`task_tools.py` sí usa el `get_registry` de ejecución) → el doble-camino S19 es real por fuente; cabo anotado para S19/Fase F.

**§ Honestidad — lo NO verificado / diferido:** el *fork* de historial (sólo spawn con prompt propio);
`background` (lanza `NotImplementedError`→S22/Fase F); `reaping`/teardown S23 (sin `finally`); auto-drain
in-loop de S21 (el integrador drena tras el turno); `scope` de `NotificationSink` (shape reducido). La
reconciliación del tracker (LAT-EXEC1 incorrecto sobre el doble-camino S19) es competencia del dueño de
`05-execution.md`, no de A2.5 — sólo se ANOTA aquí. La fidelidad del turno real depende del entorno (shim
TLS + `options.client`), no de la costura → arreglo de raíz en Fase D (`agentic_models`).

**VEREDICTO A2.5 / cierre de Fase A2:** ✅ costuras S18/S4/S21 **VALIDADAS-CORREGIDAS y ahora verificadas
por fuente 1→EOF**; walking skeleton corre un TURNO REAL end-to-end padre→subagente. Fase A2 cerrada →
siguiente = **A3** (03·context).
