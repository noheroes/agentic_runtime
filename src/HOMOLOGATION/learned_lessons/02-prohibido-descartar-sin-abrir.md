# 02 · Prohibido marcar ⛔ (descartar) sin abrir el archivo

> **Regla.** ⛔ (fuera de alcance / UI / producto) **sólo es legítimo tras ABRIR el archivo y comprobar** que lo
> es. **Nunca** por título, tamaño ni ruta. Aunque el veredicto final resulte correcto, el juicio hecho sin abrir
> es superficialidad.

## Por qué
- La categoría "esto es contenido/UI, no vale la pena abrirlo" es una **escotilla de escape**: hace el trabajo de
  permitirme **no leer**. El pre-juicio no está verificado.
- La lección concreta: archivos tildados de "UI"/"contenido" escondían **comportamiento core**. El veredicto por
  título es una apuesta, y la evidencia dice que la apuesta se pierde.

## Modo de fallo típico
- "Es un componente React / un diálogo ink / contenido de producto" → ⛔ sin abrir.
- "Son 15 archivos de contenido, greopeo el patrón y los marco a todos ⛔."

## Puerta / check
- [ ] Cada archivo del árbol del subsistema se **abrió al menos una vez** antes de clasificarlo.
- [ ] El ledger marca los ⛔ como **`íntegro → ⛔`** (abierto y confirmado), no como ⛔ a secas.
- [ ] Ninguna ⛔ ni ningún conteo de findings es **definitivo** hasta que **cada** archivo del árbol se abrió.
- [ ] Si un archivo es genuinamente no-leíble (no vendorizado, SDK externo, feature-gated ausente), se
      **documenta como tal con la razón** — no se infiere su interior ni se marca ⛔ por título.

## Evidencia
- **11·cap-mcp**: `useManageMCPConnections.ts` (tildado de "hook React UI") contenía la **reconexión con backoff**
  y los handlers `*_list_changed` — core, no UI. Al abrir lo descartado: **FIND-MCP21-24 + 2 matices**.
- **12·cap-skills**: 13 bundled marcados ⛔ por grep; al abrirlos, el veredicto ⛔-contenido resultó correcto
  **pero** apareció **FIND-SKILL19** que el grep no veía. El ⛔ sólo fue legítimo tras abrir.
- **15·storage**: se leyeron los archivos ENORMES íntegros (5105/1817/793/770) **pero** se difirió `settings/settings.ts`
  (1015) como "sin mapear" y se describió `outputsScanner.ts` (126) citando sus funciones **sin abrirlos**. Al
  abrirlos (re-audit): **FIND-STOR13** (cascada de settings 4+ niveles + invariante de seguridad `project`-excluido)
  y el skip-symlink/TOCTOU de STOR10. **Corolario**: leer los monstruos 1→EOF es necesario pero **NO suficiente** —
  la superficialidad migra a los satélites pequeños marcados por título; la puerta ("cada archivo abierto antes de
  clasificar") aplica al árbol ENTERO, no sólo al archivo grande.

Relacionadas: [[00-falsa-economia-del-rigor]] · [[01-exhaustividad-lectura-integra]] · [[03-ledger-honesto-y-puerta-de-cierre]]
