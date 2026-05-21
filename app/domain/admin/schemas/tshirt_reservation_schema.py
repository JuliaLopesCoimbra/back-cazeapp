from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TshirtSizeAvailabilityItemSchema(BaseModel):
    size: str
    quantity_physical: int
    pending_reservations: int
    available_to_reserve: int


class TshirtReservationCreateSchema(BaseModel):
    size: str = Field(..., min_length=1, max_length=10)


class TshirtReservationUserResponseSchema(BaseModel):
    id: int
    user_id: int
    size: str
    status: str
    qr_payload: str
    user_name_snapshot: str = ""
    created_at: datetime
    picked_up_at: Optional[datetime] = None
    picked_up_by_name: Optional[str] = None

    @classmethod
    def from_reservation(cls, r):
        return cls(
            id=r.id,
            user_id=r.user_id,
            size=r.size,
            status=r.status,
            qr_payload=f"N1SHIRT|{r.qr_token}",
            user_name_snapshot=r.user_name_snapshot or "",
            created_at=r.created_at,
            picked_up_at=r.picked_up_at,
            picked_up_by_name=r.picked_up_by_name,
        )


class TshirtReservationAdminItemSchema(BaseModel):
    id: int
    user_id: int
    stock_item_id: int
    size: str
    status: str
    user_name_snapshot: str
    user_email_snapshot: str
    qr_payload: str
    created_at: datetime
    picked_up_at: Optional[datetime] = None
    picked_up_by_id: Optional[int] = None
    picked_up_by_name: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_reservation(cls, r):
        return cls(
            id=r.id,
            user_id=r.user_id,
            stock_item_id=r.stock_item_id,
            size=r.size,
            status=r.status,
            user_name_snapshot=r.user_name_snapshot,
            user_email_snapshot=r.user_email_snapshot,
            qr_payload=f"N1SHIRT|{r.qr_token}",
            created_at=r.created_at,
            picked_up_at=r.picked_up_at,
            picked_up_by_id=r.picked_up_by_id,
            picked_up_by_name=r.picked_up_by_name,
        )


class TshirtCpfLookupResponseSchema(BaseModel):
    reservation_id: int
    user_name: str
    size: str
    status: str
    qr_token: str


class TshirtReservationRedeemRequestSchema(BaseModel):
    token: str = Field(..., min_length=1, max_length=500)


class TshirtReservationRedeemResponseSchema(BaseModel):
    message: str
    reservation: TshirtReservationUserResponseSchema
