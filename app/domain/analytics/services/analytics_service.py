import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, distinct, extract
from sqlalchemy.orm import Session

from app.domain.auth.models.user_model import User
from app.domain.users.models.like_model import Like
from app.domain.users.models.comment_model import Comment
from app.domain.users.models.downloaded_photo_model import DownloadedPhoto
from app.domain.users.models.notification_model import Notification
from app.domain.users.models.push_subscription_model import PushSubscription
from app.domain.admin.models.ad_view_model import AdView
from app.domain.admin.models.ad_click_model import AdClick
from app.domain.admin.models.news_model import NewsPost
from app.domain.photo_ai.models.face_search_model import FaceSearch
from app.domain.roulette.models.spin_model import Spin
from app.domain.analytics.models.page_view_model import PageView
from app.domain.analytics.schemas.analytics_schema import PageViewTrack
from app.infra.redis import redis_client

logger = logging.getLogger(__name__)

CACHE_TTL = 300


def _today_start() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _week_start() -> datetime:
    return _today_start() - timedelta(days=7)


def _month_start() -> datetime:
    return _today_start() - timedelta(days=30)


def _safe_count(value) -> int:
    return int(value) if value is not None else 0


def _period_start(period: str) -> Optional[datetime]:
    if period == "day":
        return _today_start()
    if period == "week":
        return _week_start()
    if period == "month":
        return _month_start()
    return None


# ─── User metrics ─────────────────────────────────────────────────────────────

def _get_user_metrics(auth_db: Session, period: str) -> dict:
    today = _today_start()
    week = _week_start()
    month = _month_start()
    since = _period_start(period)

    base = auth_db.query(func.count(User.id)).filter(User.role == "user")
    total_q = base.filter(User.created_at >= since) if since else base

    return {
        "total": _safe_count(total_q.scalar()),
        "new_today": _safe_count(
            auth_db.query(func.count(User.id))
            .filter(User.role == "user", User.created_at >= today)
            .scalar()
        ),
        "new_this_week": _safe_count(
            auth_db.query(func.count(User.id))
            .filter(User.role == "user", User.created_at >= week)
            .scalar()
        ),
        "new_this_month": _safe_count(
            auth_db.query(func.count(User.id))
            .filter(User.role == "user", User.created_at >= month)
            .scalar()
        ),
    }


# ─── Interaction metrics ───────────────────────────────────────────────────────

def _get_interaction_metrics(interaction_db: Session, event_id: Optional[int], period: str) -> dict:
    today = _today_start()
    since = _period_start(period)

    def likes_base():
        q = interaction_db.query(func.count(Like.id)).filter(Like.is_active == True)
        if event_id:
            q = q.filter(Like.event_id == event_id)
        return q

    def comments_base():
        q = interaction_db.query(func.count(Comment.id)).filter(Comment.deleted_at.is_(None))
        if event_id:
            q = q.filter(Comment.event_id == event_id)
        return q

    total_likes_q = likes_base().filter(Like.created_at >= since) if since else likes_base()
    total_likes = _safe_count(total_likes_q.scalar())
    new_likes_today = _safe_count(likes_base().filter(Like.created_at >= today).scalar())

    total_comments_q = comments_base().filter(Comment.created_at >= since) if since else comments_base()
    total_comments = _safe_count(total_comments_q.scalar())
    new_comments_today = _safe_count(comments_base().filter(Comment.created_at >= today).scalar())

    return {
        "total_likes": total_likes,
        "new_likes_today": new_likes_today,
        "total_comments": total_comments,
        "new_comments_today": new_comments_today,
        "total_interactions": total_likes + total_comments,
    }


# ─── Ad metrics ───────────────────────────────────────────────────────────────

