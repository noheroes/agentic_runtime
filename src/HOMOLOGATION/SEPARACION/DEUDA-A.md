# DEUDA-A — rollup transversal de CORE-GAPs (A3.DA)

> **Qué es:** el backlog consolidado de **toda** la brecha A↔B real (canónico ↔ runtime) que los 18 ciclos A3
> repartieron por categoría. No re-analiza: **re-ordena por dependencia** y resuelve lo que ninguna categoría podía
> resolver sola. **Eje rector de este rollup = el hilo de identidad** (`00-LEGEND §2.4`, `00-BLUEPRINT §2.1` 🟨).
>
> **Qué NO es:** DEUDA-B (higiene interna del runtime → `DEUDA-B.md`, A3.DB) · el catálogo de batteries
> (→ `BATTERIES.md`, A3.CAT) · el plan de construcción (→ A-CIERRE). Ver **§4**.

---

## 0. Tesis del rollup

### 0.1 Declaración de lectura (L01/L03 — honestidad primero)

**⚠ Corrección de esta misma sección (aplicada al ser interrogada por el gate del usuario).** La primera redacción
decía «leídos ÍNTEGROS 1→EOF **este ciclo**: `00-LEGEND` · `00-BLUEPRINT` · `00-INTEGRADORES` · `SEAMS` ·
`SKELETON-REPORT`». **Falso tal como estaba escrito.** Esas lecturas ocurrieron en un tramo del ciclo que después
fue **compactado**: su contenido **no estaba en el contexto** cuando se redactó este documento — lo que había era
un **resumen que afirmaba** que se habían leído. Redactar el rollup apoyándose en ese resumen y presentarlo como
«leído 1→EOF por mí» es precisamente la omisión-vestida-de-evidencia que L09 vigila.

> **Lección de método destilada (nueva, no estaba en las 11):** *tras una compactación, una lectura 1→EOF del
> tramo perdido NO se puede seguir invocando como evidencia propia — o se re-abre, o se declara heredada.*

**⚠⚠ Segunda corrección — TRAMO DE RE-VERIFICACIÓN (autorizado por el usuario, ejecutado tras el gate).** Los
tres documentos declarados «de segunda mano» arriba **se re-abrieron 1→EOF**, y por primera vez en todo el ciclo
se abrieron **archivos de código del runtime**. Estado real de la evidencia:

- **Re-abiertos 1→EOF en el tramo de re-verificación (evidencia PROPIA):** `SKELETON-REPORT.md` (138) ·
  `SEAMS.md` (435) · `00-INTEGRADORES.md` (207) · `00-LEGEND.md` (159) · `00-BLUEPRINT.md` (190) ·
  `12-cap-skills.md §2.4` (229-268). **Los 5 documentos transversales están ahora leídos 1→EOF por mí**; ninguno
  queda heredado del tramo compactado.
- **Código abierto 1→EOF (evidencia PROPIA, primera vez del ciclo):** `factory.py` (268) ·
  `execution/local/runtime.py` (435) · `execution/agents.py` (67) · `execution/fork/__init__.py` (97) ·
  `capabilities/mcp/token_storage.py` (66) · `capabilities/memory/store.py` (139) ·
  `capabilities/memory/provider.py` (103). **Por rango:** `capabilities/skills/store.py` 1-60 ·
  `context/tool_use.py` 28-57 · `loop/agent_loop.py` 170-199 · `factory.py` 195-244 (re-lectura del ensamblador).
- **Resultado del contraste:** de las **~20 anclas `archivo:línea`** que este doc citaba de segunda mano, **todas
  las verificadas resultaron exactas** (detalle en §0.1b). Dos afirmaciones se corrigieron por lectura directa
  (ID-5 cableado; alcance de §3) y **dos hallazgos nuevos** aparecieron que ningún ciclo tenía (§0.1b).
- **Sigue siendo de segunda mano — el ÚNICO perímetro que queda:** todo lo que este doc atribuye a los **18
  `SEPARACION/NN-*.md`** (§0.2, §1.2, §2 en sus partes no ancladas a código) y a **A2.5** más allá de lo que
  `SKELETON-REPORT` dice de sí mismo. **No es subsanable dentro de un ciclo** (≈795 KB ≈200k tokens); su
  mitigación real es que **A3.CAT y A-CIERRE los reabran por categoría**, no que este doc finja haberlo hecho.
- **Leídos en el tramo original, por rango exacto:** `00-LEGEND` 108-152 · `00-BLUEPRINT` 100-129 y 175-185 ·
  `11` 42-59 y 175-234 · `12` 64-81 y 182-228 · `13` 42-69 y 190-238 · `14` 88-107 y 238-295 · `15` 39-72 y
  163-198 · `16` 125-150 · `17` 168-268 · `18` 248-309 · `PLAN.md` 102-132 **truncado a 180 caracteres/línea**.

### 0.1b Qué cambió por leer el código (y qué no)

**Confirmado de primera mano, ancla por ancla** (todas exactas):

| ancla citada | verificación directa |
|---|---|
| `runtime.py:208-209` autogen | `session_id = task.session_id or f"sess_{uuid…}"` / `user_id = task.owner_id or f"user_{uuid…}"` ✅ |
| `_build_child:205-218` | exacto (`agent_id` :205, seed de permisos 214-217) ✅ |
| `runtime._persist:424` `"anon"` | `user_id = ctx.user_id or "anon"` ✅ |
| `runtime.py:430` snapshot-overwrite | `await self._storage.upload(key, session.model_dump_json()…)` ✅ (`CG-STOR-2`) |
| `token_storage.py:24` | `base = f"{user_id}/mcp/{server_name}"`, default `user_id="mcp"` (:22) ✅ |
| `factory.py:149-155` McpProvider | **no pasa `user_id=`** ⇒ fuga `mcp/mcp/<srv>` ✅ **end-to-end** |
| `skills/store.py:35-40` | `prefix="skills"` fijo sin identidad + `_key` sin sanitizar ✅ |
| `memory/store.py:106-110` | `_scope = agent_id or "main"`; `memory_dir = self._root / scope` **sin guard** ✅ |
| `memory/provider.py:52-63` | `f"{user}/{agent}"`, `user = context.user_id or "anon"` ✅ |
| `fork/__init__.py:69` | `agent_id = f"agent_{uuid4().hex[:12]}"` ✅ |
| `tool_use.py:39-42` | `user_id`/`agent_id`/`is_subagent`/`subagent_depth`; **no hay `subagent_type`** ✅ |
| `agents.py:26` | `subagent_type: str` es el primer campo de `AgentDefinition` ✅ |
| `runtime.py:342` | `if task.subagent_type and self._agent_resolver is not None:` ✅ |
| `agent_loop.py:181-183` | `logger.warning(… no hay model_caller …)` + `return` ✅ (K8) |
| `factory.py:219` S1 / `:83` slot muerto | `model_caller=config.model_caller` en :219; `models: ModelsConfig` en :83 **nunca consumido** ✅ |
| `factory.py:218-240` sin `runner=` | confirmado: no existe el argumento ⇒ **K7/S18 sin poblar** ✅ |
| `create_runtime` 243-267 | cero validación ⇒ **K8** ✅ |
| `runtime.py:228/:248/:257` voz | `stt.transcribe(audio, ctx)` / `tts.speak(text, ctx)` / `tts.flush(ctx)` ✅ (ID-6b) |
| `runtime.py:239` / `:333` | `if self._tts is None or ctx.is_subagent` / `bus = self._make_bus(task_id, on_event)` ✅ |

**Dos correcciones que la lectura directa impuso:**
1. **ID-5 NO es un gap de cableado.** `agent_resolver=config.agent_resolver` **sí está cableado**
   (`factory.py:237`), y `runtime.py:341-353` lo consume. El gap de ID-5 es **exclusivamente la clave de scope**
   (el `subagent_type` no llega al `ToolUseContext` ni a `MemoryStore._scope`), no la ausencia del resolver.
   La redacción original no lo afirmaba al revés, pero se prestaba a leerse así; queda acotada.
2. **§3 mezcla dos orígenes.** `00-INTEGRADORES §1` contiene **sólo la espina A1.7**: `OI-1..OI-23` +
   `OI-M1..M8` + `OI-EVT-1..4` (trazabilidad explícita en su §1). Los `OI-STOR-A/B/C`, `OI-MCP-A`, `OI-FAC-1`,
   `OI-VOICE-1..5` y `OI-D` que §3 cita **no están vertidos allí** — viven en el §2.5 de su `NN-*.md`.
   `00-INTEGRADORES §3` lo dice: «resto A3». **Cabo emitido a A3.CAT / A-CIERRE: verter los `OI-*` de los 12
   ciclos A3 restantes a `00-INTEGRADORES §1`.** §3 de este doc queda anotado en consecuencia.

