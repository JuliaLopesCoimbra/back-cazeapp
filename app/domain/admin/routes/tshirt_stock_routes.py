from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.permissions import require_subadmin_or_master
from app.domain.admin.controllers.tshirt_stock_controller import TshirtStockController
from app.domain.admin.repositories.tshirt_reservation_repository import (
    TshirtReservationRepository,
)
from app.domain.admin.schemas.tshirt_stock_schema import (
    TshirtStockItemCreateSchema,
    TshirtStockItemResponseSchema,
    TshirtStockItemUpdateSchema,
    TshirtStockItemWithReservationStatsSchema,
    TshirtStockMovementCreateSchema,
    TshirtStockMovementResponseSchema,
)
from app.domain.auth.models.user_model import User

router = APIRouter(prefix="/admin", tags=["Admin - T-shirt stock"])


@router.get(
    "/tshirt-stock/movements",
    response_model=list[TshirtStockMovementResponseSchema],
)
def list_tshirt_stock_movements(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_admin_db),
    _user: User = Depends(require_subadmin_or_master),
):
    return TshirtStockController.list_movements(db, limit, offset)


@router.post(
    "/tshirt-stock/{item_id}/movements",
    response_model=TshirtStockItemResponseSchema,
)
def register_tshirt_stock_movement(
    item_id: int,
    body: TshirtStockMovementCreateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_subadmin_or_master),
):
    try:
        return TshirtStockController.add_movement(
            db, item_id, body.direction, body.quantity, user
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/tshirt-stock", response_model=list[TshirtStockItemWithReservationStatsSchema])
def list_tshirt_stock(
    db: Session = Depends(get_admin_db),
    _user: User = Depends(require_subadmin_or_master),
):
    items = TshirtStockController.list_all(db)
    out: list[TshirtStockItemWithReservationStatsSchema] = []
    for it in items:
        pending = TshirtReservationRepository.count_pending_for_item(db, it.id)
        picked_up = TshirtReservationRepository.count_picked_up_for_item(db, it.id)
        base = TshirtStockItemResponseSchema.model_validate(it)
        out.append(
            TshirtStockItemWithReservationStatsSchema(
                **base.model_dump(),
                pending_reservations=pending,
                available_to_reserve=max(0, int(it.quantity) - int(pending)),
                picked_up_count=picked_up,
            )
        )
    return out


@router.get("/tshirt-stock/{item_id}", response_model=TshirtStockItemResponseSchema)
def get_tshirt_stock_item(
    item_id: int,
    db: Session = Depends(get_admin_db),
    _user: User = Depends(require_subadmin_or_master),
):
    try:
        return TshirtStockController.get_by_id(db, item_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/tshirt-stock",
    response_model=TshirtStockItemResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_tshirt_stock_item(
    body: TshirtStockItemCreateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_subadmin_or_master),
):
    try:
        return TshirtStockController.create(db, body.size, body.quantity, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/tshirt-stock/{item_id}", response_model=TshirtStockItemResponseSchema)
def update_tshirt_stock_item(
    item_id: int,
    body: TshirtStockItemUpdateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_subadmin_or_master),
):
    try:
        return TshirtStockController.update(db, item_id, body.quantity, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/tshirt-stock/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tshirt_stock_item(
    item_id: int,
    db: Session = Depends(get_admin_db),
    _user: User = Depends(require_subadmin_or_master),
):
    try:
        TshirtStockController.delete(db, item_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
