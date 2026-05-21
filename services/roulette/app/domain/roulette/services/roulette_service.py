from fastapi import HTTPException
from app.domain.roulette.repositories.roulette_repository import RouletteRepository


class RouletteService:

    @staticmethod
    def create_roulette(db, data: dict):
        existing = RouletteRepository.get_by_event(db, data["event_id"], force_db=True)
        if existing:
            raise HTTPException(status_code=400, detail="Este evento já possui uma roleta")
        return RouletteRepository.create(db, data)

    @staticmethod
    def get_by_event(db, event_id: int):
        roulette = RouletteRepository.get_by_event(db, event_id)

        if isinstance(roulette, dict):
            if not roulette.get("is_active"):
                raise HTTPException(status_code=404, detail="Roleta não encontrada ou inativa")
            return roulette

        if not roulette or not roulette.is_active:
            raise HTTPException(status_code=404, detail="Roleta não encontrada ou inativa")

        return roulette
