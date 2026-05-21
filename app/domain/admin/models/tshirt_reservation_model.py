from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.config.admin_db import AdminBase


class TshirtReservation(AdminBase):
    __tablename__ = "tshirt_reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    stock_item_id = Column(
        Integer,
        ForeignKey("tshirt_stock_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    size = Column(String(10), nullable=False)
    qr_token = Column(String(64), nullable=False, unique=True, index=True)
    user_name_snapshot = Column(String(255), nullable=False)
    user_email_snapshot = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="pending_pickup", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    picked_up_at = Column(DateTime, nullable=True)
    picked_up_by_id = Column(Integer, nullable=True)
    picked_up_by_name = Column(String(255), nullable=True)

    stock_item = relationship("TshirtStockItem", backref="tshirt_reservations")
