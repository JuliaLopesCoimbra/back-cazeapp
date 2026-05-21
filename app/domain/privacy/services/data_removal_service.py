import logging
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse

from fastapi import HTTPException, Request

from app.config.settings import settings
from app.core.security.auth_dependency import invalidate_user_cache
from app.domain.auth.models.user_model import User
from app.domain.auth.repositories.auth_repository import AuthRepository
from app.domain.auth.repositories.data_removal_request_repository import DataRemovalRequestRepository
from app.domain.auth.repositories.email_log_repository import EmailLogRepository
from app.domain.auth.models.email_log_model import EmailType, EmailStatus
from app.domain.privacy.schemas.data_removal_schema import (
    DataRemovalCheckResponse,
    DataRemovalRequestItem,
)
from app.domain.users.models.comment_like_model import CommentLike
from app.domain.users.models.comment_model import Comment
from app.domain.users.models.like_model import Like
from app.infra.email_sender import EmailSender
from app.infra.s3_upload import s3_client
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _delete_s3_photo(photo_url: Optional[str]) -> None:
    if not photo_url:
        return
    try:
        key = urlparse(photo_url).path.lstrip("/")
        if key:
            s3_client.delete_object(Bucket=settings.AWS_BUCKET, Key=key)
    except Exception as exc:
        logger.warning("Falha ao remover foto de perfil do S3: %s", exc)


def _mask_cpf(cpf: str) -> str:
    d = "".join(c for c in cpf if c.isdigit())
    if len(d) != 11:
        return "***"
    return f"***.***.{d[6:9]}-**"


def _resolve_user(db: Session, email: str, cpf_digits: str) -> Tuple[Optional[User], bool, str, Optional[str]]:
    user = AuthRepository.get_user_by_email_ci(db, email)
    if not user:
        return None, False, "email_not_found", "E-mail não encontrado."

    if not user.cpf or user.cpf != cpf_digits:
        return user, False, "cpf_not_found", "CPF não encontrado ou não confere com este e-mail."

    if user.role != "user":
        return user, False, "not_eligible", "Este fluxo é apenas para contas de usuário do aplicativo."

    return user, True, "matched", None


def _anonymize_and_deactivate(db: Session, *, user_id: int, interaction_db: Session) -> None:
    """Desativa e anonimiza completamente os dados de um usuário."""
    user = AuthRepository.get_user_by_id(db, user_id)
    if not user:
        return

    photo_url = user.profile_photo

    user.status = "inactive"
    user.deactivated_at = datetime.utcnow()
    user.deactivated_by_id = None
    user.reactivated_by_id = None
    user.reactivated_at = None

    AuthRepository.revoke_all_user_tokens(db, user_id)

    _delete_s3_photo(photo_url)
    user.name = "Usuário Removido"
    user.email = f"removed_{user_id}@removed.invalid"
    user.cpf = None
    user.profile_photo = None
    user.birth_date = None
    user.gender = None
    user.lgpd_accepted_ip = None
    user.lgpd_accepted_user_agent = None
    user.age_terms_accepted_ip = None
    user.age_terms_accepted_user_agent = None
    db.commit()
    invalidate_user_cache(user_id)

    now = datetime.utcnow()
    interaction_db.query(Like).filter(
        Like.user_id == user_id,
        Like.is_active.is_(True),
    ).update({"is_active": False, "deactivated_at": now}, synchronize_session=False)

    interaction_db.query(CommentLike).filter(
        CommentLike.user_id == user_id,
        CommentLike.is_active.is_(True),
    ).update({"is_active": False, "deactivated_at": now}, synchronize_session=False)

    interaction_db.query(Comment).filter(
        Comment.user_id == user_id,
        Comment.deleted_at.is_(None),
    ).update({"deleted_at": now, "deleted_by_user_id": None}, synchronize_session=False)

    interaction_db.commit()


