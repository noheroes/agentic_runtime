# 11 · capabilities/mcp — SEPARACION (Filosofía B)

> Ruta base `/home/noheroes/python`. Legend normativa `00-LEGEND.md` (+ `PLAN.md §3`). Marco: memoria
> **architecture-layers** (base framework + batteries · agnosticismo de identidad · invarianza T1/T2/T3 ·
> canónico = referencia de COMPLETITUD, no de FORMA). Tracker de partida (hipótesis, L11): `../11-cap-mcp.md`
> (**798 L**, 2ª vuelta gate-11; **24 FIND-MCP + 3 GAP-MCP = 27 vinculantes** enumerados uno a uno en §1.A + §3.1,
> + LAT-MCP1; §Plan `McR1..McR19` **sin `McR14`** ⇒ **18 pasos reales**).
>
> **Recuento por estado: NO ADJUDICABLE en el tracker, resuelto por enumeración aquí** (`A-CIERRE·P4″ §16.5·c26`,
> consecuencia 45). El tracker trae **dos `§Recuento` mutuamente contradictorios** (`:254-261` y `:611`) y **las
> cinco cifras marcadas `~`** en ambos; este archivo llegó a **copiarlos, y además desdoblados**
> (`✅~11·🟡~6/8·🔀~4/5·❌~14/18·⛔~9`). Un `~` no es una cifra aproximada: es la constancia de que **nadie contó**.
> Se retira la cabecera aproximada; **el estado vigente es la enumeración nominal de §1.A/§1.B/§1.C/§2.4**, cuyo
> total cuadrado está en §3.1 (**71** desde el 2026-07-30: la lectura del canónico por excepción añadió `MCP-NA-10`). Ninguna cifra de este documento vuelve a llevar `~`.
> **Cableado RE-ABIERTO 1→EOF ESTE ciclo** (Q3 L09/L11, NO heredado del gate-11): los 12 `capabilities/mcp/*.py`
> + ENSAMBLADOR `factory.py`267 · `manager.py`112 · `agent_loop.py`353 · `execution/local/runtime.py`435 ·
> `execution/fork/__init__.py`96 · `tools/dispatcher.py`85 · `tools/deferred.py`44 · `tools/native_registry.py`42.

---

## 0. Tesis de separación (Filosofía B)

**Tesis 3 capas (idéntica a 12·skills / 13·memory / 11 dentro del patrón `CapabilityProvider`):**

1. **base = MECANISMO de activación + T1-CONTRATOS.** El `CapabilityProvider` (seam T2-BASE compartido con
   skills/mcp/plan/memory, home 12) + su **consumo per-turno en el loop** = el mecanismo. Verificado por lectura
   del ENSAMBLADOR ESTE ciclo: `factory._build_capability_manager` (132-175) crea **una** instancia de
   `CapabilityManager` (194) que `LocalAgentRuntime` pasa al `AgentLoop` **de root Y de subagentes** (runtime.py:358,
   MISMA instancia) → dentro de `for _turn in range(_MAX_TURNS)` (agent_loop.py:185) cada turno
   `ctx.tool_pool = self._build_tool_pool(ctx)` (195) → `manager.build_tool_pool` (manager.py:61) →
   `manager.tools` (50-59) → `McpProvider.tools()` (provider.py:307-316) **re-lee `McpState.all_tools()` cada
   turno**. ⇒ **hot-plug per-turno** (un server que conecta/desconecta entre turnos cambia el pool en el
   siguiente). `NativeToolRegistry` **NO está en la ruta** (grep 0 prod; corroborado leyendo `factory` 1→EOF: no
   aparece). Los **T1-CONTRATOS** que MCP exige del ecosistema (naming FQ + `mcp_info`, `is_mcp`/`always_load`,
   annotations→hints en `ToolProtocol`; `new_messages`/`structured` en `ToolResult`) son invariantes que enchufan
   AMBOS integradores → **paquete de contratos** (01/09), no propios de MCP.
2. **BATTERY `battery_mcp` = la capacidad MCP concreta, OPCIONAL.** Los 12 `mcp/*.py`
   (client/provider/config/config_store/scope/auth/token_storage/state/reconcile/tool_adapter/resource_tools) son
   **un paquete estándar componible** derivado del canónico: una forma concreta de traer tools externas por el
   protocolo MCP. Su **incompletitud** frente al canónico (needs-auth, transform de content, ciclo de vida robusto,
   políticas, list_changed, dedup, env-expansion, headersHelper…) = **CORE-GAPs de la battery**, NO gaps del base
   (L10 anti-padding). AMBOS integradores la componen o la sustituyen; nunca la sobreescriben. Sub-bridge
   `battery_mcp_skills` (con 12).
3. **integrador = identidad/scope + política + interfaz.** El **user-scoping** de tokens OAuth (hoy roto,
   `user_id="mcp"` fijo), la **política allow/deny** + **aprobación de proyecto** (product policy, borde de
   seguridad), los **handlers OAuth interactivos** (browser/callback), el **watcher** y los **producers por scope**
   de config, el **trust-gate** del headersHelper, el **hook de elicitation**, y la **capa de interfaz** (flujo
   OAuth interactivo, UI de servers) — todo T3/CLI-ONLY, entra por costuras.

**§0.1 nota-identidad load-bearing (cierra/unifica cabo 15·CG-STOR-1 — bug multi-user CONFIRMADO por el ENSAMBLADOR).**
El `StorageBackedTokenStorage` keyea `base = f"{user_id}/mcp/{server_name}"` (`token_storage.py:24`) con default
`user_id="mcp"` (`provider.py:50/87`). Leyendo `factory._build_capability_manager` 1→EOF: pasa `storage=storage`
(152) **pero NUNCA `user_id=`** → el provider queda en el default `"mcp"`. Y el runtime **SÍ tiene** el `user_id`
real (`ctx.user_id`, usado para el transcript en `runtime.py:424`), pero **está desconectado** del provider MCP.
⇒ los tokens OAuth de todos los usuarios colisionan en `mcp/mcp/<srv>` (multi-user leak). Eje **persistencia**;
patrón **id-opaco + repo**: el token-store se scopea por el `.id` de usuario que el integrador atribuye, jamás por
un literal. **UNIFICADO con 15·CG-STOR-1/CG-STOR-3** (guard-path/scope/sanitize) → `CG-MCP-16`.

**§0.2 asimetría con 13·memory (verificada por cableado + CONTRATO, como 12).** `McpProvider` implementa `tools()`
(viva, per-turno) + `catalog()` no-vacío (318-327) PERO `active_context()`/`compact_context()` devuelven `[]`
(332-336) y **NO** implementa `system_prompt_section`. Verificado abriendo `capabilities/contracts.py` 1→EOF ESTE
ciclo: `system_prompt_section` es **hook OPCIONAL** (52-58: fuera del `CapabilityProvider` Protocol estructural
63-69, invocado por `manager.system_prompt_sections:90` vía `getattr` tolerante). ⇒ hoy MCP **no surface las
server-instructions** al modelo (cara B de FIND-MCP12): el mecanismo base (`system_prompt_section` per-turno, ya
vivo para memory) existe; la battery debe poblarlo. `compact_context=[]` = cara del **motor-de-compactación NO
portado** (01/02), transversal a todos los providers, **NO** B-orphan (L10, idéntico a 13·D8).

---

## 1. Tabla por finding

Leyenda TIER: `T1-CONTRATO`/`T1-MOTOR`/`T2-BASE`/`T2-COSTURA`/`BATTERY`/`T3-INTEGRADOR`/`CLI-ONLY`/`DEUDA-B`.
CORE-GAPs agrupados keystone-first en `CG-MCP-1..20` (§2.3). "núcleo|cáscara" abreviado n/c.

### A · CORE-GAPs (findings ❌/🟡/🔀-real que `battery_mcp`+contratos DEBEN cerrar) → CG-MCP-*

