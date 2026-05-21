from sqlalchemy.orm import Session
from app.domain.roulette.models.roulette_model import Roulette
from app.infra.redis import redis_client, CacheKeys


class RouletteRepository:

    @staticmethod
    def _to_dict(roulette: Roulette) -> dict:
        return {
            "id": roulette.id,
            "event_id": roulette.event_id,
            "name": roulette.name,
            "is_active": roulette.is_active,
            "roulette_image_url": roulette.roulette_image_url,
            "pointer_image_url": roulette.pointer_image_url,
            "expires_at": roulette.expires_at
        }

    @staticmethod
    def get_by_event(db: Session, event_id: int, force_db: bool = False):
        if not force_db:
            cached = redis_client.get(CacheKeys.roulette_event(event_id))
            if cached is not None:
                return cached

        result = db.query(Roulette).filter(Roulette.event_id == event_id).first()

        if result and not force_db:
            redis_client.set(CacheKeys.roulette_event(event_id), RouletteRepository._to_dict(result), ttl=900)

        return result

    @staticmethod
    def create(db: Session, data: dict):
        roulette = Roulette(**data)
        db.add(roulette)
        db.commit()
        db.refresh(roulette)
        redis_client.delete(CacheKeys.roulette_event(data["event_id"]))
        return roulette
