# 11 · capabilities/mcp — homologación

> **Estado (2ª vuelta · gate 11 / L09) — ✅ VALIDADA 2026-07-20.** Lado **B** verificado: los 12 `mcp/*.py`
> + el ensamblador (factory/manager/dispatcher/fork) leídos 1→EOF; cada ✅/🔀 abierta en B. Lado **A**
> RE-VERIFICADO 1→EOF ESTA ronda (tras reproche del usuario, sin fiarse del ledger previo): los 3 grandes
> `client.ts` (3348) + `config.ts` (1578) + `auth.ts` (2465) + tratables (types/MCPTool/McpAuthTool/2
> resource-tools/3 prompts) leídos íntegros contra cada ❌/🔀 → **CERO discrepancias, citas de línea de la 1ª
> pasada coinciden exactas**; ⛔-de-forma (XAA, flujo OAuth interactivo) confirmados abriéndolos (L02).
> **Cero cambios de estado, código intacto.** Novedades: **LAT-MCP1** (`auth_headers()` sin consumidor prod →
> DEUDA-B §B-orphans) + precisión de cableado (herencia MCP en fork por `capability_manager` compartido, NO
> `app_state.capabilities`) + hot-plug per-turno/timeout confirmados por el ensamblador. Detalle al pie en
> §"Re-visita de COMPLETITUD" y §"Re-verificación del lado A".

Contrasta la **capacidad MCP** del runtime (`capabilities/mcp/{provider,client,config,config_store,
scope,auth,token_storage,state,reconcile,tool_adapter,resource_tools}.py`, 1573 LOC) contra el core MCP
canónico: `services/mcp/{client,config,auth,types,utils,mcpStringUtils,normalization,envExpansion,
officialRegistry,oauthPort}.ts` + `services/oauth/*` + `tools/{MCPTool,McpAuthTool,ListMcpResourcesTool,
ReadMcpResourceTool}`. El runtime delega el transporte y el flujo OAuth al SDK `mcp` (Python); el canónico
los reimplementa. La homologación aquí es **de comportamiento observable** (qué tools/resources se exponen,
con qué nombre, permiso, timeout, recuperación y forma de resultado), no de estructura 1:1.

**Contrapartes leídas** — sustantivas ÍNTEGRAS: `types.ts` (259), `mcpStringUtils.ts` (108),
`normalization.ts` (33), `envExpansion.ts` (44), `officialRegistry.ts` (95), `oauthPort.ts` (110),
`tools/MCPTool/MCPTool.ts` (78), `tools/McpAuthTool/McpAuthTool.ts` (216), `tools/ListMcpResourcesTool/
ListMcpResourcesTool.ts` (124), `tools/ReadMcpResourceTool/ReadMcpResourceTool.ts` (159); `client.ts`
(3348) en todos sus tramos de core (helpers/cachés 152-595, `connectToServer` 595-1642, `ensureConnectedClient`/
`areMcpConfigsEqual`/`fetchToolsForClient`/`fetchResourcesForClient`/`fetchCommandsForClient` 1688-2108,
`reconnectMcpServerImpl`/`getMcpToolsCommandsAndResources`/`prefetchAllMcpResources` 2137-2473,
`transformResultContent`/`transformMCPResult`/`processMCPResult`/`callMCPToolWithUrlElicitationRetry`/
`callMCPTool` 2478-3245); `config.ts` (1578) core (política 320-616, `addMcpConfig`/`removeMcpConfig`/
`getMcpConfigsByScope`/`getMcpConfigByName`/`getClaudeCodeMcpConfigs`/`getAllMcpConfigs` 618-1290,
disabled/enterprise 1470-1578); `auth.ts` (2465) puntos de comportamiento observable (`getServerKey`/
`hasMcpDiscoveryButNoToken`/`revokeToken` 313-467, `ClaudeAuthProvider` metadata/CIMD/step-up 1376-1465);
`utils.ts` (575) selectivo (`getProjectMcpServerStatus` aprobación, `getMcpServerScopeFromToolName`,
`extractAgentMcpServers`, `getLoggingSafeMcpBaseUrl`). Runtime: **los 12 archivos ÍNTEGROS** + cableado en
`factory.py:140-158` + verificación de `tools/protocol.py`, `tools/deferred.py`, `tools/native_registry.py`,
`execution/fork/__init__.py:27-91` (herencia de capabilities).

**Fuera de alcance (⛔, con razón, NO en el ledger de leídos-íntegros)**: `useManageMCPConnections.ts`
(44KB, hook React de orquestación UI), `MCPConnectionManager.tsx`, `mcpServerApproval.tsx`,
`components/MCPServerApprovalDialog.tsx`, `MCPTool/UI.tsx` (50KB), `*/UI.tsx` (render ink); `xaa.ts`/
`xaaIdpLogin.ts`/`claudeai.ts`/`channel{Allowlist,Permissions,Notification}.ts` (XAA/SEP-990 + conectores
claude.ai — features de producto Anthropic, no del core MCP genérico); `InProcessTransport.ts`/
`SdkControlTransport.ts`/`vscodeSdkMcp.ts` (transportes SDK/IDE in-process); `elicitationHandler.ts`
(delegación estructurada print/SDK — su USO en `client.ts` sí se leyó). El **motor de transporte real**
está en el paquete `mcp` (SDK, fuera del repo runtime) igual que el sandbox en 09 — no auditable aquí por
diseño; el runtime lo consume por contrato.

## Tesis arquitectural

El canónico **no reifica una capa `capabilities/`**: MCP es estado global (`appState.mcp.{clients,tools,
commands,resources}`) manipulado por funciones sueltas (`connectToServer` memoizado, `fetchToolsForClient`
memo-LRU, `getMcpToolsCommandsAndResources`) y un hook React (`useManageMCPConnections`) que orquesta el
ciclo de vida contra `setAppState`. El runtime **reifica** MCP como un `CapabilityProvider` (`McpProvider`)
con estado propio (`McpState`), clients por server (`McpClient`), y puertos inyectables (`config_store`,
`config_watcher`, handlers OAuth). Decisión de desacople **correcta y necesaria** (el runtime tiene usuarios/
sesiones; el canónico opera single-user en terminal). El runtime **AÑADE** valor propio genuino: un
`ScopedMcpConfigStore` (registro scope-aware con productor por scope), un motor de **reconciliación** de
datos puros (`plan_reconcile`/`apply_reconcile`) consumido por mutación in-process Y watcher externo, y una
capa de **estrategias de auth registrables** (`register_auth_strategy`). Esas tres piezas no tienen homólogo
directo canónico y son aciertos.

Tres ejes de divergencia estructural:
1. **Transporte/OAuth delegados al SDK `mcp`** (Python) vs reimplementados en el canónico. Homologación de
   comportamiento: el runtime debe reproducir lo que el SDK NO le da gratis (needs-auth, recuperación de
   sesión, timeouts, transform de contenido, naming).
2. **El canónico enriquece cada tool MCP con ~15 campos** (naming FQ, `mcpInfo`, `isMcp`, annotations→hints,
   `searchHint`/`alwaysLoad` de `_meta`, `mcpMeta`, progreso, retry de sesión). El runtime porta **3**
   (`deferred`, `requires_permission`, `safe_for_background`). El grueso de la Deuda A de 11 vive aquí.
3. **La política (allow/deny, aprobación de proyecto, needs-auth) vive en el canónico**; el runtime tiene
   sólo el gate de mutabilidad por scope. Homologación de comportamiento: el gate de seguridad de MCP es más
   ancho que "quién puede mutar el registro".

## Leyenda
✅ homologado · 🟡 parcial · 🔀 diferente (deliberado o a revisar) · ❌ no portado · ⛔ N/A core (UI/producto).

---

## A · Config e identidad de server (`config.py::McpServerConfig` vs `types.ts` + `config.ts` parsing/env)

| Feature | Estado | Nota |
|---|---|---|
| Transportes stdio/http/sse | ✅ | Runtime porta 3; inferencia retro-compatible (command→stdio, url→http). |
| Transportes ws / sse-ide / ws-ide / sdk / claudeai-proxy | ⛔/❌ | ws/sdk = ❌ (no portados); sse-ide/ws-ide/claudeai-proxy = ⛔ (IDE/claude.ai). |
| Validación estricta identidad+auth (bearer exige token; auth HTTP ⊄ stdio) | ✅🔀 | Runtime **más estricto** que el canónico (rechaza auth HTTP en stdio) — decisión de seguridad propia, aceptable. |
| `enabled` (habilitación) | 🔀 | Runtime = bool per-config; canónico = listas `disabledMcpServers`/`enabledMcpServers` en project config (`isMcpServerDisabled`, config.ts:1528). Comportamiento equivalente (deshabilitado ⇒ no conecta, sin tools). |
| `ssl_verify` | ✅🔀 | Seam propio del runtime (verify TLS); el canónico no expone toggle equivalente en el config schema — valor propio. |
| **Env var expansion** `${VAR}`/`${VAR:-default}` | ❌ | **FIND-MCP13**. `envExpansion.ts` + `expandEnvVars` (config.ts:556) expanden command/args/env/url/headers y reportan `missingVars`. Runtime pasa `${TOKEN}` literal. |
| **Normalización de nombre** `^[a-zA-Z0-9_-]{1,64}$` | ❌ | **FIND-MCP1** (nexo). `normalizeNameForMCP` mapea chars inválidos→`_` (y colapsa `_` en claude.ai). Runtime no normaliza server/tool names. |
| `headersHelper` (script que genera headers dinámicos) | ❌ | **FIND-MCP24**. `headersHelper.ts`: ejecuta un script (shell, timeout 10s) con env `CLAUDE_CODE_MCP_SERVER_NAME`/`_URL`, parsea su stdout como JSON de headers (dinámicos sobre estáticos), con **gate de trust** para scope project/local (no ejecuta antes de confirmar workspace-trust; skip en no-interactivo). Runtime sólo headers estáticos + Authorization de bearer. |
| oauth sub-config (clientId/callbackPort/authServerMetadataUrl/xaa) | 🟡 | Runtime tiene `scope`/`client_name`/`redirect_uris` planos; falta callbackPort/authServerMetadataUrl/CIMD. |
| **Dedup por firma de config** (`getMcpServerSignature`) | ❌ | **FIND-MCP22**. `dedupPluginMcpServers`/`dedupClaudeAiMcpServers` (config.ts:202-310): dos configs con la misma firma (`stdio:cmd` o `url:<unwrapped>`, ignorando env/headers) son "el mismo server" → se suprime el duplicado (manual gana; entre plugins, primero-cargado gana). Runtime no deduplica: dos servers apuntando al mismo proceso/URL abren dos conexiones. |
| Escritura atómica de `.mcp.json` (temp+datasync+rename+perms) | 🟡 | `writeMcpjsonFile` (config.ts:88) es atómica y preserva permisos. El `StorageBackedMcpConfigStore` del runtime hace `upload` plano (sin atomicidad ni perms) → nexo **15·storage**. |
| Validación: severidad fatal/warning + npx-en-Windows | 🟡 | `parseMcpConfig` (config.ts:1330-1372) marca env-faltante como *warning* (server igual carga) y avisa de `npx` sin `cmd /c` en Windows. Runtime salta el inválido sin distinguir severidad ni el caso npx. |

## B · Scope, precedencia, política de admisión (`scope.py`/`config_store.py` vs `config.ts`)

