from sqlalchemy.orm import Session

from app.domain.admin.services.tshirt_reservation_service import TshirtReservationService


class TshirtReservationController:

    @staticmethod
    def availability(db: Session):
        return TshirtReservationService.list_availability(db)

    @staticmethod
    def get_mine(db: Session, user_id: int):
        return TshirtReservationService.get_mine(db, user_id)

    @staticmethod
    def create(db: Session, user, size: str):
        return TshirtReservationService.create_for_user(db, user, size)

    @staticmethod
    def lookup_by_cpf(admin_db: Session, auth_db: Session, cpf: str) -> dict:
        return TshirtReservationService.lookup_by_cpf(admin_db, auth_db, cpf)

    @staticmethod
    def list_admin(db: Session, limit: int, offset: int):
        return TshirtReservationService.list_admin(db, limit, offset)

    @staticmethod
    def redeem(db: Session, token: str, promoter):
        return TshirtReservationService.redeem(db, token, promoter)
