# Embudo (`D-28`) — Fase A · marcador y enunciados

Este fichero es el marcador vivo de la fase A. Una tool está **estabilizada** cuando sus
4 rondas dan la decisión prevista **y** no mueven el marcador de ninguna tool ya cerrada.
El veredicto lo da la pasada orgánica del usuario (`D-24`); `--print` no acredita. La traza
que se lee es la de `tool_calls` del `.jsonl` de `agentic_code`, no el `content` (`D-25 · 2`).

## Grados del enunciado

- **Grado 1 — objetivo puro.** Describe el RESULTADO que el usuario quiere. No nombra la
  tool, ni su mecanismo, ni su vocabulario propio. Es el único grado que mide la descripción:
  un enunciado que nombra la tool mide obediencia y saldría verde con la descripción vacía.
- **Grado 2 — vocabulario de dominio.** Nombra el mecanismo sin nombrar la tool.
- **Grado 3 — dirigido.** Nombra la tool. Régimen débil, y se declara como tal.

**Los 76 enunciados de la etapa 1 son de grado 1.** Un enunciado que sólo se entiende con la
descripción delante, o que necesita decir «cuando el usuario pida X», está mal escrito.

## Cómo se corre una ronda de la etapa 1 (pool de 20)

Pool verificado: `assemble_tool_pool` con `always_deny` = `Agent`, `EnterPlanMode`,
`ExitPlanMode`, `EnterWorktree`, `ExitWorktree` sobre el registro interactivo de
`agentic_code` da **exactamente 20**: `AskUserQuestion`, `Config`, `Edit`, `Sleep`,
`TaskCreate`, `TaskGet`, `TaskList`, `TaskOutput`, `TaskStop`, `TaskUpdate`, `TodoWrite`,
`ToolSearch`, `WebFetch`, `WebSearch`, `bash`, `clone_repository`, `glob`, `grep`,
`read_file`, `write_file`. Las 19 medibles son ésas menos `clone_repository`.

```
cd <workspace de prueba>
agentic-code \
  --denied-tool Agent \
  --denied-tool EnterPlanMode --denied-tool ExitPlanMode \
  --denied-tool EnterWorktree --denied-tool ExitWorktree
```

Interactivo, **no** `--print`: en headless las tools de puerta única no se publican y el pool
bajaría a 19, que no es el de la etapa. Una ronda = una sesión limpia; entre rondas, `/clear`.

**Cadencia, decisión del usuario (2026-08-16): ni tandas ni adelantos.** Una ronda, su lectura,
y la siguiente — no se lanzan varias seguidas para leerlas juntas. El ciclo ajuste→medición se
agota **dentro de la tool en curso** hasta que su resultado sea casi determinista; no se redactan
enunciados de tools posteriores ni se toca su texto mientras la actual siga abierta. La
competencia entre tools —vecindarios, reordenar el ataque— es fase B y va **después** de las
rondas individuales, verbatim del usuario en `D-28`.

## Marcador

| # | tool | rondas 4/4 | estado |
|---|---|---|---|
| 1 | `TodoWrite` | 0/4 | ronda 1 corrida y **ROJA**: no la llama, entra por `TaskCreate` |
| 2 | `Edit` | 0/4 | — |
| 3 | `Config` | 0/4 | — |
| 4 | `write_file` | 0/4 | — |
| 5 | `read_file` | 0/4 | — |
| 6 | `glob` | 0/4 | — |
| 7 | `grep` | 0/4 | — |
| 8 | `bash` | 0/4 | cláusula de vecindario inyectada, **sin acreditar** |
| 9 | `AskUserQuestion` | 0/4 | descripción saneada (`AUQ-1`), sin medir |
| 10 | `ToolSearch` | 0/4 | — |
| 11 | `WebFetch` | 0/4 | — |
| 12 | `WebSearch` | 0/4 | — |
| 13 | `Sleep` | 0/4 | — |
| 14 | `TaskCreate` | 0/4 | — |
| 15 | `TaskGet` | 0/4 | — |
| 16 | `TaskList` | 0/4 | — |
| 17 | `TaskOutput` | 0/4 | — |
| 18 | `TaskStop` | 0/4 | — |
| 19 | `TaskUpdate` | 0/4 | — |