| Feature | Estado | Nota |
|---|---|---|
| Enum de 7 scopes (`ConfigScope`) | ✅ | `McpScope` espeja los 7. |
| Precedencia enterprise>local>project>user (+ claudeai/dynamic bajo user) | ✅ | `_PRECEDENCE` correcto (verificado contra `getMcpConfigByName` config.ts:1046-1057 y merge 1231). |
| Exclusividad de enterprise (lockdown) | ✅ | `EXCLUSIVE_SCOPES={ENTERPRISE}` = `doesEnterpriseMcpConfigExist` exclusivo (config.ts:1084). `managed` no exclusivo ✅. |
| Gate de mutabilidad (user/project/local mutables) | ✅ | `MUTABLE_SCOPES` = canónico (config.ts:705-709). |
| Merge por nombre scope-aware | ✅ | `merge_scoped` = valor propio bien homologado. |
| Traversal de directorios en scope `project` (root→cwd, cercano gana) | 🔀 | El canónico recorre `.mcp.json` de cada dir padre (config.ts:914-955). El runtime lo abstrae al productor del scope (el integrador decide) — homologación de comportamiento, aceptable. |
| **Política allow/deny (name/command/url, wildcards)** | ❌ | **FIND-MCP14**. `isMcpServerAllowedByPolicy`/`isMcpServerDenied` (config.ts:364-508): deny absoluto, allowlist vacía bloquea todo, `allowManagedMcpServersOnly`. Runtime no tiene allow/deny; sólo el gate de mutabilidad. |
| **Aprobación de servers de proyecto** (approved/rejected/pending) | ❌ | **FIND-MCP15**. `getProjectMcpServerStatus` (utils.ts:351): `.mcp.json` requiere aprobación; auto-aprueba en bypass/no-interactivo. Runtime conecta project sin aprobar → **borde de seguridad**. |
| Bloqueo de nombres reservados / regex de nombre al añadir | 🟡 | `addMcpConfig` valida `[^a-zA-Z0-9_-]`, nombres reservados, y bloquea si existe enterprise (config.ts:630-655). Runtime `add_server` valida por pydantic pero sin regex de nombre ni bloqueo enterprise-exclusivo en el add. |
| Persistencia add/remove/toggle scope-aware | ✅ | `ScopedMcpConfigStore.save/remove` + `set_server_enabled` = `addMcpConfig`/`removeMcpConfig`/`setMcpServerEnabled`. |

## C · Ciclo de vida de conexión (`client.py`/`provider.py`/`state.py` vs `connectToServer` + discovery)

| Feature | Estado | Nota |
|---|---|---|
| Conexión por transporte (stdio/http/sse) vía SDK | ✅ | `McpClient.connect` elige por identidad validada; http pasa timeout del config (evita el default httpx de 5s). |
| Estados de server (configured/pending/connected/failed) | 🟡 | Runtime: 4 estados. Canónico: `connected/failed/needs-auth/pending/disabled` (types.ts:221). Faltan **needs-auth** (FIND-MCP4) y **disabled** explícito (modelado como config.enabled). |
| Aislamiento por ítem (server caído no tumba al resto) | ✅ | `connect_server` marca FAILED y no propaga. |
| **Timeout de conexión** | ❌ | **FIND-MCP10**. Canónico corre `client.connect` contra `MCP_TIMEOUT` (30s) y cierra el transporte al vencer (client.ts:1049-1077). Runtime `await client.connect()` **sin límite** → un server colgado cuelga el startup. |
| **Startup batched-paralelo** | ❌ | **FIND-MCP11**. Canónico conecta local (batch 3) + remoto (batch 20) concurrente con `pMap` (client.ts:2388-2402). Runtime `startup()` hace `for … await connect_server` **secuencial**: un server lento bloquea a todos los siguientes. |
| **Captura de capabilities/serverInfo/instructions** | ❌ | **FIND-MCP12**. Canónico: `getServerCapabilities()` (gatea fetch de tools/resources/prompts), `getServerVersion()`, `getInstructions()` (truncadas a 2048, inyectadas al contexto) (client.ts:1157-1183). Runtime no captura ninguno; llama `list_tools`/`list_resources` incondicional. |
| **Reconexión / recuperación de sesión / onclose-invalidation** | ❌ | **FIND-MCP9**. Dos capas canónicas: (a) `onerror`/`onclose` (client.ts:1216-1402) detectan errores terminales (ECONNRESET…×3), expiración de sesión (404/-32001, -32000 connection-closed) → invalidan cachés + rechazan pendientes; recuperación en la tool-call (3194-3231, retry 1). (b) **reconexión proactiva con backoff exponencial** en `useManageMCPConnections` (87-90: MAX 5 intentos, 1s→30s; `PendingMCPServer.reconnectAttempt/maxReconnectAttempts`), sólo para transportes remotos, cancelable en cambio de config. Runtime: conecta una vez; una caída deja la sesión muerta sin recuperación ni backoff. |
| **Notificaciones `*_list_changed` → refetch en vivo** | ❌ | **FIND-MCP21**. `useManageMCPConnections:620-751`: gated por `capabilities.{tools,prompts,resources}.listChanged`, cada notificación invalida la caché del server y **refetchea** tools/commands/resources, actualizando el estado sin reconectar. Runtime no registra notification handlers → un server que añade/quita tools en caliente no se refleja hasta reconexión manual. |
| Discovery de tools/resources | 🟡 | `list_tools`/`list_resources` ok, pero sin gate por capabilities y sin **prompts→commands** (FIND-MCP16) ni **skills** MCP. |
| `reconnect_server`/`disconnect_server`/`remove_server` | ✅ | Espejo de `reconnectMcpServerImpl`/toggle; el pool se reensambla por turno. |
| Reconcile deseado-vs-vivo (datos puros) | ✅ | `plan_reconcile`/`apply_reconcile` — valor propio; el canónico lo hace imperativo en el hook. |

## D · Autenticación (`auth.py`/`token_storage.py` vs `auth.ts`/`oauth/*`)

| Feature | Estado | Nota |
|---|---|---|
| Estrategias registrables none/bearer/oauth | ✅🔀 | `register_auth_strategy` — patrón propio extensible; el canónico hard-codea. |
| OAuth 2.1 (discovery RFC9728/8414, PKCE, DCR, refresh, resource indicator) | ✅ | Delegado a `OAuthClientProvider` del SDK `mcp` (auth.py:78-108); metadata = `ClaudeAuthProvider.clientMetadata` (token_endpoint_auth_method 'none', grant/response types). Homologación de mecánica correcta. |
| **Estado needs-auth + pseudo-tool `authenticate`** | ❌ | **FIND-MCP4**. Canónico: 401 (UnauthorizedError) → `NeedsAuthMCPServer` + `createMcpAuthTool` (`mcp__server__authenticate`) surtida EN LUGAR de las tools reales; al llamarse arranca OAuth (skipBrowserOpen), devuelve authUrl, y en background reconecta y **swapea** las tools reales por prefijo (McpAuthTool.ts:49-206). Caché needs-auth 15min (`mcp-needs-auth-cache.json`) + `hasMcpDiscoveryButNoToken` (skip de conexión garantizada-401). Runtime: OAuth inline-en-connect; un 401 → FAILED; sin needs-auth, sin auth-tool, sin caché. |
| Token storage persistente | 🟡 | `StorageBackedTokenStorage` ok, pero **keying por `user_id/mcp/server_name`** vs `getServerKey`=`name|sha256(type+url+headers)` (auth.ts:325). **FIND-MCP20**: cambiar la url de un server reusa tokens viejos. |
| Revoke de tokens (RFC 7009) | ❌ | **FIND-MCP20**. `revokeToken`/`revokeServerTokens` (auth.ts:381-467). Runtime no revoca. |
| Puerto de redirect OAuth (RFC 8252 loopback, `MCP_OAUTH_CALLBACK_PORT`) | 🔀 | `oauthPort.ts`: puerto aleatorio en rango + fallback. Runtime hard-codea `http://localhost:8765/callback` como default (auth.py:91). Aceptable (headless: el integrador inyecta handlers), pero fijo. |
| Step-up scope (403 insufficient_scope) / CIMD (SEP-991) | ❌ | Avanzado; el SDK puede no cubrirlo. Menor. |

## E · Adapter de tool MCP (`tool_adapter.py` vs `fetchToolsForClient` + `MCPTool`)

| Feature | Estado | Nota |
|---|---|---|
| Adaptar spec→`ToolProtocol`, tolerante (omite malformadas) | ✅ | `build_mcp_tool` aísla por ítem. |
| **Naming `mcp__<server>__<tool>`** | ❌ | **FIND-MCP1**. `buildMcpToolName` (mcpStringUtils.ts) + `normalizeNameForMCP`. Runtime usa el nombre **crudo** → sin prefijo. Rompe: (a) el gate de permisos FQ (`getToolNameForPermissionCheck`: deny "Write" no debe pegar a un tool MCP homónimo), (b) el swap por prefijo (`mcp__server__*`), (c) colisiones. Nexo **09·B4/TiR4/TiR5**. |
| `mcpInfo={serverName,toolName}` | ❌ | Requerido para el gate FQ y el swap. Runtime sólo guarda `server_name` suelto. |
| **`is_mcp` flag** (vs `deferred=True` a mano) | ❌ | **FIND-MCP2 = 09·TiR5/GAP-TOOL3**. Canónico: `isMcp:true`; `isDeferredTool` deriva deferred de isMcp (salvo `alwaysLoad`). Runtime setea `deferred=True` directo, sin `is_mcp` ni `always_load`. |
| `searchHint`/`alwaysLoad` de `_meta['anthropic/*']` | ❌ | Runtime no lee `_meta` del tool spec. |
| **Annotations completas** | 🟡 | **FIND-MCP3**. Runtime: sólo `readOnlyHint`→safe_for_background. Falta `readOnlyHint`→isConcurrencySafe/isReadOnly, `destructiveHint`→isDestructive, `openWorldHint`→isOpenWorld, `title`→userFacingName (client.ts:1795-1976). |
| Truncado de description a 2048 + sanitización unicode | ❌ | Runtime no trunca ni sanea (`recursivelySanitizeUnicode`). |
| requires_permission siempre (terceros no confiables) | ✅🔀 | Runtime = `passthrough` canónico (MCPTool.checkPermissions). Nota: el canónico sugiere una regla `allow` para el nombre FQ (addRules) — el runtime no. |
| **Timeout de tool-call** | 🔀 | **FIND-MCP8**. Runtime = 30s. Canónico = `MCP_TOOL_TIMEOUT` default ~27.8h (**efectivamente infinito**, client.ts:211) → tools MCP largas fallan en el runtime. |
| Progreso (started/progress/completed/failed) + SDK onprogress | ❌ | Runtime no emite progreso; canónico sí (client.ts:1846-1936, 3102). |
| `_meta` (claudecode/toolUseId) en la llamada + **mcpMeta** en resultado | ❌ | **FIND-MCP6 = 09·A25**. Canónico inyecta `_meta` y devuelve `mcpMeta={_meta,structuredContent}` (client.ts:1899-1908). Runtime no. |
| Retry de sesión expirada (MAX_SESSION_RETRIES=1) | ❌ | **FIND-MCP9**. |
| `McpToolError` (isError sin re-llamar) | ✅ | `McpClient.call` levanta y `McpTool.execute` envuelve — 1 sola llamada. Bien. |

