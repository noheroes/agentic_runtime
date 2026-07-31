# PROGRESS — log de ejecución del TRAMO 1

> Ruta base: `/home/noheroes/python`. Vive en `agentic_runtime/src/HOMOLOGATION/SEPARACION/PROGRESS.md`.
> **Naturaleza: LOG (`D-09`).** Aquí sí se apila cronología. El ESTADO vive en `TRAMO-1.md` (el guion) y la
> evidencia detallada en `EVIDENCIA.log`; este archivo es el índice corto entre los dos.
>
> Lo abre la ventana de ejecución del 2026-07-30, que descubrió que el preámbulo de `TRAMO-1.md` dirigía el log
> aquí y que el archivo **no existía**.

## Tablero de capacidades

Ninguna capacidad se marca ✅ por existir: se marca por **correr** su prueba (`L09`). `E1..E9` son el gate del
tramo (`TRAMO-1 §4`); **6 de 9 escritas y en verde en una misma corrida** (`E1`, `E3`, `E4`, `E5`, `E6`, `E9`), así
que las capacidades que esas seis acreditan —y sólo ésas— llegan a ✅.

| cap | grado guion | estado | qué corre hoy |
|---|---|---|---|
| C1 contratos T1 | G2 | 🟢 **implementada y corrida** | `test_contracts_invariant.py` con violación inyectada (exit 1) · `mypy --strict` sobre `contracts/` |
| C2 model-caller + AbortSignal | G1 | ✅ **implementada y acreditada por `E1`+`E5`** | `S1` enriquecida y poblada, `stop: AbortSignal` en toda la cadena, `AbortController` concreto, `ModelsConfig` retirado; 2 violaciones inyectadas revertidas por `sha256` |
| C3 EventBus + `stream()` | G1 | ✅ **verificada** (no reconstruida, `L11`) | orden total exacto por las DOS vías de suscripción + handler que revienta sin cortar el canal; hallazgo del orden real escrito, no maquillado |
| C4 AgentLoop | G1 | ✅ **implementada y acreditada por `E4`** | `S11` pre-turno cableado, `LoopOutcome`/`LoopEndReason`, `max_turns` por tarea, `try:` de `_run_loop` abriendo en `_build_child` |
| C5 tools + pool + dispatcher | G1 | ⛔ sin empezar | |
| C6 exec-env + confinamiento | G2 | ⛔ sin empezar | |
| C7 façade + registry | G1 | ✅ **implementada y acreditada por `E3`** | doble camino cerrado: `set_registry`/`get_registry` retirados, `task_tools.py` lee `ctx.task_registry`; `S4` gana `join(task_id)` (enriquecimiento declarado) |
| C8 subagentes DI + drenador | G1 | ✅ **implementada y acreditada por `E3`+`E9`** | `FIND-EXEC1` pagado (runner por factory inyectada → `ctx.runner`, global retirado) · `H-5` pagado (`apply_notification` sobre el historial vivo, drenaje como paso propio del loop y sólo en la raíz) |
| C9 hilo de identidad | G3 (excepción) | ✅ **rip hecho y acreditado por `E6`** (promovida G3→G1) | turno real sin `user_id` + probe en `S1` + negativa + guardia de grafía `AC-39` |
| C10 ensamblador único | G1 | ⛔ sin empezar | pero `create_runtime` ya puebla `S18`/`S21`; lo que falta es su propia ficha y `E8` |

**Gate `E1..E9`: 6 de 9 escritas (`E1`·`E3`·`E4`·`E5`·`E6`·`E9`), 12 tests, verdes en una sola corrida. Faltan
`E2`·`E7`·`E8`.**

## Cronología

### 2026-07-30 · C1 — contratos T1 invariantes
Paquete `contracts/` (13 módulos) + shims de re-export. Prueba load-bearing con violación inyectada.
`GAP-02` pagado en su mitad de contrato (`PermissionContext.mode`, default `default`). Corrigió la forma
publicada de `K4` (`kw_only=True`, porque el bus es primitiva de extensión). Detalle en `EVIDENCIA.log`.

### 2026-07-30/31 · C9 — hilo de identidad (parcial)
**Hecho y corriendo:** `user_id` **erradicado** del runtime; `Scope` opaco como único cable de persistencia;
`session_id` obligatorio con `RuntimeIdentityError`; `ID-5` cableado (`subagent_type` llega al ctx y a la clave
de memoria); `ID-3` cerrado en sus tres repos (mcp/skills/transcript) con `StorageKeys` tipado a `Scope`;
`S20`/`ID-2` inyectable por DI (`RuntimeConfig.session_repo`, opcional). `D-11` registrado.

**No hecho, y no disimulado:** `E6` (la E2E que promueve C9) sin escribir · `ID-6`/`ID-7` (identidad en los
seams de salida y hacia el proveedor de modelo) diferidos a C2, que es donde vive ese seam · `H-4`
(discovered-set comparte el `agent_id` inestable) pendiente, va con C5 · `ID-4`/`K3` guard-path **encima de la
línea de corte** por decisión del guion · `H-3` (`resume`) fuera del tramo, unidad nombrada.

