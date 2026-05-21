from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Index
from sqlalchemy.sql import func
from app.config.admin_db import AdminBase


class FaceSearch(AdminBase):
    __tablename__ = "face_searches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    event_id = Column(Integer, nullable=False, index=True)
    collection_id = Column(String(255), nullable=False, index=True)
    threshold = Column(Float, nullable=True)
    max_faces = Column(Integer, nullable=True)
    face_detected = Column(Boolean, nullable=True)
    face_confidence = Column(Float, nullable=True)
    matches_count = Column(Integer, default=0)
    searched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_face_searches_user_id", "user_id"),
        Index("idx_face_searches_event_id", "event_id"),
        Index("idx_face_searches_searched_at", "searched_at"),
        Index("idx_face_searches_collection_id", "collection_id"),
        Index("idx_face_searches_event_collection", "event_id", "collection_id", "searched_at"),
    )