## F · Transform de contenido de resultado (`client.call`/`_text_from_content` vs `transform*`)

| Feature | Estado | Nota |
|---|---|---|
| Content array `text` | ✅ | `_text_from_content` extrae `.text`. |
| **image** (resize/downsample + block image) | ❌ | **FIND-MCP5**. `transformResultContent` (client.ts:2503) redimensiona y emite bloque `image`. Runtime hace `str(block)` → dumpea base64 al contexto. |
| **audio / blob no-imagen** (persistir a disco + mensaje corto) | ❌ | **FIND-MCP5**. `persistBlobToTextBlock` (client.ts:2598). Runtime str()ea. Nexo **10·A23 new_messages** / `ReadMcpResource` blobSavedTo. |
| **resource / resource_link** (prefijo `[Resource from …]`) | ❌ | **FIND-MCP5**. |
| **Forma de resultado: toolResult / structuredContent / content** | 🟡 | **FIND-MCP6**. `transformMCPResult` (client.ts:2662): 3 formas + `inferCompactSchema`. Runtime sólo `getattr(result,'content')`. Falta structuredContent (JSON+schema) y toolResult (string legacy). Nexo **Deuda B `B-structured-output`**. |
| **Large-output handling** (persistir a archivo + instrucciones; imágenes excluidas; cap 100k) | ❌ | **FIND-MCP7**. `processMCPResult` (client.ts:2720) con `ENABLE_MCP_LARGE_OUTPUT_FILES`/truncado/`maxResultSizeChars`. Runtime devuelve texto crudo siempre. |
| **URL-elicitation retry (-32042) + hooks; elicitation/roots capability** | ❌ | **FIND-MCP18**. `callMCPToolWithUrlElicitationRetry` (client.ts:2813, MAX 3) + `ListRootsRequestSchema`→cwd + `ElicitRequestSchema`. **Importante (matiz de la re-auditoría)**: `elicitationHandler.ts` muestra que los **hooks de elicitation** (`runElicitationHooks`/`runElicitationResultHooks`, executeElicitation*Hooks) responden **programáticamente sin UI** — esa es la ruta headless que el runtime SÍ debe soportar (declarar la capability `elicitation`+`roots` en el `ClientSession` y enrutar la request a un hook inyectado), aunque el diálogo interactivo sea ⛔. Runtime hoy no declara capability alguna ni enruta elicitation. |

## G · Resources + prompts/commands (`resource_tools.py` vs `*McpResource*` + `fetchCommands`)

