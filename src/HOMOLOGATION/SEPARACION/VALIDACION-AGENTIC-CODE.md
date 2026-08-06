# VALIDACIÓN POR CONSUMIDOR REAL — `agentic_code` sobre `agentic_runtime`

> **Qué es esto.** El método de trabajo decidido por el usuario el **2026-08-06** (`DECISIONES.md · D-15`)
> y el **listado de problemas confirmados** que produjo su primera aplicación. Este fichero es de ESTADO,
> no de log (`D-09`): una viñeta es una línea, y lo que se paga se marca aquí mismo.

---

## 1 · El método

`agentic_runtime` es una librería sin usuarios. Una suite propia sólo puede probar lo que su autor
**pensó** probar, y el barrido EOF del canónico (10ª ventana) demostró el patrón de fallo dominante:
**el runtime tiene el dato cargado y no lo pone en ninguna lista que el modelo vea**. Ninguna de esas
omisiones la vio un test verde; las vio un consumidor.

El ciclo, en cuatro pasos:

1. **Ejercitar** una capacidad de `agentic_runtime` **desde `agentic_code`**, como integrador real.
2. **Leer qué está implementado en `agentic_code`** — la asimetría entre lo que el integrador necesita
   escribir y lo que el runtime le da es, ella misma, la medida del hueco.
3. **Conforme se activan más capacidades en `agentic_runtime`, implementar más capacidades en
   `agentic_code`** — los dos repos avanzan acoplados, y el integrador es la puerta.
4. **Validar la operación contra los `.jsonl`** de sesión que `agentic_code` deja: la traza real de
   mensajes, tool calls, anuncios y resultados. Es evidencia de EJECUCIÓN, no de lectura.

**Por qué los `.jsonl` mandan.** Una aserción sobre firma acredita en falso (`H-L4`); un `.jsonl` es
lo que el modelo REALMENTE recibió y lo que REALMENTE devolvió. Contra él se comprueba lo que ningún
test unitario alcanza: si el anuncio de diferidas converge, si el listado de skills llegó, si el
`system-reminder` se repite turno tras turno, si una tool anunciada era invocable.

**Lo que este método NO es.** No sustituye al contraste contra el canónico. Sigue vigente el encuadre
del usuario: *ante conducta divergente, contraste contra canónico > «arreglar» lo que no sabes si es
genuino* (`D-08`). `agentic_code` DETECTA; el canónico DICTA.

---

## 2 · Listado de problemas confirmados (orden de evidencia del usuario)

Producido por el usuario ejercitando `agentic_code` contra el runtime. **Este es el orden de ataque.**

| # | Problema | Clase | Estado |
|---|---|---|---|
| 1 | `run_shell` sin `cwd` | defecto de **CONTRATO** | ⛔ abierto — **el primero a pagar** |
| 2 | Fallback de `BashTool` (`TRAMO-1.md:183`) | conducta | ⛔ abierto |
| 3 | Remediación de `FIND-TS-1` / `TS-3` / `TS-4` | deuda ya declarada | ⛔ abierto |
| 4 | `GAP-TOOL4` | deuda ya declarada | ⛔ abierto |
| 5 | `GAP-PROMPT-1` — 15 de 25 descripciones sin homologar | superficie del modelo | ⛔ abierto |
| 6 | `FIND-E2G-2` | deuda ya declarada | ⛔ abierto |
| 7 | Abort de `WebFetch` no esperable | conducta | ⛔ abierto |
| 8 | `RuntimeFactory._modes` singleton (`factory.py:152`) | estructural | ⛔ abierto |
| 9 | Motor de permisos parcial | capacidad | ⛔ abierto |
| 10 | Stream público insuficiente para reproducir la observabilidad canónica | **observabilidad** | ⛔ abierto |

