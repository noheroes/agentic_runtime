# OMISIONES — análisis integral del corpus

> **Qué es esto.** No es un ciclo de homologación ni una pasada del ledger. Es el censo de las **omisiones
> visibles** en todo el trabajo hecho hasta hoy (2026-07-28), su **impacto medido** y el **veredicto sobre la
> necesidad de retorno**, con **sanidad** y **completitud** como los dos ejes del criterio de *cerrado con
> honestidad*.
>
> **Pedido por el usuario**, verbatim: *«has un análisis integral para mostrar las ocurrencias de omisiones
> visibles en todo el trabajo, para medir impacto y necesidad de retornar para buscar sanidad y completitud
> como ejes del criterio para trabajo cerrado con honestidad»*.
>
> **Método de este documento.** Sólo entran ocurrencias con **cita en el corpus** — el propio corpus las
> declara, o el gate del usuario las forzó y quedaron escritas. **No hay estimaciones ni extrapolaciones.**
> Los conteos de líneas son `wc -l` de hoy; los de lecturas son `EVIDENCIA.log` (180 líneas), bajo su REGLA 1
> (*si una lectura no está en el log, para el gatekeeper no ocurrió*).

---

## 0. Lo que este análisis NO cubre — primero, antes que nada

1. **No cubre el corpus `HOMOLOGATION/*.md` (trackers, 10.293 L) como objeto de auditoría.** Sólo aparece
   como *denominador*: cuántos de sus pares se han reconciliado. **Sus omisiones internas —lo que los 18
   trackers dejaron fuera del canónico— no están medidas en ningún sitio.** Eso es la **tasa de DR-2**, y
   sigue sin medir (ver §5·O-11). Este documento **no la mide**: medirla exige abrir `claude-code/src`, que
   es la pasada P6″.
2. **No cubre el código del runtime.** Un CORE-GAP mal clasificado es una omisión de *contenido*; aquí se
   miden omisiones de *proceso* (lo que no se abrió) y sus consecuencias documentadas.
3. **No re-verifica ninguna de las ocurrencias históricas.** Se toman **tal como el corpus las dejó
   escritas**. Si un ciclo declaró «11 archivos declarados 1→EOF sin estarlo», eso entra como dato; no he
   re-contado cuáles eran los 11.
4. **La lista de ocurrencias VIVAS (§5) es un mínimo, no un total.** Sólo puedo enumerar las omisiones que
   alguien —yo, en un cierre honesto, o el usuario en un gate— **llegó a nombrar**. Una omisión que nunca
   se nombró no aparece aquí, por construcción. **El documento no puede acreditar que la lista esté
   completa**, y ése es precisamente el modo de fallo que mide.

---

## 1. Cobertura real del corpus `SEPARACION` (12.362 L, 31 archivos)

| | archivos | líneas | % |
|---|---|---|---|
| **Con lectura 1→EOF registrada en `EVIDENCIA.log`** | 15 | 5.694 | 46 % |
| **Nunca abiertos 1→EOF en ningún tramo** | 16 | 6.668 | **54 %** |

**Los 15 con 1→EOF:** `00-BLUEPRINT` · `00-INTEGRADORES` · `SEAMS` · `BATTERIES` · `DEUDA-A` · `DEUDA-B` ·
`PLAN` · `DECISIONES` · `01` · `02` · `03` · `04` · `05` · `09` · `17`.

**Los 16 sin 1→EOF:** `00-LEGEND`(158) · `SKELETON-REPORT`(138) · `A-CIERRE-P1`(309) ·
`A-CIERRE-LEDGER`(554) · `A-CIERRE-P4`(906) · y **11 de los 18 `NN-*.md`**: `06`(440) `07`(216) `08`(463)
`10`(487) `11`(394) `12`(483) `13`(432) `14`(504) `15`(358) `16`(284) `18`(542) = **4.603 L**.

> **Dato duro que ordena todo lo demás.** `DEUDA-A.md` —el rollup del que salen los ≈152 CORE-GAP, los 8
> keystones y las 7 piezas de identidad— declara en su propio perímetro: *«Ninguno de los 18 se leyó
> íntegro en ningún tramo de este ciclo»* y *«No leído en ningún tramo: `PLAN.md` íntegro · ningún tracker
> `../*.md` · `DEUDA-B-transversal.md`»*. **El documento que gobierna Fase B se escribió sobre una lectura
> parcial de los documentos que consolida.** Eso no es una sospecha externa: es su §0.1.

