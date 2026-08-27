# Censo de guardas — contraste 25 tools + `skills` + `mcp` contra el canónico

**Fecha:** 2026-08-09. **Estado:** censo CERRADO, ejecución ABIERTA.
**Base:** `/home/noheroes/python`. Canónico: `claude-code/src/`. Nuestro: `agentic_runtime/src/agentic_runtime/`.

Este documento existe para que los hallazgos sobrevivan a un `/clear`. Nada de lo que
aquí se lista está aplicado. **No se ha tocado ningún fuente ni se ha hecho commit.**

---

## 0. Cómo se llegó aquí

La homologación se detuvo por intuición de que estaba mal hecha (n iteraciones que
arrastraban problemas sin subsanar). Se decidió ejercitar `agentic_code` de verdad para
descubrirlo con evidencia. El gate `E11` falló en `worktree-ida-y-vuelta` y
`registrar-plan`; al contrastar en vez de parchar, el fallo resultó no ser de prompt sino
estructural, y el barrido posterior lo generalizó.

**Conclusión del censo, en una línea:** el port fue *selectivo*, no uniformemente
superficial. Donde la guarda vivía sola dentro de la tool, se portó (a veces con exceso).
Donde la guarda **depende de un depósito de estado de sesión que no construimos**, se
resolvió **borrando la frase de la descripción en vez de construir el depósito**.
`bash` es el caso aparte: ahí no falta un depósito, falta el módulo entero.

---

## 1. La cuenta

- A tiene **40** directorios de tool en `src/tools/` (42 menos `shared/` y `testing/`).
- Nosotros tenemos **25** tools nativas. **24** mapean a una de A; `clone_repository` es
  nuestra y A no la tiene.
- **40 − 24 = 16** tools de A que no están en `native/`.
  - Cubiertas fuera de `native/` (**4**): `SkillTool` → `capabilities/skills/skill_tool.py`;
    `ListMcpResourcesTool` y `ReadMcpResourceTool` → `capabilities/mcp/resource_tools.py:16,47`;
    `MCPTool` → `capabilities/mcp/tool_adapter.py:103`.
  - **Genuinamente ausentes (12):** `BriefTool`, `LSPTool`, `McpAuthTool` (nuestro
    `capabilities/mcp/auth.py` es helper, no tool), `NotebookEditTool`, `PowerShellTool`,
    `REPLTool`, `RemoteTriggerTool`, `ScheduleCronTool`, `SendMessageTool`,
    `SyntheticOutputTool`, `TeamCreateTool`, `TeamDeleteTool`.

> Corrección registrada: en la ventana anterior dije «13 ausentes». Era mío y estaba mal.
> La cifra buena es 16, de las que 12 son ausencia real.

**Nota de método que costó el hallazgo:** filtrar por `validateInput` deja fuera la mitad.
A pone guardas en `validateInput` **y** en `call()`. Las de `call()` son justo las que
faltaban en el barrido inicial.

**Defecto de esquema de este censo (hallado al abrir el paso 3, 2026-08-10).** El formulario
censa *guardas* —superficie de rechazo—, así que hay tres clases de divergencia que **no
puede ver por construcción**, y las tres aparecieron en la primera fila que se abrió a fondo:

1. **Conducta del camino de éxito.** Lo que A hace *cuando el edit procede* no es una guarda y
   no está en ninguna fila. En `FIND-EDIT` faltaban cuatro divergencias reales de esta clase
   (borrado que arrastra el `\n`, `old_string` vacío que sustituye el contenido entero,
   escritura atómica que preserva modo y sigue symlinks, re-aplicación del estilo de comillas).
2. **¿Existe en B lo que la guarda protege?** — **DEROGADA COMO FILTRO DE ALCANCE, `D-22`
   (2026-08-10).** Palabra del usuario: *«agentic_runtime es un proyecto en fase de homologacion,
   lo que no este se crea si con esto se consigue precisamente esto, homologar comportamiento,
   algoritmo, etc de canonico. por tanto no cabria la pregunta si existe o no en B.»*
   La pregunta se sigue haciendo —dice **cuánto** hay que construir y **en qué capa**— pero su
   respuesta «no existe» **ya no autoriza a saltar la fila**, y el rótulo «sin referente en B»
   queda **prohibido como cierre**: se sustituye por «falta construir X». Lo que reabre está
   listado en `D-22` y marcado fila por fila más abajo. Enunciado original, para que se vea qué
   se derogó: *«el censo cuenta guardas de A sin comprobar que su referente exista aquí; dos de
   las ocho de `FIND-EDIT` no lo tienen (`checkTeamMemSecrets`, `.ipynb`) y estaban contadas como
   trabajo portable»* — el defecto de recuento era real, la conclusión de excluirlas no.
   Límite que `D-22` **no** borra: el núcleo sigue siendo genérico y el integrador se adapta a él
   (`architecture-layers`), así que lo que se construye es **mecanismo en `agentic_runtime`**;
   adquirir la *superficie de producto* de A en `agentic_code` (seis paletas de tema, `editorMode`,
   canales de notificación, voz, teammates) no se deduce de aquí y es decisión aparte.
3. **¿Es alcanzable desde `agentic_code`?** Si la conducta no se puede ejercitar en el único
   vehículo de prueba admitido (§4), no se puede certificar. La memoria del runtime es el caso:
   `factory.py:210` sólo registra `MemoryProvider` si el integrador puebla `memory_root` o
   `memory_store`, y `agentic_code/composition.py:235` no puebla ninguno.

**Consecuencia sobre el §3:** el orden de ataque se derivó de estos recuentos, y en la fila
abierta el recuento estaba a la vez **inflado** (dos guardas sin referente) y **corto** (cuatro
conductas ausentes). Las otras once filas no son mejor evidencia que ésta hasta que se abran.
Cada paso, al abrirse, contrasta su fila con estas tres preguntas y **corrige el censo aquí
mismo antes de inyectar**, no después.

---

## 2. Hallazgos, por tool

### `FIND-EDIT` — `Edit` (`tools/native/file_edit.py`) ← `FileEditTool/FileEditTool.ts:137-341`

A: **11** guardas. Nosotros: **4** (absoluta `:65`, confinamiento `:68`, existe `:71`,
unicidad `:79-89`). Ausentes:

| # | Guarda | Canónico | ¿Necesita depósito? |
|---|---|---|---|
| 1 | `old_string === new_string` | `:148` errorCode 1 | no |
| 2 | `checkTeamMemSecrets` | `:144` errorCode 0 | no — **sin referente en B**, ver abajo |
| 3 | deny rule (`toolPermissionContext`) | `:158` errorCode 2 | **sí** |
| 4 | UNC skip (`\\`, `//`) | `:176` | no |
| 5 | tamaño máx. 1 GiB | `:188` errorCode 10 | no |
| 6 | `old_string === ''` ⇒ crear fichero nuevo | `:222` | no |
| 7 | …y su rechazo si ya existe con contenido | `:250` errorCode 3 | no |
| 8 | redirección a `.ipynb` | `:265` errorCode 5 | no — **sin referente en B**, ver abajo |
| 9 | **read-before-edit** | `:275` errorCode 6 | **sí** (`readFileState`) |
| 10 | **stale-read** (`lastWriteTime > readTimestamp`) | `:291` errorCode 7 | **sí** |
| 11 | `validateInputForSettingsFileEdit` | `:343` | no |

Además, **dos divergencias de *matching*** que no son guardas y muerden igual:
- A normaliza **CRLF→LF** y detecta **UTF-16LE** antes de comparar (`:203-214`). Nosotros
  comparamos crudo (`file_edit.py:75`) ⇒ un `Edit` sobre fichero CRLF **falla en el nuestro
  donde en A pasa**. Detalle que faltaba: los finales se detectan sobre los **4096 primeros
  bytes y ANTES** de normalizar (`utils/fileRead.ts:75-98`), `CRLF` sii `crlf > lf`, y se
  **restituyen al escribir** (`utils/file.ts:84-98`). No es sólo cuestión de comparar.
- A usa `findActualString` (normaliza comillas tipográficas); nosotros `content.count()`
  literal (`file_edit.py:79`). Su mitad de escritura, que faltaba: `preserveQuoteStyle`
  (`FileEditTool/utils.ts:104-199`) **re-aplica el estilo del original** al `new_string`, con
  `isOpeningContext` y la regla del apóstrofo entre dos letras.

#### Conducta del camino de éxito que este censo no recogía (hallada en el paso 3)

Ninguna es una guarda; las cuatro son divergencia real y entran en el paso 3:
- **Borrado que arrastra el `\n`** — con `new_string === ''`, A borra `old_string + '\n'` si
  `old_string` no acaba en salto y el fichero contiene esa forma (`utils.ts:206-228`). B deja
  una línea en blanco donde A no la deja.
- **`old_string === ''` SUSTITUYE el contenido entero** (`utils.ts:314-322`). El
  `content.replace("", new, 1)` de Python lo **antepondría**: bug latente de B.
- **Escritura atómica** por temporal + `rename`, siguiendo symlinks y **preservando el modo**
  del destino (`utils/file.ts:362-478`). B hace `write_text` directo: pierde permisos.
- **`getPatchForEdits` falla en firme** si el resultado es idéntico al original o si la cadena
  no aparece (`utils.ts:326`, `:334`), en vez de reportar éxito.

Y cuatro más que aparecieron al releer el canónico entero para inyectar (mismo día, mismo
paso; se anotan aquí porque el orden es **contrastar hasta EOF → corregir el censo → inyectar**):
- **Literal de la guarda de no-encontrado** (`:321`): `String to replace not found in file.\nString: ${old_string}`.
  El nuestro (`file_edit.py:83`) es texto propio y además **no devuelve la cadena buscada**, que
  es justo lo que permite al modelo ver su propio error de espaciado.
- **Resultado que ve el modelo** (`:592`): `The file ${filePath} has been updated successfully.`
  El nuestro dice `Edited {file_path}`. Es conducta observable por el modelo, no cosmética.
- **Literal de multiplicidad** (`:336`) menciona `replace_all`, parámetro que B **no tiene**:
  por `opcion-inexpresable-se-rechaza` se conserva la forma (nº de coincidencias + pedir más
  contexto) **sin ofrecer** la opción inexistente. El recuento sí se homologa: se cuenta sobre
  la cadena REAL (`actualOldString`), no sobre la pedida.
- **Caso especial de fichero vacío** (`:275-294`): `old_string === '' && new_string === ''`
  sobre fichero vacío devuelve `''` sin error.

**ABIERTO, fuera del paso 3 — `FIND-EDIT-NORMALIZE`:** `normalizeFileEditInput`
(`utils.ts:581-657`) recorta blancos finales del `new_string` (salvo `.md`/`.mdx`) y
des-sanea `<fnr>`, `<n>`, `\n\nH:`… antes de aplicar el edit. **No se porta a ciegas**: no he
leído aún quién lo invoca, y sin eso no sé si actúa en toda llamada o sólo en un camino.
Requiere leer su llamador entero antes de decidir.

#### Guardas sin referente en B — **REABIERTAS por `D-22` (2026-08-10)**

El título de esta subsección decía *«no son trabajo pendiente; son trabajo inexistente»*. Es
justo lo que `D-22` deroga: no existir en B no las excluye. **Vuelven al tablero como trabajo**,
con el matiz de capa —lo que se construye es mecanismo del núcleo— y **no dentro del paso 3, que
está cerrado**: entran como pasos propios, dimensionados abajo en el §3. El análisis que sigue
queda íntegro porque sigue siendo cierto en lo que describe; lo que ya no vale es su conclusión.

- **G2 `checkTeamMemSecrets`.** El guard de A está doblemente cerrado sobre memoria de EQUIPO:
  `feature('TEAMMEM')` + `isTeamMemPath` bajo `getAutoMemPath()/team/`
  (`teamMemSecretGuard.ts:1-44`, `memdir/teamMemPaths.ts:214-220`), y su mensaje dice
  *«Team memory is shared with all repository collaborators»*. B no tiene memoria de equipo ni
  sincronización de ninguna clase (`capabilities/memory/store.py`, `provider.py`). Se cae con
  ella `secretScanner.ts` entero (40 reglas), que aquí no protegería nada porque nada sale de
  la máquina. ~~**Vuelve a ser exigible el día que exista memoria compartida.**~~ ⇒ **`D-22`:**
  lo exigible es el **escáner de secretos** (`secretScanner.ts`, 40 reglas), que es algoritmo
  puro y no depende de memoria de equipo; lo que sí depende de ella es sólo **dónde se aplica**
  (`isTeamMemPath`). Se construye el escáner; el predicado de ruta lo aporta quien tenga rutas
  compartidas. Queda como `FIND-EDIT-SECRETS`, ABIERTO, paso propio.
- **G8 `.ipynb`.** A redirige a `NotebookEdit`; B no publica esa tool (`tools/factory.py:51-77`,
  25 nativas, sin notebooks). Rechazar sin ofrecer alternativa quita capacidad en vez de
  protegerla. ~~Lo que queda abierto no es la guarda sino lo de debajo~~ ⇒ **`D-22`:** lo que
  falta es **`NotebookEditTool`**, y se construye; con ella publicada, la guarda de `.ipynb` en
  `Edit` deja de quitar capacidad y pasa a ser exactamente lo que es en A, una redirección. Sigue
  en pie lo de debajo: **`read_file.py:97` lee el notebook como texto plano**, así que el modelo
  edita el JSON a ciegas. Queda como `FIND-NOTEBOOK`, ABIERTO, paso propio (tool nueva + guarda
  de redirección en `Edit` + lectura de notebooks).

#### Alcanzabilidad (tercera pregunta del esquema)

- **G11 tiene referente real y alcanzable**: la única config propia de B que `Edit` puede tocar
  es `.mcp.json` del workspace (`agentic_code/mcp_config.py:41`, `:387`) — `state_dir` cae fuera
  del confinamiento (`composition.py:212-216`), así que `config.json`, `mcp-approvals.json` y
  `managed-mcp.json` son inalcanzables por esta tool. Y el daño que la guarda evita es exacto:
  `read_json_object` (`mcp_config.py:114-126`) lee **tolerante**, de modo que un `.mcp.json`
  roto por un edit se ignora con un `warning` y la config MCP **desaparece en silencio**. El
  predicado y el validador son del INTEGRADOR (el runtime no conoce `.mcp.json`): se siembran
  en `app_state.native` desde `author_root_context`, misma costura que `PlanModeState`
  (`composition.py:88-92`).
- **La memoria del runtime NO es alcanzable desde `agentic_code`** (`factory.py:210` vs
  `composition.py:235`): `MemoryProvider` no se construye en el único vehículo de prueba. Es
  hallazgo ajeno al paso 3 y queda **ABIERTO** — `FIND-MEM-WIRING`.

### `FIND-WRITE` — `write_file` (`tools/native/write_file.py:43-55`) ← `FileWriteTool.ts:159-217`

**Cero guardas.** A tiene 5: secretos (`:159`), deny rule (`:175` errorCode 1), UNC,
**read-before-write** (`:198-204` errorCode 2), **stale-read** (`:211-217` errorCode 3).

`write_file.py:18-19` declara la omisión, pero **solo confiesa la primera** (lectura previa).
Las otras cuatro no están declaradas en ningún sitio. Ejemplo vivo de «declarar no es pagar»
aplicado a medias.

### `FIND-STATE` — el depósito `readFileState` no existe (causa raíz de los dos anteriores)

A **mantiene** ese depósito desde las tres tools de fichero:
`FileReadTool.ts:842,1032` · `FileEditTool.ts:520` · `FileWriteTool.ts:332`.

Y tiene una **segunda guarda TOCTOU dentro de `call()`**, justo antes de escribir: relee y
lanza `FILE_UNEXPECTEDLY_MODIFIED_ERROR` — `FileEditTool.ts:452-465`,
`FileWriteTool.ts:280-292`. No estaba en el censo anterior.

Nosotros no tenemos ese depósito **en absoluto**. Sin él, las guardas 9 y 10 de `Edit` y las
2 de `write_file` son inconstruibles: **hay que decidir el asiento de estado antes**.