| ID | resumen | n\|c | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| FIND-MCP1 | naming `mcp__srv__tool` + normalización + `mcp_info` ausentes (nombre crudo `tool_adapter:43/99`) | núcleo | T1-CONTRATO | `tools/protocol.py` (`mcp_info`, name FQ) + battery_mcp lo construye | — | CG-MCP-1 |
| GAP-MCP2 | `ToolProtocol` sin `mcp_info`/`is_mcp`/`always_load` (superficie mínima para gate FQ + swap) | núcleo | T1-CONTRATO | `tools/protocol.py` | — | CG-MCP-1 (alias FIND-MCP1) |
| FIND-MCP2 | `is_mcp`/`always_load` ausentes; `deferred=True` a mano (`tool_adapter:30`, `deferred.py:27`) | núcleo | T1-CONTRATO | `tools/protocol.py`+`tools/deferred.py` (precedencia) | — | CG-MCP-2 (cierra 09·GAP-TOOL3) |
| GAP-MCP1 | precedencia `is_deferred_tool` con `always_load`/`is_mcp` | núcleo | T1-CONTRATO | `tools/deferred.py` | — | CG-MCP-2 (alias FIND-MCP2) |
| FIND-MCP3 | annotations parciales (solo `readOnlyHint`→bg; falta destructive/openWorld/concurrency/title) | núcleo | T1-CONTRATO | `tools/protocol.py` + battery mapea | — | CG-MCP-3 (`is_concurrency_safe`→09) |
| FIND-MCP5 | transform content pobre (image/audio/blob/resource → `str()` `client.py:55`) | núcleo | T1-CONTRATO+BATTERY | `ToolResult.new_messages` (B-new_messages,01) + battery transform | — | CG-MCP-4 |
| GAP-MCP3 | `ToolResult` sin canal tipado image/attachment (B-new_messages) | núcleo | T1-CONTRATO | contrato `ToolResult` (01) | — | CG-MCP-4 (alias FIND-MCP5) |
| FIND-MCP6 | solo `content` array; sin `structuredContent`/`toolResult`/schema/`mcpMeta` | núcleo | T1-CONTRATO+BATTERY | `ToolResult.structured` (B-structured-output,01) + battery | — | CG-MCP-5 (=09·A25) |
| FIND-MCP7 | large-output sin persistir/truncar/capar | núcleo | BATTERY | `battery_mcp` client (reusa persist 10) | — | CG-MCP-6 |
| FIND-MCP4 | needs-auth + pseudo-tool `authenticate` + swap-por-prefijo + caché 15min ausentes | núcleo | BATTERY | `battery_mcp` (state/provider/auth-tool) | persist (needs-auth cache) | CG-MCP-7 (decide cabo c) |
| FIND-MCP9 | sin reconexión/recuperación-de-sesión/onclose-invalidation/retry/backoff | núcleo | BATTERY | `battery_mcp` client (onclose handlers + ReconnectScheduler) | — | CG-MCP-8 |
| FIND-MCP10 | sin timeout de conexión (`connect` sin `wait_for`) | núcleo | BATTERY | `battery_mcp` client | — | CG-MCP-8 |
| FIND-MCP11 | startup secuencial (`provider.py:241-245`) vs batched-paralelo (batch 3/20) | núcleo | BATTERY | `battery_mcp` provider (gather+semaphore) | — | CG-MCP-8 |
| FIND-MCP12 | capabilities/serverInfo/instructions no capturados; `list_*` incondicional | núcleo | BATTERY+T2-BASE | `battery_mcp` client (captura) + `McpProvider.system_prompt_section` (seam base vivo) | — | CG-MCP-8 |
| FIND-MCP8 | timeout tool-call 30s vs ~∞ (`dispatcher:68/76-79` SÍ aplica el 30s) + sin progreso | núcleo | BATTERY | `battery_mcp` tool_adapter (call-timeout ≠ connect-timeout) | — | CG-MCP-9 |
| FIND-MCP13 | sin env-var expansion `${VAR}`/`${VAR:-def}` | núcleo | BATTERY | `battery_mcp` config parse | — | CG-MCP-10 |
| FIND-MCP14 | sin política allow/deny (name/command/url, wildcards) | núcleo | T2-COSTURA+T3 | `McpPolicy` seam (battery enforce, integrador provee) | — | CG-MCP-11 (borde seguridad) |
| FIND-MCP15 | sin aprobación de servers de proyecto (approved/rejected/pending) | núcleo | T2-COSTURA+T3 | `McpApprovalGate` seam (battery consulta, integrador decide) | scope/trust | CG-MCP-11 (borde seguridad) |
| FIND-MCP21 | sin handlers `*_list_changed` → no refetch en vivo | núcleo | BATTERY | `battery_mcp` client (notification handlers, gated caps) | — | CG-MCP-12 |
| FIND-MCP22 | sin dedup por firma de config (dos servers al mismo proceso/URL → doble conexión) | núcleo | BATTERY | `battery_mcp` config/scope (`server_signature`) | — | CG-MCP-13 |
| FIND-MCP23 | reconcile sobre-agresivo (`reconcile.py:61-63` desconecta CUALQUIER ausente) | núcleo | BATTERY | `battery_mcp` reconcile (scope-guard `dynamic`) | — | CG-MCP-14 (🔀-real→gap) |
| FIND-MCP24 | sin `headersHelper` (script headers dinámicos + gate de trust) | núcleo | BATTERY+T2-COSTURA | `battery_mcp` client (reusa `exec_env` 09) + trust-gate integrador | trust | CG-MCP-15 |
| FIND-MCP20 | credenciales sin keying por config-hash + sin revoke (RFC7009) | núcleo | BATTERY+T3 | `battery_mcp` token_storage (hash) + revoke + **user-scope** | persist (token key) | CG-MCP-16 (unifica 15·CG-STOR-1) |
| FIND-MCP17 | resource tools: server opcional, sin blob-persist, output `{resources:[]}`, no-deferred | núcleo | BATTERY | `battery_mcp` resource_tools (+ B-new_messages para blob) | — | CG-MCP-17 |
| FIND-MCP18 | sin elicitation/roots/URL-elicitation-retry (-32042) | núcleo | BATTERY+T2-COSTURA | `battery_mcp` (capability roots→cwd) + `elicitation-hook` integrador | — | CG-MCP-18 (interactivo=⛔) |
| FIND-MCP16 | sin prompts→commands (`mcp__srv__prompt`) ni MCP-skills (`skill://`) | núcleo | BATTERY | `battery_mcp` (fetch prompts) + bridge `battery_mcp_skills` (12) | — | CG-MCP-19 (=12·CG-SKILL-15) |
| FIND-MCP19 | cleanup sin agent_id/abort-scope + stdio sin escalación de señales | núcleo | T2-COSTURA | `battery_mcp` `cleanup_for_agent` + wiring 05·ExR6/08·CG-SIG-8 | ejecución (teardown/agente) | CG-MCP-20 (=05/08) |
| **S25·mcp_servers** | `AgentDefinition.mcp_servers` per-agente ausente (canónico **`runAgent.ts:95-218 initializeAgentMcpServers`**; `extractAgentMcpServers` es la ruta de PANTALLA y descarta las referencias por string, ver el recuadro de `CG-MCP-21`); el subagente hereda el pool del padre y **no puede añadir los suyos** | núcleo | T2-COSTURA+BATTERY | `AgentDefinition` (shape→05) + `battery_mcp` resolución + filtro FQ del pool | ejecución (per-agente) | **CG-MCP-21** |

> **Nota de origen (honestidad de procedencia).** La fila `S25·mcp_servers` **no proviene del tracker `11-cap-mcp.md`**
> — no hay `FIND-MCP*` que la cubra: es una **DR-2** (ausencia de origen) detectada por el cruce con `SEAMS §S25:438`
> en `A-CIERRE·P4″ §16.4·I3`. Se incorpora aquí porque `S25` la delega **a 11 por nombre** y ningún otro par la
> reclama. Su re-verificación contra el canónico corresponde a **P6″**.

### B · Capacidades homologadas (✅/✅🔀/🔀 sin ID en el tracker — colocadas, "sin colocar=0")

| ID | resumen | n\|c | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| MCP-OK-1 | transportes stdio/http/sse (+inferencia retro) `config.py:90-95` | núcleo | BATTERY | `battery_mcp` config | — | homologado ✅ |
| MCP-OK-2 | validación estricta identidad+auth (bearer→token; auth HTTP⊄stdio) `config.py:54-88` | núcleo | BATTERY | `battery_mcp` config (borde seg, +estricto que A) | — | ✅🔀 valor propio |
| MCP-OK-3 | `enabled` per-config (no-conecta/no-tools) `provider.py:242-245` | núcleo | BATTERY | `battery_mcp` | — | 🔀 (≡ `isMcpServerDisabled`) |
| MCP-OK-4 | `ssl_verify` toggle TLS `client.py:114/127` | núcleo | BATTERY | `battery_mcp` config | — | ✅🔀 valor propio |
| MCP-OK-5 | 7 scopes `McpScope` `scope.py:25-34` | núcleo | BATTERY | `battery_mcp` scope | — | ✅ |
| MCP-OK-6 | precedencia enterprise>local>project>user `scope.py:38-46` | núcleo | BATTERY | `battery_mcp` scope | — | ✅ |
| MCP-OK-7 | exclusividad enterprise (lockdown) `scope.py:51/84-89` | núcleo | BATTERY | `battery_mcp` scope | — | ✅ |
| MCP-OK-8 | gate de mutabilidad user/project/local `scope.py:54/69-75` | núcleo | BATTERY | `battery_mcp` scope | — | ✅ |
| MCP-OK-9 | merge por nombre scope-aware `scope.py:78-94` | núcleo | BATTERY | `battery_mcp` scope | — | ✅ valor propio |
| MCP-OK-10 | traversal project abstraído al productor del scope | núcleo | T2-COSTURA | `McpConfigStore` producer | — | 🔀 (integrador decide) |
| MCP-OK-11 | persist add/remove/toggle scope-aware `provider.py:186-224/283-293` | núcleo | BATTERY+T2-COSTURA | `battery_mcp` + `ScopedMcpConfigStore` | — | ✅ |
| MCP-OK-12 | conexión por transporte vía SDK `client.py:83-143` | núcleo | BATTERY | `battery_mcp` client | — | ✅ |
| MCP-OK-13 | aislamiento por ítem (server caído no tumba resto) `provider.py:155-162` | núcleo | BATTERY | `battery_mcp` provider | — | ✅ |
| MCP-OK-14 | reconnect/disconnect/remove server `provider.py:172-224` | núcleo | BATTERY | `battery_mcp` provider | — | ✅ |
| MCP-OK-15 | motor reconcile deseado-vs-vivo (datos puros) `reconcile.py` | núcleo | BATTERY | `battery_mcp` reconcile | — | ✅🔀 valor propio (scope-guard→CG-MCP-14) |
| MCP-OK-16 | estrategias de auth registrables none/bearer/oauth `auth.py:45-48/111-113` | núcleo | T2-COSTURA | `register_auth_strategy` extension seam | — | ✅🔀 valor propio |
| MCP-OK-17 | OAuth 2.1 completo vía SDK `mcp` `auth.py:78-108` | núcleo | BATTERY+T2-COSTURA | `battery_mcp` (+AuthDeps handlers integrador) | persist (tokens) | ✅ (subconfig callbackPort/CIMD→CG-MCP-7/8) |
| MCP-OK-18 | puerto redirect OAuth default `auth.py:91` | núcleo | T2-COSTURA | AuthDeps (integrador inyecta) | — | 🔀 (fijo, aceptable headless) |
| MCP-OK-19 | adapter spec→ToolProtocol tolerante `tool_adapter.py:67-106` | núcleo | BATTERY | `battery_mcp` tool_adapter | — | ✅ |
| MCP-OK-20 | `requires_permission` siempre (terceros no confiables) `tool_adapter.py:48` | núcleo | BATTERY | `battery_mcp` (≡ passthrough) | — | ✅🔀 |
| MCP-OK-21 | `McpToolError` (isError sin re-llamar) `client.py:174-180`+`tool_adapter:54-64` | núcleo | BATTERY | `battery_mcp` | — | ✅ |
| MCP-OK-22 | extracción de texto de content array `client.py:46-56` | núcleo | BATTERY | `battery_mcp` (base de CG-MCP-4) | — | ✅ |
| MCP-OK-23 | resource-tools condicionales (solo si hay resources) `provider.py:311-315` | núcleo | BATTERY | `battery_mcp` provider | — | ✅ |
| MCP-OK-24 | watcher de fuente externa (vector 2) `config_store.py:127-137` | núcleo | T2-COSTURA | `McpConfigWatcher` (integrador provee) | — | ✅ (espejo 15·A5) |
| MCP-OK-25 | cleanup base vía `AsyncExitStack`/`shutdown` `provider.py:295-305` | núcleo | BATTERY | `battery_mcp` (escalación/agent-id→CG-MCP-20) | — | 🔀 (base OK) |

