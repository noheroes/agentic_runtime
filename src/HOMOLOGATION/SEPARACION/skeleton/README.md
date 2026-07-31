# Walking skeleton (Fase A2) — spike de validación de costuras

> Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/skeleton/`. Ruta base `/home/noheroes/python`.
> **Spike clean-room de la Filosofía B** (base framework + costuras). NO es producción: valida las costuras de
> `../SEAMS.md` con un TURNO real ANTES de la construcción de Fase B. El `src/agentic_runtime` mímica **no se toca**.

## Decisión de ubicación (mandato A2.1 "decidir en A2.1")
Paquete spike **co-locado con los docs de diseño** bajo `SEPARACION/skeleton/`, en vez de una rama:
- Co-locación con `00-BLUEPRINT.md`/`SEAMS.md` (el spike es artefacto de Fase A; Fase B lo graduará).
- **Aislado** del `src/agentic_runtime` mímica — fuera de `files=["src/agentic_runtime"]` de mypy ⇒ el typecheck del
  spike es explícito y no contamina el del runtime. Una rama no aportaría este aislamiento y perdería la co-locación.
- Import raíz `skeleton.*` vía `PYTHONPATH=src/HOMOLOGATION/SEPARACION` (o `MYPYPATH` para el typecheck).

## Gate del ciclo (evidencia)
- **Typecheck (gate formal A2.1):** `mypy --python-version 3.12 --strict` → **0 errores**.
  ```
  cd agentic_runtime && MYPYPATH=src/HOMOLOGATION/SEPARACION \
    .venv/bin/python -m mypy --python-version 3.12 --strict src/HOMOLOGATION/SEPARACION/skeleton
  ```
- **Lint:** `uvx ruff check src/HOMOLOGATION/SEPARACION/skeleton` → All checks passed.
- **Smoke (evidencia EXTRA, no exigida por el gate):** turno canned end-to-end, `exit 0`:
  ```
  cd agentic_runtime && PYTHONPATH=src/HOMOLOGATION/SEPARACION .venv/bin/python -m skeleton._smoke
  # canal único ordenado (S5): InitEvent -> TokenEvent -> DoneEvent -> ResultEvent
  ```

## Módulos y costuras stubadas
| archivo | rol | costuras (SEAMS) |
|---|---|---|
| `contracts.py` | T1-CONTRATO mínimo | `RuntimeTask`/`Event`+taxonomía/`ToolSchema`/`ToolResult`/`Usage`/`TaskStatus` |
| `events.py` | mecanismo base | **S5** `EventBus` (subscribe/subscribe_all/emit try-except 07·A4) |
| `seams.py` | Protocols | **S1** `ModelCallerProtocol` (mín) · **S2** `AbortSignal` · **S4** `AgentRuntime` · **S9** `CompactionMotor` (A2.4) · **S10** `RetryPolicy` (declarada, A2.4) · **S11** `UserInputProcessor` · **S16** `ToolProtocol` · **S20** `SessionRepo`+`SessionId` (A2.4) |
| `tools.py` (**A2.3**) | infra de tools | **S16** `AddTool` · `ToolPool` (assemble/find) · `ToolDispatcher` (dispatch+timeout) · **S26** `DeferredToolStrategy`+`EagerToolStrategy` |
| `stubs.py` | realizaciones pasarela | `StubModelCaller` (canned texto) · `StubToolModelCaller` (canned round-trip A2.3) · `PassthroughInputProcessor` · `NullAbortSignal` · **`InMemorySessionRepo`** (S20 default base, A2.4) |
| `battery_compaction.py` (**A2.4**) | battery OPCIONAL (NO base) | **S9** `SimpleCompactionBattery` (`CompactionMotor`); módulo aparte que NINGÚN módulo base importa — se compone por fuera |
| `loop.py` | mecanismo del turno | orquesta S11 -> S1 -> S5; **bucle MULTIVUELTA con dispatch de tools** (S16/S26, A2.3); **trigger LR1 de compactación** (S9, A2.4) |
| `runtime.py` | façade base default | **S4** `LocalAgentRuntime.stream` sobre S5 (propaga pool/dispatcher/strategy) |
| `bridge.py` (**A2.2**/A2.3) | costura REAL al motor | **S1** `AgenticModelsCaller` -> `agentic_models.stream`; A2.3: `_to_context` traduce el round-trip (user/assistant-tool_use/tool) |
| `_smoke.py` | evidencia canned | turno canned texto (A2.1) + round-trip de tool canned (A2.3) |
| `_motor.py` (**A2.2**) | evidencia REAL | corre 1 turno real texto-solo (S1 -> `agentic_models` -> API) |
| `_tools.py` (**A2.3**) | evidencia REAL | turno real con tool: modelo llama `add_numbers`, dispatch aplana, re-entra |
| `_battery.py` (**A2.4**) | evidencia composición (offline) | compone `SimpleCompactionBattery` (S9) por fuera + `InMemorySessionRepo` (S20); contraste WITH/WITHOUT battery + turno sin userId + scoping por tenant |

## Crecimiento previsto (PLAN §4 · SEAMS §5)
- **A2.2** ✅ cablear **S1** -> `agentic_models`; 1 turno real texto-solo; firma S1 **validada/corregida** (ver cierre A2.2 abajo).
- **A2.3** ✅ **S16** + dispatch (`ToolPool`/`ToolDispatcher`) + **S26** eager + 1 tool nativa; bucle multivuelta en `loop.py`; turno real (ver cierre A2.3 abajo).
- **A2.4** ✅ componer 1 battery (**S9** `SimpleCompactionBattery`, vía trigger LR1 + deps-DI; **S10** declarada) + **S20** `SessionRepo` (turno sin userId, scoping en el repo); gate de composición offline (ver cierre A2.4 abajo).
- **A2.5** **S18** `SubagentRunnerProtocol` (crítico) + **S4** + **S21**; turno end-to-end; `../SKELETON-REPORT.md`.

---

## GATEKEEPER de cierre A2.1 (adaptado a ciclo de código — `00-LEGEND.md §3.3`)

**Frase de rigor:**
> De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda; ninguna categoría se
> cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar —o colocado sin abrir,
> o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

**Adaptación (honesta):** A2.1 es un ciclo de CÓDIGO (walking-skeleton andamiaje), **no** de separación de un tracker
`../NN.md`. No hay findings que repartir ni cara-integrador que desarrollar. Las "unidades" del ledger son las **costuras
que el mandato A2.1 exige stubear** (SEAMS §5 A2.1: S4/S5/S16/S11 + el mínimo de S1/S2 que un loop necesita). La
"evidencia" es typecheck + smoke, no lectura de ensamblador.

**Ledger — una fila por costura tocada en A2.1:**

| costura | mandato A2.1 | realización | evidencia | ¿ejercitada (L09) o sólo declarada? |
|---|---|---|---|---|
| **S5** `EventBus`+`stream()` | sí | `events.py`+`runtime.py` | typecheck 0 · smoke | **ejercitada** — emit/subscribe_all/orden Init→Result en el smoke |
| **S4** `AgentRuntime` façade | sí | `LocalAgentRuntime.stream` | typecheck 0 · smoke | **ejercitada** (stream); dispatch/status/result mínimos, sin subagente (A2.5) |
| **S11** `UserInputProcessor` | sí | `PassthroughInputProcessor` | typecheck 0 · smoke | **ejercitada** (invocado pre-turno; passthrough) |
| **S16** `ToolProtocol` | sí | Protocol + `StubToolContext` | typecheck 0 | **sólo DECLARADA** — loop mínimo sin dispatch (correcto por mandato; cablea A2.3) |
| **S1** `ModelCallerProtocol` (mín) | necesaria p/ loop | `StubModelCaller` canned | typecheck 0 · smoke | **ejercitada al mínimo** — firma BORRADOR, NO valido la enriquecida (A2.2) |
| **S2** `AbortSignal` | necesaria p/ `complete` | `NullAbortSignal` | typecheck 0 | **declarada** — nunca aborta; el armado real de `ctx.stop` es 08/A2.2 |

**5 preguntas de cierre:**
1. ¿Se leyeron **ÍNTEGROS** los inputs acotados del ciclo? → **sí**: `00-BLUEPRINT.md` (1→186) y `SEAMS.md` (1→414),
   ambos 1→EOF; PLAN §4/§7 y `00-LEGEND §3.3` leídos. (No aplica `../NN.md`: A2.1 no tiene tracker.)
2. ¿Reconcilia el conteo? Costuras del mandato A2.1 = **4** (S4/S5/S16/S11); stubadas = **4/4**; añadidas por necesidad del
   loop = **2** (S1/S2, declaradas honestamente como mínimas); del mandato sin stubear = **0**.
3. ¿Cada costura que declaro **cableada** se **ejercitó** (L09, no sólo declarada)? → **sí**, y distinguido: S5/S4/S11/S1
   ejercitadas por el smoke (run exit 0, no grep); **S16 NO se reclama cableada** (sólo declarada); S1 **no** se reclama
   validada en su firma enriquecida. Gate = `mypy --strict` 0 + smoke run, no inventario.
4. ¿Cara integrador al mismo detalle que la base? → **N/A** (ciclo de código, no reparte a integrador). Se respeta la
   asimetría base↔integrador: cada stub nombra su punto de sustitución por el integrador/battery en su docstring.
5. ¿Doble filo (L10)? → **sí, honesto**: no hay clasificación ❌/🔀 que inflar (no es separación). No se reclama más de lo
   ejercitado: S16 declarada≠cableada; S1 firma mínima≠validada; `dispatch/status/result` mínimos≠ciclo-de-vida.

**VEREDICTO:** `✅ NADA PENDIENTE → A2.2 (skeleton motor · cablear S1 → agentic_models · turno real)`.
Nada del mandato A2.1 quedó sin stubear; typecheck y smoke verdes. La validación de las FIRMAS (S1 enriquecida) es el
trabajo del **próximo** ciclo (A2.2), no un pendiente de A2.1.

---

## GATEKEEPER de cierre A2.2 (ciclo de CÓDIGO · motor · `00-LEGEND.md §3.3`)

**Frase de rigor:** (la misma) — *de lo que aquí se destile nace el código; ninguna costura se declara validada sin
EJERCITARLA (L09), no por inventario.*

**Adaptación (honesta):** A2.2 es un ciclo de CÓDIGO. La "unidad" del ledger es **la costura S1** (única del mandato:
cablearla a `agentic_models` y correr 1 turno real). La "evidencia" es un turno REAL corrido (`skeleton._motor`, exit 0),
no lectura de tracker. Método aplicado con fuerza: **L09** (cablear≠existir → se EJERCITÓ con un turno real, no un grep),
**L11** (no confirmar el borrador SEAMS → se abrió el código de `agentic_models` y se **corrigió** la firma S1 donde el
borrador se equivocaba), **L00** (el bloqueo de TLS/OAuth no se difirió: se resolvió y documentó).

**Ledger — la costura del mandato A2.2:**

| costura | mandato A2.2 | realización | evidencia (L09: ejercitada, no declarada) |
|---|---|---|---|
| **S1** `ModelCallerProtocol` → `agentic_models` | sí | `bridge.AgenticModelsCaller` | **EJERCITADA con turno REAL** (`_motor`, exit 0): `claude-haiku-4-5` devolvió texto real ("Hola motor.") + `Usage(in=47,out=8,total=55,cost_usd=$0.000087)`; canal S5 ordenado Init→Token→Done→Result. mypy --strict 0 · ruff 0 · smoke canned A2.1 sin regresión (exit 0). |

**Firma S1 — qué se VALIDÓ y qué se CORRIGIÓ** (abriendo `agentic_models.providers.anthropic`, L11).
**Historia de sobre-precisión → CERRADA (auto-adversarial §3.3, 2026-07-22):** la 1ª redacción dijo "ejercitado por el
turno real" en bloque (falso por exceso); una 2ª lo bajó a 🟡 "efecto-en-cable no confirmado, A2.3+" — que era **diferir a
un después inexistente** (L00/L07). Se **cerró AHORA** verificando el cable con `on_payload` (hook real de `StreamOptions`,
anthropic.py:573-576), que captura el dict `params` EXACTO enviado al SDK:
- ✅ **CONFIRMADO EN SALIDA (comportamiento observable):** `system_override` (respuesta en español, 1 frase = honró el
  system) · `stop`→`StreamOptions.signal` (turno completó sin abortar) · `Usage` con `cost≠0` (mapeo ejercitado).
- ✅ **CONFIRMADO EN CABLE (params → SDK, `_motor` on_payload):** `temperature==0.0` · `max_tokens==64` ·
  `metadata=={"user_id":"opaque-owner"}` presentes en el payload transmitido (no sólo en el code-path). 【id-opaco: sólo
  `user_id` se reenvía, anthropic.py:320-323】. **Ya no hay "después": el cable se inspeccionó.**
- ✅ **VALIDADO `Usage` enriquecido:** el provider puebla `cache_read/cache_write/total_tokens/cost` (anthropic.py:606-611)
  y el bridge los mapea; `Usage` del spike los espeja. La mímica `caller.py:228-232` los **descartaba** (fabricaba
  `thinking_tokens=0`). `cache_*`=0 en el turno frío (sin hit previo) = esperado; el **mapeo** sí se ejercitó (`cost`≠0).
- 🔀 **CORREGIDO del borrador SEAMS §S1:** `thinking`/`effort`/`tool_choice` **NO** viajan por `StreamOptions` (el borrador
  los ponía ahí). Se leen por `getattr(options, …)` (duck-typing) y sólo se pueblan vía `stream_simple(reasoning=…)`, que
  subclasa `StreamOptions` y setea `thinking_enabled`/`effort` por atributo (anthropic.py:751-792). Quedan en la firma pero
  **bridge-traducidos**, NO passthrough; **no ejercitados** por el turno texto-solo (thinking ∉ "texto-solo"). → A2.3+/battery.
- 🔀 **CORREGIDO `Usage`:** `agentic_models.Usage` **no tiene** `thinking_tokens`; el campo ficticio de la mímica se retira.
- ✅ **S2 `AbortSignal` (forma correcta, no ejercitado):** el provider consume `getattr(signal,"aborted",False)`
  (anthropic.py:717/732); el `AbortSignal` del spike **tiene** `.aborted` ⇒ arregla el 16·A6 (la mímica pasaba
  `asyncio.Event` sin `.aborted`). El turno feliz usa `NullAbortSignal`; el abort real se ejercita en 08/A2 posterior.

**HALLAZGOS de integración A2.2 (para `SKELETON-REPORT` A2.5 · deuda a Fase D `agentic_models`):**
1. **OAuth roto con anthropic-sdk 0.109.1:** la rama oauth de `_create_client` (anthropic.py:396-411) usa
   `api_key="dummy"`+`auth_token`; ese SDK emite AMBOS `X-Api-Key: dummy` y `Bearer` ⇒ 401 "invalid x-api-key". Anular
   `x-api-key` por header tampoco sirve (el SDK rechaza header `None`). **Resolución validada:** inyectar cliente
   pre-construido (`AsyncAnthropic(auth_token=…)`, sin api_key) por `options.client`. Arreglo de raíz en Fase D (la rama
   oauth debe omitir api_key). `options.client` fuerza `is_oauth=False` ⇒ betas oauth+CC y system-CC los provee el llamador.
2. **TLS del entorno (no de la costura):** proxy MITM corporativo cuya CA openssl 3.x rechaza ("Basic Constraints not
   marked critical"). Shim aislado en `_motor` (relaja `VERIFY_X509_STRICT`, la cadena se sigue verificando); `bridge.py`
   no lo conoce. Es infraestructura del dev-box, no deuda del diseño.
3. **`is_oauth=False` desactiva `_to_cc_name` (cabo FORWARD → A2.3, destapado al leer `anthropic.py` 1→EOF):** el
   workaround `options.client` fuerza `is_oauth=False` ⇒ el motor NO mapea nombres de tool a los canónicos de Claude Code
   (anthropic.py:200/248). Irrelevante en A2.2 (texto-solo, sin tools) pero **A2.3 con 1 tool nativa bajo OAuth** debe
   canonicalizar nombres (integrador/battery) o el proveedor podría rechazarlos. Desarrollado cara-integrador en
   `00-INTEGRADORES §1.2` (refinamiento A2.2) + `SEAMS §S3` (ampliación).

**5 preguntas de cierre:**
1. ¿Se leyeron **ÍNTEGROS** los inputs acotados? → **sí**: `SEAMS.md` (1→414), skeleton A2.1 completo,
   `stream.py`/`event_stream.py`/`model_types.py` 1→EOF, y **`anthropic.py` 1→806 COMPLETO** (tramos 1-259/260-427/427-539/
   540-806; la 1ª redacción lo dejó a tramos citados — cerrado tras el reto §3.3, sin contradicción a la firma; **destapó**
   el hallazgo #3 `_to_cc_name`). `00-LEGEND §3.3` leído.
2. ¿Reconcilia el conteo? Costuras del mandato A2.2 = **1** (S1); cableadas+ejercitadas = **1/1**; sin cablear = **0**.
3. ¿La costura declarada **cableada** se **EJERCITÓ** (L09, no grep)? → **sí**: turno real corrido (`_motor` exit 0), texto
   y `Usage` reales + **cable inspeccionado** (`on_payload`), no inventario. Lo NO ejercitado se declara como tal
   (thinking/effort/tool_choice, S2-abort, cache-hit).
4. ¿Cara integrador al mismo detalle? → **NO es N/A a secas** (corrección tras reto §3.3). A2.2 no reparte findings de un
   tracker, pero **destapó obligaciones de integrador** al correr un turno OAuth real. Se **desarrollaron** (6 campos) en
   `00-INTEGRADORES §1.2` (refinamiento A2.2: construcción del cliente del motor por modo de auth; identidad-CC en el
   system; consecuencia `_to_cc_name`) + `SEAMS §S3` (ampliación auth = credencial **+** modo de cliente). Reparto de caras
   nombrado: necesidad universal (OI-M2) vs identidad-CC específica (`agentic_code`) vs arreglo de raíz Fase D. El shim TLS
   sí es del runner (infra), no obligación de integrador.
5. ¿Doble filo (L10/L11)? → **sí, honesto**: no se reclamó validado lo no ejercitado (thinking/tool_choice/abort/cache-hit);
   las divergencias del borrador se marcaron 🔀 con el tramo de `agentic_models` que lo prueba, no como ✅ heredado del doc;
   el hallazgo oauth es deuda de `agentic_models` (Fase D), no brecha A↔B del runtime inflada.

**VEREDICTO:** `✅ NADA PENDIENTE → A2.3 (skeleton tools · S16 + dispatch S26/pool + 1 tool nativa)`.
S1 cableada y **ejercitada con un turno real** (texto + `Usage` reales + cable inspeccionado; mypy 0 · ruff 0 · smoke sin
regresión); firma validada/corregida contra `agentic_models` leído 1→EOF; **3** hallazgos con destino (2 integración → Fase D;
1 forward `_to_cc_name` → A2.3), cara-integrador desarrollada en `00-INTEGRADORES §1.2`+`SEAMS §S3`. Lo no ejercitado
(thinking/effort/tool_choice, S2-abort, cache-hit) es alcance declarado de ciclos posteriores, **no** un pendiente de A2.2.

---

## GATEKEEPER de cierre A2.3 (ciclo de CÓDIGO · tools · `00-LEGEND.md §3.3`)

**Frase de rigor:** (la misma) — *de lo que aquí se destile nace el código; ninguna costura se declara cableada sin
EJERCITARLA con un turno REAL (L09), no por inventario.*

**Adaptación (honesta):** A2.3 es un ciclo de CÓDIGO. Las "unidades" del ledger son las costuras del mandato:
**S16** (`ToolProtocol` → dispatch + 1 tool nativa) y **S26** (`DeferredToolStrategy`, rama eager). La "evidencia" es un
turno REAL corrido (`skeleton._tools`, exit 0) donde el modelo LLAMA la tool y el resultado se APLANA, más un canned
determinista (`_smoke`) del mismo round-trip. Método aplicado: **L09** (cablear≠existir → round-trip EJERCITADO con turno
real, no grep), **L00/L07** (los reads que el round-trip exigía —`model_types` mensajes/tool + provider anthropic
emisión/round-trip— se hicieron AHORA, no se difirieron; no se troceó lo in-scope), **L01** (los tramos del provider que
gobiernan el round-trip se leyeron íntegros), **L09-inverso** (no se añadió superficie muerta a `ToolProtocol`).

**Ledger — costuras del mandato A2.3:**

| costura | mandato A2.3 | realización | evidencia (L09: ejercitada, no declarada) |
|---|---|---|---|
| **S16** `ToolProtocol` + dispatch | sí | `tools.AddTool` + `ToolPool` + `ToolDispatcher`; bucle multivuelta en `loop.py` | **EJERCITADA con turno REAL** (`_tools`, exit 0): `claude-haiku-4-5` emitió `tool_use(add_numbers,{a:17,b:25})` (stop=tool_calls, in=683/out=71) → `ToolDispatcher` ejecutó la tool y aplanó `'42'` con el `call_id` real `toolu_01S5…` → el loop re-entró → el modelo respondió `"17 más 25 es igual a 42."` (stop=stop). Usage ACUMULADO 2 vueltas: in=1450 out=86 total=1536 cost=$0.001880. + canned `_smoke` OK (offline). mypy --strict 0 · ruff 0 · smoke texto-solo A2.1 sin regresión. |
| **S26** `DeferredToolStrategy` | sí (dispatch/pool) | `EagerToolStrategy` (default) + Protocol | **rama EAGER ejercitada** (announced = pool entero; el modelo recibió `add_numbers`). Ramas Simulada/Nativa **declaradas, NO ejercitadas** (1 tool → nada que diferir; su hogar es la battery tool-search A3·10). Honesto: no se reclama más que la eager. |

**Qué se VALIDÓ / CORRIGIÓ abriendo `agentic_models` (L11 · provider anthropic leído en los tramos del round-trip):**
- ✅ **Shape del evento `toolcall_end` CONFIRMADO** (retracción honesta de un hallazgo preliminar mío): el provider empuja
  DICTS camelCase `{"type":"toolcall_end","toolCall":<ToolCall obj>}` (anthropic.py:699) ⇒ `bridge.py` `event["toolCall"]`
  + `tc.id/.name/.arguments` era **correcto**, no un bug. La rama estaba sin ejercitar (A2.2 texto-solo); A2.3 la ejercitó.
- ✅ **Round-trip de mensajes cableado y ejercitado:** `_to_context`/`_to_message` traducen assistant-con-`ToolCall` +
  `ToolResultMessage`; el provider los convierte (tool_use `_convert_messages` anthropic.py:196; tool_result:213 casa por
  `tool_call_id`→`tool_use_id`). `done.reason=="tool_use"→"toolUse"` (_map_stop_reason:117) → bridge `→"tool_calls"` → el
  loop re-entra. Verificado por el turno real completo.
- ✅ **Cabo forward #3 de A2.2 (`_to_cc_name` desactivado bajo `options.client`) NEUTRALIZADO para tools de nombre propio:**
  `options.client`⇒`is_oauth=False` (anthropic.py:548) ⇒ `_to_cc_name`/`_from_cc_name` bypassed (248/643) ⇒ el nombre custom
  `add_numbers` round-trippeó **verbatim** (probado: el modelo lo llamó y el resultado volvió con el mismo nombre). El mapeo
  CC-canónico sólo importa para builtins CC (Bash/Read/…); un integrador que exponga builtins deberá canonicalizar (→ battery/
  integrador, ya anotado en `00-INTEGRADORES §1.2`+`SEAMS §S3`). Para el spike A2.3 no aplica.
- ✅ **`ToolDispatcher` aísla el fallo (09·D5):** tool ausente / excepción / timeout → `is_error=True` aplanado, no tumba el
  turno. Ejercitado el camino feliz; los de error son deterministas por construcción (no se reclaman "ejercitados con turno").

**Limitaciones ejercitadas (honestidad, destapadas al leer el provider 1→EOF en el reto §3.3):**
- **Multi-tool-en-un-turno NO ejercitado:** sólo se ejercitó **1** tool-call. `_convert_messages` (anthropic.py:206-219)
  **fusiona** `toolResult` consecutivos en un único turno `user` con lista de `tool_result`; mi loop añade un
  `Message(role="tool")` por call contiguamente ⇒ la fusión sería correcta, pero **leída, no ejercitada** (tool-calls
  paralelas = A2.4+/battery).
- **Caminos de error del `ToolDispatcher`** (tool ausente / excepción / timeout → `is_error`) son deterministas por
  construcción; **no** ejercitados con turno real.

**5 preguntas de cierre:**
1. ¿Se leyeron **ÍNTEGROS** los inputs acotados? → **sí**: `SEAMS.md` tramos S16/S26/S17 (+ S4 contexto), skeleton completo
   1→EOF (8 `.py` + README), `agentic_models.model_types` 1→400 COMPLETO. Tramos del provider `anthropic.py`: al **cierre
   inicial** se abrieron con `Read` `_to_cc_name`/`_from_cc_name` (45-64), `_convert_tools` (238-261), is_oauth-con-client
   (538-592), tool_use-in (638-655); **`_map_stop_reason` (111-124), `_convert_messages` (145-234) y el bloque de emisión
   (595-735) se establecieron por GREP** — grieta detectada en el reto §3.3 (L01: grep no sustituye) y **CERRADA abriéndolos
   íntegros AHORA** (revelaron: fusión de toolResult, usage en 2 sitios, accrual de args por delta; ninguna contradijo el
   bridge). El overclaim previo de esta línea (los daba por "leídos, no grepeados") queda **corregido**.
2. ¿Reconcilia el conteo? Costuras del mandato A2.3 = **2** (S16, S26); cableadas+ejercitadas = S16 **1/1** (turno real),
   S26 **rama eager 1/1** (las otras 2 ramas declaradas, no del mandato de este ciclo); sin cablear = **0**.
3. ¿Cada costura **cableada** se **EJERCITÓ** (L09, no grep)? → **sí**: turno real corrido (`_tools` exit 0) —
   tool invocada por el modelo + resultado aplanado `'42'` + respuesta final que lo cita + usage real acumulado, más canned
   offline. Lo NO ejercitado se declara: ramas Simulada/Nativa de S26, caminos de error del dispatcher, miembros de
   comportamiento de `ToolProtocol` (permisos/concurrencia → A3).
4. ¿Cara integrador al mismo detalle? → A2.3 no reparte findings de un tracker, pero **tocó** una obligación de integrador
   (canonicalización de nombres de tool CC bajo OAuth): quedó **neutralizada** para tools propias del spike y su realización
   para builtins CC ya está desarrollada en `00-INTEGRADORES §1.2`+`SEAMS §S3` (no se re-abre aquí; no hay obligación nueva).
5. ¿Doble filo (L10/L11)? → **sí, honesto**: no se reclamó validado lo no ejercitado (ramas S26, errores del dispatcher,
   miembros de comportamiento); se **retractó** un hallazgo preliminar propio (`toolcall_end` NO era bug) tras abrir el
   provider; no se añadió superficie muerta a `ToolProtocol` (L09-inverso); las correcciones se apoyan en el tramo de
   `agentic_models` que las prueba, no heredadas del doc.

**VEREDICTO:** `✅ NADA PENDIENTE → A2.4 (skeleton battery · componer 1 battery S9/S10 + S20 SessionRepo · turno sin userId)`.
S16 cableada y **ejercitada con un turno real** (el modelo llama la tool, el resultado se aplana y re-entra; mypy 0 · ruff 0 ·
canned + real verdes · sin regresión texto-solo); S26 rama eager ejercitada; round-trip validado abriendo `agentic_models`
1→EOF en los tramos pertinentes; cabo forward #3 neutralizado. Lo no ejercitado (ramas S26, errores del dispatcher, miembros
de comportamiento de `ToolProtocol`) es alcance declarado de ciclos posteriores, **no** un pendiente de A2.3.

---

## GATEKEEPER de cierre A2.4 (ciclo de CÓDIGO · battery + identidad · `00-LEGEND.md §3.3`)

**Frase de rigor:** (la misma) — *de lo que aquí se destile nace el código; la costura de composición no se declara
válida sin COMPONER una battery real por fuera y ver al base dispararla SIN conocerla (L09), no por inventario.*

**Adaptación (honesta):** A2.4 es un ciclo de CÓDIGO cuyo gate es ARQUITECTÓNICO (composición), no "1 turno real"
(eso fue A2.2/A2.3; el end-to-end real es A2.5). Por eso se valida OFFLINE con callers CANNED deterministas
(`skeleton._battery`, exit 0) + `mypy --strict` 0 + `ruff` 0 + grep de aislamiento, y **no** se re-corre el turno OAuth
(ver honestidad abajo). Las "unidades" del ledger son las costuras del mandato: **S9** (`CompactionMotor`, la battery
que se compone) y **S20** (`SessionRepo`, identidad en el repo). Método: **L09** (la composición se EJERCITA
—battery inyectada, trigger disparado, evento emitido— no se declara), **L09-inverso** (no se añadió superficie muerta:
S10 se DECLARA como el mismo patrón pero NO se ejercita porque el mandato es "1 battery"), **L00/L07** (los reads del
ciclo —SEAMS §S9/S10/S20 + skeleton in-scope 1→EOF— se hicieron AHORA; nada troceado), **L10** (lo que el base delega
a la battery/integrador por diseño B es 🔀, no gap).

**Ledger — costuras del mandato A2.4:**

| costura | mandato A2.4 | realización | evidencia (L09: ejercitada, no declarada) |
|---|---|---|---|
| **S9** `CompactionMotor` (battery vía composición) | sí | `battery_compaction.SimpleCompactionBattery` (módulo APARTE) + trigger LR1 en `loop.py` + `CompactBoundaryEvent` (07·H1) + inyección por `LocalAgentRuntime(compaction=…)` (S27 deps-DI) | **EJERCITADA offline** (`_battery`, exit 0): MISMO turno canned de tool, `compaction=None` ⇒ **0** `CompactBoundaryEvent` (trigger inerte, comportamiento idéntico a A2.3), `compaction=SimpleCompactionBattery(threshold=3,keep_last=2)` ⇒ **1** `CompactBoundaryEvent(collapsed=1)` y ambos turnos citan `42` (comportamiento preservado). **Aislamiento probado (grep 1→EOF):** `import ... battery_compaction` aparece SÓLO en `_battery.py` (el compositor); NINGÚN módulo base (loop/runtime/seams/contracts/events/stubs/tools/bridge/__init__) lo importa ⇒ el base dispara el motor conociendo sólo el Protocol. mypy 0 · ruff 0 · `_smoke` sin regresión (A2.1 texto + A2.3 round-trip verdes). |
| **S20** `SessionRepo` (turno sin userId) | sí | `SessionRepo` Protocol + `SessionId` opaco (seams) + `InMemorySessionRepo` default base (stubs) | **EJERCITADA offline** (`_battery`): `repo.create({owner,tenant,plan})` → `SessionId` OPACO `sess_…`; el `RuntimeTask` viaja con **sólo** `session_id` (sin `owner_id`, sin `user_id`); un `_MetadataProbe` sobre el seam S1 **assert**a que la metadata que el base pasó al modelo **no contiene `user_id`** (turno corre sin userId). El integrador **scopea por SU metadata**: `repo.list({tenant:'acme'})==['sess_…']` excluye la sesión de otro tenant; `get_metadata` vive en el repo, NO en el base. |
| **S10** `RetryPolicy` | **NO** (mandato = "1 battery") | Protocol DECLARADO en `seams.py`, sin battery ni cableado | **NO ejercitada, a propósito (L09-inverso).** Se fija que es EL MISMO patrón de composición que S9 (seam base + trigger en el loop + battery inyectada por fuera); su battery `resilience` + cableado (loop envuelve `complete()`, LR2) → **Fase C**. Declarada-no-cableada explícito: que exista el Protocol NO la da por validada. |

**Qué se VALIDÓ de la costura de composición (L09 · leyendo el ensamblador —`loop.py`— 1→EOF, no inventario):**
- ✅ **Trigger vivo, no rama muerta:** el `if self._compaction is not None and should_compact(...)` en la frontera de
  vuelta del bucle multivuelta se **alcanza y dispara** — probado por el contraste 0↔1 `CompactBoundaryEvent` con la MISMA
  entrada, cambiando SÓLO la inyección. Sin battery el default `None` deja el turno idéntico a A2.3 (agnosticismo del base).
- ✅ **El base no conoce la battery:** `battery_compaction` fuera de `__init__` (no es superficie del base) y sin import
  desde ningún módulo base (grep). El compositor (`_battery.py` = cara integrador del spike) es el único que la importa e
  inyecta. Esto ES la Filosofía B: base = Protocol + trigger; battery = paquete OPCIONAL compuesto por fuera.
- ✅ **Identidad opaca (S20):** el runtime lee sólo `task.session_id` (opaco); la metadata rica (owner/tenant/plan) vive en
  el repo del integrador y NO se threadea al loop/modelo (probado por `_MetadataProbe`). 🔀 por diseño B (no gap): el base
  delega la atribución de identidad al repo — el nido del hilo transversal de identidad (rollup DEUDA-A en A3.DA).

**Limitaciones / honestidad (lo que A2.4 NO validó):**
- **Turno OAuth real NO re-corrido este ciclo.** El cambio al camino real es UN branch guardado (`compaction is not None`)
  **inerte** cuando `compaction=None` — que es el default que usan `_motor`/`_tools`. Ambos siguen en los 14 archivos que
  `mypy --strict` typechea (compilan); su comportamiento en runtime es inalterado por construcción. **No** se gastó un turno
  real OAuth (no es el gate de A2.4). Declarado como no-re-verificado-este-ciclo, con el argumento de inercia.
- **Fidelidad de la compactación NO validada** (sólo la COMPOSICIÓN). `SimpleCompactionBattery` es trivial: funde la cabeza
  y conserva `keep_last` (la cola con el sub-round-trip de tools queda válida). Qué preservar / budget de tokens /
  microcompact-snip-collapse = battery `compaction` de **Fase C**; A2.4 no lo reclama.
- **`collect_compaction_context`** (firma-provider de S9 en SEAMS) DECLARADA en SEAMS pero NO implementada aquí — sin
  consumidor sería superficie muerta (L09-inverso); su hogar es la battery de Fase C.
- **S10 retry** declarada, no ejercitada (arriba).

**5 preguntas de cierre:**
1. ¿Se leyeron **ÍNTEGROS** los inputs acotados? → **sí**: lecciones skill 00–11 (PASO 0) 1→EOF; `00-LEGEND §3.3`
   (gatekeeper); `SEAMS.md` tramos **S9** (215-225), **S10** (227-237), **S20** (330-345) + matriz productor→consumidor
   (392-427); skeleton in-scope 1→EOF (contracts/seams/loop/runtime/stubs/tools/events + cabecera bridge + runners
   `_smoke`/`_tools`). Nada troceado (L07).
2. ¿Reconcilia el conteo? Costuras del mandato A2.4 = **2** (S9 componer battery, S20 sesión sin userId); ejercitadas =
   **2/2**; declaradas-no-del-mandato = **1** (S10, honesta); sin cablear del mandato = **0**.
3. ¿Cada costura **cableada** se **EJERCITÓ** (L09, no grep)? → **sí**: `_battery` exit 0 con el contraste WITH/WITHOUT
   (0↔1 `CompactBoundaryEvent`) + assert de no-userId + scoping del repo; aislamiento base↔battery probado por grep 1→EOF
   sobre los módulos base. Lo NO ejercitado se declara (turno OAuth real, fidelidad de compactación, S10, provider-seam de S9).
4. ¿Cara integrador al mismo detalle? → **sí**: el compositor `_battery.py` ES la cara integrador del spike (crea la sesión,
   elige la metadata, inyecta la battery, scopea por tenant) — desarrollada al mismo nivel que el base. La obligación de
   integrador "poseer la identidad por fuera + scopear por su metadata" quedó ejercitada, no dejada en "→ integrador".
5. ¿Doble filo (L10/L11)? → **sí, honesto**: la delegación de identidad al repo y la ausencia de motor de compactación en
   el base son **🔀 por diseño B**, no gaps inflados; y NO se disfrazó de 🔀 nada que fuera brecha (S10 se declara
   pendiente-de-Fase-C explícito, no "hecho"); no se añadió superficie muerta (S10/`collect_compaction_context` declaradas
   sin fingir cableado).

**VEREDICTO:** `✅ NADA PENDIENTE → A2.5 (skeleton integrador · S18 SubagentRunnerProtocol [crítico] + S4 + S21 · turno end-to-end · SKELETON-REPORT.md)`.
S9 EJERCITADA por composición real (battery inyectada por fuera, trigger del base disparado, base agnóstico probado por
grep); S20 EJERCITADA (id opaco + turno sin userId + scoping en el repo); S10 declarada-no-cableada (Fase C, honesto).
mypy 0 · ruff 0 · `_battery` + `_smoke` verdes · sin regresión. Lo no verificado (turno OAuth real inerte-guardado,
fidelidad de compactación, provider-seam de S9) es alcance de ciclos/fases posteriores, **no** un pendiente de A2.4.
