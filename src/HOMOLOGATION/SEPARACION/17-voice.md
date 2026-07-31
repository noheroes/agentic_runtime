# 17 · voice — SEPARACION (Filosofía B)

> Ruta base: `/home/noheroes/python`. Fuente: tracker `../17-voice.md` (336 líneas, leído **íntegro 1→336** este ciclo).
> Esquema: `00-LEGEND.md` (§2 ejes · §3 formato · §3.3 gatekeeper). Marco: memoria **architecture-layers** (B = base
> framework + batteries opcionales · agnosticismo de identidad · canónico = referencia de COMPLETITUD, no de FORMA).

---

## §0 · Tesis de la categoría + desambiguación

**Tesis.** La voz es la **única capacidad del runtime que es puro borde de I/O**: no entra al pool de tools, no tiene
catálogo, no produce estado durable. El tracker cerró la 2ª vuelta con un veredicto correcto **de fidelidad**
(comportamiento observable `audio → texto → prompt` ✅; motor STT y UI ⛔ integrador/front; 1 bug de saneo). Este ciclo
no discute ese veredicto de fidelidad: lo **re-clasifica de forma**, y ahí el resultado es distinto.

Bajo Filosofía B la pregunta no es «¿reproduce el runtime el comportamiento?» sino «¿lo reproduce **componiendo** o
**horneando**?». Leyendo el ensamblador la respuesta es inequívoca: **la voz está horneada dentro del mecanismo base**.
`LocalAgentRuntime.__init__` recibe dos parámetros de voz (`stt`, `tts`, runtime.py:76-77 → :106-107), su ciclo de vida
llama a `_wire_tts(bus, ctx)` (runtime.py:335) y a `_resolve_prompt(task, ctx)` (runtime.py:377), y `RuntimeTask` —un
**contrato T1**— lleva un campo `audio_prompt` (contracts/runtime.py:32). Un integrador que no quiera voz **igual paga
sus condicionales**, y un integrador que la quiera **distinta** (p. ej. hablar por WebSocket a un navegador, no por el
altavoz del proceso) sólo puede sustituir la primitiva, no la plomería. Eso es exactamente la dualidad
"usar-todo-vs-sobreescribir" que B existe para evitar: **la voz debe salir del núcleo y volver como battery componible**.

Y al intentar hacerla battery aparece el hallazgo estructural que el tracker no podía ver (porque medía fidelidad, no
forma): **una battery externa NO puede hoy reproducir el comportamiento que `_wire_tts` reproduce dentro del núcleo**,
porque los eventos del bus (`TokenEvent(content)`, `DoneEvent(stop_reason, usage)`, events/event_types.py 1→43) **no
llevan sobre**: ni agente, ni sesión, ni `is_subagent`. `_wire_tts` sólo puede filtrar subagentes (B4) porque el núcleo
le pasa el `ctx` **por fuera del bus** (runtime.py:239). Suscrito desde fuera, un sink de voz no sabe **quién habla**.
⇒ la extracción de la battery está **bloqueada por la pobreza del contrato de eventos** — y, leído `SEPARACION/07-events.md`
1→216, no como "consumidor de un gap ya abierto" sino como **contraejemplo a una clasificación de 07**: 07·B2 declara
🔀 *«atribución implícita por bus per-task»* y 07·B3 manda los campos de correlación (`session_id`/`uuid`) al **serializador
wire** (GAP-EVT5), razonando que *«el bus ya está scoped in-proc»*. La voz exhibe un consumidor **in-proc** que se suscribe
por la costura pública (sin `ctx`, sin wire) y que **no puede** reproducir B4 con esa premisa. Cabo a 07·B2/B3+GAP-EVT5.

Tercer eje, el de identidad: las dos firmas del seam rector son `transcribe(audio, ctx)` y `speak(text, ctx)`
(voice/protocol.py 1→58) donde `ctx` es el **`ToolUseContext` entero** (context/tool_use.py 1→70): `session_id`,
`user_id`, `messages` (la conversación completa), `tool_pool`, `app_state`, `storage`, `fs`, `git_credentials`. Es decir:
el runtime entrega a un motor de voz de terceros **la identidad interpretada y el estado entero del turno** para que
transcriba unos bytes. Eso viola la regla dura de §2.4 del LEGEND (`nunca userId/sessionId interpretados en contratos
del runtime`) por la puerta de atrás — no por un campo propio, sino por **transportar el bolso monolítico**.

**Desambiguación (qué NO afirma este doc).**
- **No** reabre el veredicto STT-only del canónico: la ausencia de TTS está verificada por barrido en el tracker (grep
  como prueba de ausencia, uso legítimo). El TTS del runtime **es superset**. Pero *superset* dice «no hay contra qué
  homologar»; **no** dice «exento de la forma B». Un superset mal ubicado es igual de mal ubicado.
- **No** convierte en deuda el motor STT ni la UI: D1-D9 y E1-E11 son **elementos de integrador**, con hogar nombrado y
  desarrollo simétrico (§2.4) — no CORE-GAPs (L10).
- **No** hereda del tracker las filas ✅/🔀: cada afirmación de cableado se re-verificó abriendo el ensamblador
  (runtime.py 1→435, factory.py 1→267, agent_loop.py 1→352) — L09/L11.
- **Sí** invierte la carga de la prueba (memoria **mimica-no-desfusion**): donde el runtime hace algo distinto **sin
  razón B explícita**, el default es CORE-GAP, no "des-fusión correcta".

**Los 5 CORE-GAPs que salen (keystone primero):** CG-V1 voz horneada en el núcleo · CG-V2 eventos sin sobre (bloquea
CG-V1) · CG-V3 fuga de identidad por `ctx` en el seam · CG-V4 = FIND-VOICE1 saneo per-chunk · CG-V5 fallo de STT
silencioso + prompt vacío al modelo.

---

## §1 · Tabla por finding

**Inventario (base del conteo del gatekeeper):** rejilla del tracker **A1-A7 (7) + B1-B5 (5) + C1-C2 (2) = 14** ·
bloques en prosa **§D (motor STT) enumerado D1-D9 (9)** y **§E (terminal/UI) enumerado E1-E11 (11)** = **34 findings**.
`FIND-VOICE1` es la etiqueta de B5 y `VoR1` su remediación (capa referenciada, no fila nueva) — misma convención que
06/10/04/13/15/14. §D/§E **no traían filas en el tracker**: se enumeran aquí porque la regla de simetría (LEGEND §1.1)
prohíbe cerrar la cara integrador con "→ integrador" a secas, y en esta categoría **la cara integrador es la masa**.

