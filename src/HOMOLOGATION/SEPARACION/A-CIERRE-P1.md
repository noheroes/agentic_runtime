# A-CIERRE · P1 — los 3 CORE-GAPs huérfanos, desarrollados (L05, 6 campos)

> **Qué es:** el desarrollo de `AC-05` (**H-3** `resume`), `AC-06` (**H-4** discovered-set) y `AC-07` (**H-5**
> drenaje de notificaciones background) — los tres CORE-GAPs que `DEUDA-A §0.1b/§2.8` emitió *sin* remediación
> desarrollada, y que por tanto bloquean el cierre de `00-BLUEPRINT §2.1` (hoy 🟨, 9/11 touchpoints).
>
> **Novedad de método (decisión del usuario, 2026-07-27):** cada ítem lleva, además de los 6 campos de L05, un
> **7º campo: ANCLA CANÓNICA** — `claude-code/src/…:L-R`. Motivo: el corpus tenía **1745 anclas de runtime y 0
> anclas canónicas**, luego toda afirmación de la forma *«esto refleja el canónico»* era **infalsificable**. P1 es
> el piloto de la regla. *Regla: una unidad sin ancla canónica no entra en Fase B.*

---

## 0. Declaración de lectura (L01/L03 — honestidad primero)

**Leído 1→EOF en este ciclo, evidencia PROPIA** (registrado en `EVIDENCIA.log` con su «PARA QUÉ»):

| archivo | L | lado |
|---|---|---|
| `~/.claude/skills/analisis-comparativo-ab/lecciones/*` (12 archivos) | 547 | método (PASO 0) |
| `SEPARACION/DEUDA-A.md` | 682 | doc |
| `agentic_runtime/…/execution/local/runtime.py` | 435 | runtime |
| `agentic_runtime/…/loop/agent_loop.py` | 352 | runtime |
| `agentic_runtime/…/execution/local/notification.py` | 73 | runtime |
| `agentic_runtime/…/tools/deferred.py` | 44 | runtime |
| `agentic_runtime/…/execution/fork/__init__.py` | 96 | runtime |
| `claude-code/src/tools/AgentTool/resumeAgent.ts` | 265 | **canónico** |

**NO leído íntegro, y por tanto NO se apoya ninguna afirmación de completitud en ello:**
- `claude-code/src/query.ts` (1729 L) — sólo se localizó por `grep` el punto de drenaje (`:1575-1577`, `:1631-1633`).
  **Consecuencia asumida:** la enumeración canónica de **AC-07** es de *mecanismo*, no de *completitud*; si el
  canónico drena o filtra en algún punto adicional de `query.ts`, este doc **no lo tiene**. → cabo `P1-c1`, hogar
  **P4-P7** (que bajo el nuevo reparto abren el canónico por categoría).
- `claude-code/src/utils/toolSearch.ts` (756 L) — leído `:545-575` (el cuerpo de `extractDiscoveredToolNames`).
  Suficiente para el mecanismo de **AC-06**; **no** para afirmar que sea el único productor del discovered-set.
  → cabo `P1-c2`, mismo hogar.
- `claude-code/src/utils/task/framework.ts` (308 L) y `tasks/LocalAgentTask/LocalAgentTask.tsx` (682 L) — **no
  abiertos**. → cabo `P1-c3`.

Los tres cabos son **de verificación**, no de trabajo: por L04 se listan como pendientes visibles, **no** se
pliegan dentro de «cabos con destino».

---

## AC-05 · `H-3` — `LocalAgentRuntime.resume` no existe

### Hecho verificado (1→EOF)
`execution/local/runtime.py` 1→EOF: la superficie pública es
`startup`(:118) · `shutdown`(:126) · `dispatch`(:134) · `stream`(:153) · `status`(:183) · `cancel`(:187) ·
`result`(:190). **No hay `resume`.** `00-INTEGRADORES §1.3` declara que el integrador consume
`resume(agent_id, message)` ⇒ el contrato publicado al integrador **nombra un método inexistente**.

### 🆕 ANCLA CANÓNICA — y por qué cambia el tamaño del ítem
`claude-code/src/tools/AgentTool/resumeAgent.ts:42-265` — `resumeAgentBackground`. **265 líneas, 14
comportamientos distintos.** La prosa de nuestro corpus lo comprimía a *«`resume(agent_id, message)`»*;
implementar desde esa prosa habría producido un método de ~10 líneas que **compila, corre y está mal**. Es el
caso testigo de por qué la regla del ancla canónica existe.

