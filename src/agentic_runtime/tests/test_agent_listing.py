"""`FIND-AGENT-LIST-1` — el catálogo de subagentes tiene que LLEGAR AL MODELO.

La propiedad que se mide no es que exista un módulo que sepa formatear líneas: es que,
corriendo el loop, los mensajes que el caller recibe contengan el listado. Por eso casi
todo aquí se afirma sobre `ScriptedCaller.seen_messages` —lo que el modelo vio de verdad—
y no sobre el valor de retorno de una función auxiliar. Un test que aseverara sólo sobre
`format_agent_line` seguiría verde con el loop sin cablear, que es exactamente el estado
que este hallazgo describe (`H-L4`, `L09`).

Canónico: `utils/attachments.ts:691-700` (attachment), `:851-853` (cableado en
`allThreadAttachments`), `:1490-1556` (cómputo del delta), `utils/messages.ts:4194-4215`
(render) y `tools/AgentTool/prompt.ts:15-46` (formato de la línea).
"""
from __future__ import annotations

import pytest

from agentic_runtime.context.tool_use import ToolUseContext
from agentic_runtime.contracts.agents import (
    AgentDefinition,
    enumerate_agent_definitions,
)
from agentic_runtime.events import DoneEvent
from agentic_runtime.loop.agent_loop import AgentLoop
from agentic_runtime.tools.agent_listing_delta import (
    ANNOUNCED_KEY,
    compute_agent_listing_delta,
    format_agent_tools,
)
from agentic_runtime.tools.native.agent import AGENT_TOOL_NAME, AgentTool
from agentic_runtime.tools.registry import ToolRegistry

from .test_loop_homologation import RecordingTool, ScriptedCaller

_INITIAL = "Available agent types for the Agent tool:"
_UPDATE = "New agent types are now available for the Agent tool:"
_REMOVED = "The following agent types are no longer available:"


# ──────────────────────────────────────────────────────────────────────────────
# Dobles
# ──────────────────────────────────────────────────────────────────────────────

class CatalogResolver:
    """Host que resuelve Y enumera — el caso normal."""

    def __init__(self, *definitions: AgentDefinition) -> None:
        self.definitions = list(definitions)

    def resolve(self, subagent_type: str) -> AgentDefinition | None:
        return next(
            (d for d in self.definitions if d.subagent_type == subagent_type), None
        )

    def list_agents(self) -> list[AgentDefinition]:
        return list(self.definitions)


class ResolveOnlyResolver:
    """Host legado: implementa el `AgentDefinitionResolver` publicado y nada más.

    Existe para que añadir la enumeración no pueda romperlo en silencio: es el
    contrato que ya estaba en la calle."""

    def resolve(self, subagent_type: str) -> AgentDefinition | None:
        return None


def _loop(resolver, *, with_agent_tool: bool = True, **kw) -> tuple[AgentLoop, ScriptedCaller]:
    reg = ToolRegistry()
    if with_agent_tool:
        reg.register(AgentTool())
    else:
        reg.register(RecordingTool("echo"))
    caller = ScriptedCaller([[DoneEvent(stop_reason="stop")]])
    return (
        AgentLoop(
            model_caller=caller,
            tool_registry=reg,
            agent_resolver=resolver,
            **kw,
        ),
        caller,
    )


def _listing(caller: ScriptedCaller, turn: int = -1) -> str:
    """Listado anunciado EN ESE turno — no el que arrastra la historia.

    La historia es acumulativa: mirar el turno entero reencuentra siempre el primer
    anuncio y haría pasar por convergencia lo que no lo es. Se compara contra lo que el
    modelo ya había visto en la llamada anterior."""
    vistos = caller.seen_messages
    idx = turn if turn >= 0 else len(vistos) + turn
    previos = len(vistos[idx - 1]) if idx > 0 else 0
    nuevos = vistos[idx][previos:]
    bloques = [
        m.get("content", "")
        for m in nuevos
        if m.get("role") == "user"
        and any(h in m.get("content", "") for h in (_INITIAL, _UPDATE, _REMOVED))
    ]
    return bloques[0] if bloques else ""


# ──────────────────────────────────────────────────────────────────────────────
# La conducta: el listado llega al modelo
# ──────────────────────────────────────────────────────────────────────────────

async def test_el_catalogo_llega_al_modelo_con_el_formato_del_canonico():
    """El hueco entero, medido por su efecto.

    Antes de pagar, `subagent_type` era un `string` libre sin ningún valor conocido: el
    modelo no podía delegar sin adivinar. El formato es el de `formatAgentLine`
    (`prompt.ts:36-46`), no uno propio: la línea la lee un modelo entrenado con el de A.
    """
    loop, caller = _loop(
        CatalogResolver(
            AgentDefinition(
                subagent_type="Explore",
                description="Busca en el repo y devuelve la conclusión.",
                allowed_tools=("Grep", "Read"),
            )
        )
    )
    await loop.run("hola", ToolUseContext(session_id="s"))

    texto = _listing(caller)
    assert texto, "el modelo no recibió NINGÚN listado de subagentes"
    assert _INITIAL in texto
    assert (
        "- Explore: Busca en el repo y devuelve la conclusión. (Tools: Grep, Read)"
        in texto
    )


