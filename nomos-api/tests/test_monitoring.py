"""Test monitoring functionality."""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import Alert, AlertRule, Metric
from nomos_api.services.metrics import AlertService, MetricsService


@pytest.mark.asyncio
async def test_metrics_service_record_and_retrieve(db_session: AsyncSession) -> None:
    """Test recording and retrieving metrics."""
    metrics_service = MetricsService(db_session)

    # Record a metric
    await metrics_service.record_metric(
        metric_name="test.metric", value=42.5, dimensions={"endpoint": "/test", "method": "GET"}, source="test"
    )

    # Retrieve the current value
    current_value = await metrics_service.get_current_value("test.metric", window_minutes=5)

    assert current_value is not None
    assert current_value == 42.5


@pytest.mark.asyncio
async def test_alert_service_threshold_check(db_session: AsyncSession) -> None:
    """Test alert threshold checking."""
    # Create an alert rule
    alert_rule = AlertRule(
        metric_name="test.error_rate",
        threshold_type="above",
        threshold_value=0.1,  # 10%
        severity="warning",
        notification_channels={"email": ["test@example.com"]},
        is_active=True,
    )
    db_session.add(alert_rule)
    await db_session.commit()

    # Record a metric that breaches the threshold
    metrics_service = MetricsService(db_session)
    await metrics_service.record_metric(
        metric_name="test.error_rate",
        value=0.15,  # 15% > 10% threshold
        dimensions={},
        source="test",
    )

    # Check alerts
    alert_service = AlertService(db_session)
    triggered_count = await alert_service.check_alerts()

    assert triggered_count == 1

    # Verify alert was created
    result = await db_session.execute(select(Alert).where(Alert.metric_name == "test.error_rate"))
    alert = result.scalar_one_or_none()

    assert alert is not None
    assert alert.severity == "warning"
    assert alert.current_value == 0.15
    assert alert.threshold_value == 0.1


@pytest.mark.asyncio
async def test_alert_acknowledge_and_resolve(db_session: AsyncSession) -> None:
    """Test alert acknowledgment and resolution."""
    # Create an alert
    alert = Alert(
        id="test-alert-123",
        severity="critical",
        metric_name="test.critical",
        current_value=100.0,
        threshold_value=90.0,
        notification_channels={"email": ["admin@example.com"]},
        context={"test": "alert"},
    )
    db_session.add(alert)
    await db_session.commit()

    # Acknowledge the alert
    alert_service = AlertService(db_session)
    acknowledged_alert = await alert_service.acknowledge_alert("test-alert-123")

    assert acknowledged_alert is not None
    assert acknowledged_alert.status == "acknowledged"

    # Resolve the alert
    resolved_alert = await alert_service.resolve_alert("test-alert-123")

    assert resolved_alert is not None
    assert resolved_alert.status == "resolved"
    assert resolved_alert.resolved_at is not None


@pytest.mark.asyncio
async def test_metrics_time_series(db_session: AsyncSession) -> None:
    """Test time series data retrieval."""
    metrics_service = MetricsService(db_session)

    # Record multiple metrics over time
    now = datetime.now(timezone.utc)
    for i in range(5):
        test_time = now - timedelta(minutes=5 - i)
        # We need to mock the timestamp for testing
        metric = Metric(
            metric_name="test.timeseries",
            value=float(i * 10),
            dimensions={"test": "series"},
            source="test",
            timestamp=test_time,
        )
        db_session.add(metric)
    await db_session.commit()

    # Retrieve time series
    series = await metrics_service.get_metrics_series("test.timeseries", window_minutes=10)

    assert len(series) == 5
    assert series[0]["value"] == 0.0
    assert series[-1]["value"] == 40.0
