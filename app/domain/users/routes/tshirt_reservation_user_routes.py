from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.auth_dependency import get_current_user
from app.domain.admin.controllers.tshirt_reservation_controller import TshirtReservationController
from app.domain.admin.schemas.tshirt_reservation_schema import (
    TshirtReservationCreateSchema,
    TshirtReservationUserResponseSchema,
    TshirtSizeAvailabilityItemSchema,
)
from app.domain.auth.models.user_model import User

router = APIRouter(prefix="/user", tags=["User - T-shirt reservation"])


@router.get(
    "/tshirt-availability",
    response_model=list[TshirtSizeAvailabilityItemSchema],
)
def user_tshirt_availability(
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    _ = user
    rows = TshirtReservationController.availability(db)
    return [TshirtSizeAvailabilityItemSchema(**r) for r in rows]


@router.get(
    "/tshirt-reservation",
    response_model=Optional[TshirtReservationUserResponseSchema],
)
def user_get_tshirt_reservation(
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    row = TshirtReservationController.get_mine(db, user.id)
    if not row:
        return None
    return TshirtReservationUserResponseSchema.from_reservation(row)


@router.post(
    "/tshirt-reservation",
    response_model=TshirtReservationUserResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def user_create_tshirt_reservation(
    body: TshirtReservationCreateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    try:
        row = TshirtReservationController.create(db, user, body.size)
        return TshirtReservationUserResponseSchema.from_reservation(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
