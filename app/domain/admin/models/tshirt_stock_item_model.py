from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.admin_db import AdminBase


class TshirtStockItem(AdminBase):
    __tablename__ = "tshirt_stock_items"

    id = Column(Integer, primary_key=True, index=True)
    size = Column(String(10), unique=True, nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    updated_by_id = Column(Integer, nullable=True)

    movements = relationship(
        "TshirtStockMovement",
        back_populates="stock_item",
        cascade="all, delete-orphan",
    )


# Garante registro do modelo irmão antes de configure_mappers (ex.: seed só importa TshirtStockItem).
from app.domain.admin.models.tshirt_stock_movement_model import (  # noqa: E402, F401
    TshirtStockMovement,
)
