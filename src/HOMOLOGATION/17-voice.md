# 17 · voice — `agentic_runtime/voice` ← canónico (`voice/`, `services/voice*`, `hooks/useVoice*`)

> **Forma del subsistema.** La voz es una **capability de borde de I/O**, no de tools: no aporta catálogo ni
> entra al pool. El runtime declara **primitivas + plomería** y **empuja el motor real al integrador**:
> `voice/{protocol.py, __init__.py}` (64 LOC) define `AudioInput`, `SpeechToTextProtocol` (`transcribe`) y
> `TextToSpeechProtocol` (`speak`/`flush`); el cableado vive en `execution/local/runtime.py`
> (`_resolve_prompt` para STT, `_wire_tts` para TTS) y el gate en `factory.py::VoiceConfig`. El runtime **no
> graba audio, no reproduce audio, no habla con ningún servicio STT** — recibe `AudioInput` (bytes) y entrega
> texto saneado a la primitiva.
>
> **La contraparte canónica es asimétrica en dos sentidos:**
> 1. **Es STT-only.** El canónico **no tiene text-to-speech en absoluto** — verificado con barrido
>    (`text-to-speech|tts|synthesi[sz]|speak(|audio.?out|speechSynthesis`): 0 hits de audio; todos los
>    "synthesize" son "sintetizar hallazgos"). El asistente **nunca habla**. → El `TextToSpeechProtocol` del
>    runtime es una **invención sin contraparte** (superset), como los ~30 providers de `agentic_models`.
> 2. **Es push-to-talk terminal dictation.** Todo el STT canónico está acoplado al terminal: keybinding
>    hold-to-talk, auto-repeat del OS, inserción en el widget de prompt-input de ink, focus-mode, waveform
>    visualizer, `/voice` slash-command. Nada de eso existe en el runtime (multi-usuario/multi-sesión, sin
>    terminal). La homologación es **de comportamiento**: ¿el runtime reproduce el *comportamiento observable*
>    (audio → texto → prompt del turno) empujando el motor y la UI al integrador/front?

**Estados:** ✅3 (core STT audio→prompt · gate por-canal · subagentes mudos) · 🔀5 (diferencias inherentes a
runtime no-interactivo) · 🟡0 · ❌1 (**FIND-VOICE1** saneo TTS por-chunk se evade en frontera) · ⛔ (motor de
grabación/streaming STT = **integrador**; keybindings/prompt-input/`/voice`/state-machine/gating GrowthBook-OAuth
= **front**, abiertos y clasificados con razón) · **superset**: TTS entero (sin contraparte canónica).

> **Estado (2ª vuelta · gate 11/L09, 2026-07-20): VALIDADA sin cambio de estado — código intacto.** Ver el bloque
> "Re-visita de COMPLETITUD" más abajo. Tabla y §Plan se sostienen; 0 costuras latentes nuevas; 1 precisión de
> clasificación (FIND-VOICE1 es tech-debt B-interno de un superset, no "Deuda A↔B" — no hay A que homologar).

---

## Re-visita de COMPLETITUD (2ª vuelta · gate 11/L09) — 2026-07-20

**Método:** cada fila ✅/🔀 verificada abriendo el consumidor real de B (no la tabla) + el **ENSAMBLADOR/cableado**
(`factory.py` gate voz + `runtime.py::_resolve_prompt`/`_wire_tts`, leídos 1→EOF) + **lado A RE-LEÍDO 1→EOF ESTA
ronda** (L11, reproche recurrente 11–16) + la **ausencia de TTS canónico RE-VERIFICADA por barrido ESTA ronda**.
**CERO discrepancias en filas documentadas · CERO cambios de estado (✅3·🔀5·❌1 intactos) · código intacto.**

### Cableado confirmado abriendo B (L09)
- **STT (A1/A2)** — `runtime.py::_resolve_prompt` (220-232, leído 1→EOF): `if self._stt is None or audio is None:
  return task.prompt`; `text = await self._stt.transcribe(audio, ctx)`; `except → task.prompt`; `return text or
  task.prompt`. Consumido en `_run_loop` (runtime.py:377 `prompt = await self._resolve_prompt(task, ctx)`). El campo
  de entrada = `RuntimeTask.audio_prompt` (contracts/runtime.py:32). **A1✅/A2🔀 sostenidos por lectura.**
- **TTS (B2/B3/B4/B5)** — `runtime.py::_wire_tts` (234-262, leído 1→EOF): retorna si `self._tts is None or
  ctx.is_subagent` (**B4** subagente mudo :239); `_on_token` → `presentation.sanitize_output(content)` → `speak`
  (**B2** incremental + **B5** saneo, :244-248); `_on_done` → si `stop_reason=="tool_calls"` no flushea, si no
  `flush` (**B3**, :252-259). Cableado en `_run_loop` (runtime.py:335 `self._wire_tts(bus, ctx)`).
