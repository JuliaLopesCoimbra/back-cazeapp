from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.domain.bolao.repositories.bolao_repository import (
    BolaoPredicitionRepository,
    BolaoUserPointsRepository,
    BolaoPrizeRepository,
    BolaoRedemptionRepository,
)
from app.domain.bolao.schemas.bolao_schema import (
    BolaoPredicitionCreate,
    BolaoFixtureResponse,
    BolaoRankingEntry,
    BolaoMyPoints,
    UserPredictionSummary,
    BolaoPrizeCreate,
)


# ── Betting closes 5 minutes before the match ──────────────────────────────────

def _betting_closes_at(match_date_str: str) -> datetime:
    match_date = datetime.fromisoformat(match_date_str.replace("Z", "+00:00"))
    return match_date - timedelta(minutes=5)


def _is_betting_open(match_date_str: str) -> bool:
    closes_at = _betting_closes_at(match_date_str)
    return datetime.now(timezone.utc) < closes_at


# ── Fixtures endpoint ──────────────────────────────────────────────────────────

def get_bolao_fixtures(db: Session, user_id: int,
                       raw_fixtures: list) -> list[BolaoFixtureResponse]:
    user_predictions = {
        p.fixture_id: p
        for p in BolaoPredicitionRepository.get_all_for_user(db, user_id)
    }

    result = []
    for f in raw_fixtures:
        fixture_id = f["fixture"]["id"]
        match_date = f["fixture"]["date"]
        closes_at = _betting_closes_at(match_date)
        prediction = user_predictions.get(fixture_id)

        result.append(
            BolaoFixtureResponse(
                fixture_id=fixture_id,
                home_team=f["teams"]["home"]["name"],
                away_team=f["teams"]["away"]["name"],
                home_logo=f["teams"]["home"]["logo"],
                away_logo=f["teams"]["away"]["logo"],
                match_date=match_date,
                status=f["fixture"]["status"]["short"],
                betting_closes_at=closes_at.isoformat(),
                user_prediction=UserPredictionSummary(
                    home_score=prediction.home_score_prediction,
                    away_score=prediction.away_score_prediction,
                    points_earned=prediction.points_earned,
                    status=prediction.status,
                ) if prediction else None,
            )
        )
    return result


# ── Create / update prediction ─────────────────────────────────────────────────

def create_or_update_prediction(db: Session, user_id: int,
                                data: BolaoPredicitionCreate,
                                raw_fixtures: list):
    fixture = next(
        (f for f in raw_fixtures if f["fixture"]["id"] == data.fixture_id), None
    )
    if not fixture:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")

    if not _is_betting_open(fixture["fixture"]["date"]):
        raise HTTPException(status_code=400,
                            detail="Apostas encerradas para esse jogo ⏰")

    return BolaoPredicitionRepository.upsert(
        db,
        user_id=user_id,
        fixture_id=data.fixture_id,
        home=data.home_score_prediction,
        away=data.away_score_prediction,
    )


# ── Settle predictions (called by Celery task when match ends) ─────────────────

def _calc_points(home_pred: int, away_pred: int,
                 actual_home: int, actual_away: int) -> tuple[int, str]:
    if home_pred == actual_home and away_pred == actual_away:
        return 10, "exact"

    pred_outcome = ("home" if home_pred > away_pred
                    else "away" if away_pred > home_pred else "draw")
    actual_outcome = ("home" if actual_home > actual_away
                      else "away" if actual_away > actual_home else "draw")

    if pred_outcome == actual_outcome:
        return 5, "outcome"

    return 0, "wrong"


def settle_predictions(db: Session, fixture_id: int,
                       actual_home: int, actual_away: int) -> int:
    predictions = BolaoPredicitionRepository.get_pending_for_fixture(db, fixture_id)
    settled = 0

    for pred in predictions:
        points, status = _calc_points(
            pred.home_score_prediction, pred.away_score_prediction,
            actual_home, actual_away,
        )
        pred.points_earned = points
        pred.status = status
        pred.settled_at = datetime.now(timezone.utc)

        if points > 0:
            BolaoUserPointsRepository.add_points(db, pred.user_id, points)

        settled += 1

    db.commit()
    return settled


# ── Ranking ────────────────────────────────────────────────────────────────────

def get_ranking(db: Session, limit: int = 50,
                offset: int = 0) -> list[BolaoRankingEntry]:
    top = BolaoUserPointsRepository.get_ranking(db, limit=limit, offset=offset)
    result = []

    for i, up in enumerate(top):
        exact = BolaoPredicitionRepository.count_by_status(db, up.user_id, "exact")
        outcome = BolaoPredicitionRepository.count_by_status(db, up.user_id, "outcome")
        result.append(
            BolaoRankingEntry(
                rank=offset + i + 1,
                user_id=up.user_id,
                total_points=up.total_points,
                exact_predictions=exact,
                correct_outcomes=outcome,
            )
        )

    return result


# ── My points ─────────────────────────────────────────────────────────────────

def get_my_points(db: Session, user_id: int) -> BolaoMyPoints:
    record = BolaoUserPointsRepository.get(db, user_id)
    rank = BolaoUserPointsRepository.get_rank(db, user_id)
    exact = BolaoPredicitionRepository.count_by_status(db, user_id, "exact")
    outcome = BolaoPredicitionRepository.count_by_status(db, user_id, "outcome")

    return BolaoMyPoints(
        total_points=record.total_points if record else 0,
        rank=rank,
        exact_predictions=exact,
        correct_outcomes=outcome,
    )


# ── Prizes ─────────────────────────────────────────────────────────────────────

def list_prizes(db: Session):
    return BolaoPrizeRepository.list_active(db)


def create_prize(db: Session, data: BolaoPrizeCreate):
    return BolaoPrizeRepository.create(db, {
        "name": data.name,
        "description": data.description,
        "total_quantity": data.total_quantity,
        "remaining_qty": data.total_quantity,
        "points_required": data.points_required,
        "prize_type": data.prize_type,
    })


# ── Redeem ─────────────────────────────────────────────────────────────────────

def redeem_prize(db: Session, user_id: int, prize_id: int):
    prize = BolaoPrizeRepository.get_by_id(db, prize_id)
    if not prize:
        raise HTTPException(status_code=404, detail="Prêmio não encontrado")

    points_record = BolaoUserPointsRepository.get(db, user_id)
    user_points = points_record.total_points if points_record else 0

    if user_points < prize.points_required:
        raise HTTPException(
            status_code=400,
            detail=f"Você precisa de mais {prize.points_required - user_points} pontos 🏆",
        )

    if prize.total_quantity > 0 and prize.remaining_qty <= 0:
        raise HTTPException(status_code=400, detail="Prêmio esgotado 😢")

    # Atomically decrement qty and deduct points
    BolaoPrizeRepository.decrement_qty(db, prize_id)
    BolaoUserPointsRepository.deduct_points(db, user_id, prize.points_required)

    return BolaoRedemptionRepository.create(
        db, user_id=user_id, prize_id=prize_id,
        points_spent=prize.points_required,
    )
