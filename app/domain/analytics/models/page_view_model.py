from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from app.config.auth_db import Base


class PageView(Base):
    __tablename__ = "page_views"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    path = Column(String(255), nullable=False, index=True)
    referrer_path = Column(String(255), nullable=True)
    device_type = Column(String(20), nullable=True)  # mobile | tablet | desktop
    duration_seconds = Column(Integer, nullable=True)
    event_id = Column(Integer, nullable=True, index=True)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_pv_path_date", "path", "viewed_at"),
        Index("idx_pv_session_date", "session_id", "viewed_at"),
    )
