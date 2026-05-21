from app.domain.admin.services.world_cup_game_service import WorldCupGameService


class WorldCupGameController:

    @staticmethod
    def create(db, data: dict, user):
        return WorldCupGameService.create(db, data, user)

    @staticmethod
    def list_by_event(db, event_id: int, limit: int = 50, offset: int = 0):
        return WorldCupGameService.list_by_event(db, event_id, limit, offset)

    @staticmethod
    def get_by_id(db, game_id: int):
        return WorldCupGameService.get_by_id(db, game_id)

    @staticmethod
    def update(db, game_id: int, data: dict, user):
        return WorldCupGameService.update(db, game_id, data, user)

    @staticmethod
    def delete(db, game_id: int, user):
        WorldCupGameService.delete(db, game_id, user)
