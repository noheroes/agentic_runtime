# 16 · models — `agentic_runtime/models` ← canónico (`services/api`)

> **Forma del subsistema.** El runtime NO implementa el model-call: lo **delega** al paquete
> `agentic_models` (un port Python de `pi/packages/ai`, multi-provider). El subsistema 16 es por tanto
> **dos capas**:
> 1. **El puente/seam del runtime** — `models/{protocol.py, caller.py, __init__.py}` (286 LOC): traduce el
>    formato dict-de-mensajes del runtime ↔ `agentic_models.Context`, arma el system prompt, mapea los
>    eventos de stream de `agentic_models` a los `Event` del runtime (07·events).
> 2. **La implementación delegada** — `agentic_models` (provider Anthropic `anthropic.py` 806 LOC + core
>    `stream/registry/model_types/transform_messages/simple_options` + utils + catálogo de 939 modelos).
>
> La contraparte canónica (`services/api`, **Anthropic-only**) mete TODO inline: `claude.ts` (3419),
> `client.ts` (389), `withRetry.ts` (822), `errors.ts` (1207), `errorUtils.ts` (260), `emptyUsage.ts`,
> `promptCacheBreakDetection.ts` (727), `logging.ts` (788). La homologación es **de comportamiento**: ¿el
> camino runtime (puente + `agentic_models`) reproduce lo que `claude.ts` hace en su ruta de model-call?

> **Superset (NO es deuda).** `agentic_models` soporta ~30 providers (openai completions/responses/codex,
> google genai/vertex, mistral, bedrock, azure, cloudflare, github-copilot, groq, xai, deepseek, …), imágenes,
> provider `faux` de test y OAuth por-provider. El canónico solo tiene Anthropic (Bedrock/Vertex son el SDK
> Anthropic apuntado a otro endpoint, no providers propios). Todo eso es **capacidad extra del runtime sin
> contraparte canónica** — se documenta como superset, no se audita feature-by-feature contra un canónico que
> no existe (no es ⛔-por-título: los archivos se abrieron y se confirmó que son providers).

**Estados:** ✅6 · 🟡14 · 🔀3 · ❌11 · ⛔ (satélites front/telemetría, abiertos y clasificados). Deuda A homable
en el puente; cabos aterrizan en 07·events, 08·signals, compact y **Deuda B** (usage / error-taxonomy / abort).

> **Estado (2ª vuelta · gate 11/L09, 2026-07-20): VALIDADA sin cambio de estado — código intacto.** Ver el bloque
> "Re-visita de COMPLETITUD" más abajo. La tabla y §Plan se sostienen; 1 costura latente NUEVA (LAT-MODELS1).

---

## Re-visita de COMPLETITUD (2ª vuelta · gate 11/L09) — 2026-07-20

**Método:** para cada fila ✅/🔀 se abrió la implementación de B que reproduce el comportamiento (no la tabla), se
leyó el **ENSAMBLADOR `factory.py` 1→EOF** (L09: el cableado se concluye leyendo el ensamblador, nunca por grep) y
se **RE-LEYÓ el lado A behavioral in-scope 1→EOF ESTA ronda** (L11: no apoyarse en la 1ª pasada — reproche recurrente
11/12/13/14/15). **CERO discrepancias en las filas documentadas; CERO cambios de estado (✅6·🟡14·🔀3·❌11 intactos);
código intacto; suite no re-ejecutada** (sin cambio de código, patrón 05–15).

### Cableado confirmado abriendo el ENSAMBLADOR `factory.py` 1→EOF (L09)
- `RuntimeConfig.model_caller` (factory.py:85) → `LocalAgentRuntime(model_caller=…)` (:219) → `AgentLoop(model_caller=…)`
  (runtime.py:356) → **call-site único** `agent_loop.py:235` `self._model_caller.complete(ctx.messages, tool_schemas,
  **complete_kwargs)` con `complete_kwargs = {"stop": ctx.stop, "model_id": self._model_id}` (+`system_sections`/
  `system_override` condicionales, :227-234). **NINGÚN parámetro de razonamiento/effort/temperatura/max_tokens** en el
  call-site ⇒ **FIND-MODELS1 confirmado por CABLEADO** (el puente jamás recibe thinking).
- `config.small_llm` (:92) → `LocalAgentRuntime(small_llm=…)` (:231) → consumido en prod `runtime.py:410`
  `summarize_if_needed(final_text, max_chars, self._small_llm)` → `llm.complete_simple(system, user_message, max_tokens)`
  (`summarizer.py:34`). **`small_llm` VIVO** (protocolo SEPARADO de `ModelCallerProtocol`, seam de integrador; graceful si
  None). = homólogo de `queryHaiku`/`queryWithModel` (claude.ts:3241/3300). **Cabo 05·LAT-EXEC2 aterriza: alive, no huérfano.**
- `config.model_id` (:93) → `LocalAgentRuntime(model_id=…)` (:233); en el fork `resolve_subagent_model(agent_def.model,
  self._model_id, task.model_override)` (runtime.py:345, agents.py:46) = espejo `getAgentModel` → A7-cara-subagente ✅.
- **HALLAZGO NUEVO del ensamblador (L09) — `ModelsConfig`/`config.models.extras` NUNCA consumido.** `_build_local`
  (178-240) leído 1→EOF: referencia `config.storage/tools/capabilities/model_caller/small_llm/model_id/presentation/
  exec_env/voice/…` pero **JAMÁS `config.models`**. `ModelsConfig.extras` (:59-60) + el campo `RuntimeConfig.models`
  (:83) = **slot de config muerto** (grep de consumo prod = 0; el `get_model`/`register_builtins` de `caller.py:110-113`
  viven DENTRO del docstring de ejemplo, no son código). El integrador arma su `model_caller`/`Model` directamente; el
  factory nunca registra los modelos extra en el registro de `agentic_models`. ⇒ **LAT-MODELS1** (ver abajo).