- **Gate por-canal (C1)** — `factory.py:214-216` (leído 1→EOF esta sesión): `stt = voice.stt if (voice.stt and
  voice.stt_enabled) else None`; ídem `tts`. **C1🔀 sostenido** (más fino que el flag único canónico).
- **Comportamiento cableado verificado por `test_voice_io.py` 1→EOF** (208): STT→prompt (97-137), TTS incremental+flush
  (144-154), disabled (157-167), saneo mono-chunk (170-181), subagente mudo (188-196), no-flush-en-tool_calls (199-208).

### FIND-VOICE1 confirmado por LECTURA (no vs canónico — no hay TTS en A)
`_wire_tts._on_token` (runtime.py:244) aplica `sanitize_output` **al `content` del chunk crudo** antes de `speak`.
Una ruta partida entre dos `TokenEvent` (`"/srv/sec"` + `"reto/app.log"`) → ningún chunk contiene el token completo
`/srv/secreto` → el saneo no matchea → **la ruta se habla en claro**, violando el invariante que el propio docstring
declara (protocol.py:51 "nunca se leen en voz alta rutas reales de infra"). El test `test_tts_text_is_sanitized_by_
presentation` (test_voice_io.py:170-181) sólo prueba una ruta contenida en **un** chunk (leído esta ronda: confirma que
NO cubre el caso partido). Remediación **VoR1** desarrollada (§Plan) — buffer de habla saneado sobre el acumulado.

### PRECISIÓN de clasificación (no voltea estado, gate-11 value-add, L10/L11)
**FIND-VOICE1 es tech-debt B-INTERNO de un superset, NO deuda A↔B.** El TTS entero es superset (el canónico **no
habla** — ver barrido abajo), así que no hay comportamiento canónico que homologar: es un **bug de corrección en un
invariante que el propio runtime declara**, no una brecha frente a A. Se distingue de los B-orphans (LAT-EXEC1/…/LAT-
MODELS1): aquéllos son **maquinaria muerta a borrar**; FIND-VOICE1 es una **ruta VIVA con fuga de corrección a
CABLEAR** (VoR1), hermano de LAT-SKILL1 (a cablear, no borrar). El doc lo enmarcaba en "§Plan Deuda A"; la etiqueta
precisa es **B-interno/superset** (el propio doc ya reconoce "TTS superset"). Estado ❌ + VoR1 **intactos**.

### Ausencia de TTS canónico — RE-VERIFICADA por barrido ESTA ronda (grep = prueba de AUSENCIA)
`grep -rIniE "speechSynthesis|text-to-speech|TextToSpeech"` sobre `claude-code/src` = **0 hits**; barrido ampliado
(`\btts\b|audio.?out|\.speak\(|say\(`, filtrando "synthesize findings") = **0 hits de audio-output**. El árbol
canónico de voz = **8 archivos** (`services/voice*`×3, `context/voice.tsx`, `commands/voice/*`×2, `voice/
voiceModeEnabled.ts`) + `hooks/useVoice*`×2, **ninguno con TTS**. Superset confirmado por AUSENCIA (uso legítimo de grep).

