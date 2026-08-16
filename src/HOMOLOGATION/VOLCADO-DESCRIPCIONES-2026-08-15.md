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
| 16 | `EnterWorktree` | `EnterWorktreeTool/prompt.ts:2-26` | FIEL | **W1 abierto** (lado `execute`), § 4ter |
| 17 | `ExitWorktree` | `ExitWorktreeTool/prompt.ts:2-31` | FIEL | **W2 PAGADO**, § 4ter |
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

### Medición de `EDIT-1` bajo el criterio de `D-25` (2026-08-15)

Ocho rondas, enunciado neutral —«en calc.py cambia el nombre de la variable alpha por total»—,
`gpt-5.4-mini`, workspace y `state-dir` nuevos por ronda. Son corridas `--print`: **observación, no
aval de cierre** (`D-24`).

| | rondas |
|---|---|
| `Edit` con `replace_all=true` | 7 |
| `Edit` con sustitución del bloque entero | 1 |
| `Edit` no usada | **0** |
| `bash` haciendo el trabajo de la tool | **0** (única aparición: un `pwd` de orientación) |

Los 8 ficheros quedaron correctos. `replace_all` se ejerce en vivo y con el argumento explícito, que
es el DELATOR que `D-24 §3` exige: no existía antes de este pago, así que ninguna respuesta de
memoria podía exhibirlo.

**Corrección de la primera lectura de esta misma medición.** Se reportó «4 rondas perdidas por
delegación en `Agent`» mirando sólo la sesión padre. Con la traza del subagente leída —clave
`tool_calls`, no bloques en `content`— las cuatro delegadas también usaron `Edit` con `replace_all`.
No hubo pérdida: hubo un instrumento que no leía donde estaba el dato. Es lo que fija `D-25 §4`.

Sigue en pie, como observación y sin ser criterio: la mitad de las rondas delega un renombrado de
una línea, y una de ellas anidó `Agent` dentro de `Agent` (`P12`).

---

## 4ter. `W2` / `FIND-WT4` — PAGADO (2026-08-15)

La fila 17 decía FIEL y era cierto del TEXTO. El hueco estaba debajo: la descripción prometía
una guarda que el `execute` no tenía. B miraba `git status --porcelain` y sólo bloqueaba si la
salida era no vacía **y** `rc == 0`; A (`ExitWorktreeTool.ts:79-113`) cuenta dos cosas y falla
CERRADO si no puede contar ninguna.

Lo construido, contra `ExitWorktreeTool.ts` leído 1→EOF:

- `EnterWorktreeTool.execute` guarda `original_head` (`git rev-parse HEAD` sobre la raíz) en el
  depósito de sesión. Sin línea base no hay forma de contar commits, y era lo que faltaba.
- `_count_worktree_changes`, homólogo de `countWorktreeChanges`: devuelve
  `(ficheros, commits)` o **`None` = no verificable**. Los `None` son el contrato, no un
  atajo: cualquier `rc != 0` y la ausencia de línea base los producen.
- `_run_no_throw` — `run_argv` de B LANZA cuando el `cwd` no existe, mientras `execFileNoThrow`
  de A no lanza nunca. Sin esta capa el fallo salía por traceback en vez de por la guarda.
- La guarda de `remove` pasa a fail-closed, con los mensajes de A: el que enumera
  (`:198`) y el de no-verificable (`:217`), ambos diciendo cómo salir.
- `keep` y el no-op sin sesión toman también los literales de A (`:185`, `:299-309`).

### Acreditación por efecto y contraste (`D-12`)

Sonda con `ConfinedFilesystem` + `LocalExecEnvironment` reales, corrida dos veces: contra el
árbol de trabajo y contra un worktree separado en `HEAD` (`sha256` del módulo previo
`e4fc2202…`), sin revertir nada.

| escenario | ANTES (`HEAD`) | DESPUÉS |
|---|---|---|
| 1 fichero sin commitear | bloquea | bloquea, y **enumera**: `Worktree has 1 uncommitted file…` |
| 1 commit, árbol LIMPIO | **NO bloquea — worktree borrado, commit perdido** | `Worktree has 1 commit on worktree/x…` |
| `git status` con `rc != 0` | **NO bloquea (fail-open)** | `Could not verify worktree state at …` |

Los dos escenarios que el paso construye salen ROJOS antes: la capa no está sin acreditar.
Una primera versión del tercer escenario (borrar el `.git` del worktree) no discriminaba —
`git status` sube al repo padre y devuelve `rc == 0`—; se rehízo con un `cwd` fuera de todo
repo, que es donde `git status` falla de verdad.

