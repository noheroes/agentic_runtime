# 09 · El trabajo es verificar COMPLETITUD A vs B, no CONFIRMAR el documento

> **Regla.** En MODO VALIDACIÓN sobre un doc existente, el objeto a validar es la **homologación A vs B**, NO el
> documento. Para **cada** comportamiento de A, se abre la **implementación de B** y se confirma que lo reproduce.
> El doc previo es una **hipótesis de partida**, nunca la fuente de verdad. Leer A + comprobar que la tabla del doc
> enumera A + comprobar que B carece de lo que el doc dice que carece = **confirmación de documentación**, que NO
> es la tarea y pasa por alto justo lo que el doc no vio.

> **Sin escotilla (vacío que cierra).** El atajo bloqueado es tratar las filas ✅/🔀 del doc como ya-resueltas
> ("el doc dice que B reproduce el comportamiento por otro mecanismo → lo acepto"). Una fila ✅/🔀 afirma un
> **comportamiento de B**; esa afirmación sólo se valida **abriendo el código de B** que supuestamente lo
> reproduce y siguiendo el dato (L02·cableado). Para las filas ❌ (ausente) la confirmación-de-doc y la
> verificación-de-completitud convergen (campo ausente = ausente); **es en las ✅/🔀 donde divergen** — y ahí es
> donde el doc previo, aun internamente coherente, puede sobre-declarar una homologación que B no cumple.

## Por qué
Un doc de categoría puede ser **internamente consistente y completo-en-apariencia** (enumera todos los campos del
tipo de A, clasifica cada uno) y aun así **no probar nada** sobre si B reproduce el comportamiento: eso vive en la
**implementación de B**, no en la declaración del tipo ni en la tabla. Confirmar el doc valida la *forma*; verificar
completitud valida el *efecto observable*. El modo de fallo #1 (superficialidad) se disfraza aquí de "validación
diligente": se lee A a fondo, se contrasta con la tabla, todo cuadra — y no se abrió una sola línea de la B que
sostiene los ✅.

## Modo de fallo típico
- Releer A 1→EOF, comprobar que la tabla del doc lista sus features, y dar la categoría por validada **sin abrir la
  implementación de B** de las filas ✅/🔀.
- Aceptar "🔀: B logra el mismo efecto por otro mecanismo" sin abrir ese mecanismo en B para confirmar que existe,
  se invoca, y es alcanzable.
- Apoyarse en el nombre de un campo/método de B (existe `presentation`, existe `stop`) en vez de seguir su
  **cableado** (¿quién lo invoca? ¿con qué args? ¿en la ruta real?).

## Puerta / check
- [ ] Cada fila **✅** se re-verificó abriendo el código de B que produce el comportamiento y siguiendo el dato de
      punta a punta (no por existencia de campo, no por la tabla).
- [ ] Cada fila **🔀** ("B lo hace por otro mecanismo") nombró y **abrió** ese mecanismo en B, confirmando que se
      invoca y es alcanzable.
- [ ] El doc previo se trató como hipótesis: cualquier ✅/🔀 no re-verificado en B se marca como tal, no se hereda.
- [ ] Los hallazgos nuevos de abrir B (costuras a medio cablear, defaults nunca sobrescritos) se registran —
      distinguiendo **deuda A-vs-B** de **tech-debt B-interno** de una extensión sin contraparte canónica (L10).

## Evidencia
- **03·context (2ª vuelta)**: la 1ª ronda de validación fue confirmación-de-doc — se leyó A (Tool.ts/AppStateStore.ts
  1→EOF) y se comprobó que B carecía de lo que el doc decía, pero las filas ✅/🔀 se aceptaron del doc. Al
  re-verificar abriendo B (`resolver.py`/`registry.py` filtro `safe_for_background`, `agent_loop.py`/`dispatcher.py`
  chequeo de `ctx.stop`, `dispatcher.py:42` invocación de `sanitize_output`) los ✅ **se sostuvieron sobre la base
  correcta** — y además apareció una **costura latente** invisible a la confirmación-de-doc: `PathPresentation.to_llm`
  no tiene ningún call site de producción (`grep to_llm` = sólo defs + fakes de test). Clasificada como tech-debt
  B-interno (extensión sin contraparte canónica), NO como deuda A-vs-B (L10, anti-padding).

Relacionadas: [[00-falsa-economia-del-rigor]] · [[01-exhaustividad-lectura-integra]] · [[02-prohibido-descartar-sin-abrir]] · [[03-ledger-honesto-y-puerta-de-cierre]]
