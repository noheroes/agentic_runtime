# VOLCADO DE DESCRIPCIONES — 25 tools nativas

Fecha: 2026-08-15 · Base: `/home/noheroes/python`
Canónico: `claude-code/src/` · B: `agentic_runtime/src/agentic_runtime/tools/native/`

Nada de lo que sigue se ha inyectado. Ningún fuente ha sido tocado.

---

## 0. Qué campo se homologa, y por qué la pregunta estaba abierta

`utils/api.ts:169-178` — `toolToAPISchema()` es el ÚNICO punto por el que un schema de tool
llega a la API, y arma el objeto así:

```ts
base = {
  name: tool.name,
  description: await tool.prompt({ ... }),
  input_schema,
}
```

El campo `description` que recibe el modelo se rellena con **`tool.prompt()`**, no con
`tool.description()`. `description()` es texto de UI/telemetría de A y NO viaja al modelo.

Corolario sobre el diferimiento, que era la duda que bloqueaba el volcado:
`formatDeferredToolLine(tool) => tool.name` (`ToolSearchTool/prompt.ts`) — el anuncio de
diferidas lleva **sólo nombres**. El `searchHint` no se renderiza (A/B `exp_xenhnnmn0smrx4`,
parado el 21-mar, sin beneficio). Cuando ToolSearch acierta, devuelve bloques
`tool_reference` que la API expande al schema COMPLETO. Es decir: diferir esconde el schema
un rato, nunca recorta el cuerpo. **El texto que el modelo acaba leyendo es íntegro.**

Dos consecuencias que gobiernan el resto del documento:

1. Un hueco en `search_hint` es un problema de RECUPERABILIDAD, no de descripción.
2. `E11` corrió con `anunciadas=24` y las descripciones enteras delante. El modelo vio todos
   los cuerpos y aun así eligió `bash`. **Las pérdidas de `E11` son problema de CONTENIDO**,
   que es exactamente lo que este volcado mide.

---

## 1. Corrección de lo que informé antes

Dije que quedaban ~17 tools sin tocar por la campaña anterior. **Era falso.** Leídos los
fuentes: `glob`, `grep`, `read_file`, `write_file`, `Agent`, las seis `Task*`, `Sleep`,
`WebSearch`, `WebFetch`, `ToolSearch`, `EnterWorktree`, `ExitWorktree` y `TodoWrite` llevan
todas nota `GAP-PROMPT-1` citando `utils/api.ts:169-178`. La campaña anterior sabía cuál era
el campo bueno y trabajó mucho más de lo que el defecto de `TodoWrite` sugería.

También retiro, por no verificada, la frase «donde se copió la corta, se copió el campo
equivocado». No la sostiene ningún fuente. Lo verificado es otra cosa, y peor de localizar:
hay descripciones **truncadas a mitad** con la nota de cabecera afirmando el rango completo.

**Segunda corrección, hecha al ejecutar.** Marqué «SIN NOTA» a `bash`, `Config`,
`EnterPlanMode` y `ExitPlanMode`. Es falso: su procedencia existe, en
`PROCEDENCIA-DESCRIPCIONES.md`. Se movió allí en `ff30127`, cuando el barrido de comentarios
se llevó las notas del fuente — y se movió **al sitio que la regla manda**, el censo y no el
código. Además está medida: `test_la_omision_esta_declarada_y_no_meramente_hecha` exige fila
con cita `FICHERO:LÍNEA` y columna de omisiones no vacía. Las cuatro filas de la tabla del
§ 2 marcadas SIN NOTA quedan **anuladas**; los defectos reales son los tres DIVERGENTE.
Lo que sí faltaba era la fila de `Edit`, y es parte del pago de `EDIT-1`.

---

## 2. Censo, 25 filas

Leyenda: **FIEL** = porta el cuerpo canónico con las omisiones declaradas en la nota ·
**DIVERGENTE** = falta texto canónico portante, o la nota miente · **SIN NOTA** = el texto
está bien pero la homologación no está declarada · **SIN CANÓNICO** = A no tiene la tool.