def _get_ad_metrics(admin_db: Session, event_id: Optional[int], period: str) -> dict:
    today = _today_start()
    since = _period_start(period)

    def views_base():
        q = admin_db.query(func.count(AdView.id))
        if event_id:
            q = q.filter(AdView.event_id == event_id)
        return q

    def clicks_base():
        q = admin_db.query(func.count(AdClick.id))
        if event_id:
            q = q.filter(AdClick.event_id == event_id)
        return q

    total_views_q = views_base().filter(AdView.viewed_at >= since) if since else views_base()
    total_views = _safe_count(total_views_q.scalar())
    views_today = _safe_count(views_base().filter(AdView.viewed_at >= today).scalar())

    total_clicks_q = clicks_base().filter(AdClick.clicked_at >= since) if since else clicks_base()
    total_clicks = _safe_count(total_clicks_q.scalar())
    clicks_today = _safe_count(clicks_base().filter(AdClick.clicked_at >= today).scalar())

    ctr = round((total_clicks / total_views * 100), 2) if total_views > 0 else 0.0

    return {
        "total_views": total_views,
        "views_today": views_today,
        "total_clicks": total_clicks,
        "clicks_today": clicks_today,
        "ctr_percent": ctr,
    }


# ─── Photo Finder metrics ─────────────────────────────────────────────────────

def _get_photo_finder_metrics(
    admin_db: Session, interaction_db: Session, event_id: Optional[int], period: str
) -> dict:
    today = _today_start()
    since = _period_start(period)

    def fs_base():
        q = admin_db.query(func.count(FaceSearch.id))
        if event_id:
            q = q.filter(FaceSearch.event_id == event_id)
        return q

    def dl_base():
        q = interaction_db.query(func.count(DownloadedPhoto.id))
        if event_id:
            q = q.filter(DownloadedPhoto.event_id == event_id)
        return q

    total_uploads_q = fs_base().filter(FaceSearch.searched_at >= since) if since else fs_base()
    total_uploads = _safe_count(total_uploads_q.scalar())
    uploads_today = _safe_count(fs_base().filter(FaceSearch.searched_at >= today).scalar())

    total_recs_q = fs_base().filter(FaceSearch.face_detected == True)
    if since:
        total_recs_q = total_recs_q.filter(FaceSearch.searched_at >= since)
    total_recognitions = _safe_count(total_recs_q.scalar())
    recognitions_today = _safe_count(
        fs_base().filter(FaceSearch.face_detected == True, FaceSearch.searched_at >= today).scalar()
    )

    total_dl_q = dl_base().filter(DownloadedPhoto.downloaded_at >= since) if since else dl_base()
    total_downloads = _safe_count(total_dl_q.scalar())
    downloads_today = _safe_count(dl_base().filter(DownloadedPhoto.downloaded_at >= today).scalar())

    recognition_rate = round(total_recognitions / total_uploads * 100, 2) if total_uploads > 0 else 0.0

    return {
        "total_uploads": total_uploads,
        "uploads_today": uploads_today,
        "total_recognitions": total_recognitions,
        "recognitions_today": recognitions_today,
        "total_downloads": total_downloads,
        "downloads_today": downloads_today,
        "recognition_rate_percent": recognition_rate,
    }


# ─── Post metrics ─────────────────────────────────────────────────────────────

def _get_post_metrics(admin_db: Session, event_id: Optional[int], period: str) -> dict:
    today = _today_start()
    since = _period_start(period)

    def pub_base():
        q = admin_db.query(func.count(NewsPost.id)).filter(
            NewsPost.status == "approved",
            NewsPost.deleted_at.is_(None),
        )
        if event_id:
            q = q.filter(NewsPost.event_id == event_id)
        return q

    total_q = pub_base().filter(NewsPost.created_at >= since) if since else pub_base()
    total_published = _safe_count(total_q.scalar())
    published_today = _safe_count(pub_base().filter(NewsPost.created_at >= today).scalar())

    def status_count(status: str) -> int:
        q = admin_db.query(func.count(NewsPost.id)).filter(
            NewsPost.status == status,
            NewsPost.deleted_at.is_(None),
        )
        if event_id:
            q = q.filter(NewsPost.event_id == event_id)
        return _safe_count(q.scalar())

    return {
        "total_published": total_published,
        "published_today": published_today,
        "pending_approval": status_count("pending"),
        "rejected": status_count("rejected"),
    }