### C · ⛔ / capa de interfaz (colocadas con destino, no descartadas — L02/L07)

| ID | resumen | n\|c | TIER | destino | nota-id | acción |
|---|---|---|---|---|---|---|
| MCP-NA-1 | transportes ws / sdk | cáscara | CLI-ONLY/⛔ | integrador con IDE (si aplica) | — | ❌/⛔ (no core) |
| MCP-NA-2 | transportes sse-ide / ws-ide / claudeai-proxy | cáscara | CLI-ONLY | integrador IDE / ⛔ | — | ⛔ IDE/claude.ai |
| MCP-NA-3 | XAA (SEP-990, identidad corporativa Anthropic) | cáscara | ⛔ | — (producto ajeno) | id (T3 externo) | ⛔ N/A core |
| MCP-NA-4 | conectores claude.ai | cáscara | ⛔ | — (producto Anthropic) | — | ⛔ N/A core |
| MCP-NA-5 | channels (permissions/allowlist/notification, KAIROS) | cáscara | ⛔ | — (producto) | — | ⛔ N/A core |
| MCP-NA-6 | InProcessTransport/SdkControlTransport/vscodeSdkMcp | cáscara | CLI-ONLY | integrador IDE | — | ⛔ IDE |
| MCP-NA-7 | flujo OAuth interactivo (browser + callback-server) | cáscara | CLI-ONLY/INTERFAZ | integrador (terminal/front) | — | ⛔-de-forma → OI-MCP-H |
| MCP-NA-8 | UI de servers MCP / diálogo de aprobación | cáscara | CLI-ONLY/INTERFAZ | integrador (front) | — | ⛔ interfaz |
| **MCP-NA-9** | **registro oficial de servidores** (`officialRegistry.ts`, **72 L** medidas — el tracker `:279` declara 95) | cáscara | ⛔ | — (catálogo de producto Anthropic; el integrador que quiera un catálogo lo provee por `ScopedMcpConfigStore`) | — | ⛔ N/A core |
| **MCP-NA-10** | **`extractAgentMcpServers`** (`utils.ts:466-553`, 88 L) — agrupa los servidores MCP del frontmatter de agente **para PINTARLOS en `/mcp`**; único consumidor `components/mcp/MCPSettings.tsx:6,49` | cáscara | ⛔ | — (superficie de UI; la ruta de comportamiento equivalente es `CG-MCP-21`, que sí es vinculante) | — | ⛔ N/A core (**UI**) |

---

## 2. Síntesis de la categoría

### 2.1 Costuras que implica (nombre · productor invoca · consumidor implementa)

> **⛔ CRUCE CON `SEAMS.md` — DEFECTO ABIERTO (`A-CIERRE·P4″ §16.5·c24/c29`, `AC-21`).** Las **diez** costuras de
> abajo estaban **todas** sin número `S` y este archivo no contenía ni una ocurrencia de la cadena `SEAMS`: **10 de
> 10**, la peor proporción de los once pares auditados (10·mem-remote: 5/12; 07: 1/7). La excusa estructural —
> `SEAMS:4` declara como fuentes sólo los `§2.1` de `{01,16,07,02,05,09}` — **queda revocada por el propio `SEAMS`**:
> la **ENMIENDA A3.CAT** (`SEAMS:21-28`, 2026-07-27) numeró `S30`/`S31` desde el **ciclo 17**, que tampoco era
> fuente. ⇒ el doc ya aceptó ampliarse fuera de las seis. **Pendiente en `SEAMS`: numerar estas diez** (ninguna
> puede numerarse desde aquí: el número lo asigna el rollup). Hasta entonces se marcan `[S-PEND]`.
>
> **Cruce en sentido inverso, resuelto aquí:**
> - **`SEAMS §S23 · on_agent_teardown(agent_id)`** (`SEAMS:415-418`, estado `ausente`) nombra a *«11 (mcp)»* entre
>   los consumidores que reap-ean lo suyo por `agent_id`. **11 lo recoge en sustancia** vía `CG-MCP-20`
>   (`cleanup_for_agent` + `AbortScope.on_abort`) — lo que faltaba era el **cable nominal**, que se establece aquí y
>   debe establecerse en `§S23` en sentido contrario. `CG-MCP-20` **≡ consumidor de `S23`**.
> - **`SEAMS §S25 · AgentDefinition`** (`SEAMS:425-441`) delega en su línea `:438` **`mcp_servers→11`**. **11 NO lo
>   recibía**: cero ocurrencias de `mcp_servers` como campo per-agente y cero de `extractAgentMcpServers` en todo
>   este archivo (en el tracker, `mcp_servers` sólo aparece en `:719` y es el campo de config **del propio runtime**,
>   no el de `AgentDefinition`). **RECLAMADO aquí** como `CG-MCP-21` (§2.3) + fila `MCP-NA`/origen en §1.C. Es el
>   espejo exacto del `isolation→10/18` del par 10 ⇒ `S25` reparte a dueños que no acusan recibo.

- **`CapabilityProvider`** [T2-BASE, home 12] — el loop invoca `manager.tools/system_prompt_sections/active_context`
  per-turno; `McpProvider` implementa. VIVO y verificado por el ensamblador (agent_loop:195/213/218).
- **`McpConfigStore` / `ScopedMcpConfigStore`** [T2-COSTURA, existe · **`[S-PEND]`**] — `provider.startup/reconcile`
  invoca `load`; el integrador registra productores por scope (managed/user/dynamic). Default
  `StorageBackedMcpConfigStore`.
- **`McpConfigWatcher`** [T2-COSTURA, existe · **`[S-PEND]`**] — `provider.startup` lo arranca con `reconcile`;
  integrador provee (poll MinIO / inotify). Espejo `McpConfigWatcher` ≈ 15·`ConfigWatcher`.
- **`register_auth_strategy` / `AuthDeps`** [T2-COSTURA, existe · **`[S-PEND]`**] — extensión de modos de auth; el
  integrador inyecta `redirect_handler`/`callback_handler`/`token_storage` (headless no abre browser).
- **`McpPolicy`** [T2-COSTURA, NUEVA · McR10 · **`[S-PEND]`**] — allow/deny name/command/url; battery filtra antes de
  conectar; integrador provee las reglas (product policy). **Borde de seguridad.**
- **`McpApprovalGate`** [T2-COSTURA, NUEVA · McR10 · **`[S-PEND]`**] — `status(name,scope)→approved|rejected|pending`;
  battery solo conecta project `approved`; integrador decide auto-aprobación (headless). **Borde de seguridad.**
- **`elicitation-hook`** [T2-COSTURA, NUEVA · McR/FIND-MCP18 · **`[S-PEND]`**] — battery declara capability
  `roots`+`elicitation` y enruta la request a un hook inyectado (responde programático sin UI).
- **`trust-gate` (headersHelper)** [T2-COSTURA, NUEVA · McR18 · **`[S-PEND]`**] — battery ejecuta el helper vía
  `exec_env` (09) solo tras workspace-trust del integrador. **Borde de seguridad.**
- **`cleanup_for_agent` → `AbortScope.on_abort`** [T2-COSTURA, cross 08·CG-SIG-8/05·ExR6 · **≡ consumidor de
  `SEAMS §S23 on_agent_teardown(agent_id)`**] — battery expone `cleanup_for_agent(agent_id)`; 05/08 lo registran en
  el abort scope del agente. Única de las diez con contraparte ya numerada en `SEAMS` (`:415-418`), aunque el cable
  faltaba en ambos sentidos hasta esta remediación.
- **`mcp_servers` per-agente ← `SEAMS §S25 AgentDefinition:438`** [T2-COSTURA, **`ausente` · RECLAMADA aquí**] —
  la definición de subagente declara sus propios servidores MCP; el runtime debe restringir el pool del subagente a
  esa lista (contraparte canónica **`initializeAgentMcpServers`**, `runAgent.ts:95-218`; `extractAgentMcpServers` es
  sólo la pantalla del `/mcp`). **No existía en este par**: ver `CG-MCP-21` (§2.3) y
  `MCP-NA-9`/§1.C. Interactúa con `_restrict_to_agent_tools` (`agent_loop.py:99-110`) y con la herencia por
  `inherit_tool_pool` (§2.6·03·CtxR7).
- **`ToolExecEnvironment`** [09, reusado · sin `S` propio: home 09] — headersHelper corre por aquí, NO subprocess
  directo.

### 2.2 Batteries que alimenta
- **`battery_mcp`** — la capacidad MCP entera (12 `mcp/*.py`): config/scope/store/client/provider/state/auth/
  token_storage/tool_adapter/resource_tools/reconcile. OPCIONAL, componible o sustituible por AMBOS integradores.
  Su incompletitud = CG-MCP-1..20 (no gaps del base, L10).
- **`battery_mcp_skills`** (bridge con `battery_skills`, 12) — prompts MCP→slash-commands (`mcp__srv__prompt`) +
  skills `skill://` `loaded_from='mcp'` (gate `MCP_SKILLS && supportsResources`). Builder `mcpSkills.ts`
  NO vendorizado (⛔ no-leíble). = 12·CG-SKILL-15/FIND-MCP16.

