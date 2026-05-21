from fastapi import HTTPException
from app.domain.roulette.repositories.prize_repository import PrizeRepository
from app.domain.admin.repositories.event_repository import EventRepository
from app.infra.redis import redis_client, CacheKeys


class PrizeService:

    @staticmethod
    def create_prize(db, admin_db, data: dict):
        event = EventRepository.get_by_id(admin_db, data["event_id"])
        if not event:
            raise HTTPException(status_code=404, detail="Evento não encontrado")

        existing = PrizeRepository.get_by_event_and_position(db, data["event_id"], data["position"])
        if existing:
            raise HTTPException(status_code=400, detail="Já existe um prêmio nesta posição da roleta")

        result = PrizeRepository.create(db, data)
        redis_client.delete(CacheKeys.prizes_event(data["event_id"]))
        return result

    @staticmethod
    def _prize_to_dict(prize) -> dict:
        return {
            "id": prize.id,
            "event_id": prize.event_id,
            "name": prize.name,
            "probability": prize.probability,
            "position": prize.position,
            "image_url": prize.image_url,
            "is_active": prize.is_active
        }

    @staticmethod
    def list_prizes(db, event_id: int, limit: int = 50, offset: int = 0):
        if offset == 0:
            cached = redis_client.get(CacheKeys.prizes_event(event_id))
            if cached:
                return cached[offset:offset + limit]

        prizes = PrizeRepository.list_by_event(db, event_id, limit, offset)

        if not prizes and offset == 0:
            raise HTTPException(404, "Nenhum prêmio encontrado")

        if offset == 0:
            prizes_dict = [PrizeService._prize_to_dict(p) for p in prizes]
            redis_client.set(CacheKeys.prizes_event(event_id), prizes_dict, ttl=600)

        return prizes