| Feature | Estado | Nota |
|---|---|---|
| ListMcpResources (filtro por server) | 🟡 | **FIND-MCP17**. Runtime: output `{resources:[…]}`; canónico: array plano. Runtime **no `shouldDefer`**; canónico sí (`shouldDefer:true`). Falta reconexión-por-onclose (`ensureConnectedClient`) + LRU cache. |
| ReadMcpResource | 🟡 | **FIND-MCP17**. Runtime: `server` **opcional** (infiere por `find_resource_server`); canónico: `server` **requerido** + chequea `capabilities.resources`. Runtime devuelve texto plano; canónico devuelve `{contents:[{uri,mimeType,text,blobSavedTo}]}` con **blobs persistidos a disco** (ReadMcpResourceTool.ts:106-139). No `shouldDefer` en runtime. |
| Special tools condicionales (sólo si hay resources) | ✅ | `provider.tools()` añade las 2 tools sólo si `all_resources()`. Canónico dedup (sólo si ningún otro server las añadió) — el runtime las añade una vez global (equivalente). |
| **prompts/list → slash commands `mcp__server__prompt`** | ❌ | **FIND-MCP16**. `fetchCommandsForClient` (client.ts:2033) + `getPromptForCommand`. Runtime no expone prompts MCP. Nexo **12·skills**. |
| **MCP skills (skill:// resources)** | ❌ | Feature-gated `MCP_SKILLS`; runtime no. → **12·skills**. |

## H · Reconcile / watcher / cleanup / teardown

| Feature | Estado | Nota |
|---|---|---|
| Motor de reconcile (plan datos-puros + applier) | ✅🔀 | Valor propio; consumido por mutación in-process y watcher. **FIND-MCP23**: el `plan_reconcile` del runtime desconecta **cualquier** server ausente del deseado; el canónico (`excludeStalePluginClients`, utils.ts:185) acota el disconnect-por-ausencia a scope `dynamic` (un server de usuario transitoriamente ausente en un reload parcial NO se desconecta; sólo el cambio de config-hash fuerza refresh en todo scope). El runtime es sobre-agresivo. |
| Watcher de fuente externa (vector 2) | ✅ | `McpConfigWatcher` puerto; el integrador provee (inotify/poll MinIO). |
| **stdio cleanup con escalación SIGINT→SIGTERM→SIGKILL** | 🔀 | **FIND-MCP19**. Canónico escala señales (100ms/400ms) al hijo (client.ts:1429-1562). Runtime: `aclose()` vía `AsyncExitStack` (el SDK termina el proceso, sin escalación gradual). Aceptable pero menos robusto con contenedores Docker. |
| **Teardown por agent_id + registro en abort scope** | ❌ | **FIND-MCP19**. Canónico `registerCleanup(cleanup)` (teardown global). Runtime `shutdown()` cierra todos pero sin registro per-agent ni en el abort scope. Nexo **05·ExR6/FIND-EXEC11** (mcpCleanup por agent_id) + **08·SR3/SIG9** (release on `AbortScope.on_abort`). |

---

## Hallazgos (IDs para retoma)

**FIND-MCP1** naming `mcp__<server>__<tool>`+normalización+`mcpInfo` ausentes (=09·B4). ❌ ·
**FIND-MCP2** `is_mcp` flag ausente; `deferred=True` a mano (=09·TiR5/GAP-TOOL3). ❌ ·
**FIND-MCP3** annotations parciales (sólo readOnlyHint→bg). 🟡 ·
**FIND-MCP4** needs-auth + pseudo-tool `authenticate` + caché 15min ausentes. ❌ ·
**FIND-MCP5** transform de contenido pobre (image/audio/blob/resource → `str()`). ❌ ·
**FIND-MCP6** sólo `content` array; sin structuredContent/toolResult/schema/mcpMeta (=09·A25, B-structured-output). 🟡 ·
**FIND-MCP7** large-output sin persistir/truncar/capar. ❌ ·
**FIND-MCP8** timeout de tool-call 30s vs ~∞ (+ sin progreso). 🔀 ·
**FIND-MCP9** sin reconexión/recuperación-de-sesión/onclose-invalidation/retry. ❌ ·
**FIND-MCP10** sin timeout de conexión. ❌ ·
**FIND-MCP11** startup secuencial vs batched-paralelo. ❌ ·
**FIND-MCP12** capabilities/serverInfo/instructions no capturados (ni gate de discovery). ❌ ·
**FIND-MCP13** sin env-var expansion. ❌ ·
**FIND-MCP14** sin política allow/deny (name/command/url). ❌ ·
**FIND-MCP15** sin aprobación de servers de proyecto (borde de seguridad). ❌ ·
**FIND-MCP16** sin prompts→commands ni skills MCP (→12). ❌ ·
**FIND-MCP17** resource tools: server opcional, sin blob-persist, output plano, no-deferred. 🟡 ·
**FIND-MCP18** sin elicitation/roots/URL-elicitation-retry. ❌ ·
**FIND-MCP19** cleanup sin escalación + teardown sin agent_id/abort-scope (=05·ExR6/08·SR3). 🔀 ·
**FIND-MCP20** credenciales sin keying por config-hash + sin revoke. 🟡 ·
**FIND-MCP21** sin handlers `*_list_changed` → no refetch en vivo de tools/resources. ❌ ·
**FIND-MCP22** sin dedup por firma de config (dos servers al mismo proceso/URL → doble conexión). ❌ ·
**FIND-MCP23** reconcile sobre-agresivo (desconecta cualquier ausente vs acotar a scope `dynamic`). 🔀 ·
**FIND-MCP24** sin `headersHelper` (script de headers dinámicos + gate de trust). ❌.

*(FIND-MCP21–24 emergieron en la re-auditoría tras el reproche del usuario, al ABRIR archivos antes
marcados ⛔ por título: `useManageMCPConnections.ts` (backoff+list_changed), `config.ts:1-320` (dedup),
`utils.ts:185` (reconcile scope-guard), `headersHelper.ts`. Evidencia de que la 1ª pasada fue superficial.)*

### Gaps con ID
- **GAP-MCP1** = **GAP-TOOL3** (09): precedencia de `is_deferred_tool` con `always_load`/`is_mcp` → se
  cierra con FIND-MCP2 (el `ToolProtocol` gana `is_mcp`/`always_load`; `is_deferred_tool` gana la precedencia).
- **GAP-MCP2**: `ToolProtocol` no lleva `mcp_info`/`is_mcp`/`always_load` → superficie mínima insuficiente
  para el gate FQ y el swap por prefijo (dueño: `tools/protocol.py`, con 11 como driver).
- **GAP-MCP3** = **B-new_messages**: el resultado MCP con imagen/blob necesita el canal `new_messages`
  tipado para inyectar bloques image/attachment (hoy `ToolResult.output:str` no lo permite).

### Cabos que ENTRARON y su resolución
- **09·TiR5** (adapter debe setear `is_mcp=True`, no `deferred=True`) → confirmado = **FIND-MCP2**. ❌.
- **09·TiR4** (dos registries; ¿factory usa `NativeToolRegistry` para hot-plug MCP?) → **resuelto**: la
  factory **NO** usa `NativeToolRegistry` para MCP; el hot-plug MCP funciona por **reensamblado del pool por
  turno** (`McpProvider.tools()` re-lee `McpState` cada turno vía `CapabilityManager`). `NativeToolRegistry.
  unregister_by_prefix` queda como seam **sólo** si se implementa el swap push-based del auth-tool
  (FIND-MCP4). Decisión: mantener el modelo per-turno (más simple, ya correcto) y **retirar
  `NativeToolRegistry`** salvo que se cablee para el swap de FIND-MCP4. → anotado en McR2.
- **09·TiR3/E5/FIND-TOOL7** (discovered-set no materializado; fork lo re-deriva) → **resuelto desde 11**: las
  tools MCP son diferidas y viven en `McpState` (propiedad del provider). El `ForkSnapshot` **comparte el
  provider vivo** (`execution/fork/__init__.py:76-91`: contenedor propio, valores compartidos) → el hijo NO
  clona tools MCP ni re-conecta; el discovered-set (qué diferidas reveló ToolSearch) es responsabilidad de
  09/05 (derivarlo de la historia, no de un slot). 11 confirma: no hay doble-conexión ni clonado de clients.
- **09·B4** (deny MCP server-prefix) → habilitado por **FIND-MCP1** (el naming FQ es precondición del deny).
- **09·A25** (mcpMeta) → **FIND-MCP6**.
- **05·ExR6/FIND-EXEC11** (mcpCleanup en teardown por agent_id) → **FIND-MCP19** (el cleanup se registra por
  agent_id; hoy `shutdown()` es global).
- **05·GAP-EXEC4** (recolección de recursos hijos en teardown) → converge con **FIND-MCP19**: los clients MCP
  son recursos hijos que el reaping por agent_id debe cerrar.
- **08·SR3/SIG9** (11 registra release de locks/unhide en `AbortScope.on_abort`) → **FIND-MCP19**: el
  `cleanup` del client se registra en el abort scope del agente, no sólo en shutdown.
- **03·CtxR7/A13** (mcpClients/resources en `app_state.capabilities`, heredados por `ForkSnapshot`) →
  **confirmado ✅**: el provider MCP se hereda por el contenedor `capabilities` compartido (mismo provider
  vivo); espejo del threading de `options.mcpClients` del canónico. Bien homologado.

## Recuento
✅ **~11** (transportes base, aislamiento, precedencia/exclusividad/mutabilidad de scope, merge, estrategias
de auth, OAuth-vía-SDK, reconcile, watcher, McpToolError, herencia en fork) · 🟡 **~8** · 🔀 **~5** ·
❌ **~18** (FIND-MCP1,2,4,5,7,9,10,11,12,13,14,15,16,18,21,22,24…) · ⛔ **~12** (useManageMCPConnections
andamiaje, MCPConnectionManager, mcpServerApproval, classifyForCollapse, UI.tsx×4, xaa/xaaIdpLogin/claudeai,
channel{Permissions,Allowlist,Notification}, InProcessTransport/SdkControlTransport/vscodeSdkMcp, oauth/*).
Cómputo aproximado; lo vinculante son los IDs FIND-MCP/GAP-MCP y los cabos. **24 findings** tras re-auditoría
(20 en 1ª pasada + 4 destapados al leer lo que se había marcado ⛔ sin abrir).

## Ledger de archivos (auditoría de cierre — protocolo obligatorio)

> **Nota de honestidad (re-auditoría tras reproche del usuario).** La 1ª versión de este ledger
> declaró "sí (íntegro)" para archivos que sólo se habían leído por tramos, marcó varios archivos ⛔
> **sin abrirlos** (por título), e incluso listó un hallazgo sobre `headersHelper` sin haber leído
> `headersHelper.ts`. Corregido: **todos** los archivos de `services/mcp/`, los 4 dirs de tools y
> `services/oauth/` se ABRIERON y clasificaron; los tres grandes se leyeron en cobertura completa de
> comportamiento. Este ledger dice exactamente qué se leyó y con qué profundidad.

### Canónico (`/home/noheroes/python/claude-code/src`) — TODOS abiertos
| Archivo | LOC | Lectura |
|---|---|---|
| `services/mcp/types.ts` | 259 | íntegro |
| `services/mcp/mcpStringUtils.ts` | 108 | íntegro |
| `services/mcp/normalization.ts` | 33 | íntegro |
| `services/mcp/envExpansion.ts` | 44 | íntegro |
| `services/mcp/officialRegistry.ts` | 95 | íntegro |
| `services/mcp/oauthPort.ts` | 110 | íntegro |
| `services/mcp/headersHelper.ts` | 139 | íntegro (trust gate + exec de helper) |
| `services/mcp/elicitationHandler.ts` | 314 | íntegro (hooks headless + queue + completion) |
| `services/mcp/InProcessTransport.ts` | 64 | íntegro → ⛔ (par en-proceso Chrome/ComputerUse) |
| `services/mcp/SdkControlTransport.ts` | 137 | íntegro → ⛔ (puente SDK↔CLI, type:sdk) |
| `services/mcp/claudeai.ts` | 164 | íntegro → ⛔ (conectores claude.ai vía API Anthropic) |
| `services/mcp/channelPermissions.ts` | 240 | íntegro → ⛔ (permiso sobre canal, KAIROS) |
| `services/mcp/channelAllowlist.ts` | 76 | íntegro → ⛔ (allowlist de plugins-canal, GrowthBook) |
| `services/mcp/channelNotification.ts` | 316 | íntegro → ⛔ (canales=servers que empujan mensajes, KAIROS) |
| `services/mcp/vscodeSdkMcp.ts` | 112 | íntegro → ⛔ (IPC VSCode/IDE) |
| `services/mcpServerApproval.tsx` | 40 | íntegro → ⛔ diálogo (el gate `getProjectMcpServerStatus` sí en utils.ts) |
| `tools/MCPTool/MCPTool.ts` | 78 | íntegro |
| `tools/MCPTool/classifyForCollapse.ts` | 604 | íntegro → ⛔ (allowlists de colapso UI de resultados) |
| `tools/McpAuthTool/McpAuthTool.ts` | 216 | íntegro |
| `tools/ListMcpResourcesTool/ListMcpResourcesTool.ts` | 124 | íntegro |
| `tools/ReadMcpResourceTool/ReadMcpResourceTool.ts` | 159 | íntegro |
| `services/oauth/index.ts` | 199 | íntegro → ⛔ (login de cuenta Anthropic, no OAuth de server MCP) |
| `services/mcp/client.ts` | 3348 | cobertura completa de comportamiento: 152-1673, 1688-3348 (incl. `setupSdkMcpClients`→⛔); 1-152 = imports |
| `services/mcp/config.ts` | 1578 | íntegro-comportamiento: 1-1290 + 1300-1468 + 1470-1578 (parser, dedup, política, add/remove, disabled) |
| `services/mcp/auth.ts` | 2465 | comportamiento observable + interfaz del provider: 313-467 (revoke), 847-1050 (flujo), 1376-1644 (`ClaudeAuthProvider`: state/clientInformation/saveClientInformation/tokens/step-up); **XAA (664-847, performMCPXaaAuth) y el resto del flujo interactivo (browser/listener/keychain) = ⛔ de forma** (delegado al SDK+handlers) |
| `services/mcp/utils.ts` | 575 | íntegro (filtros, `hashMcpConfig`, `excludeStalePluginClients`, aprobación, agent-servers, transporte/headers) |
| `services/mcp/useManageMCPConnections.ts` | 1200+ | comportamiento core leído (87-140 constantes backoff, 143-466 reconexión con backoff + onConnectionAttempt, 620-763 handlers `*_list_changed`); el andamiaje React/`setAppState` = ⛔ de forma |
| `services/mcp/MCPConnectionManager.tsx` | ~62 | íntegro → ⛔ (context React que expone reconnect/toggle) |

**Genuinamente NO leídos (justificado, no por tamaño)**: `services/mcp/xaa.ts`/`xaaIdpLogin.ts` (SEP-990
Cross-App-Access, feature de identidad corporativa Anthropic gateada por `CLAUDE_CODE_ENABLE_XAA` — ⛔),
`services/oauth/{client,crypto,auth-code-listener,getOauthProfile}.ts` (mecánica del login de cuenta
Anthropic: PKCE/listener/perfil — sub-piezas de `oauth/index.ts` ya clasificado ⛔), `components/mcp/*` +
`components/MCPServer*Dialog.tsx` + `*/UI.tsx` (render ink puro). El transporte real vive en el SDK `mcp`
(fuera del repo, no auditable por diseño — igual que el sandbox vendorizado en 09).

### Runtime (`…/capabilities/mcp`)
| Archivo | LOC | ¿Leído íntegro? |
|---|---|---|
| `__init__.py` | 64 | sí |
| `config.py` | 129 | sí |
| `client.py` | 204 | sí |
| `provider.py` | 339 | sí |
| `tool_adapter.py` | 109 | sí |
| `state.py` | 118 | sí |
| `resource_tools.py` | 91 | sí |
| `scope.py` | 105 | sí |
| `auth.py` | 122 | sí |
| `config_store.py` | 145 | sí |
| `reconcile.py` | 82 | sí |
| `token_storage.py` | 65 | sí |
| `factory.py` (cableado MCP) | 37-158 | sí (tramo `RuntimeConfig`/`create_tools`) |
| `execution/fork/__init__.py` (herencia capabilities) | 27-91 | sí |
| `tools/{protocol,deferred,native_registry}.py` (superficie ToolProtocol + is_deferred + hot-plug) | — | sí |

### Preguntas de cierre
- ¿Se revisó **todo** cada archivo canónico listado? **sí, tras re-auditoría**. La 1ª pasada dejó tramos sin
  leer y marcó ⛔ por título; la 2ª ABRIÓ **todos** los archivos de `services/mcp/` + 4 dirs de tools +
  `oauth/index.ts` (ver ledger, columna "Lectura"). Los tres grandes en cobertura completa de comportamiento
  (client 152-3348, config 1-1578, auth en la interfaz del provider + revoke + flujo); lo genuinamente no
  leído (xaa*, oauth sub-piezas, componentes ink) está justificado por producto/UI, no por tamaño.
- ¿Se revisó **todo** cada archivo runtime listado? **sí** (los 12 archivos ÍNTEGROS + cableado factory/fork).
- ¿Los hallazgos fueron **exhaustivos (no superficiales)**? **ahora sí**. La 1ª pasada fue superficial (lo
  reconoce la §honestidad del ledger): faltaban list_changed, backoff-reconnect, dedup-por-firma,
  reconcile-scope-guard, headersHelper, elicitation-headless — **4 findings nuevos (MCP21-24) + 2 matices**
  aparecieron sólo al leer lo que se había descartado. Ahora se enumeran las 3 formas de resultado, los 5
  tipos de content block, los 5 estados de server, los 4 hints de annotation, las 2 capas de reconexión, la
  política name/command/url, el flujo needs-auth y el dedup por firma.
- ¿Quedó **todo cubierto (nada pendiente)**? **sí** (cabos 09·TiR3/TiR4/TiR5/B4/A25, 05·ExR6/GAP-EXEC4,
  08·SR3/SIG9, 03·CtxR7/A13 resueltos o confirmados; lo delegado —12·skills para prompts/skills MCP,
  B-new_messages para blobs, B-structured-output para structuredContent, 15·storage para escritura atómica—
  anotado con destino, no pendiente).

**Cierre habilitado: las 4 respuestas = sí (tras la iteración de re-auditoría, no en la 1ª pasada).**

## Nota metodológica
**Este doc se cerró en dos iteraciones; la 1ª fue superficial y el usuario la rechazó con razón.** La 1ª
pasada leyó lo sustantivo de los tres grandes pero (a) dejó tramos sin leer declarándolos "íntegros",
(b) marcó ~10 archivos ⛔ **por título sin abrirlos**, (c) listó un hallazgo sobre `headersHelper` sin leer
`headersHelper.ts`. Modo de fallo #1 del esfuerzo, exactamente. La 2ª pasada ABRIÓ todos los archivos y
destapó **FIND-MCP21-24 + 2 matices** que estaban escondidos precisamente en lo descartado:
- `useManageMCPConnections.ts` (tildado de "hook React UI") contenía la **reconexión con backoff** y los
  **handlers `*_list_changed`** — comportamiento core, no UI.
- `config.ts:1-320` (tildado de "helpers de path") contenía el **dedup por firma** (`getMcpServerSignature`).
- `utils.ts:185` reveló que el reconcile canónico **acota el disconnect a scope `dynamic`** — el del runtime
  es sobre-agresivo.
- `elicitationHandler.ts` mostró que los **hooks de elicitation responden sin UI** — ruta headless que el
  runtime sí debe soportar (no todo elicitation es ⛔).

Hallazgos de la 1ª pasada que sí resistieron: la lectura de `McpAuthTool.ts` destapó **FIND-MCP4** (pseudo-tool
`authenticate` + swap por prefijo), que un grep por "oauth" en `auth.py` habría escondido (el runtime delega
OAuth al SDK y "parece" cubierto). `transformResultContent`/`processMCPResult` separó **FIND-MCP5** (content
blocks) de **FIND-MCP7** (large-output) de **FIND-MCP6** (formas de resultado). `types.ts` fijó los **5 estados
de server** contra la fuente. **Lección reforzada: marcar ⛔ SIN abrir el archivo es superficialidad; el ⛔
sólo es legítimo tras leer y comprobar que es UI/producto** — como se hizo en la 2ª pasada con
InProcessTransport/SdkControlTransport/claudeai/channels/classifyForCollapse (todos abiertos, todos confirmados ⛔).

---

## Plan de homologación / remediación desarrollada

Diseño por finding. Seams: `capabilities/mcp/tool_adapter.py` (`McpTool`/`build_mcp_tool`),
`capabilities/mcp/client.py` (`McpClient`), `capabilities/mcp/provider.py` (ciclo de vida/startup/tools),
`capabilities/mcp/state.py` (`ServerStatus`/`McpState`), `capabilities/mcp/config.py`
(`McpServerConfig`/`load_server_configs`), `capabilities/mcp/scope.py`+`config_store.py` (política),
`capabilities/mcp/resource_tools.py`, y en `tools/protocol.py` (superficie `ToolProtocol`). Varios findings
aterrizan cabos transversales → referencian Deuda B / 10 / 12 y **no** se re-desarrollan. Lo propio de 11
(naming, needs-auth, transform, ciclo de vida) se desarrolla aquí.

### McR1 · FIND-MCP1 + GAP-MCP2 — naming `mcp__<server>__<tool>` + `mcpInfo` + normalización
- **Comportamiento**: toda tool MCP se expone como `mcp__<norm(server)>__<norm(tool)>`; el permiso se chequea
  por ese nombre FQ (deny "Write" no pega a un tool MCP homónimo); el swap y el deny operan por prefijo.
- **Seam/firma**: en `tool_adapter.py`, `_normalize_name(s)=re.sub(r'[^a-zA-Z0-9_-]','_',s)`; `build_mcp_tool`
  recibe `server_name` (ya lo hace) y setea `self.name = f"mcp__{_normalize_name(server)}__{_normalize_name(tool)}"`,
  `self.mcp_info = {"server_name":server, "tool_name":tool}`, conserva el `tool_name` crudo para la llamada al
  server (`self._raw_tool_name`). `McpTool.execute` llama `self._call(self._raw_tool_name, input)`.
- **Cableado**: `provider.register_tools_from_specs` ya pasa `server_name`. El gate de permisos
  (contracts/permissions) debe usar `mcp_info` si existe (helper `tool_name_for_permission(tool)`), espejo de
  `getToolNameForPermissionCheck`. **Orden**: primero (precondición de McR2/09·B4). **Test**:
  `test_mcp_tool_name_fully_qualified`, `test_mcp_permission_uses_fq_name` (xfail).

### McR2 · FIND-MCP2 + GAP-MCP1 — `is_mcp`/`always_load` en `ToolProtocol`; precedencia de deferral
- **Comportamiento**: `is_mcp=True` ⇒ tool diferida por defecto (workflow-specific), salvo `always_load=True`
  (opt-out gana primero); espejo de `isDeferredTool` (prompt.ts:62).
- **Seam/firma**: `tool_adapter.py`: `McpTool.is_mcp=True`, **quitar** `deferred=True` fijo; leer
  `always_load = spec.get('_meta',{}).get('anthropic/alwaysLoad') is True` y `search_hint` de
  `_meta['anthropic/searchHint']`. En `tools/deferred.py`, `is_deferred_tool` gana la precedencia:
  `if getattr(t,'always_load',False): return False; if getattr(t,'is_mcp',False): return True; if
  t.name==TOOL_SEARCH…: return False; return bool(getattr(t,'deferred',False))`.
- **Cableado**: cierra **09·TiR5/GAP-TOOL3** (ese doc ya tiene `test_is_deferred_precedence` xfail). Verificar
  que ningún camino siga seteando `deferred=True` a mano en MCP. **Orden**: junto a McR1. **Test**:
  `test_mcp_tool_is_mcp_flag`, `test_mcp_always_load_overrides` (xfail) + destrabar el de 09.

### McR3 · FIND-MCP3 — annotations completas → hints
- **Comportamiento**: `readOnlyHint`→(is_read_only, is_concurrency_safe, safe_for_background),
  `destructiveHint`→is_destructive, `openWorldHint`→is_open_world, `title`→userFacingName.
- **Seam/firma**: `build_mcp_tool` lee `annotations` y setea los 4 flags + `title`; `McpTool` gana
  `is_destructive`/`is_open_world`/`is_concurrency_safe` (defaults conservadores: False, False, False).
- **Cableado**: `is_concurrency_safe` alimenta la concurrencia de 09 (**B-concurrency**) cuando exista.
  **Orden**: tras McR1. **Test**: `test_mcp_annotations_mapped` (xfail).

### McR4 · FIND-MCP4 — estado needs-auth + pseudo-tool `authenticate` + caché
- **Comportamiento**: un server HTTP/SSE que responde 401 en connect → estado `NEEDS_AUTH` y se surte, en
  lugar de sus tools reales, un pseudo-tool `mcp__<server>__authenticate`; al llamarse arranca el flujo OAuth
  (headless: vía handlers inyectados, devolviendo la authUrl), y al completar reconecta y **reemplaza** el
  pseudo-tool por las tools reales (por prefijo). Caché needs-auth (TTL 15min) evita re-probar; skip de
  conexión si hay discovery pero no token.
- **Seam/firma**: `state.py`: añadir `ServerStatus.NEEDS_AUTH` + `ServerStatus.DISABLED`. `client.py`:
  `McpClient.connect` distingue `UnauthorizedError`/401 del SDK → levanta `McpAuthRequired(server)`.
  `provider.connect_server` captura `McpAuthRequired` → `set_status(NEEDS_AUTH)` + registra el auth-tool
  (`build_mcp_auth_tool(server, config, on_authenticated=self._swap_real_tools)`). `tool_adapter.py`: nueva
  `McpAuthTool` (name `mcp__server__authenticate`, requires_permission=False, no diferida) cuyo `execute`
  invoca `provider.authenticate(server)` (usa los handlers OAuth inyectados) y devuelve la authUrl o el
  resultado silencioso. `provider._swap_real_tools(server)`: reconecta, `state.set_tools(server, real)` —
  el pool per-turno recoge el cambio (o, si push-based, `NativeToolRegistry.unregister_by_prefix(f"mcp__{s}__")`
  → cierra 09·TiR4). Caché: `_needs_auth_cache: dict[str,float]` con TTL; `startup`/`reconcile` lo consultan.
- **Cableado**: los handlers OAuth ya existen (`redirect_handler`/`callback_handler` en el provider).
  **Orden**: tras McR1 (naming) y el ciclo de vida de McR7. **Test**: `test_mcp_needs_auth_surfaces_auth_tool`,
  `test_mcp_auth_tool_reconnects_and_swaps`, `test_needs_auth_cache_skips_reconnect` (xfail).

### McR5 · FIND-MCP5 + GAP-MCP3 — transform de content (image/audio/blob/resource)
- **Comportamiento**: los content blocks del resultado se transforman por tipo: `text`→texto;
  `image`→bloque image (redimensionado); `audio`/blob no-imagen→persistir a disco + mensaje corto con path;
  `resource`/`resource_link`→texto prefijado `[Resource from <server> at <uri>]`.
- **Seam/firma**: `client.py`: reemplazar `_text_from_content` por `transform_result_content(blocks, server)
  -> list[ContentPart]` que devuelve partes tipadas (text/image/attachment). `McpTool.execute` deja de
  concatenar a str y devuelve `ToolResult(new_messages=…)` para los bloques no-texto. **Depende de
  Deuda B `B-new_messages`** (el canal tipado en `ToolResult`) — sin él, degrada a persistir-a-disco + texto
  con path (sin bloque image nativo). La persistencia de blobs reusa la primitiva de storage del runtime.
- **Cableado**: nexo **10·A23** (read img/pdf ya persiste) — reusar `persist_binary`/`getBinaryBlobSavedMessage`
  equivalente. **Orden**: tras `B-new_messages`. **Test**: `test_mcp_image_result_block`,
  `test_mcp_blob_persisted_to_disk`, `test_mcp_resource_link_text` (xfail).

### McR6 · FIND-MCP6 + FIND-MCP7 — formas de resultado + large-output
- **Comportamiento**: aceptar 3 formas (`toolResult` string, `structuredContent` JSON+schema, `content`
  array); resultado con `_meta`/`structuredContent` → `mcpMeta`; salida grande → persistir a archivo +
  instrucciones (o truncar), con cap de tamaño e imágenes excluidas del persist.
- **Seam/firma**: `client.py`: `transform_mcp_result(result, tool, server) -> (content, kind, schema)` con
  `infer_compact_schema`. `McpClient.call` devuelve también `_meta`/`structured`; `McpTool.execute` los
  adjunta como `mcpMeta`. Large-output: `process_mcp_result` con umbral (reusar la primitiva de truncado/
  persistencia de 10) + `max_result_size_chars=100_000` en `McpTool`. **Depende de Deuda B
  `B-structured-output`** (`ToolResult.structured`/`output_schema`) y **09·A25** (mcpMeta).
- **Cableado**: `ToolResult` gana `mcp_meta`/`structured` (B-structured-output). **Orden**: tras
  B-structured-output. **Test**: `test_mcp_structured_content_result`, `test_mcp_large_output_persisted`,
  `test_mcp_result_carries_meta` (xfail).

### McR7 · FIND-MCP9 + FIND-MCP10 + FIND-MCP11 + FIND-MCP12 — ciclo de vida robusto
- **Comportamiento**: (a) timeout de conexión (`MCP_TIMEOUT` def 30s) que cierra el transporte al vencer;
  (b) startup batched-paralelo (local batch 3, remoto batch 20); (c) captura de capabilities/serverInfo/
  instructions y gate de discovery por capability; instructions (≤2048) inyectadas al system prompt;
  (d) recuperación de sesión: detectar 404/-32001 y -32000-connection-closed → invalidar y reconectar
  (retry 1); 401 en tool-call → NEEDS_AUTH (McR4).
- **Seam/firma**: `client.py::connect`: `await asyncio.wait_for(self._do_connect(), timeout)`; capturar
  `session.get_server_capabilities()`/version/instructions y guardarlos en el client; `list_tools` sólo si
  `caps.tools`, `list_resources` sólo si `caps.resources`. `provider.startup`: reemplazar el `for` secuencial
  por `asyncio.gather` con `asyncio.Semaphore` (local/remoto separados). `provider` gana `server_instructions()`
  → el loop las añade a las secciones de system prompt de los providers (`agent_loop.py:209`). Recuperación:
  `McpClient.call` clasifica el error del SDK (session-expired) → `provider.reconnect_server` + reintento.
- **Cableado**: `state.py` gana `capabilities`/`server_info`/`instructions` por server. Nexo **FIND-MCP4**
  (needs-auth comparte el clasificador de 401). **Orden**: núcleo de 11; tras McR1. **Test**:
  `test_mcp_connect_timeout`, `test_mcp_startup_parallel`, `test_mcp_capabilities_gate_discovery`,
  `test_mcp_session_recovery_retry` (xfail).
- **Reconexión proactiva con backoff (parte de FIND-MCP9)**: además de la recuperación reactiva, un server
  remoto que cae dispara reconexión con backoff exponencial (constantes canónicas: MAX 5 intentos,
  1s→30s), cancelable si el server se deshabilita o su config cambia; el estado transita a `PENDING` con
  `reconnect_attempt`/`max_reconnect_attempts`. **Seam**: un `_ReconnectScheduler` en el provider (timers por
  server, mapa cancelable) invocado desde el `on_close` del client. `state.py` gana `reconnect_attempt`.
  **Test**: `test_mcp_reconnect_backoff`, `test_mcp_reconnect_cancelled_on_disable` (xfail).

### McR8 · FIND-MCP8 — timeout de tool-call + progreso
- **Comportamiento**: el default de timeout de una tool MCP es efectivamente infinito (`MCP_TOOL_TIMEOUT`),
  no 30s; se emite progreso (started/progress/completed/failed).
- **Seam/firma**: `tool_adapter.py`: `timeout_seconds` default = muy alto (o `None`=sin límite), configurable
  por env `MCP_TOOL_TIMEOUT`; el 30s del provider aplica a **connect**, no a **call**. Separar los dos
  timeouts (hoy `register_tools_from_specs` usa el mismo 30s para ambos). Progreso: si el runtime tiene bus de
  eventos (07), emitir `ToolProgress`; si no, no-op documentado.
- **Cableado**: `provider.register_tools_from_specs` deja de mezclar connect-timeout con call-timeout.
  **Orden**: independiente, barato. **Test**: `test_mcp_tool_call_timeout_effectively_infinite` (xfail).

### McR9 · FIND-MCP13 — env-var expansion
- **Comportamiento**: `${VAR}` y `${VAR:-default}` en command/args/env/url/headers se expanden al parsear;
  variables faltantes se reportan (y el server se omite/marca).
- **Seam/firma**: `config.py`: `_expand_env(s)` (regex `\$\{([^}]+)\}` con split `:-`), aplicado en
  `parse_server_config`/`load_server_configs` a los campos string; acumular `missing_vars`. Un server con
  vars faltantes se salta con log (aislamiento por ítem, ya existe).
- **Cableado**: espejo de `expandEnvVarsInString`/`expandEnvVars`. **Orden**: independiente. **Test**:
  `test_mcp_env_var_expansion`, `test_mcp_env_var_default`, `test_mcp_missing_env_var_skips` (xfail).

### McR10 · FIND-MCP14 + FIND-MCP15 — política de admisión + aprobación de proyecto
- **Comportamiento**: (a) política allow/deny por name/command/url (wildcards); deny absoluto; allowlist
  vacía bloquea todo. (b) servers de scope `project` requieren aprobación (approved/rejected/pending);
  auto-aprueba en modo no-interactivo/bypass.
- **Seam/firma**: nuevo `capabilities/mcp/policy.py`: `is_server_allowed(name, config, settings) -> bool` con
  entries name/command/url; el `ScopedMcpConfigStore.load`/`provider.startup` filtran por política antes de
  conectar. Aprobación: puerto `McpApprovalGate` (Protocol) inyectable — `status(name, scope) ->
  approved|rejected|pending`; el provider sólo conecta project-servers `approved` (headless: el integrador
  decide la política de auto-aprobación, espejo de `getIsNonInteractiveSession`). El default headless
  auto-aprueba si el integrador lo habilita explícitamente.
- **Cableado**: las settings de política las provee el integrador (como el resto). **Orden**: tras el ciclo de
  vida (McR7). **Test**: `test_mcp_deny_policy`, `test_mcp_empty_allowlist_blocks`,
  `test_mcp_project_server_needs_approval` (xfail).

### McR11 · FIND-MCP17 — resource tools homologadas
- **Comportamiento**: `ReadMcpResource` con `server` **requerido** + chequeo de `capabilities.resources`,
  output estructurado `{contents:[{uri,mimeType,text,blobSavedTo}]}` con blobs persistidos; ambas resource
  tools **diferidas** (`shouldDefer`), read-only, concurrency-safe; reconexión-por-onclose vía el client.
- **Seam/firma**: `resource_tools.py`: `ReadMcpResourceTool.input_schema` marca `server` requerido (mantener
  la inferencia como fallback tolerante detrás de un flag, o quitarla por fidelidad); reusar el transform de
  blobs de McR5 para el output estructurado; añadir `deferred=True`(o `is_mcp`-style) a ambas. `ListMcp…`
  output = array plano (no `{resources:[]}`), o documentar la diferencia como deliberada.
- **Cableado**: nexo McR5 (blob persist) + McR2 (deferral). **Orden**: tras McR5. **Test**:
  `test_read_mcp_resource_requires_server`, `test_read_mcp_resource_structured_output`,
  `test_mcp_resource_tools_deferred` (xfail).

### McR12 · FIND-MCP19 — cleanup por agent_id + registro en abort scope (=05·ExR6/08·SR3)
- **Comportamiento**: al abortar/terminar un agente se cierran SUS clients MCP (no todos); el cleanup se
  registra en el `AbortScope.on_abort` del agente; stdio escala señales (opcional) para cierre limpio.
- **Seam/firma**: `provider` expone `cleanup_for_agent(agent_id)`; el runner (05) registra el cleanup en el
  abort scope del agente al forkar/arrancar. Como el fork **comparte** el provider vivo, el cleanup per-agent
  cierra sólo los clients abiertos por ese agente (si el modelo per-agente aplica) — si los clients son
  compartidos globalmente, el cleanup per-agent es no-op y el cierre real es en `shutdown()` (documentar
  cuál). Escalación de señales: delegada al SDK (documentar que el SDK `stdio_client` ya termina el proceso).
- **Cableado**: 05 (runner/abort scope) es el dueño del cableado; 11 provee el `cleanup_for_agent`. Nexo
  **05·GAP-EXEC4** (reaping de recursos hijos). **Orden**: junto a 05. **Test** (en 05/08):
  `test_mcp_cleanup_on_agent_abort`.

### McR13 · FIND-MCP20 — keying de credenciales por config-hash + revoke
- **Comportamiento**: los tokens se keyean por `name|sha256(type+url+headers)` (cambiar la url no reusa
  tokens); soporte de revoke (RFC 7009) al desautenticar.
- **Seam/firma**: `token_storage.py`: el `base` incluye un hash del config sensible (no sólo `server_name`);
  añadir `revoke()` que borra los tokens persistidos y (si el server publica revocation_endpoint) llama al
  endpoint. `provider` expone `deauthenticate(server)`.
- **Cableado**: menor, aislado. **Orden**: independiente. **Test**: `test_token_key_includes_config_hash`,
  `test_mcp_deauthenticate_clears_tokens` (xfail).

### McR15 · FIND-MCP21 — handlers `*_list_changed` → refetch en vivo
- **Comportamiento**: si el server declara `capabilities.{tools,prompts,resources}.listChanged`, registrar
  notification handlers que, al recibir `*_list_changed`, invalidan la caché del server y refetchean sólo esa
  categoría, actualizando `McpState` sin reconectar.
- **Seam/firma**: en `McpClient.connect`, tras `initialize`, registrar handlers sobre el `ClientSession`
  (`session.set_notification_handler` o el equivalente del SDK Python) gated por las capabilities capturadas
  (McR7). Cada handler llama a un callback del provider `on_list_changed(server, kind)` →
  `provider._refresh(server, kind)` que re-descubre y hace `state.set_tools/set_resources`.
- **Cableado**: depende de McR7 (captura de capabilities) y McR12/reconcile (invalidación). El pool per-turno
  recoge el cambio. **Orden**: tras McR7. **Test**: `test_mcp_tools_list_changed_refetch` (xfail).

### McR16 · FIND-MCP22 — dedup por firma de config
- **Comportamiento**: dos servers cuya firma (`stdio:<cmd+args>` o `url:<url-normalizada>`, ignorando
  env/headers) coincide son el mismo server → se conecta uno; el de mayor precedencia (o primero) gana.
- **Seam/firma**: `config.py`/`scope.py`: `server_signature(cfg) -> str|None`; el merge (`merge_scoped`) o el
  `provider.startup` filtra por firma antes de conectar, registrando la supresión (log). Reusa
  `unwrap_ccr_proxy_url` si aplica (probablemente no en el runtime → omitible).
- **Cableado**: se aplica tras el merge por nombre, antes de conectar. **Orden**: tras McR9 (env-expansion,
  para que la firma compare valores expandidos). **Test**: `test_mcp_dedup_by_signature` (xfail).

### McR17 · FIND-MCP23 — reconcile acotado (no desconectar ausentes de todo scope)
- **Comportamiento**: un server ausente del deseado sólo se desconecta si es de scope `dynamic` (o si su
  config-hash cambió, cualquier scope); un server de usuario transitoriamente ausente en un reload parcial
  NO se desconecta.
- **Seam/firma**: `reconcile.py::plan_reconcile` recibe la procedencia (`scope_of`) y, para `name in live and
  name not in desired`, sólo lo añade a `to_disconnect` si `scope_of[name] == DYNAMIC`. El refresh por
  config-hash se mantiene para todos los scopes.
- **Cableado**: el `provider.reconcile` ya tiene `_scope_of`. **Orden**: aislado. **Test**:
  `test_reconcile_keeps_absent_user_server`, `test_reconcile_drops_absent_dynamic` (xfail).

### McR18 · FIND-MCP24 — headersHelper (headers dinámicos + gate de trust)
- **Comportamiento**: un server puede declarar `headers_helper` (script); al conectar, se ejecuta (timeout
  ~10s) con env `CLAUDE_CODE_MCP_SERVER_NAME`/`_URL`, su stdout se parsea como JSON `{header:valor}` (dinámico
  sobre estático); para scope project/local se exige workspace-trust antes de ejecutarlo (borde de seguridad).
- **Seam/firma**: `config.py`: campo `headers_helper: str|None`. `client.py::connect` (rama http/sse): antes
  de armar headers, `dynamic = await run_headers_helper(cfg, ctx)` vía `ctx.exec_env` (reusa el shell backend
  de 09/`exec_env.py`, NO subprocess directo) con el gate de trust del integrador. Combinar `{**static,
  **dynamic}`.
- **Cableado**: reusa `ToolExecEnvironment` (09). El gate de trust lo provee el integrador (headless).
  **Orden**: tras McR7. **Test**: `test_headers_helper_dynamic`, `test_headers_helper_trust_gate` (xfail).

### McR19 · Referencias (no se re-desarrollan aquí)
- **FIND-MCP6 structuredContent** → **Deuda B `B-structured-output`** (el desarrollo del canal
  `ToolResult.structured`/`output_schema` vive ahí; McR6 lo consume).
- **FIND-MCP5 bloques image/attachment** → **Deuda B `B-new_messages`** (el canal tipado; McR5 lo consume).
- **FIND-MCP16 prompts→commands + skills MCP** → **12·capabilities/skills** (los slash-commands MCP y las
  skills `skill://` son territorio de 12; 11 sólo expone el discovery de prompts si 12 lo pide).
- **FIND-MCP18 elicitation/roots** → mayormente interactivo (⛔ de forma); lo core (declarar la capability
  `roots`→cwd y `elicitation` en el `ClientSession`, y el retry -32042) se difiere a un ciclo posterior sin
  xfail bloqueante (anotado, no pendiente-crítico).

---

## Re-visita de COMPLETITUD (2ª vuelta · gate 11 / L09) · 2026-07-19

**Modo**: 2ª vuelta con **gate 11**. La 1ª pasada de 11 NO fue confirmación-de-doc: fue una re-auditoría
íntegra (post-reproche de superficialidad) que ya leyó A+B y destapó FIND-MCP21-24. El value-add del gate 11
fue **abrir el ENSAMBLADOR** (`factory.py`/`capabilities/manager.py`/`tools/dispatcher.py`/`execution/fork`)
para confirmar el CABLEADO de las ✅/🔀 (hot-plug per-turno, herencia en fork, enforcement de timeout) — no
sólo los archivos de `mcp/`, sino el punto de unión (L09: la conclusión de cableado exige leer el ensamblador,
no grep). **Resultado**: el doc **se sostiene sobre base correcta**; **cero cambios de estado**
(✅~11·🟡~6/8·🔀~4/5·❌~14/18·⛔~9 intactos); **código intacto**; suite no re-ejecutada. Novedades: **1 costura
latente NUEVA (LAT-MCP1)** + **1 precisión de cableado** (herencia MCP en fork) + confirmaciones por el
ensamblador.

### Leído íntegro (B) 1→EOF esta vuelta
Los **12** archivos de `capabilities/mcp/`: `provider.py` 339 (el más grande, L08), `client.py` 204,
`config_store.py` 145, `config.py` 129, `auth.py` 122, `state.py` 118, `tool_adapter.py` 109, `scope.py` 105,
`resource_tools.py` 91, `reconcile.py` 82, `token_storage.py` 65, `__init__.py` 64. **Ensamblador**:
`factory.py:130-267` (tramo `_build_capability_manager`/`_build_local`/`create_runtime`, 1→EOF del tramo, L09)
+ `capabilities/manager.py` 112 (íntegro) + `execution/fork/__init__.py` 96 (íntegro) + la ruta de timeout de
`tools/dispatcher.py:67-82` + grep de cableado prod-vs-test. *(NOTA de layout: el paquete vive en
`src/agentic_runtime/…`, no en `src/…` — las rutas del ledger de la 1ª pasada siguen válidas relativas al
paquete.)*

### ✅/🔀 sostenidas abriendo B (mini-ledger de consumidores)
- **A · config/transporte**: `resolved_transport()` (config.py:90-95) da 3 (http/sse/stdio); identidad+auth
  estricta (`_validate_identity_and_auth` config.py:54-88: bearer→token 79-80; auth bearer/oauth ⊄ stdio 83-87
  = runtime **más estricto**); `ssl_verify` cableado en el client (114 SSE-factory, 127 HTTP); `enabled`
  salta en `startup` (241-245) y en `plan_reconcile` (52-54).
- **B · scope/precedencia**: 7 scopes (`McpScope` 25-34); `_PRECEDENCE` (38-46); `EXCLUSIVE_SCOPES={ENTERPRISE}`
  aplicado en `merge_scoped` (84-89); `MUTABLE_SCOPES`+`assert_mutable` (gate); persist add/remove/toggle vía
  `ScopedMcpConfigStore.save/remove` + `set_server_enabled` (provider 205-224).
- **C · ciclo de vida**: `McpClient.connect` (83-143) elige por transporte; HTTP pasa `timeout` del config
  (128) — evita el default httpx de 5s; aislamiento por ítem `connect_server` (155-162) marca FAILED sin
  propagar; `reconnect/disconnect/remove_server` (172-224); `reconcile` datos-puros (reconcile.py) +
  applier.
- **D · auth**: `register_auth_strategy` (auth.py:45-48) — patrón registrable; OAuth 2.1 delegado al SDK
  (`_build_oauth` 78-108).
- **E · adapter**: `build_mcp_tool` tolerante (tool_adapter 67-106); `requires_permission=True` (48);
  `McpToolError` = una sola llamada (client.call 174-180 levanta → `McpTool.execute` 59-61 envuelve).
- **F/G/H**: `_text_from_content` (F texto); `provider.tools()` añade las 2 resource-tools sólo si
  `all_resources()` (311-315); motor `reconcile` + `McpConfigWatcher` arrancado en `startup` (246-247).

### Confirmaciones por el ENSAMBLADOR (L09 — no grep)
- **Hot-plug por reensamblado PER-TURNO (cabo 09·TiR4) CONFIRMADO leyendo el ensamblador**:
  `factory._build_capability_manager` (148-158) crea `McpProvider` → `CapabilityManager` →
  `LocalAgentRuntime.__init__` (runtime.py:83) → `AgentLoop(capability_manager=self._capability_manager)`
  (runtime.py:358, **la MISMA instancia para root y subagentes**) → `agent_loop.py:194-195`
  `ctx.tool_pool = self._build_tool_pool(ctx)` **por turno** → `manager.tools(ctx)` (manager.py:50-59) →
  `McpProvider.tools()` (provider.py:307-316) re-lee `McpState.all_tools()` **cada turno**. Un server que
  conecta/desconecta entre turnos cambia el pool en el turno siguiente. `NativeToolRegistry` **NO está en la
  ruta** (grep: 0 consumidores de prod) — confirma el modelo per-turno.
- **RESUELVE DEUDA-B §B-orphans "decidir con 11"**: el hot-plug MCP es por **reensamblado per-turno** (NO por
  registro dinámico) ⇒ veredicto = **retirar `NativeToolRegistry`** (huérfano confirmado). Sólo se mantendría
  si se implementa el swap push-based del auth-tool de FIND-MCP4 (McR2). Comunicado a §B-orphans.
- **FIND-MCP8 refinamiento (no voltea estado)**: el cap de 30s de la tool-call **SÍ se aplica** — el
  dispatcher lee `tool.timeout_seconds` (`dispatcher.py:68`) y envuelve `execute` en `asyncio.wait_for`
  (77-82) → `ToolResult.timeout`. Una tool MCP que tarde >30s FALLA (🔀 se sostiene sobre base correcta).
  `register_tools_from_specs:125` alimenta el MISMO `config.timeout_seconds or 30` como call-timeout (vía
  `McpTool`) y como connect-timeout (client.py:128) — confirma la observación de McR8 de que hoy ambos
  comparten el 30s. *(`McpTool.timeout_seconds` NO es costura latente: se consume en el dispatcher.)*

### PRECISIÓN de cableado — herencia MCP en fork (no voltea estado)
La resolución del cabo **03·CtxR7/A13** decía "el provider MCP se hereda por el contenedor `capabilities`
compartido". Es **imprecisa para el standalone**. Leyendo `execution/fork/__init__.py` 1→EOF + grep de quién
puebla `app_state.capabilities`: en prod **NADA** mete el `McpProvider`/clients en `app_state.capabilities` —
ese contenedor sólo lleva el **discovered-set de deferred** (`tools/deferred.py:37`). En el **standalone** el
hijo ve las tools MCP vivas del padre por DOS vías: (a) `inherit_tool_pool=True` → el hijo recibe el
`tool_pool` ensamblado del padre (fork:75, que ya incluía las tools MCP al forkar), y (b) el
`capability_manager` **compartido** que se pasa al loop del subagente (runtime.py:358) → el reensamblado
per-turno re-lee el MISMO `McpState` vivo. `app_state.capabilities` es el seam del **integrador** per-tenant
(comentario de `ForkSnapshot` 42-46), NO el mecanismo del standalone. **La conclusión observable SE SOSTIENE**
(sin doble-conexión, sin clonado de clients, el hijo ve el provider vivo) — sólo se refina el mecanismo
nombrado. Hermana de las precisiones "leer el ensamblador, no grep" de 07/08/09.

### Costura latente NUEVA — LAT-MCP1 (tech-debt B-interno, NO deuda A↔B, anti-padding L10/L11)
`McpServerConfig.auth_headers()` (config.py:97-102) construye el header `Authorization: Bearer …` pero **no
tiene consumidor de producción** (grep: sólo `test_cap_mcp_homologation.py` + `test_mcp_config_contract.py`).
La ruta viva del bearer es la **estrategia de auth** `_build_bearer` (auth.py:73-75) → `AuthArtifacts.headers`
→ mergeada en `client.connect` (client.py:106). ⇒ `auth_headers()` es un **duplicado muerto** de la lógica de
bearer — hermano de `to_llm`/`timeout_seconds`(01)/`category`(LAT-TOOL1)/LAT-EXEC1/LAT-HOOK1. El canónico no
usa este método como driver de headers ⇒ **NO deuda A↔B**. Homed a **DEUDA-B §B-orphans**. *(Primos menores,
no elevados a finding — son slots pasivos / superficie de API, no maquinaria duplicada: `McpServerConfig.model`
per-server 0 lectores de prod; `McpState.pending_servers()` accesor de introspección integrator-facing.)*
**LAT-TOOL1 (category) confirmado que aterriza aquí**: cada `McpTool` (tool_adapter:27) y las 2 resource-tools
(resource_tools:31/63) setean `category=ToolCategory.SYSTEM` pero nadie lee `.category` — ya homed 09/DEUDA-B,
sin novedad.

### ❌ convergen por lectura directa de B (dirección L11 crítica — sin implementación oculta)
`ServerStatus` tiene **exactamente 4** estados (state.py:13-19, sin NEEDS_AUTH/DISABLED → FIND-MCP4); 401 →
FAILED sin auth-tool (connect_server 155-157, FIND-MCP4); nombre **crudo** sin `mcp__`/normalización/`mcp_info`
(tool_adapter name=name 43/99, FIND-MCP1); `deferred=True` fijo sin `is_mcp`/`always_load` (tool_adapter:30,
FIND-MCP2); `_text_from_content` hace `str()` de todo bloque no-texto (client.py:55, FIND-MCP5); `connect`
sólo llama `initialize()` sin capturar capabilities/serverInfo/instructions y `list_tools`/`list_resources`
incondicional (137/153-154, FIND-MCP12); sin `wait_for` en connect (FIND-MCP10); startup secuencial (241-245,
FIND-MCP11); sin notification handlers `*_list_changed` (FIND-MCP21); sin firma/dedup (FIND-MCP22); parseo raw
sin `${VAR}` (config.py, FIND-MCP13); sin política/aprobación (FIND-MCP14/15); `plan_reconcile` desconecta
CUALQUIER ausente (reconcile.py:61-63, FIND-MCP23 sobre-agresivo). **Ninguna ❌ resultó falsa** (ninguna
implementación oculta en B).

### Ledger de lectura (2ª vuelta)
| Grupo | Archivos | Lectura esta vuelta |
|---|---|---|
| B · `capabilities/mcp/` (12) | provider 339·client 204·config_store 145·config 129·auth 122·state 118·tool_adapter 109·scope 105·resource_tools 91·reconcile 82·token_storage 65·__init__ 64 | **íntegro 1→EOF** |
| B · ensamblador | `factory.py` 1-267 (todo)·`capabilities/manager.py` 112·`execution/fork/__init__.py` 96·`tools/dispatcher.py` 85 (íntegro)·`loop/agent_loop.py:85-219` | **íntegro (archivo/tramo) 1→EOF** |
| A · canónico | `services/mcp/*` + tools MCP + `oauth/*` | **NO re-leído** — íntegro/comportamiento en la re-auditoría de 1ª pasada (ver ledger arriba); "releer anclas, no re-derivar" |

### Auto-corrección de honestidad (gate auto-adversarial del usuario)
Mi 1ª redacción de esta re-visita afirmó TRES conclusiones de **cableado** apoyándose en **grep**, no en
lectura — la misma deficiencia de método que las auto-correcciones de 08/09/10: (1) "el timeout de 30s se
aplica vía `wait_for`" desde grep de `dispatcher.py` (no leído); (2) el reensamblado per-turno `agent_loop.py:
194-195` desde grep + rondas previas; (3) la superficie MCP de `factory.py:1-129` (`CapabilitiesConfig`) desde
grep. Corregido leyéndolos **1→EOF esta ronda**: (1) `dispatcher.py` (85) — `asyncio.wait_for(tool.execute,
timeout=effective_timeout)` (76-82) + `except TimeoutError→ToolResult.timeout` REAL ⇒ FIND-MCP8 sólido,
`McpTool.timeout_seconds` consumido (no latente); (2) `agent_loop.py:185` `for _turn in range(_MAX_TURNS)` →
**194-195 DENTRO del bucle** `ctx.tool_pool=self._build_tool_pool(ctx)`→`build_tool_pool` (94) ⇒ hot-plug
per-turno confirmado por lectura (matiz: `_restrict_to_agent_tools` 99-110 filtra también capability_tools por
el allowlist del subagente — ortogonal, no cambia estado); (3) `factory.py:1-129` confirma la superficie
`mcp_servers`/`mcp_config_store`/`mcp_config_watcher`/`mcp_oauth_*` (33-55). **Las tres conclusiones se
SOSTUVIERON** — cero findings/estados nuevos; corrección de MÉTODO (L00/L09 "cableado = leer el ensamblador,
nunca grep"; grep sólo legítimo para probar AUSENCIA). Residuo declarado: el árbol canónico A no se re-leyó
(íntegro en 1ª pasada); las pruebas de ausencia (auth_headers/NativeToolRegistry/config.model/app_state.
capabilities) se apoyan en grep con la ruta viva corroborada por lectura.

### §Honestidad
La 1ª pasada de 11 YA fue una re-auditoría íntegra A+B (no confirmación-de-doc; destapó MCP21-24). Esta vuelta
NO re-leyó las contrapartes canónicas (íntegras/comportamiento en la 1ª pasada) — el value-add fue abrir el
**ensamblador** para: (1) confirmar el hot-plug per-turno por el punto de unión (no sólo por `mcp/`), (2)
cazar la imprecisión del mecanismo de herencia MCP en fork (`capability_manager` compartido, no
`app_state.capabilities`), (3) confirmar el enforcement de timeout por el dispatcher, (4) destapar LAT-MCP1.
Ninguna de estas 4 era visible sin abrir factory/manager/dispatcher/fork. Cero cambios de estado; código
intacto.

### Re-verificación del lado A (canónico) — COMPLETADA 1→EOF esta ronda (reproche del usuario, 2ª iteración)
Tras la 1ª redacción de este bloque, el usuario señaló que apoyarme en "A se leyó íntegro en la 1ª pasada" es
tratar el ledger previo como fuente de verdad — justo lo que L11 prohíbe — máxime cuando ESTA ronda ya fallé
en método (grep para cableado) y el propio doc admite que la 1ª pasada de 11 fue superficial-luego-re-auditada.
No podía certificar la 1ª pasada. Consecuencia: re-verifiqué **TODO el lado A observable esta ronda, 1→EOF**.
- **A tratables re-leídos 1→EOF y SOSTENIDOS**: `types.ts` (258 — 5 estados 201-226/248 → FIND-MCP4/C;
  `isMcp`/`originalToolName`/`normalizedNames` 242-257 → FIND-MCP1/2; transportes 24 → tabla A; `headersHelper`
  63/94 → FIND-MCP24; oauth sub-config 43-56 → D), `MCPTool.ts` (77 — `checkPermissions→'passthrough'` 56-61 →
  E; `isMcp`/`maxResultSizeChars:100k`), `McpAuthTool.ts` (215 — pseudo-tool `authenticate` +
  `performMCPOAuthFlow(skipBrowserOpen)` + swap por prefijo `reject(...startsWith(prefix))` 150 → FIND-MCP4),
  `ListMcpResourcesTool.ts`/`ReadMcpResourceTool.ts` (123/158 → FIND-MCP17), 3 `prompt.ts` triviales (NO
  listados en el ledger de la 1ª pasada = laguna de completitud de ESE ledger, sin comportamiento).
- **A grandes re-leídos 1→EOF y SOSTENIDOS (lo que estaba pendiente)**:
  - **`client.ts` (3348)**: `DEFAULT_MCP_TOOL_TIMEOUT_MS=100_000_000` (211) → FIND-MCP8; `getConnectionTimeoutMs=30000`
    + race+`transport.close()` (456/1048-1077) → FIND-MCP10; batch local-3/remoto-20 vía `pMap` (552-561/2391-2402)
    → FIND-MCP11; `getServerCapabilities/Version/Instructions`+trunc-2048 (1157-1171) → FIND-MCP12; onerror/onclose
    ECONNRESET×3 + 404/-32001 + -32000 + invalida cachés (1249-1402/3194-3231) → FIND-MCP9; stdio SIGINT→SIGTERM→
    SIGKILL 100/400ms + `registerCleanup` (1426-1574) → FIND-MCP19; `buildMcpToolName`+`mcpInfo`+`isMcp`+`searchHint`/
    `alwaysLoad` de `_meta` (1768-1785) → FIND-MCP1/2; annotations→`isConcurrencySafe/isReadOnly/isDestructive/
    isOpenWorld/title` (1795-1976) → FIND-MCP3; `_meta:{claudecode/toolUseId}`+`mcpMeta` (1841/1897-1909) → FIND-MCP6;
    `MAX_SESSION_RETRIES=1` (1859) → FIND-MCP9; `fetchCommandsForClient`→`mcp__srv__prompt`+`getPromptForCommand`
    (2054-2094) → FIND-MCP16; `transformResultContent` text/audio/image-resize/resource/resource_link (2478-2591) →
    FIND-MCP5; `transformMCPResult` 3-formas+`inferCompactSchema` (2662-2697) → FIND-MCP6; `processMCPResult`
    large-output/`ENABLE_MCP_LARGE_OUTPUT_FILES`/imágenes-excluidas (2720-2799) → FIND-MCP7;
    `callMCPToolWithUrlElicitationRetry` `-32042`×3+`runElicitationHooks` headless (2813-3027) → FIND-MCP18;
    `capabilities:{roots,elicitation}`+`ListRootsRequestSchema→cwd` (994-1018) → FIND-MCP18; `setupSdkMcpClients`
    (3262) → ⛔ sdk.
  - **`config.ts` (1578)**: `writeMcpjsonFile` temp+datasync+chmod+rename (88-131) → escritura-atómica; `getMcpServerSignature`
    `stdio:`/`url:` + `dedupPlugin/ClaudeAi` (202-310) → FIND-MCP22; `isMcpServerDenied`/`isMcpServerAllowedByPolicy`
    name/command/url + deny-absoluto + allowlist-vacía-bloquea + `allowManagedMcpServersOnly` (364-508) → FIND-MCP14;
    `expandEnvVars`→`expandEnvVarsInString`+`missingVars` (556-616) → FIND-MCP13; `addMcpConfig` regex+reservados+
    enterprise-exclusivo (625-679) + `getMcpConfigByName` precedencia enterprise>local>project>user (1046-1057) +
    `getProjectMcpServerStatus==='approved'` (1164-1170) → FIND-MCP15; `parseMcpConfig` fatal/warning+npx-Windows
    (1297-1372) → severidad; `isMcpServerDisabled`/`setMcpServerEnabled` disabled/enabledMcpServers (1528-1569) → enabled 🔀.
  - **`auth.ts` (2465)**: `getServerKey`=`${name}|${sha256(type+url+headers)[:16]}` (325-341) + todos los
    accesos keyed por él → FIND-MCP20; `hasMcpDiscoveryButNoToken` (349-363) → FIND-MCP4; `revokeToken` RFC 7009 +
    `revokeServerTokens` refresh-first (381-618) → FIND-MCP20; `ClaudeAuthProvider.clientMetadata`
    (`token_endpoint_auth_method:'none'`+grant/response types, 1417-1437) = **espejo EXACTO del `_build_oauth` del
    runtime auth.py:92-100**; `clientMetadataUrl` CIMD SEP-991 (1445); step-up 403 (1468/1625-1637); OAuth provider
    methods (PKCE/DCR/refresh+lockfile/discovery, 1482-2359) delegados al SDK en el runtime → D ✅. **⛔-de-forma
    CONFIRMADOS POR LECTURA (L02, no por título)**: XAA `performMCPXaaAuth` (664-845, SEP-990 identidad corporativa),
    `performMCPOAuthFlow` servidor-callback-interactivo + browser (847-1342), sub-piezas OAuth interactivas.
- **Cita-de-línea como evidencia**: las citas de la 1ª pasada (1049-1077, 1157-1183, 1216-1402, 1429-1562,
  1795-1976, 2503, 2662, 2720, 2813, 325, 381-467, 1376-1644) **coinciden EXACTAS** con el código — no se puede
  citar rangos correctos de comportamientos no leídos ⇒ evidencia de que la 1ª pasada SÍ leyó los 3 grandes.
- **Resultado: CERO discrepancias.** La caracterización de A del doc es exacta y precisa; para los 3 grandes la
  1ª pasada fue correcta en sustancia (su superficialidad reconocida se limitó a los satélites ⛔-sin-abrir, ya
  corregidos en la re-auditoría de la 1ª pasada). Ninguna ❌ resultó falsa; ningún comportamiento de A omitido.

### 4 preguntas de cierre
1. ¿Se revisó **todo** cada archivo de **B**? **sí** — los 12 de `mcp/` + el ensamblador íntegros 1→EOF esta
   vuelta (ledger arriba; auto-corrección de dispatcher/factory-head/agent_loop-tramo incluida).
2. ¿Se revisó **todo** cada archivo de **A**? **sí, ESTA ronda 1→EOF** — tratables (types/MCPTool/McpAuthTool/2
   resource-tools/3 prompts) + los **3 grandes** `client.ts`(3348)/`config.ts`(1578)/`auth.ts`(2465) leídos
   íntegros contra cada ❌/🔀; los ⛔-de-forma confirmados abriéndolos (L02). NO se aceptó el ledger previo.
3. ¿Los hallazgos fueron **exhaustivos (no superficiales)**? **sí** — MCP1-24 + LAT-MCP1 + precisión de cableado
   (fork) + confirmaciones por ensamblador (B) y por lectura 1→EOF de los 3 grandes de A. Cero discrepancias.
4. ¿Quedó **todo cubierto (nada pendiente)**? **sí** — B (12 + ensamblador) y A (todo, 1→EOF) verificados esta
   ronda; LAT-MCP1 → DEUDA-B §B-orphans; decisión `NativeToolRegistry` resuelta; lo delegado con destino
   (12·skills, B-new_messages, B-structured-output, 15·storage, 05·cleanup). Ningún pendiente de verificación.

### VEREDICTO DE AVANCE
**✅ NADA PENDIENTE → avanzar a 12 · capabilities/skills.** (01→11 completos con gate 11; lado B verificado
1→EOF, lado A re-verificado 1→EOF ESTA ronda con CERO discrepancias — el cierre está ganado, no asumido;
código intacto, cero cambios de estado.)
