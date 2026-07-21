> ⚠️ **SUPERSEDED (2026-07-19) — este corpus está RETIRADO como fuente de método.**
> Decisión del usuario: el método vive ahora **únicamente** en la skill genérica
> `~/.claude/skills/analisis-comparativo-ab/lecciones/*.md` (fuente única del PASO 0). Su método generalizable se
> plegó allí manteniendo la generalización (la lección de validación de esta carpeta, "verificar COMPLETITUD A vs B,
> no confirmar el doc" = antiguo `09` de aquí, es la **lección 11** de la skill); lo project-specific (A=canónico /
> B=runtime, subsistemas 01-18, `xfail(strict)`, tracker) vive en la memoria del esfuerzo. La coautoría-Claude
> (antiguo `06`) es preferencia del usuario, no método. **NO leer esta carpeta en el PASO 0** — se conserva sólo como
> **evidencia histórica** referenciada por los docs `NN-*.md`. Ver `HOMOLOGATION/README.md` y la memoria del esfuerzo.

# Lecciones aprendidas — corpus para una skill spec-driven con arnés

Este directorio recopila las **lecciones y correcciones** que el usuario ha venido dando durante el esfuerzo de
homologación. El objetivo declarado: construir con ellas una **skill tipo spec-driven** con **arnés** suficiente
para **corregir en lo que suelo fallar** — no un recordatorio pasivo, sino puertas verificables.

## Estructura de cada lección (contrato)
Cada archivo `NN-*.md` sigue el mismo esqueleto, pensado para ser consumido por un arnés:

- **Regla** — una línea imperativa (el *spec*).
- **Por qué** — el razonamiento; en particular, por qué la intuición/atajo falla.
- **Modo de fallo típico** — el anti-patrón concreto en el que caigo.
- **Puerta / check** — checklist **verificable**. Estas líneas son las **aserciones del arnés**: una skill
  spec-driven las convierte en gates que deben cumplirse antes de declarar un paso/subsistema cerrado.
- **Evidencia** — el costo real ya materializado (por qué la lección existe, no es teoría).

Algunas lecciones añaden un blockquote **"Sin escotilla (vacío que cierra)"** justo tras la Regla. Los enlaces
`[[nn-nombre]]` cruzan lecciones relacionadas.

## Principio rector al añadir o transcribir una lección (anti-vacío)
**Transcribir una lección NO es suavizarla.** Una Regla relajada **reabre el atajo que la originó**: la falsa
economía (00) nació de releer *"grep orienta"* como *"grep confirma"* y de usar *"es contenido"* como permiso para
no abrir. Por eso, al escribir o mover una lección:
1. La **Regla** debe ser **airtight**: los límites **ONLY / NEVER / SÓLO / NUNCA** van **inline**, no en una nota
   al pie que se pueda ignorar.
2. Declarar explícitamente el **vacío que cierra** (qué reinterpretación a la baja quedaría bloqueada) — idealmente
   como blockquote "Sin escotilla".
3. **Nunca** condensar una lección quitándole sus cláusulas anti-loophole; si hay que acortar, se acorta la
   *evidencia* o el *porqué*, **nunca** la Regla ni el "Sin escotilla".

## Índice
| # | Lección | Núcleo |
|---|---|---|
| 00 | [Falsa economía del rigor](00-falsa-economia-del-rigor.md) | No hacerlo ahora = hacerlo después, duplicado con recargo. El ahorro local no existe. **Raíz de casi todas las demás.** |
| 01 | [Exhaustividad: lectura íntegra](01-exhaustividad-lectura-integra.md) | Leer ÍNTEGRO; grep orienta, no sustituye; enumerar cada feature, no una muestra. |
| 02 | [Prohibido descartar sin abrir](02-prohibido-descartar-sin-abrir.md) | ⛔ sólo tras ABRIR y comprobar; nunca por título/tamaño. |
| 03 | [Ledger honesto y puerta de cierre](03-ledger-honesto-y-puerta-de-cierre.md) | Columna "Lectura" real + §honestidad + 4 preguntas = sí honestas. |
| 04 | [Mostrar los resúmenes al usuario](04-mostrar-los-resumenes-al-usuario.md) | Presentar ledger + 4 preguntas; no enterrarlos. **Cerrar con VEREDICTO DE AVANCE explícito** (`✅ nada pendiente→siguiente` / `⛔ pendientes`); verificación pendiente ≠ cabo con destino. |
| 05 | [Remediación desarrollada, no diferida](05-remediacion-desarrollada-no-diferida.md) | DoD paso 3: desarrollar (comportamiento·seam·firma·cableado·orden·test), no "Ajuste:" de una línea. |
| 06 | [Sin coautoría de Claude](06-sin-coautoria-de-claude.md) | Preferencia explícita del usuario (no metodología): sin `Co-Authored-By`. |
| 07 | [Fuera de alcance ≠ trocear in-scope](07-fuera-de-alcance-no-es-trocear.md) | "Fuera de alcance" SÓLO para satélites enteros de OTRO subsistema numerado; nunca trocear un archivo del subsistema actual. |
| 08 | [Superficialidad en el archivo más grande](08-superficialidad-en-el-archivo-mas-grande.md) | El archivo más grande esconde la omisión; barrer top-level + cerrar huecos; "abierto" ≠ "íntegro". |
| 09 | [Verificar completitud A vs B, no confirmar el doc](09-verificar-completitud-no-confirmar-doc.md) | En validación, el objeto es la homologación A vs B, NO el documento; cada ✅/🔀 se re-verifica abriendo el código de B, no la tabla. |

## Taxonomía
- **Metodología de rigor** (00-05, 07, 08): el modo de fallo #1 del esfuerzo es la **superficialidad**, y su motor
  es la falsa economía (00). 01-05, 07-08 son sus manifestaciones concretas y sus puertas.
- **Preferencias explícitas del usuario** (06): no deriva de un modo de fallo cognitivo sino de una instrucción
  directa; se aplica igual pero se cataloga aparte.

## Cómo lo usará la skill spec-driven (visión)
1. **Pre-condición**: antes de abrir un subsistema, cargar las Reglas como *spec* activo.
2. **Arnés en línea**: las líneas "Puerta / check" se materializan como una checklist que **debe** resolverse —
   p.ej. "ningún ⛔ sin `íntegro → ⛔` en el ledger", "ningún finding-count final con archivos sin abrir".
3. **Puerta de cierre**: no permitir declarar un subsistema cerrado hasta que (a) el ledger tenga columna Lectura
   real, (b) las 4 preguntas sean sí honestas, (c) se hayan **presentado al usuario**.
4. **Regla económica rectora** (00): ante cualquier tentación de atajo, aplicar el test *"¿tendré que hacer esto
   después?"* → si sí, el ahorro es ilusorio → hacerlo ahora.

> Corpus vivo: se añaden lecciones a medida que aparecen correcciones. Mantener el esqueleto (Regla · Por qué ·
> Modo de fallo · Puerta · Evidencia) para que el arnés pueda parsearlas de forma uniforme.