**Cuatro hallazgos NUEVOS que ningún ciclo por-categoría tenía** (emergen sólo al cruzar dos fuentes; **H-3/H-4**
salen del cotejo 1:1 de §2.8 contra `00-BLUEPRINT §2.1` leído 1→EOF):
- **H-1 (agrava ID-1, 🔒).** El autogen de `user_id` no es inocuo: `MemoryProvider._scope` keya la memoria por
  `f"{user_id}/{agent}"` (`provider.py:61-63`) y `user_id` es **un uuid nuevo por dispatch** cuando el integrador
  no inyecta `owner_id` (`runtime.py:209`). Consecuencia observable: **un runtime sin integrador escribe la
  memoria del agente principal en un directorio distinto en cada despacho** — la memoria nunca se recupera. El
  autogen no es «un default para que el runtime corra solo»: **rompe silenciosamente la persistencia que la
  categoría 13 da por funcionando.** Refuerza que ID-1 va primero.
- **H-2 (acota K3/ID-4, alcance).** El guard-path no falta «en 3 sitios» de forma simétrica: en memoria el
  segmento peligroso (`user_id`) **entra por la frontera del integrador** y se une con `Path.__truediv__`, donde
  un segmento absoluto **descarta el root entero** (`Path("/data") / "/etc/x" == Path("/etc/x")`) — es peor que
  un `..`. En skills el segmento es el **nombre del skill**. Son dos superficies de confianza distintas con **un
  mismo helper**, y la prueba de ID-4 debe cubrir el caso absoluto, no sólo `..`.
- **H-3 (CORE-GAP nuevo, hogar `05·execution`).** `LocalAgentRuntime.resume(agent_id, message)` — firma que
  `00-INTEGRADORES §1.3` declara como obligación del integrador — **no existe** (`runtime.py` 1→EOF: la superficie
  pública es `startup`/`shutdown`/`dispatch`/`stream`/`status`/`cancel`/`result`). `05·E26` se difirió «a 11/15» y
  **ni 11 ni 15 lo reclamaron**: se cayó entre dos categorías. Es exactamente el tipo de agujero que un rollup
  transversal existe para encontrar. → §2.8.
- **H-4 (acota ID-5).** El touchpoint 8 de `00-BLUEPRINT §2.1` (discovered-set MCP por `agent_id`, `09·E5`) sufre
  el **mismo** `agent_id` inestable que la memoria, pero el campo *cableado* de ID-5 sólo toca
  `provider.py:52-63`. La firma de ID-5 ya sirve; falta el segundo consumidor. → §2.8.

**No cambió nada de esto:** la clasificación de los 8 keystones, el orden de ataque, ni el saldo por destino. La
lectura de código y de los 5 transversales **confirmó** el rollup en su estructura; lo que corrigió fueron dos
afirmaciones (ID-5, §3), una sobre-afirmación (§2.8 «todos los touchpoints») y añadió 4 hallazgos.

**Leídos POR SECCIÓN (§2.3 CORE-GAPs + secciones de identidad §0.1/§0.2 + §2.4 donde el ciclo la usó para
des-contar):** los **18** `SEPARACION/NN-*.md`. **Ninguno de los 18 se leyó íntegro en ningún tramo de este
ciclo.** Motivo declarado y verificable:
los 18 suman ≈795 KB ≈200k tokens — no caben en un contexto. El `SIGUIENTE` autorizó explícitamente este recorte
**a condición de declararlo**, y queda declarado. **Consecuencia asumida:** si un CORE-GAP existe en un `NN-*.md`
**fuera** de su §2.3 y de sus notas-identidad, este rollup **no lo tiene**. No afirmo que no exista; afirmo que no
lo busqué fuera de esas secciones. Los ciclos por-categoría sí leyeron esos docs 1→EOF al escribirlos, y §2.3 es
por convención del `00-LEGEND` el lugar donde cada ciclo depositó sus CORE-GAPs — pero eso es **confianza en el
doc**, no verificación mía (L11: validar completitud ≠ confirmar el doc). **Este rollup no revalidó A↔B: es una
consolidación de las validaciones de los 18 ciclos.**

**No leído en ningún tramo:** `PLAN.md` íntegro (sólo §4 A3.x y §7 checklist) · ningún tracker `../*.md` ·
`DEUDA-B-transversal.md` (es la lectura de A3.DB) · el resto del código del runtime fuera de los 11 archivos de
§0.1. Las anclas `archivo:línea` **no listadas en la tabla de §0.1b** siguen siendo **citas de los ciclos**, no
re-verificaciones mías.

### 0.2 Inventario y su honestidad

| doc | CORE-GAPs en §2.3 | forma |
|---|---|---|
| 01·contracts | 4 | CTR-08/12/14 + CTR-09 |
| 02·loop | 7 | GAP-L1/L1b/L2/L3/L4/C4/G1 (+4 celdas plegadas A4/C10/F10/F2) |
| 03·context | 5 | FIND-CTX1/2 + GAP-CTX2/3/4 |
| 04·modes | **0** | declarado sin CORE-GAP propio (anti-padding L10) |
| 05·execution | 6 clusters | fork(E12/13/14) · lifecycle(E33/35/36) · max_turns · kill · registry · trailer |
| 06·hooks | 8 | CG-HOOK-1..8 |
| 07·events | **20** | B1·**B2**·C3·D1/D2/D3/D5·E1/E2/E3/E5·F0/F1/F2·G1/G2/G3·H1·I1·J3 |
| 08·signals | 9 | CG-SIG-1..9 |
| 09·tools-infra | 8 | gate-por-input · concurrencia · señales · new_messages · deferral · path-guards · MCP-deny · shape/budget |
| 10·tools-native | 10 | READSTATE(keystone) · EDITGUARDS · GAP-NATIVE-2 · READ · R4 · BASH · B12/R9 · BG · G3/R11 · §K |
| 11·mcp | 20 | CG-MCP-1..20 |
| 12·skills | 15 | CG-SKILL-1..15 |
| 13·memory | 10 | CG-MEM-1..10 |
| 14·plan | 11 | CG-PLAN-1..11 |
| 15·storage | 5 | CG-STOR-1..5 |
| 16·models | 9 | FIND-MODELS1/2/3/4/5-7/8/9/10/11 |
| 17·voice | 5 | CG-V1..V5 |
| 18·factory | **1** | CG-FAC-1 (declarado uno a propósito: 18 es convergencia) |

**≈153 entradas** *(era ≈152; +1 por la inversión `07·B2` en A-CIERRE·P4″)*. El número es **blando y así se declara**: 05 agrupa en clusters (6 entradas cubren 11 features),
02 pliega 4 celdas dentro de sus 7, y varios IDs son **el mismo gap con dos nombres** — la §1.1 los unifica
explícitamente. **No sumar esta columna como métrica de trabajo**: la unidad de trabajo real es el **keystone**,
no la fila.

### 0.3 Las tres tesis

**T1 — La brecha no es plana: 8 keystones gobiernan ≈2/3 del inventario.** Un backlog de 152 filas ordenado por
categoría es inaccionable y engaña sobre el coste. Ordenado por dependencia, ocho piezas desbloquean el resto; las
demás son trabajo lineal una vez que existen. §1 está ordenada así, no por categoría.

**T2 — El hilo de identidad es transversal y HOY es mímica, no diseño.** El runtime **autogenera** `user_…`/`sess_…`
(`runtime.py:208-209`, `_build_child:205-218`), literaliza scope (`user_id="mcp"`), y une segmentos crudos a rutas
(3 sitios). Ningún ciclo por-categoría podía arreglarlo: cada uno veía un touchpoint. Es **el** trabajo que este
rollup existe para hacer → §2. Bajo `mimica-no-desfusion`: el autogen **no** es "default razonable", es plomería
de identidad horneada en el núcleo que el `00-LEGEND §2.4` prohíbe.

**T3 — Tres de los ocho keystones son de SEGURIDAD, no de features.** GAP-02 (sin modo de permiso: `plan` no
confina, memory-write no está scopeado, skills auto-allow no gatea), el guard-path unificado (traversal en 3
repos), y el scope de tokens OAuth (`mcp/mcp/<srv>` = fuga multi-usuario **confirmada por el ensamblador**). Estos
tres tienen prioridad sobre cualquier funcionalidad.

---

## 1. Consolidación keystone-first

### 1.1 Los 8 keystones (K1-K8) — orden de construcción