Nueve escenarios más (limpio, `discard_changes: true` con su nota `Discarded …`, `keep`,
no-op sin sesión, ausencia de línea base) se comportan como A.

### Pasada orgánica (`D-24`), no buscada

En la tanda `wt2` (8 rondas, enunciado explícito de worktree, `--print`) la ronda 8 ejerció la
guarda en vivo: un subagente editó sin commitear, el padre pidió `remove`, y la tool rehusó
enumerando — `Worktree has 1 uncommitted file…`. Es el escenario B de la tabla de arriba
ocurriendo solo: antes de este paso ese `remove` habría borrado el worktree con el trabajo
dentro. La tanda está contaminada (arrancó antes de la inyección), y por eso NO se usa para
medir elección de tool; este dato es de conducta de la guarda, que es lo único que aquí se
acredita.

### Lo que NO se portó, y por qué

El bullet de cachés de `ExitWorktreeTool/prompt.ts:28` queda fuera **por `D-26`**: B no tiene
ninguna de las tres cachés dependientes del cwd que la frase anuncia (system prompt horneado
en `build_runtime` = `FIND-CFG-HOT`; memoria no cableada = `FIND-MEM-WIRING`; y
`plan_file.py:52` es función pura con token fijo de sesión). Portarla anunciaría una palanca
inexistente (`FIND-E11-3`). La carencia se declara en `PROCEDENCIA-DESCRIPCIONES.md`, no se
rotula como portada.

### `FIND-WT5` — el cierre no llega al subagente (abierto, siguiente paso)

Misma tanda, recuento de las 8 rondas por traza (`tool_calls` del padre y de los subagentes):

| tool | rondas en que aparece (de 8) |
|---|---|
| `read_file` / `Edit` / `glob` | 8 |
| `EnterWorktree` | 6 |
| `Agent` | 5 |
| `bash` | 5 |
| **`ExitWorktree`** | **1** |

`ws-4`, `ws-5`, `ws-6` y `ws-8` conservan su `.worktrees/…`: seis rondas entran y una sale.
La ronda 8 da el texto que lo explica, dicho por el propio subagente al que se le encargó el
cierre: «I don't have a dedicated worktree-exit tool in the available session tools, so I
can't safely remove it through the requested mechanism.» El padre sí pudo llamarla acto
seguido.

Es la misma forma del fallo reportado para `ExitPlanMode`, y ambas tools son `deferred=True`.
La causa NO se declara aquí: exige leer el pool que hereda la fork y el anuncio de diferidas
antes de nombrarla. Queda como el paso siguiente.

Nota de método: la tanda arrancó ANTES de la inyección de `W2` y la descripción cambió a
mitad, así que las rondas 1–2 y 3–8 no son comparables entre sí. El `1 de 8` de
`ExitWorktree` se sostiene a ambos lados del corte; **nada más de esta tanda se usa para
atribuir efecto a un texto**.

### `W1` — PAGADO (2026-08-15), y era dos huecos, no uno

Leído `agentic_code/src/agentic_code/composition.py` 1→EOF: **nadie consumía `_WORKTREE_KEY`**
y el modifier de `EnterWorktree` no tocaba `ctx.cwd`. «Switches the session's working
directory to the new worktree» y «Restores the session's working directory to where it was
before EnterWorktree» eran promesas sin conducta detrás.

Al buscar el homólogo apareció el segundo hueco, que es el que explica `FIND-WT5`. En A el
cwd es del PROCESO: `EnterWorktreeTool.ts:94-96` hace `process.chdir()` + `setCwd()` +
`setOriginalCwd()`, así que **cualquier subagente de A está dentro del worktree por
construcción**. En B el cwd viaja por el ctx, y el ctx del hijo no lo llevaba:
`RuntimeContextForker.fork` no lo copiaba, y `root_context_modifier` sólo corre en la raíz
(`local/runtime.py:474`). Un subagente despachado desde un worktree trabajaba siempre en la
raíz del confinamiento — que es exactamente lo que se vio en la tanda `wt2`, con el hijo
creando su worktree por `bash` fuera de sitio.

Lo construido:

- `worktree.py` — `c.cwd = str(worktree_path)` al entrar; `c.cwd = root` en los DOS caminos
  de salida (`keep` y `remove`). Homólogo de `setCwd`/`setOriginalCwd`.
- `execution/fork/__init__.py` — `ForkSnapshot.cwd` y su propagación al ctx del hijo.
- `tools/native/agent.py` — el snapshot se puebla con `ctx.cwd`.

`WorkspaceCwd` (`composition.py:44-74`) ya persiste `ctx.cwd` entre turnos, así que el
integrador no necesita cambio: el worktree sobrevive al turno igual que el `cd` de `bash`.

