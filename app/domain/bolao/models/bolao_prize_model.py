from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.config.roulette_db import RouletteBase


class BolaoPrize(RouletteBase):
    __tablename__ = "bolao_prizes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    total_quantity = Column(Integer, nullable=False, default=0)   # 0 = ilimitado
    remaining_qty = Column(Integer, nullable=False, default=0)
    points_required = Column(Integer, nullable=False)
    # shirt | ticket | merch | digital
    prize_type = Column(String(50), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