### A · STT (entrada → prompt)

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| A1 | El audio adjunto a la task se transcribe y **es** el prompt del turno | núcleo | **BATTERY** (hoy horneado como T2-BASE-MECANISMO) | paquete `agentic_runtime_voice` (composable `AudioPromptResolver`) + costura `SpeechToTextProtocol` | ejecución — el resolver recibe hoy `ctx` con `user_id`/`session_id` interpretados (→ CG-V3) | Extraer `_resolve_prompt` de `LocalAgentRuntime` a un **pre-procesador de task componible**; el núcleo sólo expone el punto de extensión `task → prompt` |
| A2 | Fallo de STT no tumba la task: `logger.warning` + cae a `task.prompt` | núcleo | **T2-BASE-MECANISMO** (política de degradación) — **defectuoso** | módulo base `execution/local` + contrato `events` | — | **CG-V5**: emitir `ErrorEvent`/evento de voz en vez de tragar; y no entregar prompt vacío al modelo |
| A3 | Streaming / transcripciones interinas | núcleo (contrato) + cáscara-CLI (preview) | **T3-INTEGRADOR** | integrador (motor STT) + costura `SpeechToTextProtocol` | — | 🔀 sostenido: `transcribe(audio)->str` one-shot; el integrador streamea **dentro** de su motor y devuelve el final. Documentar como obligación OI-VOICE-1 |
| A4 | Selección de idioma (20 langs BCP-47) | núcleo (escotilla) + cáscara-CLI (origen) | **T3-INTEGRADOR** | integrador; escotilla `AudioInput.metadata: dict` | — | 🔀 sostenido: no tipar `language` en el protocolo (el integrador posee ambos extremos) |
| A5 | Keyterms / boosting de vocabulario | núcleo (escotilla) | **T3-INTEGRADOR** | integrador; escotilla `AudioInput.metadata` | — | 🔀 sostenido; el vocabulario depende de workspace/branch que el runtime no posee |
| A6 | Formato de audio agnóstico (`data`/`mime_type`/`sample_rate`/`metadata`) | núcleo | **T1-CONTRATO** | paquete **contratos** (`AudioInput` sale de `voice/` y entra al paquete de contratos multimodales) | — | Mover `AudioInput` al paquete de contratos: es shape de dato invariante, no parte de la battery |
| A7 | Transcript **editable** antes de enviar (human-in-the-loop) | cáscara-CLI | **CLI-ONLY / INTERFAZ** | integrador (`00-INTEGRADORES.md`) | — | 🔀 sostenido, **con matiz**: el mecanismo HITL ya existe en el base (`ends_turn`, agent_loop.py:338-348); la revisión de transcript es **composición del integrador sobre él**, no capacidad ausente |

### B · TTS (superset del runtime)

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| B1 | Existencia de TTS (`speak`/`flush`) — sin contraparte canónica | núcleo | **BATTERY** + **T2-COSTURA** | paquete `agentic_runtime_voice` (sink) + costura `TextToSpeechProtocol` | ejecución (→ CG-V3) | **CG-V1**: sacar `_wire_tts` y los params `tts`/`stt` del ctor de `LocalAgentRuntime`; la battery se suscribe por la costura pública de eventos |
| B2 | Derivación incremental: un `speak` por `TokenEvent`, sin esperar el fin | núcleo | **BATTERY** (mecanismo del sink) | `agentic_runtime_voice` | — | Portar tal cual a la battery; el comportamiento es correcto, sólo cambia de casa |
| B3 | `flush` sólo al cerrar turno de habla (`stop_reason=="tool_calls"` no flushea) | núcleo | **BATTERY** (política del sink) | `agentic_runtime_voice`; depende de **T1** `DoneEvent.stop_reason` | — | Portar; **fijar `stop_reason` como vocabulario T1** (hoy es un literal string comparado en el núcleo, runtime.py:255) |
| B4 | Subagentes mudos (`ctx.is_subagent` → no suscribe) | núcleo | **BATTERY** (política) — **bloqueada** | `agentic_runtime_voice`; requiere sobre en eventos | ejecución — "quién habla" es hoy un dato fuera del stream | **CG-V2**: el sink externo no puede filtrar por agente porque `TokenEvent`/`DoneEvent` no llevan `agent_id`/`is_subagent`/`session_id`. Cabo a **07·B2/B3 + GAP-EVT5** (contraejemplo a la 🔀 de 07·B2, ver CG-V2) |
| B5 | Saneo por `PathPresentation` antes de hablar (invariante declarado en protocol.py:51) | núcleo | **BATTERY** (corrección) | `agentic_runtime_voice` | — | **CG-V4 = FIND-VOICE1**; remediación **VoR1** (§2.5). Además: el default `IdentityPresentation` es **no-op** (context/presentation.py 1→25) ⇒ el invariante es **vacuo** salvo inyección → obligación **OI-VOICE-2** del integrador |

### C · Config / gating de canal

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|
| C1 | Canal activo sii primitiva inyectada **y** flag `*_enabled` (gate en factory.py:212-216) | núcleo | **BATTERY** (composición) → residuo **DEUDA-B** | `agentic_runtime_voice`; `VoiceConfig` sale de `RuntimeConfig` | — | Bajo composición **el gate es la composición**: si no compones la battery, no hay canal. Los flags `stt_enabled`/`tts_enabled` quedan **redundantes** → borrar al extraer (o conservarlos **dentro** de la battery como toggle en caliente, decisión de la battery, no del núcleo) |
| C2 | Gating de auth (OAuth) + kill-switch (GrowthBook) + feature-flag de build | cáscara-CLI | **T3-INTEGRADOR** | integrador (`00-INTEGRADORES.md`) | — | ⛔ sostenido → obligación **OI-VOICE-3** (el integrador decide si compone el canal; el runtime no conoce auth ni flags de producto) |

### D · Motor de grabación / streaming STT → integrador (enumeración de §D del tracker)

Todos: **núcleo=no (borde de I/O del integrador)** · **TIER `T3-INTEGRADOR`** · **destino: integrador, detrás de la
costura `SpeechToTextProtocol`** · **nota-identidad `—`** (el motor lo posee el integrador; ninguna identidad cruza
al runtime). Desarrollo simétrico en §2.4.

| ID | resumen (capacidad canónica abierta y clasificada) | acción |
|---|---|---|
| D1 | Captura nativa cpal (macOS/Linux/Windows) + fallback SoX `rec` / `arecord` (ALSA); `startRecording`/`stopRecording` en modo push-to-talk (`silenceDetection:false`) | Realización del integrador; produce el `AudioInput` que cruza la costura |
| D2 | `checkVoiceDependencies`: detección de gestor de paquetes (brew/apt/dnf/pacman) + instrucciones de instalación | Pre-flight del integrador (OI-VOICE-3) |
| D3 | `checkRecordingAvailability`: guards de entorno remoto/homespace + probe WSL / `arecord` / tarjetas ALSA | Pre-flight del integrador (OI-VOICE-3) |
| D4 | `requestMicrophonePermission`: diálogo de permiso del SO (TCC en macOS) | Pre-flight del integrador (OI-VOICE-3) |
| D5 | Transporte STT streaming: WebSocket `/api/ws/speech_to_text/voice_stream` (Deepgram Nova3), OAuth Bearer, `KeepAlive` 8s / `CloseStream` | Interno del motor; el runtime nunca ve el transporte |
| D6 | Protocolo de transcripción: `TranscriptText` (interinos) · `TranscriptEndpoint` (final) · `TranscriptError` | Interno del motor; sólo el texto final cruza la costura |
| D7 | `finalize()` con 4 disparadores (endpoint post-CloseStream · sin-datos 1.5s · safety 5s · cierre de WS) + promoción del interino al cerrar | Interno del motor; define **cuándo** hay un `str` que devolver |
| D8 | Resiliencia de red: workaround de zona Cloudflare · proxy / TLS / mTLS | Interno del motor (OI-VOICE-1) |
| D9 | `getVoiceKeyterms`: 14 términos globales + basename de proyecto + palabras de branch + ficheros recientes (MAX 50) | Interno del motor; realiza A5 con conocimiento de workspace que el runtime **no posee** |

### E · Terminal / UI / comando → integrador (enumeración de §E del tracker)

Todos: **cáscara-CLI** · **TIER `CLI-ONLY / INTERFAZ`** · **destino: integrador con interfaz** (`agentic_code` =
terminal; `agentic_assistant` = capa front) · **nota-identidad `—`** salvo donde se indique. Desarrollo simétrico en §2.4.

