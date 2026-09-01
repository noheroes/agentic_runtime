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

### 2026-08-31 (e) · E2E de fase de TOOLS · PAGADO, y abre `FIND-CODE-ABORT-TOOLS-1`

Restaurada la GPU (`wsl --shutdown`; `llama-server` en `:8080`, RTX 5080), se rehace el E2E
que quedó bloqueado en `(d)`. Arnés de scratch `esc1_e2e_tools.py` (`STATE`, `TRAS`,
`PROMPT`): reproduce ESC como lo hace la TUI —`operation.cancel()` sobre el turno
(`repl.py:290-296`), no `runtime.cancel` directo— colgado del primer `ToolCallEvent` más
`TRAS`. Tool de corte: `Sleep`, que no consulta `ctx.stop` (`native/sleep.py:44`) y por eso
fija la duración de la fase de tools sin depender del shell. Dos mitades:

**Mitad canónica — la evidencia que faltaba** (`Sleep(3)`, `TRAS=0.5`, corte a `t+21.6`,
tool cerrando a `t+24.1`, dentro de la gracia de 5 s de `cancel`). El bucle reentra por
arriba con `_aborted(ctx)` y sale por `ABORTED_TOOLS` (`agent_loop.py:427-438`):
`ToolResultEvent` normal → `MessageEvent(origin=interrupt)` con
`INTERRUPT_MESSAGE_FOR_TOOL_USE` → `AbortEvent(reason=turn_cancelled, tool_use=True, turn=1)`.
Registro: `{"subtype":"error_during_execution","is_error":true,"status":"completed",
"end_reason":"aborted","abort_reason":"turn_cancelled"}`, sin clave `result` y con
`[ede_diagnostic] tail=user_text tail_origin=interrupt end_reason=aborted
stop_reason=tool_calls`. `abort.tool_use: true` y `ABORTED_TOOLS` quedan acreditados contra
modelo real.

**Mitad que abre hallazgo — `FIND-CODE-ABORT-TOOLS-1`, ABIERTO** (`Sleep(20)`, `TRAS=1`,
corte a `t+21.7` con la tool corriendo hasta `t+40.7`). La gracia expira a `t+26.7` y
`LocalAgentRuntime.cancel` cae al `kill` duro (`execution/local/runtime.py:212-214`). Medido:
**no se emite `AbortEvent`**, y el registro sale `{"subtype":"error_during_execution",
"status":"killed","end_reason":null,"abort_reason":null}` con
`tail=assistant_text tail_origin=assistant`. O sea: el consumidor **no puede distinguir un
ESC en fase de tools de una caída**, y `abort_tool_use` es `false` justo en el caso que sí es
aborto en tools. Causa medida: `ToolDispatcher._run` (`tools/dispatcher.py:75-78`) hace
`asyncio.wait_for(tool.execute(...), timeout)` sin correr carrera contra `ctx.stop.wait()`,
así que el canal de espera que `FIND-CODE-ESC-2` construyó en `contracts/abort.py` **sigue
sin consumidor en la fase de tools** —lo que aquel paso arregló fue el `await` del stream—.
**Pendiente antes de proponer nada (`D-08`):** leer en A cómo se corre esa carrera
(`query.ts` en torno a `:1508-1515` y el sitio donde A ejecuta la tool) y sólo entonces
enunciar la conducta. No se toca fuente en esta ventana.

**Al margen, medido:** la carencia declarada en `(d)` sobre `local_catalog.py` **no
reproduce hoy**: `localhost` resuelve sólo a `127.0.0.1` y `llama-server` responde 200 por
ese nombre, así que el arnés corrió con el `base_url` del repo, sin rodeo. La declaración se
mantiene —depende del entorno, no del código— pero deja de estar sorteada.

### 2026-08-31 (d) · FIND-CODE-ABORT-TERM-1 · pagado en parte, forma REABIERTA

**Pagado y en el árbol** (`agentic_code`, sin commitear al abrir esta entrada):
`capture.py` clasifica por la cola de la transcripción y no por el Terminal del bucle:
`_classify(status, snapshot)` rinde `error_during_execution` con `errors[]` y **sin clave
`result`**, `error_max_turns`, o `success` con `is_error = (tail_origin == "model_error")`.
`streaming.py` gana `tail` / `tail_origin` y `result_successful`, homólogos de
`isResultSuccessful` (`utils/queryHelpers.ts:56-94`). Los `subtype` inventados
`error_aborted` / `error_failed` / `error_killed` desaparecen: el catálogo cerrado es
`success`, `error_during_execution`, `error_max_turns`, `error_max_budget_usd`,
`error_max_structured_output_retries` (`entrypoints/sdk/coreSchemas.ts:1407-1451`).
Suite `296 passed` (base `293`), `ruff` limpio y `mypy` `Success` sobre los cuatro ficheros.
E2E contra modelo local en fase de STREAMING verificado: cierra
`{"subtype":"error_during_execution","is_error":true,"end_reason":"aborted",
"errors":["[ede_diagnostic] tail=user_text tail_origin=interrupt …"]}` sin clave `result`.

**Acreditación `D-12·b`**: 6 inyecciones → 5 rojas, 1 verde (`M2`, orden de ramas en
`_classify`). Publicado como falso negativo; ver abajo por qué no lo era.

**REABIERTO — el orden de `_classify` está invertido respecto al canónico.**
`error_max_turns` no lo decide la cola: se emite en `QueryEngine.ts:842-874` al recibir el
adjunto `max_turns_reached` **dentro del bucle de mensajes**, con `return` inmediato, o sea
ANTES del `isResultSuccessful` de `QueryEngine.ts:1082`. Y `query.ts:1508-1514` emite ese
adjunto **también en la rama de aborto en tools**, que retorna `{reason:'aborted_tools'}`
(`query.ts:1515`). Luego en A un turno abortado que cruza el tope sale `error_max_turns`.
Consecuencias a pagar en el paso siguiente:
1. En `_classify`, la rama `end_reason == "max_turns"` va ANTES del rechazo por cola.
2. La guarda `if self._end_reason != "aborted"` de `streaming.py:274` suprime un `max_turns`
   que el canónico sí honra; se retira o se separa del `end_reason`.
3. `test_max_turns_only_wins_when_the_tail_is_successful` (`tests/test_capture.py:145`)
   afirma el criterio contrario en el caso `tope_abortado`: se REESCRIBE con el criterio
   canónico, no se ablanda.
4. `M2` deja de ser falso negativo: era mi criterio el equivocado, no el mutador.

**5.b · Carencias reales, no pagadas aquí y registradas en NINGÚN otro sitio** (verificado
contra este censo, `VALIDACION-AGENTIC-CODE.md` y `SEPARACION/DECISIONES.md`): el registro
`result` de `agentic_code` no lleva `num_turns`, `duration_ms`, `duration_api_ms`,
`total_cost_usd`, `permission_denials` ni `modelUsage`, y no existen los `subtype`
`error_max_budget_usd` (`QueryEngine.ts:981-1001`) ni
`error_max_structured_output_retries` (`QueryEngine.ts:1024-1046`). `is_error` sí queda
pagado en este paso.

**Pendiente bloqueado** — ~~vigente~~ **PAGADO el 2026-08-31, ver `(e)`**: la evidencia E2E de
la fase de TOOLS (`abort.tool_use: true`,
`ABORTED_TOOLS`) se canceló y no se puede rehacer hasta restaurar la GPU. El overlay
`/usr/lib/wsl/lib` quedó con las libs de usuario 610.57.01 mientras Windows pasó a 616.56;
`llama-server` cayó a CPU. Se arregla con `wsl --shutdown`, que mata la sesión.

**Declarado**: `local_catalog.py` fija `base_url` con `localhost`, que no resuelve contra un
`llama-server` sólo-IPv4; sorteado únicamente en el arnés de scratch, NO parcheado en el repo.


### 2026-08-29 (b) — `D-56` DERIVADO: el contador mudo deja de escribir un 0, y dice de dónde viene

Palabra del usuario: `ningun cierre, trabajamos ya y luego que se prueba y se confirma recien se
cierra` + `de acuerdo`. Paga el segundo de los dos encargos de la entrada `(i)`, que arrastraba el
rótulo «bloqueado hasta el 2026-09-01 por `D-49`» desde `(j)`, `(k)`, `(l)`, `(m)` y `(a)`. Detalle
en `SEPARACION/DECISIONES.md § D-62`.

**Error mío en el rótulo, corregido:** lo que esperaba al 2026-09-01 no es el número, es la **barra
de error**. Que el contador esté mudo se mide hoy contra `llama.cpp` (`P14`), y el tamaño del
razonamiento se produce hoy contando lo que el motor sí emite; lo que exige un proveedor que
desglose `reasoning_tokens` es **calibrar** que esa cuenta acierta. Se separaron las dos preguntas y
sólo la segunda queda con fecha. `D-56` §Orden de ejecución queda **parcialmente derogada** por
`D-62`: el instrumento se construye ahora.

**Segundo error mío, y también corregido:** había anunciado que «si no hay estimador propio,
`caracteres/4` no es derivar, es inventar». Es falso: `context/estimation.py:52-53` es el estimador
homologado del runtime y **ya contempla el bloque `thinking`**. Reutilizarlo no es invención.

**Inyectado (3 fuentes + 1 test):**
- `contracts/events.py` — `Usage.thinking_tokens_source` con default `unavailable`, las tres
  constantes de procedencia y `weakest_thinking_tokens_source`, que agrega por el **eslabón más
  débil**: un total de sesión no puede ser más fiable que su peor turno.
- `events/event_types.py` — reexporte puro de lo anterior.
- `models/caller.py` — el puente acumula los `thinking_delta` del turno y, en el `done`, aplica la
  cascada sin excepciones de `D-56`: contador del proveedor ⇒ `provider`; mudo pero con razonamiento
  emitido ⇒ `rough_token_count` de lo acumulado y `counted`; ni una cosa ni otra ⇒ `unavailable`.
  Guarda de doble conteo: el bloque final sólo se suma si el turno **no** vino en deltas.
- `agentic_code/streaming.py` — `StreamUsage.thinking_tokens_source`, plegado por el mismo
  eslabón débil en la reducción del `DoneEvent`. `capture.py` **no se toca**: su `asdict` arrastra el
  campo nuevo a las dos líneas del `.jsonl`.

`agentic_models.Usage.reasoning` queda **intacto** (`D-56:3551`): es capa espejo de A y A no hace
esto.

**Acreditación (`D-12·b`):** `test_usage_reasoning_bridge.py` **3 → 12 casos**, con el `.jsonl` real
por medio. **Siete mutaciones inyectadas y revertidas** desde copia propia verificada por `sha256`,
cada una tumbando exactamente sus casos y ninguno más: procedencia siempre `provider` (2 rojas) ·
siempre `unavailable` (1) · agregado por último turno en vez de por el más débil (1) · derivación
ignorada, vuelve el 0 mudo (3) · derivado ganando al contador del proveedor (1) · sin guarda de
doble conteo (1) · `counted` por encima de `provider` en el orden de confianza (1).

**Corrección de protocolo, del propio paso:** `sha256` acredita el **fichero**, no el **módulo
cargado**. La mutación M7 era un intercambio de dos líneas **neutro en tamaño**, y el `cp` del revert
devolvió a `events.py` el mismo `mtime` que el `.pyc` escrito durante la mutación; CPython invalida
por `(mtime, size)`, así que **el bytecode mutado siguió ejecutándose** y produjo una roja falsa tras
un revert correcto. Diagnosticado evaluando el símbolo en el intérprete, no releyendo el fichero.
Regla que se añade al revert: tras reponer, **borrar el `.pyc` del módulo tocado** y recompilar. Es
la misma familia que el defecto de instrumentación de `D-60`: un instrumento ciego no dice «no sé»,
dice «no».

**Medido:** `agentic_code` **272 → 277 passed**; `agentic_models` **78 passed**, capa sin tocar;
`ruff` limpio en `agentic_code` y en `agentic_runtime` los **6** avisos preexistentes, ninguno en
fichero tocado; `mypy` `Success` en los tres fuentes de `agentic_runtime`; sin procesos
supervivientes. Las sintéticas de `agentic_runtime` no se corrieron ni se tocaron.