# ─── Roulette metrics ─────────────────────────────────────────────────────────

def _get_roulette_metrics(roulette_db: Session, event_id: Optional[int], period: str) -> dict:
    today = _today_start()
    since = _period_start(period)

    def spins_base():
        q = roulette_db.query(func.count(Spin.id))
        if event_id:
            q = q.filter(Spin.event_id == event_id)
        return q

    total_spins_q = spins_base().filter(Spin.created_at >= since) if since else spins_base()
    total_spins = _safe_count(total_spins_q.scalar())
    spins_today = _safe_count(spins_base().filter(Spin.created_at >= today).scalar())

    unique_q = roulette_db.query(func.count(distinct(Spin.user_id)))
    if event_id:
        unique_q = unique_q.filter(Spin.event_id == event_id)
    if since:
        unique_q = unique_q.filter(Spin.created_at >= since)
    unique_players = _safe_count(unique_q.scalar())

    return {
        "total_spins": total_spins,
        "spins_today": spins_today,
        "unique_players": unique_players,
    }


# ─── Notification metrics ─────────────────────────────────────────────────────

def _get_notification_metrics(notification_db: Session, period: str) -> dict:
    today = _today_start()
    since = _period_start(period)

    def notif_base():
        return notification_db.query(func.count(Notification.id))

    total_q = notif_base().filter(Notification.created_at >= since) if since else notif_base()
    total_sent = _safe_count(total_q.scalar())
    sent_today = _safe_count(notif_base().filter(Notification.created_at >= today).scalar())

    read_q = notif_base().filter(Notification.is_read == True)
    if since:
        read_q = read_q.filter(Notification.created_at >= since)
    total_read = _safe_count(read_q.scalar())
    read_rate = round(total_read / total_sent * 100, 2) if total_sent > 0 else 0.0

    push_subs = _safe_count(
        notification_db.query(func.count(PushSubscription.id)).scalar()
    )

    return {
        "total_sent": total_sent,
        "sent_today": sent_today,
        "read_rate_percent": read_rate,
        "push_subscriptions": push_subs,
    }


# ─── Page view metrics ────────────────────────────────────────────────────────

def _get_page_view_metrics(auth_db: Session, event_id: Optional[int], period: str) -> dict:
    today = _today_start()
    since = _period_start(period)

    def pv_base():
        q = auth_db.query(func.count(PageView.id))
        if event_id:
            q = q.filter(PageView.event_id == event_id)
        return q

    total_q = pv_base().filter(PageView.viewed_at >= since) if since else pv_base()
    total_views = _safe_count(total_q.scalar())
    views_today = _safe_count(pv_base().filter(PageView.viewed_at >= today).scalar())

    # Unique devices (distinct session_id)
    unique_q = auth_db.query(func.count(distinct(PageView.session_id)))
    if event_id:
        unique_q = unique_q.filter(PageView.event_id == event_id)
    if since:
        unique_q = unique_q.filter(PageView.viewed_at >= since)
    unique_devices = _safe_count(unique_q.scalar())

    # Authenticated vs anonymous
    auth_views_q = pv_base().filter(PageView.user_id.isnot(None))
    if since:
        auth_views_q = auth_views_q.filter(PageView.viewed_at >= since)
    authenticated_views = _safe_count(auth_views_q.scalar())
    anonymous_views = total_views - authenticated_views

    # Top 5 paths
    top_q = auth_db.query(PageView.path, func.count(PageView.id).label("cnt"))
    if event_id:
        top_q = top_q.filter(PageView.event_id == event_id)
    if since:
        top_q = top_q.filter(PageView.viewed_at >= since)
    top_rows = (
        top_q.group_by(PageView.path)
        .order_by(func.count(PageView.id).desc())
        .limit(5)
        .all()
    )
    top_paths = [{"path": row.path, "count": row.cnt} for row in top_rows]

    # Peak hour (UTC)
    peak_q = auth_db.query(
        extract("hour", PageView.viewed_at).label("hour"),
        func.count(PageView.id).label("cnt"),
    )
    if event_id:
        peak_q = peak_q.filter(PageView.event_id == event_id)
    if since:
        peak_q = peak_q.filter(PageView.viewed_at >= since)
    peak_row = (
        peak_q.group_by(extract("hour", PageView.viewed_at))
        .order_by(func.count(PageView.id).desc())
        .first()
    )
    peak_hour_utc = int(peak_row.hour) if peak_row else None

    # Average time on screen (seconds)
    avg_q = auth_db.query(func.avg(PageView.duration_seconds)).filter(
        PageView.duration_seconds.isnot(None)
    )
    if event_id:
        avg_q = avg_q.filter(PageView.event_id == event_id)
    if since:
        avg_q = avg_q.filter(PageView.viewed_at >= since)
    avg_duration = round(float(avg_q.scalar() or 0), 1)

    return {
        "total_views": total_views,
        "views_today": views_today,
        "unique_devices": unique_devices,
        "authenticated_views": authenticated_views,
        "anonymous_views": anonymous_views,
        "top_paths": top_paths,
        "peak_hour_utc": peak_hour_utc,
        "avg_duration_seconds": avg_duration,
    }