---

## 2. La especie: no son omisiones dispersas, es UNA con historia

Todas las ocurrencias, sin excepción, son la misma:

> **leer por tramos/`grep` donde correspondía 1→EOF, emitir el veredicto sobre esa lectura, y rotular el
> troceo con honestidad — presentando el rótulo como método.**

Y su rasgo definitorio, el que hace que sea un defecto de *proceso* y no un accidente: **el rótulo honesto
no repara nada.** `D-05` lo fija: *«etiquetar honestamente una lectura insuficiente no la convierte en
suficiente»*. Es `omisión-vestida-de-diseño` de la memoria `honestidad-no-defensiva` y la lección **L00
falsa-economía**.

**Un segundo rasgo, verificable en la tabla de §3: en NINGUNA de las 13 ocurrencias históricas el defecto lo
detectó mi propio gate.** Lo detectó el usuario preguntando *«¿hiciste EoF en todos los archivos?»*, o
apareció al abrir el archivo por otra razón. El gate auto-adversarial funciona **cuando se ejecuta**; el
defecto es que la primera redacción lo daba por ejecutado.

---

## 3. Ocurrencias HISTÓRICAS — cometidas, cazadas, corregidas (13)

Citas literales del corpus, en orden cronológico.

| # | dónde | qué se omitió | cómo se cazó |
|---|---|---|---|
| H-01 | **A2.5** | cierre inicial declaró leído lo que no lo estaba | *«se declaró leído sin serlo — retirado»* |
| H-02 | **ciclo 04** (`PLAN §7`) | *«la 1ª pasada NO hizo EOF en los ensambladores — `runtime.py`(435) sólo por `sed 283-335`; `agent_loop.py`(352)/`factory.py`(267)/`contracts/permissions.py`(33) SÓLO por grep, ni abiertos con Read = violación L08/L09»* | gate del usuario |
| H-03 | **ciclo 12** | *«el 1er cierre NO abrió `capabilities/contracts.py`»* | gate |
| H-04 | **ciclo 11** | *«reproche recurrente = 04/12»* | gate |
| H-05 | **ciclo 14** | *«reproche recurrente = 04/11/12, **4ª vez**»* + *«la auto-acreditación de rigor es en sí misma un tell de defensividad»* | gate |
| H-06 | **ciclo 17** | **5ª vez, y de CLASE NUEVA**: no se abrieron *tres docs del corpus SEPARACION sobre los que descansaba la clasificación* (`SEAMS`435, `00-INTEGRADORES`207, `07-events`216). Al abrirlos, **refutaron tres afirmaciones**. `00-BLUEPRINT`(185) siguió sin abrirse en ese ciclo | gate |
| H-07 | **ciclo 18** | *«**11 archivos declarados 1→EOF sin estarlo**»* + *«**2 de las 6 anclas de N4 apoyadas en grep**»*; la ✅ quedó **retractada** | gate |
| H-08 | **A3.DA §0.1** | *«la 1ª redacción declaraba “leídos 1→EOF este ciclo” los 5 transversales — **falso**»* | auto, al re-verificar |
| H-09 | **A3.DA §2.8** | *«todos los touchpoints cubiertos»* → real **9/11** | cotejo 1:1 contra `00-BLUEPRINT §2.1` |
| H-10 | **A3.DB §0.1** | *«titulaba “Corpus abierto ESTE ciclo (re-abierto, no heredado)”. **Eso es FALSO** y repite exactamente el defecto que `DEUDA-A §0.1` ya se había cazado»* | auto |
| H-11 | **A3.DB (1ª y 2ª redacción)** | cerró `⛔` con **3 pendientes remitidos**; al ejecutarse el tramo §7, **2 de los 3 no eran cuestiones abiertas sino decisiones no tomadas**, y una encubría un error propio | objeción del usuario |
| H-12 | **A3.CAT §8.4** | *«la versión previa remitía V1 y V4 a A-CIERRE justificándolo como “no decidible aquí”. **Era falso**: ambos se cerraban abriendo 1082 líneas»* | auto, al abrirlas |
| H-13 | **A-CIERRE·P4″** | la **columna de cruce** de los 6 pares cerrados se resolvió por tramos con grep | gate del usuario → **D-05** |

