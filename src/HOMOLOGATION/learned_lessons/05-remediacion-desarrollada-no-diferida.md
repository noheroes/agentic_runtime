# 05 · Remediación desarrollada, no diferida

> **Regla.** En el DoD, el paso de diseño (1ª pasada) **desarrolla la remediación de una vez** en el doc, por
> finding: **comportamiento · seam · firma · cableado · orden · test**. Prohibido diferirla con un "Ajuste:" de una
> línea.

## Por qué
- Un "Ajuste: añadir X" de una línea **parece** cerrar el finding pero deja todo el trabajo real (dónde va el seam,
  qué firma, cómo se cablea, en qué orden, qué test lo prueba) para "después" — que es [[00-falsa-economia-del-rigor]]
  aplicada al diseño.
- Desarrollar la remediación **obliga a entender el finding de verdad**: al escribir el seam/firma/cableado a
  menudo aparece que el finding tenía sub-ítems, dependencias con otros subsistemas, o que estaba mal planteado.

## Modo de fallo típico
- Cerrar cada fila de la tabla con "Ajuste: portar Y" sin §Plan.
- Diseñar la remediación "en la cabeza" y no dejarla escrita y desarrollada.

## Puerta / check
- [ ] Cada finding de Deuda A tiene su entrada en **§Plan de homologación / remediación desarrollada** con los 6
      campos: comportamiento, seam, firma, cableado, orden, test.
- [ ] La Deuda B (transversal) vive en su doc con remediación desarrollada + dueño(s) + test.
- [ ] Los xfail(strict) del test de homologación **codifican los targets** (passing = homologado; xfail = gap);
      ninguno hace xpass.
- [ ] Los cabos que aterrizan en subsistemas abiertos se **cierran al documentarlos**, con destino explícito.

## Evidencia
- El acuerdo de método (retoma): "paso 3 = DESARROLLAR la remediación de una vez en el doc (NO diferir con
  'Ajuste:' de una línea)". Docs 01-12 siguen §Plan (R0-R11, CR, LR, …, SkR1-SkR17).

Relacionadas: [[00-falsa-economia-del-rigor]] · [[03-ledger-honesto-y-puerta-de-cierre]]
