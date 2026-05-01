# NomOS Monitoring and Alerting System Design

## 1. Key Metrics to Monitor

### API Performance Metrics
- **Request Latency**: Track P99, P95, P50 response times per endpoint
- **Throughput**: Requests per second/minute
- **Error Rates**: 4xx/5xx errors by endpoint and status code
- **Database Query Performance**: Slow queries (>100ms)
- **Cache Hit/Miss Ratio**: Valkey cache efficiency

### Agent Health Metrics
- **Heartbeat Status**: Agents online/stale/offline counts
- **Agent Response Time**: Time to complete tasks
- **Agent Error Rates**: Task failures per agent
- **Agent Resource Usage**: CPU, memory from agent metrics

### System Health Metrics
- **Vault Status**: Sealed/unsealed/healthy
- **PostgreSQL Health**: Connection pool usage, query queue length
- **Valkey Health**: Memory usage, eviction rates
- **Gateway Health**: Online/offline status, response time
- **Background Jobs**: Worker queue length, job processing time

### Compliance Metrics
- **Incident Response Time**: Time to acknowledge/escalate incidents
- **DSGVO Deadlines**: Incidents approaching 72h deadline
- **Budget Limits**: Agents approaching cost limits
- **Approval Queue**: Pending approvals count and age

## 2. Alerting Thresholds and Notification Methods

### Critical Alerts (Immediate Notification)
- **API Unavailable**: 5xx errors > 5% for 5 minutes
- **Database Down**: PostgreSQL unavailable
- **Vault Sealed**: Unexpected vault sealing
- **Agent Fleet Failure**: >30% agents stale/offline
- **Incident Deadline Breach**: DSGVO 72h deadline missed
- **Budget Limit Breached**: Agent exceeds cost limit

### Warning Alerts (Notification within 15 minutes)
- **High Latency**: P99 latency > 500ms for 10 minutes
- **Error Rate Increase**: 4xx/5xx up 20% from baseline
- **Cache Inefficiency**: Cache miss rate > 30%
- **Agent Degradation**: >15% agents stale
- **Incident Approaching Deadline**: Within 4 hours of DSGVO deadline
- **Budget Approaching Limit**: >80% of agent budget consumed

### Notification Methods
- **Email**: For all alerts (SMTP integration)
- **Webhooks**: Slack/Teams/Microsoft Teams integration
- **Console UI**: Real-time dashboard notifications
- **Audit Log**: All alerts recorded in compliance audit trail

## 3. Integration with Existing NomOS Components

### Current Monitoring Infrastructure
- **Structured Logging**: JSONFormatter in middleware/logging.py
- **Health Checks**: /health endpoint with component status
- **Heartbeat System**: Agent heartbeat tracking
- **Incident Management**: DSGVO deadline monitoring
- **Background Workers**: ARQ job system

### Integration Points
1. **Logging Pipeline**: Enhance JSONFormatter to include metric fields
2. **Health Router**: Extend with detailed metrics endpoint
3. **Worker Jobs**: Add monitoring job for threshold checking
4. **Database Models**: Add metrics tables for time-series data
5. **API Middleware**: Instrument request/response metrics
6. **Agent Heartbeat**: Store and analyze agent metrics

## 4. Logging and Visualization

### Enhanced Logging
```python
# Extended JSONFormatter with metric fields
_EXTRA_FIELDS = (
    "request_id", "method", "path", "status", "duration_ms",
    "user_id", "agent_id", "latency_ms", "error_type", "cache_hit"
)
```

### Metrics Storage
- **Time-Series Database**: Add Prometheus or TimescaleDB
- **Retention Policy**: 30 days high-resolution, 1 year aggregated
- **Indexing**: By service, endpoint, agent_id, timestamp

### Visualization Dashboard
- **Overview Panel**: System health score, critical alerts
- **API Performance**: Latency heatmap, error rate trends
- **Agent Fleet**: Online/stale/offline pie chart, response times
- **Compliance**: Incident timeline, budget usage
- **Infrastructure**: DB connections, cache efficiency, worker queues

## 5. Implementation Approach