| ID | resumen | acción |
|---|---|---|
| E1 | State-machine de dictado `idle / recording / processing` (+ `warmingUp`) | Capacidad de interfaz obligatoria si hay dictado (OI-VOICE-4) |
| E2 | Keybinding hold-to-talk (`voice:pushToTalk`, default space): timers de release/repeat/first-press, `HOLD_THRESHOLD` 5, `WARMUP_THRESHOLD` 2, bare-char vs modifier-combo | Realización terminal (`agentic_code`); en web = botón/hotkey del front |
| E3 | Focus-mode: dictado continuo con silence-timeout 5s | Política de interfaz del integrador |
| E4 | `computeLevel` (RMS) → waveform / `audioLevels` (feedback visual de nivel) | Feedback de interfaz (OI-VOICE-4) |
| E5 | Buffering de audio durante el connect + coalescencia en bloques de 32KB | Realización del integrador (borde motor↔interfaz) |
| E6 | Early-retry (250ms) + replay de silent-drop + guards de generación de sesión | Resiliencia de interfaz; **complementa** A2 del lado del integrador |
| E7 | Inserción del interino en el prompt-input: anchoring prefix/suffix, `stripTrailing`/`resetAnchor`, `interimRange` (dim UI) | Realización de A7 en la interfaz |
| E8 | Store de estado de voz (`context/voice.tsx`): idle/recording/processing, interim, audioLevels, warmingUp | Estado **de interfaz**, no del runtime |
| E9 | `normalizeLanguageForSTT`: `settings.language` → código BCP-47 (20 langs, name→code, fallback `en`) | Realiza A4 desde la preferencia de usuario, que **posee el integrador** |
| E10 | Slash-command `/voice` (toggle) + pre-flight (mic/deps/permiso) + hint de idioma + `availability`/`isHidden` | Superficie de comando del integrador |
| E11 | Analytics `tengu_voice_*` (telemetría del ciclo de dictado) | Observabilidad de producto del integrador |

---

## §2 · Síntesis de la categoría

### 2.1 Costuras que implica

**Reconciliación contra el registro** (`SEAMS.md` 1→435 abierto en el gate, **27 firmas S1-S27**): **ninguna** de las 27
es de voz — `SpeechToTextProtocol`/`TextToSpeechProtocol` no están registradas pese a estar cableadas. Alcance honesto de
esa comprobación: `SEAMS.md` es **A1.7 (espina: 01/16/07/02/05/09)** y **no fue actualizado por los ciclos A3**, así que
descarta colisión con la espina, **no** con costuras declaradas en otros A3 (03/10/06/08/04/15/13/12/11/14). Los números
`S28`/`S29` son **propuesta para el rollup**, no asignación firme.

| Costura | Registro `SEAMS.md` | Productor (define) | Consumidor (rellena/usa) | Estado hoy |
|---|---|---|---|---|
| `SpeechToTextProtocol.transcribe(audio, ctx) -> str` | **no registrada** (hueco de SEAMS) | contratos de voz | integrador (motor STT: D1-D9) | **existe y está cableada** (runtime.py:228) pero con `ctx` monolítico → CG-V3 |
| `TextToSpeechProtocol.speak(text, ctx)` / `flush(ctx)` | **no registrada** (hueco de SEAMS) | contratos de voz | integrador (sink de audio) | **existe y está cableada** (runtime.py:248/:257) · mismo defecto de `ctx` |
| `PathPresentation.sanitize_output(text) -> str` | **S12** (`existe-fiel`) | `contracts/storage.py` (1→40) | battery TTS (choke point del invariante) | **corrige a S12**: S12 cita `runtime.py:244` como cableado fiel, y **ése es justamente el call-site per-chunk defectuoso** (CG-V4). Además el default `IdentityPresentation` es no-op ⇒ invariante vacuo sin inyección |
| `EventBusProtocol.subscribe(event_type, handler)` | **S5** (`existe-fiel`) | `events/protocol.py` (1→22) | battery TTS (sustituye al cableado interno) | S5 es fiel **en lo que cubre** (orden + aislamiento de handler); el **sobre** no está en su firma ⇒ insuficiente para un sink externo → CG-V2 |
| **`VoiceCallContext`** (propuesta `S28`) | **ausente del registro** | contratos de voz | battery + motor del integrador | **no existe** — hoy se pasa `ToolUseContext` entero (CG-V3) |
| **`TaskPromptResolver`, punto de extensión `task → prompt`** (propuesta `S29`) | **ausente del registro** | núcleo (`execution/local`) | battery STT (`AudioPromptResolver`) | **no existe** — hoy `_resolve_prompt` está horneado (runtime.py:220-232, llamado en :377). Vecina de **S11 `UserInputProcessor`** (`existe-sin-poblar`, pre-turno): decidir en el rollup si son una sola costura de pre-proceso de entrada o dos |

### 2.2 Batteries que alimenta

**Precedente registrado:** `00-INTEGRADORES.md §1.5` (abierto 1→207 en el gate) **ya lista `voice` en el catálogo de
batteries de la espina** (`compaction`/`resilience`/`caching`/`budget`/`commands`/`wire`/`structured-output`/**`voice`**/
`result-summary`, fuente `00-BLUEPRINT.md §3`), y deja para **A3.CAT** la decisión "necesaria vs opcional". Esta ficha
**no inventa** la battery: la **especifica** (contenido, composables, costuras) dentro de una casilla ya reservada.

**`agentic_runtime_voice`** — paquete opcional único con dos composables independientes:
- **`AudioPromptResolver`** (entrada): dado un `RuntimeTask` con `AudioInput`, produce el prompt del turno vía
  `SpeechToTextProtocol`. Compone en el punto de extensión `task → prompt` del núcleo. Realiza A1/A2/A6.
- **`SpeechSink`** (salida): se suscribe a `TokenEvent`/`DoneEvent` por `EventBusProtocol`, sanea con
  `PathPresentation`, segmenta en límites seguros y emite a `TextToSpeechProtocol`. Realiza B1-B5.
Ambos **se componen o se sustituyen — nunca sobreescriben**; un integrador sin voz no los instala y el núcleo no
menciona la voz en ninguna firma. `agentic_code` compone los dos; `agentic_assistant` compone `AudioPromptResolver` y
**sustituye** `SpeechSink` por uno que emite audio al canal del cliente (en un contenedor no hay altavoz).

### 2.3 CORE-GAPs (keystone primero → rollup `DEUDA-A.md`)

**CG-V1 · La voz está horneada en el mecanismo base (KEYSTONE, de forma).**
- *Comportamiento:* `LocalAgentRuntime` conoce la voz en su firma (`stt`/`tts`, runtime.py:76-77 → :106-107), en su
  ciclo de vida (`_wire_tts` :335, `_resolve_prompt` :377) y en su `RuntimeConfig` (factory.py:84 `voice:
  VoiceConfig`, gate :212-216, paso :238-239). El contrato T1 `RuntimeTask` lleva `audio_prompt`
  (contracts/runtime.py:32). Un integrador sin voz paga la superficie; uno con voz distinta no puede cambiar la
  plomería, sólo la primitiva.
- *Costura:* punto de extensión `task → prompt` (entrada) + `EventBusProtocol.subscribe` (salida). Ninguna de las dos
  requiere que el núcleo nombre "voz".
- *Firma:* núcleo → `prompt_resolvers: Sequence[TaskPromptResolver]` (protocolo `async def resolve(task, ctx) -> str |
  None`, primera no-None gana, default = `task.prompt`); battery → `AudioPromptResolver(stt, ...)` y
  `SpeechSink(tts, presentation, ...).attach(bus)`.
