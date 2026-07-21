# 01 · Exhaustividad: lectura íntegra, no muestreo

> **Regla.** Se leen **ÍNTEGRAS** todas las contrapartes canónicas relevantes, tramo a tramo hasta el 100%.
> `grep` **orienta**, no **sustituye** la lectura. Se enumera **cada** feature de la contraparte, no una muestra.
> La superficialidad es el **modo de fallo #1** de este esfuerzo.

## Por qué
- Un `grep` **sólo encuentra lo que ya se te ocurrió buscar**. Confirma o niega una hipótesis previa; **no puede
  destapar lo que no sabías que existía**. La lectura íntegra sí. Confundir "confirmé mi hipótesis con grep" con
  "leí el archivo" es el error raíz.
- Declarar un archivo "inmenso" y saltarse tramos garantiza omisiones: el costo de saltar ya se materializó
  (ver Evidencia).

## Modo de fallo típico
- Leer "por hitos" un archivo de 1000-1700 LOC y declararlo cubierto.
- Grepear un patrón esperado, no encontrar sorpresas, y dar por leído el archivo.
- Listar una **muestra** de features en vez de enumerarlas todas.

## Puerta / check
- [ ] Archivos grandes (query.ts, QueryEngine.ts, loadSkillsDir.ts, SkillTool.ts, client.ts…): leídos **íntegros**
      (idealmente de una sola llamada, o por bloques contiguos que cubran 1→EOF, registrando el rango).
- [ ] Ningún hallazgo ni conteo se apoya en un archivo sólo grepeado.
- [ ] Se enumeró **cada** feature de la contraparte, no una muestra representativa.
- [ ] Si el archivo se leyó por tramos, el ledger lo dice con **rango exacto** (ver [[03-ledger-honesto-y-puerta-de-cierre]]).

## Evidencia
- **02·loop**: leer cabeceras/helpers (que "por hitos" se saltaba) reveló `yieldMissingToolResultBlocks`, un
  invariante de API tool_use↔tool_result.
- **12·cap-skills**: el `grep` sobre los bundled buscaba "coordinator/módulo oculto" y no lo había — pero era
  ciego a que `getPromptForCommand` es un **callable dinámico ctx-aware** (FIND-SKILL19). La lectura lo destapó.

Relacionadas: [[00-falsa-economia-del-rigor]] · [[02-prohibido-descartar-sin-abrir]]
