# PLAN — Re-arquitectura B (base framework + batteries) · post-homologación

> Ruta base: `/home/noheroes/python`. Este plan vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/PLAN.md`.
> El tracker validado (2ª vuelta) vive en el directorio padre `../` (18 `NN-<sub>.md` + `DEUDA-B-transversal.md` + `README.md` + `PROGRESS.md`).

## 0. Contexto y decisiones (fuente = memoria; leer si se retoma en frío)
Memorias: **architecture-layers** (bloques 2026-07-21: Filosofía **B** base-framework+batteries · agnosticismo de identidad · invarianza **T1/T2/T3** · landscape 2 integradores · canónico=completitud-no-forma) · **mimica-no-desfusion** · **pi-runtime-reference** · **homologation-effort**.

- **Runtime = base framework agnóstico.** NO override; **composición** de batteries.
- **Frontera por INVARIANZA → T1/T2/T3.**
- **Identidad = del integrador.** El runtime lleva **ids opacos** + patrón **repo/costura** (nunca `userId`/`sessionId` en contratos).
- **Integradores originales:** `agentic_code` (CLc-like, compone batteries) · `agentic_assistant` (openclaw-like, posee orquestación).
- **Canónico = referencia de COMPLETITUD de capacidades, NO de FORMA.** No imitar el monolito.
- `learned_lessons/` del tracker está **RETIRADO** como método. Método = lecciones de la skill `~/.claude/skills/analisis-comparativo-ab/lecciones/*.md`.

## 1. Principios de ejecución (anti-superficialidad + higiene de contexto)
1. **PASO 0** al iniciar CUALQUIER ciclo de SEPARACION: leer íntegras las lecciones de la skill. Puertas activas: L00 (falsa economía), L01 (lectura íntegra), L07 (fuera de alcance), L09 (cablear=ensamblador, no grep), L10 (divergencia≠deuda), L11 (validar completitud, no confirmar doc).
2. **Ciclos CORTOS: 1 ciclo = 1 entregable.** `/clear` entre ciclos. **Nunca** encadenar 2 categorías en un mismo contexto.
3. **Lecturas ACOTADAS:** cada ciclo lista EXACTAMENTE qué leer; no leer de más (evita superar el umbral donde aparecen alucinaciones). Regla: si un ciclo pide > ~2 docs grandes + 1 ensamblador puntual → **subdividir**.
4. **Cierre de ciclo (MOSTRADO) = GATEKEEPER de `00-LEGEND.md §3.3`** (frase de rigor + ledger por-finding + 5 preguntas + VEREDICTO; sin él la categoría NO está cerrada), más: (a) artefacto escrito; (b) marcar checklist §7 + actualizar memoria SIGUIENTE; (c) enunciado de retoma.
5. **Gate auto-adversarial:** cada afirmación de clasificación/cableado respaldada por lectura (ensamblador 1→EOF, no grep); declarar qué NO se verificó.
6. **Sin código** en fases de diseño (A0, A1, A3). Código **solo** en A2 (skeleton) y Fases B+.

## 2. Estrategia (recomendación aceptada: (2) espina + walking skeleton + resto)
Fase A = diseño + validación de costuras. Fases B–F = construcción. **Detalle fino solo de Fase A**; B–F se re-decomponen en el ciclo A-CIERRE (no over-planear lo lejano = otra forma de superficialidad).

## 3. Legend / esquema de clasificación (usado por TODOS los ciclos de SEPARACION)
Cada `SEPARACION/NN-<sub>.md` contiene:
- **Tabla por finding** (ID del tracker): `ID · resumen · núcleo|cáscara-CLI · TIER · destino · nota-identidad · acción`.
- **TIERs:**
  - `T1-CONTRATO` — shape de datos invariante (message/tool/event/stream). Reimplementarlo forkea el ecosistema.
  - `T1-MOTOR` — costura al motor de modelo (`agentic_models`).
  - `T2-BASE-MECANISMO` — esqueleto/mecanismo invariante (loop, dispatch, ciclo de vida).
  - `T2-COSTURA` — interfaz que el integrador/battery rellena (repo/scope, hook-sink, tool-provider…).
  - `BATTERY` — paquete estándar OPCIONAL derivado del canónico (compactación, tool concreta, memoria, skill, mcp, plan).
  - `T3-INTEGRADOR` — identidad/sesión/transporte/política de producto. Nunca en el runtime; solo la costura.
  - `CLI-ONLY / INTERFAZ` — capa de presentación/interfaz de la referencia (terminal/UI). No al runtime (headless), pero NO se descarta: elemento a implementar en el integrador (agentic_code=terminal; agentic_assistant=front). Por completitud de capacidad, no forma verbatim.
  - `DEUDA-B` — higiene interna del runtime (borrar huérfano / cablear seam a medias).
- **Regla de destino:** T1→paquete contratos/motor · T2-BASE→módulo base · T2-COSTURA→nombre de interfaz · BATTERY→nombre de paquete · T3→integrador · CLI-ONLY/INTERFAZ→integrador (capa de interfaz) · DEUDA-B→borrar|cablear.
- **nota-identidad:** si el finding toca scope/persistencia → marcar el eje (persistencia|ejecución) + "id opaco + repo".
- **Síntesis por categoría:** costuras que implica + batteries que alimenta + **CORE-GAPs** (para el rollup DEUDA-A) + **elementos de integrador** (T3/CLI-ONLY-INTERFAZ/composición → para `00-INTEGRADORES.md`).
- **Salida de DOS caras con detalle SIMÉTRICO (def. usuario 2026-07-21):** lo que encaja en el runtime → `00-BLUEPRINT.md`; lo que ya NO encaja → `00-INTEGRADORES.md` **con el mismo rigor** (L05 adaptada). El eje PRIMARIO de `00-INTEGRADORES.md` = el **CONTRATO BASE COMÚN, el "must-be" de TODO integrador agéntico** (el runtime agnóstico no hace X ⇒ todo integrador DEBE hacer X); lo específico de cada integrador (terminal en agentic_code; multi-tenant+front en agentic_assistant) es la realización concreta, capa secundaria. `CLI-ONLY` NO es descarte: es la obligación universal "capa de interfaz/transporte", realizada específico. Nada se cierra con "→ integrador" a secas.

## 4. CICLOS — Fase A

### A0 — Andamiaje + legend (fundacional, sin tracker)
- **Objetivo:** crear `SEPARACION/00-LEGEND.md` (esquema §3), `SEPARACION/00-BLUEPRINT.md` (esqueleto del mapa base↔costuras↔batteries) y su **gemelo `SEPARACION/00-INTEGRADORES.md`** (guía del lado implementador: lo que NO encaja en runtime, con detalle simétrico) y validar el checklist §7.
- **Leer (acotado):** este PLAN + memoria architecture-layers. NADA del tracker.
- **Salida:** `00-LEGEND.md` + `00-BLUEPRINT.md` (skeleton base) + `00-INTEGRADORES.md` (skeleton integrador).
- **Gate:** legend/buckets consistentes con §3; blueprint con secciones vacías (base / costuras / batteries / integradores); integradores-doc con secciones vacías (agentic_code / agentic_assistant) + regla de simetría de detalle.

### A1 — SEPARACION de la ESPINA (6 ciclos, 1 categoría c/u)
Orden (dependencia conceptual): **contracts → models → events → loop → execution → tools-infra**.
**Para CADA ciclo A1.x:**
- PASO 0 (lecciones skill).
- **Leer (acotado):** `00-LEGEND.md` + `../NN-<sub>.md` (íntegro) + [solo si un finding exige confirmar costura] el **tramo** puntual del ensamblador (`factory.py` / `agent_loop.py`), no el archivo entero.
- **Pasos:** clasificar cada finding por TIER+destino; anotar identidad; escribir síntesis (costuras + batteries + CORE-gaps).
- **Salida:** `SEPARACION/NN-<sub>.md`.
- **Gate:** cada fila con TIER+destino; costuras nombradas; §honestidad (qué no se verificó); VEREDICTO.
- Ciclos: **A1.1** 01·contracts · **A1.2** 16·models · **A1.3** 07·events · **A1.4** 02·loop · **A1.5** 05·execution · **A1.6** 09·tools-infra.

### A1.7 — Síntesis de la ESPINA → blueprint del base + contratos de costura
- **Objetivo:** consolidar A1.1–A1.6 en `00-BLUEPRINT.md`: módulos del base framework + lista de **costuras con FIRMAS borrador** (model-caller, tool-contract, event/stream, dispatch, repo/scope) + batteries que emergen.
- **Leer (acotado):** `00-LEGEND.md` + los **6** `SEPARACION/NN.md` de la espina. NADA del tracker crudo (ya destilado).
- **Salida:** `00-BLUEPRINT.md` (espina) + `SEAMS.md` (firmas borrador con productor/consumidor) + verter el bucket "elementos de integrador" de la espina a `00-INTEGRADORES.md` (agentic_code degenerado).
- **Gate:** cada costura con firma borrador + productor/consumidor; el base es construible en un skeleton.

### A2 — WALKING SKELETON (código spike; 5 ciclos) — valida las costuras con un TURNO REAL
Ubicación: rama o paquete spike (decidir en A2.1). Evidencia = **correr**, no solo compilar.
- **A2.1 Andamiaje:** paquete/rama spike; stubs de las costuras de `SEAMS.md`; loop mínimo (sin tools). Leer: `00-BLUEPRINT.md` + `SEAMS.md`. Gate: typechecks.
- **A2.2 Motor:** cablear costura model-caller → `agentic_models`; 1 turno real texto-solo. Leer: `SEAMS.md` + API de `agentic_models` (acotado). Gate: corre 1 turno real.
- **A2.3 Tools:** dispatch + 1 tool nativa vía tool-contract. Gate: el modelo llama la tool y el resultado se aplana.
- **A2.4 Battery:** componer 1 battery trivial vía la costura de composición. Gate: la battery se anuncia/consume sin que el base la conozca.
- **A2.5 Integrador + validación:** ~20 líneas que corren el turno end-to-end; capturar aprendizajes; **CORREGIR** blueprint/SEAMS si una costura no aguantó. Salida: `SKELETON-REPORT.md` (veredicto de costuras). Gate: turno real end-to-end; costuras **validadas o corregidas**.

### A3 — SEPARACION del RESTO (batteries/capabilities + deudas; ~14 ciclos, 1 c/u)
Con costuras ya validadas por A2. Mismo formato que A1.x.
Orden sugerido: **03·context → 10·tools-native → 06·hooks → 08·signals → 04·modes → 15·storage → 13·memory → 12·skills → 11·mcp → 14·plan → 17·voice → 18·factory.**
Luego:
- **A3.DA — DEUDA-A rollup:** `SEPARACION/DEUDA-A.md` = backlog consolidado de todos los CORE-GAP (agrupado por battery/base), priorizado. Leer: los `SEPARACION/NN.md` (no el tracker).
- **A3.DB — DEUDA-B:** `SEPARACION/DEUDA-B.md` = clasificar `../DEUDA-B-transversal.md` (borrar vs cablear) por tier. Leer: ese doc + los SEPARACION previos.
- **A3.CAT — Catálogo de batteries:** `SEPARACION/BATTERIES.md` = paquetes battery con alcance, derivado de todas las síntesis.

### A-CIERRE — Blueprint final + plan de construcción B–F
- **LEDGER DE DESCARGA (insumo obligatorio, escrito 2026-07-27): `SEPARACION/A-CIERRE-LEDGER.md`** — inventario auditable de todo lo que converge aquí: **64 ocurrencias de "A-CIERRE" en 58 líneas** de 6 docs → **40 descartadas nombrándolas una a una** + **18 ítems distintos** (`AC-01..AC-18`), cada uno con origen `archivo:línea`, tipo, tamaño medido y pasada. **17 se ejecutan en A-CIERRE, 1 (RB-1..RB-6) sale a Fase B.** **A-CIERRE NO cabe en dos pasadas: se decompone en 10 (P0..P9)**, forzadas por `AC-12` = los 18 `NN-*.md` **6531 L ≈ 795 KB** repartidos en P4·P5·P6·P7 (1631+1674+1667+1559 = 6531 exacto). **2 precedencias duras:** `DEUDA-B` 1→EOF (P2) **antes** de la auditoría RV-6 de sus 37 entradas BORRAR (P3) — leerlo a trozos ya produjo un error real (`CAT-h7`); y P4–P7 **antes** de consolidar `00-INTEGRADORES §1.x` (P8), que consume los `OI-*` que sólo aparecen al reabrir por categoría. **Fase B no abre hasta que el ledger esté en 0**, salvo los 3 ítems con destino declarado fuera (`RB-*`→B · `V6`→C · `V5`→ninguno, decisión declarada).
- **Objetivo:** `00-BLUEPRINT.md` final (base + costuras + batteries) + **`00-INTEGRADORES.md` final** (guía de implementación de `agentic_code` base y `agentic_assistant`, detalle simétrico) + **decomponer Fases B–F en ciclos concretos** (ahora sí, con diseño completo).
- **Gate:** diseño construible end-to-end **por ambas caras** (base + integrador); B–F con ciclos definidos → se anexan a §4/§7. Fase E (agentic_code) y F (agentic_assistant) guiadas por `00-INTEGRADORES.md`.

## 5. Fases B–F (coarse; se detallan en A-CIERRE)
- **B — Base framework:** contratos T1 + costuras + mecanismo; ripear mímica de identidad → id opaco + repo; re-hogar los 122 tests (base / batteries / integrador).
- **C — Batteries:** construir del catálogo A3.CAT, test-gated (xfail→verde).
- **D — `agentic_models`:** solidificar como costura T1-MOTOR.
- **E — `agentic_code`:** componer base+batteries → valida el stack completo end-to-end.
- **F — `agentic_assistant`:** integrador complejo + front (bff/KrakenD/Keycloak/MinIO).

## 6. Convención de RETOMA (mínima; rescata de memoria)
El enunciado de retoma es un **disparador mínimo**; el detalle vive en este PLAN + en memoria SIGUIENTE. Enunciado tipo (pegar tras `/clear`):

> «Continuación B (SEPARACION). Ruta base `/home/noheroes/python`. Recupera de tu memoria el estado (architecture-layers, mimica-no-desfusion, pi-runtime-reference, homologation-effort) y lee `agentic_runtime/src/HOMOLOGATION/SEPARACION/PLAN.md`; ejecuta el **primer ciclo sin marcar** del checklist §7 con máximo rigor: **PASO 0 primero**, lecturas **acotadas** a lo que el ciclo indica, sin superficialidad; cierra con resumen-de-pendientes + veredicto + actualiza checklist §7 y memoria SIGUIENTE + siguiente retoma. No preguntes; procede.»

Al cerrar cada ciclo: **marcar §7** + actualizar la memoria SIGUIENTE (homologation-effort) al ciclo siguiente.

## 7. Checklist de progreso — **movido a `PLAN-CHECKLIST.md`** (2026-07-30)

> Estas 31 líneas eran **el 84 % de la masa de `PLAN.md`** (92.460 de 114.062 ch): 16 viñetas `- [x]` que
> se habían comido el informe completo de su ciclo, hasta **13.017 ch en una sola viñeta**. Viven íntegras
> y sin tocar en **`PLAN-CHECKLIST.md`**; el corte fue mecánico y `PLAN.md(:1-102) + PLAN-CHECKLIST(:tras
> cabecera)` reproduce el original byte a byte (`sha256 = a53ee1247676c458c177a05c5f05a211fa14bb8c2e2ba7db0e467f0351e2ef4c`). `DECISIONES.md · D-09`.
>
> **Al cerrar un ciclo se marca allí, en UNA línea** (ciclo · fecha · documento · veredicto). El informe
> va a `PROGRESS.md` y al destilado del ciclo — nunca aquí.