Cada keystone lista **quién lo posee** (hogar canónico, para que no se resuelva dos veces), **qué desbloquea**, y
**quiénes son la misma cosa con otro nombre** (unificaciones — la aportación propia de este rollup).

---

**K1 · `PermissionContext.mode` — los modos de permiso (= GAP-02)** — 🔒 seguridad
- **Hogar:** `06·CG-HOOK-8`. Nadie más lo implementa.
- **Es lo mismo que:** `01·CTR-08` · `03·GAP-CTX2` · `09·FIND-TOOL2` ("el mayor gap de 09") · `10·B2` ·
  `12·CG-SKILL-3` · `13·CG-MEM-9` · `14·CG-PLAN-1`. Y es **la totalidad** de 04·modes (que por eso cerró con 0
  CORE-GAPs propios y remitió aquí).
- **Qué falta:** `PermissionContext` no tiene `mode` (`default`/`acceptEdits`/`plan`/`bypassPermissions`). Hoy se
  simula con `app_state.native["plan_mode"]` = hack (DEUDA-B `B-02`).
- **Desbloquea:** el candado read-only de plan mode con exención del plan-file (`is_session_plan_file`, hoy
  pre-cableada sin consumidor) · el carve-out de escritura memory-scoped (hoy `initial_allowed_tools` concede
  `write_file` **en bloque**, no path-scoped) · el auto-allow de Skill sólo si `_skill_has_only_safe_properties` ·
  el gate FQ de tools MCP · `CG-PLAN-7` · `CG-PLAN-10` (restaurar-modo-previo).
- **Orden:** **primero de todo el rollup.** 8 categorías lo esperan y tres de sus consumidores son de seguridad.

---

**K2 · El hilo de identidad — `id opaco + repo genérico`** — 🔒 seguridad (parcial)
- **Hogar:** **este rollup** (`00-BLUEPRINT §2.1` lo dejó 🟨 apuntando aquí; `00-BLUEPRINT §1.4` sigue ⬜ por esto).
- **Es lo mismo que:** `01·CTR-05` · `03·A+`/`OI-D` · `05·E30`/`E9`/`E5`/`E7`/`E3` · `07·B3`/`K5` · `09·G6`/`E5` ·
  `11·CG-MCP-16` · `12·§0.2` · `13·CG-MEM-1`/`CG-MEM-3` · `14·§0.2` · `15·CG-STOR-1`/`CG-STOR-3` · `16·B10` ·
  `17·CG-V3` · `18·A2`/`C-cap5`.
- **Desarrollo completo (L05, 6 campos × 7 piezas):** → **§2**. Es el cuerpo de este ciclo.
- **Orden:** ID-1..ID-4 **junto a K1** (comparten el borde de seguridad); ID-5..ID-7 después de K4.

---

**K3 · Guard-path unificado (`sanitizePathKey`)** — 🔒 seguridad
- **Hogar:** `15·CG-STOR-3` (un solo helper; los ciclos verificaron que son **espejo exacto**, no parecidos).
- **Es lo mismo que:** `13·CG-MEM-1` (`<user>/<agent>` crudos, `store.py:106-110`) · `12·§0.2` (`skills/<name>`
  crudo) · `11·CG-MCP-16` (parte sanitize) · `15` propio (`FilesystemStorage._path` usa `startswith` ⇒ vulnerable
  a hermano-prefijo `/data/root-evil`; sin `\0`/`..`/absolutos/backslashes; `_write` hereda umask).
- **Regla dura de este rollup:** **un helper, cuatro consumidores.** Implementarlo cuatro veces es el fallo que la
  organización por categoría inducía; nombrarlo aquí es la razón de existir del rollup.
- **Orden:** con K2·ID-3/ID-4 (misma zona, misma prueba).

---

**K4 · Identidad en el `Event` BASE — atribución del stream**
- ⚠ **Forma corregida en A-CIERRE·P0** (ejecuta `BATTERIES §6·CAT-h10`; la decisión es de `DEUDA-B §7.2`, que la
  tomó y **no vino a aplicarla aquí**). Este keystone se titulaba *«Sobre del evento (`EventEnvelope`)»*. **Esa forma
  está descartada, por razón técnica verificada:** `EventBus.emit` despacha por **`type(event)`**
  (`bus.py:40`, `self._handlers.get(type(event))`) y `subscribe(TokenEvent, handler)` es la API tipada
  (`protocol.py:20`) ⇒ un envelope que *envuelva* al evento **colapsa todos los tipos en uno y rompe el despacho
  tipado**, que es lo mejor que hoy tiene el bus. La forma vigente es **añadir los campos de identidad al `Event`
  base**, que **todo** subtipo hereda sin tocar `emit`, `subscribe` ni ningún handler existente. **Viabilidad
  verificada:** `Event` es un frozen dataclass **sin campos** (`protocol.py:9-11`) y los **5** subtipos tienen
  **todos** sus campos con default (`event_types.py:17-43`) ⇒ añadir campos con default al base no rompe el orden
  de dataclass ni ninguna construcción existente. *Regla que este error deja escrita: una decisión que corrige un
  doc cerrado se aplica **EN** ese doc, no sólo se anota en el que la toma.*
- **Hogar:** `07·events` (anclas `07·B2`, `07·B3`, `GAP-EVT5`); **forma decidida en `DEUDA-B §7.2`**.
- **Estado del gap tras §7.2:** `07·B2` **no estaba equivocado — estaba condicionado a un seam que aún no existe.**
  Hoy las dos únicas vías públicas de recibir eventos son `dispatch(task, on_event=…)` y `stream(task)`, donde **el
  consumidor es quien despacha** (conoce el `task_id` por retorno) ⇒ la atribución implícita se sostiene *para los
  seams de hoy*. El `EventBus` se crea **dentro** de `_run_loop` (`_make_bus`, privado) y **no se expone por ningún
  accesor**: bajo Filosofía B ese seam de suscripción **tiene** que existir, y en el instante en que exista un
  handler verá eventos de **todas** las tasks del proceso. Por eso se cierra como **CORE-GAP condicionado**.
- **Es lo mismo que:** `17·CG-V2` (habilitador declarado; `SpeechSink` no puede saber quién habla).
- **Objeción formal registrada por 17, que este rollup ADOPTA:** `07·B2` cerró `parent_tool_use_id` como 🔀
  T2-BASE-MECANISMO argumentando "atribución **implícita** por bus per-task (`_make_bus(task_id)`)", y `07·B3`
  mandó `session_id`/`uuid` al serializador wire porque "el bus ya está scoped in-proc". Ambas premisas suponen
  que el consumidor **o** posee el handle del bus per-task **o** está fuera de proceso. `SpeechSink` es el tercer
  caso — **in-proc, suscrito por la costura pública, sin `ctx` y sin wire** — y ahí la atribución implícita no
  existe. **Veredicto del rollup: `07·B2` se re-abre.** No afirmo que 07 concluyera mal; afirmo, como afirmó 17,
  que concluyó **sin este consumidor sobre la mesa**, y que bajo Filosofía B (batteries externas suscritas por la
  costura pública) ese consumidor es el caso normal, no el raro.
- **Desbloquea:** toda battery de salida externa al núcleo (voz, front, telemetría, BFF multi-tenant) · la mitad
  de salida de `17·CG-V1` (bloqueada explícitamente por esto) · `16·FIND-MODELS3` (eventos thinking).
- **Orden:** antes de la extracción de voz; después de K1/K2-núcleo.

---

**K5 · `ToolResult` enriquecido — `new_messages` + `structured`/`output_schema`**
- **Hogar:** `01·contracts` (el shape) + `09·tools-infra` (el transporte).
- **Es lo mismo que:** `11·CG-MCP-4` (content image/audio/blob/resource — sin canal tipado degrada a
  persist-a-disco+texto) · `11·CG-MCP-5` (=`09·A25`, structuredContent+mcpMeta) · `12·CG-SKILL-5` (entrega del
  SKILL.md expandido como mensajes transitorios) · `09·new_messages`.
- **⚠ Discrepancia de tier no resuelta, declarada:** 11 y 12 se refieren a `B-new_messages` como "**DEUDA-B**
  transversal", pero **lo consumen desde CORE-GAPs**. Un prerrequisito de tres CORE-GAPs no puede ser higiene
  interna. Precedente: `07·§2.3` ya corrigió el tier de `B-usage` de DEUDA-B → CORE-GAP por este mismo
  razonamiento. **No lo reclasifico unilateralmente aquí** — lo dejo como **decisión explícita de A3.DB**, que es
  el ciclo que posee la frontera A/B. Registrado para que no se pierda entre los dos rollups.