### Ledger de lectura A/B — ESTA ronda (columna "Lectura")
| Lado | Archivo | LOC | Lectura ESTA ronda |
|---|---|---|---|
| B | `voice/protocol.py` | 58 | íntegro 1→EOF (AudioInput + STT/TTS protocols + invariante docstring) |
| B | `voice/__init__.py` | 6 | íntegro |
| B | `execution/local/runtime.py::_resolve_prompt`/`_wire_tts` | — | 220-262 íntegro 1→EOF (+ cableado `_run_loop` :335/:377) |
| B | `factory.py::VoiceConfig` + gate | — | 63-76·214-216·238-239 (leído 1→EOF esta sesión en 16) |
| B | `contracts/runtime.py::RuntimeTask.audio_prompt` | — | :16-32 |
| B | `tests/test_voice_io.py` | 208 | **íntegro 1→EOF** (cablea A1/B2/B3/B4/B5/C1; confirma que el test de saneo NO cubre el caso partido) |
| A | `hooks/useVoice.ts` | 1144 | **íntegro 1→EOF ESTA ronda** (más grande L08; terminal state-machine/hold-to-talk/focus/replay/retry/`normalizeLanguageForSTT`/`computeLevel` — sin core oculto) |
| A | `hooks/useVoiceIntegration.tsx` | 677 | **íntegro 1→676 ESTA ronda** (prompt-input insert/anchoring + keybinding handler; línea 677 = sourcemap base64 = no-leíble-con-razón) |
| A | `services/voice.ts` | 525 | **íntegro 1→EOF ESTA ronda** → ⛔-integrador (motor grabación cpal/SoX/arecord + probes deps/mic; sin core) |
| A | `services/voiceStreamSTT.ts` | 544 | **íntegro 1→EOF ESTA ronda** → ⛔-integrador (motor STT WS voice_stream/OAuth/KeepAlive/finalize/Nova3/keyterms/CF-workaround; sin core) |
| A | `services/voiceKeyterms.ts` | 106 | **íntegro 1→EOF ESTA ronda** → ⛔-integrador (boosting keyterms proyecto/branch/ficheros) |
| A | `context/voice.tsx` | 87 | **íntegro 1→EOF ESTA ronda** (código 1-87; línea 88 = sourcemap base64) → ⛔-front (store React estado UI voz) |
| A | `commands/voice/voice.ts` + `index.ts` | 150+21 | **íntegros 1→EOF ESTA ronda** → ⛔-front (comando `/voice` toggle + pre-flight mic/deps/permiso; registro) |
| A | `voice/voiceModeEnabled.ts` + `hooks/useVoiceEnabled.ts` | 54+25 | **íntegros 1→EOF ESTA ronda** → ⛔-front (gating auth OAuth + GrowthBook kill-switch `tengu_amber_quartz_disabled`) |

### §Nota de honestidad
- El **value-add del gate 11** fue (a) confirmar el cableado STT/TTS abriendo `_resolve_prompt`/`_wire_tts` 1→EOF y
  ver que **FIND-VOICE1 vive en `_on_token` per-chunk** (no vs canónico, que no tiene TTS), (b) **re-verificar la
  ausencia de TTS por barrido ESTA ronda** (la claim que sostiene TODA la clasificación B-superset), (c) re-leer los
  dos grandes de A 1→EOF esta ronda para confirmar que no esconden core.
- **TODO el lado A (los 10 archivos in-scope) se RE-LEYÓ 1→EOF ESTA ronda** (L11, no heredado del ledger 1ª pasada):
  los dos grandes `useVoice.ts` 1144 + `useVoiceIntegration.tsx` 1→676, Y **los 8 satélites de motor STT / front**
  (`voice.ts` 525, `voiceStreamSTT.ts` 544, `voiceKeyterms.ts` 106, `context/voice.tsx` 87, `commands/voice/voice.ts`
  150, `index.ts` 21, `voiceModeEnabled.ts` 54, `useVoiceEnabled.ts` 25) → **confirmado por lectura: motor de
  grabación/WS-STT (⛔-integrador) + store-UI/`/voice`/gating (⛔-front), NINGUNO esconde comportamiento core** que el
  runtime deba portar más allá de audio→prompt. La clasificación ⛔ se sostiene por relectura, no heredada.
- **⚠ Auto-corrección (gate auto-adversarial del usuario, 2026-07-20, MISMO reproche recurrente 11–16):** mi 1er
  cierre re-leyó sólo los **dos grandes** de A 1→EOF y declaró los 8 satélites "no re-leídos esta ronda por L07"
  (apoyo en el ledger de la 1ª pasada = fallo L11). Al reproche ("¿lectura A todo EOF?") **re-leí los 8 satélites
  1→EOF esta ronda** → cero discrepancias, ninguno esconde core; ledger corregido. L07 acota el ARCHIVO (satélite de
  otra capa) pero NO exime de RE-LEERLO esta ronda cuando "A todo EOF" es el estándar — regla re-interiorizada para 18.
- **CERO discrepancias, CERO cambios de estado, 0 costuras latentes nuevas.** Única aportación: la precisión de que
  FIND-VOICE1 es B-interno/superset (no deuda A↔B) — no eleva ni baja estado.

### 4 preguntas de cierre (2ª vuelta)
1. **¿Se revisó todo cada archivo canónico?** Sí, **los 10 in-scope íntegros 1→EOF ESTA ronda**: los dos grandes
   (`useVoice.ts` 1144, `useVoiceIntegration.tsx` 1→676) + los 8 satélites motor STT/front (`voice.ts`/`voiceStreamSTT.ts`/
   `voiceKeyterms.ts`/`context/voice.tsx`/`commands/voice/*`/`voiceModeEnabled.ts`/`useVoiceEnabled.ts`); la ausencia de
   TTS re-verificada por barrido. **Sí tras auto-corrección**: el 1er cierre dejó los 8 satélites en el ledger 1ª pasada
   (fallo L11), corregido re-leyéndolos 1→EOF esta ronda al reproche del usuario.
