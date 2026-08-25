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
