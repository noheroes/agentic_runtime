"""
Canal en-proceso de notificaciones background — implementación concreta de `S21`.

El agente hijo escribe al canal al terminar (sin referencia viva al objeto Session del
padre). El loop del padre lo **drena al arrancar su run** y aplica cada entrada al
historial vivo con `apply_notification` (`contracts/notifications.py`). Hasta `C8` ese
drain **no existía**: el docstring lo afirmaba y ningún productor lo llamaba (CORE-GAP
`H-5`), así que el padre no se enteraba nunca de que su subagente había terminado.

El contrato (`BackgroundNotification`, `NotificationSink`, `apply_notification`) vive en
`contracts/notifications.py`; aquí sólo el canal.
"""
from __future__ import annotations

import logging
from collections import defaultdict

from ...contracts.notifications import BackgroundNotification

logger = logging.getLogger(__name__)

# Canal scopeado por (scope, session_id): la frontera de aislamiento es el par, no la
# sesión sola — así no hay fuga entre tenants aunque dos compartan `session_id`. El
# primer componente era `user_id` y pasa a ser la clave del `Scope` (`C9`/`ID-3`): el
# runtime ya no conoce usuarios, sólo scopes opacos que le da el integrador.
_channel: dict[tuple[str, str], list[BackgroundNotification]] = defaultdict(list)


def put_notification(notification: BackgroundNotification) -> None:
    _channel[(notification.parent_scope, notification.parent_session_id)].append(notification)
    logger.debug(
        "notification queued: scope=%s session=%s task=%s status=%s",
        notification.parent_scope, notification.parent_session_id,
        notification.task_id, notification.status,
    )


def drain_notifications(scope: str, session_id: str) -> list[BackgroundNotification]:
    return _channel.pop((scope, session_id), [])


class InProcessNotificationSink:
    """`NotificationSink` por defecto del runtime: el canal global de este proceso.

    Es el default que mantiene al runtime ejecutable por sí solo. Un integrador
    multi-proceso inyecta el suyo (`RuntimeConfig.notification_sink`) sobre su propio
    transporte; el loop no distingue.
    """

    def put(self, notification: BackgroundNotification) -> None:
        put_notification(notification)

    def drain(self, scope: str, session_id: str) -> list[BackgroundNotification]:
        return drain_notifications(scope, session_id)


__all__ = [
    "BackgroundNotification",
    "InProcessNotificationSink",
    "drain_notifications",
    "put_notification",
]
