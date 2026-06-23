"""R1 — borrado de skills con unload del estado vivo.

El provider tenía `register_skill` (alta) pero no su inverso: un skill borrado del
store seguía invocable en el estado vivo hasta reiniciar el proceso. `unregister`
cierra ese gap de correctitud para un server long-running: quita del store (si hay) y
del `SkillsState`, de modo que desaparece del catálogo y de la tool `Skill` en el acto.
"""
from agentic_runtime.capabilities.skills import (
    SkillsProvider,
    SkillsState,
    load_skill_text,
)
from agentic_runtime.context.tool_use import ToolUseContext


def _ctx() -> ToolUseContext:
    return ToolUseContext(session_id="s1")


# --- SkillsState.remove -----------------------------------------------------

def test_state_remove_existing_returns_true_and_drops_skill():
    state = SkillsState()
    state.set_skill(load_skill_text("a", "---\ndescription: d\n---\ncuerpo"))
    assert state.get("a") is not None
    assert state.remove("a") is True
    assert state.get("a") is None
    assert state.all_skills() == []


def test_state_remove_absent_returns_false():
    state = SkillsState()
    assert state.remove("nope") is False


# --- SkillsProvider.unregister ----------------------------------------------

class _RecordingStore:
    """SkillStore en memoria que registra remove()."""

    def __init__(self) -> None:
        self._skills: dict[str, str] = {}
        self.removed: list[str] = []

    async def list(self) -> list[str]:
        return sorted(self._skills)

    async def read(self, name: str) -> str | None:
        return self._skills.get(name)

    async def write(self, name: str, content: str) -> None:
        self._skills[name] = content

    async def remove(self, name: str) -> None:
        self.removed.append(name)
        self._skills.pop(name, None)


async def test_unregister_removes_from_store_and_state():
    store = _RecordingStore()
    provider = SkillsProvider(skill_store=store)
    await provider.register_skill("x", "---\ndescription: d\n---\ncuerpo")
    assert provider.state.get("x") is not None

    assert await provider.unregister("x") is True
    assert provider.state.get("x") is None          # unload del estado vivo
    assert store.removed == ["x"]                    # persistencia borrada
    # ya no aparece en el catálogo
    assert all(c.name != "x" for c in provider.catalog(_ctx()))


async def test_unregister_absent_returns_false_but_store_cleanup_is_idempotent():
    # No cargado en estado → return False; el store.remove se intenta igual (idempotente),
    # así una entrada huérfana en el store (no cargada en estado) también se limpia.
    store = _RecordingStore()
    provider = SkillsProvider(skill_store=store)
    assert await provider.unregister("ghost") is False
    assert store.removed == ["ghost"]


async def test_unregister_without_store_still_unloads_state():
    provider = SkillsProvider()
    provider.add_skill_text("inline", "---\ndescription: d\n---\ncuerpo")
    assert await provider.unregister("inline") is True
    assert provider.state.get("inline") is None
