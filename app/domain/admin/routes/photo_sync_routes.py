import os
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.permissions import require_subadmin_or_master
from app.domain.admin.controllers.photo_sync_controller import PhotoSyncController
from app.domain.admin.schemas.photo_sync_schema import PhotoSyncHeartbeatSchema, PhotoSyncStatusSchema

router = APIRouter(prefix="/admin", tags=["Admin - Photo Sync"])

_API_KEY = os.environ.get("PHOTO_SYNC_API_KEY", "")


@router.post("/photo-sync/heartbeat", status_code=201)
def photo_sync_heartbeat(
    body: PhotoSyncHeartbeatSchema,
    x_sync_api_key: str = Header(..., alias="X-Sync-Api-Key"),
    db: Session = Depends(get_admin_db),
):
    if not _API_KEY or x_sync_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    PhotoSyncController.record_heartbeat(db, body)
    return {"ok": True}


@router.get("/photo-sync/status", response_model=PhotoSyncStatusSchema)
def photo_sync_status(
    event_id: Optional[str] = Query(None),
    db: Session = Depends(get_admin_db),
    _user=Depends(require_subadmin_or_master),
):
    return PhotoSyncController.get_status(db, event_id)