2. **¿Se revisó todo cada archivo runtime?** Sí. `voice/{protocol,__init__}.py` + cableado `_resolve_prompt`/`_wire_tts`
   + gate `factory.py` + `RuntimeTask.audio_prompt` + `test_voice_io.py` **íntegros 1→EOF esta ronda**.
3. **¿Hallazgos exhaustivos (no superficiales)?** Sí. Cada ✅/🔀 verificada abriendo el consumidor real de B; FIND-VOICE1
   confirmado leyendo `_on_token` per-chunk + el test que no cubre el caso partido; ausencia de TTS por grep. Sin gaps
   inventados (Deuda A = 1 ítem honesto; idioma/keyterms/streaming son motor del integrador, 🔀 no gap — L10).
4. **¿Todo cubierto (nada pendiente)?** Sí. Core STT ✅; TTS superset (verificado por ausencia); FIND-VOICE1/VoR1 con
   §Plan desarrollado + xfail; motor STT ⛔-integrador y UI ⛔-front con hogar nombrado. Ningún cabo "en ningún sitio".

### VEREDICTO DE AVANCE
**✅ NADA PENDIENTE → avanzar a 18·factory.** 17·voice VALIDADA con gate 11 (código intacto, cero cambios de estado,
0 costuras latentes nuevas; FIND-VOICE1 reprecisado como B-interno/superset). 01→17 completos con gate 11.

---

## Hallazgo raíz de forma

El runtime hace **exactamente** lo que su docstring declara y lo que el comportamiento observable del canónico
exige: **audio → transcripción → prompt del turno** (`_resolve_prompt`: si hay `task.audio_prompt` y el STT
está activo, transcribe y usa el texto como prompt; ante fallo/vacío cae a `task.prompt` — la voz no tumba la
task). El modelo es agnóstico al origen del prompt. **Ese core está ✅ homologado.**

La divergencia con el canónico **no es deuda** sino **reparto de responsabilidad correcto para un runtime**:
- Todo lo que el canónico mete en `services/voice.ts` (cpal/arecord/SoX), `voiceStreamSTT.ts` (WebSocket
  voice_stream/Deepgram Nova3), `voiceKeyterms.ts`, y la normalización de idioma de `useVoice.ts` es el
  **motor STT** → responsabilidad del **integrador** que implementa `SpeechToTextProtocol`. El runtime recibe
  `AudioInput` ya grabado y devuelve el `str` ya transcrito; **ambos extremos del motor los posee el integrador**,
  así que idioma/keyterms/streaming/resiliencia son concernientes internos suyos, no seams que el runtime deba
  tipar (la escotilla `AudioInput.metadata: dict` existe si los quiere pasar).
- Todo lo que el canónico mete en `useVoiceIntegration.tsx`/`context/voice.tsx`/`commands/voice/` (keybinding
  hold-to-talk, inserción interina en el prompt-input, state-machine idle/recording/processing, `/voice`,
  gating GrowthBook+OAuth) es **terminal/UI** → responsabilidad del **front** (bff/KrakenD/Keycloak).

**El único finding genuino** (destapado al leer el cableado TTS íntegro, no vs canónico sino como invariante
que el propio runtime declara): **`_wire_tts` sanea `sanitize_output` por-chunk antes de `speak`**, de modo que
una ruta real partida entre dos `TokenEvent` **evade el choke point** — el propio docstring promete "nunca se
leen en voz alta rutas reales de infra" y el streaming per-token lo rompe. Ver **FIND-VOICE1**.

---

## Tabla feature-by-feature

### A · STT (entrada → prompt) — homologación de comportamiento