### 2026-07-31 · `E6` — la E2E que promueve C9, escrita y corriendo
Tres tests reales (`test_tramo1_gate.py`): turno completo **sin `user_id`** contra Azure con `ModelSeamProbe`
decorando el caller real (nada de identidad llega a `S1`: ni mensajes, ni tools, ni system prompt) · la
**NEGATIVA** (sin identidad atribuida no hay turno ni escritura de sesión) · la **guardia de grafía**
`AC-39`/`D-11` (`extra="forbid"` hace reventar la grafía vieja en vez de descartarla en silencio). C9 pasa de
G3 a G1. **Límite declarado:** la negativa asevera `status != COMPLETED` y no `== FAILED` porque
`runtime.py:358` llama a `_build_child` **fuera** del `try:` → la excepción se va a la `asyncio.Task` y el
registry queda `RUNNING`. Defecto real del base, encontrado por la prueba, **no pagado**: toca C7.

### 2026-07-31 · C2 — `S1` enriquecida + `S2` `AbortSignal`, con el defecto `protocol.py:17,33` pagado
`AbortController` concreto (el Protocol existía **sin implementación**: por eso `ctx.stop` no se armaba nunca)
· `stop: asyncio.Event → AbortSignal` en toda la cadena, retipado que **rompió 25 tests de golpe** — la prueba
de que es load-bearing · ctx raíz armable · firma `S1` enriquecida **y poblada** por `RuntimeConfig.model_options`
· `ModelsConfig` (`LAT-MODELS1`) retirado tras verificar cero consumidores. Acreditado por `E1` (dos
observatorios: el seam **y** el cable `on_payload`) y `E5` (abort en vivo al 3er token de un stream real), más
dos violaciones inyectadas revertidas byte a byte por `sha256`. **Dos límites medidos en la wheel, no supuestos:**
`tool_choice`/`output_format` no existen en `agentic_models 0.2.0` → el puente **levanta** en vez de tragárselos;
sólo el provider `anthropic` mira `signal.aborted` dentro del SSE → el corte a mitad es **del runtime**.
**Diferidos nombrados:** propagación padre→hijo del controller vivo · `Usage` (cache/coste, `thinking_tokens=0`)
· puente bus↔`ctx.stop` (`08·signals`, sobre la línea). Detalle en `EVIDENCIA.log:263-264`.

**Deuda de lint/tipos del tramo, RE-MEDIDA el 2026-07-31 tras C2 (consecuencia 44):** `mypy --strict` =
**139 errores / 55 ficheros** (sin cambio) · `ruff` = **492** (baja desde 495; sólo se normalizaron los ficheros
propios, sin barrido del árbol) · `uv run pytest` = **673 passed, 3 skipped, 117 xfailed, 0 failed** · gate
`-m gate_tramo1` = **6 passed, 0 skipped en una sola corrida**. **Intermitencia, dicha tal cual:**
`test_runtime_e2e_real.py::test_real_sequential_dependent_tools` falló una vez en corrida completa, pasó
aislada y pasó en la re-corrida ⇒ el verde simultáneo se apoya en la segunda corrida.

**Deuda de lint/tipos del tramo (no de C9), MEDIDA en la ventana del 2026-07-30/31 (consecuencia 44, ninguna cifra heredada):**
`uv run mypy --strict src/agentic_runtime/` = **139 errores en 55 ficheros** (la memoria decía 153: la medición
manda) · `uvx ruff check src/agentic_runtime/` = **495 errores, 385 auto-fixables** (decía 498). Son parte del
gate de cierre del tramo, no de una capacidad suelta. Lo que sí está limpio hoy: `uv run mypy` (config del
proyecto) = **Success, 129 ficheros** · `uv run mypy --strict src/agentic_runtime/contracts/` = **Success, 14
ficheros** · `uvx ruff check src/agentic_runtime/contracts/` = **All checks passed** · `uv run pytest` =
**663 passed, 3 skipped, 118 xfailed, 0 failed**.

---

## 2026-07-31 · ventana 3ª del tramo — `C4` + `E4` + `C3` + el defecto de `E6` pagado

**Hecho:** `C4` implementada (`S11` cableado pre-turno · `S27` deps-DI por constructor · `LoopOutcome`/
reason-codes · `max_turns` efectivo por constructor y por tarea), `E4` —la negativa obligatoria del gate—
escrita y corriendo en 4 piezas, `C3` verificada (no reconstruida), y **pagado** el defecto que `E6` encontró
en `runtime.py:358` (el `try:` abre ahora en `_build_child` ⇒ `FAILED` registrado, no `RUNNING` eterno).

**Gate: 10 passed, 0 skipped en una sola corrida** (`E1`×2 · `E4`×4 · `E5`×1 · `E6`×3) = **4 de 9**.
Faltan `E2`·`E3`·`E7`·`E8`·`E9`. Deuda re-medida (nada heredado): `mypy --strict` **139/55** ·
`ruff` **500** · suite **685 passed / 3 skipped / 114 xfailed / 0 failed**.