**Lo que esto NO acredita, y sigue dicho:** el valor derivado **no** acredita `FIND-USAGE-REASONING`
(`D-56` §Límite); el port del parseo del contador del proveedor sigue necesitando un proveedor que lo
emita. Y la barra de error del `counted` se calibra en la ventana del 2026-09-01.

**Siguen abiertos:** `FIND-GOOGLE-CASING` · el techo de salida (`options.max_tokens` es `None` en
toda la cadena ⇒ `max_output_tokens` nunca se escribe, `openai_responses.py:142-143`) ·
`cache_write_1h` sin consumidor real, que gpt-5.x no acreditará nunca · cablear
`thinking_budget_tokens` como palanca primaria · `P1` de `PLAN-OPTIMIZACION-TUI.md` · el prototipo B
(§6-bis) · las filas de presupuesto `medium+1024` / `medium+2048`.

### 2026-08-29 (a) — `auto` deja de suplantar a `off`, y `preserve_thinking` viaja

Encargo: subsanar los hallazgos de la corrida E2E muerta y afinar el thinking, con la sospecha del
usuario —confirmada— de que operábamos Qwen3.8 como si fuera gpt-5.x. Detalle en
`SEPARACION/DECISIONES.md § D-61`.

**La semántica de Qwen3.8 no es la de gpt-5.x.** `reasoning_effort` **no es presupuesto**: su efecto
entero es una frase inyectada en la cabecera del `system`. Medido en la `tokenizer.chat_template`
del GGUF (extraída con parser propio del binario; `gguf-py` inservible sin `numpy`), `:57-71`:
`xhigh` (**el default**) pide validar supuestos y alternativas · `medium` **no inyecta nada**, es el
nivel mudo · `low` pide razonamiento breve y ir directo a la conclusión. Y `<think>` se abre
**forzado** salvo `enable_thinking:false` (`:176-183`). La corrida muerta iba en `medium`, con
`n_remain=-1`: razonamiento abierto y **ni una palabra sobre hasta dónde**. Por eso programó dentro
del pensamiento. `low` es el único de los tres que pone borde.

**El error, doble, verificado contra el canónico antes de tocar** (`openai-responses.ts:262-266`):
el colapso «no pedir nivel ⇒ apagar» **es genuino de A**, no fallo de copia. Los fallos son (1)
`auto` es invención nuestra con etiqueta falsa —prometía «default del motor» y emitía
`enable_thinking:false`—, y (2) se perdió la guarda de A al portar: A distingue `off: null` (*no
expresable* ⇒ no manda nada) de `off` **ausente**, y `tmap.get("off")` devolvía `None` en los dos
casos. Es el riesgo residual que `D-60` dejó vigilado; aquí se paga.

**Inyectado** (`D-22`, lo que no está se crea): `reasoning_off` explícito, que sólo pone
`stream_simple` cuando el nivel pedido es `off` · `_declared_off_level`, que restaura la guarda de A
· `compat["templateKwargs"]`, canal que viaja en **toda** petición porque `thinkingOffParams` sólo
se emite en la rama de apagado y no servía de vehículo · `local_catalog` declarando
`preserve_thinking: False`.

**Payload real del perfil local:** `auto` → nada (queda el `xhigh` del motor) · `low`/`medium`/
`xhigh` → su `effort` · `off` → `enable_thinking:false`. Los cinco llevan `preserve_thinking:false`.

**Por qué `preserve_thinking:false` no es agresivo:** la condición es
`preserve_thinking … or loop.index0 > ns.last_query_index` (`:119`), y `ns.last_query_index`
(`:95-105`) ignora los `user` que son puro `<tool_response>` ⇒ el razonamiento del **ciclo agentic
en curso se conserva íntegro**; sólo se poda el de ciclos cerrados. El runtime es la memoria.

**Transporte verificado en fuente de `llama.cpp`** (HEAD `c060ca97`): el convertidor
Responses→chatcmpl **copia el cuerpo entero** (`server-chat.cpp:15`) ⇒ toda clave desconocida
sobrevive, y por eso `chat_template_kwargs` llega al Jinja (`server-common.cpp:1296-1300`). Con eso
queda **corregido un finding previo**: `reasoning_budget_tokens` se acepta **del cuerpo**
(`server-common.cpp:1354-1365`), luego el sampler de `reasoning-budget.cpp` **es alcanzable desde
Responses**; la superficie anthropic sólo lo traduce. No se cablea aún: dos palancas a la vez
impedirían saber cuál actuó.

**Acreditación:** `test_thinking_off_transport.py` **4 → 8 casos** (que `auto` no manda apagado; que
`off: None` manda nada; que los `templateKwargs` viajan **con nivel activo**; que off-params y
`templateKwargs` se **mezclan**). `test_auto_returns_the_turn_to_the_engine_default` medía sólo el
borde del caller mientras el transporte hacía lo contrario: su docstring ahora cita dónde se mide la
otra mitad. `agentic_models` **74 → 78 passed**, `agentic_code` **267 passed**, sin supervivientes.
Sintéticas de `agentic_runtime` ni corridas ni tocadas.

**Corrección de cita:** la entrada `2026-08-28 (m)` dice `server-task.cpp:696`; **es `:695`** (y
`:587` en la variante no-stream). Verificado en fuente.

**Siguen abiertos:** `FIND-GOOGLE-CASING` · el techo de salida (`options.max_tokens` es `None` en
toda la cadena ⇒ `max_output_tokens` nunca se escribe, `openai_responses.py:142-143`) y la omisión
de la superficie Responses de `llama.cpp`, **la única de las tres** que no reporta ni el corte
(`status` fijo en `"completed"`) ni los tokens de razonamiento (`P14`) · el contador derivado
(`D-56`), bloqueado hasta el 2026-09-01 por `D-49`.

### 2026-08-28 (m) — `/effort` PAGADO: el catálogo lo declara el modelo, y `off` ya viaja

Segundo de los dos pendientes que autorizó `En esta ventana 1 y 2`; el encargo literal es el de la
entrada (i). Lo que faltaba **no** era sólo la superficie: el transporte de `off` no existía y el
catálogo del perfil local mentía en tres sitios.

**La plantilla del motor es la prueba** (`/props`, 184 L leídas 1→EOF): `minimal` cae en el
`raise_exception('Unexpected reasoning effort … Supported types are xhigh (default), medium, and
low.')`, o sea es un HTTP 500; `high` **no es un nivel**, la plantilla lo reescribe a `xhigh` en
silencio antes de comprobar nada; `xhigh` sí existe y estaba oculto, y es el defecto. Y `off` existe
**por `enable_thinking: false`**, no por ningún valor de `reasoning.effort`: se declaraba y no se
transportaba, que es `D-21` incumplido por nuestro propio port.

**Inyectado:** la rama `else` de `_build_params` (`providers/openai_responses.py`) que transporta el
apagado —prioridad al camino canónico `thinking_level_map["off"]`, y si no lo hay,
`compat["thinkingOffParams"] → extra_body`, porque `AsyncResponses.create` no tiene `**kwargs`—;
sin declaración no se inventa nada (`D-22`) · el catálogo local con lo medido, que declara
`['off','low','medium','xhigh']`, `clamp('high')→'xhigh'`, `clamp('minimal')→'low'` · el seam de
turno (`EFFORT_APP_STATE_KEY`/`EFFORT_SETTING` en `supported_settings.py`, `_with_effort` en
`loop/agent_loop.py`, donde `off` = `effort=None` **más** `ThinkingConfig(enabled=False)`) ·
`EffortState` y el comando `/effort [off|nivel|auto]` en `agentic_code`, sembrado desde lo
persistido en `cli.py` · y `capture.py::_digest`, que no proyectaba `extra_body` y por eso la
primera evidencia dijo «no» donde debía decir «no sé».

**E2E en el cable, los dos sentidos** (`D-15`, `llama-server` vivo): `--no-thinking` →
`extra_body:{"chat_template_kwargs":{"enable_thinking":false}}`, 200, **0** eventos de razonamiento,
respuesta `391`; `--effort xhigh` → `reasoning:{"effort":"xhigh","summary":"auto"}`, 200, **28**
eventos de razonamiento.

**Acreditación:** 4 casos nuevos en `agentic_models/tests/test_thinking_off_transport.py` y los 6 de
`agentic_code/tests/test_effort_command.py` reescritos **contra la medición, no ablandados**
(el listado exige `off, low, medium, xhigh · auto` y ausencia de `minimal`; `minimal` se rechaza con
su motivo). `D-12·b`: copia `sha256 a5450c0f…` en `mktemp -d`, mutación `off_params = None` ⇒ **una
roja**, revert con hash idéntico, 4/4 verdes, scratch borrado por ruta absoluta. `agentic_models`
**70 → 74 passed**, `agentic_code` **266 → 267 passed**, sin supervivientes; `ruff` limpio en lo
tocado, los dos avisos preexistentes de `openai_responses.py` sin tocar. Las sintéticas de
`agentic_runtime` no se corrieron ni se tocaron. Detalle en `SEPARACION/DECISIONES.md § D-60`.

**Riesgo residual declarado y NO generalizado:** `get_supported_thinking_levels` sigue declarando
`off` para cualquier modelo de razonamiento sin clave `off` en el mapa y sin off-params; se paga
donde hay medición, y queda vigilado.

**Siguen abiertos:** `FIND-GOOGLE-CASING` · el techo de salida del perfil local y la mentira de
`llama.cpp` (`server-task.cpp:696`), que va al catálogo P1–P9 · el contador de razonamiento derivado
(`D-56`), bloqueado hasta el 2026-09-01 por `D-49`.

### 2026-08-28 (l) — `FIND-MSGINDEX-USER` PAGADO: el otro `continue` del mismo bucle

Palabra del usuario: `En esta ventana 1 y 2`, sobre el pendiente que el enunciado de retoma dejaba
pre-autorizado (*«Si es el 1, la orden basta con “replica el continue”»*). Es el hermano del defecto
que pagó `D-57` y que aquella entrada dejó **medido y abierto**.

**El defecto:** `msgIndex++` vive al final del cuerpo del `for` y fuera de todas las ramas
(`openai-responses-shared.ts:263`), así que sus dos `continue` lo saltan. `D-57` pagó el del
asistente (`:220`); faltaba el del usuario con `content` en lista vacía (`:157`), que el port había
sustituido por la guarda de emisión `if parts:` (`openai_responses_shared.py:108-109`): el mensaje
no se emitía, pero el cuerpo seguía hasta el `msg_index += 1` y **el descarte consumía número**.

**Inyectado:** tres líneas por dos, `openai_responses_shared.py:108-110` — `if not parts: continue`
delante del `append`, literal del canónico. Medido con el módulo real: un texto sin firma detrás de
un usuario vacío se firmaba `msg_pi_1` donde A firma `msg_pi_0`.

**Alcance real, sin cambio respecto de `D-57`:** el repliegue sólo actúa sobre bloques de texto sin
`text_signature`, o sea historial cross-model (`transform_messages.py:127`). Y el usuario llega
intacto a la conversión (`transform_messages.py:80-82`), luego la lista vacía no se filtra antes.

**Acreditación:** un caso nuevo con criterio y citas en la docstring, que contrasta dos historiales
que sólo difieren en el usuario vacío de cabeza y exige el mismo id de repliegue; verde a la primera
⇒ **mutación inyectada y revertida** —reponer `if parts:`— desde copia propia verificada por
`sha256`: **una roja** (`assert ['msg_pi_2'] == ['msg_pi_1']`), cero falsos positivos, y el caso de
`D-57` **verde durante la mutación**, que es lo que prueba que son dos casos y no uno medido dos
veces. `agentic_models` **70 passed**, `agentic_code` **261 passed**, sin supervivientes; `ruff`
**6 avisos antes, 6 después**, los preexistentes de `D-52`/`D-53` y ninguno en línea tocada. Las
sintéticas de `agentic_runtime` no se corrieron ni se tocaron. Detalle en
`SEPARACION/DECISIONES.md § D-59`.

