from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from datetime import datetime
from typing import Optional

from app.domain.bolao.models.bolao_prediction_model import BolaoPredicition
from app.domain.bolao.models.bolao_prize_model import BolaoPrize
from app.domain.bolao.models.bolao_redemption_model import BolaoRedemption
from app.domain.bolao.models.bolao_user_points_model import BolaoUserPoints


# ── Predictions ────────────────────────────────────────────────────────────────

class BolaoPredicitionRepository:

    @staticmethod
    def upsert(db: Session, user_id: int, fixture_id: int,
               home: int, away: int) -> BolaoPredicition:
        existing = (
            db.query(BolaoPredicition)
            .filter_by(user_id=user_id, fixture_id=fixture_id)
            .first()
        )
        if existing:
            existing.home_score_prediction = home
            existing.away_score_prediction = away
            db.commit()
            db.refresh(existing)
            return existing

        prediction = BolaoPredicition(
            user_id=user_id,
            fixture_id=fixture_id,
            home_score_prediction=home,
            away_score_prediction=away,
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        return prediction

    @staticmethod
    def get_user_prediction(db: Session, user_id: int,
                            fixture_id: int) -> Optional[BolaoPredicition]:
        return (
            db.query(BolaoPredicition)
            .filter_by(user_id=user_id, fixture_id=fixture_id)
            .first()
        )

    @staticmethod
    def get_all_for_user(db: Session, user_id: int) -> list[BolaoPredicition]:
        return (
            db.query(BolaoPredicition)
            .filter_by(user_id=user_id)
            .order_by(BolaoPredicition.created_at.desc())
            .all()
        )

    @staticmethod
    def get_pending_for_fixture(db: Session,
                                fixture_id: int) -> list[BolaoPredicition]:
        return (
            db.query(BolaoPredicition)
            .filter_by(fixture_id=fixture_id, status="pending")
            .all()
        )

    @staticmethod
    def count_by_status(db: Session, user_id: int, status: str) -> int:
        return (
            db.query(BolaoPredicition)
            .filter_by(user_id=user_id, status=status)
            .count()
        )


# ── User Points ────────────────────────────────────────────────────────────────

class BolaoUserPointsRepository:

    @staticmethod
    def get(db: Session, user_id: int) -> Optional[BolaoUserPoints]:
        return db.query(BolaoUserPoints).filter_by(user_id=user_id).first()

    @staticmethod
    def add_points(db: Session, user_id: int, points: int) -> BolaoUserPoints:
        record = db.query(BolaoUserPoints).filter_by(user_id=user_id).first()
        if record:
            record.total_points += points
        else:
            record = BolaoUserPoints(user_id=user_id, total_points=points)
            db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def deduct_points(db: Session, user_id: int, points: int) -> BolaoUserPoints:
        record = db.query(BolaoUserPoints).filter_by(user_id=user_id).first()
        if not record or record.total_points < points:
            raise ValueError("Pontos insuficientes")
        record.total_points -= points
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_ranking(db: Session, limit: int = 50,
                    offset: int = 0) -> list[BolaoUserPoints]:
        return (
            db.query(BolaoUserPoints)
            .order_by(BolaoUserPoints.total_points.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_rank(db: Session, user_id: int) -> int:
        record = db.query(BolaoUserPoints).filter_by(user_id=user_id).first()
        if not record:
            return 0
        rank = (
            db.query(BolaoUserPoints)
            .filter(BolaoUserPoints.total_points > record.total_points)
            .count()
        )
        return rank + 1


# ── Prizes ─────────────────────────────────────────────────────────────────────

class BolaoPrizeRepository:

    @staticmethod
    def list_active(db: Session) -> list[BolaoPrize]:
        return (
            db.query(BolaoPrize)
            .filter_by(is_active=True)
            .order_by(BolaoPrize.points_required.asc())
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, prize_id: int) -> Optional[BolaoPrize]:
        return db.query(BolaoPrize).filter_by(id=prize_id, is_active=True).first()

    @staticmethod
    def create(db: Session, data: dict) -> BolaoPrize:
        prize = BolaoPrize(**data)
        db.add(prize)
        db.commit()
        db.refresh(prize)
        return prize

    @staticmethod
    def decrement_qty(db: Session, prize_id: int) -> BolaoPrize:
        prize = db.query(BolaoPrize).filter_by(id=prize_id).with_for_update().first()
        if not prize:
            raise ValueError("Prêmio não encontrado")
        if prize.total_quantity > 0 and prize.remaining_qty <= 0:
            raise ValueError("Prêmio esgotado")
        if prize.total_quantity > 0:
            prize.remaining_qty -= 1
        db.commit()
        db.refresh(prize)
        return prize


# ── Redemptions ────────────────────────────────────────────────────────────────

class BolaoRedemptionRepository:

    @staticmethod
    def create(db: Session, user_id: int, prize_id: int,
               points_spent: int) -> BolaoRedemption:
        redemption = BolaoRedemption(
            user_id=user_id,
            prize_id=prize_id,
            points_spent=points_spent,
        )
        db.add(redemption)
        db.commit()
        db.refresh(redemption)
        return redemption

    @staticmethod
    def list_for_user(db: Session, user_id: int) -> list[BolaoRedemption]:
        return (
            db.query(BolaoRedemption)
            .filter_by(user_id=user_id)
            .order_by(BolaoRedemption.redeemed_at.desc())
            .all()
        )
