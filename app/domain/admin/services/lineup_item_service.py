# app/domain/admin/services/lineup_item_service.py

from app.domain.admin.repositories.lineup_item_repository import LineupItemRepository
from app.domain.admin.repositories.event_repository import EventRepository
from app.infra.redis import redis_client, CacheKeys

class LineupItemService:

    @staticmethod
    def create_lineup_item(db, data: dict, user):
        if user.role not in ["admin_master", "subadmin"]:
            raise PermissionError("Apenas admin master ou subadmin podem criar itens do lineup")

        # Verifica se o evento existe
        event = EventRepository.get_by_id(db, data['event_id'], force_db=True)
        if not event:
            raise ValueError("Evento não encontrado")

        # Valida se já existe um item com a mesma ordem no mesmo evento
        if 'display_order' in data:
            existing_item = LineupItemRepository.get_by_event_id_and_order(
                db, data['event_id'], data['display_order']
            )
            if existing_item:
                raise ValueError(f"Já existe um artista com a ordem {data['display_order']}. Cada artista deve ter uma ordem única.")

        return LineupItemRepository.create(db, data, created_by_id=user.id)

    @staticmethod
    def get_lineup_items_by_event(db, event_id: int):
        """Busca todos os itens do lineup de um evento"""
        return LineupItemRepository.get_by_event_id(db, event_id)

    @staticmethod
    def get_lineup_item_by_id(db, lineup_item_id: int):
        """Busca um item do lineup por ID"""
        return LineupItemRepository.get_by_id(db, lineup_item_id)

    @staticmethod
    def update_lineup_item(db, lineup_item_id: int, data: dict, user):
        if user.role not in ["admin_master", "subadmin"]:
            raise PermissionError("Apenas admin master ou subadmin podem editar itens do lineup")

        lineup_item = LineupItemRepository.get_by_id(db, lineup_item_id)
        if not lineup_item:
            raise ValueError("Item do lineup não encontrado")

        # Valida se já existe outro item com a mesma ordem no mesmo evento
        if 'display_order' in data and data['display_order'] is not None:
            existing_item = LineupItemRepository.get_by_event_id_and_order(
                db, lineup_item.event_id, data['display_order'], exclude_id=lineup_item_id
            )
            if existing_item:
                raise ValueError(f"Já existe um artista com a ordem {data['display_order']}. Cada artista deve ter uma ordem única.")

        return LineupItemRepository.update(db, lineup_item, data, updated_by_id=user.id)

    @staticmethod
    def delete_lineup_item(db, lineup_item_id: int, user):
        if user.role not in ["admin_master", "subadmin"]:
            raise PermissionError("Apenas admin master ou subadmin podem deletar itens do lineup")

        lineup_item = LineupItemRepository.get_by_id(db, lineup_item_id)
        if not lineup_item:
            raise ValueError("Item do lineup não encontrado")

        LineupItemRepository.delete(db, lineup_item, deleted_by_id=user.id)
        return True