### 2.3 CORE-GAPs (brechas A↔B reales → rollup `DEUDA-A.md`) — CG-MCP-1..20, keystone-first
- **CG-MCP-1 · naming FQ + `mcp_info`** [FIND-MCP1/GAP-MCP2] — T1-CONTRATO **keystone**: `ToolProtocol` gana
  `mcp_info={server,tool}`; battery construye `mcp__norm(srv)__norm(tool)` (`_normalize=re.sub([^a-zA-Z0-9_-],_)`),
  conserva `_raw_tool_name` para la llamada. Gatea el gate de permisos FQ (09·B4 deny "Write"≠tool MCP homónimo) y
  el swap (CG-MCP-7). Orden: primero.
- **CG-MCP-2 · `is_mcp`/`always_load`/`search_hint` + precedencia deferral** [FIND-MCP2/GAP-MCP1] — T1-CONTRATO:
  quitar `deferred=True` fijo; `is_deferred_tool` = `always_load→False; is_mcp→True; TOOL_SEARCH→False; deferred`.
  **Cierra 09·GAP-TOOL3.** Junto a CG-MCP-1. **RESTITUIDO (P4-11-2):** la definición canónica de tool MCP trae
  además **`search_hint`** (tabla E del tracker `:147`, junto a `always_load`) — término de búsqueda que el
  descubrimiento diferido usa para encontrar la tool sin cargarla. Se perdía en el destilado pese a que
  **`SEAMS §S16` lo lista explícitamente como *A CRECER* (09·A12)**: el rollup lo espera y sin esta línea 11 no lo
  entregaba. Home del campo: `tools/protocol.py` (contrato), poblado por `battery_mcp` desde el spec del server.
- **CG-MCP-3 · annotations→hints** [FIND-MCP3] — T1-CONTRATO: `readOnlyHint`→(is_read_only,is_concurrency_safe,
  safe_for_background), `destructiveHint`→is_destructive, `openWorldHint`→is_open_world, `title`→userFacingName.
  `is_concurrency_safe` alimenta 09·B-concurrency. **Home del campo `is_concurrency_safe` = `09·FIND-TOOL1`**
  (no 11): aquí sólo se **mapea** desde `readOnlyHint`; quien lo define en `ToolProtocol` y quien lo usa como
  discriminador de topología del fan-out es 09 (ver `CG-TOOL-CONC`). 11 es productor de valor, no dueño del campo.
- **CG-MCP-4 · transform content image/audio/blob/resource** [FIND-MCP5/GAP-MCP3] — T1-CONTRATO `ToolResult.new_messages`
  (B-new_messages, 01) + battery `transform_result_content`. Sin el canal tipado degrada a persist-a-disco+texto
  (reusa persist 10·A23). Orden: tras B-new_messages.
- **CG-MCP-5 · formas de resultado + structuredContent + mcpMeta** [FIND-MCP6, =09·A25] — T1-CONTRATO
  `ToolResult.structured`/`output_schema` (B-structured-output) + battery `transform_mcp_result` 3-formas +
  `infer_compact_schema`. Orden: tras B-structured-output. **RESTITUIDO (P4-11-4):** `_meta` tiene **dos lados** y
  el destilado sólo traía el de respuesta. El canónico envía `_meta` **en la llamada** (tabla E del tracker `:153`,
  junto a `mcpMeta`), no sólo lo lee del resultado ⇒ el contrato de invocación de `battery_mcp` debe aceptar un
  `meta` de salida además de exponer `mcp_meta` de entrada. `SEAMS §S16` lista *A CRECER: mcp_meta (09·A25)* — con
  sólo la mitad de la costura, `S16` se cerraría en falso.
- **CG-MCP-6 · large-output persist/cap + higiene de salida** [FIND-MCP7] — BATTERY `process_mcp_result` (reusa
  truncado/persist 10), `max_result_size_chars=100k`, imágenes excluidas. **RESTITUIDO (P4-11-3):** además del cap
  de 100k, el canónico aplica al texto de resultado **truncado a 2048** y **sanitización unicode** (tabla E del
  tracker `:149`). No es el mismo mecanismo que el cap: el cap evita reventar el contexto, la sanitización evita que
  un server de terceros inyecte control-chars/bidi en el transcript ⇒ es **higiene de borde de confianza**, no
  cosmética, y sin dueño alternativo en ningún otro par (por eso su pérdida no era absorbible).
- **CG-MCP-7 · needs-auth + auth-tool + swap + caché** [FIND-MCP4] — BATTERY: `ServerStatus.NEEDS_AUTH`/`DISABLED`;
  `client.connect` distingue 401→`McpAuthRequired`; provider surte pseudo-tool `mcp__srv__authenticate`; al
  autenticar reconecta y **swapea** (reensamblado per-turno recoge, o `NativeToolRegistry.unregister_by_prefix` si
  push-based → **decide cabo c**); caché TTL 15min + `hasMcpDiscoveryButNoToken`. Orden: tras CG-MCP-1 + CG-MCP-8.
- **CG-MCP-8 · ciclo de vida robusto** [FIND-MCP9/10/11/12] — BATTERY: (a) connect-timeout `wait_for`; (b)
  startup batched-paralelo (gather+semaphore local-3/remoto-20); (c) captura caps/serverInfo/instructions + gate de
  discovery por capability + **instructions (≤2048) inyectadas vía `McpProvider.system_prompt_section`** (seam base
  vivo, §0.2); (d) recuperación de sesión (404/-32001/-32000, retry 1) + onclose-invalidation + **ReconnectScheduler
  backoff** (MAX 5, 1s→30s, cancelable). Núcleo de 11.
- **CG-MCP-9 · timeout tool-call ~∞ + progreso** [FIND-MCP8] — BATTERY: separar call-timeout (≈∞/`MCP_TOOL_TIMEOUT`)
  de connect-timeout (30s); hoy `register_tools_from_specs:125` los mezcla. El 30s **SÍ se aplica hoy** vía
  `dispatcher:68/76-79` (verificado). Progreso→bus eventos (07) o no-op.
- **CG-MCP-10 · env-var expansion** [FIND-MCP13] — BATTERY `config.py` `_expand_env` (`${VAR}`/`:-def`, `missing_vars`).
- **CG-MCP-11 · política admisión + aprobación proyecto** [FIND-MCP14/15] — **borde de seguridad**: `McpPolicy`
  (allow/deny) + `McpApprovalGate` (project approved/rejected/pending, auto-aprueba headless si el integrador lo
  habilita) [T2-COSTURA, contenido T3-INTEGRADOR]. Orden: tras CG-MCP-8.
- **CG-MCP-12 · `*_list_changed` refetch en vivo** [FIND-MCP21] — BATTERY: notification handlers sobre `ClientSession`
  gated por caps → `provider._refresh(server,kind)`. Tras CG-MCP-8 (captura de caps).
- **CG-MCP-13 · dedup por firma de config** [FIND-MCP22] — BATTERY `server_signature` (`stdio:cmd`/`url:norm`),
  filtra antes de conectar. Tras CG-MCP-10 (comparar valores expandidos).
- **CG-MCP-14 · reconcile scope-guard** [FIND-MCP23, 🔀-real] — BATTERY `plan_reconcile` recibe `scope_of`; ausente
  solo se desconecta si `scope==DYNAMIC` (o cambió config-hash). `reconcile.py:61-63` hoy sobre-agresivo.
- **CG-MCP-15 · headersHelper + trust-gate** [FIND-MCP24] — BATTERY: campo `headers_helper`; `client.connect`(http/sse)
  ejecuta vía `exec_env` (09, NO subprocess) con `trust-gate` del integrador; `{**static,**dynamic}`. Tras CG-MCP-8.
- **CG-MCP-16 · keying credenciales config-hash + revoke + USER-SCOPE** [FIND-MCP20 + §0.1/cabo 15·CG-STOR-1] —
  BATTERY token_storage: `base` incluye `sha256(type+url+headers)` (cambiar url no reusa) + `revoke()` (RFC7009); y
  **el `user_id` real** (id-opaco del integrador) reemplaza el literal `"mcp"` — **UNIFICADO 15·CG-STOR-1/CG-STOR-3**
  (guard-path/sanitize/scope). nota-id: persistencia. **Seam nuevo:** `factory` debe pasar el **scope opaco**
  (`RuntimeHost.scope`, firma única — ver OI-MCP-A) a `McpProvider` (hoy 148-155 no lo pasa; el runtime tiene el
  valor real, hoy usado sólo para el transcript en `runtime.py:424`). **El parámetro NO se llama `user_id`**:
  `SEAMS:16-17` `【id-opaco】` prohíbe transportar identidad interpretada en la firma.
- **CG-MCP-17 · resource tools homologadas** [FIND-MCP17] — BATTERY: `server` requerido + gate `caps.resources`,
  output estructurado `{contents:[{uri,mimeType,text,blobSavedTo}]}` (blob persist reusa CG-MCP-4), ambas deferred.
- **CG-MCP-18 · elicitation/roots headless** [FIND-MCP18] — BATTERY declara `roots`→cwd + `elicitation` + retry
  -32042; enruta a `elicitation-hook` inyectado. Diálogo interactivo = ⛔ (MCP-NA-7).
- **CG-MCP-19 · prompts→commands + MCP-skills bridge** [FIND-MCP16] — BATTERY `battery_mcp_skills` (=12·CG-SKILL-15).
  11 EMITE; 12 mergea. `mcpSkills.ts` ⛔ no-vendorizado.
- **CG-MCP-20 · cleanup per agent_id + abort-scope** [FIND-MCP19] — T2-COSTURA `cleanup_for_agent`; wiring en
  **05·ExR6/GAP-EXEC4** (reaping recursos hijos) + **08·CG-SIG-8** (`AbortScope.on_abort`). Escalación stdio→SDK.
  **≡ consumidor de `SEAMS §S23 on_agent_teardown(agent_id)`** (`SEAMS:415-418`, hoy `ausente`): 11 reap-ea *lo suyo*
  — clients stdio/http del agente, tokens en vuelo, tareas de reconnect — cuando 05 dispara el teardown. El cable
  nominal faltaba en las dos direcciones (§2.1).