**Frecuencia:** 13 ocurrencias en 18 ciclos + 3 rollups + A-CIERRE. La numeración que el propio `PLAN §7`
lleva —*«4ª vez»*, *«5ª vez»*— es la prueba de que **la corrección por ciclo nunca cortó la reincidencia**:
sólo la cortaron los tres cambios **estructurales** (`EVIDENCIA.log`, `DECISIONES.md`, `D-05`).

---

## 4. IMPACTO — qué produjo realmente la omisión (15 consecuencias nombradas)

Ordenadas por severidad, no por fecha. **Clase A** = habría roto código en Fase B. **Clase B** = veredicto o
estado falso. **Clase C** = inventario incompleto.

| clase | # | consecuencia | fuente |
|---|---|---|---|
| **A** | I-01 | **`DB-23` estaba SOBRE-EXTENDIDA**: *«el base framework no posee estado global mutable»*, aplicada literal, **condena los 3 registries de extensión vivos** (`_STRATEGIES`, `RuntimeFactory._modes`, `StorageRegistry._backends`) — *«borrarlos rompería el punto de extensión que Filosofía B necesita»* | `DEUDA-B §7.1` |
| **A** | I-02 | **`RV-6`**: *«borrar `modes/` entero» borraría **`AgentMode`**, vocabulario T1 vivo* | `DEUDA-B §9` |
| **A** | I-03 | fuga de `ToolUseContext` a punto de fosilizarse en un contrato público al copiar `transcribe(audio, ctx)` | `BATTERIES` (cierre) |
| **A** | I-04 | **11 de las 12 entradas BORRAR de `DEUDA-B` siguen SIN auditar a nivel de símbolo** — sólo `DB-01` lo está: *«queda por auditar con ese criterio el resto de las entradas BORRAR»* | `DEUDA-B §8` |
| **B** | I-05 | **`CAT-h7`**: `CAT-DB-1` **retractado** — un rollup posterior re-tieró lo que `DEUDA-B §4·cabo 7` ya había fallado, **sin abrir §4** | `DEUDA-B §10` |
| **B** | I-06 | **`AC-h6`**: **`H-4` era PREMISA FALSA** — `deferred.py`(44 L) **no lee `agent_id` en ninguna línea**; el error vino de creer el comentario `:11-13`. *«RV-5 de nuevo: un docstring no es evidencia de cableado»* | `DEUDA-A §2.8` |
| **B** | I-07 | **`RV-5` (causal, no de inventario)**: tres módulos huérfanos **documentados como si estuvieran cableados** en su propio docstring (`observer.py:5`, `registry.py:4-5`+`:66`, `notification.py:5`) — *«explica por qué estos seams cruzaron 18 ciclos por categoría antes de caer en un rollup transversal»* | `DEUDA-B §9` |
| **B** | I-08 | **`CAT-h9`**: índice de `SEAMS` titulado **«(20)» listando 27 filas**; **`S12` sobre-declarada `existe-fiel`** mientras su propio cuerpo decía *«`to_llm` sin call-site»*; `S30`/`S31` cableados y fuera del índice | `SEAMS` (enmienda) |
| **B** | I-09 | **`AC-h2`**: reparto **12 BORRAR / 11 CABLEAR** era **error aritmético** (se descontó dos veces); real **12/12**. *«La cifra buena era la de §8; ésta era la mala, y estaba **antes** en el documento, que es el orden peligroso»* | `DEUDA-B §7.4` |
| **B** | I-10 | **`CAT-h8`**: la reconciliación se contó sobre **secciones** (el contenedor recorrido) en vez de **ítems** (la unidad repartida) | `BATTERIES §6` |
| **B** | I-11 | **`AC-h3`/`AC-h5`**: la *«delegación al integrador»* de `S21` **refutada** → **CORE-GAP `H-5`**; `process_background_notification` es **estructuralmente incapaz** porque `runtime.py:397` reasigna `session.messages` | `SEAMS §S21` |
| **B** | I-12 | **`§7.3`**: `ModelRequest` pasó de *CABLEAR-remitido* a **BORRAR** — *«una clase que ya mentía sobre el contrato»*; y `RV-4`: el tracker **ya decidía borrarla**, mi remisión la había perdido | `DEUDA-B §7.3`,`§9` |
| **C** | I-13 | **denominador de `DEUDA-B` era «17»** con tabla de 16 filas y **`SIG9`/`SIG13` sin fila jamás**. *«Un sub-ítem sin nombre es un sub-ítem que Fase B no implementa»* | `DEUDA-B §8·Q2` |
| **C** | I-14 | `storage/protocol.py`: **son 6 hermanos de `log_key`, no 4** (faltaban `agent_md_key`:57 y `ltm_key`:61) | `DEUDA-B §0.1` |
| **C** | I-15 | **censo de globales: son 7, no 6** — y *«el hallazgo no es el nº 7: es que la regla estaba mal formulada»* (= I-01) | `DEUDA-B §7.1` |

