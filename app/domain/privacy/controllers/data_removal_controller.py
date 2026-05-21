from fastapi import Request
from sqlalchemy.orm import Session

from app.domain.privacy.services.data_removal_service import DataRemovalService


class DataRemovalController:
    @staticmethod
    def check(db: Session, email: str, cpf: str):
        return DataRemovalService.check_identity(db, email, cpf)

    @staticmethod
    def submit(db: Session, email: str, cpf: str, confirmed: bool, request: Request, interaction_db: Session):
        return DataRemovalService.submit_request(
            db,
            email=email,
            cpf_digits=cpf,
            confirmed=confirmed,
            request=request,
            interaction_db=interaction_db,
        )

    @staticmethod
    def list_admin(db: Session, limit: int, offset: int):
        return DataRemovalService.list_admin(db, limit=limit, offset=offset)