### `FIND-BASH` — `bash` (`tools/native/bash.py`, 271 líneas) — **SE DEJA PARA EL FINAL**

A dedica ~10.900 líneas a validar el comando:
`BashTool/bashSecurity.ts` 2592 · `bashPermissions.ts` 2621 · `readOnlyValidation.ts` 1990 ·
`pathValidation.ts` 1303 · `sedValidation.ts` 684.

Nuestro `bash.py` **no inspecciona el comando**: solo exec_env (`:243`) y recuperación de cwd
(`:246`). Lo que sí está bien portado: `_resolve_cwd` (espejo de `Shell.ts:220-238`) y el gate
`is_subagent` sobre la escritura de cwd (`:258`, espejo de `preventCwdChanges`, `Shell.ts:385`).

### `FIND-EXITPLAN` — `ExitPlanMode` (`tools/native/plan_mode.py:254`)

A rechaza si **no estás en plan mode** (`ExitPlanModeTool/ExitPlanModeV2Tool.ts:205-218`,
errorCode 1). Nosotros rechazamos si **no hay plan-file**. Son cosas distintas: el nuestro
deja salir de un plan mode que no existe. Guarda **cambiada de sitio**, no portada.

### `FIND-TODO` — `TodoWrite` (`tools/native/todo_write.py:121-127`)

Cero guardas y **dos conductas perdidas** de `TodoWriteTool.ts:65-69`:
- `todoKey = context.agentId ?? getSessionId()` (`:66`) — nosotros: slot único sin clave.
- `allDone ? [] : todos` (`:69`) — la lista **se vacía** al completarse. Nosotros no.

Es la causa estructural del fallo de `registrar-plan` en `E11`.

### `FIND-CFG-2` — `Config` (`tools/native/config.py`) — **CERRADO (2026-08-13, ver §5)**

**Enunciado anterior (INCOMPLETO, corregido el 2026-08-10 al abrir el paso 4):** *«A valida
contra `SUPPORTED_SETTINGS`; nosotros aceptamos cualquier clave y la guardamos. Ya registrado
en `config.py:24-31`.»* La fila censaba **una** guarda. Contrastado el canónico entero
(`ConfigTool/ConfigTool.ts` 467 · `supportedSettings.ts` 211 · `prompt.ts` 93 · `constants.ts` ·
`UI.tsx`, leídos 1→EOF), la divergencia no es la guarda: es que **la tool entera no hace nada**.

#### Pregunta 1 — conducta del camino de éxito (lo que la fila no podía ver)

La guarda `isSupported` (`:126-130`, `Unknown setting: "${setting}"`) es lo de menos. Lo que A
hace cuando la llamada procede, y B no:

| # | Conducta de A | Canónico | En B |
|---|---|---|---|
| 1 | **GET lee el valor REAL** del almacén (`getValue`: `getGlobalConfig()` o `getInitialSettings()` recorriendo `path`) | `:136-144`, `:436-453` | lee `app_state.native["config"]`, que nace vacío ⇒ **todo GET devuelve `null`** |
| 2 | **SET persiste** (`saveGlobalConfig` / `updateSettingsForSource('userSettings', …)`) | `:313-343` | escribe en un dict per-turno que **nadie lee y que muere con el turno** |
| 3 | `appStateKey` ⇒ sincroniza a AppState para efecto inmediato | `:356-362` | no existe |
| 4 | Coerción booleana de `"true"`/`"false"` y rechazo `${setting} requires true or false.` | `:185-201` | no existe: `"true"` se guarda como cadena |
| 5 | Validación de opciones ⇒ `Invalid value "X". Options: a, b` | `:204-214` | no existe |
| 6 | `validateOnWrite` asíncrono (p. ej. `validateModel`) | `:217-229` | no existe |
| 7 | `formatOnRead` en el GET | `:138-140` | no existe |
| 8 | `buildNestedObject` sobre `path` (`key.split('.')`) ⇒ `permissions.defaultMode` anida | `:208-211`, `:455-467` | clave plana literal |
| 9 | Escritura envuelta en `try/catch` ⇒ el error se devuelve, no revienta | `:400-410` | no hay escritura que pueda fallar |
| 10 | **Lo que ve el modelo**: `${setting} = ${value}` / `Set ${setting} to ${newValue}` / `Error: ${error}` con `is_error: true` | `:412-433` | un blob JSON crudo (`{"operation":"set",…}`) |
| 11 | **`checkPermissions`: el GET se auto-permite, el SET PREGUNTA** (`Set X to Y`) | `:98-107` | `requires_permission = False` para ambos ⇒ **B cambia config sin consentimiento**. **INEXPRESABLE hoy**, ver abajo |
| 12 | `inputSchema` estricto y `value ∈ string\|boolean\|number` | `:36-48` | admite cualquier JSON (objetos, listas) |

Las guardas 11 y 12 son guardas de pleno derecho y **tampoco estaban en el censo**: la fila se
escribió mirando `call()` y no `checkPermissions` ni el esquema.

##### Guarda 11 — inexpresable en el contrato de hoy (corrección, 2026-08-10)

Anunciarla como portable habría sido un error mío. Leído el camino entero de permisos de B:
`ToolProtocol.requires_permission` es **un booleano de clase** (`contracts/tools.py:157`), y el
propio contrato declara `check_permissions` **fuera del tramo 1** (`:4-6`). El dispatcher lo usa
como lista blanca por nombre (`tools/dispatcher.py:63-66`), no como pregunta. La única pregunta
real al humano vive en el integrador —`PermissionPolicy.handle`, `agentic_code/permissions.py:81-118`,
que sí recibe el `tool_input`— pero su compuerta es ese mismo booleano estático
(`permissions.py:98`). Consecuencias:

- `requires_permission = True` haría preguntar **también en el GET**, justo lo contrario de lo que
  A declara (`isReadOnly(input) { return input.value === undefined }`, `ConfigTool.ts:90-92`).
- Discriminar por `input` dentro del hook sería escribir política de UNA tool en el integrador:
  el núcleo no se adapta al integrador, y la costura que falta es del núcleo.
- Simular la pregunta con `ends_turn` sería teatro: el `context_modifier` ya habría escrito.

~~⇒ Guarda 11 **declarada no portable**, bloqueada por `check_permissions` (`K1`/`GAP-02`), no por
este paso. **No abre agujero hoy**: con el registro vacío todo SET muere en `Unknown setting`, y el
día que un integrador registre un ajuste, es él quien sabe si exige consentimiento.~~

**Corregido por `D-22` (mismo día, antes de inyectar nada).** El diagnóstico de arriba es
correcto y se conserva entero: hoy la guarda **no se puede expresar**. Lo que no vale es la
conclusión. Que el contrato T1 carezca de `check_permissions` no es una razón para no portar la
guarda — **es la descripción exacta de lo que hay que construir**. Y nótese que ni siquiera es
una carencia descubierta aquí: el propio contrato la declara pendiente por escrito
(`contracts/tools.py:4-6`), o sea que estaba ya reconocida como deuda y este censo la estaba
convirtiendo en criterio de exclusión. Guarda 11 ⇒ **`FIND-CFG-PERM`, ABIERTO, paso propio**, y
su alcance no es de esta fila sino del **contrato**: `check_permissions(input, ctx)` por llamada
en `ToolProtocol`, el dispatcher preguntando en vez de consultar la lista blanca por nombre
(`dispatcher.py:63-66`), el hook del integrador dejando de compuertarse por el booleano estático
(`agentic_code/permissions.py:98`) y las **25 tools** decidiendo cuál declara qué. Por eso no se
mete dentro del paso 4: no es de `Config`, es de todos.

Distinción con `D-21`, que sigue viva y no se toca: aquí la imposibilidad es **de nuestro
código** y se arregla construyendo; `D-21` habla de lo que el **motor** no sabe expresar, que no
se arregla construyendo en el núcleo.

**Segunda corrección, el mismo día: la guarda 11 vuelve DENTRO del paso 4.** La había sacado a
paso propio estimándola «grande y transversal, toca las 25 tools», y sometí a decisión del usuario
si iba detrás. Las dos cosas estaban mal y por el mismo motivo —`D-08`: el canónico ya lo tiene
contestado y yo estaba estimando en vez de leer—. `TOOL_DEFAULTS` (`Tool.ts:757-769`, aplicado en
`buildTool`, `:783-792`) da `checkPermissions` **permisivo por defecto**; `ConfigTool` lo
sobreescribe (`:98-107`). Luego lo que A exige es **la costura con default permisivo + el override
de esta tool**, no una revisión tool a tool: las otras 24 conservan su conducta actual porque eso
**es** el canónico, no porque se aplace nada. Alcance real: `check_permissions(input, ctx)` en
`ToolProtocol` con default permisivo, el dispatcher preguntándolo además de la lista blanca por
nombre (`dispatcher.py:63-66`), el hook del integrador dejando de compuertarse por el booleano
estático (`agentic_code/permissions.py:98`) y el override en `Config`, con
`isReadOnly(input) { return input.value === undefined }` (`ConfigTool.ts:90-92`) como criterio para
que el GET no pregunte. `FIND-CFG-PERM` queda como **etiqueta de la conducta, no como paso
aparte**.

La guarda **12 sí es portable hoy y efectiva**: el esquema lo hace cumplir
`agentic_models.validate_tool_arguments` antes de `execute` (`dispatcher.py:72`).

#### Pregunta 2 — ¿existe en B lo que esto protege?

`SUPPORTED_SETTINGS` es **dominio de Claude Code**, no algoritmo: `theme`, `editorMode`,
`verbose`, `preferredNotifChannel`, `autoCompactEnabled`, `autoMemoryEnabled`, `voiceEnabled`,
`teammateMode`, `remoteControlAtStartup`, las tres de notificación push… Ninguna tiene referente
aquí, y buena parte cuelga de `feature(…)`. Verificado en vivo:

- **`theme`**: `agentic_code/theme.py` es una paleta oscura fija y el propio fichero declara la
  carencia (`:14-17`): «hay un solo tema fijo; el selector es superficie que este producto no
  tiene todavía». No hay nada que conmutar.
- **`model`, `language`, `effort`, `thinking`, `max_turns`…**: viven en `Settings`
  (`agentic_code/settings.py:26-109`), **dataclass congelada** que se construye al parsear la
  línea de comandos y no se muta jamás. Y se hornean en el arranque: `compose_system_prompt` y
  `build_model_options` se evalúan **una vez**, dentro de `build_runtime`
  (`composition.py:169-176`, `:218`). Cambiarlas a mitad de sesión no tendría efecto ni aunque
  se persistieran.
- ~~**No hay `~/.claude.json` ni `settings.json`.**~~ **FALSO, y es error mío de la primera
  pasada (corregido 2026-08-10, releído `mcp_config.py` 1→EOF).** B **sí** tiene el homólogo del
  fichero global de A, y con la misma partición por scope:
  `user_config_path` = `state_dir/config.json` (`mcp_config.py:430-431`) y `local_config_path` =
  `state_dir/projects/<project_key>/config.json` (`:434-435`), más `managed-mcp.json` del
  directorio gestionado (`:425-427`). Hoy sólo guardan `mcpServers` y `disabledMcpServers`, que es
  **exactamente lo que guarda `~/.claude.json` en A además de los ajustes**. La configuración que
  B persiste de verdad es esto, más `permissions.json` (`permissions.py:141-153`), y las dos
  tienen ya superficie: `/permissions` y `/mcp approve|deny` (`repl.py:375-394`, `:488-506`).
  ⇒ **El almacén del paso 4 no se inventa: se hereda.** `Config` escribe en ese mismo fichero,
  como en A.
- **Y con él aparece un riesgo real que `saveConfigWithLock` es justo lo que evita.**
  `JsonFileServerStore._write` (`mcp_config.py:371-378`) hace **lee-modifica-escribe del payload
  entero** sin lock: lee `config.json`, sustituye `mcpServers` y vuelca. Si `Config` escribe sus
  ajustes en ese fichero por otra vía, **una escritura pisa a la otra** — un `/mcp add` borraría
  el ajuste recién puesto, o al revés. A no tiene el problema porque **todo** pasa por
  `saveConfigWithLock` (`config.ts:1153-1329`). Consecuencia de diseño para el paso 4: el almacén
  es **uno solo y compartido**, y `JsonFileServerStore` pasa a escribir por él. No es alcance
  añadido por gusto: escribir el mismo fichero por dos caminos distintos es el bug, no la
  precaución.

⇒ **B no tiene hoy NI UN ajuste escribible en caliente.** El hecho es exacto y verificado; lo que
`D-22` corrige es qué se concluye de él.

- **Sigue en pie:** portar `SUPPORTED_SETTINGS` clave a clave —seis paletas de tema, `editorMode`,
  canales de notificación push, voz, teammates— sería fabricar el **dominio de producto de A**,
  que es `homologar-es-trasladar-conducta` por el otro lado. `D-22` habla de homologar
  *comportamiento y algoritmo*, y un catálogo de ajustes no es ni una cosa ni la otra.
- **Ya NO vale:** cerrar la fila con «el registro va vacío porque B no tiene ajustes». Eso deja la
  tool sin **almacén**, y el almacén **sí es algoritmo**: `saveConfigWithLock` (`config.ts:1153-1329`)
  con lockfile, copia de seguridad con marca de tiempo, `0o600` y `pickBy` de defaults, más el GET
  cacheado con vigía (`:1044-1086`) y el `updateSettingsForSource` que devuelve `{error}` en vez de
  lanzar (`settings.ts:416-524`). Nada de eso depende de QUÉ ajustes existan. **Se construye.**
- **Y ya NO vale** dar por cerrado que un SET no puede tener efecto en caliente. La causa es de
  B y es reparable: `Settings` es dataclass congelada (`agentic_code/settings.py:26-109`) y
  `compose_system_prompt` / `build_model_options` se hornean **una vez** en `build_runtime`
  (`composition.py:169-176`, `:218`). El homólogo de `appStateKey` (conducta 3, `:356-362`) exige
  deshornear eso. Queda como `FIND-CFG-HOT`, ABIERTO, paso propio en el integrador.

Lo que entra en el paso 4, entonces: el **algoritmo entero** (registro → guarda → GET real →
coerción → opciones invocables → validación → escritura persistida → literales al modelo) **con
almacén de verdad en el núcleo**, y el registro poblado por el integrador —misma costura que el
predicado+validador de G11 del paso 3 (`composition.py:194-196`)— porque **qué** se configura sí
es suyo.

#### Pregunta 3 — ¿es alcanzable desde `agentic_code`?

La tool **está publicada** (`tools/factory.py:56`), así que el modelo la ve y la llama. Lo que no
es alcanzable es su EFECTO: `author_root_context` (`composition.py:181-197`) siembra plan mode,
cwd y los validadores de `Edit`, y **no siembra `config`**; ningún fichero de ninguno de los dos
repos lee esa clave. Por tanto:

- un SET **no se puede certificar por efecto** — no hay efecto que medir;
- sí se certifica por el `{"role": "tool"}` que entra en la historia, que es el mismo canal de
  medida de los pasos 1, 2 y 3.

**El hallazgo funcional, en una línea:** hoy `Config` le dice al modelo `{"operation":"set",
"setting":"theme","new_value":"dark"}` —que se lee como éxito— y **no ha pasado nada**. No es una
guarda que falte: es una tool que miente, y encima sin pedir permiso (guarda 11). ~~El registro
vacío no es una carencia a tapar, es el estado verdadero del producto.~~ ⇒ **`D-22`:** el registro
vacío describe el producto, no autoriza a dejar la tool sin almacén. Un registro que el integrador
puede poblar y un almacén que persiste de verdad **no** hacen que la tool mienta menos por
casualidad: la hacen funcionar.

