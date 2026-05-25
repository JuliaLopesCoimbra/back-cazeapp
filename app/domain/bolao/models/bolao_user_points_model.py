from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.config.roulette_db import RouletteBase


class BolaoUserPoints(RouletteBase):
    __tablename__ = "bolao_user_points"

    user_id = Column(Integer, primary_key=True)
    total_points = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
