import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse

from app.config.auth_db import get_db
from app.config.admin_db import get_admin_db
from app.config.interaction_db import get_interaction_db
from app.config.notification_db import get_notification_db
from app.config.roulette_db import get_roulette_db
from app.core.security.permissions import require_subadmin_or_master
from app.domain.auth.models.user_model import User
from app.domain.analytics.schemas.analytics_schema import AnalyticsSummary, InfraMetrics, PageViewTrack
from app.domain.analytics.services import analytics_service, infra_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.post("/track")
def track_page_view(
    payload: PageViewTrack,
    auth_db=Depends(get_db),
):
    """Records a page view. No auth required — tracks anonymous users too."""
    try:
        analytics_service.record_page_view(auth_db, payload)
    except Exception as e:
        logger.warning(f"Failed to record page view: {e}")
    return Response(status_code=204)


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    event_id: Optional[int] = Query(None, description="Filtrar por evento"),
    period: str = Query("all", description="Período: all | day | week | month"),
    auth_db=Depends(get_db),
    admin_db=Depends(get_admin_db),
    interaction_db=Depends(get_interaction_db),
    notification_db=Depends(get_notification_db),
    roulette_db=Depends(get_roulette_db),
    _: User = Depends(require_subadmin_or_master),
):
    return analytics_service.get_summary(
        auth_db, admin_db, interaction_db, notification_db, roulette_db,
        event_id=event_id, period=period,
    )


@router.get("/stream")
async def stream_analytics(
    event_id: Optional[int] = Query(None),
    period: str = Query("all"),
    _: User = Depends(require_subadmin_or_master),
):
    """SSE endpoint — streams fresh metrics every 5s. Auth via Bearer token."""

    async def event_generator():
        while True:
            auth_gen = get_db()
            admin_gen = get_admin_db()
            inter_gen = get_interaction_db()
            notif_gen = get_notification_db()
            roul_gen = get_roulette_db()

            auth_db = next(auth_gen)
            admin_db = next(admin_gen)
            inter_db = next(inter_gen)
            notif_db = next(notif_gen)
            roul_db = next(roul_gen)

            try:
                data = analytics_service.get_realtime(
                    auth_db, admin_db, inter_db, notif_db, roul_db,
                    event_id=event_id, period=period,
                )
                yield f"data: {json.dumps(data)}\n\n"
            except GeneratorExit:
                return
            except Exception as e:
                logger.error(f"SSE stream error: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': 'stream_error'})}\n\n"
            finally:
                auth_gen.close()
                admin_gen.close()
                inter_gen.close()
                notif_gen.close()
                roul_gen.close()

            await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/infra", response_model=InfraMetrics)
def get_infra_metrics(
    _: User = Depends(require_subadmin_or_master),
):
    """Returns AWS CloudWatch infrastructure metrics (CPU, network, ALB).
    Returns available=False when AWS_CLOUDWATCH_INSTANCE_IDS is not configured."""
    return infra_service.get_infra_metrics()