**Pata de `.jsonl` real: declarada inalcanzable por esta superficie**, no omitida — exige a la vez
un usuario con `content` vacío y un texto sin firma detrás (`D-21`). El cableado en `agentic_code`
no necesita acción: su venv monta `agentic_models` en editable sobre `agentic_models/src`.

**Siguen abiertos:** los dos encargos de la entrada (i) —el `/effort` y el contador de razonamiento
derivado, este después del 2026-09-01— · `FIND-GOOGLE-CASING` · el techo de salida del perfil local ·
y la mentira de `llama.cpp` (`server-task.cpp:696`), que va al catálogo P1–P9.

### 2026-08-28 (k) — pieza 1 de `D-50` PAGADA: barrido de comentarios de sus nueve ficheros

Paso 3 del orden acordado. `D-50` declaró el barrido **paso propio** porque los ficheros del
integrador arrastraban documentación previa cuya purga habría hecho irrevisable el diff de aquel
paso; `D-51`..`D-55` y `D-57` lo reiteraron sin cambio. Aquí se paga entero.

**Alcance:** los nueve — `compaction.py`, `repl.py`, `transcript.py`, `tui.py`,
`transcript_browser.py`, `rendering.py`, `capture.py` (los seis de `D-50` más el séptimo de `D-51`)
y los tests `test_compaction_wire.py` y `test_tui.py`. **6381 → 6114 líneas.**

**Regla aplicada (§4):** cae todo docstring y todo comentario de los siete fuentes, incluidos los
`#:` de campo y el comentario que vivía dentro del CSS de `WorkspaceTuiApp` —cadena, no token, así
que se retiró a mano—. Sobrevive la **directiva desnuda** `# noqa` / `# type:`; la prosa que
acompañaba a cuatro de ellas cae con el resto (`tui.py` ×2, `test_tui.py` ×2): la excepción es la
directiva, no el comentario pegado a ella. En los tests sobreviven el docstring de módulo de
`test_compaction_wire.py` y los de las funciones `test_*` —declaran criterio y citan el canónico—;
los de las clases de andamiaje (`CompactingCaller`, `ReadingCaller`, `RecordingCaller`,
`_ToolTurnRuntime`) **no son docstrings de un test** y caen. Las dos lecturas van declaradas porque
el §4 no las contestaba.

**Acreditación —el barrido es NEUTRO, y se mide, no se declara:** copia propia de los nueve
verificada por `sha256` antes de tocar; después, comparación del **AST con docstrings quitados de
los dos lados**: ocho `IDÉNTICO` y `tui.py` `DIFIERE` **por el único cambio de cadena previsto**,
exhibido en diff (el comentario CSS). `ruff` idéntico al baseline (limpio antes y después) y
`agentic_code` **261 passed** en 28 s, sin procesos supervivientes. Las sintéticas de
`agentic_runtime` no se corrieron ni se tocaron.

**Siguen abiertos, sin cambio:** `FIND-MSGINDEX-USER` (medido y decidible, pendiente de palabra) ·
los dos encargos de la entrada (i) —el `/effort` y el contador de razonamiento derivado, este
después del 2026-09-01— · `FIND-GOOGLE-CASING` · el techo de salida del perfil local · y la mentira
de `llama.cpp` (`server-task.cpp:696`), que va al catálogo P1–P9.

### 2026-08-28 (j) — `msg_index` PAGADO: el índice de repliegue numera mensajes EMITIDOS

Enunciado de retoma del paso 2 del orden acordado, con su pago condicionado a lo que dijera el
canónico. Dice esto: `msgIndex++` vive en `openai-responses-shared.ts:263`, al final del cuerpo del
bucle y fuera de todas las ramas, y los dos `continue` lo saltan —`:220` el asistente sin ítems,
`:157` el usuario con `content` vacío—. En A el contador numera mensajes **emitidos**; en B numeraba
los **recorridos**.

**Inyectado:** una línea retirada, `openai_responses_shared.py:169` (`msg_index += 1` delante del
`continue` del asistente vacío). Un texto sin firma detrás de un asistente descartado se firmaba
`msg_pi_2` donde A firma `msg_pi_1`.

**Alcance real, medido:** el repliegue sólo actúa sobre bloques de texto **sin** `text_signature`, y
eso es historial cross-model (`transform_messages.py:127` reconstruye el `TextContent` sin firma
cuando el mensaje no es del modelo actual). Con el mismo modelo la firma la pone el proveedor.

**Acreditación:** un caso nuevo con criterio y citas en la docstring, y **mutación inyectada y
revertida** —reponer el `msg_index += 1`— desde copia propia verificada por `sha256` (`ffad7943…`,
hash idéntico tras el revert) ⇒ **una roja, cero falsos positivos**. `agentic_models` **69 passed**,
`agentic_code` **261 passed**, sin supervivientes; `ruff` con los 6 avisos preexistentes de
`D-52`/`D-53` y ninguno nuevo. Las sintéticas de `agentic_runtime` no se corrieron ni se tocaron.
Detalle en `SEPARACION/DECISIONES.md § D-57`.

**Pata de `.jsonl` real: declarada inalcanzable por esta superficie**, no omitida — exige a la vez un
asistente sin ítems y un texto sin firma detrás, o sea historial cross-model, que ninguna corrida
produce a voluntad (`D-21`). El cableado en `agentic_code` no necesita acción: su venv monta
`agentic_models` en editable sobre `agentic_models/src`.

**Divergencia hermana NUEVA, ABIERTA y no pagada — `FIND-MSGINDEX-USER`:** el mismo defecto en el
otro camino de descarte. A hace `continue` en `:157`; el port lo sustituyó por `if parts:`
(`openai_responses_shared.py:108-109`), así que el usuario con `content` vacío sí avanza el índice.
Medido y decidible; fuera del enunciado del paso, no se toca sin palabra del usuario.

**Siguen abiertos, sin cambio:** la pieza 1 de `D-50` (paso 3) · los dos encargos de la entrada (i)
—el `/effort` y el contador de razonamiento derivado, este después del 2026-09-01— ·
`FIND-GOOGLE-CASING` · el techo de salida del perfil local · y la mentira de `llama.cpp`
(`server-task.cpp:696`), que va al catálogo P1–P9.

### 2026-08-28 (i) — `FIND-USAGE-REASONING` PAGADO: el contrato `Usage` gana `reasoning` y `cache_write_1h`

Palabra del usuario: `Se atacan los 3 en el orden que propones` + `procede`. Se paga la deuda que
`D-54` había declarado fuera de alcance; era la primera de las tres del orden acordado.

**El defecto, con línea:** el canónico lleva en `Usage` (`types.ts`) dos campos que B no tenía.
`reasoning` es SUBCONJUNTO de `output` —coste neutro— y lo pueblan **cinco** productores
(`openai-responses-shared.ts:370`, `openai-completions.ts:1141`, `anthropic-messages.ts:708`
—sólo si no es nulo—, `google-generative-ai.ts:225`, `google-vertex.ts:242`). `cacheWrite1h` es
SUBCONJUNTO de `cacheWrite` (`anthropic-messages.ts:555`) y se factura a **2 × input**
(`models.ts:385-395`): sin él, la escritura larga se cobraba a tarifa corta y **el precio del turno
salía mal**, no sólo incompleto.

**Inyectado (nueve ficheros):** `model_types.py` (los dos campos, **al final** del dataclass, para
que la construcción posicional conserve su significado) · `models/registry.py` (el tramo de 1 h en
**los dos** caminos de precio: el método `Registry.calculate_cost` y la función de módulo
`calculate_cost_values`, porque `models.ts:385-395` es un solo algoritmo que aquí vive en dos
sitios) · `openai_responses_shared.py` y `openai_completions.py` · `anthropic.py` (los dos campos)
· `google_shared.py` (`read_usage_metadata` y `read_usage_field`, lectura dual `snake`/`camel`), con
`google.py` y `google_vertex.py` recableados sobre ellas.

**Hallazgo del paso, PAGADO — `FIND-GOOGLE-USAGE`:** el caso de Google salió en rojo con el `Usage`
**entero a cero**, no sólo `reasoning`. El bloque leía `usageMetadata`/`promptTokenCount`, nombres
del SDK **TypeScript**; el SDK Python los da en `snake_case`, luego `usage_meta` era **siempre
`None`** y Google no reportaba consumo alguno. Verificado contra el SDK instalado.

**Acreditación:** ocho casos nuevos en `agentic_models` con criterio y citas en la docstring, más
tres en `agentic_code` que ejercitan el puente REAL (`caller.py`) y el capturador REAL
(`capture.py`) escribiendo la línea `.jsonl` de verdad —incluido el `Usage` antiguo sin el campo,
que debe rendir 0 y no reventar—. **Ocho mutaciones inyectadas y revertidas** desde copia propia
verificada por `sha256` ⇒ **ocho rojas**, cada una tumbando exactamente su caso. Hashes idénticos
tras cada revert (`caller.py` `fdc9ee22…`, `capture.py` `92fbdd93…`,
`openai_responses_shared.py` `bdb4ba23…`, `registry.py` `e6ad40e7…`, `anthropic.py` `d315b851…`,
`google_shared.py` `c567de8a…`, `openai_completions.py` `34323232…`). **La mutación M1 fue un falso
negativo mío y se declara:** el patrón llevaba la indentación del método de clase y no mutó la
función de módulo que el caso llama; defecto de la mutación, no del test — corregido con un caso
propio para el método y dos pasadas separadas, ambas rojas.

`agentic_models` **68 passed**, `agentic_code` **261 passed**, sin supervivientes; `ruff` sin avisos
nuevos (comparados uno a uno contra la copia previa, fichero por fichero; el único `I001` nuevo, que
dejó el barrido en `model_types.py`, se corrigió en el acto). Las sintéticas de `agentic_runtime` no
se corrieron ni se tocaron. Barrido de comentarios de los nueve ficheros, que **no** paga la pieza 1
de `D-50`. Detalle en `SEPARACION/DECISIONES.md § D-55`.

**Declarado y NO pagado — APLAZADO al 2026-09-01, no bloqueado:** la pata de `.jsonl` con
razonamiento real **no es una incidencia pendiente de resolver**. El `401` de Azure es el crédito
agotado, y su reposición tiene fecha acordada en `D-49`: el 2026-09-01. La pata viaja a esa ventana,
donde ya espera la acreditación de la compactación contra el modelo frontera; no se persigue clave
alguna hasta entonces. El `llama-server` local sí se ejercitó y **sí emite razonamiento** —medido en
vivo el 2026-08-28: item `{"type": "reasoning"}` en la ruta no-streaming y
`response.reasoning_text.delta` en la de streaming—; lo que no emite es `output_tokens_details`, o
sea el **contador**. Su `thinking_tokens: 0` es por tanto fiel **al wire** y falso sobre lo
ocurrido, y no sustituye a la pata aplazada: daría el mismo `.jsonl` antes y después de la
inyección. Catalogado como **`P14`** en `agentic_models/gpt-5.x-conducta-vs-claude.md`. **Deuda
que la fecha NO cierra:** `cache_write_1h` sólo lo emite Anthropic (`anthropic-messages.ts:555`),
así que gpt-5.x no lo acreditará **nunca**; el campo que corrige un precio mal cobrado seguirá sin
consumidor real después del 2026-09-01, y su acreditación necesita proveedor Anthropic o queda
declarada indefinidamente. **`FIND-GOOGLE-CASING`,
ABIERTO:** la misma grafía TS fuera del bloque de usage —`finishReason` (`google.py:258`) y
`thoughtSignature` (`:216`, `:222`, `:251`)—, que es paso propio con su lectura 1→EOF de los dos
ficheros gemelos.

**Dos encargos NUEVOS del usuario (2026-08-28), anotados sin tocar fuente:**

1. **`/effort` como slash command** — seleccionar nivel de razonamiento desde la TUI, incluyendo
   **`off` (no pensar)** y los niveles que el modelo **local** declare disponibles. Engancha con
   `D-21` (`off` es un nivel, no una omisión: omitirlo deja el default del motor) y con `P10·2`.
   El transporte ya existe —`caller.py` traduce `effort` y rechaza lo inexpresable—; lo que falta
   es la superficie de usuario y la consulta de niveles soportados por modelo.