**Detalle del #5** — las 15 descripciones que no están homologadas contra el canónico:
`Agent` (16.6 KB en A), `TodoWrite` (9.5 KB), `EnterPlanMode` (7.7 KB), `Config`, `ExitPlanMode`,
los 6 `Task*`, los 2 `Worktree*`, `clone_repository`.

**Detalle del #10** — es el que engancha con el barrido: el runtime **no emite el plan de tools del
turno**. `TurnToolPlan` (`deferred_strategy.py:34-39`) es interno, no viaja al stream público, y lo
único observable es `app_state.capabilities['discovered_tools']`. Un integrador **no puede
reconstruir** cuántas tools se anunciaron, cuáles iban diferidas ni cuántas quedaron fuera por
presupuesto — todo lo cual A sí contabiliza y expone (`analyzeContext.ts`). Sin esto, el paso 4 del
método (validar por `.jsonl`) es ciego para media superficie de tools: **conviene pagarlo temprano
aunque esté el último de la lista**, porque es el instrumento de medida del propio método.

---

## 3 · Cosecha del barrido EOF (10ª ventana) — entra en la misma cola

Hallazgos del barrido del canónico sobre las LISTAS de tools (nativas, MCP diferidas, skills). No los
produjo `agentic_code`, pero son de la misma familia y se atacan con el mismo instrumento.

| ID | Hallazgo | Estado |
|---|---|---|
| `FIND-DEFER-1` | El delta de diferidas se reconstruye RE-PARSEANDO el texto rendido; un `\n` en el nombre anuncia una tool inexistente, pierde la real y **el delta no converge nunca** | ⛔ abierto |
| `FIND-DEFER-2` | Sin cap de descripción de terceros (60 000 ch medidos vs `MAX_MCP_DESCRIPTION_LENGTH = 2048` de A) | ⛔ abierto |
| `FIND-AGENT-LIST-1` | Al modelo no le llega **ningún listado de subagentes**; `AgentDefinition.description` es campo muerto y `AgentDefinitionResolver` **no tiene enumeración** | ⛔ abierto |
| `FIND-SKILL9/17` | Reclasificado: al modelo **no le llega ningún listado de skills**, por ninguna de las **dos** vías de A (description de `Skill` + attachment `skill_listing` incremental) | ⛔ abierto — **primero de la pata de skills** |
| `FIND-SKILL-20` | El frontmatter PISA la identidad de la skill (A: siempre el nombre del directorio) | ⛔ abierto |
| `FIND-SKILL-21` | Sin dimensión de fuente ni precedencia; `last-wins` donde A tiene `first-wins` por identidad de fichero real | ⛔ abierto |
| `FIND-POOL-1` | Sin predicado de enablement por tool (`Tool.isEnabled()`); el integrador ha de negar POR NOMBRE, mezclando política con disponibilidad | ⛔ abierto |

**Dos `H-L4` a saldar al pagar lo anterior** — suites que acreditan la divergencia en vez de
detectarla: `test_deferred_delta.py:43-47` (consagra el reparseo de texto como mecanismo homologado) y
`test_deferred_delta.py` entero (190 L, **cero casos adversariales**). Se **reescriben**, no se amplían.

**Orden 2 arrastrado** (hallazgos de ventanas previas, sin tocar): `FIND-READ-1`, `FIND-READ-2`,
`FIND-GLOB-1`, `FIND-CFG-1`, `FIND-LOOP-1`, `FIND-E11-1`, `FIND-C10-1`, `FIND-SEQ-1`, `FIND-E2G-1`,
`FIND-E2G-2`, `FIND-C6-2`.

---

## 4 · Bajo la línea, sin tocar

`A-CIERRE` P4″ 12–18 · ledger 39 abiertos · `O-18`/`R-1b` · `R-6`/`O-16` · `ID-4`/`K3` · `H-3`.
Diferidos nombrados: `SERPER_API_KEY` del entorno vs `ctx.git_credentials` · `ForkSnapshot` no
transporta el confinamiento · `run_argv` no traduce paths DENTRO del argv.
