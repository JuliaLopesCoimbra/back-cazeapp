import secrets
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from app.domain.admin.models.tshirt_reservation_model import TshirtReservation
from app.domain.admin.models.tshirt_stock_item_model import TshirtStockItem
from app.domain.admin.models.tshirt_stock_movement_model import TshirtStockMovement
from app.domain.admin.repositories.tshirt_reservation_repository import (
    TshirtReservationRepository,
)
from app.domain.admin.repositories.tshirt_stock_repository import TshirtStockRepository
from app.domain.admin.services.tshirt_stock_service import (
    ALLOWED_SIZES,
    TshirtStockService,
    _normalize_size,
    _user_snapshot,
)


def _snap_user(user) -> tuple[str, str]:
    name = (getattr(user, "name", None) or "").strip() or "Usuário"
    email = (getattr(user, "email", None) or "").strip() or ""
    return name[:255], email[:255]


class TshirtReservationService:

    @staticmethod
    def availability_for_item(item: TshirtStockItem, pending: int) -> int:
        return max(0, int(item.quantity) - int(pending))

    @staticmethod
    def list_availability(db: Session) -> list[dict]:
        items = TshirtStockService.list_all(db)
        out = []
        for it in items:
            pending = TshirtReservationRepository.count_pending_for_item(db, it.id)
            out.append(
                {
                    "size": it.size,
                    "quantity_physical": it.quantity,
                    "pending_reservations": pending,
                    "available_to_reserve": TshirtReservationService.availability_for_item(
                        it, pending
                    ),
                }
            )
        return out

    @staticmethod
    def get_mine(db: Session, user_id: int) -> Optional[TshirtReservation]:
        return TshirtReservationRepository.get_any_by_user_id(db, user_id)

    @staticmethod
    def create_for_user(db: Session, user, size: str) -> TshirtReservation:
        if TshirtReservationRepository.get_any_by_user_id(db, user.id):
            raise ValueError(
                "Você já possui uma reserva de camiseta. Cada participante pode reservar apenas uma vez."
            )
        norm = _normalize_size(size)
        if norm not in ALLOWED_SIZES:
            raise ValueError("Tamanho inválido.")
        item = TshirtStockRepository.get_by_size(db, norm)
        if not item:
            raise ValueError("Tamanho indisponível no estoque.")
        pending = TshirtReservationRepository.count_pending_for_item(db, item.id)
        avail = TshirtReservationService.availability_for_item(item, pending)
        if avail < 1:
            raise ValueError("Não há camisetas disponíveis para este tamanho no momento.")
        uname, uemail = _snap_user(user)
        token = secrets.token_urlsafe(18)
        data = {
            "user_id": user.id,
            "stock_item_id": item.id,
            "size": norm,
            "qr_token": token,
            "user_name_snapshot": uname,
            "user_email_snapshot": uemail,
            "status": "pending_pickup",
        }
        return TshirtReservationRepository.create(db, data)

    @staticmethod
    def lookup_by_cpf(admin_db: Session, auth_db: Session, cpf: str) -> dict:
        from app.domain.auth.repositories.auth_repository import AuthRepository
        user = AuthRepository.get_user_by_cpf(auth_db, cpf)
        if not user:
            raise ValueError("Nenhum usuário encontrado com este CPF.")
        res = TshirtReservationRepository.get_any_by_user_id(admin_db, user.id)
        if not res:
            raise ValueError("Este usuário não possui reserva de camiseta.")
        return {
            "reservation_id": res.id,
            "user_name": res.user_name_snapshot or (user.name or "Usuário"),
            "size": res.size,
            "status": res.status,
            "qr_token": f"N1SHIRT|{res.qr_token}",
        }

    @staticmethod
    def list_admin(db: Session, limit: int = 100, offset: int = 0) -> list[TshirtReservation]:
        return TshirtReservationRepository.list_admin(db, limit, offset)

    @staticmethod
    def redeem(db: Session, raw_token: str, promoter) -> TshirtReservation:
        token = (raw_token or "").strip()
        if "|" in token:
            parts = token.split("|", 1)
            if len(parts) == 2 and parts[0].strip().upper() == "N1SHIRT":
                token = parts[1].strip()
        if not token:
            raise ValueError("Token inválido.")
        res = TshirtReservationRepository.get_by_qr_token(db, token)
        if not res:
            raise ValueError("Reserva não encontrada.")
        if res.status != "pending_pickup":
            raise ValueError("Esta reserva já foi retirada ou está encerrada.")
        item = TshirtStockRepository.get_by_id(db, res.stock_item_id)
        if not item:
            raise ValueError("Item de estoque não encontrado.")
        if item.quantity < 1:
            raise ValueError("Estoque físico insuficiente para concluir a retirada.")
        pid, pname = _user_snapshot(promoter)
        item.quantity = int(item.quantity) - 1
        item.updated_by_id = pid
        db.add(
            TshirtStockMovement(
                stock_item_id=item.id,
                size=item.size,
                direction="out",
                quantity=1,
                performed_by_id=pid,
                performed_by_name=pname,
            )
        )
        res.status = "picked_up"
        res.picked_up_at = datetime.utcnow()
        res.picked_up_by_id = pid
        res.picked_up_by_name = pname
        db.commit()
        db.refresh(res)
        db.refresh(item)
        return res