2. **Contador de razonamiento DERIVADO para motores que no lo desglosan** — a raíz de `P14`.
   Medido el 2026-08-28: los deltas del local son **por token** (70 de razonamiento + 54 de texto
   = 124, contra `output_tokens` 127; los 3 restantes son tokens de control no emitidos como
   texto), luego el desglose que el servidor calla **se reconstruye contando deltas**, sin
   heurística ni tokenizador —y `llama-server` expone `/tokenize` si hiciera falta exactitud—.
   **Forma acordada como correcta, y su razón:** `Usage.reasoning` de `agentic_models` se queda
   **intacto** con lo que dijo el proveedor —es capa espejo de A, y A no hace esto—; el valor
   derivado se calcula en el puente (`agentic_runtime`) y viaja con procedencia explícita
   (`thinking_tokens` + `thinking_tokens_source: "provider" | "counted"`), porque sin la marca un
   0 y un 70 calculado son indistinguibles en el `.jsonl`. **Prohibición expresa:** el valor
   derivado NO acredita `FIND-USAGE-REASONING`; si lo hiciera, el test mediría el contador propio
   en vez de la costura (`no-debilitar-la-prueba`). **Encuadre, corregido por el usuario y fijado
   en `D-56`:** esto **no** es divergencia deliberada por familia —así lo había rotulado yo, y era
   el encuadre contrario—. El canónico define que `Usage` transporta el razonamiento; sostener esa
   funcionalidad en un motor que no la desglosa es **fidelidad al contrato**, `D-22` aplicado a la
   capa de proveedor. La regla no tiene casos especiales: si el proveedor da el contador se usa el
   suyo; si no lo da pero emite razonamiento se deriva; si no se puede derivar **no se emite un 0
   mudo**, se marca indisponible. De ahí que la procedencia sea de tres valores —`provider` /
   `counted` / `unavailable`—: es lo que hace comprobable el «sin excepciones». gpt-5.x nunca entra
   en la rutina porque trae el contador. Coste: nulo, `reasoning` es subconjunto de `output`.
   **Orden:** después de la ventana del 2026-09-01, que es el único patrón contra el que calibrar
   que la cuenta de deltas acierta.

**Siguen abiertos, sin cambio:** el `msg_index` de `convert_responses_messages`
(paso 2 del orden acordado) · la pieza 1 de `D-50` (paso 3) · el techo de salida del perfil local ·
y la mentira de `llama.cpp` (`server-task.cpp:696`), que va al catálogo P1–P9.


### 2026-08-27 (h) — `FIND-RESP-INCOMPLETE` + `FIND-RESP-TERMINAL` PAGADOS: el cierre del stream es UNA costura

Palabra del usuario: `procede`. Las dos divergencias que dejó abiertas la entrada (g) se pagan
juntas porque son la misma costura —el final del stream de Responses— y viven en el fichero ya
leído 1→EOF.

**Los dos defectos anunciados, con línea:**
- `openai_responses_shared.py:461` atendía sólo `response.completed`; el canónico cierra el turno
  con **`response.completed` y `response.incomplete`** (`openai-responses-shared.ts:512-513`), así
  que un turno truncado no fijaba `usage`, ni coste, ni `stop_reason`, y la rama `"incomplete"` →
  `"length"` de `_map_stop_reason` era **inalcanzable por construcción**.
- No existía el centinela `sawTerminalResponseEvent` (`:302`, `:528-530`): un stream cortado antes
  del evento terminal se cerraba **en silencio como turno bueno**. Literal canónico:
  `"OpenAI Responses stream ended before a terminal response event"`.

**Lo que añadió el contraste hasta EOF — tres divergencias más, anunciadas antes de inyectar:**
1. El cuerpo entero del cierre colgaba de `if response:`, mientras A guarda del payload sólo `id` y
   `usage` (`:356-374`) y **calcula coste, tier y `stopReason` siempre** (`:375-387`).
2. `response.failed` no lanzaba siempre; A lanza **incondicionalmente** (`:516-525`) y, sin error ni
   razón, con el literal `"Unknown error (no error details in response)"`.
3. El precio por tier recibía el **estado** (`st = resp_status`) en vez del `service_tier` (A
   `:376-381`). Con el envoltorio real (`openai_responses.py:229-236`, que no pasa por
   `resolve_service_tier`) los multiplicadores `flex` (0.5) y `priority` **nunca** se aplicaban.

**Inyectado:** `_resp_field`, la bandera `saw_terminal_response_event`, `finalize_response`, la rama
terminal `("response.completed", "response.incomplete")`, el `response.failed` con sus tres
literales y el `raise` posterior al bucle; retirado el bloque anterior de `response.completed` (34
líneas). Las otras tres entradas al motor (`azure_openai_responses.py:211`,
`openai_codex_responses.py:570,749`) heredan la conducta sin tocarse.

**Acreditación:** cuatro casos nuevos con criterio y citas en la docstring —terminal `incomplete`,
stream sin evento terminal, `failed` que siempre lanza con el literal, y el tier que recibe el tier
y no el estado—; **cuatro mutaciones inyectadas y revertidas** desde copia propia verificada por
`sha256` (previo `c78c448c…`, inyectado `aaca33e0…`, hash idéntico tras cada revert) ⇒ **cuatro
rojas, cero falsos positivos**; y turno real contra el `llama-server` vivo con `"stop_reason":
"stop"` y `usage` completo (in 14.803 / out 250 / cache 14.709) en el `.jsonl` (`D-15`).
`agentic_models` **60 passed**, `agentic_code` **258 passed**, sin supervivientes; `ruff` con los
**6** avisos preexistentes de `D-52`/`D-53` y ninguno nuevo. Las sintéticas de `agentic_runtime` no
se corrieron ni se tocaron. Detalle en `SEPARACION/DECISIONES.md § D-54`.

**Divergencia nueva, ABIERTA y declarada fuera de alcance — `FIND-USAGE-REASONING`:** A puebla
`reasoning: usage.output_tokens_details?.reasoning_tokens` (`:370`) y nuestro `Usage`
(`model_types.py:166-173`) **no tiene el campo**, así que pagarlo es cambio del contrato `Usage`,
no de este fichero. **Sigue abierto, sin cambio:** el `msg_index` que se incrementa donde el
canónico hace `continue` (es de `convert_responses_messages`, dos líneas, sólo afecta a los ids de
repliegue `msg_pi_{n}`) · la pieza 1 de `D-50`, el barrido de comentarios de sus nueve ficheros ·
el techo de salida del perfil local · y la mentira de `llama.cpp` (`"status": "completed"`
incondicional, `server-task.cpp:696`), que va al catálogo P1–P9 y no a homologación.

### 2026-08-27 (g) — `FIND-EMPTY-TOOL-OUT` PAGADO: el resultado vacío se declara vacío

Palabra del usuario: `procede`. Segunda de las tres deudas nombradas en la entrada (e); queda la
pieza 1 de `D-50` y el techo de salida del perfil local, que no es divergencia de motor.

**El defecto, con línea:** `openai_responses_shared.py:194` (era `:201` antes del desplazamiento de
`D-52`) colapsaba a dos ramas lo que el canónico tiene en tres (`openai-responses-shared.ts:254`).
Sin texto, la salida caía **siempre** en `"(see attached image)"`: un `glob` sin coincidencias
viajaba al modelo anunciando una imagen inexistente.

**Lo que añadió el contraste hasta EOF:** `transformMessages` corre antes (`:123`) y sustituye la
imagen por su texto de repliegue cuando el modelo no admite imágenes (`transform-messages.ts:34-56`,
espejado en `transform_messages.py:33-57`), así que **la rama de imagen es defensiva y no se alcanza
por este camino ni en A**. Lo que heredaba el resultado vacío era, literalmente, una cadena muerta.

**Inyectado:** una línea, el ternario de tres ramas literal del canónico.

**Acreditación:** dos casos nuevos —el vacío exige `"(no tool output)"`; el otro fija las ramas
alcanzables y por qué la de imagen no lo es—; mutación inyectada y revertida desde copia propia
verificada por `sha256` en dos pasadas (rama retirada y literal cambiado), **dos rojas**; y turno
real contra el `llama-server` vivo con `glob *.zzz` sin coincidencias, cuyo `.jsonl` lleva
`{"type": "function_call_output", …, "output": "(no tool output)"}` en el segundo `model_request`
(`D-15`). `agentic_models` **56 passed**, `agentic_code` **258 passed**, sin supervivientes; `ruff`
sin avisos nuevos. Las sintéticas de `agentic_runtime` no se corrieron ni se tocaron. Detalle en
`SEPARACION/DECISIONES.md § D-53`.

**Dos divergencias nuevas del mismo fichero, ABIERTAS y no de este paso** (detalle en `D-53`):
`FIND-RESP-INCOMPLETE` —`response.incomplete` no se atiende (`:461` vs canónico `:512`), luego un
turno truncado no fija `usage` ni `stop_reason`, y enlaza con la mentira de `llama.cpp`— y
`FIND-RESP-TERMINAL` —falta el centinela `sawTerminalResponseEvent` (`:302`, `:528-530`), y un
stream cortado se cierra en silencio como turno bueno—.

### 2026-08-27 (f) — `FIND-PARALLEL-SLOT` PAGADO: una casilla por item, con la clave replegada a `item.id`

Palabra del usuario: `de acuerdo, procede`, precedida de su encargo de investigar antes la
implementación real del servidor (*«antes no seria bueno buscar la implementacion del modelo y la
compatibilidad real que existe con gpt?»*). La primera de las tres deudas nombradas en la entrada
(e) queda pagada; era la más cara porque **ejecuta dos veces**.

**Reproducido antes de tocar nada** (`curl` crudo a `/v1/responses`, una tool, prompt de dos
llamadas): el `added` de la segunda `function_call` llega con la primera abierta y el razonamiento
también abierto, y **todos los `done` salen al final**. Sobre la casilla única de entonces eso daba
las tres averías enunciadas en (e): firma de razonamiento nunca fijada, argumentos de la tool #1
escritos en el bloque de la #2, y un `ToolCall` fabricado fuera de `output.content` para la #2 —
neto, `b.txt` descartado y `a.txt` ejecutado dos veces.

**Investigación previa a la inyección, en fuente de `llama.cpp`** (HEAD `c060ca974`, tag `b10603`;
`tools/server/server-task.cpp:1166-1314` y `:599-714`): el emisor Responses **no escribe
`output_index` en ningún evento** —ni `content_index`, ni `summary_index`, ni `sequence_number`—
porque no existe el concepto: el estado del turno sólo guarda un id de razonamiento, uno de mensaje
y un `oai_resp_fc_id` «actual». En cambio **todo evento lleva `item_id` o `item.id`**, estables
durante el turno: la clave replegada es total, no un apaño. El solapamiento es arquitectura, no
azar. Inventario completo de lo que emite y lo que omite, en `SEPARACION/DECISIONES.md § D-52`.

**Inyectado** (`agentic_models/.../openai_responses_shared.py`): mapa `output_slots` con
`content_index` congelado al crear, casilla registrada **bajo todas las claves disponibles**
(`output_index` cuando no es `None`, más el id del item) y retirada por todas en cada `done`. Los
handlers pasan a `slot = get_slot(...); if slot is None: continue` y `output_item.done` usa
`get_or_create_slot`, con lo que desaparece la fabricación del `ToolCall` suelto. Se homologa además
el orden de resolución de argumentos del `done`, que estaba del revés respecto de `:500`.

**Acreditación:** dos casos nuevos (forma OpenAI con `output_index` y forma `llama-server` sin él,
con el orden capturado); mutación inyectada y revertida desde copia propia verificada por `sha256`
en dos pasadas —clave constante tumba los dos casos nuevos, clave sólo por índice tumba únicamente
el caso sin índice—; y el turno real contra el `llama-server` vivo con las dos tools distintas y la
firma fijada. `agentic_models` **54 passed**, `agentic_code` **258 passed**, sin supervivientes. Las
sintéticas de `agentic_runtime` no se corrieron ni se tocaron.

