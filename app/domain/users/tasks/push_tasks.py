import logging
from app.infra.celery_app import celery_app
from app.config.notification_db import get_notification_db
from app.infra.onesignal import send_to_user

logger = logging.getLogger(__name__)


@celery_app.task(name='notifications.send_push_for_notification', bind=True, max_retries=2)
def send_push_for_notification_task(self, notification_id: int):
    """Envia Web Push via OneSignal para o usuário dono da notificação."""
    from app.domain.users.models.notification_model import Notification

    from app.domain.users.repositories.notification_preference_repository import NotificationPreferenceRepository

    notification_db = next(get_notification_db())
    try:
        notification = notification_db.query(Notification).filter(
            Notification.id == notification_id
        ).first()
        if not notification:
            logger.warning("[Push] Notificação id=%s não encontrada.", notification_id)
            return

        pref = NotificationPreferenceRepository.get_by_user(notification_db, notification.user_id)
        if pref and pref.push_enabled is False:
            logger.info("[Push] Usuário %s desativou push — notificação %s ignorada.", notification.user_id, notification_id)
            return

        send_to_user(
            user_id=notification.user_id,
            title=(notification.title or "")[:60],
            message=(notification.message or "")[:80],
        )
        logger.info("[Push] Notificação id=%s enviada via OneSignal para user_id=%s", notification_id, notification.user_id)
    except Exception as e:
        logger.exception("[Push] Erro ao enviar notificação %s: %s", notification_id, e)
        raise self.retry(exc=e, countdown=30)
    finally:
        notification_db.close()