**No portable, declarado:** `logEvent('tengu_config_tool_changed')` (`:383-389`, telemetría de A);
las ramas `feature('VOICE_MODE')` (`:116-125`, `:232-308`), `feature('BRIDGE_MODE')` /
`remoteControlAtStartup` con su desajuste a `"default"` (`:150-180`, `:367-381`), `KAIROS` y
`USER_TYPE === 'ant'` (`supportedSettings.ts:134-185`) — sin referente y bajo gates de A.
`generatePrompt()` (`prompt.ts:14-93`) genera la enumeración de ajustes **desde el registro**: con
registro vacío no enumera nada, que es lo correcto y ya no hay que declararlo como omisión.

#### Helpers del canónico — leídos 1→EOF (corrección de método, 2026-08-10)

La tabla de arriba se escribió leyendo el **directorio de la tool** (5 ficheros). Eso no es «el
canónico hasta EOF»: las conductas 1, 2, 6, 9 y 11 y el propio `getOptions` **viven en helpers**, y
sostener la propuesta sin leerlos era deducir. Leídos enteros: `Tool.ts` (792) ·
`utils/config.ts` (1818, en dos páginas por el techo de la lectura) ·
`utils/settings/settings.ts` (1015) · `utils/theme.ts` (639) ·
`utils/model/modelOptions.ts` (540) · `utils/model/validateModel.ts` (159) ·
`utils/configConstants.ts` (21) · `utils/slowOperations.ts` (286). Qué cambian:

- **Confirman, no corrigen, las 12 conductas.** Nada de lo leído contradice la tabla.
- **Guarda 11 confirmada como deliberada:** `TOOL_DEFAULTS` (`Tool.ts:757-769`, aplicado en
  `buildTool`, `:783-792`) da `checkPermissions` **permisivo por defecto**. Que `ConfigTool`
  pregunte en el SET es conducta propia de la tool, no herencia del marco.
- **Conducta 2 confirmada y más honda de lo que decía la fila:** `saveGlobalConfig`
  (`config.ts:797-866`) baja por `saveConfigWithLock` (`:1153-1329`) — lockfile, copia de
  seguridad con marca de tiempo, guarda anti-pérdida-de-credenciales, modo `0o600`, y `pickBy`
  que **no escribe** los valores iguales al default. El GET (`getGlobalConfig`, `:1044-1086`)
  va por caché en memoria con vigía `fs.watchFile`. ~~Nada de esto es portable **hoy**: B no
  tiene el fichero.~~ ⇒ **`D-22`: el fichero se crea.** Esto deja de ser «el precio para el día
  que exista» y pasa a ser el **contenido del paso 4**. Lo que sí queda fuera por otra razón —no
  por ausencia— es el vigía `fs.watchFile`: B no tiene un segundo proceso escribiendo el fichero,
  y una caché invalidada por nadie es complejidad sin conducta observable. Se declara.
- **Conducta 9 precisada:** la otra mitad de la escritura, `updateSettingsForSource`
  (`settings.ts:416-524`), **no lanza**: devuelve `{ error }`. Y su semántica de mezcla es
  específica —`undefined` borra la clave, los arrays se REEMPLAZAN, y un JSON sintácticamente
  roto devuelve error **en vez de sobrescribir el fichero**—. El `try/catch` de A cubre por
  tanto dos regímenes distintos, no uno.
- **Corrección de diseño que sólo se ve aquí:** `getOptions` del registro **no puede ser una
  lista estática**. En A se resuelve en el momento de la llamada: `THEME_SETTINGS` es constante
  (`theme.ts:91-109`, 7 valores) pero `getModelOptions()` (`modelOptions.ts:461-540`) depende de
  nivel de suscripción, provider, variables de entorno, caché de config y allowlist. En el port,
  el registro guarda un **invocable**, no una tupla. Leyendo sólo el directorio de la tool esto
  habría salido mal.
- ~~**Refuerzan la pregunta 2.**~~ **Delimitan qué es producto y qué es algoritmo (releído bajo
  `D-22`).** `theme.ts` enumera 6 paletas + `auto` y `agentic_code/theme.py` tiene **una** fija:
  eso es catálogo de producto, y `D-22` no obliga a pintar cinco paletas. `modelOptions.ts`
  construye el selector desde estado de sesión que en B no existe porque `--model` se congela en
  `Settings` y se hornea en `build_runtime`: eso **no** es catálogo, es la ausencia de estado de
  sesión mutable ⇒ `FIND-CFG-HOT`. La misma lectura, partida por la línea correcta.
- **`validateOnWrite` no es portable como literal:** el de `model`
  (`validateModel.ts`, 159 líneas) hace una **consulta real a la API** con caché, con sus tres
  mensajes propios. Lo portable es la **costura** (validador asíncrono por ajuste), no su
  contenido.
- Sin hallazgo: `configConstants.ts` (`EDITOR_MODES`, `NOTIFICATION_CHANNELS`, `TEAMMATE_MODES` —
  dominio de A) y `slowOperations.ts` (`jsonStringify` es un envoltorio de registro sobre
  `JSON.stringify`).

### `FIND-WT1/2/3` — worktrees (ventana anterior, se conservan aquí)

- **`FIND-WT1`**: ninguna de las dos tools cablea `ToolUseContext.cwd`. A lo hace en
  `EnterWorktreeTool.ts:94-95` y `ExitWorktreeTool.ts:126` (en **ambas** ramas, `:263` keep y
  `:291` remove). Reproducido en aislado: 2 failed, 1 passed — y el que pasa, pasa por el
  motivo equivocado (el cwd nunca se movió).
- **`FIND-WT2`**: nuestra `ExitWorktree.description` perdió el bullet canónico sobre limpiar
  las cachés dependientes del CWD, que en A es factual (`:98-102`, `:143-145`).
- **`FIND-WT3`**: `worktree_session` vive en `app_state.native`, que **muere con el turno**, y
  nada en `agentic_code` lo recuerda.
- **`FIND-WT4` (pérdida de datos):** nuestro `ExitWorktree(remove)` solo mira
  `git status --porcelain` ⇒ **el trabajo ya commiteado pasa el filtro**, y a continuación
  `git worktree remove --force` + `git branch -D` lo destruye. La `description` promete
  rechazar por «commits not on the original branch». A sostiene esa promesa con
  `originalHeadCommit` + `countWorktreeChanges` (`ExitWorktreeTool.ts:174-224`). **Se copió la
  promesa, no la conducta que la sostiene.**

### Paridad real — sin hallazgo (verificado, no asumido)

`glob`, `grep`, `WebSearch`, `WebFetch` (A tiene **una** guarda de URL,
`WebFetchTool.ts:191-203`; la nuestra es más estricta), `Sleep`, `ToolSearch`,
`AskUserQuestion` (divergencia `ends_turn` ya declarada), `TaskGet/List/Update/Output/Stop`
(mismas ramas de error), `EnterPlanMode` (`plan_mode.py:167` ≡ `EnterPlanModeTool.ts:79`),
`Agent` (A **no** tiene guarda de profundidad; la nuestra es *añadido*, no pérdida).
`TaskCreate`: A rechaza por hooks bloqueantes (`TaskCreateTool.ts:112`) — no tenemos esa capa.

### `skills` y `mcp` — aquí el patrón SE ROMPE, en el buen sentido

- `SkillTool` de A tiene **5** guardas (`SkillTool.ts:355-428`). Una es experimental ant-only
  (errorCode 6) y otra (`type !== 'prompt'`, errorCode 5) no aplica a nuestro registro. **De
  las 3 aplicables, las 3 están portadas**: `skill_tool.py:158` (vacío/desconocido),
  `:164` (no encontrada), `:167` (disable-model-invocation, citando su `errorCode 4`).
- `mcp`: A's `MCPTool` no tiene `validateInput`. Nuestro `resource_tools.py:74-82` tiene
  guardas que A **no** tiene ahí.

Esto es lo que impide decir «el port es superficial en todo». No lo es. Es selectivo, y la
línea de corte es exactamente la del depósito de estado.

### `FIND-READ-ENC` — `read_file` **sale de «paridad real»** (hallado en el paso 3)

Estaba listado arriba como paridad verificada. **No lo es.** `read_file.py:97` hace
`path.read_text(errors="replace")`: sin detección de **UTF-16LE** por BOM y sin **CRLF→LF**,
que es exactamente la divergencia que el paso 3 corrige en `Edit`
(`utils/fileRead.ts:20-49`, `:75-98`). Consecuencias encadenadas: un fichero UTF-16LE se le
entrega al modelo como mojibake, y un fichero CRLF le llega con `\r` que luego copiará dentro
de `old_string`. Con `Edit` ya homologado, la incoherencia entre ambas tools es peor que antes.
**ABIERTO**, no se toca en el paso 3. Se ataca junto al resto de `read_file` (queda además su
lectura de notebooks como texto plano, G8 de arriba).

---

## 3. Orden de ataque (protocolo acordado: todo lo pequeño primero, `bash` al final)

Cada paso cierra con **certificación de homologación** (cita de línea canónica) y **prueba en
`agentic_code`** como verdad del resultado. Las pruebas sintéticas se reconstruyen después.

| # | Paso | Depende de depósito | Tamaño |
|---|---|---|---|
| 1 | `FIND-EXITPLAN`: guarda de modo, no de plan-file | no | mínimo |
| 2 | `FIND-TODO`: `allDone ⇒ []` | no | mínimo |
| 3 | `FIND-EDIT` guardas **1,4,5,6,7,11** (2 y 8 sin referente) + CRLF/UTF-16 + `findActualString`/`preserveQuoteStyle` + **camino de éxito** (4 conductas) | no | pequeño → **medio** |
| 4 ✅ | `FIND-CFG-2`: **algoritmo** de `Config` + **almacén único** (heredado: `state_dir/config.json`, con `JsonFileServerStore` pasando por él) + `check_permissions` con default permisivo y override en `Config` + registro poblado por el integrador. **Las 12 conductas**; ver §2 corregido y `D-22` | no | **medio → grande** |
| 5 | `FIND-WT2`: descripción de `ExitWorktree` | no | mínimo |
| 6 | `FIND-WT4`: `originalHeadCommit` + `countWorktreeChanges` (**pérdida de datos**) | parcial | medio |
| 7 | **DECISIÓN DEL ASIENTO DE ESTADO DE SESIÓN** — bloquea todo lo de abajo | — | medio |
| 8 | `FIND-WT1`/`FIND-WT3`: cable de `cwd` + persistencia de `worktree_session` | sí | medio |
| 9 | `FIND-TODO`: `todos[agentId ?? session_id]` | sí | medio |
| 10 | `FIND-STATE` + `FIND-WRITE` + `FIND-EDIT` 9,10 + TOCTOU en `call()` | sí | grande |
| 11 | `FIND-EDIT` 3 (deny rule) — necesita `toolPermissionContext` | sí | grande |
| 12 | **`FIND-BASH`** | no | el mayor |

### Trabajo REABIERTO por `D-22` (2026-08-10) — pasos nuevos, sin numerar todavía

Estaba excluido bajo el rótulo «sin referente en B», que `D-22` prohíbe como cierre. Entra como
trabajo; el orden lo fija el usuario. Ninguno se encadena a un paso ya cerrado.

| Paso | Qué falta construir | Capa | Tamaño |
|---|---|---|---|
| `FIND-EDIT-SECRETS` | escáner de secretos (`secretScanner.ts`, 40 reglas) como algoritmo; el predicado de ruta lo aporta quien tenga rutas compartidas | núcleo | medio |
| `FIND-NOTEBOOK` | `NotebookEditTool` + guarda de redirección `.ipynb` en `Edit` + lectura de notebooks en `read_file` (junto a `FIND-READ-ENC`) | núcleo | medio |
| `FIND-CFG-HOT` | deshornear `Settings`: hoy dataclass congelada y `compose_system_prompt`/`build_model_options` evaluados una vez (`composition.py:169-176`, `:218`) ⇒ homólogo de `appStateKey` | integrador | medio |
| `FIND-MEM-WIRING` | cablear memoria en `agentic_code` (`factory.py:210` no construye `MemoryProvider` sin `memory_root`/`memory_store`) ⇒ hoy toda `capabilities/memory/` es inalcanzable en el único vehículo de prueba | integrador | pequeño → medio |

**Fuera de `D-22`, por si se confunde:** la *superficie de producto* de A —seis paletas de tema,
`editorMode`, canales de notificación, voz, teammates, `KAIROS`, `USER_TYPE === 'ant'`— no es
comportamiento ni algoritmo y no entra por esta regla. Si se quiere, se pide y se dimensiona.

### El punto 7, enunciado

Hoy tenemos **cuatro** depósitos donde A tiene **uno** uniforme:
1. `app_state.native` — **per-turno** (`config`, `todos`, `worktree_session`, `plan_mode`).
2. El objeto `LocalRuntime` — sesión (`_task_registry`, `runtime.py:107`).
3. Clases ad-hoc del integrador — `WorkspaceCwd`, `PlanModeState`, `ConversationState`
   (`agentic_code/src/agentic_code/composition.py:32-77`).
4. Reconstrucción desde el historial — `deferred_delta.py:75-88`, el único robusto por
   construcción.

Nada dicta cuál debe usar una conducta ⇒ **una conducta puede quedarse sin casa en silencio**,
que es exactamente lo que pasó. Conductas de sesión de A hoy sin asiento: `todos[agentId]`,
`currentWorktreeSession`, `config`, `readFileState`, `agentNameRegistry`
(ausencia por verificar en condiciones — hoy solo comprobada por `grep`).

---

## 4. Reglas de esta fase (acordadas)

- Homologación **en vivo** contra `agentic_runtime` y `agentic_code`, no contra documentación.
- Paso a paso, con **certificación de homologación** por línea canónica.
- **`agentic_code` es la verdad** del resultado de la prueba, y **la única**: se prueba contra
  corridas REALES de `agentic_code`. Este censo es la ruta.
- Las pruebas sintéticas de `agentic_runtime` (suite y gates `E*`) **se retoman CUANDO LA
  HOMOLOGACIÓN ESTÉ CONSEGUIDA**, no antes. Mientras tanto **no significan nada**: no se
  corren, no se mantienen y **sus fallos no se persiguen**. Redactado así porque el enunciado
  anterior —«se reconstruyen después»— se leyó en el paso 1 como si permitiera correrlas, y
  costó una suite completa + 3 corridas de gates con modelo en vivo, todo fuera del paso.
  **Tampoco se editan. Sin excepción.** Si el diff de un paso deja una aserción o una docstring
  suya afirmando la conducta derogada, **se deja como está** y el desfase se anota en el §5 de
  este censo. Una suite apartada no miente a nadie porque nadie la lee; retocarla —aunque sea
  una línea, aunque se rotule «anexo»— es invertir otra vez en el enfoque abandonado, que es
  exactamente `homologar-es-trasladar-conducta`. El enunciado anterior autorizaba ese retoque
  «en una línea» y en el paso 2 se usó; se retira por eso.
- **El fuente va SIN comentarios** (regla nueva, 2026-08-10, y sustituye a la práctica de los
  pasos 1 y 2 de «declarar en el fuente»). Al tocar un fichero se **borran** los textos en forma
  de comentario y docstring explicativos que haya, y **no se añaden nuevos**. Sobreviven sólo las
  directivas de lint (`# noqa`) y el texto que es superficie de producto (descripción de la tool,
  mensajes al modelo). Motivo: un comentario que dice «homologado con `X.ts:123`» **sesga** —se
  lee como evidencia y ahorra el contraste, que es el trabajo. Lo único que guía es este censo,
  revisado y contrastado runtime-contra-canónico; lo que esté escrito en `agentic_runtime` **no
  prima**: se homologa el algoritmo del canónico. Toda justificación —línea canónica, ausencias
  deliberadas, salvedades— vive aquí y en `SEPARACION/DECISIONES.md`. Aplica también a los tests
  que se escriban.
- **`D-22` (nueva, 2026-08-10): «no existe en B» NO cierra una fila.** Si portar la conducta del
  canónico exige construir lo que falta —un almacén, una costura del contrato, un registro, un
  módulo entero— **se construye**; `agentic_runtime` está en fase de homologación. El rótulo «sin
  referente en B» queda prohibido como cierre y se sustituye por «falta construir X», con su paso.
  Dos límites que la regla **no** borra: lo que se construye es **mecanismo en el núcleo** —el
  integrador se adapta al núcleo, nunca al revés— y el **catálogo de producto** de A (temas,
  canales, modos) no es comportamiento ni algoritmo, así que entra sólo si el usuario lo pide.
  Y `D-21` sigue viva: lo que el **motor** no sabe expresar se rechaza igual, porque eso no se
  arregla construyendo aquí.
