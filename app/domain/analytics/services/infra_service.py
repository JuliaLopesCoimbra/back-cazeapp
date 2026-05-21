"""CloudWatch infrastructure metrics service."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config.settings import settings

logger = logging.getLogger(__name__)

# How far back to look for CloudWatch datapoints.
# EC2 basic monitoring: 5-min granularity + up to 5-min publish delay.
# 30-min window guarantees at least 2 datapoints regardless of alignment.
_LOOKBACK_MINUTES = 30
_PERIOD_SECONDS = 300  # 5-minute granularity


def _cw_client():
    return boto3.client(
        "cloudwatch",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY,
    )


def _latest_value(cw, namespace: str, metric_name: str, dimensions: list, statistic: str) -> Optional[float]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(minutes=_LOOKBACK_MINUTES)
    try:
        resp = cw.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start,
            EndTime=now,
            Period=_PERIOD_SECONDS,
            Statistics=[statistic],
        )
        points = resp.get("Datapoints", [])
        if not points:
            logger.debug(f"CloudWatch: no datapoints for {namespace}/{metric_name} dims={dimensions}")
            return None
        latest = sorted(points, key=lambda p: p["Timestamp"])[-1]
        return round(float(latest[statistic]), 2)
    except ClientError as exc:
        logger.error(f"CloudWatch ClientError [{namespace}/{metric_name}]: {exc.response['Error']['Code']} — {exc.response['Error']['Message']}")
        return None
    except BotoCoreError as exc:
        logger.error(f"CloudWatch BotoCoreError [{namespace}/{metric_name}]: {exc}")
        return None


def get_infra_metrics() -> dict:
    instance_ids_raw = settings.AWS_CLOUDWATCH_INSTANCE_IDS
    if not instance_ids_raw:
        return {
            "available": False,
            "instances": [],
            "alb": None,
            "period_minutes": _LOOKBACK_MINUTES,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # Suporta formato "id:label" ou apenas "id"
    parsed = []
    for entry in instance_ids_raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" in entry:
            iid, label = entry.split(":", 1)
            parsed.append((iid.strip(), label.strip()))
        else:
            parsed.append((entry, entry))

    cw = _cw_client()
    now = datetime.now(timezone.utc)

    instances = []
    for iid, label in parsed:
        dims = [{"Name": "InstanceId", "Value": iid}]
        cpu = _latest_value(cw, "AWS/EC2", "CPUUtilization", dims, "Average")
        net_in = _latest_value(cw, "AWS/EC2", "NetworkIn", dims, "Average")
        net_out = _latest_value(cw, "AWS/EC2", "NetworkOut", dims, "Average")
        status = _latest_value(cw, "AWS/EC2", "StatusCheckFailed", dims, "Maximum")
        instances.append({
            "instance_id": iid,
            "label": label,
            "cpu_percent": cpu,
            "network_in_bytes": net_in,
            "network_out_bytes": net_out,
            "status_ok": (status == 0) if status is not None else None,
        })

    alb = None
    alb_suffix = settings.AWS_CLOUDWATCH_ALB_SUFFIX
    if alb_suffix:
        alb_dims = [{"Name": "LoadBalancer", "Value": alb_suffix}]
        req = _latest_value(cw, "AWS/ApplicationELB", "RequestCount", alb_dims, "Sum")
        err = _latest_value(cw, "AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count", alb_dims, "Sum")
        resp = _latest_value(cw, "AWS/ApplicationELB", "TargetResponseTime", alb_dims, "Average")
        alb = {
            "request_count": req,
            "errors_5xx": err,
            "avg_response_ms": round(resp * 1000, 1) if resp is not None else None,
        }

    return {
        "available": True,
        "instances": instances,
        "alb": alb,
        "period_minutes": _LOOKBACK_MINUTES,
        "generated_at": now.isoformat(),
    }
