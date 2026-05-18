"""Monitoring and metrics endpoints for NomOS.

GET /api/monitoring/metrics — get current metrics
GET /api/monitoring/alerts — list active alerts
POST /api/monitoring/alerts — create manual alert
PATCH /api/monitoring/alerts/{alert_id} — acknowledge/resolve alert
GET /api/monitoring/health — extended health check with metrics
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.auth.rbac import require_admin
from nomos_api.database import get_db
from nomos_api.models import Alert, AlertRule, Metric, User
from nomos_api.schemas import (
    AlertCreate,
    AlertResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertUpdate,
    MetricsResponse,
)

logger = logging.getLogger("nomos-api.monitoring")

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> MetricsResponse:
    """Get current system metrics aggregated over the last 5 minutes."""
    five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)

    # Get API performance metrics
    result = await db.execute(
        select(Metric).where(
            Metric.metric_name.in_(["api.latency", "api.error_rate", "api.requests"]),
            Metric.timestamp >= five_minutes_ago,
        )
    )
    api_metrics = result.scalars().all()

    # Get agent health metrics
    result = await db.execute(
        select(Metric).where(
            Metric.metric_name.in_(["agent.online", "agent.stale", "agent.offline"]),
            Metric.timestamp >= five_minutes_ago,
        )
    )
    agent_metrics = result.scalars().all()

    # Get system metrics
    result = await db.execute(
        select(Metric).where(
            Metric.metric_name.in_(["system.cpu", "system.memory", "cache.hit_rate"]),
            Metric.timestamp >= five_minutes_ago,
        )
    )
    system_metrics = result.scalars().all()

    return MetricsResponse(
        api=format_metrics(api_metrics),
        agents=format_metrics(agent_metrics),
        system=format_metrics(system_metrics),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def format_metrics(metrics: Sequence[Metric]) -> dict[str, Any]:
    """Convert sequence of Metric objects to dictionary format."""
    formatted = {}
    for metric in metrics:
        key = metric.metric_name
        if key not in formatted:
            formatted[key] = {"values": [], "dimensions": metric.dimensions}
        formatted[key]["values"].append({"timestamp": metric.timestamp.isoformat(), "value": metric.value})
    return formatted


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    severity: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[AlertResponse]:
    """List active alerts, optionally filtered by severity and status."""
    query = select(Alert)

    if severity:
        query = query.where(Alert.severity == severity)

    if status:
        query = query.where(Alert.status == status)
    else:
        # Default to active alerts (not resolved)
        query = query.where(Alert.resolved_at.is_(None))

    result = await db.execute(query.order_by(Alert.triggered_at.desc()))
    alerts = result.scalars().all()

    return [AlertResponse.from_orm(alert) for alert in alerts]


@router.post("/alerts", response_model=AlertResponse, status_code=201)
async def create_alert(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> AlertResponse:
    """Create a manual alert (for testing or manual triggers)."""
    alert = Alert(
        id=alert_data.id or f"alert_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        severity=alert_data.severity,
        metric_name=alert_data.metric_name,
        current_value=alert_data.current_value,
        threshold_value=alert_data.threshold_value,
        notification_channels=alert_data.notification_channels or {"email": []},
        context=alert_data.context or {},
        status="triggered",
    )

    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return AlertResponse.from_orm(alert)


@router.patch("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    update_data: AlertUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> AlertResponse:
    """Acknowledge or resolve an alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if update_data.status:
        alert.status = update_data.status
        if update_data.status == "resolved":
            alert.resolved_at = datetime.now(timezone.utc)

    if update_data.notification_status:
        alert.notification_status = update_data.notification_status

    await db.commit()
    await db.refresh(alert)

    return AlertResponse.from_orm(alert)


@router.get("/alert-rules", response_model=list[AlertRuleResponse])
async def list_alert_rules(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[AlertRuleResponse]:
    """List all configured alert rules."""
    result = await db.execute(select(AlertRule).where(AlertRule.is_active.is_(True)))
    rules = result.scalars().all()

    return [AlertRuleResponse.from_orm(rule) for rule in rules]


@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=201)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> AlertRuleResponse:
    """Create a new alert rule."""
    rule = AlertRule(
        metric_name=rule_data.metric_name,
        threshold_type=rule_data.threshold_type,
        threshold_value=rule_data.threshold_value,
        comparison_window=rule_data.comparison_window,
        severity=rule_data.severity,
        notification_channels=rule_data.notification_channels,
        description=rule_data.description,
        is_active=rule_data.is_active,
    )

    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return AlertRuleResponse.from_orm(rule)


@router.delete("/alert-rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Delete an alert rule."""
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    await db.execute(delete(AlertRule).where(AlertRule.id == rule_id))
    await db.commit()
    return Response(status_code=204)