| # | Tool | Fuente A | Veredicto | Hallazgo |
|---|------|----------|-----------|----------|
| 1 | `bash` | `BashTool/prompt.ts` | SIN NOTA | § 3.1 |
| 2 | `glob` | `GlobTool/prompt.ts:3-7` | FIEL | — |
| 3 | `grep` | `GrepTool/prompt.ts:7-17` | FIEL | — |
| 4 | `read_file` | `FileReadTool/prompt.ts:32-48` | FIEL | § 4.1 (rama resuelta) |
| 5 | `write_file` | `FileWriteTool/prompt.ts:10-18` | FIEL | carencia pre-read declarada |
| 6 | `Edit` | `FileEditTool/prompt.ts:20-27` | **DIVERGENTE** | **EDIT-1**, § 3.2 |
| 7 | `TodoWrite` | `TodoWriteTool/prompt.ts:3-181` | **DIVERGENTE** | **T1**, § 3.3 |
| 8 | `Agent` | `AgentTool/prompt.ts:66-287` | FIEL | — |
| 9 | `ToolSearch` | `ToolSearchTool/prompt.ts:27-51` | FIEL | — |
| 10 | `WebFetch` | `WebFetchTool/prompt.ts:3-21` | FIEL | `GAP-WEBFETCH-2` en pie |
| 11 | `WebSearch` | `WebSearchTool/prompt.ts:5-33` | FIEL | — |
| 12 | `Sleep` | `SleepTool/prompt.ts:7-17` | FIEL | — |
| 13 | `AskUserQuestion` | `AskUserQuestionTool/prompt.ts:32-44` + `:10-30` | **DIVERGENTE** | **AUQ-1**, § 3.4 |
| 14 | `EnterPlanMode` | `EnterPlanModeTool/prompt.ts:16-99` | SIN NOTA | § 3.5 |
| 15 | `ExitPlanMode` | `ExitPlanModeTool/prompt.ts:5-29` | SIN NOTA | § 3.5 |
| 16 | `EnterWorktree` | `EnterWorktreeTool/prompt.ts:2-26` | FIEL | W1 (lado `execute`) |
| 17 | `ExitWorktree` | `ExitWorktreeTool/prompt.ts:2-31` | FIEL | W2 (lado `execute`) |
| 18 | `Config` | `ConfigTool` (generada) | SIN NOTA | § 3.6 |
| 19 | `clone_repository` | — | SIN CANÓNICO | § 3.7 |
| 20 | `TaskCreate` | `TaskCreateTool/prompt.ts` | FIEL | — |
| 21 | `TaskGet` | `TaskGetTool/prompt.ts` | FIEL | — |
| 22 | `TaskList` | `TaskListTool/prompt.ts` | FIEL | schema vacío, per A |
| 23 | `TaskUpdate` | `TaskUpdateTool/prompt.ts` | FIEL | `FIND-TASK-1` en pie |
| 24 | `TaskStop` | `TaskStopTool/prompt.ts` (`DESCRIPTION`) | FIEL | § 4.2 (rama resuelta) |
| 25 | `TaskOutput` | `TaskOutputTool.tsx:172-182` | FIEL | — |

Recuento: **3 DIVERGENTE · 4 SIN NOTA · 17 FIEL · 1 SIN CANÓNICO**.

---

## 3. Hallazgos

### 3.1 `bash` — SIN NOTA, y es la fila que explica `E11`

`bash.py:18-181`: **164 líneas** de descripción. Es la más larga del árbol con diferencia.
Porta el prompt canónico de A casi entero —secciones de git, de commit, de PR, de `gh`— y
además añade material propio de B que A no tiene, incluido el párrafo contra usar
intérpretes (`python -c`, heredocs) para trabajo de ficheros.

No lleva nota de homologación ni declara qué es de A y qué es de B.

Puesta al lado del resto, la asimetría es el hallazgo central de este volcado:

| tool | líneas de descripción | resultado en `E11` |
|------|----------------------|--------------------|
| `bash` | 164 | **gana los 4 escenarios perdidos** |
| `TodoWrite` | 62 (de ~178 en A) | perdió → `Agent` |
| `WebFetch` | 18 | perdió → `bash` |
| `Edit` | 11 (de 8 bullets en A) | perdió → `bash` |

El desequilibrio no está en gpt-5.x: está en nuestro repo. Al modelo se le dio un manual de
`bash` y una nota de `Edit`. Eligió lo que estaba escrito para ser elegido.

### 3.2 EDIT-1 — `Edit` pierde `replace_all` entero, sin declarar

