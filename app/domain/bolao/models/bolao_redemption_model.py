from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.config.roulette_db import RouletteBase


class BolaoRedemption(RouletteBase):
    __tablename__ = "bolao_redemptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    prize_id = Column(Integer, ForeignKey("bolao_prizes.id"), nullable=False)
    points_spent = Column(Integer, nullable=False)
    # pending | approved | delivered | cancelled
    status = Column(String(20), nullable=False, default="pending")
    admin_notes = Column(Text, nullable=True)
    redeemed_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