**Además, la única tasa medida:** en la reconciliación `tracker → SEPARACION` (P4″), **par 04 = 5 inversiones
sobre 23 fichas = 21,7 %**; agregado de los 6 pares cerrados ≈ **9-10 %**. Es la única cuantificación de
pérdida por salto de destilación que existe hoy, y **cubre 6 de 18 pares**.

### 4.1 · Lo que el impacto NO fue — contra-evidencia, con la misma cita

Sería deshonesto por exceso presentar sólo lo anterior. **Cada vez que se abrió el archivo omitido, las
anclas de código sobrevivieron:**

- `DEUDA-A §0.1` (re-verificación): 5 docs + 11 archivos re-abiertos, *«todas las verificadas resultaron
  exactas»* (≈20 anclas).
- `DEUDA-B §9` (tramo RV): *«**todas las anclas de código de §3.A/§3.B se confirmaron exactas**, y ninguna
  clasificación BORRAR/CABLEAR se invirtió. Los hallazgos son de **alcance** e **inventario**»*.
- **Par 09** (el más corrupto, donde `E5` estaba probada): **61 CONSERVADAS · 4 ENRIQUECIDAS · 4 COMPRIMIDAS ·
  1 INVENTADA · 0 perdidas**.

⇒ **El daño NO está distribuido uniformemente.** Está **concentrado en dos sitios y sólo dos**:

1. **las declaraciones de estado** (`✅`, «leído 1→EOF», los conteos y denominadores) — I-05..I-15;
2. **el ALCANCE de las órdenes de BORRAR** — I-01..I-04.

El *contenido técnico* (qué es un gap, dónde está la línea, qué hace el canónico) ha resistido cada
re-apertura. Esto **no atenúa** el problema: el sitio donde se concentra el daño es exactamente el sitio
donde Fase B leerá para escribir código, y una orden de borrado mal alcanzada es el único defecto de este
corpus que **destruye trabajo ya existente** en vez de dejar trabajo sin hacer.

---

## 5. Ocurrencias VIVAS — omisiones abiertas hoy (17)

`⬛` = bloquea Fase B · `🟧` = degrada el grado probatorio de algo ya cerrado · `⬜` = declarado y acotado.

