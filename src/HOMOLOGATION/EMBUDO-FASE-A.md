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

## Marcador

| # | tool | rondas 4/4 | estado |
|---|---|---|---|
| 1 | `TodoWrite` | 0/4 | enunciados escritos, ronda 1 pendiente de pasada orgánica |
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

Total: **0 de 19 estabilizadas · 0 de 76 rondas corridas**.

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
| 1 | R1 | — | pendiente |
| 2 | R2 | — | pendiente |
| 3 | R3 | — | pendiente |
| 4 | R4 | — | pendiente |
| C | C1 | — | pendiente |