| # | comportamiento canónico | ancla | ¿el runtime lo tiene? |
|---|---|---|---|
| 1 | Carga **transcript + metadata** del agente, en paralelo, por `agentId` | `:63-66` | ❌ no hay lectura de transcript |
| 2 | **Falla duro** si no hay transcript | `:67-69` | ❌ |
| 3 | **3 filtros** sobre los mensajes recuperados: `filterUnresolvedToolUses` · `filterOrphanedThinkingOnlyMessages` · `filterWhitespaceOnlyAssistantMessages` | `:70-74` | ❌ **crítico** — sin el 1º, reanudar un transcript cortado a mitad de un `tool_use` manda al API un `tool_use` sin `tool_result` ⇒ **400** |
| 4 | Reconstruye el `contentReplacementState` del subagente | `:75-79` | ❌ (el runtime no tiene ese estado) |
| 5 | Revalida el **worktree** (si desapareció, cae al cwd del padre en vez de crashear en el `chdir`) | `:82-92` | ❌ |
| 6 | **Bump de `mtime`** del worktree para que el cleanup de worktrees rancios no borre uno recién reanudado | `:93-97` | ❌ (ni existe el cleanup) |
| 7 | **NO re-gatea permisos** — el spawn original ya pasó el check (decisión explícita, comentada) | `:99` | n/a — pero es **decisión de diseño a heredar**, no omisión |
| 8 | Resuelve el `AgentDefinition` desde `meta.agentType`, con fallback a `GENERAL_PURPOSE_AGENT` | `:100-112` | 🟡 el resolver existe (`runtime.py:342`) pero no hay `meta` que leer |
| 9 | Resume-de-fork: reconstruye el **system prompt del padre** (prefijo cache-idéntico) o falla | `:116-148` | ❌ |
| 10 | `permissionMode` = el del agente o `'acceptEdits'`; **re-ensambla el tool pool** | `:158-164` | ❌ |
| 11 | Prompt = **mensajes recuperados + el mensaje nuevo del usuario** | `:168-171` | ❌ |
| 12 | `forkContextMessages: undefined` — re-suministrarlo duplicaría `tool_use` IDs | `:187-189` | ❌ |
| 13 | **Salta** la escritura al name-registry (la entrada original persiste) | `:197` | ❌ |
| 14 | Marca la invocación como `invocationKind: 'resume'` | `:223` | ❌ |

### Los 6 campos (L05)

- **Comportamiento.** `resume(agent_id, message)` reabre un agente ya ejecutado: recupera su transcript
  persistido, lo **sanea** (los 3 filtros de `:70-74`), le concatena el mensaje nuevo como turno de usuario, y
  despacha un run que **continúa** la identidad anterior en vez de crear una nueva. Efecto observable: el segundo
  despacho ve la conversación del primero y conserva su `agent_id`.
- **Costura.** Ninguna nueva en el borde del integrador: `resume` es un **método más de la superficie
  `AgentRuntime`**, hermano de `dispatch`. Sí requiere una costura **interna** que hoy no existe: un
  **lector** de transcript (hoy `_persist:418-432` sólo escribe). Se declara `TranscriptReader` como la cara de
  lectura del mismo `StorageProtocol`, **no** un repo nuevo — la clave ya está fijada por
  `StorageKeys.transcript_key(user_id, session_id, agent_id)` (`runtime.py:428`).
- **Firma.**
  ```python
  async def resume(self, agent_id: str, message: str, *,
                   on_event: EventHandler | None = None) -> str: ...   # -> task_id
  ```
  más, en el módulo de saneo:
  ```python
  def sanitize_resumed_messages(messages: list[dict]) -> list[dict]: ...
  # = filter_unresolved_tool_uses ∘ filter_orphaned_thinking ∘ filter_whitespace_only_assistant
  ```
  `sanitize_resumed_messages` es **el sub-ítem que la prosa ocultaba** y es el único de los 14 que provoca un
  error duro del API si falta.
- **Cableado.** `execution/local/runtime.py` — método nuevo junto a `dispatch:134`; reutiliza `_run_loop:306`
  pasándole los mensajes recuperados. **Punto exacto de inyección:** `_build_child:198-218` debe aceptar un
  `resumed: ResumedAgent | None` y, cuando venga, **no** generar `agent_id` (`:205`) sino conservar el recibido —
  es la línea que hace que `resume` sea *resume* y no *dispatch con historia*.
