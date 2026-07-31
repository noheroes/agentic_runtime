# 16 · models — SEPARACION (Filosofía B)

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/16-models.md`.
> **Ciclo A1.2** del PLAN §4. Fuente: tracker `../16-models.md` (leído íntegro 1→452, incl. re-visita L09/gate-11,
> §Plan MoR1-8, ledgers). Esquema: `00-LEGEND.md`. Re-clasifica cada finding de fidelidad-de-capacidades bajo B
> (base↔costuras↔batteries↔integrador). **No es otra tabla de deuda:** es el reparto del subsistema del **motor de
> modelo** en sus destinos de construcción.

## Naturaleza de la categoría

Esta es la categoría **más "T1-MOTOR"** de la espina, y la única partida ya **físicamente separada** bajo B:

- **`agentic_models`** (paquete aparte, port de `pi/ai`, multi-provider) = **la implementación del T1-MOTOR**. Ya
  vive fuera del runtime; el reparto B no lo re-homa — lo confirma como **el motor** (registro de modelos, providers,
  SSE, transform_messages, cache_control wire, betas, coste). Sus ~30 providers = **superset** sin contraparte
  canónica (L10 anti-padding, NO ⛔-por-título: el tracker abrió cabeceras + registro).
- **El puente `models/{caller.py, protocol.py}`** = la **costura `ModelCallerProtocol`** — el punto donde el
  **base loop** (productor, `agent_loop.py:235`) llama al motor (consumidor, `AgenticModelsCaller` o un caller del
  integrador). **Es el boundary firme donde enchufan AMBOS integradores** (memoria pi-runtime-reference: el motor +
  los contratos de datos son las joyas reutilizables; el degenerado usa el bridge, el complejo tipo openclaw embebe
  el motor y lo dirige por el protocolo de eventos).

**Hallazgo raíz reencuadrado bajo B:** toda la Deuda-A de 16 es que **la costura `ModelCallerProtocol` es demasiado
DELGADA** — su firma `complete()` (protocol.py:28-37) no transporta thinking/effort/temperature/max_tokens/
output_format/tool_choice, y sus eventos de retorno degradan Usage (sin cache/coste), descartan thinking, y colapsan
la taxonomía de error a string. El motor **ya trae la maquinaria**; falta **enriquecer la costura** para que el base
la pida y la reciba. La resiliencia (retry/fallback/watchdog) NO es del motor (lib de una request por diseño) → es
**battery compuesta en torno a la costura, en el loop**. Verificado abriendo B **ESTE ciclo** (L09/L11):
`complete()` sin params de razonamiento (protocol.py:28-37); call-site `agent_loop.py:235` pasa solo
`{stop, model_id}` (+`system_sections`/`system_override` condicionales, :227-234); `Usage(…thinking_tokens=0)`
tirando cache (caller.py:228-232); `thinking_*` skip (caller.py:245); `signal=stop` asyncio.Event (caller.py:188-190);
`ErrorEvent(message=str)` (caller.py:236-242); una sola `stream()` sin retry (caller.py:204).

---

## 1. Tabla por finding

### A · Puente / costura `ModelCallerProtocol` (`caller.py`, `protocol.py`)

| ID | resumen (comportamiento observable) | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **A1** 🔀 | Ensamblado de system prompt (base+secciones; override subagente) | núcleo (+ atribución = cáscara-CLI) | **T2-COSTURA** (assembly) + **CLI-ONLY** (atribución/CLI-prefix) + **BATTERY caching** (split bloques cache-scoped) | costura `ModelCallerProtocol` (assembly, caller.py:17-30) + integrador (atribución) + battery caching (block-split) | — | mantener `_compose_system_prompt` en la costura; `getAttributionHeader`/`getCLISyspromptPrefix` → integrador (agentic_code terminal); split de bloques con `cache_control` por-scope → battery caching |
| **A2** ❌ FIND-MODELS1 | Extended thinking / reasoning / effort | núcleo | **T1-MOTOR** (enriquecer costura) | costura `ModelCallerProtocol.complete` gana `thinking`/`effort` | — | **CORE-GAP**: el motor ya soporta thinking; la costura no lo transporta (call-site :235 sin param). Enriquecer firma (MoR1); `ModelRequest.thinking_budget` = tipo muerto → uso real o borrar |
| **A3** ❌ FIND-MODELS2 | Usage (cache_read/write + coste + thinking) | núcleo | **T1-CONTRATO** (shape `Usage`) | paquete contratos `Usage` (+cache/coste) **= 07·EVT1** + mapeo en la costura | — | **CORE-GAP**: `Usage(…thinking_tokens=0)` (caller.py:228-232) tira `u.cache_read`/`cache_write`/coste que el motor SÍ da; el loop nunca lee `done.usage`. Enriquecer DTO + mapeo (MoR2). Coordinar shape con 07 |
| **A4** ❌ FIND-MODELS3 | Eventos de razonamiento (thinking_delta/firma) | núcleo | **T1-CONTRATO** (`ThinkingEvent`→07) + **T2-COSTURA** (emisión) | contratos `ThinkingEvent` (07) + la costura deja de saltar `thinking_*` | — | **CORE-GAP**: caller.py:245 descarta `thinking_*`. Nuevo evento + persistir `ThinkingContent`+firma para replay (MoR3, tras MoR1) |
| **A5** 🟡 | Mapeo de stop_reason | núcleo | **T2-COSTURA** (traducción del caller) | costura `ModelCallerProtocol` | — | extender el mapeo (refusal→policy, max_tokens→recovery, context-window→recovery); hoy **passthrough puro** `"tool_calls" if reason=="toolUse" else (reason or "stop")` (caller.py:224-227) — **sin rama refusal/sensitive** (ver §honestidad: el tracker cita un `_map_stop_reason` inexistente en este `caller.py`) |
| **A6** ❌ FIND-MODELS4 | Abort mid-stream | núcleo | **T1-MOTOR** (costura de señal) | costura de señal (bridge envuelve `stop`) **+ 08·signals** | eje **ejecución** (aborto del run) | **CORE-GAP**: caller.py:188-190 pasa `asyncio.Event` como `signal`; el provider chequea `.aborted` (Event no lo tiene) → abort ignorado. Envolver en `CombinedAbortSignal` (MoR4). Doblemente latente: en standalone `ctx.stop` nunca se ARMA (08) |
| **A7** ✅ | Resolución de modelo por request `(provider,id)` | núcleo | **T1-MOTOR** | costura/motor (ya fiel) | — | **sin acción** — `get_registry().get_by_provider` + `ModelNotFoundError` (caller.py:199-202, re-abierto ESTE ciclo); consumidor loop pasa `model_id` (:235) |
| **A8** ✅ | Capability `native_tool_search` | núcleo | **T1-MOTOR** (flag de capacidad) | costura/motor + cabo **09·tools-infra** | — | **sin acción** — `supports_native_tool_search` (caller.py:131-144) consultado por el loop para elegir estrategia diferida (agent_loop.py:144-146, re-abierto ESTE ciclo); threshold/mode-gating viven en 09 |

### B · Motor (`agentic_models/providers/anthropic.py` + core) — ya separado

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **B1** ❌ FIND-MODELS5 | Retry/backoff (10×, jitter, retry-after, 408/409/5xx) | núcleo | **BATTERY resilience** (+ **T2-COSTURA** wrapper en loop) | battery **resilience** + costura `with_retry` en **02·loop** | — | **CORE-GAP**: NO va en `agentic_models` (una request por diseño); es battery que envuelve la costura en el loop (MoR6). Cabo 07·J3 `api_retry` |
| **B2** ❌ FIND-MODELS6 | Fallback de modelo en 529 (MAX 3→FallbackTriggered) | núcleo | **BATTERY resilience** | battery resilience + 02·loop | — | **CORE-GAP**: parte de la battery resilience (MoR6) |
| **B3** ❌ FIND-MODELS7 | Fallback streaming→non-streaming | núcleo | **BATTERY resilience** | battery resilience + 02·loop | — | **CORE-GAP**: parte de la battery resilience (MoR6) |
| **B4** ❌ | Watchdog idle + detección de stalls | núcleo | **BATTERY resilience** (idle-timeout) | battery resilience + **08·signals** / **05** (`arm_watchdog`) | eje **ejecución** (vida del stream) | **CORE-GAP**: idle-timeout en la battery resilience; se liga a `arm_watchdog` (01·CTR-15) y 08·signals |
| **B5** 🟡 FIND-MODELS8 | Betas dinámicos (`getMergedBetas`) | núcleo | **T1-MOTOR** (betas wire) + cabling por-capacidad | motor + cabos **09** (tool-search) + **MoR1** (effort) | — | CORE-GAP **parcial**: los betas core (tool-search/effort/context-management) se cablean por capacidad (MoR8); la mayoría (1P/experimental) = superset. Hoy fijo (fine-grained/interleaved/oauth) |
| **B6** 🟡 | Cache control (TTL-elegibilidad/scope/skip-write/cache_edits) | núcleo | **BATTERY caching** | battery **caching** | eje **persistencia** (scope de caché) leve | estrategia de caché rica → battery caching; hoy básico (ephemeral último-user/tool/system + short/long por `PI_CACHE_RETENTION`) |
| **B7** 🟡 | Effort / `output_config` / task_budget | núcleo | **T1-MOTOR** (= A2) | costura (misma que MoR1) | — | ruta `effort`/`output_config` existe en `_build_params` pero el puente nunca la puebla → se cubre con MoR1 |
| **B8** 🟡 | temperature | núcleo | **T1-MOTOR** (param de costura) | costura `complete` | — | exponer `temperature` en la firma/`StreamOptions`; hoy solo si set y sin thinking |
| **B9** 🟡 | max_tokens (`getMaxOutputTokensForModel`) | núcleo | **T1-MOTOR** (param) + **BATTERY** (política de cap) | costura + battery (cap/overflow-adjust) | — | resolución de cap (env override/slot-cap 8k/upper-limit/non-streaming 64k) = política → battery/motor; hoy `options.max_tokens or model.max_tokens` |
| **B10** 🟡 | tool_choice / metadata(user_id) / session-affinity | núcleo (transporta id) | **T1-MOTOR** (tool_choice) + **T3-INTEGRADOR** (metadata identidad) | costura (tool_choice) + integrador (metadata id opaco) | eje **persistencia+ejecución** · **id opaco** | tool_choice → param de la costura; `metadata.user_id`/session-affinity = integrador vía **id opaco** (consolidar transversal **A3.DA**) |
| **B11** ❌ FIND-MODELS9 | Structured outputs (`output_format`+beta) | núcleo | **T1-MOTOR** (capacidad de costura) | costura `complete` gana `output_format` | — | **CORE-GAP**: puente sin `output_format`; el canónico `BetaJSONOutputFormat`. *(Sin MoR dedicado en el tracker — sub-ítem propio; ver §2.3)* |
| **B12** 🟡 | Strip media (>100) / image-downgrade non-vision | núcleo | **T1-MOTOR** (transform_messages) | motor `agentic_models` | — | image-downgrade ✅ ya; strip-cap de media = adición al motor; parcial |
| **B13** ✅ | Reparación tool_use↔tool_result | núcleo | **T1-MOTOR** (transform_messages) | motor | — | **sin acción** — `transform_messages` (synthetic "No result"+is_error, salta assistant errored/aborted); evidencia = lectura íntegra de B en el tracker (transform_messages.py:150-171) |
| **B14** ✅ | Parse SSE (valida `message_stop`) | núcleo | **T1-MOTOR** | motor | — | **sin acción** — parser propio `_iterate_sse`/`_iterate_anthropic_events` |
| **B15** 🟡 | Coste (`UsageCost`) | núcleo | **T1-CONTRATO** (Usage coste = A3) + **T1-MOTOR** (cálculo) | contratos Usage + motor (ya calcula) | — | el motor computa `calculate_cost_values`→`UsageCost`; **el puente lo tira** → mismo fix que MoR2 (A3) |
| **B16** ✅ | Fine-grained / eager input streaming | núcleo | **T1-MOTOR** | motor | — | **sin acción** — beta fine-grained condicional |
| **B17** ✅ | OAuth (`sk-ant-oat`): tool-name↔CC, betas, user-agent | núcleo (+ credencial = integrador) | **T1-MOTOR** (mapeo wire) + **T3-INTEGRADOR** (credencial) | motor (mapeo) + integrador (credencial, ver D2) | — | **sin acción** en el mapeo (`_to_cc_name`/`_from_cc_name` fieles); el aprovisionamiento de credencial es del integrador (D2) |

### C · Manejo de error

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **C1** ❌ FIND-MODELS10 | Taxonomía de error (~30 ramas tipadas) | núcleo | **T1-CONTRATO** (`ErrorEvent.category`→07·D5) + **T2-COSTURA** (clasificación) | contratos `ErrorEvent` (07·D5, enum-7-val) + costura clasifica | — | **CORE-GAP**: `ErrorEvent(message=str)` (caller.py:236-242) colapsa todo. Categoría tipada (rate_limit/invalid_request/auth/billing/overload/unknown), espejo reducido de `classifyAPIError` (MoR5). Hogar shape = **07·events D5** |
| **C2** 🟡 FIND-MODELS11 | Detección context-overflow → compactación | núcleo | **T2-BASE-MECANISMO** (ruteo del loop) + **BATTERY compaction** | **02·loop** ruteo + seam **01·contracts** `CompactionProvider` | eje **persistencia** (scope compactación) | **CORE-GAP (cabling)**: `agentic_models/utils/overflow.py::is_context_overflow` existe pero no cableado; el loop lo pasa post-stream y enruta a `CompactionProvider` (MoR7) |
| **C3** 🟡 | Refusal (`getErrorMessageIfRefusal`) | núcleo | **T2-COSTURA** (mapeo, = A5/C1) | costura | — | refusal→policy msg (parte de A5/C1); hoy **refusal NO se trata**: pasa raw como `stop_reason` en el `DoneEvent` (caller.py:227). El tracker cita `_map_stop_reason` refusal→`error`, **inexistente en este `caller.py`** (§honestidad, L11) — la brecha es mayor de lo que el doc previo implicaba |
| **C4** ⛔ | Detalle conexión/SSL/HTML-sanitize (`errorUtils.ts`) | cáscara-CLI | **CLI-ONLY / INTERFAZ** | integrador (front/diagnostics) | — | SSL codes/cause-chain/nested-error/CloudFlare-HTML = capa de presentación de diagnóstico del integrador; el runtime lleva `diagnostics.py` mínimo. NO deuda A↔B |

### D · Auth / cliente

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **D1** 🔀 | Cliente multi-provider | núcleo | **T1-MOTOR** (superset) | motor `agentic_models` | — | **🔀 por diseño B** (más amplio: ~30 providers vs Anthropic-only). Providers propios = superset; NO deuda (L10 anti-padding) |
| **D2** 🟡 | OAuth subscriber + refresh pre-request | núcleo (auth) | **T2-COSTURA** (auth-provider seam) + **T3-INTEGRADOR** (credencial) | costura + integrador | — | `utils/oauth/anthropic.refresh` existe pero no auto-invocado pre-request; o el motor auto-refresca o el integrador provee credencial fresca por request. El aprovisionamiento (sk-ant-oat/authToken) = integrador |
| **D3** 🟡/⛔ | Custom headers / proxy / session-container / apiKeyHelper | núcleo(transporte)/integrador | **T3-INTEGRADOR** (transporte/deployment) | integrador | eje **ejecución** (session-container) leve | config de transporte/deployment = política del integrador; hoy passthrough `options.headers` + session-affinity condicional |

### E · Diagnóstico / telemetría (bloque agrupado — abierto y clasificado en el tracker)

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **E** ⛔ | `promptCacheBreakDetection.ts` (727) · `logging.ts` (788) · `dumpPrompts.ts` (226) · `sessionIngress.ts` (514) | cáscara-CLI / observabilidad | **CLI-ONLY / INTERFAZ** + **T3-INTEGRADOR** (observabilidad) | integrador (sink de observabilidad/telemetría) | eje **persistencia** (session-log) en sessionIngress | atribución de cache-break/analytics `logAPIQuery/Success/Error`/gateway-detection/debug-`/issue`/session-log remoto = capa de observabilidad del integrador (agentic_assistant analytics/BFF; agentic_code mínimo). Runtime = `diagnostics.py` mínimo. NO deuda A↔B. Abiertos 1→EOF en el tracker |

### F · Endpoints de cuenta / billing (bloque agrupado — abierto uno a uno en el tracker)

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| **F** ⛔ | `bootstrap` · `usage` · `firstTokenDate` · `adminRequests` · `overageCreditGrant` · `ultrareviewQuota` · `referral` · `grove` · `metricsOptOut` · `filesApi` | cáscara-CLI / integrador | **T3-INTEGRADOR** (front/BFF) | integrador `agentic_assistant` (front: bff/KrakenD/Keycloak/MinIO); `filesApi`→attachments | eje **persistencia** (cuenta/billing/attachments) | clientes axios de cuenta/utilización/admin/overage/referral/metrics-opt-out/attachments = viven en el **front** del integrador complejo; `agentic_code` degenerado no tiene ninguno. NO deuda A↔B. Abiertos 1→EOF en el tracker |

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica (nombre · productor invoca · consumidor implementa)
- **`ModelCallerProtocol`** (T1-MOTOR, **la costura central**) — productor: base loop (`agent_loop.py:235`
  `complete(...)`) · consumidor: bridge `AgenticModelsCaller` (**battery por defecto**) **o** caller del integrador
  complejo. **ENRIQUECIMIENTO = el grueso del trabajo:** la firma `complete()` gana `thinking`/`effort`/`temperature`/
  `max_tokens`/`output_format`/`tool_choice`; sus eventos de retorno pasan a `Usage`(cache/coste), `ThinkingEvent`,
  `ErrorEvent(category)`. *Los eventos que produce son shapes T1-CONTRATO → definidos en 07·events.*
- **costura de señal de abort** (T1-MOTOR) — productor: el puente envuelve `ctx.stop` (asyncio.Event) en un objeto
  con `.aborted` (`CombinedAbortSignal`) · consumidor: el provider del motor (`signal.aborted`). *Coordina con 08·signals
  (armado real de `ctx.stop`) — hoy doblemente latente.*
- **`with_retry`** (T2-COSTURA en el loop) — productor: el loop invoca el model-call a través de ella · consumidor:
  **battery resilience**. *Espejo reducido de `withRetry.ts`; NO en `agentic_models` (lib de una request).* Hogar 02·loop.
- **auth-provider seam** (T2-COSTURA) — productor: el puente pre-request · consumidor: integrador (credencial/refresh).

### 2.2 Batteries que alimenta (nombre · alcance)
- **resilience** — retry/backoff+jitter/retry-after + 529→fallback-de-modelo + streaming→non-streaming + idle-watchdog
  (B1/B2/B3/B4, FIND-MODELS5/6/7). Se **compone** en torno a `with_retry` en el loop (02). Emite `api_retry` (07·J3).
- **caching** — estrategia de `cache_control` (TTL-elegibilidad/global-scope/skip-write/cache_edits + split de bloques
  cache-scoped del system prompt) (B6, A1-parte). Compone/sustituye la maquinaria wire del motor.
- **compaction** — **consumidor** del trigger de overflow: el loop rutea `is_context_overflow` → `CompactionProvider`
  (C2). El seam nace en 01·CTR-09; el motor de compactación se homa en 02·loop. Models aporta **la detección**.

### 2.3 CORE-GAPs (brechas A↔B reales → rollup `DEUDA-A.md`)
- **FIND-MODELS1** (A2/B7) — thinking/effort no cableados: la costura es demasiado delgada. *(La causa raíz de la
  categoría: el motor tiene la ruta, el puente nunca la puebla.)*
- **FIND-MODELS2** (A3/B15) — Usage degradado (sin cache/coste); shape `Usage` = **07·EVT1** (misma estructura).
- **FIND-MODELS3** (A4) — eventos thinking descartados.
- **FIND-MODELS4** (A6) — abort roto (tipo de señal equivocado); ligado **08·signals**.
- **FIND-MODELS5/6/7 + B4** — sin resiliencia (retry/fallback/watchdog) → **battery resilience**, hogar **02·loop**.
- **FIND-MODELS9** (B11) — sin structured outputs; **sub-ítem propio SIN MoR en el tracker** (§Plan MoR1-8 no lo
  cubre) — se registra aquí como CORE-GAP con acción "añadir `output_format` a la costura".
- **FIND-MODELS10** (C1) — taxonomía de error colapsada; shape = **07·events D5**.
- **FIND-MODELS11** (C2) — overflow no cableado; ruteo **02·loop** + seam **01·contracts** `CompactionProvider`.
- **FIND-MODELS8** (B5, parcial) — betas core (tool-search/effort/context-management) sin cablear; cabos 09 + MoR1.

### 2.4 DEUDA-B (higiene interna del runtime, NO A↔B — L10/L11)
- **LAT-MODELS1** — `factory.ModelsConfig.extras` + campo `RuntimeConfig.models` (factory.py:83) **nunca consumidos**
  por `_build_local` (slot de config muerto; el integrador arma su `model_caller`/`Model` directo). Extensión sin
  contraparte canónica ⇒ tech-debt B-interno → **DEUDA-B §B-orphans (ítem 9)**.
- **`ModelRequest.thinking_budget`** (protocol.py:18) — tipo muerto (no referenciado por `complete`, grep prod = solo
  def + re-export). Se resuelve con MoR1 (uso real o borrar); se registra en §B-orphans junto a LAT-MODELS1.

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05; vertido formal en A1.7)
Con **capacidad observable · origen (costura del base) · firma que consume · cableado en el integrador · orden · criterio de aceptación**:

- **OI-M1 · Proveer el model-caller** *(contrato base común — must-be universal)* — **capacidad:** todo integrador
  cablea un `ModelCallerProtocol` (sin él el loop no ejecuta: `agent_loop.py:181-183` avisa y retorna). **origen:**
  costura `ModelCallerProtocol` (A-block). **firma:** `complete(messages, tools, *, stop, model_id, thinking, effort,
  temperature, max_tokens, output_format, tool_choice, system_sections, system_override)` (enriquecida). **cableado:**
  degenerado (agentic_code) usa el **bridge `AgenticModelsCaller`** (battery); complejo (agentic_assistant, openclaw-like)
  puede embeber el motor y dirigirlo por eventos. **orden:** prerrequisito de todo turno. **aceptación:** un turno real
  end-to-end texto-solo (validado en A2.2). *(realización: bridge trivial vs caller propio)*
- **OI-M2 · Proveer credencial/auth lifecycle** *(§1 política)* — **capacidad:** api_key/OAuth (sk-ant-oat) + refresh
  pre-request. **origen:** D2 (auth-provider seam) + B17 (credencial). **firma:** `api_key`/`options` del caller +
  refresh. **cableado:** el integrador inyecta la credencial y (complejo) la refresca por-usuario. **orden:** con OI-M1.
  **aceptación:** una request OAuth con token caducado se refresca sin fallar.
- **OI-M3 · Metadata de identidad del model-call** *(transversal A3.DA)* — **capacidad:** `metadata.user_id`/
  session-affinity al provider. **origen:** B10. **firma:** id **opaco** en `StreamOptions.metadata`. **cableado:** el
  integrador setea el id; el runtime no lo interpreta. **orden:** con el hilo de identidad (A3.DA). **aceptación:** el
  complejo particiona affinity por tenant sin que el runtime vea el grafo; el degenerado omite (cero ceremonia).
- **OI-M4 · Atribución + CLI-syscall-prefix del system prompt** *(§interfaz — CLI-ONLY)* — **capacidad:**
  `getAttributionHeader(fingerprint)`/`getCLISyspromptPrefix`. **origen:** A1-parte. **firma:** el integrador aporta
  el `base` del system prompt al caller. **cableado:** agentic_code (terminal) compone el prefijo; agentic_assistant
  compone el suyo. **orden:** independiente. **aceptación:** el system prompt del integrador llega intacto como `base`.
- **OI-M5 · Sink de observabilidad/telemetría** *(§interfaz)* — **capacidad:** cache-break attribution / `logAPIQuery`/
  gateway-detection / `/issue` dump / session-log. **origen:** bloque E. **firma:** eventos del stream + `diagnostics.py`.
  **cableado:** agentic_assistant → analytics/BFF; agentic_code → mínimo/stdout. **orden:** independiente. **aceptación:**
  los eventos del turno se pueden observar sin tocar el core.
- **OI-M6 · Endpoints de cuenta/billing/attachments** *(§específico agentic_assistant)* — **capacidad:** bootstrap/
  utilización/overage/referral/metrics-opt-out/Files-API. **origen:** bloque F. **firma:** clientes del front. **cableado:**
  agentic_assistant (bff/KrakenD/Keycloak/MinIO); agentic_code degenerado = ninguno. **orden:** capa front (Fase F).
  **aceptación:** el core opera sin ninguno de ellos (son del producto, no del turno).
- **OI-M7 · Presentación de diagnóstico conexión/SSL** *(§interfaz — CLI-ONLY)* — **capacidad:** SSL codes/cause-chain/
  CloudFlare-HTML sanitize. **origen:** C4. **firma:** consume `ErrorEvent(category)` (tras MoR5). **cableado:** el
  integrador renderiza el diagnóstico. **orden:** tras MoR5. **aceptación:** un error de conexión muestra hint útil.
- **OI-M8 · Config de transporte/deployment** *(§específico)* — **capacidad:** proxy/headers/session-container/apiKeyHelper.
  **origen:** D3. **firma:** `options.headers`/transporte del caller. **cableado:** el integrador configura el transporte.
  **orden:** deployment. **aceptación:** el caller respeta proxy/headers del integrador.

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor (lema de la etapa):**
> De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda; ninguna categoría
> se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar —o colocado sin
> abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### 3.1 Ledger — una fila por finding

| ID | TIER | destino | cara | evidencia | detalle | nota-identidad |
|---|---|---|---|---|---|---|
| A1 | T2-COSTURA + CLI-ONLY + BATTERY caching | costura + integrador + battery caching | ambas | ensamblador `caller.py:17-30`+`agent_loop.py:227-234` abierto ESTE ciclo | sí (§2.1 + OI-M4) | — |
| A2 | T1-MOTOR | costura `complete` (thinking/effort) | base | `protocol.py:28-37`+`agent_loop.py:235` abierto ESTE ciclo (sin param) | sí (§2.3, MoR1) | — |
| A3 | T1-CONTRATO | contratos `Usage`=07·EVT1 | ambas | `caller.py:228-232`+loop:247-258 (usage no leída) abierto ESTE ciclo | sí (§2.3, MoR2) | — |
| A4 | T1-CONTRATO + T2-COSTURA | contratos `ThinkingEvent`(07) | base | `caller.py:245` (skip) abierto ESTE ciclo | sí (§2.3, MoR3) | — |
| A5 | T2-COSTURA | costura | base | `caller.py:224-227` abierto ESTE ciclo — **corrige tracker** (§honestidad) | sí (mapeo, con C1/C3) | — |
| A6 | T1-MOTOR | costura señal + 08 | base | `caller.py:188-190` abierto ESTE ciclo | sí (§2.3, MoR4) | eje ejecución |
| A7 | T1-MOTOR | costura/motor (ya fiel) | base | ✅ `caller.py:199-202` re-abierto ESTE ciclo | sí (sin acción) | — |
| A8 | T1-MOTOR | costura/motor + 09 | base | ✅ `caller.py:131-144`+`agent_loop.py:144-146` re-abiertos ESTE ciclo | sí (sin acción) | — |
| B1 | BATTERY resilience + T2-COSTURA | battery + 02·loop | base | tracker-leído (withRetry.ts 1→EOF) + `caller.py:204` (una request) ESTE ciclo | sí (§2.2/2.3, MoR6) | — |
| B2 | BATTERY resilience | battery + 02 | base | tracker-leído | sí (MoR6) | — |
| B3 | BATTERY resilience | battery + 02 | base | tracker-leído | sí (MoR6) | — |
| B4 | BATTERY resilience | battery + 08/05 | base | tracker-leído | sí (§2.2/2.3) | eje ejecución |
| B5 | T1-MOTOR + cabling | motor + 09 + MoR1 | base | tracker-leído | sí (MoR8) | — |
| B6 | BATTERY caching | battery caching | base | tracker-leído | sí (§2.2) | eje persistencia (leve) |
| B7 | T1-MOTOR (=A2) | costura (MoR1) | base | tracker-leído | sí (folds MoR1) | — |
| B8 | T1-MOTOR | costura | base | tracker-leído | sí (param) | — |
| B9 | T1-MOTOR + BATTERY | costura + battery | base | tracker-leído | sí (política cap) | — |
| B10 | T1-MOTOR + T3-INTEGRADOR | costura + integrador | ambas | tracker-leído | sí (OI-M3) | **persist+ejec · id opaco** |
| B11 | T1-MOTOR | costura `output_format` | base | tracker-leído | sí (§2.3, sin MoR) | — |
| B12 | T1-MOTOR | motor | base | tracker-leído (transform_messages) | sí (parcial) | — |
| B13 | T1-MOTOR | motor (ya fiel) | base | ✅ tracker-leído B 1→EOF (transform_messages.py:150-171) | sí (sin acción) | — |
| B14 | T1-MOTOR | motor | base | ✅ tracker-leído B (_iterate_sse) | sí (sin acción) | — |
| B15 | T1-CONTRATO + T1-MOTOR | contratos Usage + motor | base | tracker-leído (=A3) | sí (folds MoR2) | — |
| B16 | T1-MOTOR | motor | base | ✅ tracker-leído B | sí (sin acción) | — |
| B17 | T1-MOTOR + T3-INTEGRADOR | motor + integrador (credencial) | ambas | ✅ tracker-leído B (_to_cc_name) | sí (OI-M2) | — |
| C1 | T1-CONTRATO + T2-COSTURA | contratos `ErrorEvent`(07·D5) | base | `caller.py:236-242` abierto ESTE ciclo | sí (§2.3, MoR5) | — |
| C2 | T2-BASE-MECANISMO + BATTERY compaction | 02·loop + 01·CompactionProvider | base | tracker-leído (overflow.py existe, no cableado) | sí (§2.3, MoR7) | eje persistencia |
| C3 | T2-COSTURA (=A5/C1) | costura | base | `caller.py:227` abierto ESTE ciclo — **corrige tracker** (§honestidad) | sí (folds A5/C1) | — |
| C4 | CLI-ONLY / INTERFAZ | integrador (front/diag) | integrador | tracker-leído (errorUtils.ts 1→EOF→⛔) | sí (OI-M7) | — |
| D1 | T1-MOTOR (superset) | motor | base | tracker-leído (client.ts 1→EOF) | sí (🔀 diseño, no deuda) | — |
| D2 | T2-COSTURA + T3-INTEGRADOR | costura + integrador | ambas | tracker-leído | sí (OI-M2) | — |
| D3 | T3-INTEGRADOR | integrador | integrador | tracker-leído | sí (OI-M8) | eje ejecución (leve) |
| E | CLI-ONLY + T3-INTEGRADOR | integrador (observabilidad) | integrador | tracker-leído (4 archivos 1→EOF→⛔) | sí (OI-M5) | eje persistencia (session-log) |
| F | T3-INTEGRADOR | integrador (front/BFF) | integrador | tracker-leído (10 endpoints 1→EOF→⛔) | sí (OI-M6) | eje persistencia (billing) |
| LAT-MODELS1 | DEUDA-B | §B-orphans (borrar/consumir) | base | ensamblador `factory.py:83` abierto ESTE ciclo (slot muerto) | N/A (DEUDA-B) | — |

### 3.1b §Nota de honestidad (gate auto-adversarial — L11/L10)
- **Corrección A5/C3 (L11 — validar B, no confirmar doc):** el tracker (2ª vuelta) describe un método `_map_stop_reason`
  con `refusal/sensitive → error genérico`. Al abrir `caller.py` **1→246 ESTE ciclo**, ese método **NO existe**: el
  done-handler (:222-233) hace passthrough puro `"tool_calls" if reason=="toolUse" else (reason or "stop")`, **sin rama
  refusal/sensitive**; un `reason="refusal"` sale raw como `stop_reason` en el `DoneEvent`. La clasificación A5/C3 (🟡
  T2-COSTURA, mapeo a extender) **NO cambia**; la **evidencia sí** se corrige y la brecha resulta **mayor** de lo que el
  doc previo implicaba (refusal ni siquiera se mapea a error). Ejemplo exacto del modo de fallo L11: heredar la ✅/🟡 del
  doc sin abrir B.
- **Conteo por FILA, no por el tally del tracker:** reconcilio por **fila feature-by-feature** (34 unidades = 32 filas +
  E + F), objeto correcto del SEPARACION. El tally de estados del **header del tracker** (`✅6·🟡14·🔀3·❌11`) está
  **descalibrado** frente a sus propias tablas (reales: ✅6·🟡13·🔀2·❌10 + C4⛔ + E/F⛔) — imprecisión **pre-existente del
  tracker**, fuera de alcance de re-tally; se nombra, no se hereda. Cada fila queda colocada con independencia de su símbolo.
- **Motor `agentic_models` NO re-leído ESTE ciclo (acotamiento deliberado, PLAN §1.3):** los ✅ B13/B14/B16/B17 y el 🔀 D1
  son **fidelidad del MOTOR-lib** (ya separado), no cabling del base; su destino es "motor (ya fiel)", no una costura que
  este SEPARACION reifique. Evidencia = lectura íntegra de B en el tracker (anthropic.py 806 + transform_messages 190,
  1→EOF). Re-leer el provider de 806 LOC violaría "lecturas acotadas / no leer de más". **NO es apoyo-en-grep**: es el
  destilado de una lectura íntegra previa de una lib que el reparto B no re-homa. Lo que SÍ re-abrí ESTE ciclo es **la
  costura** (`caller.py`/`protocol.py` 1→EOF) y su **cabling en el ensamblador** (`agent_loop.py:235`, `factory.py:83`).

### 3.2 Cinco preguntas de cierre
1. **¿Se leyó ÍNTEGRO `../16-models.md`?** — **Sí**, líneas 1→452 (encabezado, superset, re-visita gate-11/L09,
   mini-ledger de consumidores, ❌ por cableado, cabos, LAT-MODELS1, tabla A/B/C/D/E/F, §Plan MoR1-8, ledger de cierre).
2. **¿Reconcilia el conteo?** — filas feature-by-feature en `../16-models.md` = **32** (A1-A8·B1-B17·C1-C4·D1-D3) +
   **2 bloques agrupados** (E telemetría 4 archivos, F billing 10 endpoints) = **34 unidades**; colocadas = **34**;
   sin colocar = **0**. + **LAT-MODELS1** (costura latente de la re-visita) colocada en DEUDA-B. ✅
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador (sin grep)?** — **Sí, re-abierto en ESTE ciclo:**
   A7 `caller.py:199-202`; A8 `caller.py:131-144`+`agent_loop.py:144-146`; A1 `caller.py:17-30`+`agent_loop.py:227-234`;
   call-site `agent_loop.py:235`; inyección `factory.py:83/85`; LAT-MODELS1 `factory.py:83`. Los ✅ **B13/B14/B16/B17/D1**
   son **lecturas del MOTOR `agentic_models`** (lib ya separada), no cabling del ensamblador del base: su evidencia es la
   **lectura íntegra de B en el tracker** (anthropic.py 806 + transform_messages 190, 1→EOF) — declarado honestamente,
   NO re-leído ESTE ciclo (§honestidad). Los ❌/🟡 se apoyan en el ensamblador abierto ESTE ciclo (thinking/usage/abort/
   error) o en la ausencia probada (overflow/retry no cableados).
4. **¿La cara integrador quedó al MISMO detalle que la base?** — **Sí**: §2.5 desarrolla 8 obligaciones (OI-M1…OI-M8)
   con los 6 campos L05, primero el **contrato base común** (OI-M1 model-caller = must-be universal), luego lo específico
   (OI-M6 billing = agentic_assistant). Ningún finding cerrado con "→ integrador" a secas; los bloques E/F desarrollados,
   no descartados.
5. **¿Doble filo (L10)?** — **Sí**: ningún ❌ disfrazado de 🔀 (los 8 CORE-GAPs se mantienen como brechas reales con
   remediación desarrollada §2.3/MoR). Ninguna deuda inflada: **D1** (multi-provider) es 🔀 por diseño, NO deuda; el
   **superset** de ~30 providers NO se cuenta como brecha; **LAT-MODELS1** + `ModelRequest.thinking_budget` clasificados
   **DEUDA-B interna** (extensión sin contraparte canónica), NO deuda A↔B; **C4/E/F** = capa de interfaz/integrador
   (⛔-con-destino), NO ❌.

### 3.3 VEREDICTO
**✅ NADA PENDIENTE → A1.3 (07·events).**
Los 34 findings + LAT-MODELS1 repartidos con TIER+destino. **8 CORE-GAPs** para DEUDA-A (FIND-MODELS1/2/3/4/9/10/11 +
resilience-block y betas-core); **2 DEUDA-B** (LAT-MODELS1, `thinking_budget` muerto). Costura central
`ModelCallerProtocol` nombrada con productor/consumidor + 3 costuras auxiliares (señal-abort, `with_retry`, auth). **3
batteries** (resilience, caching, compaction-consumidor). **8 obligaciones de integrador** con detalle simétrico. Cabos
con destino explícito: **07·events** (EVT1 usage=A3, D5 error=C1, ThinkingEvent=A4, J3 api_retry) · **08·signals**
(A6/B4 abort/watchdog) · **02·loop** (resilience motor#2 + overflow-routing) · **01·contracts** (`CompactionProvider`
para C2) · **09·tools-infra** (tool-search beta/capability, A8/B5) · **05·execution** (`arm_watchdog` B4) · transversal
**A3.DA** (B10 metadata id-opaco) · **DEUDA-B §B-orphans** (LAT-MODELS1). Ninguno es pendiente de **verificación**.
