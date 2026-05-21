from typing import Optional
from sqlalchemy.orm import Session
from app.domain.admin.schemas.photo_sync_schema import PhotoSyncHeartbeatSchema, PhotoSyncStatusSchema
from app.domain.admin.services.photo_sync_service import PhotoSyncService


class PhotoSyncController:
    @staticmethod
    def record_heartbeat(db: Session, data: PhotoSyncHeartbeatSchema):
        PhotoSyncService.record_heartbeat(db, data)

    @staticmethod
    def get_status(db: Session, event_id: Optional[str] = None) -> PhotoSyncStatusSchema:
        return PhotoSyncService.get_status(db, event_id)