| # | Feature | Canónico | Runtime | Estado |
|---|---|---|---|---|
| A1 | **Audio → prompt del turno** | `useVoice` acumula transcripts → `onTranscript` → inserta en prompt-input | `_resolve_prompt`: `task.audio_prompt` + STT activo → `transcribe(audio, ctx)` → prompt; el modelo es agnóstico al origen | ✅ (comportamiento equivalente: el habla se vuelve el prompt) |
| A2 | **Fallback ante fallo de STT** | retry temprano (250ms) + replay de silent-drop + mensajes de error al usuario | `transcribe` lanza/da vacío → `logger.warning` + cae a `task.prompt` (la voz no tumba la task) | 🔀 (resiliencia = motor del integrador; el runtime sólo garantiza no-crash + fallback a texto) |
| A3 | **STT streaming / interinos** | streaming: `TranscriptText` interinos + `TranscriptEndpoint` final; live-preview; endpointing 300ms/utterance 1000ms; auto-finalize por-segmento (no-Nova3) | `transcribe(audio) -> str` **one-shot batch** (una task = un audio → un prompt) | 🔀 (sin terminal donde previsualizar; el integrador puede streamear internamente y devolver el final) |
| A4 | **Selección de idioma** | `normalizeLanguageForSTT` (20 langs BCP-47, name→code, fallback a `en`) desde `settings.language` → param `language` del WS | ninguno tipado; el integrador lo resuelve por su cuenta (o vía `AudioInput.metadata`) | 🔀 (motor del integrador — posee ambos extremos; escotilla `metadata` existe) |
| A5 | **Keyterms / boosting de vocabulario** | `getVoiceKeyterms`: 14 términos globales + basename de proyecto + palabras de branch + nombres de ficheros recientes (MAX 50) → query params | ninguno tipado (idem `AudioInput.metadata`) | 🔀 (motor del integrador) |
| A6 | **Formato de audio** | 16kHz / mono / 16-bit PCM `linear16` (fijado por el motor) | `AudioInput(data, mime_type="audio/wav", sample_rate, metadata)` — agnóstico al códec; lo interpreta el motor | ✅ (el runtime es correctamente agnóstico; el contrato lleva mime/sample_rate) |
| A7 | **Transcript editable antes de enviar** | inserta en el prompt-input como texto **editable**; el usuario revisa y pulsa Enter | el transcript **es** el prompt y la task corre (sin paso de revisión humana) | 🔀 (inherente a runtime no-interactivo: sin human-in-the-loop; front puede reintroducir edición) |

### B · TTS (salida por voz) — **superset del runtime, sin contraparte canónica**

| # | Feature | Canónico | Runtime | Estado |
|---|---|---|---|---|
| B1 | Existencia de TTS | **NINGUNA** (el canónico no habla; 0 hits de audio-output) | `TextToSpeechProtocol.speak/flush` + `_wire_tts` | **superset** (invención del runtime; no hay contra qué homologar feature-by-feature) |
| B2 | Derivación incremental | — | `_wire_tts` suscribe `TokenEvent` → `speak(text, ctx)` por-fragmento (baja latencia); `flush` en `DoneEvent` | superset ✅-diseño (verificado por `test_voice_io`: fragmento a fragmento sin esperar el fin) |
| B3 | Flush sólo al cerrar turno de habla | — | `DoneEvent(stop_reason="tool_calls")` **no** hace flush (corte por tools ≠ fin de habla); resto sí | superset ✅-diseño (matiz correcto: no vacía en cortes intermedios por tool-calls) |
| B4 | Subagentes mudos | — | `_wire_tts` retorna temprano si `ctx.is_subagent` (los subagentes son internos) | superset ✅-diseño (verificado por `test_subagent_does_not_speak`) |
| B5 | **Saneo por `PathPresentation`** | — | `sanitize_output(chunk)` antes de cada `speak` — "nunca rutas reales de infra en voz alta" | ❌ **FIND-VOICE1** (per-chunk → ruta partida entre chunks EVADE el choke point) |

### C · Config / gating de canal

| # | Feature | Canónico | Runtime | Estado |
|---|---|---|---|---|
| C1 | **Canal activo sii configurado** | `settings.voiceEnabled` (un flag para todo) | `VoiceConfig(stt, tts, stt_enabled, tts_enabled)`; el gate en `factory.py`: canal activo sii primitiva inyectada **y** flag on (`stt = voice.stt if voice.stt and voice.stt_enabled else None`) | 🔀 (equivalente; runtime es **más fino** — STT y TTS gobernables por separado) |
| C2 | Gating auth + kill-switch | `hasVoiceAuth` (OAuth token) + `isVoiceGrowthBookEnabled` (`tengu_amber_quartz_disabled`) + `feature('VOICE_MODE')` (ant-build) | ninguno — el runtime sólo mira "primitiva inyectada + flag" | ⛔ front (auth/killswitch/feature-flag = Keycloak/GrowthBook del front; el integrador decide si inyecta la primitiva) |

### D · Motor de grabación / streaming STT → ⛔ integrador (borde de I/O)