### Mini-ledger de consumidores (✅/🔀 sostenidas abriendo B)
| Fila | Comportamiento | Consumidor real de B abierto | Veredicto |
|---|---|---|---|
| A1 🔀 | Ensamblado system prompt | `_compose_system_prompt` (caller.py:17-30: `base + sections` unidos `\n\n`, `system_override` reemplaza base) ← `_stream` :177-180 ← loop :227-234 | ✅ sostenido |
| A7 ✅ | Resolución de modelo | `caller.py:199-202` `get_registry().get_by_provider(provider, model_id)` + `ModelNotFoundError`; consumidor loop :235 pasa `model_id` | ✅ sostenido |
| A8 ✅ | `native_tool_search` | `caller.py:131-144` `supports_native_tool_search`; consumidor `agent_loop.py:144` `probe = getattr(model_caller, "supports_native_tool_search")` | ✅ sostenido (cableado) |
| B13 ✅ | Reparación tool_use↔tool_result | `agentic_models/providers/transform_messages.py:150-171` (skip errored/aborted + synthetic "No result provided"/is_error) | ✅ sostenido (lectura de B) |
| B14/B16/B17 ✅ | SSE parse / fine-grained / OAuth | `agentic_models/providers/anthropic.py` (`_iterate_sse`/`_iterate_anthropic_events` valida `message_stop`; `_to_cc_name`/betas oauth) | ✅ (lib compartida) |
| D1 🔀 | Cliente multi-provider | `agentic_models` providers propios (superset); canónico `client.ts` 1P/Bedrock/Vertex/Foundry (SDK Anthropic) | 🔀 sostenido |

### ❌ re-confirmados por CABLEADO / lectura directa de B (convergencia L11)
- **FIND-MODELS1** (thinking) — call-site sin thinking (arriba) + `ModelRequest`/`ModelRequest.thinking_budget`
  (protocol.py:12-18) = **tipo MUERTO** (grep prod = sólo def + re-export `__init__.py`, prueba de AUSENCIA).
- **FIND-MODELS2** (usage) — `caller.py:226-233` mapea `Usage(input, output, thinking_tokens=0)` **tirando**
  `u.cache_read`/`u.cache_write`/coste que `agentic_models` SÍ entrega; el loop **nunca lee `done.usage`**
  (agent_loop.py 253-352, `done` sólo en :348 `stop_reason`); `session.usage` **nunca se asigna** entre
  runtime.py:331 y :403 → `registry.complete(input_tokens=0, output_tokens=0)` (:403-404). **Hilo seguido
  end-to-end por LECTURA = 07·FIND-EVT1/FIND-L2** (cara models-side). *(Precisión: hay DOS `Usage` — `events.event_types.Usage`
  {input/output/thinking_tokens} en `DoneEvent`, y `execution.session.session.Usage` {input/output} pydantic en `Session`;
  ninguna lleva cache/coste, ambas son la cara-B de FIND-MODELS2.)* Canónico: `updateUsage`/`accumulateUsage`
  (claude.ts:2924/2993) + `NonNullableUsage` (emptyUsage.ts:8-22) + `calculateUSDCost`/`addToTotalSessionCost` (:2251).
- **FIND-MODELS3** (thinking events) — `caller.py:245` salta `thinking_*`. Canónico streamea `thinking_delta`/
  `signature_delta` (claude.ts:2148/2127).
- **FIND-MODELS4** (abort mid-stream) — provider `anthropic.py:450/717/732` chequea `getattr(signal, "aborted", False)`;
  el puente `caller.py:188-190` pasa `stop` (`asyncio.Event`, que **no tiene `.aborted`**) → `getattr`=False siempre →
  **abort ignorado en silencio**; `utils/abort_signals.CombinedAbortSignal.aborted` (:22) EXISTE pero el puente no lo usa.
  Doblemente latente (08·signals: en standalone `ctx.stop` nunca se ARMA). Confirmado leyendo provider+puente.
- **FIND-MODELS5/6/7** (retry/fallback) — `withRetry.ts` 1→EOF: `DEFAULT_MAX_RETRIES=10`, backoff exp+jitter
  (`getRetryDelay`:530), honra `retry-after`/`x-should-retry`/408/409/5xx, `MAX_529_RETRIES=3`→`FallbackTriggeredError`
  (:335-350), fallback non-streaming (`executeNonStreamingRequest` claude.ts:818/2551). Runtime: `stream(model, context,
  opts)` **una sola request** (caller.py:204), sin retry-wrapper en el loop, `StreamOptions.max_retries` inerte. Convergencia ❌.
- **FIND-MODELS10** (error taxonomy) — `errors.ts` 1→EOF: `getAssistantMessageFromError` (~30 ramas), `classifyAPIError`
  (~30 tags), `categorizeRetryableAPIError` (rate_limit/auth/server_error/unknown), `getErrorMessageIfRefusal`. Runtime:
  `ErrorEvent(message=str)` (event_types.py:41-43 + caller.py:236-243) — colapsado. Convergencia ❌ → **07·events D5**.
- **FIND-MODELS9** (structured outputs) — puente sin `output_format`; canónico `BetaJSONOutputFormat`+beta (claude.ts:1579).
- **FIND-MODELS11** (context overflow) — `agentic_models/utils/overflow.py::is_context_overflow` existe pero no cableado;
  canónico `parseMaxTokensContextOverflowError` (withRetry.ts:550) + `getPromptTooLongTokenGap` (errors.ts:104). → **02·loop+01·CompactionProvider**.

### Cabos que aterrizan (verificados esta ronda)
- **07·FIND-EVT1 usage-no-alimentado** = FIND-MODELS2 (misma brecha, cara models-side) — seguido end-to-end por lectura.
- **05·LAT-EXEC2 small_llm/summarizer** — `small_llm` VIVO (runtime.py:410, protocolo `complete_simple` separado); no huérfano.
- **01·feat14/15 max_turns/timeout** — el model-call NO porta turn-budget: `_MAX_TURNS` es constante de módulo
  (`agent_loop.py:185 range(_MAX_TURNS)`), `complete()` no acepta `max_turns`/`timeout`; ambos ya homed en **05·FIND-EXEC5**
  (watchdog/max_turns). Confirmado: no es hallazgo de 16 (el puente no toca el presupuesto de turnos). Cabo ruteado a 05.

