# 08 · La superficialidad se esconde en el archivo más grande

> **Regla.** En cada subsistema, el archivo **MÁS GRANDE** es donde se esconde la omisión. Se barre su **top-level
> de punta a punta** y se **CIERRAN los huecos entre declaraciones** (cabeceras, helpers, ramas entre funciones
> exportadas) — no se glosa por "hitos". **"Abierto" ≠ "íntegro"**: que coincida el conteo de líneas prueba que se
> abrió, no que se leyó.

> **Sin escotilla (vacío que cierra).** El atajo bloqueado es leer las funciones "importantes" del archivo grande,
> ver que el LOC coincide con lo esperado, y declararlo cubierto — dejando sin leer justo cabeceras/helpers/huecos
> entre declaraciones, que es **donde viven los invariantes y las variantes omitidas**. Coincidir el conteo de
> líneas **no** es evidencia de lectura íntegra; es evidencia de que el archivo se abrió. La regla no se cumple con
> "leí lo sustantivo del archivo grande".

## Por qué
El modo de fallo recurrente del esfuerzo no es saltarse un archivo entero — es **subcubrir el más grande** de cada
subsistema. La omisión no está en las funciones exportadas obvias sino en los intersticios: un helper, una cabecera,
una variante de un enum, una rama entre dos funciones. Barrer el top-level completo y cerrar los huecos lo caza.

## Modo de fallo típico
- Leer "por hitos" un archivo de 1000-5000 LOC y declararlo cubierto.
- Tomar "el conteo de líneas coincide con lo esperado" como prueba de lectura íntegra.
- Enumerar las variantes/funciones principales y no cerrar los huecos entre ellas.

## Puerta / check
- [ ] El archivo **más grande** de cada subsistema se leyó **1→EOF**, cerrando huecos entre declaraciones.
- [ ] Ninguna cobertura se apoya en "el LOC coincide" (**abierto ≠ íntegro**).
- [ ] Se barrió el **top-level completo**: cada declaración exportada + helpers + cabeceras + ramas intermedias.
- [ ] En el ledger, ese archivo figura como `íntegro` con rango real, no "sí" genérico (ver [[03-ledger-honesto-y-puerta-de-cierre]]).

## Evidencia
- **06·hooks**: `utils/hooks.ts` (5022 LOC) estaba **glosado** → al leer íntegro: `HOOK_EVENTS`=**27** (no 28),
  +HOOK8 (dos motores executeHooks/OutsideREPL), +HOOK9/10/11, y ~15 ejecutores omitidos.
- **07·events**: la enumeración de variantes escondía el `init/handshake` (F0 ❌ sin fila).
- **08·signals**: `StreamingToolExecutor.ts`/`toolExecution.ts`/`useCancelRequest.ts` leídos por grep+ventanas →
  al leer íntegro aparecieron **6 ❌ nuevos**. (El caso que originó el mandato de re-auditoría.)
- **02·loop**: `yieldMissingToolResultBlocks` vivía en los helpers, no en la función principal.

Relacionadas: [[01-exhaustividad-lectura-integra]] · [[02-prohibido-descartar-sin-abrir]] · [[00-falsa-economia-del-rigor]]
