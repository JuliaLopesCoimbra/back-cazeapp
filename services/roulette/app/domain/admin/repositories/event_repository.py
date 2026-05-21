from sqlalchemy.orm import Session
from app.domain.admin.models.event_model import Event


class EventRepository:
    @staticmethod
    def get_by_id(db: Session, event_id: int, include_deleted: bool = False, force_db: bool = False):
        query = db.query(Event).filter(Event.id == event_id)
        if not include_deleted:
            query = query.filter(Event.deleted_at.is_(None))
        return query.first()