**Divergencia nueva, ABIERTA y no de este paso:** `llama.cpp` emite `"status": "completed"`
**incondicionalmente** al cerrar el stream (`server-task.cpp:696`), también cuando paró por techo de
salida. Un turno truncado se anuncia completado y `_map_stop_reason` no puede distinguirlo. Destino
catálogo P1–P9, no homologación.

**Sigue pendiente, sin cambio:** `FIND-EMPTY-TOOL-OUT` (una línea) · el techo de salida del perfil
local · la pieza 1 de `D-50`, el barrido de comentarios de sus nueve ficheros.

### 2026-08-27 (e) — `D-51`: la observabilidad del `/compact` completa, y la deuda arrastrada, NOMBRADA

Palabra del usuario: *«2 ampliar evento, 3 registrar, 4 no queda fuera es deuda que vienes
arrastrando»*, y `procede` sobre el anuncio. Se pagan las piezas 2 y 3 de lo que `D-50` dejó
**declarado y no pagado**; se toman como un paso porque son la misma costura —`/compact` es comando
local, no turno— y se acreditan con el mismo `.jsonl` real (`D-15`).

**Inyectado (2 ficheros en `agentic_runtime`, 7 en `agentic_code`):**
- `contracts/events.py` — `CompactionEvent.user_context`. El dato ya llegaba al prompt del
  resumidor (`engine.py:752-755`), al marcador (`:779-788`) y a `summarize_metadata` (`:800-805`),
  y se caía en los dos `emit`: la única costura pública por la que un consumidor puede pintarlo.
  `A` lo pinta en línea aparte del titular (`CompactSummary.tsx:48`, `Context: “{userContext}”`).
- `context/compact/engine.py` — relleno del campo en las dos rutas. Sólo la **parcial** lo trae:
  la completa manda ese texto como `custom_instructions`, igual que `A`; el campo existe y va
  vacío, que es lo que `D-21` exige de una opción que la ruta no expresa.
- `capture.py` — `user_context` dentro de `compact_metadata`, junto a `trigger` y `pre_tokens`;
  y `PayloadRecorder.borrow`, que **guarda y restaura** en vez de anular.
- `transcript.py` / `rendering.py` / `tui.py` / `transcript_browser.py` — `context_line`
  (`└ contexto: “…”`), fuera del titular, en las cuatro superficies.
- `compaction.py` — segunda costura `recording`, un context manager que envuelve la llamada al
  motor; sin ella, `nullcontext()`.
- `repl.py` — `_ensure_compaction_capture()` extraído de `_emit_compaction`, y `_record_compaction`
  prestando el grabador. El orden es el motivo de la forma: **`on_payload` ocurre ANTES del primer
  `CompactionEvent`**, luego el sumidero perezoso de `D-50` llegaba tarde por construcción. `borrow`
  y no `attach`/`detach`: la compactación automática ocurre DENTRO de un turno y un `detach` dejaría
  al turno en vuelo sin grabador.

**Pruebas:** `test_compaction_wire.py` de 26 a **30**; `agentic_code` **258 verdes**; `ruff` limpio;
sin procesos supervivientes. Las sintéticas de `agentic_runtime` no se corrieron ni se tocaron.
Detalle en `SEPARACION/DECISIONES.md § D-51`.

#### Deuda que vengo arrastrando (no es cola neutra: es mía)

Las tres estaban rotuladas «laterales» y «fuera de este paso». El rótulo se retira. Ninguna se paga
en esta ventana; las tres quedan **medidas, con línea, y decidibles**:

1. **`FIND-PARALLEL-SLOT` — defecto propio, localizado. PAGADO en la entrada (f), `D-52`.**
   `agentic_models/.../openai_responses_shared.py:281-284` tiene **una sola casilla** donde el
   canónico tiene un mapa (`openai-responses-shared.ts:288-354`, `outputSlots`), así que con dos
   `function_call` en la misma respuesta el segundo `added` pisa al primero. Consecuencias probadas
   en el cable (conn 8): `thinking_signature` nunca se fija, la primera tool se **descarta** y la
   segunda se **ejecuta dos veces** — efecto lateral repetido. Segunda capa, que no está en el
   canónico: `llama-server` no manda `output_index`, luego la clave del mapa se repliega a
   `item.id`/`item_id`. **Vigilancia:** es el más caro de los tres —ejecuta dos veces— y no tiene
   test que lo detenga hoy.
2. **`FIND-EMPTY-TOOL-OUT` — defecto propio, de una línea, NO pagado.**
   `openai_responses_shared.py:201` colapsa a dos ramas lo que el canónico tiene en tres
   (`openai-responses-shared.ts:254`): falta `"(no tool output)"`, así que un `glob` sin
   coincidencias viaja al modelo como `(see attached image)`. **Vigilancia:** visto en el cable, el
   modelo lo registró como anomalía y lo rodeó con `ls -la` — degrada la conducta sin fallar.
3. **Techo de salida del perfil local — NO es divergencia, y lo que queda no es del motor.**
   Ya rectificado el 2026-08-27 (b): la fórmula es literal de `A` y el 4.096 sale del `max_tokens`
   de la ficha (`local_catalog.py:21`), con lo que `min(4.096, scaled(20.000))` da 4.096 con las dos
   políticas. **Lo medido y vigilado:** este modelo gasta ~1.600 de esos 4.096 en razonamiento que
   no sabe callar, luego el resumen útil son ~2.300. La palanca es la ficha contra lo que el
   `llama-server` admita, y la patología del prompt de resumen ante gpt-5.x/Qwen: catálogo P1–P9
   (`agentic_models/gpt-5.x-conducta-vs-claude.md`), no homologación.

Sigue en pie, sin cambio, la pieza 1 de `D-50`: **el barrido de comentarios de los ficheros
tocados es paso propio**.

### 2026-08-27 (d) — `FIND-COMPACT-MANUAL-EVENT` PAGADO: la frontera la crea la función de compactación

Palabra del usuario: *«primero, si has detectado que lo que implemento Codex, no se alinea al
canonico, alinearlo, en el resto estoy de acuerdo.»* El hallazgo estaba enunciado abierto en el §2
de este censo (líneas 705-712 y 815-827) y cae dentro del punto 2 de `D-49` —la variante manual del
interín—, sin reabrir ningún tramo (`D-41`…`D-48`).

**El defecto:** `ManualCompaction._compact` (`agentic_code/src/agentic_code/compaction.py`) llamaba
al motor **sin `emit=`**, así que `/compact` no producía **ningún `CompactionEvent`**: ni línea en la
captura `.jsonl` ni frontera pintada. El canónico crea la frontera **dentro de la función** de
compactación en las dos rutas (`services/compact/compact.ts:598-602` la completa, `:1014-1020` la
parcial); la ruta automática ya pasaba `AgentLoop._emit`, luego el mismo evento era observable o
invisible según por dónde entrase — la misma forma que `D-46·2` cerró para el PTL.

**Lo hecho, cinco superficies:**
1. `compaction.py` — `emit` como quinto campo con default, tipado `EventHandler`
   (`agentic_runtime/contracts/events.py:77`, el alias público equivalente al `EmitFn` privado del
   motor), pasado a `compact_conversation` y a `partial_compact_conversation`.
2. `repl.py` — sumidero propio del `/compact`: `StreamCapture` perezoso por sesión con
   `prompt="/compact"`. `/compact` es comando local, **no turno**: sin `begin_turn`/`dispatch_prompt`
   no hay captura ni presentación montadas para él (`D-22`).
3. `repl.py` — `last_capture_path` **no** se desplaza; el camino nuevo se publica por
   `compaction_capture_path`.
4. `transcript.py` + `tui.py` + `transcript_browser.py` — la frontera es una fila del transcript que
   **no abre turno**: cuelga de `self._current or self._turns[-1]`, protegiendo el recuento de
   `ConversationState` y el corte del `PayloadRecorder`. Fila: `✻ conversación compactada` con
   `Ctrl+O para el historial`.
5. `rendering.py` y `_display_text` — se caen los contadores inventados de la etapa Codex
   (`pre → post tokens`, `resumen de N caracteres`) y el glifo `⧉`; queda lo que A dicta
   (`CompactBoundaryMessage.tsx:5-17`, `CompactSummary.tsx:31-73`): resumidos, conservados, sentido.
   La nota de `reasoning_fallback` se conserva por `D-21`.

**Acreditación:** `tests/test_compaction_wire.py` **26 casos** (6 nuevos: las dos rutas del `emit`,
la dirección de la parcial, la frontera aterrizando en un `.jsonl` real (`D-15`), el sumidero del
REPL con `prompt == "/compact"` y `last_capture_path is None`, y la fila del store que no fabrica
turno) · `tests/test_tui.py` **25 casos**, con la fila montada en un `TranscriptApp` real y la
comprobación de que `"tokens"` **no** aparece pintado · `ruff` limpio · suite de `agentic_code`
**254 passed** · sin procesos supervivientes. Las suites sintéticas de `agentic_runtime` no se
corrieron ni se tocaron. Detalle en `SEPARACION/DECISIONES.md § D-50`.

**Declarado, no pagado:** el barrido de comentarios de los ficheros tocados sigue siendo paso propio
· `CompactionEvent` no lleva `user_context`, así que la línea `Context: "…"` de A no se puede pintar
sin tocar el contrato del núcleo · `PayloadRecorder` es por turno, luego la petición de modelo del
propio `/compact` y el coste del resumidor siguen sin registrarse (preexistente).

### 2026-08-27 (c) — `D-49`: la acreditación de la compactación tiene FECHA, y no es hoy

Palabra del usuario: *«la compactacion homologada de A se probaria contra el modelo frontera el 1ro
de setiembre cuando exista el credito repuesto, mientras tanto trabajabamos en una variante manual
para el modelo local»*. Verificado `SEPARACION/DECISIONES.md` entero (`D-01`…`D-48`): **el acuerdo
no estaba escrito**; su raíz sí lo estaba (`D-40`, el local es stopgap con fecha y lo medido en él
no es conducta). Se registra como **`D-49`**.

**Consecuencia sobre las dos entradas de abajo, que quedan reencuadradas y no retiradas:** lo que la
sonda del 2026-08-27 acredita es **mecanismo** —caché del hilo superviviente a la compactación,
reparto del coste, y los dos defectos de port que el cable destapó—, que es la clase «código y
aritmética» de `D-40`. Lo que **no** acredita es la compactación homologada de A: eso se prueba
contra **gpt-5.4 el 2026-09-01**. Todo lo relativo a la CALIDAD del resumen en esta corrida
—~1.600 tokens de razonamiento vertidos al texto, ~2.300 útiles de un techo de 4.096, las dos
declaraciones de crecimiento— es **observación del modelo local con su modelo dicho**, destino
catálogo P1–P9, no fila de marcador.

**La vía viva del ínterin es la VARIANTE MANUAL**: `/compact`, `from:N`, `upto:N` sobre los pivotes
de `/history`, más los guardas de la política `local`. De los cuatro abiertos, `FIND-COMPACT-MANUAL-EVENT`
cae dentro de esa vía; `FIND-PARALLEL-SLOT` y `FIND-EMPTY-TOOL-OUT` son defectos de adaptador con
línea canónica en pi/ai y no dependen de la fecha.

### 2026-08-27 (b) — los cuatro abiertos de la sonda, **resueltos contra el canónico** (`D-08`)

Ventana de lectura: **cero mutaciones de fuente**. Se leyeron 1→EOF `models/caller.py` (441),
`agentic_models/.../openai_responses_shared.py` (486), `pi/packages/ai/src/api/
openai-responses-shared.ts` (552), `claude-code/src/services/compact/compact.ts` (1705),
`claude-code/src/utils/context.ts` y `context/compact/engine.py` (1002).

**Corrección de un error mío de la entrada anterior.** Sostuve que `/v1/responses` de
`llama-server` no rinde `timings`. **Es falso:** el bloque va en la raíz del `response.completed`
(`cache_n`, `prompt_n`, `prompt_ms`, `prompt_per_second`, `predicted_n`, `predicted_ms`,
`predicted_per_second`). La sonda derivó el prompt-eval del TTFT por esa creencia equivocada; los
números del propio servidor **corroboran** la tabla publicada (conn 18: prompt 5.570 @882,5 t/s =
6,3 s; predicted 3.898 en 142,95 s @27,26 t/s), así que ninguna conclusión de medida cambia. Lo
que cambia es la afirmación, que queda retirada.

