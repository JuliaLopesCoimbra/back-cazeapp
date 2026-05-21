from app.domain.admin.repositories.world_cup_game_repository import WorldCupGameRepository


class WorldCupGameService:

    @staticmethod
    def create(db, data: dict, user):
        data["created_by_id"] = user.id
        return WorldCupGameRepository.create(db, data)

    @staticmethod
    def list_by_event(db, event_id: int, limit: int = 50, offset: int = 0):
        return WorldCupGameRepository.list_by_event(db, event_id, limit, offset)

    @staticmethod
    def get_by_id(db, game_id: int):
        return WorldCupGameRepository.get_by_id(db, game_id)

    @staticmethod
    def update(db, game_id: int, data: dict, user):
        data["updated_by_id"] = user.id
        return WorldCupGameRepository.update(db, game_id, data)

    @staticmethod
    def delete(db, game_id: int, user):
        WorldCupGameRepository.delete(db, game_id, user)
