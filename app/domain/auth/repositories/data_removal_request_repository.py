from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.domain.auth.models.data_removal_request_model import DataRemovalRequest


class DataRemovalRequestRepository:
    @staticmethod
    def create(
        db: Session,
        *,
        email_submitted: str,
        cpf_submitted: str,
        user_id: Optional[int],
        user_name_snapshot: Optional[str],
        match_found: bool,
        request_ip: Optional[str],
        request_user_agent: Optional[str],
    ) -> DataRemovalRequest:
        row = DataRemovalRequest(
            email_submitted=email_submitted,
            cpf_submitted=cpf_submitted,
            user_id=user_id,
            user_name_snapshot=user_name_snapshot,
            status="pending",
            match_found=match_found,
            request_ip=request_ip,
            request_user_agent=request_user_agent,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def get_any_for_user(db: Session, user_id: int) -> Optional[DataRemovalRequest]:
        return (
            db.query(DataRemovalRequest)
            .filter(DataRemovalRequest.user_id == user_id)
            .first()
        )

    @staticmethod
    def list_requests(
        db: Session,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DataRemovalRequest]:
        limit = min(max(limit, 1), 200)
        return (
            db.query(DataRemovalRequest)
            .order_by(DataRemovalRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def mark_completed(
        db: Session,
        row: DataRemovalRequest,
    ) -> DataRemovalRequest:
        row.status = "completed"
        row.processed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        return row
