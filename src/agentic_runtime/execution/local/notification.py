"""
BackgroundNotificationChannel — canal de notificaciones para agentes background.

El agente hijo escribe al canal al terminar (sin referencia viva al objeto Session
del padre). El loop padre drena el canal al inicio de cada turno, convierte las
entradas en mensajes <task-notification> y aplica display_messages si corresponde.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..session import Session

logger = logging.getLogger(__name__)

# Canal scopeado por (user_id, session_id): la identidad de ciclo de vida es el par,
# no la sesión sola — así no hay fuga entre usuarios aunque dos compartan session_id.
_channel: dict[tuple[str, str], list[BackgroundNotification]] = defaultdict(list)


@dataclass
class BackgroundNotification:
    parent_session_id: str
    task_id: str
    status: str  # "completed" | "failed" | "killed"
    description: str
    notification_text: str
    parent_user_id: str = ""
    final_text: str = ""
    parent_execution_id: str = ""


def put_notification(notification: BackgroundNotification) -> None:
    _channel[(notification.parent_user_id, notification.parent_session_id)].append(notification)
    logger.debug(
        "notification queued: user=%s session=%s task=%s status=%s",
        notification.parent_user_id, notification.parent_session_id,
        notification.task_id, notification.status,
    )


def drain_notifications(user_id: str, session_id: str) -> list[BackgroundNotification]:
    return _channel.pop((user_id, session_id), [])


def process_background_notification(session: "Session", notification: BackgroundNotification) -> None:
    """Comportamiento genérico del runtime: actualiza el ref del subagente en el
    padre e inyecta un mensaje <task-notification> en su historial.

    La presentación (display) y la persistencia NO son responsabilidad de esta
    función: el runtime emite eventos y persiste vía StorageProtocol; el consumidor
    proyecta su UI escuchando esos eventos (G2/D4).
    """
    for ref in session.metadata.background_tasks:
        if ref.task_id == notification.task_id:
            ref.status = notification.status
            break

    xml = (
        f'<task-notification task_id="{notification.task_id}" status="{notification.status}">\n'
        f"<description>{notification.description}</description>\n"
        f"<result>{notification.notification_text}</result>\n"
        f"</task-notification>"
    )
    session.messages.append({"role": "user", "content": xml})
    logger.debug(
        "notification processed: session=%s task=%s status=%s",
        session.session_id, notification.task_id, notification.status,
    )
