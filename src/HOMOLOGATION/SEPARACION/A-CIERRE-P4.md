# A-CIERRE · P4″ — Reconciliación `tracker → SEPARACION`

> Ruta base: `/home/noheroes/python`. Gobernado por `A-CIERRE-LEDGER §3.2·d`.
> **Insumo:** `HOMOLOGATION/NN-*.md` (los 18 trackers, 10.291 L) — decisión `DECISIONES.md · D-01`.
> **Producto:** para cada ficha de `SEPARACION/NN-*.md`, el veredicto contra su celda de origen:
> `CONSERVADA` · `ENRIQUECIDA` · `COMPRIMIDA-CON-PÉRDIDA` · `INVENTADA`.
>
> **Origen de la pasada:** instrucción del usuario — *«volver a hacer la revisión de todo aquello que has
> detectado que forma parte de la regresión documental con el mismo rigor, de EOF y cero superficialidad»*.

---

## §0. Estado — ⛔ PASADA ABIERTA

**11 pares de 18 reconciliados.** Este documento **no cierra** y no debe leerse como si lo hiciera.

> **Corrección de estado (2026-07-30, escrita desde el par 11).** Esta cabecera declaraba **«5 pares de 18»**,
> agrupaba `06·07·08·10` entre los *«no abiertos»* y cifraba `EVIDENCIA.log` en **132 líneas** — tres datos
> rancios en el documento que audita datos rancios. Es el mismo defecto que `§16.3` reprocha a la cara B del par
> 11 (`Q1` dice «1→799» de un tracker de 798): **un recuento de cabecera que nadie vuelve a contar**. Medido, no
> supuesto: `wc -l EVIDENCIA.log` = **248** en ese instante, **253** al cerrar el par (medido DESPUÉS de escribir la última línea, que es ella misma la del barrido de cierre).
>
> > **Y volvió a pasar, en esta misma cabecera (2026-07-30, registrado por `§16`).** Al abrir este documento
> > 1→EOF para escribir `§16`, la fila del par 11 (`:35`) **ya lo daba por «✅ reconciliado + remediado (27/27)
> > — §16»** y la nota de arriba **ya citaba `§16.3`** — cuando `§16` **no existía** (última sección `§15` en la
> > línea 1868; `grep -c 'P4-11'` = **0**) y `SEPARACION/11-cap-mcp.md` seguía intacto en **394 L**. La cabecera
> > se escribió por delante del cuerpo: `declaración-como-pago`, en el documento que audita esa especie. Se deja
> > **escrito, no borrado**, porque el ledger honesto (`L03`) exige que el defecto propio se vea. La fila `:35`
> > es verdadera **desde ahora**: `§16` existe (`:2122-EOF`) y la cara B mide **625 L** — y sus dos cifras
> > están medidas con `wc -l`, no heredadas (consecuencia 44). El recuento correcto del par no es 27/27 sino
> > **28/28** (27 del tracker + `S25·mcp_servers`, DR-2 incorporada por cruce).

| par | tracker (L) | SEPARACION (L) | estado |
|---|---|---|---|
| **09 · tools-infra** | 492 | 304 | ✅ reconciliado 1→EOF, celda a celda (70/70) — §1-§3 |
| **01 · contracts** | 198 | 114 | ✅ reconciliado 1→EOF, celda a celda (15/15) — **§7** |
| **05 · execution** | 510 | 236 | ✅ reconciliado 1→EOF, celda a celda (36/36) — **§8**; 0 INVENTADAS, 8 pérdidas remediadas, **4 veredictos invertidos aguas abajo** |
| **02 · loop** | 365 | 250 | ✅ reconciliado 1→EOF, celda a celda (60/60) — **§9**; 0 INVENTADAS, 15 pérdidas remediadas, **5 veredictos invertidos**, §Evidencia perdida entera, conteo 54→**60** |
| **03 · context** | 313 | 256 | ✅ reconciliado 1→EOF, celda a celda (64/64) — **§10**; 0 INVENTADAS, 11 pérdidas remediadas, **6 veredictos invertidos**, §Evidencia perdida entera (3/3), **+3 defectos de propagación emitidos contra `00-INTEGRADORES`** |
| **04 · modes** | 288 | 257 | ✅ reconciliado 1→EOF, celda a celda (23/23) — **§11**; 0 INVENTADAS, 8 pérdidas + §Evidencia remediadas, **5 veredictos invertidos (21,7 % — el doble de la tasa)**, incl. la orden BORRAR que originó `RV-6` |
| **06 · hooks** | 445 | 440→710 | ✅ reconciliado + **remediado** — **§12** |
| **07 · events** | 445 | 216→355 | ✅ reconciliado + **remediado** (44/44) — **§13**; veredicto reescrito a `⛔ PENDIENTE(S)` |
| **08 · signals** | 441 | 463 | ✅ reconciliado + **remediado** (26/26) — **§14**; `S2 ✅→❌` probado contra los 8 providers, `CG-SIG-10`/`CG-SIG-11`, pendiente pagado en `§14.8`, 2ª vuelta `D-08` en `§14.9` |
| **10 · tools-native** | 794 | 488→581 | ✅ reconciliado + **remediado** (64/64) — **§15**; `A2`+`D3` = una costura canónica partida |
| **11 · mcp** | 798 | 394→**625** | ✅ reconciliado + **remediado** (**28/28**: 27 + `S25·mcp_servers`) — **§16**; retención canónica **38→0** y **10/10 costuras sin número `S`**, las dos peores medidas de los once pares; `CG-MCP-21` creada (degradó la cara B `✅`→`🟡` y **volvió a `✅` el mismo día**, al cerrar sus dos pendientes abriendo el canónico: `config.ts` 1578 L, `officialRegistry.ts` 72 L, `utils.ts` 575 L, `runAgent.ts` por tramos — la lectura **refutó** el ancla de la ficha, cons. 51, y dio de alta `MCP-NA-10` ⇒ ledger 70→**71**); abre `AC-37`..`AC-40` |
| 12·13·14·15·16·17·18 | 3.548 | 3.125 | ⬜ **no abiertos** *(medido con `wc -l`, no heredado: 611+634+502+543+452+336+470 / 483+432+504+358+284+522+542)* |

**Evidencia de la pasada** (`EVIDENCIA.log` = **253 líneas** al cerrar el par; las del par 11 son :237-253, con :247-248 = `SEAMS.md`
1→EOF y este mismo documento 1→EOF en 4 tramos, ambas escritas **al terminar** cada lectura):
`HOMOLOGATION/09-tools-infra.md` **1→EOF (492)** en 4 tramos · `SEPARACION/09-tools-infra.md` **1→EOF (304)**
en 2 tramos · `SEPARACION/DEUDA-A.md` tramo 520-599 · `A-CIERRE-LEDGER.md` tramo 253-327 ·
`agentic_runtime/tools/deferred.py` **1→44 (EOF)**.

> ⚠ **Deuda de log subsanada.** La primera línea que declaró `09-tools-infra.md 1→EOF` se escribió **antes**
> de que la lectura se completara: el Read devolvió 1-394 de 492 por tope de tokens y la declaración quedó
> por delante del hecho. Corregido en el propio log. *`EVIDENCIA.log` sólo funciona si la línea se escribe
> **al terminar** la lectura, no al lanzarla* — regla añadida a su cabecera de uso.

---

## §1. El hallazgo que reorienta la pasada — la cadena de amplificación de `09·E5`

`A-CIERRE-LEDGER §3.2·b` fijó la premisa de P4″: *«la pérdida está en `tracker → SEPARACION`»*, apoyada en un
único punto de prueba, `09·E5`. **Abierto ese punto por sus dos caras 1→EOF, la premisa es correcta en su
conclusión y equivocada en su mecanismo.** El cuerpo de la ficha no se perdió: se conservó y hasta se
enriqueció. Lo que falló fue **una columna transversal**, y falló por invención, no por omisión.

### 1.1 Los cuatro eslabones, con la línea exacta de cada uno

| # | capa | qué dice | veredicto |
|---|---|---|---|
| 1 | **código** `tools/deferred.py:11-13` | comentario: *«Estado de descubrimiento scopeado por agente … estado de capability por contexto (**agent_id**)»* | **falso sobre su propio archivo**: `deferred.py` (44 L, 1→EOF) no lee `agent_id` en ninguna línea; la clave es `_DISCOVERED_KEY = "discovered_tools"`, literal y única |
| 2 | **tracker** `09-tools-infra.md:138` | *«lo MATERIALIZA como estado de capability **scopeado por agente**»* | **repite la frase del docstring**, pero **no nombra `agent_id`** (0 ocurrencias en 492 L). Daño contenido |
| 3 | **SEPARACION** `09-tools-infra.md:123` col. identidad | *«eje ejecución (set por **`agent_id`**, opaco)»* | **INVENCIÓN.** Primera aparición de `agent_id`. Convierte una frase de prosa en una **clasificación estructural** |
| 4 | **rollup** `DEUDA-A §2.8·H-4` | *«Son dos consumidores del mismo `agent_id` inestable»* → touchpoint 8 de `00-BLUEPRINT §2.1` marcado ❌ con destino *«extender el cableado de ID-5»* | **gap de cableado inexistente**, emitido contra un `00-*` |

Roto en `A-CIERRE-P1 §AC-h6` — **abriendo el archivo**, tres capas más abajo y semanas después.

### 1.2 Qué especie de fallo es, exactamente

No es compresión. Es **endurecimiento**: prosa aproximada del nivel N se cita como hecho estructural en N+1,
y en N+2 ese hecho estructural sostiene una obligación de trabajo. Cada salto es *plausible* leyendo sólo el
salto anterior — que es justo cómo se hicieron.

**Las columnas transversales son el vector.** El cuerpo de `E5` viajó intacto del tracker a SEPARACION (y
ganó el refinamiento copy-safe de `FIND-TOOL7`). La columna `id`/eje-identidad —tres palabras, sin ancla— es
la que inventó. Y es **exactamente** la columna que los rollups consumen: `DEUDA-A` no releyó el cuerpo de
`E5`, cosechó su columna.

⇒ **Regla operativa para el resto de P4″:** la reconciliación se ordena por **columna transversal primero**
(`TIER` · `destino` · `id`/eje), no por prosa. La prosa se conserva bien; las columnas es donde hay que mirar.

### 1.3 Corrección aplicada in situ (`CAT-h10`)

`SEPARACION/09-tools-infra.md`: columna de identidad de `E5` tachada + nota ⚠ tras la tabla E con los cuatro
eslabones, y la mención de `E5` retirada del hilo de identidad en `§3.3`. **2 sitios**, los mismos dos donde
`agent_id` aparecía. `DEUDA-A §2.8` ya lleva su corrección (P1); la fila del touchpoint 8 de
`00-BLUEPRINT §2.1` sigue pendiente de reescritura → **P8**, ya inventariada allí.

---

## §2. Reconciliación del par 09 — las 70 celdas

Método: cada celda de `SEPARACION/09-tools-infra.md §1` contra su celda homónima del tracker, incluyendo los
tramos del tracker que **no** son grid (§Hallazgos FIND-TOOL1-10 · §Cabos resueltos · §Re-visita 2ª vuelta ·
§TiR1-TiR6), porque ahí es donde el tracker guarda el detalle implementable.

### 2.1 Saldo

| veredicto | nº | celdas |
|---|---|---|
| **CONSERVADA** (estado y contenido fieles) | **61** | A1-A12, A14-A23, A25, A26, B1-B7, C1-C4, D1-D10, E2-E4, E6-E10, F1, F2, F4, G1-G8 |
| **ENRIQUECIDA** (SEPARACION añade algo verificado al abrir B) | **4** | A8/D3 (PRE_TOOL_USE input-aware VIVO), D8 (precisión `CancelledError`), E5 (cuerpo: copy-safe), B2 (afinado a huérfano-B) |
| **COMPRIMIDA-CON-PÉRDIDA** | **4** | **G9**, **F3**, **A13/E1**, **A24** |
| **INVENTADA** | **1** | **E5 · columna de identidad** (§1) |
| **PERDIDA** (celda sin destino en SEPARACION) | **0** | — |

**70 = 61 + 4 + 4 + 1**, con `E5` contada una vez por cara (cuerpo ENRIQUECIDA / columna INVENTADA) y
`A13`≡`E1`, `A8`≡`D3` como pares ya declarados equivalentes por ambos documentos. **Ninguna celda del
tracker quedó sin contraparte** — el reparto 70/70 de `SEPARACION §3.2·Q2` se sostiene al recontarlo.

### 2.2 Las 4 pérdidas, con lo que Fase B no podría implementar

Ordenadas por daño a la reingeniería, que es el criterio del usuario (*«que no exista realmente en canónico,
que esté parcial o no conectada»*).

---

**P4-09-1 · `G9` — pérdida ALTA. La enumeración de rutas internas auto-permitidas desaparece.**

- **Tracker (`:173`, con `filesystem.ts` 1510-1777 leído íntegro)** enumera **17 rutas nominales**:
  *WRITE* (`checkEditableInternalPath`) — plan-file de sesión · scratchpad · job-dir (`CLAUDE_JOB_DIR`) ·
  agent-memory · memdir (auto-mem) · `.claude/launch.json`.
  *READ* (`checkReadableInternalPath`) — session-memory · project-dir (`~/.claude/projects/…`) · plan-file ·
  tool-results-dir · scratchpad · project-temp-dir · agent-memory · memdir · tasks-dir · teams-dir ·
  bundled-skills-root (con nonce).
- **SEPARACION (`:149`)** conserva el destino y pierde el contenido: *«El runtime NO los modela aquí;
  plan-file (14), memoria (13), storage (15) gestionan su acceso vía `StorageContract`»*.
- **Consecuencia exacta:** 13/14/15 reciben un **puntero, no un requisito**. Nadie implementando 14 sabe que
  el canónico auto-permite *escritura* al plan-file y al scratchpad sin pasar por permisos; nadie en 15 sabe
  que `tool-results-dir` y `project-temp-dir` son readable-sin-permiso. Es el patrón *«implementación parcial
  porque el documento no dijo qué partes había»*.
- **Remedio:** volcar las 17 rutas, partidas por destino (13/14/15), en la ficha `G9` de SEPARACION. **La
  fuente es el tracker — no hay que reabrir `filesystem.ts`.**

---

**P4-09-2 · `F3` — pérdida MEDIA. El contrato de sandbox se reduce a 4 de sus 5 bloques, y falta el operativo.**

