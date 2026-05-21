from sqlalchemy.orm import Session
from app.domain.users.models.user_photo_model import UserPhoto


class UserPhotoRepository:
    @staticmethod
    def get(db: Session, user_id: int, event_id: str, drive_file_id: str) -> UserPhoto | None:
        return db.query(UserPhoto).filter(
            UserPhoto.user_id == user_id,
            UserPhoto.event_id == event_id,
            UserPhoto.drive_file_id == drive_file_id,
        ).first()

    @staticmethod
    def list_by_user_event(db: Session, user_id: int, event_id: str) -> list[UserPhoto]:
        return (
            db.query(UserPhoto)
            .filter(UserPhoto.user_id == user_id, UserPhoto.event_id == event_id)
            .order_by(UserPhoto.associated_at.desc())
            .all()
        )

    @staticmethod
    def create(db: Session, data: dict) -> UserPhoto:
        record = UserPhoto(**data)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def mark_notified(db: Session, user_id: int, event_id: str, drive_file_id: str):
        db.query(UserPhoto).filter(
            UserPhoto.user_id == user_id,
            UserPhoto.event_id == event_id,
            UserPhoto.drive_file_id == drive_file_id,
        ).update({"notified": True})
        db.commit()

    @staticmethod
    def count_by_drive_file(db: Session, event_id: str, drive_file_id: str) -> int:
        return (
            db.query(UserPhoto)
            .filter(UserPhoto.event_id == event_id, UserPhoto.drive_file_id == drive_file_id)
            .count()
        )