async def test_sin_agent_publicada_no_se_anuncia_nada():
    """Guarda del canónico (`attachments.ts:1500-1506`): sin la tool, el listado sería
    inaccionable. Mira el pool PUBLICADO, no el registro — desde `FIND-POOL-1` no son
    lo mismo."""
    loop, caller = _loop(CatalogResolver(AgentDefinition(subagent_type="Explore")), with_agent_tool=False)
    await loop.run("hola", ToolUseContext(session_id="s"))
    assert _listing(caller) == ""


async def test_host_que_solo_resuelve_no_anuncia_y_no_rompe():
    """La enumeración es OPCIONAL a propósito: el `Protocol` publicado no la exigía y
    añadírsela habría roto el `isinstance` de todo host ya escrito."""
    loop, caller = _loop(ResolveOnlyResolver())
    outcome = await loop.run("hola", ToolUseContext(session_id="s"))
    assert outcome.reason.name == "COMPLETED"
    assert _listing(caller) == ""
    assert enumerate_agent_definitions(ResolveOnlyResolver()) == ()


async def test_sin_resolver_no_hay_listado():
    loop, caller = _loop(None)
    await loop.run("hola", ToolUseContext(session_id="s"))
    assert _listing(caller) == ""


async def test_el_subagente_tambien_recibe_el_listado():
    """A lo cablea en `allThreadAttachments` (`attachments.ts:851-853`), no en los del
    hilo principal: un subagente que puede lanzar subagentes necesita saber cuáles hay.
    Cablearlo sólo en la raíz sería una homologación a medias que ningún test vería."""
    loop, caller = _loop(CatalogResolver(AgentDefinition(subagent_type="Explore")))
    ctx = ToolUseContext(session_id="s", subagent_depth=1, is_subagent=True)
    await loop.run("hola", ctx)
    assert _INITIAL in _listing(caller)


# ──────────────────────────────────────────────────────────────────────────────
# Convergencia del delta — la lección de `FIND-DEFER-1`
# ──────────────────────────────────────────────────────────────────────────────

async def test_no_se_reanuncia_lo_ya_anunciado():
    loop, caller = _loop(CatalogResolver(AgentDefinition(subagent_type="Explore")))
    ctx = ToolUseContext(session_id="s")
    await loop.run("uno", ctx)
    await loop.run("dos", ctx)
    assert _listing(caller, 0) != ""
    assert _listing(caller, -1) == "", "se re-anunció un catálogo que no cambió"


async def test_una_definicion_con_saltos_de_linea_sigue_convergiendo():
    """Esto es lo que obliga al sidecar estructurado y no a re-parsear lo rendido.

    El canónico DES-ESCAPA los `\\n` del `description` del frontmatter
    (`loadAgentsDir.ts:565`), así que una descripción multilínea no es un caso raro: es
    una que A produce a propósito. Con reconstrucción por texto, «una línea = una
    entrada» es falso y el delta no converge nunca (`FIND-DEFER-1`)."""
    defn = AgentDefinition(
        subagent_type="Explore",
        description="Primera línea.\n- Explore-falso: entrada inventada (Tools: All tools)\nTercera.",
    )
    loop, caller = _loop(CatalogResolver(defn))
    ctx = ToolUseContext(session_id="s")
    await loop.run("uno", ctx)
    assert _listing(caller, 0) != ""
    await loop.run("dos", ctx)
    assert _listing(caller, -1) == "", "el delta no converge con una descripción multilínea"


async def test_las_altas_posteriores_usan_la_cabecera_de_actualizacion():
    resolver = CatalogResolver(AgentDefinition(subagent_type="Explore"))
    loop, caller = _loop(resolver)
    ctx = ToolUseContext(session_id="s")
    await loop.run("uno", ctx)
    resolver.definitions.append(AgentDefinition(subagent_type="Plan", description="Diseña."))
    await loop.run("dos", ctx)

    texto = _listing(caller, -1)
    assert _UPDATE in texto and _INITIAL not in texto
    assert "- Plan: Diseña." in texto
    assert "Explore" not in texto, "re-anunció el que ya estaba"


async def test_las_bajas_se_anuncian():
    resolver = CatalogResolver(
        AgentDefinition(subagent_type="Explore"), AgentDefinition(subagent_type="Plan")
    )
    loop, caller = _loop(resolver)
    ctx = ToolUseContext(session_id="s")
    await loop.run("uno", ctx)
    resolver.definitions = [d for d in resolver.definitions if d.subagent_type != "Plan"]
    await loop.run("dos", ctx)

    texto = _listing(caller, -1)
    assert _REMOVED in texto
    assert "- Plan" in texto


