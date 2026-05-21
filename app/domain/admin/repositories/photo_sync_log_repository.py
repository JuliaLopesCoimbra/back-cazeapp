from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from app.domain.admin.models.photo_sync_log_model import PhotoSyncLog


class PhotoSyncLogRepository:
    @staticmethod
    def create(db: Session, data: dict) -> PhotoSyncLog:
        entry = PhotoSyncLog(**data)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def get_last(db: Session, event_id: Optional[str] = None) -> Optional[PhotoSyncLog]:
        q = db.query(PhotoSyncLog)
        if event_id:
            q = q.filter(PhotoSyncLog.event_id == event_id)
        return q.order_by(desc(PhotoSyncLog.cycle_at)).first()

    @staticmethod
    def get_last_with_drive_count(db: Session, event_id: Optional[str] = None) -> Optional[PhotoSyncLog]:
        q = db.query(PhotoSyncLog).filter(PhotoSyncLog.total_drive_files > 0)
        if event_id:
            q = q.filter(PhotoSyncLog.event_id == event_id)
        return q.order_by(desc(PhotoSyncLog.cycle_at)).first()

    @staticmethod
    def list_recent(db: Session, limit: int = 20, event_id: Optional[str] = None) -> List[PhotoSyncLog]:
        q = db.query(PhotoSyncLog)
        if event_id:
            q = q.filter(PhotoSyncLog.event_id == event_id)
        return q.order_by(desc(PhotoSyncLog.cycle_at)).limit(limit).all()

    @staticmethod
    def list_uploads(db: Session, limit: int = 50, event_id: Optional[str] = None) -> List[PhotoSyncLog]:
        q = db.query(PhotoSyncLog).filter(PhotoSyncLog.uploaded > 0)
        if event_id:
            q = q.filter(PhotoSyncLog.event_id == event_id)
        return q.order_by(desc(PhotoSyncLog.cycle_at)).limit(limit).all()

    @staticmethod
    def sum_indexed_today(db: Session, event_id: Optional[str] = None) -> int:
        today = datetime.utcnow().date()
        q = db.query(func.sum(PhotoSyncLog.indexed)).filter(
            func.date(PhotoSyncLog.cycle_at) == today
        )
        if event_id:
            q = q.filter(PhotoSyncLog.event_id == event_id)
        return q.scalar() or 0

    @staticmethod
    def sum_uploaded_total(db: Session, event_id: Optional[str] = None) -> int:
        q = db.query(func.sum(PhotoSyncLog.uploaded))
        if event_id:
            q = q.filter(PhotoSyncLog.event_id == event_id)
        return q.scalar() or 0

    @staticmethod
    def delete_older_than(db: Session, days: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(PhotoSyncLog).filter(PhotoSyncLog.cycle_at < cutoff).delete()
        db.commit()
        return deleted

    @staticmethod
    def count_today(db: Session, event_id: Optional[str] = None) -> int:
        today = datetime.utcnow().date()
        q = db.query(func.count(PhotoSyncLog.id)).filter(
            func.date(PhotoSyncLog.cycle_at) == today
        )
        if event_id:
            q = q.filter(PhotoSyncLog.event_id == event_id)
        return q.scalar() or 0
