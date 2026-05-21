from fastapi import APIRouter, Depends, Response
from app.core.security.auth_dependency import get_current_user
from app.config.notification_db import get_notification_db
from app.domain.auth.models.user_model import User
from app.domain.users.controllers.notification_preference_controller import NotificationPreferenceController
from app.domain.users.schemas.notification_preference_schema import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate
)
from app.infra.onesignal import delete_user_by_external_id

router = APIRouter(prefix="/notifications", tags=["Notification Preferences"])

@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_notification_preferences(
    notification_db = Depends(get_notification_db),
    user: User = Depends(get_current_user)
):
    """Retorna as preferências de notificações do usuário"""
    return NotificationPreferenceController.get(notification_db, user.id)

@router.put("/preferences", response_model=NotificationPreferenceResponse)
def update_notification_preferences(
    data: NotificationPreferenceUpdate,
    notification_db = Depends(get_notification_db),
    user: User = Depends(get_current_user)
):
    """Atualiza as preferências de notificações do usuário"""
    return NotificationPreferenceController.update(notification_db, user.id, data)


@router.delete("/onesignal-identity", status_code=204)
def delete_onesignal_identity(user: User = Depends(get_current_user)):
    """Deleta o external_id do usuário no OneSignal para resolver conflito de alias."""
    delete_user_by_external_id(user.id)
    return Response(status_code=204)

