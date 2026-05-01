"""Metrics collection and alert processing services."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import Alert, AlertRule, Metric

logger = logging.getLogger("nomos-api.metrics")


class MetricsService:
    """Service for collecting, storing, and querying metrics."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_metric(
        self, metric_name: str, value: float, dimensions: dict[str, str] | None = None, source: str | None = None
    ) -> None:
        """Record a single metric data point."""
        metric = Metric(metric_name=metric_name, value=value, dimensions=dimensions or {}, source=source)
        self.session.add(metric)
        await self.session.commit()

    async def get_current_value(
        self, metric_name: str, *, window_minutes: int = 5, dimensions: dict[str, str] | None = None
    ) -> float | None:
        """Get the current value of a metric (average over time window)."""
        window_start = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        query = select(Metric.value).where(Metric.metric_name == metric_name, Metric.timestamp >= window_start)

        if dimensions:
            for key, value in dimensions.items():
                query = query.where(Metric.dimensions[key].astext == value)

        result = await self.session.execute(query)
        values = result.scalars().all()

        if not values:
            return None

        return sum(values) / len(values)

    async def get_metrics_series(
        self, metric_name: str, *, window_minutes: int = 60, dimensions: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        """Get time-series data for a metric."""
        window_start = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        query = (
            select(Metric)
            .where(Metric.metric_name == metric_name, Metric.timestamp >= window_start)
            .order_by(Metric.timestamp)
        )

        if dimensions:
            for key, value in dimensions.items():
                query = query.where(Metric.dimensions[key].astext == value)

        result = await self.session.execute(query)
        metrics = result.scalars().all()

        return [{"timestamp": m.timestamp.isoformat(), "value": m.value, "dimensions": m.dimensions} for m in metrics]


class AlertService:
    """Service for managing alerts and notifications."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_alerts(self) -> int:
        """Check all alert rules and trigger alerts if thresholds are breached.

        Returns:
            Number of new alerts triggered.
        """
        # Get all active alert rules
        result = await self.session.execute(select(AlertRule).where(AlertRule.is_active.is_(True)))
        rules = result.scalars().all()

        triggered_count = 0
        metrics_service = MetricsService(self.session)

        for rule in rules:
            # Get current metric value
            current_value = await metrics_service.get_current_value(
                rule.metric_name, window_minutes=self._parse_comparison_window(rule.comparison_window)
            )

            if current_value is None:
                continue

            # Check if threshold is breached
            if self._check_threshold(rule, current_value):
                # Check if alert already exists for this rule
                result = await self.session.execute(
                    select(Alert).where(Alert.rule_id == rule.id, Alert.resolved_at.is_(None))
                )
                existing_alert = result.scalar_one_or_none()

                if not existing_alert:
                    # Create new alert
                    alert = Alert(
                        rule_id=rule.id,
                        severity=rule.severity,
                        metric_name=rule.metric_name,
                        current_value=current_value,
                        threshold_value=rule.threshold_value,
                        notification_channels=rule.notification_channels,
                        context={
                            "current_value": current_value,
                            "threshold_value": rule.threshold_value,
                            "comparison_window": rule.comparison_window,
                        },
                    )
                    self.session.add(alert)
                    triggered_count += 1

                    logger.warning(
                        "Alert triggered: %s %s %.2f (threshold: %.2f)",
                        rule.metric_name,
                        rule.threshold_type,
                        current_value,
                        rule.threshold_value,
                    )

                    # Send notifications
                    await self._send_notifications(alert)

        await self.session.commit()
        return triggered_count

    def _parse_comparison_window(self, window: str | None) -> int:
        """Parse comparison window string to minutes."""
        if not window:
            return 5

        if window.endswith("m"):
            return int(window[:-1])
        elif window.endswith("h"):
            return int(window[:-1]) * 60
        elif window.endswith("d"):
            return int(window[:-1]) * 60 * 24
        else:
            return 5

    def _check_threshold(self, rule: AlertRule, current_value: float) -> bool:
        """Check if current value breaches the threshold."""
        if rule.threshold_type == "above":
            return current_value > rule.threshold_value
        elif rule.threshold_type == "below":
            return current_value < rule.threshold_value
        elif rule.threshold_type == "change":
            # For change detection, we'd need historical comparison
            # This is simplified for now
            return abs(current_value - rule.threshold_value) > (rule.threshold_value * 0.1)

        return False

    async def _send_notifications(self, alert: Alert) -> bool:
        """Send alert notifications via configured channels."""
        # This would be implemented with actual notification services
        # For now, just log the notification attempt

        logger.info("Sending alert notification for %s (severity: %s)", alert.metric_name, alert.severity)

        # Update notification status
        alert.notification_status = "sent"
        await self.session.commit()

        return True

    async def acknowledge_alert(self, alert_id: str) -> Alert | None:
        """Acknowledge an alert."""
        result = await self.session.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()

        if alert:
            alert.status = "acknowledged"
            await self.session.commit()
            await self.session.refresh(alert)

        return alert

    async def resolve_alert(self, alert_id: str) -> Alert | None:
        """Resolve an alert."""
        result = await self.session.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()

        if alert:
            alert.status = "resolved"
            alert.resolved_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(alert)

        return alert