### Phase 1: Core Monitoring (2 weeks)
1. **Enhance Logging Middleware**
   - Add latency tracking to RequestLoggingMiddleware
   - Include error classification in logs
   - Add cache hit/miss tracking

2. **Extend Health Endpoint**
   - Add `/api/health/metrics` with detailed metrics
   - Include historical trends (last 24h)
   - Add Prometheus-compatible `/metrics` endpoint

3. **Agent Metrics Collection**
   - Store agent metrics from heartbeats
   - Calculate agent health scores
   - Detect anomalies in agent behavior

### Phase 2: Alerting System (1 week)
1. **Alert Threshold Configuration**
   - Database table for alert rules
   - Admin UI for threshold management
   - Default thresholds with overrides

2. **Notification Service**
   - Email sender integration
   - Webhook dispatcher
   - Alert deduplication and throttling

3. **Alert Processing Job**
   - Scheduled job checking thresholds
   - Alert escalation logic
   - Notification delivery tracking

### Phase 3: Visualization (2 weeks)
1. **Metrics API**
   - Time-series query endpoints
   - Aggregation functions
   - Filtering by time range and dimensions

2. **Dashboard UI**
   - React components for charts
   - Real-time updates via WebSocket
   - Historical comparison views

3. **Export and Integration**
   - Prometheus exporter
   - Grafana dashboard templates
   - SIEM integration (Splunk/ELK)

### Phase 4: Advanced Features (Ongoing)
- Anomaly detection using ML
- Predictive alerting
- Capacity planning reports
- SLA compliance reporting

## Implementation Details

### Database Schema Extensions

```sql
-- Alert rules table
CREATE TABLE alert_rules (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    threshold_type VARCHAR(50) NOT NULL, -- 'above', 'below', 'change'
    threshold_value FLOAT NOT NULL,
    comparison_window INTERVAL,
    severity VARCHAR(50) NOT NULL, -- 'critical', 'warning', 'info'
    notification_channels JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Alert history table
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    rule_id INTEGER REFERENCES alert_rules(id),
    severity VARCHAR(50) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    current_value FLOAT NOT NULL,
    threshold_value FLOAT NOT NULL,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    notification_status VARCHAR(50) NOT NULL, -- 'pending', 'sent', 'failed'
    notification_channels JSONB,
    context JSONB
);

-- Time-series metrics table
CREATE TABLE metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    dimensions JSONB NOT NULL, -- {"endpoint": "/api/agents", "method": "GET"}
    value FLOAT NOT NULL,
    source VARCHAR(50) -- 'api', 'agent', 'system'
);

-- Create indexes for performance
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX idx_metrics_name ON metrics(metric_name);
CREATE INDEX idx_metrics_dimensions ON metrics USING GIN(dimensions);
```

### Alert Processing Job

```python
# nomos_api/worker/jobs/alerts.py
async def process_alerts(ctx: dict[str, Any] | None) -> int:
    """Check all alert rules and trigger notifications.
    
    Runs every minute. Evaluates current metrics against thresholds
    and creates alerts when thresholds are breached.
    """
    from nomos_api.models import AlertRule, Alert
    from nomos_api.services.metrics import get_current_metrics
    
    async with session_factory() as session:
        # Get all active alert rules
        rules = await session.execute(select(AlertRule))
        alert_rules = rules.scalars().all()
        
        triggered_count = 0
        for rule in alert_rules:
            # Get current metric value
            current_value = await get_current_metrics(
                rule.metric_name, 
                rule.comparison_window
            )
            
            # Check threshold
            if rule.should_trigger(current_value):
                # Create alert if not already active
                existing = await session.execute(
                    select(Alert).where(
                        Alert.rule_id == rule.id,
                        Alert.resolved_at.is_(None)
                    )
                )
                
                if not existing.scalar_one_or_none():
                    alert = Alert(
                        rule_id=rule.id,
                        severity=rule.severity,
                        metric_name=rule.metric_name,
                        current_value=current_value,
                        threshold_value=rule.threshold_value,
                        context={"current": current_value, "threshold": rule.threshold_value}
                    )
                    session.add(alert)
                    triggered_count += 1
                    
                    # Send notifications
                    await send_alert_notifications(alert)
        
        await session.commit()
        return triggered_count
```

