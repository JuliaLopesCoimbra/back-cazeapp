from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TshirtStockItemCreateSchema(BaseModel):
    size: str = Field(..., min_length=1, max_length=10)
    quantity: int = Field(..., ge=0)


class TshirtStockItemUpdateSchema(BaseModel):
    quantity: int = Field(..., ge=0)


class TshirtStockMovementCreateSchema(BaseModel):
    direction: Literal["in", "out"]
    quantity: int = Field(..., ge=1)


class TshirtStockItemResponseSchema(BaseModel):
    id: int
    size: str
    quantity: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by_id: Optional[int] = None

    class Config:
        from_attributes = True


class TshirtStockItemWithReservationStatsSchema(TshirtStockItemResponseSchema):
    pending_reservations: int = 0
    available_to_reserve: int = 0
    picked_up_count: int = 0


class TshirtStockMovementResponseSchema(BaseModel):
    id: int
    stock_item_id: int
    size: str
    direction: str
    quantity: int
    performed_by_id: int
    performed_by_name: str
    created_at: datetime

    class Config:
        from_attributes = True