**(3) `FIND-EMPTY-TOOL-OUT` — DEFECTO de nuestro port, con línea.**
`openai_responses_shared.py:201` colapsa a dos ramas lo que el canónico tiene en tres:

| | canónico `openai-responses-shared.ts:254` | nuestro port `:201` |
|---|---|---|
| hay texto | `textResult` | `text_result` |
| no hay texto pero sí imágenes | `"(see attached image)"` | `"(see attached image)"` |
| **ni texto ni imágenes** | **`"(no tool output)"`** | *(rama ausente)* ⇒ cae en la de imagen |

Un `glob` sin coincidencias viaja al modelo como `(see attached image)`. Fuente de homologación de
este fichero es **pi/ai**, no claude-code. La corrección es la tercera rama, literal.

**(4) `FIND-PARALLEL-SLOT` — DEFECTO, no conducta de la API.** Probado en el cable, no inferido.
De 21 respuestas, **5** traen dos `function_call` en la misma respuesta (conns 1, 4, 7, 8, 11) y en
**las cinco** los dos `output_item.added` llegan **antes** que los dos `done`. Conn 8, cronológico:
`added(rs_WnI2DUy58)` → `added(fc_fJUlhLla3, glob)` → 9 deltas → `added(fc_VrJxyvjIp, bash)` →
120 deltas → `done(rs_…)` → `done(fc_fJUlhLla3)` → `done(fc_VrJxyvjIp)`.

Causa, localizada: `openai_responses_shared.py:281-284` tiene **una sola casilla**
(`current_item` / `current_block`, con `block_index()` = «el último»), así que el segundo `added`
**pisa** al primero y cada `done` decide por `isinstance(current_block, …)`. Consecuencias, las
tres del mismo origen: el `done` del razonamiento falla su `isinstance` ⇒ **`thinking_signature`
nunca se fija y se pierde el round-trip**; el `done` de A emite `toolcall_end` **llevando B** ⇒ A
se pierde; el `done` de B encuentra la casilla vacía y cae al `else` (`:426-428`), que reconstruye
B desde `item_dict_done` ⇒ **B se emite dos veces**. En conn 8: `glob` descartada y `bash`
ejecutada **dos veces** — un efecto lateral repetido.

El canónico no tiene el defecto por construcción: `openai-responses-shared.ts:288-354` mantiene
`const outputSlots = new Map<number, ResponsesOutputSlot>()` con `getSlot`/`createSlot`/
`getOrCreateSlot` y `outputSlots.delete(event.output_index)` al cerrar; cada delta y cada `done`
resuelven **su** casilla. Divergencia de nuestro port ⇒ defecto nuestro.

**Segunda capa, que sí es decisión y no está en el canónico:** `llama-server` **no manda
`output_index`** (las claves del payload son `item`/`item_id`/`delta`). Un port literal por
`output_index` degeneraría igualmente a una casilla. La clave del mapa debe replegarse a
`item.id`/`item_id`. Va al catálogo P1–P9 (`agentic_models/gpt-5.x-conducta-vs-claude.md`).

`models/caller.py` queda **exonerado**: reenvía cada `toolcall_end` tal cual lo recibe.

**(1) ¿Hay algo que pagar del `/compact`? El canónico dice que sí, y dice qué.**

| | A (`compact.ts`) | B, medido en la sonda |
|---|---|---|
| razonamiento | `thinkingConfig: { type: 'disabled' }` (`:1305`) | se pide `ThinkingConfig(enabled=False)`; el modelo lo rechaza y `_summarize_once` (`engine.py:464-491`) repliega a `thinking=None` ⇒ el razonamiento por defecto corrió y **~1.600 de los 3.898 tokens** son razonamiento vertido al texto (~58 s de 143) |
| techo de salida | `min(COMPACT_MAX_OUTPUT_TOKENS = 20_000, max del modelo)` (`context.ts:12`, `compact.ts:1317-1320`) | **la misma fórmula**: `_assemble` hace `min(max_output_tokens, scaled(MAX_OUTPUT_TOKENS_FOR_SUMMARY = 20_000))` (`window.py:74`). Los 4.096 salen del `max_tokens` de la definición del modelo (`local_catalog.py:21`), no de una divergencia |
| caché de prompt | camino bifurcado por defecto: comparte el prefijo del hilo, `skipCacheWrite: true`, y **no** fija `maxOutputTokens` para no invalidar la clave (`:1179-1200`) | `cached_tokens = 0` — equivalente al camino de repliegue de A, no al de por defecto |

El repliegue de razonamiento **no** es divergencia (`D-21` se cumple: se declara). **Y el techo
tampoco lo es** — rectificado el mismo día, antes de que nadie decidiera sobre ello: la fórmula es
literal de A y el 4.096 es el `max_tokens` que la ficha del modelo declara, con lo que
`min(4.096, scaled(20.000))` da 4.096 con las dos políticas (`canonical` y `local`, ventana
65.536). Del `/compact` **no hay nada que pagar en el motor**: los 20.000 son de Claude porque
Claude los admite.

**Lo que sí queda, y no es del motor:** este modelo gasta ~1.600 de esos 4.096 en razonamiento que
no sabe callar, así que el resumen útil son ~2.300 tokens de un techo de 4.096. La palanca es la
ficha (`local_catalog.py:21`, `max_tokens`) contra lo que el `llama-server` admita de verdad, y la
patología del prompt de resumen ante gpt-5.x/Qwen. Catálogo P1–P9, no homologación.

**(2) `FIND-COMPACT-MANUAL-EVENT` — el canónico lo contesta.** A crea la frontera **dentro de la
propia función de compactación**, con `createCompactBoundaryMessage(isAutoCompact ? 'auto' :
'manual', …)` (`:598-602`) y `createCompactBoundaryMessage('manual', …)` (`:1014-1020`): **no hay
ruta manual muda**. Nuestro motor tampoco la tiene —`compact_conversation` (`:667-682`) y
`partial_compact_conversation` (`:846-861`) emiten `CompactionEvent` **cuando se les pasa
`emit`**—. La divergencia está en el integrador: `ManualCompaction._compact`
(`agentic_code/compaction.py:118-152`) llama **sin `emit`**. El arreglo es esa llamada, y con él
el texto de `_display_text` (`:154-174`) pasa a ser redundante con el render `⧉`.

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
- ~~**`FIND-RENDER-PARALLEL`** — con tools en paralelo el deck rotula la primera con el nombre y
  las demás con el `call_…|fc_…` crudo (`agentic_code/rendering.py`).~~ **ENUNCIADO FALSO,
  retractado el 2026-08-27.** El render es correcto y `rendering.py` no interviene: lo que se veía
  era el síntoma de un defecto del adaptador, renombrado **`FIND-PARALLEL-SLOT`** y probado en la
  entrada de abajo.

**Corrección del rótulo «pendientes de la palabra del usuario» (2026-08-27).** El § 5 del tramo 5
arrastraba dos temas bajo ese rótulo —la rama de `CompactionEvent` en `capture.py::_canonical_message`
y el render de compactación en `rendering.py`— y esta entrada los copió sin contrastar. **Las dos
cosas estaban mal.** Primera: el aplazamiento fue **decisión mía**, no del usuario; llamarlo «su
palabra» convirtió una omisión propia en una espera ajena, y además la enterró donde no se ve, que
es justo lo que impide contestarla. Segunda: contrastado el fuente 1→EOF, **los dos mecanismos ya
existen** —`capture.py:233-256` proyecta el `CompactionEvent` a `system/compact_boundary` con sus
catorce campos, y `rendering.py:190-192`, `:218-268` pinta `⧉ compactado` con desglose, sentido del
parcial y el aviso de repliegue de razonamiento—. Lo que queda no es lo que decía el rótulo, y sale
medido de esta sonda:

**`FIND-COMPACT-MANUAL-EVENT`, ABIERTO y decidible.** `ManualCompaction._compact`
(`agentic_code/compaction.py:118-152`) llama al motor **sin `emit`**, así que la ruta `/compact` no
produce `CompactionEvent`: ni línea en el `.jsonl` de captura ni render `⧉`. En la corrida de esta
sonda el usuario sólo vio `compactando…` y el `Compacted · …` que imprime `_display_text`
(`:154-174`). Los dos consumidores están construidos y alimentados **sólo por la ruta automática**
del lazo. Decidir: si `/compact` debe emitir el evento —y entonces el texto de `_display_text` pasa
a ser redundante con el render— o si la ruta manual se queda deliberadamente muda en el capture.
Es divergencia con A, que sí emite `compact_boundary` en las dos rutas.

**PUNTO DE RETOMA** (superado por la entrada `2026-08-27 (b)`, que los resuelve, y encuadrado por
`D-49`): (a) del `/compact` no hay nada que pagar en el motor; (b) `FIND-COMPACT-MANUAL-EVENT`,
abierto y de la variante manual. Más los dos laterales de la corrida, `FIND-EMPTY-TOOL-OUT` y
`FIND-PARALLEL-SLOT` (antes rotulado `FIND-RENDER-PARALLEL`, enunciado retractado).

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

## § 5 · addendum 2026-08-29 (c) — techo de salida y presupuesto de razonamiento cableados

Hecho, en `agentic_models`: `utils/estimate.py` **nuevo** (port de `estimate.ts`);
`providers/simple_options.py` con `clamp_max_tokens_to_context`, la firma de A
`build_base_options(model, context, options, api_key)`, `thinking_budget_param` y
`supports_thinking_budget` ensanchado **por declaración del modelo**, no por `api`;
el suelo de 16 tokens en `openai_responses.py` **y** en `azure_openai_responses.py`;
la emisión del presupuesto por `extra_body` y su reenganche en `stream_simple`;
`'thinkingBudgetParam': 'thinking_budget_tokens'` en el perfil local; y los **nueve**
llamantes de `build_base_options` pasando `context`.

Medido en vivo contra `llama-server` + `unsloth/Qwen3.8-27B-GGUF:UD-IQ4_XS`: `/slots` pasa
de `n_predict=-1` a `n_predict=4096`; y con el mismo prompt en `xhigh`, presupuesto **32** ⇒
139 caracteres de razonamiento frente a **4096** ⇒ 11.274. Las dos palancas actúan y no se
estorban.

Pruebas: `agentic_models` **78 → 96 verdes** (`test_output_ceiling.py` 10 +
`test_thinking_budget_transport.py` 8), acreditadas por **12 mutaciones revertidas → 12 rojas,
0 falsos positivos**, con purga de bytecode en cada revert (`D-62`) y `sha256` comprobado.
`agentic_code` **277 verdes**, sin cambio. Sin procesos supervivientes. Detalle, addendum a
`D-61` (la guarda `thinking_end_tags` de `server-common.cpp:1360`) y lo que queda abierto, en
`SEPARACION/DECISIONES.md § D-63`.

## § 5 · addendum 2026-08-29 (d) — el presupuesto ya no puede fallar en silencio

El riesgo que el addendum (c) dejaba anotado se paga en la misma ventana que lo produjo, por
palabra del usuario: la guarda `thinking_end_tags` es del motor, pero que nadie reportase su
incumplimiento era nuestro.

Contra fuente de `llama.cpp` (`HEAD c060ca974`, leída 1→EOF) queda establecido que la guarda **no
es observable a priori** —`/props` y `jinja::caps` no llevan las etiquetas— y que **no equivale a
«el modelo razona»**: `common_chat_params_init_muse_glimmer` (`chat.cpp:3332`) declara
`supports_thinking = true` sin fijarlas. El veredicto sólo puede salir de contrastar lo pedido
contra lo vuelto, con el criterio del sampler (`reasoning-budget.cpp:117-131`, `:166-186`): si el
presupuesto actuó, el razonamiento no excede `presupuesto + |secuencia de fin|`.