- **Orden:** K5 antes de `CG-MCP-4/5` y de `CG-SKILL-5` (dependencia dura declarada por ambos).

---

**K6 · Motor de compactación (no portado)**
- **Hogar:** `01·CTR-09` (`CompactionProvider`, el seam) + `02·GAP-L4` (el motor).
- **Cara aguas-abajo en 4 categorías:** `compact_context()` devuelve `[]` y **no tiene ningún caller de prod** en
  memory, plan, skills y mcp. Los cuatro ciclos verificaron esto por grep y **los cuatro rehusaron contarlo como
  B-orphan propio** (L10) — correcto, y este rollup lo ratifica: es **un** gap con cuatro caras, no cinco gaps.
- **Es también:** `14·CG-PLAN-4` (preservar el plan a través de la compactación) · `16·FIND-MODELS11` (overflow no
  cableado; models aporta la **detección**, el ruteo es 02) · `02·B1-B9/C9/D1` · `07·H1` (`CompactBoundaryEvent`).
- **Nota de forma:** el destino es la **battery `compaction`** (`00-BLUEPRINT §3`), ya validada como composable
  por A2.4 (S9). El gap A↔B es que el motor no existe, no que falte el seam.

---

**K7 · Fork completo + `SubagentRunnerProtocol` poblado**
- **Hogar:** `05·execution` (fork E12/E13/E14 + lifecycle) · el cableado es `18·B-runner-wiring` (DEUDA-B) sobre
  el patrón DI ya fijado por **A2.5** (`SKELETON-REPORT`: S18 ✅ cableada en el skeleton, **sin poblar** en el
  runtime real — `SEAMS §S18` = "sin-poblar (crítico)").
- **Desbloquea:** `13·CG-MEM-2` (auto-extracción por fork al cierre de turno — "la mayor brecha" de 13, necesita
  fork *cache-safe*) · `12·CG-SKILL-8` (fork-dispatch en la tool) · `14·CG-PLAN-2` (agentes built-in
  `Explore`/`Plan` read-only; sin ellos el reminder de 5 fases nombra tipos que no resuelven ⇒ **instrucción core
  no-funcional**) · `14·CG-PLAN-5` (heredar el plan) · `10·F1` (`Agent` tool) · `11·CG-MCP-20` (cleanup per
  `agent_id`).
- **Nota:** hoy **todo** spawn de subagente devuelve `ToolResult.error`. Es el gap con mayor ratio
  impacto/esfuerzo del inventario: el mecanismo existe, el ensamblador no lo puebla.

---

**K8 · Fail-fast de la composición**
- **Hogar:** `18·CG-FAC-1` (único CORE-GAP de 18, y el ciclo declaró que es honesto que sea uno).
- **Qué falta:** `create_runtime(RuntimeConfig())` devuelve hoy un runtime **silenciosamente no funcional** — sin
  `model_caller`, `AgentLoop.run` hace `logger.warning` + `return` (`agent_loop.py:181-183`). El canónico hace
  fail-fast (`entrypoints/init.ts:65` → `ConfigParseError` → `gracefulShutdownSync(1)`).
- **Por qué es keystone bajo B:** con batteries componibles, el número de configuraciones inválidas explota. Se
  amplía a validar `Battery.requires()` (S28) — **el mismo mecanismo, no dos**.
- **Orden:** **último de los keystones pero antes de las Fases C-D**: es la red que hace que los errores de
  composición de todo lo anterior sean visibles al ensamblar, no al primer turno.

---

### 1.2 El resto, por destino (no por categoría)

Agrupado por **quién lo construye**, que es la pregunta que A3.CAT y A-CIERRE necesitan responder.

**(a) BASE — contratos y mecanismo del núcleo** *(lo que ningún integrador puede aportar)*
- **Señales/cancelación — `08·CG-SIG-1..9`** (bloque coherente, casi keystone): `reason` en el abort · árbol de
  hijos · `interrupt_behavior` · cancelación in-flight · `aborted` rico · señal interrumpible · `interrupt()`
  público · `AbortScope.on_abort` (que `11·CG-MCP-20` consume) · separación work-level vs agent-level. Cruza
  `16·FIND-MODELS4` (abort roto, tipo de señal equivocado) y `05·E15` (kill ⇒ pérdida de trabajo).
- **Eventos — `07`, 19 entradas** menos las plegadas en K4/K5/K6: taxonomía de error (`D5`, = `16·FIND-MODELS10`),
  `usage` completo (`B-usage`, **ya recalificado a CORE-GAP por 07**, = `16·FIND-MODELS2` — mismo shape), init,
  terminales.
- **Loop — `02`:** `GAP-L1`/`L1b`/`L2`/`L3`/`C4`/`G1` + `05·E16` (max_turns) + `05·E18/E19` (trailer).
- **Contexto — `03`:** `FIND-CTX2`, `GAP-CTX3`, `GAP-CTX4` (`FIND-CTX1`→10·R0, `GAP-CTX2`→K1).
- **Ejecución — `05`:** lifecycle `E33/E35/E36` · registry enriquecido `E9` · `E15` · **`E26`/`H-3` (`resume` ausente — CORE-GAP nuevo con hogar en 05, ver §2.8)**.
- **Infra de tools — `09`:** concurrencia (que consume `is_concurrency_safe` de `CG-MCP-3`) · señales · deferral
  (que `CG-MCP-2` cierra: **`09·GAP-TOOL3` queda cerrado por 11**) · safety-fs · MCP deny · shape/budget.
  ⚠ **Movido desde `(b) BATTERY` en A-CIERRE·P0** (ejecuta `BATTERIES §6·CAT-h2`): `09·§2.2` declara estos ítems
  **base-mecanismo/costura** de forma explícita — son el transporte y las guardas sobre los que *cualquier* tool
  corre, no comportamiento componible. Los de **`10`** sí son battery y se quedan en (b). El error era de archivo,
  no de clasificación: ninguna categoría lo había clasificado mal, este rollup lo archivó bajo el epígrafe equivocado.
- **Modelos — `16`:** thinking/effort no cableados (`FIND-MODELS1`, "la causa raíz de la categoría: el motor tiene
  la ruta, el puente nunca la puebla") · `FIND-MODELS9` structured outputs (**sub-ítem sin remediación en el
  tracker; 16 lo registró como CORE-GAP nuevo**) · `FIND-MODELS8` betas core.
- **Storage — `15`:** `CG-STOR-2` (durabilidad incremental del transcript: hoy snapshot-overwrite por completion,
  `runtime.py:430` ⇒ crash mid-turn pierde el turno) · `CG-STOR-4` (`download_range`) · `CG-STOR-5` (frontera
  `StorageContract`↔`StorageProtocol` + adaptador — **no es gap de forma, es clarificación de seam**).
- **Voz — `17·CG-V1`** (la voz está horneada en el núcleo: `stt`/`tts` en la firma de `LocalAgentRuntime`) y
  **`CG-V5`** (fallo de STT silencioso ⇒ prompt **vacío** al modelo: el usuario habla, el STT falla, y el agente
  responde a `""` sin que ninguna capa se entere). `CG-V5` es **2 líneas y es independiente** — el ítem de mejor
  ratio del inventario entero.

**(b) BATTERY — lo que se construye fuera del núcleo y se compone**
- **`battery_mcp`** — el bloque más grande del rollup: `CG-MCP-1..20`. Sub-keystone interno: `CG-MCP-1` (naming FQ
  `mcp__srv__tool` + `mcp_info`) gatea el gate de permisos FQ y el swap. Núcleo funcional: `CG-MCP-8` (ciclo de
  vida robusto: connect-timeout, startup batched, caps/instructions, recuperación de sesión + backoff).
- **`battery_skills`** — `CG-SKILL-1..15`. Keystone interno `CG-SKILL-1` (frontmatter 16 campos + dos ejes
  ortogonales) y `CG-SKILL-2` (prompt-provider ctx-aware + bash-injection con gate `loaded_from != 'mcp'` —
  seguridad). Gap MAYOR: **el standalone no surface el listing** (`CG-SKILL-4`).
- **`battery_memory`** — `CG-MEM-1..10`; el grande es `CG-MEM-2` (auto-extracción por fork), que depende de K7+K1.
- **`battery_plan`** — `CG-PLAN-1..11`; `CG-PLAN-1`=K1, `CG-PLAN-2` depende de K7, `CG-PLAN-3` de K2/ID-3.
- **`battery_voice`** — `CG-V1/V3/V4` (extracción); `CG-V2`=K4.
- **`battery_compaction`** = K6 · **`battery_resilience`** = `16·FIND-MODELS5/6/7+B4` (hogar 02·loop).
- **Tools nativas — `10`:** `FIND-NATIVE-READSTATE` (**keystone de 10**) · `EDITGUARDS` · `GAP-NATIVE-2` ·
  corrección de READ · `R4` · BASH persistente · `B12/R9` · background · `G3/R11` · §K (Brief/SyntheticOutput/
  NotebookEdit/LSP/Cron).
