from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


# ── Predictions ────────────────────────────────────────────────────────────────

class BolaoPredicitionCreate(BaseModel):
    fixture_id: int
    home_score_prediction: int
    away_score_prediction: int

    @field_validator("home_score_prediction", "away_score_prediction")
    @classmethod
    def score_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Placar não pode ser negativo")
        return v


class BolaoPredicitionResponse(BaseModel):
    id: int
    fixture_id: int
    home_score_prediction: int
    away_score_prediction: int
    points_earned: int
    status: str
    settled_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Fixtures com prediction do usuário ─────────────────────────────────────────

class UserPredictionSummary(BaseModel):
    home_score: int
    away_score: int
    points_earned: int
    status: str


class BolaoFixtureResponse(BaseModel):
    fixture_id: int
    home_team: str
    away_team: str
    home_logo: str
    away_logo: str
    match_date: str
    status: str
    betting_closes_at: str
    user_prediction: Optional[UserPredictionSummary] = None


# ── Ranking ────────────────────────────────────────────────────────────────────

class BolaoRankingEntry(BaseModel):
    rank: int
    user_id: int
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    total_points: int
    exact_predictions: int
    correct_outcomes: int


# ── Points ─────────────────────────────────────────────────────────────────────

class BolaoMyPoints(BaseModel):
    total_points: int
    rank: int
    exact_predictions: int
    correct_outcomes: int


# ── Prizes ─────────────────────────────────────────────────────────────────────

class BolaoPrizeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    total_quantity: int = 0
    points_required: int
    prize_type: str

    @field_validator("prize_type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        allowed = {"shirt", "ticket", "merch", "digital"}
        if v not in allowed:
            raise ValueError(f"prize_type deve ser um de: {allowed}")
        return v


class BolaoPrizeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    total_quantity: int
    remaining_qty: int
    points_required: int
    prize_type: str
    is_active: bool

    model_config = {"from_attributes": True}


# ── Redemptions ────────────────────────────────────────────────────────────────

class BolaoRedeemRequest(BaseModel):
    prize_id: int


class BolaoRedemptionResponse(BaseModel):
    id: int
    prize_id: int
    points_spent: int
    status: str
    redeemed_at: datetime

    model_config = {"from_attributes": True}