Hecho: `Usage` gana `thinking_budget_tokens` y `thinking_budget_honored` en
`agentic_runtime/contracts/events.py`, con umbral grueso `×2 + 64` —detecta el fallo mudo, **no
mide** el presupuesto— y `None` allí donde no hay evidencia; `caller.py` los emite en el `done` y
`agentic_code/streaming.py` los porta y los agrega al peor turno. `agentic_models` no se toca: el
núcleo no adquiere conocimiento de motor.

Pruebas: `agentic_code` **277 → 286 verdes** (`test_thinking_budget_verdict.py`, 9 casos),
acreditadas por **11 mutaciones revertidas → 11 rojas, 0 falsos positivos**, con purga de bytecode
(`D-62`) y `sha256` comprobado. En vivo: presupuesto 64 ⇒ 63 tokens, `honored=True`; sin
presupuesto ⇒ 1424, `None`; y control negativo con el presupuesto bajo un nombre que el motor no
lee ⇒ 1884, **`honored=False`**. Sin procesos supervivientes. Detalle en
`SEPARACION/DECISIONES.md § D-64`.

Retoma: quedan abiertos y sin tocar la calibración de `counted` contra un proveedor que
desglose `reasoning_tokens` (2026-09-01), `FIND-GOOGLE-CASING`, `cache_write_1h` sin consumidor
real, y `P1` de `PLAN-OPTIMIZACION-TUI.md` con el prototipo B (§ 6-bis).

## § 5 · addendum 2026-08-30 — `FIND-RT-MAXTURNS-1` pagado (primero de los cinco cortes E2E)

Hecho, en `agentic_runtime`: `MaxTurnsEvent(max_turns, turn_count)` en `contracts/events.py` y su
reexporte por el shim; `_MAX_TURNS = 50` **borrado** y `self._max_turns = max_turns` a secas ⇒
`None` = sin límite, como A (`maxTurns?: number`, `query.ts:191`); el `for … in range()` del bucle
pasa a `while True` con guarda que **emite al bus** antes de romper, en lugar del `logger.warning`
que nadie leía (`query.ts:1704-1712`); `TaskRecord` gana `end_reason`/`end_detail`; y
`execution/local/runtime.py:384` recoge el `LoopOutcome` que descartaba.

En `agentic_code` (`cablear-en-agentic-code-al-cerrar`): `StreamSnapshot` porta el terminal, la
captura emite el adjunto `max_turns_reached` y rotula su línea `result` como `error_max_turns`
—homólogo de `SDKResultErrorSchema`— con `status: "completed"`, y el aviso se pinta como fila de
transcript (`MaxTurnsBlock`), por `stderr` en el renderer de texto y con widget propio en la TUI.
El techo se pide con `--max-turns`, que ya existía.

Decisión (d): `TaskStatus.COMPLETED` **se conserva** —la tarea no falló— y el terminal viaja como
DATO; lo rotula el consumidor, como en A.

Pruebas: `agentic_code` **286 → 293 verdes** (`tests/test_max_turns_wire.py`, 7 casos), acreditadas
por **4 mutaciones revertidas → 4 rojas, 0 falsos positivos**, con purga de `__pycache__` en cada
revert (`D-62`). `ruff` limpio en los once ficheros tocados; `mypy` con su único error preexistente,
comprobado idéntico en `HEAD`. Sin procesos supervivientes. Sintéticas de `agentic_runtime` ni
corridas ni tocadas. Detalle en `SEPARACION/DECISIONES.md § D-65` y en
`SEPARACION/VALIDACION-AGENTIC-CODE.md § 2 septies` / `§ 4 quinquies`.

Retoma: los cuatro cortes restantes de la observación E2E, por orden — `FIND-CODE-ESC-1`
(cancelación por ESC, inyección de 5 puntos ya anunciada), `FIND-RT-COMPACT-EVT-1` (la compactación
no tiene evento de INICIO), `FIND-RT-TOOLINPUT-1` (`caller.py:278-299` descarta `toolcall_start` y
`toolcall_delta`, luego `StreamMode.TOOL_INPUT` no describe nunca lo que nombra) y
`FIND-CODE-TODO-1` (verificar antes si `RuntimeContextForker` comparte `app_state`). Siguen abiertos
y sin tocar: la calibración de `counted` (2026-09-01), `FIND-GOOGLE-CASING`, `cache_write_1h` sin
consumidor real, y `P1` de `PLAN-OPTIMIZACION-TUI.md`.

## § 5 · addendum 2026-08-31 — `FIND-CODE-ESC-1` pagado (segundo de los cinco cortes E2E)

El cable del aborto estaba tendido y **sin corriente**: `AbortSignal` existía, `ctx.stop` viajaba
hasta el proveedor y el bucle lo consultaba en sus tres guardas, pero `LocalAgentRuntime.cancel`
iba directo al `kill` sin levantarlo nunca. El ESC mataba la corrutina desde fuera y el turno salía
`error_killed` / `end_reason: null` / `result: ""`, con el texto parcial perdido y los `tool_use`
**huérfanos** envenenando la sesión siguiente. En A el aborto es cooperativo y sale por la rama de
éxito (`query.ts:1005-1052`), cerrando antes los pendientes con `'Interrupted by user'`
(`query.ts:123-149`).

Hecho, en `agentic_runtime`: los tres literales canónicos en `contracts/abort.py`; `AbortEvent`
(homólogo del `UserInterruptionMessage`) en `contracts/events.py` y su reexporte por el shim;
`ABORTED_HARD` en `loop/outcome.py`; `TaskRecord.stop` + `set_stop` y un `kill(...)` que acepta
`result`/`end_reason`/`end_detail`; `cancel(...)` **con gracia** (5 s por defecto,
`wait_for(shield(task))`) que levanta la señal y deja al bucle cerrar en orden, cayendo al kill duro
sólo si la gracia expira; la rama `CancelledError` de `_run_loop` que ahora **vuelca sesión y
persiste** igual que la ruta feliz; y, en `agent_loop.py`, `_announce_abort(...)` en las tres
salidas más el volcado del assistant parcial y el **cierre de los huérfanos** con `is_error=True`.

En `agentic_code` (`cablear-en-agentic-code-al-cerrar`): `StreamSnapshot.abort_reason`/
`abort_tool_use`, el mapeo `{type:'system', subtype:'abort', …}` en la captura, y un `driver` que
**deja de fabricar** `KILLED`/`""`: lee el terminal de quien abortó.

Acreditación (`D-12·b`): copia propia sellada de los 10 fuentes, `PRE`/`POST` verificados por
`sha256sum -c`, purga de `__pycache__` en cada paso (`D-62`). Con `pre` el defecto reaparece entero;
con `post`, el `.jsonl` da `subtype: "error_aborted"` / `status: "completed"` /
`abort_reason: "turn_cancelled"`, el `tool_result` del huérfano y los 40 tokens parciales
conservados. Harness 4/4: `aborted_streaming`, `aborted_tools`, huérfano cerrado y `aborted_hard`
contra un modelo sordo. `agentic_code` **293 verdes**;
`test_repl_cancels_active_turn_and_returns_to_prompt` **reescrito con el criterio nuevo, no
ablandado**. `mypy` con su único error preexistente (`agent_loop.py:266`); **`ruff` no se pudo
correr: no está instalado** en ninguno de los dos entornos, la estática fue `compileall` + `mypy`.
Sin procesos supervivientes. Sintéticas de `agentic_runtime` ni corridas ni tocadas. Detalle en
`SEPARACION/DECISIONES.md § D-66`.

Deroga la divergencia 2 de `D-65`: el segundo `yield` de la rama de aborto (`query.ts:1506-1514`)
**queda portado**.

Retoma: los tres cortes restantes, por orden — `FIND-RT-COMPACT-EVT-1` (la compactación no tiene
evento de INICIO; anotado de paso: `events/event_types.py` **no** reexporta `CompactionEvent`),
`FIND-RT-TOOLINPUT-1` (`caller.py:278-299` descarta `toolcall_start`/`toolcall_delta`;
`streaming.py:166`) y `FIND-CODE-TODO-1` (verificar antes si `RuntimeContextForker` comparte
`app_state`). Hallazgos nuevos anotados y **no** tocados: `LoopEndReason.MODEL_ERROR` sale rotulado
`subtype: "success"` con `end_reason: null` —`capture.finish` lee el snapshot, no el `TaskRecord`—,
y el umbral de 350 ms del ESC en `tui.py` es conducta de producto no homologada. Siguen abiertos:
la calibración de `counted` (2026-09-01), `FIND-GOOGLE-CASING`, `cache_write_1h` sin consumidor
real, y `P1` de `PLAN-OPTIMIZACION-TUI.md`.

## § 5 · addendum 2026-08-31 (b) — las dos hipótesis que dejó abiertas el ESC, resueltas contra el canónico

Ventana de **lectura**: cero mutaciones de fuente. Leídos 1→EOF `claude-code/src/query.ts` (1730, en
dos páginas por el techo de 25k tokens) y `claude-code/src/services/api/claude.ts` (3419, en cuatro),
más `agentic_code/capture.py` (361) y `driver.py` (144).

**Corrección de un error mío, del propio corte.** Sostuve en el cierre anterior que un ESC en pleno
streaming aterriza en `{ reason: 'model_error' }`. Es **falso**, y salió de leer el canónico por
tramos en vez de hasta EOF: `claude.ts:2794-2799` —y su gemelo de la rama de repliegue por 404,
`:2738-2741`— hace `if (error instanceof APIUserAbortError) { releaseStreamResources(); return }`, o
sea el generador **vuelve limpio sin emitir nada**; el `for await` de `query.ts` termina normal y el
terminal es `aborted_streaming` (`query.ts:1015-1051`). El `catch` externo de `query.ts:955-997`
**no se alcanza** por ESC. Lo que B emite ya era eso, así que la conducta homologada no cambia; lo
que se retira es la afirmación.

**H1 — «el razonamiento en vuelo se pierde al abortar» (1588 `ThinkingEvent`, ninguno `final`):
CERRADA, no es hallazgo.** A no materializa jamás un bloque de pensamiento sin cerrar: el
`AssistantMessage` se construye y se emite **sólo** dentro de `case 'content_block_stop'`
(`claude.ts:2171-2211`); un stream que acaba sin ningún bloque completo se trata como fallo de proxy
y no como contenido recuperable (`:2350`); y cuando A sí retiene un parcial con firma inválida, lo
**destruye** —tombstone con su motivo escrito (`query.ts:712-725`) y `stripSignatureBlocks` antes de
reintentar (`:924-929`)—. Nuestra captura, además, **ya registra todos los deltas**: `capture.py:73-80`
graba cada evento del bus sin filtrar y `:161-183` proyecta el `ThinkingEvent` no final como
`content_block_delta`/`thinking_delta`, que es la misma forma que A emite en `:2299-2303`. Lo único
ausente sería un `content_block_stop` sintético con `signature: ""`, que es exactamente lo que la
remediación del ecosistema prohíbe escribir. **Retirada mi propuesta H1-b**, y con ella su
justificación «por auditabilidad», que era invención mía y no criterio del canónico.

**H2 — el terminal del kill duro invisible en el `.jsonl`: sale como CORTE PROPIO,
`FIND-CODE-ABORT-TERM-1`.** No engorda `FIND-CODE-ESC-1`, que queda cerrado como está. Va emparejado
con el hallazgo `LoopEndReason.MODEL_ERROR` rotulado `subtype: "success"` con `end_reason: null`,
porque los dos nacen del mismo sitio: `capture.py:82-112`, donde `finish()` deriva el `subtype` de
`status`/`snapshot.end_reason` y **no tiene rama** para un turno que muere sin snapshot terminal.

**Re-medido contra modelo real sobre el árbol de hoy** (`llama-server` vivo, `D-15`), porque el
cierre no puede descansar en la corrida de otra ventana: **cinco turnos**, cuatro abortados y uno
que terminó solo. Los cuatro abortados dan el mismo terminal —`subtype: "error_aborted"`,
`status: "completed"`, `end_reason: "aborted"`, `abort_reason: "turn_cancelled"`— con el
`{type:'system', subtype:'abort'}` y el `[Request interrupted by user]` presentes en los cuatro.

