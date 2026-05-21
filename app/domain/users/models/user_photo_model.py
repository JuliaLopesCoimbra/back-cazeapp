from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.config.interaction_db import InteractionBase


class UserPhoto(InteractionBase):
    __tablename__ = "user_photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    event_id = Column(String(50), nullable=False, index=True)
    drive_file_id = Column(String(255), nullable=False)
    s3_key = Column(String(500), nullable=True)
    similarity = Column(Float, nullable=True)
    notified = Column(Boolean, default=False, nullable=False)
    associated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "drive_file_id", name="uq_user_photo_user_drive"),
        Index("idx_user_photos_user_id", "user_id"),
        Index("idx_user_photos_event_id", "event_id"),
        Index("idx_user_photos_user_event", "user_id", "event_id"),
    )
