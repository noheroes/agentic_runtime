# 00 · LEGEND — esquema de clasificación de la SEPARACION (Filosofía B)

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/00-LEGEND.md`.
> **Fuente normativa:** `PLAN.md §3`. Este doc lo **desarrolla** en un esquema operable que **TODOS** los
> ciclos `SEPARACION/NN-<sub>.md` reutilizan literalmente. Si `PLAN.md §3` y este doc discrepan, manda `PLAN.md`.
> Marco conceptual: memoria **architecture-layers** (Filosofía B = base framework + batteries · agnosticismo de
> identidad · invarianza T1/T2/T3 · canónico = referencia de COMPLETITUD, no de FORMA).

---

## 1. Propósito de la SEPARACION

La 2ª vuelta de homologación produjo un tracker feature-by-feature (18 categorías en `../NN-<sub>.md`) que mide
**fidelidad de capacidades** del runtime frente al canónico. La SEPARACION es la fase de **MEJORA DE FORMA**: releer
cada finding del tracker y **re-clasificarlo bajo Filosofía B**, respondiendo tres preguntas por finding:

1. **¿Es núcleo del base framework, o cáscara de un integrador/CLI?** (columna `núcleo | cáscara-CLI`)
2. **¿Qué grado de invarianza tiene?** → **TIER** (T1 / T2 / BATTERY / T3 / CLI-ONLY / DEUDA-B).
3. **¿A dónde va?** → **destino** (paquete de contratos, módulo base, nombre de costura, nombre de battery, integrador, borrar/cablear).

Más una **nota-identidad** (si toca scope/persistencia) y una **acción** concreta.

El producto NO es otra tabla de deuda: es el **mapa de descomposición base ↔ costuras ↔ batteries ↔ integradores**
que alimenta el walking skeleton (A2) y las Fases B–F de construcción.

### 1.1 Salida de DOS caras, con detalle SIMÉTRICO (definición del usuario 2026-07-21)
La SEPARACION reparte **todo** lo documentado en las 2 vueltas — nada se descarta:
- **Cara runtime/base** — lo que **encaja** (T1 / T2 / BATTERY) → `00-BLUEPRINT.md` → guía de construcción del base (Fases B–D).
- **Cara integrador** — lo que **ya NO encaja en el runtime** (T3 identidad/sesión, política de producto, capa de
  interfaz ex `CLI-ONLY`, composición de batteries) → **`00-INTEGRADORES.md`**. **Eje PRIMARIO = el CONTRATO BASE
  COMÚN, el "must-be" que TODO integrador agéntico hereda** (el runtime deliberadamente no hace X ⇒ todo integrador
  DEBE hacer X): comportamientos base estándar de cualquier integrador. Las necesidades **específicas** de cada
  integrador (terminal en agentic_code; multi-tenant+front en agentic_assistant) son la **realización concreta**
  de esas obligaciones universales — capa secundaria, no el eje. Guía Fases E–F.

**Regla de SIMETRÍA de detalle:** un finding que cae al integrador se desarrolla con el **MISMO rigor** que uno que
se queda en el base (L05 adaptada: **capacidad observable · costura que rellena / battery que compone · firma ·
cableado en el integrador · orden · criterio de aceptación**). Prohibido cerrarlo con "→ integrador" a secas.

---

## 2. Ejes de clasificación

### 2.1 Eje `núcleo | cáscara-CLI`
- **núcleo** — comportamiento del base framework o de una battery: vive en `agentic_runtime` o en un paquete battery.
- **cáscara-CLI** — presentación/terminal/UI del canónico (render, teclado, spinner, markdown-a-terminal). **No al
  runtime** (headless), pero **NO se descarta**: es capa de interfaz → **elemento a implementar en el integrador**
  (ver TIER `CLI-ONLY / INTERFAZ`, §2.2). Marcar cáscara-CLI **sólo tras abrir** el finding (lección 02: prohibido por título).

### 2.2 Eje TIER (grado de invarianza)

| TIER | Qué es | Regla de destino |
|---|---|---|
| **T1-CONTRATO** | Shape de datos invariante (message / tool / event / stream). Reimplementarlo forkea el ecosistema — es el boundary donde enchufan AMBOS integradores. | → paquete de **contratos** |
| **T1-MOTOR** | Costura al motor de modelo (`agentic_models`): cómo se invoca el modelo, streaming, tool-calls a nivel wire. | → paquete/costura **motor** |
| **T2-BASE-MECANISMO** | Esqueleto/mecanismo invariante que el base framework **posee**: loop, dispatch, ciclo de vida de turno/ejecución. Mecanismo, no política. | → módulo del **base** |
| **T2-COSTURA** | Interfaz que el integrador o una battery **rellena**: repo/scope, hook-sink, tool-provider, model-caller, event/stream-sink. El base define la firma, no el contenido. | → **nombre de interfaz** (costura) |
| **BATTERY** | Paquete estándar **OPCIONAL** derivado del canónico: comportamiento específico (compactación, una tool concreta, memoria, skill, mcp, plan). Se **compone o sustituye — nunca sobreescribe**. | → **nombre de paquete** battery |
| **T3-INTEGRADOR** | Identidad / sesión / transporte / política de producto. **Nunca** en el runtime; sólo la costura por la que entra. | → **integrador** (+ la costura T2 asociada) |
| **CLI-ONLY / INTERFAZ** | Capa de presentación/interfaz de la referencia (terminal / UI). **No al runtime** (headless), pero **NO se descarta**: es **elemento a implementar en el integrador** que tenga interfaz (`agentic_code` = terminal; `agentic_assistant` = capa front separada). Se documenta por **completitud de capacidad, no por forma verbatim**. Legítimo **sólo tras abrir** el finding (L02). | → **integrador** (`00-INTEGRADORES.md`) |
| **DEUDA-B** | Higiene interna del runtime: huérfano a borrar, o seam cableado a medias a completar. No es deuda frente al canónico. | → **borrar** \| **cablear** |

**Relación T1/T2/T3 ↔ etiquetas de architecture-layers** (`BASE-MECANISMO / COSTURA / PAQUETE-ESTÁNDAR / INTEGRADOR`):
- `BASE-MECANISMO` ≡ **T2-BASE-MECANISMO** (+ los contratos **T1** que el mecanismo mueve).
- `COSTURA` ≡ **T2-COSTURA** (y **T1-MOTOR** es la costura específica al motor de modelo).
- `PAQUETE-ESTÁNDAR` ≡ **BATTERY**.
- `INTEGRADOR` ≡ **T3-INTEGRADOR**.

### 2.3 Eje destino (§3 del PLAN, forma canónica)
`T1-CONTRATO → paquete contratos` · `T1-MOTOR → paquete/costura motor` · `T2-BASE → módulo base (nombrado)` ·
`T2-COSTURA → nombre de interfaz` · `BATTERY → nombre de paquete` · `T3 → integrador (+ costura)` ·
`CLI-ONLY / INTERFAZ → integrador (00-INTEGRADORES.md, capa de interfaz)` · `DEUDA-B → borrar | cablear`.

### 2.4 nota-identidad (transversal — SEAM-DE-IDENTIDAD/SESIÓN)
Si el finding toca **scope / persistencia / atribución de usuario o sesión**, se marca el **eje** afectado y el patrón:
- **eje:** `persistencia` (durable: sesión/transcript/memoria/storage) \| `ejecución` (efímero: turno/run/task/fork).
- **patrón obligado:** **id opaco + repo genérico**. El runtime reifica **sólo el `.id` opaco** de la unidad y delega
  create/open/list/delete/fork + scoping a un **repo inyectado**, genérico sobre una **metadata que el integrador define**.
  **Nunca** `userId` / `sessionId` interpretados en contratos del runtime; **ningún objeto global de identidad/scope**.
- Estos findings se **consolidan** en el hilo transversal (rollup en `DEUDA-A.md`), no se resuelven categoría a categoría.

---

## 3. Formato de cada `SEPARACION/NN-<sub>.md`

Cada doc de categoría contiene, en este orden:

### 3.1 Tabla por finding
Una fila por **ID del tracker** (`../NN-<sub>.md`), con columnas:

| ID | resumen | núcleo \| cáscara-CLI | TIER | destino | nota-identidad | acción |
|---|---|---|---|---|---|---|

- **ID** — el identificador del finding en el tracker (p.ej. `FIND-EVT1`).
- **resumen** — una línea del comportamiento observable (no la forma).
- **núcleo | cáscara-CLI** — eje §2.1.
- **TIER** — eje §2.2.
- **destino** — eje §2.3 (nombre concreto: paquete / módulo / interfaz / battery / integrador / borrar|cablear).
- **nota-identidad** — §2.4 si aplica; `—` si no toca scope/persistencia.
- **acción** — el paso concreto de separación (extraer contrato X, definir costura Y, empaquetar battery Z, borrar huérfano W…).

### 3.2 §Síntesis de la categoría
- **Costuras que implica** — lista de interfaces T2-COSTURA / T1-MOTOR que esta categoría exige (nombre + productor + consumidor).
- **Batteries que alimenta** — paquetes BATTERY que emergen de esta categoría (nombre + alcance).
- **CORE-GAPs** — findings donde el base/battery **debe** reproducir un comportamiento y **hoy no lo hace** (para el rollup `DEUDA-A.md`).
  Distinguir de DEUDA-B (higiene interna) y de divergencia deliberada 🔀 (lección 10: no inflar deuda).
- **Elementos de integrador** — findings que caen al integrador (T3 / CLI-ONLY-INTERFAZ / composición de batteries),
  cada uno con su detalle simétrico (§1.1). Se vierten a `00-INTEGRADORES.md`, **primero al CONTRATO BASE COMÚN**
  (obligación universal "must-be" de todo integrador), y **sólo lo genuinamente específico** a la capa por-integrador.

### 3.3 GATEKEEPER de cierre (obligatorio, MOSTRADO — L03/L04/L09). Sin esto la categoría NO está cerrada.

**Frase de rigor (lema de la etapa):**
> De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda; ninguna categoría
> se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin colocar —o colocado sin
> abrir, o desarrollado sólo del lado del base— es, exacto, el código que nacerá incompleto e inútil.

**Ledger — una fila por CADA finding del tracker `../NN.md`:**

| ID | TIER | destino | cara (base\|integrador\|ambas) | evidencia | detalle desarrollado | nota-identidad |
|---|---|---|---|---|---|---|

- **evidencia:** `tracker-leído` \| `ensamblador tramo archivo:L-R abierto` \| `no-requirió-código`.
- **detalle desarrollado:** `sí (6 campos L05)` \| `N/A (⛔/DEUDA-B)`.

**5 preguntas de cierre** (la respuesta honesta *es* la evidencia, o *es* un `⛔`):
1. ¿Se leyó **ÍNTEGRO** `../NN.md`? → sí + rango, o `⛔`.
2. ¿Reconcilia el conteo? findings en `../NN.md` = **X**; colocados = **X**; sin colocar = **0**. Si ≠ 0 → `⛔` (no hay cierre).
3. ¿Cada **✅/🔀 que afirma cableado** abrió el tramo del ensamblador (`archivo:L-R`), sin apoyarse en grep? → lista de tramos; cada afirmación sin tramo = `⛔` (no es ✅ todavía).
4. ¿La **cara integrador** quedó al MISMO detalle que la base? → sí; cualquier "→ integrador" a secas = `⛔`.
5. ¿**Doble filo** (L10)? Ningún ❌ disfrazado de 🔀; ninguna deuda inflada con lo que es de otra capa. → sí, o nómbralo.

**VEREDICTO** (obligatorio al pie): `✅ NADA PENDIENTE → A(N+1)` **o** `⛔ PENDIENTE(S): <lista con tipo + destino>`.
**Regla dura (L04):** una pregunta con `⛔` prohíbe el `✅ NADA PENDIENTE`; un pendiente de verificación NO se pliega dentro de "cabos con destino".

---

## 4. Reglas de método vigentes (puertas activas — PASO 0 de cada ciclo)

Método = lecciones de la skill `~/.claude/skills/analisis-comparativo-ab/lecciones/*.md` (el mirror
`learned_lessons/` está **RETIRADO**). Puertas que aplican con más fuerza en la SEPARACION:

- **L00** falsa economía — el atajo no ahorra, difiere con recargo.
- **L01** lectura íntegra — el tracker `../NN.md` de la categoría se lee **íntegro**; grep orienta, no sustituye.
- **L07** fuera de alcance ≠ trocear — un finding de esta categoría se clasifica **aquí**, no se difiere "a otra parte".
- **L09** cablear ≠ existir — costura declarada ≠ costura cableada; el cableado se verifica **leyendo el ensamblador 1→EOF**, nunca por grep.
- **L10** divergencia ≠ deuda — lo que B hace distinto **por diseño B** (agnosticismo, multi-sesión, headless) es 🔀, no CORE-GAP; no inflar ni ocultar deuda.
- **L11** validar completitud, no confirmar doc — el tracker previo es **hipótesis**; una fila ✅/🔀 sólo vale re-abriendo el código de B.

---

## 5. Glosario mínimo
- **base framework** — `agentic_runtime`: contratos T1 + costura de motor + mecanismo de orquestación + costuras. NO orquestación embebida.
- **battery** — paquete de implementación estándar OPCIONAL derivado del canónico. Se compone/sustituye, nunca sobreescribe.
- **costura (seam)** — interfaz que el base define y el integrador/battery rellena.
- **integrador** — producto sobre el base: `agentic_code` (fino/degenerado, compone batteries) · `agentic_assistant` (complejo, posee orquestación).
- **canónico** — `claude-code/src`. Referencia de **COMPLETITUD de capacidades**, NO de forma.
- **id opaco** — token de identidad/sesión que el runtime transporta pero **no interpreta**; el integrador lo atribuye.
