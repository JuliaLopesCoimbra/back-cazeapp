from sqlalchemy import func
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.domain.admin.models.tshirt_reservation_model import TshirtReservation


class TshirtReservationRepository:

    @staticmethod
    def get_any_by_user_id(db: Session, user_id: int) -> TshirtReservation | None:
        return (
            db.query(TshirtReservation)
            .filter(TshirtReservation.user_id == user_id)
            .first()
        )

    @staticmethod
    def count_pending_for_item(db: Session, stock_item_id: int) -> int:
        return (
            db.query(func.count(TshirtReservation.id))
            .filter(
                TshirtReservation.stock_item_id == stock_item_id,
                TshirtReservation.status == "pending_pickup",
            )
            .scalar()
            or 0
        )

    @staticmethod
    def count_picked_up_for_item(db: Session, stock_item_id: int) -> int:
        return (
            db.query(func.count(TshirtReservation.id))
            .filter(
                TshirtReservation.stock_item_id == stock_item_id,
                TshirtReservation.status == "picked_up",
            )
            .scalar()
            or 0
        )

    @staticmethod
    def get_by_qr_token(db: Session, token: str) -> TshirtReservation | None:
        return (
            db.query(TshirtReservation)
            .filter(TshirtReservation.qr_token == token)
            .first()
        )

    @staticmethod
    def create(db: Session, data: dict) -> TshirtReservation:
        row = TshirtReservation(**data)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def list_admin(db: Session, limit: int = 100, offset: int = 0) -> list[TshirtReservation]:
        return (
            db.query(TshirtReservation)
            .order_by(desc(TshirtReservation.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