- `D-08`: ante conducta divergente, se lee el fuente de A. No se deduce.
- No se parchan conductas. Se contrasta.
- Toda inyección se **anuncia antes** de tocar el fuente.
- Nada se commitea sin la palabra del usuario.
- **`/clear` tras CADA paso terminado.** Se optimizan los tokens que quedan: una ventana =
  un paso. Este documento es el punto de retoma; se actualiza el §5 antes del `/clear`.

---

## 5. Estado de ejecución

### 2026-08-27 — `K6` · **TRAMO 6 cerrado** (`D-48`) + **sonda de ejecución** (sólo medida)

**Marcador del tramo 6**, con lo que consta en el cierre y en `SEPARACION/DECISIONES.md § D-48`
(cinco divergencias declaradas allí; no se reproducen aquí): motor de compactación **parcial**
homologado contra `claude-code/src/services/compact/compact.ts` y expuesto en el integrador como
`/compact [from:N|upto:N] [instrucciones]` sobre los pivotes que publica `/history`. Acreditado
por **inyección revertida desde copia verificada por `sha256`** (`D-12 · b`): **9 inyecciones,
9 rojas**. Suite en **247 verdes**. Commits: `agentic_runtime` `9c86aee` (`fase-b/tramo-1`),
`agentic_code` `0b66a84` (`fase-b/find-pool-1`); ambos árboles limpios al cerrar.

#### La sonda de ejecución — **SOLO SE MIDE**

No se optimizó nada, no se tocó el motor, no se añadió ni un test. Instrumento **fuera de los
repos** (scratch de sesión): proxy TCP que graba el cable `127.0.0.1:8099 → :8080` y una sonda sin
TUI que conduce una sesión REAL de `agentic_code` por la costura ya existente
`WorkspaceRepl(reader=…)`. Ni un fichero de ninguno de los dos repos fue modificado por la sonda;
el `base_url` se redirigió en memoria sobre `LOCAL_CATALOG`. Modelo: `local/unsloth/
Qwen3.8-27B-GGUF:UD-IQ4_XS`, `llama-server` de un slot, KV `q4_0`, `/v1/responses` (SSE).

Sesión de 10 pasos: 4 turnos de trabajo real (leer, editar con `Edit`, `bash`, resumir),
`/history`, `/compact`, un turno posterior, `/history`, `/compact upto:1`, `/status`.

**Resultado funcional: correcto.** El agente leyó `README.md`/`src/invoice.py`, añadió
`total_with_vat(lines, country, discount_percent)` componiendo `subtotal → apply_discount →
with_vat`, respetó «no toques los tests», y ante la fricción real del entorno (`python` inexistente,
`pytest` no instalado) se recuperó: verificó las aserciones a mano con `python3 -c` y luego reportó
`No module named pytest` **tal cual** cuando se le pidió literalidad. Tools usadas: `read_file`,
`glob`, `bash`, `Edit`. Toolset publicado en cada llamada del hilo: **24**.

**Los cuatro cronómetros** (`in`/`cached` del `response.completed`; `ttft` medido en el cable):

| # | medida | in | cached | new | out | ttft | total | pp t/s | tg t/s |
|---|---|---|---|---|---|---|---|---|---|
| — | 1ª vuelta, contexto **frío** | 16.961 | 0 | 16.961 | 199 | 19,94 s | 27,58 s | **850,8** | 26,03 |
| 1 | turno normal **caliente** (línea base) | 21.145 | 21.071 | 74 | 167 | 0,49 s | 7,34 s | — | **24,39** |
| 2 | **`/compact` completo** | 5.570 | **0** | 5.570 | **3.898** | 7,05 s | **150,00 s** | 790,2 | 27,27 |
| 3 | **1er turno tras el compact** | 19.209 | **16.701** | 2.508 | 217 | 4,17 s | 12,89 s | 602,1 | 24,88 |
| 4 | **`/compact upto:1`** | 3.000 | **0** | 3.000 | 2.827 | 3,96 s | **105,34 s** | 756,9 | 27,89 |

Pasos completos: 41,33 s · 107,91 s · 6,24 s · 7,41 s · `/history` 0,05 s · **`/compact` 150,07 s** ·
turno posterior 16,80 s · `/history` 0,05 s · **`/compact upto:1` 105,40 s** · `/status` 0,05 s.
Generación plana en toda la sesión: **24,4–26,2 t/s** en el hilo, **27,3–27,9 t/s** en las dos
llamadas de compactación (sin tools en el prompt).

**Lo que se buscaba, contestado con número.** La llamada de compactación **no comparte clave de
caché con el hilo**: confirmado por los dos lados —`cached_tokens = 0` en el `response.completed` y
`n_prompt_tokens_cache = 0` leído en `/slots` en pleno vuelo—, tal como predice el propio
contrato de B (`system_override` propio, `tools` ausente del cuerpo, `max_tokens` propio de 4096).
**Pero el segundo reprocesado completo NO se produce:** el turno (3) reutilizó **16.701 de 19.209**
tokens y arrancó en 4,17 s, no en los ~20 s de un prefijo frío. Los 2.508 nuevos son el resumen
recién insertado, que es coste inevitable de la conducta, no de la caché. El criterio del enunciado
—«si el turno (3) tarda como el (2), la caché se rompió en ambos sentidos»— **no se cumple**:
12,89 s contra 150,00 s. La caché del hilo sobrevive a la compactación.

**Dónde está el coste real, entonces.** No en el reprocesado (7,05 s de los 150) sino en la
**generación del resumen**: 3.898 tokens a 27,3 t/s = **142,95 s**, el 95 % del `/compact`. Y
**3.898 roza el techo de 4.096**: una conversación mayor toparía. El contraste (4) confirma que
manda el prefijo —3.000 de entrada contra 5.570— pero el ahorro es sólo de 45 s porque la salida
apenas baja (2.827): el parcial abarata lo que menos pesa.

**Peculiaridad gpt-5.x, para el catálogo P1–P9** (`agentic_models/gpt-5.x-conducta-vs-claude.md`):
de los 3.898 tokens del resumen, **~1.600 son razonamiento vertido al canal de texto** antes del
`<analysis>` —un recuento cronológico completo que luego el modelo repite dentro del `<summary>`—.
Con el razonamiento apagado en la llamada de compactación (como en A, `compact.ts:1305`), este
modelo no calla: lo escribe. Es ~60 s de los 143 y ~40 % del resumen persistido. Medido, no tocado.

**KV `q4_0`: sin degradación atribuible.** El resumen reproduce rutas absolutas, el contenido final
íntegro de `invoice.py`, el `21.78` del cálculo, los tres errores del entorno y la restricción «no
toques los tests»; y el turno (3) contestó correctamente fichero y línea. Nada que anotar por
cuantización en esta corrida.

**Declaraciones de compactación, tal cual las emitió el integrador:**
- `/compact` → `Compacted · 39 mensajes resumidos · 1625 → 2022 tokens`
- `/compact upto:1` → `Compacted · 3 mensajes resumidos · 2389 → 2729 tokens` +
  `parcial hasta el pivote · 6 mensajes conservados literales`

Las dos declaran **crecimiento** de tokens. Se anota como medida, sin interpretarla aquí; en el
cable el prefijo real del hilo sí bajó, de 21.145 a 19.209 (−1.936).

**Dos hallazgos laterales, ABIERTOS y no tocados** (aparecieron en la corrida, no se persiguen en
esta ventana):
- **`FIND-EMPTY-TOOL-OUT`** — una salida de tool **vacía** (`glob` sin coincidencias) viaja al
  modelo como el literal **`(see attached image)`** (visto en el cable, `call_mksKrj…`). El modelo
  lo registró como anomalía y lo rodeó con `ls -la`. Es del adaptador `openai-responses`.
- **`FIND-RENDER-PARALLEL`** — con **tools en paralelo** en una misma respuesta, el deck rotula la
  primera con el nombre de la tool y las demás con el `call_…|fc_…` crudo
  (`agentic_code/rendering.py`). Cae junto al render de compactación, que sigue pendiente de la
  palabra del usuario.

**PUNTO DE RETOMA.** Con el número en la mano se decide si hay algo que pagar del `/compact`; la
sonda no propone nada. Siguen **pendientes de la palabra del usuario** los dos aplazados del tramo
5: la rama de `CompactionEvent` en `capture.py::_canonical_message` y el render de compactación en
`rendering.py`.

### 2026-08-26 — `K6` motor de compactación · **TRAMO 5 de 6 cerrado** (`D-46`)

Ventana de un paso. Lo decidido queda en `SEPARACION/DECISIONES.md § D-46`; aquí el marcador y
**el punto de retoma**.

**Inyectado (6 ficheros, un repo — `agentic_runtime`):**
- `context/compact/engine.py` — el reintento por `prompt too long`. `MAX_PTL_RETRIES = 3`
  (`compact.ts:227-228`), `group_messages_by_api_round` (par de `grouping.ts:24-50`),
  `truncate_head_for_ptl_retry` (par de `compact.ts:243-291`), el clasificador
  (`is_prompt_too_long_text`), el parseo del par `N tokens > M` y el marcador sintético
  `PTL_RETRY_MARKER`. `_summarize_once` se extrae para que el lazo reutilice el repliegue de
  razonamiento de `D-43 · 5`.
- `context/estimation.py` — **se paga el hueco del estimador**: `TRANSPORTED_ROLES`
  = `{user, assistant, tool}`. Ver abajo.
- `contracts/events.py` — `CompactionEvent` gana `ptl_attempt`, `dropped_messages` y
  `remaining_messages` (`D-22`; en A eso es `logEvent('tengu_compact_ptl_retry')`, telemetría).
- `context/compact/__init__.py` — reexportes.
- `tests/test_compact_engine.py` (sección C bis, 11 casos) y `tests/test_context_window.py`
  (`test_only_the_roles_that_travel_to_the_model_count`, reescrito contra el criterio).

**El hueco del estimador, y por qué era bloqueante.** `rough_token_count_for_message` devolvía 0
para `role:"tool"`, así que la masa entera de salidas de tools valía cero: el acumulador del gap
no alcanzaba nunca su objetivo, el recorte se clampaba a `len(groups) - 1` y el primer reintento
se llevaba **todo menos la última ronda**. A no tiene el hueco porque sus resultados de tool son
bloques `tool_result` dentro de mensajes de usuario; en B viven en mensajes propios
(`agent_loop.py:533-537`). El marcador de frontera (`system`) sigue sin contar.

**Divergencias declaradas:** agrupación por estructura y no por `message.id` (B no lo lleva); el
PTL se clasifica **también** desde el `ErrorEvent` porque el puente puede rendirlo por los dos
canales; y `compact_conversation` **no** emite el evento `failed` —lo emite
`auto_compact_if_needed` desde su `except`, y hacerlo en los dos sitios reportaría dos fallos por
una compactación—; los intentos quemados viajan en `PromptTooLongError.ptl_attempts`.

**Prueba:** los dos ficheros del tramo **58 passed**; núcleo de compactación + eventos + lazo,
**152 passed, 9 xfailed**; `agentic_code` **231 passed**, sin tocar. Verdes a la primera ⇒
acreditados por **inyección revertida desde copia verificada por `sha256`** (`D-12 · b`, nunca
`git checkout`): **9 mutaciones, las 9 muertas**. Una de ellas destapó un test que no medía —
`…three_retries_is_the_ceiling…` comparaba `MAX_PTL_RETRIES` contra sí misma, así que subirla a 5
dejaba la suite verde—; se reescribió fijando el número canónico y los literales.

**Las sintéticas de `agentic_runtime` siguen apartadas** (§ 4) y no se tocaron.

**Desfase de este § 5, anotado y no tapado:** el **tramo 4** cerró sin entrada aquí — su registro
íntegro está en `SEPARACION/DECISIONES.md § D-45` y su commit es `98386c7`. Esta entrada salta,
por tanto, del tramo 3 al 5; no se reconstruye el marcador ausente a posteriori.

**PUNTO DE RETOMA — tramo 6, el último:**
6. Parcial + `/compact` en `agentic_code`; hooks (**`POST_COMPACT` no existe en
   `hooks/protocol.py`** ⇒ se construye, `D-22`); ampliar `D-42`.

**Y después del tramo 6:** la sonda de ejecución desde `agentic_code` con enunciado expreso
(resultado funcional, uso de tools, t/s, tiempo, declaraciones de compactación), examinando el
riesgo del KV `q4_0`. Siguen **pendientes de la palabra del usuario** los dos aplazados: la rama
de `CompactionEvent` en `capture.py::_canonical_message` y el render de compactación en
`rendering.py`.

### 2026-08-26 — `K6` motor de compactación · **TRAMO 3 de 6 cerrado** (`D-44`)

Ventana de un paso: el motor del tramo 2 pasa de existir a **estar cableado**. Lo decidido queda
en `SEPARACION/DECISIONES.md § D-44`; aquí el marcador y **el punto de retoma**.

**Inyectado (5 ficheros, 2 repos):**
- `loop/agent_loop.py` — punto de llamada **al principio del cuerpo de la vuelta** (tras
  `ctx.turn_count += 1`, antes de `_build_tool_pool`), con `AutoCompactTracking` vivo en `run()` y
  `AgentLoop._emit` como `emit` del motor. La llamada al modelo manda
  `messages_after_compact_boundary(ctx.messages)`; la frontera y el resumen se **añaden** por
  `_append(..., origin="compact")` — la historia no se reemplaza (`D-42`). El `ContextBudget` entra
  por kwarg; sin él el punto de llamada no existe y el lazo sale idéntico a antes.
- `execution/local/runtime.py` y `factory.py` — el cable `RuntimeConfig.context_budget` →
  `LocalAgentRuntime` → `AgentLoop`.
- `agentic_code/composition.py` y `cli.py` — el presupuesto **sube por encima de `build_runtime`**:
  se resuelve una vez desde `model_definition` y lo consumen los dos, `RuntimeConfig` y
  `UsageLedger`. Antes lo calculaba sólo el medidor.

**La compactación NO consume vuelta.** `tracking.turn_counter` avanza sólo en la recursión tras
tools (par de `query.ts:1523`/`:1679`), nunca en la vuelta que compacta: si consumiera, robaría en
silencio de `--max-turns`.

**Ancla de uso — añadido sobre el enunciado literal del tramo, declarado.** El `DoneEvent` sella
`UsageAnchor(usage.context_tokens, len(<enviados>))` y el motor lo recibe, así que el umbral se
dispara con números reales en vez de con `len/4`. Es lo que paga la deuda que el tramo 1 anotó
(«todo se estima»); lo que sigue sin poblarse es `session.usage`
(`execution/local/runtime.py`), que no bloquea porque el dato viaja por el `DoneEvent`.

**Divergencia declarada: ámbito del `tracking`.** El `AgentLoop` se construye **por task**, o sea
por prompt de usuario: `consecutive_failures` (cortacircuitos) y `last_compacted_tokens` (freno de
recompactación) se reinician cada turno. Medida y **no persistida**: el asiento de estado de sesión
sigue siendo el punto 7 del § 3.

**Barrido de comentarios (§ 4)** en los cinco ficheros: `agent_loop.py` 806→559,
`execution/local/runtime.py` 623→448, `factory.py` 348→232, `composition.py` 312→240,
`cli.py` 362→324. Directivas `# noqa` conservadas una a una; `ruff` limpio en los cinco.

**Prueba:** `agentic_code/tests/test_compaction_wire.py` (**nuevo**, criterio y citas en la
docstring) — la compactación ocurre **dentro** del turno sin gastar vuelta, y el ancla dispara el
umbral que la estimación sola no alcanzaría. Los dos casos pasaron a la primera, así que se
**falsificaron** con `context_budget=None`: peticiones de resumen 0 y el corpus viajando en la 2ª
llamada — miden el cable, no el decorado. Suites: `agentic_code` **229 passed**;
`agentic_runtime/.../tests/test_compact_engine.py` **27 passed**.