`services/voice.ts` (525): captura nativa cpal (macOS/Linux/Windows) + fallback SoX `rec`/arecord (ALSA);
`checkVoiceDependencies` (detección brew/apt/dnf/pacman); `checkRecordingAvailability` (guards remote/homespace,
probe WSL/arecord/ALSA-cards); `requestMicrophonePermission` (diálogo TCC); `startRecording`/`stopRecording`
(push-to-talk = `silenceDetection:false`). — `services/voiceStreamSTT.ts` (544): WebSocket a
`/api/ws/speech_to_text/voice_stream` (Anthropic, Deepgram Nova3 vía `tengu_cobalt_frost`); OAuth Bearer;
`KeepAlive`(8s)/`CloseStream`; `TranscriptText`/`TranscriptEndpoint`/`TranscriptError`; `finalize()` con 4
disparadores (post-closestream-endpoint/no-data-1.5s/safety-5s/ws-close); promoción de interino al cerrar;
workaround de zona Cloudflare; proxy/TLS/mTLS. — `services/voiceKeyterms.ts` (106): vocabulario de boosting.

**Abiertos y clasificados ⛔-integrador** (lección 02: cada uno abierto 1→EOF antes de clasificar): son el
**motor STT** que el integrador implementa detrás de `SpeechToTextProtocol`. El runtime recibe `AudioInput`
grabado y devuelve el `str`; el integrador posee grabación, WS, idioma, keyterms y resiliencia. No se portan
(hogar: integrador). No es ⛔-por-título — se leyeron íntegros y se confirmó que son borde de I/O.

### E · Terminal / UI / comando → ⛔ front (bff/KrakenD/Keycloak)

`hooks/useVoice.ts` (1144): orquestación hold-to-talk — state-machine idle/recording/processing,
`normalizeLanguageForSTT`, `computeLevel` (RMS waveform), timers de release/repeat/first-press, focus-mode
(dictado continuo, silence-timeout 5s), buffering de audio durante connect + coalescencia 32KB, early-retry,
silent-drop replay, guards de generación de sesión, analytics (`tengu_voice_*`). —
`hooks/useVoiceIntegration.tsx` (676): inserción interina en el prompt-input (anchoring prefix/suffix),
`stripTrailing`/`resetAnchor`, keybinding-handler (`voice:pushToTalk` default space, HOLD_THRESHOLD 5,
WARMUP_THRESHOLD 2, bare-char vs modifier-combo), `interimRange` (dim UI). — `context/voice.tsx` (87):
store React de estado de voz (idle/recording/processing, interim, audioLevels, warmingUp). —
`hooks/useVoiceEnabled.ts` (25): intent+auth+GB. — `voice/voiceModeEnabled.ts` (54): gating. —
`commands/voice/{voice,index}.ts` (150+21): slash-command `/voice` toggle + pre-flight (mic/deps/permission),
hint de idioma, `availability: claude-ai`, `isHidden`.

**Abiertos y clasificados ⛔-front** (lección 02/08: los grandes `useVoice.ts` 1144 y `useVoiceIntegration.tsx`
676 leídos **1→EOF**, cerrando huecos; sourcemaps base64 = no-leíble-con-razón): son **terminal/UI/comando** —
keybindings, widget de prompt-input, state-machine de grabación, `/voice`, gating de plataforma. En esta
arquitectura viven en el **front**, no en el core-lib. El *comportamiento* que sí debe existir en el runtime
(audio→prompt, gate por-canal, saneo de salida, subagentes mudos) **existe** (tablas A/B/C). No se portan.

---

## §Plan de homologación / remediación desarrollada (Deuda A)

> **Deuda A de 17 = un (1) ítem.** El core STT está homologado; el resto es reparto de responsabilidad correcto
> (integrador/front), documentado como ⛔-abierto o 🔀-inherente, **no** como pendiente. El único gap portable es
> una fuga de invariante en el TTS del runtime, destapada al leer el cableado íntegro (lección 08). **No se
> inventa Deuda A ficticia para "parecer exhaustivo"** (lección 00/03: el ledger honesto es el control de calidad).

**VoR1 — Saneo TTS resistente a frontera de chunk (FIND-VOICE1)**
- *Comportamiento:* el invariante declarado ("nunca se leen en voz alta rutas reales de infra") debe cumplirse
  aunque una ruta real quede partida entre dos `TokenEvent` (p.ej. `"/srv/sec"` + `"reto/app.log"`). Hoy
  `sanitize_output` se aplica **por-chunk** (`runtime.py:244`), así que ninguno de los dos fragmentos contiene
  el token completo `/srv/secreto` → el saneo no matchea → **la ruta se habla en claro**. El test actual
  (`test_tts_text_is_sanitized_by_presentation`) sólo prueba una ruta contenida en **un** chunk, por lo que no
  cubre el caso partido.