- *Cableado:* borrar `stt`/`tts` del ctor y `_wire_tts`/`_resolve_prompt` del cuerpo de `execution/local/runtime.py`
  (220-262, 335, 377); el composable de entrada se invoca donde hoy está :377; el de salida se suscribe al bus que hoy
  se crea en :333. `AudioInput` migra al paquete de contratos (A6); `audio_prompt` **se conserva** en `RuntimeTask`
  como campo de entrada multimodal T1 (es shape de dato, no plomería) — o se generaliza a `attachments`.
- *Orden:* **bloqueado por CG-V2** para la mitad de salida (B4 no es reproducible desde fuera hoy). La mitad de
  entrada (A1) es extraíble ya.
- *Criterio:* un `grep -i "stt\|tts\|voice\|audio"` sobre `execution/` y `factory.py` da **0 hits** y los 8 tests de
  `test_voice_io.py` siguen pasando **componiendo la battery desde el test**, sin tocar el núcleo.

**CG-V2 · Los eventos no llevan sobre: ninguna battery externa sabe quién habla (HABILITADOR).**
- *Comportamiento:* `TokenEvent(content)` y `DoneEvent(stop_reason, usage)` (events/event_types.py 1→43) son
  anónimos. `_wire_tts` filtra subagentes (B4) porque recibe `ctx` **por parámetro** (runtime.py:239), no por el
  stream. Un sink suscrito por `subscribe()` recibiría los tokens del agente principal y de **todos** los subagentes
  mezclados, sin poder distinguirlos — y en `agentic_assistant`, sin poder saber **a qué sesión/usuario** enviar el
  audio.
- *Relación con 07 (corregida tras abrir `SEPARACION/07-events.md` 1→216 — antes lo atribuí mal a «FIND-EVT1,
  taxonomía pobre»; **FIND-EVT1 es usage/result terminal**, mapeado allí a D1/E2/E3, no a la anonimia del evento):* los
  anclajes correctos son **07·B2**, **07·B3** y **GAP-EVT5**. Y no son un gap que este ciclo herede, sino una
  **clasificación de 07 que la voz contradice**: 07·B2 cierra `parent_tool_use_id` como 🔀 T2-BASE-MECANISMO
  («atribución **implícita** por bus per-task, `_make_bus(task_id)`») y 07·B3 manda `session_id`/`uuid` al **serializador
  wire** porque «el bus ya está scoped in-proc». Ambas premisas asumen que el consumidor **o** posee el handle del bus
  per-task **o** está fuera de proceso. `SpeechSink` es el tercer caso: **in-proc, suscrito por la costura pública, sin
  `ctx` y sin wire** — y ahí la atribución implícita no existe y el wire no aplica. ⇒ 07·B2 debe re-examinarse en su
  rollup con este consumidor sobre la mesa; **no** afirmo aquí que la conclusión de 07 sea errónea, afirmo que fue
  tomada sin este caso.
- *Costura:* sobre común de evento (`agent_id`, `session_id` opaco, `is_subagent`, `turn`) — o bus por-run cuyo
  handle ya identifica al emisor.
- *Firma:* ~~`Event` gana un `EventEnvelope` (campos opacos, no interpretados por el runtime); `subscribe` puede
  filtrar por envelope.~~ → **FORMA CORREGIDA en A-CIERRE·P0 (AC-h1, ejecuta `CAT-h10`; 17-voice.md abierto
  1→EOF 2026-07-27):** el **`Event` BASE gana los campos de identidad** `task_id` · `agent_id` · `session_id` ·
  `seq` · `ts` (opacos, no interpretados por el runtime), **NO un `EventEnvelope` que envuelva**. Razón técnica
  verificada en `DEUDA-B §7.2`: `EventBus.emit` despacha por **`type(event)`** (`bus.py:40`) y `subscribe(TokenEvent,
  handler)` es la API tipada (`protocol.py:20`) ⇒ un envelope que envuelve **colapsa los 5 subtipos en uno y rompe el
  despacho tipado**, que es lo mejor que hoy tiene el bus. Viable porque `Event` es un frozen dataclass **sin campos**
  (`protocol.py:9-11`) y los 5 subtipos tienen **todos** los suyos con default (`event_types.py:17-43`) ⇒ añadir campos
  con default al base no rompe el orden de dataclass ni ninguna construcción existente. El filtrado de `SpeechSink` por
  `agent_id`/`is_subagent` se hace **sobre el propio evento**, sin envelope y sin `ctx`. `agent_id` es el mismo hilo de
  **K4 · ID-5 · H-4** ⇒ un solo cableado, tres consumidores.
- *Cableado:* `events/event_types.py` + `events/bus.py` (1→45) + el emisor `AgentLoop._emit` (agent_loop.py:152-154,
  llamado en :248/:312/:324) + `_make_bus` (runtime.py:333).
- *Orden:* **primero de todos**; CG-V1 (salida) depende de él. Se resuelve en el ciclo/rollup de **07·events**, no
  aquí — aquí queda **registrado como dependencia dura + objeción a 07·B2**, con su consumidor concreto nombrado.
- *Criterio:* `SpeechSink` externo reproduce B4 (subagentes mudos) **sin** recibir `ToolUseContext`.

**CG-V3 · El seam de voz transporta el bolso monolítico del turno (identidad).**
- *Comportamiento:* `transcribe(audio, ctx)` / `speak(text, ctx)` (voice/protocol.py 1→58) entregan a un motor de
  terceros el `ToolUseContext` completo (context/tool_use.py 1→70): `user_id`, `session_id`, `messages` (la
  conversación entera), `tool_pool`, `app_state`, `storage`, `fs`, `git_credentials`. Un motor de voz **no necesita
  nada de eso**; y el LEGEND §2.4 prohíbe expresamente identidad interpretada y objetos globales de scope en los
  contratos del runtime. Es una fuga por transporte, no por campo propio.
- *Costura:* `VoiceCallContext` mínimo y opaco.
- *Firma:* `@dataclass(frozen=True) class VoiceCallContext: id: str  # opaco, no interpretado` + `metadata:
  Mapping[str, Any]` + `stop: Event | None` (cancelación cooperativa). `transcribe(audio, vctx)` / `speak(text,
  vctx)` / `flush(vctx)`.
- *Cableado:* `voice/protocol.py` (firmas) + los 3 call-sites (runtime.py:228, :248, :257) — que tras CG-V1 viven en
  la battery.
- *Orden:* independiente de CG-V2; hacer **junto con** CG-V1 (mismo archivo, misma extracción).
- *Criterio:* un fake de motor que haga `dir(vctx)` no puede alcanzar `messages`, `user_id` ni `storage`; el test de
  homologación lo asevera.
- *nota-identidad:* eje **ejecución**; patrón **id opaco** (el integrador atribuye; el runtime transporta).

**CG-V4 · Saneo TTS per-chunk evade el choke point (= FIND-VOICE1, corrección).** Ver §2.5 (VoR1). Reclasificación de
forma: sigue siendo un gap **real y vivo**, y tras CG-V1 su hogar es la battery `SpeechSink`, no el núcleo. Además, el
default `IdentityPresentation` (context/presentation.py 1→25, ambos métodos no-op) hace el invariante **vacuo** salvo
inyección explícita → se convierte en obligación del integrador (**OI-VOICE-2**), no en más deuda del runtime.

**CG-V5 · El fallo de STT es silencioso y puede entregar un prompt VACÍO al modelo.**
- *Comportamiento:* `_resolve_prompt` (runtime.py:220-232) captura `Exception` → `logger.warning` → `return
  task.prompt`; y `return text or task.prompt` hace lo mismo con una transcripción vacía. **Nada se emite al bus.** En
  el flujo de voz real `task.prompt` es `""` (así lo ejercita `test_voice_io.py:106`), de modo que el fallback
  entrega `""` a `AgentLoop.run`, que lo inserta tal cual como mensaje `user` (agent_loop.py:179) y llama al modelo.
  Resultado observable: **el usuario habla, el STT falla, y el agente responde a un mensaje vacío** — sin que ninguna
  capa de arriba pueda enterarse. El canónico, en cambio, muestra el error y ofrece retry (A2/E6). Bajo
  **mimica-no-desfusion** esto no es "resiliencia headless": es un gap de observabilidad con carga de prueba invertida.