- **Orden.** Tras **ID-2** (`SessionRepo` define la clave) e **ID-3** (scope de persistencia). **Y antes que
  AC-06**: el discovered-set es estado que hoy vive en el `ctx` y que un `resume` debe reconstruir (ver AC-06 ·
  §consecuencia). Depende además de **AC-h4** (abajo), sin el cual `resume` no tiene entrada que leer en el caso
  que más importa.
- **Prueba.** (a) despachar → dejar completar → `resume(agent_id, "sigue")` ⇒ el `ctx.messages` del 2º run
  **contiene** los del 1º y el `agent_id` es **el mismo** (hoy: `AttributeError`). (b) transcript cuyo último
  mensaje es un `tool_use` sin `tool_result` ⇒ tras `sanitize_resumed_messages` **no** queda ningún `tool_use`
  huérfano (hoy: no existe la función). (c) `resume` de un `agent_id` inexistente ⇒ error explícito, no un run
  vacío silencioso (espejo de `:67-69`).

### 🆕 AC-h4 (hallazgo nuevo de P1) — el transcript **no se escribe** en el caso que más importa
`_persist` se invoca en `runtime.py:416`, es decir **sólo en la ruta de éxito**. Las dos rutas de excepción
retornan antes: `except asyncio.CancelledError` hace `raise` en `:387`, y `except Exception` hace `return` en
`:394`. **Consecuencia observable: un agente que falla, se cancela o expira por watchdog NO deja transcript** —
y son exactamente los agentes que un usuario quiere reanudar. `resume` sobre ellos daría el error de `:67-69`
del canónico, correctamente, **por una razón equivocada**: no es que no exista, es que el runtime no lo guardó.
**Remediación:** mover la persistencia a un `finally` (o persistir incrementalmente, que es lo que
`15·CG-STOR-2` ya pide por otra razón — **convergen**). *Este hallazgo no estaba en ningún doc: sale de leer
`runtime.py` 1→EOF con la pregunta «¿de dónde lee `resume`?» — que sólo se formula al desarrollar el ítem.*

---

## AC-06 · `H-4` — el discovered-set ⚠ **la premisa de `DEUDA-A` es falsa**

### 🆕 AC-h6 (hallazgo nuevo de P1) — re-tipificación del ítem
`DEUDA-A §2.8·H-4` afirma: *«el touchpoint 8 (discovered-set MCP por `agent_id`, `09·E5`) sufre el **mismo**
`agent_id` inestable que la memoria … falta el segundo consumidor [de ID-5]»*. **Falso, verificado 1→EOF.**

`tools/deferred.py` (44 L, leído entero) **no lee `agent_id` en ninguna línea**. El estado vive en
`ctx.app_state.capabilities["discovered_tools"]` (`:14`, `:30-37`) — es estado **por contexto**, y la clave es
literal y única, sin componente de identidad.

**Origen del error, y es el de siempre:** `deferred.py:11-13` lleva un comentario que dice *«Estado de
descubrimiento **scopeado por agente** … lo materializamos como estado de capability por contexto
(**agent_id**)»*. `DEUDA-A` tomó esa frase por descripción del mecanismo. **RV-5 otra vez: un docstring no es
evidencia.** Con `ID-5` (`subagent_type`) no hay nada que cablear aquí porque **no hay nada keyado por
`agent_id`**.

⇒ **H-4 se retira como «segundo consumidor de ID-5»** y se re-emite como **dos gaps reales y distintos**:

### 🆕 ANCLA CANÓNICA
`claude-code/src/utils/toolSearch.ts:545-575` — `extractDiscoveredToolNames(messages)`. El canónico **NO
almacena** el discovered-set: lo **deriva del historial** en cada uso, recorriendo los bloques `tool_reference`
dentro de los `tool_result` (`:568-575`). Consumidores verificados por `grep`: `services/api/claude.ts:1158`
(decide qué schemas diferidos se envían), `services/tools/toolExecution.ts:590`, y tres sitios de compactación.

**Diferencia estructural (no cosmética):** *derivar* es idempotente y **sobrevive por construcción** a cualquier
transporte de la historia (resume, compactación, fork con herencia de mensajes). *Almacenar en `ctx`* no
sobrevive a nada de eso salvo que alguien lo transporte explícitamente — y el canónico, precisamente porque
deriva, sólo necesita un acarreo especial en **un** punto: el `compact_boundary`, que lleva
`preCompactDiscoveredTools` (`toolSearch.ts:553-559`) porque ahí la historia **se destruye**.