- *Seam:* `_wire_tts` deja de saltar directo de `TokenEvent` a `speak`. Introduce un **buffer de habla** en la
  clausura: `_on_token` acumula texto y emite a `speak` **sólo hasta el último límite seguro** (fin de
  frase/whitespace) tras sanear el acumulado; retiene la cola parcial. `_on_done` **flushea el resto**
  (saneado) antes de `flush`. El saneo se aplica **sobre el acumulado**, no sobre el fragmento crudo.
- *Firma:* dentro de `_wire_tts`, refs de clausura `buffer: list[str]` / `pending: str`; helper
  `_emit_safe(text_final: str)` que sanea y `speak`. Sin cambio en `TextToSpeechProtocol` (la primitiva sigue
  recibiendo `str` ya saneado y ya segmentado en fragmentos seguros).
- *Cableado:* `execution/local/runtime.py:243-259` (`_on_token`/`_on_done`).
- *Orden:* independiente; no toca STT ni el protocolo.
- *Test:* xfail(strict)→pass `test_tts_sanitizes_across_chunk_boundary`: un stream `["el log está en /srv/sec",
  "reto/app.log"]` con la `_RealPathPresentation` de `test_voice_io` **no** debe hablar `/srv/secreto` en
  ningún `spoken`. Hoy falla (se habla la ruta partida) → el fallo ES la evidencia del gap.

> **Nota — idioma/keyterms/streaming (A3/A4/A5) NO son Deuda A.** El motor STT lo posee el integrador en
> **ambos** extremos (construye el `AudioInput`, implementa `transcribe`, tiene `ctx`): idioma/keyterms/streaming
> son concernientes **internos** suyos, con la escotilla `AudioInput.metadata: dict` disponible si quiere
> tiparlos. Tiparlos en el protocolo del runtime sería sobre-ingeniería contra un canónico terminal-específico.
> Se documentan 🔀 (reparto de responsabilidad), no como gap.

**Cabos que aterrizan fuera de 17:** ninguno. El subsistema es autocontenido; el TTS es superset sin
dependencias transversales nuevas (el saneo reusa el contrato `PathPresentation` de 01·contracts / 03·context,
ya existente — VoR1 no añade seam transversal, sólo corrige el *cuándo/sobre-qué* se aplica).

---

## Ledger de cierre (columna "Lectura")

### Runtime
| Archivo | LOC | Lectura |
|---|---|---|
| `voice/protocol.py` | 58 | íntegro (1→EOF) |
| `voice/__init__.py` | 6 | íntegro |
| `tests/test_voice_io.py` | 208 | íntegro (define el comportamiento cableado: STT→prompt, TTS incremental+flush, saneo, subagente-mudo, no-flush-en-tool_calls) |
| `execution/local/runtime.py` (cableado voz) | — | tramos 210-262 (`_resolve_prompt` + `_wire_tts`) + 306-380 (`_run_loop`: `_wire_tts`→`_resolve_prompt`→`loop.run`) — íntegros |
| `factory.py` (`VoiceConfig` + gate) | — | tramos 63-89 (`VoiceConfig`/`RuntimeConfig`) + 210-240 (gate `stt/tts` por flag) — íntegros |
| `contracts/runtime.py` (`RuntimeTask.audio_prompt`) | — | tramo 12-32 (campo `audio_prompt`) — íntegro |

### Canónico
| Archivo | LOC | Lectura |
|---|---|---|
| `hooks/useVoice.ts` | 1144 | **íntegro 1→EOF** (archivo más grande del subsistema; barrido top-level completo, huecos cerrados — lección 08) |
| `hooks/useVoiceIntegration.tsx` | 676 | **íntegro 1→676** (código; línea 677 = sourcemap base64 = no-leíble-con-razón) |
| `services/voiceStreamSTT.ts` | 544 | íntegro → ⛔ integrador (motor STT WebSocket) |
| `services/voice.ts` | 525 | íntegro → ⛔ integrador (motor de grabación cpal/SoX/arecord) |
| `services/voiceKeyterms.ts` | 106 | íntegro → ⛔ integrador (boosting) |
| `commands/voice/voice.ts` | 150 | íntegro → ⛔ front (comando `/voice` + pre-flight) |
| `context/voice.tsx` | 87 | íntegro (código 1-88; resto sourcemap) → ⛔ front (store de estado UI) |
| `voice/voiceModeEnabled.ts` | 54 | íntegro → ⛔ front (gating GrowthBook/OAuth) |
| `hooks/useVoiceEnabled.ts` | 25 | íntegro → ⛔ front |
| `commands/voice/index.ts` | 21 | íntegro → ⛔ front (registro de comando) |