**Lo que la ventana ENCONTRÓ, dicho antes que lo que hizo:**
1. **`FIND-EXEC1` medido:** `create_runtime` **nunca llama `set_runner`** ⇒ hoy, en producción, **todo** spawn de
   subagente devuelve `is_error`. `E4` lo asevera en vez de narrarlo. Es de `C8` y **bloquea `E3`**.
2. **La ficha de `C3` no describe su propio canal:** no existen `InitEvent`/`ResultEvent` y `Done` precede a los
   `ToolResultEvent` del turno. «Los 3 runners» no está definido en el corpus (aparece una vez, `TRAMO-1.md:82`);
   se interpreta como los 3 **emisores** y la interpretación se declara en el test.
3. **La firma de `S11` del borrador `SEAMS` era incorrecta**, resuelto por `D-08` leyendo el canónico 1→EOF:
   resultado único con booleano, no unión. Divergencia **registrada** en `SEAMS.md §S11`, no silenciada.
4. **Intermitencia diagnosticada** (`test_real_sequential_dependent_tools`, 1 de 6): el modelo emite a veces las dos
   tool calls en el mismo turno con un placeholder `__PENDING__`. **No es defecto del runtime.** El test aseveraba
   `s2.calls[0]`; ahora asevera la dependencia real. 8/8 verdes después — **no** se declara eliminada.

**INCIDENTE DE MÉTODO (ventana anterior), dicho entero:** se usó `git checkout <file>` para revertir una violación
inyectada. Todo el trabajo del tramo está **sin commitear** (HEAD = `cce603f`), así que eso destruyó trabajo de
`C2`/`C9` en `agent_loop.py` y `runtime.py`. Recuperados byte a byte desde el JSONL de la sesión y confirmados por
la suite volviendo a su cifra exacta. **Regla permanente: en este repo no se usa `git checkout`;** el revert de una
violación es restauración desde copia propia verificada por `sha256` (`D-09`).

**Commit de control `141cbb8`** en rama `fase-b/tramo-1` (139 ficheros, +23 087/−696): cierra la exposición.
De aquí en adelante cada término cierra con commit de control **antes** del enunciado de retoma.

## 2026-07-31 · ventana 4ª del tramo — `C8` + `C7`: `FIND-EXEC1` y `H-5` pagados, `E3` y `E9` escritas

**Qué se hizo.** `C8`: el runner de subagentes pasa de singleton global a **DI por factory**
(`RuntimeConfig.subagent_runner_factory` → `LocalAgentRuntime(runner_factory=…)` → `ctx.runner`); `set_runner`/
`get_runner` **retirados**; `SubagentSpec` sustituye a `ForkContext` en `S18` (lleva `parent_snapshot`, divergencia
declarada); `S4` gana `join(task_id)` porque un spawn en foreground es el padre bloqueando en el hijo y sin él la
única forma de esperar era romper la costura por dentro. `H-5`: nuevo `contracts/notifications.py` con
`NotificationSink` + **`apply_notification(messages, n)`** sobre el historial vivo;
`process_background_notification` retirada; el drenaje es un **paso propio del `AgentLoop`**. `C7`: `_registry`/
`set_registry`/`get_registry` retirados, `task_tools.py` lee `ctx.task_registry`.

**Defecto encontrado y pagado en la misma ventana.** El fork hereda `session_id` **y** `scope`, luego la clave del
canal es la misma para padre e hijo: con el drenaje incondicional un subagente se comía la notificación de su
hermano. `_drain_notifications` drena **sólo en la raíz**.

**La pieza 3 de `E4` murió como estaba anunciado** y está reescrita al revés: hoy asevera que el ensamblador SÍ
puebla `S18` **y que la costura llega al `ctx`** (testigo `S11` dentro del turno, no `hasattr`).

**Acreditación por violación inyectada** (anunciada antes de tocar el fuente; revert desde copia propia verificado
con `sha256 -c`, nunca `git checkout`): `V5` quitar `ctx.runner = self._runner` → rojas **`E3`** y la pieza 3 de
`E4`, verde `E9` (que usa el runner por la façade) — discrimina el threading del ensamblado; `V6` anular el drenaje
→ roja **`E9`** y **sólo** `E9`.

**Gate: 12 passed, 0 skipped en una sola corrida** (`E1`×2 · `E3`×1 · `E4`×4 · `E5`×1 · `E6`×3 · `E9`×1) = **6 de 9**.
Faltan `E2`·`E7`·`E8`. Deuda re-medida, nada heredado: suite **688 passed / 3 skipped / 112 xfailed / 0 failed** ·
`mypy --strict` **139 err / 55 f** (idéntico al baseline: `C7`/`C8` no añaden deuda de tipos) · `ruff` **500**
(idéntico).

**Intermitencia reportada, no escondida:** `test_runtime_e2e_real.py::test_real_sequential_dependent_tools` (ajeno
a `C7`/`C8`, no-determinismo del modelo ya diagnosticado el 2026-07-31) falló en 2 de 4 corridas completas de esta
ventana y pasó aislado y en las otras 2 completas. El verde simultáneo se apoya en las corridas 3ª y 4ª, dicho tal
cual.