**Corrección de método dentro de la propia medición:** los tres primeros tiros cortaban con un
`sleep` a ojo y **dos de tres cayeron en pleno razonamiento** (1512, 1384 y 1140 `ThinkingEvent`,
ninguno final, cero texto), o sea no ejercitaban la rama del parcial; el cuarto ni siquiera abortó
porque el turno acabó antes. El corte pasó a **colgar del bus** —ESC 3 s después del primer
`TokenEvent`— y con eso la rama queda medida: **81 tokens emitidos, `result` con el texto parcial
conservado** en vez del `""` del defecto, y el assistant parcial en la captura.

Y esas mismas corridas **confirman H1 en vivo por el otro lado**: los 1140–1512 `ThinkingEvent` del
turno abortado **están en el `.jsonl`**, que es exactamente lo que decía el cierre — el razonamiento
en vuelo no se pierde, se graba como deltas.

**`FIND-CODE-ESC-2`, ABIERTO — y corrige el alcance de lo que el addendum (a) daba por cerrado.**
La rama de aborto **durante la fase de tools** no estaba medida contra modelo real: los cinco turnos
de arriba salieron con `tool_use: false`. Medida ahora, con el corte colgado del primer
`ToolCallEvent`, **dos de tres caen al kill duro**: `subtype: "error_killed"`, `status: "killed"`,
`end_reason: null`, `result: ""` — el patrón exacto del defecto que este corte decía cerrar.

Localizado, no supuesto. En los dos turnos matados el último evento de la captura es
`TurnStartEvent`: la tool **ya devolvió** su resultado y el bucle abrió la vuelta siguiente, así que
el ESC cae **durante el prefill de la segunda llamada al modelo**. El hueco entre ese último evento
y la línea `result` es de **5,21 s** y **9,01 s** contra los **0,00 s** del turno que sí abortó
limpio (ése estaba emitiendo texto). O sea: la gracia de 5 s de `cancel(...)` expira esperando a un
modelo cuyo prefill son ~20 s, y el camino cae al `kill` duro con el terminal mudo.

Hipótesis a verificar en el corte, **no dada por buena aquí**: que la señal llegue al proveedor no
basta si la petición HTTP en vuelo no se cancela con ella, y el bucle sólo la consulta entre pasos.
En A el aborto es inmediato porque el `signal` va al SDK y rinde `APIUserAbortError`
(`claude.ts:2434-2451`, `:2794-2799`). Se resuelve leyendo el camino del proveedor 1→EOF, no
subiendo la gracia: un temporizador mayor tapa la medida sin arreglar la conducta.

Retoma: **`FIND-CODE-ESC-2` pasa al frente de la cola**, por delante de `FIND-RT-COMPACT-EVT-1`,
`FIND-RT-TOOLINPUT-1` y `FIND-CODE-TODO-1`, con `FIND-CODE-ABORT-TERM-1` detrás — su terminal mudo
es la otra cara de este mismo kill.

## § 5 · addendum 2026-08-31 (c) — `FIND-CODE-ESC-2` pagado: la señal ya corta la petición en vuelo

La hipótesis del addendum (b) queda **confirmada en fuente**, y el defecto era de dos piezas, no de
una. (1) `contracts/abort.py` sólo sabía **consultarse**: `aborted` era una propiedad y no había
ningún canal por el que despertar a un `await` bloqueado —el homólogo JS es sondeable *y* esperable
(`signal.aborted` + `addEventListener("abort")`)—, así que nada podía sacar al consumidor de
`EventStream.__aiter__`. (2) Ningún proveedor entregaba la señal a la capa HTTP y el productor salía
**desprendido** por `asyncio.ensure_future`, luego cerrar el consumidor dejaba la petición viva: el
bucle sólo podía enterarse del aborto cuando llegara un evento, y en un prefill de ~20 s no llega
ninguno. La gracia de 5 s expiraba esperando a nadie.

Hecho, en `agentic_runtime`: `AbortSignal` gana `async def wait()` en el Protocol y `AbortController`
lo implementa con un `asyncio.Event` **perezoso** (se crea al primer `wait`, para no exigir bucle en
construcción); `abort()` lo levanta. Nada más cambia: literales, `AbortReason` y `__all__` intactos.

En `agentic_models`, la pieza genérica que evita nueve copias: `utils/abort_signals.py` suma
`watch_abort(signal)` —usa `wait()` si el objeto lo tiene, y si no cae a sondeo de 50 ms, de forma
que la señal se acepta por **pato** y la capa de modelos no importa del núcleo— y
`launch_with_abort(coro, options)`, que sustituye al `ensure_future` crudo: lanza la corrutina,
vigila la señal en paralelo y **cancela la Task** cuando se levanta. Cancelar la Task interrumpe el
`await` de httpx/SDK y cierra la conexión: es el equivalente Python del `signal` que en A rinde
`APIUserAbortError` (`claude.ts:2434-2451`, `:2794-2799`).

La trampa que obliga a tocar los nueve proveedores: `asyncio.CancelledError` **no es** `Exception`,
así que el `except Exception` terminal de cada fichero no lo vería y el stream quedaría sin cerrar.
Cada proveedor recibe por eso una rama `except asyncio.CancelledError` **delante** de la suya, con
su propio barrido de parciales, `stop_reason = "aborted"`, `push({"type":"error"})`, `end()` y
`raise` —la cancelación se repropaga, no se traga—. Tres ediciones por fichero, misma forma en
`anthropic`, `google`, `google_vertex`, `openai_responses`, `azure_openai_responses`,
`openai_completions`, `mistral`, `openai_codex_responses` y `amazon_bedrock`.

**La gracia sigue en 5 s.** `caller.py` y `agent_loop.py` no se tocan. `stream.py` tampoco: el asa de
la Task no existe ahí, y un envoltorio en ese punto habría desbloqueado al consumidor dejando la
petición en vuelo —corrección de diseño propia, anunciada antes de mutar—.

Acreditación contra modelo real (`D-15`), `llama-server` en `:8080`, mismo prompt y mismo harness
colgado del primer `ToolCallEvent`: ESC a 2,0 s corta en la **vuelta 2** y ESC a 6,0 s en la
**vuelta 3**, los dos con `subtype: "error_aborted"`, `status: "completed"`,
`end_reason: "aborted"`, `abort_reason: "turn_cancelled"`; el tiro a 12,0 s no abortó porque el
turno acabó antes, y se declara inconcluyente en vez de contarlo. **`error_killed` / `status:
killed` / `end_reason: null` no reaparecen en ninguna corrida.** Estática: `compileall` OK en los
once ficheros tocados. Sin procesos supervivientes. Sintéticas de `agentic_runtime` ni corridas ni
tocadas.

Queda declarado y **no** pagado aquí: el `result: ""` del turno abortado en fase de tools sigue
vacío. No es de este corte —es `capture.finish` derivando el terminal sin rama para el parcial de
tools—, y es exactamente `FIND-CODE-ABORT-TERM-1`, que pasa al frente.

Riesgo aceptado y verificado por E2E: añadir `wait` al Protocol `@runtime_checkable` cambia el
veredicto de un `isinstance(..., AbortSignal)` para objetos sin ese método; el camino real pasa.
Los dos `# TODO(port)` de `amazon_bedrock.py` (`BotoConfig` no llega a `session.client()`,
`use_bearer` sin cablear) se **conservan** pese al barrido de comentarios, por ser deuda de port
declarada y medida: borrarlos sería esconderla.

### Barrido de los nueve: siete estaban pagados, tres no

Inyectar el helper no basta si el proveedor no tiene dónde suspenderse. Barridos uno a uno contra
los SDK instalados:

**`google.py` — no era «existe-roto», estaba MUERTO, y corrige mi propia nota.** Sostuve que el SDK
Python «previsiblemente ignora» `config["abortSignal"]`. Medido:
`GenerateContentConfig` es pydantic con `extra=forbid` y devuelve
`ValidationError: Extra inputs are not permitted [extra_forbidden]`. Como el runtime **siempre**
pasa `ctx.stop`, toda llamada a Google reventaba en `_build_params` y el `except Exception` la
disfrazaba de error de modelo. Pagado: la línea sale y queda sólo la pre-guarda
`if signal.aborted: raise` —el aborto viaja por cancelación de Task, que es el mecanismo
homologado—. De paso queda medido que el camelCase **sí** lo acepta el SDK por alias
(`maxOutputTokens` → `max_output_tokens`): `FIND-GOOGLE-CASING` no se dispara por esta vía.

**`google_vertex.py` — cliente síncrono dentro de una corrutina.**
`client.models.generate_content_stream` devuelve `Iterator`; `client.aio.models.…` es corrutina y
devuelve `AsyncIterator` (comprobado por introspección del paquete). El fichero hacía `async for`
sobre el **síncrono**: no ha podido funcionar nunca, y aun funcionando no tendría un solo punto de
suspensión, luego el `cancel` sería sordo. Pagado: `await client.aio.models.generate_content_stream`
más la pre-guarda que le faltaba, por simetría con Google.

Verificado contra el SDK real: los dos `config` validan y las dos pre-guardas disparan
`Request aborted` con la señal levantada.

**Pagados ya, comprobados uno a uno:** `anthropic` (`with_streaming_response` + `async for`),
`openai_responses`, `azure_openai_responses`, `openai_completions` (`AsyncOpenAI`), `mistral`
(`await mistral.chat.stream` + `async for`) y `openai_codex_responses` (`httpx.AsyncClient`).
`faux.py` no está en `providers/__init__.py` y no se toca. La rama `providers/images` no es
streaming —se consume con un `await` directo y su `except Exception` no atrapa `CancelledError`—,
así que la cancelación ya propaga limpia y no necesita nada.

### `DEUDA-BEDROCK-ABORT-1` — declarada, medida y APLAZADA por palabra del usuario

`amazon_bedrock.py` es el único proveedor que queda **sordo al aborto**, y no por olvido: boto3 es
síncrono de arriba abajo. `client.converse_stream(**command_input)` (`:431`) bloquea, y
`for item in response.get("stream", [])` (`:445`) itera bloqueando. **Cero `await` en todo el bucle
de streaming.** Como `Task.cancel()` sólo actúa en un punto de suspensión, el `launch_with_abort`
no puede interrumpirlo; y mientras el modelo emite, el turno bloquea el event loop entero —bus y
TUI incluidos—.

Forma del pago, ya diseñada y **no** aplicada: `await asyncio.to_thread(client.converse_stream,
**command_input)` para la llamada, y tirar del `EventStream` chunk a chunk con
`await asyncio.to_thread(next, it, _FIN)` —un punto de suspensión por chunk, el loop libre— más el
cierre del stream en la rama `CancelledError`. Unas diez líneas.

Aplazada por decisión del usuario (2026-08-31): Bedrock no está en uso previsible a corto plazo y
el corte de cabecera pesa más. **No se rotula como pagada.** Y aunque se aplicase hoy, quedaría sin
acreditación en vivo: no hay credenciales AWS en esta máquina, así que sólo podría declararse
cableada en forma y **no medida contra proveedor real** (`D-56`). Se paga cuando Bedrock entre en
uso, o antes si aparece consumidor.

### Corrección: `ruff` sí está instalado

El addendum `2026-08-31` afirma que **`ruff` no se pudo correr, no está instalado en ninguno de los
dos entornos**. Está rancio: `ruff 0.16.1` vive en el venv de `agentic_code`. Corrido ahora, y
medido contra los blobs de `HEAD` fichero a fichero: los 43 hallazgos de `providers/` son **todos
preexistentes**, cero añadidos por este diff. Los **dos** que sí eran míos —`typing.Coroutine`
deprecado en `abort_signals.py` y `__slots__` sin ordenar en `contracts/abort.py`— quedan pagados,
no rotulados.

Retoma: `FIND-CODE-ABORT-TERM-1` al frente, y detrás `FIND-RT-COMPACT-EVT-1`, `FIND-RT-TOOLINPUT-1`
y `FIND-CODE-TODO-1`. Siguen abiertos: `DEUDA-BEDROCK-ABORT-1` (arriba), la calibración de `counted`
(2026-09-01), `FIND-GOOGLE-CASING`, `cache_write_1h` sin consumidor real, y `P1` de
`PLAN-OPTIMIZACION-TUI.md`.
