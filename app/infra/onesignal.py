import logging
import requests
from app.config.settings import settings

logger = logging.getLogger(__name__)

ONESIGNAL_URL = "https://onesignal.com/api/v1/notifications"


def _headers() -> dict:
    return {
        "Authorization": f"Key {settings.ONESIGNAL_API_KEY}",
        "Content-Type": "application/json",
    }


def _send(payload: dict) -> bool:
    if not settings.ONESIGNAL_APP_ID or not settings.ONESIGNAL_API_KEY:
        logger.warning("OneSignal não configurado — notificação push ignorada.")
        return False
    try:
        payload["app_id"] = settings.ONESIGNAL_APP_ID
        response = requests.post(ONESIGNAL_URL, json=payload, headers=_headers(), timeout=10)
        logger.info("[OneSignal] payload keys=%s status=%s body=%s", list(payload.keys()), response.status_code, response.text[:300])
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar notificação pelo OneSignal: {e}")
        return False


def send_to_user(user_id: int, title: str, message: str) -> bool:
    """Envia notificação para um usuário específico pelo ID do banco."""
    return _send({
        "include_aliases": {"external_id": [f"n1_{user_id}"]},
        "target_channel": "push",
        "headings": {"en": title, "pt": title},
        "contents": {"en": message, "pt": message},
    })


def delete_user_by_external_id(user_id: int) -> bool:
    """Deleta usuário OneSignal pelo external_id para resolver conflito de alias."""
    if not settings.ONESIGNAL_APP_ID or not settings.ONESIGNAL_API_KEY:
        return False
    try:
        url = f"https://api.onesignal.com/apps/{settings.ONESIGNAL_APP_ID}/users/by/external_id/n1_{user_id}"
        response = requests.delete(url, headers=_headers(), timeout=10)
        logger.info("[OneSignal] delete external_id=n1_%s status=%s", user_id, response.status_code)
        return response.status_code in (200, 202, 204, 404)
    except Exception as e:
        logger.error(f"Erro ao deletar usuário OneSignal: {e}")
        return False


def send_to_all(title: str, message: str, excluded_user_ids: list = None) -> bool:
    """Envia notificação para todos os usuários inscritos, excluindo quem desativou push."""
    payload = {
        "included_segments": ["All"],
        "headings": {"en": title, "pt": title},
        "contents": {"en": message, "pt": message},
    }
    if excluded_user_ids:
        payload["excluded_external_user_ids"] = [f"n1_{uid}" for uid in excluded_user_ids]
    return _send(payload)


def send_for_category(category_tag: str, title: str, message: str) -> bool:
    """Envia broadcast para todos os subscribers. Filtragem por categoria pode ser
    reativada futuramente via tags quando houver base de usuários com preferências salvas."""
    payload = {
        "included_segments": ["All"],
        "headings": {"en": title, "pt": title},
        "contents": {"en": message, "pt": message},
    }
    return _send(payload)
