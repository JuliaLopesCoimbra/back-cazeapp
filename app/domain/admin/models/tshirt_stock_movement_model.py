from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.config.admin_db import AdminBase


class TshirtStockMovement(AdminBase):
    __tablename__ = "tshirt_stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    stock_item_id = Column(
        Integer,
        ForeignKey("tshirt_stock_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    size = Column(String(10), nullable=False)
    direction = Column(String(3), nullable=False)  # "in" | "out"
    quantity = Column(Integer, nullable=False)
    performed_by_id = Column(Integer, nullable=False)
    performed_by_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    stock_item = relationship("TshirtStockItem", back_populates="movements")
