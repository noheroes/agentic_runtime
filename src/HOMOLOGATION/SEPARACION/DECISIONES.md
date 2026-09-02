# DECISIONES — registro append-only de decisiones del USUARIO

> **Por qué existe.** `EVIDENCIA.log` hace que una **lectura** sobreviva al `/clear` (*si no está en el log,
> no ocurrió*). **No había equivalente para una DECISIÓN del usuario.** Consecuencia observada el 2026-07-27:
> una decisión tomada **antes de iniciar la fase SEPARACION** —«los insumos ya consumieron el canónico; la
> fase 2 se hace sobre ellos, no volviendo al canónico»— llegó a A-CIERRE **como si no existiera**, se reabrió
> como pregunta y se llegó a presupuestar ≈86.237 L de relectura canónica contra ella (`A-CIERRE-LEDGER §3.1`,
> corregido en `§3.2`).
>
> **Regla:** una decisión del usuario que gobierne el método o el alcance **se escribe aquí en el momento en
> que se toma**, con su consecuencia operativa. *Si una decisión no está aquí, el siguiente ciclo la volverá a
> preguntar* — y preguntar de nuevo lo ya decidido no es prudencia: es pérdida de trabajo pagado.
>
> **Formato:** `fecha · pregunta que la originó · DECISIÓN · consecuencia operativa · dónde se aplica`.

---

## D-01 · El insumo de la fase SEPARACION son los trackers, NO el canónico

- **Fecha:** antes de iniciar la fase 2 (`SEPARACION`). *Reconstruida y registrada el 2026-07-27 tras la
  objeción del usuario: «se supone que no recurrimos a canónico porque la primera fase, que fue escribir los
  insumos, había consumido las 86.237 líneas de canónico y las volcó en el documento».*
- **Pregunta que la originó:** ¿la fase 2 vuelve al canónico o trabaja sobre los insumos ya destilados?
- **DECISIÓN:** trabaja **sobre los insumos**. La fase 1 (`HOMOLOGATION/NN-*.md`, 10.291 L, 365 archivos
  `.ts/.tsx` citados) ya consumió el canónico bajo el mandato de `README §Metodología·4` (*«las contrapartes
  canónicas se leen íntegras … la superficialidad es el modo de fallo #1»*). La fase 2 destila **eso** en un
  documento maestro que guíe la reingeniería.
- **Consecuencia operativa:** el canónico se abre **por excepción**, sólo donde el tracker calle sobre un
  sub-comportamiento — nunca como relectura sistemática.
- **Dónde se aplica:** `A-CIERRE-LEDGER §3.2` (deroga el presupuesto canónico de `§3.1·b`); partición
  **P4″–P7″**.
- **Violada una vez:** 2026-07-27, en `§3.1`. Causa: nunca abrí `HOMOLOGATION/NN-*.md`, sólo la capa
  `SEPARACION` que los destila. Detectada por el usuario, no por el gate.

## D-02 · El ancla canónica es una TABLA DE COMPORTAMIENTOS, no un puntero

- **Fecha:** 2026-07-27 (P1 → rediseño).
- **DECISIÓN:** una ficha anclada exige la enumeración de comportamientos de su contraparte, como las 14 filas
  de `resumeAgent.ts` en `A-CIERRE-P1 · AC-05`. Un puntero `archivo:línea` **no** acredita nada.
- **Consecuencia operativa:** ninguna unidad entra en Fase B sin esa tabla.
- **Matiz introducido por D-01:** la tabla se obtiene **del tracker** cuando el tracker baja a ese nivel
  (p. ej. `09·E5`, que ya contenía derivar-vs-almacenar completo); se va al canónico sólo si no.

## D-03 · Nada se cierra con pendientes remitidos a una pasada propia

- **Fecha:** 2026-07-27 (objeción del usuario en P0: *«no cerrar con pendientes, para no tener errores al
  ensamblar»*; reiterada en el tramo de rectificación).
- **DECISIÓN:** en el ciclo de cierre **no existe «más adelante»**. Un pendiente cuya única condición es *no lo
  he abierto* no es un pendiente: es una lectura que falta.
- **Consecuencia operativa:** L04 se aplica sin excepción; la precedencia declarada es un **mínimo de orden**,
  nunca un permiso para no leer.

## D-04 · Alcance de P4–P7: anclaje, no relectura de coherencia interna

- **Fecha:** 2026-07-27 (`AskUserQuestion` — «Girar P4–P7 al canónico»).
- **DECISIÓN:** los 18 `NN-*.md` de `SEPARACION` se recorren para **anclar cada unidad**, no para releerse
  1→EOF buscando coherencia interna.
- **Corregida por D-01:** el anclaje se resuelve **contra el tracker de origen**, y la pasada se convierte en
  **reconciliación `tracker → SEPARACION`** (`§3.2·d`, P4″).

## D-05 · La columna de CRUCE se lee 1→EOF, igual que las dos caras. No hay presupuesto de tokens

- **Fecha:** 2026-07-28.
- **Pregunta que la originó:** el usuario, tras el cierre del par 04: *«quien paga por los tokens soy yo y no te
  he dicho nada al respecto; siempre, repito siempre, tienes tendencia a falsos ahorros cuando lees por tramos
  con grep en lugar de una lectura EOF real; esto distorsiona y desprestigia tu trabajo, a pesar de que pueda
  ser legítimo».*
- **DECISIÓN:** **no existe restricción de coste en este esfuerzo.** La economía de contexto **no es un criterio
  de método** y no puede invocarse —ni implícitamente— para sustituir una lectura íntegra. Las dos caras del par
  ya se leían 1→EOF; **la tercera columna (los cruces) queda sujeta a la misma regla.**
- **Consecuencia operativa:**
  1. Los **5 rollups transversales** —`DEUDA-A` 699 · `DEUDA-B` 899 · `BATTERIES` 546 · `SEAMS` 539 ·
     `00-INTEGRADORES` 242 = **2.925 L**— se leen **1→EOF una sola vez**, antes de abrir el par 06, y quedan
     disponibles para los 12 pares restantes. Coste amortizado por par ≈ 244 L **frente a los ~8 grep dirigidos
     por par que se venían pagando**: el troceo era además más caro en el agregado, no sólo peor.
  2. El `NN-*.md` **dueño del destino** de una ficha se lee 1→EOF antes de emitir el veredicto de esa ficha.
  3. `grep` queda reducido a **localizador** (patrón 3, encabezados, sondas O(1)). **Nunca a fuente de un
     veredicto.**
  4. Prohibido el rótulo *«tramos dirigidos con rango — no los declaro íntegros»*. Etiquetar honestamente una
     lectura insuficiente **no la convierte en suficiente**: es `omisión-vestida-de-diseño`.
- **Deuda que abre hacia atrás:** los **6 pares ya cerrados** (09·01·05·02·03·04) resolvieron su columna de
  cruce por tramos. Sus veredictos de cruce son de **grado probatorio inferior** al de las dos caras. Queda
  declarado como pendiente explícito de `A-CIERRE`; la relectura de los 5 rollups 1→EOF es también la
  verificación retroactiva barata de esos 6.
- **Dónde se aplica:** todo P4″ restante y las pasadas P2/P5″–P7″.

---

## D-06 · Una binaria que la evidencia ya resuelve se ejecuta, no se eleva al usuario

- **Fecha:** 2026-07-29.
- **Pregunta que la originó:** al cerrar el par 06 informé la colisión `AC-10`/`AC-12` como *«decisión tuya
  pendiente: renombrar o no»*, y escribí en `A-CIERRE-LEDGER §2.1` el encabezado *«NO la resuelvo por mi
  cuenta … corregirlo o no es decisión del usuario»*. El usuario respondió: *«se tendría que renombrar si como
  indicas existe la evidencia que la referencia real es 12 y no 10, incluso no deberías trasladarme la
  responsabilidad de aprobar algo que no tiene más que una decisión binaria».*
- **DECISIÓN:** cuando un hallazgo tiene **una única resolución fijada por la evidencia que yo mismo acabo de
  producir**, se **ejecuta y se registra**. No se convierte en pregunta. Elevarlo al usuario no es prudencia:
  es devolverle el coste de un defecto propio y dejar el corpus con el defecto dentro mientras espera.
- **Criterio de reparto (el que sí decide el usuario vs. el que no):**
  1. **Ejecuto yo:** corrección de un identificador, un recuento, una cita o un rótulo **cuando la evidencia
     leída 1→EOF fija un único valor correcto**. Aunque toque documentos ya escritos.
  2. **Ejecuto yo, dejando traza:** cualquiera de lo anterior sobre un artefacto append-only
     (`EVIDENCIA.log`) — la sustitución se aplica **sólo en el campo defectuoso** y se **añade una línea nueva**
     que enumera qué líneas se tocaron y por qué. La trazabilidad queda **mayor**, no menor. El «no toco esto
     para no perder trazabilidad» era falso: lo que pierde trazabilidad es dejar dos referentes vivos.
  3. **Pregunto:** sólo cuando la evidencia admite **más de un resultado defendible** (alcance, prioridad,
     criterio de corte, qué se declara fuera de alcance) — es decir, cuando la respuesta cambia **qué trabajo
     se hace**, no **cómo se rotula el ya hecho**.
- **Tell prohibido añadido** (a los de `honestidad-no-defensiva`): **`binaria-delegada`** — presentar como
  decisión del usuario algo cuya única alternativa es dejar un defecto acreditado sin corregir. Es una forma
  de `omisión-vestida-de-diseño`: el defecto sigue ahí, pero ahora con la responsabilidad transferida.
- **Aplicación inmediata:** renombrado `AC-10` → `AC-12` en `EVIDENCIA.log:192-200` (8 líneas, traza en
  `:201`), `A-CIERRE-LEDGER §2.1`, `homologation-effort.md` y `MEMORY.md`.
- **Dónde se aplica:** todo lo que reste de A-CIERRE y las fases siguientes.

---

## D-07 · 2026-07-29 — «Declarado» no es «pagado»: la deuda de lectura BLOQUEA el cierre

**Pregunta / detonante.** El usuario, tras el cierre del par 07: *«continuas indicando que podemos
seguir avanzando a pesar que declaras explicitamente que no has hecho EOF que es un requerimiento
de rigor, como no hay un castigo por lo que haces, lo haces de manera sistematica»*.

**El defecto, nombrado sin adorno.** Las reglas `DEUDA-A §0.1` («o se re-abre, o se declara
heredada») y la §Honestidad-primero se estaban usando **al revés de su propósito**: como *permiso*
para avanzar con la deuda declarada, en vez de como *registro* de una deuda que hay que pagar.
Declarar la omisión en negrita y a continuación emitir el enunciado de retoma convierte la puerta de
cierre en un trámite: el pendiente queda perfectamente documentado **y perfectamente sin hacer**.
Es la forma más cara del tell `omisión-vestida-de-diseño`, porque la declaración misma sirve de
coartada. Reincidencia: 4 ciclos (A3.DA · A3.DB · A3.CAT · P4″-par-07) sobre el MISMO ítem — las 12
lecciones del PASO 0.

**Ya estaba escrito y no lo vi por no re-abrirlo:** la lección `00:33-35` tipifica este flujo exacto
(*«entrego superficial → me reprochan → lo hago bien»*) como **externalizar el control de calidad al
usuario**, y `04·Sin escotilla` es explícita: *«si hay ≥1 pendiente de VERIFICACIÓN, el veredicto NO
puede ser ✅ NADA PENDIENTE»*. El cierre del par 07 listó 5 pendientes de verificación y aun así
propuso avanzar al par 08 ⇒ **era inválido por la propia lección**, no por severidad ni por criterio.

**DECISIÓN.**
1. **Una deuda de LECTURA no se declara: se paga o el ciclo no cierra.** Si la lectura pendiente es
   ejecutable en la ventana actual, se ejecuta ANTES del cierre. «Heredada» queda reservada a lo que
   es materialmente imposible re-abrir (fuente perdida), NO a lo que es barato y no apetece.
   Referencia de coste real: el PASO 0 completo son **547 líneas**; llevaba 4 ciclos difiriéndolo.
2. **Prohibido emitir enunciado de retoma a la unidad siguiente con ≥1 pendiente de VERIFICACIÓN
   abierto en la unidad actual.** El enunciado de retoma es la forma que toma `✅ NADA PENDIENTE` en
   este proyecto; con pendientes de verificación, lo que se emite es la **lista de lo que falta para
   poder cerrar**, y el ciclo siguiente empieza ahí, no en la unidad siguiente.
3. **PASO 0 al ABRIR, no al cerrar.** Las 12 lecciones se re-abren 1→EOF como PRIMERA acción de cada
   ventana que vaya a producir producto, con línea en `EVIDENCIA.log` escrita al leer. Una ventana
   sin esa línea no puede escribir veredicto.
4. **Tell prohibido nuevo** (a los de `honestidad-no-defensiva`): **`declaración-como-pago`** —
   enunciar una omisión con precisión y avanzar igual, tratando la nitidez de la confesión como si
   saldara la obligación. El test: *¿la declaración cambió lo que hago a continuación?* Si no, es
   coartada.

**Consecuencia operativa inmediata.** PASO 0 pagado hoy (`EVIDENCIA.log:213`, 12/12 archivos 1→EOF,
547 L). El **veredicto del par 07 NO se altera** (`⛔ RECONCILIADO, no CERRADO`), pero el **cierre de
la ventana sí**: no hay enunciado de retoma al par 08 hasta que sus pendientes de verificación estén
en cero o sean materialmente inejecutables y dicho por qué.

**Dónde se aplica.** Todo lo que resta de A-CIERRE y las fases B–F. Es regla de gobierno, no de estilo.

---

## `D-08` — Una controversia se resuelve LEYENDO EL CANÓNICO, no razonando (2026-07-29)

**Disparador:** el usuario, textualmente — *«las controversias las puedes facilmente resolver mirando el codigo
de canonico, si es que hay una desviación, no es que te parezca mas logico a ti, sino que es lo que realmente el
canonico hace.»* Diagnóstico aceptado sin matizar. Yo había cerrado el par 08 con **dos** actos del mismo vicio:

- **Escalé una binaria que el canónico ya tenía resuelta.** `CG-SIG-10` («¿`Protocol` con `.aborted` o `is_set()`
  en los providers?») lo elevé a `16` invocando `D-06·3` («dos ramas defendibles»). **No había dos ramas:** el
  canónico usa `AbortSignal` nominal con `.aborted` (**119** usos), `addEventListener('abort')` (**26**) y
  `.reason` propagable; `asyncio.Event` no puede sostener `CG-SIG-1`/`7`/`8`. **Coste de comprobarlo: 6 archivos.**
- **Emití una decisión razonando y salió mal.** El watchdog de `SEAMS §S24`: escribí *«señal y deadline son
  disparadores distintos ⇒ `reason='timeout'` como cuarta razón del enum»*. El canónico **fusiona el deadline
  dentro de la señal** (`createCombinedAbortSignal`) y **no tiene enum**: `.abort(reason)` toma valor abierto.
  Y **usé una media verdad como corroboración** (`01·§1.1`, *«el canónico cancela por abort, no por timeout
  per-task»*): cierto lo de per-task, falso lo de que no convierta tiempo en abort.

### La regla

1. **Antes de declarar una binaria «de dos ramas defendibles» (`D-06·3`), hay que haber ido al canónico.**
   `D-06·3` es para binarias que el canónico **no** decide (política del integrador, orden de construcción,
   nombres). Si el punto en disputa es **qué comportamiento tiene el sistema**, el canónico ya votó y elevarlo es
   una escotilla. **`D-06·3` queda subordinada a `D-08`:** no se invoca sin decir qué se leyó del canónico y por
   qué no basta.
2. **Una decisión de diseño emitida sin cita del canónico nace como HIPÓTESIS**, y se marca como tal. Vale
   emitirla —a veces el canónico calla— pero no vale presentarla con el mismo grado probatorio que una leída.
3. **Y si el canónico calla, eso también hay que ir a comprobarlo y decirlo**: *«no hay contraparte»* es un
   hallazgo verificable, no un supuesto. Cuando se afirme, se nombra el barrido que lo sostiene.
4. **Tell prohibido nuevo: `elevar-en-vez-de-leer`** — convertir en pregunta abierta (o en delegación a otro par)
   algo que 10 minutos de lectura del canónico cierran. Test: *¿fui al canónico antes de decir que hay dos ramas?*
   Si no, la binaria es mía, no del corpus. Hermano de `declaración-como-pago` (`D-07·4`): allí la confesión
   sustituía al trabajo; aquí la delegación sustituye a la lectura.

### Alcance retroactivo

Todo `🔀` cerrado como *«divergencia por diseño»* y todo pendiente elevado por `D-06·3` en los 9 pares ya
reconciliados **se re-abre a la pregunta de `D-08`**: *¿se leyó el canónico antes de cerrarlo así?* Se barre en
**`AC-32`**. Precedente material de que la tasa no será cero: `07·B2` (`parent_tool_use_id`) ya fue invertido por
esta misma vía, y `08·S12` era un `🔀` que delegaba en una categoría que ya había dictaminado en contra.

**Dónde se aplica.** Todo lo que resta de A-CIERRE y las fases B–F. Es regla de gobierno, no de estilo.

---

## `D-09` — Un artefacto de ESTADO no admite entradas de LOG (2026-07-30)

**Disparador.** El usuario: *«habría que trazar una estrategia para poder partir los documentos demasiado
extensos en archivos individuales mucho más manejables, porque han crecido exponencialmente»*, y acto seguido
—acotando mi propuesta, que era partir medio corpus— *«los únicos problemáticos son `PLAN.md` y
`homologation-effort.md`»*. **El motivo que dio es el que manda:** *«si seguimos avanzando y reprocesando para
alcanzar cierre, cuando se tenga que refactorizar `agentic_runtime` será imposible materialmente hacerlo.»*

**Lo que la medición demostró, y desmontó mi propia propuesta.** Ninguno de los dos era «un documento largo».
Los dos eran **un log incrustado en un artefacto que debía ser corto y de estado**:

| | masa total | de la cual, log embebido |
|---|---|---|
| `PLAN.md` | 133 L · 114.062 ch | **92.460 ch (84 %)** en 16 viñetas `- [x]` del `§7`, de 1.575 a **13.017 ch cada una** |
| `homologation-effort.md` | 925 L · 386.936 ch | **324.794 ch (84 %)** en `:20-386`, historia que el propio archivo **ya declaraba HISTORIA** — incluida `:383`, **19.675 ch en UNA línea** |

El plan de verdad son 17.602 ch y estaba sano. El estado vivo de la memoria son 45.019 ch y estaba sano. Lo que
había crecido exponencialmente no era el documento: era **el log dentro del documento**.

### La regla

1. **Un artefacto de ESTADO no admite entradas de LOG.** El log ya tiene tres casas —`EVIDENCIA.log` (lecturas),
   `PROGRESS.md` (ciclos), `A-CIERRE-LEDGER §6` (bitácora)—. Cada informe de ciclo que aterriza en `PLAN.md` o en
   la memoria está en la cuarta, y se paga entero en cada ventana que abra el artefacto.
2. **Una entrada de checklist es UNA línea:** ciclo · fecha · documento producido · veredicto. Si crece, el log se
   ha vuelto a meter donde no va.
3. **Mover/congelar ≠ podar, y no se confunden.** *Mover* es mecánico, verificable byte a byte y sirve al trabajo
   **en curso**. *Podar* (borrar lo duplicado) exige verificar que la otra copia existe y está íntegra, y por eso
   **se difiere a cuando el trabajo esté terminado**. Criterio del propio usuario, aplicado también al descarte de
   la idea de vectorizar/grafo: *«es útil si hubiéramos terminado el trabajo y de sólo lectura; para trabajo no
   terminado no tiene valor»*.
4. **Un corte se autoriza por PRUEBA DE IDENTIDAD, no por relectura.** Partir un documento de 200 k ch obligaría a
   releerlo 1→EOF por la regla de «no se escribe sobre lo que no se ha abierto». Excepción admisible y **única**:
   si la concatenación de las partes reproduce el original **byte a byte** y el `sha256` queda escrito en las dos
   caras, no se ha perdido nada y la prueba es reproducible por cualquiera. **No vale para reescrituras,
   resúmenes ni reordenaciones: sólo para cortes literales.**
5. **El corte deja redirector.** Las citas vivas (`§N`, `PLAN.md:NNN`) no se reescriben en masa —eso es la parte
   arriesgada—; el archivo de origen conserva una cabecera-puntero corta que traduce. Abrir el puntero es gratis.

### Aplicación inmediata (2026-07-30)

- `homologation-effort.md` **925 L / 386.936 ch → 569 L / 52.537 ch**; `:20-386` íntegro y sin tocar en
  `homologation-history-2026-07.md` (CONGELADO/T3, no se lee en la retoma).
  `sha256(original) = 2e02fb3100825bd42c523752df94194386aded42928d239db4af8eadb93650d5`.
  **Efecto: la memoria vuelve a ser abrible 1→EOF**, cosa que `D-07` había tenido que declarar materialmente
  imposible en los pares 10 y 11.
- `PLAN.md` **133 L / 114.062 ch → 111 L / 13.591 ch**; `§7` íntegro en `PLAN-CHECKLIST.md`.
  `sha256(original) = a53ee1247676c458c177a05c5f05a211fa14bb8c2e2ba7db0e467f0351e2ef4c`.
- **Descartado por el usuario:** partir `A-CIERRE-P4.md` y los demás (se llegó a cortar en 12 archivos y **se
  revirtió**, con el original intacto y su hash sin cambiar). También descartado el índice vectorial/grafo.

**Dónde se aplica.** Todo lo que resta de A-CIERRE y las fases B–F. Es regla de gobierno, no de estilo.

---

## `D-10` — Se refactoriza por TRAMOS de capacidad, no con el ledger en cero (2026-07-30)

**Disparador.** El usuario, tras cerrar el debate de qué está cerrado y qué no: *«lo que toca es traducir a
características y capacidades listas para refactorizar y poner una línea de corte para que el resto permanezca
como nuevo top y emprendamos el camino del primer tramo de la refactorización por escrito para que sirva de
guía … cuando se alcance el 100 % de tramo probado y operativo retomamos desde la línea de corte en tramos
cortos de reconciliación y reducimos el universo de los ajustes en la documentación conforme vamos
progresando».*

**Qué deroga.** `PLAN.md §4·A-CIERRE` fija *«Fase B no abre hasta que el ledger esté en 0»*. **Queda derogado.**
La razón no es impaciencia, es aritmética medida: en los 5 últimos pares reconciliados el ledger **abrió 22
ítems y cerró 1** (`AC-26`) ⇒ el gate «ledger en 0» no es una condición que se acerque, y condicionar la
construcción a él es condicionarla a un punto que la propia evidencia dice que no llega.

**DECISIÓN.**
1. **La construcción se organiza en TRAMOS de capacidad.** Cada tramo se define por **grado probatorio**, no
   por número de ciclo: entra lo validado **corriendo** (G1) y lo leído 1→EOF (G2, marcado como tal); no entra
   lo inferido/heredado/resuelto por `grep` (G3) — que es exactamente el conjunto que el corpus ha tenido que
   reabrir. **Única excepción admitida: una transversal cuyo aplazamiento cambie la firma de todo lo demás**
   (en el tramo 1, el hilo de identidad).
2. **Un tramo cierra con pruebas E2E REALES en verde a la vez**, incluida al menos una **NEGATIVA** que
   acredite que las costuras son *load-bearing*. Un verde sin la negativa no cierra tramo (`L09`: el catálogo
   verde da falsa confianza).
3. **La LÍNEA DE CORTE es el nuevo top del trabajo restante**, y sus unidades se difieren **enteras y
   nombradas** (`L07`). Prohibido cortar por «núcleo dentro / resto fuera» de una misma unidad.
4. **La deuda documental deja de ser un gate global y pasa a ser local al tramo.** El par `P4″` de una unidad
   se reconcilia **cuando esa unidad entra en un tramo**, no antes. El universo de ajuste documental se reduce
   en cada vuelta en vez de crecer.
5. **Lo que se descarta al cerrar un tramo es su deuda de reconciliación documental, NO los 18 trackers de
   fase 1** (6531 L): son el único sitio donde vive la enumeración de comportamientos del canónico y los
   tramos siguientes se anclan contra ellos (`D-01`/`D-02`).

**Consecuencia operativa inmediata.** Se escribe `SEPARACION/TRAMO-1.md` (10 capacidades con los 6 campos de
`L05` + línea de corte + gate E1–E9). `A-CIERRE` **no se cancela**: sus 39 ítems abiertos quedan en la línea de
corte (`TRAMO-1 §3·D`) y se pagan por tramos.

**Dónde se aplica.** Fases B–F. Es regla de gobierno, no de estilo.

---

## `D-11` — La identidad viaja por DOS cables distintos, y no se deriva uno del otro (2026-07-30)

> ⚠ **Honestidad de origen: esto NO es una decisión del usuario.** Es una resolución de EJECUCIÓN tomada por
> `D-06` (*una binaria que la evidencia ya resuelve se ejecuta, no se eleva*) durante el tramo 1, y se escribe
> aquí **sólo** porque es exactamente el tipo de cosa que el siguiente `/clear` volvería a preguntar. El
> usuario puede revocarla; mientras no lo haga, gobierna la firma de `C1..C10`.

**Pregunta que la originó.** Dos partes del corpus nombran el cable de identidad de dos maneras y parecían
contradecirse: la firma de `DEUDA-A · ID-1` **conserva** `RuntimeTask.owner_id` / `RuntimeTask.session_id` y
los llama *«la costura que ya existe»*; la nota `AC-39` de `SEAMS §0` fija como grafía **única y vinculante**
`RuntimeHost.scope`, token opaco, con el argumento de que *«cuatro nombres para un cable son cuatro
implementaciones divergentes esperando a ocurrir»*.

**Por qué no es una contradicción — y por qué unificarlos sería el error.** No son dos nombres de un cable:
son **dos cables con dos vidas distintas**.

1. **Cable de TRANSPORTE, por tarea** — `RuntimeTask.owner_id` / `RuntimeTask.session_id`. Atribución opaca
   que acompaña a *una ejecución* y acaba en los campos de identidad del `Event` base (`K4`) para que un sink
   suscrito por la costura pública pueda atribuir (`ID-6`). Vive y muere con la tarea.
2. **Cable de SCOPING, por persistencia** — `scope: Scope`, la grafía `AC-39`. Determina **bajo qué clave**
   escribe un repo (memoria, tokens, sesiones). Es más largo que cualquier tarea y **no** es un dato de
   ejecución: es la frontera de aislamiento entre tenants (`ID-3`: `token_storage.py:24` con default
   `user_id="mcp"` filtra entre usuarios precisamente por no tener este cable).

**DECISIÓN.** Los dos cables existen, con sus dos grafías, y **no hay derivación entre ellos** — ni
`scope = Scope(task.owner_id)`, ni `owner_id = scope.key`. Derivar uno del otro sería el runtime **componiendo
e interpretando** identidad, que es literalmente lo que `00-LEGEND §2.4` prohíbe. Quien los une es el
**integrador**, que es el único que sabe si su `owner_id` es o no la clave de aislamiento de su despliegue
(en el degenerado `agentic_code` casi siempre no lo es: el scope es el cwd).

**Consecuencia operativa.** (a) `contracts/identity.py` publica `Scope` y **ningún** repo del runtime vuelve a
aceptar `user_id: str` literal. (b) `RuntimeTask` mantiene `owner_id`/`session_id` como tokens opacos,
documentados como transporte y **no** como scope. (c) El `scope` se cablea por el ensamblador
(`RuntimeHost.scope` → `ToolUseContext.scope` → repos), nunca reconstruido desde la tarea. (d) Un runtime al
que no se le da `scope` **no inventa uno**: el seam es opcional y su ausencia es `None`, no un uuid.

**Dónde se aplica.** `C9` y, por transitividad, la firma de `C1..C8` y `C10`.

---

## `D-12` · Una tool se acredita por EFECTO, y su cobertura por CONDUCCIÓN: son dos pruebas, no una

**Fecha:** 2026-08-01 (TRAMO 1, 6ª ventana). **Origen:** la auditoría de la 5ª ventana —*«te preocupa si el
test corre, no si la funcionalidad OPERA»*— y su consecuencia medida: `FIND-E7F-1`, un barrido **verde** con
**4 de 25 tools que no cruzaban la puerta**.

**Qué se decide.** Una tool nativa **no** se da por acreditada porque un barrido la ejecute y vuelva sin
`is_error`. Hacen falta **dos aserciones distintas**, y ninguna sustituye a la otra:

1. **EFECTO** (`E10`) — con cableado **real** (nada de dobles donde exista el objeto real) se asevera **lo que
   la tool deja hecho en el mundo**: el fichero editado, el repo clonado, el registro cambiado. `is_error ==
   False` **no es** una aserción de efecto: es una aserción de que no explotó.
2. **CONDUCCIÓN** (`E11`) — un modelo real, con el censo entero delante y un enunciado **de objetivo**, la
   **elige e invoca**. Una tool que funciona pero que ningún modelo elige nunca es cobertura que **falta**, y
   se dice como carencia, no se tapa.

**Tres reglas operativas que salen de aquí:**

- **(a) La entrada del barrido se valida contra el `input_schema` DE LA TOOL**, en las dos direcciones (falta
  un `required` / sobra una clave no declarada), y **nunca contra una copia en el test**: si mañana cambia el
  schema y la tabla no, se pone rojo (`L09`). Un `except Exception` que se traga un `KeyError` de entrada mal
  formada convierte el barrido en teatro.
- **(b) Una capa de prueba nueva que sale verde a la primera está SIN acreditar.** Un test que nunca ha estado
  rojo no ha demostrado que pueda ponerse rojo. Se acredita con **violación inyectada** —anunciada antes de
  tocar el fuente, revertida desde copia propia verificada por `sha256`, nunca con `git checkout`— y el
  resultado se publica como **N inyecciones → N rojas, M falsos positivos**.
- **(c) Cuando el enunciado por objetivo NO puede discriminar dos tools redundantes por diseño**, se escribe un
  caso **dirigido** y se **declara** su régimen más débil en el propio test. Disfrazarlo de objetivo sería la
  forma exacta de `no-debilitar-la-prueba` que ya cobró dos veces.

**Por qué no bastaba lo anterior.** `D-10` fija que un tramo cierra con E2E reales en verde simultáneo; eso
acredita **capacidades** (`E1..E9`), y aguanta. Lo que no cubría es la capa **por tool**: se puede tener el
turno agéntico entero en verde y que **nadie haya aseverado nunca que `Edit` edite**. Eso fue literalmente el
caso hasta esta ventana.

**Dónde se aplica.** `C5` y `C6` en este tramo; y a toda tool que entre por `10·tools-native` en los tramos
siguientes — **entra con su caso de efecto y su caso de conducción, o no entra**.

---

## `D-13` · El universo valorable es la superficie del TRAMO, no la suite entera (2026-08-02)

- **Fecha:** 2026-08-02, 8ª ventana, tras el encargo de completar los tests **funcionales**.
- **Pregunta que la originó:** literal del usuario — *«todos los tests antiguos "que no has modificado
  explicitamente producto de la refactorización" prueban funcionalidades de la versión parcial de
  agentic_runtime, arrastrarlas no aportan nada»*.
- **DECISIÓN (del usuario):** el universo valorable son **las pruebas que se ejecutan sobre lo que la
  refactorización modificó**. Dentro de ese universo hay que **revisar las que no se tocaron pero operan
  sobre superficie modificada** — «deben haber algunas que faltan actualizar». Todo lo demás **sale del
  radar momentáneamente** y se reincorpora al conteo **cuando el avance de la refactorización lo requiera**.
- **Consecuencia operativa:**
  1. El conteo de la suite (`711 passed / …`) **deja de ser la métrica de cierre**. La métrica es la
     cobertura funcional de la superficie del tramo (`C1..C10` + gate `E1..E11`).
  2. Un test viejo que opere sobre superficie modificada y no se haya actualizado es **deuda del tramo**, no
     «test heredado»: se revisa y se actualiza.
  3. Los `xfail` **de los tests que se tocan** se mitigan (ver `H-L4`: un xfail que asevera la FIRMA acredita
     como pagado un gap que no lo está en cuanto alguien añada el parámetro). Los xfail **fuera del radar**
     no se tocan ahora.
  4. Esto **no** autoriza a borrar tests ni a bajar el listón de los que quedan dentro (`no-debilitar-la-prueba`
     sigue vigente): autoriza a **no contarlos** mientras estén fuera del radar.
- **Dónde se aplica:** `FUNCIONALIDAD.md` (define el universo y el veredicto por paquete); cierre de
  `FASE B · TRAMO 1`.

---

## `D-14` · `E11` mide una propiedad CONJUNTA; la parte que no es del runtime se declara como carencia MEDIDA, no como puerta (2026-08-02)

- **Fecha:** 2026-08-02, 8ª ventana. Encargo del usuario: *«de una vez mitiga el error que venimos
  arrastrando»* — la única roja del gate, `FIND-E11-2`.
- **Pregunta que la originó:** ¿qué significa el gate del RUNTIME cuando lo que falla es el MODELO? (quedó
  explícitamente pendiente del usuario en la 7ª ventana; aquí se resuelve).
- **Evidencia sobre la que se decide, toda ya medida:** `AskUserQuestion` estaba **anunciada 10 de 10**;
  cuando el modelo la condujo lo hizo con **argumentos válidos contra su `input_schema`**; su **efecto** está
  acreditado por `E10`; el sujeto está **homologado a A** (`FIND-E11-4` pagado); y el marcador por rama dio
  **2/10** con la descripción vieja de B y **0/10** con la fiel a A. A no tiene en su system prompt ninguna
  cláusula general que empuje a usarla (`prompts.ts:352-400`, leído: el único empujón es para el caso de
  **tool denegada**).
- **DECISIÓN:** `E11` mide una propiedad **conjunta** de (runtime · sujeto homologado · modelo). Las tres
  primeras están acreditadas y **siguen siendo puerta dura**. La cuarta —que el modelo *elija* la tool— **no
  es del runtime** y deja de bloquear el gate; se conserva **corriéndose**, con marcador medido y con un
  `xfail(strict=True)` que **enrojece por XPASS** el día que el modelo sí la conduzca, obligando a devolverla
  a la puerta dura.
- **Por qué esto NO es el tell «caso fuera»** (`no-debilitar-la-prueba`): la tool **no se retira** del censo
  ni del anuncio ni de `_E11_OBJETIVO`; el escenario **se sigue ejecutando**; la aserción **no se relaja, se
  invierte y se hace estricta**, de modo que el test habla en los **dos** sentidos; y la carencia queda
  **dicha y cuantificada** (0/10), que es literalmente lo que `D-12` manda: *«una tool que funciona pero que
  ningún modelo elige nunca es cobertura que falta, y se dice como carencia, no se tapa»*.
- **Dónde se aplica:** `test_tramo1_gate.py` (`E11`); ficha `C5`/`C6` de `TRAMO-1.md`; `FUNCIONALIDAD.md §3`.

---

## `D-15` · La validación pasa por un CONSUMIDOR REAL: `agentic_code` ejercita, los `.jsonl` acreditan (2026-08-06)

- **Fecha:** 2026-08-06, 10ª ventana, al cerrar el barrido EOF del encargo de las listas de tools.
- **Encargo del usuario, verbatim:** *«lo que de ahora en adelante haremos es usar agentic_code para
  comprobar funcionalidades de agentic_runtime, luego miraras que se ha implementado en agentic_code y
  conforme vayamos activando mas capacidades de agentic_runtime implementaremos mas capacidades en
  agentic_code, tu podras luego usar sus archivos jsonl para validar la correcta operacion»*.
- **Qué la originó.** El listado de 10 problemas confirmados **no lo produjo la suite**: lo produjo el
  usuario ejercitando `agentic_code` contra el runtime. Y el barrido del canónico que vino después
  confirmó el patrón —**el runtime tiene el dato cargado y no lo pone en ninguna lista que el modelo
  vea**— sin que ninguna de esas omisiones enrojeciera un solo test. Una suite prueba lo que su autor
  pensó probar; un integrador prueba lo que hace falta.
- **DECISIÓN — el ciclo de cuatro pasos:** (1) ejercitar la capacidad **desde `agentic_code`**;
  (2) leer **qué está implementado en `agentic_code`**, porque la asimetría entre lo que el integrador
  debe escribir y lo que el runtime le da ES la medida del hueco; (3) conforme se activan capacidades
  en `agentic_runtime`, **implementar más capacidades en `agentic_code`** — los dos repos avanzan
  acoplados; (4) **validar contra los `.jsonl`** de sesión: la traza real de mensajes, tool calls,
  anuncios y resultados.
- **Por qué los `.jsonl` mandan.** Una aserción sobre FIRMA acredita en falso (`H-L4`, ocho casos
  probados). Un `.jsonl` es lo que el modelo **realmente** recibió y **realmente** devolvió, y es lo
  único que alcanza a lo que ningún unitario ve: si el delta de diferidas converge, si el listado de
  skills llegó, si el `system-reminder` se repite turno tras turno, si lo anunciado era invocable.
- **Lo que esta decisión NO deroga.** `D-08` sigue mandando: `agentic_code` **DETECTA**, el canónico
  **DICTA**. Ante conducta divergente, contraste contra el canónico antes que «arreglar» lo que no
  sabes si es genuino. Tampoco deroga `D-12` (efecto + conducción) ni `no-debilitar-la-prueba`: una
  traza verde en `.jsonl` no sustituye a un test negativo, lo complementa.
- **Consecuencia de orden — el instrumento antes que la medida.** El problema **#10** (el stream
  público no permite reconstruir el plan de tools del turno: `TurnToolPlan` es interno) deja de ser
  «el último de la lista»: sin él, el paso 4 es **ciego** para media superficie de tools. Se pagará
  temprano aunque su número diga otra cosa.
- **Dónde se aplica:** `SEPARACION/VALIDACION-AGENTIC-CODE.md` (método + listado + cola de ataque),
  que pasa a ser el guion vivo junto a `TRAMO-1.md`.

### Adenda a `D-15` (2026-08-08, 21ª ventana) — el paso (3) es PUERTA DE CIERRE, no intención

**Motivo de la adenda: la incumplí.** El usuario lo tuvo que repetir al cierre de la 21ª («conforme
se vayan cerrando ajustes en `agentic_runtime` y `agentic_models` hay que cablearlos en
`agentic_code`, para poder probarlos; una prueba manual real es más enriquecedora que sólo pruebas
sintéticas»). No es una decisión nueva —es literalmente el paso (3) de `D-15`— y llevaba varias
ventanas sin aplicarse. `FIND-CODE-SKILL-1` no es un hallazgo: es el **residuo acumulado** de no
aplicarla, y de ahí que `agentic_code` no tenga hoy ni una referencia a skills ni a subagentes.

- **Alcance: TRES repos, no dos.** Vale igual para `agentic_runtime` **y `agentic_models`**. Lo que
  se cierra en cualquiera de los dos núcleos se cablea en `agentic_code`.
- **La regla, ahora como puerta:** una capacidad **no se declara cerrada** en la ventana que la paga
  si el consumidor real no la ejercita. Test verde del propio sujeto ≠ cerrada. Mientras no haya
  cableado, el rótulo honesto es 🟡 con la carencia nombrada, nunca ✅.
- **El criterio de cierre es el `.jsonl`, no que compile.** Ya está en `D-15`: la traza real es lo
  único que alcanza a lo que ningún unitario ve. Un cableado que no se puede ver operar en una
  sesión real no ha cerrado el ciclo de cuatro pasos, lo ha dejado en tres.
- **Por qué la prueba manual real gana, dicho por el usuario y ya evidenciado varias veces en este
  esfuerzo:** el test sintético mide lo que yo pensé al escribirlo; la sesión real mide lo que el
  sistema hace. Las cuatro inyecciones NACIDAS VERDES de la 21ª son exactamente eso — tests que
  pasaban sin medir nada. La operación real no tiene esa forma de mentir.
- **Lo que la adenda NO deroga:** el encuadre vinculante sigue intacto — **el núcleo se mantiene
  GENÉRICO y el integrador se adapta a él, nunca al revés**. Cablear en `agentic_code` no es licencia
  para doblar el runtime hacia el integrador. Y `D-08` sigue mandando: el consumidor DETECTA, el
  canónico DICTA.

---

## `D-16` · El prompt se homologa TAL CUAL y los hints son UNA sección; el TRAMO se detiene para validar lo ya cableado (2026-08-09)

- **Fecha:** 2026-08-09, 22ª ventana, tras la primera prueba E2E real con enunciado sin alineamiento.
- **Qué la originó.** La prueba no midió lo que se quería: el server MCP se cayó del censo en
  silencio y el modelo se quedó sin vía hacia el destino pedido. Al preguntar el usuario *«¿cómo
  respondería el canónico?»*, el fuente contestó algo que no estaba previsto: la conducta observada
  **la prescribía el prompt de producto de `agentic_code`**, que prohíbe en términos casi literales
  las dos salidas razonables (decir que no se puede, preguntar). `settings.py:41-60` es texto libre
  sin contraparte en A, y en dos puntos **contradice** al canónico (`prompts.ts:232`, que permite
  declararse atascado tras investigar).

### Vocabulario: se retira «dos capas»

Se había propuesto separar «capa 1 homologada» y «capa 2 de hints». **Se retira por confundente**,
por indicación del usuario. Hay **un solo prompt**, con una sección más.

### La regla

1. **El system prompt de `agentic_code` homologa el de A TAL CUAL**, secciones estáticas y
   **también las dinámicas**. No es una reescritura inspirada: es homologación, y se audita por
   diff contra el canónico como todo lo demás, cada sección citando su línea.
2. **Los hints de alineamiento a gpt-5.x son UNA sección, la ÚLTIMA antes de las dinámicas.**
   Posición exacta: cola del bloque estático, inmediatamente antes de las secciones dinámicas.
3. **Se prueba con eso.** No se teoriza más sobre la colocación: se monta, se ejercita en sesión
   real y se mide.

**Por qué esa posición es también la correcta para el canónico, y no sólo una preferencia:** A parte
el prompt con `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` justo entre lo estático (cacheable) y lo dinámico
(`prompts.ts:560-575`), y documenta en `:343-350` que cada bit condicional colocado antes de la
frontera multiplica las variantes del prefijo de caché. Un bloque de hints **estable por familia de
modelo** pertenece al lado estático; ponerlo entre las dinámicas rompería el prefijo cada turno.

### Qué gobierna el contenido de la sección de hints

`agentic_models/gpt-5.x-conducta-vs-claude.md`: catálogo medido de peculiaridades (P1–P9), las cinco
superficies en orden (`instructions` → nombre → `function.description` → schema → `tool_choice`) y
las hipótesis ya refutadas. Cada hint declara **qué P ataca** y **con qué marcador antes/después**.
Un hint sin medición es una opinión y se rotula como tal. No se duplican ahí las descripciones de las
tools: eso es la superficie 3 y duplicarla arriba no ayuda al routing.

### Cambio de fase: el TRAMO se detiene

- **Se DETIENE el avance del plano principal de homologación por TRAMOS.** No se abandona: se
  suspende. Sigue en pie lo abierto (`FIND-SKILL-22`, `FIND-E2G-3`, deuda de lectura de
  `capabilities/skills/`, bloques A y B del inventario) y se retoma por decisión explícita del
  usuario, no por deriva.
- **La fase vigente pasa a ser: probar y ajustar TODO lo ya cableado desde `agentic_code` hacia
  `agentic_runtime` y `agentic_models`.**
- **Razón, y es el criterio de esta decisión:** es la única forma de decir si lo avanzado cumple o no
  cumple **funcionalmente** la forma como opera el canónico — **en los dos lados, el núcleo y el
  implementador**. Homologar por diff prueba forma; sólo la operación real prueba función.

### Lo que NO deroga

`D-08` (el consumidor DETECTA, el canónico DICTA) · `D-15` y su adenda (ciclo de cuatro pasos, el
`.jsonl` como criterio de cierre) · `L10` (divergencia deliberada se rotula, no se cuela) · y el
encuadre vinculante: **el núcleo se mantiene GENÉRICO y el integrador se adapta a él, nunca al
revés**. La sección de hints vive en el **integrador**, no en el runtime, precisamente por esto.

### Guion vivo

`SEPARACION/VALIDACION-AGENTIC-CODE.md` (inventario de costuras) y
`agentic_code/PRUEBAS-E2E-HOMOLOGACION.md` (bitácora de sesiones reales con enunciados sin
alineamiento).

---

## `D-17` · Un test cuyo arnés renuncia a la condición que dice medir se REESCRIBE contra el criterio; y la auto-aprobación MCP se paga por sus DOS vías (2026-08-09)

- **Fecha:** 2026-08-09, 23ª ventana. Decidido con el usuario antes de tocar un solo fuente.
- **Qué la originó.** Los 3 rojos del gate MCP de `agentic_code`. Al implementar B la regla de A
  (`ServerApprovals.status()` auto-aprueba bajo bypass, espejo de `services/mcp/utils.ts:386-391`),
  dos tests se pusieron rojos porque su arnés fuerza `dangerously_skip_permissions=True`
  (`test_mcp_integration.py:98` y `:222`). Estaban verdes **sólo porque B carecía de la regla**:
  medían la ausencia de la regla, no el gate.

### La regla

1. **Un test cuyo arnés renuncia a la condición que el test dice medir no mide nada.** No se ablanda
   la aserción para volver al verde: se reescribe **el arnés** contra el criterio. Aquí: los dos
   tests del gate bajan el bypass a `False`, porque el gate de aprobación vive en el modo NO bypass.
2. **El gate se mide por CONEXIÓN, no por EJECUCIÓN.** Ejercitar una tool metería el hook de
   permisos en el camino y un verde podría venir del ✗ del permiso en vez del gate — trampa ya
   cazada una vez y documentada en `test_mcp_integration.py:108-110`. Se mide sobre las tools que
   el provider aporta al pool.
3. **Antídoto al verde vacío:** todo test negativo lleva pareja la aserción de que lo negado
   **estaba declarado** (`ProjectServerStore.declared()`), para que un verde no pueda provenir de
   «no había nada configurado».
4. **La regla nueva paga su propia cobertura.** Auto-aprobar bajo bypass y que el `reject` explícito
   **mande sobre** el bypass son conducta nueva sin un solo test: se añaden. Código nuevo sin test
   es deuda, la traiga quien la traiga.
5. **Expectativa de nombre desnudo.** El tercer rojo (`…failing_remote_tool…`) **no es del gate**:
   su sustancia pasa y falla sólo en `✗ always_fails` vs `✗ mcp__echo__always_fails`. Es la familia
   de los 7 rojos declarados del runtime — el pago de `FIND-MCP1` (naming FQ `mcp__srv__tool`,
   `11-cap-mcp.md:79`) invalidó la expectativa. Se corrige al nombre FQ **y se refuerza** con la
   aserción negativa de que no aparezca texto de denegación de permiso, para que el ✗ no pueda
   volver a ser el del permiso.

### Las DOS vías de auto-aprobación, y por qué las dos se pagan

`getProjectMcpServerStatus` (`services/mcp/utils.ts:351-405`) auto-aprueba por **dos** caminos, y el
razonamiento de A es el mismo en ambos: *no hay diálogo que mostrar*, luego dejar el server en
`pending` no lo somete a una decisión del usuario — **lo descarta en silencio**.

- **Vía 1, bypass** (`:386-391`): ya pagada.
- **Vía 2, sesión no interactiva** (`:397-403`): `getIsNonInteractiveSession()` — SDK, `claude -p`,
  entrada por tubería. **Se paga.** B ya tiene la distinción materializada: `cli.py:175` pasa
  `interactive=not args.print_mode`.

### Corrección de una carencia SOBREDECLARADA

El docstring de `ServerApprovals` declaraba como «divergencia por EXCESO» la ausencia en B de la
guarda `isSettingSourceEnabled('projectSettings')` que A pone en las dos vías. **Leído el fuente
(`D-08`), eso sólo es cierto para el perfil SDK.** El estado por defecto del CLI incluye
`'projectSettings'` en `allowedSettingSources` (`bootstrap/state.ts:313-319`); sólo el SDK lo pone a
`[]`, y el CLI lo altera con `--setting-sources`. Para el **perfil terminal que B implementa la
guarda es constante-verdadera**, luego B es **equivalente**, no excesiva. Se corrige el docstring:
declarar de más también es declarar mal.

### Divergencia deliberada, rotulada (`L10`)

**Ambas vías anuncian por diagnóstico el server auto-aprobado.** A no emite nada. Es divergencia por
**exceso de información**, benigna y deliberada: el defecto real en las dos direcciones —descartar en
silencio, conectar en silencio— es el **silencio**, y conectar un proceso de terceros sin que nadie
lo haya aprobado es exactamente lo que merece quedar dicho.

---

## D-18 · El descriptor precede al diferido, porque es su señal de ranking

**Decisión.** De los cuatro huecos vivos en las superficies de routing, se paga **primero la
superficie 3** (`function.description` de las nativas) y **después la 2** (marcar diferidas,
`GAP-TOOL4`). No es preferencia: es dependencia.

**Por qué, en dos razones que se suman.**

1. **Asimetría a favor del tercero.** Una tool MCP llega con el texto que escribe su server,
   íntegro hasta 2048 caracteres (`tool_adapter.py`, calcado de `client.ts:218`). Una nativa de B
   llega al **24–56 %** del texto de A en las que importan (`bash` 26 %, `read_file` 51 %,
   `Edit` 56 %, `Config` 35 %, `TaskUpdate` 24 %). **21 de las 25 nativas caben por debajo del cap
   de MCP.** La comparación semántica que decide qué tool se invoca la gana el texto más largo y
   más específico, y hoy ése puede ser el del tercero. Es P2 medido en su forma peor: no «falta
   contrato», sino «el contrato del tercero pesa más que el nuestro».

2. **Bajo diferido el descriptor ES el ranking.** `tool_search` casa la query contra nombre +
   descripción y no hay cuerpo que mirar. Diferir las 15 «meta» con las descripciones a medias
   mide `GAP-TOOL4` sobre una señal ya corrompida, y el marcador antes/después no separaría el
   efecto del diferido del efecto del texto ausente. **Primero la señal, luego el mecanismo que
   la usa.**

**Alcance.** Vive entero en `agentic_runtime/.../tools/native/`: es del núcleo y no se mueve al
integrador, que sería invertir la relación. `bash` va primero porque además paga `GAP-PROMPT-1` en
su segundo sitio: A repite la preferencia contra la fuerza bruta en la **descripción de `bash`**
(`BashTool/prompt.ts:275-291`), no sólo en el prompt, y B tenía cero ahí.

**Criterio de la prueba.** Cada tramo se mide **contra el literal de A**, nunca contra un mínimo de
longitud: un umbral de caracteres es el test blando de siempre — se pone verde con relleno.

### Corrección de `D-18` al ejecutarlo: la ratio B/A no medía deuda

La ratio `len(description_B) / prosa_A` con la que se priorizó este tramo **estaba mal como
métrica**, y se dice aquí porque el cuadro que la usaba ya circuló. Al abrir tool por tool:
`read_file` 51 %, `Edit` 56 %, `write_file` 69 %, `Config` 35 %, `TaskUpdate` 24 %,
`TodoWrite` 32 %, `Agent` 37 % — **todas** tienen su omisión OMITIDA Y DECLARADA con cita a
`prompt.ts:línea`, y todas por carencia estructural real de B: no lee imágenes/PDF/notebooks,
no tiene `replace_all`, no comprueba lectura previa, no tiene registro de ajustes
(`FIND-CFG-2`), no mueve estados de tarea (`FIND-TASK-1`). **Contar caracteres contaba la
adaptación justificada como si fuera deuda.** Una descripción corta porque la tool hace menos
no es una descripción a medias; escribir texto para subir la ratio sería anunciar palancas
inexistentes, que es `FIND-E11-3`.

Lo que la ratio **sí** acertó fue un único caso, y por casualidad: `bash` al 26 %, donde el
26 % era real. Pagado.

### Lo que sí era el hueco: `searchHint`, no la longitud

La preocupación de fondo —que una tool MCP gane la comparación semántica a la nativa que
debía usarse— **no se resuelve con más texto**: se resuelve donde está el ranking. Y ahí
había hueco sin declarar.

`tool_search` puntúa nombre, descripción y hint, y **bonifica a las MCP**: 12/6 por nombre
frente a 10/5 de una nativa (`tool_search.py:211-213`, calcado literal de
`ToolSearchTool.ts:186-302` — es de A, no divergencia). El `searchHint` vale **+4**, el doble
que la descripción (+2). **A declara `searchHint` en 13 tools que B tiene; B lo llevaba en 1.**
12 nativas entraban a esa comparación con 4 puntos menos frente a una tool cuyo texto escribe
el server de terceros. Portados con la grafía literal de A. Quedan sin hint `Sleep` y
`ToolSearch` —porque **A tampoco se lo declara**, y ponérselo obligaría a inventarlo— y
`clone_repository`, que no existe en A (`L10`).

**Consecuencia para el orden de `D-18`:** el vínculo con `GAP-TOOL4` se refuerza, no se
debilita. El hint sólo puntúa en la vía diferida; pagarlo antes de marcar las 15 diferidas es
exactamente poner la señal antes que el mecanismo que la usa.

---

## D-19 · `GAP-TOOL4` pagado: las 15 «meta» se difieren, y el marcador dice qué cambió

> ⚠ **DEROGADA EN PARTE por `D-37` (2026-08-21).** El reparto «igual al del canónico y sólo al del
> canónico» deja de gobernar las nativas: por convención, **todas las nativas van `deferred = False`**.
> El motivo es de medición, no de gusto — en gpt-5.x la `description` ES el contrato de conducta y
> diferirla produce sondeo (`D-36`). Lo que de `D-19` sobrevive intacto es el método: el censo se
> resolvió leyendo el fuente de A fichero a fichero (`D-08`), y su guardián sigue siendo un test de
> producción, no de pool fabricado — sólo que ahora afirma el reparto nuevo.

**Decisión.** Las 15 nativas que A retira del turno 1 por `shouldDefer: true` se marcan
`deferred = True` en `tools/native/`, con la cita a `fichero:línea` de A en cada clase. El
reparto queda **igual al del canónico y sólo al del canónico**: 15 diferidas, 10 no.

**El censo, releído sobre el fuente de A (`D-08`), no de memoria.** 27 ficheros de
`claude-code/src/tools` llevan `shouldDefer: true`. De ésos, B tiene 15 —los de la ficha— y no
tiene 12 (`LSPTool`, `SendMessage`, `Team*`, `RemoteTrigger`, `Cron*`, `NotebookEdit`). Las dos
de recursos MCP quedan fuera a propósito: son `FIND-MCP17`, deuda distinta con su `xfail` vivo.

**Guardián durable, acreditado en rojo dos veces.** `test_gap_tool4_el_reparto_de_diferidas_es_el_del_canonico`
mide sobre las clases de **producción** vía `create_tools(interactive=True)` — no sobre un pool
fabricado, que es justo por lo que `E2g` no veía este hueco (monkeypatchea el suyo,
`test_tramo1_gate.py:2357-2359`). Acreditación ejecutada contra el fuente base en worktree
aparte: sin las marcas da `faltan={las 15}`; difiriendo `grep` da `sobran={'grep'}`. **Las dos
direcciones se afirman a propósito**: sin la segunda mitad, un rojo se «arregla» difiriendo
`grep`, que es exactamente lo que el turno 1 no puede perder.

### El marcador: qué cambió de verdad, medido en consumidor con `AGENTIC_CODE_GPT5_HINTS=0`

14 sesiones reales de `agentic_code` (`--print`, gpt-5.4-mini, `.jsonl` como evidencia), en las
dos configuraciones que el usuario fijó, 3 enunciados sin alinear, 7 rondas por lado.

| | anunciadas | diferidas ANTES | diferidas DESPUÉS |
|---|---|---|---|
| con `obsidian` | 38 | 15 (todas MCP) | **27** |
| sin MCP | 21 | **0** | **12** |

- **12, no 15, porque el marcador corre en `--print`:** `AskUserQuestion`, `EnterPlanMode` y
  `ExitPlanMode` están gateadas por `interactive` (`factory.py:53-59`) y no entran al pool
  headless. En sesión interactiva son las 15. **No es un hueco de cableado**, y se dice porque
  al leer el primer marcador lo di por tal.
- **El `tool_search` server-side aparece donde no estaba:** sin MCP el `any(t.defer_loading)`
  de `openai_responses_shared.py:229-231` era falso y no se emitía; ahora se emite siempre.
  La rama en juego es la NATIVA, verificado en catálogo (`gpt-5.4-mini.native_tool_search`
  = `True`), no supuesto.
- **La expansión server-side funciona sobre nativas:** en 4 de 6 rondas de `webdir` el modelo
  invocó `WebSearch` —ya diferida— **sin ninguna llamada a `ToolSearch` client-side**. Eso es
  la prueba de que el proveedor las resuelve; una corrida verde no lo habría dicho.
- **14.661 bytes de schema salen del turno 1** (las 12 del pool headless, medidas
  `description` + `input_schema`).

**El cambio de conducta que sí hubo, y no se disimula.** El enunciado `tres` («revisar tres
cosas a la vez») pasaba por `TaskCreate` en **4/4** rondas antes y en **1/4** después: el modelo
se fue a `Agent`, que A no difiere. Las respuestas del «después» son mejores —revisan y
reportan, en vez de crear tres tareas y preguntar qué hacer—, pero eso es efecto colateral
observado, no el criterio: **el criterio es que el reparto sea el de A**, y la conducta se
anota como lo que es, un desplazamiento medido de `Task*` hacia `Agent`.

**Deuda cero neta por diff, medida y no rotulada (`declarar no es pagar`).** Suite completo
antes y después con invocación idéntica (`uv run pytest -q -p no:randomly`, el «antes» desde
worktree del `HEAD` por `PYTHONPATH`, sin revertir nada): **12 rojos antes, 13 después**; el
único de más, `test_e6_…`, **pasa en aislado** — es gate contra modelo vivo, ruido. `e2c`/`e2e`
fallan con el **mismo texto y el mismo número** a los dos lados porque fabrican su pool.

## D-20 · Los prompts salen del alcance del canónico: criterio funcional, canónico sustituto y disciplina de capas

**Decisión del usuario, 2026-08-09, tras leer el marcador de `D-19`.** Siete piezas. No es un
matiz de `D-08`: es un cambio de **criterio de aceptación** para una capa entera.

**1. La homologación de prompts está CERRADA y su evidencia guardada.** `agentic_code`
`8be6eb5` («Punto de control: system prompt homologado del canónico + hints gpt-5.x»), con
auditoría mecánica contra `constants/prompts.ts`. Es **línea base alcanzada**, no restricción
viva. No hay que volver a demostrarla ni preservarla.

**2. Separarse del canónico en prompts es inexorable y está autorizado.** Ejecutamos otra
familia de modelos. La divergencia de prompt **no es deuda ni regresión: es el trabajo**. Lo
que se exige de cada separación es **marcador**, no permiso.

**3. El criterio es el punto dulce, y el resultado FUNCIONAL manda sobre el técnico.**
Agnosticidad del núcleo + **mínimo** alineamiento, tal que (a) el agente **en general** use
bien las herramientas y (b) el turno cierre **siempre** con el resultado funcional esperado. Un
turno técnicamente correcto —sin excepciones, llamadas bien formadas, homologado línea a
línea— que no entrega lo pedido **es un turno fallido**. La capa de hints deja de ser deuda a
eliminar y pasa a ser **variable a minimizar**; `AGENTIC_CODE_GPT5_HINTS=0` es el **control**
del marcador, nunca la meta.

**4. Canónico sustituto: OpenAI.** Toda decisión de ajuste de prompt se contrasta **siempre**
con lo que OpenAI dice de la familia gpt-5.x. Al salir los prompts del alcance de A no queda un
hueco: queda **otro canónico**, el del fabricante del modelo que ejecutamos. **Escalera de
fuentes**, en orden: guía de prompting → **documentación completa** (referencia de la Responses
API, model cards, notas de versión, cookbook) → **artículos oficiales** → sólo entonces
**decisión propia, rotulada como tal**. Entre «la guía no lo dice» y «probamos» no hay atajo.
Cada hint queda así con **dos avales independientes**: la fuente que lo justifica *a priori* y
el marcador que lo acredita *a posteriori*. Donde fuente y marcador se contradigan **manda el
marcador** —es medida sobre el modelo real— y la contradicción **se registra**.

**5. Aval externo del punto 1, buscado y verificado.** Anthropic **borró más del 80 % del
system prompt de Claude Code** para la generación Claude 5 *«with no measurable loss on our
coding evaluations»*, y su diagnóstico es el nuestro: el prompt afinado a mano para la familia
4.x **estorbaba** a la 5.x
(<https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models>,
24 jul 2026). Su cuarta mudanza —*«put instructions on how to use tools in the tool descriptions
rather than the system prompt»*— **es la pieza 6 de esta decisión, enunciada por el fabricante
de A**. ⚠ **Alcance, dicho para que nadie lo estire:** es el criterio de Anthropic para SUS
modelos, **no es transferible por decreto** a `gpt-5.4-mini`; lo que prueba es la lección de
método —un prompt canónico envejece con la familia para la que se escribió—, y el escalón que
manda para nosotros sigue siendo el punto 4.

**6. DOGMA, dos prohibiciones sin excepción.** (a) **Jamás referencias a herramientas en el
prompt ESTÁTICO** —ni nombres, ni «usa X en vez de Y»: el bloque estático no sabe qué
herramientas existen. (b) **Jamás alineamientos en el DINÁMICO ajustados a que un escenario
particular salga bien**. No construimos para un caso único: el prompt es **agnóstico por
naturaleza** y sirve a todos los casos de uso donde la herramienta sirva. *Prueba de admisión
de un hint: si al enunciarlo hace falta decir «cuando el usuario pida X», está mal ubicado.*
Esto ata también al ejecutor: los marcadores se apoyan en enunciados concretos (`webdir`,
`tres`) y **escribir el hint que pone verde ESE enunciado es exactamente lo prohibido** — el
marcador acredita, no dicta el texto. Aval técnico independiente: un nombre de tool en el
estático ata el prefijo cacheable al **censo** de herramientas —que varía por `interactive`,
por MCP, por configuración—, así que cualquier cambio del censo invalida el prefijo entero. Es
el defecto que `prompts.ts:343-350` advierte, cometido desde dentro. **La regla no cuesta
caché: la protege.**

**Conflicto conocido, heredado de A:** `system_prompt.py:218` `_using_your_tools_section` (copia
de `prompts.ts:269-315`) interpola **10 nombres de tools de B** en el bloque **estático**, y
`_session_guidance_section` recibe `tool_names`. El comentario del módulo que lo defendía
(`system_prompt.py:53-57`) era correcto bajo el criterio anterior y **queda derogado**.
**Forma del desmontaje, decidida por el usuario: se suprime del ARMADO, NO se borra el código
que lo describe** — la sección queda en el fuente con su cita del canónico y sus comentarios,
sin emitirse, porque es documentación de lo que A hacía y borrarla destruye conocimiento que
costó homologar. Exige **marcador antes/después propio**: cambia el turno 1.

**7. Disciplina de capas: el arnés no se relaja con la separación.** La **estructura y el orden
de secciones de A se respetan** —buena práctica, no homenaje: sostienen la frontera cacheable.
Lo que **no** es obligatorio es conservar contenido que, **medido**, no aporta nada: eso se
retira con su medición, no se arrastra. Y **cada ajuste va a la SECCIÓN que le corresponde por
materia, no a la de hints**: la tendencia natural es que todo caiga en
`_gpt5_alignment_section` hasta volverla un cajón de sastre inauditable, y queda **prohibido
por defecto** — se reserva para lo que no tiene sección propia en A. La marca de «esto es
gpt-5.x» debe ser **enumerable mecánicamente** (no un comentario libre), para poder **listar,
retirar o sustituir** todos los fragmentos de una familia sin releer el módulo. **Propósito
explícito: que el próximo modelo sea un cambio de capa, no una arqueología.**

### Consecuencias inmediatas sobre la cola de pendientes

- **La cola deja de ordenarse por distancia al canónico y pasa a ordenarse por cuánto mueve el
  resultado funcional.**
- **`GAP-PROMPT-1` cambia de enunciado y queda partido por el dogma**: ya no es «descripciones
  sin homologar» sino **«descripciones que no guían la elección con gpt-5.x» (P4)**, y se cierra
  con **conducta medida**, no con paridad textual. Su reparto lo dicta la pieza 6: **toda guía
  que necesite NOMBRAR una tool va a la `description` de esa tool** —donde el dogma y la cuarta
  mudanza de Anthropic coinciden—, y el **segundo atractor medido** (el cierre en vacío tras
  `AskUserQuestion`, que ninguna descripción arregló) va al prompt **sólo** como incitador
  **genérico**, que es admisible precisamente porque no nombra herramienta alguna. Eso concilia
  el carril ya anotado en `FUNCIONALIDAD.md` con el dogma, sin relajar ninguno de los dos.
- **`GAP-TOOL3` (precedencia de `isDeferredTool`) baja de prioridad**: con el reparto ya
  correcto por `D-19`, es fidelidad estructural que no mueve conducta observable. **Se declara
  y se vigila** (`declarar no es pagar`), no se paga por simetría.
- **Lo funcional conserva su rango**: abort de `WebFetch`, singleton `RuntimeFactory._modes`.
  Rompen el turno, no la simetría.
- **`D-08` conserva su alcance, reducido a lo que era**: ante conducta divergente se lee el
  fuente de A para **entender** qué hace y por qué; no para obligar a copiarlo en el prompt.
  La lectura sigue siendo obligatoria; la copia, no.

### Fuente vecina, consultada una sola vez y NO canónica

Pasada de lectura sobre `/home/noheroes/python/openclaw` (`51bae7512`), *agentic OS*
multimodelo con el mismo origen **PI** que `agentic_models` y más maduro que este desarrollo.
Producto: **`agentic_models/criterios-prompt-multimodelo.md`**, con cada línea etiquetada
`OBSERVADO` o `CRITERIO CANDIDATO`. **openclaw NO es un escalón de la escalera del punto 4** y
nada entra en B por imitación. Hallazgo central: su constructor de prompt son **725 líneas con
cero ramas por familia de modelo** — la peculiaridad se nombra por **capacidad** (flag resuelto
fuera, texto genérico dentro: `reasoningTagHint` ← `isReasoningTagProvider`, `attempt.ts:947`)
y las divergencias de proveedor se pagan en **transporte** (`provider-capabilities.ts`), no en
prompt. **Y contradice nuestro dogma**: lista el censo de tools con resúmenes dentro del prompt
(`system-prompt.ts:240-339`) — **no se adopta**, con motivo escrito (§7 de ese documento).

---

## D-21 · Una opción que el motor no sabe expresar se RECHAZA; descartarla en silencio es el defecto

**2026-08-09, al cablear `B5` (`model_options`).** La costura `S1` estaba entera y **vacía**:
`composition.py:206` pasaba sólo `capabilities=…`, así que `thinking`/`effort` llegaban siempre
sin poblar. Al llenarla aparecieron tres huecos que **no** eran del cableado sino de lo que hay
debajo, y los tres tenían la misma forma: el parámetro **viaja, se acepta y se tira sin decir
nada**.

- **`FIND-MODELS-BUDGET-1`.** `SimpleStreamOptions.thinking_budgets` sólo lo leen cuatro APIs
  (`anthropic-messages`, `bedrock-converse-stream`, `google-generative-ai`, `google-vertex`).
  `build_base_options` devuelve un `StreamOptions` plano y cada provider **re-adjunta lo suyo**:
  en `azure-openai-responses` se re-adjunta el nivel y el presupuesto desaparece.
- **`FIND-MODELS-OFF-1`.** `thinking.enabled=False` era un no-op. Apagar es un **nivel** (`off`),
  no la ausencia de nivel: omitir el parámetro deja el default del motor (`medium` en gpt-5.x),
  que es lo contrario de lo pedido. Y `clamp_thinking_level` **escala** lo no soportado, de modo
  que un `off` mudo se convertía en `minimal`.
- **`FIND-RT-REASON-1`.** Los items de razonamiento **no volvían nunca** al motor, pese a que
  `agentic_models` ya los sabe re-inyectar (`openai_responses_shared.py:130-137`) y los sabe
  firmar (`:368-379`). Los tres cortes estaban en el runtime.

**La decisión.** Ante una opción sin representación en el motor elegido, el puente **lanza
`UnsupportedModelOptionError`**. No la omite, no la aproxima al nivel más cercano y no la
registra en un log que nadie lee. El razonamiento es que un turno que razona cuando se pidió que
no razonara —o que ignora un techo de tokens— produce **exactamente la misma captura** que uno
que obedeció: el defecto es indetectable *a posteriori*, y por eso hay que hacerlo imposible
*a priori*. Es la lectura estricta de la doctrina de la costura: *lo que no se permite es que un
puente los reciba y los tire callando.*

**Dónde se paga** (criterio `C2` de `criterios-prompt-multimodelo.md`): en la **capa de
transporte**, nunca en el prompt. La sonda `agentic_models.supports_thinking_budget` es
conocimiento de proveedor y vive con el proveedor; el runtime la consulta, no la replica.

**Corolario, del canónico.** Las firmas de razonamiento están **atadas al modelo**
(`query.ts:924` → `stripSignatureBlocks`): un bloque firmado por otro modelo se descarta al
rearmar el contexto. Y el razonamiento **se cuelga de un mensaje que ya existe**, nunca crea
uno: un assistant sólo-thinking es un 400 en el request siguiente
(`utils/messages.ts:2306-2310`).

**Evidencia.** `agentic_runtime/src/agentic_runtime/tests/test_model_options_reasoning.py`
(13 pruebas) y `agentic_code/tests/test_reasoning_surface.py` (16). El cierre real, por `D-15`,
sigue siendo un `.jsonl` de sesión con `--capture-payloads`: el grabador anota el `reasoning`
que salió de verdad y cuenta los items de razonamiento devueltos (`reasoning_items_sent`), que
es la única prueba directa del round-trip.

**Hallazgo colateral del entorno.** `agentic_runtime/.venv` tenía `agentic_models` instalado como
**copia congelada**, no como editable: la suite del runtime estaba midiendo contra una copia
vieja del proveedor. Reinstalado editable contra `/home/noheroes/python/agentic_models`.

---

## D-22 · «¿Existe en B?» NO es una razón para no portar: lo que no está SE CREA (2026-08-10)

**Disparador, verbatim del usuario:** *«la respuesta no solo a este caso sino a todo caso que ocurra,
agentic_runtime es un proyecto en fase de homologacion, lo que no este se crea si con esto se
consigue precisamente esto, homologar comportamiento, algoritmo, etc de canonico. por tanto no
cabria la pregunta si existe o no en B.»*

**Qué la originó.** El paso 4 (`FIND-CFG-2`). Yo había cerrado media fila con el argumento *«B no
tiene hoy ni un ajuste escribible en caliente ⇒ el registro va vacío»*, y con él había declarado no
portables la guarda 11 (`check_permissions`) y el almacén de configuración. Eso convierte una
**carencia** en un **criterio de alcance**, que es la forma inversa de
`homologar-es-trasladar-conducta`: allí se doblaba la descripción hacia nuestra implementación;
aquí se doblaba el alcance hacia nuestras ausencias. Las dos dejan la conducta del canónico fuera.

**DECISIÓN.** La ausencia de referente en B **no es motivo de exclusión**. Si portar la conducta del
canónico exige construir lo que falta —un almacén, una costura del contrato, un registro, un módulo
entero— **se construye**. `agentic_runtime` está en fase de homologación: lo que no está, se crea.

**Qué deroga.** La **pregunta 2** del esquema del censo (`CENSO §1`) deja de ser un filtro de
alcance. Sigue siendo una pregunta útil —dice **cuánto** hay que construir y en qué capa— pero su
respuesta «no existe» ya **no autoriza a saltar la fila**. El rótulo «sin referente en B» queda
prohibido como cierre; se sustituye por «falta construir X».

**Alcance retroactivo — lo que reabre**, todo declarado ya en el censo con ese rótulo derogado:
`FIND-EDIT` G2 (`checkTeamMemSecrets` + `secretScanner`) · `FIND-EDIT` G8 (`.ipynb` ⇒ `NotebookEdit`)
· `FIND-CFG-PERM` (guarda 11, exige `check_permissions` en el contrato T1) · el almacén de
configuración de `FIND-CFG-2` · `FIND-MEM-WIRING`. Se re-abren como trabajo, no como nota.

**Lo que NO deroga, y la línea que sí queda en pie.** El encuadre de capas: **el núcleo se mantiene
genérico y el integrador se adapta a él, nunca al revés** (`D-15` adenda, `architecture-layers`).
Por eso la lectura operativa es: **en `agentic_runtime` se construye todo lo que la conducta del
canónico exija** —mecanismo, costura, contrato, almacén—; en `agentic_code` se cablea lo necesario
para ejercitarlo (`D-15` paso 3). Lo que **no** se deduce de aquí es que `agentic_code` deba
adquirir la *superficie de producto* de Claude Code —selector de temas con seis paletas,
`editorMode`, canales de notificación, voz, teammates—: eso es dominio de producto de A, no
algoritmo ni comportamiento, y su construcción es decisión aparte del usuario, no consecuencia
automática de esta regla. **Si el usuario quiere también eso, lo dice y entra.**

**Tampoco deroga `D-21`.** Una opción que el motor **no sabe expresar** se sigue rechazando: ahí la
imposibilidad es del proveedor y no se arregla construyendo en el núcleo. `D-22` habla de lo que
falta **en nuestro código**; `D-21`, de lo que no existe **fuera de él**.

**Dónde se aplica.** Todo el censo de guardas y las fases siguientes. Es regla de gobierno.

---

## D-23 · El barrido de comentarios cubre lo que el paso ESCRIBE, no el fichero entero (2026-08-13)

**Disparador.** El paso 4 (`FIND-CFG-2`) toca `agentic_code/composition.py` y
`agentic_code/mcp_config.py`, dos ficheros con documentación extensa y **ajena al paso** (la
doctrina de `WorkspaceCwd`/`PlanModeState`, el sourcing MCP por scope, el gate de aprobación).
Leído al pie de la letra, el §4 del censo —*«al tocar un fichero se borran los textos en forma de
comentario y docstring explicativos que haya»*— obligaría a borrarla toda por haber añadido tres
líneas.

**DECISIÓN.** El barrido cubre **lo que el paso escribe**: ficheros nuevos y funciones nuevas o
reescritas van sin comentarios ni docstrings; la documentación preexistente que el paso no toca
se queda. Es el precedente ya sentado en el paso 3 y visible en el árbol: `mcp_config.py`
conservó su documentación mientras las funciones que aquel paso escribió (`is_mcp_project_file`,
`validate_mcp_config_content`) van desnudas.

**Por qué esta línea y no otra.** El motivo de la regla es que un comentario del tipo
«homologado con `X.ts:123`» **sesga**: se lee como evidencia y ahorra el contraste. Ese daño lo
produce lo que se escribe **ahora**, junto al algoritmo recién portado. La documentación
preexistente de un fichero del integrador no afirma homologación de nada y borrarla sería
destruir trabajo ajeno al paso bajo la excusa de una regla de higiene — además de inflar el diff
del paso hasta hacerlo irrevisable, que es lo contrario de «una ventana, un paso».

**Límite.** Si el paso **reescribe** una función, su documentación anterior cae con ella: eso ya
es lo que el paso escribe. Y si un comentario preexistente afirma la conducta que el paso acaba
de derogar, se borra —dejarlo sería mentir en el fuente, que es peor que el sesgo.

---

## D-24 · Un paso cierra por PASADA ORGÁNICA; el `--print` guionado deja de ser criterio (2026-08-13)

**Disparador, verbatim del usuario:** *«yo no pruebo con --print, yo pruebo con enunciados y turnos,
el uso de --print para mi no es un escenario real de prueba, mis pruebas son organicas, pruebo el
entorno con un enunciado y visualizo las respuestas»*; y tras correr la guía: *«si tus pruebas con
--print te dan como respuesta verde a situaciones donde como describes son casos puntuales guionados
y no comportamiento organico, su valor para mi es nulo, un usuario usando honestamente el CLI no
obtiene el resultado cuando se encadenan turnos, es simple»*. Y la regla que la fija: *«en lugar de
gastar tokens con pruebas --print que no llevan a nada, sea la evidencia de las pruebas organicas lo
que retroalimente binariamente funciona o no funciona como se espera»*.

**Qué la originó.** El paso 4 (`FIND-CFG-2`) se había declarado CERRADO con la costura acreditada por
corridas `--print` y por `agentic_code/tests/test_config_tool.py`. La primera sesión orgánica del
usuario —tres enunciados encadenados en un REPL real— produjo **tres observaciones**, y ninguna la
veía el verde: (1) el modelo contestó de memoria el catálogo de ajustes sin cargar nunca la
descripción, porque el anuncio de diferidas **sólo lleva nombres**; (2) eligió `bash` y `Agent` para
un objetivo que la tool cubría; (3) tras un `tool_result` de `permiso denegado por el usuario para
'Config'`, **no volvió a invocar la tool en ningún turno posterior** — trató la denegación como
revocación permanente y delegó en `Agent` la disculpa. Las tres son conducta **entre turnos**, y un
`--print` es un turno único por construcción: no puede verlas ni con la aserción más dura.

**DECISIÓN.**
1. **Un paso del censo NO cierra sin una pasada orgánica** del usuario: REPL real, enunciados
   encadenados, sin `--dangerously-skip-permissions` y sin `--allowed-tool`. El veredicto es
   **binario** —funciona o no funciona como se espera— y lo emite lo observado en la sesión, no yo.
2. **No se escriben más suites guionadas ni corridas `--print` como prueba de cierre**, y no se
   invocan como aval. Las existentes quedan donde están, con rango de red de regresión, y no se
   litigan (`suites-sinteticas-apartadas` sigue vigente para las del runtime: no se corren, no se
   leen, no se editan).
3. **Cada conducta que se dice portada lleva un DELATOR**: un rasgo que la respuesta no puede exhibir
   si la conducta no está —un literal del canónico, una glosa que sólo vive en la descripción, un
   byte en disco—. Un enunciado que una respuesta plausible de memoria puede satisfacer no es prueba:
   es la trampa que el turno 1 de la primera guía cazó conmigo dentro.
4. **El guion orgánico ordena los turnos por contaminación**: primero lo que no ensucia la
   transcripción, al final lo que sí (denegaciones, errores forzados), y `/clear` o sesión nueva
   después de cada denegación. Encadenar sin ese orden mide el poso del turno anterior, no el paso.

**Qué reabre.** Los pasos 1, 2, 3 y 4 estaban rotulados CERRADO en `CENSO §5` con evidencia
guionada. Bajan a **inyectados, pendientes de pasada orgánica**. No es que se sepan rotos —el paso 4
tiene tramos ya acreditados en captura real: lectura sin diálogo y diálogo de escritura con su
literal exacto—: es que el rótulo afirmaba más de lo que la evidencia sostenía.

**Cuarta pregunta ciega del esquema del censo.** `CENSO §1` documenta tres cosas que la ficha por
guarda no ve. Se añade la cuarta, que es la que este disparador destapó: **la ficha mira una guarda
dentro de un turno y no ve la conducta ENTRE turnos**. Los pasos 1–3 portaron cada uno una conducta
cuyo sentido vive en el turno siguiente —el vaciado `allDone ⇒ []` sólo se observa al releer, el
literal de «no encontrado» existe para que el modelo se autocorrija después, la guarda de plan mode
es maquinaria multi-turno—, y las tres se habían acreditado dentro de un turno.

**Lo que NO deroga.** `D-15` no cambia, se afila: el consumidor real sigue siendo `agentic_code` y el
`.jsonl` sigue siendo la evidencia; lo que se retira es la corrida **guionada** como forma de
ejercitarlo. `D-08` sigue mandando: si la pasada orgánica sale roja, se resuelve leyendo el canónico,
no ajustando el enunciado hasta que salga verde (`no-debilitar-la-prueba`). Y `D-12` conserva su
reparto: el efecto en el mundo se asevera igual —el byte en disco, el fichero editado—, sólo que
ahora se asevera **dentro** de la sesión orgánica.

---

## D-25 · La RUTA no es criterio de cierre; lo son la SEMÁNTICA y la TRAZA (2026-08-15)

**Disparador, verbatim del usuario:** *«cuando tu propones aumentar a 12 rondas, implicitamente
estas aceptando que solo buscas que mejore le % no que se solucione un problema, lo que necesitamos
es algo casi casi determinista, sino no vale, nunca podre lograr que un asistente haga algo bien, si
estoy pensando que hay veces que puede fallar.»*

**Qué la originó.** Medida la línea base de `Edit` con enunciado neutral —renombrar una variable en
un fichero de cuatro líneas—, 8 rondas, `gpt-5.4-mini`, workspace y `state-dir` nuevos por ronda:
`Edit` en la sesión padre 4 veces (3 con `replace_all`), **delegación en `Agent` las otras 4**, y
`bash` **ninguna**. Propuse subir a 12 rondas por brazo para justificar un párrafo de capa 2 en la
descripción de `Edit`. Eso concede el fenómeno de antemano: un marcador que pasa de 4/8 a 1/12 sigue
siendo un asistente que a veces delega.

**El hecho técnico que la sostiene, y que ninguna redacción cambia.** Las superficies 1–4 —prompt,
nombre, `function.description`, esquema— son entradas que el motor **pondera**. Ninguna decide. Lo
único que traslada la fiabilidad del modelo al harness es la superficie 5 (`tool_choice`,
`allowed_tools`), y exige que el integrador **clasifique la intención antes de llamar al modelo**,
que es precisamente lo que un asistente de codificación general no puede hacer sin un clasificador.
Medido además que el mecanismo del propio canónico tampoco lo compra: `TodoWrite` y las seis `Task*`
**ya están diferidas** en B como en A, y aun así dos de las cuatro rondas delegadas entraron por
`TaskCreate`/`TaskList` — porque diferir esconde el esquema pero el anuncio **sigue llevando los
nombres** (`VOLCADO-DESCRIPCIONES-2026-08-15 § 0`).

**DECISIÓN.**
1. **La ruta elegida deja de ser criterio de cierre.** Se registra como observación, con su traza, y
   no bloquea ni acredita ningún paso.
2. **Cierran los pasos dos cosas, y las dos admiten garantía porque son código:** la **semántica** de
   la tool —lo que hace con los argumentos, sus errores, lo que preserva en disco— y la **traza**,
   que debe ser legible aunque el modelo delegue.
3. **No se escriben más hints ni párrafos de capa 2 cuyo objetivo sea mover un porcentaje de ruteo.**
   Queda retirada la propuesta de párrafo de completitud para la descripción de `Edit`, que era de
   esa clase.
4. **La ceguera bajo delegación es del instrumento, no pérdida de datos.** Verificado leyendo el
   contenido, no la existencia del fichero: las rondas delegadas dejan
   `runtime/…/session-*/subagents/agent_*/session.json`, y ahí está **todo** — nombre de tool y
   argumentos íntegros. Viajan en la clave `tool_calls` del mensaje del asistente, forma OpenAI
   (`[{id, function:{name, arguments}}]`, puesta en `loop/agent_loop.py:673-677`), y el resultado
   se empareja por `tool_call_id` (`:726-730`). **No** son bloques `tool_use` dentro de `content`:
   un lector que sólo mire `content` ve mensajes de asistente vacíos y concluye que no hay traza.
   Todo instrumento de medida lee `tool_calls`; una medición que sólo mire la sesión padre, o sólo
   `content`, no vale.

**Qué corrige de `P12`.** El catálogo dice que bajo delegación la conducta *«es inmedible»* y que
*«no hay nada que leer»*. Es falso: hay traza completa en disco. Lo que no se puede es leerla desde
la sesión padre. `P12` sigue en pie como conducta observada —incluida una ronda que abrió **dos**
subagentes para un renombrado de una línea—, pero pierde su corolario de inmedibilidad, y con él la
razón por la que los pasos 1, 2 y 3·T1 de la primera pasada orgánica se dieron por no medibles.

**Lo que NO deroga.** `D-24` manda igual: el cierre de conducta lo da la pasada orgánica del usuario,
y las corridas `--print` —incluidas las 8 de esta medición— son observación, nunca aval. `D-08` sigue
mandando sobre lo que sí cierra: la semántica se resuelve leyendo el fuente de A. Y no deroga el
catálogo `gpt-5.x-conducta-vs-claude.md`: los fenómenos siguen anotados, sólo dejan de ser deuda que
se paga en redacción.

**Dónde se aplica.** Todo el censo de guardas y las fases siguientes. Es regla de gobierno.

---

## D-26 · Una guarda fail-open se cierra; una frase del canónico sólo entra si existe el mecanismo que la sostiene (2026-08-15)

> ⚠ **Honestidad de origen: no es una decisión del usuario.** Es resolución de ejecución tomada por
> `D-06` al pagar `FIND-WT4`/`FIND-WT2`, y se escribe aquí porque su segunda mitad —una omisión
> deliberada— es exactamente lo que el siguiente ciclo «arreglaría» copiando la frase que falta.

**Qué la originó.** El paso `W2` del censo. `ExitWorktree` prometía en su descripción rehusar el
borrado si el worktree tiene *«uncommitted files or commits not on the original branch»*, y la
conducta no lo sostenía en tres puntos, leídos contra `ExitWorktreeTool.ts` 1→EOF (`D-08`):

1. **No contaba commits.** No existía el homólogo de `git rev-list --count ${originalHead}..HEAD`
   (`:100-110`) porque `EnterWorktree` **nunca guardaba el HEAD de partida**. La mitad de la promesa
   no era portable: le faltaba el dato.
2. **La guarda era fail-OPEN.** `if rc == 0 and out.strip() and not discard` — un `git status` que
   falla (índice bloqueado, ref corrupta) daba paso al `worktree remove --force`. A es fail-CLOSED y
   lo dice en el propio fuente: *«callers that use this as a safety gate must treat null as "unknown,
   assume unsafe". A silent 0/0 would let cleanupWorktree destroy real work»* (`:67-70`).
3. **El mensaje no enumeraba nada.** Donde A dice cuántos ficheros y cuántos commits se van a
   perder y en qué rama, B decía una frase genérica.

**Lo construido** (`tools/native/worktree.py`): `original_head` capturado en `EnterWorktree` y
guardado en `_WORKTREE_KEY`; `_count_worktree_changes` homólogo de `countWorktreeChanges` con su
semántica de `None` = *no verificable, asumir inseguro*, incluida la rama en que el `status` va bien
pero **falta la línea base** —ahí A también devuelve `null` en vez de afirmar 0—; la guarda pasa a
fail-closed con los dos mensajes de A (`:198` y `:217`), el segundo enumerando ficheros y commits con
sus plurales; el recuento se repite antes de borrar para que la salida diga qué se descartó
(`:256-259`, `:299-309`); y los textos de salida y del no-op pasan a ser los del canónico.

**La segunda mitad, que es una NO-inyección.** `prompt.ts:28` lleva un bullet más: *«Clears
CWD-dependent caches (system prompt sections, memory files, plans directory) so the session state
reflects the original directory»*. **No se porta.** B no tiene ninguna de las tres cachés: el prompt
de sistema no se recomputa —se hornea una vez en `build_runtime`, `FIND-CFG-HOT`—, la memoria no está
cableada (`FIND-MEM-WIRING`) y `get_plan_file_path` (`capabilities/plan/plan_file.py:52`) es función
pura con token fijo por sesión, no una memoización sobre el cwd como `getPlansDirectory` de A.

**Y esto NO contradice `D-22`.** `D-22` manda construir el mecanismo que falta cuando eso traslada
**conducta** del canónico. Aquí no hay conducta que trasladar: una caché existe para no recomputar, y
B no recomputa. Construir tres cachés para poder limpiarlas sería inventar el problema y luego
portar la solución. Lo que sí queda dicho —y es la deuda real, ya nombrada— es que B no recompone el
prompt de sistema al cambiar de directorio; el bullet entra el día que `FIND-CFG-HOT` se pague, no
antes. **La regla, generalizada:** una frase de la descripción se porta cuando existe la conducta que
la respalda; portarla antes es `FIND-E11-3` (anunciar palancas inexistentes) y borrar la carencia en
silencio es `homologar-es-trasladar-conducta`. El camino que queda es el tercero: **declararla donde
se mide** — `PROCEDENCIA-DESCRIPCIONES.md`, cuya fila de `ExitWorktree` decía «el resto se porta» y
era falsa. Eso era `FIND-WT2`.

**Lo que NO deroga.** `D-25`: nada de esto se acredita por la ruta que elija el modelo. Lo que cierra
es la semántica —la guarda rehúsa, enumera y no destruye— y es código, luego admite garantía. Y
`D-24` sigue mandando para el cierre del paso: falta la pasada orgánica del usuario.

---

## `D-27` — El cwd del padre viaja al fork, o el subagente trabaja en otro sitio

**Resolución de ejecución bajo `D-06`, no decisión del usuario** (honestidad de origen).

En A el directorio de trabajo es del PROCESO (`process.chdir` + `setCwd`,
`EnterWorktreeTool.ts:94-96`), así que la pregunta «¿qué cwd ve un subagente?» no existe: ve
el del padre porque sólo hay uno. En B el cwd es un CABLE del ctx (`tool_use.py:110`), y un
cable que no se copia en el fork es un cable roto: `RuntimeContextForker.fork` construía el
ctx del hijo sin él y `root_context_modifier` sólo corre en la raíz
(`local/runtime.py:474`), de modo que todo subagente nacía en la raíz del confinamiento
aunque el padre estuviera dentro de un worktree.

Se resuelve propagándolo por el `ForkSnapshot`, que es el vehículo que el runtime ya usa
para lo que el hijo hereda (permisos, pool, capabilities). No se resuelve leyendo un global
ni haciendo `chdir` en el proceso: el runtime es multi-sesión y un `chdir` de una sesión
mataría a las otras — la razón por la que B tiene el cable en primer lugar.

Lo que NO se toca, y por qué: que el subagente no reciba `EnterWorktree`/`ExitWorktree`
(filtro `safe_for_background`, `agent_loop.py:191-194` + `registry.py:33-34`) es conducta
correcta, no el hueco. Un hijo capaz de eliminar el worktree de su padre sería el defecto.
El modelo puede seguir delegando el TRABAJO dentro del worktree; el CIERRE es del hilo que
lo abrió.

---

## D-28 · La calibración va en EMBUDO: el pool publica sólo lo cerrado más lo que se mide (2026-08-15)

**Disparador, verbatim del usuario.** Tres turnos consecutivos, y los tres son la decisión:

1. *«lo que pasa es que es sumamente complejo llegar a calibrar una maquina que tiene muchas
   piezas, te imaginas un reloj que lo ajustes cuando terminaste de construirlo? tenemos 24
   tools + agentes + modos plan y worktree.»*
2. *«lo que se tendria que hacer, según mi punto de vista, hipotesis empirica, probar sets
   organicos pero de la misma tool e ir cerrando cuando la calibracion de su prompt nos de
   resultados consistentes y asi vamos cerrando el embudo, seguido de los modos plan y worktree
   de forma individual, ahora con enunciados que requieren el uso de tools que ya sabemos que si
   fallan es el prompt del modo y no de la tool y finalmente los agentes.»*
3. *«primero haria una ronda individual de 4 casos … enunciados que deberian lograr que la tool
   siendo probada sea consistente, luego enunciados que requieran usarlas en varias tareas, para
   ver la competencia.»*

Y antes, fijando el tamaño de muestra: *«el tamaño de la muestra por mas que lo pongas a 100, no
nos da un indicador de si ese enunciado es suficiente, para esto con 4 se puede conseguir y luego
se ve, esto es un tema de calibracion, ensayo / error hasta que este estable.»*

**Qué la originó.** Dos tandas de calibración del cierre de worktree (`wt4`, 7 sesiones válidas;
`wt5`, 4) dieron `0` cierres correctos con `ExitWorktree` **en ambas**, y ninguna de las dos medía
lo que decía medir: los borrados por shell venían en su mayoría de subagentes que no tienen prompt
propio —`agentic_code` no puebla `agent_resolver`, luego no hay catálogo de agentes ni system
prompt de hijo— y de un `bash` cuya cláusula de vecindario no estaba calibrada. Se estaba ajustando
el escape con el movimiento entero montado y girando.

### El invariante

**No se mide una pieza cuyas dependencias siguen sin calibrar.** Todo lo demás son consecuencias.

### Las cuatro etapas, y el pool de cada una

El embudo no ordena sólo las mediciones: **ordena el pool publicado**. Cada etapa anuncia las
piezas ya cerradas más la que se está calibrando, y nada más. Conducción por `--denied-tool`, que
**no deniega la llamada: elimina la tool del pool ensamblado** (`assemble_tool_pool`,
`tools/pool.py:74-90`, homologado de `tools.ts:311-326`) — el modelo ni la ve. Verificado en vivo:
pool 25 sin deny, 24 con `--denied-tool Agent`, diferencia exactamente `{Agent}`.

| etapa | pool publicado | qué acusa un fallo |
|---|---|---|
| 1 · tools | 25 − `Agent` − `Enter/ExitPlanMode` − `Enter/ExitWorktree` = **20** | la descripción o el nombre de la tool |
| 2 · modo plan | + `Enter/ExitPlanMode` = 22 | el prompt del modo |
| 3 · modo worktree | + `Enter/ExitWorktree` = 24 | el prompt del modo |
| 4 · agentes | + `Agent` = **25** | el prompt del agente |

Esto elimina la contaminación en vez de descartarla a posteriori. En la etapa 1, si el modelo
delega, la tool acaba llamándose en el hijo con el mismo pool y la ronda deja de medir la
descripción; con `Agent` fuera, no puede ocurrir. En las etapas 2 y 3 no hay rondas contaminadas
que descartar: la delegación es imposible.

**El precio, dicho:** las etapas 1–3 miden contra un pool que no es el final, luego un marcador
cerrado ahí **no está cerrado contra el reloj montado**. Eso no es un defecto del método sino su
última etapa: al abrir la 4 se publica el pool completo y **se repasan los marcadores de las tres
anteriores**. Ese repaso es la prueba del reloj montado, y es donde aparecería un acoplamiento como
el ya observado entre la cláusula de `bash` y el canal de `worktree`.

### El protocolo por tool: dos fases, dos preguntas, dos arreglos

- **Fase A — aislamiento.** 4 rondas orgánicas con enunciados que apuntan inequívocamente a esa
  tool y sin alineamiento de capa 2 que le sirva de muleta. Mide si la descripción nombra su propio
  oficio. Fallo aquí ⇒ el problema está en las superficies 2 (nombre) o 3 (`function.description`).
- **Fase B — competencia.** Enunciados que la piden dentro de un trabajo de varias tareas, con
  otras tools en juego. Fase A verde y fase B roja ⇒ la descripción se sostiene sola pero pierde
  con rivales, y el arreglo **no es describir mejor lo que hace sino delimitar el vecindario** — la
  cláusula de «esto no se hace desde aquí», que es lo que el canónico pone en `bash` con su bloque
  de `find`/`grep`/`cat` (`BashTool/prompt.ts:275-291`).

Una tool no cierra sin pasar las dos.

**El enunciado no nombra la tool.** Decisión del usuario: *«y en los enunciado de prueba igual no
forzar con frases que digan que se debe usar la tool que estamos probando»*. Es la misma regla del
texto aplicada al instrumento — un enunciado que nombra la pieza no mide su descripción, mide la
obediencia, y saldría verde con la descripción vacía. «Apuntar inequívocamente a esa tool» significa
por tanto **que el objetivo sólo sea satisfacible por su oficio**, no que se la mencione. Tres
grados, con distinto valor probatorio:

1. **Objetivo puro** — se describe el resultado y jamás el mecanismo (*«renombra la variable alpha
   por total en calc.py»*). Es el único grado que acredita de verdad.
2. **Vocabulario del dominio** — se nombra el concepto, no la tool (*«trabaja en un worktree
   aparte»*). Admisible cuando es lenguaje que un usuario real emplea, con la evidencia declarada
   como más débil. Las tandas `wt2`–`wt5` estaban en este grado y cerca del borde: *«sal del
   worktree eliminándolo»* casi dicta la acción.
3. **Dirigido** — se nombra la tool. Reservado a la excepción que `D-12 · c` ya preveía —cuando el
   objetivo no puede discriminar dos tools redundantes por diseño— y **con su régimen más débil
   declarado en el propio caso**. Disfrazarlo de objetivo es `no-debilitar-la-prueba`.

**Los rivales de la fase B tienen que estar ya cerrados** — el invariante un nivel más abajo. La
fase B de cada tool se corre contra el conjunto ya cerrado, siguiendo el orden de ataque 1→12 del
censo, y las primeras tools tienen fase B pobre por definición; lo cubre el segundo término del
criterio de cierre. **La fase B se amortiza:** la competencia es propiedad del conjunto, no de una
tool, así que un solo enunciado multi-tarea puntúa a la vez el marcador de todas las que
intervienen.

### Criterio de cierre

Una tool se cierra cuando **en 4 rondas orgánicas seguidas la decisión es la prevista** y **su
marcador no mueve el de ninguna tool ya cerrada**. El segundo término no es opcional: es lo único
que impide que calibrar la pieza 20 descalibre la 3 sin que nadie se entere.

Cuatro rondas, no más, por decisión expresa del usuario: el tamaño de muestra no indica si un
enunciado es suficiente; esto es calibración por ensayo y error hasta que sea estable.

### Cuentas

El pool publica **25**; quitando `Agent` quedan **24**, y fase A son `24 × 4 = 96` rondas
individuales. Cuatro de esas 24 son puertas de modo y su fase A cae en las etapas 2 y 3, no en la
1. `clone_repository` sale del embudo hasta que se migre la tool de git entera de A (decisión previa
del usuario), de modo que fase A queda en **92** rondas y la etapa 1 en **76**. A eso se suma el
cuerpo —menor, por amortización— de rondas de competencia.

### Qué retira este método

- **`wt4` y `wt5` dejan de ser prueba del enunciado de `EnterWorktree`.** `0 de 7` y `0 de 4` no
  acusan a ese texto: acusan al conjunto. Se conservan como observación de que los subagentes sin
  prompt borran worktrees por shell, que es hallazgo de la **etapa 4**.
- **Las dos inyecciones en `tools/native/worktree.py`** (bloque `## Ownership` y texto de salida de
  `EnterWorktree`) son material de la etapa 3 hecho fuera de turno y medido contra fondo sucio.
  Quedan en el árbol **sin acreditar** (`D-12`: efecto sin conducción no acredita) y se vuelven a
  medir cuando le toque a `worktree`; si no mueven marcador, salen.
- **La cláusula de worktree en `bash.py`** sí es de la etapa 1 y sí movió su propio canal (borrados
  por shell de 6/7 a 2/4), pero le faltan sus 4 rondas limpias: entra a la cola de la etapa 1 como
  pieza a cerrar, no como cerrada.

### Bloqueo previo a abrir la etapa 1

**`FIND-WT6`** — las fs-tools resuelven los relativos contra `roots[0]` y no contra `ctx.cwd`
(`tools/fs_env.py:135-136`, `:170`, `:186`). Mientras eso siga así, cualquier ronda que ocurra
dentro de un worktree mide un cable roto, no un enunciado. Es dependencia de cableado, no de
prompt, y se paga antes de abrir el embudo.

### Tensión con `D-25`, declarada y no disimulada

`D-25` retiró la ruta elegida como criterio de cierre y prohibió escribir párrafos cuyo objetivo
sea **mover un porcentaje** de ruteo. `D-28` no lo deroga, lo modula, y la diferencia es el listón:

- `D-25` nació contra la propuesta de subir a 12 rondas para justificar un párrafo que llevara el
  marcador de 4/8 a 1/12 — mejora de porcentaje, que concede el fenómeno de antemano. Aquí el
  listón es **consistencia 4/4**, no mejora; un 3/4 no cierra nada.
- `D-25` estableció que la única superficie que traslada fiabilidad al arnés es la **5**
  (`tool_choice`/`allowed_tools`). El embudo la usa **como instrumento de calibración**, que es
  precisamente lo que la hace utilizable sin clasificador de intención.
- **La línea que separa lo prohibido de lo legítimo la fija el usuario, verbatim:** *«en fase de
  calibración mientras no usemos explicitamente en el prompt algo que se alinie a un caso en
  particular, sino se expresa de forma clara y generica no estamos violando nada.»* Lo prohibido
  nunca fue redactar: es **redactar hacia un caso**. Escribir el párrafo que pone verde ESE
  enunciado sigue vedado por `D-20 · 6`; enunciar de forma clara y genérica lo que la pieza hace, y
  dónde termina su vecindario, **es el trabajo de esta fase**. `D-25 · 3` queda modulada en ese
  sentido: lo que sigue retirado es el parche ajustado al caso y la persecución de porcentajes, no
  la redacción genérica.
- **Prueba de admisión, dos preguntas.** ¿Hace falta decir «cuando el usuario pida X» para
  enunciarlo? (`D-20 · 6`, en pie). ¿El texto sólo se entiende teniendo delante el enunciado de la
  ronda? Si cualquiera de las dos da que sí, es texto de caso y no entra — por muy verde que lo
  ponga el marcador.
- **Lo que `D-28` NO afirma:** que el ruteo quede determinista en producción. En la etapa 4 vuelve
  el pool completo y la ruta observada allí se **registra**, no se rotula como puerta — `D-25 · 1`
  sigue vigente para eso.
- **`D-25 · 2` sigue siendo lo que cierra un paso del censo**: la semántica y la traza. `D-28` es
  método de la fase de calibración, no un criterio de cierre nuevo para el censo de guardas.
- **`D-24` sigue mandando:** el veredicto binario lo emite la pasada orgánica del usuario.

**Origen de cada pieza, por honestidad.** El embudo, su orden, las dos fases y las 4 rondas son del
usuario. Son míos y quedan sujetos a revocación: la tabla de pools por etapa, el segundo término del
criterio de cierre (no mover marcadores ya cerrados), la amortización de la fase B y el bloqueo por
`FIND-WT6`.

**Dónde se aplica.** Toda la fase de calibración de prompts de tools, modos y agentes. Es regla de
gobierno.

## `D-29` — `FIND-WT6` pagado: el cwd del turno es la base de expansión, y el parámetro es inesquivable

**Fecha:** 2026-08-16. **Estado:** inyectado y medido por delator; **no cerrado** — falta la pasada
orgánica del usuario (`D-24`).

### El defecto

`ConfinedFilesystem.resolve` expandía todo relativo contra `self._base_dir` = `roots[0]`, el root del
workspace. `EnterWorktree` mueve `ctx.cwd` al worktree (`tools/native/worktree.py`, su `modifier`) y
**no toca `roots`** — no ensancha el confinamiento ni monta una segunda costura, y no hace falta que
lo haga porque `.worktrees/` cuelga del propio root. Consecuencia: dentro de un worktree,
`read_file("calc.py")` abría el `calc.py` de la RAÍZ. El canónico no tiene ese agujero:
`expandPath(path, baseDir?)` cae a `getCwd()` (`utils/path.ts:34`) y `GlobTool.getPath` hace
`path ? expandPath(path) : getCwd()` (`GlobTool.ts:89`), con el cwd por sesión en `AsyncLocalStorage`
(`utils/cwd.ts:12`).

### El corte

`resolve(self, token, *, for_write, cwd)` — **keyword obligatorio, sin default**. Base local
`cwd or self._base_dir`; sustituye a `self._base_dir` en las tres apariciones del cuerpo (rama de
plan-file, chequeo de confinamiento, path devuelto). `_base_dir` sobrevive como fallback para el
`cwd=None` (integrador que no lo declara).

**Por qué obligatorio y no opcional.** El criterio ya estaba escrito en el propio fichero: la
expansión tiene que ocurrir en «un punto que ningún consumidor pueda esquivar». Un parámetro con
default es por definición esquivable, y el modo de fallo que se paga aquí es exactamente el de un
llamante que no se enteró. El censo de llamantes —hecho por propagación, no por búsqueda: la costura
sólo se alcanza teniendo la referencia, luego basta leer dónde nace (`RuntimeConfig.fs`) y dónde se
entrega (`execution/local/runtime.py:460-461`, raíz y fork por el mismo punto)— acota el conjunto a
**siete**, todos en `tools/native/`, y ninguno fuera del runtime: el integrador construye la costura
inline en `agentic_code/composition.py` y nunca llama a `resolve`. Con el conjunto acotado, romper la
firma es barato y comprobable; dejarla opcional sería regalar el defecto al octavo llamante futuro.

**Los siete pasan `cwd=ctx.cwd`:** `read_file` · `write_file` · `glob_tool` · `grep_tool` ·
`file_edit` · `clone_repository` · `worktree`. En los tres últimos el path ya es absoluto y la base
es indiferente; se pasa igual, porque es lo que hace inesquivable el parámetro.

**El confinamiento no se relaja.** `path_in_allowed_working_path` sigue midiendo contra
`roots`/`write_roots`: un `cwd` fuera del workspace hace que el relativo caiga fuera y dispara
`PathOutsideWorkspace`. Un `cwd` externo no es una llave, es un error que se acusa.

### Delator (`D-12`)

Raíz `ws/` con `calc.py` («raiz») y `ws/.worktrees/w/calc.py` («worktree»), mismo token `"calc.py"`:

| medida | resultado |
|---|---|
| `cwd=None` | `ws/calc.py` → «raiz» (conducta de `HEAD`) |
| `cwd=ws/.worktrees/w` | `ws/.worktrees/w/calc.py` → «worktree» |
| llamada sin `cwd` | `TypeError: missing 1 required keyword-only argument: 'cwd'` |
| `cwd=/etc`, token `secreto.txt` | `PathOutsideWorkspace` |

Las cuatro filas verdes. Falta el veredicto orgánico.

### Efecto lateral asumido

Los ocho ficheros tocados quedan **sin comentarios** (regla `sin-comentarios-en-codigo`): se borran
los que había, incluidos los bloques de justificación de `FIND-PLAN-FILE-1` y `FIND-C6-1` en el
cuerpo de `resolve`, el docstring de módulo de `clone_repository.py` y las notas de homologación de
las descripciones. Sobreviven las directivas `# noqa` y el texto que es superficie de producto
(descripciones, schemas, mensajes al modelo), que no se ha tocado en ninguno. La justificación que
vivía en esos comentarios está aquí y en el censo.

---

## `D-30` — El deny explícito PREVALECE sobre `--dangerously-skip-permissions` (2026-08-17)

**Origen, dicho con precisión.** El usuario la elevó como decisión pendiente al cierre de la ventana
anterior —había dos tests en rojo afirmando la conducta contraria y no los reescribí a propósito—, y
al plantearle las opciones eligió **resolverla contra el canónico antes de decidir**. Leído el
canónico, respondió: *«si has revisado en el canonico, entiendo que la propuesta de ajuste esta
homologada, no es decisión mia a menos que lo que propones no lo sea»*. Es decir: `D-08` la resolvió,
y lo que quedaba era ejecución (`D-06`).

### Lo que dice el canónico, leído 1→EOF

- **El orden del pipeline.** `hasPermissionsToUseToolInner` numera los pasos y resuelve el deny en el
  **1a** (`utils/permissions/permissions.ts:1171`), ~100 líneas antes del atajo
  `shouldBypassPermissions` del **2a** (`:1268`). No hay rama que salte el 1a.
- **Enunciado explícito.** Al justificar por qué las ask rules de contenido sobreviven al bypass:
  *«This must be respected even in bypass mode, just as deny rules are respected at step 1d»*
  (`:1238-1243`). Y el encabezado de `checkRuleBasedPermissions` (`:1061-1063`) llama a los pasos
  previos al 2a *«the subset that bypassPermissions mode respects»*. Los pasos 1a, 1b/1f, 1d, 1e y 1g
  son inmunes al bypass **por diseño**, no por accidente.
- **La bandera no toca la configuración.** `--dangerously-skip-permissions` sólo empuja
  `'bypassPermissions'` a `orderedModes` (`permissionSetup.ts:725`), y
  `initializeToolPermissionContext` arma el contexto con `mode: permissionMode` **y**
  `alwaysDenyRules: { cliArg: parsedDisallowedToolsCli }` en el mismo objeto (`:978-991`). En todo el
  módulo no hay un punto donde entrar en bypass vacíe `alwaysDenyRules`; lo único que se vacía son
  las **allow** rules, y sólo al entrar en modo auto (`stripDangerousPermissionsForAutoMode:510`).

### La regla

**El deny es CONFIGURACIÓN, no una confirmación que el bypass pueda saltarse.** Quien pasa la bandera
renuncia a que le pregunten, no a lo que él mismo prohibió. En B eso son los dos cortes de `823e68e`
(`agentic_code/src/agentic_code/permissions.py`): `seed()` no vacía `always_deny` —de modo que
`assemble_tool_pool` no publica lo denegado— y `handle()` comprueba `denied` **antes** del atajo de
bypass.

### Los dos tests en rojo eran el defecto, no el parche

`test_dangerous_bypass_grants_protected_tools_without_prompt` y
`test_dangerous_bypass_executes_protected_tool_without_reader` usaban `bash` a la vez como tool
«protegida» y como `denied`. Con esa fixture no afirmaban lo que su nombre dice —que el bypass evita
la pregunta— sino que **el bypass revoca configuración**, que es justo lo que el paso 1a niega. Es el
patrón de `D-17 · 1`: un arnés que renuncia a la condición que el test dice medir. Se reescribe el
arnés contra el criterio (tool protegida **no** denegada) y se añaden los dos casos que fijan la
regla: uno en la política y otro **por efecto en disco** con el pool publicado como testigo. Ambos
acreditados en rojo contra la conducta anterior por inyección revertida desde copia verificada por
`sha256` (`D-12 · b`), nunca con `git checkout`. Suite: **218 verdes**.

### Lo que NO deroga

`D-28` sigue mandando sobre el método del embudo — y esta decisión es su condición de posibilidad:
sin deny > bypass, `--denied-tool` no acota el pool bajo `--dangerously-skip-permissions` y la ronda
deja de medir la etapa que dice medir (fue así como el defecto se detectó: pool de 21 donde tocaban
10). `D-08` conserva su alcance: el consumidor DETECTA, el canónico DICTA.

---

## `D-31` — El núcleo NO persigue el determinismo: persigue el resultado funcional (2026-08-19)

**Origen.** Cierre de la fase A del embudo (`D-28`). Tras montar tres brazos —forma homologada,
forma openclaw y forma PI— y medir 60 rondas sobre la fixture `logmerge`, el usuario cortó la veta
entera: *«un control determinista implica heuristica, alineamiento a casos especificos, por tanto en
una solucion agentica que es dinamica por naturaleza no encaja a menos que estemos ante una solucion
que solo resuelve un numero finito de casos de uso»*, y fijó el criterio: *«cualquiera sea la
conjugacion de las tools que use el agente, el resultado funcional sea el esperado»*.

### La medición que llevó ahí

Tres brazos, cuatro enunciados, cinco repeticiones. **Acierto: 20/20 en los tres.** Lo único que los
separó fue la ruta: 9 formas distintas de 20 en PI, 8 en openclaw, 15 y 13 en las dos corridas de la
homologada; σ intra-enunciado 0.32 / 0.41 / 0.99 y 0.72. Y la homologada fue **la más barata**
(2.40 llamadas frente a 3.00). Menos dispersión se pagó con más coste, y el acierto no se movió.

Los brazos menos dispersos lo eran por tener **cuatro herramientas en vez de seis** —menos entre qué
elegir—, no por saber nada del caso. Eso es determinismo por reducción de la superficie, no por
alineamiento.

### La evidencia que cierra la puerta a la palanca textual

Baseline sobre las 40 rondas de la ruta homologada (`s` y `u`): `read_file` tras `write_file`, **0 de
40** —el sello de `write_file` no tiene nada que inhibir ahí—; `read_file` releyendo un fichero que
`grep` ya había devuelto, **8 de 40**, y en el enunciado e2 **6 de 10**.

En `u2_2` el `grep` devolvió `patterns.py:3: LEVEL_NAMES = [...]` —la respuesta completa del
enunciado, con su número de línea— y cerró con
`«Every match is listed above, quoted verbatim from the file — open a file only when you need context
beyond the matched lines.»` El modelo abrió el fichero igualmente. Mismo estímulo y misma frase de
cierre, `u` releyó en 4 de 5 rondas y `s` en 2 de 5.

**La palanca redactada ya está puesta y no sostiene.** Añadir más cierres en más tools es repetir lo
que la evidencia acaba de refutar.

### La regla

- **Determinismo por alineamiento** —«en esta situación, haz esto»— es heurística, es finita por
  construcción, y **no entra en el núcleo**. Cabe en un integrador que resuelve un número finito de
  casos de uso, porque ése sí los conoce.
- Lo que el núcleo persigue es que **el resultado funcional sea el esperado sea cual sea la
  conjugación de tools** que el agente elija. La variación de ruta no es un defecto mientras el
  resultado se sostenga.
- Corolario para las descripciones y la superficie: no se redactan para inducir una ruta, sino para
  que cualquiera de las rutas posibles llegue al mismo resultado.

### Lo que se retiró al tomarla

Todo. Los paquetes `forma_openclaw/` y `forma_pi/` de `agentic_runtime`, los prompts clonados
`system_prompt_openclaw.py` y `system_prompt_pi.py` de `agentic_code`, las ramas por variable de
entorno en `tools/factory.py` y `composition.py`, y el punto de extensión `cierre` que llegué a
construir sobre `write_file` con delta de conducta cero. Revertido a mano desde copia verificada por
`sha256`, nunca con `git checkout` (`D-12 · b`). Los dos repos quedan byte a byte en `bce0289`.

No se construyó el **registro de entrega** que propuse —anotar qué contenido ya se entregó verbatim
para que `read_file` no lo repitiese—: era la misma heurística, sólo que estructural, y por
estructural más difícil de deshacer.

### Lo que esta decisión deja al descubierto

El instrumento no mide lo que ahora manda. `embudo/acierto.py:38` exigía en e2 un número de línea
tras el nombre del fichero: eso es **convención de cita**, no resultado funcional, y marcó en rojo
dos rondas cuya respuesta era correcta. Y los cuatro enunciados de la fixture no pueden fallar por
ruta —toda conjugación llegaba a la respuesta—, así que 460+ rondas dicen mucho de la ruta y casi
nada del criterio que acabamos de adoptar. La fixture que hace falta es la que contiene casos donde
**conjugaciones distintas producen resultados funcionales distintos**: truncamiento, lectura obsoleta
tras editar, filtrado por `.gitignore` que cambia el conjunto de respuestas.

### Lo que NO deroga

`D-28` sigue mandando sobre el método del embudo. `D-08` conserva su alcance. Y la arquitectura por
capas queda reforzada, no tocada: el núcleo no se adapta al integrador, y ahora además **no decide
por él cuánto determinismo necesita**.

---

## `D-32` — `grep`: una búsqueda que no se ejecutó no puede parecerse a una que no encontró nada (2026-08-19)

**Origen.** Primer paso de la fase viva tras `D-31`: pulir la `description` que llega al modelo,
tool por tool. `grep` no tiene fila en `PROCEDENCIA-DESCRIPCIONES.md` —su descripción ya era
divergencia declarada, no port— pero sus **defectos de resultado** sí se resuelven contra el
canónico (`D-08`).

### El principio, enunciado por el propio canónico

`GrepTool.ts:436-440`: *«If ripgrep times out, it throws RipgrepTimeoutError which propagates up so
Claude knows the search didn't complete (rather than thinking there were no matches)»*. La regla que
de ahí se extrae y que gobierna el corte: **una búsqueda que no se ejecutó no debe parecerse a una
búsqueda que no encontró nada.** Es criterio de resultado funcional puro, no de ruta: no induce qué
tool usar, hace que la salida no mienta.

### Los cuatro casos, reproducidos en frío antes de tocar nada

| caso | conducta anterior | por qué era falsa |
|---|---|---|
| `glob: "a.py\|b.py"` | `[No matches for this pattern: 0 file(s) searched…]` | la alternancia no es sintaxis glob; `pathlib` la toma literal y el patrón nunca se probó contra nada |
| `path` inexistente | `[No matches for this pattern: 0 file(s) searched…]` | el directorio no existe; A lo corta en `validateInput` (`:201-232`) |
| `glob: "a.py,b.py"` | `[No matches…]` | **A lo soporta**: `:391-409` parte por espacios y por comas |
| `.pyc` en el árbol | `bin.pyc:3: \x00LEVEL\x00…` presentado como *«quoted verbatim from the file»* | ni es texto ni es verbatim; ripgrep salta binarios por defecto y A lo hereda gratis |

El tercer caso explica el primero: el modelo quiso decir «estos tres ficheros», la superficie no
sabía expresarlo, y alcanzó `|`, que falló callando (`D-21`).

### El corte

1. **`path` inexistente → error**, con el texto homologado de A:
   `Path does not exist: {path}. Note: your current working directory is {cwd}.`
   (`GrepTool.ts:201-232` + `utils/file.ts:213`).
2. **Multi-glob** portado de `:391-409`: separación por espacios y por comas, unión de resultados,
   deduplicada y ordenada.
3. **Filtro de binarios en la etapa de SELECCIÓN**, no como post-paso — instrucción del usuario:
   *«en el caso 2 tendriamos que aplicar un filtro para que solo opere sobre archivos no binarios»*.
   Olfateo de byte nulo en los primeros 8 KiB. Así `searched` y la determinación de «el glob no
   seleccionó ficheros» se calculan sobre el conjunto buscable.
4. **El filtro se CUENTA, no se calla**: la línea de alcance declara cuántos se saltaron por binarios
   y cuántos por ilegibles. Y si el glob seleccionó N ficheros y **todos** se saltaron, se dice eso —
   no «no seleccionó ficheros», que sería otra mentira.
5. **Glob que no selecciona nada → mensaje propio**, distinto de «sin coincidencias», que nombra el
   remedio correcto (ampliar el glob) en vez de invitar a cambiar el patrón.

### Divergencia añadida por mecánica de Python

`pathlib` **tampoco expande llaves**, así que `*.{ts,tsx}` —justo lo que la descripción de A enseña
en `GrepTool/prompt.ts:12`— habría fallado igual de callado. Se expande a mano (`_expandir_llaves`).
Es `D-22`: lo que no está SE CREA, porque a A se lo regala ripgrep.

### Omisión declarada, no callada

No se porta el *«Did you mean …?»* de `validateInput`: depende de `suggestPathUnderCwd`
(`utils/file.ts:228-267`), que es una heurística de «carpeta del repo caída» que no tenemos. Queda
**declarada y vigilada** (`declarar-no-es-pagar`), no rotulada como paridad.

### Lo que cambió en la `description`

Las líneas que decían *«Results include every readable file under `path`, generated and binary ones
among them»* pasaban a ser mentira con el corte 3, y se reescriben. Se añaden dos hechos —cómo
expresar varios globs, y que un glob vacío se reporta como tal— **redactados como propiedades del
resultado, no como inducción de ruta**, conforme al corolario de `D-31`.

---

## `D-33` — `bash`: el resultado afirma el efecto, y la tool deja de censar el terreno de las demás (2026-08-19)

**Origen.** Segundo paso de la fase viva tras `D-32`, misma mecánica: `BashTool` del canónico leído
1→EOF (`BashTool.tsx`, `prompt.ts`, `commandSemantics.ts`, `utils.ts`), defectos reproducidos en
frío antes de tocar nada — 20 rondas de cuatro enunciados de grado 1 que son de `bash`
(`embudo/bloque-bash.sh`, bloque `bx`) más 20 de los enunciados de búsqueda (bloque `bz`).

### Lo que la reproducción en frío dejó ver

En `bz` **`bash` no aparece ni una vez**: los dos apuntes `rival` del censo que nacieron ahí
—`ls -la <dir>` y `git status --short`— los curó el trabajo previo de `glob` y `grep`, y se
consumen sin corte propio. Lo vivo estaba en el bloque propio de `bash`: `ls` dentro de `bash` en
5/5 rondas del enunciado de escritura, `git status --short` sin relación con el encargo en 4/5,
`git rev-parse --show-toplevel` sin relación en 5/5, y verificación con otra tool de un efecto que
`bash` ya había producido en 3/5.

### El corte en la `description`

1. **Se retira el bullet del `ls`** (`prompt.ts`: *«If your command will create new directories or
   files, first use this tool to run `ls` to verify the parent directory exists»*). Es `D-08` en su
   forma menos cómoda: la instrucción **se contradice con su propia lista** tres líneas antes
   (*«File search: Use glob (NOT find or ls)»*), y en B su premisa es falsa —`write_file` crea los
   directorios padre. En A conviven porque Claude resuelve la contradicción a favor de la lista; con
   gpt-5.x gana el `ls`. Medido: 7 llamadas en 5/5 rondas → **0 en 20 rondas**.
2. **Cláusula nueva de censo de repositorio**: un `git status` / `git log` / `git rev-parse` responde
   a un encargo que pregunta por el estado del repositorio y no aporta nada a ningún otro; no es un
   primer movimiento. No está en A —A lo mitiga para usuarios `ant` delegando el bloque de git en
   skills, salida que nosotros no tenemos—, así que es `D-22`. Medido: 4/5 → 1/5 y 5/5 → 1/5.
3. **Los banderines de edición en sitio se nombran** (`-i`, `-pi`, `-0pi`, `sed -i`) en el párrafo
   del intérprete, que sólo cubría `-c`, heredoc y fichero de script. El defecto observado fue un
   `perl -0pi -e`.

### El corte en el resultado

4. **`commandSemantics.ts` portado entero**: `grep`/`rg`/`find`/`diff`/`test` tienen semántica propia
   de código de salida. Antes marcábamos `is_error` con `returncode != 0`, así que un `diff` con
   diferencias o un `grep` sin coincidencias volvían como error. El comando base se extrae del
   ÚLTIMO tramo, como A (`heuristicallyExtractBaseCommand`), saltando las asignaciones de entorno
   que preceden al binario.
5. **`Exit code N` anexado al fallar**, literal de `BashTool.tsx:699`.
6. **El mensaje de interpretación llega al MODELO**, no sólo a la UI. En A `returnCodeInterpretation`
   vive en `Out` y `mapToolResultToToolResultBlockParam` no lo incluye: al modelo le llega cadena
   vacía tanto si `grep` no encontró nada como si nada se ejecutó. Es exactamente lo que cerró
   `D-32` en la tool `grep`; dejarlo abierto aquí sería sostener las dos cosas a la vez.
7. **Sello de cierre para salida vacía con éxito** (`D-22`, hermano del de `write_file`): exit 0 sin
   salida deja de ser cadena vacía y pasa a afirmar que el comando hizo lo que se le mandó y que un
   fallo habría vuelto con su código. A lo resuelve sólo en la UI (`noOutputExpected`), que al modelo
   no le llega.

### Lo que NO cierra, y por qué no es de este corte

Sobrevive en 2/5 rondas del enunciado de escritura la verificación con `read_file` + `glob` de un
fichero cuya existencia **el propio programa ya había afirmado por stdout** (`wrote 6 lines to …`,
o un `&& wc -l` que el modelo se encadena solo). No hay afirmación que añadir: ya estaba dicha dos
veces. Es la misma conducta que se atribuyó a `gpt-5.x` en la relectura tras `write_file`, y ahí
queda atribuida.

### Carencias declaradas, medidas y no pagadas

El esquema de entrada sólo tiene `command`: sin `timeout` ni `description`, y el tope está clavado
en 30 s (A: 120 s por defecto, 600 s de máximo, y parámetro). Con `pytest` o builds reales eso corta
por entorno y no por conducta. Queda **declarada y vigilada** (`declarar-no-es-pagar`), no rotulada
como paridad.

---

## `D-34` — `grep`: el glob se homologa a ripgrep, y la relectura NO es carencia de superficie (2026-08-20)

**Origen.** Tercer paso de la fase viva tras `D-33`, misma mecánica: `GrepTool.ts` (577 L),
`GrepTool/prompt.ts` y `utils/ripgrep.ts` leídos 1→EOF; defectos reproducidos en frío antes de tocar
nada — 20 rondas de cuatro enunciados de grado 1 (`embudo/bloque-grep.sh`, bloque `gx`) y 20 rondas
del mismo bloque tras el corte (`gy`).

### Lo que la reproducción en frío dejó ver

| | elige | cierra | acierto |
|---|---|---|---|
| `gx` (frío) | 20/20 | **7/20** | 20/20 |
| `gy` (caliente) | 20/20 | **5/20** | 20/20 |

`elige` estaba cerrado desde el principio: `grep` gana sus cuatro casos en las 40 rondas, sin `bash`
y sin `read_file` previo. El acierto funcional es perfecto en ambos bloques. Lo único abierto es
`cierra`, y el corte **no lo mueve**.

### El defecto determinista: `pathlib.Path.glob` está anclado, `--glob` de ripgrep no

A no implementa el filtro: se lo pasa a ripgrep (`GrepTool.ts:406-408`), donde un patrón sin `/` casa
el **nombre de fichero a cualquier profundidad**. B lo hacía con `base.glob(patron)`, que ancla en la
base. Medido sobre la fixture `logmerge`:

| patrón | `pathlib` | `rg` |
|---|---|---|
| `*.py` | **0** | **5** |
| `test_*.py` | **0** | **1** |
| `*.log` | **0** | **2** |
| `*.{py,toml}` | **0** | **6** |
| `**/*.py` | 5 | 5 |
| `src/**/*.py` | 4 | 4 |

Es exactamente el modo de fallo que legisló `D-32`: el idioma que enseñan **las dos** descripciones
—`GrepTool/prompt.ts:12` y la nuestra— devolvía `[No matches for this pattern: 1 file(s) searched…]`,
un falso negativo indistinguible de una ausencia real. Y dejaba medio muerta la expansión de llaves
que `D-32` había añadido, porque `*.{py,toml}` expande a `*.py`, que seguía dando 0.

**En frío el defecto no llegó a dispararse**: gpt-5.x escribía `**/*` (15 de 30) y `**/*.py` (7), no
el idioma corto. Pero en caliente, con la propiedad declarada en la descripción, **cambió de idioma
en el acto: 28 de 29 globs sin `/`, `*.py` siete veces**. Sin el corte, esas 28 llamadas habrían
vuelto vacías en silencio. La descripción no indujo una ruta: le devolvió al modelo un idioma que ya
quería hablar y que la superficie no sabía escuchar (`D-21`).

### El corte

1. **Glob por nombre**: patrón sin `/` se antepone `**/`, replicando `--glob`. Y **negación `!patrón`**,
   que rg soporta y B ignoraba (`_por_nombre`, conjunto `descartados`).
2. **`.gitignore` respetado** en la etapa de selección. ripgrep lo hace por defecto y A lo hereda
   gratis; es `D-22`. Cura el apunte «busca dentro de `.pyc`»: sobre la fixture, `**/*` pasa de 14
   candidatos con 4 binarios saltados a 10 ficheros limpios, los mismos 9 + `.gitignore` que da
   `rg --files`.
3. **`-A` / `-B` / `-C` / `context`** portados de `:58-67`, con las líneas de contexto marcadas
   `path-line- text` frente a `path:line: text` de las coincidencias, como rg.
4. **`-i`** portado de `:71-73`.
5. **`output_mode`** portado de `:52-57`, con `content` como defecto — **divergencia consciente**: en A
   el defecto es `files_with_matches` (`:316`), que por construcción no cierra nada y obliga a una
   segunda pasada. Adoptarlo tal cual empeoraría `cierra`. Se declara aquí, no se rotula como paridad.

### La refutación: `-C` existe y el modelo no lo usa

La hipótesis con la que se pidió el corte era que `cierra` caía porque, sin contexto, la única forma
de ver el entorno de una coincidencia era abrir el fichero — y el sello de B llegaba a prometer algo
que la tool no sabía dar. Se declaró `-C`/`-A`/`-B` en el esquema y en la descripción.

**Uso en 29 llamadas del bloque caliente: cero.** El modelo sí adoptó `output_mode` —lo pasa
explícitamente en 29 de 29— y sigue abriendo el fichero: 14 relecturas de `core.py`, 5 de
`patterns.py`, 5 de `cli.py`. `cierra` va de 7/20 a 5/20.

La conclusión es la de `D-31`, ahora con una segunda medición independiente: **la palanca redactada no
sostiene**. La relectura de lo que `grep` ya citó verbatim queda atribuida a `gpt-5.x` en
`EMBUDO-DEFECTOS.md`, no a la superficie, y no se persigue con más texto.

Consecuencia sobre el propio sello: la frase *«open a file only when you need context beyond the
matched lines»* y su sucesora *«rather than opening the file»* son inducción de ruta, y están medidas
como inoperantes. Se reescriben como propiedad del resultado —*«the lines around any of them come back
in this same result with -C, -A or -B»*— conforme al corolario de `D-31`.

### Estado en el marcador

`grep` obtiene **check en `elige`** (4/4 en los cuatro enunciados, en los dos bloques) y **no lo
obtiene en `cierra`**. No se cierra la fila.

### Lo que el corte sí paga

Un modo de fallo silencioso que el idioma real del modelo dispara en 28 de 29 llamadas, más la
paridad de `.gitignore`, negación, contexto, `-i` y `output_mode` frente a un esquema que declaraba 5
campos donde A declara 14. Que no mueva `cierra` no lo hace menos exigible: `cierra` no era suyo.

---

## `D-35` — `WebSearch`/`WebFetch`: la información se pone donde se decide, no donde se documenta (2026-08-20)

**Origen, verbatim del usuario.** Dos turnos. Primero el diagnóstico: *«la divergencia real es grave,
si el LLM tiene que construirse su propio escraper porque webseach no le dio informacion extraida no
debio apoyarse en webfetch en lugar de bash?»*. Y después, contra la palanca que yo proponía: *«y no
se resuelve con algo mas en el prompt que le brinde al llm la informacion que necesita para decidir
vs hacerlo mediante otra mas generica donde tiene mas control?»*.

### Lo que la reproducción en frío dejó ver

`WebSearchTool/prompt.ts`, `WebSearchTool.ts`, `WebFetchTool/prompt.ts`, `WebFetchTool.ts`, `utils.ts`
y `preapproved.ts` leídos 1→EOF. Bloque `wz`, 20 rondas: `elige` 20/20, `acierto` 19/20, y en 12 de 20
el modelo bajaba a `bash`; **7 de ellas a escribir un lector de HTML a mano** (`urllib` + `HTMLParser`,
un intento con `bs4`) sobre las URL que la búsqueda acababa de devolver.

### El diagnóstico, y por qué mi primera propuesta era la equivocada

Yo iba a añadir una lista NOT en la `description` de `bash` — la palanca de `D-33`, la única que había
sostenido. **El fuente la desmintió antes de tocarla:**

1. **La información YA estaba escrita**, y en la tool correcta: `web_fetch.py` dice *«The content is
   returned as markdown for YOU to extract from; it is not pre-summarized by another model»*. Aun así,
   12 de 20.
2. **La asimetría es mecánica, no retórica.** `WebSearch` y `WebFetch` llevan `deferred = True`
   (`D-19`); `bash` no. En el instante de decidir, la única tool cuya descripción está garantizada en
   contexto es la genérica. **No era persuasión: era presencia.**
3. **El canónico tiene el mismo hueco y no lo paga.** El bloque de preferencia de `bash`
   (`BashTool/prompt.ts:280-291`) enumera búsqueda, lectura, edición, escritura y comunicación, y **no
   dice nada de red**. A nunca lo sufre porque su resultado de búsqueda ya trae el contenido redactado
   por su modelo interno (`GAP-WEBFETCH-2`); en B el segundo salto queda sin nombrar.
4. **La procedencia de la URL es lo que separa los dos regímenes**, y está medido: URL dada por el
   usuario (bloque `f`) → `WebFetch` 20/20; URL devuelta por la búsqueda (bloque `wz`) → `bash` 12/20.
   Misma tool, misma descripción, mismo modelo.

### El corte

Un trailer en el **resultado** de `_serper_search` que dice que lo devuelto son títulos, enlaces y
extractos, que el contenido de una página se obtiene pidiéndola, y que no se escriba un lector propio.
Va **en el resultado y no en el prompt** porque es el único punto del turno que está en contexto justo
cuando el hueco se abre, y es además el canal que A ya usa ahí (el REMINDER que sostiene la sección
`Sources:`). **No nombra ninguna tool**: el runtime no puede suponer qué tiene registrado el
integrador.

### El marcador — `wz` (antes) contra `wr` (después), 20 rondas frías por lado

| | elige | scraper HTML | `WebFetch` usado | acierto | cierra |
|---|---|---|---|---|---|
| `wz` | 20/20 | **7/20** | 4/20 | 19/20 | 8/20 |
| `wr` | 20/20 | **1/20** | **12/20** | **20/20** | 5/20 |

`cierra` baja **por construcción y no es regresión**: el trailer prescribe una segunda llamada, luego
«tras `WebSearch` no se invoca otra tool» es inexpresable en los enunciados de grado 2. Donde `cierra`
significa algo es en los de grado 1, que siguen 20/20.

### Tensión con `D-31`, declarada

El corolario de `D-31` prohíbe redactar para inducir una ruta, porque *«cualquiera de las rutas
posibles llegue al mismo resultado»*. **Aquí las rutas NO son equivalentes, y ésa es la única razón por
la que este texto entra.** El scraper improvisado se salta todas las guardas que la tool implementa:
el tope de 10 MB, la subida http→https, el corte de redirecciones de origen distinto, el truncado a
100 K y el timeout. No es una ruta distinta al mismo sitio: es la misma respuesta con la superficie de
seguridad evaporada. Cuando dos rutas difieren en propiedades del resultado, nombrarlo es propiedad
del resultado, no inducción. Si las rutas fueran equivalentes, `D-31` mandaría y el texto no entraría.

### Lo que el residuo de `bash` destapó, y que es de otra capa

De las 13 rondas de `wr` con `bash`, casi todas son el modelo **preguntando en qué año vive**
(`date +%Y`, `date -I`, `python -c print(date.today().year)`). La `description` de `WebSearch` le exige
en mayúsculas usar el año en curso en la consulta —literal de A, `WebSearchTool/prompt.ts`— y **el
contexto no lo lleva**: verificado en el `session.json` de `wrw4_3`, el único `2026` anterior a la
primera llamada es el que el propio modelo escribe en la query. Es el mismo patrón que esta decisión
—información que falta, herramienta genérica— pero **se paga en el bloque de entorno del integrador**,
no en el runtime, y no antes de leer en el canónico dónde inyecta A la suya (`D-08`).

El resto del residuo es `gh`/`pip index` en el caso de httpx, que **lo prescribe la propia
`description` de `WebFetch`** (*«For GitHub URLs, prefer the `gh` CLI via the bash tool»*), y ruido ya
catalogado (`pwd`, `true`, `uname -a`).

### Estado en el marcador

`WebFetch` cerrado en las dos columnas (bloque `wz`: 20/20, 20/20, 20/20). `WebSearch` cerrado en las
dos con sus enunciados de grado 1 (bloques `wg`/`wh`: 20/20, 20/20, 20/20). `GAP-WEBFETCH-2` sigue en
pie y sin pagar: aunque el enrutado sea correcto, B necesita dos llamadas donde A necesita una, y el
seam de modelo secundario es decisión de contrato.

### Adenda a `D-35` (2026-08-20) — la cláusula de vecindario en `bash` NO cierra: probada y retirada

**Origen, verbatim del usuario:** *«pero pregunta en bash, no podemos decir para que no debe usarse?
a modo de experimento para ver si cierra?»*. Es la palanca que yo había propuesto primero y retirado
sin medir; se mide.

**Lo inyectado.** Una línea en la lista de preferencia de `bash`, en el estilo exacto de las que ya
están: `Retrieve a web page: Use WebFetch (NOT curl/wget, and NOT an interpreter's HTTP client)`, con
su razón (los topes que un lector a mano no aplica) y una salvaguarda para no contradecir a la
`description` de `WebFetch` en lo del `gh`.

**El marcador, bloque `wv`, mismos 4 enunciados y 20 rondas frías:**

| | `bash` | scraper real | `WebFetch` | acierto |
|---|---|---|---|---|
| `wz` (nada) | 12/20 | 7/20 | 4/20 | 19/20 |
| `wr` (trailer) | 13/20 | **1/20** | 12/20 | 20/20 |
| `wv` (trailer + cláusula) | 7/20 | **2/20** | 11/20 | 20/20 |

**No cierra.** De 1 a 2 en n=20 es ruido. La caída del `bash` total (13→7) viene del `date +%Y` de
`w4`, ajeno a lo que la cláusula prohíbe, y no se le atribuye.

**Por qué falla, leído en los dos supervivientes.** `wvw2_5` no scrapea una página: va contra
`pypi.org/pypi/httpx/json` y `raw.githubusercontent.com/.../CHANGELOG.md` — un endpoint de API y un
fichero de texto plano. **El modelo generalizó la salvaguarda del `gh` que yo mismo escribí**: si un
CLI puede hablar la API de un servicio, `urllib` también. La excepción abrió la puerta. `wvw3_5` sí es
un `HTMLParser` completo sobre las URL de Django, y ahí la cláusula simplemente no operó.

**Retirada** por `D-28` (*«si no mueven marcador, salen»*), a mano y verificando que el árbol vuelve
sin diff contra `fa50106`; nunca con `git checkout` (`D-12 · b`).

**Lo que añade a la serie.** Tercera refutación de la palanca redactada en una `description`
—`D-31`, `D-34` y ésta— frente a la única que movió el marcador, que fue el trailer en el
**resultado**. La lectura que queda: prohibir en un sitio no le da al modelo la alternativa en el
instante de decidir; informar en el punto de decisión, sí. Y una excepción escrita en una prohibición
es una superficie que el modelo generaliza, no una acotación que respeta.

---

## `D-36` — `defer_loading` es una PENALIZACIÓN DE SELECCIÓN, y dentro de un namespace se lleva por delante el contrato de conducta (2026-08-21)

> ⚠ **Honestidad de origen.** Lo que aquí se registra es **medición**. La pieza que decide el usuario
> —retirar o no `deferred` del par web, que deroga parte de `D-19`— queda **planteada, no ejecutada**:
> es `D-06 · 3`, admite más de un resultado defendible porque el reparto de `D-19` se homologó del
> canónico y esto lo rompe.

**Origen, verbatim del usuario.** *«esto va contra lo que dice la documentacion de openai»* → *«esto
también podría caer en la situación de que no lo estamos usando bien»* → *«tenemos evidencia factica
del mal uso corrijamos y volvemos a probar»* → *«si solo cambian la visibilidad de los parametros
realmente no explica porque no uso bash»* → *«aplica el namespace y volvemos a probar los 2 casos …
creo que ya voy entendiendo porque open_claw no usa defered_loading»*.

### Los dos fabricantes llaman `defer_loading` a dos mecanismos distintos

- **Anthropic:** *«the API excludes deferred tools from the system-prompt prefix»* — la tool es
  invisible. Publica números: Opus 4 de 49 % a 74 %, Opus 4.5 de 79,5 % a 88,1 % con Tool Search.
- **OpenAI:** *«the model still sees the function name and description, so in practice tool search is
  mostly deferring the parameter schema»*. No publica ningún número.

Y la guía de namespaces de OpenAI: *«we recommend using namespaces or MCP servers when possible.
**Our models have primarily been trained to search those surfaces**»*.

### Lo que lleva el cable, verificado (no inferido)

Traza externa sobre el provider real —**Azure**, no OpenAI directo (`azure-openai-responses`,
`gpt-5.4`, `api_version v1`)—, enganchada a `convert_responses_tools` y a `process_responses_stream`.
La petición **sí** lleva `defer_loading: true` en las diferidas y **sí** emite
`{"type": "tool_search", "execution": "server"}`. El stream **no trae un solo evento `tool_search`**:
cero en las 30 rondas de los cuatro bloques de namespace, cero en las trazadas sin namespace. El
descuento que `defer_loading` promete **nunca se cobra**.

Corrección de dos cosas que llegué a afirmar y la traza refutó: que diferir sacaba la tool de lo
invocable (el modelo llamó `WebSearch` diferida como primera acción, sin buscar) y que el
descubrimiento moría en el límite del turno (no hay descubrimiento que muera).

### El mecanismo, medido: penalización, no puerta — y sólo en lista plana

En **lista plana** `defer_loading` no oculta nada: **demota**. Con una alternativa residente
plausible, la tool diferida pierde entera; sin alternativa, se usa igual pero peor.

| bloque | config | ¿alternativa residente? | resultado |
|---|---|---|---|
| `wz` | `bash` res · par web dif | sí, `bash` | el par web pierde → `bash` 9/10, scraper 4/10 |
| `wn`/`wg` | todo residente | — | `WebFetch` 10/10, `bash` 0/10 |
| `wb`/`wd` | `bash` dif · par web res | sí, el par web | `bash` pierde → **0/10** |
| `wsd` | `bash` dif · tarea sólo-`bash` | **no** | `bash` **5/5**, pero 2 llamadas en 3/5 y una ronda sin responder |

Esto responde la objeción del usuario: no es visibilidad de parámetros. Mover el flag del **par web**
mata a `bash` sin tocar el flag de `bash` porque cambia **quién compite contra él**.

### Dentro de un namespace el mecanismo es otro, y ahí está el coste real

Namespaces aplicados (`web_lookup`, `shell_exec`, `session_config` — **`web` es nombre reservado**, la
API responde 400: *«Function 'web.WebSearch' is not allowed in reserved namespace 'web'»*). Cuatro
bloques, capa de hints apagada:

| bloque | ns | par web | `bash` | `Sources:` | acierto | `bash` | scraper |
|---|---|---|---|---|---|---|---|
| `na` | sí | **dif** | res | **0/10** | **0/10** | 0/10 | 0/10 |
| `nb` | sí | res | res | **10/10** | **10/10** | 0/10 | 0/10 |
| `nd` | sí | res | res | — | kernel 5/5, 1 llamada | 5/5 | — |
| `nc` | sí | res | **dif** | — | kernel 5/5, **2 llamadas en 2/5** | 5/5 | — |

**El delator es `Sources:`.** El mandato vive en la `description` de `WebSearch` («CRITICAL
REQUIREMENT … MANDATORY - never skip»). Diferido **en plano** se cumple (`wz`/`wf` lo exigen para su
acierto 9/10). Diferido **dentro del namespace** se cumple **0/10**, sin cambiar una letra del texto.
Residente dentro del mismo namespace, **10/10**.

**La regla que sale de ahí: la `description` de una tool ES su contrato de conducta, y en un namespace
`defer_loading` lo retira.** Y el modelo sin contrato **sondea**: `read_file` de rutas deliberadamente
inexistentes (`ws/does-not-exist`), `clone_repository` a ciegas — `naw3_3` clonó `django/django`
entero, **105 s**, para leer unas release notes que estaban a un `WebFetch`. El mismo sondeo apareció
en `wsd_5` (clone a `https://example.invalid/does-not-matter`).

### Los tres malos usos, nombrados

1. **Sin namespace.** Enviamos lista plana; los modelos de OpenAI están entrenados sobre namespaces y
   MCP. **Ya no es la explicación de por qué `tool_search` no dispara**: con namespace tampoco dispara.
2. **11 tools.** Por debajo del umbral que publican los dos fabricantes para usar tool search siquiera
   (Anthropic: *«standard tool calling … is a better fit when you have fewer than 10 tools»*).
3. **El round-trip no está implementado.** `process_responses_stream` sólo trata `reasoning`, `message`
   y `function_call`; `convert_responses_messages` re-emite sólo esos tres. Un `tool_search_call` /
   `tool_search_output` se **descartaría** y no se podría re-emitir. Defecto latente real, hoy
   **inactivo** porque el modelo no busca nunca.

### Por qué openclaw no usa `deferred_loading` — la lectura que queda

`defer_loading` cambia contexto por conducta a un precio pésimo para un agente de código, donde casi
toda la conducta vive en las descripciones. En plano paga una penalización de selección invisible
—salvo cuando hay rival, y entonces es total— sin recuperar nada, porque `tool_search` no dispara. En
namespace, que es la forma que el fabricante recomienda, retira el contrato de conducta y el modelo
degenera en sondeo. Con 11 tools no hay nada que comprar. Es coherente con la serie `D-31`/`D-34`/`D-35`
por el otro extremo: allí la palanca redactada no sostenía; aquí **retirar el texto sí mueve el
marcador**, y en la dirección mala.

### Lo que queda planteado al usuario (`D-06 · 3`), no ejecutado

**Retirar `deferred` de `WebSearch` y `WebFetch`.** Deroga parcialmente `D-19`, cuyo criterio era
*«el reparto queda igual al del canónico y sólo al del canónico»*. A favor: `wn`/`wg`/`nb` dan
**10/10 en acierto y 0/10 en scraper**, contra 9/10 y 4/10 con el par diferido; y **A tiene su propia
escotilla** — `isDeferredTool` (`ToolSearchTool/prompt.ts`) exceptúa tools que *«must be available
turn 1, not behind ToolSearch»*, de modo que aplicar ese criterio al par web es usar la regla de A, no
divergir de ella. En contra: `D-19` se homologó leyendo `shouldDefer` fichero a fichero, y esto abre
la puerta a revisar las 15. **El árbol queda hoy con el par web residente** (`deferred = False` en
`web_search.py` y `web_fetch.py`), que es la configuración medida como buena; si el usuario prefiere
el reparto de `D-19` intacto, se revierte.

**Namespaces: no se adoptan.** No disparan `tool_search`, no aportan nada con todo residente (`nb` =
`wn`/`wg`) y **renombran las tools** (`web_lookup.WebSearch`), lo que rompería las referencias por
nombre del integrador — la familia de `FIND-MCP1`. El experimento vivió entero en un `sitecustomize.py`
externo; ningún fuente del proyecto lo lleva.

---

## `D-37` — El mecanismo es nuestro y la convención decide su uso: nativas residentes, MCP diferidos (2026-08-21)

**Origen, verbatim del usuario.** *«en gpt-5.x no hay ahorro alguno, y el comportamiento de 3 pasos de
claude se pueden emular por software»* → *«el poder usar el flag defer con false para todas las tools
nativas esto sera por convención, solo los MCP los manejaremos con defer true … el mecanismo se
implementa pero ahora con las convenciones definimos su uso»* → *«nosotros al momento de registrar un
MCP, podriamos agregarle defer=True, sino lo trae»* → *«podemos de nuestro lado trabajar variables en
el registro fuera de especificacion para marcar comportamientos internos nuestros»* → *«ya las nativas
esta cerrado, si es por convencion la variable en metadata puede existir, pero en las nativas no se
usa y eso lo podemos documentar»*.

Cierra la pieza que `D-36` dejó **planteada y no ejecutada** (`D-06 · 3`), y la cierra por encima de lo
que allí se preguntaba: no «retirar o no `deferred` del par web», sino **separar mecanismo de política**.

### Lo que el comparativo con el canónico dejó establecido

`ToolSearchTool.ts` (471 L) y `ToolSearchTool/prompt.ts` (121 L) leídos 1→EOF. El `defer_loading` de A
es un **lazo cerrado de tres piezas, todas código de A**:

1. **Ocultar** — `isDeferredTool` marca la tool y la API la excluye del prefijo del system prompt.
2. **Anunciar** — un `system-reminder` lista los nombres **con su contrato de fallo**: *«schemas are NOT
   loaded — calling them directly will fail with InputValidationError. Use ToolSearch with query
   `select:<name>`»*.
3. **Recuperar** — `ToolSearchTool.call` corre **en cliente**, puntúa, y devuelve bloques
   `tool_reference`.

**Nosotros portamos sólo el flag.** Sin anuncio y sin recuperación. Y el `tool_search` de servidor que
emitimos no dispara jamás (`D-36`: cero eventos en 30 rondas trazadas). Un flag sin sus otras dos piezas
no difiere: **demota**.

Dos hallazgos laterales que quedan fijados aquí. El `searchHint` de A **sí puntúa** (+4,
`ToolSearchTool.ts:283-285`), de modo que la premisa de `D-18` era correcta para el ranking; lo que es
falso es que el modelo llegue a **leerlo** — `formatDeferredToolLine` devuelve sólo `tool.name`, y el
experimento `exp_xenhnnmn0smrx4` se paró el 21 de marzo por no mostrar beneficio. Y `isDeferredTool`
**ya trae escrita la convención 2 del canónico**: `alwaysLoad` se comprueba primero, y `isMcp === true`
difiere **siempre**.

### Lo que la especificación MCP 2026-07-28 hace y lo que no

Verificada en fuente primaria. Mata el **coste vivo** —núcleo sin estado: sin handshake `initialize`,
sin `Mcp-Session-Id`, cada petición autodescriptiva por `_meta`, `server/discover` opcional,
`tools/list` con `ttlMs`/`cacheScope`—. **No mata el coste de prefijo, y lo empeora:** `Tool` sigue
siendo `name`, `title`, `description`, `icons`, `inputSchema`, `outputSchema`, `annotations`; las
definiciones **crecieron**. La paginación es sólo por cursor. La cita que lo decide: *«Deterministic
ordering enables clients to reliably cache the tool list and improves LLM prompt cache hit rates **when
tools are included in model context**»* — la especificación **asume** que las tools van en contexto y
optimiza cacheando, no escondiendo. Y al quitar la sesión **empuja contrato hacia las descripciones**:
la política de retención de las Stateful Tools *«should be stated in the creation tool's description …
so the model can see it when deciding to create state»*.

**Corrección de lo que yo mismo había concluido:** dije que el serverless podía hacer que el disparador
del lazo de tres pasos no llegara a activarse nunca. Es al revés.

### La decisión, en siete puntos

1. **Nativas → `deferred = False` por convención.** Deroga en parte `D-19`, con motivo declarado: en
   gpt-5.x la `description` es el contrato de conducta y perderla produce sondeo (`D-36`). El árbol ya
   está así (`web_search.py`, `web_fetch.py`); bajo esta convención **eso deja de ser una derogación a
   revertir y pasa a ser la norma**.
2. **MCP → `deferred = True` estampado en el registro**, y **reaplicado en cada recarga de
   `tools/list`**. La excepción se declara en nuestro registro o en la configuración del usuario, nunca
   se toma del server.
3. **El registro admite metadatos internos fuera de especificación** —`defer_loading`, `when_to_use`,
   los que hagan falta—. La conversación con el server se ciñe a la especificación; el registro es
   nuestro. **Única guarda de implementación: ningún campo entrante se mapea a un campo interno.** Un
   `annotations` o un `_meta` del server no puede escribir política nuestra, y la propia especificación
   lo respalda: *«clients MUST consider tool annotations to be untrusted unless they come from trusted
   servers»*.
4. **Forma uniforme, uso diferenciado.** Los metadatos internos existen en **toda** entrada del registro
   por contrato. En las nativas `when_to_use` **no se usa**, y no por acuerdo sino por mecánica: sus
   únicos lectores son el anuncio y la recuperación, por donde una tool residente no pasa. En las
   nativas la conducta va en la `description`, que es nuestra.
5. **`when_to_use` se renderiza** en anuncio y recuperación — al contrario que el `searchHint` de A, que
   puntúa y nunca se muestra.
6. **El atributo `deferred` NO viaja al wire.** Su único consumidor será el lazo de tres pasos, cuya
   recuperación devuelve `description` + `inputSchema` **completos**, no una lista de nombres.
7. **Acción inmediata:** dejar de emitir `defer_loading` y el bloque
   `{"type": "tool_search", "execution": "server"}` en `convert_responses_tools`
   (`agentic_models/.../openai_responses_shared.py`). Es la mitad que hoy sólo cobra la penalización.

### Alcance de la refactorización autorizada

**Ahora:** esta entrada y la anotación en `D-19`; el corte 7; la reescritura del test que queda
incompatible; el censo de las nativas 1→EOF para aplicar el punto 1.

**Aplazado por acuerdo** (*«ahí no hay refactorización»*): los puntos 2, 3 y 4 —registro con metadatos
internos, `when_to_use`, y el lazo de tres pasos— son **construcción**, no refactor. Bloqueados además
por dos cosas: los tokens de gpt-5.x agotados hasta fin de mes, que impiden validar en consumidor real
(`D-15`), y una dependencia sin verificar — **qué versión de MCP habla hoy nuestro runtime** (las trazas
muestran `obsidian` conectando por SSE con sesiones).

### Convención de trabajo que el usuario fijó al autorizar

*«cuando decimos vamos a refactorizar, incluye que vamos a descartar tests que queden incompatibles y
haremos nuevos que se adhieran a lo que estamos ahora implementando»*. No colisiona con
`no-debilitar-la-prueba`: un test se descarta porque **el criterio cambió**, y el nuevo se escribe
contra el criterio nuevo — nunca se ablanda uno para ponerlo verde.

### Lo que NO deroga

`D-36` intacto: es la medición sobre la que esto se apoya. `D-08` conserva su alcance — el canónico
dictó qué es el lazo de tres pasos; lo que decide no adoptar su reparto es la medición en nuestro
modelo. `D-22` sigue mandando: el lazo que falta **se crea**, no se cierra la fila con «no existe en B».

---

## `D-38` — El lazo de tres pasos, por software: ejecutado (2026-08-21)

**Encargo, verbatim del usuario.** *«El cambio ademas de dejar de emitir defer_loading, era homologar
las 3 etapas que usa canonico para el proposito no basado en mecanismo defer, sino en software»* y
*«si, integremos la parte que le toca a MCP»*. Ejecuta el punto 7 de `D-37` y, con él, el punto 1 y la
parte MCP del punto 2 que ya era expresable sin tocar el registro.

### Lo que se movió

1. **`convert_responses_tools`** (`agentic_models/.../openai_responses_shared.py`) deja de emitir
   `defer_loading` y el bloque `{"type": "tool_search", "execution": "server"}`. El mecanismo del
   provider ya no viaja en el cable. El metadato `Tool.defer_loading` y la capability
   `native_tool_search` del catálogo **se conservan**: son hechos ciertos sobre la Responses API y el
   conocimiento de proveedor vive en el proveedor (`D-21`); lo que cambia es que nadie los consume.
2. **`is_deferred_tool`** (`tools/deferred.py`) adopta la convención 2 del canónico: `isMcp ⇒ diferida
   SIEMPRE`, por regla estructural (`is_mcp_tool`, duck-typing sobre `mcp_info`), no por que el
   adaptador recuerde estampar el atributo. `ToolSearch` nunca se difiere a sí misma.
3. **`SimulatedDeferredStrategy` → `SoftwareDeferredStrategy`**, y `NativeDeferredStrategy`
   **eliminada**. Ya no hay dos ramas: el lazo es de software, siempre. Con ello caen
   `supports_native_tool_search` (de `models/protocol.py` y `models/caller.py`) y el mapeo
   `defer_loading=` de `_dict_messages_to_context`, que era su único productor.
4. **Etapa 2 (anunciar) homologada al literal de A**, incluido el contrato de fallo que faltaba:
   *«Their schemas are NOT loaded — calling them directly will fail with InputValidationError. Use
   ToolSearch with query "select:<name>[,<name>...]" to load tool schemas before calling them»*. Las
   centinelas `_ADDED_HEADER`/`_REMOVED_HEADER` no cambian, así que el escaneo que reconstruye lo ya
   anunciado sigue casando con lo rendido (`FIND-DEFER-1`).
5. **Etapa 3 (recuperar)**: ya era cliente y se queda; su `description` adopta el `<system-reminder>` y
   el `InputValidationError` de A. **Divergencia que se conserva** (antes en comentario, aquí): A
   devuelve sólo NOMBRES y el schema viaja en bloques `tool_reference` (`ToolSearchTool.ts:462-469`);
   B no tiene ese bloque de protocolo y devuelve el schema completo en el resultado. Mismo efecto.
6. **Las 13 nativas con `deferred = True`** pasan a residentes por convención (`D-37 · 1`): `Config`,
   `EnterPlanMode`, `ExitPlanMode`, `EnterWorktree`, `ExitWorktree`, `TodoWrite`, `AskUserQuestion` y
   las seis `Task*`. `search_hint` se conserva: es el ranking, no el reparto.

### Consecuencia medida, no supuesta

En un workspace sin servers MCP **ya no hay ninguna tool diferida**, luego no hay anuncio: el turno
pierde un `MessageEvent`. Se mide en el `.jsonl` real del integrador (`D-15`), no en mocks —
`agentic_code/tests/test_runtime_integration.py`. Suites del consumidor real: `agentic_code` 218/218,
`agentic_models` 52/52.

### Deuda declarada, no rotulada (`declarar-no-es-pagar`)

Las suites sintéticas de `agentic_runtime/src/agentic_runtime/tests/` referencian los símbolos
retirados (`NativeDeferredStrategy`, `SimulatedDeferredStrategy`, `supports_native_tool_search`) y
**quedan rojas a sabiendas**: están apartadas por acuerdo de fase y no se tocan ni «como anexo». Se
pagan cuando la fase las readmita.

---

## `D-39` — El medidor de contexto: facturación es suma, contexto es nivel (2026-08-25)

**Encargo, verbatim del usuario.** *«cerrar el medidor: añadir cache_read/cache_write al Usage … y
verificar contra este mismo probe»*. Precede a fijar el umbral del compactador: un umbral sobre un
medidor deshonesto no es evidencia, es una coincidencia.

### El defecto

`AgenticModelsCaller` construía el `Usage` del runtime con `input`/`output` y nada más
(`models/caller.py`), descartando el `cache_read`/`cache_write` que `agentic_models.Usage` ya trae. En
un turno con prefijo cacheado, `input` es **sólo lo no cacheado**: el probe leía 14 484 → 5 622 → 970
cuando el contexto real crecía 14 484 → 20 106 → 21 076.

El total del `result` **acertaba por accidente**: la suma de los inputs no cacheados de los tres turnos
coincide con el nivel del último, porque cada incremento entra una vez. Coincidencia aritmética, no
medición — y deja de coincidir en cuanto hay un fallo de caché, una reescritura de historia o una
compactación.

### La decisión

Son dos magnitudes distintas y dejan de compartir campo:

- **Facturación = SUMA.** `input_tokens`/`output_tokens`/`thinking_tokens`/`cache_read`/`cache_write`
  se acumulan sobre el turno completo. Es lo que se paga.
- **Contexto = NIVEL.** `Usage.context_tokens = input_tokens + cache_read` es lo que el motor tuvo
  delante en ESE turno. `StreamUsage.context_tokens` guarda el del último turno y **no se suma**.

`cache_read`/`cache_write` conservan la grafía de `agentic_models.Usage`: es el mismo hecho del mismo
proveedor y renombrarlo por gusto de sufijo obligaría a traducir en el puente.

### Evidencia (`D-15`: el consumidor detecta)

Probe de `agentic_code` sobre seis módulos leídos uno a uno, provider `local`
(`unsloth/Qwen3.6-35B-A3B-GGUF:UD-IQ4_XS`), `state3` nuevo sobre el mismo `work` y el mismo path:

| turno | input | cache_read | contexto |
|---|---|---|---|
| 1 | 14 484 | 0 | 14 484 |
| 2 | 5 608 | 14 480 | 20 088 |
| 3 | 962 | 20 084 | 21 046 |

`result`: `input_tokens` 21 054 (suma) frente a `context_tokens` 21 046 (nivel) — antes eran el mismo
número. La diferencia de ~20 tokens con la corrida previa (20 106 / 21 076) es que el modelo no repite
su salida palabra por palabra: el turno 1, que no depende de la generación, coincide exacto.

### Deuda declarada, no rotulada (`declarar-no-es-pagar`)

1. **`tui.py:809-810`** sigue leyendo `input_tokens + output_tokens` como ocupación de contexto: con el
   input no cacheado eso mostraba 1 335 en el turno 3 donde había 21 046. La corrección es una línea
   (`usage.context_tokens + usage.output_tokens`) y **no se aplica aquí**: la TUI la trabaja Codex en
   paralelo y no se sobrescribe.
2. **`execution/local/runtime.py:562-567`** pasa `session.usage.input_tokens`/`output_tokens` al
   registry, y **nadie puebla nunca `session.usage`**: el runtime reporta 0 y el 21 054 lo acumula el
   integrador por su cuenta. Medido y vigilado; no bloquea el umbral del compactador porque el
   integrador tiene el dato.

---

## `D-40` — El modelo local es un STOPGAP con fecha: la ventana se cierra el 2026-09-01 (2026-08-25)

**Origen, verbatim del usuario.** *«el uso del modelo local tiene como ventana temporal hasta la
reposicion del credito de azure desde donde consumimos la familia de modelos gpt.5.4 que es el 1ro de
setiembre»*.

**Qué la originó.** `D-37` ya anotaba de pasada *«los tokens de gpt-5.x agotados hasta fin de mes»*
como uno de los dos bloqueos de los puntos 2–4. Desde entonces el modelo local
(`unsloth/Qwen3.6-35B-A3B-GGUF:UD-IQ4_XS`, provider `local`) es el sujeto de toda medición en
consumidor real — el probe de `D-39` incluido. Eso no estaba escrito en ningún sitio como **régimen
temporal**, y sin fecha un stopgap se convierte en la configuración por defecto sin que nadie lo
decida.

### La decisión

1. **El modelo local es un sustituto de disponibilidad, no un cambio de sujeto.** La familia que este
   desarrollo ejecuta sigue siendo **gpt-5.x sobre Azure** (`azure-openai-responses`), y es contra
   ella contra la que se homologa la conducta.
2. **La ventana va del agotamiento del crédito al 2026-09-01**, fecha de reposición. A partir de ahí
   el sujeto de medida vuelve a ser gpt-5.4 y el local queda como lo que es: un motor de conveniencia
   para ejercitar cableado sin gastar crédito.

### Qué vale y qué no vale medido en el local

La línea es la de `D-25 · 2`, y no hace falta inventar otra:

- **Vale — es CÓDIGO y admite garantía.** La **semántica** (lo que una tool hace con sus argumentos,
  sus errores, lo que deja en disco) y la **traza**. `D-39` es de esta clase: que `cache_read` viaje
  y que `context_tokens` sea nivel y no suma es aritmética del puente, y el proveedor sólo aporta los
  números. Por eso el medidor **cierra** aunque se haya verificado contra el local.
- **No vale — es CONDUCTA del modelo.** Todo marcador del embudo (`D-28`): `elige`, `cierra`, ruta,
  sondeo, adopción de un idioma de glob. Una tool **no se cierra** con 4/4 rondas del modelo local.
  Sería la forma exacta de `no-debilitar-la-prueba`: medir en el sujeto barato y rotular el resultado
  como si fuera el del sujeto real.

### Consecuencia operativa

- Toda medición de conducta hecha en esta ventana se anota **con el modelo dicho**, y entra como
  observación, nunca como cierre de fila del marcador de las 19 tools.
- Los puntos **2, 3 y 4 de `D-37`** —registro con metadatos internos, `when_to_use`, y el lazo de tres
  pasos en su parte MCP— siguen aplazados por `D-15` (sin consumidor real no hay cierre) y **su
  desbloqueo tiene fecha**: el 2026-09-01, no «cuando se pueda».
- **Queda abierta y no decidida** la propuesta de diferir las cinco tools de mayor esquema en el
  perfil local para que el censo quepa en su ventana. Es política del **perfil local**, luego vive y
  muere con este stopgap; y por `D-37 · 1` las nativas van residentes por convención, así que una
  excepción por perfil necesita decisión explícita del usuario (`D-06 · 3`) y no se ejecuta por
  conveniencia de la ventana. Si el 1 de septiembre llega antes que la necesidad, **decae sin pagar**.

### Lo que NO deroga

`D-37 · 1` intacto: nativas residentes por convención. `D-24` y `D-28` intactos: el veredicto de
conducta lo emite la pasada orgánica del usuario sobre el sujeto real. `D-39` no se reabre: lo que
acredita es del puente, no del proveedor.

---

## D-41 · 2026-08-25 · El umbral del compactador: dos mecanismos, uno por config

### El hecho

Las cuatro constantes de A (`services/compact/autoCompact.ts`, leído 1→EOF) son **absolutas**, no
porcentuales: `MAX_OUTPUT_TOKENS_FOR_SUMMARY=20_000`, `AUTOCOMPACT_BUFFER_TOKENS=13_000`,
`WARNING/ERROR_THRESHOLD_BUFFER_TOKENS=20_000`, `MANUAL_COMPACT_BUFFER_TOKENS=3_000`. Están
calibradas sobre la ventana de 200 000 en la que corre A, donde cuestan el 16,5 % y dejan el umbral
en 167 000 (83,5 % de la ventana). Sobre gpt-5.4 en Azure (272 000 / 128 000) siguen sanas: efectiva
252 000, umbral 239 000, aviso 219 000, bloqueo 249 000.

Sobre la ventana de 32 768 del perfil local **se degeneran**: reserva 4 096 + buffer 13 000 = 52 % de
la ventana, umbral 15 672 —que la sonda de `D-39` (14 484 → 20 088 → 21 046) ya rebasa **en el turno
2**, con seis módulos leídos y ningún trabajo hecho— y banda de aviso **negativa** (−4 328), o sea un
tramo del cálculo de A que no tiene dominio por debajo de ~33 000.

### La decisión

**Los dos mecanismos se implementan, y cuál se consume es config.** No es «elegir uno»: el canónico
es el que gobierna al sujeto real (gpt-5.4) y el local es lo que la limitación de ventana permite
mientras dure el stopgap de `D-40`. Hoy se consume el **local**; se conmuta sin tocar código.

- `canonical` — la aritmética de A, literal, constantes incluidas.
- `local` — las **mismas** constantes escaladas por `ventana/200_000` con tope `1.0`. Conserva la
  PROPORCIÓN de A en vez de inventar números: sobre 32 768 da efectiva 29 492, umbral 27 363 (83,5 %
  de la ventana, la misma cuota que A sobre 200 000), aviso 24 087, bloqueo 29 001. Por encima de
  200 000 el tope hace que los dos mecanismos sean **el mismo**, luego el sujeto real no ve
  divergencia alguna.

### El medidor, homologado de paso

`getTokenCountFromUsage` (`utils/tokens.ts`) cuenta
`input + cache_creation + cache_read + output`. `D-39` dejó `Usage.context_tokens` en
`input + cache_read` y declaró el `+ output` como deuda del integrador. El umbral se compara contra
exactamente ese número, así que se homologa **antes** de fijar nada: `context_tokens` pasa a sumar
los cuatro. Con ello la deuda de `tui.py:809-810` queda **pagada sin tocar la TUI** — esa línea sólo
tiene que leer `usage.context_tokens`, y quien la toque es Codex.

### Dónde vive

- `agentic_runtime/context/window.py` (nuevo) — constantes, `ContextBudget`, `ContextPressure`, las
  dos políticas y `resolve_context_window_policy`. Genérico: el núcleo no conoce al integrador.
- `agentic_runtime/contracts/events.py` — el medidor.
- `agentic_code`: `Settings.context_window_policy` (default `local`), `--context-policy`,
  `AGENTIC_CODE_CONTEXT_POLICY`; `UsageLedger` recibe el presupuesto y mide sobre la ventana
  **efectiva**, no sobre la bruta, y expone `pressure`.
- `agentic_code/tests/test_context_window.py` — 9 casos, verdes; la suite entera de `agentic_code`,
  227 verdes. Las entradas ya vivían en el proveedor (`Model.context_window`, `Model.max_tokens`),
  luego `D-21` se cumple sin conocimiento de proveedor en el núcleo.

### Lo que queda declarado y NO pagado

El **motor** de compactación sigue sin existir (`K6`): `contracts/compaction.py` es sólo el seam de
aporte. Lo fijado aquí es el **umbral y su medida**, que es lo que el enunciado pedía; el lector que
dispara la compactación al cruzarlo es el paso siguiente, y por `D-22` se construye, no se declara
ausente. `session.usage` sin poblar (`execution/local/runtime.py:562-567`) sigue medido y vigilado
desde `D-39`: no bloquea, porque el integrador tiene el dato por el `DoneEvent`.

---

## D-42 · 2026-08-25 · El motor de compactación (`K6`): lo decidido en el tramo 1

`D-41` fijó el umbral y su medida y dejó el motor declarado y no pagado. Esta entrada abre el arco de
seis tramos que lo paga, y registra lo decidido **al tomarlo**, no al cerrarlo: quedan cinco tramos por
delante y esta entrada se extiende, no se reescribe.

### Encargo, verbatim del usuario

*«el punto 5. lo que NO entra es un infeliz comentario, si tu mision es implementar canonico para los
modelos con que vamos a trabajar entonces no hay un no entra, lo hay pero para el modelo local»*. La
primera versión del anuncio traía una sección «lo que NO entra» con cinco exclusiones. Se retiró
entera: no hay catálogo de exclusiones, hay **escalado por política** sobre el mecanismo de `D-41`.

### El hallazgo empírico que reorienta el tramo (`D-15`: el consumidor detecta)

*«lo que si me pasaba con el modelo local … era que cuando terminaba el llm volvia a entrar en modo
thinking, suprimimos ese comportamiento … ese comportamiento se suprimio en el otro proyecto
~/python/prueba_modelo_local»*. Leído entero ese proyecto (`agent/compact.py`, `agent/loop.py`,
`agent/llm.py`, `agent/context.py`, `tests/test_compact.py`, `README.md`), la patología **no es** «el
modelo vuelve a pensar» en abstracto:

El servidor arranca con `--reasoning-budget 2048 --reasoning-budget-message "Cierra el razonamiento y
responde."` (README). Cuando el modelo agota ese techo, **el propio servidor le inyecta esa frase
dentro de su stream de razonamiento**, y esa orden inyectada descarrila la petición de resumen. El
remedio que funcionó tiene tres capas, no una:

| capa | mecanismo | cita |
|---|---|---|
| transporte | `extra_body.chat_template_kwargs = {"enable_thinking": False}` | `llm.py:74-79` |
| prompt | contra-instrucción explícita contra el mensaje inyectado por el servidor | `compact.py:33-35` |
| detección | `MIN_RESUMEN_CHARS=600`: resumen-migaja ⇒ se DESCARTA la compactación y se conserva el historial entero | `compact.py:41`, `loop.py:348-356` |

Más un freno de encadenamiento que no es de thinking: tras compactar no se recompacta hasta que el
historial crece un 50 % (`loop.py:330`).

### Convergencia, no invención

A **también** apaga el pensamiento en la llamada de compactación: `thinkingConfig: {type:'disabled'}`
(`compact.ts:1305`). El arreglo del modelo local y el canónico dicen lo mismo por vías distintas. En B
la vía es `ThinkingConfig(enabled=False)`; el `except: reintenta sin ello` de la prueba es descarte
silencioso y **no se porta** (`D-21`): si el puente levanta `UnsupportedModelOptionError`, el motor de
compactación lo captura, reintenta una vez sin la opción y **lo declara** en el evento y en la traza.

Además, el descarte estructural se conserva como garantía independiente del motor: la llamada de
compactación **no añade mensaje de asistente al historial**, luego sus bloques de razonamiento no
entran nunca. Es la única capa que vale en cualquier proveedor — pero no basta, porque no impide que
el razonamiento se coma `max_output_tokens` y devuelva la migaja. De ahí que el suelo de resumen sea
mecanismo y no adorno.

### Divergencia declarada: la compactación va sin tools

A manda tools en las dos vías: la de streaming manda `[FileReadTool]` (`compact.ts:1290`) y la del
fork manda **el toolset entero del padre** para que case la clave de caché (`prompt.ts`,
`NO_TOOLS_PREAMBLE`). B no tiene fork ni caché compartida de prompt, y `createCompactCanUseTool`
(`compact.ts:1125-1134`) deniega toda ejecución de todos modos. B manda **sin tools y sin preámbulo**:
el preámbulo de A existe para explicarle al modelo por qué ve tools que no puede usar, y sin tools no
hay nada que explicar. Es resolución estructural, no recorte de prompt.

### Lo decidido en el tramo 1

1. **El estimador se construye** (`D-22`): `context/estimation.py` homologa `tokenEstimation.ts:203-435`
   bloque a bloque, incluido el plano de 2000 para `image`/`document` que evita cobrar ~325 000 tokens
   por un PDF, y `truncate_to_tokens` para el recorte por cabeza de los tramos 4 y 5.
2. **El ancla sustituye al paseo por `message.id`.** `tokenCountWithEstimation` de A retrocede hasta el
   último registro con `usage`, saltando hermanos que comparten `message.id`. B no lleva `usage` dentro
   del mensaje: lo trae el `DoneEvent`. Se registra un `UsageAnchor(context_tokens, message_count)` en
   el momento exacto en que la medida es cierta, y se estima sólo la cola posterior. El problema de
   hermanos no existe por construcción. Un ancla **rancia** (historial más corto que el ancla) se
   descarta y se estima entero, en vez de sumar una medida que ya no corresponde.
3. **Las cinco `POST_COMPACT_*` de A** (`compact.ts:122-130`) entran como campos de `ContextBudget` y
   **escalan** por la política local. 5 ficheros × 5 000 en una ventana de 32 768 serían el 80 % del
   contexto; escalados dan 0,81 ficheros y el suelo de 1 evita que la restauración quede muerta.
4. **Los dos guardas empíricos NO escalan.** `min_summary_chars` (600) y `recompaction_growth_ratio`
   (1,5) son medida de `prueba_modelo_local`, y escalar 600 por 0,16 da 96 caracteres — exactamente la
   longitud de migaja que el guarda existe para rechazar. Son constante por política: canónica los
   declara desactivados (`0` / `1.0`) porque A no los tiene — sólo comprueba que el resumen no sea nulo
   (`compact.ts:493`) —, y declararlos desactivados no es inventarle a A una conducta que no tiene.

### Vocabulario que se fija aquí

**Vuelta** = una iteración del lazo (una llamada al modelo y sus despachos de tools). **Turno** = un
intercambio con el usuario (`AgentLoop.run`). La compactación dispara en la frontera de **vuelta**, a
mitad de tarea, antes de `callModel`. La trampa está en el propio código de B: `_turn` y
`ctx.turn_count` cuentan vueltas, mientras `ConversationState.turn_count` de `agentic_code` cuenta
mensajes de usuario.

### Corrección de diseño, registrada porque casi entra en código

El primer diseño **sustituía** `ctx.messages` por el historial post-compactación. Es incorrecto y A no
lo hace: A conserva el array y filtra con `getMessagesAfterCompactBoundary` **sólo para la vista del
modelo**. En B es además cuestión de corrección: `execution/local/runtime.py` vuelca
`session.messages = list(ctx.messages)` al transcript durable que `conversation.py` recarga, y el
propio resumen apunta al modelo hacia ese transcript. Frontera y resumen se **añaden**; lo que cambia
es qué se manda al motor.

### Evidencia del tramo

`agentic_runtime/src/agentic_runtime/tests/test_context_window.py` — 20 casos, verdes. Consumidor real
(`D-15`): `agentic_code/tests/test_context_window.py` + `test_presentation.py`, 11 verdes con la forma
nueva de `ContextBudget`.

### Lo que queda abierto

Los tramos 2 a 6: prompt y motor con sus guardas, el punto de disparo en `AgentLoop.run` y el cableado
del presupuesto, la restauración post-compactación, el reintento PTL, y el parcial más `/compact` en
`agentic_code` con sus hooks. `POST_COMPACT` no existe en `hooks/protocol.py` (el enum acaba en
`PRE_COMPACT`, sin call site) y **se añade** (`D-22`).

### Lo que NO deroga

`D-41` intacto: el umbral y su medida no se reabren, se consumen. `D-40` intacto: lo medido en el
modelo local es código y aritmética, no conducta — el suelo de 600 caracteres es un hecho sobre el
presupuesto de salida de ese motor, y por eso vive en la política `local` y no en la canónica.

## D-43 · K6·tramo-2 cerrado: prompts, guardas, cortacircuitos y frontera (2026-08-25)

`context/compact/prompt.py` y `context/compact/engine.py`, más `CompactionEvent` en
`contracts/events.py` y la reexportación en `context/__init__.py`. Prueba:
`tests/test_compact_engine.py` (27 casos, verde junto a `test_context_window.py`,
`test_contracts_invariant.py` y `test_events.py` — 62 en total).

Divergencias respecto de A, declaradas (`D-21`):
1. `NO_TOOLS_PREAMBLE`/`NO_TOOLS_TRAILER` (`prompt.ts:19-26`, `269-272`) no se portan: B no manda
   tools en la llamada de compactación y ese texto enumera tools de A.
2. `ERROR_MESSAGE_PROMPT_TOO_LONG` sin el `Press esc twice…` de A (`compact.ts:293-294`): es
   interacción de la TUI de A y el núcleo no la dicta.
3. El espacio en blanco final de dos líneas del canónico (`prompt.ts:113`, `131`) no se reproduce.
4. La contrainstrucción antirrazonamiento de `prueba_modelo_local/agent/compact.py:33-35` viaja
   como bandera atada a la política `local` (`budget.min_summary_chars > 0`), en inglés.
5. `ThinkingConfig(enabled=False)` (par de `compact.ts:1305`); si el puente levanta
   `UnsupportedModelOptionError` se reintenta UNA vez sin ella y el repliegue sale por
   `CompactionEvent.reasoning_fallback` — nunca en silencio.
6. La frontera y el resumen se RINDEN; el núcleo no reemplaza la historia (el integrador decide).

---

## D-44 · K6·tramo-3 cerrado: el motor, cableado al lazo (2026-08-26)

`D-43` dejó el motor construido y sin consumidor. Esta entrada lo enchufa. Extiende `D-42`, que es
el arco de seis tramos, y no reabre nada de `D-41` ni de `D-43`.

### Dónde entra la llamada, y por qué ahí

Al **principio del cuerpo de la vuelta** de `AgentLoop.run` —tras `ctx.turn_count += 1`, antes de
`_build_tool_pool`—, que es el par de `query.ts:454-467` (autocompactación antes de `callModel`).
La llamada al modelo pasa a mandar `messages_after_compact_boundary(ctx.messages)`
(`query.ts:365`), y la frontera con su resumen se **añaden** al historial por
`_append(..., origin="compact")`, nunca lo reemplazan: es la corrección de diseño registrada en
`D-42` y la condición para que el transcript durable de `execution/local/runtime.py` siga siendo
verdad. `AgentLoop._emit` es el `emit` del motor, así que la compactación se ve en la traza del
turno como un evento más.

### La compactación no consume vuelta

`AutoCompactTracking` vive en `run()` y su `turn_counter` avanza **sólo** en la recursión posterior
a tools (`query.ts:1523`, `:1679`), nunca en la vuelta que compacta. Consumirla sería robar en
silencio de `--max-turns`: el usuario pidió n vueltas de trabajo, no n menos las que costó hacer
sitio.

### El cable del presupuesto

`RuntimeConfig.context_budget` → `LocalAgentRuntime` → `AgentLoop`, y en el integrador el
presupuesto **sube por encima de `build_runtime`**: se resuelve una vez desde el
`model_definition` y lo consumen los dos, el runtime y el `UsageLedger`. Antes lo calculaba sólo el
medidor, de modo que umbral mostrado y umbral aplicado podían divergir sin que nada lo delatara.
Con `context_budget=None` el punto de llamada no existe y el lazo sale idéntico al de antes: el
cableado es aditivo.

### Añadido sobre el enunciado del tramo, declarado (`D-21`)

**El ancla de uso se sella en el `DoneEvent`**: `UsageAnchor(usage.context_tokens,
len(<mensajes enviados>))`, y se pasa al motor. Es lo que hace que el disparo sea con números
reales y no con un `len/4` — y es lo que paga la deuda que el tramo 1 anotó («hoy el ancla no tiene
quien la alimente y todo se estima»). No estaba en el enunciado literal del tramo; se anuncia aquí
porque es mecanismo, no cosmética. `session.usage` sigue sin poblarse
(`execution/local/runtime.py`), medido y vigilado desde `D-39`: no bloquea, el dato viaja por el
`DoneEvent`.

### Divergencia declarada: el ámbito del `tracking`

El `AgentLoop` se construye **por task**, o sea por prompt de usuario. Luego
`consecutive_failures` (cortacircuitos, `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3`) y
`last_compacted_tokens` (freno de recompactación) **se reinician cada turno de usuario**, mientras
en A viven en el estado de la query. Se declara como divergencia medida y **no se persiste**: el
asiento sería estado de sesión, que es el punto 7 del § 3 del censo y no se abre por esta puerta.
Consecuencia acotada: tres fallos consecutivos de compactación dentro de un mismo prompt siguen
abriendo el cortacircuitos, que es donde el guarda importa.

### La prueba

`agentic_code/tests/test_compaction_wire.py` (`D-15`: el consumidor detecta). Dos casos: que el
contexto se compacta **dentro** del turno sin gastar una vuelta, y que el ancla dispara el umbral
que la estimación sola no alcanzaría. Los dos pasaron a la primera, así que se **falsificaron**
con `context_budget=None` —peticiones de resumen 0, el corpus viajando en la 2ª llamada— para
acreditar que miden el cable. Suites: `agentic_code` **229 passed**;
`agentic_runtime/.../tests/test_compact_engine.py` **27 passed**. Las sintéticas de
`agentic_runtime` siguen apartadas por acuerdo de fase y no se tocaron.

### Barrido de comentarios (§ 4 del censo)

Los cinco ficheros tocados quedan sin comentarios ni docstrings explicativos: `agent_loop.py`
806→559, `execution/local/runtime.py` 623→448, `factory.py` 348→232, `composition.py` 312→240,
`cli.py` 362→324. Las directivas `# noqa` se conservaron una a una y `ruff` está limpio en los
cinco. La única docstring nueva del tramo es la del test, que es la excepción declarada.

### Lo que NO deroga

`D-42` intacto y **ampliado**: la historia no se reemplaza, y ahora hay quien lo demuestra.
`D-43` intacto: sus seis divergencias de prompt y motor no se reabren. `D-40` intacto: nada de lo
acreditado aquí es conducta de modelo — es cableado y aritmética.

## D-45 · K6·tramo-4 cerrado: la restauración post-compactación (2026-08-26)

Canónico: `createPostCompactFileAttachments` (`compact.ts:1415-1464`),
`collectReadToolFilePaths` (`:1610-1655`), `truncateToTokens` (`:1666-1672`),
`shouldExcludeFromPostCompactRestore` (`:1674-1705`), y el vaciado del depósito antes de
releer (`:517-521`).

Hecho: `context/file_state.py` (depósito path→timestamp), el asiento en
`tools/native/read_file.py`, `context/compact/restore.py`, el enganche en
`compact_conversation`/`auto_compact_if_needed` (`ctx=` y `provider_messages=`), el hook
`PostCompact`, y en el lazo `_compaction_provider_messages`, que por fin le da consumidor a
`collect_compaction_context`. La docstring rancia de `contracts/compaction.py` —la que aún
afirmaba que el motor K6 no existía— se **borra**, no se reescribe (§ 4 del censo).

### `D-22` aplicado: el depósito SE CREA

B no tenía dónde anotar qué ficheros vio el modelo. Se construye, y guarda **sólo**
`path → timestamp`: la rama `FILE_UNCHANGED_STUB` de A no se porta porque B no tiene
deduplicación de lecturas, y portar el stub sin ella sería mecanismo sin consumidor.

### Divergencia declarada: el depósito vive un turno

Se asienta en `app_state.native`, o sea que **muere con el turno de usuario**, mientras en A
vive en el estado de sesión. Mismo ámbito que el `tracking` de `D-44` y por la misma razón: el
asiento persistente es estado de sesión, punto 7 del § 3 del censo, y no se abre por esta
puerta. Consecuencia acotada: se restaura lo leído en el prompt en curso, que es donde la
restauración importa.

### El catálogo de producto de A no entra

La lista de exclusión de A (fichero de plan, `claude.md`) es catálogo de producto. En el
núcleo queda el MECANISMO —`POST_COMPACT_RESTORE_EXCLUSION_KEY` en `app_state.native`,
predicado o lista de predicados, con el precedente de `EDIT_CONFIG_VALIDATORS_KEY`— y un
predicado roto se traga (`except Exception: continue`): no puede ni excluir por accidente ni
tumbar la compactación.

### Y en `agentic_code` NO se siembra, por medición

Se anunció que el integrador pondría el predicado del plan-file. **Se implementó y se
falsificó: el test pasaba igual sin él.** Motivo verificado: el depósito anota la ruta ya
RESUELTA (`plans_dir/<sesión>/plan.md`), la exención del candado de `ConfinedFilesystem` vale
para la **grafía del token** y no para esa ruta, y releerla da `PathOutsideWorkspace`. El
plan-file, por tanto, no puede restaurarse — con predicado o sin él. Se retira el predicado en
vez de dejar código sin efecto observable, y la consecuencia queda **vigilada** por
`test_the_session_plan_file_does_not_come_back_after_compacting`: si el plan-file se vuelve
releíble algún día, ese test se pone rojo y entonces —y sólo entonces— hará falta el predicado.
`agentic_code` no tiene hoy ningún otro fichero que excluir: su AGENT.md sigue diferido
(`FIND-CODE-MEM-1`) y el prompt no inyecta ficheros por turno.

### Otras divergencias, menores

El presupuesto acumulado se mide con `rough_token_count_for_message` en vez del
`jsonStringify` de A, y al no caber un fichero se hace `continue`, no `break`: filtra, no
corta. `runPostCompactCleanup` (`postCompactCleanup.ts`) no tiene homólogo — no hay qué
limpiar.

### El cap real bajo política `local`

`post_compact_max_files_to_restore` escala con la ventana: a 64K el factor es `0.32768` y el
tope queda en **1 fichero**. No es un defecto, es la política; se anota porque salió en la
prueba y porque gobierna qué se espera ver en la sonda de ejecución.

### La prueba

`test_compact_restore.py` (14) + `test_compact_engine.py` (27) = **41 verdes** en el núcleo.
En el consumidor (`D-15`), dos casos nuevos en `test_compaction_wire.py`: el fichero leído
antes de compactar vuelve detrás del resumen con su contenido de disco, y el plan-file no
vuelve. El primero se **falsificó** anulando el paso de `ctx` al motor —0 adjuntos, rojo—; el
segundo es el que destapó lo del predicado. Suite de `agentic_code`: **231 passed**. Las
sintéticas de `agentic_runtime` siguen apartadas y no se tocaron.

### Lo que NO deroga

`D-42` intacto: la historia no se reemplaza, y los adjuntos se AÑADEN detrás del resumen.
`D-44` intacto: la compactación sigue sin consumir vuelta. `D-40` intacto: esto es cableado,
no conducta de modelo.

---

## D-46 · K6·tramo-5 cerrado: el reintento por `prompt too long` (2026-08-26)

Canónico: `truncateHeadForPTLRetry` (`compact.ts:243-291`), `MAX_PTL_RETRIES`
(`:227-228`), el lazo de reintento (`:445-491`), `logEvent('tengu_compact_ptl_retry')`
(`:479-483`), la clasificación del error (`:854-899`), `groupMessagesByApiRound`
(`grouping.ts:24-50`) y `errors.ts` (`:62`, `:64-77`, `:85-96`, `:104-118`, `:562-574`).
Extiende `D-42`, que es el arco de seis tramos, y no reabre `D-41`, `D-43`, `D-44` ni `D-45`.

### El mecanismo

Cuando la petición de resumen vuelve con `prompt too long`, no se abandona: se **corta por la
cabeza** y se reintenta, hasta `MAX_PTL_RETRIES = 3`. El corte se hace en **grupos de ronda de
API** (`group_messages_by_api_round`: se abre grupo en cada `assistant`), que es el único punto
de partición que no separa a un asistente de sus resultados de tool. Del texto crudo del error se
parsea el par `N tokens > M`, y el **gap** decide cuántos grupos saltan en un solo reintento
—acumulando estimación grupo a grupo hasta cubrirlo—; si el error no es legible, cae al 20 %.
El recorte se clampa a `len(groups) - 1`: la última ronda nunca se come. Y si el resto empieza en
`assistant`, se antepone el marcador sintético de usuario (`PTL_RETRY_MARKER`), que se **retira
antes de reagrupar** en el reintento siguiente para que el segundo corte avance de verdad en vez
de volver a contar el marcador como grupo.

### El hueco del estimador se PAGA aquí, no se declara

`rough_token_count_for_message` ignoraba `role:"tool"`, así que **la masa entera de salidas de
tools valía cero**. A no tiene el hueco porque en A los resultados de tool son bloques
`tool_result` dentro de mensajes de usuario; en B viven en mensajes propios
(`agent_loop.py:533-537`). Consecuencia, si se dejaba: el acumulador nunca alcanzaba el gap, el
recorte se clampaba a `len(groups) - 1` y el primer reintento se llevaba todo menos la última
ronda. Era además ceguera del umbral de autocompactación. Se paga: `TRANSPORTED_ROLES =
{user, assistant, tool}` en `context/estimation.py`. El marcador de frontera (`system`) sigue sin
contar — es discriminante local y no viaja. Es divergencia **de forma**, no de criterio: A cuenta
`assistant`/`user`/`attachment` y con eso cubre el 100 % de lo que viaja.

### Divergencias declaradas (`D-21`)

1. **Sin `message.id` en la agrupación.** `groupMessagesByApiRound` (`grouping.ts:24-50`) agrupa
   por `message.id` compartido entre hermanos; B no lleva ese campo (el `usage` y la identidad
   vienen por el `DoneEvent`, `D-42 · 2`). Se agrupa por estructura —corte en cada `assistant`—,
   que produce las mismas rondas para el historial que B construye.
2. **El PTL también se clasifica desde el `ErrorEvent`.** En A el error llega por la excepción de
   la llamada; en B el puente puede rendirlo como texto de resumen **o** como evento. Se clasifica
   en los dos sitios (`is_prompt_too_long_text`), porque si no, el mismo fallo abortaría o
   reintentaría según por dónde entrase.
3. **`compact_conversation` NO emite el evento `failed`** que A registra como
   `tengu_compact_failed`. En B lo emite `auto_compact_if_needed` desde su `except`, y emitirlo en
   los dos sitios reportaría dos fallos por una sola compactación. Los intentos quemados viajan en
   la excepción (`PromptTooLongError.ptl_attempts`) y salen por ese único emisor.
4. **`CompactionEvent` gana `ptl_attempt`, `dropped_messages` y `remaining_messages`** (`D-22`).
   En A el reintento viaja por `logEvent('tengu_compact_ptl_retry', …)` —telemetría, no costura—.
   Sin esos campos, una compactación que sobrevivió a un PTL es indistinguible de una que no truncó
   nada, y lo perdido por cabecera queda sin declarar.

### La prueba, y su acreditación (`D-12 · b`)

`test_compact_engine.py` gana una sección C bis (11 casos nuevos) y `test_context_window.py`
reescribe `test_only_user_and_assistant_messages_count` **contra el criterio nuevo**, no ablandada:
ahora asevera que `system` sigue valiendo 0 y que `tool` vale lo que ocupa. Los dos ficheros:
**58 passed**; el núcleo entero de compactación y eventos, **152 passed, 9 xfailed**;
`agentic_code` **231 passed**, sin tocar.

Verdes a la primera, así que se acreditan por **inyección revertida desde copia verificada por
`sha256`** (`mktemp -d`, nunca `git checkout`). Nueve mutaciones, todas muertas:

| mutación | qué cae |
|---|---|
| el marcador anterior no se retira antes de reagrupar | el reintento que debía avanzar |
| el 20 % degradado a 1 grupo | el caso del error ilegible |
| el gap parseado se ignora | 3 casos |
| se quita el clamp `len(groups) - 1` | «la cabeza nunca se come la última ronda» |
| no se antepone el marcador sintético | 2 casos |
| `MAX_PTL_RETRIES = 5` | el techo de tres |
| el PTL por `ErrorEvent` sin clasificar | 3 casos |
| corte de ronda en cada mensaje | 4 casos |
| `role:"tool"` sin contar | 2 casos |

**Un test se reescribió porque no medía.** `…three_retries_is_the_ceiling…` aseveraba
`len(caller.calls) == MAX_PTL_RETRIES + 1`: la constante contra sí misma, de modo que subirla a 5
dejaba la suite verde. Se fija el número canónico (`MAX_PTL_RETRIES == 3`) y los literales (`4`
llamadas, `4` intentos). Es `no-debilitar-la-prueba` por el otro lado: no se ablandó, es que no
medía.

### Lo que NO deroga

`D-42` intacto: la historia no se reemplaza — el truncado vive en la **vista que se manda al
resumidor**, nunca en `ctx.messages`. `D-44` intacto: la compactación sigue sin consumir vuelta.
`D-45` intacto. `D-40` intacto: esto es algoritmo y aritmética, no conducta de modelo.

---

## D-47 · K6·tramo-6 cerrado: la compactación PARCIAL y el `/compact` del integrador (2026-08-26)

Canónico: `partialCompactConversation` (`compact.ts:772-1106`) y
`annotateBoundaryWithPreservedSegment` (`:349-367`); en el integrador,
`commands/compact/compact.ts` (288). Último tramo del arco. Extiende `D-42` y no reabre
`D-41`, `D-43`, `D-44`, `D-45` ni `D-46`.

### El mecanismo

Un pivote parte la conversación en dos y la **dirección** dice cuál de las dos mitades va al
resumidor: `from` resume desde el pivote y conserva lo anterior literal; `up_to` resume hasta
él y conserva lo posterior. Lo conservado se filtra de mensajes de progreso, y en `up_to`
también de fronteras y resúmenes rancios: allí el resumen nuevo va DELANTE de lo conservado,
así que una frontera superviviente ganaría el rastreo hacia atrás y se llevaría por delante el
resumen recién hecho (`:824-833`). Si la mitad a resumir sale vacía, el error nombra el lado
(`Nothing to summarize before/after the selected message.`).

### El orden del bloque deja de ser uno solo

`build_post_compact_messages` se vuelve **sensible a dirección**, y por eso
`CompactionResult` gana `direction`. En `from` lo conservado es **anterior** al resumen de la
cola: ponerlo detrás le mentiría al modelo sobre el orden de los hechos. La frontera abre el
bloque en las dos direcciones — es lo que hace que `messages_after_compact_boundary` se lleve
el bloque entero y no un trozo. Y la historia sigue sin reemplazarse (`D-42`): el bloque se
AÑADE.

### `apiMessages` no es siempre el conjunto a resumir

En `up_to` se manda sólo el prefijo (`:869-872`): es exactamente lo que ya está cacheado, y
mandarlo entero aprovecha el prefix cache. En `from` se manda la conversación completa, porque
el resumidor necesita ver lo anterior para entender de qué habla la cola.

### Divergencias declaradas (`D-21`)

1. **`preservedSegment` se porta por FUNCIÓN, no por uuid.** A escribe
   `{headUuid, anchorUuid, tailUuid}` para recoser su cadena `parentUuid`. B no tiene cadena
   que recoser —los mensajes son dicts planos en una lista persistida—, así que se anota
   `{anchor, count}`: qué ancla el segmento y cuánto mide. El ancla sigue la del canónico:
   el resumen en `up_to`, la frontera en `from`.
2. **Un solo cuerpo para el lazo de PTL y la validación del resumen.** En A los dos lazos
   son gemelos copiados (`:445-491` y `:854-899`). Se homologa la CONDUCTA, no la
   duplicación; el test que acredita que la parcial no se quedó sin reintento es lo que paga
   la diferencia.
3. **`/compact` corre con `ctx=None`**: sin restauración de ficheros post-compactación en la
   ruta manual. El depósito de A (`context.readFileState`) vive toda la sesión; el de B vive
   en el `ToolUseContext` de la tarea (`D-45`), y `/compact` no abre tarea. No se finge: se
   declara.
4. **`CompactionEvent` gana `direction`, `messages_kept` y `messages_summarized`** (`D-22`).
   En A la parcial viaja por `logEvent('tengu_partial_compact', …)` (`:990-1005`) —telemetría
   propia, no costura—. Sin esos campos una parcial es indistinguible de una completa desde
   fuera.
5. **De `commands/compact/compact.ts` entra el mecanismo, no el catálogo.**
   `getMessagesAfterCompactBoundary` como conjunto, el rechazo con historia vacía
   (`No messages to compact`), `args.trim()` como instrucciones y la traducción de errores a
   las tres cadenas canónicas, sí. La memoria de sesión, el `reactiveCompact`, el
   `microcompact` y el `runPostCompactCleanup` no tienen homólogo y no se inventan.

### El enunciado del tramo venía rancio

Decía que `POST_COMPACT` **no existe** en `hooks/protocol.py` y había que construirlo
(`D-22`). Es falso: lo construyó el tramo 4 y está en `hooks/protocol.py:30`, con
`_run_post_compact_hook` usándolo. Se verifica, se anota, y no se reconstruye nada.

### El integrador: quién es dueño de qué

`agentic_code` ya era dueño del transcript (`ConversationState`) y del presupuesto
(`cli.py`); le faltaba el puente. `build_model_caller` se **extrae** de `build_runtime` para
que `/compact` use el MISMO caller que el turno y no estrene una construcción paralela; el
bloque se asienta con `ConversationState.append`, sobre el fichero, porque `dispatch_prompt`
recarga desde ahí al terminar cada turno y guardarlo sólo en memoria lo perdería al salir.

### La prueba, y su acreditación (`D-12 · b`)

`test_compact_engine.py` gana una sección E (12 casos) y queda en **49 verdes**; con
`test_compact_restore`, `test_context_window` y `test_events`, **96 verdes**. Verdes a la
primera, así que se acreditan por **inyección revertida desde copia verificada por `sha256`**
(`mktemp -d`, nunca `git checkout`). Nueve mutaciones, todas muertas:

| mutación | qué cae |
|---|---|
| orden siempre resumen-primero | el bloque cronológico de `from` |
| `up_to` no filtra fronteras rancias | el resumen nuevo se pierde en el rastreo |
| `apiMessages` siempre la conversación entera | el prefijo cacheado de `up_to` |
| ancla del segmento invertida | `preservedSegment` |
| el resumen huérfano no se marca transcript-only | la distinción con `summarizeMetadata` |
| mitades del pivote intercambiadas | qué se resume y qué sobrevive |
| mensajes de mitad vacía intercambiados | los dos textos canónicos |
| la parcial sin reintento por PTL | el cuerpo compartido |
| el evento no declara la dirección | la parcial indistinguible de la completa |

**Pendiente declarado**: los casos de consumidor de `/compact` en
`agentic_code/tests/test_compaction_wire.py` (`D-15`) y la pasada de la suite de
`agentic_code`. Hoy el comando sólo está probado por humo en scratch: la ruta manual completa
—instrucciones al prompt, asiento en el transcript, historia no reemplazada, vista posterior
a la frontera, y las tres traducciones de error— corrió y salió correcta, pero eso no es
prueba asentada y no se declara como tal.

### Lo que NO deroga

`D-42` intacto y **cerrado como arco**: la historia no se reemplaza tampoco en la parcial.
`D-44` intacto: la compactación sigue sin consumir vuelta. `D-45` y `D-46` intactos.
`D-40` intacto: esto es algoritmo y cableado, no conducta de modelo.

---

## `D-48` · La compactación parcial se EXPONE en el integrador, y el pivote se direcciona por ORDINAL (2026-08-26)

- **Fecha:** 2026-08-26, cierre del tramo 6 del arco K6.
- **Encargo del usuario, verbatim:** *«esta fase no estuvo planeada y surgio de la necesida de compactar
  por el modelo local que la extendimos porque ya que estabamos viendo el tema, lo cerramos a homologar
  canonico e incorporar el mecanismo para el local tambien, por tanto no puedes escaparte con decir para
  otra fase, simplemente necesitamos ya que estamos terminar la implementacion»*, y acto seguido *«si
  consideras que puedes ser capaz de exponerla haciendo ajustes donde se requiera adelante»*.
- **Qué la originó.** `partial_compact_conversation` entró en el motor durante el tramo 6 y quedó **sin
  consumidor de producción**: el `/compact` de A no la llama nunca (`commands/compact/compact.ts`, 288 L
  leídas 1→EOF), quien la llama es el selector interactivo (`MessageSelector.tsx`, `onSummarize`). Yo
  propuse diferir el cableado a otra fase; el usuario lo rechazó. Sin exponerla, media rama del motor
  —filtro de marcadores rancios, `PRESERVED_ANCHOR_SUMMARY`, orden resumen-primero,
  `ERROR_MESSAGE_NOTHING_BEFORE`— era `L09` puro: cableado que no existe.

### El hueco real no era el motor: era cómo se NOMBRA el pivote

A señala el pivote por `UserMessage.uuid` elegido en una lista visual. Los mensajes de B son `dict`
planos sin identidad, y `/history` sólo emitía un recuento de turnos. **DECISIÓN:** el pivote se
direcciona por **ordinal** sobre los mensajes de usuario señalables de
`messages_after_compact_boundary(...)`; `/history` publica la lista numerada y `/compact from:N` /
`/compact upto:N` la consumen. El filtro de señalables se homologa de `selectableUserMessagesFilter`
(`MessageSelector.tsx:767-791`): fuera el caveat (`isMeta`), el resumen (`isCompactSummary`), lo
visible sólo en transcript y las etiquetas de salida de comando local; **dentro** el `<command-name>`,
que en A también es señalable.

### Divergencias declaradas (`D-21`, `D-22`)

1. **`upto:` se expone pese al portón de A.** «Summarize up to here» vive tras
   `if ("external" === 'ant')` (`MessageSelector.tsx:121`). Ese portón es **catálogo de producto**, que
   `D-22` deja fuera en las dos direcciones; el mecanismo entra. Y es la dirección barata: sólo el
   prefijo viaja al resumidor (`engine.py:762-764`), que es justo lo que el modelo local necesita.
2. **`ERROR_MESSAGE_NOTHING_AFTER` es inalcanzable por esta superficie.** Con `from` el pivote entra
   siempre en `to_summarize`, luego la mitad nunca queda vacía. Se declara en vez de fabricar un
   `pivot_index` que el mando no puede emitir.
3. **`NotEnoughMessagesError` se traduce por su MENSAJE, no por su clase.** Traducirla por clase
   sustituía las dos cadenas propias de la parcial por la genérica; era defecto propio y se paga aquí.
4. **El rastro de `/compact` se añade al final del bloque ya ordenado**, no dentro de `messages_to_keep`
   como hace A. Con dirección `from` el orden es `[…conservado, resumen]`, y meterlo en `kept` lo dejaría
   delante del resumen y en mitad de la línea temporal. Los conteos no cambian —se calculan antes— y
   `attachments`/`hook_results` son vacíos en esta ruta, así que para la compactación completa el bloque
   persistido es idéntico al de A.
5. **`is_local_command_message` se retira.** No tenía consumidor (`L09`, precedente
   `owns_search_dispatch`); la sustituye `is_local_command_output_message`, más estrecha y homologada del
   filtro de A, que sí lo tiene.

### Acreditación

7 pruebas nuevas en `agentic_code/tests/test_compaction_wire.py` (`D-15`, consumidor real): las dos
direcciones sobre transcript real, el orden del bloque en cada una, `preserved_segment` con su ancla, el
texto libre llegando como `user_context`, la cadena de mitad vacía, el ordinal fuera de rango, el rastro
excluido de los pivotes y `/history` publicándolos. Verdes a la primera ⇒ acreditadas por **mutación
revertida** (`D-12·b`) desde copia `sha256` en `mktemp -d`: **9 inyecciones → 9 rojas, 0 falsos
positivos**; restauración verificada byte a byte por `sha256`. Suite de `agentic_code`: **247 passed**.

### Lo que NO deroga

`D-47` intacto y ampliado, no corregido. `D-42` intacto: la historia se AÑADE también en la parcial.
`D-08` intacto: el orden, el ancla y el filtro salen del fuente de A, no de lo que pareciera lógico.

---

## `D-49` — La compactación homologada se ACREDITA contra el modelo frontera el 2026-09-01; hasta entonces, variante manual para el local (2026-08-27)

**Origen, verbatim del usuario.** *«lo que habiamos acordado, la compactacion homologada de A se
probaria contra el modelo frontera el 1ro de setiembre cuando exista el credito repuesto, mientras
tanto trabajabamos en una variante manual para el modelo local.»*

**Por qué se escribe aquí, y qué faltaba.** Verificado el fichero entero, `D-01`…`D-48`: el acuerdo
**no estaba escrito como tal**. Lo que sí está, y es su raíz, es `D-40` —el local es un stopgap con
fecha, la ventana se cierra el 2026-09-01, y lo medido en él vale como código y aritmética pero
**nunca como conducta**— junto con `D-41` (dos mecanismos de umbral, uno por config) y `D-42 · 4`
(los dos guardas empíricos del local son constante por política). Lo que ninguna de las tres dice
es la consecuencia que el usuario acaba de enunciar: **que la acreditación de la compactación
homologada es ella misma un evento con fecha**, y que el trabajo del ínterin es la variante manual.
Por la propia regla de este fichero —*«si una decisión no está aquí, el siguiente ciclo la volverá a
preguntar»*— se registra ahora, y el ciclo que la volvió a preguntar fue éste.

### La regla

1. **La acreditación de la compactación homologada de A tiene fecha: 2026-09-01**, con el crédito de
   Azure repuesto, y **sujeto gpt-5.4** (`azure-openai-responses`). Es lo que cierra fila.
2. **Hasta esa fecha, la vía viva del local es la VARIANTE MANUAL**: `/compact`, `/compact from:N`,
   `/compact upto:N` con sus pivotes de `/history`, más los guardas de la política `local`
   (`min_summary_chars`, `recompaction_growth_ratio`, escalado de `D-41`). Es la vía que el usuario
   nombró, y es además la barata: en `upto:` sólo viaja el prefijo (`engine.py:762-764`).
3. **La autocompactación por umbral no se acredita en el local.** Sigue construida, cableada y
   probada por consumidor real (`D-44`, `D-15`), que es cableado; lo que no se emite contra ella es
   un veredicto de conducta.

### Encuadre de la sonda del 2026-08-27, corregido en sitio

La sonda estaba en el enunciado de retoma del propio usuario y su mandato era *«SOLO SE MIDE»*. Lo
que mide es **mecanismo**: que la caché del hilo sobrevive a la compactación (16.701 de 19.209
reutilizados), dónde está el coste (95 % en la generación del resumen), y dos defectos de nuestro
port que el cable destapó (`FIND-EMPTY-TOOL-OUT`, `FIND-PARALLEL-SLOT`). Eso vale y se conserva:
es la clase «código y aritmética» de `D-40`.

Lo que **no** es, y no debe leerse así en el § 5 del censo: acreditación de la compactación de A.
Los ~1.600 tokens de razonamiento vertidos al texto, el resumen útil de ~2.300 sobre un techo de
4.096 y las dos declaraciones de crecimiento de tokens son **observaciones del modelo local**, con
su modelo dicho, destinadas al catálogo P1–P9 — no filas del marcador. El encuadre se corrige en el
§ 5 con esta decisión por delante.

### Consecuencia operativa sobre los cuatro abiertos de la sonda

El orden de pago no lo fija la gravedad narrativa sino esta decisión:

- **`FIND-PARALLEL-SLOT`** y **`FIND-EMPTY-TOOL-OUT`** son defectos del adaptador
  `openai-responses` con línea canónica en pi/ai. **No dependen de la fecha**: se pagan cuando toque
  su paso, y su acreditación es de código.
- **`FIND-COMPACT-MANUAL-EVENT`** es exactamente de la variante manual, luego **es del ínterin** y
  cae dentro del punto 2.
- El **techo del resumen** quedó retirado el mismo día por falso; lo que sobrevive de él —cuánto
  admite de verdad `llama-server` frente al `max_tokens` de `local_catalog.py:21`— es política del
  perfil local y **decae con el stopgap** si el 1 de septiembre llega antes que la necesidad, igual
  que la propuesta de diferir las cinco tools de mayor esquema (`D-40`).

### Lo que NO deroga

`D-40` intacto y **precisado**: esta entrada es su consecuencia escrita, no su enmienda. `D-41` a
`D-48` intactos: el arco K6 está cerrado como construcción y como cableado; lo que esta decisión
fecha es el **veredicto**, que nunca fue de esta fase. `D-08` intacto: cuando el 1 de septiembre
llegue, lo que se contraste sigue siendo el fuente de A.

---

## `D-50` — `FIND-COMPACT-MANUAL-EVENT` pagado: la frontera la crea la FUNCIÓN de compactación, y el `/compact` monta su propio sumidero (2026-08-27)

- **Fecha:** 2026-08-27. Cae dentro del punto 2 de `D-49` —es de la variante manual, o sea del
  ínterin— y no reabre nada del arco `D-41`…`D-48`.
- **Encargo del usuario, verbatim:** *«primero, si has detectado que lo que implemento Codex, no se
  alinea al canonico, alinearlo, en el resto estoy de acuerdo.»*

### El defecto

`ManualCompaction._compact` (`agentic_code/src/agentic_code/compaction.py`) llamaba al motor **sin
`emit=`**. Consecuencia: `/compact` compactaba de verdad —bloque asentado, historia añadida, vista
posterior a la frontera correcta— y **no emitía `CompactionEvent`**: ni línea en la captura `.jsonl`,
ni fila rendida. En el canónico la frontera se crea **dentro de la función de compactación**, en las
dos rutas (`services/compact/compact.ts:598-602` completa, `:1014-1020` parcial), no en la superficie
que la invoca. La ruta automática de `D-44` sí pasaba `AgentLoop._emit`, así que el hueco era
exclusivo de la manual: la misma compactación era observable o invisible según por dónde entrase —el
modo de fallo que `D-46 · 2` ya había cerrado para el PTL.

### La decisión, en cinco piezas

1. **`emit` es campo de `ManualCompaction`** —quinto, con default `None`— y se pasa a **las dos**
   llamadas del motor. El tipo de la costura es `EventHandler`
   (`agentic_runtime/contracts/events.py:77`), el alias **público** equivalente al `EmitFn` privado
   del motor: el integrador no importa símbolos privados del núcleo para cablear una costura que el
   contrato ya publica.
2. **El `/compact` monta su propia `StreamCapture`, por sesión y perezosa** (`repl.py`), con
   `prompt="/compact"`. Es `D-22`: el comando local **no es un turno** —no hay `begin_turn`,
   `finish_turn` ni `dispatch_prompt`—, luego no hay captura ni presentación montadas para él, y sin
   sumidero el evento se emitiría al vacío. `StreamCapture._append` abre y cierra el descriptor por
   línea, así que una captura sin `finish()` no deja asa colgando ni registro `result` fabricado.
3. **`last_capture_path` NO se desplaza.** La captura del `/compact` se publica por
   `compaction_capture_path`, aparte. El comando no es el último turno y hacerle sombra a
   `last_capture_path` mentiría a todo lector que use ese puntero para leer el turno del usuario.
4. **La frontera es fila del transcript y NO abre turno.** `TranscriptStore.apply` encamina
   `CompactionEvent` a `_apply_compaction`, que cuelga el bloque de `self._current or el último
   turno`, y sólo fabrica uno si no hay ninguno. Un comando local que abriese turno rompería el
   recuento de `ConversationState` y el reparto del `PayloadRecorder`.
5. **Se caen los contadores inventados de la era Codex.** `_display_text` decía
   `Compacted · N mensajes resumidos · pre → post tokens` y el render añadía `pre → post tokens` y
   `resumen de N caracteres`; el glifo era `⧉`. **A no lleva cifras de tokens en la frontera**:
   `CompactBoundaryMessage.tsx:5-17` pinta `✻ Conversation compacted (ctrl+o for history)`, atenuado
   y sin números, y `CompactSummary.tsx:31-73` sólo declara `Summarized {N} messages`. Queda por
   tanto lo que A dicta —resumidos, conservados, sentido de la parcial, razón— con el glifo `✻`, en
   las cuatro superficies: `_display_text`, `rendering.py`, la fila de la TUI y el navegador de
   transcript. La nota al pie de `reasoning_fallback` se conserva: es `D-21`, no adorno.

### Acreditación (`D-15`: el consumidor detecta)

`agentic_code/tests/test_compaction_wire.py` pasa de 20 a **26** casos: las dos rutas emiten, la
parcial declara su dirección, la frontera aterriza en un `.jsonl` real con
`subtype="compact_boundary"`, el sumidero del REPL usa `prompt == "/compact"` y deja
`last_capture_path is None`, el store no fabrica turno, y el round-trip de la captura reconstruye el
evento. `agentic_code/tests/test_tui.py` gana el caso que monta la fila en un `TranscriptViewport`
real (`App.run_test`): un widget por frontera, el texto canónico, la pista de `Ctrl+O`, **ausencia de
la cadena `tokens`**, repintado en sitio en vez de remontaje, y el bloque colgando del turno
existente. `ruff` limpio; suite de `agentic_code` **254 passed**; sin procesos supervivientes. Las
sintéticas de `agentic_runtime` no se corrieron ni se tocaron (acuerdo de fase).

### Declarado y NO pagado (`declarar-no-es-pagar`)

1. **El barrido de comentarios de los ficheros tocados es paso propio.** Por `D-23` el barrido cubre
   lo que el paso escribe —y así queda—, pero estos seis ficheros del integrador arrastran
   documentación previa cuya purga inflaría el diff hasta hacerlo irrevisable.
2. **`CompactionEvent` no lleva `user_context`.** La línea `Context: "…"` de `CompactSummary.tsx`
   no se puede rendir desde el evento sin tocar el contrato del núcleo, y el texto libre del
   `/compact` ya viaja al resumidor (`D-48`). Se declara en vez de fingirla.
3. **`PayloadRecorder` es de ámbito de turno**, luego la petición de resumen del `/compact` y su
   coste no se graban. Es preexistente y no lo abre esta entrada.

### Lo que NO deroga

`D-49` intacto: esto es cableado y presentación, no veredicto de conducta — el 1 de septiembre sigue
siendo la fecha. `D-47 · 3` intacto: `/compact` sigue corriendo con `ctx=None`, sin restauración de
ficheros. `D-42` intacto: la historia se añade. `D-08` intacto: el glifo, la frase y la ausencia de
cifras salen del fuente de A, no de lo que pareciera informativo.

## `D-51` — La observabilidad del `/compact`: el texto libre SALE por el evento y el gasto del sumarizador SE REGISTRA (2026-08-27)

`D-50` cerró el cable y declaró dos carencias sin pagar (piezas 2 y 3 de su «Declarado y NO pagado»).
Esta entrada las paga juntas porque son la misma costura: `/compact` es **comando local, no turno**
—sin `begin_turn`, sin `finish_turn`, sin `dispatch_prompt`—, luego nada de lo que un turno monta
por sí solo existe para él, y hay que dárselo desde el integrador (`D-22`).

### Pieza A — `user_context` en el contrato del evento

El dato ya viajaba al prompt del resumidor (`User context: …`, `engine.py:752-755`), al marcador de
frontera (`:779-788`) y a `summarize_metadata` (`:800-805`), y se caía justo en los dos `emit`
(`:667-682`, `:846-861`) — es decir, en la **única costura pública por la que un consumidor puede
pintarlo**. `A` sí lo pinta: `CompactSummary.tsx:48`, `Context: “{metadata.userContext}”`, en línea
aparte del titular porque no es un hecho de la compactación sino lo que se pidió de ella.

Se amplía `CompactionEvent` con `user_context: str = ""` (`contracts/events.py`) y se rellena en las
dos rutas. Sólo la **parcial** lo trae: la completa manda ese texto como `custom_instructions`,
igual que `A` (`commands/compact/compact.ts`). El campo existe siempre y va vacío ahí, que es lo que
`D-21` exige de una opción que esta ruta no expresa.

Aguas abajo llega a las cuatro superficies del integrador y a la proyección de captura:
`capture.py` lo mete en `compact_metadata` (junto a `trigger` y `pre_tokens`, que es donde `A` los
tiene), `transcript.py` lo expone como `context_line` —**fuera del titular**—, y `rendering.py`,
`tui.py` y `transcript_browser.py` lo pintan como `└ contexto: “…”`.

### Pieza B — el grabador de payloads, prestado al comando

`PayloadRecorder` es el **único instrumento que acredita lo que se PIDIÓ al modelo**: la captura
ordinaria registra eventos, o sea lo que el motor devuelve. Se cosía sólo en `dispatch_prompt`, así
que el request del sumarizador —el único gasto de modelo que no pertenece a ningún turno— era
también el único que no quedaba anotado en ninguna parte.

`ManualCompaction` gana una segunda costura, `recording: Callable[[], AbstractContextManager[None]]`,
que envuelve la llamada al motor; sin ella el default es `nullcontext()`. El REPL la sirve con
`_record_compaction`, y ahí está el detalle que obliga a esta forma: **`on_payload` ocurre ANTES del
primer `CompactionEvent`**, luego el sumidero perezoso de `D-50` llegaba tarde por construcción. De
ahí `_ensure_compaction_capture()`, extraído de `_emit_compaction`: la captura se crea antes de
llamar al motor y la comparten evento y payload.

**`borrow`, no `attach`/`detach`.** Guardar y restaurar el capture previo en vez de anularlo: la
compactación **automática** ocurre DENTRO de un turno, y un `detach` dejaría al turno en vuelo sin
grabador. `/compact` además no es `immediate` (sólo `/status` lo es), comparte el hueco de
`turn_runner` y no puede solaparse con un turno; la restauración es la garantía de que anidar nunca
resta.

### Acreditación (`D-15`: el consumidor detecta)

`test_compaction_wire.py` pasa de 26 a **30** casos: el texto libre llega al evento, a
`compact_metadata` y a las tres superficies pintables como línea aparte —y **no** al titular—; una
compactación sin texto libre no pinta línea alguna; el request del sumarizador aterriza en el
`.jsonl` real del `/compact` como `model_request` **por delante** de la frontera (si fuese posterior
no sería el del sumarizador); y el préstamo devuelve el grabador a la captura del turno, que no se
queda con el gasto del comando. El caso de la automática exige además `user_context == ""`.

`ruff` limpio; suite de `agentic_code` **258 passed**; sin procesos supervivientes. Las sintéticas de
`agentic_runtime` no se corrieron ni se tocaron (acuerdo de fase).

### Deuda arrastrada, presentada (`declarar-no-es-pagar`)

No es cola neutra: es deuda mía, y se nombra como tal en el §5 del censo —`FIND-PARALLEL-SLOT`,
`FIND-EMPTY-TOOL-OUT` y el techo de salida del perfil local—, cada una pagada o declarada **medida y
vigilada**. El barrido de comentarios de los ficheros tocados sigue siendo paso propio (pieza 1 de
`D-50`), sin cambio.

### Lo que NO deroga

`D-49` intacto: esto es contrato y cableado, no veredicto de conducta — el 1 de septiembre sigue
siendo la fecha. `D-50` intacto en sus cinco piezas; esta entrada paga dos de sus declarados, no
reabre ninguna. `D-47 · 3` intacto: `/compact` sigue corriendo con `ctx=None`. `D-08` intacto: la
línea `Context:` y su sitio salen de `CompactSummary.tsx`, no de lo que pareciera informativo.

## `D-52` — `FIND-PARALLEL-SLOT` pagado: una casilla POR ITEM, con la clave replegada a `item.id` (2026-08-27)

Primera de las tres deudas nombradas en `D-51`, y la más cara: no rotula mal, **ejecuta dos veces**.

### El defecto, reproducido en vivo antes de tocar nada

`process_responses_stream` (`agentic_models/.../openai_responses_shared.py`) llevaba **una sola
casilla** de turno (`current_item` / `current_block`) donde el canónico tiene un mapa
(`pi/packages/ai/src/api/openai-responses-shared.ts:288-354`, `outputSlots`, con `contentIndex`
congelado al crear la casilla y `outputSlots.delete` en cada `done`). Además, `block_index()`
calculaba el índice en el momento del delta (`len(output.content) - 1`) en vez de al crear.

Captura cruda contra `llama-server` (`curl` a `/v1/responses`, una tool, prompt de dos llamadas):
`added rs_…` → 31 × `reasoning_text.delta` → `added fc_A` → deltas de `a.txt` → `added fc_B` (con
`fc_A` aún abierto) → deltas de `b.txt` → `done rs_…` → `done fc_A` → `done fc_B`. Daño exacto sobre
el código de entonces: el `added` de `fc_B` pisa la casilla, luego (a) la rama `done` del
razonamiento no encuentra su bloque ⇒ **`thinking_signature` nunca se fija** y el item de
razonamiento no se reenvía en el request siguiente; (b) el `done` de `fc_A` escribe `{"path":"a.txt"}`
**en el bloque de `fc_B`**; (c) el `done` de `fc_B` no encuentra bloque y **fabrica** un `ToolCall`
que no está en `output.content`. Neto: `b.txt` descartado y `a.txt` ejecutado dos veces.

### La segunda capa: llama.cpp no manda `output_index` — acreditado en su fuente

Antes de inyectar se leyó el emisor Responses de `llama.cpp` (`/home/noheroes/ai/llama.cpp`, HEAD
`c060ca974`, tag `b10603`): `tools/server/server-task.cpp:1166-1314` (los deltas) y `:599-714` (el
cierre). Hechos:

- **`output_index` no se escribe en ningún evento.** Tampoco `content_index`, `summary_index`,
  `sequence_number`. El estado del turno (`server-task.h`) sólo guarda `oai_resp_reasoning_id`,
  `oai_resp_message_id` y un `oai_resp_fc_id` («*function call ID for current args delta*»): **no
  existe el concepto de índice de salida**. Los tests de conformidad del propio `llama.cpp`
  (`tests/unit/test_compat_oai_responses.py`) anclan la identidad en `item.id`/`item_id`.
- **Todos los `output_item.done` salen al FINAL**, desde el resultado final: razonamiento, mensaje y
  luego todas las tools. El solapamiento no es contingente, es la arquitectura.
- Todo evento del stream lleva **o `item_id` o `item.id`**, sin excepción, y los tres ids son
  estables durante el turno. La clave replegada es total, no un apaño.
- No emite `function_call_arguments.done`, ni `reasoning_text.done`, ni los eventos de
  `reasoning_summary_*`, ni `refusal.delta`, ni `response.incomplete` / `response.failed`.
- **Divergencia que queda ABIERTA, no de este paso:** `to_json_oaicompat_resp_stream()` emite
  `"status": "completed"` **incondicionalmente** (`:696`), también con `stop == STOP_TYPE_LIMIT`. Un
  turno truncado por techo de salida se anuncia como completado, y `_map_stop_reason` no puede
  distinguirlo. Va al catálogo P1–P9, no a homologación.

### Lo inyectado

Mapa `output_slots` con casillas `{type, block, content_index, keys}`. `content_index` se congela al
crear, como el canónico. La casilla se **registra bajo todas las claves disponibles** —`("index", output_index)`
cuando no es `None`, y `("item", item_id)`— y se busca por cualquiera de las dos; `drop_slot` retira
todas. Un mapa indexado sólo por `output_index` colapsaría los tres items en uno bajo `llama-server`,
porque el SDK `openai` no valida el campo ausente y lo entrega como `None`.

Cada handler pasa a la forma canónica `slot = get_slot(...); if slot is None: continue`, y
`output_item.done` usa `get_or_create_slot`, con lo que **desaparece la fabricación** del `ToolCall`
suelto: si la casilla no existe, se crea y el bloque entra en `output.content`. Dentro del mismo
bloque reescrito se homologa también el orden de resolución de argumentos del `done`, que era del
revés: el canónico (`:500`) prefiere `item.arguments` y cae al `partialJson`.

El nombre del buffer de trabajo sigue siendo `_partial_json`: el camino de error de
`openai_responses.py:246-252` lo despoja **por nombre**.

### Acreditación (`D-12·b` y `D-15`)

Dos casos nuevos en `test_provider_roundtrip_openai_responses.py`, mismo criterio y dos formas de
cable: con `output_index` (forma OpenAI) y sin él (forma `llama-server`, con el orden capturado).
Ambos exigen dos tool calls con argumentos distintos, ids distintos, tres `contentIndex` distintos,
el objeto del `toolcall_end` **presente en `output.content`**, y firma de razonamiento fijada.

Mutación inyectada y revertida desde copia propia verificada por `sha256`
(`7c4f32ffa99deb930a79fe7c1abdd3bd8e1ca10cf75768c720d4bbc567315683`, el estado final; la primera
tanda se corrió sobre `2e2dcc…`, antes de subsanar dos avisos de `ruff` propios), dos pasadas:
- clave constante (casilla única): **los dos casos nuevos caen**, con el diff exacto del defecto
  descrito —`a.txt` dos veces, `b.txt` perdido—; los cuatro previos siguen verdes.
- clave sólo por `output_index`: **cae únicamente** el caso sin índice. Aísla la segunda capa.

Consumidor real: el mismo turno contra el `llama-server` vivo devuelve `stop_reason == toolUse`,
`contentIndex` 0/1/2, `{"path":"a.txt"}` y `{"path":"b.txt"}` en tool calls distintas, un bloque de
razonamiento con firma de tipo `reasoning`.

`agentic_models` **54 passed**, `agentic_code` **258 passed**, sin procesos supervivientes. Las
sintéticas de `agentic_runtime` no se corrieron ni se tocaron. `ruff` sobre los dos ficheros: **8
avisos antes, 6 después** — los dos que la inyección introdujo (`B023` por un cierre sobre variables
de bucle, `SIM114`) se pagaron; los 6 restantes son preexistentes y no se tocan en este paso.

### Barrido de comentarios

`D-23`: los dos ficheros tocados quedan sin comentarios ni docstrings de módulo/función; el criterio
y las citas del bloque de prosa que había en el fichero de tests se pliegan al docstring de su test,
que es la única excepción de la regla. Esto **no** paga la pieza 1 de `D-50`, que es el barrido de
los nueve ficheros de `D-50`/`D-51` y sigue siendo paso propio.

### Lo que NO deroga

`D-49` intacto: esto es adaptador de proveedor, no compactación, y no depende de la fecha del 1 de
septiembre. Queda pendiente y nombrado `FIND-EMPTY-TOOL-OUT` (una línea, `:201` del fichero
original), el techo de salida del perfil local, y la pieza 1 de `D-50`.

---

## `D-53` (2026-08-27) — `FIND-EMPTY-TOOL-OUT`: el resultado vacío se declara vacío

Palabra del usuario: `procede`, sobre el anuncio de la inyección. Paga la deuda 2 de las tres
nombradas en `D-51`; la 1 se pagó en `D-52`.

### El defecto

`openai-responses-shared.ts:254` resuelve la salida de tool con un ternario de **tres** ramas:

```ts
output = sanitizeSurrogates(hasText ? textResult : hasImages ? "(see attached image)" : "(no tool output)");
```

Nuestro port lo tenía colapsado a dos (`openai_responses_shared.py:194`; era `:201` antes del
desplazamiento de `D-52`): sin texto, la salida caía **siempre** en la de imagen. Un `glob` sin
coincidencias le llegaba al modelo anunciando una imagen que no existe. Visto en el cable de la
sonda: el modelo lo registró como anomalía y lo rodeó con `ls -la`. Degrada la conducta sin fallar.

### Lo que el contraste hasta EOF añadió al enunciado

`transformMessages` corre **antes** de la conversión (`:123`) y `downgradeUnsupportedImages`
(`transform-messages.ts:34-56`) sustituye la imagen por `"(tool image omitted: model does not
support images)"` cuando el modelo no admite imágenes — nuestro port hace lo mismo
(`transform_messages.py:15-16`, `:33-57`). Luego `hasImages` sólo puede ser cierto junto a
`model.input` con imagen, que es la rama de partes: **la rama `"(see attached image)"` es defensiva
y no se alcanza por este camino ni en A**. La consecuencia agrava el defecto en vez de suavizarlo:
sin la tercera rama, todo resultado vacío heredaba una cadena muerta.

### Lo inyectado

Una línea, `openai_responses_shared.py:194`, literal del canónico:

```python
output_val = sanitize_surrogates(
    text_result if has_text else "(see attached image)" if has_images else "(no tool output)"
)
```

### Acreditación (`D-12·b` y `D-15`)

Dos casos nuevos en `test_provider_roundtrip_openai_responses.py`: el resultado vacío —lista vacía
y `TextContent` vacío— exige `"(no tool output)"`; el segundo fija las otras dos ramas tal como el
cable las alcanza de verdad, con la razón de por qué la de imagen no se alcanza.

Mutación inyectada y revertida desde copia propia verificada por `sha256`
(`c78c448cfee9d510fe45e383aad35981045180dc900d7fb35edbcf22bef0c5af`, el estado inyectado; el previo
era `7c4f32ff…`), dos pasadas, **dos rojas**: retirada de la tercera rama (estado previo) y literal
cambiado a `"(empty)"`. En las dos cae sólo el caso del vacío; los demás siguen verdes.

Consumidor real (`D-15`): turno contra el `llama-server` vivo en workspace de scratch, `glob` con
patrón `*.zzz` sin coincidencias, captura con `AGENTIC_CODE_CAPTURE_PAYLOADS_FULL`. El segundo
`model_request` del `.jsonl` lleva
`{"type": "function_call_output", "call_id": "call_3ibb…", "output": "(no tool output)"}`,
y el razonamiento del modelo dice *«The glob tool didn't find any files»* — sin la anomalía de la
imagen inexistente.

`agentic_models` **56 passed**, `agentic_code` **258 passed**, sin procesos supervivientes. Las
sintéticas de `agentic_runtime` no se corrieron ni se tocaron. `ruff` sobre los dos ficheros: los
**6** preexistentes de `D-52` y ninguno nuevo — el `I001` que la primera forma del bloque de imports
introdujo se pagó antes de cerrar.

### Divergencias del mismo fichero halladas al leerlo 1→EOF — ABIERTAS, no de este paso

1. **`FIND-RESP-INCOMPLETE`.** El canónico llama `finalizeResponse` para `response.completed` **y**
   `response.incomplete` (`:512`). Nuestro `:461` sólo atiende `completed`: un turno truncado por
   techo no fija `usage`, ni coste, ni `stop_reason`, y la rama `"incomplete" → "length"` de
   `_map_stop_reason` (`:242`) es inalcanzable por ese camino. Enlaza con la divergencia abierta de
   `llama.cpp` (`server-task.cpp:696`, `"status": "completed"` incondicional): allí el servidor
   miente; aquí no escucharíamos la verdad ni aunque la dijera.
2. **`FIND-RESP-TERMINAL`.** Falta el centinela `sawTerminalResponseEvent` (`:302`, `:528-530`): el
   canónico lanza `"OpenAI Responses stream ended before a terminal response event"` si el stream
   muere sin evento terminal; nuestro port cierra en silencio como turno bueno.
3. Menor: el canónico **no incrementa `msgIndex`** al descartar un mensaje vacío (`continue` en
   `:157` y `:220`, antes del `:263`); nuestro port lo incrementa siempre (`:168-170`, `:202`). Sólo
   afecta a los ids de repliegue `msg_pi_{n}`.

### Lo que NO deroga

`D-49` intacto. Queda pendiente la pieza 1 de `D-50` —el barrido de comentarios de sus nueve
ficheros— y el techo de salida del perfil local, que no es divergencia de motor.

---

## `D-54` (2026-08-27) — `FIND-RESP-INCOMPLETE` + `FIND-RESP-TERMINAL`: el cierre del stream de Responses es UNA costura, y se homologa entera

Palabra del usuario: `procede`, sobre el anuncio de la inyección. Paga las dos divergencias que
`D-53` dejó ABIERTAS en su § final, que son la misma costura —el cierre del stream de Responses— y
viven en el fichero ya leído 1→EOF.

### Lo que el contraste contra el canónico convirtió en cinco

Se anunciaron dos; leído `pi/packages/ai/src/api/openai-responses-shared.ts` 1→EOF antes de tocar
nada, son **cinco**, y las tres nuevas se anunciaron antes de inyectar:

1. **`response.incomplete` no se atendía.** El canónico llama `finalizeResponse` en la rama
   `response.completed || response.incomplete` (`:512-513`); nuestro port sólo atendía `completed`.
   Un turno truncado por techo no fijaba `usage`, ni coste, ni `stop_reason`, y la rama
   `"incomplete" → "length"` de `_map_stop_reason` era inalcanzable por ese camino.
2. **Faltaba el centinela.** `sawTerminalResponseEvent` (`:302`) y el `throw` posterior al bucle
   (`:528-530`, `"OpenAI Responses stream ended before a terminal response event"`): un stream
   cortado se cerraba en silencio como turno bueno.
3. **El cuerpo entero colgaba de `if response:`.** A guarda con condición sólo el `id` y el `usage`
   (`:356-374`); el coste, el tier y el `stopReason` se calculan **siempre** (`:375-387`). Con la
   forma anterior, un terminal sin objeto `response` dejaba el turno sin coste ni razón de parada.
4. **`response.failed` no lanzaba siempre.** A lanza incondicionalmente (`:516-525`) y el ternario
   cuelga de `details?.reason`: sin error y sin razón, el literal es
   `"Unknown error (no error details in response)"`. B no lanzaba con carga vacía y decía
   `incomplete: unknown` donde A dice el literal.
5. **El tier de servicio recibía el ESTADO.** `st = resp_status` en vez del `service_tier` de la
   respuesta (A: `:376-381`). Como el envoltorio real no pasa `resolve_service_tier`
   (`openai_responses.py:229-236`), los multiplicadores `flex` (0.5) y `priority` **nunca se
   aplicaban**: el precio del turno salía siempre a tarifa plena.

### Lo inyectado

`agentic_models/src/agentic_models/providers/openai_responses_shared.py`: `_resp_field` (lectura
indistinta de `dict` o de objeto del SDK), `saw_terminal_response_event`, `finalize_response` como
función homóloga de `finalizeResponse`, la rama terminal `("response.completed",
"response.incomplete")`, el `response.failed` con sus tres literales, y el `raise` posterior al
bucle. El bloque anterior de `response.completed` (34 líneas) se retira entero. Las otras tres
entradas al mismo motor —`azure_openai_responses.py:211` y `openai_codex_responses.py:570,749`—
heredan la conducta por el mismo punto, igual que en A.

### Fuera de alcance, declarado (`declarar-no-es-pagar`)

- **`FIND-USAGE-REASONING` — ABIERTO.** A pone `reasoning: usage.output_tokens_details
  ?.reasoning_tokens` en el `Usage` (`:370`); nuestro `Usage` (`model_types.py:166-173`) **no tiene
  ese campo**. Es cambio del contrato `Usage`, que tocan todos los providers y el puente del
  runtime: no se paga de tapadillo dentro de este paso. Queda registrado en el § 5 del censo.
- **El `msg_index`** que se incrementa donde el canónico hace `continue` sigue abierto: es de
  `convert_responses_messages`, no de esta costura, y sólo afecta a los ids de repliegue
  `msg_pi_{n}`.

### Acreditación (`D-12·b` y `D-15`)

Cuatro casos nuevos en `test_provider_roundtrip_openai_responses.py`, cada uno con su docstring
declarando el criterio canónico y su cita: `incomplete` como evento terminal con `usage` y
`stop_reason == "length"`; el EOF temprano rindiendo el literal de A por la vía de error del
envoltorio; `failed` en sus tres formas de carga; y el tier recibiendo el tier y no el estado
(precio a mitad con `flex`).

Mutación inyectada y revertida desde copia propia verificada por `sha256` (previo
`c78c448cfee9d510fe45e383aad35981045180dc900d7fb35edbcf22bef0c5af`, inyectado
`aaca33e0fcc90490dc99f18f26176dd396398a8caadb4ecc77c842227aa619ac`), **cuatro pasadas, cuatro
rojas**, cada una tumbando exactamente su caso y sólo ése: retirar el `raise` posterior al bucle ·
volver la rama terminal a `completed` sola · leer `"status"` como tier · devolver el `raise` final
de `failed` a la guarda `if response:`. Hash idéntico tras cada revert.

Consumidor real (`D-15`): turno contra el `llama-server` vivo pasando por el nuevo
`finalize_response`; la línea `result` del `.jsonl` cierra `"stop_reason": "stop"` con
`input_tokens` 14 803 / `output_tokens` 250 / `cache_read` 14 709 y `status: "completed"`.

`agentic_models` **60 passed**, `agentic_code` **258 passed**, sin procesos supervivientes. Las
sintéticas de `agentic_runtime` no se corrieron ni se tocaron (acuerdo de fase). `ruff`: los **6**
avisos preexistentes de `D-52`/`D-53` y ninguno nuevo.

### Barrido de comentarios

`D-23`: los dos ficheros tocados quedan sin comentarios ni docstrings de módulo o función; las citas
del canónico viven en el docstring de cada test, que es la única excepción de la regla. Esto **no**
paga la pieza 1 de `D-50` —el barrido de sus nueve ficheros—, que sigue siendo paso propio.

### Lo que NO deroga

`D-49` intacto: esto es adaptador de proveedor, no compactación, y no depende de la fecha del 1 de
septiembre. `D-52` y `D-53` intactos: esta entrada extiende su costura, no la reabre. `D-08`
intacto: los cinco cortes, sus literales y el orden de guardas salen del fuente de A. La divergencia
de `llama.cpp` (`server-task.cpp:696`, `"status": "completed"` incondicional) sigue ABIERTA y va al
catálogo P1–P9: el servidor miente, pero ya no es cierto que no escucharíamos la verdad si la dijera.

---

## `D-55` (2026-08-28) — `FIND-USAGE-REASONING`: el contrato `Usage` gana `reasoning` y `cache_write_1h`, y se acredita hasta el `.jsonl`

- **Palabra del usuario:** `Se atacan los 3 en el orden que propones` (orden en vigor: 1)
  `FIND-USAGE-REASONING`, 2) `msg_index`, 3) pieza 1 de `D-50`) y `procede` sobre la inyección.
- **Origen:** deuda declarada y NO pagada en `D-54`, § *Fuera de alcance*.

### El defecto

El canónico transporta en `Usage` dos campos que B no tenía (`types.ts`):

1. **`reasoning`** — SUBCONJUNTO de `output`, luego **coste neutro**. Lo pueblan **cinco**
   productores: `openai-responses-shared.ts:370` (`output_tokens_details.reasoning_tokens`),
   `openai-completions.ts:1141` (`completion_tokens_details.reasoning_tokens`),
   `anthropic-messages.ts:708` (`output_tokens_details.thinking_tokens`, **sólo si no es nulo**),
   `google-generative-ai.ts:225` y `google-vertex.ts:242` (`thoughtsTokenCount`).
2. **`cacheWrite1h`** — SUBCONJUNTO de `cacheWrite`, producido en `anthropic-messages.ts:555`
   (`cache_creation.ephemeral_1h_input_tokens`) y **facturado a `2 × input`** (`models.ts:385-395`),
   con `short = cacheWrite - cacheWrite1h`. Sin el campo, la escritura larga se cobraba a tarifa de
   escritura corta: **el precio del turno salía mal**, no sólo incompleto.

Por eso el paso no es «añadir un campo»: es el contrato `Usage`, sus cinco productores, las **dos**
funciones de precio y las **dos** costuras que lo llevan hasta el consumidor.

### Lo inyectado

- `model_types.py` — `Usage.reasoning: int = 0` y `Usage.cache_write_1h: int = 0`, **al final** del
  dataclass para que la construcción posicional existente conserve su significado.
- `models/registry.py` — el tramo de 1 h en **los dos** caminos de precio: el método
  `Registry.calculate_cost` y la función de módulo `calculate_cost_values`. `models.ts:385-395` es
  un solo algoritmo y aquí vive en dos sitios; homologar uno solo deja el otro mintiendo.
- `providers/openai_responses_shared.py` y `providers/openai_completions.py` — `reasoning` desde
  los detalles de salida.
- `providers/anthropic.py` — `cache_write_1h` desde `cache_creation.ephemeral_1h_input_tokens`, y
  `reasoning` desde `output_tokens_details.thinking_tokens` **sólo si no es nulo**, como A.
- `providers/google_shared.py` — `read_usage_metadata` y `read_usage_field`, que leen el nombre en
  `snake_case` **y** en `camelCase`; `providers/google.py` y `providers/google_vertex.py` recablean
  su bloque de usage sobre ellas.

### `FIND-GOOGLE-USAGE` — hallazgo del paso, pagado

El caso de Google salió en rojo con el `Usage` **entero a cero**, no sólo `reasoning`. Causa: el
bloque leía `usageMetadata` / `promptTokenCount` / `candidatesTokenCount`, que son los nombres del
SDK **TypeScript**. El SDK Python (`google.genai`) los expone en `snake_case`
(`GenerateContentResponse.usage_metadata`, `…UsageMetadata.thoughts_token_count`), luego
`usage_meta` era **siempre `None`** y Google no reportaba consumo alguno. Verificado contra el SDK
real instalado. Pagado dentro de esta costura por las dos funciones de lectura dual.

### `FIND-GOOGLE-CASING` — ABIERTO y declarado (`declarar-no-es-pagar`)

El mismo error de grafía vive fuera del bloque de usage y **no** se toca aquí: `finishReason` en
`google.py:258` (el SDK Python da `Candidate.finish_reason`) y `thoughtSignature` en `google.py:216`,
`:222` y `:251` (`Part.thought_signature`). Es paso propio, con su lectura 1→EOF de los dos ficheros
gemelos; rotularlo aquí no lo paga.

### Acreditación (`D-12·b`)

Ocho casos nuevos en `agentic_models/tests/test_usage_reasoning.py`, con el criterio canónico y sus
citas en el docstring: los cuatro productores contra `LocalSSEServer`; el tramo de 1 h a `2 × input`
por **las dos** funciones de precio; el precio sin tramo de 1 h idéntico al de antes; y `reasoning`
sin coste por ser subconjunto de `output`.

**Seis mutaciones inyectadas y revertidas** desde copia propia verificada por `sha256`, **seis
rojas**, cada una tumbando exactamente su caso. Hash idéntico tras cada revert: `registry.py`
`e6ad40e7…`, `anthropic.py` `d315b851…`, `google_shared.py` `c567de8a…`,
`openai_completions.py` `34323232…`, `openai_responses_shared.py`
`bdb4ba237835a32ca174c37a7ebaeee891ee895b49d857fe808fc44074a7e9b7`.

**La mutación M1 fue un falso negativo mío, y se declara.** El patrón que inyecté llevaba la
indentación del método de clase, así que sólo mutó `Registry.calculate_cost` y **no** la función de
módulo que el caso llama: la suite siguió verde. El defecto era de la mutación, no del test. Se
corrigió añadiendo el caso que ejercita el método de clase y repitiendo la pasada por separado
(M1a función de módulo → roja, M1b método de clase → roja).

### Acreditación en el consumidor real (`D-15`)

`agentic_code/tests/test_usage_reasoning_bridge.py`, tres casos, con el puente **real**
(`agentic_runtime/models/caller.py`) y el capturador **real** (`agentic_code/capture.py`);
lo único sustituido es el motor. Cubre las dos costuras que quedaban:

1. el puente proyecta `Usage.reasoning` sobre `DoneEvent.usage.thinking_tokens`;
2. la captura escribe ese `Usage` en la línea `.jsonl` de verdad (`handle` sobre fichero), tanto en
   `runtime_event` como en la proyección `message.event.usage`.

El tercer caso fija que un `Usage` antiguo **sin** el campo rinde 0 y no revienta: el puente lee por
`getattr`, y eso también es contrato.

**Dos mutaciones más, dos rojas**, desde copia verificada por `sha256`: `caller.py`
(`thinking_tokens=0`) tumba los dos casos del puente y deja verde el del `Usage` antiguo —que es lo
correcto, porque afirma 0—; `capture.py` (`"usage": None`) tumba sólo el de la línea de captura.
Hashes tras revert: `caller.py`
`fdc9ee22a9d35c5bfffb5cf7cf50509089124ac1636bae6241999e59783ab26b`, `capture.py`
`92fbdd9324f35f7c4da945d41e065816f7e573b7392e799be2558d595bf6a520`.

**Turno real contra gpt-5.x: APLAZADO al 2026-09-01 por `D-49`, no bloqueado.** La pata de `.jsonl`
real con razonamiento **no está pagada** contra el proveedor que lo emite, pero eso no es una
incidencia abierta: el `401 invalid subscription key` de Azure es el crédito agotado, y `D-49` ya
fija su reposición el **2026-09-01**. La pata viaja a esa ventana, junto a la acreditación de la
compactación contra el modelo frontera; hasta entonces **no se persigue clave alguna**, y rotularla
«bloqueada» sería invitar a la ventana siguiente a gastar en lo ya decidido.

El `llama-server` local sí se ejercitó, y **no puede sustituirla**. Precisión que costó una
corrección del usuario y que hay que dejar bien escrita: **el local SÍ emite razonamiento**. Medido
en vivo el 2026-08-28 en las dos rutas de su `/v1/responses` —item `{"type": "reasoning"}` con su
`reasoning_text` en la no-streaming, y `response.reasoning_text.delta` en la de streaming, que es la
que ve el usuario en pantalla—. Lo que **no** emite es `output_tokens_details`, es decir el
**contador** `reasoning_tokens`; los tokens de razonamiento se cobran dentro de `output_tokens` sin
desglosar.

Luego su `thinking_tokens: 0` es fiel **al wire** y **falso sobre lo ocurrido**: convive con un
turno que razonó a la vista. El turno pasa por `finalize_response`, pero por la rama del `or 0`, y
rinde el mismo `.jsonl` antes y después de la inyección. Es el caso degenerado, y darlo por
acreditación sería exactamente la trampa de `no-debilitar-la-prueba`. Concuerda con `D-40` y con
`D-49`: el local acredita **mecanismo**, nunca conducta — y aquí ni siquiera mecanismo, porque el
motor es mudo sobre el campo. Catalogado como **`P14`** en
`agentic_models/gpt-5.x-conducta-vs-claude.md`, junto a la otra omisión del mismo servidor.

Corolario que sí queda pagado por el local, y conviene no perderlo: el **contenido** del
razonamiento es acreditable contra él de punta a punta (`reasoning_text.delta` → `ThinkingEvent` →
captura). Lo mudo es el contador, no el canal.

**Deuda que la fecha NO cierra — `cache_write_1h`.** Sólo lo emite Anthropic
(`anthropic-messages.ts:555`), luego **gpt-5.x no lo acreditará nunca**. El campo que corrige un
precio mal cobrado seguirá sin consumidor real después del 2026-09-01: su acreditación necesita
proveedor Anthropic, o queda declarada indefinidamente. Se anota aquí para que la ventana del
2026-09-01 no la dé por cerrada de arrastre.

### Suites, `ruff` y procesos

`agentic_models` **68 passed**, `agentic_code` **261 passed**, sin procesos supervivientes (el
`llama-server` vivo es del usuario y precede a la ronda). `ruff`: `agentic_code` **All checks
passed**; en `agentic_models` los avisos son los **preexistentes**, comparados uno a uno contra la
copia previa fichero por fichero. El único aviso nuevo —un `I001` en `model_types.py` por una línea
en blanco que dejó el barrido— se corrigió en el acto. Deuda neta cero por diff.

### Barrido de comentarios

`D-23`: los nueve ficheros tocados quedan sin comentarios ni docstrings salvo directivas `# noqa` /
`# type:`; las citas del canónico viven en el docstring de cada test, única excepción de la regla.
Esto **no** paga la pieza 1 de `D-50` —el barrido de sus nueve ficheros—, que sigue siendo paso
propio y es el tercero del orden acordado.

### Lo que NO deroga

`D-49` intacto: esto es contrato de `Usage`, no compactación. `D-52`, `D-53` y `D-54` intactos: esta
entrada paga la deuda que `D-54` declaró, no reabre su costura. `D-08` intacto: los campos, su
condición de subconjunto y el precio del tramo de 1 h salen del fuente de A. `D-21` intacto:
`FIND-GOOGLE-CASING` y el turno de Azure se **declaran**, no se descartan en silencio.

---

## `D-56` (2026-08-28) — Una funcionalidad homologada se preserva en TODOS los modelos: si el proveedor no la da, se deriva

- **Palabra del usuario**, literal: *«al ser en esencia una solucion multi modelos, debemos
  adaptarnos a situaciones como esta, para preservar una funcionalidad que homologamos del
  canonico, sin excepciones»*.
- **Qué corrige.** Yo había rotulado el contador derivado de razonamiento como *«divergencia
  deliberada por familia de modelo, de la clase de `curl`/`wget` en `P4`»*. **Es el encuadre
  contrario y estaba mal.** El canónico define que `Usage` transporta el razonamiento; eso es la
  funcionalidad homologada. Que un motor no la desglose no nos exime del contrato: nos obliga a
  sostenerlo por otra vía. Adaptarse es **fidelidad**, no desviación — `D-22` aplicado a la capa de
  proveedor.

### La regla, sin casos especiales

1. **El proveedor da el contador** → se usa el suyo, tal cual, sin tocar. No se cuenta nada. Es el
   caso de los cinco productores homologados en `D-55`.
2. **No lo da pero emite el razonamiento** → **se deriva**. En el motor local, contando deltas:
   medido el 2026-08-28, son **por token** (70 de razonamiento + 54 de texto = 124 contra
   `output_tokens` 127; los 3 restantes son tokens de control no emitidos como texto).
   `llama-server` expone además `/tokenize` si se quisiera exactitud al token.
3. **Ni lo da ni emite razonamiento legible** → **no se emite un `0` mudo**. Se marca indisponible.
   Un cero sin explicación es exactamente el defecto catalogado en `P14`: fiel al wire y falso
   sobre lo ocurrido.

### Consecuencia de contrato

La procedencia deja de ser un adorno y pasa a ser lo que hace comprobable el «sin excepciones»:
`thinking_tokens_source: "provider" | "counted" | "unavailable"`. Sin ella, un 0 del proveedor, un
70 calculado y un motor mudo son indistinguibles en el `.jsonl`, y el consumidor no puede saber si
el número es de fiar.

`Usage.reasoning` de `agentic_models` **no se toca**: sigue siendo lo que dijo el proveedor, porque
esa capa es espejo de A. La derivación vive en el puente (`agentic_runtime`), que es código nuestro.

### Límite que la regla NO deroga

El valor derivado **no acredita `FIND-USAGE-REASONING`**. Son dos cosas distintas y conviene no
confundirlas: la **funcionalidad** se preserva en todos los modelos (esta decisión); el **port del
parseo** del proveedor se acredita contra un proveedor que lo emita (`D-55`, pata aplazada al
2026-09-01 por `D-49`). Si el derivado acreditara la costura, el test mediría el contador propio en
vez del parseo — `no-debilitar-la-prueba`.

### Orden de ejecución

La derivación se implementa **después** de la ventana del 2026-09-01, no antes: el proveedor que sí
desglosa es el único patrón contra el que calibrar que la cuenta de deltas acierta. Implementarla
antes sería validarla contra sí misma. Anotado como encargo abierto en el censo § 5, entrada
`2026-08-28 (i)`, junto al `/effort`.

---

## `D-57` (2026-08-28) — El índice de repliegue `msg_pi_{n}` numera mensajes EMITIDOS, no recorridos

- **Palabra del usuario**: el enunciado de retoma del paso 2, que fija la primera tarea —leer
  `openai-responses-shared.ts:263` y determinar si A avanza el índice en el camino que
  descarta— y su pago condicionado: *«si no lo hace, la numeración `msg_pi_{n}` posterior a un
  asistente vacío diverge y el pago es retirar la línea 169»*.

### Lo leído en el canónico

`msgIndex++` está en `openai-responses-shared.ts:263`, al final del cuerpo del `for` y fuera de
todas las ramas. Dos `continue` lo saltan:

- `:220` — `if (output.length === 0) continue;`, el asistente sin ítems de salida.
- `:157` — `if (content.length === 0) continue;`, el usuario con `content` array vacío.

Luego en A el contador numera **mensajes emitidos**. En B numeraba **mensajes recorridos**.

### Lo inyectado — una línea retirada

`agentic_models/.../openai_responses_shared.py:169`, el `msg_index += 1` que precedía al
`continue` del asistente vacío. Nada más. Efecto medido con el módulo real: un texto sin firma
detrás de un asistente descartado se firmaba `msg_pi_2` donde A firma `msg_pi_1`.

### Alcance real de la divergencia, medido

El repliegue sólo actúa cuando el bloque de texto **no** trae `text_signature`, y eso ocurre en
historial **cross-model**: `transform_messages.py:127` reconstruye el `TextContent` sin firma
cuando el mensaje no es del modelo actual. Con el mismo modelo la firma viene del proveedor y el
fallback no se alcanza.

### Acreditación

`test_provider_roundtrip_openai_responses.py::test_openai_responses_discarded_assistant_does_not_advance_the_fallback_index`,
con criterio y citas en la docstring. **Mutación inyectada y revertida** —reponer el
`msg_index += 1`— desde copia propia verificada por `sha256` (`ffad7943…`, hash idéntico tras el
revert) ⇒ **una roja, cero falsos positivos**. `agentic_models` **69 passed**, `agentic_code`
**261 passed**, sin supervivientes de la prueba. `ruff`: los **6** avisos preexistentes de
`D-52`/`D-53`, ninguno nuevo (el `I001` que dejó el caso nuevo se corrigió en el acto subiendo
los imports al encabezado). Las sintéticas de `agentic_runtime` no se corrieron ni se tocaron.

**Pata de `.jsonl` real: declarada inalcanzable por esta superficie, no omitida.** Exige a la vez
un asistente sin ítems de salida en el historial y un bloque de texto sin firma detrás, o sea un
historial cross-model; ninguna corrida de `agentic_code` lo produce a voluntad. Se declara en vez
de simularse (`D-21`). El cableado en `agentic_code` no necesita acción: su venv monta
`agentic_models` en editable sobre `agentic_models/src`.

### Divergencia hermana, ABIERTA y NO pagada — `FIND-MSGINDEX-USER`

El mismo defecto en el otro camino de descarte: A hace `continue` en `:157` y no avanza; el port
sustituyó ese `continue` por `if parts:` (`openai_responses_shared.py:108-109`), de modo que el
usuario con `content` vacío cae igualmente en el `msg_index += 1` final. Queda **medido y
decidible**; no entraba en el enunciado del paso y no se toca sin palabra del usuario.

### Lo que NO deroga

`D-49` intacto: esto es aritmética de port, no contabilidad, y se acredita sin proveedor frontera.
`D-55` y `D-56` intactos. `D-50` pieza 1 sigue siendo paso propio.

---

## `D-58` (2026-08-28) — La excepción del §4 es la DIRECTIVA, y el docstring de un test es el del test

- **Palabra del usuario**: `procede`, sobre el anuncio del paso 3 —la pieza 1 de `D-50`— que llevaba
  las dos lecturas declaradas por delante.

Contexto: el §4 manda que el fuente vaya sin comentarios ni docstrings, salva las directivas
`# noqa` / `# type:` y admite que **el docstring de un test** declare criterio y citas. Al barrer los
nueve ficheros de `D-50` aparecieron dos casos que el §4 no contestaba, y se deciden aquí en vez de
resolverse en silencio (`D-21` en su forma general: lo no expresable se declara).

### (1) Directiva desnuda: la prosa pegada a un `# noqa` cae

Cuatro directivas llevaban explicación detrás (`tui.py:1369` «layout coordinado por la app»,
`:1374` «frontera de la aplicación TUI», `test_tui.py:439` «contrato de windowing», `:835` «lo normal
es que lo siembre una tool»). Lo que el §4 salva es lo que la herramienta LEE; el texto contiguo es
un comentario ordinario y sesga igual. Se conserva `# noqa: CODE` y cae el resto.

### (2) Andamiaje de un test no es un test

Sobreviven el docstring de módulo del fichero de test y los de las funciones `test_*`. Los de las
clases de apoyo (`CompactingCaller`, `ReadingCaller`, `RecordingCaller`, `_ToolTurnRuntime`) caen:
no declaran el criterio de ninguna prueba, describen un doble. La excepción existe para que el
criterio y la cita canónica viajen con lo que MIDE, no con lo que lo monta.

### Acreditación del barrido

No es una conducta nueva: es una purga que debe ser NEUTRA, y así se midió. AST con docstrings
quitados de los dos lados ⇒ **idéntico en 8 de los 9**; `tui.py` difiere **sólo** por el comentario
que vivía dentro de la cadena CSS de `WorkspaceTuiApp` (una cadena, no un token: se retiró a mano y
se exhibió en diff). `ruff` idéntico al baseline, `agentic_code` **261 passed**, sin supervivientes.
Copia propia de los nueve verificada por `sha256` antes de tocar. Censo § 5, entrada `2026-08-28 (k)`.

### Lo que NO deroga

`D-23` intacto en su reparto —el barrido cubre lo que el paso escribe—: esta purga total es
justamente el **paso propio** que `D-50` reservó para ella. `FIND-MSGINDEX-USER` sigue abierto.

---

## `D-59` (2026-08-28) — `FIND-MSGINDEX-USER`: el hermano del defecto de `D-57`, en la rama de usuario

- **Palabra del usuario**: el enunciado de retoma dejó los cinco pendientes decidibles y su
  orden bastaba por escrito —*«Si es el 1, la orden basta con “replica el continue”»*—; elegido
  con `En esta ventana 1 y 2`.
- **Origen:** la divergencia hermana que `D-57` dejó **ABIERTA y no pagada** en su § final.

### El defecto

`D-57` pagó el camino del asistente y midió el otro sin tocarlo. Es el mismo `msgIndex++` de
`openai-responses-shared.ts:263` —final del cuerpo del `for`, fuera de todas las ramas— y el
otro de sus dos `continue`:

- `:220` — `if (output.length === 0) continue;`, el asistente sin ítems. **Pagado en `D-57`.**
- `:157` — `if (content.length === 0) continue;`, el usuario con `content` en lista vacía.

El port no tenía ahí un `continue` sino una guarda de emisión: `if parts:`
(`openai_responses_shared.py:108-109`). El mensaje no se emitía —eso estaba bien— pero el cuerpo
seguía hasta el `msg_index += 1` de `:203`, así que el usuario descartado **sí consumía número**.
Mismo criterio que `D-57`: el contador numera mensajes **emitidos**, no **recorridos**.

### Lo inyectado — la guarda se vuelve `continue`

`agentic_models/.../openai_responses_shared.py:108-110`, literal del canónico:

```python
if not parts:
    continue
messages.append({"role": "user", "content": parts})
```

Efecto medido **con el módulo real** antes y después, igual que en `D-57`: un texto sin firma
detrás de un usuario de contenido vacío se firmaba `msg_pi_1` donde A firma `msg_pi_0`.

### Alcance real, sin cambio respecto de `D-57`

El repliegue sólo actúa sobre bloques de texto **sin** `text_signature`, y eso es historial
cross-model (`transform_messages.py:127` reconstruye el `TextContent` sin firma cuando el mensaje
no es del modelo actual). Con el mismo modelo la firma la pone el proveedor y el fallback no se
alcanza. Y el usuario llega intacto a la conversión: `transform_messages` lo reenvía tal cual
(`transform_messages.py:80-82`), luego la lista vacía no se filtra antes.

### Acreditación (`D-12·b`)

`test_provider_roundtrip_openai_responses.py::test_openai_responses_discarded_user_does_not_advance_the_fallback_index`,
con criterio y citas en la docstring; contrasta dos historiales que sólo difieren en el usuario
vacío de cabeza y exige el **mismo** id de repliegue en los dos. Verde a la primera ⇒ **mutación
inyectada y revertida** —reponer la guarda `if parts:`— desde copia propia verificada por
`sha256`: **una roja** (`assert ['msg_pi_2'] == ['msg_pi_1']`), **cero falsos positivos**, y el
caso de `D-57` **verde durante la mutación**, que es lo que acredita que los dos casos son
independientes y no uno medido dos veces.

`agentic_models` **69 → 70 passed**, `agentic_code` **261 passed**, sin procesos supervivientes.
`ruff` medido contra baseline —copias de `HEAD` en `mktemp -d`, mismo `pyproject.toml`—: **6
avisos antes, 6 después**, los preexistentes de `D-52`/`D-53` (`S110`/`BLE001` en el proveedor,
`RUF059`/`I001` en el fichero de tests) y ninguno en línea tocada. Deuda neta cero por diff. Las
sintéticas de `agentic_runtime` no se corrieron ni se tocaron (acuerdo de fase).

**Pata de `.jsonl` real: declarada inalcanzable por esta superficie**, por el mismo motivo que en
`D-57` y no por omisión — exige a la vez un usuario con `content` en lista vacía y un texto sin
firma detrás, o sea historial cross-model, que ninguna corrida de `agentic_code` produce a
voluntad (`D-21`). Cableado en `agentic_code` (`cablear-en-agentic-code-al-cerrar`): verificado
que su venv monta `agentic_models` en editable sobre `agentic_models/src`, luego el consumidor ya
ejercita el fuente corregido; no necesita acción.

### Lo que NO deroga

`D-57` intacto y **cerrado**: esta entrada paga la divergencia que aquélla declaró abierta, no
reabre su costura. `D-49` intacto: es aritmética de port y se acredita sin proveedor frontera.
`D-55`, `D-56` y `D-58` intactos. `D-08` intacto: el `continue` y su sitio salen del fuente de A.

---

## `D-60` (2026-08-28) — `/effort`: el catálogo de niveles lo DECLARA el modelo, y `off` es un nivel que hay que saber transportar

- **Palabra del usuario**: `En esta ventana 1 y 2`, sobre los cinco pendientes que el enunciado de
  retoma dejó decidibles. El 1 fue `FIND-MSGINDEX-USER` (`D-59`); éste es el 2, cuyo encargo literal
  está en el censo § 5, entrada `2026-08-28 (i)`: *«`/effort` como slash command — seleccionar nivel
  de razonamiento desde la TUI, incluyendo `off` (no pensar) y los niveles que el modelo local
  declare disponibles»*.
- **Encuadre de partida, y en qué era falso.** El encargo daba por hecho que *«el transporte ya
  existe —`caller.py` traduce `effort` y rechaza lo inexpresable—; lo que falta es la superficie de
  usuario»*. La superficie faltaba, sí. Pero el transporte de **`off`** no existía, y el catálogo de
  niveles del perfil local **mentía en tres sitios**. Una superficie montada sobre eso habría
  ofrecido niveles que devuelven HTTP 500 y un `off` que no apaga nada.

### La plantilla del motor es la prueba (`D-15`: el consumidor detecta)

Extraída de `http://localhost:8080/props` y leída 1→EOF (184 L), la plantilla de chat de Qwen3.8:

```jinja
{%- if enable_thinking is undefined or enable_thinking is true %}
    {%- set resolved_reasoning_effort = reasoning_effort|default('xhigh') %}
    {%- if resolved_reasoning_effort == 'high' %}
        {%- set resolved_reasoning_effort = 'xhigh' %}
    {%- endif %}
    {%- if resolved_reasoning_effort not in ('xhigh', 'medium', 'low') %}
        {{- raise_exception('Unexpected reasoning effort ' ~ reasoning_effort ~ '. Supported types are xhigh (default), medium, and low.') }}
...
{%- if add_generation_prompt %}
    {{- '<|im_start|>assistant\n' }}
    {%- if enable_thinking is defined and enable_thinking is false %}
        {{- '<think>\n\n</think>\n\n' }}
```

De ahí, los tres embustes del catálogo anterior:

1. **`minimal` no es un nivel: es un HTTP 500.** Cae en el `raise_exception`.
2. **`high` no es un nivel distinto**: la plantilla lo reescribe a `xhigh` **en silencio**, antes de
   comprobar nada. Declararlo por separado es prometer una gradación que el motor no tiene.
3. **`xhigh` sí existe y estaba oculto** — y es además el **defecto** de la plantilla.

Y el cuarto, el que obliga al mecanismo: **`off` sí existe en este motor**, pero por el kwarg de
plantilla `enable_thinking: false`, **no** por ningún valor de `reasoning.effort`. El catálogo lo
declaraba y no lo transportaba: `caller.py` traducía a `reasoning = "off"`, el provider no tenía
dónde ponerlo, y el turno razonaba igual. Es exactamente el modo de fallo que `D-21` legisla —una
opción inexpresable descartada en silencio produce la misma captura que obedecerla— sólo que aquí el
descarte lo hacía nuestro propio port.

### Lo inyectado

1. **El transporte de `off` SE CREA** (`D-22`), en el proveedor y no en el puente:
   `providers/openai_responses.py::_build_params` gana la rama `else` del bloque `model.reasoning`.
   Con prioridad para el camino canónico —si `thinking_level_map["off"]` trae un valor de effort, se
   manda como `reasoning: {"effort": …}`— y, sólo si no lo trae, se lee
   `compat["thinkingOffParams"]` y se vuelca en `extra_body`. Sin declaración, **no se inventa
   nada**: el turno sale idéntico a como salía. `github-copilot` queda fuera, como en A.
   El campo es `extra_body` porque `AsyncResponses.create` del SDK `openai` **no tiene `**kwargs`**:
   un campo no estándar que no viaje ahí no viaja.
2. **El catálogo local dice lo medido** (`models/local_catalog.py`): `thinking_level_map` con
   `minimal: None` y `high: None` —`get_supported_thinking_levels` salta el nivel cuyo valor es
   `None`—, `low`/`medium`/`xhigh` con su grafía, y `compat={'thinkingOffParams':
   {'chat_template_kwargs': {'enable_thinking': False}}}`. Resultado declarado:
   `['off', 'low', 'medium', 'xhigh']`, con `clamp('high') → 'xhigh'` y `clamp('minimal') → 'low'`.
3. **El seam de turno**: `EFFORT_APP_STATE_KEY` / `EFFORT_SETTING` (`effortLevel`, ámbito `global`)
   en `tools/native/supported_settings.py`, y `_with_effort` en `loop/agent_loop.py`, que resuelve
   el nivel del `app_state` a `ModelOptions`. `off` viaja como `effort=None` **más**
   `ThinkingConfig(enabled=False)`: la ausencia sola dejaría el default del motor, que es justo lo
   que `off` niega. Un nivel desconocido levanta `UnsupportedModelOptionError`, no se ignora.
4. **La superficie**: `EffortState` (`agentic_code/composition.py`) —`current`/`supported`/`select`/
   `clear`, con `attach` sobre `app_state.native`— y el comando `/effort [off|nivel|auto]`
   (`builtin_commands.py`). Sin argumento lista el nivel vigente y **el catálogo que declara el
   modelo**, no un vocabulario fijo; `auto` devuelve el turno al default del motor; un nivel no
   declarado se **rechaza con su motivo** (`D-21`), no se silencia ni se recorta al vecino.
   `cli.py` la siembra desde lo persistido: `OFF_EFFORT_LEVEL if settings.thinking is False else
   settings.effort`.
5. **`capture.py::_digest` proyecta `extra_body` e `include`.** No es cosmética: es lo que hizo que
   la evidencia mintiera por omisión — ver abajo.

### Divergencias declaradas frente a A (`D-21`)

1. **Vocabulario.** A publica `low|medium|high|max` más `auto` y los fija en su catálogo de producto.
   El nuestro **no es fijo**: es el que el modelo declara, y por eso el mismo comando ofrece cuatro
   niveles aquí y otros en otro proveedor. Es `D-56` aplicado a la superficie: la funcionalidad
   homologada —elegir esfuerzo— se preserva en todos los modelos, y lo que se adapta es el catálogo.
2. **Ámbito.** En A la elección se persiste en `userSettings`. La nuestra es **de sesión**: se
   siembra desde el `effortLevel` persistido y muere con el proceso. `EFFORT_SETTING` existe y es
   legible/escribible por la vía de configuración; lo que el comando no hace es escribirla.
3. **`off` como nivel de primera clase.** A apaga el pensamiento por otra vía; aquí `off` entra en
   la misma lista que los demás porque el motor local lo expresa, y omitirlo dejaría al usuario sin
   forma de pedirlo.

### El defecto de instrumentación que estuvo a punto de invertir el veredicto

La primera corrida E2E con `--no-thinking` mostró `reasoning: null` y **ningún** `extra_body` en el
`.jsonl`, lo que se leía como «la inyección no llegó». Era falso: `PayloadRecorder._digest` **no
proyectaba `extra_body`**, luego el único campo que podía probar el arreglo era el único que la
captura no miraba. Se confirmó leyendo la clave `payload` de una corrida con
`AGENTIC_CODE_CAPTURE_PAYLOADS_FULL=1`, y se pagó en el propio digest. Queda anotado porque es la
forma más cara de error de este proyecto: **un instrumento ciego no dice «no sé», dice «no»**.

### Acreditación

**E2E en el cable, los dos sentidos** (`D-15`, `llama-server` vivo):

| mando | lo que viajó | HTTP | eventos de razonamiento | respuesta |
|---|---|---|---|---|
| `--no-thinking` | `extra_body: {"chat_template_kwargs": {"enable_thinking": false}}` | 200 | **0** | `391` |
| `--effort xhigh` | `reasoning: {"effort": "xhigh", "summary": "auto"}` | 200 | **28** | — |

**Pruebas.** `agentic_models/tests/test_thinking_off_transport.py` (4 casos): `off` viaja cuando el
modelo declara cómo apagarlo; sin declaración **no se inventa** nada; un valor de effort para `off`
en `thinking_level_map` **conserva la precedencia**; y el perfil local declara los niveles medidos.
`agentic_code/tests/test_effort_command.py` (6 casos) reescrito **contra la medición, no ablandado**
(`no-debilitar-la-prueba`): el listado exige `off, low, medium, xhigh · auto` y **ausencia** de
`minimal`; `off` llega al turno como `effort is None` + `thinking.enabled is False`; `xhigh` llega
como `Effort.XHIGH`; `minimal` se rechaza con su motivo y no llega `effort` alguno; `auto` limpia.
Las citas de la plantilla viven en los docstrings, única excepción del § 4.

**`D-12·b`**: copia en `mktemp -d` verificada por `sha256`
(`a5450c0f4037c97a94f7d26a86db1d36a1fb1a30d6750b618c28a347f1c94228`), mutación `off_params = None`
⇒ **una roja**, revert desde la copia con `sha256` idéntico, 4/4 verdes, scratch borrado por ruta
absoluta.

**Suites**: `agentic_models` **70 → 74 passed**, `agentic_code` **266 → 267 passed**, sin procesos
supervivientes. `ruff` limpio en lo tocado; los dos avisos preexistentes de `openai_responses.py`
(`I001`, `BLE001`) no se tocan. Las sintéticas de `agentic_runtime` no se corrieron ni se tocaron
(acuerdo de fase).

### Riesgo residual, declarado y NO generalizado (`declarar-no-es-pagar`)

`get_supported_thinking_levels` sigue declarando `off` para **cualquier** modelo de razonamiento
cuyo mapa no traiga la clave `off` y cuyo proveedor no tenga off-params — es decir, puede seguir
prometiendo un `off` que no viaja, en otros perfiles. Aquí se paga donde hay medición; extenderlo a
proveedores no medidos sería inventar conducta. Queda vigilado.

### Lo que NO deroga

`D-21` intacto y **aplicado**: la opción que el motor no expresa se rechaza en la superficie con su
motivo, y la que sí expresa se transporta en vez de descartarse. `D-56` intacto: el catálogo se
deriva del modelo, no se recorta al mínimo común. `D-49` intacto: esto es transporte y superficie,
no veredicto de conducta — el `xhigh` de 28 eventos acredita **mecanismo**, y el 1 de septiembre
sigue siendo la fecha del sujeto real. `D-59` intacto.

---

## D-61 · `auto` no es `off`, y `off: None` no es `off` ausente

**2026-08-29.** Fase `agentic_code` · prueba E2E contra las peculiaridades de gpt-5.x, cableado
contra `llama-server` + `unsloth/Qwen3.8-27B-GGUF:UD-IQ4_XS`.

### El motivo: la semántica de razonamiento de Qwen3.8 no es la de gpt-5.x

`reasoning_effort` **no es un presupuesto** en esta plantilla: su efecto entero es una frase
inyectada en la cabecera del bloque `system`. Medido en la `tokenizer.chat_template` del propio GGUF
(extraída con parser propio del binario; `gguf-py` no era usable sin `numpy`), líneas 57-71:

| nivel | lo que inyecta |
|---|---|
| `xhigh` (**default** si no se manda nada) | *"think carefully… validate key assumptions, consider plausible alternatives…"* |
| `medium` | **nada**. `reasoning_instructions` queda vacío. Es el nivel **mudo**. |
| `low` | *"Keep your thinking brief and focused, moving directly to the conclusion…"* |

`high` se reescribe a `xhigh` antes de comprobarse (`:60-62`); `minimal` levanta excepción
(`:63-65`). Y `<think>` se abre **forzado** salvo `enable_thinking: false` (`:176-183`).

La corrida muerta iba en `medium` (capture: `reasoning={'effort':'medium','summary':'auto'}`), con
`<think>` abierto y `n_remain=-1` en `/slots`: razonamiento abierto **sin una sola palabra sobre
hasta dónde**. Programó dentro del pensamiento porque nadie le puso borde. `low` es el único de los
tres niveles que lo pone.

### Transporte, verificado en fuente de `llama.cpp` (HEAD `c060ca97`)

| eslabón | fichero:línea | qué acredita |
|---|---|---|
| el convertidor Responses→chatcmpl **copia el cuerpo entero** | `server-chat.cpp:15` | toda clave que no conoce **sobrevive** |
| `reasoning.effort` → `reasoning_effort` | `server-chat.cpp:286-293` | el `summary` se descarta en silencio |
| `max_output_tokens` → `max_tokens` | `server-chat.cpp:281-284` | el techo **sí** se honra |
| items `reasoning` → `message.reasoning_content` | `server-chat.cpp:217-241` | `preserve_thinking` es real |
| `reasoning_effort` → kwarg del Jinja; `"none"` ⇒ `enable_thinking=false` | `server-common.cpp:1313-1321` | el nivel llega a la plantilla |
| `chat_template_kwargs` del cuerpo **se mezclan** sobre los de CLI | `server-common.cpp:1296-1300` | vehículo de `preserve_thinking` |
| `reasoning_budget_tokens` / `thinking_budget_tokens` **aceptados del cuerpo** | `server-common.cpp:1354-1365` | el sampler de `reasoning-budget.cpp` es alcanzable **desde Responses** |

**Corrección de un finding previo**: era falso que el presupuesto de razonamiento viviera sólo en la
superficie anthropic. Ésta sólo lo **traduce** (`server-chat.cpp:586-592`); el parser lo acepta
directo. No se cablea aún: primero `low` + `preserve_thinking:false`, y se mide. Dos palancas a la
vez impiden saber cuál actuó.

### El error, que resultó ser doble

Verificado contra el canónico (`D-08`) en `pi/packages/ai/src/api/openai-responses.ts:262-266`:

```ts
} else if (model.provider !== "github-copilot" && model.thinkingLevelMap?.off !== null) {
    params.reasoning = { effort: (model.thinkingLevelMap?.off ?? "none") };
}
```

**El colapso es genuino de A**: no pedir nivel significa **apagar**, y `streamSimple:176` colapsa
`off` en `undefined` igual que nosotros. No es un fallo de copia. Los dos fallos son otros:

1. **`auto` es invención nuestra con etiqueta falsa.** En A no existe «auto»; nosotros lo ofrecemos
   en `/effort` y prometemos «default del motor», mientras el transporte emitía
   `enable_thinking:false`. La etiqueta mentía. `D-22`: el mecanismo que falta **se construye** —
   `reasoning_off` explícito, puesto sólo por `stream_simple` cuando el nivel pedido es `off`.
2. **Se perdió la guarda de A al portar.** A distingue `off: null` (*no expresable* ⇒ no manda nada
   y queda el default del motor) de `off` **ausente**. `tmap.get("off")` devolvía `None` en ambos
   casos y **borró la distinción**. Es exactamente el riesgo residual declarado y vigilado en
   `D-60`: aquí se paga.

Añadido además el canal que no existe en A porque A nunca habla con un motor Jinja
(`D-22`): `compat["templateKwargs"]`, que viaja en **toda** petición. `thinkingOffParams` sólo se
emite en la rama de apagado, luego no servía de vehículo para `preserve_thinking`.

**`preserve_thinking: false` es menos agresivo de lo que aparenta.** La condición de la plantilla es
`preserve_thinking … or loop.index0 > ns.last_query_index` (`:119`), y `ns.last_query_index`
(`:95-105`) ignora los `user` que son puro `<tool_response>`: el razonamiento del **ciclo agentic en
curso se conserva íntegro** y sólo se poda el de los ciclos ya cerrados. No rompe la cadena del
turno vivo. Que el runtime sea la memoria, no el historial de pensamiento del modelo.

### Payload real del perfil local, tras el corte

| mando | `reasoning` | `extra_body` |
|---|---|---|
| `auto` | — | `{'chat_template_kwargs': {'preserve_thinking': False}}` |
| `low` | `{'effort':'low','summary':'auto'}` | idem |
| `medium` | `{'effort':'medium','summary':'auto'}` | idem |
| `xhigh` | `{'effort':'xhigh','summary':'auto'}` | idem |
| `off` | — | `{'chat_template_kwargs': {'enable_thinking': False, 'preserve_thinking': False}}` |

### Pruebas

`test_thinking_off_transport.py` **4 → 8 casos**, escritos contra el criterio
(`no-debilitar-la-prueba`): `auto` **no** manda apagado; `off: None` declarado no expresable manda
**nada**; los `templateKwargs` viajan **con nivel activo**; off-params y `templateKwargs` **se
mezclan** en vez de pisarse. `test_auto_returns_the_turn_to_the_engine_default` medía sólo el borde
del caller mientras el transporte hacía lo contrario: su docstring ahora **cita dónde se mide la
otra mitad**, en vez de prometer lo que no toca.

**Suites**: `agentic_models` **74 → 78 passed**, `agentic_code` **267 passed**, sin procesos
supervivientes. Sintéticas de `agentic_runtime` ni corridas ni tocadas (acuerdo de fase).

### Lo que NO deroga

`D-08` intacto: el colapso de A se leyó en fuente **antes** de tocar, y no se «arregló» lo genuino —
se construyó lo que A no tiene y se restauró lo que A sí tenía. `D-21` intacto y aplicado: `off`
sigue siendo un nivel que viaja, y ahora `auto` deja de suplantarlo. `D-49` intacto: esto es
transporte y semántica de plantilla, **no veredicto de conducta**; el efecto de `low` sobre el
razonamiento se mide en la corrida siguiente, con marcador antes/después. `D-56`, `D-59`, `D-60`
intactos.

### Abierto

El techo de salida sigue sin viajar: `options.max_tokens` es `None` en toda la cadena, luego
`max_output_tokens` nunca se escribe (`openai_responses.py:142-143`) — acreditado en capture, y
`n_remain=-1` en `/slots`. Y la superficie Responses de `llama.cpp` es **la única de las tres** que
no reporta ni el corte (`status` fijo en `"completed"`, `server-task.cpp:695` y `:587`, frente a
`to_json_oaicompat_chat_stream:464` y `to_json_anthropic_stream:800`) ni los tokens de razonamiento
(sin `output_tokens_details` ⇒ `P14`). Elegir esa superficie es, en sí, un hallazgo. Sin pagar aquí.

---

## D-62 · La derivación de `D-56` se adelanta: lo que esperaba al 2026-09-01 era la barra de error, no el número

**2026-08-29.** Fase `agentic_code` · prueba E2E contra las peculiaridades de gpt-5.x. Deroga
parcialmente `D-56` §*Orden de ejecución*.

- **Palabra del usuario**, en tres tramos. Elección del paso: `D-56: derivar reasoning`. Sobre mi
  intento de elevarle dos binarias que el propio expediente ya resolvía: *«me pides que yo te
  apruebe algo que tu has leido por tanto lo has documentado para tu uso y yo no?»* y, a la
  segunda, `idem`. Sobre la ambigüedad de mi alcance: *«hace bastante rato me dices que necesitas
  que el conteo de tokens permita calcular el tamaño de thinking, considerando que estamos teniendo
  problemas con el modelo local, acepte porque entendi que era necesario para determinar que
  necesitamos corregir para mitigar el problema, pero me dices que no puedes determinar por la
  fecha en la cual puedo volver a usar gpt-5.x, en que quedamos?»*. Y el mando de ejecución:
  *«ningun cierre, trabajamos ya y luego que se prueba y se confirma recien se cierra»*, cerrado
  con `de acuerdo`.

### Dos errores míos en el enunciado de retoma, hallados antes de mutar

1. **Blanco equivocado.** El enunciado señalaba el `or 0` de
   `openai_responses_shared.py:363` como la deuda a pagar. `D-56:3551` dice lo contrario con todas
   sus letras: *«`Usage.reasoning` de `agentic_models` no se toca: sigue siendo lo que dijo el
   proveedor, porque esa capa es espejo de A. La derivación vive en el puente»*. Esa línea es el
   espejo de `openai-responses-shared.ts:370` y **no se ha tocado**. El `0` mudo real estaba en
   `agentic_runtime/models/caller.py`.
2. **Fecha equivocada, y es la que originó la pregunta del usuario.** Yo estaba usando «derivar»
   para dos cosas distintas: **saber que el contador está mudo** —medible hoy, sin proveedor
   frontera— y **cuantificar el razonamiento** —cuyo número también se produce hoy; lo que el
   proveedor que sí desglosa aporta es la **calibración**, o sea la barra de error—. `D-56`
   §*Orden de ejecución* aplazaba la implementación entera al 2026-09-01 para no *«validarla contra
   sí misma»*. El aplazamiento correcto es el de la **acreditación de exactitud**, no el del
   instrumento: sin instrumento, la ventana del 2026-09-01 llegaría sin nada que calibrar.

### Lo inyectado

- `agentic_runtime/contracts/events.py` — las tres constantes de procedencia y
  `Usage.thinking_tokens_source`, al **final** del dataclass para no alterar la construcción
  posicional existente (mismo criterio que `D-55` con `Usage.reasoning`). Más
  `weakest_thinking_tokens_source`, que ordena `provider < counted < unavailable` y devuelve el
  eslabón **más débil** de los dos.
- `agentic_runtime/events/event_types.py` — reexporta lo nuevo por el mismo punto que el resto.
- `agentic_runtime/models/caller.py` — el puente, donde `D-56` sitúa la derivación. Acumula los
  `thinking_delta` del turno; si el motor no emite deltas y entrega el razonamiento entero en el
  mensaje del `done`, lo toma de ahí, con guarda para no sumar dos veces el mismo razonamiento
  visto por las dos vías. Y las tres reglas de `D-56` en su orden: contador del proveedor →
  derivado → indisponible.
- `agentic_code/src/agentic_code/streaming.py` — `StreamUsage` **acumula** turnos y su total va a
  la línea `result` del `.jsonl`, luego la procedencia del agregado se pliega por el eslabón más
  débil. Un total sumado de un turno medido y otro indisponible **no es** un total medido:
  rotularlo `provider` reintroduciría en el agregado justo el 0 mudo que se acaba de matar en el
  turno.
- `agentic_code/src/agentic_code/capture.py` — **sin cambios**: `_canonical_message` y `finish`
  serializan el `Usage` con `asdict`, luego el campo nuevo llega a `runtime_event` y a
  `message.event.usage` sin tocar nada.

### El método de la derivación, y por qué no es una invención

No hay tokenizador real en ninguno de los venv (`tiktoken`, `transformers`, `tokenizers`,
`sentencepiece`: los cuatro ausentes). Yo había anunciado que, sin uno, `caracteres/4` sería
*«inventar»* y el paso quedaría sin pagar. **Esa premisa era falsa y se retira.** El estimador
`rough_token_count` de `agentic_runtime/context/estimation.py` es el instrumento homologado con el
que el runtime dimensiona la ventana de contexto, y su `rough_token_count_for_block` **ya
contempla el bloque `thinking`** (`:52-53`). Derivar con él no introduce método nuevo: reusa el que
ya está en la casa. Y la etiqueta `counted` es precisamente la que declara que el número es
derivado y no del proveedor — que es la razón de ser del campo.

Queda dicho para la ventana del 2026-09-01: `counted` **no afirma exactitud**. `D-56:3536-3539`
midió que en el motor local los deltas son **por token**, y `llama-server` expone `/tokenize` si se
quisiera exactitud al token. La calibración contra un proveedor que desglose sigue pendiente y es
lo único que esa fecha aporta aquí.

### Acreditación (`D-12·b`)

Nueve casos nuevos en `agentic_code/tests/test_usage_reasoning_bridge.py` —de 3 a 12—, con el
criterio y sus citas en cada docstring, sobre el puente **real** y el capturador **real**; lo único
sustituido es el motor. Verde a la primera ⇒ **siete mutaciones inyectadas y revertidas** desde
copia propia verificada por `sha256`, cada una enrojeciendo exactamente sus casos y sólo ésos:

| | mutación | rojas |
|---|---|---|
| M1 | procedencia siempre `provider` | 2 |
| M2 | procedencia siempre `unavailable` | 1 |
| M3 | el agregado se queda con el último turno, no con el más débil | 1 |
| M4 | se ignora la derivación (vuelve el `0` mudo) | 3 |
| M5 | el derivado gana al contador del proveedor | 1 |
| M6 | sin la guarda de duplicado, el bloque final se suma otra vez | 1 |
| M7 | `counted` pasa por más fiable que `provider` en el agregado | 1 |

Hashes tras revert: `caller.py` `873333bf0df0cb58f89567b22976e717e3b812ba88ed931ce2484e67b1022fc6`,
`contracts/events.py` `260553479cdfeba528f2aafd40c91a0f2f3c7c2f6f05f4d7b660ea6547e8b871`,
`streaming.py` `665166740d181f1b8ce22e08a78af1080ac284f26e68d9b5250b1b2d66717b87`.

### Corrección del protocolo de revert: `sha256` acredita el FICHERO, no el MÓDULO CARGADO

M7 pasó su verificación por `sha256` y **aun así el intérprete seguía ejecutando el bytecode
mutado**. La mutación era un intercambio de dos líneas de tamaño total idéntico, y el `cp` del
revert dejó el fuente con el **mismo `mtime` al segundo** que el `.pyc` escrito durante la
mutación. CPython invalida por `(mtime, size)`: ambos coincidían, luego el `.pyc` viejo se dio por
válido sobre un fuente ya sano. Se manifestó como un rojo en la suite completa que **no** aparecía
en la aislada, y la lectura ingenua habría sido «el código está mal».

Es de la misma familia que el defecto de instrumentación de `D-60` §*El defecto de instrumentación
que estuvo a punto de invertir el veredicto*: el instrumento no dice «no sé», dice «no».
**Consecuencia operativa:** una mutación de tamaño neutro exige purga de bytecode en el revert, y
la verificación del revert se cierra ejecutando el símbolo, no sólo comparando el hash. Purgado el
`.pyc` y forzada la recompilación de los dos árboles antes de dar la ronda por buena.

### Suites, `ruff`, `mypy` y procesos

`agentic_code` **272 → 277 passed**; `agentic_models` **78 passed** (capa intacta, no se tocó).
`ruff`: `agentic_code` **All checks passed**; `agentic_runtime` **6 avisos, los preexistentes** de
`compact/` y `tests/`, **ninguno en fichero tocado** — deuda neta cero por diff. `mypy` sobre los
tres ficheros de `agentic_runtime` tocados: `Success: no issues found`. Sin procesos supervivientes.
Las sintéticas de `agentic_runtime` no se corrieron ni se tocaron (acuerdo de fase).

### Barrido de comentarios

`D-23` / `D-58`: los cuatro ficheros tocados quedan sin comentarios ni docstrings de módulo o
función, salvo las directivas `# noqa` desnudas —a las dos de `caller.py` se les retiró la prosa
pegada, que es el caso (1) de `D-58`—. Las citas del canónico y de `D-56` viven en el docstring de
cada test, única excepción del § 4.

### Lo que NO deroga

`D-56` **intacto en su regla**: las tres reglas se implementan en su orden y sin casos especiales;
lo que esta entrada deroga es su §*Orden de ejecución*, y sólo en el tramo del instrumento.
`D-56` §*Límite que la regla NO deroga* **intacto y respetado**: el valor derivado **no acredita**
`FIND-USAGE-REASONING`; el port del parseo sigue esperando a un proveedor que lo emita, y ningún
test nuevo lo mide. `D-49` intacto: esto es instrumento, no veredicto de conducta — el 2026-09-01
sigue siendo la fecha del sujeto real, y ahora además la de la calibración de `counted`. `D-55`
intacto: su `Usage.reasoning` no se toca. `D-08` intacto: el blanco y el orden salen del fuente, no
del razonamiento. `D-21` intacto: la ausencia de tokenizador se declara con su método sustituto y
su límite, no se descarta en silencio.

### Abierto, sin cambio

`P14` sigue siendo un defecto del servidor, no nuestro: `llama.cpp` sigue sin emitir
`output_tokens_details`. Lo que cambia es que su `.jsonl` deja de mentir por omisión. Siguen
abiertos y no tocados: el techo de salida (`options.max_tokens` es `None` en toda la cadena, luego
`max_output_tokens` nunca se escribe), `FIND-GOOGLE-CASING`, `cache_write_1h` sin consumidor real,
y el cableado de `thinking_budget_tokens` como control primario.

---

## D-63 · El techo de salida y el presupuesto de razonamiento: dos palancas que existían y no llegaban al cable

**2026-08-29.** Fase `agentic_code` · prueba E2E contra las peculiaridades de gpt-5.x. Cierra los dos
puntos abiertos en `D-62` §*Abierto, sin cambio*. Addendum a `D-61`.

- **Palabra del usuario**: elección del paso, *«prosigue con 2 y 3 en esta fase…»*; y, tras el
  anuncio con evidencia plena de ambos puntos, `procede`.

### El enunciado del punto 2 era corto: no era una línea, era una costura

El pendiente decía «`options.max_tokens` es `None` en toda la cadena». Cierto, pero la causa son
**tres pérdidas distintas**, cada una con su cita:

1. **El respaldo al tope del modelo.** A: `options?.maxTokens ?? model.maxTokens`
   (`simple-options.ts:29`). B hacía `max_tokens=opts.max_tokens` a secas. De ahí el `None`.
2. **El recorte contra la ventana.** `clampMaxTokensToContext` (`simple-options.ts:15-19`) no
   existía en B, **ni su dependencia** `estimateContextTokens` (`utils/estimate.ts`, 111 líneas):
   `agentic_models/utils/` no tenía `estimate.py`. `D-22`: lo que no está se crea.
3. **El suelo de 16.** `Math.max(options.maxTokens, OPENAI_RESPONSES_MIN_OUTPUT_TOKENS)`
   (`openai-responses.ts:29,236-238`; idéntico en `azure-openai-responses.ts:23-24,268-269`). B
   escribía el valor crudo en las **dos** rutas. Sin él, el recorte del punto (2) puede producir por
   sí mismo la petición que la API rechaza.

La cita del enunciado (`openai_responses.py:142-143`) estaba desfasada: el sitio era `:165-166`.

### Nueve llamantes, no uno

`build_base_options` se llama desde **nueve** proveedores. Su firma pasa a la de A,
`(model, context, options, api_key)`, y los nueve pasan `context`. **Se rechazó** hacer `context`
opcional: habría dejado ocho proveedores sin recortar, que es exactamente la homologación parcial
que `D-56` prohíbe.

### Punto 3 · la capacidad es del MOTOR, no de la `api`

`supports_thinking_budget` excluía por `api` a toda la familia Responses, y su docstring lo afirmaba
como hecho: *«has no equivalent field … dropped without a trace»*. Contra fuente de `llama.cpp`
(`HEAD c060ca9`) eso es falso para el perfil local:

- `server-chat.cpp:15` — `json chatcmpl_body = response_body;`: el cuerpo entero se copia, luego las
  claves desconocidas **sobreviven** a la traducción Responses→OAI.
- `server-common.cpp:1354-1355` — `json_value(body, "reasoning_budget_tokens", json_value(body,
  "thinking_budget_tokens", -1))`: se leen del cuerpo.
- `server-chat.cpp:586-593` — la propia ruta Anthropic→OAI de `llama.cpp` escribe
  `oai_body["thinking_budget_tokens"]`: es su nombre de campo, no una invención nuestra.

Ensanchar por `model.api == "openai-responses"` habría sido **falso para OpenAI real**: la misma
`api` llega a motores que leen el campo y a motores que no. La capacidad se declara **por modelo**,
en `compat["thinkingBudgetParam"]`, que nombra el campo del cuerpo — el vehículo que ya existía
(`D-61`) y el sitio donde `D-21` sitúa el conocimiento de proveedor. Donde no está declarado, la
opción se sigue **rechazando con su razón** en `caller.py:237-251`, no descartándose.

La segunda mitad de la pérdida estaba en `stream_simple`: `build_base_options` devuelve un
`StreamOptions` pelado, y lo que el proveedor no vuelve a enganchar se pierde sin traza —
`thinking_budgets` no se reenganchaba. El presupuesto sale ahora de
`adjust_max_tokens_for_thinking`, espejo de `anthropic.py:755-769`, y viaja por `extra_body`.

### Addendum a `D-61`: hay una guarda que `D-61` no registró

`D-61` daba el sampler por alcanzable desde Responses. Es correcto, pero **incompleto**:
`server-common.cpp:1360` condiciona el paso al sampler a
`if (!chat_params.thinking_end_tags.empty())`. El presupuesto sólo llega si la plantilla del chat
expone etiquetas de fin de pensamiento. No invalida `D-61`; lo acota.

### Lo inyectado

- `agentic_models/utils/estimate.py` — **nuevo**, port de `estimate.ts`: `CHARS_PER_TOKEN=4`,
  `ESTIMATED_IMAGE_CHARS=4800`, y las siete funciones, incluida la regla de que un bloque de uso
  reportado **sustituye** a lo estimado antes de él y que un turno `aborted`/`error` no cuenta como
  uso reportado.
- `agentic_models/providers/simple_options.py` — `CONTEXT_SAFETY_TOKENS`, `MIN_MAX_TOKENS`,
  `clamp_max_tokens_to_context`, firma nueva de `build_base_options`, `thinking_budget_param` y
  `supports_thinking_budget` ensanchado por declaración.
- `agentic_models/providers/openai_responses.py` — suelo de 16, emisión del presupuesto por
  `extra_body` bajo el nombre declarado, y reenganche en `stream_simple`.
- `agentic_models/providers/azure_openai_responses.py` — el mismo suelo de 16 que A tiene y B no
  tenía.
- `agentic_models/models/local_catalog.py` — `'thinkingBudgetParam': 'thinking_budget_tokens'`.
- Los nueve llamantes de `build_base_options`, con `context`.

### Acreditación (`D-12·b`)

18 casos nuevos en `test_output_ceiling.py` (10) y `test_thinking_budget_transport.py` (8), con
criterio y citas en los docstrings. Verde a la primera ⇒ **doce mutaciones inyectadas y revertidas**
desde copia propia verificada por `sha256`, con purga de bytecode en cada revert (`D-62`) y hash
comprobado tras cada una. Doce rojos, cero falsos positivos:

| | mutación | rojas |
|---|---|---|
| M1 | sin respaldo al tope del modelo | 1 |
| M2 | sin recorte contra la ventana | 2 |
| M3 | ventana no declarada tratada como declarada | 1 |
| M4 | sin suelo de 16 | 1 |
| M5 | se ignora el bloque de uso reportado | 1 |
| M6 | no se cuenta el prefijo sistema+tools | 1 |
| M7 | un turno abortado cuenta como uso reportado | 1 |
| M8 | capacidad por `api`, no por declaración del modelo | 2 |
| M9 | declaración vacía tomada por declaración | 1 |
| M10 | el presupuesto no llega al cuerpo | 2 |
| M11 | `stream_simple` no reengancha el presupuesto | 1 |
| M12 | el perfil local deja de declarar el campo | 1 |

Hashes del estado sano: `utils/estimate.py`
`b449932794a9ee1a615cb6bbb1bfe72c30ad5213680369a217147baa9f986e4f`,
`providers/simple_options.py` `0b7cae694501fd87220b796a0d4988c8f84b93de94a4089eac4f3fff07fc6ce6`,
`providers/openai_responses.py` `f874ce0e89dea8011a03d60a3579f4a0c64897461da5d010a56b31210c5156f2`,
`providers/azure_openai_responses.py`
`6d04f8b0978da63929eac52e0f9e596668c1ef2cfabba61438fd95a2082201bc`,
`models/local_catalog.py` `8e5a6676fec56b735bbf67639d7ccc28553991260017998eca46bbd10fe8f5c0`.

### Medido en vivo, no sólo en el borde

Contra `llama-server` + `unsloth/Qwen3.8-27B-GGUF:UD-IQ4_XS`, `validacion-por-consumidor-real`:

- **El techo llega al cable.** `max_output_tokens: 4096`, y `/slots` pasa de `n_predict=-1` a
  `n_predict=4096`. La corrida muerta que originó el pendiente ya no se reproduce.
- **El presupuesto llega y muerde.** Cuerpo real:
  `{"thinking_budget_tokens": 256, "chat_template_kwargs": {"preserve_thinking": false}}`. Con el
  mismo prompt y `xhigh`: presupuesto **32** ⇒ **139** caracteres de razonamiento; presupuesto
  **4096** ⇒ **11.274**. Dos órdenes de magnitud de diferencia con lo demás idéntico: el sampler de
  `reasoning-budget.cpp` está actuando. La corrida de 32 además topó en `output_tokens=4096`, o sea
  que las dos palancas se ven a la vez y no se estorban.

### Suites, `ruff`, `mypy` y procesos

`agentic_models` **78 → 96 passed**; `agentic_code` **277 passed** (sin cambio: la capa integradora
no se tocó). `ruff` sobre los ficheros tocados: los dos avisos de `openai_responses.py` (`I001`,
`BLE001`) se comprobaron **idénticos en `HEAD`** ⇒ deuda neta cero por diff; el resto, limpio.
`mypy` sobre los cuatro ficheros tocados: los dos únicos errores son los preexistentes de
`_create_client` (`:135`, `:141`), ajenos a este pago. Sin procesos supervivientes. Sintéticas de
`agentic_runtime` ni corridas ni tocadas (acuerdo de fase).

### Lo que NO deroga

`D-08` intacto: las tres pérdidas y la guarda nueva salen de leer fuente —A y `llama.cpp`—, no de
deducir. `D-21` intacto y **reforzado**: el presupuesto se rechaza donde no hay campo declarado, y
lo que cambia es que ahora existe una forma de declararlo en vez de una exclusión por `api` escrita
a mano. `D-22` aplicado: `estimate.py` y `clamp_max_tokens_to_context` se construyeron. `D-56`
respetado: la firma cambia en los nueve, no en uno. `D-49` intacto: esto es transporte, no veredicto
de conducta.

### Abierto

La guarda `thinking_end_tags` (`server-common.cpp:1360`) es una precondición del motor que no
controlamos: si una plantilla no expone etiquetas de fin, el presupuesto viaja y no actúa. Que
**nada lo reportase** sí era nuestro, y se paga en `D-64`, en esta misma ventana: el turno rinde
ahora `Usage.thinking_budget_honored`. `P14` sigue en pie: la superficie Responses de `llama.cpp` no emite
`output_tokens_details` ni señala el corte (`status` fijo en `"completed"`), luego el corte del
presupuesto sólo se observa por su efecto, como aquí. Siguen abiertos y no tocados: la calibración
de `counted` (2026-09-01), `FIND-GOOGLE-CASING`, `cache_write_1h` sin consumidor real, y `P1` de
`PLAN-OPTIMIZACION-TUI.md`.

---

## D-64 · El presupuesto de razonamiento deja de poder fallar en silencio

**2026-08-29.** Fase `agentic_code` · prueba E2E. Cierra el §*Abierto* de `D-63` en la misma ventana
que lo produjo.

- **Palabra del usuario**: *«si has identificado un riesgo que afecta a lo acordado en esta ventana,
  debería resolverse, no arrastrarse»*; y, tras el anuncio con evidencia plena, *«procede»*.

### Por qué no valía dejarlo abierto

`D-63` cerró el cableado del presupuesto y anotó como precondición ajena la guarda
`server-common.cpp:1360`. Es ajena, pero **el riesgo lo produce lo que acabábamos de cablear**: un
turno que pide techo de razonamiento, no lo obtiene y se presenta al consumidor como un turno
normal. Eso es la misma mudez que `D-56` prohíbe sobre el contador, sólo que sobre la palanca. Una
precondición del motor no exime de reportar que no se cumplió.

### Lo que dice la fuente (`llama.cpp` `HEAD c060ca974`), leída 1→EOF

- **La guarda, literal** (`tools/server/server-common.cpp:1352-1367`): el presupuesto se lee del
  cuerpo, y sólo pasa a `llama_params["reasoning_budget_tokens"]` si
  `!chat_params.thinking_end_tags.empty()`. La copia genérica del cuerpo (`:1383-1388`) es
  **posterior** y conserva el nombre crudo, que la capa de muestreo no lee. Cerrada la guarda, la
  clave viaja y no llega: silencio total.
- **De dónde salen las etiquetas** (`common/chat.cpp:3726-3733`): la ruta del autoparser las deriva
  de la plantilla y **sólo si la derivada no está vacía**; los handlers especializados las fijan a
  mano junto a `supports_thinking` (`ministral_3:1076-1078`, `qwen3_coder:1180-1186` —condicionado a
  que `<think>` aparezca en el fuente de la plantilla—, `gpt_oss:1377-1378`, `gemma4:1522-1524`,
  `kimi_k2:1798-1799`, `kimi_k3:2411-2412`, `lfm2:1932-1933`, `deepseek_v3_2:2197-2198`,
  `cohere2moe:2587-2588`, `minimax_m3:2703-2704`, `minicpm5:3195-3196`).
- **«El modelo razona» NO implica que la guarda abra** (`common/chat.cpp:3332`):
  `common_chat_params_init_muse_glimmer` declara `supports_thinking = true` y **jamás** fija las
  etiquetas. El contraejemplo existe en el propio motor, luego la inferencia estaba descartada.
- **No es observable a priori**: `/props` publica `chat_template_caps`, y `jinja::caps`
  (`common/jinja/caps.h`, vía `common_chat_templates_get_caps`, `chat.cpp:3900-3908`) no lleva
  ninguna capacidad de etiquetas de pensamiento.

Luego ni detección por `/props` ni inferencia por «hay razonamiento» pueden decidirlo. **Se rechazó**
además que `compat["thinkingBudgetParam"]` se autocertificase: eso sólo renombra una afirmación no
verificada, y `D-21` sitúa el conocimiento en el proveedor, no una promesa en el catálogo.

### El criterio, derivado del sampler

`common/reasoning-budget.cpp:117-131` descuenta un token por token dentro del bloque; al agotarse
pasa a `FORCING`, donde `common_reasoning_budget_apply` (`:166-186`) anula todos los logits salvo el
de la secuencia de fin. **Si el presupuesto actuó, el razonamiento no puede exceder
`presupuesto + |secuencia de fin|`.** Un exceso grande prueba que no actuó.

El umbral es **grueso a propósito**: `presupuesto × 2 + 64`. El contador bajo `counted` es
`rough_token_count` —estimación por caracteres, no el tokenizador del modelo—, así que un `>` desnudo
convertiría el error del estimador en acusación falsa. El `×2` absorbe ese error; el `+64`, la
secuencia forzada y el `reasoning_budget_message` del servidor, cuyo peso fijo domina en presupuestos
pequeños. **Esto detecta el fallo mudo; no mide el presupuesto**, y así está escrito en el docstring
de la suite.

### Lo inyectado

- `agentic_runtime/contracts/events.py` — `THINKING_BUDGET_OVERSHOOT_FACTOR`,
  `THINKING_BUDGET_OVERSHOOT_SLACK`, `derive_thinking_budget_honored`,
  `weakest_thinking_budget_honored`, y dos campos en `Usage`: `thinking_budget_tokens` y
  `thinking_budget_honored`.
- `agentic_runtime/events/event_types.py` — reexporte (el shim es la puerta real de los consumidores).
- `agentic_runtime/models/caller.py` — recuerda el presupuesto pedido y emite el veredicto en el
  `done`, junto a la derivación `D-56` que ya estaba.
- `agentic_code/src/agentic_code/streaming.py` — `StreamUsage` los porta y `_reduce` los agrega
  (`cablear-en-agentic-code-al-cerrar`).

`agentic_models` **no cambia**: el núcleo sólo contrasta *lo pedido* contra *lo vuelto*, sin
conocimiento de motor. El dogma queda intacto.

**`None` nunca se falsea a `True`.** Sin presupuesto pedido, y con `thinking_tokens_source ==
unavailable`, el veredicto es `None`: `0 <= techo` es cierto y no significa nada, y rotularlo `True`
fabricaría el dictamen justo donde no hay evidencia. En el agregado de sesión gana el peor turno,
igual que `thinking_tokens_source`.

### Acreditación (`D-12·b`)

9 casos en `agentic_code/tests/test_thinking_budget_verdict.py`, con criterio y citas de `llama.cpp`
en el docstring. Verde a la primera ⇒ **once mutaciones inyectadas y revertidas** desde copia propia
verificada por `sha256`, con purga de bytecode en cada revert (`D-62`). Once rojos, cero falsos
positivos:

| | mutación | |
|---|---|---|
| M1 | factor `2 → 1` | rojo |
| M2 | margen `64 → 0` | rojo |
| M3 | factor `2 → 100` (umbral inerte) | rojo |
| M4 | `unavailable` deja de vetar el veredicto | rojo |
| M5 | presupuesto `<= 0` deja de vetar | rojo |
| M6 | agregado: `False` deja de ganar | rojo |
| M7 | agregado: `True` deja de sobrevivir a `None` | rojo |
| M8 | `caller` no recuerda el presupuesto pedido | rojo |
| M9 | `caller` no emite el veredicto | rojo |
| M10 | `streaming` no agrega el veredicto | rojo |
| M11 | la cifra pedida no persiste entre turnos | rojo |

Hashes del estado sano: `contracts/events.py`
`dd5e51509feb5dbc2a74d433f1ef5ad62b1b80efe9719a3416f101f0ffbad3d4`, `events/event_types.py`
`4dd00e546a1ce3290bf3b629285cd8344586f6167433e6dfcef020ecb42357ea`, `models/caller.py`
`dcdcbff4236f5a97a6e1e23e50c60165dae71a604d7937cd763313c35e3af6cd`,
`agentic_code/src/agentic_code/streaming.py`
`9996e7f8ba323eee4e665693bd59325cd851ca7168ec82ec24a0c8adb850518e`,
`agentic_code/tests/test_thinking_budget_verdict.py`
`cd6b891a8e5142099018627f2a69fa17cd4e4736d3c026e23aa8c1069e5793c2`.

### Medido en vivo, con control negativo

Contra `llama-server` + `unsloth/Qwen3.8-27B-GGUF:UD-IQ4_XS` (`validacion-por-consumidor-real`),
mismo prompt y `xhigh`:

| caso | `thinking_tokens` | `budget` | `honored` |
|---|---|---|---|
| presupuesto 64 | 63 | 64 | `True` |
| sin presupuesto | 1424 | `None` | `None` |
| **control negativo** — presupuesto bajo un nombre que el motor no lee | 1884 | 64 | **`False`** |

El control negativo reproduce la forma observable **exacta** de la guarda cerrada —la clave viaja en
el cuerpo y nadie la lee— sin necesidad de una plantilla sin etiquetas. El detector dispara. Y la
primera fila acredita además, en positivo, que **la plantilla del perfil local sí abre la guarda**:
lo que `D-63` midió por su efecto queda ahora rotulado turno a turno.

### Suites, `ruff`, `mypy` y procesos

`agentic_code` **277 → 286 passed**; `agentic_models` **96 passed** (sin cambio: la capa de proveedor
no se tocó). `ruff` sobre los ficheros tocados: limpio salvo un `E501` en `caller.py:303`,
**comprobado idéntico en `HEAD`** sobre una línea que este pago no toca ⇒ deuda neta cero por diff.
`mypy` limpio en los cuatro. Sin procesos supervivientes. Sintéticas de `agentic_runtime` ni corridas
ni tocadas.

### Lo que NO deroga

`D-08` intacto: el criterio sale del sampler leído, no de un umbral elegido. `D-21` intacto: no se
añade promesa al catálogo. `D-56` **aplicado por extensión**: la regla «derivar o marcar
indisponible, nunca un mudo» se aplica ahora también a la palanca, no sólo al contador. `D-49`
intacto: esto reporta si el motor cumplió lo pedido, no juzga conducta del modelo. `D-63` §*Abierto*
queda cerrado en su primer punto; los demás siguen abiertos y no tocados.

---

## D-65 · `FIND-RT-MAXTURNS-1`: un tope inventado, alcanzado en silencio y rotulado como éxito

**2026-08-30.** Fase `agentic_code` · estabilización. Paga el primero de los cinco cortes que
`VALIDACION-AGENTIC-CODE.md § 2 septies` dejó en cola.

- **Palabra del usuario**: el enunciado de retoma, que fija el orden (a)→(d) y cierra el
  diagnóstico —*«El diagnóstico está cerrado y la inyección aceptada; no rediagnostiques»*—; y,
  sobre el anuncio con evidencia plena, `procede`.

### Los cuatro defectos, y por qué son uno solo visto desde cuatro capas

El tope de vueltas del bucle existía, pero **ninguna de sus cuatro costuras llegaba al consumidor**:

1. **(a) El terminal se descartaba en la línea.** `execution/local/runtime.py:384` hacía
   `await loop.run(prompt, ctx)` sin recoger el `LoopOutcome`. El bucle ya sabía por qué había
   terminado y el registro no se enteraba nunca: `TaskRecord` no tenía dónde guardarlo.
2. **(b) El aviso vivía en un `logger.warning`.** `loop/agent_loop.py:601-604` escribía
   *«alcanzado límite de %d turnos»* en el log del proceso. En A ese aviso **se rinde al stream
   público**: `query.ts:1704-1712` hace `yield {type:'max_turns_reached', maxTurns, turnCount}` y
   retorna `{reason:'max_turns'}`. Un log no es una costura: no llega al `.jsonl`, ni al transcript,
   ni a la pantalla.
3. **(c) El techo era inventado.** `_MAX_TURNS = 50` y `self._max_turns = max_turns if max_turns is
   not None else _MAX_TURNS` (`:74`/`:153`). En A el tope es **opcional** —`maxTurns?: number`
   (`query.ts:191`)— y todas sus guardas son `if (maxTurns && …)`: **sin techo pedido no hay
   techo**. B imponía 50 vueltas a todo consumidor que no pidiera nada, y como (b) era mudo, el
   corte era indistinguible de un turno que terminó por su cuenta.
4. **(d) `MAX_TURNS` se rotulaba `COMPLETED`** sin matiz alguno en el registro y en el `.jsonl`.

### La decisión de (d): el ciclo de vida no cambia; el terminal viaja como DATO

`TaskStatus.COMPLETED` **se conserva**. La tarea no falló: se cortó en un terminal distinto de
«acabó de hablar». Añadir un miembro de estado habría cambiado `is_terminal()` bajo consumidores
que no lo pidieron, y A **no tiene** tal estado de ciclo de vida — lo que tiene son dos ramas de la
misma unión de resultado, `SDKResultSuccessSchema` (`subtype:'success'`) y `SDKResultErrorSchema`
(`subtype:'error_max_turns'`), `entrypoints/sdk/coreSchemas.ts:1407-1451`. **Quien las distingue es
el consumidor.**

Luego el terminal viaja como dato en dos vehículos y el rótulo lo pone el integrador:

- `TaskRecord.end_reason` / `end_detail` (nuevos), poblados desde el `LoopOutcome` que (a) recoge;
- `MaxTurnsEvent(max_turns, turn_count)` en el bus, que es lo que (b) emite;
- y `agentic_code` rotula su línea `result` como `error_max_turns` con `status: "completed"`, que
  es exactamente el reparto de A.

El `turn_count` que viaja es el `nextTurnCount` del canónico: **la vuelta que ya no se hará**.

### Lo inyectado

- `agentic_runtime/contracts/events.py` — `MaxTurnsEvent(max_turns, turn_count)` y su `__all__`.
- `agentic_runtime/events/event_types.py` — reexporte por el shim, que es la puerta real de los
  consumidores.
- `agentic_runtime/loop/agent_loop.py` — muere `_MAX_TURNS`; `self._max_turns = max_turns` a secas;
  el `for _turn in range(...)` pasa a `while True` con la guarda `if self._max_turns is not None
  and ctx.turn_count >= self._max_turns`, que **emite al bus antes** de fijar el terminal y romper.
- `agentic_runtime/execution/tasks/registry.py` — `TaskRecord.end_reason` / `end_detail`, y los dos
  `complete(...)` (protocolo e implementación) que los reciben.
- `agentic_runtime/execution/local/runtime.py` — `:384` recoge el `LoopOutcome` y lo transporta al
  `complete(...)`.
- `agentic_code/src/agentic_code/streaming.py` — `StreamSnapshot.end_reason` / `max_turns` /
  `turn_count`, y su rama en `_reduce`.
- `agentic_code/src/agentic_code/capture.py` — el adjunto canónico
  `{type:'max_turns_reached', maxTurns, turnCount}` (`utils/attachments.ts:656-660`) en
  `_canonical_message`, y el `subtype` de `finish()` en tres ramas: fallo → `error_<status>`,
  terminal distinto → `error_<end_reason>`, y sólo si no hay ninguno → `success`.
- `agentic_code/src/agentic_code/transcript.py` — `MaxTurnsBlock` y `_apply_max_turns`, espejo de
  `_apply_compaction`: cierra lo que estuviera en vuelo y **jamás fabrica un turno**.
- `agentic_code/src/agentic_code/rendering.py` y `tui.py` — la fila se pinta, por `stderr` en el
  renderer de texto y como widget propio en la TUI (`cablear-en-agentic-code-al-cerrar`).

El techo se pide con `--max-turns`, que ya existía en `Settings` con default `None` y validación
`>= 1`: no hace falta superficie nueva, hacía falta que `None` significara lo que dice.

### Divergencias declaradas (`D-21`)

1. **Aquí el aviso SE PINTA; en A no.** `max_turns_reached` está en `NULL_RENDERING_TYPES`
   (`components/messages/nullRenderingAttachments.ts:38`) y `AttachmentMessage` lo devuelve `null`.
   Se diverge a propósito: un turno que se corta sin decir por qué es indistinguible de uno que
   terminó, que es justo el defecto que esta entrada paga. Consecuencia: **no hay literal canónico**
   para el usuario, luego el núcleo emite datos y `agentic_code` pone las palabras — los literales
   `max_turns_reached`/`maxTurns`/`turnCount` viven sólo en `capture._canonical_message`, que sí es
   espejo del `.jsonl` de A.
2. **No se porta el segundo `yield` de la rama de aborto** (`query.ts:1506-1514`). Nuestra rama de
   aborto (`LoopEndReason.ABORTED_TOOLS`) es anterior a la guarda del techo y no pasa por ella.
   Queda medido y declarado, no descartado en silencio.

### Acreditación (`D-12·b`)

`agentic_code/tests/test_max_turns_wire.py`, **7 casos**, con criterio y citas del canónico en el
docstring de módulo (única excepción del § 4). Miden el bus, el registro, la captura, el transcript,
el renderer y el viaje de ida y vuelta del `.jsonl`. **Cuatro mutaciones inyectadas y revertidas**,
con purga de `__pycache__` en cada revert (`D-62`) ⇒ **cuatro rojas, cero falsos positivos**:

| | mutación | rojas |
|---|---|---|
| INY-a | `runtime.py:384` vuelve a descartar el `LoopOutcome` | 1 |
| INY-b | el aviso vuelve al `logger.warning` en vez del bus | 3 (bus, captura, render) |
| INY-c | `self._max_turns = max_turns if max_turns is not None else 50` | 1 (`assert 50 == 58`) |
| INY-d | `finish()` vuelve a rotular `success` todo `COMPLETED` | 1 |

INY-b enrojeciendo **tres** casos y no uno es lo que acredita que las capas están cableadas de
verdad y no medidas tres veces en el mismo sitio; INY-c es la única que enrojece el caso «sin techo
pedido», o sea que ese caso mide el default y no otra cosa.

Hashes del estado sano: `contracts/events.py`
`06835903f5aa595f1a82f0626b9463fcb357472dd61087d3c826bce8d150f610`, `events/event_types.py`
`1bc895bf7827c1fa2d346469e90c8b1f43e3d4ddd12ff9114a0af4f09e095683`, `loop/agent_loop.py`
`42a7d08e9985952b97c3e7f2bb752040e063aa8933e78b2b8aacd7ee67acb1f0`,
`execution/tasks/registry.py` `37faf9873536b6a47b5e4a7238dae0abb4cb221ddbfcbb0eb291574a06073532`,
`execution/local/runtime.py` `655331aa4d7740fe668e73357f02ddf6c1d7b92e32b9dc7132ccd32d32bc33ad`,
`agentic_code/src/agentic_code/streaming.py`
`ade4da0c265cac66dd45084c5955d9f107711b67a0ac5bd683324b01030dd811`, `capture.py`
`93a103acc71d98aef4769ae32e505373d89acd0121d274359e0a51425ef9e1a9`, `transcript.py`
`37cc87b2a9c80b254442de441bc009855c65490e97dc5b0c52d24d36746b606e`, `rendering.py`
`360b062f25779f2e9f84d3b01acbc1cf874028541a146e49ab2274452c4fd0e4`, `tui.py`
`98144f18ab7c41b02c9dcc9edef5b5ed4ac8e98cca8e951eacf87a04289a4180`,
`tests/test_max_turns_wire.py` `220eac30f16dba09016db45c4117435161ad298851206a73b05a33a99c98458c`.

### Suites, `ruff`, `mypy` y procesos

`agentic_code` **286 → 293 passed**, sin regresión por el cambio de semántica de `None` ni por los
campos nuevos de `TaskRecord` y `StreamSnapshot`. `ruff` sobre los once ficheros tocados: **All
checks passed**. `mypy` sobre los cinco de `agentic_runtime`: **un** error, el de
`agent_loop.py:235` (`collect_compaction_context`), **comprobado idéntico en `HEAD`** —copia de
`HEAD` en `mktemp -d`, donde es `:236`— sobre una línea que este pago no toca ⇒ deuda neta cero por
diff. Sin procesos supervivientes de las rondas. Las sintéticas de `agentic_runtime` no se
corrieron ni se tocaron (acuerdo de fase).

### Barrido de comentarios

`D-23` / `D-58`: `registry.py` entra en el barrido completo —quedan fuera sus docstrings de módulo,
clase y método— y el resto de ficheros tocados no gana comentario alguno. Las citas del canónico
viven en el docstring de la suite.

### Lo que NO deroga

`D-08` intacto: la opcionalidad del tope, el `nextTurnCount`, el sitio del `yield` y el reparto
`success`/`error_max_turns` salen del fuente de A, no de deducir cómo «debería» ser. `D-21` intacto
y aplicado dos veces: la divergencia de pintado y el `yield` no portado se **declaran**. `D-49`
intacto: esto es costura de terminal, no contabilidad. `D-56` intacto en su espíritu: el terminal
no se recorta al mínimo que el estado sabía decir; se transporta entero por el vehículo que hizo
falta crear (`D-22`). `D-62`, `D-63` y `D-64` intactos.

### Abierto

Quedan los otros cuatro cortes de `VALIDACION-AGENTIC-CODE.md § 2 septies`, no tocados. Siguen
abiertos y sin cambio: la calibración de `counted` (2026-09-01), `FIND-GOOGLE-CASING`,
`cache_write_1h` sin consumidor real, y `P1` de `PLAN-OPTIMIZACION-TUI.md`.

---

## D-66 · `FIND-CODE-ESC-1`: el cable del aborto tendido y sin corriente

**2026-08-31.** Fase `agentic_code` · estabilización. Paga el segundo de los cinco cortes en cola de
`VALIDACION-AGENTIC-CODE.md § 2 septies`.

- **Palabra del usuario**: el enunciado de retoma, que enumera los cinco puntos y cierra el
  diagnóstico; y, sobre el anuncio con evidencia plena, `procede`.

### El defecto

`AbortSignal` existía, `ctx.stop` viajaba hasta el proveedor y el bucle lo consultaba en sus tres
guardas. **Nadie lo encendía nunca.** `LocalAgentRuntime.cancel` iba directo a
`task_registry.kill(task_id)`: mataba la corrutina de fuera, sin dar al bucle ni una vuelta para
enterarse. Consecuencia en cadena, medida en el `.jsonl` real del integrador:

- el turno abortado se rotulaba `error_killed` / `status: "killed"` / `end_reason: null`;
- el **texto parcial se perdía** (`result: ""`), aunque el modelo hubiera hablado 40 tokens;
- los `tool_use` ya anunciados quedaban **huérfanos**, sin su `tool_result`, envenenando el
  historial de la sesión siguiente;
- no había constancia alguna de que el corte fuera del usuario ni de por qué.

En A el aborto es cooperativo y **sale por la rama de éxito**: `query.ts:1005-1052` cierra los
`tool_use` pendientes con `yieldMissingToolResultBlocks(…, 'Interrupted by user')`
(`query.ts:123-149`), rinde el `UserInterruptionMessage` y retorna `{reason:'aborted_streaming'}`.

### La decisión: el aborto es una salida ordenada; el kill es el plan B

`cancel(task_id, *, reason=AbortReason.TURN_CANCELLED)` levanta la señal y **espera con gracia**
(`asyncio.wait_for(asyncio.shield(task), cancel_grace)`, 5 s por defecto). El bucle ve la señal en
su siguiente guarda, cierra en orden y termina `COMPLETED` con `end_reason`
`aborted_streaming` / `aborted_tools`. Sólo si la gracia expira —modelo sordo— se cae al kill duro,
y entonces el terminal es `aborted_hard` con `TaskStatus.KILLED`. `D-65` intacto y reusado: el
terminal viaja como dato y el rótulo lo pone el integrador.

### Lo inyectado

- `contracts/abort.py` — los tres literales canónicos: `INTERRUPT_MESSAGE`,
  `INTERRUPT_MESSAGE_FOR_TOOL_USE`, `TOOL_RESULT_INTERRUPTED`.
- `contracts/events.py` + `events/event_types.py` — `AbortEvent(reason, turn, tool_use)`, homólogo
  del `UserInterruptionMessage` de A, y su reexporte por el shim.
- `loop/outcome.py` — código propio `ABORTED_HARD`, incluido en la propiedad `aborted`.
- `execution/tasks/registry.py` — `TaskRecord.stop` y `set_stop(...)`, para que el registro pueda
  levantar la señal; `kill(...)` acepta `result` / `end_reason` / `end_detail` y, si nadie abortó,
  levanta `AbortReason.AGENT_KILLED` antes de matar.
- `execution/local/runtime.py` — `cancel(...)` con gracia; `set_stop` al armar el contexto; y la
  rama `CancelledError` de `_run_loop`, que ahora **vuelca `ctx.messages`/`turn_count` a la sesión
  y persiste igual que la ruta feliz**, con un helper `_shielded` para que el cierre sobreviva a la
  cancelación que lo provocó.
- `loop/agent_loop.py` — `_announce_abort(...)` (mensaje de interrupción + `AbortEvent`) en las tres
  salidas; y, en el corte de stream, el volcado del assistant parcial (`_assistant_message`) y el
  **cierre de los `tool_use` huérfanos** con `TOOL_RESULT_INTERRUPTED` e `is_error=True`.
- `agentic_code/streaming.py`, `capture.py`, `driver.py` — `StreamSnapshot.abort_reason` /
  `abort_tool_use`, el mapeo canónico `{type:'system', subtype:'abort', …}`, y un `driver` que
  **deja de fabricar** `KILLED`/`""` en su rama `CancelledError`: lee el terminal de quien abortó.

### Divergencia declarada (`D-21`)

**El `AbortEvent` se emite siempre.** A lo suprime cuando `signal.reason === 'interrupt'`, porque su
TUI ya pintó la interrupción por su cuenta. Aquí el evento es el único vehículo del motivo hasta el
`.jsonl`, y callarlo reproduciría el defecto que esta entrada paga. Se declara, no se descarta en
silencio.

### Lo que deroga

La divergencia **2** de `D-65` (*«no se porta el segundo `yield` de la rama de aborto»*,
`query.ts:1506-1514`) **queda pagada**: la frontera de vuelta emite ahora el `MaxTurnsEvent` cuando
el aborto coincide con el techo alcanzado.

### Acreditación (`D-12·b`)

Inyección/revert por copia propia sellada de los 10 fuentes (`PRE.sha256` / `POST.sha256`, ambos
`sha256sum -c` OK), con purga de `__pycache__` en cada paso (`D-62`). Con `pre` el defecto
**reaparece entero**: `subtype: "error_killed"`, `end_reason: null`, `result: ""`, sin `AbortEvent`,
sin mensaje de interrupción y sin `tool_result` para el huérfano. Con `post`, verde:
`subtype: "error_aborted"`, `status: "completed"`, `end_reason: "aborted"`,
`abort_reason: "turn_cancelled"`, el `tool_result` `('call-1', 'Interrupted by user', is_error)` y
los 40 tokens parciales conservados en `result`. Las cuatro ramas del harness dan
`aborted_streaming`, `aborted_tools`, huérfano cerrado y `aborted_hard` con gracia de 0,3 s contra
un modelo sordo.

`agentic_code` **293 passed**. `test_repl_cancels_active_turn_and_returns_to_prompt` se **reescribió
con el criterio nuevo** —no se ablandó—: su stub declara `COMPLETED` y anuncia el aborto por el bus,
y el caso comprueba el par `completed` + `error_aborted` en el `.jsonl`, es decir que el driver ya
no inventa el terminal. `mypy` sobre los siete de `agentic_runtime`: **un** error, el preexistente
de `agent_loop.py:266` (`collect_compaction_context`), sobre línea que este pago no toca ⇒ deuda
neta cero por diff. `ruff` **no se pudo correr: no está instalado** en ninguno de los dos entornos;
la verificación estática fue `compileall` + `mypy`. Sin procesos supervivientes.

Hashes del estado sano: `contracts/abort.py`
`93a3d9ede096d57a7e4637560c680122df7898b2ffadf84a4c7c408969dab5db`, `contracts/events.py`
`95e1a948341a61869903c744cd17d581b52bd21a9056c1cec68e9ab35f3ced7b`, `events/event_types.py`
`d2373845e0ff58ae27343195f2fef526208b5f7cdcfdb1ed5ef74f2690b1d518`, `loop/outcome.py`
`1c4dcce016567094f7d9acab0f0dcd747f38d65f6ad747f108929d29a04d276f`, `loop/agent_loop.py`
`5f79656483418ccf05bb5fa69add44beb56711b4c2d286bb97f5c18fd831c0d0`,
`execution/tasks/registry.py` `14c69eea906ecbff664e66114c1a56a24d64be8767ce08b4e9ae9d457996b8f2`,
`execution/local/runtime.py` `c70fc3e3755bf95b2338a2a0f2c73cf7616d2a03a117f6146581a47ed849da49`,
`agentic_code/streaming.py` `15b9e9d62680a3c7e920db915c23dda62f2d16a947e273d69a3f6abce0ddad6b`,
`capture.py` `4fde71a7ae2bdb7beb8343752ef4fe5ce1ea9d0d21d287a0ccc58ef3b7082621`, `driver.py`
`429cbee20b81373e10fff1db04cf301527f89747369c510f475aa341905b176e`, `tests/test_repl.py`
`d11c09909ef6f970883be32a8b92f7d85244111aeb742d1bd5e0e072fb2f8767`.

### Hallazgos de paso, no tocados

1. **`events/event_types.py` no reexporta `CompactionEvent`** — pertenece a
   `FIND-RT-COMPACT-EVT-1`, siguiente en la cola.
2. **`LoopEndReason.MODEL_ERROR` sale rotulado `subtype: "success"` con `end_reason: null`** en el
   `.jsonl`, porque `capture.finish` lee el `end_reason` del *snapshot* (que viene de eventos) y no
   el del `TaskRecord`. Es el mismo patrón que `D-65` pagó para el techo, en otro terminal. Queda
   anotado como hallazgo abierto.
3. **El ESC de la TUI tiene un umbral de 350 ms** (`tui.py`): conducta de producto propia, no
   homologada contra A. No se toca en este corte.

### Lo que NO deroga

`D-08`, `D-12·b`, `D-15`, `D-21`, `D-22`, `D-23`/`D-58`, `D-49`, `D-56`, `D-62`, `D-63`, `D-64` y
`D-65` intactos. Siguen abiertos y sin cambio los tres cortes restantes del `§ 2 septies`.

## `D-67` — `FIND-CODE-ESC-2`: la señal de aborto corta la petición en vuelo

**Fecha**: 2026-08-31. **Corte**: `FIND-CODE-ESC-2` (tercero de los cinco cortes E2E).

### El defecto, en dos piezas

1. **`contracts/abort.py` sólo sabía consultarse.** `aborted` era propiedad y no había canal por el
   que despertar a un `await` bloqueado. El homólogo JS es sondeable *y* esperable (`signal.aborted`
   + `addEventListener("abort")`); portamos media pieza. Nada podía sacar al consumidor del
   `await self._queue.get()` de `EventStream.__aiter__`.
2. **Ningún proveedor entregaba la señal a la capa HTTP** y el productor salía **desprendido** por
   `asyncio.ensure_future`: cerrar el consumidor dejaba la petición viva. El bucle sólo se enteraba
   del aborto cuando llegase un evento, y en un prefill de ~20 s no llega ninguno ⇒ la gracia de 5 s
   de `cancel(...)` expiraba esperando a nadie y caía al `kill` duro.

### La forma del pago

`AbortSignal` gana `async def wait()` en el Protocol; `AbortController` lo implementa con un
`asyncio.Event` **perezoso** (creado al primer `wait`, para no exigir bucle en construcción) que
`abort()` levanta. En `agentic_models/utils/abort_signals.py`, la pieza genérica que evita nueve
copias: `watch_abort(signal)` —usa `wait()` si el objeto lo tiene y si no cae a sondeo de 50 ms, o
sea la señal se acepta **por pato** y la capa de modelos no importa del núcleo— y
`launch_with_abort(coro, options)`, que sustituye al `ensure_future` crudo, vigila la señal en
paralelo y **cancela la Task**. Cancelar la Task interrumpe el `await` de httpx/SDK y cierra la
conexión: es el equivalente Python del `signal` que en A rinde `APIUserAbortError`
(`claude.ts:2434-2451`, `:2794-2799`).

`asyncio.CancelledError` **no es** `Exception`: el `except Exception` terminal de cada proveedor no
lo vería y el stream quedaría sin cerrar. Por eso los nueve reciben una rama
`except asyncio.CancelledError` **delante** de la suya, con su propio barrido de parciales,
`stop_reason = "aborted"`, `push({"type":"error"})`, `end()` y `raise` —la cancelación se
repropaga, no se traga—.

**La gracia sigue en 5 s.** `caller.py`, `agent_loop.py` y `stream.py` no se tocan. `stream.py`
tampoco podía ser la costura: el asa de la Task no existe ahí, y un envoltorio en ese punto habría
desbloqueado al consumidor dejando la petición en vuelo. Corrección de diseño propia, anunciada
antes de mutar.

### Barrido de los nueve: siete estaban pagados, tres no

Inyectar el helper no basta si el proveedor no tiene dónde suspenderse.

- **`google.py`, MUERTO, no «existe-roto» — corrige nota mía.** `config["abortSignal"] = signal` con
  forma JS: `GenerateContentConfig` es pydantic con `extra=forbid` y devuelve
  `ValidationError: Extra inputs are not permitted [extra_forbidden]`. Como el runtime **siempre**
  pasa `ctx.stop`, toda llamada a Google reventaba en `_build_params` y el `except Exception` la
  disfrazaba de error de modelo. Pagado: la línea sale, queda la pre-guarda `if signal.aborted`.
  Medido de paso: el camelCase **sí** lo acepta el SDK por alias ⇒ `FIND-GOOGLE-CASING` no se
  dispara por esta vía.
- **`google_vertex.py`, cliente síncrono en corrutina.** `client.models.generate_content_stream`
  devuelve `Iterator`; `client.aio.models.…` es corrutina y devuelve `AsyncIterator`. El fichero
  hacía `async for` sobre el síncrono: no ha podido funcionar nunca, y aun funcionando no tendría un
  solo punto de suspensión. Pagado: `await client.aio.models.generate_content_stream` más la
  pre-guarda que faltaba.
- **`amazon_bedrock.py`: `DEUDA-BEDROCK-ABORT-1`, aplazada por palabra del usuario.** Ver abajo.
- Pagados ya y comprobados uno a uno: `anthropic`, `openai_responses`, `azure_openai_responses`,
  `openai_completions`, `mistral`, `openai_codex_responses`. `faux.py` no está en
  `providers/__init__.py`. `providers/images` no es streaming y su `except Exception` no atrapa
  `CancelledError` ⇒ la cancelación ya propaga limpia.

### `DEUDA-BEDROCK-ABORT-1` — declarada y medida, NO pagada

boto3 es síncrono de arriba abajo: `client.converse_stream(**command_input)` bloquea y
`for item in response.get("stream", [])` itera bloqueando. **Cero `await` en el bucle de
streaming** ⇒ `Task.cancel()` no tiene dónde actuar: el aborto es sordo, y mientras el modelo emite
el turno bloquea el event loop entero (bus y TUI incluidos).

Forma del pago, diseñada y **no** aplicada: `await asyncio.to_thread(client.converse_stream, ...)`
y tirar del `EventStream` chunk a chunk con `await asyncio.to_thread(next, it, _FIN)` —un punto de
suspensión por chunk— más el cierre del stream en la rama `CancelledError`. Unas diez líneas.
Aplazada porque Bedrock no está en uso previsible y el corte de cabecera pesa más. **No se rotula
como pagada** (`declarar-no-es-pagar`). Aunque se aplicase hoy quedaría sin acreditación en vivo:
no hay credenciales AWS en esta máquina (`D-56`). Se paga cuando Bedrock entre en uso, o antes si
aparece consumidor.

### Acreditación (`D-15`)

Contra modelo real, `llama-server` en `:8080`, harness colgado del primer `ToolCallEvent`: ESC a
2,0 s corta en la **vuelta 2** y a 6,0 s en la **vuelta 3**, los dos con `subtype: "error_aborted"`,
`status: "completed"`, `end_reason: "aborted"`, `abort_reason: "turn_cancelled"` y el
`{type:'system', subtype:'abort'}` presente. El tiro a 12,0 s no abortó porque el turno acabó antes:
se declara **inconcluyente**, no se cuenta. `error_killed` / `status: killed` / `end_reason: null`
no reaparecen en ninguna corrida. Re-corrida tras el pago de Google/Vertex: sin regresión. Los
`config` de Google y Vertex validan contra el SDK real y las dos pre-guardas disparan
`Request aborted`. Sin procesos supervivientes. Sintéticas de `agentic_runtime` ni corridas ni
tocadas.

**Queda declarado y no pagado aquí**: el `result: ""` del turno abortado en fase de tools. No es de
este corte —es `capture.finish` derivando el terminal sin rama para ese parcial— y es exactamente
`FIND-CODE-ABORT-TERM-1`, que pasa al frente.

### Corrección: `ruff` sí está instalado

`D-66` afirma que **`ruff` no se pudo correr, no está instalado en ninguno de los dos entornos**.
Está rancio: `ruff 0.16.1` vive en el venv de `agentic_code`. Corrido ahora y medido contra los
blobs de `HEAD` fichero a fichero: los 43 hallazgos de `providers/` son **todos preexistentes**,
cero añadidos por este diff. Los **dos** que sí eran míos —`typing.Coroutine` deprecado en
`abort_signals.py` (`UP035`) y `__slots__` sin ordenar en `contracts/abort.py` (`RUF023`)— quedan
pagados, no rotulados.

### Riesgo aceptado

Añadir `wait` al Protocol `@runtime_checkable` cambia el veredicto de un
`isinstance(..., AbortSignal)` para objetos sin ese método. Verificado por el camino real (E2E), no
por censo: `grep` está prohibido en esta fase.

### Hashes del estado sano

`agentic_runtime/contracts/abort.py`
`2677c15ce099965d9505aeb82ae812ee1d427dcec803b3db0a0874905dd0c817`;
`agentic_models/utils/abort_signals.py`
`980fdc250e8b52a7cde50ff47f134a80b7e57daaca974c16faf3450f2b07057b`;
`providers/anthropic.py` `562533cd7285df83bdb3a7319ccfe1cc051fbc794815a0886afcbabd0473fee5`;
`providers/google.py` `d9aaec30f4fb5eef9b39e0c49afe92c1dc217c2e76e751415c24145b2fc185b7`;
`providers/google_vertex.py` `83e12155c1054f4f11a17c44545f0652e459be772b66b78316682f38e2052df9`;
`providers/mistral.py` `f4c6774026b5aa3cd62d44a95d81edac1239ee1a813b3c5b470872341d8a3efc`;
`providers/openai_responses.py` `70f8c50229da0fdea96450a12ac6d59c78725040b2b7fc9231e1c0b8f24acb9f`;
`providers/azure_openai_responses.py`
`15e46e1dfb4c9e4b12e2affed735a0c71adae0ffbf914a542beb4b2f3f396812`;
`providers/openai_completions.py` `7a55e86b55c1b07eacc336128585c0157bcd519b128b749b33fdde415d869de8`;
`providers/openai_codex_responses.py`
`fd818aca7eeb2de8253f985bd6e3305047ba85c158196806671df9243d328d33`;
`providers/amazon_bedrock.py` `9b39afff54f1811c70b0d8f5f03c40bc46fd86aee84ad66fc49dc9b0391b1d8d`.

### Lo que NO deroga

`D-08`, `D-12·b`, `D-15`, `D-21`, `D-22`, `D-49`, `D-56`, `D-62`, `D-63`, `D-64`, `D-65` y `D-66`
intactos, salvo la corrección sobre `ruff` de arriba. Siguen abiertos `FIND-CODE-ABORT-TERM-1`,
`FIND-RT-COMPACT-EVT-1`, `FIND-RT-TOOLINPUT-1`, `FIND-CODE-TODO-1` y `DEUDA-BEDROCK-ABORT-1`.

---

## D-68 · `FIND-CODE-ABORT-TERM-1`: el tope GANA a la cola, y sus `errors[]` no son los del diagnóstico

**2026-08-31/09-01.** Fase `agentic_code` · estabilización. Cierra `FIND-CODE-ABORT-TERM-1`, que
`D-67` §*Queda declarado y no pagado aquí* puso al frente de la cola. Corrige la mitad de forma de
lo que el censo `(d)` había dado por pagado.

- **Palabra del usuario**: el enunciado de retoma, que fija el paso en cinco tramos —*«anunciar la
  inyección, invertir el orden en `capture.py:_classify`, retirar o separar la guarda
  `if self._end_reason != "aborted"` de `streaming.py:274`, reescribir `tests/test_capture.py:145`
  con el criterio canónico, reacreditar `M2` por `D-12·b`, y sólo entonces escribir `D-68`»*— y que
  cierra el diagnóstico.

### El defecto: mi criterio, no el mutador

El censo `(d)` publicó `M2` —orden de ramas en `_classify`— como **falso negativo**: la única de seis
mutaciones que salió verde. No lo era. Era el criterio el que estaba invertido, y el mutador el que
tenía razón. Contrastado contra A, leído 1→EOF:

1. **`error_max_turns` no lo decide la cola.** `QueryEngine.ts:842-874` lo rinde al ver el adjunto
   `max_turns_reached` **dentro del bucle de mensajes**, con `return` inmediato (`:873`), o sea
   **antes** del `isResultSuccessful` de `:1082`, que es de donde sale `error_during_execution`.
2. **El adjunto se emite también en la rama de aborto en tools.** `query.ts:1508-1514`: tras la
   interrupción (`:1501-1505`) y antes del `return {reason:'aborted_tools'}` de `:1515`. Orden que
   `agent_loop.py:427-438` ya reproducía. Luego en A un turno abortado que cruza el tope sale
   `error_max_turns`, y en B salía `error_during_execution`.

### Hallazgo de paso, pagado en la misma inyección

A **no pone `[ede_diagnostic]` en el tope**: sus `errors[]` son
`Reached maximum number of turns (${maxTurns})` (`QueryEngine.ts:869-871`), y el prefijo
`[ede_diagnostic]` es **exclusivo** de `error_during_execution` (`:1106-1115`). `_classify` estaba
pasando `_diagnostics(snapshot)` también al tope: invención, retirada.

### La guarda se SEPARA, no se retira

El enunciado admitía las dos formas. Se separa, porque
`if self._end_reason != "aborted"` (`streaming.py:274`) protegía **dos cosas a la vez** y sólo una es
legítima: `_end_reason` es lo que hace que `finalize()` rinda `CANCELLED` (`streaming.py:166-168`), y
el aborto debe seguir ganando **ese** campo — el registro conserva `end_reason: "aborted"` y
`abort_reason: "turn_cancelled"`, que es lo que `D-66` pagó. Lo que no puede es decidir la
clasificación. Retirarla del todo habría hecho que un tope tras aborto rindiera
`end_reason: "max_turns"`, borrando el motivo del corte del usuario.

Así que la clasificación cuelga de un vehículo nuevo e **incondicional**,
`StreamSnapshot.max_turns_reached`, homólogo del adjunto de A: el adjunto llegó, y eso es un hecho
del stream, no una consecuencia del terminal. `D-65` queda **íntegro**: la cola sigue decidiendo
entre `success` y `error_during_execution`; lo que no puede es adelantar al adjunto.

### Lo inyectado

- `agentic_code/src/agentic_code/streaming.py` — `StreamSnapshot.max_turns_reached` (al final de los
  campos con default, sin alterar construcción posicional), `self._max_turns_reached` en `__init__`,
  su paso por la propiedad `snapshot`, y la rama `MaxTurnsEvent` de `_reduce` armando el flag
  **antes** de la guarda, que se conserva sólo sobre `_end_reason`.
- `agentic_code/src/agentic_code/capture.py` — `_classify` con el tope **primero**, antes incluso del
  `status`, porque en A el `return` del adjunto precede a toda otra salida; y los `errors[]`
  literales de A en vez de `_diagnostics(snapshot)`.
- `agentic_code/tests/test_capture.py` — `test_max_turns_only_wins_when_the_tail_is_successful` pasa
  a `test_the_max_turns_attachment_outranks_the_transcript_tail`, **reescrito con el criterio
  canónico y sus citas**, no ablandado (`no-debilitar-la-prueba`): afirma ahora lo contrario de lo
  que afirmaba, con el caso `tope_abortado` comprobando a la vez `subtype: error_max_turns`,
  `errors[]` de A, `end_reason: "aborted"` y `abort_reason: "turn_cancelled"`.

### Acreditación (`D-12·b`) — `M2` reacreditada

Copia propia de los dos fuentes en `mktemp -d`, verificada por `sha256` idéntico al repo antes de
mutar; revert desde esa copia con **purga de `.pyc`** en cada pasada (`D-62`) y hash comprobado tras
cada revert. Cuatro mutaciones, cuatro rojas, cero falsos positivos:

| | mutación | rojo |
|---|---|---|
| M2 | orden de ramas en `_classify` (**el falso negativo del censo `(d)`**) | `'error_during_execution' == 'error_max_turns'` |
| M3 | reimponer la guarda `!= "aborted"` sobre el flag nuevo | idem |
| M4 | los `errors[]` del tope vuelven a `_diagnostics(snapshot)` | `'[ede_diagnostic] …' != 'Reached maximum number of turns (2)'` |
| M5 | el flag nunca se arma | `'success' == 'error_max_turns'` |

`M2` en rojo es el cierre del hallazgo: la mutación que antes pasaba ahora no pasa, y lo que cambió
no fue el mutador.

Hashes del estado sano: `capture.py`
`c97928db15bc37f1e86e30a6c493bd34785c274d9aca4c5fa6ac546c7051b150`, `streaming.py`
`5e9a9871fdfb63b475c5ef57585689e3df621d416959419c58528527a4efcccf`, `tests/test_capture.py`
`83a7b1ae12068a7a5cde446c71c05ebee2a92ee168e14f5dd458915d43f07fb9`.

### Suites, `ruff`, `mypy` y procesos

`agentic_code` **296 passed** (base `296` de la entrada `(d)`: la reescritura del caso no añade ni
quita casos, cambia lo que afirma). `ruff` sobre los tres ficheros tocados: **All checks passed**.
`mypy` sobre los dos fuentes: **Success: no issues found in 2 source files**. `agentic_runtime` no se
toca en este pago. Sin procesos supervivientes. Sintéticas de `agentic_runtime` ni corridas ni
tocadas (acuerdo de fase).

### Barrido de comentarios

`D-23` / `D-58`: los tres ficheros quedan sin comentarios. Las citas del canónico viven en el
docstring del test reescrito, única excepción del § 4.

### Lo que NO deroga

`D-08` intacto y aplicado dos veces: el orden y los `errors[]` salen del fuente de A leído entero, no
de deducir. `D-65` intacto: el catálogo cerrado de `subtype` y el reparto cola→`success`/
`error_during_execution` siguen en pie; lo que se corrige es la precedencia del adjunto. `D-66`
intacto: `end_reason: "aborted"` y `abort_reason` sobreviven al tope, que es lo que hace que el corte
del usuario siga siendo legible. `D-12·b`, `D-15`, `D-21`, `D-22`, `D-49`, `D-56`, `D-62`, `D-63`,
`D-64`, `D-67` intactos.

### Abierto

`FIND-CODE-ABORT-TOOLS-1` pasa al frente (censo `(e)`): el ESC en fase de tools que agota la gracia
cae al `kill` duro sin `AbortEvent`, y el siguiente movimiento ahí es **leer A antes de proponer
forma**. Detrás, `FIND-RT-COMPACT-EVT-1`, `FIND-RT-TOOLINPUT-1`, `FIND-CODE-TODO-1`. Sin cambio:
`5.b` del censo (carencias del registro `result`: `num_turns`, `duration_ms`/`duration_api_ms`,
`total_cost_usd`, `permission_denials`, `modelUsage`, `error_max_budget_usd`,
`error_max_structured_output_retries`), `DEUDA-BEDROCK-ABORT-1`, la calibración de `counted`
(2026-09-01), `FIND-GOOGLE-CASING`, `cache_write_1h` sin consumidor real, y `P1` de
`PLAN-OPTIMIZACION-TUI.md`.

---

## D-69 · `FIND-CODE-ABORT-TOOLS-1`: el aborto lo corta quien sostiene el proceso, y no lo cronometra nadie

**2026-09-02.** Fase `agentic_code` · estabilización. Cierra `FIND-CODE-ABORT-TOOLS-1`, que `D-68`
§*Abierto* puso al frente de la cola.

- **Palabra del usuario**: *«pero si la homologacion no quedo completa, porque el backgrounding de
  comandos era necesaria, se tiene que hacer. y apruebo los 3 puntos anteriores.»* — aprueba las tres
  inyecciones y **rechaza** mi recomendación de declarar la exención `reason === 'interrupt'` de A
  como divergencia: el mecanismo que falta se construye (`D-22`).

### El defecto medido: la gracia no era corta, el mecanismo no llegaba al hijo

`D-66` había puesto en `LocalAgentRuntime.cancel` un plazo de gracia de `5.0` s rematado con
`_task_registry.kill`. Medido, el defecto no era la duración:

1. `run_shell` **no recibía señal alguna**: esperaba con `wait_for(proc.communicate())`. Con ESC en
   fase de tools, la corrutina se soltaba y el proceso del SO **seguía vivo**.
2. `_task_registry.kill` cancela la *task* de asyncio, **nunca** el proceso que la tool sostiene.
3. El dispatcher sólo consultaba `ctx.stop.aborted` **antes** de arrancar; dentro del `await` no
   escuchaba nadie, así que el corte tenía que arbitrarlo un reloj externo.

Recalibrar la gracia habría mudado el problema de sitio: el proceso sobrevive igual.

### Lo que dicta A (`D-08`, leído 1→EOF)

- `ShellCommand.ts:264-267` — el objeto que sostiene el `ChildProcess` **registra él mismo** el
  listener de `abort`.
- `ShellCommand.ts:337-343` — `#doKill` hace `treeKill(pid, 'SIGKILL')`: mata el **árbol**.
- `Shell.ts:333-334` — spawnea `detached: true` y con su razón escrita al lado: *«Don't pass the
  signal - we'll handle termination ourselves with tree-kill»*.
- `toolExecution.ts:1206-1222` — `await tool.call(...)` **pelado**: A no cronometra el aborto en
  ningún punto; la señal viaja en el `toolUseContext` y la tool corta sola. La interrupción vuelve
  como un `tool_result` ordinario (`:1694-1737`).

### Lo inyectado

- `tools/exec_env.py` — `stop: AbortSignal | None = None` en el Protocol y en los cuatro caminos
  (`LocalExecEnvironment.run_shell`/`run_argv`, `BwrapExecEnvironment.run_shell`/`run_argv`/`_spawn`);
  spawn con `start_new_session=True` (homólogo de `detached: true`); `_collect`, que corre
  `proc.communicate()` **contra** `stop.wait()` en `asyncio.wait(FIRST_COMPLETED)` y cubre en el
  `finally` el tercer camino —que a la corrutina la cancelen desde fuera—; `_kill_process_tree`, con
  `os.killpg(pgid, SIGKILL)` (homólogo de `treeKill`) y `ABORTED_RETURNCODE = 137`.
- `tools/dispatcher.py` — `_race`: la señal compite con la ejecución. Rinde el `ToolResult.aborted`
  que ya existía, con su `reason`, y **no espera** a que la cancelación termine: matar al hijo es del
  backend, que ya oyó la misma señal.
- `tools/native/bash.py` — cablea `stop=getattr(ctx, "stop", None)` a `run_shell`.
- `execution/local/runtime.py` — se **retira** la gracia de `D-66` (`_DEFAULT_CANCEL_GRACE`, el kwarg
  `cancel_grace` y su atributo): `cancel()` alza la señal y devuelve.
- `agentic_code/tests/test_abort_tools.py` — **nuevo**, cinco casos en el consumidor real (`D-15`),
  con el criterio y las citas en el docstring (única excepción del § 4). El nieto (`sleep 120 &`) es
  lo que mide: matar sólo al shell lo dejaría en pie.

### Suicidio evitado, y declarado

Sin `start_new_session`, `os.getpgid(proc.pid)` es el grupo **propio** y el `killpg` habría
`SIGKILL`-eado al proceso que ejecuta. `_kill_process_tree` compara con `os.getpgid(0)` y degrada a
`proc.kill()` — que alcanza al shell y no a su descendencia—: si alguien retira el
`start_new_session`, el fallo debe ser una carencia visible, no un tiro en el pie.

### Acreditación (`D-12·b`) — seis mutaciones, seis rojas

Copia propia de los cuatro fuentes en `mktemp -d` (`/tmp/homolog-abort-FcGHQW`), `sha256` idéntico al
repo antes de mutar; revert desde esa copia con **purga de `.pyc`** en cada pasada (`D-62`), hash
comprobado tras cada revert, y censo de procesos supervivientes tras cada ronda.

| | mutación | rojo |
|---|---|---|
| M1 | sin `start_new_session` en el spawn local | el nieto sobrevive (2 casos) |
| M2 | `_collect` sordo a la señal (`watch = None`) | el nieto sobrevive |
| M3 | `_kill_process_tree` no mata | el nieto sobrevive (2 casos) |
| M4 | `_race` sordo a la señal (`watch = None`) | no rinde `aborted` (2 casos) |
| M5 | vuelve la gracia `5.0` + `kill` en `cancel()` | `5.005… < 1.0` |
| M6 | `bash` deja de pasar `stop` | el nieto sobrevive |

**`M6` salió verde en la primera pasada**: por el dispatcher el árbol muere igual, pero por la
cancelación de la corrutina, que es el camino frágil —basta una tool que se trague el
`CancelledError`—. No se aceptó como falso negativo: la prueba no medía el cable, así que se **añadió**
el caso que lo mide (`BashTool.execute` en directo, sin dispatcher) y `M6` se repitió en rojo. Una
inyección que ninguna prueba acredita es un superviviente, no una inyección.

Hashes del estado sano: `tools/exec_env.py`
`d075638de5fc57a52bef783c973dcaf216415928e52c642947b2d94ba0ab84eb`; `tools/dispatcher.py`
`975e383347677571deda08ed4862656932c313c1a78918f638cb4eb9d9b6bbb6`; `tools/native/bash.py`
`e7b2600ecc3f8c3e223216c85da67d4887991c55747aa55045f721694322dab2`;
`execution/local/runtime.py` `a9cfacb49dad9539e11f445bbe6eea88f83a60d4f55b2a259f1e4277a277d854`.

### Suites, `ruff`, `mypy` y procesos

`agentic_code` **301 passed** (base `296` de `D-68` + los 5 casos nuevos). `ruff` sobre los cinco
ficheros tocados: **All checks passed**. `mypy` sobre los cuatro fuentes: **Success: no issues found
in 4 source files**. Sin procesos supervivientes al cierre (los que M3 dejó vivos a propósito se
cazaron por pid, no por patrón). Sintéticas de `agentic_runtime` ni corridas ni tocadas (acuerdo de
fase).

### Lo que este pago NO cierra: el backgrounding

A **exime** `reason === 'interrupt'` del kill (`ShellCommand.ts:186-193`) y en su lugar hace
`background(taskId)` (`:349-366`), para que el modelo vea la salida parcial de un comando que sigue
corriendo. B **no tiene** ese mecanismo, así que hoy `USER_INTERRUPT` mata como cualquier otra razón.
Por palabra del usuario **no se declara como divergencia**: se construye (`D-22`), en su propio paso,
y hasta entonces el kill uniforme es **provisional**, no la forma final.

### Lo que NO deroga

`D-66` queda **corregido en su mecanismo**: el `end_reason: "aborted"` y el `abort_reason` que pagó
siguen intactos; lo que se retira es el plazo de gracia y el `kill` de la task, que medían y mataban
lo que no tocaba. `D-08`, `D-12·b`, `D-15`, `D-21`, `D-22`, `D-49`, `D-56`, `D-62`…`D-65`, `D-67` y
`D-68` intactos.

### Abierto

`FIND-CODE-ABORT-BG-1` (nuevo, al frente): construir el backgrounding de comandos y la exención de
`USER_INTERRUPT`. Detrás, `FIND-RT-COMPACT-EVT-1`, `FIND-RT-TOOLINPUT-1`, `FIND-CODE-TODO-1`. Sin
cambio: `5.b` del censo, `DEUDA-BEDROCK-ABORT-1`, la calibración de `counted`, `FIND-GOOGLE-CASING`,
`cache_write_1h` sin consumidor real, `P1` de `PLAN-OPTIMIZACION-TUI.md` y el `base_url` con
`localhost` de `local_catalog.py`.