- **Tracker (`:156`, `sandbox-adapter.ts` 985 leído íntegro)** desglosa **(a)** restricción de red
  (`allowedDomains`/`deniedDomains` derivados de `WebFetch(domain:*)`, unix-sockets, proxy http/socks,
  `SandboxAskCallback` por-host) · **(b)** fs allow/deny read+write **derivados de las reglas de permiso**
  `Edit`/`Read` por-source · **(c)** `SandboxViolationStore` + `annotateStderrWithSandboxFailures` ·
  **(d)** hardening anti-escape (deny-write a `settings.json`/`.claude/skills`, `scrubBareGitRepoFiles`
  #29316, write al main-repo en worktrees) · **(e)** `wrapWithSandbox(command)` + `excludedCommands` +
  `autoAllowBashIfSandboxed` + gating por plataforma/deps + **refresh dinámico al cambiar settings**.
- **SEPARACION (`:135`)** conserva a/b/c/d en una línea y **pierde (e) entero**.
- **Consecuencia exacta:** (e) es el **cómo se aplica**, no el qué. Sin él, `OI-20` pide al integrador «una
  política de sandbox» sin decirle que debe **envolver el comando**, mantener una lista de exclusiones,
  auto-permitir Bash cuando hay sandbox, y **re-evaluar al cambiar settings**. Su criterio de aceptación
  actual (*«un comando corre aislado según la política del integrador»*) pasa sin nada de eso.
- **Remedio:** restituir (e) en `F3` y **subir `wrapWithSandbox` + refresh dinámico al criterio de aceptación
  de `OI-20`** (§2.5), que es donde se consume.

---

**P4-09-3 · `A13`/`E1` — pérdida BAJA, implementable. Falta un carve-out de la precedencia de deferral.**

- **Tracker `E1` (`:134`)** lista los carve-outs canónicos (`prompt.ts:62`) como
  `FORK_SUBAGENT`(Agent) / `Brief` / **`SendUserFile`** → false.
- **SEPARACION `E1` (`:119`)** dice *«carve-outs (Agent/Brief)»*. **`SendUserFile` desaparece.**
- **Nota de honestidad:** la pérdida **empieza en el propio tracker** — su `TiR5` (`:480`) ya lista sólo
  `FORK_SUBAGENT`/`Brief`. SEPARACION heredó de la sección de remediación, no del grid. **No es un fallo del
  segundo salto**; es un fallo *interno* del primero que el segundo propagó.
- **Consecuencia:** `is_deferred_tool` se implementará con 2 carve-outs de 3 ⇒ `SendUserFile` quedará
  diferida cuando el canónico la carga siempre. Exactamente *«implementación parcial»*, del tamaño de una
  línea.
- **Remedio:** añadir `SendUserFile` en `E1` y en `TiR5` del tracker (los dos sitios).

---

**P4-09-4 · `A24` — pérdida BAJA. `ends_turn` se cae del canal tool→loop.**

- **Tracker `A24` (`:82`, corrección de 10·J)**: *«el loop SÍ aplica `context_modifier` … **y `ends_turn`
  (338-339) por ask_user/exit_plan**»*.
- **SEPARACION `A24` (`:79`)** conserva `context_modifier` y su cableado, y **no menciona `ends_turn`**.
- **Consecuencia:** el canal «resultado de tool que altera el control del loop» queda documentado a medias.
  `ends_turn` es el mecanismo por el que `ask_user`/`exit_plan` cierran el turno; sin declararlo, `D7`/
  `B-new_messages` se diseñará sólo para `new_messages` + `context_modifier`.
- **Remedio:** añadirlo a `A24`/`D7` con su ancla `agent_loop.py:338-339`.

### 2.3 Lo que la reconciliación NO encontró (declarado en positivo, L10)

- **Ningún ❌ del tracker degradado a 🔀 en SEPARACION.** Los seis CORE-GAP grandes (FIND-TOOL1/2/3/4/6/9)
  llegan con el mismo estado y el mismo peso; `§2.3` incluso nombra a FIND-TOOL2 *«el mayor gap de 09»*.
- **Ninguna celda perdida.** 70 de 70 tienen contraparte con TIER y destino.
- **Un cambio de estado, declarado:** `B2` 🟡→🔀, legítimo — recoge el refinamiento de la 2ª vuelta del
  tracker (huérfano B-interno, no deuda A↔B) y lo declara en `§2.4`.
- **Cuatro enriquecimientos reales**, todos productos de abrir B en A1.6, no de imaginar: el `PRE_TOOL_USE`
  input-aware vivo (que el tracker subdeclaraba), la precisión de `CancelledError`, el copy-safe de `E5`, la
  cadena `factory:210 → :228 → runtime:318 → bash:27`.

**Sobre la tesis previa:** `§3.2·b` decía que `DEUDA-A §2.8` *«corrompió»* lo que el tracker tenía. Medido:
`SEPARACION/09` conservó el cuerpo íntegro; quien corrompió fue **este documento en su columna transversal**,
y `DEUDA-A` amplificó. La diferencia importa porque cambia dónde hay que mirar en los 17 pares restantes.

---

## §3. Re-verificación de las 5 sondas de `§3.2·c` — mezclaban dos fallos distintos

Las 5 sondas se re-corrieron sobre **los 18 trackers y los 18 SEPARACION** (grep de ausencia = T-C,
legítimo para probar que algo no está):

| sonda | en los 18 trackers | en los 18 SEPARACION | especie |
|---|---|---|---|
| `resumeAgent` (05·E26/GAP-EXEC3) | ✅ sí | ✅ sí | — |
| `extractDiscoveredToolNames` (09·E5) | ✅ sí, completa | ✅ cuerpo sí / columna inventada | **DR-1** |
| task-notification | ✅ sí | ✅ sí | — |
| `filterUnresolvedToolUses` · `filterOrphanedThinkingOnlyMessages` · `filterWhitespaceOnlyAssistantMessages` | ❌ **0** | ❌ **0** | **DR-2** |
| `forkContextMessages` · `invocationKind` | ❌ **0** | ❌ **0** | **DR-2** |

*(Las únicas ocurrencias en todo el corpus están en `A-CIERRE-P1.md` y en el propio ledger — es decir, las
introdujo P1 al tabular `resumeAgent.ts`, no existían antes.)*

**⇒ `§3.2·c` conflaba dos defectos bajo un solo encabezado.** Son distintos en causa, en coste y en remedio:

- **DR-1 · regresión documental** (`tracker → SEPARACION`) — el contenido existe y se degrada al destilar.
  Forma dominante medida en 09: **invención en columna transversal** + **enumeración colapsada a puntero**.
  **Se arregla contra el tracker. Coste bajo. Es P4″.**
- **DR-2 · ausencia de origen** (`canónico → tracker`) — el sub-comportamiento **nunca entró** en el corpus.
  No es regresión: es alcance no cubierto por la fase 1. **Sólo se arregla contra `claude-code/src`, y es lo
  único que justifica abrir el canónico** (`D-01`: por excepción). **Es P6″.**

**La tabla de `§3.2·c` no era «3 conservadas / 2 perdidas» sobre un mismo eje.** Eran 3 casos de DR-1 (dos
limpios, uno degradado) y 2 casos de DR-2. Corregido en el ledger.

**Lo que esto NO permite decir todavía:** una muestra de 5 sondas + 1 par de 18 **no es una tasa**. Sigue sin
medirse cuántas fichas de DR-2 hay — y de eso depende el tamaño de P6″, que es la única incógnita real que
queda antes de Fase B.

---

## §4. Consecuencias para el resto de P4″

1. **Orden de lectura por par:** columnas transversales (`TIER`·`destino`·`id`) → §2.x (costuras/CORE-GAP/OI)
   → cuerpo. Es donde apareció el 100 % de lo grave en 09.
2. **Buscar activamente los dos patrones medidos**, no leer en general:
   - *enumeración → puntero*: toda ficha cuyo destino sea otra categoría (`→10`, `→11`, `→13/14/15`) y cuyo
     tracker traiga una lista nominal. `G9` y `F3` fueron ambas de este tipo.
   - *prosa → clasificación*: toda columna transversal sin ancla de código propia.
3. **Verificar la propagación a los rollups** en cada pérdida encontrada. La cadena de `E5` sólo hizo daño
   cuando `DEUDA-A` la cosechó; una pérdida no cosechada es barata, una cosechada llega a `00-BLUEPRINT`.
4. **Los 17 pares restantes siguen sin abrir.** 9.799 L de tracker + 6.237 L de SEPARACION.

---

## §5. GATEKEEPER (`00-LEGEND §3.3` — MOSTRADO)

**1. ¿Se leyó ÍNTEGRO lo que esta pasada afirma haber reconciliado?**
**Sí, y sólo eso.** `HOMOLOGATION/09-tools-infra.md` 1→492 (4 tramos, tope de tokens) y
`SEPARACION/09-tools-infra.md` 1→304 (2 tramos). `deferred.py` 1→44. `DEUDA-A` y el ledger, por tramos
dirigidos, **ambos ya 1→EOF en P0** y registrados. **Los otros 17 pares NO se abrieron y §0 lo dice en la
primera tabla, no en una nota al pie.**

**2. ¿Reconcilia el conteo?** **Sí.** 70 celdas en el tracker (A26·B7·C4·D10·E10·F4·G9), 70 con veredicto,
0 sin colocar: 61 + 4 + 4 + 1 = 70.

**3. ¿Cada afirmación de corrupción se apoya en el archivo abierto, no en grep ni en docstring?**
**Sí — y el hallazgo central es precisamente que alguien no lo hizo.** `agent_id` se declaró ausente tras
leer `deferred.py` entero (44 L) y contar 0 ocurrencias en el tracker (492 L). El grep se usó **sólo para
probar ausencia** (sondas DR-2), que es su uso legítimo.

**4. ¿La cara integrador quedó al mismo detalle?** **Sí.** `P4-09-2` no se quedó en el diagnóstico: el bloque
(e) está restituido en la ficha `F3` **y** subido al criterio de aceptación de `OI-20` (§2.5), que es donde el
integrador lo consume. Las **4 pérdidas están remediadas en el documento**, no sólo señaladas (§6·1).

**5. ¿Doble filo (L10)?** **Sí.** Se registran 4 enriquecimientos reales y se declara que **ningún ❌ fue
degradado** y **ninguna celda perdida** — el segundo salto de destilación es, en 09, **mayoritariamente
fiel**. Inflar 09·E5 a «el corpus está corrompido» habría sido padding en la dirección alarmista. Y en
sentido contrario: `§3.2·b` de mi propio ledger queda **corregido**, no defendido.

## §6. VEREDICTO

**⛔ PASADA ABIERTA — par 09 CERRADO (70/70 reconciliadas, 5 defectos, 5 remediados); 17 pares sin abrir.**

No se declara ✅ la pasada. Lo cerrado y lo abierto, separados:

**Cerrado, con edición aplicada (6 sitios):**
1. `E5` columna identidad — **retirada** del eje de identidad + nota ⚠ con los 4 eslabones (2 sitios).
2. `G9` — **17 rutas restituidas**, partidas por destino 12/13/14/15/integrador, con criterio de aceptación.
3. `F3` — **bloque (e) restituido** + subido al criterio de aceptación de `OI-20` (2 sitios).
4. `E1` — **`SendUserFile`** restituido en SEPARACION **y en el `TiR5` del tracker** (2 sitios).
5. `A24`/`D7` — **`ends_turn`** declarado como tercer portador del canal resultado→control-del-loop.

**Abierto, y no se cierra dando ninguno por descontado:**
1. **17 pares** por reconciliar — 9.799 L de tracker + 6.237 L de SEPARACION. Ninguno abierto.
2. **`A-CIERRE-LEDGER §3.2·b`/`·c`** por reescribir con la distinción DR-1/DR-2 *(se hace a continuación,
   en esta misma pasada — no se remite)*.
3. **La tasa de DR-2 sigue sin medir** ⇒ el tamaño de **P6″** sigue desconocido, y con él la suspensión de
   `§3.1·e` sigue sin poder levantarse. Ésta es la incógnita que gobierna si Fase B puede abrir.
   *(Actualizado en §7: el par 01 aporta los **5 primeros DR-2 fuera de las 5 sondas**. Sigue sin ser una tasa.)*

---

## §7. Reconciliación del par 01 · contracts — las 15 fichas

Leídos 1→EOF en esta pasada: `HOMOLOGATION/01-contracts.md` (198) y `SEPARACION/01-contracts.md` (114),
en ese orden y por **columna transversal primero**, como manda §4.1.

### 7.1 Saldo

| veredicto | nº | fichas |
|---|---|---|
| **CONSERVADA** | **9** | CTR-01, CTR-02, CTR-06, CTR-08, CTR-10, CTR-11, CTR-12, CTR-13, CTR-15 |
| **ENRIQUECIDA** (con **estado cambiado y no declarado**) | **1** | CTR-05 |
| **COMPRIMIDA-CON-PÉRDIDA** | **5** | CTR-03, CTR-04, CTR-07, CTR-09, CTR-14 |
| **INVENTADA** | **0** | — |
| **PERDIDA** (ficha sin destino) | **0** | — |

**15 = 9 + 1 + 5.** Los 15 features del tracker (feats 1-15) tienen contraparte 1:1 con `CTR-01..CTR-15`;
el conteo de `SEPARACION §3.2·Q2` (15 = 15 = 0) se sostiene al recontarlo.

**Tasa de pérdida: 5/15 (33 %) frente a 4/70 (6 %) en 09.** No es que 01 esté peor escrito: es que 01 es la
categoría **sin archivos-A propios** (contratos = seams inventados), así que **toda** su contraparte canónica
viaja como cita dentro de las celdas — y la cita es justo lo que la destilación no conserva. **Predicción
comprobable para el resto de P4″:** la pérdida escala con la densidad de citas canónicas del tracker, no con
su tamaño. `05·execution` (46 citas → **0** conservadas) es el siguiente candidato duro.

### 7.2 El hallazgo sistémico — `P4-01-1`: la columna canónica no se perdió, **no existe**

En 09 las pérdidas eran de celda (`G9`, `F3`). En 01 el defecto es **de esquema**: la tabla de §1 tiene siete
columnas —`ID · resumen · núcleo|cáscara · TIER · destino · nota-identidad · acción`— y **ninguna** para la
contraparte canónica, que era la 2ª columna del tracker. No se cayó una cita: se cayeron **las 15 a la vez**,
por construcción del formato.

Medido sobre los 18 pares (citas `*.ts`, `grep -o`, conteo bruto no-único):

| | trackers | SEPARACION | retención |
|---|---|---|---|
| citas canónicas | **1130** | **105** | **≈9 %** |
| pares en cero | — | **01 · 05 · 07** | — |

**Doble filo (L10), explícito:** esto **no** significa «se perdió el 91 % del contenido». SEPARACION destila
*hacia destinos de construcción*, y re-citar el canónico no era su trabajo declarado; el mecanismo y el
comportamiento sobreviven en la mayoría de las celdas (9 de 15 CONSERVADAS aquí, 61 de 70 en 09). Lo que la
cifra mide es **una cosa concreta y consecuente**: bajo la regla del 7º campo (*ninguna unidad entra en Fase B
sin ancla canónica*), **el 91 % de las anclas hay que ir a buscarlas al tracker**.

Y ahí está la conclusión **en positivo**, que es la útil: **están en el tracker.** 1130 citas. Anclar no exige
reabrir `claude-code/src` — exactamente lo que `D-01` decidió y lo que `§3.1` había presupuestado al revés
(≈86.237 L). **Restituir el puntero es P4″ y es barato; tabularlo como comportamientos (`D-02`) sigue siendo
P6″/T-A.** El `§1.1` que esta pasada añade a `SEPARACION/01` son **punteros, no anclas acreditadas**, y así
está rotulado allí.

### 7.3 Las 5 pérdidas, con lo que Fase B no podría implementar

**P4-01-2 · `CTR-03` — el shape del campo se vuelve más libre que el canónico.**
Tracker `:25`: `AgentTool.model: z.enum(['sonnet','opus','haiku'])` + sentinel `inherit`. SEPARACION: *«el
contrato expone el campo (alias/opaco)»*. Consecuencia: `model_override: str` libre, y la restricción canónica
desaparece del corpus (`sonnet|opus|haiku` = **0 ocurrencias** en los 18 SEPARACION **y** en `16-models`).
Es una decisión de **shape T1**, la más cara de revertir. *Anti-padding:* `getAgentModel` y `inherit` **sí**
sobreviven —y mejor— en `05·E2` (✅ cableado, `agents.py:46-58`), así que el puntero de CTR-03 («se diseña en
05») estaba además **desactualizado**: no está pendiente, está hecho. `isCoordinatorMode`→undefined es
legítimamente ⛔ por `04·A1`. **Remediado:** enum+sentinel restituidos, puntero corregido.

**P4-01-3 · `CTR-04` — desaparece que en el canónico el fork **no se pide con un flag**.**
Tracker `:26`: fork implícito **por omisión de `subagent_type`**, con sentinel `FORK_SUBAGENT_TYPE='fork'`.
SEPARACION conserva el 🔀 pero no el mecanismo; `FORK_SUBAGENT` = **0 ocurrencias** en los 18 SEPARACION.
Consecuencia: se congela `fork_context: bool` como shape T1 sin haber comparado con la alternativa canónica.
La byte-identidad y el guard sí están (y enriquecidos) en `05·E13`/`E14`. **Remediado in situ.**

**P4-01-4 · `CTR-05` — endurecimiento ✅\*→CORE-GAP sin declarar.** *(no es pérdida de contenido; es la
columna transversal otra vez, y por eso va aquí)*
El tracker `:27` daba el autogen `user_<hex>`/`sess_<hex>` por **✅\* adición correcta**; la ficha lo reescribe
como **mímica de single-user a ripear**, sobre la misma línea `runtime.py:208-209` y sin evidencia nueva. Es
**la misma especie que `09·E5`** (prosa del nivel N → hecho estructural en N+1 → obligación en N+2: aquí
`DEUDA-A·ID-1` 🔒, el primer ítem del hilo de identidad).
**La diferencia con `E5` es el desenlace, y es la lección:** al abrir `DEUDA-A §0.1b·H-1` resulta **corroborado
de primera mano** — `MemoryProvider._scope` keya por `f"{user_id}/{agent}"` (`provider.py:61-63`) y el autogen
da un uuid nuevo **por dispatch**, así que la memoria del agente principal se escribe en un directorio distinto
cada vez. **El veredicto se sostiene; lo que faltaba era declarar el cambio.** ⇒ **endurecer no es *per se*
inventar: la diferencia es si alguien abrió el archivo.** `E5` no lo abrió (y era falso); `H-1` sí (y era
cierto). **Remediado:** §2.3b nuevo en `SEPARACION/01` — sección de cambios-de-estado-declarados, que la ficha
no tenía y 09 sí (`§2.4`).

**P4-01-5 · `CTR-07` — los scopes de permiso canónicos: 4 → 3 → 0.**
Tracker `:29`/`:181`: `alwaysAllowRules`/`alwaysDenyRules` con **cuatro** scopes nominales
`command`/`project`/`localSettings`/`userSettings`, y el mapeo real de B (los colapsa a **dos**:
`command` persistente / `session` volátil). SEPARACION deja *«project/user/local»* en una nota-identidad —tres,
aproximados— y pierde el mapeo. **`localSettings`/`userSettings` = 0 ocurrencias en los 18 SEPARACION.**
Consecuencia exacta: `OI-4` pedía al integrador *«persistir reglas por scope»* con un criterio de aceptación
que **una implementación de 2 scopes aprueba**. **Remediado:** los 4 nombres restituidos + el criterio de
aceptación de `OI-4` reescrito para que distinga los cuatro (y suspenda al que colapse, que es lo que B hace).

**P4-01-6 · `CTR-09` — `services/compact/`: 8 sub-servicios → «el motor».** *(el mayor, y el único que toca P6″)*
Tracker `:31` enumera `auto` · `micro` · `api-micro` · `sessionMemory` · `timeBased` · `postCleanup` ·
`grouping` · `prompt`. SEPARACION: *«el motor (trigger/estrategia/presupuesto) es CORE-GAP homed en 02»* —
patrón **enumeración→puntero**, idéntico a `G9`. Contrastado con el destino: `SEPARACION/02 §2.2` describe la
battery `compaction` por sus propias features (B1-B7, B9, C9, D1), lo que cubre `auto`(B6) y `micro`(B4);
`sessionMemory` vive en 13. **Los otros cinco —`api-micro`, `timeBased`, `postCleanup`, `grouping`, `prompt`—
tienen 0 ocurrencias en los 18 trackers Y en los 18 SEPARACION.**
⇒ **especie mixta, y hay que decirlo separado:** los **nombres** son DR-1 (estaban en el tracker 01, se
perdieron al destilar → restituidos aquí); el **comportamiento** es **DR-2** (nunca entró en el corpus; ningún
tracker los caracterizó) → **P6″, contra `claude-code/src`, por la excepción de `D-01`**. Son los **5 primeros
DR-2 identificados fuera de las 5 sondas de `§3.2·c`**.

**P4-01-7 · `CTR-14` — el hijo-fork arranca con 200 turnos, y eso se cayó en los dos destilados.**
Tracker `01:36` y tracker `05:51` traen `forkSubagent.ts:65` = **`maxTurns: 200`**. Ni `SEPARACION/01·CTR-14`
ni `SEPARACION/05·E16` lo conservan. Consecuencia: al cablear `max_turns` (FIND-EXEC5) el fork heredaría el
tope del padre o el `_MAX_TURNS=50`, cuando el canónico le da 200 propios. **Es el patrón `SendUserFile` de
09·`P4-09-3` repetido: la pérdida ocurre en dos destilados independientes del mismo dato.** *Anti-padding:* la
precedencia `maxTurns ?? agentDefinition.maxTurns` y el frontmatter de `loadAgentsDir` **sí** sobreviven, y
enriquecidos, en `05·E16`/`E28`. **Remediado en los dos sitios.**

### 7.4 Lo que la reconciliación NO encontró (en positivo, L10)

- **0 INVENTADAS.** La columna `nota-identidad` —el vector que falló en `09·E5`— aquí es **fiel en las 8 fichas
  que la llevan**: `eje ejecución` (CTR-04/CTR-15), `eje persistencia` (CTR-07/CTR-09/CTR-10), `persist+ejec ·
  id opaco+repo` (CTR-05), y el honesto *«— (arg `session` roza identidad)»* de CTR-12. Ninguna afirma un
  mecanismo; todas asignan un eje. **La lección de `E5` no se generaliza a «las columnas mienten»**: miente la
  columna que afirma *cómo funciona algo* sin abrirlo.
- **0 PERDIDAS.** Las 15 fichas tienen TIER y destino.
- **Ningún ❌ degradado a 🔀.** `CTR-08` (GAP-02) sigue CORE-GAP; `CTR-12` (GAP-01) sigue CORE-GAP de cableado.
- **Ninguna deuda inflada.** `CTR-11` (`to_llm`), `CTR-13` (`@runtime_checkable`), `CTR-15` (`arm_watchdog`
  no-op) se mantienen **DEUDA-B interna**, no A↔B — el juicio L10 del tracker viajó intacto.
- **La cara integrador se ENRIQUECIÓ:** `OI-1..OI-5` con los 6 campos L05 **no existen en el tracker**. Es
  producto legítimo del segundo salto, no destilación.

### 7.5 Dos sub-pérdidas menores, remediadas sin ficha propia

- **`CTR-08`**: el shape de CR1 quedó tras el puntero «CR1» — se perdían **2 de sus 3 campos**
  (`additional_working_directories`, `pre_plan_mode`). Traídos del tracker `:150-152`.
- **`CTR-12`**: el punto y la secuencia de cableado quedaron tras «CR2» — traídos del tracker `:161-167`
  (`agent_loop.py:176-179`, orden expand→inline→slash→cortar-turno, firma 5-arg).
- **Los nombres de los 4 tests `xfail`** que ya codifican los targets (el 6º campo de L05) no aparecían en
  ninguna ficha. Restituidos en `§1.1`.

### 7.6 Consecuencias que se añaden a §4

5. **Tercer patrón, de esquema y no de celda:** *columna que la tabla de destino no tiene*. Se detecta
   comparando **encabezados**, no contenidos, y cuesta un `grep -c` por par. Aplicarlo primero en cada par
   restante: es O(1) y en 01 destapó las 15 celdas de una vez.
6. **Cuarto: cambio de estado no declarado** (`✅→gap` o `gap→🔀`). El par 09 tenía su §2.4 para esto; 01 no la
   tenía. **Comprobar en cada par que existe la sección de cambios declarados**, y si falta, reconstruirla
   comparando los símbolos de estado ficha a ficha.
7. **Un puntero también se degrada por quedar rancio** (`CTR-03`: «se diseña en 05» cuando `05·E2` ya lo daba
   ✅ cableado). Al verificar propagación (§4.3) hay que mirar **el veredicto** del destino, no sólo si el
   contenido llegó.

---

## §8. Par **05 · execution** — tracker 510 L · SEPARACION 236 L · 36 fichas (E1-E36)

**Predicción del usuario al abrirlo:** *«46 citas canónicas → 0 conservadas = máximo riesgo predicho»*.
**Confirmada, y con el mecanismo ya explicado por `§7.2·P4-01-1`:** la tabla de SEPARACION **no tiene columna de
contraparte canónica** (encabezados `| ID | resumen | núcleo|cáscara-CLI | TIER | destino | nota-identidad | acción |`
frente a `| # | Feature (canónico) | Runtime | Estado | Nota |`), luego las citas no cabían. Retención `.ts` = **46 → 1**
(y esa única superviviente había sido restituida por `§7·P4-01-7`, no sobrevivió sola).

### 8.1 Saldo (36 celdas)

| veredicto | n | fichas |
|---|---|---|
| **CONSERVADA** | 27 | E1·E2·E4·E6·E10·E11·E12·E15·E17·E19·E21·E22·E23·E25·E27·E28·E29·E30·E31·E34·E35·E36 + §AgentDefinition (12 campos) |
| **ENRIQUECIDA** (verificada en código) | 1 | E3/E8 — columna de identidad |
| **COMPRIMIDA-CON-PÉRDIDA** | 8 | E20 · E18 · E13/E14 · E9/E32 · `disallowedTools` · §2.1 usage · E33 · E7 |
| **INVENTADA** | **0** | — |
| **PERDIDA** (sin TIER ni destino) | **0** | 36/36 colocadas |

**Las 8 pérdidas están remediadas in situ** (L05: desarrollada, no diferida), rotuladas `P4-05-1..8` en
`SEPARACION/05-execution.md`. Más `P4-05-9` (§1.1, criterio de aceptación) = **9 remediaciones, 15 ediciones**.

### 8.2 Las 8 pérdidas, con su consecuencia (no con su etiqueta)

1. **`P4-05-1` · E20 — algoritmo de permisos: 5 pasos → 3.** Se perdieron **(c)** `awaitAutomatedChecksBeforeDialog`
   (async + puede-mostrar espera los checks automáticos antes de abrir diálogo) y **(e)** el override de `effort`.
   Consecuencia: se habría implementado un gate de permisos que abre diálogo antes de tiempo.
2. **`P4-05-2` · E18 — trailer: 3 → 1.** El destilado sólo conservó el trailer **sync**. Perdidos: el mapeo propio de
   `async_launched` (hint + `output_file` + `canReadOutputFile` + guía «no dupliques el trabajo») y la **condición**
   del skip one-shot (*sólo si NO hay worktree*), más el `task_notification` por canal SDK (`enqueueSdkEvent`)
   **distinto** del canal del LLM-loop. Consecuencia: el resultado que ve el modelo padre al lanzar en background
   habría salido vacío de instrucciones.
3. **`P4-05-3` · E13/E14 — `FORK_AGENT`: 4 campos → 1.** Sólo sobrevivió `maxTurns:200` (y por rebote de `P4-01-7`).
   Perdidos `tools:['*']`, `model:'inherit'`, `permissionMode:'bubble'`. Consecuencia: `bubble` es **entrada** del
   algoritmo (b) de E20 — sin él, el fork no bubblea permisos al padre y E20 se implementa contra un caso que no se
   ejercita.
4. **`P4-05-4` · E9/E32 — enumeración→puntero.** «faltan `type`» perdió que `TaskType` son **7 tipos** y que
   `generateTaskId` = **prefijo-por-tipo + `randomBytes` base36⁸**, es decir que **el tipo es legible desde el id**
   (que es lo que hace barato el `getTaskByType().kill()` de E32). También se perdió `endTime`.
5. **`P4-05-5` · `disallowedTools` — 4 reglas → «añadir denylist».** Perdidas las tres denylists distintas
   (`ALL_AGENT_*` vs `CUSTOM_AGENT_*` — el pool **depende de si el agente es builtin**) y las 2 excepciones
   (`ExitPlanMode` en plan mode, MCP siempre).
6. **`P4-05-6` · §2.1 usage — el shape entero.** Decía «usage» sin un solo campo. Perdidos los 7 campos y, sobre todo,
   la **regla de agregación asimétrica**: `latestInputTokens` se **queda con el último** (la API lo devuelve
   acumulativo) y `cumulativeOutputTokens` **se suma**. Consecuencia: sumar el input es el bug más natural del mundo
   y produce doble conteo en cada turno — con `maxBudgetUsd` colgando de ahí.
7. **`P4-05-7` · E33 — el disparador sin el mecanismo.** Se conservó `autoBackgroundMs` 120s y se perdió **cómo se
   desengancha**: `Promise.race(next-message, background-signal)` → `agentIterator.return()` → closure detached →
   `enqueueAgentNotification` → retorna `async_launched`. Lo conservado es lo obvio; lo perdido, lo difícil.
8. **`P4-05-8` · E7 — nombre canónico borrado.** `recordSidechainTranscript` → «`_persist`→`StorageKeys`». Con el
   nombre se fue la **relación padre↔hijo** (es un *sidechain* del transcript del padre), que es justo lo que 15
   necesita para modelar la clave.

### 8.3 **Cuatro veredictos invertidos aguas abajo** — el patrón 4 en su forma severa

Esta es la aportación del par 05 al método. Las 4 fichas eran **fieles a su tracker** y aun así son **falsas hoy**,
porque un rollup posterior invirtió el veredicto **sin volver a tocar el doc de categoría**. Están tabuladas en la
nueva **`SEPARACION/05-execution.md §2.6`** (R1-R4): E5/LAT-EXEC2 → **CORE-GAP `H-5`** (nadie drena el canal ⇒ el
padre nunca sabe que su hijo terminó; 5 sitios corregidos) · E24 → **inyección `ctx.runner`**, no `set_runner`
(`DB-27`/`DB-23`: cablearlo habría construido el global que otra decisión manda borrar; 4 sitios) ·
`B-registry-dual-path` **subdeclarado** (`DB-04`/`DB-h1`: no es riesgo latente, **las 6 Task\* tools fallan siempre
hoy**) · E26 → `AC-05` **ya cerrado** con 14 comportamientos anclados + bloqueante `AC-h4`.

**Los 4 se detectaron abriendo `DEUDA-B` y `A-CIERRE-P1`, no leyendo `05`.** Un doc de categoría no es la última
palabra sobre sus propias fichas.

### 8.4 Lo que **NO** se perdió (anti-padding en positivo, L10)

`totalPausedMs` sí aterrizó (en 08·SIG6) · `maxBudgetUsd` en 02/03/07 · `SyntheticOutputTool`/structured-output en
10/02/09/16 · el descarte `utils/tasks.ts` en 10 · `ExitPlanMode` en 14/10 · las 36 fichas tienen TIER **y** destino
(0 perdidas) · las notas de identidad de E3/E8 (`session_id`/`user_id`/`subagent_depth`) **no son invención**: se
verificaron abriendo `execution/fork/__init__.py` **1→EOF**, donde `ForkSnapshot:36-38` las declara literalmente.
**Este par tiene 0 INVENTADAS** — el defecto de `09·E5` no se repite aquí.

### 8.5 Consecuencias que se añaden a §4/§7.6

8. **El patrón 4 tiene una forma severa: no «el destilado cambió el estado», sino «el estado cambió DEBAJO del
   destilado».** No se caza comparando las dos caras del par —ambas coinciden— sino cruzando la ficha con los
   rollups transversales. **Añadir a cada par restante un cruce contra `DEUDA-A`/`DEUDA-B`/`BATTERIES`/`P0`/`P1`.**
   En 05 fueron 4 de 36 fichas (11 %); a esa tasa quedan ~30 inversiones en los 15 pares restantes.
9. **La compresión ataca preferentemente el mecanismo y conserva el disparador** (pérdidas 2, 6, 7). Un destilado
   dice *qué* pasa y pierde *cómo*; lo primero se re-deriva, lo segundo no. **Al leer por columnas, sospechar de
   toda celda que nombre un umbral, un flag o un evento sin decir qué lo consume.**
10. **La sección de criterio de aceptación se pierde entera, no por celdas** (`P4-05-9`): 13 nombres de test + el
    estado xfail-strict, desaparecidos de un archivo que conserva 36 fichas. **Y el xfail-strict era el único
    mecanismo del corpus que detecta un doc rancio desde el código** — precisamente el defecto de §8.3.
    **Comprobar en cada par restante si el tracker tenía §Evidencia y si sobrevivió.**

---

## §9. Par **02 · loop** — reconciliado 1→EOF por ambas caras (4/18)

**Lecturas de este par** (`EVIDENCIA.log` 150→153): `HOMOLOGATION/02-loop.md` **1→EOF (365)** ·
`SEPARACION/02-loop.md` **1→EOF (250)** · `agentic_runtime/loop/agent_loop.py` **1→EOF (353)**
(este último *para qué*: resolver `F8`, no como inventario).

### 9.0 Patrón 3 aplicado primero (encabezados, O(1)) — tercera confirmación de `P4-01-1`

| capa | encabezado de tabla |
|---|---|
| tracker | `# · Feature canónica · Runtime · Estado · Diferencia / ajuste holístico` |
| SEPARACION | `ID · resumen · núcleo\|cáscara-CLI · TIER · destino · nota-identidad · acción` |

La columna **`Feature canónica` no tiene sucesora**. Retención de citas `.ts`: **23 → 1** (y la única
superviviente es prosa de §Naturaleza, no un ancla). Desaparece entero el bloque de anclas del ledger del
tracker (`:270-272`): `yieldMissingToolResultBlocks`:123/984 · `maxTurns`/`max_turns_reached`:1508-1511/1705-1711 ·
`attemptWithFallback`:650-655/894-897 · `microcompact`/`autocompact`/`getMessagesAfterCompactBoundary`:52/365/413 ·
reason codes:1051/1175/1515/1520/1711. Tercer par consecutivo con el mismo defecto **de esquema** (01: 1130→105;
05: 46→1) ⇒ `P4-01-1` deja de ser hallazgo y pasa a ser **la premisa de P6″**.

### 9.1 Saldo — **60/60 celdas**

| veredicto | n | fichas |
|---|---|---|
| CONSERVADA | 41 | A1·A2·A3·B1-B5·B7-B9·C1·C3·C5-C9·C11·D2-D4·D6·D7·E1·E2·E6·F1·F2·F4-F6·F10-F14·G4·G5·G6 |
| ENRIQUECIDA (verificada) | 4 | A5 · C10 · G2 · G3 |
| **COMPRIMIDA-CON-PÉRDIDA** | **15** | A4·B6·B10·C2·C4·C12·D1·D5·E3·E4·E5·F3·F8·F9·G1 |
| INVENTADA | **0** | — |
| PERDIDA (sin colocar) | **0** | las 60 tienen fila en el ledger §3.1 |

**Las 4 ENRIQUECIDAS se verificaron abriendo el destino, no el puntero:** `A5`→`01·CTR-14` + `05·E16`
(ambas fichas existen y ya cargan `forkSubagent.ts:65 maxTurns=200`) · `G2`/`G3` ganan la **cara integrador**
que el tracker no tiene (OI-8/OI-9 con los 6 campos L05) · `C10` gana el corte contrato-de-imagen ↔ handling.

**Las 0 INVENTADAS se acreditaron** contrastando las **20 anclas** de `SEPARACION/02` contra `agent_loop.py`
1→EOF: `24/185` (`_MAX_TURNS`) · `49-63` (DI) · `112-130/218` (recall) · `143-146` (capability) · `173/186`
(abort) · `179` · `189` (punto LR1) · `194`/`201-205` (path legacy) · `195` (pool por turno) · `227-239`
(`complete`) · `247-281` · `253-254` (`done.usage` no leído) · `267-270` vs `272-281` · `287-323`/`287-344` ·
`293` (docstring `plan_mode`) · `300-313` · `332-337` · `338-339` · `348-349`. **Las 20 son exactas.**

### 9.2 Las 15 pérdidas (`P4-02-1..15`) — remediadas *in situ* en `SEPARACION/02-loop.md`

1. **`P4-02-1` · A4 — 9 reason codes → 6 y una elipsis.** Se perdieron `stop_hook_prevented`, `blocking_limit`,
   `image_error`. No es cosmético: **`blocking_limit` es la salida de B9 y `image_error` la de C10**, ambas fichas
   vivas del mismo documento ⇒ la elipsis cortó el enlace entre el enum de terminación y dos gaps que lo alimentan.
2. **`P4-02-2` · B6 — el mecanismo del motor.** Perdidos `consecutiveFailures` (circuit-breaker),
   `AutoCompactTrackingState` y `tengu_auto_compact_succeeded`; además el destilado **sustituyó** ese evento
   canónico por `compact_boundary` (07·H1), que es otra cosa (telemetría de éxito ≠ emisión de frontera). Y se
   perdió el **carve-out** que impide el error de reutilización más probable: *`execution/local/summarizer.py`
   sólo condensa el OUTPUT de un subagente background, **no** la historia del turno*. Consecuencia 9 en estado puro.
3. **`P4-02-3` · B10 — `finalContextTokensFromLastResponse`.** Sobrevivió `tokenCountWithEstimation` (el camino
   caro) y se perdió el barato: tomar el conteo de la última respuesta en vez de estimarlo.
4. **`P4-02-4` · C2 — 10 opciones → 7, y la firma actual.** Perdidos `advisorModel`, `queryTracking` y
   **`maxOutputTokensOverride`** — que es justamente el mando que ejecuta la recuperación de **D2** (escalar
   8k→64k): sin él, D2 queda descrita sin el parámetro que la hace posible. Perdida también la firma viva
   `complete(messages,tools,stop,model_id,system_sections?,system_override?)`, el punto de partida de la ampliación.
5. **`P4-02-5` · C4 — «descartando parciales» sin el cómo.** El tracker dice **tombstones de mensajes huérfanos +
   `stripSignatureBlocks`**; el destilado deja «descartar parciales (respeta C11)».
6. **`P4-02-6` · C12 — `accumulateUsage`.** Sobrevive `updateUsage`; se pierde el acumulador. **Cruce obligado con
   `P4-05-6`**: la agregación es **asimétrica** (`latestInputTokens` se queda con el último, `cumulativeOutputTokens`
   se suma). Las tres fichas de 02 que mandan acumular usage (C12/B10/G4) no lo decían.
7. **`P4-02-7` · D1 — «single-shot cada uno».** Perdida la guarda anti-bucle de las dos rutas de recuperación PTL.
8. **`P4-02-8` · D5 — `stopHookActive`.** Perdido el nombre de la guarda de re-entrada, que es exactamente lo que
   impide que `preventContinuation` haga girar el loop para siempre.
9. **`P4-02-9` · E3 — la evidencia de que es opt-in.** Perdidos `feature('COORDINATOR_MODE')`, el env
   `CLAUDE_CODE_COORDINATOR_MODE`, los dos archivos (`coordinator/coordinatorMode.ts`,
   `utils/swarm/inProcessRunner.ts`) y 2 de las 4 INTERNAL_WORKER_TOOLS (`TeamDelete`, `SyntheticOutput`).
   Sin los gates, el ⛔ de OI-10 pierde su justificación verificable.
10. **`P4-02-10` · E4 — dos comportamientos no-UI dentro de un ⛔ de UI.** Perdidos `saveCacheSafeParams` y
    `cleanupComputerUseAfterTurn`: **no son bookkeeping de interfaz**, son limpieza de estado real al cerrar turno.
    ⚠ **doble filo (L10)**: el ⛔ de la fila puede estar sobre-extendido; queda marcado, no resuelto.
11. **`P4-02-11` · E5 — el snapshot de `sessionId`, con la nota de identidad en «—».** Perdidos el
    **snapshot `sessionId`** de `buildQueryConfig` y el gate `emitToolUseSummaries`. Es la **especie de `09·E5`
    en el sentido contrario**: allí la columna de identidad *inventó*, aquí *omitió* — y el eje afectado es el
    mismo (K4/ID-5). El único caso del par en que la nota-identidad debía decir algo y dice «—».
12. **`P4-02-12` · F3 — el fallback `runTools` del propio canónico.** Su pérdida cambia la lectura de la fila: el
    dispatch secuencial de B no es sólo «correcto pero más lento», es **un modo que el canónico también tiene**.
13. **`P4-02-13` · F8 — `getCommandsByMaxPriority` y la exclusión de slash.** Se conservó *qué* se drena y se
    perdieron la **prioridad** y el **filtro**. (La fila tiene además una inversión de estado: §9.3·I1.)
14. **`P4-02-14` · F9 — el criterio del dedup canónico.** Perdido `readFileState`: el canónico deduplica contra
    **ficheros ya leídos**, el runtime contra **la historia de mensajes**. No es el mismo criterio, y el destilado
    concluye «efecto cercano» tras haber borrado justamente aquello en lo que difieren. ⚠ doble filo.
15. **`P4-02-15` · G1 — `resultText` de comandos locales.** Perdido el **camino de retorno**: un comando local no
    sólo intercepta el turno, puede producir texto que alimenta el turno. Es lo que hace que `01·CR2` («si devuelve
    resultado terminal, cortar el turno») tenga algo que devolver.

### 9.3 **Cinco veredictos invertidos aguas abajo** (consecuencia 8) — tabulados en `02-loop.md §2.6`

| # | ficha | decía | dice hoy la evidencia |
|---|---|---|---|
| **I1** | `F8` | 🔀 *«drain al INICIO del turno … consumidor real»* | **CORE-GAP `H-5`**. `agent_loop.py:83` nace con `_turn_start_hooks = []`; el único registrador del base es `runtime.py:371-374`, y sólo re-emite hooks **suministrados por el integrador** (`root_turn_start_hooks is not None`). `drain_notifications`/`process_background_notification` **no tienen caller**. Concuerda con `RV-7`/`DB-29`/`AC-07` y con `SEAMS §S21` («put sí, drain INEXISTENTE») y `05·§2.6·R1`. **Segundo error en la misma celda:** `_run_turn_start_hooks()` se invoca en `:176`, **antes** del `for` de `:185` ⇒ se dispara **una vez por `run()`, no al inicio de cada turno** — el placement que la fila declara divergente ni siquiera es el que el código tiene |
| **I2** | `C12`/`B10`/`G4`/§2.1/§2.4 | «= DEUDA-B `B-usage`» | **CORE-GAP**. Recalificado por `07·§2.4` y ratificado en `DEUDA-B §·fila 6` (residual → `DB-14`/`DB-15`) |
| **I3** | `F2`/§2.3/§2.4 | «parte hack = DEUDA-B `B-02`» | **CORE-GAP = GAP-02/K1** (`DEUDA-B §·fila 1`); sólo el canal no tipado `app_state.native["plan_mode"]` queda como DEUDA-B, y renombrado **`DB-19`**, secuenciado tras K1 |
| **I4** | §2.2 batteries | 5 nombres libres + «error-recovery NO es battery» | `BATTERIES.md:166` asigna a 02 los IDs **B01·B04·B05·B07**, `memory` es *alimentada*, y `DEUDA-A:349` da a **`B02 resilience`** hogar **02·loop**. La nota es media verdad: el esqueleto resiliente es base, **la política de reintento sí es battery** (`BATTERIES.md:279`) |
| **I5** | §3.2·Q5 y §3.3 | «`B-usage`/`B-02`/path-legacy son DEUDA-B interna, **NO** deuda A↔B» | **falso para 2 de 3** por I2/I3 ⇒ la propia pregunta de doble filo daba un falso negativo. `path-legacy`→`18·FaR2` **sí** se sostiene (y gana el acople `18·N1`: borrarlo rompe `create_loop`) |

Tasa: **5/60 = 8,3 %**, del mismo orden que el 11 % de 05 ⇒ la estimación de ~30 inversiones en los pares
restantes se sostiene.

### 9.4 Consecuencia 10 — el tracker **sí** tenía §Evidencia y **no** sobrevivió (`P4-02-16`)

`HOMOLOGATION/02-loop.md:25-35` lleva `## Evidencia ejecutada`: lint (`ruff`/`mypy` 5 archivos/`bandit`),
**`14 passed, 5 xfailed`**, el desglose de los sintéticos y del e2e, y **8 nombres de test**
(`test_loop_accepts_configurable_max_turns` · `test_loop_wires_compaction_engine` ·
`test_loop_accepts_fallback_model` · `test_loop_fires_stop_hook_at_turn_end` · `test_loop_compacts_when_over_budget` ·
`test_loop_retries_then_fallbacks` · `test_stop_hook_can_continue_loop` · `test_loop_homologation`).
**En `SEPARACION/02-loop.md` había 0 de esos 8 y ninguna sección de criterio de aceptación.** Idéntico a
`P4-05-9` ⇒ **2 de 2 pares con §Evidencia la han perdido entera**; deja de ser incidencia y pasa a ser
**defecto de esquema del destilado** (como la columna canónica). Restituida en `§1.0`.

### 9.5 Dos defectos en la **capa tracker** (no son DR-1: la pérdida no empieza en el destilado)

- **`P4-02-17` · el swap de GAP-IDs se corrigió en 3 caras de 4.** La `§Nota de honestidad (2ª vuelta)` declara
  corregido el intercambio «en las 3 caras», pero `§Evidencia ejecutada:34-35` sigue diciendo *«GAP-L3 fallback
  model»* cuando GAP-L3 es el token-budget y el fallback es **GAP-C4**. La cara que no se revisó es justamente la
  que el destilado luego no copió — el error sobrevivió porque nadie volvió a leerla.
- **`P4-02-18` · el conteo está mal en las dos capas, con errores independientes.** El tracker declara «Sobre
  **46** features» (y su tally por estado suma 52); `SEPARACION` declara **54** en cuatro sitios (línea 4, título
  §3.1, Q2, §3.3) **mientras su propio desglose de Q2 suma 60**: `5+10+12+7+6+14+6`. Las filas reales son **60**.
  Y el error ya se **propagó**: `05·§3.2·Q2` cita «02·loop "~46" vs 54 reales» como precedente. Corregidos los
  cinco sitios (4 en 02 + 1 en 05).
- **`F8` nació sobre-declarada en el tracker**, no en el destilado: la re-visita L09 (`:322`) escribió «consumidor
  real» tras abrir `runtime.py:372-374` **sin abrir quién suministra `root_turn_start_hooks`**. `SEPARACION` fue
  **fiel**; por eso I1 es patrón 4 severo y no invención — y por eso sólo el cruce con los rollups lo caza.

### 9.6 Lo que **NO** se perdió (anti-padding, L10)

Las 60 fichas tienen TIER **y** destino · C11/FIND-L1 conserva **íntegro** el razonamiento de buffer-then-commit
con sus tres tramos de línea y su «sin remediación (L10)» — la ficha más difícil del par es la mejor conservada ·
los 4 motores siguen ❌ sin degradarse a 🔀 · los 5 productores de `context_modifier` y los 2 de `ends_turn`
llegaron con nombre y línea · la corrección de honestidad de Q3 (evidencia heredada → propia) sobrevivió ·
`G2`/`G3` **mejoraron** al ganar cara de integrador. **La destilación de 02 es fiel en el cuerpo y pierde en los
márgenes**: enumeraciones, gates y nombres canónicos — exactamente el perfil medido en 01 y 05.

### 9.7 Consecuencias que se añaden a §4/§7.6/§8.5

11. **Un error aritmético se propaga entre documentos antes que un error conceptual.** El «54» de 02 llegó a 05
    como dato de apoyo en **11 días** sin que nadie sumara los siete addendos que estaban escritos al lado.
    ⇒ **en cada par, sumar los addendos del propio Q2 antes de creerse el total** (coste: una suma).
12. **La §Evidencia se pierde entera en 2 de 2 pares que la tenían** ⇒ dejar de tratarlo como incidencia:
    **el destilado no tiene ranura para el criterio de aceptación**, igual que no la tiene para la columna
    canónica. Son los dos agujeros estructurales del esquema de SEPARACION.
13. **Una corrección que se aplica «en las N caras» debe enumerar las N caras** (`P4-02-17`): el tracker dijo 3 y
    eran 4, y la no enumerada es la que sobrevivió con el error hasta hoy.

---

## §10. Par **03 · context** — tracker 313 L · SEPARACION 256 L · 64 fichas (5/18)

**Ambas caras 1→EOF en esta pasada** (`EVIDENCIA.log` 156-160, escritas al TERMINAR cada lectura — REGLA 2).

### 10.1 Saldo

| veredicto | nº | fichas |
|---|---|---|
| CONSERVADA | 46 | resto |
| ENRIQUECIDA | 7 | A4, A23, A33, A+, E7, F1, F2 |
| **COMPRIMIDA-CON-PÉRDIDA** | **11** | A5, A6, A7, A12, A24, A25, B2, B3, B5, D2, E1 |
| **INVENTADA** | **0** | — |
| PERDIDA | 0 | — |

**46 + 7 + 11 = 64** ✅ — y el conteo del propio Q2 **se sumó** en lugar de creerse (consecuencia 11):
33 (A1-A33) + 1 (A+) + 12 (B) + 3 (C) + 2 (D) + 8 (E) + 5 (F) = **64**. A diferencia de `02` (declaraba 54,
reales 60), aquí **no hay error aritmético que propagar**.

**Las 0 INVENTADAS se acreditan**, no se declaran: las anclas canónicas del destilado se contrastaron una a una
contra las del tracker (`Tool.ts:181` freshness-guard · `:246` nested-memory · `:123-138`/`:124` permissions ·
`:330` · `AppStateStore.ts:109` + `getDefaultAppState:500-503` · `forkedAgent.ts:345-462`) — **todas exactas**.

### 10.2 Las 11 pérdidas — remediadas *in situ* en `SEPARACION/03-context.md`

| # | ficha | qué se perdió | patrón |
|---|---|---|---|
| `P4-03-1` | **A5** `readFileState` | el **doble consumidor** (freshness-guard *y* dedup de nested-memory), el hecho B de que `FileEditTool` *«lee y reemplaza sin verificar lectura previa ni mtime»*, y la firma exacta de CtxR1 | 1 enumeración→puntero |
| `P4-03-2` | **A6** `setAppState` | el **invariante canónico**: es **no-op para subagentes async** — y es *la razón de existir* de A7 | 5 mecanismo→disparador |
| `P4-03-3` | **A7** | «registro **Y kill**» quedó en «registro»; y el porqué (A6) | 1 |
| `P4-03-4` | **A12** | `effortValue` y `advisorModel` desaparecidos del título | 1 |
| `P4-03-5` | **A24** | los 2 nombres de campo (`nestedMemoryAttachmentTriggers`, `loadedNestedMemoryPaths`) | 1 |
| `P4-03-6` | **A25** | `dynamicSkillDirTriggers` + `discoveredSkillNames` — y **`discoveredSkillNames` es el discovered-set** del eje `DEUDA-A §2.8·H-4` / `09·E5` | 1 (+ pérdida de nexo transversal) |
| `P4-03-7` | **B2** | el **shape canónico entero** de `toolPermissionContext`: faltan **5 campos, no 1** (`alwaysAskRules` = sin canal HITL, `additionalWorkingDirectories`, `isBypassPermissionsModeAvailable`, `prePlanMode`, además de `mode`) y el shape real de B (3 campos) | 1 — **la más grave** |
| `P4-03-8` | **D2** | el **segundo choke point `runtime.py:244` (stream TTS)** y el test que lo fija (`test_choke_point_covers_messages_and_bus`) ⇒ quien implemente el saneo habría cubierto **uno** | 5 |
| `P4-03-9` | **B3** | `pluginReconnectKey` (sin él no hay re-handshake de plugins tras caída) | 1 |
| `P4-03-10` | **B5** | `viewingAgentTaskId` (4 campos, no 3) | 1 |
| `P4-03-11` | **E1** | `readFileState` **clonado** como parte del aislamiento canónico — justo el hecho que motiva CtxR1 | 1 |
| `P4-03-12` | **§Evidencia** | **entera**: 11 passed/3 xfailed, los **3 nombres de `xfail(strict)`** con sus anclas, y los 5 tests objetivo | agujero de esquema |

### 10.3 Las 6 inversiones (9,4 %) — patrón 4 severo

Registradas en la nueva **`SEPARACION/03-context.md §2.6`**. Ninguna se caza comparando las dos caras (coinciden):
sólo cruzando contra los rollups. Resumen: **I1** `B9`/`OI-B` — el drenaje del `NotificationSink` **no es del
integrador**, no existe caller de `drain_notifications` ⇒ CORE-GAP `H-5`/`AC-07`, y el turn-start hook dispara
1 vez por `run()` · **I2** `A4`/CtxR5 — la firma decidida es `subagent_type: str | None` (`ID-5`) con consumidor
nombrado `MemoryStore._scope`, no `agent_type` · **I3** `B2` — es `DB-19` secuenciado tras `K1`, y el
`PlanModeProvider()` incondicional es decisión de composición (`CAT-h3`), no deuda · **I4** `A+` — el rip del
autogen va **dentro** de la remediación de `H-1` · **I5** `D2` — «cablear o borrar» ya está **decidido**:
`S31.sanitize` con estado entre chunks, y `S12` corregida a `existe-parcial` · **I6** §2.2 — IDs canónicos
B05/B15/B16/B08 (+B22) y **03 origina 0 batteries propias**.

Tasa acumulada de inversión: `05` 11 % · `02` 8,3 % · `03` 9,4 % ⇒ estimación estable ~**9-10 %**, ≈ 28-30
inversiones aún latentes en los 13 pares restantes.

### 10.4 Hallazgo nuevo — **la inversión también se propaga hacia ARRIBA** (`P4-03-P1..P3`)

Es el primer par en que el defecto se detecta **en la capa consolidadora**, no sólo en el par:

- **`P4-03-P1` — el 3er salto de destilación TAMBIÉN inventa.** `00-INTEGRADORES §1.7:181` resume los OI de 03 como
  *«presentación, estado de ficheros, attachments»*: **ninguna** de esas tres corresponde a las cinco obligaciones
  reales (render · notificaciones · prepend · identidad · attribution). Hasta ahora la invención se había medido
  sólo en el salto tracker→SEPARACION; **existe igual en SEPARACION→consolidador**, y allí nadie la está midiendo.
- **`P4-03-P2` — colisión de IDs `OI-A`/`OI-B`** entre `03` y `10` en `§1.7:181/:185`: los OI son per-categoría y
  el consolidador los mezcla sin prefijo ⇒ **prefijar `OI-03-A`…**.
- **`P4-03-P3` — el consolidador arrastra 2 estados rancios**: `§1.4` mantiene *«no se auto-drena»* con criterio de
  aceptación imposible (=I1) y `§1.6:165` sigue diciendo `B-02` por `DB-19` (=I3).

**Consecuencia operativa:** la precedencia declarada del ledger (*P4-P7 antes de consolidar `00-INTEGRADORES §1.x`*)
era una precedencia de **orden**; queda demostrado que además es una precedencia de **corrección** — el §1.x actual
contiene material que P4″ invalida, y no puede consolidarse tal cual.

### 10.5 Anti-padding en positivo (L10, doble filo)

Lo que este par hizo **bien** y no se degrada para engordar el hallazgo: **0 INVENTADAS** en las 64 fichas y **0
perdidas**; ningún ❌ disfrazado de 🔀 (FIND-CTX1 y GAP-CTX3 siguen ❌); las **15 UI-callbacks de A33 sobrevivieron
enumeradas una a una** y los ~55 campos de `B12` están correctamente excluidos de la deuda A↔B (son capa de
interfaz del canónico single-user); el detalle de `F1` (branch/main/status-short/log-5/user.name/tope 2k) llegó
intacto; y la cara integrador **`OI-A..OI-E` es producto genuino del segundo salto** — no existía en el tracker.

### 10.6 Consecuencias nuevas para el resto de P4″

14. **La invención existe en los DOS saltos.** Medir sólo tracker→SEPARACION deja fuera SEPARACION→consolidador.
    A partir de aquí, cada par cierra comprobando **la línea que `00-INTEGRADORES §1.7` le dedica** (es una sola
    línea por categoría: coste O(1), y 1/1 estaba inventada).
15. **Los IDs locales (`OI-*`, `R*`, `CG-*`) colisionan al consolidarse.** El esquema los emite per-categoría sin
    prefijo. Verificarlo por par mientras se pasa (barato ahora, ambiguo después).
16. **Q3 releída sigue cazando**: 1 de 6 costuras de 03 afirmaba consumidor inexistente. La forma del defecto se
    repite (`02·F8`, `03·B9`): **la ficha nombra el consumidor deseado y lo escribe como si estuviera cableado**.
    Regla de lectura: en la columna *consumidor*, un sustantivo sin `archivo:línea` es una **hipótesis**.
17. **Cuando el conteo Q2 se suma y cuadra, se dice.** No todo par arrastra el error de `02`; declararlo verificado
    (con la suma escrita) es lo que distingue «comprobado» de «heredado».

---

## §11. Par **04 · modes** — tracker 288 L · SEPARACION 257 L · 23 fichas (6/18)

**Ambas caras 1→EOF en esta pasada** (`EVIDENCIA.log` 167-168, escritas al TERMINAR — REGLA 2).

### 11.0 Patrón 3 primero (encabezados, O(1)) — quinta confirmación de `P4-01-1`

| capa | encabezado |
|---|---|
| tracker | `# · Feature canónica · Runtime · Estado · Diferencia / ajuste holístico` (y en D: `# · Símbolo runtime · ¿Contraparte canónica? · Estado · …`) |
| SEPARACION | `ID · resumen · núcleo\|cáscara · TIER · destino · nota-id · acción` |

`Feature canónica` **sin sucesora**. Retención de citas `.ts`: **31 → 6**. Es la retención más alta medida
(01: 1130→105 · 05: 46→1 · 02: 23→1 · 03: 30→4), y **no contradice `P4-01-1`**: las 6 supervivientes son **nombres
de archivo canónico en prosa** (`coordinatorMode.ts`, `useSessionBackgrounding.ts`) usados como *rótulo de sección*,
**no anclas `archivo:línea`**. Las anclas con línea que el tracker sí tenía —`tools.ts:69-70/92/93/95`,
`getCoordinatorSystemPrompt` 146-160, `constants/tools.ts:55-102`— **desaparecieron todas**. ⇒ el defecto de esquema
se confirma incluso donde el conteo bruto parece benigno: **contar `.ts` sobreestima la retención; hay que contar
`.ts:` con línea.** (Refinamiento de método, no excepción.)

### 11.1 Saldo — 23/23

| veredicto | n | fichas |
|---|---|---|
| CONSERVADA | 12 | A1·A5·B2·B5·B7·B8·D1·D2·D3·D5·D6·D7 |
| ENRIQUECIDA (verificada) | 3 | A4 · C3 · D4 |
| **COMPRIMIDA-CON-PÉRDIDA** | **8** | A2·A3·B1·B3·B4·B6·C1·C2 |
| **INVENTADA** | **0** | — |
| PERDIDA (sin colocar) | **0** | 23/23 colocadas |

**Q2 SUMADA y correcta** (consecuencia 17): A1-A5·5 + B1-B8·8 + C1-C3·3 + D1-D7·7 = **23**, y el destilado declara
23 en los tres sitios (§1 título, Q2, §3.1). **No hay error aritmético que propagar** — como `03`, a diferencia de `02`.

**Las 0 INVENTADAS se acreditan abriendo código, no declarándolas.** La afirmación load-bearing de 04 es **negativa**
(«`modes/` es huérfano»), y una ausencia mal probada es justo el defecto de `09·E5`. Verificado 1→EOF / por ancla
exacta: `modes/protocols.py` 1→16 (`AgentMode` es `str,Enum` con `"foreground"/"background"/"fork"`; `ModeManagerProtocol`
:11-16) · `modes/manager.py:42-44` (`on_transition`) · `agent_loop.py:91` (`mode = "background" if ctx.is_subagent
else "foreground"` — **exacta**) · `tools/registry.py` (`list_available` compara **sólo** `== "background"`) ·
`capabilities/resolver.py:39-49` (filtra por `ctx.is_subagent`) · `execution/tasks/registry.py:107-110`
(`set_backgrounded` escribe **sólo** el flag) y `:117-124` (`kill` **no** toca el flag) · `execution/local/runtime.py`
`_notify` **294-304** con guard `parent_session_id is None`:297 y gate de completado `:408` · `execution/fork/__init__.py:21`
(`ForkPolicy`). **Las 3 ENRIQUECIDAS son producto genuino del 2º salto**: A4 y C3 consolidan material que en el
tracker vivía en §Re-auditoría/§Cruces (no en la celda), y **D4 aporta el refinamiento `:408` que el tracker no
tenía** — la notificación está gateada por **KIND** (`parent_session_id`), no por `is_backgrounded`, lo que
**refuerza** FIND-MODE1 en vez de suavizarlo.

### 11.2 Las 8 pérdidas (`P4-04-1..8`) + `P4-04-9` — remediadas *in situ*

1. **`P4-04-1` · A2** — «reconcilia el modo» conservó el **disparador** y perdió los **dos efectos**: flip del env y
   emisión de `tengu_coordinator_mode_switched`. Consecuencia 9 en estado puro.
2. **`P4-04-2` · A3** — perdidas la firma `(mcpClients, scratchpadDir)` y, sobre todo, **el nexo A↔C**: el listado de
   tools que el prompt del coordinador anuncia **es `ASYNC_AGENT_ALLOWED_TOOLS`**. Sin él, A y C parecen ejes
   independientes cuando el canónico los cose.
3. **`P4-04-3` · B1** — perdido el hecho load-bearing del mini-ledger del tracker (`:235`): `is_backgrounded`
   **se escribe y NUNCA se lee en producción**. Es el dato que distingue «flag con consumidor» de «flag que sólo el
   integrador consumirá» (OI-MODE-B). Fase B lo habría implementado creyendo que el base lo consulta.
4. **`P4-04-4` · B3** — perdida la **disyunción** de `handleBackgroundSession()`: backgroundea *la query actual* **o**
   re-backgroundea *el foregrounded*, según haya vista o no. Un gesto, dos comportamientos; OI-MODE-A pedía uno.
5. **`P4-04-5` · B4** — perdido el invariante «el registry **no toca `ctx`**» (=03·B3): re-background no invalida el
   contexto del task vivo.
6. **`P4-04-6` · B6** — perdido el invariante «`is_backgrounded` **intacto** tras `kill`». Verificado en
   `registry.py:117-124`. Es **la razón** de que el canónico re-backgroundee al abortar: el flag sobrevive al kill.
7. **`P4-04-7` · C1** — **enumeración→puntero**, la de mayor coste del par: los **13 nombres** de
   `ASYNC_AGENT_ALLOWED_TOOLS` (`Read·Grep·Glob·Web*·Todo·Shell·Edit·Write·Notebook·Skill·Synthetic·ToolSearch·Worktree`)
   desaparecidos. **C2 es una reconciliación 1:1 contra una lista que el documento ya no contenía.**
8. **`P4-04-8` · C2** — perdidas **las 8 anclas** (4 canónicas `tools.ts:69-70/92/95/93` + 4 de runtime
   `worktree.py:61,129` · `agent.py:60` · `task_tools.py:178` · `task_tools.py:210`) **y los motivos canónicos**
   (*«prevent recursion»*, *«requires main-thread task state»*) — que son justo el insumo con que 10 decide 🔀 vs ❌.
9. **`P4-04-9` · §Evidencia — entera** (3 archivos de test con su reparto de intención, el `xfail(strict)`
   **`test_mode_manager_gates_notification`**, la suite 561·3·11). **4 de 4 pares con §Evidencia la han perdido.**

*(Además `P4-04-10`, higiene: el destilado reprodujo la basura `</content></invoke>` al EOF — la misma fuga de
escritura que el tracker declara haber corregido en su §Re-auditoría. **Se corrigió en el origen y reapareció en la
capa derivada.**)*

### 11.3 **Cinco veredictos invertidos (21,7 %)** — tabulados en `04-modes.md §2.6`

`I1` `D1`/`D2`/`§2.4` «borrar `modes/` entero» → **`RV-6`/`DB-01`: CONSERVAR `AgentMode`** (vocabulario T1 vivo;
sus valores *son* los strings crudos de `agent_loop.py:91`) · `I2` `B7`/`§0`/`§2.1` «notifica al terminar» →
**CORE-GAP `H-5`/`AC-07`**, 0 callers de `drain_notifications` · `I3` `C1` «mecanismo invertido = ventaja» →
**CORE-GAP-restrictividad**, `10·E3` revierte el bool a dos `frozenset` nombradas · `I4` `C2` «pendiente en 10·R10» →
**RESUELTO** (`10·E2`/`E4`) · `I5` `§0.1` GAP-02 → puntero **rancio**, el dueño es hoy el keystone **`K1`**.

**`I1` es el hallazgo de mayor coste del par**, y su forma es la peor posible: **04 es la categoría que originó la
regla `RV-6`** («BORRAR se escribe a nivel de símbolo, nunca de módulo, con lista explícita de lo que SOBREVIVE») y
es **el precedente que `A-CIERRE-LEDGER·AC-09` cita** para auditar las 37 entradas BORRAR restantes — **y su propio
documento seguía llevando la orden incorrecta**. La regla se extrajo del caso y **no se aplicó al caso**. Es la
misma especie que `CAT-h10` (*«una decisión que corrige un doc cerrado se APLICA EN ese doc»*), ahora con la vuelta
de tuerca de que el doc no corregido es **la fuente del precedente**.

**Sub-hallazgo `P4-04-N` — `RV-6` resolvió el ARCHIVO, no el MIEMBRO.** `RV-6` conserva `AgentMode` *entero*
(`FOREGROUND/BACKGROUND/FORK`) sin pronunciarse sobre `FORK`; pero el único consumidor del enum, `list_available(mode=…)`,
**compara sólo contra `"background"`** ⇒ si `AgentMode` pasa a ser el vocabulario T1 del gating, **`FORK` queda como
miembro que nadie puede pasar**, y el argumento original de `D2` (mezcla de ejes ortogonales; el fork real es
`ForkPolicy`) **sigue vivo dentro del enum conservado**. Ruteado a **`AC-09`**, que es la auditoría símbolo-a-símbolo
— **no lo cierra `RV-6`**. *Corolario de método:* una corrección de alcance a nivel de archivo puede dejar intacta
la pregunta a nivel de símbolo que la motivó; `AC-09` debe verificar **miembro a miembro**, no archivo a archivo.

### 11.4 Consecuencia 14 — la línea de `00-INTEGRADORES §1.7` (2º par medido)

`§1.7:182` dedica a 04: *«política de modo/backgrounding **encima** de la primitiva del base (04 no aporta battery).
Swarm = ⛔ fuera de alcance»*. Contrastada contra las 2 OI reales: **cubre `OI-MODE-A`** (disparo del backgrounding)
y **rotula mal `OI-MODE-B`**, que no es «política de modo» sino **multiplexado/proyección de la vista**
(`foregroundedTaskId`) — la obligación *must-be universal de todo integrador con vista*. Y *«Swarm = fuera de
alcance»* omite que §2.5 lo rutea deliberadamente a `00-INTEGRADORES` como **blueprint de arranque**. ⇒ **1 de 2 OI
bien representada.** Marcador acumulado: **2 de 2 pares con la línea del consolidador defectuosa** (03: 0/5
inventada · 04: 1/2 parcial). La precedencia «P4-P7 antes de consolidar §1.x» **se confirma como de corrección**.

**Consecuencia 15 (colisión de IDs): NEGATIVA aquí, y eso es información.** 04 emite `OI-MODE-A`/`OI-MODE-B`
—**ya prefijados por categoría**— frente a los `OI-A`/`OI-B` de 03 y 10 que colisionan. El esquema no es
uniformemente defectuoso: **04 demuestra que la convención correcta ya existe en el corpus**, luego `P4-03-P2` no
pide inventar un prefijo sino **generalizar el que 04 ya usa**.

**Consecuencia 16 (Q3 relectura): 3 de 3.** La costura de §2.1 nombraba `notification.py put/drain/process` — un
**sustantivo sin `archivo:línea` de caller** ⇒ hipótesis ⇒ falsa. La forma se repite exacta en `02·F8`, `03·B9` y
`04·§2.1`. Agravante nuevo: aquí la hipótesis estaba **respaldada por un re-export** (`__init__.py:12,37-38`), que
es lo que la hizo creíble. **Un símbolo exportado no es un símbolo invocado** — variante de `RV-5` (*un docstring no
es evidencia de cableado*) aplicada al `__init__.py`.

### 11.5 Lo que **NO** se perdió ni se degradó (anti-padding, L10, doble filo)

Las 23 fichas tienen TIER **y** destino (0 perdidas) · **0 INVENTADAS** pese a que la tesis central es una
**ausencia** · la disección de los 3 ejes ortogonales (sesión/backgrounding/fork) llegó **íntegra y es el aporte real
del par** · `§0.1` (la desambiguación load-bearing «permission modes ≠ AgentMode») es **producto genuino del 2º
salto**: no existe en el tracker y **evita** que 04 se infle con un finding ajeno · las 4 `INTERNAL_WORKER_TOOLS` de
A5 sobrevivieron **enteras** (frente a `02·E3`, que perdió 2 de 4 — `P4-02-9`) · `TaskType(×7)` sobrevivió en §2.3 ·
las 5 fichas ⛔ del swarm **no se contaron como ❌×5** · **`FIND-MODE1` se sostiene**: `ModeManager` sigue huérfano y
su borrado sigue decidido — `RV-6` corrigió el **alcance**, no el veredicto. Declarar «04 está corrompido» por I1
sería padding alarmista: **12 de 23 fichas intactas y 3 mejoradas**.

### 11.6 Consecuencias nuevas para el resto de P4″

18. **La tasa de inversión de un par es proporcional a cuánto delega.** 04 invierte al **21,7 %**, el doble de la
    tasa acumulada, y el mecanismo es legible: **17 de sus 23 fichas apuntan a un dueño ajeno**; no posee battery ni
    CORE-GAP propio. *Una ficha que delega no controla su veredicto: se invierte cuando su dueño decide, y nadie
    avisa al remitente.* ⇒ **sonda O(1) para los 12 pares restantes: contar las fichas cuyo `destino` es otra
    categoría.** Alta proporción ⇒ priorizar el cruce con rollups sobre la lectura de prosa. Revisión al alza de la
    estimación: los pares delegadores rondarán el 20 %, no el 10 %.
19. **Contar `.ts` sobreestima la retención canónica; hay que contar `.ts:` con número de línea.** 04 retiene 31→6,
    la cifra más benigna del corpus, y aun así **perdió el 100 % de sus anclas con línea**: las 6 supervivientes son
    rótulos de sección en prosa. La sonda del patrón 3 se corrige — sigue siendo O(1).
20. **Una regla extraída de un caso no se aplica sola a ese caso.** `RV-6` nació de 04 y 04 seguía sin corregir.
    ⇒ al cerrar cada par, comprobar si **originó** alguna regla/precedente citado en los rollups y si **se le
    aplicó**. Ampliación de `CAT-h10`.
21. **Una corrección de alcance a nivel de ARCHIVO puede dejar viva la pregunta a nivel de SÍMBOLO** (`P4-04-N`:
    `RV-6` salvó `AgentMode` sin decidir sobre `FORK`). `AC-09` debe auditar **miembro a miembro**.
22. **Un símbolo re-exportado en `__init__.py` no es un símbolo invocado.** Es lo que dio verosimilitud a la costura
    falsa de `§2.1`. Al probar ausencia de cableado, **descartar los re-exports antes de contar callers**.

---

## §12. Par **06 · hooks** — tracker 464 L · SEPARACION 440 L · 74 fichas (**`AC-12`** · 7/18)

**Ambas caras 1→EOF en esta pasada**, y **re-abiertas** tras la compactación de contexto (`EVIDENCIA.log` 193-194
y la re-apertura de esta sección). La columna de **CRUCE** se leyó 1→EOF completa por primera vez bajo `D-05·1`:
`00-INTEGRADORES` 242 · `DEUDA-A` 699 · `BATTERIES` 546 · `SEAMS` 539 · `DEUDA-B` 1129 = **3.155 L**. `DEUDA-B` se
re-abrió aquí porque su 1→EOF anterior era **pre-`/clear`** ⇒ heredada por el precedente `A3.DB·RV`, no propia.

### 12.0 Patrón 3 primero (encabezados, O(1)) — sexta confirmación de `P4-01-1`

| capa | encabezado |
|---|---|
| tracker | `Feature · Canónico · Runtime · Estado` (y en E: `Punto · Canónico · Runtime · Estado`) |
| SEPARACION | `ID · resumen · núcleo\|cáscara · TIER · destino · est. · id` |

`Canónico` **sin sucesora**, séptima vez. Retención de anclas `.ts:` **con línea**: **7 → 0 = 100 % de pérdida**
(consecuencia 19 aplicada: se cuentan `.ts:NNN`, no `.ts`). Las 7 del tracker: `coreTypes.ts:25/26-52`,
`utils/hooks.ts:3932`, `runAgent.ts:532`, `toolHooks.ts:332/372/510-561`, `utils/hooks.ts:434/622-641`. **Mismo
perfil severo que el par 04.** Y desaparece además el **inventario de contrapartes con LOC** de la cabecera
(`schemas/hooks.ts` 222 · `types/hooks.ts` 290 · `hookEvents.ts` 192 · `hookHelpers.ts` 83 · `utils/hooks.ts` 5022 ·
`stopHooks.ts` 473 · `toolHooks.ts` 650 · `PermissionContext.ts` 388 · `registerFrontmatterHooks.ts` 67 ·
`registerSkillHooks.ts` 64), que es lo único que acreditaba la escala de lo leído.

### 12.1 Saldo — 74/74 unidades nombradas

| veredicto | n | fichas |
|---|---|---|
| CONSERVADA | 54 | 50 del grid + `KH1`·`KH4`·`KH5`·`KH6` |
| ENRIQUECIDA (verificada) | 10 | D11·E2·E3·E6·E8·E9·F2·G4·I4 + `KH3` |
| **COMPRIMIDA-CON-PÉRDIDA** | **10** | A6·B1·B4·C2·C4·D1·D2·D10·E1 + `KH2` |
| **INVENTADA** | **0** | — |
| PERDIDA (sin colocar) | **1** | **el párrafo de kill-switches** (tracker :264-266) |

**Q2 NO reconcilia, y falla en tres sitios a la vez.** El ledger `§3.1` tiene **72 filas** contadas una a una
(68 grid + `K3`/`K4`/`K5`/`K6`); su propio título dice *«74 = grid 68 + K6»* (= **69**); y `§3.2·2` declara
**«74 filas de ledger; colocados = 74; sin colocar = 0»** sumando `K1-K6` como 6 y excluyendo acto seguido `K1`/`K2`
en `:383` (*«no cuentan como los 74»*). Las tres cifras son mutuamente incompatibles. Es exactamente la regla que
`BATTERIES·CAT-h8` escribió —*contar sobre la unidad distribuida, no sobre el contenedor*— incumplida en el
documento que la cita.

**Las 0 INVENTADAS se acreditan por lectura, no por declaración.** Las 9 ENRIQUECIDAS son producto genuino del 2º
salto y todas del mismo tipo: **ausencia leída en fuente**, que el tracker afirmaba sin ancla — E2 `agent_loop.py:314-323` ·
E3 `:324-328` · E6 `:346-352` · E8 `runtime.py:294-304` · E9 `runtime.py:306-366` · F2 `permissions.py:6-33` ·
G4 `runtime.py:285-292` · I4 `runner.py:20-31` · D11 `runner.py:33-60`. Es el aporte real del par y hay que decirlo:
06 es el único par medido cuyo destilado **mejora la prueba de las ausencias**.

### 12.2 Las 11 pérdidas (`P4-06-1..11`) — remediadas *in situ* en `SEPARACION/06-hooks.md`

1. **`P4-06-1` · `KH2` — la más cara del par, y es una pérdida de `D-02`.** La cabecera del tracker (:29-42) enumera
   los **26 ejecutores canónicos por evento con su línea** (`executePreToolHooks` 3394 … `executeWorktreeRemoveHook` 4967).
   Es **la única tabla de comportamientos canónicos de la categoría 06**, y nació precisamente como
   auto-corrección de superficialidad (`RE-AUDIT-HOOK-COMPLETO`, *«la lista previa omitía ~15»*). El destilado la
   reduce a una línea —*«~15 ejecutores canónicos omitidos en 1ª lista»*— con TIER `meta` y `det. N/A` ⇒ **queda
   fuera de la capa que Fase B lee**. Bajo `D-02` una ficha sin tabla de comportamientos no entra en Fase B: aquí la
   tabla existía y se descartó por clasificarla como higiene documental.
2. **`P4-06-2` · kill-switches — la única unidad SIN COLOCAR del par.** El tracker (:264-266) registra
   `shouldDisableAllHooksIncludingManaged` (managed `disableAllHooks`) y `CLAUDE_CODE_SIMPLE`, presentes **en ambos
   motores**. No tienen fila, ni celda, ni mención en las 440 líneas del destilado. Es un **must-have de
   `battery_hooks_config`**: un motor de hooks configurable que no honre el apagado gestionado no es sustituible por
   el motor multi-tenant de `agentic_assistant`. Su ausencia es la que rompe el «sin colocar = 0». *(Causa
   estructural: el párrafo **no tiene ID en el tracker** — todo lo demás de la RE-AUDITORÍA sí. Lo que no se nombra
   no se reparte.)*
3. **`P4-06-3` · `E1` — estado compuesto colapsado.** El tracker declara `✅ (payload) / 🟡 (consumo, ver F)`; el
   destilado escribe `✅` a secas. La mitad perdida **es el gate lossy**, o sea el corazón de `CG-HOOK-5`. Un ✅ limpio
   en el punto de disparo más importante invita a Fase B a no tocarlo.
4. **`P4-06-4` · `A6`** — perdidas las dos anclas que el tracker había ganado en la re-auditoría:
   `executeSubagentStartHooks` (**`utils/hooks.ts:3932`**) y su disparo (**`runAgent.ts:532`**). Eran la prueba de que
   SubagentStart existe como ejecutor dedicado y no sólo dentro de `runAgent.ts` — el hallazgo mismo de
   `RE-AUDIT-HOOK-COMPLETO`, borrado en la fila que lo motivó.
5. **`P4-06-5` · `C4`** — de las **6** fuentes de `getHooksConfig` (`settings snapshot · registered · session ·
   frontmatter · skill · plugin`) sobreviven 4, y se pierden justo **`registered` y `session`** — las dos en-proceso,
   que son las que el `HookRunner` **ya implementa**. Sin ellas, la battery parece tener que aportar 100 % de la
   resolución cuando el base ya cubre dos fuentes.
6. **`P4-06-6` · `C2`** — enumeración→puntero: las claves de `matchQuery` (`tool_name/source/trigger/reason/…`)
   desaparecen; queda «`matchQuery` por evento».
7. **`P4-06-7` · `D1`/`D2`** — perdidos **los porqués de los dos 🟡**: `stopReason` y *«no re-inyecta al loop»* (D1);
   *«solo deny, no allow explícito»* (D2). Un 🟡 sin su porqué es indistinguible de un ✅ degradado.
8. **`P4-06-8` · `B1`/`B4`/`D10`** — tres detalles de config que la battery debe implementar y ya no constan:
   `shell:bash/powershell` (B1), `headers env` (B4), `event-name check` (D10).
9. **`P4-06-9` · §Recuento entero** (:280-283). No se reproduce. Ver 12.3·`T2`: era un dato **defectuoso**, y perderlo
   impidió detectarlo.
10. **`P4-06-10` · §Evidencia entera** (:285-288): `test_hooks_homologation.py` **3 passed + 8 xfailed(strict)**, los
    19 tests previos que cubren 06 (`test_hooks.py` 8 · `test_pre_tool_use_hook.py` 7 · `test_root_turn_start_hooks.py` 4),
    suite global **571 · 3 · 26**, lint verde. **5 de 5 pares con §Evidencia la han perdido** — el patrón es total.
11. **`P4-06-11` · la cabecera de contrapartes canónicas con LOC** (:7-49) y las **7 anclas `.ts:línea`** → 0 (ver 12.0).

### 12.3 Dos defectos en la **capa tracker** (no son DR-1: la pérdida no empieza en el destilado)

- **`T1` · `FIND-HOOK4` no existe y `FIND-HOOK8` tampoco.** §Hallazgos salta de `FIND-HOOK3` a `FIND-HOOK5`; y el
  §Plan `HR7` (:456) cita **«FIND-HOOK8»**, que en §Hallazgos no está — su contenido vive como `RE-AUDIT-HOOK8`.
  ⇒ **el destilado no inventó nada**: `KH4 · "FIND-HOOK8/RE-AUDIT-HOOK8"` reproduce fielmente el alias del tracker.
  *(Corrijo aquí una anotación mía previa de `EVIDENCIA.log`:194 que lo atribuía al destilado.)* Lo que sí es del
  destilado es `§3.2·1`, que declara haber leído *«Hallazgos FIND-HOOK1-8»* — un rango del que faltan dos.
- **`T2` · el §Recuento del tracker está mal en las CINCO cifras, y por eso 06 declara 58 findings sobre un grid de 68.**
  Contado fila a fila en esta pasada: ✅ **4** · 🟡 **9** · 🔀 **17** · ❌ **32** · ⛔ **5** = **67**, más `E1`, cuyo
  estado es compuesto (`✅/🟡`) = **68**. Declarado: `✅ 6 · 🟡 12 · 🔀 14 · ❌ 20 · ⛔ 6` = **58**. La desviación
  grave es **❌ 32 vs 20**: el tracker sub-declaró en 12 el número de gaps de su propia tabla. Ninguna interpretación
  de `E1` reconcilia esa diferencia. **Y el destilado, al no reproducir el Recuento (`P4-06-9`), no lo detectó** —
  ilustración exacta de por qué un dato heredado sin re-contar es peor que un dato ausente.

### 12.4 **Cinco inversiones aguas arriba** — patrón 4 en su forma severa, y aquí no es aguas abajo

Las de 03/04 eran fichas cuyo *dueño* las revirtió. Las de 06 son distintas y peores: **los rollups de destino no
recogen lo que 06 les manda**.

- **`I1` · `DEUDA-A §1.2` no reparte 06.** `§0.2` acredita a 06 con **8 CORE-GAPs** (`CG-HOOK-1..8`), pero `§1.2`
  —la sección que distribuye *todo lo no-keystone*— lista **(a) BASE**: 08/07/02/03/05/09/16/15/17 y **(b) BATTERY**:
  mcp/skills/memory/plan/voice/compaction/resilience/10. **06 no aparece en ninguna de las dos.** ⇒ `CG-HOOK-1..7`
  **no tienen destino en el rollup**; sólo `CG-HOOK-8` sobrevive, y por ser `K1`.
- **`I2` · `BATTERIES` B17 lo confirma por el otro lado.** La columna *«CORE-GAPs que la completan»* de
  `battery_hooks_config` dice **«—»**, cuando `B16·plan` sí lista `CG-PLAN-1..11`. Y sin embargo `CG-HOOK-1`
  (taxonomía) y `CG-HOOK-2` (disparos) son la **condición de posibilidad** de la battery: sin eventos declarados y
  disparados no hay nada que configurar. Dos rollups independientes, el mismo agujero ⇒ no es un descuido de
  redacción.
- **`I3` · dos de las cuatro costuras de `§2.1` no existen en `SEAMS`.** `HookSinkProtocol`/`HookRunner` y
  `HookDecision` rico caen dentro de **S8**; pero el **seam de reawake** (`KH3`) y la **costura fs-watch** (`D9`)
  **no están en el índice de 29**. La causa es estructural y está escrita en `SEAMS:4`: A1.7 se destiló de
  `{01,16,07,02,05,09}` — **06 nunca fue fuente de SEAMS**. `A3.CAT` hizo exactamente este trabajo para la voz
  (numeró `S30`/`S31`, cerrando el cabo 5 de `BATTERIES §4.5`) y **nadie lo hizo para 06**.
- **`I4` · remisión circular.** `SEAMS·S8` enumera **5** fire points y cierra: *«el detalle de fire points + shape
  `Hook*Event` se desarrolla en **06·hooks** (A3); aquí se fija el punto y la firma»*. En 06 ese detalle es
  precisamente `KH2`, degradado a `meta`/`det. N/A` (`P4-06-1`). **A remite a B y B lo tiene fuera de alcance.**
  Es `L09` (*cablear ≠ existir*) aplicado a la documentación: una remisión no es una entrega.
- **`I5` · colisión de espacio de nombres `K*` — la más peligrosa por silenciosa.** 06 numera sus extras
  `K1..K6`, y `K1..K8` son **los keystones globales** de `DEUDA-A`. Colisiones reales: `06·K4` = dos motores
  vs **`K4` = identidad en el `Event` base**; `06·K5` = `LAT-HOOK1` vs **`K5` = `ToolResult.new_messages`**; y
  `06·K1` = corrección de dato vs **`K1` = `PermissionContext.mode`**, que es *el keystone cuyo hogar es 06*.
  El destilado ya tropieza con ello en `§2.4`, que titula *«DEUDA-B `K5·LAT-HOOK1`»*: leído desde `DEUDA-B` —donde
  `K5` es el keystone CORE-GAP y la fila 4 del ledger lo remite a `DEUDA-A`— la línea afirma que un CORE-GAP es
  DEUDA-B. **Remediado renumerando los extras de 06 a `KH1..KH6`** (misma medicina que consecuencia 15).

### 12.5 Consecuencia 14 — la línea de `00-INTEGRADORES §1.7` (3er par medido) + un ENDURECIMIENTO nuevo en `§1.6`

`§1.7:183` dedica a 06 una línea: *«`OI-HOOK-A … OI-HOOK-E` | 06·hooks | proveer el `HookRunner` —
`RuntimeConfig.hook_runner=None` por defecto (`factory.py:86`) ⇒ sin él, ninguna battery puede registrar hooks
(18·C2)»*. Enumera las 5 OI en la celda de ID y luego **desarrolla una sola**: cubre `OI-HOOK-A` (proveer el sink) y
**omite B (HITL `ask`), C (persistir grants), D (componer o sustituir la battery), E (reawake async)**. ⇒ **1 de 5.**
Marcador acumulado: **3 de 3 pares con la línea del consolidador defectuosa** (03: 0/5 inventada · 04: 1/2 parcial ·
06: 1/5 parcial). La precedencia *«P4-P7 antes de consolidar §1.x»* deja de ser cautela y pasa a ser **dato**.

**Y un ENDURECIMIENTO en `§1.6`, que es peor que la omisión.** «Política / hooks / gates» fija como *contrato que el
integrador consume*: `hook PRE_TOOL_USE(tool_name, tool_input, call_id, ctx) -> block|modified_input`. Esa firma es,
literalmente, **el gate lossy que `CG-HOOK-5` declara insuficiente** (ignora `stop`, `additional_context`, sin
`behavior` allow/ask/deny, sin merge con reglas). El consolidador la marca como CORE-GAP **sólo** en `PermissionMode`.
⇒ prosa aproximada de nivel N (el estado *de hoy*) citada como hecho estructural en N+1 (el *contrato*): si Fase B lee
`§1.6`, implementa el gate pobre y lo da por bueno. Es el vector `ENDURECIMIENTO` en su forma canónica, y el primero
detectado **en el consolidador** y no en el destilado.

**Un segundo ENDURECIMIENTO, éste del destilado:** `CG-HOOK-1` titula *«taxonomía 11→**~20 core-portables**»*. El
tracker dice **11 → 27** en los tres sitios donde habla de taxonomía (`FIND-HOOK1`, `RE-AUDIT-HOOK-COUNT`, `HR1`) y
**nunca fija un subconjunto numerado** — `HR1` sólo dice *«cuenta ≥ los core-portables»*. El «~20» no existe en la
capa de origen: es una cifra nacida en el 2º salto que Fase B leería como objetivo de implementación.

### 12.6 Lo que **NO** se perdió ni se degradó (anti-padding, L10, doble filo)

Las 74 unidades tienen TIER **y** destino · **0 INVENTADAS** · la **tesis arquitectural** (el sistema configurable es
🔀 delegado ⇒ battery, no CORE-GAP) llegó **íntegra y correctamente reificada** como `battery_hooks_config`, y es un
salto real: el tracker la argumenta en prosa, el destilado la convierte en una battery con alcance enumerado,
`OPCIONAL`, con los dos perfiles de composición nombrados (`agentic_code` compone / `agentic_assistant` sustituye) —
y **`BATTERIES §1` y `§2.3·B17` lo confirman verbatim**, incluido el seam `S8` y la traza `06·hooks | B17` de `§3` ·
los **8 CORE-GAP** llevan los 6 campos `L05` completos · las **5 OI** llevan los 6 campos y el eje primario explícito
(*contrato base común*), que es justo donde 03 falló · **9 ausencias pasaron de afirmadas a probadas en fuente**
(12.1) · `DEUDA-A §0.2` acredita *«06 | 8 | CG-HOOK-1..8»* **exacto**, y `K1` está bien hogareado en `CG-HOOK-8`,
**enriquecido** de 3 a 8 equivalencias · `DEUDA-B` recoge la única deuda propia de 06 (`DB-07`/`LAT-HOOK1`) con sus 6
campos, su orden (`HR5`) y su prueba (`test_hooks_homologation.py:212-215`, `xfail(strict)`→verde), y el barrido
`§2.4` sobre `06:248-255` **no** infló ninguna entrada más. Decir «06 está corrompido» por `I1-I5` sería padding:
**54 de 74 fichas intactas, 10 mejoradas, y la tesis —que es el producto— llegó entera.** Lo que falló no es el
destilado de 06: son **los rollups que debían recogerlo**.

### 12.7 Consecuencias nuevas para el resto de P4″

23. **La inversión también va AGUAS ARRIBA: un par puede estar bien destilado y aun así no llegar a Fase B.** 06
    entrega 8 CORE-GAPs con `L05` completo y `DEUDA-A §1.2` no reparte ninguno; entrega una battery y `BATTERIES·B17`
    no le acredita CORE-GAPs; entrega 4 costuras y `SEAMS` sólo numera 2. ⇒ **sonda O(1) obligatoria para los 11
    pares restantes: buscar el nombre de la categoría en las secciones de REPARTO de los 5 rollups** (no en sus
    índices ni en sus tablas de trazabilidad, que sí la citan). Un par citado en el índice y ausente del reparto es
    el modo de fallo nuevo.
24. **Una categoría que no fue fuente de un rollup no tiene costuras en él, y nadie lo detecta.** `SEAMS` se destiló
    de 6 categorías; `A3.CAT` reparó el caso de 17 (S30/S31) **sin generalizar la reparación**. ⇒ **las 12
    categorías que no fueron fuente de A1.7 deben cotejar su `§2.1` contra el índice de 29**, una por una. `06`
    aporta ya dos candidatas (reawake, fs-watch).
25. **Prohibido reusar el espacio de nombres `K*` para extras locales.** Colisiona con los keystones `K1..K8`, y la
    colisión no da error: produce frases verdaderas en un doc y falsas en otro (`§2.4` de 06). ⇒ **auditar `K\d` en
    los 11 destilados restantes** y renumerar a `<CAT>H\d` donde sea local. Generalización de la consecuencia 15.
26. **Un §Recuento no reproducido es un §Recuento no verificado — y los trackers los tienen mal.** 06 declara 58
    sobre 68 (❌ 20 vs 32 reales). El destilado no lo copió y por eso no lo cazó. ⇒ **en cada par restante, contar el
    grid fila a fila y contrastarlo con el §Recuento del tracker antes de emitir el saldo**, aunque el destilado no
    lo mencione. Coste O(n) sobre una tabla ya abierta; es la sonda más barata que queda.


### 12.8 · REMEDIACIÓN APLICADA — `SEPARACION/06-hooks.md` 440 → 710 L (2026-07-28)

**Estado del par: 06 pasa de *diagnosticado* a *remediado*.** Las **11 pérdidas `P4-06-1..11`** y la inversión
`I5` están **aplicadas in situ**; ya no son un pendiente de este documento.

| pérdida | dónde quedó | comprobación |
|---|---|---|
| `P4-06-1` **KH2** | **§1.0 nueva** — los **26 ejecutores con línea**, tabla de comportamientos `D-02`; promovido de `meta`/`det. N/A` a `T1-CONTRATO` **colocable** y con fila propia en el ledger | 26 filas contadas contra tracker `:29-42`; ⛔ UI (`4584`/`4675`) nombrados y excluidos |
| `P4-06-2` **KH7** | fila `KH7` + **§2.2** (must-have de battery **y** guarda en `HookRunner`) | era la **única unidad sin colocar** del saldo 74/74 |
| `P4-06-3` **E1** | grid + ledger + `§3.2·3` | estado compuesto `✅ payload / 🟡 consumo` |
| `P4-06-4` **A6/E9** | grid, ambas filas | anclas `utils/hooks.ts:3932` + `runAgent.ts:532` |
| `P4-06-5` **C4** | grid | 6 fuentes; `registered` y `session` recuperadas |
| `P4-06-6` **C2** | grid | claves `tool_name/source/trigger/reason/…` |
| `P4-06-7` **D1/D2** | grid | los dos *porqués* del 🟡 |
| `P4-06-8` **B1/B4/D10** | grid | `shell:bash\|powershell` · `headers` env · event-name check |
| `P4-06-9` **§Recuento** | **§3.2·2**, restituido **con tabla de deltas** | 58 declarado vs **68** real; ❌ 20 vs **32** |
| `P4-06-10` **§Evidencia** | **§1.1 nueva** | íntegra, con los 8 `xfail(strict)` como criterio de aceptación |
| `P4-06-11` **cabecera+anclas** | **§0.1 nueva** | 10 contrapartes con LOC + las **7 anclas** (retención 7→0 revertida) |
| `I5` **namespace** | todo el documento | `K1..K6` → `KH1..KH6`; verificado que no queda ningún `K\d` local (los `K1..K8` residuales son citas explícitas a los keystones de `DEUDA-A`) |
| `I4` **circularidad** | §2.1 | roto por el lado de 06: `executeInBackground` `:184`, exit-2 → `enqueuePendingNotification` |

**Además:** `CG-HOOK-1` corregido de *«11→~20»* a **11 → 27** (endurecimiento propio); ledger `§3.1`
**re-contado fila a fila = 74** con composición nueva y **aviso explícito de que el 74 anterior era falso en
tres sitios**; `VEREDICTO §3.4` reescrito de `✅ NADA PENDIENTE` a **`⛔ PENDIENTE(S)`**.

**Lo que NO cierra esta remediación, y por eso el par no está cerrado:** `I1` · `I2` · `I3` y el
**ENDURECIMIENTO de `00-INTEGRADORES §1.6`** viven en los rollups y en el consolidador. Quedan abiertos como
**`AC-19` · `AC-20` · `AC-21`** y las dos correcciones de la capa tracker como **`AC-22`**
(`A-CIERRE-LEDGER §2.2`). **La tasa `DR-2` de la categoría sigue sin medir** (`O-11`/`P6″`).

---

## §13. Par **07 · events** — tracker 445 L · SEPARACION 216 L · 44 fichas (**`AC-12`** · 8/18)

**Ambas caras 1→EOF en esta pasada** (`HOMOLOGATION/07-events.md` 445 en 1-200 + 200-445 · `SEPARACION/07-events.md`
216), **re-abiertas tras la compactación** de contexto. La columna de **CRUCE** se leyó 1→EOF **entera y propia**
bajo `D-05·1`: `BATTERIES` 546 · `DEUDA-B` 1129 · **y re-abiertos en este mismo tramo** `SEAMS` 539 ·
`DEUDA-A` 699 · `00-INTEGRADORES` 242 = **3.155 L**. Los tres últimos se re-abrieron porque su 1→EOF era
**pre-compactación**: invocarlos desde el resumen habría sido exactamente la omisión que `DEUDA-A §0.1` documenta
contra sí misma. **No fue ceremonia: la re-lectura refutó una de mis propias anotaciones** (ver `13.4·I5`).

### 13.0 Patrón 3 primero (encabezados, O(1)) — séptima confirmación de `P4-01-1`

| capa | encabezado |
|---|---|
| tracker | `Feature · Canónico · Runtime · Estado` |
| SEPARACION | `ID · resumen · núcleo\|cáscara-CLI · TIER · destino · nota-identidad · acción` |

`Canónico` **sin sucesora**, octava vez. Retención de anclas canónicas: el tracker cita **5 archivos `.ts` con LOC**
(`coreSchemas.ts` 1854 · `remote/sdkMessageAdapter.ts` 303 · `utils/hooks/hookEvents.ts` 192 · `query.ts` 1729 ·
`QueryEngine.ts` 1295) y **≥9 anclas `.ts:línea`** ganadas en la RE-AUDITORÍA 2026-07-12 (unión de 24 variantes
`1854-1881` · init `1457-1494` · enum de error `1256-1266`/`1352` · `SDKSessionInfoSchema` `1812-1852` ·
`SDKRateLimitInfo` `1305-1345` · `SDKResultError` `1428-1451` · `priority` `1280` · `ModelUsageSchema` `17-28`).
El destilado retiene **0**. **7 → 0 = 100 % de pérdida.**

**Y el reverso, que es lo que hace este par diagnóstico:** el destilado carga **23 anclas `.py:línea`** distintas
del lado B. No es un documento pobre en evidencia — es un documento **con una sola columna de evidencia**. Confirma
la medición de `§7.2·P4-01-1`: `01·05·07` son los tres pares **en cero canónico**, y la causa no es descuido sino
que el encabezado del destilado **no tiene dónde ponerlo**.

### 13.1 Saldo — 44/44 fichas (A1-K5)

| veredicto | n | fichas |
|---|---|---|
| CONSERVADA | **35** | A1·A3·A4 · B2·B3 · C1·C2·C4·C5 · D3·D4 · E1·E2·E3·E4·E5 · F1·F2·F3·F4 · G1·G2·G4 · H1·I1 · J2·J3·J4·J5·J6 · K1·K2·K3·K4·K5 |
| ENRIQUECIDA (verificada) | **0** | — |
| **COMPRIMIDA-CON-PÉRDIDA** | **9** | A2 · B1 · C3 · D1 · D2 · D5 · F0 · G3 · J1 |
| **INVENTADA** | **0** | — |
| PERDIDA (fila sin colocar) | **0** de 44 | — |
| **PERDIDA (unidad del tracker fuera del grid)** | **2** | **§Plan de remediación `EvR1-EvR7`** · **§0 cabecera de contrapartes** |

**`ENRIQUECIDA = 0` es un dato, no una ausencia de mérito.** 06 fue el par que *mejoró la prueba* (9 ausencias
pasaron de afirmadas a probadas en fuente). 07 no añade **ni una** ancla ni una verificación que el tracker no
tuviera ya: lo que añade —TIER, destino, nota-identidad— es el trabajo propio de la capa, no producto nuevo. El
destilado de 07 es **fiel y plano**.

**`INVENTADA = 0` se acredita por lectura**, ficha a ficha: no hay una sola afirmación del destilado sin origen en
el tracker. Los cuatro `OI-EVT-*` de `§2.5` **derivan**, no inventan.

**c26 · Recuento re-contado fila a fila en esta pasada (sobre la tabla del tracker, no sobre el destilado):**
`✅ 4` (A3·A4·C2·D4) · `🟡 6` (B1·D2·D5·E1·G2·G3) · `🔀 16` · `❌ 14` · `⛔ 4` (F4·J6·K3·K4) = **44**.
Coincide **exactamente** con el re-recuento del destilado (`§3.2·2`). Ver `13.3·T1`.

### 13.2 Las 12 pérdidas (`P4-07-1..12`)

1. **`P4-07-1` · el §Plan de remediación `EvR1-EvR7` ENTERO — la pérdida cara del par, y es de `L05`.**
   El tracker desarrolla **siete** remediaciones con **firma + cableado + orden + test nombrado**:
   `InitEvent(tools, model, mcp_servers, permission_mode, skills, slash_commands, agents)` (EvR2) ·
   `ToolProgressEvent(call_id, partial_output, elapsed_ms)` (EvR5) · `SessionStateEvent(state: Literal[…])` ·
   `ResultEvent(subtype, usage, result_text)` · `ErrorEvent` gana `code` · `to_sdk_message(event)->dict` · más los
   **siete tests** (`test_stream_starts_with_init`, `test_wire_serializes_all_core_events`,
   `test_bash_emits_progress`, `test_session_state_emitted_on_ends_turn`,
   `test_result_event_carries_subtype_and_usage`, `test_error_event_has_code`, `test_event_taxonomy_covers_core`).
   El destilado conserva **punteros** —«(EvR5)», «(EvR2)»— y **una** firma (`to_sdk_message`, y sólo porque
   `OI-EVT-2` la necesita). **Cero tests, cero órdenes, cero campos de firma.**
   **La asimetría es la que hay que nombrar:** `§2.5` sí despliega los 6 campos `L05` **para los cuatro `OI-EVT`**
   (cara integrador) mientras la cara BASE —los 19 CORE-GAPs— se queda sin ninguno. Es el **inverso** del reparto
   habitual, y deja a Fase B con el *qué* de 19 gaps y el *cómo* de ninguno.
2. **`P4-07-2` · §0 cabecera de contrapartes canónicas + mapa de emisión/consumo** (tracker :3-28). Desaparecen los
   5 archivos con LOC (13.0) **y** el mapa del lado B con líneas (`events/{protocol.py 23, bus.py 46,
   event_types.py 44, __init__.py 15}` ≈128 LOC · `models/caller.py:207-245` · `agent_loop.py` `_emit` 152 /
   247-258 / 312 / 324 · `runtime.py:234-304` · `registry.py:112` · `session.py:16,42`). Era lo único que acreditaba
   la escala de lo leído. **8º par con esta misma pérdida.**
3. **`P4-07-3` · `F0` · 5 campos del frame `init` + un shape.** El tracker enumera **14**; el destilado retiene 9 y
   pierde `apiKeySource` · `betas` · `claude_code_version` · `cwd` · `fast_mode_state`, más la forma
   `mcp_servers[]{name, status}` (queda «mcp» a secas). `init` es el frame del que **el front del integrador
   bootstrapea la vista** (`00-INTEGRADORES §1.4`): cinco campos menos es una vista que arranca ciega. Pérdida
   `D-02` pura.
4. **`P4-07-4` · `J1` · 7 de 11 campos de `SDKRateLimitInfo`, y uno rompe el propio documento.** Sobreviven
   `five_hour/seven_day/overage ×12 reasons/isUsingOverage`; se pierden **`status` (`allowed`/`warning`/
   `rejected`)** · `resetsAt` · `utilization` · `overageStatus` · `overageResetsAt` · `surpassedThreshold` ·
   `seven_day_opus`/`seven_day_sonnet`. **Consecuencia interna verificable:** el criterio de aceptación de
   `§2.5·OI-EVT-4` dice *«un `rejected` de rate-limit corta el turno con mensaje de cuota»* — cita un valor del
   enum `status` **que el destilado ya no define en ninguna parte**. Un criterio de aceptación que se apoya en un
   campo borrado del mismo documento.
5. **`P4-07-5` · `D5` · la taxonomía de error vive en DOS niveles, y el destilado la aplana a uno.** El tracker:
   *(a)* enum inline por-mensaje-assistant, *(b)* `subtype` terminal del result (D2) — **taxonomías distintas**. El
   destilado conserva los 7 valores y el par `rate_limit`(reintentable)/`billing_error`(fatal), pero pierde la
   distinción de niveles y el valor `max_output_tokens` (truncado). Riesgo directo: Fase B fusiona
   `ErrorEvent.code` con `ResultEvent.subtype` en un solo enum.
6. **`P4-07-6` · `D1` · `duration_ms`/`api_ms`** del `SDKResultMessage`. Los dos únicos campos de *tiempo* del
   mensaje terminal; sin ellos `OI-EVT-2` serializa un result sin latencia.
7. **`P4-07-7` · `D2` · el ancla `agent_loop.py:352`** — el límite de 50 turnos **sólo loguea un warning**, que es
   la razón física de que `error_max_turns` no exista. Se pierde el sitio donde hay que producirlo (converge con
   `DEUDA-B·DB-30`, `_MAX_TURNS=50` hardcodeado `agent_loop.py:24`). También `num_turns` de la lista de accounting
   del error.
8. **`P4-07-8` · `B1` · tres tipos de delta descartados dejan de constar.** El tracker: *sólo* `text_delta` →
   `TokenEvent`; se descartan `thinking_*`, **`content_block_start`/`content_block_stop`**, **`message_start`**
   (`caller.py:245`), y el canónico reenvía además **`signatures`**. El destilado conserva `thinking` y «índices de
   bloque» y pierde los tres nombres restantes — que son justo los que delimitan bloques en el stream.
9. **`P4-07-9` · `C3` · `task_id` del `tool_progress`** (queda `elapsed` + `tool_use_id`) y la cadencia *«cada N s»*.
   Con `EvR5` también perdido (`P4-07-1`), la ficha entera queda sin firma.
10. **`P4-07-10` · `A2` · el defecto observable, convertido en tier.** El tracker afirma un hecho: *«el orden
    relativo entre `push_event` (poll) y `emit` (push) **no está garantizado** para el consumidor; el canónico lo
    garantiza por construcción»*. El destilado escribe *«el split 3-canales es divergencia por-diseño… el wire
    intercala»*. La divergencia es real y el tier es correcto (L10) — **pero el hecho desaparece**: un consumidor
    que mezcle los dos canales puede ver desorden, y eso es requisito del serializador `S6`, no una nota de estilo.
    Es el patrón `brecha→matiz` en su forma leve, y por eso se cuenta.
11. **`P4-07-11` · `G3` · la liga `05·GAP-EXEC1` (dedup de notificación)**. El destilado conserva `_notify`
    `runtime.py:294`, el gate `parent_session_id` (297) y `final_text` vacío (`05·FIND-EXEC3`), y pierde justo la
    remisión al gap de deduplicación — el que decide si el padre recibe la notificación **una** vez.
12. **`P4-07-12` · goteo de campo (4).** `I1` pierde `output` (distinto de `stdout`/`stderr`) · `J3` pierde `error` ·
    `K5` pierde **`fileSize`** · `E1` pierde el *porqué* de los cache-tokens (*«prefijo byte-idéntico del fork,
    05»*), que es la única frase que ligaba el accounting con el fork.

### 13.3 Dos defectos en la **capa tracker** (no son DR-1)

- **`T1` · el §Resumen de estados del tracker (:200) está mal en CUATRO de cinco cifras.** Declara
  `✅5 · 🟡8 · 🔀15 · ❌16 · ⛔4` = **48** *«sobre ~48 features»*. Contado fila a fila aquí: **4·6·16·14·4 = 44**,
  que son exactamente las 44 filas de su propio grid. Las cinco cifras suman su propio total ⇒ se presentan como
  **partición**, no como conteo de otra unidad; bajo ninguna lectura se reproducen desde la tabla.
  **Y aquí 07 hace lo que 06 no hizo:** el destilado **re-contó** y publicó `✅4·🟡6·🔀16·❌14·⛔4` en su
  `§Nota de honestidad`. **El número del destilado es el correcto** — verificado por mí sobre la tabla del tracker.
  **Lo que falla es el diagnóstico:** lo rotula *«fuzz de sub-features»*, es decir, archiva un **recuento erróneo**
  como si fuera una diferencia de denominador. Ver consecuencia 28.
- **`T2` · la remediación `EvR2` es más estrecha que el hallazgo `F0` del mismo tracker.** `F0` enumera **14**
  campos del `init`; la firma de `EvR2` propone `InitEvent` con **7**. El tracker se contradice a sí mismo entre su
  tabla y su plan, y como el destilado perdió **ambos** (`P4-07-1`/`P4-07-3`), la contradicción no llegó a
  detectarse en ninguna capa.

### 13.4 **Cinco inversiones aguas arriba** — y una de ellas invierte una anotación mía

- **`I1` · `07·B2` es el 20º CORE-GAP de 07 y no vive en 07.** Tres fuentes independientes lo cierran:
  `DEUDA-A §1.1·K4` (:234-239, *«se cierra como **CORE-GAP condicionado**»*), `DEUDA-A §4(d)` (:661-667, la línea
  *«bajo objeción, NO cerrado»* **tachada** y sustituida por *«CERRADO por `DEUDA-B §7.2`… tiene tier, forma y
  hogar»*) y `DEUDA-B §7.2`, que además aporta la razón técnica verificada: `EventBus.emit` despacha por
  **`type(event)`** (`bus.py:40`) ⇒ la forma no es un `EventEnvelope` sino **campos de identidad en el `Event`
  base**, viable porque los 5 subtipos tienen todos sus campos con default.
  **`SEPARACION/07-events.md` no se enteró:** la fila `B2` sigue **🔀 T2-BASE-MECANISMO**, `§2.3` sigue listando
  **19** CORE-GAPs y `§3.2·5` sigue archivando la familia bajo *«divergencias por-diseño»*.
  **Y el defecto se propaga:** `DEUDA-A §0.2:139` acredita a 07 con **19** copiando la lista del destilado ⇒ **el
  recuento corregido no existe en ningún documento del corpus**. Es el espejo de `06·I1`: allí el rollup no recogió
  a la categoría; aquí el rollup **corrigió** a la categoría y la categoría nunca lo supo.
- **`I2` · c24 = 6 de 7. La séptima costura de `§2.1` no tiene número en `SEAMS`.** Numeradas: `Event`+`EventBus`
  y `stream()` → **S5** · wire → **S6** · `on_progress` → **S7** · hook-sink → **S8** · model-caller → **S1**
  (y, fuera de `§2.1`, `H1`→**S9**, `J3`→**S10**). Sin número: **el «cable de usage-accounting»** (`E2`/`E3`, el
  `B-usage` que **07 mismo recalificó** a CORE-GAP). `S1` cita `07·E1`, pero eso es el **shape** del `Usage` en la
  firma del caller, no el **cable** `DoneEvent.usage → agregado de sesión → breakdown por modelo`.
  **Consecuencia dura:** `BATTERIES·B04 budget` declara depender de `B-usage`, y `SEAMS §5` es el índice desde el
  que se planifica la construcción ⇒ **una costura sin `S#` no aparece en ningún plan**.
  **Es peor que `06·I3`:** allí la causa estructural era que 06 **nunca fue fuente** de `SEAMS`. `SEAMS:4` dice que
  se destiló de `{01,16,07,02,05,09}` — **07 sí fue fuente**, y aun así perdió una de sus siete. La consecuencia 24
  se queda corta (ver consecuencia 29).
- **`I3` · `SEAMS·S21` remite tres cosas a 07 que 07 nunca recibió — y el dueño real no es 07.** `:405`
  (*«Auto-drain in-loop … → sigue anclado en 07·events, NO se realizó aquí»*), `:408` (*«el hook de turn-start se
  dispara una vez por `run()` … → ancla en 07·events, no aquí»*) y `:407` (el shape XML `<task-notification>`).
  En `SEPARACION/07-events.md` **no hay fila para ninguna de las tres**: `F3` aporta sólo `post_turn_summary` y `G3`
  la *emisión*. Pero la re-lectura de `DEUDA-B §9` lo resuelve al revés de como parecía: el dueño es **`DB-29`/
  `H-5`** (CORE-GAP con hogar en `DEUDA-A`, remediación en `AC-07`), no 07. ⇒ **no es una capacidad que 07 haya
  perdido: es una remisión mal dirigida** que debe re-apuntarse a `H-5`/`AC-07`.
- **`I4` · cita colgada `07·E19` en `SEAMS:405`.** El bloque E de 07 es `E1..E5`. El origen real es **`05·E19`**,
  como el propio `:407` escribe (*«05·E19 → 07»*): al remitir, el prefijo se perdió y quedó un ID inexistente.
  Misma familia que el `FIND-HOOK4` fantasma del par 06. Corrección determinada (D-06·1).
- **`I5` · un residuo del rótulo descartado — y la refutación de una anotación mía.**
  **Anotación previa mía, FALSA:** en el tramo anterior registré que `DEUDA-A` *«sigue cargando la forma
  `EventEnvelope` en `§1.1·K4` y `§2·ID-6` (= `CAT-h10` sin ejecutar)»*. Re-abierto `DEUDA-A` 1→EOF: **`CAT-h10` SÍ
  se ejecutó en A-CIERRE·P0** y la forma vigente está declarada en los seis sitios que `SEAMS:490-492` enumera —
  `K4` (:221-232), `ID-6` (:492-499), `§2.8·9` (:538), `§3·§1.4` (:600), `§4(d)` (:661-667).
  **Lo que sí queda:** `DEUDA-A §1.3:362` («orden de ataque») aún dice **«`K4` (sobre del evento)»** — el título
  descartado, séptimo sitio que sobrevivió al barrido. Corrección determinada (D-06·1). *La anotación errónea de
  `EVIDENCIA.log:204` queda trazada con línea nueva, per `D-06·2`.*

### 13.5 Consecuencia 14 — **no aplica a este par**, y en su lugar aparece un ENDURECIMIENTO en `§1.4`

**07 no tiene línea en `00-INTEGRADORES §1.7`, y es correcto:** `§1.7` vierte los `OI-*` de los **12 ciclos A3**;
07 pertenece a la **espina A1.7** y sus obligaciones están vertidas **y realizadas** en `§1.2` (`OI-EVT-1`, stream),
`§1.4` (`OI-EVT-2` wire · `OI-EVT-3` init) y `§2.2` (`OI-EVT-4`, capa de cuenta rate-limit/auth/overage). El
marcador de la consecuencia 14 sigue en **3 de 3 pares medidos**; **07 no es medible** y no se fuerza un 4º dato.

**Pero `§1.4` contiene un ENDURECIMIENTO, y es del mismo tipo que el de `§1.6` que destapó el par 06.** Su criterio
de aceptación exige al integrador: *«un subagente background completado **notifica al padre** en el siguiente
límite de turno»*, con origen declarado `S21 NotificationSink (05·E5/E19)`. **Ese criterio es hoy no-satisfacible
por el integrador**, y lo prueban dos fuentes leídas 1→EOF: `SEAMS·S21:391-397` (*«el hook está SUB-PARAMETRIZADO
… `process_background_notification(session, n)` exige el `Session`, que se construye dentro de `_run_loop` y no se
expone por ningún accesor … **La delegación al integrador no está incompleta: es imposible**»*) y `DEUDA-B §9/
DB-29` (`H-5`: maquinaria completa sin call-site ⇒ capacidad ausente, no delegación). ⇒ prosa de nivel N (el
*estado* de hoy) citada como obligación exigible en N+1 (el *contrato del integrador*). Segundo ENDURECIMIENTO
detectado **en el consolidador**.

### 13.6 Lo que **NO** se perdió ni se degradó (anti-padding, L10, doble filo)

- **La frase que sostiene todo el par llegó verbatim.** El tracker :346-362 establece que la costura de consumo del
  wire es *«genuinamente externa **por diseño**, hermana de `subscribe_all`/`register` de hooks (06), **NO** un
  huérfano tipo `observer/`; distinta de `FIND-EXEC1`, donde la ruta interna SÍ está rota porque el factory nunca
  llama `set_runner`»*. El destilado la conserva íntegra en `§2.1` **con la etiqueta L10**. Es la frase que impide
  que `DEUDA-B` archive `S6` como maquinaria muerta a borrar — es decir, es exactamente el tipo de frase cuya
  pérdida produjo el **36 % de órdenes BORRAR destructivas** que midió `R-1`. Aquí no se perdió.
- **La corrección de tier de `B-usage` (DEUDA-B → CORE-GAP, L10) viajó a TRES destinos.** `DEUDA-A §1.2(a):316-318`
  (*«ya recalificado a CORE-GAP por 07»*) · `DEUDA-B §1` (que toma `07·§2.4` como **el precedente del rollup
  entero**: *«A3.DB aplica ese criterio a los 7 ítems»*) · `BATTERIES·B04`. **Es justo lo que NO ocurrió en el par
  06**, donde la corrección de tier se quedó en casa.
- **c23 es el positivo más fuerte de los 8 pares medidos.** `DEUDA-A §0.2:139` acredita **19** CORE-GAPs y los
  **enumera uno a uno** (`B1·C3·D1/D2/D3/D5·E1/E2/E3/E5·F0/F1/F2·G1/G2/G3·H1·I1·J3`) — coincidencia exacta con
  `07·§2.3`; `§1.2(a)` los reparte por destino. `BATTERIES` sitúa **cinco** unidades con 07 como origen
  (`B01 compaction` ← `07·H1` · `B04 budget` · `B05 commands` ← `07·J6` · `B06 wire` ← `07·GAP-EVT5/K4/K5` ·
  `B11 background-agents` ← `07·F3`) y `§3` traza la fila `07·events`. `00-INTEGRADORES` **realiza** las cuatro
  `OI-EVT`. **Incluso las 4 filas ⛔/CLI-ONLY** (`C4`/`F4`/`K3`/`J6`) reciben hogar de integrador
  (`§1.4:125-126`). Ningún par anterior repartió tan completo.
- **44/44 reconcilia de verdad**, verificado por mí fila a fila (c26), y el destilado es **la única de las dos caras
  cuyo recuento es correcto**. Su `§Nota de honestidad` (:209-212) documenta además su propia sobre-declaración
  (haber citado `bus.py`/`protocol.py`/`event_types.py`/`agent_loop.py:312/324` sin abrirlos ese ciclo) y la
  re-apertura antes de firmar: **es el único destilado medido que se auto-corrige en el propio documento**.
- **0 INVENTADAS · 0 filas sin colocar · las 44 con TIER y destino.**

Decir «07 se destiló mal» sería padding: **35 de 44 fichas intactas, 0 inventadas, la tesis arquitectural entera y
el reparto aguas arriba impecable.** Lo que 07 pierde no son fichas: es **su capa de remediación** (`13.2·1`) y
**su columna canónica** (`13.0`). Y lo que le falla no es su destilado: es que **nadie le devolvió la corrección de
`B2`** (`13.4·I1`).

### 13.7 Consecuencias nuevas para el resto de P4″

27. **Un par puede reconciliar 44/44 fichas y perder entera su capa de remediación.** Las fichas son el *qué*; el
    §Plan de remediación es el *cómo*, y es lo que Fase B consume. ⇒ **sonda `c27` obligatoria en los 10 pares
    restantes: cotejar el §Plan/§Remediación del tracker contra el destilado ítem a ítem** (firma · cableado ·
    orden · test), **no** contra el grid. Un `(EvRn)` entre paréntesis **no** es la remediación.
28. **El destilado puede corregir al tracker y aun así fallar el diagnóstico.** 07 re-cuenta bien (44) y rotula la
    diferencia como «fuzz de sub-features» en vez de decir *«el §Recuento del tracker está mal»*. ⇒ cuando las dos
    caras discrepen en un recuento, **exigir que el destilado nombre cuál de las dos está mal**. Una discrepancia
    archivada como diferencia de denominador es un defecto **no reportado**, y sobrevive.
29. **Generaliza y corrige la consecuencia 24.** Una costura declarada en `§2.1` y no numerada en `SEAMS` es
    invisible al plan de construcción **aunque la categoría SÍ haya sido fuente de `SEAMS`** (07 lo fue y le falta
    1 de 7). ⇒ el cotejo `§2.1` ↔ índice de 29 es obligatorio para **los 18**, no sólo para las 12 no-fuente.
30. **Un criterio de aceptación del consolidador puede exigir al integrador algo que el base le hace imposible.**
    ⇒ **sonda `c30`: cada criterio de aceptación de `00-INTEGRADORES` que cite una costura debe contrastarse con el
    estado de esa costura en `SEAMS`.** Si el estado es `ausente`/`existe-sin-poblar`/`existe-put-sin-drain`, el
    criterio **no es satisfacible** y es ENDURECIMIENTO, no obligación.
31. **c25 tiene una segunda forma, y renumerar es la respuesta equivocada.** En 06 los `K\d` eran **extras locales**
    del destilado ⇒ renumerar a `KH\d` era correcto. En 07 los `K1..K5` son **filas nativas del grid del tracker**
    (bloque `K · Transcripto`): renumerarlas rompería la reconciliación 44=44, que es justo lo que este par hace
    bien. ⇒ **la regla correcta no es renumerar, es la disciplina de prefijo**: `07·K5` (fila) vs `K5` (keystone de
    `DEUDA-A`). `DEUDA-A` la respeta (`§1.1·K2` cita `07·B3`/`07·K5`); **`BATTERIES·B06` la rompe**: su fila usa
    `origen: 07·GAP-EVT5/K4/K5` (filas) y, dos columnas después, `CORE-GAPs: K4 (identidad en el Event base) · K5`
    (keystones) — **dos referentes distintos con la misma grafía en la misma fila**.
32. **La firma del §Plan del tracker puede estar recortada respecto de su propia contraparte canónica.** Apareció al
    restituir `EvR2`: la firma del tracker tiene **7 parámetros** y el `init` de `coreSchemas.ts:1457-1494` tiene
    **14**. No es una pérdida del destilado —el destilado no llegó a traerla— sino un defecto **de la capa tracker**
    que la destilación habría propagado intacto. ⇒ **`c27` se extiende: al cotejar el §Plan ítem a ítem, cada firma
    se contrasta además contra los campos de su contraparte canónica citada en el propio tracker.** Restituir una
    firma incompleta es peor que no restituirla: le da grado probatorio a un recorte.

### 13.8 · REMEDIACIÓN — **APLICADA** (2026-07-29)

`SEPARACION/07-events.md`: **216 → 355 L** (+139, +64 %). Precedente: el par 06 fue 440 → 710 L.

**A · Las 12 pérdidas, una por una:**

| # | pérdida | dónde se restituyó | qué se escribió |
|---|---|---|---|
| `P4-07-1` | §Plan de remediación EvR1-EvR7 (el bloque mayor) | **§2.6 nueva** | los 7 ítems con los **6 campos L05** (comportamiento · seam · firma · cableado · orden · prueba). Corrige de paso la asimetría inversa: la cara integrador (§2.5) tenía sus 6 campos y los 20 CORE-GAPs del base **ninguno**. Al escribir `EvR2` se detectó que **la firma del tracker tiene 7 parámetros y la canónica 14** ⇒ la firma a implementar es la de 14 |
| `P4-07-2` | §0 cabecera: 5 contrapartes canónicas con LOC + mapa de emisión | **§0.1 nueva** | tabla de las 5 (`coreSchemas.ts` 1854 · `sdkMessageAdapter.ts` 303 · `hookEvents.ts` 192 · `query.ts` 1729 · `QueryEngine.ts` 1295) con qué aporta cada una + los emisores/consumidores del runtime con ancla. **Revierte el patrón 3 en este par: 0 → 5 contrapartes, 0 → 8 anclas `.ts:línea`** |
| `P4-07-3` | F0: 6 de 14 campos del `init` | fila **F0** | los 6 (`apiKeySource`·`betas`·`claude_code_version`·`cwd`·`fast_mode_state`·`mcp_servers[]{name,status}`) **con su razón de ser**, no como lista: el `status` de MCP es el único punto del protocolo donde se sabe que un servidor no levantó |
| `P4-07-4` | J1: 7 de 11 campos del rate-limit | fila **J1** | shape completo. Documenta que **`status` (allowed/warning/rejected) era el único campo con semántica de control** y que **OI-EVT-4 cita `rejected`** ⇒ el corpus dependía de un valor que el documento había dejado de definir |
| `P4-07-5` | D5: taxonomía de error de dos niveles + `max_output_tokens` | fila **D5** | los dos niveles (enum del assistant `1256-1266` vs `subtype` del `SDKResultError` `1428-1451`) **no se aplanan**; `max_output_tokens` no es fallo — colapsarlo hace reintentar lo que debía continuar |
| `P4-07-6` | D1: `duration_ms` / `api_ms` | fila **D1** | los **dos relojes** y por qué su diferencia importa (atribuir latencia a tools vs modelo) |
| `P4-07-7` | D2: ancla `agent_loop.py:352` + `num_turns` | fila **D2** | no es «límite ausente» sino **límite sin efecto ni reporte** (sólo warning, y sin `num_turns` nadie puede detectarlo a posteriori) |
| `P4-07-8` | B1: `message_start` · `content_block_start/stop` · `signatures` | fila **B1** | el canónico reenvía el raw stream event completo; sin índices de bloque no se reensamblan bloques concurrentes y sin `signatures` no se re-envía thinking firmado |
| `P4-07-9` | C3: `task_id` + cadencia | fila **C3** | `task_id` **además de** `tool_use_id` (una tool larga corre dentro de un subagente ⇒ liga B2) y **heartbeat periódico**, no un disparo único al cruzar umbral |
| `P4-07-10` | A2: el orden relativo push↔poll no garantizado | fila **A2** | «garantiza orden **dentro de un canal**»; quien reconstruya el stream (OI-EVT-2) **impone** el orden, no lo asume. *(Era el `brecha→matiz` leve del par.)* |
| `P4-07-11` | G3: liga `05·GAP-EXEC1` (dedup) | fila **G3** | la notificación no está deduplicada ⇒ estados terminales repetidos; la dedup pertenece a 05, el síntoma se observa aquí |
| `P4-07-12` | goteo de campos: I1 `output` · J3 `error` · K5 `fileSize` · E1 cache | filas **I1·J3·K5·E1** | cada uno con su consecuencia: `output` = la **decisión** del hook (no su traza); `error` = si el reintento tiene sentido; `fileSize` = lo que hace del índice un índice; cache = el coste **no es aproximable, es incalculable** |

**B · La inversión `I1` (B2), aplicada en 5 sitios del documento:** fila **B2** (🔀 T2-BASE → **CORE-GAP
condicionado**, con la acción «campos en el `Event` base, **no** envelope») · **§2.3** (19 → **20 CORE-GAPs**,
con `B2` en la lista) · **§3.1** (fila del ledger) · **§3.2·5** (la pregunta de doble filo pasa de «ninguno» a
«uno sí lo era»: `G4` es divergencia, `B2` no) · **§3.2·2** (el reparto pasa a `✅4·🟡6·🔀15·❌15·⛔4 = 44`; el
total no cambia).

> **Lo que la remediación hizo explícito DENTRO del par** *(ya establecido en `13.4·I1`; aquí queda escrito en el
> documento que lo sufría)*: `DEUDA-A §1.1·K4` **ya contenía esta inversión** —
> «*objeción formal registrada por 17, que este rollup ADOPTA: `07·B2` cerró `parent_tool_use_id` como 🔀
> argumentando atribución implícita*»— y ya la cerraba como **CORE-GAP condicionado**. La corrección se adoptó
> **aguas arriba y nunca bajó al documento del par**. `I1` no es, por tanto, un hallazgo nuevo de P4″: es una
> **propagación que faltaba**, viva y sin aplicar desde que 17 la formuló. Es la misma clase de defecto que
> `AC-03`/`CAT-h10` (decisión tomada en un doc, no aplicada en el que la sufre) y que `DEUDA-A` ya se había
> escrito a sí misma como regla: «*una decisión que corrige un doc cerrado se aplica EN ese doc*».

**C · El VEREDICTO reescrito:** `✅ NADA PENDIENTE → A1.4` ⇒ **`⛔ PENDIENTE(S)` — RECONCILIADO, no CERRADO**,
con separación explícita entre lo firme (44 filas · 20 CORE-GAPs · 7 costuras · 4 batteries · 4 OI-EVT · §2.6 ·
§0.1) y los 6 pendientes que viven fuera. El destino de flujo (A1.4 · 02·loop) no cambia. Mismo patrón que 06.
También se corrigió el **diagnóstico blando** de la §Nota de honestidad («*el delta con 48 es la fuzz de
sub-features*») por el hecho medido: **4 de las 5 cifras del §Resumen del tracker están mal** y los signos van en
direcciones opuestas ⇒ §Resumen desincronizado de su propio grid, no granularidad distinta (`T1`).

**D · Correcciones determinadas FUERA del par (D-06·1, ejecutadas, no elevadas):**

| doc | antes | ahora |
|---|---|---|
| `DEUDA-A §0.2` | `07·events \| 19 \| B1·C3·…` | `20`, con `B2` en la forma; total `≈152` → `≈153` |
| `DEUDA-A §1.3:362` | «**K4** (sobre del evento)» — último residuo del rótulo descartado | «identidad en el `Event` base», con puntero a `§1.1·K4`. **Cierra `I5`**: los 6 sitios de `CAT-h10` ya estaban corregidos en P0 y éste era el séptimo, no un fallo de P0 |
| `SEAMS:405` | `→ 07·E19` (**ID inexistente**: el grid de 07 acaba en `E5`) | `→ 05·E19`, que es lo que la firma BORRADOR dos líneas más abajo ya decía. **Cierra `I4`** |
| `BATTERIES·B06` | `07·GAP-EVT5/K4/K5` (filas) y `K4 · K5` (keystones) en la misma fila | prefijos disciplinados (`07·Kn` filas / `DA·Kn` keystones) + nota de la colisión. **Cierra la parte determinada de la consecuencia 31** |

**E · Lo que NO se cerró y por qué (queda como ítem de ledger):**
- **`I2`** — el cable de usage-accounting **sin número S** en `SEAMS` (c24 = 6/7), pese a que 07 **sí** fue
  documento de origen del rollup. Anotado en `07 §2.1`; asignar el S# es trabajo de `SEAMS`, no del par.
- **`I3`** — las tres remisiones de `SEAMS·S21` cuyo dueño real es `H-5`/`DB-29`, no 07. Requiere abrir S21 con su
  dueño delante: **no es una sustitución de una grafía**.
- **`BATTERIES·B06`**, el `K5` de la columna *CORE-GAPs*: dos lecturas defendibles (`07·K5` SessionInfo vs
  keystone `DA·K5` `ToolResult`). **D-06·3 ⇒ no la resuelvo por mi cuenta.**
- **ENDURECIMIENTO en `00-INTEGRADORES §1.4`** (prosa aproximada de este nivel citada como hecho estructural en
  el siguiente).
- **`EvR7`**: rótulo asignado por eliminación; declarado como tal **dentro** de §2.6. El contenido de los siete
  ítems no depende de la asignación.

---

## §14. Par **08 · signals** — tracker 441 L · SEPARACION 463 L · 26 fichas (**`AC-12`** · 9/18)

**Ambas caras 1→EOF en esta pasada y RE-ABIERTAS tras la compactación** (`HOMOLOGATION/08-signals.md` 441 ·
`SEPARACION/08-signals.md` 463, una llamada cada una). La re-apertura no fue ceremonia: la primera lectura tenía
su línea `AC-28` escrita en `EVIDENCIA.log`, pero el **contenido** había caído del lado comprimido, y este par
exige **cadenas exactas** para editar. Es el tercer caso en `A-CIERRE` en que `DEUDA-A §0.1` se paga en vez de
declararse; los dos anteriores (`EVIDENCIA.log:204` y el pendiente 3 del par 07) **refutaron** anotaciones mías.

**Columna de CRUCE 1→EOF y propia, 5/5** — `SEAMS` 539 · `00-INTEGRADORES` 242 (tramo anterior) ·
**`DEUDA-A` 700 · `DEUDA-B` 1129 · `BATTERIES` 573** (este tramo) = **3.183 L**.

**Primera inversión estructural de `P4″`: el destilado es MÁS LARGO que el tracker** (463 vs 441). En los ocho
pares anteriores la relación fue siempre la contraria (07: 216 vs 445). No es volumen-camuflaje: se mide abajo
(`14.1`) que el exceso es **producto real** — 11 de 26 fichas ENRIQUECIDAS y una cara de integrador nueva.
Y precisamente por eso este par es el más peligroso de la pasada: **un documento que produce de más puede
arrastrar un ✅ falso sin que el saldo lo delate.** Es lo que ocurrió.

### 14.0 Patrón 3 primero (encabezados, O(1)) — novena confirmación de `P4-01-1`

| capa | encabezado |
|---|---|
| tracker | `# · Feature (canónico) · Runtime · Estado · Nota` |
| SEPARACION | `ID · resumen · núcleo\|cáscara · TIER · destino · est. · acción` |

`Feature (canónico)` **sin sucesora**, novena vez. Retención de la columna A: el tracker cita **11 archivos `.ts`
con LOC** (`abortController.ts` 99 · `StreamingToolExecutor.ts` 530 · `useCancelRequest.ts` 276 · `Task.ts` 125 ·
`toolExecution.ts` 1745 · `Tool.ts` 792 · `QueryEngine.ts` 1295 · `query.ts` 1729 · `toolHooks.ts` 650 ·
`claude.ts` 3419 · `useBackgroundTaskNavigation.ts`) y **≳30 anclas `.ts:línea`**. El destilado retiene **cero
LOC** y **4 anclas** (`query.ts:1015` · `query.ts:1046,1501` · `StreamingToolExecutor:221-233` · `Task.ts:53`).
**≈87 % de pérdida de la columna canónica** — mejor que el 100 % de `01·05·07`, peor que `06`.

**Matiz que este par añade al patrón:** aquí la pérdida **no** es indiferente. `S2` es una fila cuya verdad se
decide en la **frontera** entre B y la librería de modelos, y el destilado se quedó con la mitad B del cable.
El patrón 3 dejó de ser una pérdida documental y produjo un **error de estado** (`14.2`).

### 14.1 Saldo — 26/26 fichas

| veredicto | n | fichas |
|---|---|---|
| CONSERVADA | **10** | S6 · S7 · S9 · S11 · S17 · S19 · S24 · S25 · **S2 (DR)** · **S12 (DR)** |
| **ENRIQUECIDA (verificada)** | **11** | S3 · S4 · S5 · S8 · S10 · S13 · S14 · S20 · S21 · S22 · S23 |
| **COMPRIMIDA-CON-PÉRDIDA** | **5** | S1 · S8ᵇ · S16 · S18 · SIG13 |
| **INVENTADA** | **0** | — |
| PERDIDA (fila sin colocar) | **0** de 26 | — |
| **PERDIDA (unidad del tracker fuera del grid)** | **3** | **§Estado** (suite + los 7 xfails) · **§Gaps·GAP-SIG3** (rótulo) · **§Detalle·pieza 1** (`ToolStatus`+`isConcurrencySafe`) |
| **PERDIDA (contra la columna de CRUCE, no contra el tracker)** | **6** | `DB-h2` · la corrección `RV-6` de `DB-03` · `16·FIND-MODELS4` · `05·E15` · `11·CG-MCP-20` · `SEAMS §S24` watchdog |

*(`S8` aparece dos veces por ejes distintos: ENRIQUECIDA en remediación —el tracker la remitía a `SR2` sin
desarrollar y el destilado le escribe los 6 campos `L05`— y COMPRIMIDA en la descripción canónica, `14.3·P4-08-14`.
Se cuenta **1 vez** en el total, en su eje dominante; el desglose se declara aquí para que las cifras cuadren:
10+11+5 = 26 con `S8` contada en ENRIQUECIDA.)*

**`ENRIQUECIDA = 11` es el dato que invierte el par 07.** El tracker escribe literalmente en `SR2` (:275):
*«Aquí se referencian; no se re-desarrollan»* — cinco findings (SIG2/3/4/10/11) remitidos a `DEUDA-B §B-signals`
sin firma, sin cableado, sin orden, sin prueba. **El destilado los desarrolla**: `CG-SIG-1..6` llevan los 6 campos
`L05` completos. En 07 la cara BASE se quedó sin ninguno y la del integrador con todos; **en 08 ocurre lo
contrario y además la cara del integrador se crea de cero** (el tracker sólo tenía *«es del integrador»* en `S14`;
el destilado escribe `OI-SIG-A/B/C` con los 6 campos). Este destilado **no es fiel y plano: es productivo.**

**`INVENTADA = 0` se acredita ficha a ficha**: `LAT-SIG1` y los tres `OI-SIG-*` **derivan** de material del tracker
(la precisión de cableado del arming; `S14`/`S20`), no lo fabrican.

**c26 · Recuento re-contado fila a fila sobre la tabla del tracker** (no sobre el destilado):
`✅3` (S2·S6·S20) · `🟡3` (S1·S7·S9) · `🔀4` (S12·S16·S18·S15) · `❌14` · `⛔1` (S14) = **25 filas**, `S15` contada
`🔀`. Cuadra **exacto** con el `§Recuento` del tracker (:125) y con el re-recuento del destilado (26 = 25 + SIG13).
**Cero cambio de estado no declarado en el segundo salto.** El cambio de estado que este ciclo SÍ produce
(`S2`, `S12`) **no** es del destilado: es una corrección mía sobre **ambas caras** (`14.2`).

### 14.2 El defecto portante — **`S2 ✅` y `S12 🔀` son falsos, y lo prueba el código**

Éste es el hallazgo del par y hay que ponerlo antes que el saldo entero, porque un `✅` en una fila `T1-MOTOR`
es el permiso para no construir nada.

**Lo que el destilado afirma** (tres sitios, todos categóricos):
- `:72` `| S2 | … | ✅ | cableado incondicional (verificado agent_loop.py:227+caller.py:188-190); **homologación
  del seam** |`
- `:140-142` `§2.1`: *«seam T1-MOTOR de corte (S2/S12, **cableado** …) — consumidor:
  `agentic_models.StreamOptions.signal` **corta** fetch/stream y surface `APIUserAbortError`»*
- `:371-372` `§3.2·Q3`: lo lista como `✅` re-abierto **en este ciclo** contra el runtime real.

**Lo que hay en el código, leído 1→EOF por mí en este ciclo y sin apoyarme en ningún rollup:**

| paso | fuente | contenido |
|---|---|---|
| 1 | `models/caller.py:151` y `:166` | `stop: Optional[asyncio.Event] = None` |
| 2 | `models/caller.py:188-190` | `if stop is not None: opts = replace(opts, signal=stop)` |
| 3 | `agentic_models/model_types.py:100` | `signal: Any \| None = None  # asyncio.Event or AbortSignal equivalent` |
| 4 | **los 8 providers** | el corte se gatea **siempre** en `getattr(signal, "aborted", False)` |
| 5 | censo por símbolo | ocurrencias de `is_set()` en todo `agentic_models` = **CERO** |

Anclas del paso 4: `anthropic.py:450,717,732` · `openai_responses.py:238,254` ·
`openai_codex_responses.py:99,259,464,580,663,669,697,759,773` · `azure_openai_responses.py:213,229` ·
`amazon_bedrock.py:534,549` · `mistral.py:389,404` · `faux.py:275,284,297,311,327`.
`openai_completions.py:512` ni siquiera lo consulta para abortar: `if options.signal: req_opts["timeout"] = None`.

**`asyncio.Event` no expone `.aborted`.** El `getattr` devuelve `False` en toda ejecución posible ⇒ **el corte no
ocurre en ningún provider, nunca.** El seam no está *«cableado con la verificación fina pendiente en 16»*: está
**roto en el tipo del contrato**. Hay tubería y no hay señal.

**El comentario del paso 3 es la trampa, y es `RV-5` en estado puro** — *«un docstring no es evidencia de
cableado»*. `# asyncio.Event or AbortSignal equivalent` afirma exactamente lo que el código refuta.

**Corroboración independiente** (posterior a mi lectura, no fuente de ella — el orden importa bajo `L11`):
- `SEAMS §S2` clasifica el seam **`existe-roto`**: *«16·A6: se pasa `asyncio.Event`, el provider chequea `.aborted`
  que `Event` no tiene ⇒ abort ignorado»*.
- `DEUDA-A §1.2(a)`: *«`08·CG-SIG-1..9` … **Cruza `16·FIND-MODELS4` (abort roto, tipo de señal equivocado)**»*.

⇒ **El destilado tenía DOS rollups de su propia columna de cruce diciendo lo contrario, y no los consultó
para esta fila.** Eso es `L11` incumplido en el punto exacto donde `L11` existe: *el doc previo es una HIPÓTESIS.*

**Y hay un tercer testigo dentro del propio destilado, leído al revés.** `§2.4` (:277-282) observa que
`caller.py:204-245` no envuelve el `async for` en un `try/except` de abort, y concluye que un
`APIUserAbortError` *«propagaría como Exception genérica»*. La mecánica es correcta; **la premisa es falsa**: no
hay `APIUserAbortError` que propagar, porque el provider nunca aborta. El documento estaba a una pregunta de
distancia del defecto —*¿y quién lanza esa excepción?*— y no la hizo.

**Consecuencias de estado (aplicadas en la remediación, `14.9`):**
1. `S2` **`✅ → ❌`**. No es `🟡`: `🟡` sería «existe degradado». Aquí el comportamiento observable —cortar la
   llamada al modelo— **no ocurre**. Es un `CORE-GAP` nuevo, **`CG-SIG-10`**, con dueño compartido `08`↔`16`.
2. `S12` **`🔀 → ❌`**. Un `🔀` es *«divergencia por capa, delegado»*. No se puede delegar a una capa que ya
   dictaminó en contra: `16·FIND-MODELS4` **ya falló** este cable. Bajo `L07`, remitir a una categoría que ya
   resolvió el punto **en contra** no es homar con destino — es enterrar.
3. El `§3.4 VEREDICTO ✅ NADA PENDIENTE` **cae**. `L04`, sin escotilla: *«si hay ≥1 pendiente de VERIFICACIÓN, el
   veredicto NO puede ser ✅ NADA PENDIENTE»*. Y éste no es siquiera un pendiente abierto: es un pendiente
   **resuelto en contra**.
4. **Es un defecto de la capa TRACKER también** (`14.4·T1`): el gate-11 del tracker (:324) escribió
   *«Plumbing cableado en la ruta real del loop. ✅»* siguiendo el dato hasta `StreamOptions.signal` y parándose
   ahí. La frontera de un seam es el sitio donde hay que **seguir**, no donde se puede parar.

### 14.3 Las 16 pérdidas (`P4-08-1..16`)

1. **`P4-08-1` · el `✅`/`🔀` falsos** — desarrollado en `14.2`. Marca **DR** (defecto de re-verificación, no de
   destilación: el contenido viajó íntegro; lo que viajó mal es su estado).
2. **`P4-08-2` · `DB-SIG-1`/`S16`/`S18` están RANCIOS contra `R-1`/`RV-6` — y ésta es una de las entradas que
   `R-1` midió como destructivas.** El destilado ordena (`:246` título, `:249` acción, `:110`, `:112`, `§0:43`)
   *«borrar `SignalBus`/`SignalType`/`SignalHandle`»* y *«borrar `signals/` entero»*. `DEUDA-B §3.A·DB-03` fue
   **corregida el 2026-07-28** por `R-1` bajo `RV-6` (ninguna entrada BORRAR puede escribirse a nivel de módulo):
   *MUEREN* `_Node` (`bus.py:11-14`) · `SignalHandle` (:17-27) · `SignalBus` (:29-87) · `register_handler`
   (:89-96) · la semántica `RESUME`-limpia-señal (:68-69) · `SignalHandler` (`protocols.py:11-14`) · el
   `__init__.py`; ***SOBREVIVE* `SignalType`**, reubicado al **mismo módulo de vocabulario `T1`** al que `DB-01`
   manda `AgentMode` y `DB-25` manda `stop_reason`. Ejecutar el destilado tal como está **borra un símbolo vivo**.
   Es `CAT-h10` literal: *una decisión que corrige un doc cerrado se aplica EN ese doc*, y `R-1` corrigió
   `DEUDA-B` sin bajar a los destilados. `R-1` cerró con **4 de 11 entradas (36 %)** que habrían destruido código
   vivo o roto el paquete; **ésta es la quinta, y vive en otro documento.**
3. **`P4-08-3` · la precondición `DB-h2` no aparece en el destilado.** `DEUDA-B §5·DB-h2` (:714-716):
   *«borrar `signals/` tiene una precondición no escrita. `SignalType.PAUSE/RESUME` es la única traza nominal de
   pausa/reanudación, y **H-3** (`resume` no existe) sigue sin cableado desarrollado. Borrar antes de que H-3
   tenga hogar elimina el vocabulario sin sustituto.»* El destilado (`DB-SIG-3`, :256-260) manda borrar y ofrece
   *«si el runtime quiere pausa, su hogar es 04/05»* **sin condicionar el borrado a nada**. Bajo `L03` esto es
   delegación **con** destino pero **sin** orden — y el orden es justamente lo que evita la pérdida.
4. **`P4-08-4` · cuatro anclas `SRn` incumplidas contra la promesa del propio `§0`.** `:55` promete:
   *«`SRn` = entrada del §Plan del tracker»*. Verificado contra `HOMOLOGATION/08-signals.md:262-305`:
   `CG-SIG-6` (=SIG11) **no lleva `SR2`** aunque `SR2` lo enumera (:271) · `CG-SIG-7` **no lleva `SR1`** aunque
   `SR1` incluye `interrupt()` dentro del `AbortScope` (:268) · `DB-SIG-2` y `DB-SIG-3` **no llevan `SR1`**
   aunque `SR1` es literalmente *«FIND-SIG1 + SIG5 + SIG6»* · los 7 homed-fuera **no llevan `SR5`**
   (`SR5` = SIG7/SIG8/SIG12). La promesa se cumple en 5 ítems de 12. `AC-27` endurecido: **reconciliar la
   estructura del `§Plan` ítem a ítem** — un solo tracker vuelve a rendir defecto.
5. **`P4-08-5` · los xfails existentes: 4 de 7, y faltan los tres que importan.** El tracker (:242) da la
   evidencia de suite: *«6 passed + 7 xfailed strict; los xfail codifican SIG1/2/3/4/5/6/10»*. El destilado cita
   `SIG2`, `SIG3`, `SIG4`, `SIG10`. **Faltan `SIG1`, `SIG5`, `SIG6`** — exactamente los tres de `DB-SIG-1/2/3`,
   donde el destilado propone un test **nuevo** (`test_no_orphan_signalbus_in_real_path`) sin decir qué pasa con
   los que ya existen. `DEUDA-B` sí lo dice: `test_signal_bus.py` (13 tests) **se retira entero** y los xfails
   `FIND-SIG1`(:63)/`FIND-SIG5`(:148) **se RETIRAN, no se ponen en verde** (un xfail que codifica un gap
   desaparecido no «pasa»: deja de tener objeto). La distinción es ejecutable y se perdió.
6. **`P4-08-6` · el `§Estado` del tracker no tiene contraparte.** Suite global `582 passed · 3 skipped ·
   40 xfailed`, lint verde (ruff/mypy/bandit). Es la línea base contra la que Fase B medirá regresión.
7. **`P4-08-7` · `GAP-SIG3` sin rótulo.** El tracker (:220) agrupa los tres ejes (reason · árbol ·
   `interruptBehavior`) en **un** gap. El destilado los reparte bien en `CG-SIG-1/2/3` pero **nunca nombra
   `GAP-SIG3`**, mientras sí nombra `GAP-SIG1` y `GAP-SIG2`. Pérdida de etiqueta, no de contenido — pero
   asimétrica, y las etiquetas son el índice por el que 16 y 09 entrarán a este documento.
8. **`P4-08-8` · `ToolStatus` + `isConcurrencySafe` sin colocar.** El tracker abre el detalle de
   `StreamingToolExecutor` (:44) con *«Tres `ToolStatus` (queued/executing/completed/yielded) + control de
   concurrencia (`isConcurrencySafe`): safe corren en paralelo, no-safe en exclusiva»*. Las **otras cinco**
   piezas del bloque recibieron fila-S (S8·S21·S22·S23 + `getAbortReason`); **ésta no la recibió en el tracker ni
   la recoge el destilado**. Su hogar lo nombra el propio tracker en su brief de 09 (:437): **`FIND-TOOL1`**
   (*«dispatcher SECUENCIAL, sin `isConcurrencySafe`»*). Se homa a **09** en la remediación.
9. **`P4-08-9` · los cabos entrantes de `DEUDA-A §1.2(a)` no se recogen**: `16·FIND-MODELS4` (que es el que
   dictamina sobre `S2`/`S12`) y `05·E15` (*kill ⇒ pérdida de trabajo*, que es el argumento material a favor de
   `CG-SIG-9`). El destilado cita *«11·mcp registra su release»* pero **sin el identificador `11·CG-MCP-20`**,
   que es como `BATTERIES §2.3` lo indexa: una remisión sin identificador no es localizable desde el otro lado.
10. **`P4-08-10` · los cabos entrantes de `SEAMS` no se recogen**: `§S24` (watchdog/deadline —
    `01·CTR-15 arm_watchdog` es no-op y su decisión es *«completar o retirar según lo cubra el `AbortScope`»*,
    o sea **depende de 08** y 08 no lo menciona) y `§S4·A2.5` (*«`cancel`/`runtime_id` NO realizados en el
    skeleton; cancel→08·signals»*).
11. **`P4-08-11` · `LAT-SIG1` deja abierta una binaria que el rollup ya cerró.** El destilado: *«o el loop
    construye `ModelRequest` … o se borra el campo `stop`/la clase»*. `DEUDA-B §7.3`/`§3.A·DB-10(b)` ya decidió:
    **BORRAR ahora** — `ModelRequest` declara `thinking_budget` que el motor **no soporta** y le faltan
    `system_sections`/`system_override` que el motor **sí usa**. Bajo `D-06·1` esto se **ejecuta**, no se eleva.
12. **`P4-08-12` · patrón 3** — `14.0`. Aquí con consecuencia material, no sólo documental.
13. **`P4-08-13` · `S1` pierde las dos anclas de `Task.ts`**: *«un controller POR task»* (:39) y la nota
    *«abortController were dead weight»* para kill (:71) — que es precisamente el argumento canónico de por qué
    el nivel *agent* y el nivel *work* son distintos (`CG-SIG-9`).
14. **`P4-08-14` · `S8`/`CG-SIG-4` pierde la tercera condición del bubble y la regresión que lo justifica.**
    El tracker (:46) da **tres**: `reason !== 'sibling_error'` **AND** el padre no estaba abortado **AND** no hay
    `discard` — más la razón de existir (*regresión #21056*, `ExitPlanMode`). El destilado conserva dos y pierde
    *«el padre no estaba abortado»*, que es la que evita el doble-abort, y el número de regresión, que es la única
    prueba de que la condición no es teórica.
15. **`P4-08-15` · `SIG13` pierde su ancla canónica y `TaskStopTool`.** El tracker referencia
    `useBackgroundTaskNavigation.ts:156-158` (*Escape sobre teammate running → aborta el turno, NO mata*) y liga
    a `TaskStopTool`/`emitTaskTerminatedSdk('stopped')`. El destilado conserva `TaskStop` y pierde el resto.
16. **`P4-08-16` · `c28` no adjudicado.** El tracker cuenta `context/adapters.py` = **86** L (:391); el destilado
    = **85** (:413, :430). `wc -l` = **85** ⇒ el destilado acierta. **Pero no nombra que el tracker se equivoca**,
    y `c28` exige exactamente eso: cuando las dos caras discrepan en un conteo, el destilado debe **nombrar cuál
    está mal**, o el lector siguiente vuelve a medirlo.

### 14.4 Defectos de la **capa tracker** (no son del segundo salto)

- **`T1` · el gate-11 del tracker paró en la frontera del seam.** `:324` sigue `S2` hasta
  `agentic_models.StreamOptions.signal` y escribe `✅`. El dato tenía **un paso más** —qué hace el consumidor con
  ese `signal`— y ese paso estaba a un `grep .aborted` de distancia. La regla que este par deja escrita:
  **en una fila `T1-MOTOR`, el cableado termina en el CONSUMIDOR, no en el punto de entrega.** El tracker se
  auto-absolvió además explícitamente (:412: *«No es sobre-declaración de estado (S2/S6/S20 siguen ✅ …)»*), lo
  que convirtió una omisión en una garantía.
- **`T2` · `SIG9` y `SIG13` nunca recibieron fila-S en el tracker** (`DEUDA-B §2` filas 3.1/3.2 lo dice:
  *«SIG9/SIG13 nunca recibieron fila»*). El destilado **lo corrige** —`SIG13` explícito como fila 26,
  `SIG9`→`CG-SIG-8`— y eso es mérito suyo, registrado en `14.1`.
- **`T3` · `adapters.py` 86 vs 85** (`14.3·P4-08-16`).

### 14.5 Sondas — resultado una a una

| sonda | objeto | resultado |
|---|---|---|
| **c23** | inversión aguas arriba en el REPARTO de los rollups | **DEFECTO** — `DEUDA-A §1.2(a)` y `SEAMS §S2` contradicen `S2 ✅` y el destilado no lo absorbió (`14.2`). En sentido inverso, `BATTERIES §3`/`§5` **confirman** `§2.2` (ninguna battery, primitiva del base) |
| **c24/c29** | `§2.1` (6 costuras) vs el índice de 29 seams de `SEAMS` | **PARCIAL** — las 6 tienen contraparte, pero `SEAMS §S24` (watchdog) y `§S4·A2.5` (cancel del skeleton) apuntan **a 08** y no tienen contraparte aquí (`P4-08-10`) |
| **c25/c31** | colisión de namespace `S*` | **DEFECTO** — `SEAMS` numera `S1..S31` (costuras); 08 numera `S1..S25` (filas del grid), **sin prefijo**. Colisiones materiales: `08·S2` (propagación al modelo) vs `SEAMS·S2` (la señal de abort) · `08·S16` (`SignalBus`) vs `SEAMS·S16` (`ToolProtocol`) · `08·S4` vs `SEAMS·S4` (skeleton, cuyo `A2.5` **remite a 08**). Remedio = la disciplina de prefijos de `BATTERIES·B06`, **nunca renumerar** |
| **c26** | re-conteo del grid fila a fila | **LIMPIO** — 26 = 25 + SIG13; los 5 estados cuadran exacto con el `§Recuento` del tracker; cero cambio no declarado |
| **c27/c32** | `§Plan` `SR1-SR5` ítem a ítem | **DEFECTO** — 4 anclas ausentes + el bloque homed-fuera (`P4-08-4`) |
| **c28** | discrepancia de conteo entre caras | **DEFECTO de forma** — el destilado acierta (85) pero no adjudica (`P4-08-16`) |
| **c30** | `00-INTEGRADORES` vs estado de seams | **LIMPIO** — `§1.7` lleva `OI-SIG-A/B/C` con *«sobre la primitiva del base (08 no aporta battery)»*, coherente con `§2.2` y con `BATTERIES §3` |

### 14.6 Lo que **NO** se perdió ni se degradó (anti-padding, `L10`, doble filo)

Bajo `L10` hay que decir también lo que este destilado hizo bien, o el balance miente por el otro lado:

- **La tesis de las DOS cascadas sobrevive verbatim y con su matiz** (`§0`:16-21): árbol de `AbortController`
  in-turn vs kill de tasks para background, *«no una»*. Es la frase portante del par y no se aguó.
- **`§2.2 Ninguna battery` es correcta y está corroborada por la columna de cruce**: `BATTERIES §3` escribe
  *«08·signals | NINGUNA — la cancelación es primitiva del base. Anti-padding (L10)»* y `§5` la clasifica
  `base-mecanismo`. El destilado **no fabricó** una battery para llenar la casilla.
- **La nota anti-padding del `parent_stop`** (`§2.4`:271-276) es exacta: delegación de arming por diseño, no
  huérfano, no deuda A↔B. Y está **verificada en fuente**, no argumentada.
- **La re-clasificación de tier `DEUDA-B → CORE-GAP`** (`§3.3`:445-449) es el trabajo propio de la capa y está
  declarada como divergencia con el tracker en vez de silenciada.
- **`LAT-SIG1` es un hallazgo NUEVO** que sólo la lectura `1→EOF` destapó, y el destilado lo dice así.
- **La confesión de `§3.3`** (la 1ª pasada leyó `agent_loop.py`/`caller.py` por tramos, y se cerró el hueco) es
  el modelo de honestidad que `L01` pide. Su ironía es que el hueco **se cerró** y el defecto de `S2` sobrevivió
  igual: **leer `caller.py` 1→EOF era necesario y no suficiente** — hacía falta cruzar a `agentic_models`.
  Es `02·§Evidencia·3` («la superficialidad MIGRA») aplicada a través de un **límite de paquete**.

### 14.7 Consecuencias nuevas para el resto de `P4″`

32. **Regla de frontera de seam** (de `14.2`/`T1`): en toda fila marcada `T1-MOTOR` o `T1-CONTRATO` cuyo
    consumidor viva **en otro paquete** (`agentic_models`, `agentic_code`, `agentic_assistant`), el `✅` exige
    abrir **el consumidor**, no el punto de entrega. Aplica de inmediato a **16·models** (par pendiente) y a
    toda fila que delegue en `StreamOptions`.
33. **Un `🔀` no puede delegar en una categoría que ya dictaminó en contra.** Antes de aceptar un
    *«verificar en NN»*, comprobar si `NN` ya resolvió. Barrido pendiente sobre los 9 pares reconciliados.
34. **Barrido de rancidez `R-1`/`RV-6` en los destilados** (`P4-08-2`): `R-1` corrigió `DEUDA-B` a nivel de
    símbolo el 2026-07-28, pero **los `NN-*.md` que ordenan borrar no se tocaron**. Éste es el primero que se
    audita y estaba mal. Los pares con entradas `DB-*` de borrado (03·04·05·07·09·10…) hay que barrerlos.
    **Abre `AC-29`.**
35. **Comprobar `DB-h*` (precondiciones de `DEUDA-B §5`) en cada par**, no sólo las entradas `§3.A`: una
    precondición no escrita en el destilado es un borrado sin orden (`P4-08-3`).
36. **Disciplina de prefijos, no renumeración** (`c25`): fijarla de una vez para `S*` como `BATTERIES·B06` la
    fijó para `K*`. **Abre `AC-30`.**
37. **Un pendiente de VERIFICACIÓN se paga en la MISMA ventana en que se abre, o el par no cierra** (`D-07·1`).
    El pendiente 2 de `08·§3.4` («no he verificado el alcance del daño sobre `01`/`02`») se pagó el mismo día
    (`§14.8`) y **rindió un `✅` falso**. Declararlo y arrastrarlo habría sido el tell `declaración-como-pago`
    exacto: la declaración era honesta y no cambiaba nada de lo que yo hacía a continuación.

---

## 14.8 Pago del pendiente 2 del par 08 — el alcance del daño de `CG-SIG-10` sobre `01`/`02`

**Por qué está aquí y no en un ciclo posterior.** `08·§3.4` lo dejó escrito como pendiente de VERIFICACIÓN con
la fórmula correcta («no lo he verificado y **no lo declaro verificado**»), pero `D-07·1` dice que una deuda de
**lectura** se paga o el ciclo no cierra, y `D-07·2` prohíbe emitir enunciado de retoma con ≥1 pendiente de
verificación abierto. Éste **era una lectura**, no una decisión ajena. Se pagó abriendo
**`SEPARACION/01-contracts.md` 1→164** y **`SEPARACION/02-loop.md` 1→318** íntegros, con la pregunta que los
abrió (`CAT-h9`): *¿qué celda de estos dos docs afirma un comportamiento que sólo es cierto si el abort corta la
petición al modelo?*

### 14.8.1 Saldo de la verificación — 4 celdas, 1 estado falso

| doc | celda | estado previo | estado ahora | naturaleza |
|---|---|---|---|---|
| `02·loop` | **`G5`** `interrupt()` ⇒ `abortController.abort()` | **✅** | **🟡** | **estado FALSO** — corregido |
| `02·loop` | `F6` abort durante tools | 🟡 | 🟡 | causa mal atribuida — corregida |
| `01·contracts` | `CTR-15` `timeout_seconds` | 🟡 rama abierta | 🟡 **rama cerrada** | disyuntiva pendiente — **resuelta** |
| `01·contracts` | `CTR-12` firma de CR2 | 🟡 | 🟡 | firma rancia — corregida |

**El `✅` falso (`02·G5`).** La ficha decía *«`interrupt()` ⇒ `abortController.abort()` … vía cooperativa abierta
aquí (`ctx.stop`, `agent_loop.py:173/186` + `dispatcher.py:54`)»* y lo acreditaba en `§3.2·Q3` con esos tramos
abiertos. Los tramos **son ciertos**: el loop sí consulta `ctx.stop` en frontera de turno y el dispatcher sí lo
consulta por tool call. Lo que el `✅` afirmaba de más es la **equivalencia con el canónico**, y ahí el canónico
hace una cosa que B no hace: `abortController.abort()` **corta la petición HTTP en vuelo**. Con `CG-SIG-10`
probado (`caller.py:188-190` entrega un `asyncio.Event` y los 8 providers gatean con
`getattr(signal, "aborted", False)`), en B un abort **durante la generación** no hace nada hasta que el stream
termina por sí solo. El comportamiento observable diverge exactamente en el caso de uso que motiva la feature:
el usuario que interrumpe una respuesta larga. ⇒ **🟡**, no ✅.

**La rama cerrada (`01·CTR-15`).** La ficha ofrecía *«completar (`asyncio.wait_for`/deadline→kill) **o retirar el
campo si 08·signals cubre la cancelación**»*. La respuesta es **completar**: el `AbortScope` de `08·SR1` modela
cancelación **por señal** (alguien decide parar) y no **deadline por tiempo** (nadie decide; vence un plazo).
**Corroboración independiente y desde el propio `01`** —no importada de 08—: su `§1.1` ya registraba *«sin
contraparte: el canónico cancela por abort, no por timeout per-task»*, es decir `arm_watchdog` es extensión de B,
y una extensión no se justifica delegándola en una costura que no la implementa. La decisión emitida en
`08·§2.3` (vencimiento entra por la misma puerta con `reason='timeout'` como cuarta razón del enum) queda
**aplicada en `01`**, por `CAT-h10`.

### 14.8.2 Los dos hallazgos que la verificación produjo y nadie había previsto

**(a) `02·G5` es el SEGUNDO fallo de `Q3` en ese mismo documento — y por la punta contraria a `F8`.** `02` ya
había retirado `F8` de su lista de `Q3` con la lección *«abrir el tramo acredita que el punto de registro existe,
no que alguien registre algo»* ⇒ Q3 pasó a leerse *«¿abrió el tramo **y** identificó al productor?»*. `G5` falla
la **otra** punta: identifica al productor perfectamente (`agent_loop.py:173/186` **sí** pone la señal) y no abre
al **consumidor**, que vive en otro paquete y la lee con un atributo que el objeto no tiene. Es el caso testigo
de la **consecuencia 32** (regla de frontera de seam) y obliga a la tercera redacción de Q3:
> *¿abrió el tramo, identificó al productor **y**, cuando la costura cruza paquete, abrió al consumidor?*

**(b) `02·I6` es de ESPECIE DISTINTA a `I1..I5` — y abre un vector de rancidez que nadie vigilaba (`AC-31`).**
La tabla `§2.6` de `02` se titula *«veredictos invertidos aguas abajo»* y sus cinco entradas comparten causa: las
invirtió un **rollup** transversal escrito después. `I6` lo invierte **otro par** —`08`— al abrir código que caía
en su lado de la frontera. Consecuencia operativa: el barrido de rancidez que `AC-29` ordena contra los rollups
**no cubre este vector**. Cada par reconciliado puede haber cerrado celdas de sus pares vecinos, y en 9 pares ya
reconciliados nadie ha mirado hacia atrás. **Abre `AC-31`.**

### 14.8.3 Anti-padding (`L10`) — lo que la verificación NO encontró

Para que el saldo no se lea como «01 y 02 estaban podridos»: se revisaron **las 75 fichas** de ambos docs
(15 de `01`, 60 de `02`) contra la pregunta de arriba y **71 no dependen del corte del modelo**. En particular
**no** están dañadas: `02·A4` (los reason codes `aborted_*` describen el enum, no el mecanismo) · `02·C11`
(el invariante «todo `tool_use` recibe `tool_result` aun en abort» se sostiene por el `break`-antes-de-persistir,
que no depende de dónde se detecte el abort) · `02·G1`/`F8`/`B*` (motores ausentes, indiferentes a la señal) ·
`01·CTR-01..14` salvo las dos citadas. Y el `✅` de `02·G5` **no era invención**: los tramos que citaba existen y
funcionan; el defecto es de **alcance de la afirmación**, no de fabricación de evidencia — la especie contraria a
`09·E5`.

---

## 14.9 Segunda vuelta sobre el par 08 — el canónico resuelve las dos controversias, y en una me contradice

**Disparador (usuario):** *«las controversias las puedes facilmente resolver mirando el codigo de canonico, si es
que hay una desviación, no es que te parezca mas logico a ti, sino que es lo que realmente el canonico hace.»*
Regla nueva **`D-08`** en `DECISIONES.md`. Lo que sigue es lo que la lectura produjo. **Coste: 6 archivos del
canónico.** Lo que ese coste compró: un pendiente cerrado, un hallazgo nuevo, una decisión mía refutada y una
media verdad retirada de la columna de corroboraciones.

### 14.9.1 Lo que dice el canónico (censo de primera mano, `claude-code/src`)

| hecho | evidencia |
|---|---|
| El tipo es **`AbortSignal` nominal**, no un pato | anotado en firma en `claude.ts:721,764,829,1022,3251,3310` · `awaySummary.ts:31` · `elicitationHandler.ts:34,217,267` · `toolUseSummaryGenerator.ts:34` · `mcp/client.ts:2830,2839,2847,3041` |
| Se lee sincrónicamente por **`.aborted`** | **119** ocurrencias |
| Se escucha por **`addEventListener('abort')`** | **26** ocurrencias |
| Lleva **`.reason`**, **valor abierto**, propagado padre→hijo | `.abort('interrupt')` (`handlePromptSubmit.ts:331`, `print.ts:1861`) · `.abort('sibling_error')` (`StreamingToolExecutor.ts:362`) · `.abort(new DOMException('The operation timed out.','TimeoutError'))` (`mcp/client.ts:519`) · propagación `abortController.ts:35,76` · lectura de vuelta `StreamingToolExecutor.ts:308` |
| **El corte lo ejecuta el CLIENTE HTTP**, no un sondeo | `anthropic.beta.messages.create({...params, stream:true}, { signal })` `claude.ts:1826/1843`; ídem `:733,776,870,902,2558,2657`; `fetch(url,{...init,signal})` `mcp/auth.ts:206,229` |
| El sondeo de `.aborted` sirve para **desambiguar**, no para cortar | `claude.ts:2434-2458`: si llega `APIUserAbortError` **y** `signal.aborted` ⇒ abort de usuario; si **no** estaba abortada ⇒ era el timeout interno del SDK ⇒ se re-lanza como `APIConnectionTimeoutError` |
| El **deadline se compone DENTRO de la señal** | `createCombinedAbortSignal(signal, {signalB?, timeoutMs?})`, `utils/combinedAbortSignal.ts` 1→47: `setTimeout(abortCombined, timeoutMs)` sobre el **mismo** controller + `cleanup()` que libera timer y listeners. Consumidores: `hooks.ts:2149,2196,3089,3281,4758` · `execPromptHook.ts:59` · `execAgentHook.ts:80` · `execHttpHook.ts:151` · `print.ts:4189` |
| El árbol padre→hijo es **WeakRef + `{once:true}`** con limpieza | `abortController.ts:68-99` |

### 14.9.2 Controversia 1 — `CG-SIG-10`: no había dos ramas

Yo la había dejado como *«binaria con dos ramas defendibles ⇒ `D-06·3`, la decide 16»*: (a) `Protocol` con
`.aborted`+`reason`, (b) providers gateando en `is_set()`. **La rama (b) no es defendible**: `asyncio.Event` no
tiene `reason`, no admite listener de abort ni propagación padre→hijo ⇒ **no puede sostener `CG-SIG-1` (reason),
`CG-SIG-7` (árbol) ni `CG-SIG-8` (`on_abort`)**, que son tres findings de este mismo documento. Ejecutada (a) por
`D-06·1`.

**Y el reparto de culpa estaba invertido.** Mi nota decía que (b) *«obliga a tocar 8 ficheros»*, insinuando que
el problema estaba del lado de los providers. Es al revés: el `getattr(signal, "aborted", False)` de los 8
providers **mimetiza correctamente el canónico**; el defecto está **entero en el productor** (`caller.py` entrega
un `asyncio.Event`). Se arregla **un** punto, no ocho.

### 14.9.3 Hallazgo nuevo que la misma lectura destapa — `CG-SIG-11`

Aun con el tipo correcto, **`.aborted` sondeado sólo corta entre chunks**: si el servidor deja de emitir, el
`await` sigue colgado. El canónico no sondea para cortar — **entrega la señal al cliente HTTP** y el SDK cierra la
conexión. ⇒ `CG-SIG-10` (tipo) y `CG-SIG-11` (entrega al cliente) son **dos trabajos**, y el segundo sobrevive a
arreglar el primero. Test que los distingue: con el tipo arreglado y sin entrega, `test_abort_cuts_model_stream`
(faux, chunks continuos) **pasa** y `test_abort_closes_http_stream` (servidor mudo) **no**. Consecuencia sobre
`§14.8`: `02·G5` no vuelve a `✅` con `CG-SIG-10`; necesita **también** `CG-SIG-11`.

### 14.9.4 Controversia 2 — el canónico REFUTA mi decisión del watchdog

Emití en `08·§2.3` (y la propagué a `01·CTR-15`): *«el `AbortScope` cubre cancelación por señal, no deadline por
tiempo; un watchdog que dispara `abort.interrupt(reason='timeout')` es un productor del scope ⇒ `arm_watchdog` se
completa, con `reason='timeout'` como cuarta razón del enum»*. Saldo tras leer:

| parte | veredicto | por qué |
|---|---|---|
| el vencimiento entra **por la misma puerta** que el abort ⇒ `arm_watchdog` **se completa**, no se retira | ✅ **sobrevive** | no hay mecanismo de deadline paralelo en el canónico |
| *«un watchdog externo llama a `interrupt()` sobre el scope»* | ❌ **cae** | el canónico **compone la fuente dentro de la señal** y devuelve `cleanup()`; firma correcta `combine(scope, timeout_s=...) -> (scope_hijo, cleanup)`, con `cleanup` **obligatorio** (el propio canónico documenta la fuga: ~2,4 KB/llamada bajo Bun) |
| *«cuarta razón del **enum**»* | ❌ **cae** | no hay enum: `.abort(reason)` es **valor abierto**. Cerrarlo a un enum es **divergencia declarable** (`L10`), no homologación ⇒ **corrige `CG-SIG-1`**, escrito asumiendo enum cerrado |
| corroboración citada (`01·§1.1`: *«el canónico cancela por abort, no por timeout per-task»*) | ⚠ **media verdad usada como entera** | cierto que no hay campo per-task; **falso** que no convierta tiempo en abort — lo hace **por operación**. Corregida en `01·§1.1` por `CAT-h10` |

**Lo que esto dice del método, sin adornos:** la decisión llevaba una tabla, un razonamiento y una cita de apoyo,
y **dos de sus tres afirmaciones eran falsas**. La cita de apoyo no era un control independiente: era una frase
del corpus que decía a medias lo que yo quería oír. Un razonamiento bien presentado tiene exactamente el mismo
aspecto tenga o no respaldo en el canónico — por eso la regla no puede ser *«razonar con cuidado»*, tiene que ser
**ir a leer** (`D-08`).

### 14.9.5 Consecuencia sobre el ledger

**`AC-32` (nuevo):** barrer bajo `D-08` todo `🔀` cerrado como *«divergencia por diseño»* y todo pendiente elevado
por `D-06·3` en los 9 pares reconciliados, preguntando *¿se leyó el canónico antes de cerrarlo así?* Precedente de
que la tasa no será cero: `07·B2` ya fue invertido por esta vía y `08·S12` delegaba en una categoría que ya había
dictaminado en contra. **Consecuencia 38:** `D-06·3` queda **subordinada a `D-08`** — no se invoca sin decir qué
se leyó del canónico y por qué no basta.

---

## §15. Par **10 · tools-native** — tracker 794 L · SEPARACION 488 L · 64 fichas (**`AC-12`** · 10/18)

**El par más grande de los 18.** 1282 L de las dos caras; el tracker (794) es el archivo más grande de todo
`HOMOLOGATION` salvo `PROGRESS`. Eje rector elegido en el PASO 0: lecciones **08** (la omisión se esconde en el
archivo más grande) + **07** (prohibido trocear un in-scope en «núcleo + resto») — porque **este par es el
precedente material de `L07` dentro del propio corpus**: su tracker lleva DOS veces (`:38-43` y `:333-338`) la
«Nota de corrección» que confiesa haber troceado `BashTool.tsx`/`FileReadTool.ts`/`utils/tasks.ts` en «núcleo», y
de releerlos íntegros salieron `A3b`/`A3c`/`A3d`/`B9`-`B12`. El tracker lo dice sin adornos: *«La superficialidad
es el modo de fallo #1 del esfuerzo»*.

### 15.1 El hallazgo del par — `A2` y `D3` son **una sola costura canónica partida en dos celdas**, y las dos se suavizaron

Es el hallazgo que reorienta el par, y sólo aparece con las **dos rejillas simultáneamente en contexto** más una
lectura del canónico bajo `D-08`.

**Lo que hizo el destilado, celda a celda:**

- **`A2`** (`isReadOnly`/`isConcurrencySafe`). Tracker: **❌** (*«sin `is_read_only`/`is_concurrency_safe` en el
  protocolo; el dispatcher es secuencial → el flag no tendría consumidor»*). Destilado `:53`: conserva el rótulo
  ❌ en el ID pero la columna `acción` dice ***«🔀 sin consumidor hoy ⇒ **no gap activo** (L10)»***, y `Q5`
  `:429-431` lo consolida (*«no se cuenta como deuda viva»*), y el ledger `:329` lo escribe ya como *«🔀 L10 sin
  consumidor»*. **Degradación ❌→🔀 en tres sitios.**
- **`D3`** (`context_modifier`/`ends_turn`). Tracker `§J:221-222`, **re-clasificación explícita**: 09·A24 ❌ →
  **🟡**, con **DOS** razones nombradas — (a) *«sin gating por `is_concurrency_safe==False` que el canónico
  exige»* y (b) *«sin declararlo en el protocolo»*. Destilado `:103`: **✅**, con la fórmula *«CORR a 09·A24/D7
  (❌→✅ aplicado)»*. Conserva (b) como `DEUDA-B`. **Pierde (a) entera.** **Inversión 🟡→✅.**

**Lo que dice el canónico** (`D-08`; leído **1→EOF**, `claude-code/src/services/tools/toolOrchestration.ts`,
189 L, más el censo de los 52 usos de `isConcurrencySafe` y `StreamingToolExecutor.ts:391`):

1. `partitionToolCalls` (`:91-116`) **particiona la tanda de tool_use por `isConcurrencySafe`**, agrupando
   llamadas consecutivas seguras en un lote; `runTools` (`:19-82`) ejecuta cada lote **concurrentemente**
   (`runToolsConcurrently`, fan-out hasta `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY`, **default 10**, `:8-12`) **o
   serialmente**. `isConcurrencySafe` **no es un flag decorativo: es el discriminador de la topología de
   ejecución del canónico.** Sin él no hay ejecución paralela de tools, que es comportamiento observable.
2. Y —esto es lo que nadie había leído— **el lote concurrente NO aplica los `contextModifier` al vuelo**: los
   **encola** por `toolUseID` (`:42-48`) y los aplica **sólo cuando el lote entero ha terminado** (`:54-62`),
   mientras la rama serial los aplica inmediatamente (`:140-142`). `StreamingToolExecutor.ts:391`
   (`if (!tool.isConcurrencySafe && contextModifiers.length > 0)`) refuerza el mismo acoplamiento.

⇒ **En el canónico `context_modifier` y `isConcurrencySafe` son un solo mecanismo.** El `✅` del runtime en `D3`
es correcto **únicamente porque** su dispatcher es secuencial: es un **✅ condicionado a la ausencia de `A2`**, y
esa condición **no está escrita en `D3`**. El destilado sí la escribió en `A2` (*«reabrir si el dispatcher gana
concurrencia»*) — pero la puso en la celda equivocada: en `A2` es una nota de archivo, en `D3` es la
**precondición de un ✅**. En cuanto `R10`/09 den concurrencia al dispatcher (que es plan declarado, no
hipótesis), `D3` pasa a **incorrecto en silencio** y el runtime aplicará modifiers a mitad de un lote paralelo.

**Y el «sin consumidor» de `A2` era falso ya hoy**, sin esperar al canónico: `DEUDA-A §1.2(a):322` escribe
*«concurrencia (que consume `is_concurrency_safe` de `CG-MCP-3`)»* — **hay consumidor en el plan**. Se cumplen a
la vez la **regla (32)** (el consumidor vive en otro paquete/par ⇒ el estado exige abrirlo) y la **regla (33)**
(el `🔀` delega en `→09`, y 09 **todavía no aloja** `ToolStatus`/`isConcurrencySafe` — el par 08 lo dejó
explícitamente como *«ejecución con dueño ajeno: homar en `09·FIND-TOOL1`»*). **`L10` se invocó al revés:** no es
una divergencia deliberada sin contraparte, es una **capacidad canónica ausente** con consumidor nombrado.

**Saldo:** `A2` = **COMPRIMIDA-CON-PÉRDIDA con inversión ❌→🔀** · `D3` = **COMPRIMIDA-CON-PÉRDIDA con inversión
🟡→✅**. Abre **`CG-TOOL-CONC`** (ver `15.6`).

### 15.2 Los dos recuentos internos que la cara B se contradice a sí misma — y la doble refutación externa

| declaración | dónde | realidad contada ítem a ítem | refutación externa |
|---|---|---|---|
| *«**11 costuras** nombradas»* | `§3.3:480` | **§2.1 tiene DOCE bullets** (`:162-192`): `read_file_state` · `fs_safety` · `exec_env`-vivo · `git_credentials` · `ctx.fs` · allowlist-bg · PreToolUse · `context_modifier`/`ends_turn` · choke-point `PathPresentation` · `new_messages` · `ctx.lsp` · `StorageContract` | — |
| *«**8 obligaciones** de integrador»* | `Q4:420-421` y `§3.3:482-483` | **§2.5 tiene NUEVE fichas** (`:261-313`): OI-fs-safety · OI-perm · OI-git-cred · OI-web-policy · OI-naming · OI-B · OI-lsp · OI-cron · **OI-A** | **DOBLE e independiente**: `00-INTEGRADORES §1.7:185` lista **los nueve nombres**; `BATTERIES §4.1:219-220` escribe literalmente *«las **9** de tools nativas (10)»* |

El segundo caso tiene una firma reveladora: `Q4:420-421` **enumera los nueve** pero escribe *«8 obligaciones
(OI-fs-safety / … / OI-cron **+ OI-A render**)»* — el noveno va pegado con un `+`, fuera del recuento, como si
«render» no fuese una obligación. Es exactamente el defecto que `BATTERIES §6·CAT-h11` y `§8.2·Q2` prohíben:
**contar por contenedor y no por ítem**. Y el emisor es el destilado: los dos receptores independientes cuentan
bien. **Sonda `c28`: el destilado no adjudica ninguna de las dos discrepancias — ni siquiera las ve.**

### 15.3 `OI-remote` — la obligación colocada «a secas» que `Q4` jura que no existe

`K6` (`§1·K:149`) y el ledger (`:385`) dan como destino **`OI-remote` (si genérico)**. **No hay ficha `OI-remote`
en `§2.5`**, y **`00-INTEGRADORES §1.7` no lo lista**. `Q4:422-423` afirma: *«ningún finding cerrado con "→
integrador" a secas»*. Es falso. ⇒ **`Q4` es incorrecta en DOS de sus tres afirmaciones** (el conteo y el
«ninguno a secas»); sólo sobrevive la tercera (las ⛔ llevan satélite nombrado).

### 15.4 Nombres de destino que el receptor no reconoce

- **`battery_fs` no existe.** El catálogo (`BATTERIES §2.5·B22`) la llama **`battery_fs_tools`**. El destilado usa
  el nombre correcto en **3** sitios (`:52`, `:195`, `:328`) y **`battery_fs` en 24** (`:54-68`, `:146`,
  `:330-344`, `:382`). No es cosmética: la columna `destino` es el identificador por el que el receptor resuelve
  la delegación, y **24 de 27 no resuelven**.
- **`battery_todos` es un nombre INVENTADO.** `C2:92` y el ledger `:358` dan destino *«`battery_meta`/`battery_todos`»*.
  En el catálogo **no existe**: `TodoWrite` vive **dentro** de `B25 battery_meta`, junto a Config/Sleep/AskUserQuestion.
- **`battery_plan` sí existe** (`BATTERIES §2.5` no lo lista porque es `B16`, compartida 14+10). **No es defecto** —
  se comprobó antes de acusar.

### 15.5 Lo que la columna de cruce refuta y el destilado no absorbió (`c23`)

1. **`DB-h1`/`RV-8` + `DB-27` — el candidato más fuerte de la regla (32) de todo el par.** `DEUDA-B §5`:
   `create_runtime` **nunca llama `set_registry()`** ⇒ **las 6 tools `Task*` levantan `RuntimeError`→`ToolResult.error`
   SILENCIOSAMENTE EN CADA LLAMADA**; y `DB-27`: el factory **nunca llama `set_runner()`** ⇒ **todo spawn de
   subagente falla**. Las fichas `F1`/`F3`/`F4` y `G2`/`G5` del destilado llevan **✅/homólogo** sin una sola nota.
   Un `✅` de superficie cuyo consumidor no está cableado **no es un ✅ de comportamiento**.
2. **`BATTERIES §6·CAT-h5:339-341`** dice que `battery_agent`/`battery_task` tienen *«alcance hoy inoperante»* y
   que **su composición no es verificable hasta `K7`**, apoyándose en `DB-h1`. Ausente de las filas F/G.
3. **`DB-06`** («el radio de explosión más grande de las 12 entradas BORRAR») aterriza casi entero en 10 —
   **18 de sus ~25 productores son tools nativas de este par**, más `scripts/e2e_runtime_test.py` y 24 archivos de
   test— y el destilado lo lleva como **3 líneas en `§2.4` delegadas a 09**; encima, en la entrada duplicada.
4. **`DEUDA-A §1.1·K1:187` cita `10·B2`** como el gap de **modo de permiso**. `10·B2` en **las dos caras** es el
   **shell persistente** (`FIND-NATIVE-BASH`/`R8`). El propio destilado escribe *«B2/GAP-CTX2 (mode contract,
   →01·CTR-08)»* en `D1:101`: **usa «B2» para dos cosas distintas**, y la colisión ya se propagó a un **keystone**
   de `DEUDA-A`.
5. **`DEUDA-A §1.1·K5:255-265`** lista los consumidores de `new_messages` (`11·CG-MCP-4/5`, `12·CG-SKILL-5`,
   `09·new_messages`) y **omite `10·A3`** (image/pdf) **y `10·K1`** (Brief), que el destilado declara bloqueados
   exactamente por ese canal. **Dos consumidores que el keystone no ve.**

### 15.6 Sondas — resultado una a una

| sonda | objeto | resultado |
|---|---|---|
| **c23** | inversión aguas arriba en el REPARTO de los rollups | **DEFECTO, el más grave de los 10 pares** — cinco refutaciones no absorbidas (`15.5`): `DB-h1`/`DB-27` contra `F*`/`G*`, `CAT-h5`, el radio de `DB-06`, y **dos keystones de `DEUDA-A` contaminados por 10** (`K1` cita mal `10·B2`; `K5` omite `10·A3`/`10·K1`) |
| **c24/c29** | `§2.1` (12 costuras) vs el índice de **29** seams de `SEAMS` | **DEFECTO** — `SEAMS:4` declara como fuentes las `§2.1` de **{01,16,07,02,05,09}**: **10 no es fuente**. **CINCO de las doce no tienen número `S`**, y entre ellas **el KEYSTONE del par** (`ctx.read_file_state`), más `FsSafetyPolicy`, `ctx.git_credentials`, la allowlist de bg-gating y `ctx.lsp`. En sentido inverso, `SEAMS §S23` nombra *«10 (bash-bg)»* consumidor del reaping y `§S25` delega *«isolation→10/18»*: **dos fichas que 10 no tiene** |
| **c25/c31** | colisión de namespace | **DEFECTO** — `10·K1..K12` es el **namespace `K*` más grande del corpus** y colisiona de frente con las keystones `DEUDA-A·K1..K8`. Materialmente ya mordió: `15.5·4` y `15.5·5` son **`DEUDA-A·K1` y `DEUDA-A·K5` hablando de `10·K*`/`10·B2`**. Remedio = **prefijo** (`10·Kn` vs `DA·Kn`), **nunca renumerar** (precedente `BATTERIES·B06` / consecuencia 31 / `AC-30`) |
| **c26** | re-conteo del grid fila a fila | **NO ADJUDICABLE, y ése es el resultado** — el `§Recuento` del tracker (`:305-316`) emite **las cinco cifras con tilde de aproximación** (`~10 ✅ · ~12 🟡 · ~14 🔀 · ~20 ❌ · ~8 ⛔`): **no hay recuento verificable que reproducir**. El re-conteo fila a fila que sí hice (A=17 · B=12 · C=5 · D=3 · E=4 · F=4 · G=5 · H=2 = 52; +K=12 = **64**) **cuadra exacto** con la enumeración `Q2` del destilado. **Mérito del destilado**: sustituyó un recuento aproximado e inauditable por 64 celdas nominadas y auditables |
| **c27/c32** | `§Plan` `R0-R11` ítem a ítem | **DEFECTO DE FORMA, declarado por el propio destilado** — `Q2:15-16` dice que el §Plan es *«la capa de remediación… referenciada en `acción`, **no re-contada**»*. Correcto para el **conteo**; el problema es que tampoco se **re-desarrolla**: el tracker despliega `R0-R11` en **~200 L** (`:523-725`) con los 6 campos `L05` (firma exacta, cableado, orden, test nombrado — p.ej. `check_read_before_edit(ctx,path) -> str \| None`, `FsSafetyPolicy.check_write(path,content) -> str \| None`, el centinela `command; printf "\n<sentinel>$?\n"` de `R8`), y en el destilado `R6` es **una etiqueta en una celda**. Su propia frase de rigor (`:320-322`) dice *«de lo que aquí se destile nace el código»*: con `R0-R11` sólo referenciado, **el código nace sin firma ni test** salvo que quien implemente abra el tracker — y nada en el doc se lo dice |
| **c28** | discrepancia de conteo entre caras | **DEFECTO** — hay **tres** conteos discrepantes (12 vs 11 costuras · 9 vs 8 obligaciones · `Q1` dice *«1→793»* cuando el tracker tiene **794**) y el destilado **no adjudica ninguno**: los dos primeros son contradicciones **internas** entre sus propias secciones (`15.2`) |
| **c30** | `00-INTEGRADORES` vs estado de seams | **DEFECTO** — `§1.7:185` lista **nueve** OI-* de 10 (refutando el «8»), y **`OI-remote` no está** ni allí ni en `§2.5` pese a ser destino declarado de `K6` (`15.3`). Además **ningún OI-* de 10 está en la espina `OI-1..23`/`OI-M1..8`/`OI-EVT-1..4`** |

### 15.7 Lo que **NO** se perdió (anti-padding, `L10`, doble filo)

Sin esto el balance miente por el otro lado:

- **La «cara oscura» de la tesis 2 sobrevive y es lo mejor del destilado** (`:30-34`): *«los invariantes que el
  canónico impone DENTRO del tool… el runtime no los tiene ni en el tool ni en un seam → aterrizan aquí como
  **CORE-GAP reales**, no como delegación»*. Es precisamente la frase que impide vestir de «política del
  integrador» un `❌`. El destilado la conserva **y la usa**: `A5`/`A7`/`A8`/`A9` quedan CORE-GAP, no OI.
- **`§"Implementación de las tools no portadas"` (tracker `:729-793`, 6 diseños) se transportó bien** — y era
  la unidad que yo había predicho como la más fácil de perder. Llegan `BriefEvent{markdown,attachments,status}`
  al `event_queue` (`K1`), `native['final_output']` vía `context_modifier` (`K2`), el prereq `R2`/`R3` +
  `safe_for_background=True` de NotebookEdit (`K3`), el seam `ctx.lsp: LspProvider | None` con auto-deshabilitado
  (`K4`) y el reparto tools+store / disparo-del-integrador de Cron (`K5`). **CONSERVADA.**
- **Los tres BUGs reales se mantienen como BUGs, no se estetizaron**: `read_file /dev/zero` **cuelga el proceso**
  (`A3c`), `grep` sin match (rc=1) **se reporta como error** (`B12`), y el runtime **pisa cambios silenciosamente**
  entre lectura y edición (`A8`). Los tres con esa palabra.
- **El anti-padding es correcto y valiente**: `clone_repository` (`B8`) e `inherit_messages` (`F2`) se declaran
  **extensiones de B sin contraparte ⇒ NO deuda** (`L10`), en un par donde inflar habría sido gratis.
- **`E2`/`GAP-TOOL2`=`GAP-MODE2`**: el destilado mantiene el hallazgo incómodo de que el runtime es **más
  restrictivo de lo debido** — un gap que no duele y que era fácil callar.
- **`§3.2-bis` es honestidad de la buena**: confiesa que en la 1ª entrega del ciclo 17 archivos se marcaron
  *«heredados»* (*«atajo de falsa economía que el usuario cazó»*) y los releyó 1→EOF. Su **único** defecto es de
  rótulo: se titula *«re-lectura íntegra de B (1→EOF ESTE ciclo)»* mientras la fila `agent_loop.py` declara
  **«tramo 280-352»** — «abierto ≠ íntegro» (`L08`) **a nivel de título de sección**, aunque la fila y `:470` lo
  confiesan. Es el tercer episodio del mismo defecto en este par (tracker `:497`, tracker `:38-43`, aquí).
- **`LAT-TOOL1` se resuelve bien**: el destilado responde *«el canónico tampoco usa este enum como driver»* ⇒ NO
  deuda A↔B. Correcto. Su defecto es de forma: **está dos veces literalmente** en `§2.4` (`:244-246` y
  `:250-252`), lo que infla la sección de 4 entradas reales a 5.

### 15.8 Consecuencias nuevas para el resto de `P4″`

39. **Una celda cuyo `✅` depende de que OTRA celda siga siendo `❌` debe escribir esa dependencia en el `✅`, no
    en el `❌`** (de `15.1`). El destilado puso la condición en `A2` («reabrir si el dispatcher gana concurrencia»)
    y dejó `D3` en `✅` limpio. La condición pertenece **al que se beneficia de ella**. Barrido pendiente:
    todo `✅` de un mecanismo cuyo homólogo canónico esté **acoplado a una capacidad ausente**. **Abre `AC-33`.**
40. **Dos celdas que en el canónico son UN mecanismo no pueden repartirse en dos categorías sin una nota de
    acoplamiento.** `A2`→09 y `D3`→loop rompieron en dos lo que `toolOrchestration.ts` implementa junto, y por eso
    ninguno de los dos destinos ve el problema completo. **Regla: al homear una celda «→NN», comprobar si el
    canónico la implementa en el mismo punto que otra celda ya homeada a un NN distinto.** **Abre `AC-34`.**
41. **El nombre de destino se valida contra el catálogo receptor, siempre** (de `15.4`): `battery_fs` (24 usos) y
    `battery_todos` no existen en `BATTERIES`. Barrido sobre los 10 pares reconciliados de toda columna `destino`
    que nombre `battery_*`/`OI-*`/`S*`/`CG-*`. **Abre `AC-35`.**
42. **Un recuento declarado en el VEREDICTO se re-cuenta ítem a ítem, no se lee.** Los tres de este par (11/12,
    8/9, 793/794) sobrevivieron a un gate-11 y a un gate auto-adversarial. El tell es el `+` de `Q4:421`
    (*«…+ OI-A render»*): **cuando un enumerado lleva un ítem colgado tras un `+`, ahí está el descuadre.**
43. **El `§Plan` del tracker es contenido, no anexo** (de `c27/c32`): un destilado que lo referencia por etiqueta
    incumple su propia frase de rigor. Mínimo exigible = el destilado **declara explícitamente** que el detalle
    `L05` no vive en él y **dónde vive con rango de líneas**. **Abre `AC-36`.**

---

## §16 · Par **11 · mcp** — tracker `11-cap-mcp.md` **798 L** · destilado `SEPARACION/11-cap-mcp.md` **394 L** · 27 fichas vinculantes
### (`AC-12` · **11º de 18** · consecuencias **45-49**)

**Grado probatorio de esta sección.** Cara A (798 L) y cara B (394 L) leídas 1→EOF; `SEAMS.md` (539 L) y `00-INTEGRADORES.md` (242 L) leídos 1→EOF **en esta ventana** (T1, `EVIDENCIA.log:247`). `DEUDA-A` (699 L), `DEUDA-B` (1130 L), `BATTERIES.md` (572 L) y `A-CIERRE-LEDGER.md` (1046 L): **T2-LOG** (`EVIDENCIA.log:244`, ventana anterior) — se dice, no se disimula. `claude-code/src/services/mcp/config.ts` (1578 L) y `officialRegistry.ts` (72 L): **T2-HEREDADO al escribir esta seccion, ELEVADOS A T1 el 2026-07-30** — se re-abrieron los dos 1→EOF en la ventana de cierre (`EVIDENCIA.log:251`) y **la lectura no refutó ninguna de las dos conclusiones**: `addMcpConfig:625-761` es la puerta de admisión (regex de nombre `:630`, reservados `:637`/`:645`, enterprise excluyente `:651`, schema `:658`, denylist `:668`, allowlist `:675`, colisión por scope `:682-710`) y la firma de dedup (`getMcpServerSignature:202`) vive en otra ruta, nunca en `add`; `officialRegistry` es telemetría pura. **Aplazar a P6″ era innecesario y estaba mal dicho: `D-08` manda LEER el canónico, no elevarlo.**

**Defecto de este mismo documento, declarado antes que los ajenos.** Al abrir `A-CIERRE-P4.md` 1→EOF se encontró que `§0:15` ya decía *«11 pares de 18 reconciliados»*, que `§0:35` ya daba la fila del par 11 como *«✅ reconciliado + remediado (27/27) — §16»* con `394→(remediado)`, y que la nota `§0:17-21` **citaba `§16.3`** — cuando `§16` no existía (última sección `§15` en `:1868`, `grep -c 'P4-11'` = **0**) y `11-cap-mcp.md` seguía intacto en 394 L. La cabecera se escribió por delante del cuerpo: es **exactamente** la especie que esta pasada audita (`declaración-como-pago`), cometida en el producto propio. Queda saneada en `§16.8`; se registra aquí porque el orden obligado es *lo no verificado primero*.

### §16.0 · Patrón 3 — columnas ausentes por esquema

| columna | cara A (tracker) | cara B (destilado) | veredicto |
|---|---|---|---|
| anclas canónicas `archivo.ts:línea` | **38** (contadas con la línea, consecuencia 19) | **0** | **PERDIDA total** |
| tests nombrados / criterio de aceptación | **42** nombres | **0** | **PERDIDA total** |
| LOC de contrapartes leídas (`:14-47`) | 6 archivos con tamaño | ausente | **PERDIDA** |

Retención canónica **38 → 0**: **la peor medida de los once pares**. El destilado no conserva ni una sola coordenada del canónico, de modo que ninguna de sus 27 fichas es re-verificable sin volver al tracker. Décima confirmación consecutiva del patrón 3 — ya no es hallazgo de par, es propiedad del esquema `SEPARACION/*`, y así se anota en la consecuencia 20 (ya emitida) sin volver a numerarla.

### §16.1 · Saldo ficha a ficha — **27 = 27**

Re-contadas una a una las filas de `§1.A:67-97` contra las fichas del tracker: **27 vinculantes, correspondencia exacta**, sin ficha inventada y sin ficha caída. `§1.B` (25 `MCP-OK`) y `§1.C` (8 `MCP-NA`) cuadran con sus orígenes salvo por las dos ausencias de `§16.2·P4-11-7`. **El saldo nominal del par es correcto**; los defectos de abajo son de *contenido* y de *cruce*, no de conteo de fichas.

### §16.2 · Pérdidas

| id | qué se pierde | origen (cara A) | especie |
|---|---|---|---|
| **P4-11-1** | el **§Plan `McR1-19`** completo: 226 L → `§2.3` 59 L ≈ **26 %**, sin firmas, sin orden de aplicación, sin tests | `:374-599` | COMPRIMIDA-CON-PÉRDIDA (**la mayor del par**) |
| **P4-11-2** | `search_hint` / `alwaysLoad` en la definición de herramienta MCP | `:147` (tabla E) | PERDIDA — y `SEAMS·S16:295` la lista *A CRECER (09·A12)*: el rollup la espera y 11 no la trae |
| **P4-11-3** | truncado a **2048** + sanitización unicode del resultado MCP | `:149` | PERDIDA (higiene de salida, sin dueño alternativo) |
| **P4-11-4** | `_meta` **del lado llamada** + `mcpMeta` | `:153` | PERDIDA — `SEAMS·S16` la lista *A CRECER (09·A25)*: llega la mitad de la costura |
| **P4-11-5** | las 38 anclas `.ts:N` y la cabecera de contrapartes con LOC | `:14-47`, passim | PERDIDA (patrón 3, §16.0) |
| **P4-11-6** | los 42 tests nombrados | passim | PERDIDA (patrón 3, §16.0) |
| **P4-11-7** | filas `MCP-NA` de **`officialRegistry`** y de **`extractAgentMcpServers`** | `:279`, `:35` | PERDIDA — y la segunda es la contraparte de `SEAMS·S25` (ver `§16.4·I3`) |
| **P4-11-8** | el «menor plegado» de regex-de-nombre / nombres reservados en `addMcpConfig` **mal ruteado** a `CG-MCP-13` cuando el gate canónico es `CG-MCP-11` + `CG-MCP-1` | `§2.3:231-233` | COMPRIMIDA-CON-PÉRDIDA + destino erróneo **[T1 desde 2026-07-30: `config.ts` re-abierto 1→EOF; `addMcpConfig:625-761` confirma admisión, y `getMcpServerSignature:202` confirma que la firma de dedup NO pasa por `add`]** |

### §16.3 · Defectos de la capa tracker (no imputables al destilado)

- **T1 · `McR14` no existe.** El §Plan salta `McR13`→`McR15` y aun así el propio tracker se autodescribe *«McR1-19»*; la cara B copia el rango fantasma en su cabecera `:6`. Un plan cuya numeración el autor no verificó.
- **T2 · Dos `§Recuento` mutuamente contradictorios** (`:254-261` y `:611`), **con las cinco cifras marcadas `~`** en ambos. Origen de la sonda `c26` NO ADJUDICABLE (§16.5).
- **T3 · Tres declaraciones «A (canónico) NO re-leído»** (`:706`, `:722-723`, `:726-727`) **revocadas por `§Re-verificación lado A` `:734-781`** (*«COMPLETADA 1→EOF… CERO discrepancias»*) **dentro del mismo archivo** — y son las tres primeras, no la última, las que viajaron a la cara B (`:358`, `:386`). Consecuencia 46.
- **T4 · Tamaños declarados sin medir.** `officialRegistry.ts` **95** declarado / **72** medido; `types.ts` **259** en `:14-47` y **258** en su propia `§Re-verificación:737`; ±1 en otros cuatro. **[`officialRegistry.ts` = 72 L re-medido y re-leído 1→EOF el 2026-07-30 ⇒ T1; los demás tamaños siguen T2]**
- **T5 · `utils.ts` declarado «selectivo» en `:34` e «íntegro» en `:300`** — el mismo archivo, dos estados opuestos en el mismo documento (L08: *abierto ≠ íntegro*, aquí en su forma más literal).

### §16.4 · Inversiones aguas arriba

- **I1 · `NativeToolRegistry` — patrón 4 contra `DEUDA-B §3.A·DB-05`.** La cara B (`§2.4:239-241`) lo **condiciona** («se mantiene SOLO si `CG-MCP-7` implementa el swap push-based»); `DB-05`, tal como quedó tras `R-1`/`RV-6`, ordena el borrado **incondicional**, y `CG-MCP-7` re-crea `unregister_by_prefix` **sobre `ToolRegistry`**, no como excepción al borrado. Misma especie que `P4-08-2` (consecuencia 34 / `AC-29`): **segundo caso auditado de esta especie, segundo defectuoso**.
- **I2 · `pending_servers()` — contradicción con `DB-28`.** `§2.4:244-245` lo trata como *nota, no ítem*; `DEUDA-B` lo indexa como **`DB-28`**. El par y el rollup receptor no coinciden en si existe la entrada. Consecuencia 49.
- **I3 · `SEAMS·S25` delega `mcp_servers→11` y 11 no lo recibe.** `SEAMS:438` — *`# DELEGADOS: mcp_servers→11 · skills/hooks→12/06 · effort→16 · memory→13 · isolation→10/18`*. En la cara B: **0 ocurrencias de `mcp_servers`**, **0 de `extractAgentMcpServers`**; en la cara A, `mcp_servers` aparece **sólo en `:719`** y es el campo de config **del propio runtime**, no el campo per-agente de `AgentDefinition`. Es el **espejo exacto** del `isolation→10/18` del par 10 (`§15.4`): mismo rollup, misma línea, par siguiente ⇒ **deja de ser incidencia y pasa a ser propiedad de `S25`**.
- **I4 · Cuatro grafías para una costura, y una viola el invariante transversal.** `11·§2.5·OI-MCP-A` ofrece **dos** firmas alternativas (`create_runtime(config.capabilities.mcp_user=…)` **o** `McpProvider(user_id=ctx.user_id)`); `DEUDA-A·ID-3` usa `scope=`; `00-INTEGRADORES §1.7·C5` fija **`RuntimeHost.scope`, token opaco, `user_id` NO interpretado**. Y `SEAMS:16-17` declara **transversal** el invariante `【id-opaco】`: *«ninguna firma transporta `userId`/`sessionId` interpretados»*. ⇒ la firma `McpProvider(user_id=ctx.user_id)` **no es una variante de grafía: es la firma prohibida por el invariante**, ofrecida al integrador en pie de igualdad con la correcta. **Hallazgo de cruce más grave del par.** Consecuencia 48.
- **I5 · `S23` ↔ `CG-MCP-20`: sustancia sí, cable nominal no.** `SEAMS:415-418` da `on_agent_teardown(agent_id)` como `ausente` y nombra *«11 (mcp)»* entre los consumidores que reap-ean lo suyo; `11·CG-MCP-20:229-230` **sí** recoge el trabajo (`cleanup_for_agent` + `AbortScope.on_abort`, `[FIND-MCP19]`) y **sí** nombra a sus dueños de cableado (`05·ExR6/GAP-EXEC4` + `08·CG-SIG-8`). Pero **ninguna de las dos caras nombra `S23`** y `§S23` no nombra `CG-MCP-20`. Falta el cruce bidireccional; **la sustancia está**. Se anota como inversión **benigna** — no como pérdida (L10).

### §16.5 · Las siete sondas

| sonda | qué se contrastó | veredicto |
|---|---|---|
| **c23** | 27 fichas ↔ `DEUDA-A` / `DEUDA-B` / `BATTERIES` / `00-INTEGRADORES` **[rollups en T2-LOG salvo `00-INTEGRADORES`, T1]** | **DEFECTO** — `I1`·`I2`·`I4` no absorbidas. Positivo simultáneo: `B12 battery_mcp` y `B14 battery_mcp_skills` **existen** en el catálogo receptor ⇒ `AC-35` **satisfecho** |
| **c24/c29** | `§2.1` (10 costuras) ↔ índice de **29** costuras de `SEAMS` | **DEFECTO — el peor medido de los once pares.** **10 de 10 sin número `S`**; cero ocurrencias de la cadena `SEAMS` en toda la cara B. Frente a 5/12 (par 10) y 1/7 (par 07). **La excusa estructural queda revocada**: `SEAMS:4` limita las fuentes a `{01,16,07,02,05,09}`, pero la **ENMIENDA A3.CAT** (`SEAMS:21-28`) numeró `S30`/`S31` desde el **ciclo 17**, que tampoco era fuente ⇒ el doc ya aceptó ampliarse fuera de las seis y no se generalizó. En sentido inverso: `S23` recogida en sustancia (`I5`), **`S25` huérfana** (`I3`) |
| **c25/c31** | colisión de namespace de identificadores | **LIMPIO** — `CG-MCP-*`, `MCP-OK-*`, `MCP-NA-*`, `OI-MCP-*`, `FIND-MCP*`, `McR*`: **todo prefijado**, cero `K\d` locales. Es el **contra-ejemplo** del par 10 (`K1..K12`) y del 06: la convención que pedía la consecuencia 15 **ya está aplicada aquí** |
| **c26** | recuentos declarados ↔ recuento propio | **NO ADJUDICABLE** (2º par, tras el 10). Las cinco cifras con `~` en **las dos** declaraciones del tracker, y **contradictorias entre sí**. **Peor que el par 10**: allí el destilado sustituyó el `~` por 64 celdas nominadas; aquí la cara B **lo propaga y además lo desdobla** (`🟡~6/8`, `🔀~4/5`, `❌~14/18`). Contrapeso honesto: el re-conteo de `§1.A` da **27 = 27** exacto (§16.1) |
| **c27/c32** | §Plan del tracker ↔ `§2.3` | **DEFECTO** — 226 L → 59 L ≈ **26 %**, referenciado y no re-desarrollado; misma especie que `P4-07-1` y que el `c27/c32` del par 10 (tercera reincidencia). Agravante propio: el rango citado (`McR1-19`) **incluye un `McR14` inexistente** |
| **c28** | autodeclaraciones de completitud del destilado | **DEFECTO** (3er par consecutivo). `Q1:339` afirma *«sí, **1→799**»* sobre un tracker de **798 L** — gemelo exacto del «1→793»/794 del par 10; `§3.1:301` cuadra el ledger como *«27+25+8+**3** DEUDA-B = **63**»* cuando `§2.4` tiene **8** entradas ⇒ **68**; `officialRegistry.ts` 95 vs 72. **Ninguna de las tres adjudicada por el propio doc** |
| **c30** | reparto `00-INTEGRADORES` ↔ `OI-MCP-*` | **LIMPIO CON MATIZ** — `§1.7:186` asigna `OI-MCP-A … OI-MCP-I` (los **nueve**, por rango) a `11·cap-mcp`: a diferencia de `10·OI-remote`, **no falta ninguno**. Matiz: la única línea que el lector del consolidador ve resume las nueve como *«declarar servidores, scope, stores de config/token y los handlers OAuth interactivos»* y **omite justamente el borde de seguridad** (`OI-MCP-B` política allow/deny, `OI-MCP-C` gate de aprobación, `OI-MCP-F` trust-gate). Bajo el contrato del propio `§1.7` (el detalle vive en el dueño) no es defecto de reparto. Persiste, como en el par 10: **ningún `OI-MCP-*` está en la espina `OI-1..23` / `OI-M1..8` / `OI-EVT-1..4`** |

### §16.6 · Anti-padding: lo que el par hace bien (L10)

1. **27 = 27**, re-contadas ítem a ítem, sin inflar ni caer ninguna.
2. **9 de 9 cabos entrantes reconocidos** (`§1.A` + `§2.6`) — se predijo pérdida aquí y la lectura la **refutó**.
3. **`c25` limpio**: el **único** par medido con el namespace íntegramente prefijado.
4. **`AC-35` satisfecho**: las dos baterías declaradas existen en `BATTERIES` (contra el par 10, con `battery_fs` duplicada 24 veces y `battery_todos` inexistente).
5. **El bug multiusuario de `§0.1` es el mejor hallazgo del par y llegó entero y acreditado *end-to-end en el ensamblador*** — `token_storage.py:24` (`base = f"{user_id}/mcp/{server_name}"`), default `"mcp"` en `provider.py:50/87`, y `factory.py:149-155` que pasa `storage=` y **nunca** `user_id=`. No es un docstring (`RV-5`) ni un «existe» (L09: *cablear ≠ existir*): es la cadena completa. Y queda **triplemente corroborado** por `00-INTEGRADORES §1.7·C5`.
6. `compact_context=[]` y `system_prompt_section` OPCIONAL **no** se inflan a B-orphan; los ⛔ de `mcpSkills.ts`/UI **no** se cuentan como ❌ y se nombra la categoría concreta (L07).

### §16.7 · Consecuencias **45-51**

**45.** **Un recuento con `~` es una declaración de que nadie contó — y su daño real no es el número: es que inmuniza al documento contra la sonda `c26`.** Los dos únicos pares NO ADJUDICABLES de once (10 y 11) son exactamente los dos que traen `~` en las cinco cifras. La diferencia entre ellos es la lección: **el par 10 sustituyó el `~` por 64 celdas nominadas; el 11 lo copió y lo desdobló.** ⇒ **regla: al heredar un `§Recuento` con `~`, el destilado sustituye la cifra por la enumeración; copiarla —y con más razón desdoblarla en `~6/8`— es propagar la ausencia de conteo.** Abre **`AC-37`**.

**46.** **Una afirmación revocada más adelante en el MISMO archivo sigue viajando: se cita la última aparición, no la primera.** Las tres «A canónico NO re-leído» (`:706`, `:722-723`, `:726-727`) fueron revocadas por `:734-781` **dentro del propio tracker**, y son las revocadas las que la cara B copió (`:358`, `:386`). Es la **variante intra-archivo del patrón 4** — el estado cambió bajo la cita sin salir del documento. ⇒ **regla: al destilar un doc con re-visitas o re-verificaciones, fijar el estado vigente de cada afirmación leyendo de EOF hacia atrás.** Abre **`AC-38`**.

**47.** **Un `✅ NADA PENDIENTE` cuyo propio gate declara una fuente sin leer es auto-refutable, y lo es por dos vías a la vez.** `§3.4` firma ✅ mientras `§3.2·Q3` dice «A (canónico) NO re-leído»: bajo `L04` el ✅ cae **por la declaración**; bajo `L11` (*el doc previo es una hipótesis*) cae **por haberla copiado sin verificar** — y de hecho ya era falsa. Las dos caras del mismo error conviviendo en un documento de 394 líneas. ⇒ **`§3.4` se degrada de ✅ a ⛔.**

**48.** **El nombre de un parámetro de costura es parte de la costura.** Cuatro grafías para un cable (`user_id=` · `mcp_user=` · `scope=` · `RuntimeHost.scope`), y **una de ellas contradice el invariante `【id-opaco】` que `SEAMS:16-17` declara transversal** — ofrecida además al integrador como alternativa legítima. ⇒ **regla: toda firma nueva que transporte identidad se contrasta contra `SEAMS:16-17` y `00-LEGEND §2.4` antes de escribirse, y ningún par puede ofrecer dos firmas alternativas sin decir cuál cumple el invariante.** Abre **`AC-39`**.

**49.** **Una entrada que el rollup receptor indexa como ítem no puede quedarse como «nota, no ítem» en el par.** `pending_servers()` es `DB-28` en `DEUDA-B` y «nota» en `11·§2.4`; `NativeToolRegistry` es `DB-05` **incondicional** y «condicionado» en 11. ⇒ **regla: el recuento de `§2.4` se cuadra contra el índice de `DEUDA-B`, nunca contra sí mismo** — aquí la falta de ese cuadre produjo el «3 DEUDA-B» de `§3.1` frente a las 8 entradas reales.

**50.** **«Pendiente de P6″» sólo es legítimo para una ausencia de ORIGEN (DR-2 pura). Si el archivo canónico existe y es abrible, la pasada que lo necesita lo abre — aplazarlo es el tell `elevar-en-vez-de-leer`.** Esta misma sección se escribió declarando *dos* incorporaciones «re-verificables sólo en P6″»; una de ellas, el ruteo del gate de nombre, dependía de `config.ts`, un archivo de 1578 líneas que estaba ahí todo el tiempo. Se abrió 1→EOF en la ventana de cierre, **confirmó** el ruteo y lo elevó a T1 sin coste de pasada. `D-08` no dice «resuelve la controversia cuando toque»: dice **resuélvela leyendo el canónico**. Lo que sí queda en P6″ es `extractAgentMcpServers`, porque ahí no falta una lectura — **falta que el tracker lo hubiera traído**, y eso ninguna lectura de esta pasada lo repara.

**51.** **Una costura se ancla a la función que EJECUTA el comportamiento, no a la que lo MUESTRA — y cuando dos funciones operan sobre el mismo campo, la de UI suele ver MENOS.** `CG-MCP-21` se creó anclada a `extractAgentMcpServers`; al abrir el canónico por excepción resultó ser la ruta de pantalla del `/mcp` (único consumidor `components/mcp/MCPSettings.tsx:6,49`), y —lo que convierte el error en daño— **descarta las referencias por string** (`utils.ts:483`, *«Skip string references»*) que la ruta real, `runAgent.ts:95-218 initializeAgentMcpServers`, **sí resuelve y conecta** (`:140-151`). Portar la ficha con el ancla de UI habría producido un runtime que acepta definiciones inline y **ignora silenciosamente** las referencias por nombre. Añádase que la ruta real trae lo que ninguna pantalla enseña: **ciclo de vida asimétrico** (sólo los clientes creados inline se limpian, `:194-210`/`:818`, porque limpiar uno compartido mataría el MCP del padre), **fusión aditiva** (`:214`, el subagente no recibe un subconjunto sino el pool del padre MÁS los suyos — lo que **refutó** la formulación con la que yo mismo escribí la ficha), un **gate 【borde-seguridad】** que salta el MCP de frontmatter sólo para agentes no admin-trusted (`:112-127`) y **degradación no fatal** en los tres modos de fallo. **Regla: antes de escribir la contraparte canónica de una ficha, censar los consumidores de la función candidata; si todos son de presentación, la función es `MCP-NA` y el gap está en otro sitio.**

### §16.8 · Remediación **APLICADA** en `SEPARACION/11-cap-mcp.md` — **394 → 625 L**

| pérdida / defecto | dónde quedó | comprobación |
|---|---|---|
| `P4-11-1` §Plan 226 L → 59 L | **§2.7 NUEVA** · orden de aplicación en 6 olas con la dependencia que justifica cada una | restitución **parcial y declarada como tal**: se restituyen orden y dependencias; **no** las firmas por `McR` ni los criterios de aceptación, que siguen sólo en el tracker `:374-599`. Dicho en el propio §2.7, no en nota al pie |
| `P4-11-2` `search_hint` | `CG-MCP-2` (renombrada *`is_mcp`/`always_load`/`search_hint`*) | cruzado con `SEAMS §S16` *A CRECER (09·A12)*: el rollup lo esperaba |
| `P4-11-3` truncado 2048 + sanitización unicode | `CG-MCP-6` (renombrada *+ higiene de salida*) | se argumenta por qué **no** es el mismo mecanismo que el cap de 100k: borde de confianza, no cosmética |
| `P4-11-4` `_meta` del lado llamada | `CG-MCP-5` | *«`S16` se cerraría en falso con media costura»* |
| `P4-11-7` filas ausentes | **`MCP-NA-9`** (`officialRegistry`, **72 L** medidas vs 95 declaradas) + fila **`S25·mcp_servers`** en §1.A | la segunda con **nota de origen** explícita: es DR-2, no viene del tracker |
| `P4-11-8` menor mal ruteado | §2.3 *Menores plegados — DESPLEGADOS*: `regex`/reservados de `addMcpConfig` **`CG-MCP-13` → `CG-MCP-11` + `CG-MCP-1`** | **pagado: `config.ts` re-abierto 1→EOF el 2026-07-30 y el ruteo CONFIRMADO a T1** — se escribió primero por razón estructural (admisión ≠ dedup) y después se verificó contra el canónico, que es el orden correcto pero no el orden suficiente |
| `c24/c29` · 10 costuras sin `S` | §2.1 con bloque **⛔ CRUCE CON `SEAMS`** al frente + `[S-PEND]` en las 7 que 11 debe numerar | precisión que evita sobre-reclamar: de las diez, `CapabilityProvider` (home 12) y `ToolExecEnvironment` (home 09) **no son de 11**; `cleanup_for_agent` ya tenía contraparte (`S23`) |
| `I3` · `S25:438 mcp_servers→11` huérfana | **`CG-MCP-21` CREADA** + fila en §1.A + costura en §2.1 | alcance en tres partes (shape→05, resolución→battery, filtro FQ→gateado por `CG-MCP-1`) y la distinción explícita frente al `mcp_servers` global del tracker `:719`, que fue la causa del huérfano |
| `I5` · `S23` ↔ `CG-MCP-20` | cable nominal escrito en §2.1 **y** en `CG-MCP-20` | falta el sentido inverso, **en `SEAMS`** — declarado como PENDIENTE 1, no dado por pagado |
| `I4` · 4 grafías + violación de `【id-opaco】` | `OI-MCP-A` reescrita a **una** firma `RuntimeHost.scope` + cita literal de `SEAMS:16-17`; `CG-MCP-16` alineada | las dos firmas anteriores se retiran **con la razón escrita**, no en silencio |
| `I1` · `NativeToolRegistry` vs `DB-05` | §2.4 y §2.6·(c): retirar **incondicionalmente**; se explica por qué la condición era además innecesaria | *«un par no puede reintroducir por la puerta de atrás una condición que el rollup receptor ya cerró»* |
| `I2` · `pending_servers()` vs `DB-28` | §2.4: reconocido **ítem**, no nota; entra en el recuento | el veredicto de fondo (conservar) **no** cambia — se dice |
| `c26` · recuento con `~` | cabecera `:6` **retirada** y sustituida por enumeración + nota de por qué | *«un `~` es la constancia de que nadie contó»* |
| `c28` · 3 cifras no medidas | `Q1` 799→**798** + `McR1-19`→**18 pasos reales**; ledger 63→**70** con el desglose del error (8 DEUDA-B contadas como 3); `officialRegistry` 95→**72** | el ledger explica que **con las entradas de entonces** el total correcto ya era 68 |
| `T3` · frase revocada viajando | `Q3` y `§3.3` corregidas citando `../11-cap-mcp.md:734-781` y la laguna confesada de `:745` | consecuencia 46 aplicada al propio texto |
| `§3.4` `✅ NADA PENDIENTE` | **degradado a 🟡** con los **dos pendientes que NO se cierran desde el archivo** nombrados uno a uno | consecuencia 47; ninguno se declara pagado |
| `H-3` | **RECHAZADO expresamente** en §3.3·bis (home = 05) | `L07`: lo fuera de alcance se nombra, no se silencia ni se adopta |
| `L05`/`AC-36` | §3.3·bis enumera lo hallado **con rango de líneas** en cada cita | — |

**Positivo conservado sin inflar (L10):** §3.3·bis cierra listando lo que se sostuvo tal cual — 27=27, 9/9 cabos, namespace íntegramente prefijado, `B12`/`B14` existentes, y el bug multiusuario acreditado en el ensamblador. No se reescribió nada de eso.

**Lo que esta remediación NO paga, y por qué no puede:**
1. **El alta de los números `S`** de las siete costuras `[S-PEND]` y los dos cables inversos (`S23`, `S25`): el número lo asigna `SEAMS`, no el par. → remediación de columna de cruce, abajo.
2. **Las 38 anclas canónicas y los 42 tests**: patrón 3, transversal a `SEPARACION/*`. Escribir anclas no re-verificadas en esta pasada sería fabricar evidencia; se declara y se deja al esquema.
3. **~~Las dos incorporaciones DR-2 … sólo en P6″.~~ CERRADAS LAS DOS EL 2026-07-30, abriendo el canónico por excepción a instancia del usuario.** `utils.ts` 1→EOF (575 L) + censo de consumidores + `runAgent.ts` (:1-240, :640-834) **refutaron el ancla de `CG-MCP-21`** y la ficha se reescribió a T1 (ver consecuencia 51); `config.ts` 1→EOF (1578 L) y `officialRegistry.ts` 1→EOF (72 L) **confirmaron** el ruteo del gate de nombre y el `MCP-NA-9`. **Queda cero DR-2 pendiente en este par.** Texto original tachado, no borrado:
   ~~Las dos incorporaciones DR-2 marcadas T2-HEREDADO, re-verificables sólo en P6″.~~ **CORREGIDO 2026-07-30: era falso para una de las dos y para la única que quedaba el aplazamiento era evitable.** `config.ts` (1578 L) y `officialRegistry.ts` (72 L) se abrieron 1→EOF en la ventana de cierre ⇒ el ruteo del gate de nombre es **T1** y no debe nada a P6″. Sigue siendo DR-2 pura **sólo `extractAgentMcpServers`** (ausencia de origen: el tracker nunca lo trajo), y eso sí lo cierra P6″. **Decir «sólo verificable en P6″» de algo que se podía abrir en el acto es el tell `elevar-en-vez-de-leer` (`D-08`).**

### §16.9 · Ítems de ledger que abre el par 11

| id | qué | por qué no se cierra aquí |
|---|---|---|
| **`AC-37`** | barrido **`~`-en-recuento** sobre los 18 destilados: sustituir toda cifra aproximada heredada por enumeración nominal | consecuencia 45; afecta a pares ya cerrados (10 y 11 confirmados) ⇒ es barrido, no arreglo de par |
| **`AC-38`** | barrido **última-aparición-manda**: en cada destilado, verificar que ninguna afirmación citada del tracker fue revocada más adelante **en el mismo tracker** | consecuencia 46; requiere re-leer los 18 trackers de EOF hacia atrás |
| **`AC-39`** | **unificación de nombres de costura de identidad** (`user_id=` · `mcp_user=` · `scope=` · `RuntimeHost.scope`) y contraste de **toda** firma que transporte identidad contra `SEAMS:16-17` + `00-LEGEND §2.4` | consecuencia 48; toca `DEUDA-A·ID-3`, `00-INTEGRADORES §1.7·C5`, 11 y 15 a la vez |
| **`AC-40`** | comprobar los **otros cuatro delegados de `S25`** (`skills/hooks→12/06`, `effort→16`, `memory→13`) y, si alguno más está huérfano, **corregir el estado `existe-parcial` de `S25`** | cae en los pares 12/13/16, aún no auditados. *(La parte de este ítem que SÍ era pagable —numerar las siete costuras MCP y escribir los dos cables inversos— **se pagó en la misma ventana**, no se declaró: ver abajo.)* |

**`PENDIENTE 1` de `§16.8` — PAGADO, no declarado (`D-07`).** `SEAMS.md` estaba abierto 1→EOF en esta ventana
(`EVIDENCIA.log:247`), así que la remediación de columna de cruce se aplicó en vez de aplazarse. **`ENMIENDA
A-CIERRE.MCP (2026-07-30)` en `SEAMS.md` (539 → 606 L):**
- **Altas `S32`-`S38`** (índice **29 → 36**): `McpConfigStore`/`ScopedMcpConfigStore` · `McpConfigWatcher` ·
  `register_auth_strategy`/`AuthDeps` · **`McpPolicy`** · **`McpApprovalGate`** · `elicitation-hook` ·
  **`trust-gate` del headersHelper**. Las tres en negrita nacen **`ausente` y marcadas 【borde-seguridad】**: hasta
  hoy, un lector del rollup **no veía** que la admisión de servidores MCP, la aprobación de servidores de proyecto y
  el gate del script de headers son decisiones del integrador. Ese es el daño que `c24/c29` mide — no el número que
  falta, sino **la costura que no existe para quien lee el rollup**.
- **La exclusión de `SEAMS:4` queda derogada por escrito**, con su motivo: `A3.CAT` ya la había roto numerando
  `S30`/`S31` desde el ciclo 17. Regla vigente anotada para 12·13·14·15·16·17·18: **si está cableada, se numera**.
- **`§S23`** gana la lista de consumidores registrados, con `11·CG-MCP-20` como **el único con cable nominal**; 10 y
  12 quedan explícitamente marcados como *sin comprobar*.
- **`§S25`** gana una **tabla de estado de sus seis delegados**: `isolation`→10 ❌ huérfano, `mcp_servers`→11 ❌
  huérfano **ahora resuelto** (`CG-MCP-21`), y los otros cuatro ⬜ sin comprobar — con la advertencia de que **dos de
  dos han fallado** y de que su estado `existe-parcial` habrá que corregirlo si cae un tercero.
- **`【id-opaco】`** gana la nota de aplicación de `AC-39`: grafía única vinculante **`RuntimeHost.scope`**, con la
  constancia de que la firma `user_id=` publicada por `11·OI-MCP-A` **incumplía el invariante**.
- **Matriz §4** ampliada con las 8 filas correspondientes (las 7 altas + `S23`).

**Nota sobre `S25` (la que más peso tendrá aguas abajo).** `SEAMS:438` reparte **seis** delegados y en dos pares consecutivos (10·`isolation`, 11·`mcp_servers`) el dueño nombrado **no los tenía**. Quedan cuatro sin comprobar — `skills/hooks→12/06`, `effort→16`, `memory→13` — y los tres pares que los reciben (12, 13, 16) están en la cola. **Predicción registrada para poder fallar en público:** si al menos uno de los cuatro aparece también huérfano, `S25` deja de ser una costura con huecos y pasa a ser **una costura que nunca se cableó**, y su estado `existe-parcial` en `SEAMS:425` estará mal puesto.

