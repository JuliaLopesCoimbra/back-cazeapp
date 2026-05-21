from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.auth.models.user_model import User
from app.domain.bolao.schemas.bolao_schema import (
    BolaoPredicitionCreate,
    BolaoRedeemRequest,
    BolaoPrizeCreate,
)
from app.domain.bolao import services as bolao_service
from app.domain.football.services.football_service import get_brazil_fixtures


class BolaoController:

    @staticmethod
    def get_fixtures(db: Session, user: User):
        raw = get_brazil_fixtures()
        return bolao_service.get_bolao_fixtures(db, user.id, raw)

    @staticmethod
    def create_prediction(db: Session, user: User,
                          data: BolaoPredicitionCreate):
        raw = get_brazil_fixtures()
        return bolao_service.create_or_update_prediction(db, user.id, data, raw)

    @staticmethod
    def get_ranking(db: Session, limit: int, offset: int):
        return bolao_service.get_ranking(db, limit=limit, offset=offset)

    @staticmethod
    def get_my_points(db: Session, user: User):
        return bolao_service.get_my_points(db, user.id)

    @staticmethod
    def list_prizes(db: Session):
        return bolao_service.list_prizes(db)

    @staticmethod
    def create_prize(db: Session, user: User, data: BolaoPrizeCreate):
        if user.role not in ("admin_master", "subadmin"):
            raise HTTPException(status_code=403, detail="Acesso negado")
        return bolao_service.create_prize(db, data)

    @staticmethod
    def redeem_prize(db: Session, user: User, data: BolaoRedeemRequest):
        return bolao_service.redeem_prize(db, user.id, data.prize_id)

    @staticmethod
    def get_my_redemptions(db: Session, user: User):
        from app.domain.bolao.repositories.bolao_repository import BolaoRedemptionRepository
        return BolaoRedemptionRepository.list_for_user(db, user.id)
