# NomOS Monitoring and Infrastructure Hardening - Operational Runbooks

## Table of Contents

1. [Standard Operating Procedures](#standard-operating-procedures)
2. [Alert Response Procedures](#alert-response-procedures)
3. [System Maintenance](#system-maintenance)
4. [Emergency Procedures](#emergency-procedures)
5. [Vault Management](#vault-management)
6. [Setup and Configuration](#setup-and-configuration)

## Standard Operating Procedures

### Daily Operations Checklist

**Morning Check (09:00)**
- [ ] Review active alerts in console
- [ ] Check system health dashboard
- [ ] Verify all components (Vault, PostgreSQL, Valkey, Gateway) are healthy
- [ ] Review overnight logs for errors
- [ ] Check agent fleet status

**Evening Check (17:00)**
- [ ] Review unresolved alerts
- [ ] Check metric trends for anomalies
- [ ] Verify backup completion
- [ ] Check budget usage for all agents

### Weekly Operations Checklist

**Monday - System Health Review**
- [ ] Review weekly metric trends
- [ ] Check database performance metrics
- [ ] Verify cache hit ratios
- [ ] Review agent task completion rates

**Wednesday - Security Review**
- [ ] Check Vault audit logs
- [ ] Review failed authentication attempts
- [ ] Verify 2FA compliance
- [ ] Check for outdated secrets

**Friday - Capacity Planning**
- [ ] Review resource usage trends
- [ ] Check storage capacity
- [ ] Review API latency trends
- [ ] Plan for upcoming capacity needs

## Alert Response Procedures

### Critical Alert Response

**Alert: API Unavailable (5xx errors > 5% for 5 minutes)**

**Immediate Actions:**
1. Acknowledge alert in console
2. Check `/api/health` endpoint for component status
3. Review recent logs: `docker logs nomos-api --since 5m`
4. Check database connectivity: `docker exec nomos-api psql -c "SELECT 1"`

**Troubleshooting Steps:**
1. Restart API service: `docker restart nomos-api`
2. Check database: `docker restart nomos-postgres`
3. Verify Vault status: `vault status`
4. Check for resource exhaustion: `docker stats`

**Escalation:**
- If unresolved within 15 minutes, escalate to engineering team
- If database issue, contact DBA team
- If infrastructure issue, contact cloud provider support

**Resolution:**
- Document root cause in alert notes
- Mark alert as resolved
- Create follow-up task for permanent fix

### Warning Alert Response

**Alert: High API Latency (P99 > 500ms for 10 minutes)**

**Immediate Actions:**
1. Acknowledge alert
2. Check current latency metrics: `GET /api/monitoring/metrics?metric=api.latency`
3. Review slow query logs
4. Check for traffic spikes

**Troubleshooting Steps:**
1. Identify slow endpoints: Check metrics by endpoint dimension
2. Review database query performance
3. Check cache hit ratios
4. Verify no blocking operations

**Mitigation:**
- Add caching for slow endpoints
- Optimize database queries
- Consider horizontal scaling
- Implement rate limiting if traffic spike

**Resolution:**
- Monitor for improvement
- Mark resolved when latency returns to normal
- Document findings

### Info Alert Response

**Alert: Maintenance Window Starting**

**Actions:**
1. Acknowledge alert
2. Notify team via Slack
3. Check maintenance schedule
4. Verify backup completion

**Post-Maintenance:**
1. Verify all services restarted successfully
2. Check system health
3. Monitor for any issues
4. Mark alert resolved

## System Maintenance

### Monthly Maintenance Window

**Preparation (1 week before):**
- [ ] Schedule maintenance window
- [ ] Notify all users
- [ ] Prepare rollback plan
- [ ] Test changes in staging

**During Maintenance:**
1. Enable maintenance mode in console
2. Apply database migrations
3. Deploy new versions
4. Restart services in order:
   - Vault
   - PostgreSQL
   - Valkey
   - API
   - Worker
   - Console
   - Gateway
5. Verify system health
6. Disable maintenance mode

**Post-Maintenance:**
- [ ] Verify all alerts cleared
- [ ] Check error logs
- [ ] Monitor system for 1 hour
- [ ] Document any issues

### Database Maintenance

**Weekly Vacuum:**
```bash
docker exec nomos-postgres vacuumdb --analyze --all
```

**Monthly Backup:**
```bash
docker exec nomos-postgres pg_dump -U nomos -Fc nomos > backup_$(date +%Y%m%d).dump
```

**Backup Verification:**
```bash
docker exec -i nomos-postgres pg_restore --verify backup_latest.dump
```

### Cache Maintenance

**Weekly Cache Check:**
```bash
# Check Valkey memory usage
docker exec nomos-valkey redis-cli info memory

# Check hit ratios
docker exec nomos-valkey redis-cli info stats | grep keyspace_hits
```

**Monthly Cache Optimization:**
```bash
# Analyze cache keys
docker exec nomos-valkey redis-cli --bigkeys

# Adjust maxmemory policy if needed
docker exec nomos-valkey redis-cli config set maxmemory-policy allkeys-lru
```

## Emergency Procedures

### System Outage

**Immediate Response:**
1. Declare incident in Slack
2. Activate incident response team
3. Check monitoring dashboard
4. Verify component status

**Recovery Steps:**
1. Check infrastructure (VMs, containers, network)
2. Verify database availability
3. Check Vault status
4. Restart services in dependency order

**Communication:**
- Update status page
- Notify affected users
- Provide regular updates
- Post-mortem within 24 hours

### Security Incident

**Immediate Response:**
1. Isolate affected systems
2. Preserve logs and evidence
3. Activate security team
4. Rotate compromised credentials

**Containment:**
1. Identify attack vector
2. Block malicious IPs
3. Patch vulnerabilities
4. Restore from clean backups

**Post-Incident:**
- Full system audit
- Security improvements
- User notification (if PII affected)
- Regulatory reporting (if required)

### Data Corruption

**Immediate Response:**
1. Take database offline
2. Verify backup integrity
3. Identify corruption scope
4. Notify stakeholders

**Recovery:**
1. Restore from last known good backup
2. Replay transactions if possible
3. Verify data integrity
4. Bring systems back online

**Prevention:**
- Implement additional validation
- Enhance backup frequency
- Add data integrity checks

## Vault Management

### Vault Initialization

**First-Time Setup:**
```bash
# Run vault-init service
docker compose up vault-init

# Verify initialization
cat /vault/init/init-output.json
```

**Check Vault Status:**
```bash
vault status
vault operator unseal [unseal_key]
```

### Secret Management

**Add New Secret:**
```bash
vault kv put nomos/secrets/[category] key=value
```

**Read Secret:**
```bash
vault kv get nomos/secrets/[category]
```

**Rotate Secret:**
```bash
# Generate new secret
NEW_SECRET=$(openssl rand -base64 48)

# Update in Vault
vault kv put nomos/secrets/[category] key=${NEW_SECRET}

# Restart services using the secret
docker restart [service_name]
```

### AppRole Management

**Create New AppRole:**
```bash
vault write auth/approle/role/[role_name] \
  token_policies="[policy_name]" \
  token_ttl=1h \
  token_max_ttl=4h \
  secret_id_ttl=0
```

**Get AppRole Credentials:**
```bash
ROLE_ID=$(vault read -format=json auth/approle/role/[role_name]/role-id | jq -r '.data.role_id')
SECRET_ID=$(vault write -format=json -f auth/approle/role/[role_name]/secret-id | jq -r '.data.secret_id')
```

**Revoke AppRole:**
```bash
vault write auth/approle/role/[role_name]/secret-id/destroy secret_id=[secret_id]
```

### Vault Backup

**Snapshot Backup:**
```bash
vault operator raft snapshot save nomos-vault-$(date +%Y%m%d).snap
```

**Restore from Snapshot:**
```bash
vault operator raft snapshot restore nomos-vault-latest.snap
```

**Disaster Recovery:**
1. Initialize new Vault cluster
2. Restore from snapshot
3. Unseal with recovery keys
4. Verify all secrets intact
5. Update AppRole credentials

## Setup and Configuration

### First-Time Setup Wizard

**Access Wizard:**
1. Navigate to `http://localhost:3040/setup`
2. Follow 4-step process:
   - Step 1: Vault Unseal Key
   - Step 2: Admin Account + 2FA
   - Step 3: LLM Provider
   - Step 4: Complete

**Manual Setup (if wizard unavailable):**
```bash
# Get unseal key
curl -X GET "http://localhost:8060/system/unseal-key"

# Create admin
curl -X POST "http://localhost:8060/users/bootstrap" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "[strong_password]"}'

# Setup 2FA (optional)
curl -X POST "http://localhost:8060/auth/2fa/setup"

# Configure LLM provider
curl -X PATCH "http://localhost:8060/settings" \
  -H "Content-Type: application/json" \
  -d '{"nvidia_api_key": "[api_key]"}'
```

### Configuration Management

**Environment Variables:**
```bash
# Required variables
NOMOS_DB_PASSWORD=strong_password
VAULT_ADDR=http://vault:8200

# Optional monitoring variables
MONITORING_METRICS_RETENTION_DAYS=30
MONITORING_ALERT_CHECK_INTERVAL=60

# Notification settings
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=alerts@nomos.local
SMTP_PASSWORD=your-password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

**Configuration File:**
```yaml
# nomos-api/config.yaml
monitoring:
  metrics_retention_days: 30
  metrics_aggregation_interval: "5m"
  alert_check_interval: "1m"

notification:
  default_channels:
    - "email:admin@nomos.local"
    - "webhook:https://slack.com/alerts"

thresholds:
  api_error_rate: 0.05
  api_latency_p99: 500
  agent_stale_percentage: 0.15
```

### Alert Rule Management

**Create Alert Rule:**
```bash
curl -X POST "http://localhost:8060/api/monitoring/alert-rules" \
  -H "Content-Type: application/json" \
  -H "X-NomOS-API-Key: your-api-key" \
  -d '{
    "metric_name": "api.error_rate",
    "threshold_type": "above",
    "threshold_value": 0.05,
    "severity": "critical",
    "comparison_window": "5m",
    "notification_channels": {
      "email": ["admin@nomos.local"],
      "webhook": ["https://slack.com/alerts"]
    },
    "description": "High API error rate detected"
  }'
```

**List Alert Rules:**
```bash
curl -X GET "http://localhost:8060/api/monitoring/alert-rules" \
  -H "X-NomOS-API-Key: your-api-key"
```

**Delete Alert Rule:**
```bash
curl -X DELETE "http://localhost:8060/api/monitoring/alert-rules/[rule_id]" \
  -H "X-NomOS-API-Key: your-api-key"
```

### Notification Channel Management

**Test Notification:**
```bash
curl -X POST "http://localhost:8060/api/monitoring/alerts" \
  -H "Content-Type: application/json" \
  -H "X-NomOS-API-Key: your-api-key" \
  -d '{
    "severity": "info",
    "metric_name": "test.alert",
    "current_value": 1,
    "threshold_value": 0,
    "description": "Test notification",
    "notification_channels": {
      "email": ["test@nomos.local"],
      "webhook": ["https://slack.com/test"]
    }
  }'
```

**Update SMTP Configuration:**
```bash
# Update .env
SMTP_HOST=new-smtp.example.com
SMTP_PORT=587
SMTP_USER=new-user@nomos.local
SMTP_PASSWORD=new-password

# Restart API
docker restart nomos-api
```

## Monitoring and Metrics

### Key Metrics to Monitor

**API Performance:**
- Request volume and throughput
- Latency percentiles (P99, P95, P50)
- Error rates by endpoint
- Cache hit/miss ratios

**Agent Health:**
- Online/stale/offline counts
- Task success/failure rates
- Response times
- Resource usage

**System Health:**
- Database connection pool usage
- Valkey memory usage
- Vault sealed/unsealed status
- Gateway response times

**Compliance:**
- Incident response times
- DSGVO deadline tracking
- Budget usage per agent
- Approval queue metrics

### Dashboard Setup

**Main Dashboard:**
- System health score
- Critical alerts summary
- API performance overview
- Agent fleet status
- Resource usage trends

**API Performance Dashboard:**
- Latency heatmap by endpoint
- Error rate trends
- Throughput metrics
- Cache efficiency

**Agent Fleet Dashboard:**
- Online/stale/offline pie chart
- Response time distribution
- Task completion rates
- Resource usage by agent

**Compliance Dashboard:**
- Incident timeline
- DSGVO deadline tracking
- Budget usage by agent
- Approval queue metrics

### Metric Queries

**Get API Latency:**
```bash
curl -X GET "http://localhost:8060/api/monitoring/metrics?metric=api.latency&window=5m" \
  -H "X-NomOS-API-Key: your-api-key"
```

**Get Agent Status:**
```bash
curl -X GET "http://localhost:8060/api/monitoring/metrics?metric=agent.status" \
  -H "X-NomOS-API-Key: your-api-key"
```

**Get Error Rates:**
```bash
curl -X GET "http://localhost:8060/api/monitoring/metrics?metric=api.error_rate&dimensions[endpoint]=/api/agents" \
  -H "X-NomOS-API-Key: your-api-key"
```

## Troubleshooting Guide

### Common Issues and Solutions

**Issue: Alerts Not Triggering**

**Checklist:**
- [ ] Verify alert rule is active
- [ ] Check metric names match exactly
- [ ] Confirm thresholds are appropriate
- [ ] Review comparison windows
- [ ] Check alert processing job logs

**Solution:**
```bash
# Check alert rules
curl -X GET "http://localhost:8060/api/monitoring/alert-rules" \
  -H "X-NomOS-API-Key: your-api-key"

# Check current metrics
curl -X GET "http://localhost:8060/api/monitoring/metrics" \
  -H "X-NomOS-API-Key: your-api-key"

# Check worker logs
docker logs nomos-worker
```

**Issue: Notifications Not Sent**

**Checklist:**
- [ ] Verify notification channel configuration
- [ ] Check SMTP/webhook credentials
- [ ] Review notification service logs
- [ ] Test with manual alert creation

**Solution:**
```bash
# Test SMTP connection
swaks --to test@nomos.local --from alerts@nomos.local --server smtp.example.com --auth LOGIN --auth-user alerts@nomos.local

# Check notification logs
docker logs nomos-api | grep "NotificationService"

# Test webhook
curl -X POST "https://slack.com/alerts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test notification"}'
```

**Issue: High Metric Storage**

**Checklist:**
- [ ] Check metrics retention period
- [ ] Review aggregation windows
- [ ] Identify high-volume metrics
- [ ] Consider sampling strategy

**Solution:**
```bash
# Check current storage
SELECT COUNT(*) FROM metrics;

# Adjust retention (in .env)
MONITORING_METRICS_RETENTION_DAYS=14

# Restart API
docker restart nomos-api
```

**Issue: Vault Connection Problems**

**Checklist:**
- [ ] Verify Vault is running
- [ ] Check Vault status
- [ ] Verify AppRole credentials
- [ ] Check network connectivity

**Solution:**
```bash
# Check Vault status
vault status

# Check AppRole credentials
cat /vault/init/approle-creds.env

# Test Vault connection
vault kv get nomos/secrets/system

# Restart Vault
docker restart nomos-vault
```

**Issue: Setup Wizard Not Loading**

**Checklist:**
- [ ] Verify API is running
- [ ] Check system status endpoint
- [ ] Verify Vault is initialized
- [ ] Check console logs

**Solution:**
```bash
# Check system status
curl -X GET "http://localhost:8060/system/status"

# Check API logs
docker logs nomos-api

# Check console logs
docker logs nomos-console

# Restart services
docker restart nomos-api nomos-console
```

## Best Practices

### Alert Management

**Do:**
- Start with few critical alerts
- Tune thresholds based on real behavior
- Use appropriate severity levels
- Document runbooks for each alert
- Review alerts monthly

**Don't:**
- Create alerts for every metric
- Use overly sensitive thresholds
- Ignore alert fatigue
- Forget to document resolutions

### Metrics Collection

**Do:**
- Sample high-volume metrics
- Aggregate appropriately
- Implement retention policies
- Dimension wisely

**Don't:**
- Collect every request
- Store raw data indefinitely
- Add unnecessary dimensions
- Ignore storage costs

### Vault Management

**Do:**
- Regularly rotate secrets
- Backup Vault snapshots
- Monitor audit logs
- Test disaster recovery

**Don't:**
- Store secrets in code
- Share root tokens
- Ignore security alerts
- Skip backups

### System Maintenance

**Do:**
- Schedule regular maintenance
- Test changes in staging
- Have rollback plans
- Monitor after changes

**Don't:**
- Make changes without testing
- Ignore warning signs
- Skip documentation
- Forget to communicate

## Conclusion

These operational runbooks provide comprehensive guidance for managing the enhanced NomOS monitoring and infrastructure hardening features. Follow these procedures to ensure system reliability, security, and optimal performance.