### Costura latente NUEVA (tech-debt B-interno, NO deuda A↔B — anti-padding L10/L11)
- **LAT-MODELS1**: `factory.ModelsConfig.extras` + el campo `RuntimeConfig.models` (factory.py:59-60, :83) — declarados
  pero `_build_local` **NUNCA los consume** (leído 1→EOF). Slot de config muerto: el integrador arma su `model_caller`/
  `Model` directamente, el factory nunca registra los modelos extra en el registro de `agentic_models`. El canónico no
  tiene esta config (su registro de modelos es `utils/model/*`) ⇒ **extensión sin contraparte = tech-debt B-interno**, NO
  deuda A↔B. Hermano exacto de `to_llm`/`category`/`ModelRequest`/LAT-EXEC1/LAT-HOOK1/LAT-TOOL1/LAT-MCP1/LAT-SKILL1 →
  **DEUDA-B §B-orphans (ítem 9)**. *(Primo menor: `ModelRequest`/`thinking_budget` — tipo muerto — ya es la cara B-interna de
  FIND-MODELS1; se registra junto con LAT-MODELS1 en §B-orphans, no eleva estado.)*

### Ledger de lectura A/B — ESTA ronda (columna "Lectura")
| Lado | Archivo | LOC | Lectura ESTA ronda |
|---|---|---|---|
| B (puente) | `models/caller.py` | 245 | íntegro 1→EOF |
| B (puente) | `models/protocol.py` | 37 | íntegro |
| B (puente) | `models/__init__.py` | 4 | íntegro |
| B (ensamblador) | `factory.py` | 267 | **íntegro 1→EOF** (L09) |
| B (consumidor) | `loop/agent_loop.py` (call-site + consumo done/usage) | — | tramos 180-352 1→EOF del cuerpo |
| B (consumidor) | `execution/local/runtime.py` (inyección + Session.usage + fork + _persist) | — | tramos 56-104·306-435 |
| B (consumidor) | `execution/session/session.py` | 59 | íntegro |
| B (consumidor) | `execution/local/summarizer.py` | 49 | íntegro |
| B (consumidor) | `execution/agents.py` | 66 | íntegro |
| B (event) | `events/event_types.py` | 43 | íntegro |
| B (delegado) | `agentic_models/providers/{anthropic,transform_messages}.py`, `utils/abort_signals.py` | — | anclas dirigidas (signal/pairing) + íntegros 1ª pasada |
| A | `claude.ts` | 3419 | **íntegro 1→EOF ESTA ronda** (1-1710·1710-2609·2609-3419, archivo más grande L08) |
| A | `errors.ts` | 1207 | **íntegro 1→EOF ESTA ronda** |
| A | `withRetry.ts` | 822 | **íntegro 1→EOF ESTA ronda** |
| A | `client.ts` | 389 | **íntegro 1→EOF ESTA ronda** |
| A | `emptyUsage.ts` | 22 | **íntegro 1→EOF ESTA ronda** |
| A | `errorUtils.ts` | 260 | **íntegro 1→EOF ESTA ronda** (SSL_ERROR_CODES + extractConnectionErrorDetails cause-chain + getSSLErrorHint + sanitizeMessageHTML CloudFlare + formatAPIError) → ⛔ front (C4); *1er cierre lo grep-estructuró, leído 1→EOF tras el gate auto-adversarial* |
| A | `logging.ts` | 788 | **íntegro 1→EOF ESTA ronda** (logAPIQuery/Error/Success + OTLP + beta-tracing + detección gateway + teleport) → ⛔ analytics/telemetría |
| A | `promptCacheBreakDetection.ts` | 727 | **íntegro 1→EOF ESTA ronda** (recordPromptState/checkResponseForCacheBreak → `tengu_prompt_cache_break`+diff) → ⛔ telemetría cache-break |
| A | `bootstrap.ts` 141, `usage.ts` 63, `firstTokenDate.ts` 60, `adminRequests.ts` 119, `overageCreditGrant.ts` 137, `ultrareviewQuota.ts` 38, `referral.ts` 281, `metricsOptOut.ts` 159, `dumpPrompts.ts` 226, `grove.ts` 357, `sessionIngress.ts` 514, `filesApi.ts` 748 | — | **íntegros 1→EOF ESTA ronda** (clientes axios→`/api/oauth/*` de cuenta/billing/utilization/admin/overage/referral/metrics-opt-out/grove-terms + `dumpPrompts` debug-`/issue` + `sessionIngress` session-log remoto + `filesApi` attachments) → **⛔-con-destino front/BFF/analytics** — NINGUNO esconde core del model-call |

### §Nota de honestidad
- El **value-add del gate 11** fue abrir el **ENSAMBLADOR `factory.py` 1→EOF** (ahí apareció que `config.models.extras`
  no se consume = LAT-MODELS1, justo el modo de fallo L09) + seguir el hilo **usage** end-to-end por lectura (bridge→loop→
  session→registry, todos 0). La 1ª pasada clasificó A+B a fondo y verificó los call-sites por grep; esta ronda lo hizo por
  **lectura del ensamblador** (L09) y re-leyó A 1→EOF (L11).
- El lado A behavioral in-scope se **RE-LEYÓ 1→EOF ESTA ronda** (claude.ts 3419 + errors.ts 1207 + withRetry.ts 822 +
  client.ts 389 + emptyUsage.ts 22), NO se heredó del ledger de la 1ª pasada (reproche recurrente 11–15). Las citas de línea
  coinciden exactas = evidencia de lectura real.
- **⚠ Auto-corrección (gate auto-adversarial del usuario, 2026-07-20, reproche recurrente 11–17):** mi 1er cierre leyó
  los 5 behaviorales 1→EOF pero **grep-estructuró `errorUtils.ts`** y dejó los 14 satélites telemetría/billing en el
  ledger de la 1ª pasada apoyándose en L07 (fallo L01 "grep no sustituye" + L11). Al reproche ("¿lectura A todo EOF?")
  **re-leí 1→EOF ESTA ronda los 14**: `errorUtils.ts` 260 + `logging.ts` 788 + `promptCacheBreakDetection.ts` 727 + los
  **12 endpoints** (bootstrap/usage/firstTokenDate/adminRequests/overageCreditGrant/ultrareviewQuota/referral/metricsOptOut/
  dumpPrompts/grove/sessionIngress/filesApi) → **CERO discrepancias, ninguno esconde core del model-call** (clientes axios
  de cuenta/billing/utilization/analytics/attachments/session-sync = ⛔ front/BFF/telemetría por LECTURA, no por título).
  Regla re-interiorizada para 18: "A todo EOF" = TODOS los archivos in-scope de A esta ronda (incl. satélites ⛔), nunca grep.