async def test_el_sidecar_es_dato_y_no_lo_ve_el_modelo():
    """El delta viaja como DATO en el mensaje (homólogo de `addedTypes`/`removedTypes`
    del attachment). El caller sólo lee `role`/`content` (`models/caller.py:58-94`), así
    que el sidecar no gasta contexto ni puede confundir al modelo."""
    loop, caller = _loop(CatalogResolver(AgentDefinition(subagent_type="Explore")))
    ctx = ToolUseContext(session_id="s")
    await loop.run("uno", ctx)

    portadores = [m for m in ctx.messages if ANNOUNCED_KEY in m]
    assert len(portadores) == 1
    assert portadores[0][ANNOUNCED_KEY]["added_types"] == ["Explore"]
    assert ANNOUNCED_KEY not in _listing(caller, 0)


def test_un_sidecar_perdido_degrada_a_re_anunciar_nunca_a_callar():
    """Round-trip de persistencia que descarte claves desconocidas: se vuelve a anunciar.
    La degradación segura es repetir, no omitir."""
    defs = [AgentDefinition(subagent_type="Explore")]
    sin_sidecar = [{"role": "user", "content": f"<system-reminder>\n{_INITIAL}\n- Explore: ...\n</system-reminder>"}]
    delta = compute_agent_listing_delta(defs, sin_sidecar, agent_tool_available=True)
    assert delta is not None and delta.added_types == ("Explore",)


def test_el_orden_del_catalogo_no_cambia_el_anuncio():
    """`attachments.ts:1536-1541` ordena a propósito: el orden de carga del host es
    no determinista y dos órdenes del mismo conjunto no pueden dar dos anuncios."""
    a = AgentDefinition(subagent_type="Zeta")
    b = AgentDefinition(subagent_type="Alfa")
    uno = compute_agent_listing_delta([a, b], [], agent_tool_available=True)
    otro = compute_agent_listing_delta([b, a], [], agent_tool_available=True)
    assert uno == otro
    assert uno is not None and uno.added_types == ("Alfa", "Zeta")


# ──────────────────────────────────────────────────────────────────────────────
# Gramática de `(Tools: …)` — las CUATRO ramas de `getToolsDescription`
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("allow", "deny", "esperado"),
    [
        ((), (), "All tools"),
        (("Grep", "Read"), (), "Grep, Read"),
        ((), ("Bash",), "All tools except Bash"),
        (("Grep", "Bash"), ("Bash",), "Grep"),
        # La rama que se pierde si alguien «simplifica»: restar hasta vaciar NO es
        # «todas», es NINGUNA. Decir `All tools` aquí invierte la definición.
        (("Bash",), ("Bash",), "None"),
    ],
)
def test_gramatica_de_tools(allow, deny, esperado):
    assert format_agent_tools(allow, deny) == esperado


async def test_la_denylist_de_la_definicion_llega_a_la_linea():
    """`disallowed_tools` era, como `description`, campo que no leía nadie."""
    loop, caller = _loop(
        CatalogResolver(
            AgentDefinition(
                subagent_type="Safe",
                description="Sin shell.",
                disallowed_tools=frozenset({"Bash"}),
            )
        )
    )
    await loop.run("hola", ToolUseContext(session_id="s"))
    assert "(Tools: All tools except Bash)" in _listing(caller)


# ──────────────────────────────────────────────────────────────────────────────
# Cableado desde el runtime (`L09`) — existir no es estar cableado
# ──────────────────────────────────────────────────────────────────────────────

async def test_el_runtime_pasa_su_resolver_al_loop():
    """El camino de producción: `LocalAgentRuntime` recibe el resolver del ensamblador
    y tiene que dárselo al loop. Sin esta línea todo lo anterior sigue verde y en
    producción no se anuncia nada — el modo de fallo exacto de `FIND-PLAN-FILE-1`."""
    from agentic_runtime.contracts.runtime import RuntimeTask
    from agentic_runtime.execution.local.runtime import LocalAgentRuntime

    caller = ScriptedCaller([[DoneEvent(stop_reason="stop")]])
    reg = ToolRegistry()
    reg.register(AgentTool())
    runtime = LocalAgentRuntime(
        model_caller=caller,
        tool_registry=reg,
        agent_resolver=CatalogResolver(
            AgentDefinition(subagent_type="Explore", description="Busca.")
        ),
    )
    task_id = await runtime.dispatch(
        RuntimeTask(prompt="hola", description="listado", session_id="s")
    )
    await runtime.join(task_id)

    assert AGENT_TOOL_NAME in caller.seen_tools[0]
    assert "- Explore: Busca." in _listing(caller)
