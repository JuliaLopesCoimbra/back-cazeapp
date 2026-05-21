from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.domain.admin.models.tshirt_stock_movement_model import TshirtStockMovement


class TshirtStockMovementRepository:

    @staticmethod
    def list_all(
        db: Session, limit: int = 100, offset: int = 0
    ) -> list[TshirtStockMovement]:
        return (
            db.query(TshirtStockMovement)
            .order_by(desc(TshirtStockMovement.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