- *Costura:* contrato de eventos (`ErrorEvent`, ya existe en events/event_types.py) + la costura de resolución de
  prompt (CG-V1: `resolve` devuelve `None` ⇒ el turno **no arranca**).
- *Firma:* `AudioPromptResolver.resolve` → emite `ErrorEvent(message=..., recoverable=True)` y devuelve `None`
  cuando no hay texto; el núcleo, ante prompt vacío y sin resolver, **aborta la task** en vez de llamar al modelo.
- *Cableado:* hoy runtime.py:226-232 + :377-380; tras CG-V1, la battery + el guard de prompt vacío en el núcleo.
- *Orden:* independiente; se puede arreglar **antes** de la extracción (2 líneas) y re-ubicar después.
- *Criterio:* test — STT que lanza, `task.prompt=""` ⇒ (a) se observa un `ErrorEvent` en el bus, (b) el
  `model_caller` **no** se invoca.

### 2.4 Elementos de integrador (detalle simétrico — se vierten a `00-INTEGRADORES.md`)

#### CONTRATO BASE COMÚN (eje primario: obligaciones "must-be" de TODO integrador con voz)

**Nomenclatura corregida en el gate.** La primera redacción acuñó el prefijo `MB-V*` sin comprobar la convención.
Abierto `00-INTEGRADORES.md` 1→207: el registro es **`OI-*`** — numérico por categoría de la espina (01→OI-1..5 ·
02→OI-6..10 · 05→OI-11..17 · 09→OI-18..23) con prefijo de categoría cuando la hay (16→`OI-M#`, 07→`OI-EVT-#`).
Renombradas a **`OI-VOICE-1..5`**. `OI-VOICE-*` **no colisiona** con OI-1..23 / OI-M1..M8 / OI-EVT-1..4.

**Anclaje y test de duplicación** contra las 6 obligaciones universales ya consolidadas (`00-INTEGRADORES §1.1-1.6`) —
dos de las cinco **no son obligaciones nuevas sino refuerzos** de una existente, y así se declaran:

| | ancla en `00-INTEGRADORES` | ¿nueva o refuerzo? |
|---|---|---|
| **OI-VOICE-1** motor STT | §1.5 (composición de batteries) + §1.4 (borde de I/O) | **nueva** — ninguna OI cubre un borde de captura/transcripción |
| **OI-VOICE-2** `PathPresentation` real | §1.4, que **ya consume `sanitize_output` (S12)** vía OI-22/09·D9 | **REFUERZO**, no obligación nueva: §1.4 pide consumir el choke; aquí se endurece a *«si compones salida por voz, el default no-op deja de ser aceptable — DEBES inyectar una real»*. Se vierte como cláusula de §1.4, no como fila aparte |
| **OI-VOICE-3** gating de disponibilidad/producto | §1.5 (elegir qué compone) + §1.6 (política) | **REFUERZO** de §1.5: el caso voz añade *pre-flight de dispositivo/permiso del SO* al criterio de composición, que §1.5 sólo planteaba como selección de tool-set |
| **OI-VOICE-4** ciclo de dictado + feedback + edición | §1.4 (capa de interfaz/transporte) | **nueva** sub-obligación de §1.4 (§1.4 cubre render/transcript/wire, no captura interactiva ni HITL de entrada) |
| **OI-VOICE-5** observar y reportar el fallo de STT | §1.4 (consumo del stream) | **nueva** sub-obligación de §1.4, **dependiente de CG-V5** (hoy no hay evento que observar) |

**OI-VOICE-1 · El integrador POSEE el motor STT completo, en ambos extremos.**
- *Capacidad observable:* de un micrófono (o de un stream de cliente) sale un `AudioInput` y entra un `str` transcrito.
- *Costura que rellena:* `SpeechToTextProtocol.transcribe`.
- *Firma:* `async def transcribe(self, audio: AudioInput, vctx: VoiceCallContext) -> str`.
- *Realización:* captura (D1) · pre-flight (D2-D4) · transporte y protocolo de streaming (D5-D7) · resiliencia de red
  (D8) · idioma (A4/E9) · keyterms (D9/A5). El runtime **no tipa nada de esto**: viaja por `AudioInput.metadata` si el
  integrador quiere pasarlo entre sus propias capas.
- *Orden:* prerequisito de cualquier entrada por voz.
- *Criterio:* el runtime recibe bytes y devuelve prompt sin conocer códec, idioma, proveedor ni transporte.

**OI-VOICE-2 · El integrador que active salida por voz DEBE inyectar una `PathPresentation` real y decidir la política de subagentes.**
- *Capacidad observable:* nunca se pronuncia una ruta real de infraestructura; los subagentes no hablan (o hablan, si
  el producto lo quiere — pero es **decisión declarada**, no accidente).
- *Costura:* `PathPresentation` (inyectada en `RuntimeConfig.presentation`, factory.py:88/:207) + configuración del
  `SpeechSink`.
- *Firma:* `sanitize_output(text: str) -> str` no trivial.
- *Realización:* `agentic_code` (terminal, un solo usuario, rutas locales legítimas) puede quedarse con identidad
  **declarándolo**; `agentic_assistant` (multi-tenant, contenedor) **debe** mapear rutas de host a rutas de tenant.
- *Orden:* antes de componer `SpeechSink`.
- *Criterio:* test del integrador: un stream con una ruta real —**partida entre chunks**— no la pronuncia (mismo
  target que VoR1, aplicado del lado del integrador).

**OI-VOICE-3 · El gating de disponibilidad y de producto es del integrador, ANTES de componer el canal.**
- *Capacidad observable:* si no hay micro, dependencias, permiso, auth o el kill-switch está activo, la voz
  simplemente **no se ofrece** (y el usuario recibe una razón accionable).
- *Costura:* **ninguna del runtime** — el gate es la composición (C1) más la política del integrador (C2).
- *Firma:* pre-flight del integrador `-> VoiceAvailability{available, reason, remediation}`.
- *Realización:* `agentic_code`: D2-D4 + comando `/voice` (E10). `agentic_assistant`: permiso de micro del navegador
  + Keycloak (auth) + flag de producto en el bff; el front decide y el bff compone (o no) la battery para esa sesión.
- *Orden:* antes de crear el runtime de la sesión.
- *Criterio:* con la voz denegada, el proceso runtime no tiene ninguna referencia a primitivas de voz.

**OI-VOICE-4 · El integrador con interfaz DEBE proveer el ciclo de dictado, su feedback y la edición del transcript — o renunciar explícitamente.**
- *Capacidad observable:* el usuario sabe en todo momento si se está grabando, ve nivel de audio, puede cancelar, y
  revisa/edita el texto antes de que se convierta en el prompt.
- *Costura:* ninguna del runtime (es interfaz) + el mecanismo HITL ya existente del base (`ends_turn`,
  agent_loop.py:338-348) si la revisión ocurre **dentro** de un turno.
- *Firma:* propia de la interfaz (E1-E8, E10-E11).
- *Realización:* `agentic_code` = state-machine + keybinding hold-to-talk + waveform + inserción en prompt-input
  (E1-E8, E10). `agentic_assistant` = componente del front (botón push-to-talk, medidor, textarea editable), estado
  en el store del front, telemetría propia (E11); el bff no ve nada de esto.
