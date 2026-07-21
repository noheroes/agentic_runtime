"""04·modes — homologación del subsistema `modes/` contra el canónico.

Contexto: en el canónico "modo" son TRES ejes ortogonales (sesión coordinator/normal,
backgrounding por-task, fork). El runtime los colapsa en `AgentMode` + `ModeManager`,
que — el hallazgo central — NO está cableado a ninguna ruta de ejecución. La ruta real
de backgrounding vive en `execution/tasks/registry.TaskRecord.is_backgrounded` (KIND) +
`execution/local/notification` (canal <task-notification>).

Estos tests fijan:
- lo homologado (ejes ortogonales: KIND fija toolset, flag mutable no re-filtra) — ya cubierto
  en test_modes_background.py; aquí se afirma la relación modes/ ↔ ruta real.
- FIND-MODE1 (xfail strict): `ModeManager.on_complete` promete gobernar la notificación,
  pero `LocalAgentRuntime._notify` la encola incondicionalmente (runtime.py:408). El manager
  no gobierna nada.
"""
import inspect

import pytest

from agentic_runtime.modes import AgentMode, ModeManager


# --- lo homologado: modes/ existe y su semántica local es coherente ----------

def test_agentmode_enumerates_three_conflated_axes():
    """AgentMode colapsa fg/bg (eje backgrounding) + fork (eje aislamiento)."""
    assert {m.value for m in AgentMode} == {"foreground", "background", "fork"}


def test_mode_manager_local_semantics_are_self_consistent():
    """En aislamiento el manager es coherente: BACKGROUND ⇒ on_complete True."""
    mgr = ModeManager()
    mgr.register(task_id="t1", mode=AgentMode.BACKGROUND)
    assert mgr.on_complete("t1") is True
    mgr.set_mode("t1", AgentMode.FOREGROUND)
    assert mgr.on_complete("t1") is False


# --- FIND-MODE1: el manager NO gobierna la notificación real -----------------

@pytest.mark.xfail(
    strict=True,
    reason="FIND-MODE1: LocalAgentRuntime._notify encola la notificación de forma "
    "incondicional (gateada sólo por parent_session_id, runtime.py:408); nunca "
    "consulta ModeManager.on_complete. El subsistema modes/ está huérfano.",
)
def test_mode_manager_gates_notification():
    """La notificación al completar DEBERÍA consultar ModeManager.on_complete.

    Se comprueba estructuralmente: el source de la ruta de notificación del
    LocalAgentRuntime debería referenciar el ModeManager / on_complete. Hoy no lo
    hace — la decisión "¿notifico?" la toma un `if parent_session_id is not None`.
    """
    from agentic_runtime.execution.local import runtime as local_runtime

    src = inspect.getsource(local_runtime)
    # Si modes/ estuviera cableado, la ruta de notificación consultaría al manager.
    assert "on_complete" in src or "ModeManager" in src or "AgentMode" in src
