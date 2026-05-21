from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.config.auth_db import get_db
from app.core.security.permissions import require_subadmin_or_master, require_promotor_or_above
from app.domain.admin.controllers.tshirt_reservation_controller import TshirtReservationController
from app.domain.admin.schemas.tshirt_reservation_schema import (
    TshirtCpfLookupResponseSchema,
    TshirtReservationAdminItemSchema,
    TshirtReservationRedeemRequestSchema,
    TshirtReservationRedeemResponseSchema,
    TshirtReservationUserResponseSchema,
)
from app.domain.auth.models.user_model import User

router = APIRouter(prefix="/admin", tags=["Admin - T-shirt reservations"])


@router.get(
    "/tshirt-reservations",
    response_model=list[TshirtReservationAdminItemSchema],
)
def admin_list_tshirt_reservations(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_admin_db),
    _user: User = Depends(require_subadmin_or_master),
):
    rows = TshirtReservationController.list_admin(db, limit, offset)
    return [TshirtReservationAdminItemSchema.from_reservation(r) for r in rows]


@router.get(
    "/tshirt-reservations/lookup-cpf",
    response_model=TshirtCpfLookupResponseSchema,
)
def admin_lookup_tshirt_by_cpf(
    cpf: str = Query(..., min_length=11, max_length=11),
    admin_db: Session = Depends(get_admin_db),
    auth_db: Session = Depends(get_db),
    _user: User = Depends(require_promotor_or_above),
):
    try:
        result = TshirtReservationController.lookup_by_cpf(admin_db, auth_db, cpf)
        return TshirtCpfLookupResponseSchema(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/tshirt-reservations/redeem",
    response_model=TshirtReservationRedeemResponseSchema,
)
def admin_redeem_tshirt_reservation(
    body: TshirtReservationRedeemRequestSchema,
    db: Session = Depends(get_admin_db),
    promoter: User = Depends(require_promotor_or_above),
):
    try:
        res = TshirtReservationController.redeem(db, body.token, promoter)
        return TshirtReservationRedeemResponseSchema(
            message="Retirada registrada com sucesso.",
            reservation=TshirtReservationUserResponseSchema.from_reservation(res),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