### Gap (a) — el estado no sobrevive al transporte de la historia
- **Comportamiento.** El conjunto de tools diferidas descubiertas debe estar disponible siempre que la historia
  que lo justifica esté presente. Hoy vive en `ctx.app_state.capabilities` y **el `ctx` muere con el run**.
- **Costura.** Dos opciones, y **la recomendación es la del canónico**: sustituir el almacén por una
  **derivación** `discovered_tool_names(ctx) -> set[str]` que recorra `ctx.messages`. Elimina el problema en vez
  de transportarlo, y hace innecesarios los acarreos de resume y de fork.
- **Firma.** `discovered_tool_names(ctx)` **conserva su firma actual** (los 2 call-sites de
  `deferred_strategy.py:60` y las marcas de `tool_search.py:67` / `skill_tool.py:63` no cambian); cambia sólo su
  implementación. `mark_tools_discovered` pasa a **escribir una marca en el mensaje de resultado**, no en
  `app_state`.
- **Cableado.** `tools/deferred.py:30-37` (el cuerpo) · sin cambios en `tools/deferred_strategy.py:60,67` ·
  sin cambios en `tools/native/tool_search.py:67` ni en `capabilities/skills/skill_tool.py:63`. **El coste real
  del cambio es 1 archivo.**
- **Orden.** Antes de **AC-05**: si `resume` aterriza primero sobre el almacén-en-`ctx`, hereda el defecto y hay
  que escribir un acarreo que la derivación vuelve innecesario. Converge con **K6** (compactación): derivando,
  K6 sólo necesita el equivalente de `preCompactDiscoveredTools`.
- **Prueba.** Reanudar (o forkear con `inherit_messages=True`) un agente que descubrió `X` ⇒
  `discovered_tool_names(ctx)` contiene `X` **sin** que nadie lo haya transportado (hoy: vacío).

### Gap (b) — la herencia por fork contradice al canónico
- **Comportamiento.** `ForkPolicy` trae `inherit_capabilities: bool = True` (`fork/__init__.py:27`) e
  `inherit_messages: bool = False` (`:24`), y `RuntimeContextForker.fork` copia la bolsa en `:78`
  (`dict(snap.capabilities)`). ⇒ **por defecto, el hijo hereda el discovered-set del padre sin heredar la
  historia que lo produjo.** El canónico, derivando de `messages`, le daría a ese hijo un conjunto **vacío**.
  Efecto observable: al subagente se le anuncian schemas de tools diferidas que **él nunca descubrió**.
- **Costura / firma / cableado.** Ninguna nueva: **el gap (a) lo cierra solo**. Derivando de `ctx.messages`, la
  herencia del discovered-set pasa a seguir automáticamente a `inherit_messages`, que es la semántica canónica.
  *Se registra como gap separado porque, si se eligiera la opción de «transportar el almacén» en vez de derivar,
  (b) **seguiría abierto** y habría que arreglarlo aparte.* Es el argumento decisivo a favor de derivar.
- **Orden / prueba.** Con (a). Test: fork con `inherit_messages=False` de un padre con `X` descubierta ⇒ el hijo
  **no** ve `X` anunciada (hoy: sí la ve).

**Saldo de AC-06:** el touchpoint 8 de `00-BLUEPRINT §2.1` **no se cierra cableando ID-5** (nada que cablear);
se cierra con el gap (a). El touchpoint queda **correctamente atribuido** por primera vez.

---

## AC-07 · `H-5` — el canal de notificaciones background no tiene drenador

### Hecho verificado (1→EOF + ensamblador)
- **Productor cableado ✅:** `runtime.py:294-304` (`_notify`) llama `put_notification`, invocado en las 3 rutas
  terminales (`:385` killed · `:392` failed · `:413` completed).
- **Consumidor: NO EXISTE.** `grep` de `drain_notifications|process_background_notification` sobre todo el
  runtime devuelve **sólo** re-exports (`__init__.py:12,37-39` · `execution/__init__.py:3,15-17`) y **tests**.
  Cero call-sites de producción.
- **Y el docstring miente:** `notification.py:5` afirma *«El loop padre drena el canal al inicio de cada turno,
  convierte las entradas en mensajes `<task-notification>` y aplica display_messages si corresponde»*. Ninguna
  de las tres cosas ocurre. **RV-5.**

