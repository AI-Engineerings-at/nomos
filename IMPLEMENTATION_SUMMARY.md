# NomOS Monitoring and Alerting Implementation Summary

## Overview
This document summarizes the comprehensive monitoring and alerting system implemented for NomOS, covering API performance, agent health, system metrics, and compliance monitoring.

## 1. Core Components Implemented

### Database Schema Extensions
**New Tables Added:**
- `alert_rules`: Stores alert threshold configurations
- `alerts`: Records triggered alerts and their status
- `metrics`: Time-series data for all monitored metrics

**Key Fields:**
- Alert rules with configurable thresholds and notification channels
- Alert history with severity, status, and resolution tracking
- Metrics with timestamps, dimensions, and source attribution

### API Endpoints
**Monitoring Router (`/api/monitoring`):**
- `GET /metrics`: Get current system metrics aggregated over time windows
- `GET /alerts`: List active alerts with filtering by severity/status
- `POST /alerts`: Create manual alerts (for testing or special cases)
- `PATCH /alerts/{alert_id}`: Acknowledge or resolve alerts
- `GET /alert-rules`: List configured alert rules
- `POST /alert-rules`: Create new alert rules
- `DELETE /alert-rules/{rule_id}`: Remove alert rules

### Services
**MetricsService (`nomos_api/services/metrics.py`):**
- `record_metric()`: Store time-series metric data
- `get_current_value()`: Calculate current metric values with aggregation
- `get_metrics_series()`: Retrieve time-series data for visualization

**AlertService (`nomos_api/services/metrics.py`):**
- `check_alerts()`: Evaluate all rules against current metrics
- `acknowledge_alert()`: Mark alerts as acknowledged
- `resolve_alert()`: Mark alerts as resolved
- Notification dispatching via email/webhooks

### Background Jobs
**Alert Processing Job (`nomos_api/worker/jobs/alerts.py`):**
- Runs every minute via ARQ worker
- Checks all active alert rules
- Creates alerts when thresholds breached
- Sends notifications via configured channels

### Middleware
**API Metrics Middleware (`nomos_api/middleware/metrics.py`):**
- Automatically collects request/response metrics
- Tracks latency, error rates, request volumes
- Stores metrics in time-series database

## 2. Key Metrics Collected

### API Performance Metrics
- **Request Volume**: Counts by endpoint/method/status
- **Latency**: P99, P95, P50 response times
- **Error Rates**: 4xx/5xx errors by endpoint
- **Throughput**: Requests per minute

### Agent Health Metrics
- **Heartbeat Status**: Online/stale/offline counts
- **Task Completion**: Success/failure rates
- **Response Times**: Task execution duration
- **Resource Usage**: CPU/memory from agent reports

### System Health Metrics
- **Database**: Connection pool usage, query performance
- **Cache**: Hit/miss ratios, memory usage
- **Vault**: Sealed/unsealed status
- **Gateway**: Online/offline, response time

### Compliance Metrics
- **Incident Response**: Time to acknowledge/escalate
- **DSGVO Deadlines**: Time remaining for reporting
- **Budget Usage**: Current vs. limit per agent
- **Approval Queue**: Pending approvals count/age

## 3. Alerting System

### Threshold Types
- **Above**: Trigger when metric exceeds threshold
- **Below**: Trigger when metric falls below threshold  
- **Change**: Trigger when metric changes significantly

### Severity Levels
- **Critical**: Immediate action required (e.g., API down)
- **Warning**: Potential issues (e.g., high latency)
- **Info**: Informational alerts (e.g., maintenance)

### Notification Channels
- **Email**: SMTP integration for alert emails
- **Webhooks**: Slack/Teams/Microsoft Teams integration
- **Console UI**: Real-time dashboard notifications
- **Audit Log**: All alerts recorded for compliance

### Default Alert Rules
```python
# Example default rules that could be seeded
DEFAULT_ALERT_RULES = [
    {
        "metric_name": "api.error_rate",
        "threshold_type": "above",
        "threshold_value": 0.05,  # 5%
        "severity": "critical",
        "comparison_window": "5m",
        "notification_channels": {
            "email": ["admin@nomos.local"],
            "webhook": ["https://slack.com/alerts"]
        }
    },
    {
        "metric_name": "agent.stale_percentage",
        "threshold_type": "above",
        "threshold_value": 0.15,  # 15%
        "severity": "warning",
        "comparison_window": "15m",
        "notification_channels": {
            "email": ["ops@nomos.local"]
        }
    }
]
```

## 4. Integration Points

### Existing Component Enhancements
1. **Health Router**: Extended with detailed metrics endpoint
2. **Agent Heartbeat**: Enhanced to store agent metrics
3. **Incident Management**: Integrated with alerting system
4. **Logging**: Enhanced structured logging with metric fields
5. **Background Workers**: Added alert processing job

