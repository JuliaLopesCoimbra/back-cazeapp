from sqlalchemy.orm import Session

from app.domain.admin.services.tshirt_stock_service import TshirtStockService


class TshirtStockController:

    @staticmethod
    def list_all(db: Session):
        return TshirtStockService.list_all(db)

    @staticmethod
    def get_by_id(db: Session, item_id: int):
        return TshirtStockService.get_by_id(db, item_id)

    @staticmethod
    def create(db: Session, size: str, quantity: int, user):
        return TshirtStockService.create(db, size, quantity, user)

    @staticmethod
    def update(db: Session, item_id: int, quantity: int, user):
        return TshirtStockService.update_quantity(db, item_id, quantity, user)

    @staticmethod
    def delete(db: Session, item_id: int):
        TshirtStockService.delete(db, item_id)

    @staticmethod
    def list_movements(db: Session, limit: int, offset: int):
        return TshirtStockService.list_movements(db, limit, offset)

    @staticmethod
    def add_movement(db: Session, item_id: int, direction: str, quantity: int, user):
        return TshirtStockService.add_movement(db, item_id, direction, quantity, user)