| # | omisión viva | tamaño | estado | dónde se declara |
|---|---|---|---|---|
| **O-01** ⬛ | **Los 18 `NN-*.md` de SEPARACION nunca leídos íntegros por el rollup que los consolida.** Hoy: **11 de 18 sin 1→EOF en ningún tramo** | **4.603 L** | abierta | `DEUDA-A §0.1` · `AC-12`/`V7` |
| **O-02** ⬛ | **12 pares de P4″ sin reconciliar** (06·07·08·10·11·12·13·14·15·16·17·18) | 8.125 L tracker + 5.125 L SEPARACION | abierta | `A-CIERRE-LEDGER §3.2·d` |
| ~~**O-03**~~ ✅ | ~~**11 de las 12 entradas BORRAR sin auditar a nivel de símbolo**~~ (contramedida de `RV-6` aplicada sólo a `DB-01`) → **CERRADA 2026-07-28 por `R-1`**: las 12/12 llevan bloque `⚙ RV-6` en `DEUDA-B §3.A` con MUEREN·SOBREVIVEN·colateral, sobre 16 archivos de código abiertos 1→EOF (`EVIDENCIA.log` 181-191). **Saldo: 4 de 11 entradas habrían destruido algo vivo o roto el paquete aplicadas literalmente** — 2 correcciones de alcance (DB-03 `SignalType`, DB-24 `voice/protocol.py`), 3 colaterales no declarados (DB-06, DB-10, DB-16), 1 precondición dura (DB-26) | 11 entradas | **cerrada** | `DEUDA-B §3.A` + `§8` |
| **O-04** ⬛ | **`00-INTEGRADORES §2` = «Estado: ⬜ vacío»**. La **cara integrador del contrato no existe**: `agentic_code` 🟨 «grado-cero sembrado», `agentic_assistant` 🟨 con el detalle remitido a *A-CIERRE / Fase F* | 2 integradores | abierta | `00-INTEGRADORES §2` |
| **O-05** ⬛ | **10 de las 33 batteries (`B01-B07`,`B09-B11`) no existen en el runtime**; su columna «se borra del base» dice `n/a — no existe hoy`. *«no es un reparto verificado: es una casilla vacía por ausencia … **no acredito ninguna de las 10 como des-fusión correcta**»* | 10/33 | abierta | `BATTERIES §8.2·Q5` |
| **O-06** ⬛ | **`S28`/`S29`** (`Battery`+`compose()`, `RuntimeManifest`) = **BORRADOR NO VALIDADO** — son los dos seams sobre los que descansa Filosofía B entera | 2 seams | abierta | `SEAMS` |
| **O-07** 🟧 | **11 seams que A2 NO valida**: `S2`/`S3` (abort/auth) · `S6` (wire) · `S7` (on_progress) · `S8` fire-points STOP/POST · `S22`/`S23` · `S24` · `S25` delegates · `S30`/`S31`. *«Se listan aquí para que A2 no las dé por validadas (L09)»* | 11 | abierta | `SEAMS §5` = `SKELETON-REPORT §3` |
| **O-08** 🟧 | **`00-BLUEPRINT`(228) leído ANTES de una compactación** ⇒ evidencia **HEREDADA (T3)**, no propia | 228 L | abierta | `BATTERIES §0.1` · `AC-10`/`V2` |
| **O-09** 🟧 | **Los 10 tramos `§2.5`** igualmente pre-compactación = heredados | 10 tramos | abierta | `BATTERIES §0.1` · `AC-11`/`V3` |
| **O-10** ⬛ | **Canónico nunca abierto 1→EOF**: `query.ts`(1729) · `toolSearch.ts`(756) · `framework.ts`(308) · `LocalAgentTask.tsx`(682) | 3.475 L | abierta | `A-CIERRE-P1 c1/c2/c3` |
| **O-11** ⬛ | **La tasa de DR-2 (ausencia de origen `canónico → tracker`) sigue SIN MEDIR** ⇒ **el tamaño de P6″ es desconocido** y `§3.1·e` queda **suspendida** | desconocido | abierta | `A-CIERRE-LEDGER §3.2` |
| **O-12** 🟧 | **`DEUDA-A §5`: el rollup NO re-validó A↔B categoría por categoría** — *«fuera de ese perímetro la garantía sigue siendo **consolidación fiel de los 18 ciclos**, no **verificación independiente**»* | ≈152 gaps | declarada | `DEUDA-A §5` |
| **O-13** 🟧 | **2 de los 6 almacenes globales de `18·N4` no re-verificados** — *«no los afirmo ni los niego aquí»* | 2 | declarada | `DEUDA-B §0.2` |
| **O-14** 🟧 | **`client.py` y `agent.py` abiertos por tramo, no 1→EOF** (declarado en el propio gatekeeper Q3 de `DEUDA-B`) | 2 archivos | declarada | `DEUDA-B §8·Q3` |
| **O-15** 🟧 | **`00-LEGEND`(158) y los 18 tramos `§2.4`** declarados **HEREDADOS sin re-abrir** — sostienen la procedencia de `DB-16..DB-28` | 158 L + 18 tramos | declarada | `DEUDA-B §8·Q1` |
| **O-16** 🟡 | **`A-CIERRE-P1`(309), `A-CIERRE-LEDGER`(554→**596**), `A-CIERRE-P4`(906→**1096**) nunca 1→EOF** — son los documentos que **gobiernan la pasada en curso**. **2026-07-28: `A-CIERRE-P4` ✅ 1→EOF (1096 L) y `A-CIERRE-LEDGER` ✅ 1→EOF (573 L). Queda `A-CIERRE-P1` (309 L)** | ~~1.769~~ → **309 L** | **parcial (2/3)** | `EVIDENCIA.log:199` + §6.3 del ledger |
| **O-17** ⬜ | **`3 perfiles de composición` sin ningún integrador vivo que los ejerza** | 3 | abierta | `BATTERIES §8.3` · `V6` |
| **O-18** 🟧 | **Las 12 entradas CABLEAR (`DEUDA-B §3.B`) no están auditadas a nivel de símbolo.** Abierta **por `R-1`** (2026-07-28): al aplicar `RV-6` al lado BORRAR apareció que **4 de 11** órdenes estaban mal alcanzadas (36 %). `§3.B` se escribió con el mismo método y en la misma sesión, y nadie ha comprobado que sus órdenes *«cablear X»* nombren el símbolo correcto, el seam correcto y el punto de unión real (**L09: cablear ≠ existir**). No bloquea Fase B como `O-03` —un cableado mal alcanzado **no destruye**, deja algo sin conectar— pero degrada el grado probatorio de la mitad viva del rollup | 12 entradas | **abierta (nueva)** | `DEUDA-B §3.B` · esta pasada |

