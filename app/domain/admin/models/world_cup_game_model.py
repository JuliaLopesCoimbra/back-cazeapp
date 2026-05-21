from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.config.admin_db import AdminBase


class WorldCupGame(AdminBase):
    __tablename__ = "world_cup_games"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    game_date = Column(Date, nullable=True)
    game_time = Column(Time, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    updated_by_id = Column(Integer, nullable=True)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, nullable=True)

    event = relationship("Event", backref="world_cup_games")
