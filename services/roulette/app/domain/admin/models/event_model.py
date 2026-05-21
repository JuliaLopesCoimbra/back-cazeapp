from sqlalchemy import Column, Integer, DateTime
from app.config.admin_db import AdminBase


class Event(AdminBase):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
