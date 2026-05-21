from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.config.auth_db import get_db
from app.config.interaction_db import get_interaction_db
from app.core.security.permissions import require_subadmin_or_master
from app.domain.auth.models.user_model import User
from app.domain.privacy.controllers.data_removal_controller import DataRemovalController
from app.domain.privacy.schemas.data_removal_schema import (
    DataRemovalCheckRequest,
    DataRemovalCheckResponse,
    DataRemovalSubmitRequest,
    DataRemovalRequestItem,
)
from app.infra.redis import check_rate_limit

router = APIRouter(tags=["Privacy / LGPD"])


@router.post("/data-removal/check", response_model=DataRemovalCheckResponse)
def data_removal_check(
    body: DataRemovalCheckRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    allowed, _ = check_rate_limit(
        f"data-removal-check:ip:{ip}",
        max_requests=20,
        window_seconds=3600,
        critical=False,
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas de verificação. Tente novamente mais tarde.",
            headers={"Retry-After": "3600"},
        )
    return DataRemovalController.check(db, body.email, body.cpf)


@router.post("/data-removal/request")
def data_removal_request(
    body: DataRemovalSubmitRequest,
    request: Request,
    db: Session = Depends(get_db),
    interaction_db: Session = Depends(get_interaction_db),
):
    ip = request.client.host if request.client else "unknown"
    allowed, _ = check_rate_limit(
        f"data-removal-request:ip:{ip}",
        max_requests=5,
        window_seconds=86400,
        critical=False,
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Limite de solicitações atingido. Tente novamente em 24 horas.",
            headers={"Retry-After": "86400"},
        )
    return DataRemovalController.submit(
        db,
        email=body.email,
        cpf=body.cpf,
        confirmed=body.confirmed,
        request=request,
        interaction_db=interaction_db,
    )


@router.get("/data-removal/admin/requests", response_model=list[DataRemovalRequestItem])
def data_removal_admin_list(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_subadmin_or_master),
):
    _ = admin
    return DataRemovalController.list_admin(db, limit=limit, offset=offset)