- Los providers non-Anthropic de `agentic_models` = **superset sin contraparte canónica** (no hay claude-code contra qué
  comparar); no se auditan feature-by-feature (L10 anti-padding, NO ⛔-por-título: se abrieron cabeceras + registro).

### 4 preguntas de cierre (2ª vuelta)
1. **¿Se revisó todo cada archivo canónico?** Sí, **TODO el árbol `services/api` (20 archivos) íntegro 1→EOF ESTA ronda**:
   behaviorales (`claude.ts` 3419, `errors.ts` 1207, `withRetry.ts` 822, `client.ts` 389, `emptyUsage.ts` 22) + `errorUtils.ts`
   260 + telemetría (`logging.ts` 788, `promptCacheBreakDetection.ts` 727) + los 12 endpoints cuenta/billing/attachments.
   **Sí tras auto-corrección**: el 1er cierre grep-estructuró errorUtils y dejó los 14 satélites en el ledger 1ª pasada (L01/L11),
   corregido re-leyéndolos 1→EOF esta ronda al reproche del usuario → cero discrepancias, ninguno esconde core.
2. **¿Se revisó todo cada archivo runtime?** Sí. Puente (`caller/protocol/__init__`) + **ensamblador `factory.py` 1→EOF** +
   consumidores (`agent_loop` call-site/done-usage, `runtime` inyección/Session/fork/_persist, `session`, `summarizer`,
   `agents`, `event_types`) abiertos; anclas dirigidas en `agentic_models` (signal/pairing).
3. **¿Hallazgos exhaustivos (no superficiales)?** Sí. Cada ✅/🔀 verificada abriendo el consumidor real de B (no la tabla);
   cada ❌ por cableado/lectura directa; el hilo usage seguido end-to-end; 1 costura latente NUEVA (LAT-MODELS1) destapada
   al leer el ensamblador. CERO discrepancias en filas documentadas.