*(La fila «Infra de tools — 09» que este epígrafe archivaba **se movió a `(a) BASE`** en A-CIERRE·P0 — `CAT-h2`.)*

**(c) COSTURA/INTEGRADOR** — → **§3**.

### 1.3 Orden de ataque consolidado

1. **K1** (modos de permiso) + **K2·ID-1..ID-4** + **K3** (guard-path) — el borde de seguridad, todo junto.
2. **K7** (fork/runner) — desbloquea 5 categorías y hoy rompe el 100% de los subagentes.
3. **K5** (`ToolResult`) → habilita el grueso de mcp + skills.
4. **K4** (identidad en el `Event` base — *forma corregida en A-CIERRE·P0, ver §1.1·K4; el rótulo «sobre del evento» está descartado*) + **K2·ID-5..ID-7** → habilita batteries externas y la extracción de voz.
5. **K6** (compactación) — bloque propio, 4 caras se cierran a la vez.
6. Bloque `08·CG-SIG-*` (coherente, poco acoplado hacia fuera).
7. Batteries por volumen: mcp → skills → memory → plan → voice.
8. **K8** (fail-fast) antes de abrir Fase C.

*(`17·CG-V5` es independiente y trivial: hacerlo cuando se toque, sin esperar orden.)*

---

## 2. El hilo de identidad como diseño desarrollado (L05 — 6 campos)

> **Por qué aquí y no en una categoría:** ningún ciclo veía más de un touchpoint. `00-BLUEPRINT §2.1` los enumeró
> y los remitió explícitamente a A3.DA. El patrón obligado (`00-LEGEND §2.4`) es **id opaco + repo genérico**: el
> runtime reifica **sólo el `.id`**, nunca interpreta `userId`/`sessionId`, y **no existe objeto global de
> identidad**. Lo que sigue son **siete piezas**, cada una con los 6 campos.
>
> **Nido central = `SessionRepo`** (`05·E30`, `SEAMS §S20`), estado actual **`existe-mímica`**.

---

### ID-1 · Ripear el autogen de identidad del núcleo 🔒
- **Comportamiento:** hoy el runtime **inventa identidad**: `_build_child` fija
  `user_id = task.owner_id or f"user_{uuid}"` y `session_id = f"sess_{uuid}"` (`runtime.py:208-209`,
  `_build_child:205-218`), y `18·A2` confirma la misma semilla en el factory. Consecuencia observable: dos
  procesos del mismo usuario producen identidades distintas, y el integrador **no puede** imponer la suya sin
  pelear con el default. Bajo `mimica-no-desfusion` esto es plomería horneada, no un default benigno.
  *(Efecto lateral ya catalogado: el `"anon"` de `runtime._persist:424` es **inalcanzable** precisamente porque el
  autogen nunca deja `None` — al ripear el autogen esa rama pasa a ser alcanzable y correcta.)*
  **⚠ Agravante H-1 (verificado de primera mano, §0.1b):** el autogen **rompe la memoria**. `MemoryProvider._scope`
  keya por `f"{user_id}/{agent}"` (`provider.py:61-63`) y ese `user_id` es un uuid **nuevo por despacho**
  (`runtime.py:209`) ⇒ sin integrador que atribuya, el agente principal escribe su memoria en un directorio
  distinto cada vez y **nunca la recupera**. Esto convierte ID-1 de «higiene de contrato» en **corrección de un
  fallo funcional silencioso**, y es la razón dura de que vaya primero.
- **Costura:** la que ya existe — `RuntimeTask.owner_id`/`session_id` (`01·CTR-05`, T3-INTEGRADOR que el núcleo
  **transporta**) + el repo inyectado. No se crea seam nuevo: se **quita** el fallback.
- **Firma:** `ToolUseContext.user_id: str` y `.session_id: str` pasan a ser **requeridos y opacos** (sin default);
  `create_runtime` los exige o exige el `SessionRepo` que los produce (converge con **K8**). Ningún tipo del
  runtime gana un campo `identity`.
- **Cableado:** `execution/local/runtime.py:198-218` (`_build_child`) — borrar los dos `f"..._{uuid}"`;
  `factory.py` (semilla `18·A2`) — dejar de autogenerar y validar presencia.
- **Orden:** **primero del hilo.** Todo lo demás keya sobre el id; keyear sobre un id inventado propaga el defecto.
- **Prueba:** construir un runtime sin identidad ⇒ `RuntimeConfigError` (no un `user_<hex>` silencioso); con
  identidad atribuida, `grep -n "user_\|sess_" execution/local/runtime.py` no muestra ninguna generación.

### ID-2 · `SessionRepo` genérico — el nido central
- **Comportamiento:** `05·E30` reificó `Session` como behavior-homolog (**el canónico no tiene sesiones** — es
  divergencia deliberada de B, no deuda). Pero el runtime **posee** la sesión en vez de delegarla, y
  `SEAMS §S20` la marca `existe-mímica`. Un integrador multi-tenant no puede sustituir el ciclo
  create/open/list/delete/fork ni el scoping.
- **Costura:** `SessionRepo` genérico sobre metadata **definida por el integrador** (`Repo[MetaT]`); el runtime
  consume **sólo** `.id`. Precedente vivo y validado: la referencia PI muestra que un integrador complejo
  (openclaw) **no usa** los tipos `Session*` del core y habla sólo el protocolo — el boundary real es
  **protocolo + motor**, no el repo. Este diseño lo respeta: el repo es seam **opcional**.
- **Firma:** `class SessionRepo(Protocol[MetaT])` con `create(meta) -> SessionId` · `open(id)` · `list(scope)` ·
  `delete(id)` · `fork(id, meta)`; `SessionId = NewType("SessionId", str)` opaco. `TaskRegistryProtocol`
  (`05·E9`, hoy **`existe-doble-camino`**, `SEAMS §S19`) se alinea al **mismo** patrón — un repo genérico, no dos
  diseños distintos.
- **Cableado:** `session/session.py:38-59` (abierto 1→EOF por 05) pierde la posesión; `execution/tasks/registry.py`
  colapsa su doble camino; el integrador inyecta ambos por DI (patrón fijado por **A2.5**, criterio
  `SKELETON-REPORT §4.2`: registro **por instancia**, no por clase/módulo).
- **Orden:** tras ID-1; **antes** de ID-3 (el scope de persistencia keya sobre lo que el repo define).
- **Prueba:** `A2` ya validó S20 ✅ con un repo de juguete; el criterio de cierre es que el runtime real pase el
  mismo test — dos integradores con metadata **incompatible** componen el mismo núcleo sin tocarlo.

### ID-3 · Scope de persistencia uniforme, multi-repo 🔒
- **Comportamiento:** hoy cada repo inventa su clave y **uno de ellos filtra entre usuarios**:
  - **tokens OAuth MCP** — `base = f"{user_id}/mcp/{srv}"` con default `user_id="mcp"` y el factory **nunca** pasa
    el real (`token_storage.py:24` + `provider.py:50/87` + `factory.py:149-155`) ⇒ **todos los usuarios colisionan
    en `mcp/mcp/<srv>`**. Confirmado por el **ensamblador**, no por el tracker. Fuga multi-usuario.
  - **skills** — `prefix="skills"` fijo, **sin componente de identidad** (`store.py:35-40`) ⇒ dos usuarios bajo la
    misma clave.
  - **memoria** — `<user_id>/<agent>` (`provider.py:52-63`) ✅ patrón correcto, pero ver ID-4.
  - **transcript** — `<uid>/<sid>/…` ✅ correcto.
  - **taxonomía del base** — 6/7 claves declaradas están **muertas** y los stores inventan la suya
    (`15·CG-STOR-1`).
- **Costura:** **NO un `StorageManager` god-object.** `15·§0.2` estableció el patrón y `13·§0.1` lo **confirmó por
  el ensamblador** (memoria usa `MemoryStore`, **nunca** `StorageProtocol`; son dos ejes distintos que comparten
  la nota-identidad pero no el seam). El diseño es: **N repos coexistentes** (transcript→`StorageProtocol` ·
  memoria→`MemoryStore` · sesión→`SessionRepo` · config/catálogo→batteries sobre blob), **todos** con la misma
  regla de clave.