- **CG-MCP-21 · `mcp_servers` per-agente (`AgentDefinition`)** [**NUEVO en A-CIERRE·P4″ §16**; reclama la
  delegación ``SEAMS §S25:438 `mcp_servers→11```. **Ficha REESCRITA a T1 el 2026-07-30 tras leer el canónico por
  excepción: la primera versión estaba anclada a la función equivocada** — ver el recuadro al final] — T2-COSTURA +
  BATTERY.

  **Contraparte canónica real: `tools/AgentTool/runAgent.ts:95-218 initializeAgentMcpServers`**, cableada en
  `:653` (llamada), `:661-664` (fusión de tools con `uniqBy` por `name`), `:685` (`mcpClients: mergedMcpClients` en
  las opciones del subagente) y **`:818` `await mcpCleanup()` dentro de un `finally`** — «runs on normal completion,
  abort, or error». **Comportamiento, leído 1→EOF, no inferido:**
  1. **Dos formas de spec, con ciclo de vida OPUESTO** (`:140-170`): un **string** es *referencia por nombre*, se
     resuelve con `getMcpConfigByName` y **reutiliza el cliente memoizado del padre ⇒ NO se limpia al terminar el
     agente**; un **inline `{nombre: config}`** recibe `scope:'dynamic'`, se marca `isNewlyCreated` y **sí se limpia**
     (`:194-210`, *«shared clients … are memoized and used by the parent context»*). Limpiar un cliente compartido
     mataría MCP del padre: **es la razón de que la lista `newlyCreatedClients` exista aparte**.
  2. **Aditivo, nunca sustitutivo** (`:214`): `[...parentClients, ...agentClients]`. El subagente **no** recibe un
     subconjunto del pool del padre — recibe el pool del padre **más** los suyos. *(Esto corrige la formulación
     anterior de esta ficha: el canónico no implementa «dar a un subagente un subconjunto de servers».)*
  3. **【borde-seguridad】** (`:112-127`): con `isRestrictedToPluginOnly('mcp')`, el MCP de frontmatter se salta
     **sólo para agentes controlados por el usuario**; plugin, built-in y `policySettings` son `isSourceAdminTrusted`
     y **sí cargan** — con el motivo escrito de que bloquearlos *«breaks plugin agents … contradicting "plugin-provided
     always loads"»*. Un runtime que copie esto como un booleano plano reproduce la forma y pierde la regla.
  4. **Degradación no fatal** (`:145-151`, `:156-162`, `:186-191`): servidor no encontrado, spec con ≠1 clave o
     conexión fallida ⇒ `logForDebugging` + `continue`. **El agente arranca igual.**

  **Estado en el runtime: ausente en ambas caras.** El subagente hereda el pool entero por `inherit_tool_pool`
  (fork:75) + `capability_manager` COMPARTIDO (`runtime.py:358`), y `_restrict_to_agent_tools`
  (`agent_loop.py:99-110`) filtra por *nombre de tool*, no por *server*. **Alcance:** (a) campo en `AgentDefinition`
  admitiendo **las dos formas** (str | dict de una clave) — dueño del shape = 05, ver `S25`; (b) conexión + fusión
  aditiva y **`cleanup` en `finally` que sólo cierra lo creado inline** — `battery_mcp`; (c) el gate admin-trusted del
  punto 3. **No** requiere `CG-MCP-1`: el canónico no filtra por prefijo aquí, **fusiona y deduplica por `name`**
  (`uniqBy`), así que la dependencia declarada antes («orden: tras CG-MCP-1») **queda retirada** — sólo (c) del
  filtro FQ la conserva si se quisiera además restringir. **No** es el `mcp_servers` de `config.py` del runtime
  (tracker `:719`), que es global: confundirlos fue lo que dejó la delegación huérfana.

  > ⚠ **Corrección de mi propia ficha, dejada escrita (L03).** Esta ficha nació citando **`extractAgentMcpServers`**
  > como contraparte canónica. Al abrir el canónico 1→EOF (`utils.ts` 575 L) y censar sus consumidores, resultó que
  > **su único consumidor es `components/mcp/MCPSettings.tsx:6,49`: es la ruta de PANTALLA del `/mcp`**, y su propio
  > docstring lo dice (*«used to show agent-specific MCP servers in the /mcp command»*). Más aún: `extractAgentMcpServers`
  > **descarta las referencias por string** (`utils.ts:483`, *«Skip string references»*) mientras que
  > `initializeAgentMcpServers` **las resuelve y conecta** (`runAgent.ts:140-151`) ⇒ **las dos funciones no ven el
  > mismo conjunto de servidores**, y anclar el gap a la de UI habría portado la mitad ciega del comportamiento.
  > La delegación de `S25` es correcta y el gap es real; **el ancla estaba mal, y sólo abrir el canónico lo detectó**
  > — `L09`: cablear ≠ existir, aplicado a mi propio documento.
- **Menores plegados — DESPLEGADOS (P4-11-8).** Se listan con su destino real; el plegado previo llevaba uno a
  destino equivocado:
  - oauth-subconfig `callbackPort`/CIMD → **CG-MCP-7/8** (sin cambio).
  - escritura-atómica de `.mcp.json` → **15·storage** `StorageProtocol` atomicidad (sin cambio; fuera de 11).
  - severidad `fatal`/`warning` del parse + caso `npx`-Windows → **CG-MCP-10** (sin cambio).
  - **regex de nombre de server + nombres reservados en `addMcpConfig` → `CG-MCP-11` + `CG-MCP-1`, NO `CG-MCP-13`
    (CORREGIDO).** `CG-MCP-13` es dedup por *firma de config* (dos entradas distintas apuntando al mismo
    proceso/URL): un problema de **eficiencia/consistencia**. La validación de nombre es **admisión** — rechaza el
    nombre antes de persistirlo — y por tanto vive en el borde de seguridad `CG-MCP-11`; su parte de *forma* del
    nombre es la misma normalización que `CG-MCP-1` aplica al construir `mcp__norm(srv)__norm(tool)`, y ambas deben
    usar **una sola** función o un nombre admitido puede producir una FQ colisionante. **[T1 desde 2026-07-30 (`config.ts` 1→EOF):** la
    caracterización del gate canónico procede de `claude-code/src/services/mcp/config.ts` leído en ciclo anterior,
    no re-abierto en la ventana de esta corrección — el ruteo se corrige por razón estructural, y la cita canónica
    queda marcada para re-verificar en P6″.**]**
  - step-up 403 → **CG-MCP-7** (sin cambio).

### 2.4 DEUDA-B (higiene interna — L10, NO A↔B)
- **LAT-MCP1 · `McpServerConfig.auth_headers()` duplicado muerto** [`config.py:97-102`] — **borrar**. Verificado
  ESTE ciclo: la ruta viva del bearer es `auth._build_bearer` (73-75)→`AuthArtifacts.headers`→`client.connect:105-106`;
  `auth_headers()` sin consumidor de prod. Hermano de to_llm/category/LAT-EXEC1/LAT-HOOK1/LAT-SKILL1.
- **`NativeToolRegistry` huérfano** [cabo c, 09·TiR4 · **= `DEUDA-B §3.A·DB-05`**] — **retirar,
  INCONDICIONALMENTE**. Confirmado por el ensamblador: hot-plug es reensamblado per-turno (agent_loop:195), no
  registro dinámico; `native_registry.py` 0 prod-consumers. **CORREGIDO (`A-CIERRE·P4″ §16.4·I1`):** la redacción
  previa lo condicionaba —«se mantiene SOLO si CG-MCP-7 implementa el swap push-based»— y eso **contradice a
  `DB-05`**, que tras la auditoría `R-1`/`RV-6` ordena el borrado sin condición. La condición era además
  innecesaria: `CG-MCP-7` **no necesita este módulo**, re-crea `unregister_by_prefix` **sobre `ToolRegistry`** si
  llega a hacer el swap push-based — no como excepción al borrado. Un par no puede reintroducir por la puerta de
  atrás una condición que el rollup receptor ya cerró. → `B-orphans`/A3.DB.
- **`McpServerConfig.model`** [`config.py:49`, 0 lectores prod] — slot pasivo; **cablear** si `battery_mcp_skills`
  usa modelo per-server, si no **borrar**. → A3.DB.
- **`McpState.pending_servers()`** [`state.py:80-81` · **= `DEUDA-B·DB-28`**] — accesor de introspección
  integrator-facing; **conservar** (superficie de API, no maquinaria muerta). **CORREGIDO (`§16.4·I2` /
  consecuencia 49):** aquí figuraba como *«nota, no B-orphan»* mientras `DEUDA-B` **lo indexa como ítem `DB-28`**.
  El veredicto de fondo (conservar) no cambia; lo que cambia es que **es un ítem del ledger**, no una nota — y por
  eso entra en el recuento de §3.1, que antes lo excluía. Un elemento que el rollup receptor numera no puede
  quedarse sin numerar en el par que lo emite.
- **LAT-TOOL1 (`category`)** — `McpTool` (tool_adapter:27) + resource-tools (31/63) setean `SYSTEM`, nadie lee.
  Ya homed 09/DEUDA-B; aterriza sin novedad.
- **LAT-CAP1 (`CapabilityActivation`) — comprobado ESTE ciclo, NO aterriza en MCP.** Abriendo `contracts.py`
  1→EOF (26-38): el shape inerte destapado en 12 (0 prod-consumers) **no lo usa `McpProvider`** (leído 1→EOF,
  devuelve listas `tools/catalog/resources/active_context`, nunca `CapabilityActivation`). Ya homed 12/A3.DB; sin
  novedad en 11 (registro de honestidad: se verificó, no se heredó).
- **`CapabilitySummary.deferred` no seteado para tools MCP** [`provider.py:319-327` catalog no pasa `deferred=`
  aunque `McpTool.deferred=True`] — cosmético: `catalog()` sin prod-consumer (=12, solo `manager.catalog` en tests)
  ⇒ cara de introspección, **NO** B-orphan (L10). Menor, no elevado.
- **`compact_context`/`active_context`=[]** [provider.py:332-336] — cara del motor-compact NO portado (01/02) +
  seam de recall; **NO** B-orphan nuevo (L10, =13·D8).

