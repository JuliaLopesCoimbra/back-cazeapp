import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config.roulette_db import get_roulette_db
from app.domain.auth.controllers.auth_controller import get_current_user
from app.domain.auth.models.user_model import User
from app.domain.bolao.controllers.bolao_controller import BolaoController
from app.domain.bolao.schemas.bolao_schema import (
    BolaoPredicitionCreate,
    BolaoPredicitionResponse,
    BolaoFixtureResponse,
    BolaoRankingEntry,
    BolaoMyPoints,
    BolaoPrizeResponse,
    BolaoPrizeCreate,
    BolaoRedeemRequest,
    BolaoRedemptionResponse,
)

router = APIRouter(prefix="/bolao", tags=["bolao"])


@router.get("/fixtures", response_model=list[BolaoFixtureResponse])
def get_fixtures(
    db: Session = Depends(get_roulette_db),
    current_user: User = Depends(get_current_user),
):
    return BolaoController.get_fixtures(db, current_user)


@router.post("/predictions", response_model=BolaoPredicitionResponse, status_code=201)
def create_prediction(
    data: BolaoPredicitionCreate,
    db: Session = Depends(get_roulette_db),
    current_user: User = Depends(get_current_user),
):
    return BolaoController.create_prediction(db, current_user, data)


@router.get("/ranking", response_model=list[BolaoRankingEntry])
def get_ranking(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_roulette_db),
    current_user: User = Depends(get_current_user),
):
    return BolaoController.get_ranking(db, limit=min(limit, 100), offset=offset)


@router.get("/my-points", response_model=BolaoMyPoints)
def get_my_points(
    db: Session = Depends(get_roulette_db),
    current_user: User = Depends(get_current_user),
):
    return BolaoController.get_my_points(db, current_user)


@router.get("/prizes", response_model=list[BolaoPrizeResponse])
def list_prizes(
    db: Session = Depends(get_roulette_db),
    current_user: User = Depends(get_current_user),
):
    return BolaoController.list_prizes(db)


@router.post("/prizes", response_model=BolaoPrizeResponse, status_code=201)
def create_prize(
    data: BolaoPrizeCreate,
    db: Session = Depends(get_roulette_db),
    current_user: User = Depends(get_current_user),
):
    return BolaoController.create_prize(db, current_user, data)


@router.post("/redeem", response_model=BolaoRedemptionResponse, status_code=201)
def redeem_prize(
    data: BolaoRedeemRequest,
    db: Session = Depends(get_roulette_db),
    current_user: User = Depends(get_current_user),
):
    return BolaoController.redeem_prize(db, current_user, data)


@router.get("/my-redemptions", response_model=list[BolaoRedemptionResponse])
def my_redemptions(
    db: Session = Depends(get_roulette_db),
    current_user: User = Depends(get_current_user),
):
    return BolaoController.get_my_redemptions(db, current_user)


# ── Dev/test only ──────────────────────────────────────────────────────────────

def _guard_dev(current_user: User):
    if os.getenv("ENV") == "production":
        raise HTTPException(status_code=403, detail="Indisponível em produção")
    if current_user.role not in ("admin_master", "subadmin"):
        raise HTTPException(status_code=403, detail="Acesso negado")


class SettleTestPayload(BaseModel):
    fixture_id: int
    actual_home: int
    actual_away: int


@router.post("/dev/settle", include_in_schema=False)
def dev_settle_fixture(
    data: SettleTestPayload,
    db: Session = Depends(get_roulette_db),
    current_user: User = Depends(get_current_user),
):
    _guard_dev(current_user)
    from app.domain.bolao.services.bolao_service import settle_predictions
    count = settle_predictions(db, data.fixture_id, data.actual_home, data.actual_away)
    return {"settled": count, "fixture_id": data.fixture_id,
            "result": f"{data.actual_home}x{data.actual_away}"}


@router.post("/dev/reset/{fixture_id}", include_in_schema=False)
def dev_reset_fixture(
    fixture_id: int,
    db: Session = Depends(get_roulette_db),
    current_user: User = Depends(get_current_user),
):
    _guard_dev(current_user)
    from app.domain.bolao.models.bolao_prediction_model import BolaoPredicition
    from app.domain.bolao.repositories.bolao_repository import BolaoUserPointsRepository

    settled = (
        db.query(BolaoPredicition)
        .filter(
            BolaoPredicition.fixture_id == fixture_id,
            BolaoPredicition.status != "pending",
        )
        .all()
    )

    for pred in settled:
        if pred.points_earned > 0:
            record = BolaoUserPointsRepository.get(db, pred.user_id)
            if record:
                record.total_points = max(0, record.total_points - pred.points_earned)
        pred.status = "pending"
        pred.points_earned = 0
        pred.settled_at = None

    db.commit()
    return {"reset": len(settled), "fixture_id": fixture_id}
