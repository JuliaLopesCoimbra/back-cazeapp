from typing import List, Optional
from pydantic import BaseModel


class UserMetrics(BaseModel):
    total: int
    new_today: int
    new_this_week: int
    new_this_month: int


class InteractionMetrics(BaseModel):
    total_likes: int
    new_likes_today: int
    total_comments: int
    new_comments_today: int
    total_interactions: int


class AdMetrics(BaseModel):
    total_views: int
    views_today: int
    total_clicks: int
    clicks_today: int
    ctr_percent: float


class PhotoFinderMetrics(BaseModel):
    total_uploads: int
    uploads_today: int
    total_recognitions: int
    recognitions_today: int
    total_downloads: int
    downloads_today: int
    recognition_rate_percent: float


class PostMetrics(BaseModel):
    total_published: int
    published_today: int
    pending_approval: int
    rejected: int


class RouletteMetrics(BaseModel):
    total_spins: int
    spins_today: int
    unique_players: int


class NotificationMetrics(BaseModel):
    total_sent: int
    sent_today: int
    read_rate_percent: float
    push_subscriptions: int


class TopPath(BaseModel):
    path: str
    count: int


class PageViewMetrics(BaseModel):
    total_views: int
    views_today: int
    unique_devices: int
    authenticated_views: int
    anonymous_views: int
    top_paths: List[TopPath]
    peak_hour_utc: Optional[int]
    avg_duration_seconds: float


class PageViewTrack(BaseModel):
    session_id: str
    path: str
    referrer_path: Optional[str] = None
    device_type: Optional[str] = None
    duration_seconds: Optional[int] = None
    user_id: Optional[int] = None
    event_id: Optional[int] = None


class AnalyticsSummary(BaseModel):
    users: UserMetrics
    interactions: InteractionMetrics
    ads: AdMetrics
    photo_finder: PhotoFinderMetrics
    posts: PostMetrics
    roulette: RouletteMetrics
    notifications: NotificationMetrics
    page_views: PageViewMetrics
    generated_at: str
    cached: bool


# ─── Infra / CloudWatch ───────────────────────────────────────────────────────

class InstanceMetrics(BaseModel):
    instance_id: str
    label: str
    cpu_percent: Optional[float]
    network_in_bytes: Optional[float]
    network_out_bytes: Optional[float]
    status_ok: Optional[bool]


class ALBMetrics(BaseModel):
    request_count: Optional[float]
    errors_5xx: Optional[float]
    avg_response_ms: Optional[float]


class InfraMetrics(BaseModel):
    available: bool
    instances: List[InstanceMetrics]
    alb: Optional[ALBMetrics]
    period_minutes: int
    generated_at: str