**Commiteado** (palabra del usuario, 2026-08-26): `agentic_code` `0c59cac` en
`fase-b/find-pool-1`; en `agentic_runtime`, el commit de cabeza de `fase-b/tramo-1` es el que trae
esta misma entrada.

**PUNTO DE RETOMA — tramos 4→6:**
4. Restauración post-compactación sobre `compact_context()` + estado de ficheros leídos. La
   docstring de `contracts/compaction.py` está **rancia**: sigue afirmando que el motor `K6` no
   existe.
5. PTL: clasificador, truncado de cabecera, reintento (`MAX_PTL_RETRIES = 3`, `PTL_RETRY_MARKER`).
6. Parcial + `/compact` en `agentic_code`; hooks (**`POST_COMPACT` no existe en
   `hooks/protocol.py`** ⇒ se construye, `D-22`); ampliar `D-42`.

### 2026-08-25 — `K6` motor de compactación · **TRAMO 1 de 6 cerrado** (`D-42`)

Ventana de un paso. Lo decidido queda íntegro en `SEPARACION/DECISIONES.md § D-42`; aquí el
marcador y **el punto de retoma**.

- **Retractado el «lo que NO entra».** Palabra del usuario: si la misión es implementar el
  canónico para los modelos con que se va a trabajar, **no hay lista de exclusiones**; lo que
  varía es el **escalado de política** para el modelo local (mecanismo `D-41`). El prompt
  estático tampoco se replica por fe: el texto que parchea una patología de Claude se sustituye
  por lo que parchee la patología **medida** de nuestros modelos.
- **Hallazgo empírico extraído de `~/python/prueba_modelo_local`** (leído entero, nada tocado) —
  no se reinventa, se homologa. Cuatro capas, con cita:

  | capa | mecanismo | cita |
  |---|---|---|
  | transporte | `extra_body.chat_template_kwargs = {"enable_thinking": False}` (flag de plantilla jinja de llama.cpp, **no** el parámetro `reasoning` de la API) | `llm.py:70-79` |
  | prompt | contra-instrucción explícita a la frase que inyecta el servidor | `compact.py:33-35` |
  | detección | `MIN_RESUMEN_CHARS=600` ⇒ resumen migaja ⇒ **se descarta la compactación y se conserva el historial entero** | `compact.py:41`, `loop.py:348-356` |
  | encadenado | no se recompacta hasta que el historial crece un 50 % | `loop.py:330` |

  **Causa raíz**, y es artefacto de servidor, no «el modelo vuelve a pensar»: el arranque de
  Qwen3.6 lleva `--reasoning-budget 2048 --reasoning-budget-message "Cierra el razonamiento y
  responde."` (`README.md`), así que al agotarse el presupuesto **el servidor inyecta una orden
  dentro del razonamiento del propio modelo** y descarrila la petición de resumen.
- **Convergencia con A, corrección de lo que dije antes:** desactivar el razonamiento en la
  llamada de compactación **no es remedio de modelo local**. A lo hace igual —
  `thinkingConfig: { type: 'disabled' }` (`compact.ts:1305`). Lo que **no** se porta es el
  `except: reintentar sin ello` silencioso de la prueba: viola `D-21`. B pide
  `ThinkingConfig(enabled=False)`, y ante `UnsupportedModelOptionError` reintenta una vez sin
  ello **declarándolo** en el evento/traza.
- **Divergencia declarada con cita:** A manda `[FileReadTool]` en el camino de streaming
  (`compact.ts:1281-1290`) y el toolset entero del padre en el camino bifurcado (para que case
  la clave de caché). B manda **ninguna**: no tiene fork ni caché de prompt compartida, y
  `createCompactCanUseTool` (`:1125-1134`) deniega toda ejecución de todos modos.
- **Vocabulario que evita la trampa:** *vuelta* = una iteración del lazo (una llamada al modelo
  + sus despachos); *turno* = un intercambio con el usuario (`AgentLoop.run`). La compactación
  dispara en el límite de **vuelta**, a mitad de tarea, antes de `callModel`. La trampa está en
  el propio código de B: `_turn`/`ctx.turn_count` son vueltas, `ConversationState.turn_count`
  son mensajes de usuario.

**Inyectado en el tramo 1 (4 ficheros):**
- `context/estimation.py` (**nuevo**) — homólogo de `services/tokenEstimation.ts:203-435` más el
  ancla de `utils/tokens.ts`: `rough_token_count` (4 B/token, `Math.round` reproducido con
  `math.floor(x+0.5)` porque el `round` de Python es bancario), densidad 2 B/token para
  `json/jsonl/jsonc`, **2000 fijos** por bloque `image`/`document` (el catch-all cobraría ~325k
  por un PDF de 1 MB en base64), `tool_use` = nombre + input serializado, recursión en
  `tool_result`, y sólo cuentan `user`/`assistant`. `truncate_to_tokens` con marcador.
- `context/window.py` — las cinco constantes `POST_COMPACT_*` (`compact.ts:122-130`) y los dos
  guardas empíricos; `ContextBudget` gana siete campos y `_assemble` pasa de ocho posicionales a
  recibir el invocable `scaled`.
- `context/__init__.py` — reexportes.
- `tests/test_context_window.py` (**nuevo**) — 20 casos, criterio y citas en la docstring.

**Lo que escala y lo que NO (`D-41` + medida):** los cinco `POST_COMPACT_*` **escalan** —5
ficheros × 5k serían el 80 % de una ventana de 32 768—, con suelo de 1 para que la restauración
no quede muerta. `min_summary_chars` y `recompaction_growth_ratio` **no escalan**: 600 × 0,16 =
96 caracteres es exactamente la longitud de migaja que el guarda existe para rechazar. La
política `canonical` los declara desactivados (0 / 1.0) porque A sólo comprueba `if (!summary)`
(`compact.ts:493`) — desactivar no es inventarle a A una conducta que no tiene.

**Prueba:** `agentic_runtime/.../tests/test_context_window.py` **20 passed**; consumidor
(`agentic_code` `tests/test_context_window.py` + `test_presentation.py`) **11 passed**.

**PUNTO DE RETOMA — tramos 2→6, uno por ventana, cada uno con su prueba y su cierre aquí:**
2. `compact/prompt.py` (base + los dos parciales) y `compact/engine.py` con guardas, cortacircuitos
   (`MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3`) y frontera.
3. Punto de llamada **al principio del cuerpo de la vuelta** en `AgentLoop.run`, antes de
   `_build_tool_pool`, + cable `RuntimeConfig.context_budget` → `LocalAgentRuntime` → lazo;
   `agent_loop.py:573` pasa a mandar `messages_after_compact_boundary(ctx.messages)`; la
   compactación **no consume vuelta** (si no, roba en silencio de `--max-turns`). En
   `agentic_code/cli.py:256-265` el presupuesto sube por encima de `build_runtime` y se pasa a los dos.
4. Restauración post-compactación sobre `compact_context()` + estado de ficheros leídos.
5. PTL: clasificador, truncado de cabecera, reintento (`MAX_PTL_RETRIES = 3`, `PTL_RETRY_MARKER`).
6. Parcial + `/compact` en `agentic_code`; hooks (**`POST_COMPACT` no existe en
   `hooks/protocol.py`** ⇒ se construye, `D-22`); ampliar `D-42`.

**Deuda vigilada, no bloqueante:** nadie puebla `session.usage`
(`execution/local/runtime.py:562-567`), así que hoy el ancla de medida real no tiene quien la
alimente y todo se estima. Y sigue sin decidir la propuesta de `D-40` de diferir en el perfil
local las cinco tools de esquema más grande.

### 2026-08-21 — `D-38`: el lazo de tres pasos, por software (ejecutado)

Ventana de un paso, dentro de la fase viva (embudo `D-28`, etapa A). Ejecuta `D-37` y lo
registrado queda íntegro en `SEPARACION/DECISIONES.md § D-38`; aquí sólo el marcador.

- **Mecanismo fuera del cable:** `convert_responses_tools` deja de emitir `defer_loading` y el
  `{"type": "tool_search", "execution": "server"}`. Caen con él `supports_native_tool_search`
  (contrato y puente) y `NativeDeferredStrategy`; `SimulatedDeferredStrategy` pasa a
  `SoftwareDeferredStrategy`, rama única.
- **Convención aplicada:** las **13** nativas que llevaban `deferred = True` pasan a residentes
  (`Config`, `Enter/ExitPlanMode`, `Enter/ExitWorktree`, `TodoWrite`, `AskUserQuestion`, las seis
  `Task*`). `is_deferred_tool` adopta la regla estructural del canónico: `isMcp ⇒ diferida
  siempre`, por `mcp_info`, no por que el adaptador recuerde el atributo.
- **Etapas 2 y 3 homologadas al literal de A**, con el contrato de fallo que faltaba
  (`InputValidationError` + `select:<name>[,<name>...]`). Centinelas de parseo intactas.
- **Consecuencia medida:** sin servers MCP no hay diferidas ⇒ **no hay anuncio**, y el turno
  pierde un `MessageEvent`. Medido en el `.jsonl` real (`D-15`). `agentic_code` **218 passed**,
  `agentic_models` **52 passed**.
- **Deuda declarada:** las suites sintéticas de `agentic_runtime/.../tests/` referencian los
  símbolos retirados y **quedan rojas a sabiendas** (§ 4, no se tocan).
- **Pendiente inmediato, ya acordado:** revisar el **capability MCP** con el mismo método de censo
  que se viene usando con las nativas.

### 2026-08-16 — etapa 0 del embudo cerrada salvo dos declaraciones; abierta la etapa 1

La fase viva **no es este censo**: es el embudo `D-28`, y su marcador vive en
`EMBUDO-FASE-A.md`. Este censo aporta a la etapa 1 sólo el **orden de ataque 1→12** del § 3.

- **`T1` PAGADO** — `todo_write.py` recibe el bloque `## Examples` de
  `TodoWriteTool/prompt.ts:27-142` (4 ejemplos de uso + 4 de no uso, con sus `<reasoning>`),
  entre `## When NOT to Use This Tool` y `## Task States and Management`.
  `${FILE_EDIT_TOOL_NAME}` ⇒ `Edit`. **Barridos los comentarios del fichero** por la regla del
  § 4: lo que decían —`allDone ⇒ []`, `todoKey = agentId ?? sessionId`,
  `verificationNudgeNeeded` y la salvedad per-turno de `app_state.native`— está íntegro en el
  § Paso 2 de este censo, verificado antes de borrarlo.
- **`AUQ-1` PAGADO, con corrección del diagnóstico.** El `preview` del `inputSchema` de A es
  estático (`AskUserQuestionTool.tsx:17`) y no depende del formato: el «puntero roto» estaba
  también en la rama por defecto de A, así que **el esquema de B era FIEL y no se toca**. Lo
  que faltaba era la costura condicional de `prompt()`. Construida (`D-22`) como
  `AskUserQuestionTool(question_preview_format=None|"markdown"|"html")`, la declara el
  integrador —quien renderiza es el integrador—, y `agentic_code` declara `markdown`, que es
  lo que su TUI hace (`decision_view.py:294-303`). Dos frases del literal de A quedan fuera
  por FALSAS en B (layout side-by-side; «sólo single-select»), declaradas en `PROCEDENCIA`,
  donde además se **crea** la fila de `AskUserQuestion`, que no existía.
- **Queda de la etapa 0:** las declaraciones SIN NOTA de `bash` (§ 3.1 del volcado) y `Config`
  (§ 3.6), y la pasada orgánica de `FIND-WT6`.
- **Etapa 1 abierta.** Tool nº 1 = `TodoWrite` (paso 2 del orden de ataque; el paso 1,
  `FIND-EXITPLAN`, es puerta de modo y va a la etapa 2). Sus 4 enunciados de grado 1 + un
  control de no uso están escritos en `EMBUDO-FASE-A.md`, con la receta de corrida y el pool
  de 20 verificado. **Ronda 1 pendiente de la pasada orgánica del usuario** (`D-24`).
- Prueba de no regresión de lo tocado: suite de `agentic_code` **216 passed**; `ruff` y `mypy`
  limpios en los tres fuentes. No acredita nada del embudo — es red, no aval (`D-24`).

**Pasos cerrados:** 1 — `FIND-EXITPLAN` · 2 — `FIND-TODO` (`allDone ⇒ []`) · 3 — `FIND-EDIT` ·
4 — `FIND-CFG-2`. Todos ellos **bajados a «inyectados, pendientes de pasada orgánica»** por `D-24`.
**Inyectado en esta ventana:** `FIND-CFG-3` (catálogo de ajustes in-tree + cable `app_state`→petición,
2026-08-14), igualmente **pendiente de pasada orgánica**.
**Paso siguiente:** 5 — `FIND-WT2` (descripción de `ExitWorktree`), **sin abrir**.
**Commiteado** (palabra del usuario, 2026-08-14, para que Codex pueda trabajar sobre el árbol):
`agentic_code` `06e5ed0` en `fase-b/find-pool-1` · `agentic_runtime` `ff30127` en `fase-b/tramo-1`.

### `FIND-CFG-3` — el catálogo de ajustes vivía fuera del árbol (2026-08-14) — INYECTADO

**Cómo se destapó.** `E11` (`GATE_E11_SEED=1641356436`) midió al modelo conduciendo `Config` seis
veces con argumentos válidos y al runtime respondiendo `Error: Unknown setting: "model"`. El
diagnóstico que di primero —«registro vacío y sin costura para poblarlo»— **era falso en su mitad**:
la costura existe y el integrador la usa (`composition.py`, `ToolsConfig(extras=[ConfigTool(...)])`),
y `registry.py:18` registra por nombre, así que el extra pisa al nativo. Lo real era otra cosa.

**El defecto, contra el canónico.** En A no existe una `ConfigTool` sin catálogo: `ConfigTool.ts:126`
consulta `isSupported`, que lee `SUPPORTED_SETTINGS` del módulo hermano `supportedSettings.ts`
(211 líneas, **in-tree**), y `prompt.ts:18-46` genera el listado recorriendo esa misma constante. En
B el catálogo se había reducido a **una** clave declarada en el integrador, y `ConfigTool()` caía a
`EMPTY_REGISTRY` — una tool publicada en el pool nativo que sólo sabía decir `Unknown setting`.

**`isEnabled()` — no hay que homologar nada.** Leído `ConfigTool.ts` 1→EOF: el `buildTool` de
`:67-434` **no declara `isEnabled`**. La tool se publica siempre. Lo condicional en A es el catálogo
entrada por entrada (`supportedSettings.ts:134-185`, por `feature(...)`/`USER_TYPE`, y el
kill-switch de `voiceEnabled` en `ConfigTool.ts:116-125` + `prompt.ts:23-28`).

**Lo inyectado.**
- `tools/native/supported_settings.py` (nuevo) — homólogo de `supportedSettings.ts`: `SettingDescriptor`
  (se muda aquí, como el `SettingConfig` de A) y `SUPPORTED_SETTINGS` a nivel de módulo, con
  `model`, `alwaysThinkingEnabled` y `permissions.defaultMode`.
- `config.py` — `EMPTY_REGISTRY` **desaparece**; `ConfigRegistry()` defaultea al catálogo y
  `ConfigTool()` con él. Sin stores cableados el `set` responde `Invalid setting source`, que dice
  la verdad (el host no cableó almacenamiento) en vez de negar que el ajuste exista.
- `loop/agent_loop.py` — `_resolve_model_request`: el `appStateKey` de A (`supportedSettings.ts:94`,
  `mainLoopModel`) **no tenía cable en B**. `model_id` y `thinking` se resuelven por turno desde
  `app_state.native`; sin nada sembrado el turno sale idéntico a antes. `D-22`: se construyó.
- `agentic_code/composition.py` — deja de declarar ajustes (sólo aporta stores y etiquetas) y siembra
  en `app_state` lo persistido (`persisted_app_state`), que es lo que hace que el ajuste sobreviva
  a la sesión.