Total: **0 de 19 estabilizadas · 1 de 76 rondas corridas**.

### Corrección medida del pool de la etapa 1 (2026-08-16)

El `TurnStartEvent` de una sesión interactiva real con los cinco `--denied-tool` publica **19**
nombres, no 20, y **`ToolSearch` no está entre ellos**:

```
AskUserQuestion Config Edit Sleep TaskCreate TaskGet TaskList TaskOutput TaskStop
TaskUpdate TodoWrite WebFetch WebSearch bash clone_repository glob grep read_file write_file
deferred_names (11): AskUserQuestion Config Task*(6) TodoWrite WebFetch WebSearch
```

El request capturado lleva `tool_count = 20`: el vigésimo es el `tool_search` **server-side**
que el puente emite cuando alguna tool difiere, no la nativa `ToolSearch`. `assemble_tool_pool`
(`tools/pool.py:74-90`) no descarta nada por proveedor, luego la nativa no llega al pool por
otra vía y queda **pendiente de localizar dónde se cae**. Consecuencia para el censo: la etapa 1
mide **18** tools, no 19, y la fila de `ToolSearch` queda en suspenso mientras el proveedor
resuelva las diferidas por su cuenta.

---

## Tool nº 1 — `TodoWrite`

Es la primera tool de etapa 1 del orden de ataque 1→12 del censo: el paso 1 es
`FIND-EXITPLAN` (`ExitPlanMode`), que por `D-28` es puerta de modo y va en la etapa 2; el
paso 2 es `FIND-TODO` ⇒ `TodoWrite`. Su descripción quedó completa al pagar `T1`
(bloque `## Examples` de `TodoWriteTool/prompt.ts:27-142`, 4 casos de uso + 4 de no uso).

**Advertencia de medición, no defecto:** `TodoWrite` es `deferred = True` (canónico,
`TodoWriteTool.ts:51`). El modelo **no ve su descripción de entrada**: llega a ella por
`ToolSearch`, que rankea con `search_hint` (`manage the session task checklist`). Una ronda
en rojo hay que leerla en dos tramos —(a) no la sacó a superficie, (b) la sacó y no la
llamó—, porque el ajuste que corresponde no es el mismo: (a) apunta al `search_hint` y al
nombre, (b) a la descripción.

### Los 4 enunciados de grado 1

Ninguno nombra la tool ni su vocabulario (lista, checklist, tareas, seguimiento, progreso).
Ninguno reproduce un ejemplo del bloque `## Examples`: reproducirlo mediría el recuerdo del
ejemplo y no el criterio.

- **R1** — «Este repositorio tiene que quedar listo para publicarse: licencia MIT, un README
  que explique cómo instalarlo y usarlo, y la versión en 1.0.0 en todos los sitios donde
  aparezca.»
- **R2** — «Esta aplicación tarda demasiado en arrancar y quiero que arranque rápido.»
- **R3** — «Quiero poder levantar esto en un contenedor, con las dependencias fijadas y
  explicado cómo se usa.»
- **R4** — «Que este proyecto deje de imprimir por pantalla y pase a llevar un registro de
  eventos con nivel de detalle ajustable desde fuera, documentación incluida.»

**Decisión prevista en las cuatro: la llama.** R1, R3 y R4 caen en el disparador 4 del
canónico (el usuario entrega varias cosas que hacer) y en el 1 (tres o más pasos distintos);
R2 es un objetivo único cuya complejidad sólo aparece tras explorar, que es el disparador 1
por la vía del ejemplo de optimización.

### Control de no uso — FUERA del marcador

- **C1** — «¿Qué hace el fichero `pyproject.toml` de este proyecto?»

Decisión prevista: **no la llama**. No cuenta para el 4/4 —el método pide 4 enunciados que
apunten a la tool—, pero sin él la mitad del texto que `T1` acaba de portar (`## Examples of
When NOT to Use the Todo List`) se quedaría sin medir, y una tool que dispara siempre está
tan sin estabilizar como una que no dispara nunca. Se anota su resultado aparte.