A (`FileEditTool/prompt.ts:20-27`) tiene 8 bullets. B (`file_edit.py:34-44`) tiene 4, sin
nota alguna. Falta texto canónico portante:

- `getPreReadInstruction()` (`:5`): «You must use your `Read` tool at least once in the
  conversation before editing. This tool will error if you attempt an edit without reading
  the file.» — B no lo enforcea (no hay `readFileState`), así que la línea no puede
  copiarse tal cual; es la misma carencia ya declarada en `write_file`, pero aquí ni
  siquiera está declarada.
- `:26` (segunda mitad): «…or use `replace_all` to change every instance of `old_string`.»
- `:27`: «Use `replace_all` for replacing and renaming strings across the file. This
  parameter is useful if you want to rename a variable for instance.»

Las dos últimas no son omisiones de redacción: **el esquema de B no tiene `replace_all`**
(`file_edit.py:45-62`). Una tool que no puede renombrar en bloque obliga al modelo a N
llamadas o a irse a `sed`. Es lo que hizo en `E11`. Candidata `D-22` de manual: lo que no
está SE CREA. Construir `replace_all` es lo que habilita portar los dos bullets.

### 3.3 T1 — `TodoWrite`: la nota afirma un rango que el texto no cubre

`todo_write.py:36` dice «Homologada contra `TodoWriteTool/prompt.ts:3-181`». El texto de B
termina en `todo_write.py:104` y **no contiene el bloque `## Examples`** del canónico
—los ejemplos con `<example>`/`<reasoning>` que ocupan el grueso de esas 181 líneas y que
son la parte que enseña al modelo CUÁNDO llamar. La nota certifica un trabajo que no está
hecho: esto es lo que el encargo llamó «sellado incompleto en un commit».

Aparte, en pie y ya declaradas: `priority` (invención de B que A no tiene, `L10`) y `T2`
(`execute` devuelve un blob JSON `{old_todos,new_todos}` donde A devuelve una frase).

### 3.4 AUQ-1 — `AskUserQuestion` promete una sección que no existe

`ask_user.py` porta `ASK_USER_QUESTION_TOOL_PROMPT` (`prompt.ts:32-44`) pero **no porta
`PREVIEW_FEATURE_PROMPT` (`prompt.ts:10-30`)**, que es donde A explica el formato del
campo `preview`. En A eso lo decide `AskUserQuestionTool.tsx:117-125`: si
`getQuestionPreviewFormat()` está definido, el cuerpo se concatena.

El problema es que el esquema de B **sí** expone `preview`, y su propio `description` de
campo dice «See the tool description for the expected content format» — apuntando a una
sección que B no incluye. El modelo recibe un puntero roto.

Sin nota de homologación tampoco.

### 3.5 `EnterPlanMode` / `ExitPlanMode` — SIN NOTA

`plan_mode.py:*`: los dos textos son ports fieles de la rama externa de A
(`getEnterPlanModeToolPromptExternal()`, `EXIT_PLAN_MODE_V2_TOOL_PROMPT`), con los nombres
de tool localizados a `glob`/`grep`/`read_file`. El contenido está bien; lo que falta es la
declaración: qué rama se eligió (externa vs `…Ant()`), y que `WHAT_HAPPENS_SECTION`
(`:4-14`) queda fuera por colgar de `isPlanModeInterviewPhaseEnabled()`.

### 3.6 `Config` — SIN NOTA, sin hueco

`config.py:115-157`: la descripción se GENERA del registro
(`generate_description(registry)`), igual que A. Estructura homóloga —encabezado, `## Usage`,
listado por fuente, `## Examples`—. No hay hueco de contenido; falta sólo la nota.

### 3.7 `clone_repository` — SIN CANÓNICO

A no tiene tool de clone (clona por `bash` con red y credenciales del host). B la tiene por
necesidad: su `bash` corre en `BwrapExecEnvironment` con `--unshare-all`, sin red. La
divergencia está declarada extensamente en la cabecera del módulo
(`clone_repository.py:1-20`). En `E11` es la ÚNICA de las once que el modelo condujo bien,
y su descripción son 4 líneas propias.