Acreditación por contraste (sonda con `EnterWorktree`/`ExitWorktree`/`AgentTool` reales y un
runner falso que captura el `SubagentSpec`), contra el árbol y contra `HEAD`:

| | ANTES (`HEAD`) | DESPUÉS |
|---|---|---|
| `cwd` dentro del worktree tras `EnterWorktree` | **False** | True |
| `cwd` restaurado tras `ExitWorktree` (`keep` y `remove`) | **False** — queda apuntando al worktree, que en `remove` ya no existe | True |
| `ForkSnapshot` lleva el `cwd` del padre | **el campo no existía** | sí |
| el ctx del subagente hereda `cwd` | **None** | sí |

La primera versión de la fila 2 no medía: sin `cd` intermedio, «restaurado» sale cierto por
trivialidad cuando el cwd nunca cambió. Se rehízo fijando el cwd al worktree antes de salir.

### `FIND-WT5` — causa establecida por lectura

`agent_loop.py:191-194` elige `mode = "background" if ctx.is_subagent else "foreground"` y
`registry.py:33-34` filtra ese modo por `safe_for_background`. `EnterWorktree` y
`ExitWorktree` lo tienen en `False`, luego **el subagente no recibe esas tools**, y por eso
dijo lo que dijo. Eso NO se cambia: son estado de sesión del hilo principal, y un hijo que
pudiera borrar el worktree del padre sería el defecto, no el remedio. Lo que sí era defecto
—que el hijo ni siquiera trabajara DENTRO del worktree— queda pagado arriba con `W1`.

`ExitPlanMode` comparte forma (`deferred=True`, `safe_for_background=False`, más
`is_enabled() -> self._interactive` y una `check_permissions` que deniega sin plan mode o sin
fichero de plan, `plan_mode.py:214-234`). **No se toca en este paso**: su fallo se reportó en
el hilo principal, donde el filtro de subagente no aplica, así que la causa es otra y exige
su propia medición.

---

## 4quater. Pasada orgánica posterior a `W1` (`exp-wt3`, 3 rondas, gpt-5.4-mini)

Enunciado idéntico en las tres: *«trabaja en un worktree: crea el worktree, edita ahí calc.py
para que imprima el doble de alpha, y cuando termines sal del worktree eliminándolo.»*

| ronda | padre | hijos | ¿`ExitWorktree`? |
|---|---|---|---|
| 1 | `Agent`x1 `EnterWorktree`x1 `glob`x1 `read_file`x2 `Edit`x1 `bash`x7 | `glob`x1 `read_file`x2 `Edit`x1 `bash`x3 | no — borró con `bash git worktree remove` |
| 2 | `EnterWorktree`x1 `Agent`x5 `glob`x1 `read_file`x8 `Edit`x2 `bash`x5 | `glob`x2 `read_file`x4 `TaskList`x1 | no — ídem |
| 3 | `Agent`x2 `read_file`x1 `Edit`x2 | `Agent`x1 `glob`x1 `read_file`x1 `bash`x2 | no — ni siquiera hubo `EnterWorktree` |

`ExitWorktree`: **0 de 3**. `W1` pagó el cwd del fork; no pagó —ni pretendía— que el modelo
elija la tool. El cierre sigue perdiéndolo contra `bash`, que es el hallazgo de partida y
sigue abierto.

Ronda 3 es `FIND-WT5` en estado puro: el padre delegó el ciclo entero a subagentes, y el de
salida contestó *«I can't remove or verify the worktree session with the tools available
here.»* El padre lo dio por hecho y nunca llamó a nada.

### `FIND-WT6` — el `cwd` viaja al hijo, pero las fs-tools no lo miran

Ronda 2 gastó 5 `Agent` y 8 `read_file` del padre en un bucle de contradicción: tres hijos
seguidos informaron `print(alpha)` mientras el `calc.py` del worktree ya decía
`print(alpha * 2)`. No es alucinación — leían otro fichero.

Causa establecida por lectura, no por conjetura: `ConfinedFilesystem._base_dir` devuelve
`self._roots[0]` (`tools/fs_env.py:135-136`), y `resolve` expande los relativos contra ese
base fijo (`:170`, `:186`). El `cwd` de la sesión no entra en la resolución en ningún punto,
así que tras `EnterWorktree` un `read_file("calc.py")` abre el de la raíz del workspace. A
expande contra `getCwd()`, que es justo lo que `EnterWorktreeTool.ts:94-96` mueve.

Es además una de las dos causas del coste que se arrastra: el bucle de relecturas que el
usuario describe como *«constantemente se invierte tiempo en el loop repitiendo la misma
tarea»* aquí tiene un origen medido, no una impresión. Se ataca en su propia ventana.

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