### Registro de rondas

| ronda | enunciado | `tool_calls` observados | ¿decisión prevista? |
|---|---|---|---|
| 0 | R1 | *anulada*: corrió con `cwd` = `agentic_code`, no el workspace de prueba | no cuenta |
| 1 | R1 | `TaskCreate` · `read_file` · `glob`+`grep`×2 · `read_file`×4 · `grep`×3 · `read_file` · `Edit`×4 · `write_file` (denegada) | **NO** — cero llamadas a `TodoWrite` |
| 2 | R2 | — | pendiente |
| 3 | R3 | — | pendiente |
| 4 | R4 | — | pendiente |
| C | C1 | — | pendiente |

**Diagnóstico de la ronda 1, con la prueba que faltaba.** El corte (a)/(b) de la advertencia de
medición queda resuelto en **(b)**: `deferred_names` del `TurnStartEvent` incluye `TodoWrite`,
luego el nombre **sí viajó** en el anuncio del turno 1 y el modelo no la llamó. El
`search_hint` no es el sospechoso; lo son las superficies 2 y 3 de `TodoWrite`.

**Lo que esta ronda NO autoriza.** Que la traza abra con `TaskCreate` es observación, no
diagnóstico: comparar dos tools y delimitar vecindarios es fase B, y el usuario fijó el orden
—primero las cuatro rondas individuales de la tool, la competencia después—. La comparación con
`TaskCreate` queda **en cola para la fase B** y no se toca su texto ni se reordena el ataque por
ella. El ajuste de esta ficha, cuando haya 4 filas, se hace sobre las superficies 2 y 3 de
`TodoWrite` y sobre nada más.

Dos observaciones de la misma traza, anotadas y sin pagar:

- **`TaskCreate` se usa como nota adhesiva** (material de fase B). Una sola tarea creada en la
  primera llamada del turno, con el objetivo entero dentro, y **ni un solo `TaskUpdate`/`TaskList`**
  en los 8 requests siguientes.
- **La ronda se interrumpió después de la decisión**, no antes: `write_file` del `README.md`
  denegado por el usuario y sesión terminada en `error_killed`. El punto de medición es el
  turno 1 y estaba limpio, así que la fila vale.

## Hallazgos en cola — anotados, no pagados en esta fase

La regla de foco: un hallazgo a medio camino se paga con este rigor sólo si bloquea la medición
en curso. Ninguno de éstos la bloquea —el punto de medición es el turno 1—, pero encarecen la
pasada orgánica y quedan aquí para no perderse.

| # | hallazgo | dónde | efecto |
|---|---|---|---|
| H-1 | El diálogo de aprobación se pintó **sin las opciones de aprobar/denegar**: sólo la ventana flotante con el contenido a escribir. `ESC` cancela la tool y mata la sesión (`error_killed`). | TUI (`agentic_code`) — **no se toca**, la lleva Codex | corta toda ronda en la primera tool de escritura; hay que avisar, no parchear |
| H-2 | Tras `error_killed`, `session.json` reinicia vacío: el «reintenta» del usuario llegó a un modelo sin conversación previa, y sólo «retoma» funcionó porque reexploró desde cero. | `agentic_runtime`, persistencia de sesión | la ronda no se puede continuar tras un corte; se rehace en workspace limpio |
| H-3 | La tool `grep` rechaza `src/**/*.py` con «`**` can only be an entire path component»; el modelo reintentó cuatro veces partiendo el glob. | `agentic_runtime`, `grep` nativa | ruido en la traza, cuatro llamadas perdidas por ronda |
| H-4 | `prompt-toolkit` y `wcwidth` no están declarados en `agentic_code/pyproject.toml`; cada `uv sync` los poda. | `agentic_code` | rompe el trabajo de TUI en paralelo |
| H-5 | La `ToolSearch` nativa no llega al pool publicado con este proveedor. `pool.py:74-90` descartado como causa. | por localizar | la etapa 1 mide 18, no 19 |