### ⚠ Corrección de mi propia nota de P0 (AC-h3)
En P0 escribí que el seam recomendado **no** es `root_turn_start_hooks` porque *«dispara una vez por `run()`, no
por turno»*. **El hecho es cierto** (`agent_loop.py:176`, antes del bucle `for _turn in range(_MAX_TURNS)` de
`:185`) **pero la inferencia era floja**: en el runtime un `run()` = **un prompt de usuario**, y el canónico
drena por prompt de usuario, no por turno de modelo. La frecuencia **coincide**.

**La razón real por la que el seam no sirve es otra, y es más fuerte:** el hook está **sub-parametrizado**.
`_root_turn_start_hooks(task)` (`runtime.py:373`) recibe `task` y devuelve corrutinas **de cero argumentos**
(`agent_loop.py:160`, `Callable[[], Coroutine[Any, Any, None]]`). Con `task` el integrador **sí** puede drenar
(tiene `session_id`/`owner_id`), pero **no puede aplicar** lo drenado: `process_background_notification(session,
n)` necesita el `Session`, que se construye **dentro** de `_run_loop` (`runtime.py:331`) y **no se expone**; y
tampoco recibe el `ctx` para tocar `ctx.messages`. **La delegación al integrador es imposible, no incompleta.**

### 🆕 AC-h5 (hallazgo nuevo de P1) — `process_background_notification` **no puede funcionar** aunque se cablee
`notification.py:68` hace `session.messages.append({...})`. Pero `runtime.py:397`, al terminar el loop, hace
`session.messages = list(ctx.messages)` — **reasigna la lista entera**. El `Session` del runtime **no es el
historial vivo**: es un *sumidero de copia* que se rellena al final. ⇒ cualquier XML inyectado en
`session.messages` **se descarta silenciosamente** y jamás llega al modelo.

Es el peor perfil posible: función escrita, **exportada en la API pública**, con **7 tests que pasan** (los
tests construyen un `Session` de juguete y verifican el append, `tests/test_background_notification_channel.py:99-141`)
y **estructuralmente incapaz** de producir su efecto en el runtime real. Los tests verifican la función, no el
comportamiento. *Este es el patrón exacto que motivó todo el esfuerzo de homologación.*

### 🆕 ANCLA CANÓNICA
`claude-code/src/query.ts:1575-1577` — los subagentes **sólo** drenan las `task-notification` dirigidas a ellos:
`cmd.mode === 'task-notification' && cmd.agentId === currentAgentId`. Y `:1631-1633` — las notificaciones se
convierten en **attachments** junto con los `prompt`, es decir entran por el **mismo canal que el input de
usuario**, no por un canal aparte.
⚠ **Alcance declarado:** `query.ts` **no** se leyó 1→EOF (1729 L) ⇒ esto es el **mecanismo**, no la
**completitud** del drenaje canónico. Cabo `P1-c1`.

**Lo que el ancla aporta y nuestro doc no tenía:** el filtrado **por destinatario** (`cmd.agentId ===
currentAgentId`). El canal del runtime keya por `(user_id, session_id)` (`notification.py:22,37`) — **no por
agente** ⇒ en una sesión con dos agentes background, **cualquiera** de los dos drenaría las notificaciones del
otro. No es un gap que ningún doc registrara.

### Los 6 campos (L05)

- **Comportamiento.** Al empezar a procesar un prompt de usuario, el agente padre recoge las notificaciones de
  sus subagentes background terminados **dirigidas a él**, las convierte en mensajes `<task-notification>` en su
  historial y actualiza el `status` del `BackgroundTaskRef` correspondiente. Efecto observable: el padre **se
  entera** de que su subagente terminó y puede razonar sobre el resultado. Hoy no se entera nunca.
- **Costura.** Un paso propio del `AgentLoop`, **no** un hook del integrador — porque el comportamiento es
  genérico del runtime (lo dice el propio `notification.py:50`) y porque, como se demostró arriba, el hook no
  puede alcanzar el estado que necesita. Se sitúa en `run()` **entre** `_run_turn_start_hooks()` (`:176`) y el
  `append` del prompt (`:179`): el orden respecto a `_inject_recall` es **observable** (ambos escriben en
  `ctx.messages`) y el canónico mete las notificaciones **con el input de usuario** (`query.ts:1631-1633`) ⇒ van
  **antes** del prompt.