### Enhanced Health Endpoint

```python
# nomos_api/routers/health.py
@router.get("/metrics", response_model=dict)
async def metrics() -> dict:
    """Return detailed metrics in Prometheus format."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    # Collect API metrics
    api_metrics = collect_api_metrics()
    
    # Collect agent metrics
    agent_metrics = await collect_agent_metrics()
    
    # Collect system metrics
    system_metrics = collect_system_metrics()
    
    # Format as Prometheus text
    output = generate_latest(
        REGISTRY.unregister()  # Combine all metrics
    )
    
    return Response(content=output, media_type=CONTENT_TYPE_LATEST)
```

### Notification Service

```python
# nomos_api/services/notifications.py
class NotificationService:
    def __init__(self):
        self.email_client = EmailClient()
        self.webhook_client = WebhookClient()
        
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via configured notification channels."""
        success = True
        
        # Email notification
        if "email" in alert.notification_channels:
            recipients = alert.notification_channels["email"]
            subject = f"[NomOS {alert.severity.upper()}] {alert.metric_name} alert"
            body = self._format_email_body(alert)
            email_success = await self.email_client.send(recipients, subject, body)
            success = success and email_success
        
        # Webhook notification
        if "webhook" in alert.notification_channels:
            webhook_urls = alert.notification_channels["webhook"]
            payload = self._format_webhook_payload(alert)
            webhook_success = await self.webhook_client.send(webhook_urls, payload)
            success = success and webhook_success
        
        return success
```

## Deployment and Operations

### Configuration
```yaml
# Monitoring configuration in settings
monitoring:
  # Metrics collection
  metrics_retention_days: 30
  metrics_aggregation_interval: "5m"
  
  # Alerting
  alert_check_interval: "1m"
  default_notification_channels:
    - "email:admin@nomos.local"
    - "webhook:https://slack.com/alerts"
  
  # Thresholds
  default_thresholds:
    api_error_rate: 0.05  # 5%
    api_latency_p99: 500  # ms
    agent_stale_percentage: 0.15  # 15%
```

### Monitoring Setup
```bash
# Add to docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    depends_on:
      - nomos-api
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-storage:/var/lib/grafana
    depends_on:
      - prometheus
```

### Alert Examples

**Critical API Failure Alert**
```json
{
  "alert_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
  "severity": "critical",
  "metric": "api.error_rate",
  "current_value": 0.12,
  "threshold": 0.05,
  "triggered_at": "2026-04-13T14:30:45Z",
  "context": {
    "endpoint": "/api/agents/list",
    "error_type": "database_connection_failed",
    "affected_users": 42
  },
  "notification_channels": ["email", "slack"]
}
```

**Agent Health Warning**
```json
{
  "alert_id": "z9y8x7w6-5432-10uv-wxyz-abcdefghijkl",
  "severity": "warning",
  "metric": "agent.stale_percentage",
  "current_value": 0.18,
  "threshold": 0.15,
  "triggered_at": "2026-04-13T14:35:12Z",
  "context": {
    "total_agents": 50,
    "stale_agents": 9,
    "stale_agent_ids": ["agent-1", "agent-5", "agent-42"]
  }
}
```

## Success Metrics

1. **Mean Time to Detect (MTTD)**: < 1 minute for critical issues
2. **Mean Time to Acknowledge (MTTA)**: < 5 minutes for critical alerts
3. **Alert Accuracy**: < 5% false positives
4. **System Availability**: 99.95% uptime
5. **Compliance**: 100% DSGVO incidents notified within deadline

## Risks and Mitigations

**Risk**: Alert fatigue from too many notifications
**Mitigation**: Implement smart alert grouping and throttling

**Risk**: Performance impact from detailed metrics collection
**Mitigation**: Use sampling for high-volume metrics, async processing

**Risk**: Complex setup and maintenance
**Mitigation**: Provide default configurations, health checks for monitoring system

**Risk**: Notification channel failures
**Mitigation**: Multiple fallback channels, alert delivery monitoring

This comprehensive monitoring and alerting system will provide real-time visibility into the NomOS system health, enable proactive issue resolution, and ensure compliance with operational and regulatory requirements.