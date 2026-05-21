from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PhotoSyncHeartbeatSchema(BaseModel):
    event_id: str
    server_name: str = ""
    new_files: int = 0
    uploaded: int = 0
    indexed: int = 0
    no_face: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    total_drive_files: int = 0
    new_s3_keys: list[str] = []


class PhotoSyncLogResponseSchema(BaseModel):
    id: int
    event_id: str
    server_name: str
    cycle_at: datetime
    new_files: int
    uploaded: int
    indexed: int
    no_face: int
    errors: int
    duration_seconds: float
    total_drive_files: int = 0

    class Config:
        from_attributes = True


class PhotoSyncStatusSchema(BaseModel):
    is_alive: bool
    last_cycle_at: Optional[datetime]
    seconds_since_last_cycle: Optional[int]
    total_indexed_today: int
    total_cycles_today: int
    total_drive_files: int
    total_s3_files: int
    recent_logs: list[PhotoSyncLogResponseSchema]
    upload_logs: list[PhotoSyncLogResponseSchema]
