# 00 · La falsa economía del rigor

> **Regla.** No hacer el trabajo con rigor **ahora** no lo ahorra: lo **difiere y lo duplica con recargo**.
> El "ahorro" que promete la lógica-local no existe en la práctica. Por tanto no hay nada que resistir —
> el camino riguroso es el camino barato.

> **Sin escotilla (vacío que cierra).** Esta lección nació de **suavizar otra**: "grep **orienta**, no sustituye"
> se releyó como "grep **confirma**", y "es contenido de producto" se usó como permiso para no abrir. El vacío que
> se cierra aquí es tratar cualquier atajo como "ahorro" sin verificar que no es sólo **trabajo diferido**. Ante la
> tentación, el test es único y no admite excepción: *"si no lo hago ahora, ¿tendré que hacerlo después?"* → si sí,
> **no hay ahorro** → hacerlo ahora.

## Por qué (la aritmética real)
La tentación del atajo nace de una **contabilidad local**: "este archivo es barato de saltar". Es falsa. La
contabilidad correcta es **global**: la tarea no está hecha hasta que está bien hecha. Como el proceso tiene una
**puerta de cierre** (ledger honesto + 4 preguntas + revisión del usuario), el trabajo saltado **siempre vuelve**.

El atajo sólo "paga" en un mundo donde **nadie verifica** — y todo el proceso existe para verificar. Apostar el
atajo es apostar a que no te revisan, dentro de un sistema cuyo propósito es revisar. Es irracional por construcción.

Y el retorno no es 1+1, es **duplicación con recargo**:
- La re-auditoría cuesta **más** que la lectura original: hay que **recargar contexto ya descartado** y
  **reconciliar/reescribir** el doc, los tests y el índice construidos sobre la pasada superficial.
- Latencia del ida-y-vuelta con el usuario.
- Un **impuesto de confianza** que no se recupera con un `git`.
- Coste ≈ **2.5×** + impuesto.

## Modo de fallo típico
- Bajar el rigor **exactamente** donde predigo que "no hay nada" — cuando esa predicción es lo no verificado y
  el costo de equivocarse es justo el hallazgo perdido.
- Sustituir lectura por `grep` (ver [[01-exhaustividad-lectura-integra]]) o marcar ⛔ por título
  (ver [[02-prohibido-descartar-sin-abrir]]).
- Tratar la re-auditoría como un flujo aceptable ("entrego superficial → me reprochan → lo hago bien"): eso
  **externaliza el control de calidad al usuario**. Que "aparezca algo al re-auditar" no valida el proceso —
  **prueba que la 1ª pasada era insuficiente por defecto**.

## Coste compuesto (aunque NO te detecten)
Un doc de subsistema superficial **envenena a los que dependen de sus cabos**. Un `FIND` inferido o un cabo mal
cerrado se **hereda** por los subsistemas siguientes. "No detectado" no significa "gratis": significa que el costo
**se movió a un lugar más difícil de rastrear y se amplificó**. Diferido **y** compuesto.

## Puerta / check (lo que un arnés debe forzar)
- [ ] El default es **hacerlo completo ahora**; saltarse algo requiere **justificación explícita por-ítem**,
      registrada, y sólo **después** de haberlo abierto.
- [ ] Antes de declarar un paso "hecho", preguntar: *"si no lo hago ahora, ¿tendré que hacerlo después?"*.
      Si la respuesta es sí → el ahorro es ilusorio → hacerlo ahora.
- [ ] Contabilizar el costo sobre **la tarea completa**, nunca sobre el paso aislado.

## Evidencia (costo ya materializado)
- **11·cap-mcp**: la 1ª pasada marcó ~10 archivos ⛔ sin abrirlos → la re-auditoría destapó **FIND-MCP21-24 + 2
  matices** escondidos justo en lo descartado. Trabajo rehecho.
- **12·cap-skills**: la 1ª pasada marcó 13 bundled ⛔ por `grep` e infirió FIND-MCP16 → al ABRIRLOS apareció
  **FIND-SKILL19** (`getPromptForCommand` es un callable dinámico) y se descubrió que `mcpSkills.ts` no estaba
  vendorizado. Doc, tests y README rehechos.
- **02·loop**: la lectura "por hitos" omitió `yieldMissingToolResultBlocks` (invariante API tool_use↔tool_result).

**En los tres casos el atajo NO ahorró nada — sólo movió el mismo trabajo (y más) al turno siguiente.**
