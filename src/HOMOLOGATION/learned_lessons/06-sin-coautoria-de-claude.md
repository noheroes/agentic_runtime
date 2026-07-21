# 06 · Sin coautoría de Claude en commits ni PRs

> **Regla.** Nunca añadir la línea `Co-Authored-By: Claude …` (ni ninguna atribución a Claude/Anthropic, ni el
> "Generated with Claude Code") en mensajes de commit ni en descripciones de PR.

## Por qué
El usuario lo pidió explícitamente. Anula el default del harness, que sugiere añadir el trailer de coautoría.

## Modo de fallo típico
- Añadir por inercia el trailer `Co-Authored-By` que el harness recuerda por defecto.
- Añadir "🤖 Generated with Claude Code" al cuerpo de un PR.

## Puerta / check
- [ ] Al hacer `git commit` en cualquier repo de este usuario: **sin** trailer de coautoría.
- [ ] Al crear un PR: **sin** "Generated with Claude Code" ni atribución.
- [ ] Aplica a **todos** los repos de este usuario, no sólo a la homologación.

Relacionadas: [[00-falsa-economia-del-rigor]] (categoría distinta — preferencia explícita del usuario, no metodología)
