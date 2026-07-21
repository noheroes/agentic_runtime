# 04 · Mostrar los resúmenes al usuario, no enterrarlos

> **Regla.** Los resúmenes que el protocolo exige al cerrar (el **ledger** con columna "Lectura" y las **4 preguntas**
> de cierre) se **presentan al usuario** en la respuesta, no sólo se escriben dentro del doc. Y la respuesta
> **SIEMPRE termina con un VEREDICTO DE AVANCE explícito e inequívoco**: o bien **`✅ NADA PENDIENTE → avanzar a
> <siguiente subsistema>`**, o bien **`⛔ PENDIENTE(S) antes de avanzar: <lista con destino y tipo>`**. Nunca se
> cierra sin ese veredicto.

> **Sin escotilla (vacío que cierra).** El atajo bloqueado es responder la pregunta 4 ("¿todo cubierto?") con un
> "sí, cabos con destino" y **plegar dentro de esos cabos trabajo de verificación aún pendiente** (una re-visita
> diferida, un subsistema sin re-verificar con el método vigente), enterrándolo como si fuera un cabo delegado.
> **Trabajo de verificación pendiente NO es un cabo con destino**: es un bloqueador de avance y va en la línea
> `⛔ PENDIENTE`, visible, con su tipo. El veredicto de avance NO admite versión implícita: o se declara
> `✅ NADA PENDIENTE` por escrito, o se lista lo que falta. Un cierre sin veredicto explícito = superficialidad que
> permite saltarse un pendiente sin que nadie lo note.

## Por qué
La puerta de cierre sólo protege si el usuario puede **verla** sin abrir el doc. Enterrar el ledger y las 4
preguntas convierte una verificación en una afirmación no comprobable ("confía en que lo hice"). Mostrarlos es lo
que permite al usuario detectar una sobre-declaración — que es justo el punto de la puerta.

## Modo de fallo típico
- Cerrar un subsistema con "listo, suite verde, README actualizado" **sin** mostrar el ledger ni las 4 respuestas.
- Asumir que "está en el doc" equivale a "el usuario lo revisó".
- Cerrar **sin veredicto de avance**: mencionar un pendiente "de pasada" en medio del resumen y luego avanzar
  como si no existiera (el pendiente se evapora entre líneas).
- Contestar la pregunta 4 con "todo cubierto, cabos con destino" cuando queda **trabajo de verificación** sin
  hacer (una re-visita diferida) — plegado dentro de "cabos" y así invisibilizado.

## Puerta / check
- [ ] Al cerrar un subsistema, la respuesta al usuario incluye (o enlaza y resume fielmente): el **estado del
      ledger** (qué se leyó íntegro / por tramos / ⛔-abierto / no-leíble) y las **4 preguntas respondidas**.
- [ ] **La respuesta termina con un VEREDICTO DE AVANCE explícito**: `✅ NADA PENDIENTE → avanzar a <NN+1>` **o**
      `⛔ PENDIENTE(S): <lista>`. Cada pendiente lleva **tipo** (verificación / remediación / decisión-del-usuario)
      y **destino**. Si hay ≥1 pendiente de **verificación**, el veredicto NO puede ser `✅ NADA PENDIENTE`.
- [ ] Los **pendientes de verificación** (re-visitas diferidas, filas ✅/🔀 no re-verificadas con el método
      vigente) se listan como bloqueadores de avance, **NO** se pliegan dentro de "cabos con destino" de la
      pregunta 4.
- [ ] Si alguna respuesta es "sí tras re-auditoría", se **dice explícitamente** — no se presenta como si la 1ª
      pasada hubiera bastado.
- [ ] Cualquier sobre-declaración detectada se marca en la respuesta, no sólo se corrige en silencio en el doc.

## Evidencia
- **12·cap-skills**: el usuario preguntó *"¿por qué no me muestras los resúmenes que el protocolo te exige?"* — el
  ledger y las preguntas estaban en el doc pero no se le presentaron, y la respuesta 1 estaba sobre-declarada.
- **01·contracts re-visita L09 (2026-07-18)**: el resumen mencionó "de pasada" que quedaba la **re-visita de
  completitud de 02·loop** pendiente y, sin veredicto de avance explícito, propuso saltar directo a 04·modes — el
  pendiente casi se pierde. El usuario lo detectó (*"el resumen no mostraba de forma clara esos pendientes, no lo
  pases por alto"*). Un `⛔ PENDIENTE(S)` obligatorio al pie lo habría hecho imposible de enterrar.

Relacionadas: [[03-ledger-honesto-y-puerta-de-cierre]] · [[00-falsa-economia-del-rigor]]
