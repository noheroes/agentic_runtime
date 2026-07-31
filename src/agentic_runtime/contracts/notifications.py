"""
`S21` · `NotificationSink` — el canal `<task-notification>` padre↔hijo.

Contrato T1 del tramo 1 (`C8`), en el mismo tier que `contracts/user_input.py`: el
protocolo y el comportamiento GENÉRICO viven aquí, la implementación concreta del canal
en `execution/local/notification.py`, y el consumidor (`AgentLoop`) sólo conoce esto.

**Por qué la firma cambió** (`SEAMS §S21`, `AC-07`): la anterior era
`process_background_notification(session, n)` y **no podía funcionar aunque se cableara**
— hacía `session.messages.append(...)` mientras `_run_loop` reasigna
`session.messages = list(ctx.messages)` al terminar, de modo que el XML inyectado se
descartaba en silencio. El `Session` del runtime no es el historial vivo: es un sumidero
de copia. Por eso el comportamiento se expresa sobre **el historial vivo**
(`apply_notification(messages, n)`) y no sobre la sesión.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass
class BackgroundNotification:
    """Lo que el hijo deja en el canal al terminar, sin referencia viva al padre."""

    parent_session_id: str
    task_id: str
    status: str  # "completed" | "failed" | "killed"
    description: str
    notification_text: str
    # Clave del `Scope` del padre (`C9`/`ID-3`): el canal se escopa por el par
    # (scope, session_id) — la frontera de aislamiento es el par, no la sesión sola.
    parent_scope: str = ""
    final_text: str = ""


@runtime_checkable
class NotificationSink(Protocol):
    """Costura `S21`. El productor es el hijo (`put`), el consumidor el loop del padre
    (`drain`, un paso propio antes de componer el turno)."""

    def put(self, notification: BackgroundNotification) -> None: ...

    def drain(self, scope: str, session_id: str) -> list[BackgroundNotification]: ...


def render_notification(notification: BackgroundNotification) -> str:
    """El XML `<task-notification>` que ve el modelo del padre."""
    return (
        f'<task-notification task_id="{notification.task_id}" '
        f'status="{notification.status}">\n'
        f"<description>{notification.description}</description>\n"
        f"<result>{notification.notification_text}</result>\n"
        f"</task-notification>"
    )


def apply_notification(messages: list[Any], notification: BackgroundNotification) -> None:
    """Comportamiento genérico del runtime: aplica una notificación al **historial vivo**.

    Entra como `role:"user"` porque es lo que el canónico hace —las notificaciones viajan
    como *attachment* junto a la entrada del usuario (`query.ts:1631-1633`)—, no como un
    turno del asistente que el modelo pudiera creer suyo.

    La presentación (display) y la persistencia NO son de esta función: el runtime emite
    eventos y persiste vía `StorageProtocol`; el consumidor proyecta su UI escuchando esos
    eventos.
    """
    messages.append({"role": "user", "content": render_notification(notification)})


__all__ = [
    "BackgroundNotification",
    "NotificationSink",
    "apply_notification",
    "render_notification",
]