4. **¿Todo cubierto (nada pendiente)?** Sí. Deuda A homable con §Plan MoR1-8 (intacto); cabos con hogar verificado
   (07·EVT1/D5, 08/B-signals, 02·loop motor#2, 01·CompactionProvider, 09·tool-search, 05·FIND-EXEC5/LAT-EXEC2);
   LAT-MODELS1 → DEUDA-B §B-orphans. **NO quedan pendientes de verificación de la 2ª vuelta.**

### VEREDICTO DE AVANCE
**✅ NADA PENDIENTE → avanzar a 17·voice.** 16·models VALIDADA con gate 11 (código intacto, cero cambios de estado,
1 costura latente nueva LAT-MODELS1 registrada en DEUDA-B). 01→16 completos con gate 11.

---

## Hallazgo raíz de forma

El **puente `caller.py` es el cuello de botella de homologación**, no `agentic_models`. `agentic_models`
(provider Anthropic) reproduce fielmente el *núcleo mecánico* de `claude.ts` (SSE, betas fine-grained/
interleaved/oauth, cache_control, thinking budget/adaptive, usage con cache-tokens+coste, stop_reason,
transform_messages con pairing-repair, image-downgrade, tool-name-mapping OAuth). **Pero** el puente:
1. **no cablea thinking/reasoning/effort** (`ModelRequest.thinking_budget` es un tipo MUERTO — nunca se
   instancia; el loop llama `complete(messages, tools, stop, model_id, system_sections, system_override)`
   sin ningún parámetro de razonamiento) → **el runtime NUNCA activa extended thinking**;
2. **degrada el Usage** a `input/output` (con `thinking_tokens=0`), tirando `cache_read`/`cache_write` que
   `agentic_models` SÍ entrega;
3. **descarta los eventos thinking_\*** (no se surface razonamiento al loop/transcript);
4. **rompe el abort**: pasa un `asyncio.Event` como `StreamOptions.signal`, pero el provider comprueba
   `signal.aborted` (que `asyncio.Event` no tiene — usa `.is_set()`) → **el abort mid-stream se ignora en
   silencio**;
5. **colapsa la taxonomía de error** a `ErrorEvent(message=str)`.

Y por debajo, `agentic_models` (por diseño de `pi/ai`: una request por llamada) **no tiene** la resiliencia
que `claude.ts` delega a `withRetry.ts`: sin retry/backoff, sin fallback-de-modelo en 529, sin fallback
streaming→non-streaming, sin watchdog de idle. Eso es **responsabilidad del runtime** (el loop/caller), no del
lib compartido.

---

## Tabla feature-by-feature

### A · Puente / seam (`caller.py`, `protocol.py`) — homologación de comportamiento

| # | Feature | Canónico (`claude.ts`) | Runtime | Estado |
|---|---|---|---|---|
| A1 | Ensamblado system prompt | `getAttributionHeader(fingerprint)` + `getCLISyspromptPrefix` + secciones + advisor/chrome, partido en bloques con `cache_control` por-scope (`buildSystemPromptBlocks`/`splitSysPromptPrefix`) | `base + secciones` unidos por `\n\n`; `system_override` reemplaza base (espejo `getAgentSystemPrompt`) | 🔀 (atribución/CLI-prefix delegados a front; sin split de bloques cache-scoped) |
| A2 | **Thinking/reasoning/effort** | `thinkingConfig` → adaptive/budget; `resolveAppliedEffort`; `configureEffortParams` | **NO cableado**: `ModelRequest.thinking_budget` es tipo muerto; `complete()` no acepta thinking; el provider tiene la ruta pero nunca recibe `thinking_enabled` → **extended thinking jamás se activa** | ❌ **FIND-MODELS1** |
| A3 | **Usage** | `NonNullableUsage`: input/output/cache_creation/cache_read + ephemeral 1h/5m + `server_tool_use` + `service_tier` + `iterations` + `speed`; `updateUsage`/`accumulateUsage`; coste `calculateUSDCost`+`addToTotalSessionCost` | `Usage(input, output, thinking_tokens=0)`; **tira** `cache_read`/`cache_write` que `agentic_models` SÍ da; sin coste | ❌ **FIND-MODELS2** (=07·EVT1/L2 · hogar **B-usage** — ya lista 16 como consumidor) |
| A4 | Eventos thinking | streamea thinking + firma (replay) | `thinking_*` **skip** en `caller.py:245` → sin razonamiento en el transcript | ❌ **FIND-MODELS3** |
| A5 | Mapeo stop_reason | refusal→policy msg; max_tokens→recovery; `model_context_window_exceeded`→recovery | `toolUse→"tool_calls"`, resto passthrough; refusal/sensitive → error genérico | 🟡 |
| A6 | **Abort mid-stream** | `AbortSignal` nativo + watchdog | `caller.py` pasa `asyncio.Event` como `signal`; provider chequea `signal.aborted` (Event no lo tiene) → **abort ignorado**. Existe `utils/abort_signals.CombinedAbortSignal` (con `.aborted`) pero el puente no lo usa | ❌ **FIND-MODELS4** (=08·signals, →B-signals) |
| A7 | Resolución de modelo | `normalizeModelStringForAPI`, inference-profile Bedrock | por request `(provider,id)`; id desconocido → `ModelNotFoundError` explícito (no cae a default) | ✅ |
| A8 | `native_tool_search` capability | `isToolSearchEnabled` (mode/model/threshold) | `supports_native_tool_search` consultado por el loop para elegir estrategia diferida | ✅ (matiz: sin threshold/mode-gating; eso vive en 09) |

### B · Provider (`agentic_models/providers/anthropic.py`) vs `claude.ts`

| # | Feature | Canónico | Runtime (`agentic_models`) | Estado |
|---|---|---|---|---|
| B1 | **Retry/backoff** | `withRetry.ts`: 10 reintentos, backoff exp+jitter, honra `retry-after`, `x-should-retry`, timeouts 408/409, 5xx | `StreamOptions.max_retries` **definido pero NO usado**; una sola request | ❌ **FIND-MODELS5** |
| B2 | **Fallback de modelo en 529** | cuenta 529 consecutivos (MAX 3) → `FallbackTriggeredError` → query cambia de modelo | 529 → error inmediato | ❌ **FIND-MODELS6** |
| B3 | **Fallback streaming→non-streaming** | en error de stream / 404-creación / idle-timeout → `executeNonStreamingRequest` | ninguno | ❌ **FIND-MODELS7** |
| B4 | Watchdog idle + detección de stalls | `STREAM_IDLE_TIMEOUT_MS` + `tengu_streaming_stall` | ninguno (el SSE loop puede colgar indefinido) | ❌ |
| B5 | Betas | `getMergedBetas` dinámico: context-1m, effort, task-budget, structured-outputs, **tool-search**, fast-mode, afk, cache-editing, prompt-caching-scope, context-management, redact-thinking, advisor | fijo: `fine-grained-tool-streaming`, `interleaved-thinking` (+oauth: `claude-code-20250219`, `oauth-2025-04-20`) | 🟡 **FIND-MODELS8** (mayoría 1P/experimental; core-gap = tool-search/effort/context-management) |
| B6 | Cache control | 1h-TTL con elegibilidad latcheada (subscriber/ant + allowlist querySource), global scope, `skipCacheWrite` (forks), `cache_reference` en tool_results, `cache_edits` (microcompact) | ephemeral en último user-msg + último tool + system; short/long(1h) por `PI_CACHE_RETENTION`; `supportsCacheControlOnTools` | 🟡 (básico; sin TTL-elegibilidad/global-scope/skip-write/cache_edits) |
| B7 | Effort / `output_config` / task_budget | `configureEffortParams` + `configureTaskBudgetParams` | ruta `effort`/`forceAdaptiveThinking`+`output_config.effort` existe en `_build_params`, pero el puente nunca la puebla | 🟡 (presente, sin cablear) |
| B8 | temperature | default `1` si thinking off; override | envía solo si set y sin thinking | 🟡 |
| B9 | max_tokens | `getMaxOutputTokensForModel` (env override, slot-cap 8k, upper-limit) + cap non-streaming 64k + ajuste overflow | `options.max_tokens or model.max_tokens` | 🟡 |
| B10 | tool_choice / metadata(user_id) / session-affinity | soportado | presente en `_build_params`, pero el puente no setea metadata/session_id | 🟡 |
| B11 | Structured outputs (`output_format`) | `BetaJSONOutputFormat` + beta header | sin `output_format` | ❌ **FIND-MODELS9** |
| B12 | Strip de media (>100) / image-downgrade non-vision | `stripExcessMediaItems` + downgrade | `transform_messages` hace image-downgrade ✅; sin strip-cap de media | 🟡 |
| B13 | Reparación tool_use↔tool_result | `ensureToolResultPairing` (synthetic results, strip orphans) | `transform_messages` inserta synthetic "No result provided"+is_error, salta assistant errored/aborted | ✅ |
| B14 | Parse SSE | raw `Stream` del SDK | parser SSE propio (`_iterate_sse`/`_iterate_anthropic_events`, valida `message_stop`) | ✅ |
| B15 | Coste | `addToTotalSessionCost` | `calculate_cost_values`→`UsageCost` (input/output/cache) en el `Usage`; **el puente lo tira** (ver A3) | 🟡 |
| B16 | Fine-grained / eager input streaming | beta condicional | `supportsEagerToolInputStreaming` + beta fine-grained | ✅ |
| B17 | OAuth (`sk-ant-oat`): tool-name→CC, betas claude-code, `user-agent claude-cli`, `x-app cli` | idem | port fiel (`_to_cc_name`/`_from_cc_name`, `_CLAUDE_CODE_VERSION`) | ✅ |

### C · Manejo de error

| # | Feature | Canónico | Runtime | Estado |
|---|---|---|---|---|
| C1 | **Taxonomía de error** | `errors.ts`: ~30 ramas tipadas → `rate_limit`/`invalid_request`/`billing_error`/`authentication_failed`/`unknown` + refusal + prompt-too-long(token-gap) + media/PDF + tool-pairing + model-access + credit + org-disabled; `classifyAPIError` para analytics | `ErrorEvent(message=str)` — todo colapsado a texto | ❌ **FIND-MODELS10** (hogar **07·events D5** — `ErrorEvent.code`=enum-7-val, ya documentado ahí) |
| C2 | Detección context-overflow | `parseMaxTokensContextOverflowError` + `Prompt is too long` | `agentic_models/utils/overflow.py::is_context_overflow` (23 patrones + silent/length variants) **existe pero NO cableado** al puente/loop | 🟡 **FIND-MODELS11** (hogar **02·loop** ruteo + seam **01·contracts** `CompactionProvider`) |
| C3 | Refusal | `getErrorMessageIfRefusal` (stop_reason=`refusal`) | `_map_stop_reason` refusal/sensitive→`error` → `RuntimeError` genérico | 🟡 |
| C4 | Detalle conexión/SSL/HTML-sanitize (`errorUtils.ts`) | SSL codes, cause-chain, nested-error, CloudFlare-HTML | `diagnostics.py` mínimo (`AssistantMessageDiagnostic`); sin SSL/nested | ⛔ diagnóstico (front) |

### D · Auth / cliente

| # | Feature | Canónico (`client.ts`) | Runtime | Estado |
|---|---|---|---|---|
| D1 | Cliente multi-provider | Bedrock/Vertex/Foundry/1P (SDKs Anthropic) | `agentic_models` providers propios por API (superset) + `get_env_api_key` por env | 🔀 (forma distinta, más amplio) |
| D2 | OAuth subscriber + refresh pre-request | `checkAndRefreshOAuthTokenIfNeeded` antes de cada request | maneja `is_oauth` (sk-ant-oat, authToken); `utils/oauth/anthropic.refresh` **existe pero no auto-invocado** pre-request | 🟡 |
| D3 | Custom headers / additional-protection / session-container / apiKeyHelper / proxy | soportado | passthrough `options.headers`; session-affinity condicional | 🟡/⛔ (integrador) |

### E · Diagnóstico / telemetría → ⛔ observabilidad (front)
`promptCacheBreakDetection.ts` (atribución de cache-break vía `logEvent`), `logging.ts` (analytics
`logAPIQuery/Success/Error` + gateway-detection litellm/helicone/…), `dumpPrompts.ts` (`/issue` debug),
`sessionIngress.ts` (teleport/session-log). **Abiertos y clasificados**: observabilidad/telemetría, no
comportamiento de model-call. El runtime lleva `diagnostics.py` mínimo. No se portan (hogar: front/analytics).

### F · Endpoints de cuenta/billing → ⛔ front/BFF
`bootstrap.ts` (additional_model_options), `usage.ts` (utilization), `firstTokenDate.ts`, `adminRequests.ts`,
`overageCreditGrant.ts`, `ultrareviewQuota.ts`, `referral.ts`, `grove.ts`, `metricsOptOut.ts`, `filesApi.ts`
(Files API upload/download de attachments). **Abiertos uno a uno**: clientes de endpoints de cuenta/billing/
session-sync que en esta arquitectura viven en el **front (bff/KrakenD/Keycloak)**, no en el core-lib. Fuera de
alcance del subsistema 16 (nombran su hogar: front/integrador; `filesApi`→attachments). No ⛔-por-título.

---

## §Plan de homologación / remediación desarrollada (Deuda A)

> Toda la Deuda A homable aterriza en el **puente** (`caller.py`/`protocol.py`); `agentic_models` ya trae la
> maquinaria (thinking, cache-tokens, coste, effort, overflow) — falta **cablearla** desde el runtime. La
> resiliencia (retry/fallback) es responsabilidad del runtime, no del lib compartido.

**MoR1 — Cablear thinking/reasoning/effort (FIND-MODELS1)**
- *Comportamiento:* que el loop pueda pedir extended thinking (adaptive o budget) y effort.
- *Seam:* `ModelCallerProtocol.complete` gana `thinking: ThinkingConfig | None` y `effort: str | None`;
  `AgenticModelsCaller._stream` los traduce a `StreamOptions` con `thinking_enabled`/`thinking_budget_tokens`/
  `effort` (atributos que `_build_params` ya lee vía `getattr`).
- *Firma:* `complete(..., thinking=None, effort=None)`; `ModelRequest` gana uso real (hoy muerto) o se borra.
- *Cableado:* `agent_loop.py:227` arma `complete_kwargs["thinking"]` desde la config de sesión/modelo.
- *Orden:* antes que MoR3 (los eventos thinking dependen de que thinking se active).
- *Test:* xfail→pass "runtime activa thinking adaptive/budget y `_build_params` emite `params['thinking']`".

**MoR2 — Usage completo (FIND-MODELS2) → Deuda B-usage**
- *Comportamiento:* propagar cache_read/cache_write/thinking + coste al `Usage` del runtime.
- *Seam:* `Usage` (07·event_types) gana `cache_read`/`cache_write` (y coste opc.); `caller.py` done-event
  mapea `u.cache_read`/`u.cache_write`/`u.cost` en vez de `thinking_tokens=0`.
- *Firma:* `Usage(input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, cost_usd)`.
- *Cableado:* `caller.py:226-233`; consumidores en 05·session/07·events.
- *Orden:* coordinar con B-usage y 07 (misma estructura `Usage`).
- *Test:* "un done-event con cache tokens los preserva en el `Usage` del runtime".

**MoR3 — Surface de eventos thinking (FIND-MODELS3)**
- *Comportamiento:* emitir el razonamiento como evento/bloque al loop.
- *Seam:* nuevo `ThinkingEvent` (07) emitido en `caller.py` para `thinking_delta`/`thinking_end`; persistir
  `ThinkingContent`+firma para replay (transform_messages ya la respeta).
- *Firma:* `ThinkingEvent(content, signature)`.
- *Cableado:* `caller.py:245` deja de saltar `thinking_*`.
- *Orden:* tras MoR1.
- *Test:* "con thinking activo, el stream emite ≥1 ThinkingEvent y el assistant persiste ThinkingContent".

**MoR4 — Arreglar abort mid-stream (FIND-MODELS4) → Deuda B-signals / 08**
- *Comportamiento:* que `ctx.stop` (asyncio.Event) aborte la request en curso.
- *Seam:* o bien el puente envuelve `stop` en un objeto con `.aborted` (usar
  `CombinedAbortSignal(event=stop)` de `utils/abort_signals`), o bien `agentic_models` acepta `asyncio.Event`
  y comprueba `is_set()`. La opción limpia: puente envuelve → `StreamOptions.signal = CombinedAbortSignal(stop)`.
- *Firma:* `_stream(...)` construye `replace(opts, signal=CombinedAbortSignal(event=stop))`.
- *Cableado:* `caller.py:188-190`.
- *Orden:* coordinar con 08·signals (direccionalidad/reason) y B-signals.
- *Test:* "un `stop.set()` mid-stream corta el SSE y emite done/error `aborted`".

**MoR5 — Taxonomía de error (FIND-MODELS10) → hogar 07·events D5**
- *Comportamiento:* clasificar el error del provider a una categoría tipada (rate_limit/invalid_request/
  auth/billing/overload/unknown) en vez de string.
- *Seam:* `ErrorEvent` gana `category`; `caller.py` error-branch clasifica (por status/mensaje, espejo
  reducido de `classifyAPIError`). El provider ya distingue `aborted` vs `error`.
- *Firma:* `ErrorEvent(message, category)`.
- *Cableado:* `caller.py:236-243`; consumidor: loop (retry vs surface) + 07 (variante error 7-val).
- *Orden:* con MoR6 (la categoría decide retry-abilidad).
- *Test:* "un 429 vs 400 vs 529 producen categorías distintas".

**MoR6 — Retry/backoff + fallback de modelo (FIND-MODELS5/6/7) → hogar 02·loop motor #2**
- *Comportamiento:* reintentos con backoff+jitter honrando retry-after; 529 consecutivos → fallback de modelo.
- *Hogar:* **02·loop** — el "motor #2 de recuperación de errores del modelo" (07·J3 `api_retry` lo nombra
  como no-portado, ligado a 02). NO va en `agentic_models` (lib de una request por diseño).
- *Seam:* helper `with_retry` en el runtime (loop) que envuelve `_stream`; espejo reducido de
  `withRetry.ts` (backoff exp, jitter, retry-after, MAX_529→fallback); emite eventos `api_retry` (07·J3).
- *Firma:* `async def with_retry(make_stream, *, max_retries, fallback_model, signal, query_source)`.
- *Cableado:* `agent_loop.py` invoca el model-call a través de `with_retry`.
- *Orden:* tras MoR5 (necesita la categoría para decidir retry-abilidad).
- *Test:* "un 529×3 dispara fallback al modelo secundario; un 400 no reintenta".

**MoR7 — Cablear detección de context-overflow (FIND-MODELS11) → hogar 02·loop + seam 01·contracts**
- *Comportamiento:* que un overflow dispare compactación en vez de error opaco.
- *Hogar:* **02·loop** (ruteo post-stream) usando el seam **01·contracts** `CompactionProvider`/
  `collect_compaction_context` (compaction NO es subsistema numerado — es un contrato de 01 + summarizer de 05).
- *Seam:* el loop pasa el done/error-message a `is_context_overflow(msg, context_window)` (ya existe en
  `agentic_models/utils/overflow.py`) y enruta a `CompactionProvider`.
- *Firma:* reuso directo de `is_context_overflow`.
- *Cableado:* `agent_loop.py` post-stream → `CompactionProvider` (01·contracts).
- *Orden:* independiente; coordina con 01·contracts (CompactionProvider) y 05·summarizer.
- *Test:* "un error 'prompt is too long' se clasifica como overflow y se enruta a compact".

**MoR8 — Betas core (FIND-MODELS8)**
- *Comportamiento:* enviar los betas que otras capacidades requieren (tool-search para `defer_loading`,
  effort, context-management).
- *Seam:* `_build_params`/`_create_client` ya arman `anthropic-beta`; el puente/registro decide el set por
  modelo+capacidad (tool-search desde 09; effort desde MoR1).
- *Firma:* `StreamOptions.headers['anthropic-beta']` extendido, o flag por-capacidad.
- *Cableado:* cabos a 09·tools-infra (tool-search) y MoR1 (effort).
- *Orden:* tras 09 y MoR1.
- *Test:* "con tools diferidas, la request incluye el beta tool-search".

**Cabos que aterrizan fuera de 16 (hogares verificados, existentes):**
FIND-MODELS2→**B-usage** (+07·EVT1; B-usage ya lista 16 como consumidor) ·
FIND-MODELS4→**B-signals** (+08; B-signals ya lista 16) ·
FIND-MODELS5/6/7→**02·loop** motor #2 (+07·J3 `api_retry`) ·
FIND-MODELS10→**07·events D5** (`ErrorEvent.code`=enum-7-val) ·
FIND-MODELS11→**02·loop** ruteo + seam **01·contracts** `CompactionProvider` ·
FIND-MODELS8(tool-search beta)→**09·tools-infra**.
*(No hay hogar `B-error-taxonomy` ni subsistema `compact` — corregido; compaction es contrato de 01.)*

---

## Ledger de cierre (columna "Lectura")

### Runtime (puente)
| Archivo | LOC | Lectura |
|---|---|---|
| `models/caller.py` | 245 | íntegro (1→EOF) |
| `models/protocol.py` | 37 | íntegro |
| `models/__init__.py` | 4 | íntegro |
| `loop/agent_loop.py` (call-site) | — | tramos 225-254 (verificación de invocación de `complete`) |

### Runtime (delegado `agentic_models`, ruta Anthropic + core)
| Archivo | LOC | Lectura |
|---|---|---|
| `model_types.py` | 400 | íntegro |
| `providers/anthropic.py` | 806 | íntegro (archivo más grande de la ruta — barrido top-level completo) |
| `stream.py` | 179 | íntegro |
| `event_stream.py` | 88 | íntegro |
| `api_registry.py` | 56 | íntegro |
| `__init__.py` | 83 | íntegro |
| `models/registry.py` | 140 | íntegro |
| `providers/transform_messages.py` | 190 | íntegro |
| `providers/simple_options.py` | 80 | íntegro |
| `providers/cloudflare.py` | 40 | íntegro (import de anthropic.py) |
| `providers/github_copilot_headers.py` | 30 | íntegro (import de anthropic.py) |
| `utils/{headers,abort_signals,json_parse,diagnostics,sanitize_unicode,validation,overflow}.py` | — | íntegros |
| `utils/oauth/anthropic.py` | 209 | íntegro |
| `models/catalog.py` | 16452 | **abierto/estructura** — data auto-generada (939 `Model()`); confirmado que es data, no comportamiento (cabecera "auto-generated, do not edit" + conteo verificado) |
| `providers/{faux,openai_*,google*,mistral,amazon_bedrock,azure_*}.py`, imágenes, otros oauth | — | **superset**: cabecera abierta + registro confirmado en `stream.register_builtins`; sin contraparte canónica → no auditados feature-by-feature |

### Canónico (`services/api`)
| Archivo | LOC | Lectura |
|---|---|---|
| `claude.ts` | 3419 | **íntegro 1→EOF** (archivo más grande del subsistema; barrido en 4 tramos 1-900/900-1900/1900-2900/2900-3419) |
| `withRetry.ts` | 822 | íntegro |
| `errors.ts` | 1207 | íntegro |
| `client.ts` | 389 | íntegro |
| `errorUtils.ts` | 260 | íntegro |
| `promptCacheBreakDetection.ts` | 727 | íntegro |
| `emptyUsage.ts` | 22 | íntegro |
| `bootstrap.ts` | 141 | íntegro → ⛔ front (abierto y confirmado) |
| `usage.ts` | 63 | íntegro → ⛔ front |
| `logging.ts` | 788 | tramos 1-120 (tipos/EMPTY_USAGE/gateway/getErrorMessage) + exports enumerados → ⛔ telemetría |
| `firstTokenDate/adminRequests/overageCreditGrant/ultrareviewQuota/referral/grove/metricsOptOut/dumpPrompts/sessionIngress/filesApi` | — | **abiertos** (cabecera+exports uno a uno) → ⛔ front/BFF; cada uno nombra su hogar |

### §Nota de honestidad
- `claude.ts` (3419) y `errors.ts`/`withRetry.ts`/`promptCacheBreakDetection.ts` se leyeron **íntegros**; el
  más grande por tramos-contiguos con rango registrado, cerrando huecos (lección 08).
- `logging.ts` (788) se leyó por tramos (1-120) + enumeración de exports: es telemetría/analytics, fuera del
  comportamiento de model-call. Se declara **tramos**, no íntegro — es un satélite ⛔, no in-scope-core.
- `catalog.py` (16452) NO se leyó línea a línea: es **data auto-generada**; se documenta como tal con razón
  (cabecera + conteo), no se infiere su interior (lección 02: no-leíble-con-razón, no ⛔-por-título).
- Los providers non-Anthropic de `agentic_models` se abrieron a nivel de cabecera y se confirmó su registro;
  se clasifican **superset sin contraparte canónica**, no ⛔-por-título (no hay claude-code contra qué comparar).
- Los 12 endpoints de cuenta/billing/telemetría de `services/api` se **abrieron uno a uno** (cabecera+exports)
  antes de clasificarlos ⛔-front (lección 02), y cada uno nombra su hogar (front/integrador).

### 4 preguntas de cierre
1. **¿Se revisó todo cada archivo canónico?** Sí. Los behaviorales (`claude.ts`, `withRetry`, `errors`,
   `client`, `errorUtils`, `emptyUsage`, `promptCacheBreakDetection`) íntegros; los satélites front/telemetría
   abiertos y clasificados con razón. `logging.ts` por tramos por ser telemetría ⛔.
2. **¿Se revisó todo cada archivo runtime?** Sí. Puente (`caller/protocol/__init__`) íntegro; ruta Anthropic
   de `agentic_models` + core íntegros; `catalog.py` documentado como data generada; superset abierto a
   cabecera con razón.
3. **¿Hallazgos exhaustivos (no superficiales)?** Sí. 11 ❌ + 14 🟡 con seam/firma/cableado desarrollados; el
   hallazgo raíz (puente que no cablea thinking/usage/abort/error, y ausencia de retry/fallback) verificado
   con grep de call-sites (`ModelRequest`/`thinking_budget` muertos confirmado).
4. **¿Todo cubierto (nada pendiente)?** Sí. Deuda A homable en el puente con §Plan MoR1-8; cabos que aterrizan
   fuera se anotan con **hogar numerado/existente verificado** (B-usage, B-signals, 02·loop motor #2,
   07·events D5, 01·contracts CompactionProvider, 09·tools-infra); superset y ⛔-front documentados con razón.
   *(Corrección tras revisión: se habían nombrado dos hogares inexistentes —`B-error-taxonomy` y `compact`—;
   reasignados a 07·D5 y 02·loop/01·contracts respectivamente. Ningún cabo queda "en ningún sitio".)*

---

## Targets de test de homologación (xfail(strict))
- `test_runtime_activates_extended_thinking` (MoR1) — xfail
- `test_usage_preserves_cache_tokens` (MoR2) — xfail
- `test_thinking_events_surfaced` (MoR3) — xfail
- `test_stop_event_aborts_stream` (MoR4) — xfail
- `test_error_event_has_typed_category` (MoR5) — xfail
- `test_529_triggers_model_fallback` / `test_400_not_retried` (MoR6) — xfail
- `test_prompt_too_long_routes_to_compact` (MoR7) — xfail
- `test_deferred_tools_send_tool_search_beta` (MoR8) — xfail
- `test_oauth_tool_name_mapping` / `test_tool_result_pairing_repair` / `test_sse_requires_message_stop` /
  `test_model_resolution_by_provider_id` — **passing** (comportamiento ya homologado, B13/B14/B17/A7)