**Descargadas hoy (2026-07-28), bajo `D-05`:** `V5` (`PLAN.md` 1→134 — la etiqueta *«decisión, no omisión»*
era falsa) · `AC-08`/`V4′` (`DEUDA-B` 1→899, **el único transversal que ya había producido un error real por
leerse a trozos**) · la mitad de `AC-10`/`V2` (`00-INTEGRADORES` 1→243) · la **columna de cruce** de los 6
pares cerrados (`SEAMS`+`BATTERIES`+`DEUDA-A`+`DEUDA-B`+`00-INTEGRADORES` = 2.925 L 1→EOF).

**Resultado de esas descargas: 0 inversiones nuevas.** Las anclas cruzadas en los 6 pares cerrados por grep
resultaron **correctas al re-leerse íntegras**. El grado probatorio sube; el veredicto no cambia. Es
información — no exculpa el método, porque el resultado no se sabía **antes** de abrir.

---

## 6. Los dos ejes del criterio

### 6.1 · SANIDAD — *¿lo escrito es VERDADERO?*

Modo de fallo: **una afirmación falsa sobrevive al cierre y Fase B la ejecuta.** El peor caso concreto es una
orden de BORRAR mal alcanzada, porque **destruye** algo vivo en vez de omitirlo.

- **Ocurrencias que la dañan:** I-01 · I-02 · I-03 · I-04 (clase A) + I-05..I-12 (clase B).
- **Estado hoy:** **dos** órdenes de borrado mal alcanzadas ya se cazaron (`DB-23`, `RV-6`) y `DEUDA-B` lo
  escribe sin adornos: *«**es la segunda vez que este ciclo produce ese defecto**»* y *«**no puedo afirmar
  convergencia**»*. La contramedida existe (**`RV-6`: BORRAR se escribe a nivel de símbolo, con la lista
  explícita de lo que SOBREVIVE**) pero está aplicada a **1 de 12** entradas (**O-03**).
- **Veredicto del eje:** **⛔ NO SANO.** No por sospecha genérica: por una contramedida escrita, aceptada y
  **aplicada al 8 %** de su perímetro, sobre la clase de defecto que ya se produjo dos veces.
- **⚙ ACTUALIZACIÓN 2026-07-28 (`R-1` ejecutada) — el eje pasa a `🟡 SANO EN SU PERÍMETRO AUDITADO`.** `RV-6`
  está ahora aplicada a **12/12** entradas BORRAR. Y la sospecha no era genérica ni pesimista: **estaba
  subestimada**. De las 11 auditadas, **4 estaban mal escritas de forma que Fase B habría hecho daño**:
  `DB-03` (borra `SignalType`, el único vocabulario de pausa/reanudación del runtime — el clon exacto del
  caso `AgentMode` que originó `RV-6`), `DB-24` (borra la "superficie de voz" sin salvar
  `voice/protocol.py`, dejando a `battery_voice` sin protocolo que implementar), `DB-06` (omite el export y
  los ~25 productores ⇒ el paquete no importa) y `DB-16` (habría arrastrado `agent_md_key`/`ltm_key` por el
  mismo argumento "0 referencias" que mata a `log_key`, matando la persistencia de `AGENT.md` y de LTM).
  Más `DB-26`, cuya ejecución fuera de orden persiste bajo `"None/…"` **en silencio**.
  **Tasa observada: 36 % de órdenes de borrado defectuosas** (4/11), más 1 con precondición no escrita.
  El eje **no** vuelve a `✅`: sanidad plena exigiría además auditar el lado CABLEAR con el mismo criterio,
  que **no** se ha hecho y **no** está en `R-1..R-6` — se anota abajo como **O-18**.