- `tools/dispatcher.py:69-71` — el `ASK` sin resolver **tiraba `decision.deny_message`** y rendía una
  frase genérica. Con esto `PLAN_REJECTION_PREFIX` tiene por fin consumidor.

**Red de regresión — NO es prueba de cierre (`D-24`).** Lo que sigue son suites guionadas: quedan
como red y **no se invocan como aval**. El cierre lo emitirá la pasada orgánica del usuario, con su
delator: pedirle al agente en REPL real que cambie el modelo de la sesión y comprobar que el turno
siguiente sale con el modelo nuevo (y que el `config.json` del proyecto lo lleva en disco).

`agentic_code` `tests/test_config_tool.py`: `test_setting_the_model_governs_the_request_of_the_next_turn`
mide `model_ids == ["model", "modelo-elegido"]` (el cambio alcanza al **turno en curso**) y
`["modelo-elegido"]` en la sesión siguiente; `test_disabling_thinking_reaches_the_request` mide
`ThinkingConfig(enabled=False)` en la petición. Runtime: `test_tool_dispatcher.py` gana los dos casos
del `deny_message` (rendido cuando el `ASK` no se resuelve, y no rendido cuando se concede).

**`E11` remedido tras la inyección (`GATE_E11_SEED=2947933778`).** El escenario que destapó el
hallazgo pasa a verde: `✔ ajuste-de-sesion → condujo ['Config']`, donde antes el runtime rendía
`Error: Unknown setting: "model"` seis veces seguidas. `Config` entra por primera vez en la lista de
conducidas: `['AskUserQuestion', 'Config', 'EnterWorktree', 'TaskList', 'TaskOutput', 'TaskStop']`.
El gate **sigue rojo por otros cinco escenarios**, y ninguno toca `Config`: `traer-una-url` y
`clonar-repo` y `editar-en-sitio` resueltos con `bash` en vez de `WebFetch`/`clone_repository`/`Edit`,
`worktree-ida-y-vuelta` que entra pero no sale (`EnterWorktree` + `bash`, sin `ExitWorktree`), y
`registrar-plan` delegando en `Agent` en vez de `TodoWrite`. Es el patrón gpt-5.x ya catalogado
—preferencia por `bash` y por delegar en `Agent`—, no regresión de esta inyección. `E11` corrió al
límite de 50 turnos. Su vigilante (`test_e11_vigila_carencias_declaradas`) cae por arrastre —el global
`_E11_CARENCIA_OBSERVADA` sólo se puebla si el gate completa—, no por carencia excusada. **Sigue siendo red de regresión, no aval de cierre.**

**Criterios reescritos, no ablandados.** `_e10_config` aseveraba que la tool del pool rechaza `model`
con `Unknown setting` — criterio del mundo en que la tool podía existir sin catálogo. Ahora asevera
que anuncia su catálogo, que una clave **fuera** de él sigue siendo `Unknown setting` y que sin store
no escribe. Igual en `test_config_solo_enumera_lo_que_su_catalogo_declara`.

### Pasada orgánica en vivo — T2 y diagnóstico de la TUI (2026-08-14)

Antes de abrir el paso 5 se está ejercitando `agentic_code` de verdad (sesión interactiva, nunca
`--print`) contra las conductas ya cerradas. Lo de esta ventana:

**T2 — gate de plan, veredicto: la conducta homologada es CORRECTA.** Reconstruido desde la
captura `20260814T001908-34d9290b3ecc.jsonl`: seq 77 `ToolCallEvent ExitPlanMode` (00:27:38) ⇒ 24 s
de modal ⇒ seq 80 `ToolResultEvent` con el **literal canónico de rechazo** (00:28:02) ⇒ seq 81
`TurnStartEvent` del turno 16 ⇒ seq 82 `result subtype=error_killed status=killed` (00:28:03.46).
La tecla fue **Esc**, que en `PermissionScreen` está bindeada a `choose('cancel')`; `cancel` no cae
ni en `_TURN_KEYS` ni en `_PROJECT_KEYS`, así que `PermissionPolicy.handle` devuelve
`HookDecision.blocked(deny_message)`. **El plan mode sobrevive al rechazo por construcción**: la
aprobación es una decisión de permiso (`ExitPlanMode.check_permissions` ⇒
`PermissionDecision.ask(plan, remember=False)`), y `execute` sólo corre si se concedió — luego
`PlanModeState.rearm()` es **código muerto**, y su retirada queda pendiente de decisión.

**Falta por certificar de T2:** repetirlo **aprobando** el plan, para ver el `tool_result` de
aprobación y que la tecla no entre en el historial de prompts.

#### Segunda corrida de T2 — `20260814T012230-46f5a22fbb83.jsonl` (01:22:30→01:26:21)

**El turno ya no muere.** `ExitPlanMode` en seq 39 (01:25:22) ⇒ 50,8 s de modal ⇒ seq 42 con el
mismo literal de rechazo e `is_error=true` ⇒ **turno 8** que relee el plan, **turno 9** que responde
en streaming, y cierre en `subtype=success status=completed` con `anomalies: []`. El `error_killed`
de la corrida anterior era del `Esc` sobre `PermissionScreen`, **no del gate**: Codex encaminó
`ExitPlanMode` a `PlanApprovalScreen` (`tui.py:1120-1125`), donde `Esc` va a `_reject()` y devuelve
`n <feedback>`. Confirmado por el usuario en vivo: la ventana de plan se muestra con Markdown y sus
dos botones, «Seguir planificando» y «Aprobar e implementar» ⇒ **requisito arrastrado, cumplido**.
Sigue siendo la rama de **rechazo**: la de aprobación no se ha ejercitado ni una vez.

**`H-7` (ABIERTO, hallado al revisar esta corrida).** Contenido de aprobación del canónico
(`ExitPlanModeV2Tool.ts:483-489`, leído 1→EOF): tras la primera línea van
`Your plan has been saved to: ${filePath}` y `You can refer back to it if needed during
implementation.`, antes del `## Approved Plan:`. `PLAN_APPROVED_TEMPLATE`
(`tools/native/plan_mode.py:25-28`) **omite esas dos líneas**, y no es inexpresable: B tiene
`get_plan_file_path(ctx)` y lo usa dos líneas más abajo. Fuera con razón el `teamHint` (cuelga de
`TeamCreateTool`, ausente en B) y la rama `isAgent` (`:452-459`).

**Sin certificar, declarado:** `PLAN_REJECTION_PREFIX` (`plan_mode.py:30-33`) **no aparece en
`ExitPlanModeV2Tool.ts`**. Procede de otro punto del canónico que no se ha leído; no se da por
genuino hasta contrastarlo.

**Para el catálogo de gpt-5.x:** cero `ThinkingEvent` en 181 registros y `thinking_tokens: 0` — la
superficie de razonamiento recién añadida no tiene qué pintar con este proveedor. Y se repite la
relectura redundante del plan (seq 34 y 44).

**Diagnóstico del «cuelgue» de la TUI — no era cuelgue, es coste de render.** Medido, no
afirmado, con dos capturas reales replicadas en `TranscriptStore`:

| | plegado | desplegado |
|---|---|---|
| 10 items (captura 00:19) | 35,1 ms | **1505,2 ms** |
| 14 items (captura 18:19) | 36,1 ms | **866,6 ms** |

Por tool, con `preview_lines=8`: `Edit` 263,0 ms (entrada 5112 B) · `write_file` 193,2 ms y
84,2 ms · `Agent` 38,0 / 31,5 ms — 681,3 ms en 16 tools. `store.apply` suma 2,5–20,5 ms y
`store.items` 0,04–0,08 ms: **la capa de dominio no es el coste**. Causa: `_limit_lines`
(`tool_view.py:93`) acota **sólo el resultado**, mientras la ENTRADA entra entera en Pygments
(`Syntax`, `:165`, `:172`) y en `Markdown` (`:190`); se suma el auto-despliegue del deck mientras
una tool está `RUNNING` (`transcript.py:228`) y el repintado del deck **entero** ante el cambio de
cualquiera de sus tools (`tui.py:389`). De ahí 0,2–1,5 s de bloqueo por ráfaga, que se libera al
terminar la tool y plegarse el deck. El REPL queda **exonerado** con repro headless de la ruta Esc.

**Entregado a Codex como requisito (la TUI no se toca desde aquí):** acotar la entrada como se
acota el resultado, **antes** de `Syntax`/`Markdown`; cachear el renderable por
`(tool.id, status, finished_at)`; repintar sólo las tools cuyo id esté en `changed_ids`. Y el
requisito arrastrado: encaminar `ExitPlanMode` a una pantalla de aprobación de plan —hoy cae en
`_render_fallback`, sin Markdown y con un botón `[p] proyecto` que aquí es aprobación de un solo
uso—, lo que exige que `PermissionReader` lleve el **nombre de la tool**.

**Requisito CUMPLIDO y remedido (2026-08-14, commit `f2fe6bc` de Codex).** Mismas capturas, mismo
banco, con el arreglo puesto: 10 items (00:19) **1505,2 ms ⇒ 411,5 ms** · 14 items (18:19)
**866,6 ms ⇒ 315,8 ms** · 10 items (01:22) 156,2 ms. `_limit_lines` acota ahora también la entrada
antes de Pygments (`tool_view.py:137`, `:166`), con caché y repintado selectivo en `tui.py`. Y el
nombre de la tool llega a la UX vía `PermissionRequest` (`permissions.py`), que además arrastra el
feedback del usuario al `deny_message`. Queda coste residual, pero ya no bloquea segundos.

**Deuda declarada, no tapada:** `composition.py`, `rendering.py` y `mcp_config.py` entraron en el
commit **conservando comentarios de ventanas anteriores**, en contra de la regla del §4. Barrerlos
habría sido una mutación grande y no anunciada dentro de un commit de coordinación. Queda medida y
vigilada; se paga al tocar cada fichero.

**Hallazgos abiertos de la pasada orgánica:** **H-4** — un subagente caído se sirve como
`"(no output)"` con `is_error=False`, contra `AgentTool/runAgent.ts` · **H-5** — `arm_watchdog` es
`pass` · **H-6** — notificación de tarea duplicada para el `Agent` en primer plano.

**Fuera del censo, para no perderlo:** `.env` está en `AGENTIC_CODE_MODEL=gpt-5.4` por la
comparación de modelos; vuelve a `gpt-5.4-mini` al terminarla. Turnos orgánicos pendientes: T1
(ficheros encadenados), T3 (`Edit` sobre CRLF), T4 (no encontrado + sugerencia), T5 (rechazo de
`.mcp.json`), T6 (valor inválido de `Config`), T7 (config de proyecto corrupta + copia, el último).

### Paso 4 — `FIND-CFG-2` — CERRADO (2026-08-13)

**Alcance ejecutado:** el algoritmo entero de `Config` con **almacén de verdad en el núcleo**,
la costura `check_permissions` con **default permisivo** y su override en `Config` (guarda 11,
que `D-22` devolvió a este paso), y el **registro poblado por el integrador**. Las **12
conductas** del §2 quedan portadas.

#### Certificación por línea canónica

Leídos 1→EOF en esta ventana y la anterior: `ConfigTool/ConfigTool.ts` (467) ·
`ConfigTool/supportedSettings.ts` (211) · `ConfigTool/prompt.ts` (93) · `Tool.ts` (792) ·
`utils/config.ts` (1818, en dos páginas) · `utils/settings/settings.ts` (1015).

| Conducta | Canónico | En B |
|---|---|---|
| 1 GET lee el valor REAL recorriendo `path` | `:136-144`, `:436-453` | `_read_path` sobre el almacén del `source`; ausencia = centinela `_MISSING` ⇒ `undefined` |
| 2 SET persiste | `:313-343`, `config.ts:1153-1329` | `ConfigStore.update` (fichero real, un solo escritor) |
| 3 `appStateKey` ⇒ efecto inmediato | `:356-362` | `context_modifier` que escribe `app_state.native[app_state_key]`; el descriptor de B no lo usa hoy y el efecto en caliente sigue siendo `FIND-CFG-HOT` |
| 4 coerción booleana + `${setting} requires true or false.` | `:185-201` | literal |
| 5 opciones ⇒ `Invalid value "X". Options: a, b` | `:204-214` | literal, con `", ".join` |
| 6 `validateOnWrite` asíncrono | `:217-229` | costura `validate_on_write` que admite síncrono o awaitable ⇒ `(valid, error)` |
| 7 `formatOnRead` en el GET | `:138-140` | costura `format_on_read` |
| 8 `buildNestedObject` sobre `key.split('.')` | `:208-211`, `:455-467` | `_assign` recursivo, **preservando identidad** si el valor ya estaba ⇒ el `update` no reescribe |
| 9 escritura envuelta ⇒ el error se devuelve | `:400-410`, `settings.ts:416-524` | `try/except` alrededor de `update`; `ConfigStore` **no lanza** al leer (fichero corrupto ⇒ defaults + copia) |
| 10 literales al modelo | `:412-433` | `{setting} = {json}` · `Set {setting} to {json}` · `Error: {msg}` con `is_error` |
| 11 GET auto-permitido, SET **pregunta** (`Set X to Y`) | `:98-107`, `:90-92` | `ConfigTool.check_permissions`; el criterio de sólo-lectura es literal: `"value" not in input` |
| 12 esquema estricto, `value ∈ string\|boolean\|number` | `:36-48` | `input_schema` con `additionalProperties: false`, lo hace cumplir `validate_tool_arguments` antes de `execute` |

**Almacén** — `saveConfigWithLock` (`config.ts:1153-1329`) + `getConfig` (`:1429-1488`):
lock (mkdir con reclamo por caducidad a 10 s, sustituto de `proper-lockfile`, que no está
instalado), copia con marca de tiempo bajo `backups/` con intervalo mínimo de 60 s y poda a 5,
`0o600`, `pickBy` de defaults al escribir y `{**defaults, **parsed}` al leer —los dos son la
misma pieza: se omite lo que vale el default y se repone al leer—, tira de BOM y copia del
fichero corrupto con deduplicación por contenido (`:1521-1561`).

**Costura de permisos** — `TOOL_DEFAULTS` (`Tool.ts:757-769`, aplicado en `buildTool`,
`:783-792`): `check_permissions` es **defaultable**, no miembro del `ToolProtocol`. Se sigue el
precedente ya existente de `tool_is_enabled`, para que el `runtime_checkable` no rompa a las
tools de terceros. El dispatcher la consulta **después** de validar el esquema, como A, que
llama `checkPermissions` sólo si `validateInput` pasó. Las otras 24 tools **no se tocan**: el
default permisivo *es* su conducta canónica.

**Registro poblado por el integrador:** una sola clave, `permissions.defaultMode`, la única de
`SUPPORTED_SETTINGS` con referente real en B (`PermissionMode`), y ejercita el camino anidado.
El **catálogo de producto** de A (temas, `editorMode`, canales, voz, teammates) sigue fuera por
el segundo límite de `D-22`. `generatePrompt()` (`prompt.ts:14-93`) sí se porta como
**mecanismo**: la descripción de la tool se genera desde el registro en el constructor, y por
eso la tool la entrega el integrador vía `ToolsConfig(extras=…)` — `ToolRegistry.register` pisa
por nombre y `create_tools` registra los `extras` después de las nativas, así que **no hace
falta tocar `factory.py`**.

**Dos escritores sobre un fichero, cerrado:** `JsonFileServerStore.save/remove` escriben ahora
por el mismo `ConfigStore` para los scopes `user` y `local` (`state_dir/config.json` y
`state_dir/projects/<key>/config.json`). El `.mcp.json` del workspace conserva su escritura
atómica: no lo comparte nadie y no procede sembrar un `backups/` dentro del repo del usuario.