- *Orden:* después de OI-VOICE-1/OI-VOICE-3.
- *Criterio:* la capacidad E1-E11 está cubierta o **explícitamente renunciada** en el doc del integrador (completitud
  de capacidad, no forma verbatim).

**OI-VOICE-5 · El integrador DEBE observar y reportar el fallo de transcripción.**
- *Capacidad observable:* si el STT falla o devuelve vacío, el usuario lo sabe y puede reintentar; el turno no se
  gasta contra un prompt vacío.
- *Costura:* `ErrorEvent` del contrato de eventos (tras CG-V5) + la resiliencia propia del integrador (E6:
  early-retry, replay de silent-drop).
- *Firma:* handler de `ErrorEvent` en el consumidor del stream.
- *Realización:* `agentic_code` = mensaje en terminal + retry con el mismo buffer de audio. `agentic_assistant` =
  evento al front por WS + botón de reintento; el audio se retiene en el cliente, no en el runtime.
- *Orden:* depende de CG-V5.
- *Criterio:* fallo inyectado en el motor STT ⇒ el usuario ve un error, no una respuesta a la nada.

#### Realización por integrador (capa secundaria)

| | `agentic_code` (fino/terminal) | `agentic_assistant` (complejo/multi-tenant + front) |
|---|---|---|
| **Motor STT (D1-D9)** | Proceso local: captura nativa/SoX, pre-flight de deps y permisos del SO, transporte al proveedor elegido | El **navegador** captura (MediaRecorder/WebRTC); el bff recibe el stream y transcribe server-side; sin cpal/ALSA ni permisos de SO — el permiso es del navegador |
| **Interfaz (E1-E11)** | Terminal: keybinding hold-to-talk, waveform ASCII, inserción interina en prompt-input, `/voice` | Front web: componente de dictado, medidor, transcript editable en textarea; `/voice` no existe (es UI, no comando) |
| **Salida TTS (B1-B5)** | Compone `SpeechSink` con un motor local (altavoz del proceso) | **Sustituye** `SpeechSink`: en contenedor no hay altavoz; el "habla" es audio sintetizado enviado por WS al cliente **de esa sesión** ⇒ necesita el sobre de evento (CG-V2) para saber a quién enviarlo |
| **Gating (C2/OI-VOICE-3)** | Auth del proveedor + flag local | Keycloak (auth) + KrakenD (routing) + flag de producto por tenant en el bff |
| **Identidad** | Degenerado: una sesión, un usuario; `VoiceCallContext.id` = constante | El bff atribuye: `VoiceCallContext.id` = id opaco de la sesión; el mapeo id→(tenant, usuario, canal) vive **fuera** del runtime |

### 2.5 VoR1 — remediación de CG-V4 / FIND-VOICE1 (heredada del tracker, re-ubicada)

Sostenida sin cambios en sustancia (buffer de habla saneado sobre el acumulado, emisión hasta el último límite seguro,
resto en `_on_done` antes de `flush`; target `test_tts_sanitizes_across_chunk_boundary`, hoy `xfail(strict=True)` en
`tests/test_voice_homologation.py:54-78`). **Cambio de forma:** el cableado destino ya no es
`execution/local/runtime.py:243-259` sino `SpeechSink` de la battery `agentic_runtime_voice`. Si se arregla **antes** de
CG-V1, el arreglo viaja con la extracción sin re-trabajo (la clausura pasa a método del sink).

### 2.6 DEUDA-B (higiene interna)

| Ítem | Tipo | Detalle |
|---|---|---|
| `VoiceConfig.stt_enabled` / `tts_enabled` | **borrar** (al extraer) | Redundantes bajo composición: no componer la battery **es** el gate (C1). Si se quiere toggle en caliente, vive dentro de la battery, no en `RuntimeConfig` |
| `RuntimeConfig.voice` (factory.py:84) + gate :212-216 + paso :238-239 | **borrar** (al extraer) | Superficie de voz en el ensamblador genérico |
| `LocalAgentRuntime(stt=…, tts=…)` (:76-77, :106-107) | **borrar** (al extraer) | Ídem en el núcleo |
| `DoneEvent.stop_reason == "tool_calls"` comparado como literal (runtime.py:255; espejo en agent_loop.py:348) | **cablear** | El vocabulario de `stop_reason` es T1 y hoy es string mágico en dos capas; fijarlo como enum/constante del contrato antes de que una battery externa dependa de él |

### 2.7 Cabos que aterrizan fuera de 17

- **07·events** — CG-V2 (sobre de evento). Dependencia dura de CG-V1 (mitad de salida) y de la sustitución del sink en
  `agentic_assistant`. **No** es "ya documentado allí": 07 clasificó la atribución in-proc como suficiente (B2 🔀) y
  mandó los campos de correlación al wire (B3 → GAP-EVT5). Lo que este ciclo aporta es un **consumidor in-proc por la
  costura pública** que refuta esa suficiencia ⇒ **re-examen de 07·B2 en su rollup**, con 17·B4/CG-V2 como caso de prueba.
- **`SEAMS.md` (rollup de costuras)** — tres correcciones al registro, halladas al abrirlo 1→435:
  1. **S12 `PathPresentation` está sobre-declarada.** Su estado es `existe-fiel` citando *«`sanitize_output` cableado
     `dispatcher.py:42` + **`runtime.py:244`**»* — pero `runtime.py:244` **es** el call-site per-chunk de la voz, es decir
     el defecto CG-V4/FIND-VOICE1. El choke es fiel en `dispatcher.py:42` y **defectuoso** en el de TTS ⇒ el estado
     correcto es `existe-parcial` con el defecto nombrado por call-site.
  2. **Hueco de cobertura:** `SpeechToTextProtocol`/`TextToSpeechProtocol` están **cableadas y no registradas** entre las
     27 firmas (S1-S27). SEAMS es A1.7-espina y no se actualizó en A3; el rollup debe absorber las costuras de los A3.
  3. **Vecindad S11:** el punto de extensión `task → prompt` (propuesta S29) solapa con **S11 `UserInputProcessor`**
     (`existe-sin-poblar`, productor = el loop **pre-turno**). Decidir en el rollup: una sola costura de pre-proceso de
     entrada, o dos (una pre-`AgentLoop` a nivel de `RuntimeTask`, otra intra-turno a nivel de `UserInput`).
- **01·contracts** — `AudioInput` migra al paquete de contratos (A6) y `stop_reason` se fija como vocabulario T1 (2.6).
- **03·context** — `PathPresentation` / `IdentityPresentation` no cambian; sólo se documenta que el default no-op
  vuelve vacuo el invariante de B5 (obligación OI-VOICE-2, no deuda nueva).
- **18·factory** (siguiente ciclo) — la retirada de `VoiceConfig` de `RuntimeConfig` es un caso concreto del patrón
  general "config del núcleo vs composición de batteries" que 18 debe resolver de forma sistemática.

---

## §3 · GATEKEEPER de cierre (00-LEGEND §3.3)

> **Frase de rigor.** De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda;
> ninguna categoría se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar
> —o colocado sin abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

### Ledger — una fila por CADA finding (34)