### 2.5 Elementos de integrador (→ `00-INTEGRADORES.md`, detalle simétrico L05/§1.1)
Eje PRIMARIO = **contrato base común (must-be de todo integrador MCP)**; específico por-integrador = secundario.
- **OI-MCP-A · atribuir scope opaco a los tokens** [must-be] — el integrador DEBE pasar **su** identificador de
  scope al `battery_mcp`/token-store; el runtime nunca lo interpreta. **Firma única y normalizada
  (CORREGIDO, `§16.4·I4` / consecuencia 48): `RuntimeHost.scope` — token OPACO.** Cableado: `factory`→`McpProvider`
  (hoy `factory.py:148-155` pasa `storage=` y **nunca** el scope). Orden: con CG-MCP-16. Aceptación: dos usuarios,
  claves de token disjuntas. *(agentic_code: user único, scope constante; agentic_assistant: multi-tenant real.)*

  > **Por qué se retiran las dos firmas anteriores.** Este ítem ofrecía *«`create_runtime(config.capabilities.mcp_user=…)`
  > o `McpProvider(user_id=ctx.user_id)`»*, y `DEUDA-A·ID-3` usaba una tercera grafía (`scope=`), y
  > `00-INTEGRADORES §1.7·C5` una cuarta (`RuntimeHost.scope`) — **cuatro nombres para un mismo cable**. No es un
  > problema de estilo: **`SEAMS:16-17` declara transversal el invariante `【id-opaco】`** — *«ninguna firma
  > transporta `userId`/`sessionId` interpretados; los repos son genéricos sobre una metadata que el integrador
  > define y el runtime lee sólo el `.id` opaco (LEGEND §2.4)»*. La firma `McpProvider(user_id=ctx.user_id)` **nombra
  > la identidad en el parámetro** y por tanto es exactamente la que el invariante prohíbe; se ofrecía al integrador
  > en pie de igualdad con la correcta. Queda **una sola** firma, alineada con `C5` y con `15·CG-STOR-1/CG-STOR-3`.
  > El **bug de fondo no cambia** y sigue siendo el mejor hallazgo del ciclo (§0.1): hoy el literal `"mcp"` colisiona
  > entre usuarios.
- **OI-MCP-B · política allow/deny** [must-be] — reglas name/command/url. Firma: `McpPolicy` provider. Aceptación:
  server denegado no conecta. *(agentic_code: settings local; agentic_assistant: policy por tenant.)*
- **OI-MCP-C · gate de aprobación de proyecto** [must-be] — `McpApprovalGate`. Aceptación: project pending no
  conecta hasta aprobar. *(agentic_code: prompt terminal/auto-bypass; agentic_assistant: endpoint front.)*
- **OI-MCP-D · handlers OAuth interactivos** [must-be, headless] — `redirect_handler`/`callback_handler`.
  *(agentic_code: abre browser+listener local; agentic_assistant: redirige por el front, callback por URL de tenant.)*
- **OI-MCP-E · productores de config por scope + watcher** [must-be] — `ScopedMcpConfigStore.set_producer` +
  `McpConfigWatcher`. *(agentic_code: `.mcp.json` + inotify; agentic_assistant: MinIO + poll/evento.)*
- **OI-MCP-F · trust-gate del headersHelper** [must-be, borde seg] — workspace-trust antes de ejecutar el script.
- **OI-MCP-G · hook de elicitation** [opcional] — responder programático a elicitation/roots.
- **OI-MCP-H · capa de interfaz OAuth/MCP** [CLI-ONLY] — flujo interactivo (browser/callback UI) + gestión de
  servers. *(agentic_code: terminal; agentic_assistant: front `new_core`.)* = MCP-NA-7/8.
- **OI-MCP-I · transportes IDE** [opcional] — in-process/sdk/vscode solo si el integrador es IDE. = MCP-NA-1/2/6.

### 2.6 Cabos que SALEN (con destino)
- **(a) 12·CG-SKILL-15/FIND-MCP16** → CG-MCP-19: 11 EMITE los comandos MCP; 12 mergea. `mcpSkills.ts` ⛔.
- **(b) 15·CG-STOR-1** → **UNIFICADO en CG-MCP-16** (user-scope de tokens; guard-path/sanitize/scope común con 15).
- **(c) 09·TiR4/NativeToolRegistry** → **RESUELTO**: retirar **incondicionalmente** (DEUDA-B §2.4 = `DB-05`). La
  coletilla previa «salvo swap CG-MCP-7» queda **retirada** (`§16.4·I1`): `CG-MCP-7`, si hace swap push-based, lo
  hace sobre `ToolRegistry`.
- **(d) 11·LAT-MCP1** → DEUDA-B §2.4 (borrar).
- **(e) `compact_context`** → cara motor-compact (01/02), NO B-orphan (§2.4/§0.2).
- **09·A25 (mcpMeta)** → CG-MCP-5. **09·B4 (deny prefijo)** → habilitado por CG-MCP-1. **09·TiR3/FIND-TOOL7**
  (discovered-set fork-safe) → confirmado ESTE ciclo: `deferred.mark_tools_discovered:34-37` **REEMPLAZA** la clave
  (no muta) + `fork:78` copia shallow del contenedor → sin aliasing; sostenido.
- **05·ExR6/GAP-EXEC4 · 08·CG-SIG-8/SR3** → CG-MCP-20 (cleanup por agent_id en abort scope; 05/08 dueños del wiring).
- **03·CtxR7/A13** → **precisión sostenida**: la herencia MCP en subagentes es por `inherit_tool_pool` (fork:75) +
  `capability_manager` COMPARTIDO (runtime.py:358), **NO** por `app_state.capabilities` (que solo lleva el
  discovered-set, `deferred.py:37`). `ForkSnapshot.capabilities` (fork:42-46) = seam del integrador per-tenant.
  Conclusión observable (sin doble-conexión/clonado) intacta.

### 2.7 Orden de aplicación (restitución PARCIAL del §Plan del tracker — P4-11-1)

El tracker dedica **226 L** (`../11-cap-mcp.md:374-599`) a un plan `McR1..McR19` (**`McR14` no existe** ⇒ 18 pasos)
y este destilado lo había comprimido a **59 L** ≈ **26 %**, sin orden explícito ni firmas. La compresión no era
absorbible: un plan sin orden no es aplicable, y las dependencias entre CG son reales (el naming FQ **gatea** el
filtro per-agente y el swap; la captura de capabilities **gatea** los handlers de `list_changed`). Orden derivado de
las dependencias declaradas por cada CG:

| ola | CG | por qué va aquí |
|---|---|---|
| **0 · contratos** | CG-MCP-1 · CG-MCP-2 · CG-MCP-3 | tocan `tools/protocol.py`/`deferred.py`; **todo lo demás depende del naming FQ**. `is_concurrency_safe` se **mapea** aquí pero su home es 09·FIND-TOOL1 |
| **1 · contratos de resultado** | CG-MCP-4 · CG-MCP-5 | requieren `ToolResult.new_messages` / `.structured` del paquete 01 (B-new_messages, B-structured-output): **bloqueadas fuera de 11** |
| **2 · ciclo de vida** | CG-MCP-8 → CG-MCP-12 · CG-MCP-15 | `CG-MCP-8` captura caps/serverInfo/instructions; sin esa captura no hay gate para `list_changed` (12) ni para el headersHelper (15) |
| **3 · admisión y credenciales** | CG-MCP-11 · CG-MCP-16 · CG-MCP-7 | borde de seguridad primero (política + aprobación), luego el keying/scope de tokens, luego needs-auth (que usa ambos) |
| **4 · resto de battery** | CG-MCP-6 · CG-MCP-9 · CG-MCP-10 → CG-MCP-13 · CG-MCP-14 · CG-MCP-17 · CG-MCP-18 | `CG-MCP-13` tras `CG-MCP-10` (dedup compara valores **ya expandidos**) |
| **5 · cruces con otros pares** | CG-MCP-19 (→12) · CG-MCP-20 (→05/08) · CG-MCP-21 (→05 shape + 09 filtro FQ) | dependen de trabajo cuyo dueño **no es 11**; se emiten, no se ejecutan aquí |

> **Lo que NO queda restituido, dicho en claro.** Esta tabla restituye el **orden y las dependencias**; **no**
> restituye las **firmas paso a paso** del §Plan ni sus criterios de aceptación por McR, que siguen viviendo sólo en
> `../11-cap-mcp.md:374-599`. Tampoco se restituyen las **38 anclas canónicas `.ts:línea`** ni los **42 tests
> nombrados** del tracker: es el **patrón 3** (columnas ausentes por esquema en todo `SEPARACION/*`), no una omisión
> de este par, y su reparación es transversal — no se simula aquí escribiendo anclas que esta pasada no ha
> re-verificado. Consecuencia práctica: **para implementar, el §Plan del tracker sigue siendo lectura obligatoria**;
> este documento reparte y ordena, no sustituye.

---

## 3. GATEKEEPER de cierre (L03/L04/L09/L11 — MOSTRADO)

**Frase de rigor:** De lo que aquí se destile nace el código. Ningún finding se coloca sin abrir lo que lo respalda;
ninguna categoría se cierra sin repartirla entera y con las dos caras al mismo detalle. Lo que aquí quede sin
colocar —o colocado sin abrir, o desarrollado solo del lado del base— es, exacto, el código que nacerá incompleto.

### 3.1 Ledger — 28 vinculantes (24 FIND-MCP + 3 GAP-MCP + 1 S25·mcp_servers) + 25 MCP-OK + **10** MCP-NA + 8 DEUDA-B = **71**

> **Recuento CORREGIDO (`§16.5·c28`).** La cifra anterior era **63** — «27 + 25 + 8 + **3** DEUDA-B» — y contaba
> **3** entradas de DEUDA-B cuando `§2.4` tiene **8** (LAT-MCP1 · NativeToolRegistry · `model` · `pending_servers`
> (`DB-28`) · LAT-TOOL1 · LAT-CAP1 · `CapabilitySummary.deferred` · `compact_context/active_context`): el total real
> con el ledger de entonces era **68**, no 63. Con las dos incorporaciones de esta remediación —`S25·mcp_servers`
> (vinculante, `CG-MCP-21`) y `MCP-NA-9` (`officialRegistry`)— quedó en **70**, y en **71** el 2026-07-30 al añadirse `MCP-NA-10` (`extractAgentMcpServers`, ruta de pantalla) tras leer el canónico por excepción. La causa del descuadre está en la
> consecuencia 49: el recuento se cuadraba contra sí mismo en vez de contra el índice de `DEUDA-B`.

