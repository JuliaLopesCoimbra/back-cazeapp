from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String
from app.config.admin_db import AdminBase


class PhotoSyncLog(AdminBase):
    __tablename__ = "photo_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), nullable=False, index=True)
    server_name = Column(String(100), nullable=False, default="")
    cycle_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    new_files = Column(Integer, nullable=False, default=0)
    uploaded = Column(Integer, nullable=False, default=0)
    indexed = Column(Integer, nullable=False, default=0)
    no_face = Column(Integer, nullable=False, default=0)
    errors = Column(Integer, nullable=False, default=0)
    duration_seconds = Column(Float, nullable=False, default=0.0)
    total_drive_files = Column(Integer, nullable=False, default=0)
