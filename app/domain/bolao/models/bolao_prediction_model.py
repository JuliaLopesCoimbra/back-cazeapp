from sqlalchemy import Column, Integer, SmallInteger, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.config.roulette_db import RouletteBase


class BolaoPredicition(RouletteBase):
    __tablename__ = "bolao_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    home_score_prediction = Column(SmallInteger, nullable=False)
    away_score_prediction = Column(SmallInteger, nullable=False)
    points_earned = Column(Integer, nullable=False, default=0)
    # pending | exact | outcome | wrong | cancelled
    status = Column(String(20), nullable=False, default="pending")
    settled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "fixture_id", name="uq_bolao_user_fixture"),
    )
