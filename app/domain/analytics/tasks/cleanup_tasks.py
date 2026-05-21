"""Celery Beat tasks for analytics data lifecycle management."""
import logging
from datetime import datetime, timedelta, timezone

from app.infra.celery_app import celery_app
from app.config.auth_db import SessionLocal
from app.domain.analytics.models.page_view_model import PageView  # noqa: F401

logger = logging.getLogger(__name__)

PAGE_VIEW_RETENTION_DAYS = 90


@celery_app.task(name="analytics.cleanup_page_views", ignore_result=True)
def cleanup_page_views():
    """Delete page_views records older than 90 days. Runs daily at 03:00 UTC."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=PAGE_VIEW_RETENTION_DAYS)
    db = SessionLocal()
    try:
        deleted = (
            db.query(PageView)
            .filter(PageView.viewed_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        logger.info(f"analytics.cleanup_page_views: deleted {deleted} rows older than {cutoff.date()}")
        return {"deleted": deleted}
    except Exception as exc:
        db.rollback()
        logger.error(f"analytics.cleanup_page_views failed: {exc}", exc_info=True)
        raise
    finally:
        db.close()