| ID | TIER | destino | cara | evidencia | detalle desarrollado | nota-identidad |
|---|---|---|---|---|---|---|
| A1 | BATTERY | `agentic_runtime_voice::AudioPromptResolver` | ambas | ensamblador `execution/local/runtime.py:220-232`+`:377` abierto (archivo 1→435) | sí (6 campos L05, CG-V1) | ejecución · id opaco |
| A2 | T2-BASE-MECANISMO | módulo base `execution/local` + contrato eventos | ambas | `runtime.py:226-232` + `loop/agent_loop.py:179` (1→352) | sí (6 campos, CG-V5) | — |
| A3 | T3-INTEGRADOR | integrador (motor STT) | integrador | tracker-leído + `voice/protocol.py:1-58` | sí (OI-VOICE-1) | — |
| A4 | T3-INTEGRADOR | integrador; escotilla `AudioInput.metadata` | integrador | `voice/protocol.py` (AudioInput 1→58) | sí (OI-VOICE-1 · E9) | — |
| A5 | T3-INTEGRADOR | integrador; escotilla `metadata` | integrador | ídem | sí (OI-VOICE-1 · D9) | — |
| A6 | T1-CONTRATO | paquete **contratos** (`AudioInput`) | base | `voice/protocol.py:1-58` + `contracts/runtime.py:32` (1→67) | sí (acción de migración) | — |
| A7 | CLI-ONLY / INTERFAZ | integrador con interfaz | integrador | `loop/agent_loop.py:338-348` (mecanismo HITL existente) | sí (OI-VOICE-4 · E7) | — |
| B1 | BATTERY + T2-COSTURA | `agentic_runtime_voice::SpeechSink` | ambas | `runtime.py:76-77`,`:106-107`,`:234-262`,`:335` (1→435) | sí (6 campos, CG-V1) | ejecución · id opaco |
| B2 | BATTERY | `SpeechSink` | base | `runtime.py:243-248` + `test_voice_io.py:144-154` (1→208) | sí (portar) | — |
| B3 | BATTERY | `SpeechSink` (+ T1 `stop_reason`) | base | `runtime.py:252-259` + `test_voice_io.py:199-208` | sí (portar + DEUDA-B 2.6) | — |
| B4 | BATTERY (bloqueada) | `SpeechSink`; requiere sobre de evento | base | `runtime.py:239` + `events/event_types.py` 1→43 + `bus.py` 1→45 | sí (6 campos, CG-V2) | ejecución |
| B5 | BATTERY (corrección) | `SpeechSink` | ambas | `runtime.py:241-248` + `context/presentation.py` 1→25 + `contracts/storage.py` 1→40 + `test_voice_homologation.py:54-78` | sí (VoR1, 6 campos + OI-VOICE-2) | — |
| C1 | BATTERY (composición) → DEUDA-B | `agentic_runtime_voice`; borrar flags | ambas | `factory.py:63-76`,`:212-216`,`:238-239` (1→267) | sí (2.6 + OI-VOICE-3) | — |
| C2 | T3-INTEGRADOR | integrador (auth/kill-switch) | integrador | tracker-leído (canónico) + `factory.py:212-216` (ausencia en B) | sí (OI-VOICE-3) | — |
| D1 | T3-INTEGRADOR | integrador tras `SpeechToTextProtocol` | integrador | tracker-leído (A abierto 1→EOF en 2ª vuelta) | sí (OI-VOICE-1) | — |
| D2 | T3-INTEGRADOR | integrador (pre-flight) | integrador | tracker-leído | sí (OI-VOICE-3) | — |
| D3 | T3-INTEGRADOR | integrador (pre-flight) | integrador | tracker-leído | sí (OI-VOICE-3) | — |
| D4 | T3-INTEGRADOR | integrador (pre-flight) | integrador | tracker-leído | sí (OI-VOICE-3) | — |
| D5 | T3-INTEGRADOR | integrador (transporte) | integrador | tracker-leído | sí (OI-VOICE-1) | — |
| D6 | T3-INTEGRADOR | integrador (protocolo interno) | integrador | tracker-leído | sí (OI-VOICE-1) | — |
| D7 | T3-INTEGRADOR | integrador (finalize) | integrador | tracker-leído | sí (OI-VOICE-1) | — |
| D8 | T3-INTEGRADOR | integrador (resiliencia de red) | integrador | tracker-leído | sí (OI-VOICE-1) | — |
| D9 | T3-INTEGRADOR | integrador (keyterms) | integrador | tracker-leído | sí (OI-VOICE-1 · A5) | — |
| E1 | CLI-ONLY / INTERFAZ | integrador con interfaz | integrador | tracker-leído | sí (OI-VOICE-4) | — |
| E2 | CLI-ONLY / INTERFAZ | integrador con interfaz | integrador | tracker-leído | sí (OI-VOICE-4, realización por integrador) | — |
| E3 | CLI-ONLY / INTERFAZ | integrador con interfaz | integrador | tracker-leído | sí (OI-VOICE-4) | — |
| E4 | CLI-ONLY / INTERFAZ | integrador con interfaz | integrador | tracker-leído | sí (OI-VOICE-4) | — |
| E5 | CLI-ONLY / INTERFAZ | integrador (borde motor↔interfaz) | integrador | tracker-leído | sí (OI-VOICE-1/OI-VOICE-4) | — |
| E6 | CLI-ONLY / INTERFAZ | integrador (resiliencia) | integrador | tracker-leído + `runtime.py:226-232` (contraparte base A2) | sí (OI-VOICE-5) | — |
| E7 | CLI-ONLY / INTERFAZ | integrador (prompt-input) | integrador | tracker-leído + `agent_loop.py:338-348` | sí (OI-VOICE-4 · A7) | — |
| E8 | CLI-ONLY / INTERFAZ | integrador (store de UI) | integrador | tracker-leído | sí (OI-VOICE-4) | — |
| E9 | CLI-ONLY / INTERFAZ | integrador (idioma desde preferencia) | integrador | tracker-leído | sí (OI-VOICE-1 · A4) | — |
| E10 | CLI-ONLY / INTERFAZ | integrador (comando/superficie) | integrador | tracker-leído | sí (OI-VOICE-3/OI-VOICE-4) | — |
| E11 | CLI-ONLY / INTERFAZ | integrador (telemetría) | integrador | tracker-leído | sí (OI-VOICE-4) | — |

*(`FIND-VOICE1` = etiqueta de B5; `VoR1` = su remediación en §2.5 — capa referenciada, no fila adicional.)*

### 5 preguntas de cierre

1. **¿Se leyó ÍNTEGRO `../17-voice.md`?** **Sí — 1→336** este ciclo (no heredado: el tracker se releyó completo tras
   abrir los contratos, para enumerar §D/§E con su literalidad).
2. **¿Reconcilia el conteo?** Findings en `../17-voice.md` = **34** (rejilla A1-A7·7 + B1-B5·5 + C1-C2·2 = 14; §D
   enumerado D1-D9 = 9; §E enumerado E1-E11 = 11). Colocados = **34**. Sin colocar = **0**. ✅
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador, sin grep?** Sí. Tramos abiertos **1→EOF**
   (archivo completo, no fragmento): `execution/local/runtime.py` **1→435** (STT :220-232 · TTS :234-262 · `_run_loop`
   :317 presentation, :333 bus, :335 wire, :377 resolve, :380 run) · `factory.py` **1→267** (`VoiceConfig` :63-76 ·
   gate :212-216 · paso :238-239) · `loop/agent_loop.py` **1→352** (emisión `_emit` :152-154 / :248 · inserción de
   prompt :179 · `ends_turn` :338-348) · `events/bus.py` **1→45** · `events/event_types.py` **1→43** ·
   `events/protocol.py` **1→22** · `events/__init__.py` **1→15**. **Contratos abiertos ANTES de escribir** (regla dura
   del ciclo): `voice/protocol.py` **1→58** · `voice/__init__.py` **1→6** · `contracts/runtime.py` **1→67** ·
   `contracts/storage.py` **1→40** (`PathPresentation`) · `context/presentation.py` **1→25** (`IdentityPresentation`
   no-op) · `context/tool_use.py` **1→70**. Evidencia B-side: `tests/test_voice_io.py` **1→208** ·
   `tests/test_voice_homologation.py` **1→78**. Grep usado **sólo** como prueba de ausencia (consumidores de
   `stt`/`tts`/`audio_prompt` fuera de `voice/`: los 3 archivos ya abiertos + tests), nunca como evidencia de cableado.
   **Ampliación forzada por el gate del usuario:** la pregunta cubre el ensamblador, y ahí la respuesta era sí; pero la
   **clasificación** se apoyaba también en tres docs del corpus SEPARACION que **no abrí en la 1ª pasada** —
   `SEAMS.md` (435), `00-INTEGRADORES.md` (207), `SEPARACION/07-events.md` (216). Abiertos 1→EOF en la 2ª pasada;
   refutaron tres afirmaciones y el doc está corregido (ver §Nota de honestidad). **Sigue sin abrirse**:
   `00-BLUEPRINT.md` (185) — citado de segunda mano vía `00-INTEGRADORES §1.5`; y `../17-voice.md` del **canónico** no
   se releyó (evidencia `tracker-leído` para las 20 filas D/E, declarado abajo).