| ID | TIER | destino | cara | evidencia | detalle | nota-id |
|---|---|---|---|---|---|---|
| FIND-MCP1 | T1-CONTRATO | tools/protocol + battery | ambas | `tool_adapter.py:43/99` (name crudo) abierto | sí (CG-MCP-1) | — |
| GAP-MCP2 | T1-CONTRATO | tools/protocol | base | `tool_adapter.py` abierto | sí (CG-MCP-1) | — |
| FIND-MCP2 | T1-CONTRATO | tools/protocol+deferred | base | `tool_adapter.py:30`+`deferred.py:17-27` abiertos | sí (CG-MCP-2) | — |
| GAP-MCP1 | T1-CONTRATO | tools/deferred | base | `deferred.py:25-27` abierto | sí (CG-MCP-2) | — |
| FIND-MCP3 | T1-CONTRATO | tools/protocol + battery | ambas | `tool_adapter.py:93-96` abierto | sí (CG-MCP-3) | — |
| FIND-MCP5 | T1-CONTRATO+BATTERY | ToolResult(01)+battery | ambas | `client.py:46-56` abierto | sí (CG-MCP-4) | — |
| GAP-MCP3 | T1-CONTRATO | ToolResult(01) | base | `client.py:55` abierto | sí (CG-MCP-4) | — |
| FIND-MCP6 | T1-CONTRATO+BATTERY | ToolResult(01)+battery | ambas | `client.py:174-180` abierto | sí (CG-MCP-5) | — |
| FIND-MCP7 | BATTERY | battery_mcp | base | `client.py:174-180` abierto | sí (CG-MCP-6) | — |
| FIND-MCP4 | BATTERY | battery_mcp | ambas | `provider.py:155-157`+`state.py:13-19` abiertos | sí (CG-MCP-7) | persist |
| FIND-MCP9 | BATTERY | battery_mcp | base | `client.py:83-143` abierto (solo initialize) | sí (CG-MCP-8) | — |
| FIND-MCP10 | BATTERY | battery_mcp | base | `client.py:83-143` (sin wait_for) | sí (CG-MCP-8) | — |
| FIND-MCP11 | BATTERY | battery_mcp | base | `provider.py:241-245` (for secuencial) | sí (CG-MCP-8) | — |
| FIND-MCP12 | BATTERY+T2-BASE | battery + system_prompt_section | ambas | `client.py:137/153-154`+`manager.py:81-96` | sí (CG-MCP-8) | — |
| FIND-MCP8 | BATTERY | battery_mcp | base | `dispatcher.py:68/76-79`+`provider.py:125` abiertos | sí (CG-MCP-9) | — |
| FIND-MCP13 | BATTERY | battery_mcp | base | `config.py:105-126` (parse sin expand) | sí (CG-MCP-10) | — |
| FIND-MCP14 | T2-COSTURA+T3 | McpPolicy+integrador | ambas | `config_store/scope` abiertos (sin policy) | sí (CG-MCP-11) | — |
| FIND-MCP15 | T2-COSTURA+T3 | McpApprovalGate+integrador | ambas | `provider.py:228-245` (conecta sin aprobar) | sí (CG-MCP-11) | scope/trust |
| FIND-MCP21 | BATTERY | battery_mcp | base | `client.py:136-137` (sin handlers) | sí (CG-MCP-12) | — |
| FIND-MCP22 | BATTERY | battery_mcp | base | `scope.py`/`config.py` (sin firma) | sí (CG-MCP-13) | — |
| FIND-MCP23 | BATTERY | battery_mcp | base | `reconcile.py:61-63` abierto | sí (CG-MCP-14) | — |
| FIND-MCP24 | BATTERY+T2-COSTURA | battery + trust-gate | ambas | `client.py:100-134` (solo headers estáticos) | sí (CG-MCP-15) | trust |
| FIND-MCP20 | BATTERY+T3 | battery + user-scope | ambas | `token_storage.py:24`+`factory.py:148-155` abiertos | sí (CG-MCP-16, unifica 15) | persist |
| FIND-MCP17 | BATTERY | battery_mcp | base | `resource_tools.py:44/71-83` abiertos | sí (CG-MCP-17) | — |
| FIND-MCP18 | BATTERY+T2-COSTURA | battery + elicitation-hook | ambas | `client.py:136-137` (sin capability) | sí (CG-MCP-18) | — |
| FIND-MCP16 | BATTERY | battery_mcp_skills(12) | ambas | `provider.py:307-330` (sin prompts) | sí (CG-MCP-19) | — |
| FIND-MCP19 | T2-COSTURA | battery + 05/08 | ambas | `provider.py:295-305` (shutdown global) | sí (CG-MCP-20) | ejecución |
| MCP-OK-1..25 | BATTERY/T2-COSTURA | battery_mcp/costuras | base/ambas | 12 `mcp/*.py` 1→EOF (§1.B con cita) | N/A (✅/🔀) | — |
| MCP-NA-1..8 | CLI-ONLY/⛔ | integrador/⛔ | integrador | ledger tracker (⛔ abiertos L02) | N/A (⛔) | — |
| LAT-MCP1 | DEUDA-B | borrar | base | `config.py:97-102` vs `auth.py:73-75`+`client.py:105-106` | N/A | — |
| NativeToolRegistry | DEUDA-B | retirar | base | `native_registry.py`1→42 + `agent_loop.py:195` (per-turno) | N/A | — |
| McpServerConfig.model | DEUDA-B | cablear\|borrar | base | `config.py:49` (0 lectores) | N/A | — |

### 3.2 Cinco preguntas de cierre
1. **¿ÍNTEGRO `../11-cap-mcp.md`?** → **sí, 1→798** (tesis + tablas A-H + FIND-MCP1-24 + GAP-MCP1-3 + cabos +
   §Recuento + ledger + §Plan + Re-visita gate-11 + Re-verificación A). Es hipótesis (L11), no fuente de verdad.
   **CORREGIDO:** decía *«1→799»* sobre un archivo de **798 L**, y citaba el §Plan como *«McR1-19»* cuando **`McR14`
   no existe** en el tracker (salta `McR13`→`McR15`) — se copió el rango que el propio tracker se autoatribuye sin
   contarlo. Un «1→N» con N distinto del tamaño real es la marca de una declaración no medida (`§16.5·c28`).
2. **¿Reconcilia el conteo?** vinculantes = **28** = 24 FIND-MCP + 3 GAP-MCP (del tracker) + 1 DR-2 incorporada por
   cruce (`S25·mcp_servers`); colocados = **28** (todos en §1.A → CG-MCP-1..**21**); **sin colocar = 0**.
   (+ 25 MCP-OK homologadas + **10** MCP-NA interfaz/⛔ + **8** DEUDA-B — ver la corrección de §3.1).
3. **¿Cada ✅/🔀 que afirma cableado abrió el tramo del ensamblador (sin grep)?** → **sí, 1→EOF ESTE ciclo
   (ganado en 2 iteraciones — ver §3.3):**
   hot-plug per-turno `agent_loop.py:185/194-195` (+ `_restrict_to_agent_tools` 99-110) → `manager.py:50-59/61-79` →
   `provider.py:307-316`; misma instancia root/subagente `factory.py:194` + `runtime.py:358`; McpProvider condicional
   `factory.py:148-155` (`storage=` sí, `user_id=` NO → CG-MCP-16); timeout `dispatcher.py:68/76-79`+`provider.py:125`;
   herencia fork `fork/__init__.py:26/75/78` (inherit_tool_pool + shared-container, NO app_state); LAT-MCP1
   `config.py:97-102` vs `auth.py:73-75`+`client.py:105-106`; `NativeToolRegistry` 0-prod `native_registry.py`1→42;
   `is_deferred` `deferred.py:17-27/34-37`; startup secuencial `provider.py:241-245`; reconcile `reconcile.py:61-63`.
   **+ CONTRATOS (2ª iteración, subsanando la sobre-declaración del 1er cierre):** `contracts.py`1→77
   (`CapabilityProvider` Protocol 41-69 + `system_prompt_section` OPCIONAL 52-58 → funda §0.2; `CapabilityActivation`
   26-38 = LAT-CAP1 comprobado, no aterriza en MCP); `tools/protocol.py`1→62 (`ToolProtocol` 51-61 SIN
   `mcp_info`/`is_mcp`/`always_load`/`is_destructive`/`is_open_world`/`is_concurrency_safe`; `ToolResult` 18-48 SIN
   `new_messages`/`structured`/`output_schema` → fundan CG-MCP-1/2/3/4/5, antes inferidos de imports); `tools/pool.py`
   1→79 (`assemble`/`find` 22-45 native-gana+deny → hot-plug intacto). **Grep solo para AUSENCIA** (auth_headers/
   NativeToolRegistry/scope sin caller), con la ruta viva corroborada por lectura.
   **CORREGIDO (`§16.3·T3` / consecuencia 46):** aquí se afirmaba *«A (canónico) NO re-leído»*. Esa frase se copió
   de `../11-cap-mcp.md:706/722-723` **sin ver que el propio tracker la revoca 30 líneas más abajo**, en
   `§Re-verificación lado A :734-781` (*«COMPLETADA 1→EOF … CERO discrepancias»*, con `types.ts` 258, `MCPTool` 77,
   `McpAuthTool` 215, List 123, Read 158). El estado vigente del tracker es **A re-leído**, con **una laguna
   confesada** (`:745`: los tres `prompt.ts`). Se cita la **última** aparición, no la primera.
4. **¿Cara integrador al MISMO detalle que base?** → **sí** — §2.5 OI-MCP-A..I con capacidad·costura·firma·cableado·
   orden·aceptación; ningún "→ integrador" a secas.
