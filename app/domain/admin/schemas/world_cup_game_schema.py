from pydantic import BaseModel
from datetime import datetime, date, time
from typing import Optional


class WorldCupGameResponseSchema(BaseModel):
    id: int
    event_id: int
    title: str
    description: Optional[str] = None
    photo_url: Optional[str] = None
    game_date: Optional[date] = None
    game_time: Optional[time] = None
    created_at: datetime
    created_by_id: Optional[int] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