**No portado y declarado:** vigía `fs.watchFile` de la caché del GET (`config.ts:1044-1086`) —
B no tiene un segundo proceso escribiendo el fichero · `wouldLoseAuthState` (`:1253-1288`) —
dominio de credenciales de A · `logEvent('tengu_config_tool_changed')` (`:383-389`) ·
ramas `feature('VOICE_MODE')`, `feature('BRIDGE_MODE')`, `KAIROS`, `USER_TYPE === 'ant'` ·
el catálogo de ajustes. **`FIND-CFG-HOT` sigue ABIERTO**: `Settings` continúa congelada y el
prompt/las opciones de modelo se hornean una vez, así que un SET de esas claves tampoco tendría
efecto en caliente — por eso no se registran.

#### La prueba — `agentic_code`, y sólo `agentic_code`

`agentic_code/tests/test_config_tool.py` (NUEVO, `ConfigCallingCaller`): siete corridas reales,
midiendo por EFECTO (bytes de `config.json`) y sobre el `{"role": "tool"}` que entra en la
historia:

1. SET ⇒ `Set permissions.defaultMode to "plan"` y el fichero anida `permissions.defaultMode`;
2. SET+GET ⇒ `permissions.defaultMode = "acceptEdits"`;
3. clave desconocida ⇒ `Error: Unknown setting: "editorMode"`;
4. valor fuera de opciones ⇒ `Error: Invalid value "turbo". Options: …` y **nada se escribe**;
5. sin concesión, el SET se **deniega** y el GET **no** (guarda 11 en el vehículo real);
6. el modo persistido gobierna el `permission_context` del **turno siguiente**, observado en el
   ctx que el runtime autoriza;
7. el registro llega a la **descripción que el modelo lee**, por `ToolSearch` (la tool es
   diferida, así que ése es su único camino al modelo).

**Verificadas como NO VACUAS** con tres plugins efímeros de pytest, sin tocar fuente:
registro neutralizado (`build_config_registry` ⇒ vacío, modo persistido ⇒ `None`) ⇒ caen 6 de 7;
`check_permissions` permisiva ⇒ cae **exactamente** la 5; prefijo `Error: ` retirado ⇒ caen 3 y 4.

Suite de `agentic_code`: **169 passed**. `ruff` + `mypy` limpios en los dos repos sobre lo tocado.

#### Lectura del §4 (regla de comentarios) adoptada en este paso

El texto literal del §4 obligaría, al tocar `composition.py` o `mcp_config.py`, a borrar toda su
documentación previa —incluida la ajena a este paso—. El precedente del paso 3 es el contrario y
está a la vista en `mcp_config.py`: su documentación quedó intacta y las funciones que el paso 3
escribió van sin comentarios. **Se adopta ese precedente:** el barrido cubre lo que el paso
escribe. Los ficheros nuevos y las funciones nuevas de este paso van sin comentarios ni
docstrings; la documentación preexistente ajena no se toca. Registrado como **`D-23`** en
`SEPARACION/DECISIONES.md`, con su límite: si el paso **reescribe** una función, su documentación
cae con ella, y un comentario que afirme conducta ya derogada se borra.

#### Desfase en suite apartada — NO SE TOCA y **NO VERIFICADO**

Este paso cambia por completo la salida de `Config` (de un blob JSON a los literales canónicos)
y añade una costura al dispatcher. Es previsible que alguna aserción sintética de
`agentic_runtime` afirme la conducta anterior. **No se ha comprobado**: por el §4 esas suites no
se corren ni se leen. Queda anotado para la reconstrucción.

#### Ficheros del paso 4 (10 + este censo)

`agentic_runtime/src/agentic_runtime/storage/config_store.py` (nuevo) ·
`agentic_runtime/src/agentic_runtime/storage/__init__.py` ·
`agentic_runtime/src/agentic_runtime/contracts/tools.py` ·
`agentic_runtime/src/agentic_runtime/tools/protocol.py` ·
`agentic_runtime/src/agentic_runtime/tools/dispatcher.py` ·
`agentic_runtime/src/agentic_runtime/tools/native/config.py` ·
`agentic_code/src/agentic_code/permissions.py` ·
`agentic_code/src/agentic_code/mcp_config.py` ·
`agentic_code/src/agentic_code/composition.py` ·
`agentic_code/tests/test_config_tool.py` (nuevo) · este censo.

### Regla de gobierno `D-22` — registrada (2026-08-10), reabre trabajo

Palabra del usuario: *«lo que no este se crea si con esto se consigue precisamente esto,
homologar comportamiento, algoritmo, etc de canonico. por tanto no cabria la pregunta si existe o
no en B.»* Registrada en `SEPARACION/DECISIONES.md` como **`D-22`** y aplicada aquí: §1 pregunta 2
**derogada como filtro de alcance**, §4 con la regla, §3 con la tabla de trabajo reabierto
(`FIND-CFG-PERM`, `FIND-EDIT-SECRETS`, `FIND-NOTEBOOK`, `FIND-CFG-HOT`, `FIND-MEM-WIRING`), y en el
§2 las tres conclusiones que se apoyaban en la pregunta derogada, tachadas y rehechas en sitio
(G2 y G8 de `FIND-EDIT`; guarda 11 y la pregunta 2 de `FIND-CFG-2`).

**Corrección de método, mismo día, a instancia del usuario:** tras aplicar `D-22` sometí a su
decisión dos puntos del alcance del paso 4 —si el almacén único entraba ya, y si `check_permissions`
iba detrás—. Su respuesta: *«no entiendo porque me pides que decida yo, algo que en un proceso de
homologacion ya esta dicho del lado canonico que es la referencia»*. Correcto, y es `D-08`: los dos
estaban contestados en A —`saveConfigWithLock` como escritor único (`config.ts:1153-1329`) y
`TOOL_DEFAULTS` permisivo + override de `ConfigTool` (`Tool.ts:757-769`, `ConfigTool.ts:98-107`)— y
lo que yo llamaba «decisión» era una estimación mía de tamaño, no un hallazgo. **Lo que el canónico
dicta no se somete a decisión; se lee.** Al usuario se le consulta lo que A no contesta: el catálogo
de producto, el orden entre pasos, el commit.

**Los pasos 1, 2 y 3 NO se reabren.** Lo que `D-22` les quita no es lo inyectado sino dos
exclusiones que se declararon cerradas: G2 y G8 salen de «trabajo inexistente» y pasan a
`FIND-EDIT-SECRETS` y `FIND-NOTEBOOK`, con paso propio.

### Paso 3 — `FIND-EDIT` — CERRADO (2026-08-10)

**Alcance tras contrastar la fila con las tres preguntas del esquema (§1):** guardas
**1, 4, 5, 6, 7, 11**; las dos divergencias de matching **con su mitad de escritura**
(restitución de finales de línea, `preserveQuoteStyle`); y las **cuatro conductas del camino de
éxito** que el censo no recogía. Fuera: **2 y 8**, sin referente en B (razonado en el §2).

**Ficheros tocados (4 + este censo):**
`agentic_runtime/src/agentic_runtime/tools/native/edit_text.py` (**nuevo**: matching, comillas
tipográficas, encoding/finales de línea, escritura atómica, mensajería — equivalente de
`FileEditTool/utils.ts` + `utils/fileRead.ts` + helpers de `utils/file.ts`; no cabe dentro de la
tool y `write_file` lo heredará en su paso) ·
`agentic_runtime/src/agentic_runtime/tools/native/file_edit.py` (reescritura de `execute` +
`EDIT_CONFIG_VALIDATORS_KEY`) · `agentic_code/src/agentic_code/mcp_config.py`
(`is_mcp_project_file`, `validate_mcp_config_content`) ·
`agentic_code/src/agentic_code/composition.py` (siembra del par predicado+validador de G11, por
`cablear-en-agentic-code-al-cerrar`). Prueba nueva: `agentic_code/tests/test_edit_tool.py`.

**Lo que NO está en `edit_text.py` y en A sí:** la mitad de PRESENTACIÓN de
`getPatchForEdits` (el `patch` estructurado que alimenta la UI de diff y el contador de líneas)
y sus `throw` de display. B no renderiza diffs de edición. Se portó la mitad que decide el
CONTENIDO.

**Correcciones al censo hechas al abrirlo** (todas ya aplicadas arriba, no pendientes):
1. Defecto de esquema del censo entero, con sus tres preguntas — §1.
2. Cuatro conductas del camino de éxito ausentes en la fila `FIND-EDIT` — §2.
3. G2 y G8 marcadas sin referente; qué se cae con ellas y cuándo vuelven a ser exigibles — §2.
4. Alcanzabilidad de G11 (`.mcp.json`, y por qué las otras tres configs no) — §2.
5. `read_file` **retirado** de «paridad real» ⇒ `FIND-READ-ENC`, abierto — §2.
6. Tamaño del paso 3 en el §3: de «pequeño» a «medio», y su enunciado corregido.

**Corrección de un error MÍO, no del censo:** en la ventana anterior sostuve que el censo daba
G11 por dependiente del paso 4 / del depósito. Es falso: su fila siempre dijo «no». El encuadre
equivocado era mío y no había que corregir nada ahí.

**Certificación por línea canónica** — `FileEditTool/FileEditTool.ts`, `FileEditTool/utils.ts`,
`utils/fileRead.ts`, `utils/file.ts`, `utils/format.ts` y `utils/settings/validateEditTool.ts`,
leídos enteros (1→EOF) en esta ventana. Orden de `execute` = orden de `validateInput`:

| Conducta | Canónico | En B |
|---|---|---|
| UNC | `:179-181` | primero, **antes** de la comprobación de absoluta: en POSIX `\\srv\share` no es absoluta y saldría por el mensaje equivocado tras haber tocado disco. A la deja pasar a permisos; B confina a workspace y la rechaza |
| `old === new` | `:148` | literal `No changes to make: old_string and new_string are exactly the same.` |
| techo 1 GiB | `:84`, `:186-200` | literal, con `formatFileSize` (`format.ts:9-23`) y `_fixed1` medio-arriba como `toFixed(1)` de JS |
| BOM `ff fe` ⇒ UTF-16LE, CRLF→LF | `fileRead.ts:20-49`, `:75-98` | `read_file_with_metadata`: finales detectados sobre los **4096 primeros bytes y ANTES** de normalizar, `CRLF` sii `crlf > lf` |
| restitución al escribir | `file.ts:84-98` | `write_text_content`: normaliza a LF antes de rehacer CRLF (si no, un `new_string` con `\r\n` daría `\r\r\n`) |
| escritura atómica | `file.ts:362-478` | temporal `pid+ms` + `os.replace`, **sigue symlinks** y **preserva el modo**; vuelta a escritura directa si el `rename` falla |
| no existe + `old===''` ⇒ crear | `:226-228` | igual |
| no existe ⇒ error + sugerencia | `:230-245`, `file.ts:213`, `:228-267`, `:178-207` | literal, con `suggestPathUnderCwd` **por delante** de `findSimilarFile`; el cwd se pasa como argumento, no por global (`FIND-WT1`) |
| existe + `old===''` | `:249-263` | `content.strip() != ''` (fichero de sólo blancos cuenta como vacío) |
| `findActualString` | `utils.ts:73-93` | devuelve la subcadena REAL del fichero, no la buscada |
| no encontrado | `:316-327` | literal `String to replace not found in file.\nString: {old_string}` |
| multiplicidad | `:329-343` | recuento sobre la cadena REAL; el literal de A ofrece `replace_all`, que B no tiene ⇒ se conserva la forma sin ofrecer lo inexpresable (`opcion-inexpresable-se-rechaza`) |
| `preserveQuoteStyle` | `utils.ts:104-199` | con `isOpeningContext` (rayas em/en incluidas) y el apóstrofo entre letras ⇒ siempre derecha |
| borrado que arrastra el `\n` | `utils.ts:206-228` | igual |
| `old===''` sustituye el contenido ENTERO | `utils.ts:314-322` | explícito: `content.replace("", new, 1)` de Python lo antepondría |
| fichero vacío con ambos vacíos ⇒ `''` | `utils.ts:275-294` | igual |
| fallo en firme si nada cambió | `utils.ts:326` | `EditNotApplied`. El segundo `throw` (`:334`) coincide con el primero habiendo un solo edit |
| validación de config + **escape** | `validateEditTool.ts:14-45` | si el contenido ya era inválido ANTES del edit, se permite. Sin el escape, un `.mcp.json` roto sería inarreglable por la tool que tendría que arreglarlo |
| resultado al modelo | `:592` | literal `The file {file_path} has been updated successfully.` |

**No portado y declarado** (aquí, ya no en el fuente, por la regla nueva del §4):
G2 y G8 sin referente (§2) · G3 deny rule, G9 read-before-edit, G10 stale-read y el recheck
TOCTOU de `call()` (`:451-468`), los cuatro colgados del depósito ⇒ pasos 7, 10 y 11.
**Mientras falten, este `Edit` puede pisar una escritura ajena sin avisar.**

#### La prueba — `agentic_code`, y sólo `agentic_code`

`agentic_code/tests/test_edit_tool.py` (NUEVO, `EditCallingCaller`): cinco turnos reales de
`agentic_code`, midiendo por EFECTO —los bytes del fichero— y, donde el punto es el rechazo,
sobre el `{"role": "tool"}` que entra en la historia, o sea lo que el modelo ve:

1. fichero CRLF editado ⇒ sigue **entero** en CRLF;
2. `old_string` con comillas rectas casa contra fichero con tipográficas **y las restituye**;
3. edit que rompería `.mcp.json` ⇒ **rechazado** y el fichero **intacto**;
4. `.mcp.json` ya roto ⇒ el edit **pasa** (escape), aunque siga roto después;
5. borrar una línea **no deja línea en blanco**.

**Verificadas como NO VACUAS**, una a una, con plugin efímero de pytest (`NEUTRALIZA=…`) que
neutraliza **sólo** la conducta nueva, sin tocar fuente: `crlf` ⇒ cae 1; `quotes` ⇒ cae 2;
`guard` (validación fuera) ⇒ cae 3; `escape` (guarda sin escape) ⇒ cae 4; `delete` ⇒ cae 5.
Cada modo tumba **exactamente un** test y deja los otros cuatro verdes.

Primera redacción del test 4 reparaba el fichero a JSON válido y por eso **no medía el
escape**: pasaba igual con el escape quitado. Se reescribió para que el resultado siga siendo
inválido, que es el único caso donde el escape decide.

Suite de `agentic_code`: **152 passed**. `ruff` + `mypy` limpios en `agentic_runtime` (los dos
ficheros) y en `agentic_code` (25 ficheros).

#### Desfase en suite apartada — NO SE TOCA y **NO VERIFICADO**

Este paso cambia literales que el modelo ve (`Edited {file_path}` → el literal canónico, y el
mensaje de no-encontrado) y añade conducta de escritura. Es previsible que alguna aserción de la
suite sintética de `agentic_runtime` los afirme. **No se ha comprobado**: por el §4 esas suites
no se corren ni se leen en esta fase, y afirmar aquí un desfase concreto sin haberlo visto sería
inventarlo. Queda anotado para la reconstrucción.

**Hallazgo colateral ABIERTO, ajeno al paso 3 — `FIND-MEM-WIRING`:** `agentic_code` no cablea
memoria por ningún camino (`factory.py:210` sólo registra `MemoryProvider` con `memory_root` o
`memory_store`; `composition.py:235` pasa sólo `mcp_config_store`) ⇒ toda la capa
`capabilities/memory/` es inalcanzable en el único vehículo de prueba admitido por el §4.

### Paso 2 — `FIND-TODO` (`allDone ⇒ []`) — CERRADO (2026-08-10)

**Inyectado** en `agentic_runtime/src/agentic_runtime/tools/native/todo_write.py:125-144`: el
`context_modifier` ya no almacena `todos`, almacena `[] if all_done else todos`.

**Certificación por línea canónica** — `TodoWriteTool/TodoWriteTool.ts:65-102`, releída en vivo:

```ts
const allDone = todos.every(_ => _.status === 'completed')   // :69
const newTodos = allDone ? [] : todos                        // :70
context.setAppState(prev => ({ ...prev, todos: { ...prev.todos, [todoKey]: newTodos } }))  // :88-94
return { data: { oldTodos, newTodos: todos, ... } }          // :96-102
```

