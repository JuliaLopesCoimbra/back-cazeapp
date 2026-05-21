from datetime import datetime
from sqlalchemy.orm import Session
from app.domain.admin.models.world_cup_game_model import WorldCupGame


class WorldCupGameRepository:

    @staticmethod
    def create(db: Session, data: dict) -> WorldCupGame:
        game = WorldCupGame(**data)
        db.add(game)
        db.commit()
        db.refresh(game)
        return game

    @staticmethod
    def list_by_event(db: Session, event_id: int, limit: int = 50, offset: int = 0):
        return (
            db.query(WorldCupGame)
            .filter(
                WorldCupGame.event_id == event_id,
                WorldCupGame.deleted_at.is_(None),
            )
            .order_by(WorldCupGame.game_date.asc(), WorldCupGame.game_time.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, game_id: int) -> WorldCupGame:
        game = (
            db.query(WorldCupGame)
            .filter(WorldCupGame.id == game_id, WorldCupGame.deleted_at.is_(None))
            .first()
        )
        if not game:
            raise ValueError(f"Jogo com ID {game_id} não encontrado")
        return game

    @staticmethod
    def update(db: Session, game_id: int, data: dict) -> WorldCupGame:
        game = WorldCupGameRepository.get_by_id(db, game_id)
        for key, value in data.items():
            setattr(game, key, value)
        db.commit()
        db.refresh(game)
        return game

    @staticmethod
    def delete(db: Session, game_id: int, user) -> None:
        game = WorldCupGameRepository.get_by_id(db, game_id)
        game.deleted_at = datetime.utcnow()
        game.deleted_by_id = user.id
        db.commit()