def _send_internal_alert(db: Session, *, request_id: int, email: str, cpf_masked: str, user_name: Optional[str]) -> None:
    to_addr = (settings.DATA_REMOVAL_NOTIFICATION_EMAIL or "").strip()
    if not to_addr:
        logger.warning(
            "DATA_REMOVAL_NOTIFICATION_EMAIL não configurado; alerta de remoção #%s não enviado.",
            request_id,
        )
        return

    subject = f"[Remoção de dados LGPD] Cadastro removido #{request_id}"
    admin_url = f"{settings.FRONTEND_URL.rstrip('/')}/pages/admin/data-removal-requests"
    safe_name = user_name or "(sem nome)"
    html = f"""
    <div style="font-family:Arial,sans-serif;font-size:14px;color:#111;">
      <h2 style="margin-bottom:8px;">Cadastro removido automaticamente (LGPD)</h2>
      <p>O usuário solicitou a remoção de seus dados e o cadastro foi desativado e anonimizado imediatamente.</p>
      <p><strong>ID do registro:</strong> {request_id}</p>
      <p><strong>E-mail informado:</strong> {email}</p>
      <p><strong>CPF (mascarado):</strong> {cpf_masked}</p>
      <p><strong>Nome (snapshot):</strong> {safe_name}</p>
      <p><a href="{admin_url}">Ver histórico no painel administrativo</a></p>
      <p style="color:#666;font-size:12px;">Categoria interna: remoção de dados — enviado via Resend (SMTP).</p>
    </div>
    """

    log = EmailLogRepository.create_log(
        db=db,
        recipient_email=to_addr,
        subject=subject,
        email_type=EmailType.OTHER,
        user_id=None,
        status=EmailStatus.PENDING,
        extra_data={
            "category": "data_removal_alert",
            "data_removal_request_id": request_id,
        },
    )

    EmailSender.send_email(
        to=to_addr,
        subject=subject,
        html=html,
        db_session=db,
        email_log_id=log.id,
    )


class DataRemovalService:
    @staticmethod
    def check_identity(db: Session, email: str, cpf_digits: str) -> DataRemovalCheckResponse:
        user, exists, reason, message = _resolve_user(db, email, cpf_digits)
        if exists:
            return DataRemovalCheckResponse(exists=True, message="Cadastro encontrado.", reason=reason)
        return DataRemovalCheckResponse(exists=False, message=message, reason=reason)

    @staticmethod
    def submit_request(
        db: Session,
        *,
        email: str,
        cpf_digits: str,
        confirmed: bool,
        request: Request,
        interaction_db: Session,
    ) -> dict:
        if not confirmed:
            raise HTTPException(status_code=400, detail="Confirme a solicitação para continuar.")

        user, exists, reason, message = _resolve_user(db, email, cpf_digits)
        if not exists:
            raise HTTPException(status_code=400, detail=message or "Não foi possível validar os dados.")

        existing = DataRemovalRequestRepository.get_any_for_user(db, user.id)
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Este cadastro já passou pelo processo de remoção.",
            )

        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")

        user_name_snapshot = user.name

        row = DataRemovalRequestRepository.create(
            db,
            email_submitted=email.strip().lower(),
            cpf_submitted=cpf_digits,
            user_id=user.id,
            user_name_snapshot=user_name_snapshot,
            match_found=True,
            request_ip=ip,
            request_user_agent=ua[:1000] if ua else None,
        )

        _anonymize_and_deactivate(db, user_id=user.id, interaction_db=interaction_db)

        DataRemovalRequestRepository.mark_completed(db, row)

        try:
            _send_internal_alert(
                db,
                request_id=row.id,
                email=row.email_submitted,
                cpf_masked=_mask_cpf(cpf_digits),
                user_name=user_name_snapshot,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Falha ao enviar e-mail de alerta LGPD: %s", exc)

        return {
            "message": "Seus dados foram removidos com sucesso conforme a LGPD.",
            "request_id": row.id,
        }

    @staticmethod
    def list_admin(db: Session, *, limit: int, offset: int) -> list[DataRemovalRequestItem]:
        rows = DataRemovalRequestRepository.list_requests(db, limit=limit, offset=offset)
        out: list[DataRemovalRequestItem] = []
        for r in rows:
            out.append(
                DataRemovalRequestItem(
                    id=r.id,
                    email_submitted=r.email_submitted,
                    cpf_masked=_mask_cpf(r.cpf_submitted),
                    user_id=r.user_id,
                    user_name_snapshot=r.user_name_snapshot,
                    match_found=r.match_found,
                    created_at=r.created_at.isoformat() if r.created_at else None,
                    processed_at=r.processed_at.isoformat() if r.processed_at else None,
                    request_ip=r.request_ip,
                )
            )
        return out