- **Firma.**
  ```python
  # el drenaje pasa a keyar por destinatario, no sólo por sesión
  def drain_notifications(user_id: str, session_id: str, agent_id: str) -> list[BackgroundNotification]: ...
  class BackgroundNotification:  # gana el destinatario
      parent_agent_id: str = ""
  # y la aplicación opera sobre el historial VIVO, no sobre el Session-sumidero
  def apply_notification(messages: list[dict], n: BackgroundNotification) -> None: ...
  ```
  `process_background_notification(session, n)` **se retira** (su firma es la causa de AC-h5). El
  `BackgroundTaskRef.status` se actualiza donde viva el registro de tasks, no dentro del inyector.
- **Cableado.** `loop/agent_loop.py` — paso nuevo en `run()` tras `:176`, alimentado por una dependencia
  inyectada en `__init__` (`notification_drain: Callable | None = None`) para no acoplar el loop al módulo
  `execution.local`. `execution/local/runtime.py:355-366` — pasarla al construir el `AgentLoop`.
  `execution/local/runtime.py:299-304` — `_notify` puebla `parent_agent_id`. **`root_turn_start_hooks` NO se
  toca**: sigue siendo un seam legítimo del integrador para otras cosas; simplemente deja de ser (falsamente)
  el hogar de esto.
- **Orden.** Independiente de AC-05 y AC-06. Depende de **K7** para ser *observable* de punta a punta (hoy todo
  spawn de subagente devuelve `ToolResult.error`, `DEUDA-A §1.1·K7` ⇒ nunca hay un background que notifique), pero
  **no** para implementarse ni para probarse.
- **Prueba.** (a) `put_notification` + un `run()` del padre ⇒ `ctx.messages` **contiene** el
  `<task-notification>` **antes** del prompt del usuario (hoy: no contiene nada). (b) dos agentes background en
  la misma `(user, session)` ⇒ cada padre drena **sólo** las suyas (hoy: imposible, no hay destinatario).
  (c) test de regresión de AC-h5: tras un `run()` completo, el mensaje inyectado **sigue** en `session.messages`
  (hoy fallaría por la reasignación de `runtime.py:397`).

---

## Saldo de P1

**Ítems del ledger cerrados:** AC-05 ✅ · AC-06 ✅ (re-tipificado) · AC-07 ✅ — los tres con los 6 campos de L05
**más** ancla canónica.

**Hallazgos nuevos (3):**
- **AC-h4** — `_persist` sólo corre en la ruta de éxito (`runtime.py:416` vs `:387`/`:394`) ⇒ los agentes
  fallidos/cancelados no dejan transcript ⇒ `resume` no tiene entrada justo donde más se necesita. Converge con
  `15·CG-STOR-2`.
- **AC-h5** — `process_background_notification` es **estructuralmente incapaz**: escribe en `session.messages`,
  que `runtime.py:397` reasigna. Exportada en la API pública, con 7 tests verdes.
- **AC-h6** — la premisa de `H-4` en `DEUDA-A §2.8` es **falsa** (`deferred.py` no lee `agent_id`); el error
  vino de creer un docstring. Re-emitido como dos gaps reales, ambos cerrados por **derivar** el discovered-set
  del historial como hace el canónico.

**Correcciones a trabajo propio (2):**
- Mi nota de **AC-h3/P0** sobre el seam de AC-07 tenía el hecho bien y la inferencia floja; la razón real es la
  **sub-parametrización** del hook, no su frecuencia. Corregido arriba y en `SEAMS §S21`.
- **`DEUDA-A §2.8·H-4`** queda corregido en su propio documento (regla `CAT-h10`).

**Pendientes de VERIFICACIÓN (L04 — bloqueadores visibles, no «cabos con destino»):**
- `P1-c1` — `query.ts` (1729 L) no leído 1→EOF ⇒ AC-07 tiene mecanismo canónico, no completitud. → **P4-P7**.
- `P1-c2` — `utils/toolSearch.ts` (756 L) leído sólo `:545-575` ⇒ AC-06 idem. → **P4-P7**.
- `P1-c3` — `utils/task/framework.ts` (308) y `LocalAgentTask.tsx` (682) **no abiertos** ⇒ el ciclo de vida
  canónico de la task background no está contrastado. → **P4-P7**.

**Efecto sobre `00-BLUEPRINT §2.1`:** los touchpoints 5 y 8 pasan a tener **cableado desarrollado**. El §2.1
**no** se marca ✅ todavía: el touchpoint 8 se cierra por un mecanismo distinto del que su fila declara, y esa
fila debe reescribirse (→ P8, consolidación de los `00-*`).