- **Firma:** un tipo `Scope` opaco (`@dataclass(frozen=True) class Scope: key: str`) que el integrador produce y
  cada repo antepone; **cero** repos que acepten `user_id: str` literal. `McpProvider(..., scope=)` sustituye al
  `user_id="mcp"`. *(`18·N5`/S28 ya previó `RuntimeHost.scope`: converge.)*
- **Cableado:** `factory.py:148-155` (pasar el scope a `McpProvider` — **seam nuevo**, hoy no existe el paso) ·
  `factory.py:132,174` (`18·C-cap5`, el `user_id` no se hila a los stores) · `skills/store.py:35-40` ·
  `storage/protocol.py` (cablear la taxonomía muerta).
- **Orden:** con K3 (misma prueba, misma zona).
- **Prueba:** dos scopes distintos ⇒ **cero** claves compartidas en cualquier repo; test explícito de que el
  token OAuth del usuario A no es legible bajo el scope de B (hoy **falla**).

### ID-4 · Guard-path unificado 🔒 (= K3, aquí por su cara de identidad)
- **Comportamiento:** los componentes de la clave son **ids del integrador** y se unen **crudos** a rutas: memoria
  (`store.py:106-110`, un `user_id`/`agent_id` con `..` o absoluto escapa del root — `Path / "/etc/…"`), skills
  (`f"{prefix}/{name}{SUFFIX}"`), storage (`_path` con `startswith`). El canónico sanitiza
  (`validateMemoryPath`/`sanitizePath`/`sanitizePathKey`).
- **Costura:** un helper único en el base — es el punto exacto donde "el runtime no interpreta la identidad" se
  encuentra con "pero sí debe defenderse de ella". **No interpretar ≠ confiar.**
- **Firma:** `def sanitize_path_key(segment: str) -> str` (rechaza `\0`, `..`, absolutos, backslashes) +
  `def is_within(root: Path, p: Path) -> bool` (resolución real, **no** `startswith`).
- **Cableado:** los 4 consumidores de K3, más `14·§0.2` (la variante subagente del plan-file incrusta `agent_id`;
  atraviesa `ctx.storage`, así que hereda el guard del integrador — **verificar que el adaptador lo aplique**).
- **Orden:** con ID-3.
- **Prueba:** un `Scope` con `../../etc` ⇒ excepción, no escritura; test de hermano-prefijo (`/data/root-evil`).

### ID-5 · Identidad **estable** del subagente (tipo, no uuid)
- **Comportamiento:** la memoria del subagente se keya por `context.agent_id` = **uuid fresco por fork**
  (`fork/__init__.py:69`, `agent_{uuid}`) ⇒ **la memoria de un subagente-de-tipo-X no persiste entre despachos**.
  El canónico keya por `sanitizeAgentTypeForPath(agentType)` = estable. La raíz usa el slot `"main"` (correcto).
- **Costura:** ninguna nueva — **el tipo YA está en la frontera y el resolver YA está cableado** (verificado de
  primera mano, §0.1b): `AgentDefinition.subagent_type` (`agents.py:26`), consumido en `runtime.py:342`, con
  `agent_resolver=config.agent_resolver` pasado por el ensamblador en **`factory.py:237`**. **ID-5 NO es un gap
  de cableado** (a diferencia de K7/S18, que sí lo es). El gap es **exclusivamente la clave de scope**: el
  `subagent_type` no se hilvana al `ToolUseContext` (que sólo tiene `user_id`/`agent_id`/`is_subagent`/
  `subagent_depth`, `tool_use.py:39-42`) ni llega a `MemoryStore._scope`.
- **Firma:** `ToolUseContext.subagent_type: str | None`; `MemoryStore._scope` usa
  `subagent_type or ("main" if not is_subagent else agent_id)`.
- **Cableado:** `context/tool_use.py:39-42` (campo) · `fork/__init__.py` (propagar) · `provider.py:52-63` (clave).
- **Orden:** tras ID-3; independiente de ID-6/ID-7.
- **Prueba:** dos despachos del mismo `subagent_type` en sesiones distintas ⇒ **misma** clave de memoria; dos
  tipos distintos ⇒ claves distintas.

### ID-6 · Identidad en los seams de SALIDA (campos en el `Event` base + `VoiceCallContext`)
- **Comportamiento:** dos fugas opuestas. **(a) Falta identidad:** `TokenEvent`/`DoneEvent`
  (`events/event_types.py` 1→43) son **anónimos** — un sink suscrito por la costura pública recibe tokens del
  principal y de todos los subagentes **mezclados** (`_wire_tts` sólo distingue porque recibe `ctx` **por
  parámetro**, `runtime.py:239`). **(b) Sobra identidad:** `transcribe(audio, ctx)`/`speak(text, ctx)`
  (`voice/protocol.py` 1→58) entregan a un **motor de terceros** el `ToolUseContext` **completo**: `user_id`,
  `session_id`, `messages` (la conversación entera), `tool_pool`, `app_state`, `storage`, `fs`,
  `git_credentials`. Un motor de voz no necesita nada de eso; el `00-LEGEND §2.4` lo prohíbe expresamente.
- **Costura:** **campos de identidad opacos en el `Event` BASE** en la salida (⚠ **NO** un `EventEnvelope` que
  envuelva — forma descartada, ver K4) y un **contexto mínimo opaco** en las costuras de terceros
  (`VoiceCallContext`). Misma regla en ambas direcciones: **el runtime transporta un id, no un bolso.**
- **Firma:** `@dataclass(frozen=True) class Event:` gana `task_id: str = ""`, `agent_id: str = ""`,
  `session_id: str = ""`, `seq: int = 0`, `ts: float = 0.0` (campos **no interpretados**, todos con default para
  no romper el orden de dataclass de los 5 subtipos existentes); el filtrado de un sink se hace sobre esos campos,
  **no** sobre un envelope (`subscribe(TokenEvent, handler)` conserva su tipado genérico intacto). Y
  `@dataclass(frozen=True) class VoiceCallContext: id: str; metadata: Mapping[str, Any]; stop: Event | None`.
  *(`agent_id` es **el mismo** hilo que ID-5 y H-4: se cablea una vez y sirve a los tres — `DEUDA-B §7.4`.)*
- **Cableado:** `events/event_types.py` + `events/bus.py` (1→45) + emisor `AgentLoop._emit` (`agent_loop.py:152-154`,
  llamado en `:248/:312/:324`) + `_make_bus` (`runtime.py:333`); y `voice/protocol.py` + los 3 call-sites
  (`runtime.py:228,:248,:257`, que tras `17·CG-V1` viven en la battery).
- **Orden:** = K4. Los **campos de identidad del `Event` base** van **primero** (la mitad de salida de `CG-V1`
  depende de ellos, y `S31 SpeechSink` está explícitamente **detrás de K4**); `VoiceCallContext` es independiente
  y va con la extracción (`S30`/`S31`, `SEAMS`).
- **Prueba:** `SpeechSink` **externo** reproduce el comportamiento actual (subagentes mudos) **sin** recibir
  `ToolUseContext`; y un fake de motor que haga `dir(vctx)` **no puede alcanzar** `messages`, `user_id` ni
  `storage`.

### ID-7 · Identidad hacia el proveedor de modelo
- **Comportamiento:** `16·B10` — `metadata(user_id)` y session-affinity no se transportan a la llamada. El
  proveedor no puede aplicar rate-limiting ni abuse-detection por usuario, y un integrador multi-tenant no puede
  pedir afinidad de sesión.
- **Costura:** `ModelRequest` gana un campo de metadata **opaca**; el runtime lo pasa sin interpretarlo. **T1-MOTOR
  la ranura, T3-INTEGRADOR el contenido** (así lo clasificó 16, y este rollup lo mantiene).
- **Firma:** `ModelRequest.metadata: Mapping[str, str] | None` (el integrador decide si mete su id opaco).
- **Cableado:** el seam S1 `ModelCallerProtocol` (cableado real en **`factory.py:219`** — no `:83`, que es el slot
  muerto `LAT-MODELS1`) + el emisor de la request en el loop.
- **Orden:** independiente; con `16·FIND-MODELS1` (misma costura demasiado delgada, misma zona).
- **Prueba:** un `model_caller` fake asevera que recibe la metadata que el integrador puso, y que el runtime **no
  la leyó** en ningún punto intermedio.

### 2.8 Saldo del hilo — cotejo 1:1 contra `00-BLUEPRINT §2.1` (verificado 1→EOF)

Los touchpoints de `00-BLUEPRINT §2.1` (líneas 110-116) son **11**, y el cotejo honesto es **9 cubiertos, 2 no**:

| # | touchpoint (`00-BLUEPRINT §2.1`) | cubierto por | ¿el campo *cableado* de esa pieza lo incluye? |
|---|---|---|---|
| 1 | `SessionRepo` (05·E30) | ID-2 | ✅ sí |
| 2 | `TaskRegistry` repo (05·E9) | ID-2 | ✅ sí (`execution/tasks/registry.py`) |
| 3 | scoping notif/transcript (05·E5/E7) | ID-3 | ✅ sí |
| 4 | ids opacos de ejecución (05·E3/E8/E33/E35/E36) | ID-1 | ✅ sí |
| 5 | **resume (05·E26)** | ID-2 | ❌ **NO — ver H-3** |
| 6 | `metadata.user_id` del model-call (16·B10) | ID-7 | ✅ sí |
| 7 | `StorageContract` token→path (09·G6) | ID-3/ID-4 | ✅ sí |
| 8 | **discovered-set por `agent_id` (09·E5)** | ID-5 | ❌ **NO — ver H-4** |
| 9 | `session_id`/`uuid` del wire (07·B3) | ID-6 | ✅ sí — **por los campos `session_id`/`seq` del `Event` base**, no por un envelope (forma corregida en A-CIERRE·P0, `CAT-h10`) |
| 10 | índice de sesiones `SDKSessionInfo` (07·K5→15) | ID-2/ID-3 | ✅ sí |
| 11 | mímica a ripear (`_build_child` autogen) | ID-1 | ✅ sí |

**⚠ Corrección:** la redacción anterior decía «**todos** sus touchpoints quedan cubiertos». **Falso.** Dos no lo
están, y ambos se descubren sólo al cotejar la lista contra el campo *cableado* de cada pieza — que es lo que este
cotejo hace y la afirmación global ocultaba.

- **H-3 · `resume` no existe (touchpoint 5).** `00-INTEGRADORES §1.3` declara como firma que el integrador consume
  `LocalAgentRuntime.resume(agent_id, message)`. **Verificado leyendo `execution/local/runtime.py` 1→EOF: ese
  método NO existe** — la superficie pública es `startup`/`shutdown`/`dispatch`/`stream`/`status`/`cancel`/`result`.
  No es un gap de scope (ID-2 le da la clave), es un **método ausente**. `05·E26` quedó «diferido a 11/15» y ni 11
  ni 15 lo reclamaron. **Destino: CORE-GAP nuevo, hogar `05·execution`, prerequisito ID-2+ID-3** (la clave del
  transcript desde la que se reabre). **No lo pliego dentro de ID-2**: es trabajo distinto.
- ~~**H-4 · el discovered-set no lo cablea ID-5 (touchpoint 8).** `09·E5` scopea el set de tools MCP descubiertas por
  `agent_id`. ID-5 sustituye `agent_id` por `subagent_type` **sólo en la clave de memoria**
  (`provider.py:52-63`); su campo *cableado* **no incluye** el discovered-set. Son dos consumidores del mismo
  `agent_id` inestable. **Destino: extender el cableado de ID-5 al discovered-set** — la firma (`ToolUseContext.
  subagent_type`) ya sirve; falta el consumidor. Converge con `11·CG-MCP-20` (cleanup per `agent_id`).~~

  ⚠ **PREMISA FALSA — corregido en A-CIERRE·P1 (`AC-h6`, `tools/deferred.py` abierto 1→EOF 2026-07-27).**
  El discovered-set **no está keyado por `agent_id`**: `tools/deferred.py` (44 L, leído entero) **no lee
  `agent_id` en ninguna línea**. El estado vive en `ctx.app_state.capabilities["discovered_tools"]`
  (`deferred.py:14`, `:30-37`) — clave **literal y única**, sin componente de identidad. Por tanto **ID-5
  (`subagent_type`) no tiene nada que cablear aquí**, y este hallazgo **no es** «el segundo consumidor de ID-5».
  **Origen del error:** `deferred.py:11-13` lleva un comentario que afirma *«Estado de descubrimiento scopeado
  por agente … estado de capability por contexto (**agent_id**)»*; este rollup tomó esa frase por descripción del
  mecanismo. **RV-5 de nuevo: un docstring no es evidencia de cableado.**
  **Re-emitido como dos gaps reales** (desarrollados con los 6 campos en **`A-CIERRE-P1.md §AC-06`**):
  **(a)** el canónico **deriva** el set del historial (`claude-code/src/utils/toolSearch.ts:545-575`,
  `extractDiscoveredToolNames`) y por eso sobrevive por construcción a resume/compactación/fork; el runtime lo
  **almacena en el `ctx`**, que muere con el run ⇒ la remediación es **derivar**, no transportar (1 archivo).
  **(b)** `ForkPolicy` trae `inherit_capabilities=True` (`fork/__init__.py:27`) con `inherit_messages=False`
  (`:24`) ⇒ **el hijo hereda el discovered-set sin la historia que lo produjo**, donde el canónico le daría un
  conjunto vacío. El gap (a), resuelto derivando, cierra (b) automáticamente.
  ⇒ el **touchpoint 8 se cierra por un mecanismo distinto del que esta fila declaraba**; la fila de §2.8 debe
  reescribirse en la consolidación de los `00-*` (**P8**).

**Saldo real:** `00-BLUEPRINT §2.1` queda **🟨→ casi ✅**: el *diseño* del hilo está completo y los 11 touchpoints
**identificados**, pero **2 de 11 no tienen cableado desarrollado**. Se marca ✅ **sólo cuando H-3 y H-4 se
desarrollen** (A-CIERRE, con los 6 campos como el resto). **`00-BLUEPRINT §1.4` («Módulos base del resto», hoy ⬜)
sí queda desbloqueado** — su bloqueo era el diseño del hilo, no estos dos cabos.

---

## 3. Cara integrador

> Regla (`00-INTEGRADORES §1`): lo que aquí se lista **no** es deuda del runtime — es **obligación del
> integrador**. Se documenta para que el saldo del rollup no la absorba ni la pierda.

> **⚠ Acotación de origen (verificada al re-abrir `00-INTEGRADORES.md` 1→EOF, §0.1b-2).** Sólo `OI-1..OI-23`,
> `OI-M1..M8` y `OI-EVT-1..4` **están vertidos** en `00-INTEGRADORES §1` (espina A1.7). Los `OI-STOR-*`,
> `OI-MCP-A`, `OI-FAC-1`, `OI-VOICE-*` y `OI-D` que se citan abajo viven **en el §2.5 de su `NN-*.md`** y aún no
> se han vertido — `00-INTEGRADORES §3` lo declara pendiente («resto A3»). **Cabo emitido a A3.CAT / A-CIERRE.**

**Obligaciones universales tocadas por DEUDA-A** (`00-INTEGRADORES §1.1-1.6`):
- **§1.1 — Atribuir identidad/sesión** 【nido central】 — `OI-1` · `OI-D` · `OI-11`. **Se vuelve exigible con
  ID-1**: al ripear el autogen, el integrador **debe** atribuir. Es el cambio de contrato más visible de este
  rollup.
- **§1.3 — Proveer los repos de persistencia** — `OI-STOR-A` (backend del blob) + `OI-STOR-B/C` + `OI-MCP-A`
  (pasar el scope a los tokens — hoy **imposible**, no hay parámetro: ID-3 lo crea) + el `Scope` de ID-3.
- **§1.4 — Interfaz/transporte** — `OI-EVT-2/3` (serializador wire, índice de sesiones) consumen **los campos de
  identidad del `Event` base** que aporta ID-6 (~~el envelope~~ — forma descartada, ver K4).
- **§1.5 — Composición de batteries** — `OI-FAC-1`: el base **no trae catálogo por defecto**; sin composición hay
  un runtime núcleo que corre un turno de texto y nada más. K8 lo hace fallar ruidosamente.
- **§1.6 — Política/hooks** — el integrador decide el `mode` inicial de K1 y el `PermissionGate` (S17,
  `parcial-vivo`).
- **Voz** — `OI-VOICE-1..5` (nomenclatura corregida en el gate de 17: `OI-*`, no `MB-V*`).
- **Modelos** — `OI-M3` (metadata de identidad, ID-7) sobre `OI-M1` (proveer el model-caller).

**Los dos integradores, contrastados:**

| eje | `agentic_code` (grado cero, CLc-like) | `agentic_assistant` (complejo, openclaw-like) |
|---|---|---|
| Identidad (ID-1/2) | una sesión, un usuario; `Scope` constante | el BFF atribuye; `SessionRepo` multi-tenant real |
| Persistencia (ID-3) | FS local, un repo por eje | MinIO; N repos + sidecar meta (`18·C6`, `15·STOR11`) |
| Eventos (ID-6) | consume in-proc | serializador **SSE** multi-tenant + `init` para bootstrap del front |
| Voz | compone `AudioPromptResolver` + `SpeechSink` local | compone el resolver y **sustituye** el sink (sin altavoz en contenedor) |
| Ejecución | `LocalAgentRuntime` | `RemoteAgentRuntime`/CCR/teleport (`18·D3`, `05·E31`, `OI-15`) con affinity por tenant |

