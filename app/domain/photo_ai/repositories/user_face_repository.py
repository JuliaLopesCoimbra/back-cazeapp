from sqlalchemy.orm import Session
from app.domain.photo_ai.models.user_face_model import UserFace


class UserFaceRepository:
    @staticmethod
    def get_by_user_event(db: Session, user_id: int, event_id: str) -> UserFace | None:
        return db.query(UserFace).filter(
            UserFace.user_id == user_id,
            UserFace.event_id == event_id,
        ).first()

    @staticmethod
    def create(db: Session, data: dict) -> UserFace:
        record = UserFace(**data)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete(db: Session, user_face: UserFace):
        db.delete(user_face)
        db.commit()

    @staticmethod
    def list_by_event(db: Session, event_id: str) -> list[UserFace]:
        return db.query(UserFace).filter(UserFace.event_id == event_id).all()