4. **¿La cara integrador quedó al MISMO detalle que la base?** Sí, y en esta categoría **es la cara mayoritaria**
   (20 de 34 findings). §D y §E **no tenían filas** en el tracker: se enumeraron D1-D9 / E1-E11 y se desarrollaron en
   §2.4 por el eje primario (5 obligaciones OI-VOICE-1…OI-VOICE-5 con capacidad·costura·firma·realización·orden·criterio) más
   la realización por integrador. **Ningún finding cerrado con "→ integrador" a secas.**
5. **¿Doble filo (L10)?** Revisado en ambos sentidos.
   - *No inflar:* A3/A4/A5 (streaming, idioma, keyterms) y D1-D9/E1-E11 se mantienen 🔀/⛔ — el integrador posee el
     motor en ambos extremos y la interfaz no es del runtime headless. **No** se convirtieron en deuda.
   - *No ocultar:* al revés, aquí el filo cortó en la otra dirección. Tres filas que el tracker daba por buenas
     (**B1/B2/B4 superset ✅-diseño**, **C1 🔀 "más fino que el canónico"**) se **re-clasifican**: el comportamiento es
     correcto, pero su **ubicación** viola B (CG-V1) y una de ellas (B4) resulta **no reproducible** fuera del núcleo
     (CG-V2). Y **A2 🔀** ("resiliencia = motor del integrador") se reclasifica a **CORE-GAP (CG-V5)**: tragar la
     excepción sin emitir evento y entregar `""` al modelo no es des-fusión, es pérdida de observabilidad — carga de
     prueba invertida según **mimica-no-desfusion**. Ninguna de estas cuatro es deuda **frente al canónico**; son
     deuda **frente a la Filosofía B**, que es lo que esta fase mide.

### §Nota de honestidad — lo NO verificado primero

- **PASE DE CORRECCIÓN tras el gate del usuario (2ª iteración).** La 1ª redacción cerró con ✅ **sin haber abierto tres
  archivos del corpus SEPARACION sobre los que apoyaba clasificación**: `SEAMS.md`, `00-INTEGRADORES.md` y
  `SEPARACION/07-events.md`. Abiertos 1→EOF (435 · 207 · 216) y **corregido lo que refutaron**: (a) «2 costuras NUEVAS»
  → reconciliado contra las 27 firmas S1-S27, con alcance declarado (SEAMS no cubre A3) y con **corrección a S12**
  (sobre-declarada `existe-fiel` citando el call-site defectuoso); (b) `MB-V*` → **`OI-VOICE-*`** (convención real) y
  **dos de las cinco degradadas de "obligación nueva" a "refuerzo"** de §1.4/§1.5 ya existentes; (c) **CG-V2 re-anclado**:
  mi cita a «07·FIND-EVT1 (taxonomía pobre)» era **incorrecta** — FIND-EVT1 es usage/result terminal (07 lo mapea a
  D1/E2/E3); los anclajes son 07·B2/B3+GAP-EVT5, y la relación no es herencia sino **objeción** a la 🔀 de 07·B2. La ✅
  anterior no estaba ganada; ésta se firma con esos tres archivos leídos.
- **El paquete `agentic_runtime_voice` es una propuesta de nombre/forma, no una decisión ratificada.** Con el matiz
  ganado en el gate: la **casilla** sí está reservada (`00-INTEGRADORES §1.5` lista `voice` en el catálogo de batteries,
  fuente `00-BLUEPRINT.md §3`, con "necesaria vs opcional" diferido a A3.CAT); lo no ratificado es el **nombre de
  paquete** y el reparto en dos composables. **`00-BLUEPRINT.md` (185) no lo abrí**: la casilla la leo citada desde
  `00-INTEGRADORES §1.5`, no de primera mano.
- **La realización de `agentic_assistant` (front web, MediaRecorder, bff) es diseño derivado de la memoria
  architecture-layers, no de código leído** — ese integrador **no existe todavía**. Es una obligación documentada, no
  una descripción de algo construido.
- **No re-leí el lado canónico este ciclo.** D1-D9 y E1-E11 se enumeran de la prosa del tracker (§D/§E), que sí
  registra lectura 1→EOF de los 10 archivos en la 2ª vuelta. Para una fase de **clasificación de forma** eso basta
  (no estoy midiendo fidelidad), pero lo declaro: la evidencia de esas 20 filas es `tracker-leído`, no lectura
  primaria de A esta ronda.
- **No ejecuté la suite.** El estado `xfail(strict)` de `test_tts_sanitizes_across_chunk_boundary` lo tomo del código
  del test y del cableado leído, no de una corrida.

### VEREDICTO

**✅ NADA PENDIENTE → A3·18·factory** — firmado en **2ª iteración**, tras que el gate del usuario destapase tres
archivos del corpus SEPARACION sin abrir. La ✅ de la 1ª iteración queda **retractada y sustituida** por ésta.

34/34 findings colocados (0 sin colocar) · 5 CORE-GAPs con remediación desarrollada (CG-V1 keystone · CG-V2 habilitador,
**objeción a 07·B2** · CG-V3 identidad · CG-V4=VoR1 · CG-V5 observabilidad) · 4 ítems DEUDA-B · 1 battery
(`agentic_runtime_voice`, 2 composables, en casilla ya reservada del catálogo) · 6 costuras, de ellas **2 ausentes del
registro `SEAMS.md`** (`VoiceCallContext` → propuesta S28 · `TaskPromptResolver` → propuesta S29, vecina de S11) y **2
cableadas pero no registradas** (`SpeechToTextProtocol`/`TextToSpeechProtocol`) · **3 correcciones a docs previos**
(`SEAMS §S12` sobre-declarada · hueco de cobertura de SEAMS en A3 · re-examen de 07·B2) · 5 obligaciones de CONTRATO BASE
COMÚN **`OI-VOICE-1..5`** (2 de ellas declaradas **refuerzo** de §1.4/§1.5, no obligaciones nuevas) + realización por
integrador · 5 cabos fuera de 17 (07·events bloqueante, `SEAMS.md` rollup, 01·contracts, 03·context, 18·factory).

Las salvedades de §Nota de honestidad son **declaraciones de alcance de evidencia**, no findings sin colocar. La única
lectura que sigue pendiente y **declarada como tal** es `00-BLUEPRINT.md` (185), citado de segunda mano: no sostiene
ninguna clasificación de este doc, sólo la existencia de la casilla `voice` en el catálogo, que `00-INTEGRADORES §1.5`
transcribe.