**Nota de forma (no de deuda):** que `agentic_assistant` posea su identidad **por fuera** y hable sólo el
protocolo es exactamente el blueprint de la referencia PI. El `SessionRepo` es por eso seam **opcional**: el
integrador degenerado lo usa, el complejo puede ignorarlo. Un diseño que lo hiciera obligatorio sería el error.

---

## 4. Lo que NO es DEUDA-A

> Modelo tomado de `18·§2.3b`, que separó esto explícitamente para no inflar el rollup. Sin esta sección, DEUDA-A
> absorbe trabajo que no es brecha A↔B y el backlog miente sobre su tamaño (L10, doble filo).

**(a) Requisitos de re-arquitectura B (`18·§2.3b`, RB-1..RB-6).** El canónico **no** tiene un mecanismo de
composición mejor — tiene un singleton global. Que B se imponga un punto de composición explícito (RB-1/S28),
descomponer `RuntimeConfig` (RB-2), tipar la superficie (RB-3), alcanzabilidad total (RB-4), registro por
instancia (RB-5) y contrato del `execution_mode` (RB-6) es **trabajo de forma que B se debe a sí misma**.
Confundirlo con deuda del canónico sería inflar. → A-CIERRE / Fase B.

**(b) DEUDA-B — higiene interna** (→ `DEUDA-B.md`, A3.DB): `B-02` (el hack `native["plan_mode"]`, que **muere** al
llegar K1) · `B-runner-wiring` · `B-dead-resolver` + `B-create-loop` (⚠ decisión **conjunta**: borrar el resolver
**rompe** `create_loop`) · `B-global-registries` (6 almacenes globales) · `B-untyped-composition` ·
`B-unreachable-knobs` · `B-dead-ternary` · `B-orphans` (incl. `LAT-MODELS1`, `ModelRequest.thinking_budget`,
`NativeToolRegistry`/`.category`, observer/) · `log_key` (decisión borrar-vs-cablear) · `"anon"` inalcanzable de
`_persist:424` · el autogen `user_<hex>` **como limpieza** (su cara A↔B es ID-1; la cara B es el código muerto que
deja) · **`LAT-CAP1`** (nuevo, hallado al re-abrir `12·§2.4`: `CapabilityActivation` en `capabilities/contracts.py:26-38`
**sin productor ni consumidor** — decisión CABLEAR-vs-BORRAR, **A3.DB**).

**(c) Caras aguas-abajo que NO se re-cuentan** (L10, y los ciclos ya lo rulearon uno a uno):
- `compact_context() == []` en memory/plan/skills/mcp — **una** cara de K6, no cuatro gaps.
- `is_session_plan_file` sin consumidor (`plan_file.py:58-63`) — costura de exención **pre-cableada a medias** que
  K1 consumirá; cara-B de un ❌ ya contado.
- `EXPLORE_AGENT_TYPE`/`PLAN_AGENT_TYPE` — **no** son orphans: sí se consumen en el reminder; su falta de
  resolución es `CG-PLAN-2` (K7), no maquinaria muerta.
- `LAT-HOOK1`/`to_llm` — mismo criterio.

**(d) Divergencias deliberadas 🔀 — divergencia ≠ deuda (L10):**
- `13·A2` — scope de auto-memory por **git-root** (worktrees comparten): el runtime scopea, la **política** es del
  integrador.
- `14·C3` — token de plan-file **fijo** (`/plans/plan.md`): el namespace de sesión da la unicidad; el word-slug del
  canónico (retry-colisión + caché) **no aplica**.
- `18·F3` — no hay estado global sembrado (~90 campos en el canónico): bajo B el estado es per-`ctx`/per-`Session`
  **porque hay multi-sesión**. `18·F5` — no memoizar el runtime es **correcto** multi-tenant.
- `05·E30` — que exista `Session` cuando el canónico no la tiene es behavior-homolog deliberado.
- `12·FIND-SKILL13` (hot-reload) — cubierto por la API register/unregister viva; falta sólo el hook `ConfigChange`.
- ~~**⚠ Bajo objeción, NO cerrado:** `07·B2` (atribución implícita por bus per-task) — ver **K4**. Se re-abre.~~
  **CERRADO por `DEUDA-B §7.2` (aplicado aquí en A-CIERRE·P0, misma familia que `CAT-h10`).** Veredicto: `07·B2`
  **no concluyó mal — concluyó condicionado a un seam que aún no existe**. Para los seams de hoy
  (`dispatch(on_event=)`/`stream`) el consumidor **es** quien despacha y la atribución implícita se sostiene; el
  `EventBus` no se expone por ningún accesor, así que la objeción de 17 se confirma **por ausencia**, no por error.
  Queda como **CORE-GAP condicionado** con forma decidida (campos en el `Event` base) = **K4**. Ya **no** es una
  divergencia bajo objeción: tiene tier, forma y hogar.

**(e) ⛔ Fuera de alcance** (L07 — declarado, no troceado): `mcpSkills.ts` **no vendorizado** (no legible) ·
diálogo interactivo de elicitation MCP (`MCP-NA-7`) · snapshot-sync VCS de memoria (`OI-MEM-F`, diferido por el
integrador) · `18·C6` `WorkerStateUploader` (fuera del factory, hogar nombrado en `agentic_assistant`).

**(f) Pendiente de DECISIÓN, no de trabajo:** el tier de `B-new_messages` (ver **K5**) — **A3.DB decide**.

---

## 5. Saldo

- **⬜ → ✅:** `00-BLUEPRINT §5` (puntero DEUDA-A) · `00-BLUEPRINT §2.1` (SEAM-DE-IDENTIDAD 🟨→resuelto en diseño).
- **Desbloqueado:** `00-BLUEPRINT §1.4` («Módulos base del resto»), que esperaba este hilo.
- **Emitido a otros ciclos** *(estado actualizado en A-CIERRE·P0)*: decisión de tier de `B-new_messages` →
  **A3.DB ✅ resuelto** (`§4·cabo 1`: CORE-GAP K5; residual DEUDA-B = DB-13) · re-apertura de `07·B2` →
  **A3.DB ✅ resuelto** (`§7.2`: CORE-GAP condicionado, forma = campos en el `Event` base) · composición por
  defecto de cada integrador → **A3.CAT ✅ resuelto** (`BATTERIES §1`: 3 perfiles, ninguna battery obligatoria) ·
  `log_key` borrar-vs-cablear → **A3.DB** · **`LAT-CAP1` cablear-vs-borrar → A3.DB** (nuevo) · **verter los
  `OI-*` de los 12 ciclos A3 restantes a `00-INTEGRADORES §1` → A3.CAT / A-CIERRE** (nuevo).
- **Aportado por el tramo de re-verificación (4 hallazgos):** **H-1** el autogen rompe el scope persistente de la
  memoria (agrava ID-1 de contrato a fallo funcional) · **H-2** el guard-path de ID-4 debe cubrir el segmento
  **absoluto**, no sólo `..` · **H-3** `LocalAgentRuntime.resume` **no existe** — CORE-GAP nuevo, hogar
  `05·execution`, caído entre 11 y 15 · **H-4** el discovered-set `09·E5` no queda cableado por ID-5. Ninguno de
  los 18 ciclos los tenía: los cuatro emergen al **cruzar dos fuentes**, que es la única cosa que un rollup
  transversal puede hacer y una categoría no.
- **`00-BLUEPRINT §2.1` NO se marca ✅:** queda 🟨 con 9/11 touchpoints cableados. H-3 y H-4 son su condición de
  cierre (A-CIERRE, con los 6 campos). La marca ✅ que este ciclo puso primero era prematura y está retirada.
- **No cerrado y no fingido:** este rollup **no** re-validó A↔B categoría por categoría (§0.1). El tramo de
  re-verificación cubrió los **5 docs transversales** (1→EOF) y **11 archivos de código**, y en ese perímetro
  todas las anclas contrastadas resultaron exactas; **fuera de ese perímetro** (los 18 `NN-*.md`, los trackers)
  la garantía sigue siendo *consolidación fiel de los 18 ciclos*, no *verificación independiente* — y esa brecha
  **no se cierra aquí**: se cierra en A3.CAT/A-CIERRE reabriendo por categoría.