### 6.2 · COMPLETITUD — *¿está TODO colocado?*

Modo de fallo: **un sub-ítem sin nombre es un sub-ítem que Fase B no implementa** (`DEUDA-B §8·Q2`, literal).
No rompe nada: **deja de existir en silencio.**

- **Ocurrencias que la dañan:** I-13 · I-14 · I-15 (clase C) + todo el perímetro vivo de §5.
- **Estado hoy:** la cara **base** está repartida y contada (`18=18=0`, `12/12`, 33 batteries, 29 seams,
  ≈152 CORE-GAP). La cara **integrador** —que es la mitad del contrato bajo Filosofía B— está **vacía**
  (**O-04**), y **10 de 33 batteries no tienen cara base que repartir** (**O-05**). Los dos seams que
  *sostienen* la filosofía son **borrador no validado** (**O-06**).
- **Veredicto del eje:** **⛔ NO COMPLETO**, y de forma asimétrica: **completo del lado del base, vacío del
  lado del integrador.** Es exactamente contra lo que advierte el lema del gatekeeper: *«lo que aquí quede
  sin colocar —o colocado sin abrir, o **desarrollado sólo del lado del base**— es, exacto, el código que
  nacerá incompleto e inútil»*.

---

## 7. NECESIDAD DE RETORNO — veredicto

**Sí, hay que retornar.** No como acto de prudencia sino porque **hay trabajo identificado, acotado y
pendiente**, y `D-03` ya prohíbe cerrar con pendientes cuya única condición sea *no lo he abierto*.

### 7.1 · Retorno OBLIGATORIO antes de Fase B (bloquea)

| orden | qué | por qué **este** orden | coste |
|---|---|---|---|
| ~~**R-1**~~ ✅ | ~~**O-03** — auditar las 11 entradas BORRAR a nivel de símbolo, con lista de lo que SOBREVIVE~~ **HECHA 2026-07-28.** Rendimiento: **4/11 defectuosas + 1 con precondición no escrita**. Coste real: 16 archivos de código 1→EOF (≈1.100 L) + 1 censo-localizador. La predicción *«es barato»* se cumplió; la predicción implícita *«y probablemente confirmatorio»* **no** | **primero, y es barato**: es el único defecto que **destruye código**, ya se produjo 2/2 veces al buscarse, y la contramedida está escrita. Ninguna de las otras 16 omisiones tiene esa combinación | 11 entradas sobre `DEUDA-B §3.A` ya leído |
| **R-1b** | **O-18** — misma auditoría de símbolo sobre las **12 entradas CABLEAR** de `§3.B` | **abierta por el resultado de R-1**: si el lado BORRAR, escrito con el mismo método, dio 36 % de órdenes mal alcanzadas, asumir que el lado CABLEAR está sano es exactamente la inferencia que `RV-6` prohíbe. Va **después** de R-2/R-3 sólo porque no destruye | 12 entradas sobre `DEUDA-B §3.B` ya leído |
| **R-2** | **O-02** — los 12 pares P4″ | es la pasada en curso; **es también el vehículo de O-01** (reconciliar el par obliga a abrir el `NN-*.md`) | 13.250 L |
| **R-3** | **O-01** — se **descarga con R-2**: 11 de los 18 se abren al reconciliar sus pares | no es una pasada aparte | (incluido) |
| **R-4** | **O-11** — medir la tasa de DR-2 sobre una muestra | mientras no se mida, **P6″ es de tamaño desconocido** y ningún plan de Fase B es dimensionable | muestra, no censo |
| **R-5** | **O-04** + **O-05** + **O-06** — cara integrador, las 10 batteries inexistentes, `S28`/`S29` | son la **mitad ausente** del contrato; sin ellos Fase B escribe base sin saber contra qué compone | Fase F / A-CIERRE |
| **R-6** 🟡 | **O-16** — los 3 docs de A-CIERRE 1→EOF. **2 de 3 hechos (2026-07-28):** `A-CIERRE-P4.md` **1→EOF 1096 L** (`EVIDENCIA.log:199`) y `A-CIERRE-LEDGER.md` **1→EOF 573 L** (abierto para escribir `§2.2`). **FALTA `A-CIERRE-P1.md` (309 L)** | gobiernan la pasada en curso y **nunca se abrieron enteros**. Es el mismo defecto de H-06 (*los docs del corpus son fuente primaria igual que el código*) aplicado al ledger que dirige el trabajo. **Confirmado por el hecho:** abrir el ledger entero destapó una **colisión de identificador** (`AC-10` rotulando dos cosas distintas) que ninguna lectura por tramos habría cruzado — **resuelta por renombrado a `AC-12` el 2026-07-29** (`A-CIERRE-LEDGER §2.1` · `DECISIONES D-06` · `EVIDENCIA.log:201`) | ~~1.769 L~~ → **309 L restantes** |

