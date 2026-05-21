from sqlalchemy.orm import Session

from app.domain.admin.models.tshirt_stock_item_model import TshirtStockItem
from app.domain.admin.models.tshirt_stock_movement_model import TshirtStockMovement
from app.domain.admin.repositories.tshirt_stock_repository import TshirtStockRepository
from app.domain.admin.repositories.tshirt_stock_movement_repository import (
    TshirtStockMovementRepository,
)

ALLOWED_SIZES = frozenset({"PP", "P", "M", "G", "GG", "EXG"})
SIZE_ORDER = ["PP", "P", "M", "G", "GG", "EXG"]


def _normalize_size(size: str) -> str:
    s = (size or "").strip().upper()
    if s == "XG" or s == "XGG":
        return "EXG"
    return s


def _sort_key(row):
    try:
        return SIZE_ORDER.index(row.size)
    except ValueError:
        return 99


def _user_snapshot(user) -> tuple[int, str]:
    name = (getattr(user, "name", None) or "").strip()
    if not name:
        name = (getattr(user, "email", None) or "Usuário").strip()
    return int(user.id), (name or "Usuário")[:255]


class TshirtStockService:

    @staticmethod
    def list_all(db: Session):
        rows = TshirtStockRepository.list_all(db)
        return sorted(rows, key=_sort_key)

    @staticmethod
    def list_movements(db: Session, limit: int = 100, offset: int = 0):
        return TshirtStockMovementRepository.list_all(db, limit, offset)

    @staticmethod
    def get_by_id(db: Session, item_id: int):
        row = TshirtStockRepository.get_by_id(db, item_id)
        if not row:
            raise ValueError("Item de estoque não encontrado.")
        return row

    @staticmethod
    def create(db: Session, size: str, quantity: int, user):
        norm = _normalize_size(size)
        if norm not in ALLOWED_SIZES:
            raise ValueError(
                "Tamanho inválido. Use um de: PP, P, M, G, GG, EXG."
            )
        if TshirtStockRepository.get_by_size(db, norm):
            raise ValueError("Já existe estoque cadastrado para este tamanho.")
        uid, uname = _user_snapshot(user)
        row = TshirtStockItem(size=norm, quantity=0, updated_by_id=uid)
        db.add(row)
        db.flush()
        if quantity > 0:
            row.quantity = quantity
            db.add(
                TshirtStockMovement(
                    stock_item_id=row.id,
                    size=norm,
                    direction="in",
                    quantity=quantity,
                    performed_by_id=uid,
                    performed_by_name=uname,
                )
            )
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def update_quantity(db: Session, item_id: int, new_quantity: int, user):
        row = TshirtStockService.get_by_id(db, item_id)
        old_q = row.quantity
        delta = new_quantity - old_q
        uid, uname = _user_snapshot(user)
        if delta != 0:
            direction = "in" if delta > 0 else "out"
            db.add(
                TshirtStockMovement(
                    stock_item_id=row.id,
                    size=row.size,
                    direction=direction,
                    quantity=abs(delta),
                    performed_by_id=uid,
                    performed_by_name=uname,
                )
            )
        row.quantity = new_quantity
        row.updated_by_id = uid
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def add_movement(db: Session, item_id: int, direction: str, quantity: int, user):
        if quantity < 1:
            raise ValueError("Quantidade deve ser pelo menos 1.")
        if direction not in ("in", "out"):
            raise ValueError("Direção inválida: use 'in' ou 'out'.")
        row = TshirtStockService.get_by_id(db, item_id)
        uid, uname = _user_snapshot(user)
        if direction == "out":
            if row.quantity < quantity:
                raise ValueError("Estoque insuficiente para esta retirada.")
            new_q = row.quantity - quantity
        else:
            new_q = row.quantity + quantity
        db.add(
            TshirtStockMovement(
                stock_item_id=row.id,
                size=row.size,
                direction=direction,
                quantity=quantity,
                performed_by_id=uid,
                performed_by_name=uname,
            )
        )
        row.quantity = new_q
        row.updated_by_id = uid
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def delete(db: Session, item_id: int):
        row = TshirtStockService.get_by_id(db, item_id)
        TshirtStockRepository.delete(db, row)