### Data Flow
```
[API Requests] → [Metrics Middleware] → [Metrics Service] → [Database]
[Agent Heartbeats] → [Heartbeat Service] → [Metrics Service] → [Database]
[Alert Rules] → [Alert Service] → [Notification Service] → [Email/Webhooks]
[Dashboard] → [Metrics API] → [Visualization] → [User]
```

## 5. Implementation Status

### ✅ Completed
- Database schema extensions (alert_rules, alerts, metrics)
- Monitoring API endpoints (metrics, alerts, alert-rules)
- Metrics collection service
- Alert processing service
- Alert notification system
- API metrics middleware
- Background alert processing job
- Database migration script

### 🚧 In Progress
- Advanced visualization dashboard
- Prometheus/Grafana integration
- Machine learning anomaly detection
- Capacity planning reports

### 📋 Planned Enhancements
- SLA compliance reporting
- Predictive alerting
- Multi-channel notification fallbacks
- Alert escalation policies
- Maintenance windows

## 6. Deployment Instructions

### Database Migration
```bash
# Apply the monitoring tables migration
cd nomos-api
alembic upgrade head
```

### Configuration
Add to `.env`:
```env
# Monitoring settings
MONITORING_METRICS_RETENTION_DAYS=30
MONITORING_ALERT_CHECK_INTERVAL=60

# Notification settings  
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=alerts@nomos.local
SMTP_PASSWORD=your-password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### Start Services
```bash
# Start the API with monitoring enabled
docker compose up -d nomos-api

# Start the worker with alert processing
docker compose up -d nomos-worker
```

## 7. Example Usage

### Create Alert Rule
```bash
curl -X POST "http://localhost:8060/api/monitoring/alert-rules" \
  -H "Content-Type: application/json" \
  -H "X-NomOS-API-Key: your-api-key" \
  -d '{
    "metric_name": "api.latency",
    "threshold_type": "above",
    "threshold_value": 500,
    "severity": "warning",
    "comparison_window": "5m",
    "notification_channels": {
      "email": ["admin@nomos.local"],
      "webhook": ["https://slack.com/alerts"]
    },
    "description": "High API latency detected"
  }'
```

### Get Current Metrics
```bash
curl -X GET "http://localhost:8060/api/monitoring/metrics" \
  -H "X-NomOS-API-Key: your-api-key"
```

### List Active Alerts
```bash
curl -X GET "http://localhost:8060/api/monitoring/alerts?severity=critical" \
  -H "X-NomOS-API-Key: your-api-key"
```

### Acknowledge Alert
```bash
curl -X PATCH "http://localhost:8060/api/monitoring/alerts/alert-123" \
  -H "Content-Type: application/json" \
  -H "X-NomOS-API-Key: your-api-key" \
  -d '{"status": "acknowledged"}'
```

## 8. Monitoring Best Practices

### Alert Management
- **Start Conservative**: Begin with few critical alerts
- **Tune Thresholds**: Adjust based on real-world behavior
- **Avoid Alert Fatigue**: Use appropriate severity levels
- **Document Alerts**: Include runbooks for each alert type
- **Regular Review**: Monthly review of alert effectiveness

### Metrics Collection
- **Sample High-Volume Metrics**: Not every request needs recording
- **Aggregate Appropriately**: Use time windows that make sense
- **Retention Policies**: Balance detail with storage costs
- **Dimension Wisely**: Only add dimensions that will be queried

### Dashboard Design
- **Overview First**: High-level health score on main dashboard
- **Drill-Down**: Detailed views for troubleshooting
- **Historical Context**: Show trends, not just current values
- **Actionable**: Include links to relevant tools

## 9. Troubleshooting

### Common Issues

**Alerts Not Triggering:**
- Check alert rule is active
- Verify metric names match exactly
- Confirm thresholds are appropriate
- Check comparison windows

**Notifications Not Sent:**
- Verify notification channel configuration
- Check SMTP/webhook credentials
- Review notification service logs
- Test with manual alert creation

**High Metric Storage:**
- Reduce metrics retention period
- Increase aggregation windows
- Sample high-volume metrics
- Archive old metrics to cold storage

## 10. Future Enhancements

### Short-Term (Next 3 Months)
- **Prometheus Exporter**: Standard metrics endpoint
- **Grafana Dashboards**: Pre-configured visualizations
- **Alert Escalation**: Multi-level notification policies
- **Maintenance Windows**: Suppress alerts during maintenance

### Medium-Term (Next 6 Months)
- **Anomaly Detection**: ML-based pattern recognition
- **Capacity Planning**: Predict resource needs
- **SLA Reporting**: Compliance with service agreements
- **Multi-Tenancy**: Per-customer alerting profiles

### Long-Term (Next Year)
- **AIOps Integration**: Automated remediation
- **Root Cause Analysis**: Automatic incident correlation
- **Predictive Alerting**: Forecast issues before they occur
- **Benchmarking**: Compare against industry standards

## Conclusion

This comprehensive monitoring and alerting system provides real-time visibility into the NomOS platform, enabling proactive issue resolution and ensuring compliance with operational requirements. The system is designed for extensibility, allowing for future enhancements as monitoring needs evolve.