### 7.2 · Retorno NO obligatorio — se declara y se vive con ello

- **O-07** (11 seams sin ejercitar): declarado explícitamente *para que A2 no los dé por validados*. Se
  ejercitan **cuando exista el integrador**, no antes. **No es omisión encubierta: es alcance declarado.**
- **O-10** (canónico 1→EOF): **`D-01` lo gobierna** — el insumo de esta fase son los trackers. Sólo se abre
  por excepción, y `R-4` dirá cuánta excepción hace falta. **Reabrirlo por sistema sería tirar la fase 1
  entera.**
- **O-08 · O-09 · O-12..O-15** (evidencia heredada / perímetro declarado): degradan el grado probatorio, no
  lo anulan. Se re-abren **cuando algo dependa de ellos**, y sólo entonces.

### 7.3 · Lo que NO hace falta rehacer

**Nada del contenido técnico ya anclado.** §4.1 es la prueba: en cada re-apertura las anclas de código
resultaron exactas y ninguna clasificación BORRAR/CABLEAR se invirtió. **Este documento no propone una
re-auditoría general del corpus, y sería un error proponerla** — el defecto no está en el contenido, está en
las declaraciones de estado y en el alcance de las órdenes. Se repara donde está.

---

## 8. Veredicto final

> **⛔ El trabajo NO está cerrado con honestidad — y la razón no es que las omisiones estén ocultas: es que
> están CENSADAS, DECLARADAS y ABIERTAS.**
>
> Los dos ejes fallan por motivos distintos y no intercambiables:
> - **Sanidad ⛔** — una contramedida contra el defecto más destructivo (borrar algo vivo), ya producido dos
>   veces, aplicada a **1 de 12** entradas.
> - **Completitud ⛔** — la cara base está repartida y contada; la **cara integrador está vacía**, y 10 de 33
>   batteries no tienen cara base que repartir.
>
> **Lo que SÍ está sano:** el mecanismo de detección. `EVIDENCIA.log`, `DECISIONES.md` y `D-05` son los tres
> únicos cambios que cortaron una reincidencia de 13 ocurrencias en 18 ciclos, y son estructurales, no
> promesas de conducta. Este documento existe porque el corpus, cuando se abre entero, **dice la verdad sobre
> sí mismo**: cada una de las 17 omisiones vivas está escrita por el ciclo que la cometió.
>
> **El riesgo real ya no es la omisión que no se ve. Es la omisión que se ve, se nombra, y se remite.**
> `A3.CAT` remitió `V1`/`V4` *«por prudencia»* y ambos se cerraban abriendo 1.082 líneas; al abrirlas
> salieron **cinco hallazgos y una fuga de identidad a punto de fosilizarse en un contrato público**. Ése es
> el precedente que gobierna: **el pendiente que se remite cuando la única condición es *no lo abrí* no es
> prudencia.**

---

*Generado 2026-07-28. Base de lectura: `EVIDENCIA.log` 180 líneas; `SEPARACION/*.md` 12.362 L
(`wc -l`); `HOMOLOGATION/*.md` 10.293 L. Los 5 rollups transversales (2.925 L) leídos 1→EOF este día bajo
`D-05`.*
