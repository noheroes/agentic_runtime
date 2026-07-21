# 03 · Ledger honesto y puerta de cierre

> **Regla.** Nunca declarar "leído íntegro" lo leído por tramos. El ledger de cierre lleva una columna **"Lectura"**
> por archivo (`íntegro` / `íntegro → ⛔` / `tramos-con-rango` / `no-leíble-con-razón`) + una **§nota de honestidad**.
> El cierre se habilita sólo cuando las **4 preguntas** se responden **sí, honestamente**.

## Por qué
El ledger es el mecanismo que hace verificable el rigor. Si el ledger sobre-declara ("sí, íntegro" para algo
leído por tramos, o ⛔ para algo no abierto), la puerta de cierre deja de proteger y el atajo pasa. La honestidad
del ledger **es** el control de calidad.

## Las 4 preguntas de cierre (deben ser sí, honestas)
1. ¿Se revisó **todo** cada archivo **canónico** listado?
2. ¿Se revisó **todo** cada archivo **runtime** listado?
3. ¿Los hallazgos fueron **exhaustivos (no superficiales)**?
4. ¿Quedó **todo cubierto (nada pendiente)**? (lo delegado se anota con **destino**, no como pendiente)

## Modo de fallo típico
- Poner "sí (íntegro)" en la columna Lectura de un archivo leído a medias.
- Responder "sí" a la pregunta 1 cuando quedan archivos sin abrir.
- Enterrar el ledger y las preguntas en el doc en vez de resolverlos con honestidad (ver [[04-mostrar-los-resumenes-al-usuario]]).

## Puerta / check
- [ ] Cada archivo tiene su columna **Lectura** con el valor real (no "sí" genérico).
- [ ] Los archivos leídos por tramos declaran el **rango exacto** (p.ej. `152-1673, 1688-3348`).
- [ ] Existe una **§nota de honestidad** que reconoce explícitamente cualquier superficialidad de una pasada previa.
- [ ] Las 4 preguntas están respondidas y **son sí de verdad**; si una es "sí tras re-auditoría", se dice así.
- [ ] Lo genuinamente no-leíble aparece con razón (no vendorizado / SDK externo / gating), no como ⛔ por título.

## Evidencia
- **11·cap-mcp**: la 1ª versión del ledger declaró "sí (íntegro)" para archivos leídos por tramos y listó un
  hallazgo sobre `headersHelper` **sin haber leído** `headersHelper.ts`. Corregido en la re-auditoría.
- **12·cap-skills**: la pregunta 1 se respondió "sí" con 13 bundled sin abrir + FIND-MCP16 inferido; la
  re-auditoría la corrigió a "sí, **tras la re-auditoría** (en la 1ª pasada NO)".

Relacionadas: [[00-falsa-economia-del-rigor]] · [[02-prohibido-descartar-sin-abrir]] · [[04-mostrar-los-resumenes-al-usuario]]
