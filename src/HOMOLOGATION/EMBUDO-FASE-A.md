# Embudo — Fase A · marcador

Se anota **sólo la estabilización**: 4 de 4 con la decisión prevista. Un check y nada más.
Todo lo anterior de este fichero (método, enunciados, diagnósticos) está en el historial de git.

Dos columnas, ambas exigidas para avanzar:

- **elige** — la tool gana los 4 casos que son suyos.
- **cierra** — el resultado basta: tras su llamada no se invoca otra tool para obtener lo que ese resultado debía afirmar (existencia, efecto, alcance).

## Bloque 1 — individuales

| tool | elige | cierra |
|---|---|---|
| `write_file` | ok | ok |
| `read_file` | ok | ok |
| `glob` | ok | ok |
| `grep` | | |
| `bash` | | |
| `WebSearch` | | |
| `WebFetch` | | |

## Bloque 2 — compuestas

| tool | elige | cierra |
|---|---|---|
| `TodoWrite` | | |
| `Edit` | | |

## Bloque 3 — familia `Task`, marcador único

| tools | elige | cierra |
|---|---|---|
| `TaskCreate` · `TaskGet` · `TaskList` · `TaskOutput` · `TaskStop` · `TaskUpdate` | | |

## Bloque 4 — aparte

| tool | elige | cierra |
|---|---|---|
| `AskUserQuestion` | | |

Fuera del embudo: `Config` · `Sleep` · `ToolSearch`.