Se anota aquí de paso: el párrafo `FIND-CFG-3` del censo de guardas sigue listando
`clonar-repo` entre las pérdidas de `bash`. **La traza lo da en verde** (`✔ clonar-repo →
condujo ['clone_repository']`). El párrafo hay que corregirlo.

---

## 4. Ramas del canónico que quedaban por resolver, resueltas

### 4.1 `Read` — qué argumentos pasa A a `renderPromptTemplate`

`FileReadTool.ts:347-360` los computa de `getDefaultFileReadingLimits()`. En `limits.ts:76-85`
tanto `includeMaxSizeInPrompt` como `targetedRangeNudge` salen **`undefined`** por defecto
(sólo los puebla el override de growthbook `tengu_amber_wren`). Por tanto la rama de A por
defecto es:

- `maxSizeInstruction = ''` (cadena vacía)
- `offsetInstruction = OFFSET_INSTRUCTION_DEFAULT` — «You can optionally specify a line
  offset and limit …, but it's recommended to read the whole file by not providing these
  parameters»

Que es exactamente la rama contra la que se homologó `read_file.py`. Fila cerrada.

### 4.2 `TaskStop` — su `prompt()`

`TaskStopTool.ts:95-97`: `async prompt() { return DESCRIPTION }`, con `DESCRIPTION` el de
`prompt.ts` (8 líneas). El `description()` de `:92-94` («Stop a running background task by
ID») es el que NO viaja. Fila cerrada, y confirma de nuevo el § 0.

---

## 4bis. `EDIT-1` — PAGADO (2026-08-15)

Lo construido, no lo rotulado:

- `edit_text.py` — `apply_edit_to_file`/`apply_edit` toman `replace_all`, calcados de
  `applyEditToFile` (`FileEditTool/utils.ts:206-228`), incluida la rama de borrado que se
  come el salto sobrante. `count = -1 if replace_all else 1` es el homólogo exacto del
  `replaceAll` vs `replace` de A.
- `file_edit.py` — `replace_all` en el esquema con la glosa literal de A
  (`types.ts:15-17`); el error de multi-match pasa a ser el de A (`FileEditTool.ts:336`),
  que **dice cómo salir** en vez de sólo negar; descripción portada de
  `getDefaultEditDescription()`, rama no-Ant.
- `PROCEDENCIA-DESCRIPCIONES.md` — fila de `Edit` con canónico, adaptaciones y la carencia
  de pre-lectura declarada.
- `FIND-NATIVE-READ/A6` deja de ser `xfail(strict)`: pasó a XPASS al construirse el
  parámetro. La deuda estaba declarada desde antes y ahora está pagada, no rotulada.
- Tres tests nuevos en `test_tool_descriptions_homologation.py`: que el texto y el esquema
  van juntos, que la sustitución múltiple ocurre **en disco**, y que la descripción NO
  promete la guarda de pre-lectura que B no enforcea.

Suite: verde salvo `test_storage_lifecycle::test_the_event_loop_closes_after_persisting_a_
session`, roja de antes y ajena a este cambio. `agentic_code`: 219 pasados.

Falta la pasada orgánica (`D-24`), que es lo siguiente.

---

## 5. Qué queda, y en qué orden

Certificar el volcado exige cerrar tres filas DIVERGENTE y cuatro SIN NOTA. Orden propuesto,
de mayor a menor efecto sobre el desequilibrio medido en `E11`:

1. **EDIT-1** — construir `replace_all` (`D-22`) y portar los bullets `:26`-`:27`; declarar
   la carencia de pre-read como en `write_file`.
2. **T1** — portar el bloque `## Examples` de `TodoWriteTool/prompt.ts`, o corregir la nota
   para que diga la verdad sobre el rango. Lo primero; lo segundo sería rotular en vez de
   pagar (`declarar-no-es-pagar`).
3. **AUQ-1** — portar `PREVIEW_FEATURE_PROMPT`, o retirar `preview` del esquema. Un puntero
   roto no se deja.
4. **§ 3.1 `bash`** — declarar qué es de A y qué es de B. No se recorta: se declara.
5. **SIN NOTA** — `EnterPlanMode`, `ExitPlanMode`, `Config`.
6. Corregir el párrafo `FIND-CFG-3` del censo de guardas (`clonar-repo` está en verde).

Cada punto, una ventana. Y ninguno se acredita cerrado sin pasada orgánica (`D-24`).
