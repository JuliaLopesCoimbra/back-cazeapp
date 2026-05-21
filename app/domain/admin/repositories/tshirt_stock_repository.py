from typing import Optional, List
from sqlalchemy.orm import Session

from app.domain.admin.models.tshirt_stock_item_model import TshirtStockItem


class TshirtStockRepository:

    @staticmethod
    def list_all(db: Session) -> List[TshirtStockItem]:
        return db.query(TshirtStockItem).all()

    @staticmethod
    def get_by_id(db: Session, item_id: int) -> Optional[TshirtStockItem]:
        return db.query(TshirtStockItem).filter(TshirtStockItem.id == item_id).first()

    @staticmethod
    def get_by_size(db: Session, size: str) -> Optional[TshirtStockItem]:
        return db.query(TshirtStockItem).filter(TshirtStockItem.size == size).first()

    @staticmethod
    def create(db: Session, data: dict) -> TshirtStockItem:
        row = TshirtStockItem(**data)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def update(db: Session, item: TshirtStockItem, data: dict) -> TshirtStockItem:
        for key, value in data.items():
            setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete(db: Session, item: TshirtStockItem) -> None:
        db.delete(item)
        db.commit()
