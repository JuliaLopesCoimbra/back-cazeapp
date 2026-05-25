from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.domain.admin.repositories.photo_sync_log_repository import PhotoSyncLogRepository
from app.domain.admin.schemas.photo_sync_schema import (
    PhotoSyncHeartbeatSchema,
    PhotoSyncStatusSchema,
)

ALIVE_THRESHOLD_SECONDS = 600


class PhotoSyncService:
    @staticmethod
    def record_heartbeat(db: Session, data: PhotoSyncHeartbeatSchema):
        PhotoSyncLogRepository.create(db, {
            "event_id": data.event_id,
            "server_name": data.server_name,
            "new_files": data.new_files,
            "uploaded": data.uploaded,
            "indexed": data.indexed,
            "no_face": data.no_face,
            "errors": data.errors,
            "duration_seconds": data.duration_seconds,
            "total_drive_files": data.total_drive_files,
        })
        if datetime.utcnow().minute == 0:
            PhotoSyncLogRepository.delete_older_than(db, days=30)

        if data.new_s3_keys:
            try:
                from app.domain.admin.models.event_model import Event
                event = db.query(Event).filter(Event.id == int(data.event_id)).first()
                if event and event.brand_key == "n1_torcida":
                    from app.domain.photo_ai.tasks.face_matching_tasks import match_new_photos_task
                    match_new_photos_task.delay(data.event_id, data.new_s3_keys)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to queue face matching task: {e}")

    @staticmethod
    def get_status(db: Session, event_id: Optional[str] = None) -> PhotoSyncStatusSchema:
        last = PhotoSyncLogRepository.get_last(db, event_id)
        last_with_drive = PhotoSyncLogRepository.get_last_with_drive_count(db, event_id)
        recent = PhotoSyncLogRepository.list_recent(db, limit=20, event_id=event_id)
        uploads = PhotoSyncLogRepository.list_uploads(db, limit=50, event_id=event_id)
        total_indexed = PhotoSyncLogRepository.sum_indexed_today(db, event_id)
        total_cycles = PhotoSyncLogRepository.count_today(db, event_id)
        total_s3 = PhotoSyncLogRepository.sum_uploaded_total(db, event_id)

        is_alive = False
        seconds_since = None
        if last:
            delta = (datetime.utcnow() - last.cycle_at).total_seconds()
            seconds_since = int(delta)
            is_alive = delta < ALIVE_THRESHOLD_SECONDS

        return PhotoSyncStatusSchema(
            is_alive=is_alive,
            last_cycle_at=last.cycle_at if last else None,
            seconds_since_last_cycle=seconds_since,
            total_indexed_today=total_indexed,
            total_cycles_today=total_cycles,
            total_drive_files=last_with_drive.total_drive_files if last_with_drive else 0,
            total_s3_files=total_s3,
            recent_logs=recent,
            upload_logs=uploads,
        )