**Detalle que el censo no recogía y que hay que portar con cuidado:** lo que se ALMACENA es
`newTodos` (vaciado); lo que se DEVUELVE es **`todos`** (`:99`), no `newTodos`. A informa al
modelo lo que el modelo escribió y guarda el vaciado. Nuestro `output` ya devolvía `todos`, así
que sólo cambió el `modifier`. `all([])` en Python ≡ `[].every()` en JS (ambos ciertos) ⇒ la
lista vacía entra por la misma rama, sin caso especial.

**No portado y declarado** (en el fuente, no sólo aquí):
- `todoKey = context.agentId ?? getSessionId()` (`:67`) — es el **paso 9**; depende del paso 7.
- `verificationNudgeNeeded` (`:76-86`, `:104-113`) — cuelga de `feature('VERIFICATION_AGENT')`
  y del flag de growthbook `tengu_hive_evidence`: experimento de A, no conducta general.

**Salvedad declarada (abierta, la cierra el paso 7):** `_TODOS_KEY` vive en `app_state.native`,
que muere con el turno ⇒ el vaciado sólo es observable DENTRO del turno.

#### La prueba — `agentic_code`, y sólo `agentic_code`

`agentic_code/tests/test_runtime_integration.py::test_a_finished_checklist_does_not_survive_into_the_next_write`
(NUEVA, con `TodoCallingCaller`). Tres `TodoWrite` en un mismo turno —lista viva, la misma toda
`completed`, y una tercera— midiendo sobre el `{"role": "tool"}` que entra en la historia: es
decir, **lo que el modelo ve en la vuelta siguiente**, no un campo interno. Comprueba las tres
cosas: que la lista viva sí se arrastra (si no, pasaría por no guardar nada nunca), que la
cerrada **no resucita** (`old_todos == []`) y que lo devuelto sigue siendo el input.

**Verificada como NO VACUA:** plugin efímero de pytest que reinstala el `execute` anterior, sin
tocar fuente ⇒ el test cae **exactamente** en la aserción del vaciado
(`old_todos` = la lista completada). Con la conducta puesta, verde.

Suite de `agentic_code`: **147 passed**. `ruff`/`mypy` sin avisos nuevos en lo tocado.

#### Desfase registrado en suite apartada — NO SE TOCA

`agentic_runtime/src/agentic_runtime/tests/test_tramo1_gate.py:3157` (`_e10_todo_write`) afirma
`ctx.app_state.native["todos"] == nuevos` con `nuevos` entero en `completed`. Tras este paso esa
afirmación **es falsa** y rotula como canónica la conducta derogada. **Se deja como está**, por
el §4. Cuando se reconstruyan las sintéticas, la línea correcta es `== []`.

En esta ventana llegué a editarla y **se revirtió**: la regla que lo permitía («se toca en una
línea, como anexo») se retiró del §4 por este mismo caso.

### Paso 1 — `FIND-EXITPLAN` — CERRADO (2026-08-09)

**Inyectado** en `agentic_runtime/src/agentic_runtime/tools/native/plan_mode.py:252-278`:
guarda de **modo** como PRIMERA comprobación de `ExitPlanModeTool.execute`, leyendo
`_PLAN_MODE_KEY` de `app_state.native` (el mismo asiento que escribe `EnterPlanMode` en
`:173`), con el mensaje canónico **literal**. La guarda de plan-file se conserva **detrás**,
no se sustituye: es propia de B (A recibe el plan por input, nosotros lo leemos del fichero).

**Certificación por línea canónica** — `ExitPlanModeTool/ExitPlanModeV2Tool.ts:203-218`
(`validateInput`, errorCode 1), releída en vivo en esta ventana:

```ts
const mode = getAppState().toolPermissionContext.mode
if (mode !== 'plan') { … message: 'You are not in plan mode. This tool is only for exiting
  plan mode after writing a plan. If your plan was already approved, continue with
  implementation.', errorCode: 1 }
```

Y su razón, que en B vale igual (`:201-203`): la tool se anuncia **esté o no en modo**
(`deferred = True`), y el rechazo va **antes de `checkPermissions`** «to avoid showing the
approval dialog».

**No portado y declarado** (en el comentario del fuente, no solo aquí):
- `isTeammate()` (`:198-200`) — B no tiene concepto de teammate ⇒ rama inaplicable.
- `logEvent('tengu_exit_plan_mode_called_outside_plan')` (`:204-209`) — telemetría de A.

**Salvedad declarada (abierta, la cierra el paso 7):** `_PLAN_MODE_KEY` vive en
`app_state.native`, que muere con el turno. En `agentic_code` lo repone `PlanModeState`
(`composition.py:65-77`); un integrador que no lo reponga vería falso rechazo.

#### Lo que destapó al inyectarla (hallazgo colateral, ya pagado)

Los dos E2E de plan de `agentic_code` —`test_an_approved_plan_lets_the_agent_out_of_plan_mode`
y `test_a_rejected_plan_puts_the_agent_back_in_plan_mode`— **salían de un plan mode en el que
nunca entraban** y pasaban. No se ablandó la guarda: se reescribió el guion con el criterio,
añadiendo `EnterPlanMode` al preludio. Ahora el round-trip es real.

#### La prueba — `agentic_code`, y sólo `agentic_code`

`agentic_code/tests/test_hitl.py::test_exiting_a_plan_mode_never_entered_opens_no_door`
(NUEVA). Con plan-file escrito y sin `EnterPlanMode`: la tool erra con el mensaje canónico, el
turno **no** se cede y al humano **no** se le pide aprobar nada — que es la consecuencia
entera de la guarda, no sólo su rama de error.

**Verificada como NO VACUA:** neutralizando sólo la guarda (plugin efímero de pytest, sin
tocar fuente) el test **falla por timeout** — la puerta se abre y nadie contesta. Con la
guarda, verde.

Suite de `agentic_code`: **146 passed**. Lint (`ruff` + `mypy`) limpio en lo tocado.

#### Anexos (NO son la certificación)

Tocados de paso, porque el diff los deja inconsistentes si no:
- El `xfail(strict=True)` `FIND-PLAN2` de `tests/test_cap_plan_homologation.py` dejó de ser
  xfail (con strict, seguir pasando lo pondría en rojo). Ahora exige el literal canónico y que
  no se siembre `_PLAN_EXIT_PENDING_KEY`.
- Docstring corregida en `tests/test_plan_mode_binding.py:83`: llamaba a la guarda de
  plan-file «homólogo del guard del canónico». No lo es — es el error de
  `homologar-es-trasladar-conducta` puesto por escrito.

#### Desvío de método cometido en este paso (queda escrito para no repetirlo)

Tras cerrar la prueba en `agentic_code` se corrió la suite de `agentic_runtime` y se fue a
perseguir sus 4 fallos de gate de modelo en vivo (`E9`, `E2f`, `E11`, `E11_vigila`). **Eso
estaba fuera de sitio por decisión previa**: el §4 dice que la verdad del resultado es
`agentic_code` y que las pruebas sintéticas de hoy **se reconstruyen después**
(`validacion-por-consumidor-real`). Litigar esa suite ahora no certifica nada y consume
modelo en vivo.

Lo único que merece conservarse de aquel desvío, como dato y no como certificación:
- En las trazas de las corridas de `E11`, `PlanMode` aparece **0 veces** — el modelo nunca
  llamó a `Enter`/`ExitPlanMode`, luego la guarda no estuvo en ningún camino ejecutado.
- **`FIND-GATE-PARPADEO` (ABIERTO, ajeno a esta fase):** `E9` y `E2f` cambian de rojo a verde
  **con el mismo código** — `E9` falló en suite y pasó aislado; `E2f` falló, pasó y volvió a
  fallar con `GATE_E2F_SEED=1` **fijo** (la semilla fija el escenario, no el muestreo). Es la
  misma patología que `FIND-E11-3` ya corrigió en la vigía de `E11` —*«parpadeaba en rojo y
  verde con el mismo código»*, `test_tramo1_gate.py:4216`— y que nunca se aplicó a estos dos.
  Se anota para que, cuando se reconstruyan las sintéticas, su rojo no se lea como ruido ni su
  verde como prueba.

### Estado del árbol al cerrar el paso 2

**Sin commit.** Y ojo al preparar el commit de control: ambos repos traen ficheros modificados
**de ventanas anteriores, ajenos a este paso** — `agentic_runtime`: `models/caller.py` y los
tests `test_capability_persistence/_registration_e2e/_wiring`, `test_deferred_delta`,
`test_model_options_reasoning`, `test_tramo1_gate`; `agentic_code`: `src/agentic_code/rendering.py`,
`tests/test_reasoning_surface.py`, `tests/test_runtime_integration.py`. **No barrerlos dentro
del commit de este paso sin decidirlo antes.**

Ficheros del paso 1 (5):
`agentic_runtime/src/agentic_runtime/tools/native/plan_mode.py` ·
`agentic_runtime/src/agentic_runtime/tests/test_cap_plan_homologation.py` ·
`agentic_runtime/src/agentic_runtime/tests/test_plan_mode_binding.py` ·
`agentic_code/tests/test_hitl.py` · este censo.

Ficheros del paso 3 (6):
`agentic_runtime/src/agentic_runtime/tools/native/edit_text.py` (nuevo) ·
`agentic_runtime/src/agentic_runtime/tools/native/file_edit.py` ·
`agentic_code/src/agentic_code/mcp_config.py` ·
`agentic_code/src/agentic_code/composition.py` ·
`agentic_code/tests/test_edit_tool.py` (nuevo) · este censo.
Los cuatro fuentes van **sin comentarios**, por la regla nueva del §4; el barrido de los
comentarios que quedan en el resto de ambos repos **no se hace de golpe**: cada fichero se
limpia cuando un paso lo toque.

Ficheros del paso 2 (3):
`agentic_runtime/src/agentic_runtime/tools/native/todo_write.py` ·
`agentic_code/tests/test_runtime_integration.py` · este censo.
`test_tramo1_gate.py` **no** es de este paso: lo que se le hizo está revertido y su diff
vigente es íntegramente de ventanas anteriores (verificado con `git diff -U0`).

## § 5 · addendum 2026-08-25 — tramo 2 cerrado

Hecho: `context/compact/prompt.py` (port de `prompt.ts` 375), `context/compact/engine.py`
(guardas de historia vacía / resumen vacío / prefijo de error de API / suelo local, cortacircuitos
`MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3`, freno de rebrote, frontera y `strip_images`),
`CompactionEvent`, reexportación y `tests/test_compact_engine.py` (27 verdes). Detalle y
divergencias en `SEPARACION/DECISIONES.md § D-43`.

Retoma por el tramo 3: punto de llamada al inicio del cuerpo de vuelta de `AgentLoop.run`
(`loop/agent_loop.py:496-512`), cableado del presupuesto (`RuntimeConfig.context_budget` →
`LocalAgentRuntime` → bucle), `agent_loop.py:573` mandando `messages_after_compact_boundary`, y
`AgentLoop._emit` como `emit` del motor. La compactación NO consume vuelta.

## § 5 · addendum 2026-08-26 — tramo 4 cerrado

Hecho: `context/file_state.py` (nuevo, depósito de ficheros leídos), asiento en
`tools/native/read_file.py`, `context/compact/restore.py` (nuevo), enganche en
`context/compact/engine.py` (`ctx=`, `provider_messages=`, hook `PostCompact`),
`loop/agent_loop.py::_compaction_provider_messages` —el consumidor que le faltaba a
`collect_compaction_context`—, `hooks/protocol.py` (`POST_COMPACT`), y la docstring rancia
de `contracts/compaction.py` **borrada**. Pruebas: `test_compact_restore.py` 14 +
`test_compact_engine.py` 27 = 41 verdes; `agentic_code` 231 verdes con los dos casos nuevos
de `tests/test_compaction_wire.py`. Detalle y divergencias en `SEPARACION/DECISIONES.md § D-45`.

Hallazgo del tramo, anotado: `agentic_code` **no** siembra
`POST_COMPACT_RESTORE_EXCLUSION_KEY`. El plan-file no puede restaurarse de todos modos —el
depósito guarda la ruta resuelta, fuera del workspace, y la exención del candado vale para la
grafía del token—; el predicado se implementó, se falsificó y se retiró. La consecuencia queda
vigilada por un test.

Retoma por el tramo 5: reintento por PTL (`truncateHeadForPTLRetry`, `compact.ts:243-291`).

## § 5 · addendum 2026-08-26 — tramo 5 cerrado

Hecho: `truncate_head_for_ptl_retry`, `group_messages_by_api_round`, el marcador sintético
`PTL_RETRY_MARKER`, el lazo de reintento en `compact_conversation`, el parseo del gap desde el
texto del error, y el pago del hueco del estimador (`TRANSPORTED_ROLES` incluye `tool`).
Detalle, divergencias y las nueve mutaciones de acreditación en
`SEPARACION/DECISIONES.md § D-46`.

## § 5 · addendum 2026-08-26 — tramo 6 cerrado (último del arco K6)

Hecho, en `agentic_runtime`: `partial_compact_conversation` y
`split_partial_compact_messages`, `annotate_boundary_with_preserved_segment`,
`CompactionResult.direction` y `build_post_compact_messages` sensible a dirección, el lazo de
PTL y la validación del resumen factorizados en un solo cuerpo para las dos rutas, y
`CompactionEvent` con `direction`/`messages_kept`/`messages_summarized`.
En `agentic_code`: `/compact` con instrucciones opcionales
(`compaction.py` nuevo, `ManualCompaction`), `build_model_caller` extraído de
`build_runtime` para que el comando use el MISMO puente que el turno,
`ConversationState.append` (asiento del bloque en el transcript, que es la fuente de verdad
porque `dispatch_prompt` hace `reload()`), y el cable `cli.py` → `WorkspaceRepl` →
`BuiltinCommandContext`.

`POST_COMPACT` **ya existía**: lo construyó el tramo 4 (`hooks/protocol.py:30`). El enunciado
de retoma que decía lo contrario estaba rancio; se anota y no se reconstruye nada.

Pruebas: `test_compact_engine.py` **49 verdes** (sección E nueva, 12 casos), acreditados por
nueve mutaciones revertidas desde copia verificada por `sha256` —todas muertas—;
`test_compact_engine` + `test_compact_restore` + `test_context_window` + `test_events`
= **96 verdes**. Detalle y divergencias en `SEPARACION/DECISIONES.md § D-47`.

**Pendiente del tramo, PAGADO en la misma ventana**: los casos de consumidor de `/compact`
en `agentic_code/tests/test_compaction_wire.py` (`D-15`) y la pasada de la suite.

## § 5 · addendum 2026-08-26 — la parcial EXPUESTA en el integrador (cierre del tramo 6)

Hecho, en `agentic_code`: `/compact from:N` y `/compact upto:N` con texto libre detrás que
viaja como `user_context`; `selectable_pivot_indices` (homologado de
`selectableUserMessagesFilter`, `MessageSelector.tsx:767-791`); `/history` publicando la lista
numerada de pivotes, que es la superficie que el ordinal necesitaba; el rastro del comando
añadido al final del bloque ya ordenado; y la traducción de `NotEnoughMessagesError` por su
MENSAJE, que era defecto propio y se paga aquí.
En `agentic_runtime`: `is_local_command_message` retirada por no tener consumidor (`L09`) y
sustituida por `is_local_command_output_message`, que sí lo tiene.

Divergencia declarada (`D-21`/`D-22`): `upto:` se expone pese a que A lo esconde tras
`if ("external" === 'ant')` — ese portón es catálogo de producto. Y
`ERROR_MESSAGE_NOTHING_AFTER` queda declarado **inalcanzable** por esta superficie.

Pruebas: `agentic_code` **247 verdes**, con 7 casos nuevos acreditados por **9 mutaciones
revertidas → 9 rojas, 0 falsos positivos**, restauración verificada por `sha256`. Sin procesos
supervivientes. Detalle en `SEPARACION/DECISIONES.md § D-48`.

Retoma: la **sonda de ejecución** desde `agentic_code`, con enunciado expreso (resultado
funcional, uso de tools, t/s, tiempo, declaraciones de compactación) y el riesgo del KV `q4_0`
a examen.