5. **¿Doble filo (L10)?** → **sí.** Ningún ❌ disfrazado de 🔀 (FIND-MCP8/23 marcados 🔀 en el tracker se
   re-clasifican **CORE-GAP** por ser brechas reales de la battery, no divergencias por diseño). Ninguna deuda
   inflada: los ⛔ de producto (XAA/claude.ai/channels/IDE) NO se cuentan como deuda de B (MCP-NA, capa ajena); la
   incompletitud de `battery_mcp` es gap **de la battery**, no del base (L10); `compact_context=[]` NO se eleva a
   B-orphan (cara motor-compact). LAT-MCP1/NativeToolRegistry = higiene B-interna, NO A↔B.

### 3.3 §Honestidad
**⚠ CIERRE EN 2 ITERACIONES (gate auto-adversarial del usuario "¿EoF en todos?", 2026-07-24 — reproche recurrente
idéntico a 04·modes/12·skills).** Mi 1er cierre **sobre-declaró la Q3**: afirmó "cada ✅/🔀 abrió el tramo 1→EOF"
habiendo abierto los 12 `mcp/*.py` + los 8 del ensamblador (factory/manager/agent_loop/runtime/fork/dispatcher/
deferred/native_registry) PERO **NO** los tres archivos de CONTRATO que la tesis apoya — `capabilities/contracts.py`
(el seam `CapabilityProvider` en que descansa §0.1/§0.2/§2.1, INFERIDO de provider/manager = fallo L08 idéntico al
de 12 con este mismo archivo), `tools/protocol.py` (donde CG-MCP-1..5 colocan los gaps T1-CONTRATO, afirmados SIN
abrir el contrato) y `tools/pool.py`. Al reproche los leí 1→EOF: **resultado = CERO cambios de clasificación**
—cada CG se sostuvo— **pero eso solo se sabe tras leerlos** (idéntico a 04·modes). Fundamentos ahora reales:
`ToolProtocol`/`ToolResult` confirmados sin `mcp_info`/`is_mcp`/`always_load`/annotations/`new_messages`/`structured`;
`system_prompt_section` OPCIONAL confirma §0.2; **LAT-CAP1 comprobado — NO aterriza en MCP** (registro de honestidad,
§2.4). El value-add legítimo del ciclo (1ª iteración) fue el ENSAMBLADOR: hot-plug per-turno + misma-instancia +
**bug multi-user de tokens** verificable en el punto de unión (`factory` pasa `storage=` pero nunca `user_id=` pese a
`ctx.user_id`) → CG-MCP-16 unifica 15·CG-STOR-1; LAT-MCP1 (ruta viva `auth._build_bearer` vs muerto `auth_headers`);
`NativeToolRegistry` huérfano. Re-clasificación L10 doble-filo: FIND-MCP8/23 (🔀 tracker)→CORE-GAP. **Lección
re-interiorizada (3ª vez, tras 12 y 04): en ciclo cuyo eje ES un SEAM, el archivo del CONTRATO (`contracts.py`/
`protocol.py`) se abre 1→EOF, NUNCA se infiere del consumidor — y la Q3 no se declara "sí" hasta que TODO lo que la
clasificación apoya está abierto, no solo el ensamblador de ejecución.** Suite no re-ejecutada (fase diseño, código
intacto). Estado vigente de A: **re-verificado 1→EOF en la 2ª vuelta del tracker**, con la laguna confesada de los
tres `prompt.ts` (`../11-cap-mcp.md:745`) — la frase «A no re-leído» que figuraba aquí estaba **revocada por su
propia fuente** (Q3, consecuencia 46).

**§3.3·bis — PASADA `A-CIERRE·P4″` (2026-07-30, `AC-12` par 11/18).** Este documento fue reconciliado ficha a ficha
contra el tracker leyendo **bloques homólogos de las dos caras a la vez**, más la columna de cruce de los rollups.
Lo encontrado, sin adornos (detalle en `A-CIERRE-P4.md §16`):
- **Cruce con `SEAMS`: 10 de 10 costuras sin número `S`** y cero menciones de `SEAMS` en todo el archivo — la peor
  proporción de los once pares. **Corregido y CERRADO en la misma ventana**: `SEAMS` numera `S32`-`S38` (índice
  `29→36`, `ENMIENDA A-CIERRE.MCP`) y registra los dos cables inversos (`S23`, `S25`). *(De las diez, dos no eran de
  11 —`CapabilityProvider` home 12, `ToolExecEnvironment` = `S15`— y la décima es el consumidor de `S23`.)*
- **`S25:438` delegaba `mcp_servers→11` y 11 no lo recibía** ⇒ `CG-MCP-21` **creado** (DR-2, re-verificable en P6″).
- **Cuatro grafías para una costura**, una de ellas (`user_id=`) **violando el invariante `【id-opaco】`** de
  `SEAMS:16-17` ⇒ firma unificada a `RuntimeHost.scope` (OI-MCP-A).
- **Tres pérdidas de contenido restituidas**: `search_hint` (CG-MCP-2), truncado 2048 + sanitización unicode
  (CG-MCP-6), `_meta` del lado llamada (CG-MCP-5) — las dos primeras esperadas por `SEAMS §S16` como *A CRECER*.
- **Un menor plegado mal ruteado** (`regex`/reservados de `addMcpConfig`: `CG-MCP-13`→`CG-MCP-11`+`CG-MCP-1`).
- **Dos inversiones aguas arriba corregidas**: `NativeToolRegistry` re-alineado con `DB-05` (incondicional; aquí
  estaba condicionado) y `pending_servers()` reconocido como `DB-28` (aquí, «nota, no ítem»).
- **Tres cifras no medidas**: `1→799` sobre 798 · ledger 63 con 8 entradas contadas como 3 · `officialRegistry.ts`
  95 declaradas / **72** reales.
- **Frase revocada que seguía viajando**: la «A no re-leído» de Q3/§3.3, refutada por el propio tracker `:734-781`.
- **`H-3` — RECHAZADO expresamente.** No aterriza en 11: su home es **05**. Se deja constancia para que la próxima
  pasada no vuelva a plantearlo (`L07`: fuera de alcance se nombra, no se silencia ni se adopta).
- **Lo que se sostuvo tal cual (L10, doble filo):** las 27 fichas originales cuadran 27=27; los 9 cabos entrantes
  estaban todos reconocidos; el namespace está **íntegramente prefijado** (único par sin colisión de IDs); las dos
  baterías declaradas (`battery_mcp`=B12, `battery_mcp_skills`=B14) **existen** en `BATTERIES`; y el bug
  multi-usuario de §0.1 llegó **entero y acreditado en el ensamblador**, no por docstring.

### 3.4 VEREDICTO
**🟡 RECONCILIADO Y REMEDIADO — con dos pendientes que NO se cierran desde este archivo.** El `✅ NADA PENDIENTE`
anterior queda **degradado** (`§16.7`, consecuencia 47): era **auto-refutable**, porque el propio gate `§3.2·Q3`
declaraba una fuente sin leer mientras `§3.4` firmaba que no había pendientes — y encima esa declaración ya era
falsa. Estado real tras la remediación:
- **28 vinculantes** repartidos por TIER+destino (CG-MCP-1..**21**, sin-colocar = 0); 25 MCP-OK + **10** MCP-NA
  colocados; **8** entradas DEUDA-B (LAT-MCP1 borrar · NativeToolRegistry retirar **incondicionalmente** = `DB-05` ·
  `model` cablear|borrar · `pending_servers` conservar = `DB-28` · LAT-TOOL1 · LAT-CAP1 no-aterriza ·
  `CapabilitySummary.deferred` · `compact_context/active_context`); cabo b unificado (CG-MCP-16), cabo c resuelto;
  cara integrador simétrica (OI-MCP-A..I) con la firma corregida; ensamblador + CONTRATOS abiertos 1→EOF.
- **~~PENDIENTE 1~~ → PAGADO en la misma ventana (2026-07-30, `ENMIENDA A-CIERRE.MCP` en `SEAMS.md`).** Las siete
  costuras `[S-PEND]` son ahora **`S32`-`S38`** (índice `29→36`), con `S35`/`S36`/`S38` marcadas 【borde-seguridad】
  y `ausente`; los cables inversos `S23→CG-MCP-20` y `S25→CG-MCP-21` están escritos en sus fichas y en la matriz
  §4. *(No se declaró y se dejó para después: `D-07` — declarar no es pagar. Se pagó porque `SEAMS.md` estaba
  abierto 1→EOF en esta misma ventana; de no estarlo, no habría podido tocarse.)*
- **~~PENDIENTE 2 (en P6″, no aquí)~~ → PAGADO ENTERO el 2026-07-30, canónico abierto por excepción.** Decía:
  *«re-verificar en P6″ las dos incorporaciones DR-2»*. **Ninguna de las dos necesitaba esperar a P6″.**
  (a) El ruteo del gate de nombre: `config.ts` **1→EOF (1578 L)** y `officialRegistry.ts` **1→EOF (72 L)** ⇒
  `addMcpConfig:625-761` **confirma** admisión y `getMcpServerSignature:202` **confirma** que la firma de dedup no
  pasa por `add` ⇒ **T1, nada refutado**. (b) `CG-MCP-21`: `utils.ts` **1→EOF (575 L)** + censo de consumidores +
  `runAgent.ts` (973 L; `:1-240` y `:640-834` abiertos) ⇒ **la lectura SÍ refutó**: el ancla `extractAgentMcpServers`
  era la ruta de **pantalla**, la contraparte real es **`initializeAgentMcpServers:95-218`**, y la ficha se
  **reescribió a T1** con las dos formas de spec, el ciclo de vida asimétrico del cleanup, la fusión aditiva, el
  gate admin-trusted 【borde-seguridad】 y la degradación no fatal. **La dependencia declarada «orden: tras
  CG-MCP-1» quedó RETIRADA** por la misma lectura.
**Los dos pendientes de este par están en cero, y ninguno se cerró declarándolo: se cerró abriendo el canónico.**
La lección se paga cara y conviene escribirla: **el pendiente que parecía formal (a) se confirmó, y el que se dio
por menor (b) escondía un ancla equivocada.** Si `PENDIENTE 2` se hubiera «declarado» y remitido a P6″ como estaba
escrito, la ficha `CG-MCP-21` habría viajado con la mitad ciega del comportamiento hasta Fase B.