# ─── Record page view ─────────────────────────────────────────────────────────

def record_page_view(auth_db: Session, payload: PageViewTrack) -> None:
    view = PageView(
        session_id=payload.session_id,
        user_id=payload.user_id,
        path=payload.path,
        referrer_path=payload.referrer_path,
        device_type=payload.device_type,
        duration_seconds=payload.duration_seconds,
        event_id=payload.event_id,
    )
    auth_db.add(view)
    auth_db.commit()


# ─── Public API ───────────────────────────────────────────────────────────────

def _build_result(
    auth_db, admin_db, interaction_db, notification_db, roulette_db,
    event_id, period,
) -> dict:
    users = _get_user_metrics(auth_db, period)
    interactions = _get_interaction_metrics(interaction_db, event_id, period)
    ads = _get_ad_metrics(admin_db, event_id, period)
    photo_finder = _get_photo_finder_metrics(admin_db, interaction_db, event_id, period)
    posts = _get_post_metrics(admin_db, event_id, period)
    roulette = _get_roulette_metrics(roulette_db, event_id, period)
    notifications = _get_notification_metrics(notification_db, period)
    page_views = _get_page_view_metrics(auth_db, event_id, period)
    return {
        "users": users,
        "interactions": interactions,
        "ads": ads,
        "photo_finder": photo_finder,
        "posts": posts,
        "roulette": roulette,
        "notifications": notifications,
        "page_views": page_views,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cached": False,
    }


def get_realtime(
    auth_db: Session,
    admin_db: Session,
    interaction_db: Session,
    notification_db: Session,
    roulette_db: Session,
    event_id: Optional[int] = None,
    period: str = "all",
) -> dict:
    try:
        return _build_result(
            auth_db, admin_db, interaction_db, notification_db, roulette_db, event_id, period
        )
    except Exception as e:
        logger.error(f"Erro ao coletar métricas em tempo real: {e}", exc_info=True)
        raise


def get_summary(
    auth_db: Session,
    admin_db: Session,
    interaction_db: Session,
    notification_db: Session,
    roulette_db: Session,
    event_id: Optional[int] = None,
    period: str = "all",
) -> dict:
    cache_key = f"analytics:summary:e{event_id or 0}:p{period}"

    cached = redis_client.get(cache_key)
    if cached:
        cached["cached"] = True
        return cached

    try:
        result = _build_result(
            auth_db, admin_db, interaction_db, notification_db, roulette_db, event_id, period
        )
    except Exception as e:
        logger.error(f"Erro ao coletar métricas: {e}", exc_info=True)
        raise

    redis_client.set(cache_key, result, ttl=CACHE_TTL)
    return result
