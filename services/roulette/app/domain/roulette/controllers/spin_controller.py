from app.domain.roulette.services.spin_service import SpinService


class SpinController:

    @staticmethod
    def spin(db, user, event_id: int):
        return SpinService.spin(db, user.id, event_id)