### §Nota de honestidad
- Los dos archivos grandes (`useVoice.ts` 1144, `useVoiceIntegration.tsx` 676) se leyeron **1→EOF**, no por
  hitos (lección 08); los sourcemaps base64 finales se declaran **no-leíble-con-razón** (data generada), no ⛔.
- **La ausencia de TTS en el canónico se VERIFICÓ con barrido** (`text-to-speech|tts|synthesi[sz]|speak(|
  audio.?out|speechSynthesis|say(`) sobre todo `src`, no se asumió: 0 hits de audio-output. Por eso el TTS del
  runtime se clasifica **superset** (sin contraparte), no ❌-no-portado.
- **Los 5 archivos de motor STT (`voice.ts`/`voiceStreamSTT.ts`/`voiceKeyterms.ts` + los grandes) se abrieron
  íntegros ANTES de clasificarlos ⛔** (lección 02): el veredicto ⛔-integrador/⛔-front es tras leer, no por
  título. Al leer `voiceStreamSTT.ts` íntegro se confirmó que es el motor (WS/OAuth/Deepgram) y no esconde
  comportamiento core del runtime; al leer `useVoice.ts` íntegro se confirmó que retry/replay/state-machine son
  orquestación terminal, no lógica que el runtime deba portar.
- **FIND-VOICE1 se destapó leyendo el cableado TTS del runtime íntegro** (`_wire_tts` per-chunk), no comparando
  con el canónico (que no tiene TTS). Es un invariante que el **propio runtime declara** y su implementación
  viola en frontera de chunk. No es padding: el test actual no cubre el caso partido.
- **Deuda A = 1 ítem** honestamente. No se inventaron gaps de idioma/keyterms/streaming como Deuda A porque el
  motor STT lo posee el integrador en ambos extremos (lección 00: no confundir "el canónico tiene más código"
  con "el runtime tiene un gap" cuando ese código es responsabilidad de otra capa).

### 4 preguntas de cierre
1. **¿Se revisó todo cada archivo canónico?** Sí. Los 10 archivos del árbol voice (`voice/`, `services/voice*`,
   `hooks/useVoice*`, `context/voice.tsx`, `commands/voice/*`) leídos íntegros; los dos grandes 1→EOF. Los
   consumidores del flag `voiceMode` en PromptInput/keybindings/components (grep amplio) son **UI-terminal del
   front**, fuera del carve-out global del README (UI/ink/terminal), no del árbol voice — no in-scope-core.
2. **¿Se revisó todo cada archivo runtime?** Sí. `voice/{protocol,__init__}.py` + `test_voice_io.py` íntegros;
   el cableado en `execution/local/runtime.py` (`_resolve_prompt`/`_wire_tts`/`_run_loop`), el gate en
   `factory.py` y el campo `audio_prompt` en `contracts/runtime.py` leídos en sus tramos exactos.
3. **¿Hallazgos exhaustivos (no superficiales)?** Sí. Se enumeró **cada** feature canónica (grabación, streaming
   STT, keyterms, idioma×20, state-machine, focus-mode, retry/replay, prompt-input, keybindings, `/voice`,
   gating) y se clasificó una a una. El único gap portable (FIND-VOICE1) salió de leer el cableado TTS íntegro,
   con seam/firma/cableado/test desarrollados (lección 05). La ausencia de TTS canónico se verificó con grep,
   no se asumió.
4. **¿Todo cubierto (nada pendiente)?** Sí. Core STT ✅; TTS superset documentado; motor STT ⛔-integrador y
   terminal/UI ⛔-front, **abiertos y clasificados con razón** (nombran su hogar: integrador / front); Deuda A =
   VoR1 con §Plan desarrollado + xfail. Ningún cabo queda "en ningún sitio".

---

## Targets de test de homologación (xfail(strict))
- `test_tts_sanitizes_across_chunk_boundary` (VoR1 / FIND-VOICE1) — **xfail**: hoy `_wire_tts` sanea per-chunk;
  una ruta partida entre dos `TokenEvent` se habla en claro. Passing = invariante de saneo restaurado.
- **Passing** (comportamiento ya homologado, codificado en `test_voice_io.py`): `test_stt_transcription_arrives_as_prompt`
  (A1) · `test_stt_disabled_uses_text_prompt` / `test_stt_without_audio_keeps_text_prompt` (C1 gate) ·
  `test_tts_speaks_each_chunk_incrementally_then_flush` (B2) · `test_tts_disabled_does_not_speak` (C1) ·
  `test_tts_text_is_sanitized_by_presentation` (B5 caso mono-chunk) · `test_subagent_does_not_speak` (B4) ·
  `test_tts_no_flush_on_tool_call_turn` (B3).
