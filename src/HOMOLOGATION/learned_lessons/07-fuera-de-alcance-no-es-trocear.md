# 07 · "Fuera de alcance" ≠ trocear un archivo in-scope

> **Regla.** Declarar un archivo **"fuera de alcance"** (sacarlo del ledger) es legítimo **SÓLO** para
> archivos-satélite **ENTEROS** que pertenecen a **OTRO subsistema numerado concreto** (01-18). Es **PROHIBIDO**
> usar esa cláusula para **trocear** un archivo que **ES** del subsistema actual en "núcleo + resto→a otro sitio".
> Un archivo in-scope se lee **ENTERO ahora**.

> **Sin escotilla (vacío que cierra).** El atajo que esta regla bloquea es reinterpretar "fuera de alcance" para
> leer sólo el núcleo de un tool/archivo del subsistema actual y mandar "el resto" a un subsistema futuro **que no
> existe**. **No hay ningún subsistema de los 11-18 donde "continúe" el resto de un archivo del subsistema actual
> — este es su único hogar.** Trocear un in-scope es *diferir trabajo a ningún sitio* = [[00-falsa-economia-del-rigor]]
> aplicada al alcance. La regla NO admite versión relajada: "fuera de alcance" nombra siempre un subsistema
> numerado concreto, o no es fuera de alcance.

## Por qué — el test mental (obligatorio antes de declarar algo fuera de alcance)
*"¿Este archivo **ENTERO** se audita en un subsistema numerado **concreto** de los que faltan?"*
- Sí, y nombro cuál (p.ej. `bashPermissions.ts`→GAP-02, `spawnMultiAgent.ts`→05, tools MCP→11) → fuera de alcance, sale del ledger.
- "No, es este mismo subsistema" (aunque sólo me interese una parte) → se lee **ENTERO ahora**.

## Modo de fallo típico
- Declarar "BashTool: núcleo auditado, el resto fuera de alcance" sin nombrar qué subsistema audita "el resto".
- Usar la cláusula legítima (satélites enteros) como coartada para **trocear** un in-scope.
- Leer sólo las funciones "interesantes" de un tool nativo y dar el archivo por cubierto.

## Puerta / check
- [ ] Todo archivo marcado "fuera de alcance" **nombra el subsistema numerado concreto** que lo audita **entero**.
- [ ] **Ningún archivo in-scope** se troceó en "núcleo + resto"; los in-scope se leen 1→EOF.
- [ ] El test mental se aplicó y su resultado quedó registrado en el ledger.
- [ ] Un archivo parcial-leído **no** cuenta como íntegro: o entero, o satélite-de-otro-subsistema.

## Evidencia
- **10·tools-native** (reproche del usuario): `BashTool.tsx`/`FileReadTool.ts`/`utils/tasks.ts` se trocearon como
  "núcleo + resto". Al releerlos **ÍNTEGROS** aparecieron A3b (números de línea), A3c (device-guard: leer
  `/dev/zero` colgaría) + binarios, A3d/B9 (dedup/sed-edit-readState), B10 (onProgress), B11 (preventCwd), B12
  (interpretCommandResult) — todo escondido en "el resto" que se iba a diferir a ningún sitio.

Relacionadas: [[00-falsa-economia-del-rigor]] · [[01-exhaustividad-lectura-integra]] · [[08-superficialidad-en-el-archivo-mas-grande]]
