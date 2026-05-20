# NomOS Monitoring and Infrastructure Hardening - Troubleshooting Guide

## Table of Contents

1. [Common Issues](#common-issues)
2. [Alerting System](#alerting-system)
3. [Metrics Collection](#metrics-collection)
4. [Vault Integration](#vault-integration)
5. [Setup Wizard](#setup-wizard)
6. [Performance Issues](#performance-issues)
7. [Logging and Monitoring](#logging-and-monitoring)
8. [Advanced Troubleshooting](#advanced-troubleshooting)

## Common Issues

### Alerts Not Triggering

**Symptoms:**
- Alert conditions are met but no alerts are created
- Monitoring dashboard shows breached thresholds but no alerts
- Alert processing job runs but no new alerts appear

**Root Causes:**
1. Alert rule is inactive or misconfigured
2. Metric names don't match between rules and collected data
3. Threshold values are inappropriate
4. Comparison windows are incorrect
5. Alert processing job is failing

**Diagnosis Steps:**
```bash
# 1. Check alert rules configuration
curl -X GET "http://localhost:8060/api/monitoring/alert-rules" \
  -H "X-NomOS-API-Key: your-api-key"

# 2. Verify current metrics
curl -X GET "http://localhost:8060/api/monitoring/metrics" \
  -H "X-NomOS-API-Key: your-api-key"

# 3. Check alert processing job logs
docker logs nomos-worker | grep -i alert

# 4. Verify alert rule status
SELECT id, metric_name, threshold_type, threshold_value, is_active 
FROM alert_rules;
```

**Solutions:**
1. **Activate alert rule:**
   ```bash
   # Update rule to set is_active=true
   curl -X PATCH "http://localhost:8060/api/monitoring/alert-rules/[rule_id]" \
     -H "Content-Type: application/json" \
     -H "X-NomOS-API-Key: your-api-key" \
     -d '{"is_active": true}'
   ```

2. **Fix metric name mismatch:**
   ```bash
   # Check exact metric names in database
   SELECT DISTINCT metric_name FROM metrics;
   
   # Update rule with correct metric name
   curl -X PATCH "http://localhost:8060/api/monitoring/alert-rules/[rule_id]" \
     -H "Content-Type: application/json" \
     -H "X-NomOS-API-Key: your-api-key" \
     -d '{"metric_name": "correct_metric_name"}'
   ```

3. **Adjust thresholds:**
   ```bash
   # Get current metric values
   SELECT metric_name, AVG(value) as avg_value 
   FROM metrics 
   WHERE timestamp > NOW() - INTERVAL '1 hour'
   GROUP BY metric_name;
   
   # Update threshold to appropriate value
   curl -X PATCH "http://localhost:8060/api/monitoring/alert-rules/[rule_id]" \
     -H "Content-Type: application/json" \
     -H "X-NomOS-API-Key: your-api-key" \
     -d '{"threshold_value": 0.10}'
   ```

4. **Fix comparison window:**
   ```bash
   # Update comparison window
   curl -X PATCH "http://localhost:8060/api/monitoring/alert-rules/[rule_id]" \
     -H "Content-Type: application/json" \
     -H "X-NomOS-API-Key: your-api-key" \
     -d '{"comparison_window": "15m"}'
   ```

5. **Restart alert processing job:**
   ```bash
   # Restart worker container
docker restart nomos-worker
   
   # Check job execution
docker logs -f nomos-worker
   ```

### Notifications Not Sent

**Symptoms:**
- Alerts are triggered but no notifications received
- Notification status shows "failed" or "pending"
- Users report not receiving alert emails or webhooks

**Root Causes:**
1. Incorrect notification channel configuration
2. SMTP/webhook credentials invalid
3. Notification service errors
4. Network connectivity issues
5. Rate limiting by notification providers

**Diagnosis Steps:**
```bash
# 1. Check notification configuration
SELECT notification_channels FROM alert_rules WHERE id = [rule_id];

# 2. Test SMTP connection
swaks --to test@nomos.local --from alerts@nomos.local \
  --server smtp.example.com --auth LOGIN \
  --auth-user alerts@nomos.local

# 3. Check notification service logs
docker logs nomos-api | grep "NotificationService"

# 4. Test webhook endpoint
curl -X POST "https://slack.com/alerts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test notification"}'

# 5. Check alert notification status
SELECT notification_status, notification_channels 
FROM alerts WHERE id = [alert_id];
```

**Solutions:**
1. **Fix SMTP configuration:**
   ```bash
   # Update .env with correct SMTP settings
   SMTP_HOST=smtp.example.com
   SMTP_PORT=587
   SMTP_USER=alerts@nomos.local
   SMTP_PASSWORD=correct-password
   
   # Restart API
docker restart nomos-api
   ```

2. **Update webhook URL:**
   ```bash
   # Update alert rule with correct webhook
   curl -X PATCH "http://localhost:8060/api/monitoring/alert-rules/[rule_id]" \
     -H "Content-Type: application/json" \
     -H "X-NomOS-API-Key: your-api-key" \
     -d '{
       "notification_channels": {
         "webhook": ["https://hooks.slack.com/services/correct/webhook"]
       }
     }'
   ```

3. **Test notification service:**
   ```bash
   # Create test alert
   curl -X POST "http://localhost:8060/api/monitoring/alerts" \
     -H "Content-Type: application/json" \
     -H "X-NomOS-API-Key: your-api-key" \
     -d '{
       "severity": "info",
       "metric_name": "test.notification",
       "current_value": 1,
       "threshold_value": 0,
       "description": "Test notification",
       "notification_channels": {
         "email": ["test@nomos.local"],
         "webhook": ["https://slack.com/test"]
       }
     }'
   ```

4. **Check network connectivity:**
   ```bash
   # Test SMTP port connectivity
   telnet smtp.example.com 587
   
   # Test webhook URL connectivity
   curl -v "https://hooks.slack.com/services/..."
   ```

5. **Implement notification fallbacks:**
   ```yaml
   # Add multiple notification channels
   notification:
     default_channels:
       - "email:admin@nomos.local"
       - "email:backup@nomos.local"
       - "webhook:https://slack.com/primary"
       - "webhook:https://slack.com/backup"
   ```

### High Metric Storage Usage

**Symptoms:**
- Database growing rapidly
- Slow metric queries
- High disk usage alerts
- Performance degradation

**Root Causes:**
1. Metrics retention period too long
2. High-volume metrics collected too frequently
3. Insufficient aggregation
4. Unnecessary dimensions
5. No data archiving strategy

**Diagnosis Steps:**
```bash
# 1. Check current storage usage
SELECT COUNT(*) as total_metrics FROM metrics;
SELECT pg_size_pretty(pg_total_relation_size('metrics')) as metrics_size;

# 2. Identify high-volume metrics
SELECT metric_name, COUNT(*) as count 
FROM metrics 
GROUP BY metric_name 
ORDER BY count DESC 
LIMIT 10;

# 3. Check retention settings
SELECT metrics_retention_days FROM system_settings;

# 4. Analyze metric growth
SELECT 
  DATE_TRUNC('day', timestamp) as day,
  COUNT(*) as count
FROM metrics 
GROUP BY day 
ORDER BY day DESC 
LIMIT 30;
```

**Solutions:**
1. **Reduce retention period:**
   ```bash
   # Update .env
   MONITORING_METRICS_RETENTION_DAYS=14
   
   # Restart API
docker restart nomos-api
   
   # Clean up old metrics
   DELETE FROM metrics WHERE timestamp < NOW() - INTERVAL '14 days';
   ```

2. **Increase aggregation windows:**
   ```yaml
   # Update configuration
   monitoring:
     metrics_aggregation_interval: "15m"
   ```

3. **Sample high-volume metrics:**
   ```python
   # Update metrics collection to sample
   def should_sample_metric(metric_name):
       high_volume_metrics = ['api.request_count', 'agent.heartbeat']
       if metric_name in high_volume_metrics:
           return random.random() < 0.1  # Sample 10%
       return True
   ```

4. **Archive old metrics:**
   ```bash
   # Export old metrics
   pg_dump -t metrics -w -Fc nomos > metrics_archive_$(date +%Y%m%d).dump
   
   # Delete archived data
   DELETE FROM metrics WHERE timestamp < NOW() - INTERVAL '6 months';
   
   # Store archive in cold storage
   aws s3 cp metrics_archive_*.dump s3://nomos-backups/metrics/
   ```

5. **Optimize indexing:**
   ```sql
   # Add additional indexes
   CREATE INDEX idx_metrics_timestamp_name ON metrics(timestamp, metric_name);
   CREATE INDEX idx_metrics_day ON metrics(DATE_TRUNC('day', timestamp));
   
   # Analyze tables
   ANALYZE metrics;
   ```

## Alerting System

### False Positive Alerts

**Symptoms:**
- Alerts triggering when no real issue exists
- Multiple alerts for same non-issue
- Alert fatigue among operators

**Root Causes:**
1. Thresholds set too sensitive
2. Inappropriate comparison windows
3. Metric calculation errors
4. Temporary spikes triggering alerts

**Solutions:**
1. **Adjust thresholds:**
   ```bash
   # Get baseline metrics
   SELECT 
     metric_name,
     AVG(value) as avg,
     STDDEV(value) as stddev,
     MAX(value) as max
   FROM metrics 
   WHERE timestamp > NOW() - INTERVAL '7 days'
   GROUP BY metric_name;
   
   # Set thresholds at 3 standard deviations
   curl -X PATCH "http://localhost:8060/api/monitoring/alert-rules/[rule_id]" \
     -H "Content-Type: application/json" \
     -H "X-NomOS-API-Key: your-api-key" \
     -d '{"threshold_value": [avg + 3*stddev]}'
   ```

2. **Increase comparison windows:**
   ```bash
   # Use longer windows to smooth temporary spikes
   curl -X PATCH "http://localhost:8060/api/monitoring/alert-rules/[rule_id]" \
     -H "Content-Type: application/json" \
     -H "X-NomOS-API-Key: your-api-key" \
     -d '{"comparison_window": "30m"}'
   ```

3. **Implement alert throttling:**
   ```python
   # Add cooldown period to alert processing
   def should_trigger_alert(rule, current_value):
       last_alert = get_last_alert_for_rule(rule.id)
       if last_alert and (now - last_alert.triggered_at) < rule.cooldown_period:
           return False
       return rule.should_trigger(current_value)
   ```

4. **Add confirmation requirements:**
   ```bash
   # Require multiple consecutive breaches
   curl -X PATCH "http://localhost:8060/api/monitoring/alert-rules/[rule_id]" \
     -H "Content-Type: application/json" \
     -H "X-NomOS-API-Key: your-api-key" \
     -d '{"required_consecutive_breaches": 3}'
   ```

### Alert Fatigue

**Symptoms:**
- Operators ignoring alerts
- Slow response times
- High volume of low-severity alerts

**Solutions:**
1. **Prioritize alerts:**
   ```bash
   # Review and adjust severity levels
   curl -X PATCH "http://localhost:8060/api/monitoring/alert-rules/[rule_id]" \
     -H "Content-Type: application/json" \
     -H "X-NomOS-API-Key: your-api-key" \
     -d '{"severity": "warning"}'  # Downgrade from critical
   ```

2. **Group related alerts:**
   ```python
   # Implement alert grouping
   def group_alerts(alerts):
       groups = {}
       for alert in alerts:
           key = f"{alert.metric_name}-{alert.dimensions}"
           if key not in groups:
               groups[key] = []
           groups[key].append(alert)
       return groups
   ```

3. **Implement maintenance windows:**
   ```bash
   # Add maintenance window configuration
   curl -X POST "http://localhost:8060/api/monitoring/maintenance-windows" \
     -H "Content-Type: application/json" \
     -H "X-NomOS-API-Key: your-api-key" \
     -d '{
       "start_time": "2026-04-20T02:00:00Z",
       "end_time": "2026-04-20T04:00:00Z",
       "description": "Weekly maintenance"
     }'
   ```

4. **Create alert suppression rules:**
   ```bash
   # Suppress alerts during known events
   curl -X POST "http://localhost:8060/api/monitoring/alert-suppressions" \
     -H "Content-Type: application/json" \
     -H "X-NomOS-API-Key: your-api-key" \
     -d '{
       "metric_pattern": "api.latency",
       "start_time": "2026-04-20T02:00:00Z",
       "end_time": "2026-04-20T04:00:00Z",
       "reason": "Scheduled maintenance"
     }'
   ```

## Metrics Collection

### Missing Metrics

**Symptoms:**
- Expected metrics not appearing in database
- Gaps in metric data
- Incomplete dashboard visualizations

**Diagnosis:**
```bash
# 1. Check metrics collection logs
docker logs nomos-api | grep "MetricsService"

# 2. Verify middleware is active
curl -X GET "http://localhost:8060/api/health" | grep middleware

# 3. Check for errors in metric recording
SELECT error_count, last_error 
FROM metrics_collection_status;

# 4. Verify metric dimensions
SELECT DISTINCT dimensions FROM metrics 
WHERE metric_name = 'missing_metric';
```

**Solutions:**
1. **Enable debug logging:**
   ```bash
   # Update logging configuration
   LOG_LEVEL=debug
   
   # Restart API
docker restart nomos-api
   
   # Check detailed logs
docker logs -f nomos-api | grep -i metric
   ```

2. **Verify middleware registration:**
   ```python
   # Check middleware is properly registered in main.py
   from nomos_api.middleware.metrics import MetricsMiddleware
   
   app.add_middleware(MetricsMiddleware)
   ```

3. **Fix metric recording errors:**
   ```bash
   # Check database constraints
   SELECT constraint_name, constraint_definition
   FROM information_schema.table_constraints
   WHERE table_name = 'metrics';
   
   # Fix data type mismatches
   ALTER TABLE metrics 
   ALTER COLUMN value TYPE FLOAT;
   ```

4. **Implement metric validation:**
   ```python
   # Add validation before recording
   def validate_metric(metric_name, value, dimensions):
       if not metric_name or not isinstance(metric_name, str):
           raise ValueError("Invalid metric name")
       if not isinstance(value, (int, float)):
           raise ValueError("Metric value must be numeric")
       if not isinstance(dimensions, dict):
           raise ValueError("Dimensions must be a dictionary")
   ```

### Metric Calculation Errors

**Symptoms:**
- Incorrect metric values
- Impossible values (negative, NaN)
- Inconsistent aggregations

**Diagnosis:**
```bash
# 1. Check raw metric data
SELECT * FROM metrics 
WHERE metric_name = 'problem_metric' 
ORDER BY timestamp DESC 
LIMIT 10;

# 2. Verify aggregation queries
SELECT 
  metric_name,
  AVG(value) as avg,
  MAX(value) as max,
  MIN(value) as min
FROM metrics 
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY metric_name;

# 3. Check for data type issues
SELECT value, pg_typeof(value) 
FROM metrics 
WHERE metric_name = 'problem_metric';
```

**Solutions:**
1. **Fix aggregation functions:**
   ```python
   # Correct aggregation logic
   def get_current_value(metric_name, window):
       query = """
       SELECT 
         AVG(value) as avg_value,
         MAX(value) as max_value,
         MIN(value) as min_value
       FROM metrics
       WHERE metric_name = :metric_name
       AND timestamp > NOW() - :window::INTERVAL
       """
       return execute_query(query, metric_name=metric_name, window=window)
   ```

2. **Handle edge cases:**
   ```python
   # Add null/NaN handling
   def safe_aggregate(values):
       cleaned = [v for v in values if v is not None and not math.isnan(v)]
       return sum(cleaned) / len(cleaned) if cleaned else 0
   ```

3. **Fix data type issues:**
   ```sql
   # Convert problematic values
   UPDATE metrics 
   SET value = 0 
   WHERE value IS NULL OR value = 'NaN';
   
   # Add constraints
   ALTER TABLE metrics 
   ADD CONSTRAINT positive_value CHECK (value >= 0);
   ```

4. **Implement data validation:**
   ```python
   # Validate before insertion
   def validate_value(value):
       if value is None:
           return 0
       if isinstance(value, str):
           try:
               return float(value)
           except ValueError:
               return 0
       if math.isnan(value):
           return 0
       return max(0, float(value))
   ```

## Vault Integration

### Vault Connection Issues

**Symptoms:**
- API fails to start
- Secrets not loaded
- Vault-related errors in logs
- "Vault unavailable" health status

**Diagnosis:**
```bash
# 1. Check Vault status
vault status

# 2. Verify Vault container
docker ps | grep vault
docker logs nomos-vault

# 3. Check API Vault client logs
docker logs nomos-api | grep -i vault

# 4. Test Vault connectivity
curl -v http://vault:8200/v1/sys/health

# 5. Check AppRole credentials
cat /vault/init/approle-creds.env
```

**Solutions:**
1. **Restart Vault:**
   ```bash
   # Restart Vault container
docker restart nomos-vault
   
   # Check status
   vault status
   ```

2. **Reinitialize Vault:**
   ```bash
   # Remove old initialization
   rm -rf /vault/file/*
   rm -rf /vault/init/*
   
   # Re-run init container
docker compose up vault-init
   
   # Restart API
docker restart nomos-api
   ```

3. **Fix AppRole credentials:**
   ```bash
   # Get new AppRole credentials
   ROLE_ID=$(vault read -format=json auth/approle/role/nomos-api/role-id | jq -r '.data.role_id')
   SECRET_ID=$(vault write -format=json -f auth/approle/role/nomos-api/secret-id | jq -r '.data.secret_id')
   
   # Update credentials file
   echo "VAULT_ROLE_ID=${ROLE_ID}" > /vault/init/approle-creds.env
   echo "VAULT_SECRET_ID=${SECRET_ID}" >> /vault/init/approle-creds.env
   
   # Restart API
docker restart nomos-api
   ```

4. **Check network connectivity:**
   ```bash
   # Test connection from API container
docker exec nomos-api ping vault
   docker exec nomos-api telnet vault 8200
   
   # Check DNS resolution
docker exec nomos-api cat /etc/hosts
   ```

### Vault Sealed

**Symptoms:**
- Vault status shows "sealed"
- Secrets cannot be accessed
- API fails with "Vault sealed" errors

**Diagnosis:**
```bash
# 1. Check Vault seal status
vault status | grep sealed

# 2. Check unseal keys
cat /vault/file/init-output.json

# 3. Check auto-unseal configuration
grep auto_unseal /vault/file/init-output.json
```

**Solutions:**
1. **Manual unseal:**
   ```bash
   # Get unseal key
   UNSEAL_KEY=$(jq -r '.unseal_keys_b64[0]' /vault/file/init-output.json)
   
   # Unseal Vault
   vault operator unseal ${UNSEAL_KEY}
   
   # Verify status
   vault status
   ```

2. **Enable auto-unseal:**
   ```bash
   # Reinitialize with auto-unseal
   vault operator init -key-shares=1 -key-threshold=1 -format=json > /vault/file/init-output.json
   
   # Update configuration
   echo '{"auto_unseal": true}' > /vault/file/config.json
   
   # Restart Vault
docker restart nomos-vault
   ```

3. **Check init container:**
   ```bash
   # Verify init container completed
   docker logs vault-init
   
   # Check for initialization file
   ls -la /vault/file/init-output.json
   
   # Re-run init container if needed
docker restart vault-init
   ```

4. **Recover from backup:**
   ```bash
   # Restore from snapshot
   vault operator raft snapshot restore nomos-vault-latest.snap
   
   # Unseal
   vault operator unseal [unseal_key]
   
   # Restart services
docker restart nomos-vault nomos-api
   ```

### Missing Secrets

**Symptoms:**
- API fails to start with "secret not found"
- Missing configuration values
- Services unable to authenticate

**Diagnosis:**
```bash
# 1. Check Vault secrets
vault kv list nomos/secrets/

# 2. Verify specific secrets
vault kv get nomos/secrets/system
vault kv get nomos/secrets/database

# 3. Check init container logs
docker logs vault-init | grep "Generating system secrets"

# 4. Verify initialization marker
ls -la /vault/init/initialized
```

**Solutions:**
1. **Regenerate secrets:**
   ```bash
   # Generate new secrets
   JWT_SECRET=$(openssl rand -base64 48)
   PLUGIN_API_KEY="npk-$(openssl rand -hex 24)"
   GATEWAY_TOKEN="gw-$(openssl rand -hex 24)"
   
   # Store in Vault
   vault kv put nomos/secrets/system \
     jwt_secret="${JWT_SECRET}" \
     plugin_api_key="${PLUGIN_API_KEY}" \
     gateway_token="${GATEWAY_TOKEN}"
   
   vault kv put nomos/secrets/database \
     password="${NOMOS_DB_PASSWORD:-changeme}"
   
   # Restart services
docker restart nomos-api nomos-worker
   ```

2. **Re-run init container:**
   ```bash
   # Remove initialization marker
   rm -f /vault/init/initialized
   
   # Re-run init container
docker restart vault-init
   
   # Verify secrets
   vault kv get nomos/secrets/system
   ```

3. **Check secret files:**
   ```bash
   # Verify secret files exist
   ls -la /vault/init/gateway-token
   ls -la /vault/init/plugin-api-key
   
   # Check permissions
   chmod 644 /vault/init/gateway-token
   chmod 644 /vault/init/plugin-api-key
   
   # Restart gateway
docker restart nomos-gateway
   ```

4. **Recover from backup:**
   ```bash
   # Restore secrets from backup
   vault kv put nomos/secrets/system @secrets-backup.json
   
   # Verify
   vault kv get nomos/secrets/system
   
   # Restart services
docker restart nomos-api nomos-worker nomos-gateway
   ```

## Setup Wizard

### Wizard Not Loading

**Symptoms:**
- Blank page at `/setup`
- "Setup required" but wizard unavailable
- JavaScript errors in console

**Diagnosis:**
```bash
# 1. Check system status
curl -X GET "http://localhost:8060/system/status"

# 2. Verify API response
curl -X GET "http://localhost:8060/system/unseal-key"

# 3. Check console logs
docker logs nomos-console

# 4. Check browser console for errors
# (F12 > Console tab)
```

**Solutions:**
1. **Check API availability:**
   ```bash
   # Verify API is running
   docker ps | grep nomos-api
   
   # Check API logs
docker logs nomos-api
   
   # Restart API
docker restart nomos-api
   ```

2. **Verify system status:**
   ```bash
   # Check if setup is actually required
   curl -X GET "http://localhost:8060/system/status"
   
   # If not required, should redirect to login
   # If required, should show wizard
   ```

3. **Check console configuration:**
   ```bash
   # Verify console environment variables
   docker inspect nomos-console | grep NOMOS_API_URL
   
   # Update if needed
   NOMOS_API_URL=http://nomos-api:8060
   
   # Restart console
docker restart nomos-console
   ```

4. **Clear browser cache:**
   ```
   # Chrome: Settings > Privacy > Clear browsing data
   # Firefox: Options > Privacy & Security > Clear Data
   # Safari: Safari > Clear History
   
   # Hard refresh: Ctrl+F5 or Cmd+Shift+R
   ```

### Step 1: Vault Unseal Key Issues

**Symptoms:**
- Unseal key not displayed
- "Failed to fetch unseal key" error
- Auto-unseal not working

**Diagnosis:**
```bash
# 1. Check unseal key endpoint
curl -X GET "http://localhost:8060/system/unseal-key"

# 2. Verify Vault initialization
ls -la /vault/file/init-output.json

# 3. Check Vault status
vault status

# 4. Verify init container completed
cat /vault/init/initialized
```

**Solutions:**
1. **Re-run init container:**
   ```bash
   # Remove initialization marker
   rm -f /vault/init/initialized
   
   # Re-run init container
docker restart vault-init
   
   # Verify unseal key
   curl -X GET "http://localhost:8060/system/unseal-key"
   ```

2. **Manual unseal:**
   ```bash
   # Get unseal key
   UNSEAL_KEY=$(jq -r '.unseal_keys_b64[0]' /vault/file/init-output.json)
   
   # Unseal Vault
   vault operator unseal ${UNSEAL_KEY}
   
   # Restart API
docker restart nomos-api
   
   # Retry wizard
   ```

3. **Check API endpoint:**
   ```python
   # Verify endpoint implementation
   @router.get("/system/unseal-key")
   async def get_unseal_key():
       try:
           with open("/vault/file/init-output.json") as f:
               data = json.load(f)
           return {
               "unseal_key": data["unseal_keys_b64"][0],
               "auto_unseal": os.path.exists("/vault/file/config.json")
           }
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))
   ```

4. **Enable auto-unseal:**
   ```bash
   # Configure auto-unseal
   echo '{"auto_unseal": true}' > /vault/file/config.json
   
   # Restart Vault
docker restart nomos-vault
   
   # Refresh wizard
   ```

### Step 2: Admin Creation Issues

**Symptoms:**
- "Failed to create admin" error
- Password validation errors
- Recovery key not displayed

**Diagnosis:**
```bash
# 1. Check bootstrap endpoint
curl -X POST "http://localhost:8060/users/bootstrap" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@nomos.local", "password": "Test1234!"}'

# 2. Check password validation
# Password must be 12+ chars with upper, lower, digit, special

# 3. Verify database connectivity
curl -X GET "http://localhost:8060/api/health"

# 4. Check API logs
docker logs nomos-api | grep "bootstrap"
```

**Solutions:**
1. **Fix password requirements:**
   ```
   # Use strong password:
   - Minimum 12 characters
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one digit
   - At least one special character
   
   # Example: MySecurePass123!
   ```

2. **Check database connection:**
   ```bash
   # Test database connectivity
   docker exec nomos-api psql -U nomos -c "SELECT 1"
   
   # Restart database if needed
docker restart nomos-postgres
   
   # Re-run bootstrap
   ```

3. **Verify email format:**
   ```
   # Use valid email format
   # Example: admin@nomos.local
   
   # Check validation
   if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
       raise ValueError("Invalid email format")
   ```

4. **Check for existing admin:**
   ```bash
   # Check if admin already exists
   SELECT * FROM users WHERE is_admin = true;
   
   # If exists, use login instead of bootstrap
   # Or delete existing admin (careful!)
   DELETE FROM users WHERE is_admin = true;
   ```

### Step 3: LLM Provider Issues

**Symptoms:**
- Provider test fails
- API key validation errors
- Connection refused errors

**Diagnosis:**
```bash
# 1. Check provider status endpoint
curl -X GET "http://localhost:8060/proxy/status"

# 2. Verify API key format
# NVIDIA: nvapi-...
# OpenAI: sk-...
# Anthropic: sk-ant-api03-...

# 3. Test provider directly
curl https://api.nvidia.com/v1/models \
  -H "Authorization: Bearer [api_key]"

# 4. Check gateway logs
docker logs nomos-gateway
```

**Solutions:**
1. **Verify API key:**
   ```
   # Check key format matches provider:
   # NVIDIA: nvapi- + 36 chars
   # OpenAI: sk- + 48 chars
   # Anthropic: sk-ant-api03- + 32 chars
   
   # Regenerate key if needed
   ```

2. **Check network connectivity:**
   ```bash
   # Test connection to provider
   curl -v https://api.nvidia.com
   
   # Check DNS resolution
   nslookup api.nvidia.com
   
   # Check firewall rules
   ```

3. **Verify gateway configuration:**
   ```bash
   # Check gateway environment variables
   docker inspect nomos-gateway | grep NVIDIA_API_KEY
   
   # Update if needed
   NVIDIA_API_KEY=[correct_key]
   
   # Restart gateway
docker restart nomos-gateway
   ```

4. **Test with different provider:**
   ```
   # Try OpenAI as fallback
   curl -X PATCH "http://localhost:8060/settings" \
     -H "Content-Type: application/json" \
     -d '{"openai_api_key": "[openai_key]"}'
   
   # Test OpenAI
   curl -X GET "http://localhost:8060/proxy/status?provider=openai"
   ```

## Performance Issues

### High API Latency

**Symptoms:**
- Slow API responses
- High P99 latency
- Timeout errors

**Diagnosis:**
```bash
# 1. Check current latency metrics
curl -X GET "http://localhost:8060/api/monitoring/metrics?metric=api.latency"

# 2. Identify slow endpoints
SELECT 
  dimensions->>'endpoint' as endpoint,
  AVG(value) as avg_latency,
  MAX(value) as max_latency
FROM metrics 
WHERE metric_name = 'api.latency'
GROUP BY endpoint 
ORDER BY avg_latency DESC;

# 3. Check database query performance
SELECT 
  query,
  total_time,
  calls,
  mean_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

# 4. Check cache hit ratios
SELECT 
  metric_name,
  AVG(value) as ratio
FROM metrics 
WHERE metric_name LIKE 'cache.%'
GROUP BY metric_name;
```

**Solutions:**
1. **Optimize database queries:**
   ```sql
   # Add missing indexes
   CREATE INDEX idx_users_email ON users(email);
   
   # Analyze query plans
   EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@nomos.local';
   
   # Optimize slow queries
   ```

2. **Improve caching:**
   ```bash
   # Increase cache TTL
   CACHE_TTL=300  # 5 minutes
   
   # Add cache for slow endpoints
   @cache(ttl=300)
   async def get_slow_data():
       # ...
   ```

3. **Scale horizontally:**
   ```yaml
   # Add more API replicas
   nomos-api:
     deploy:
       replicas: 3
   
   # Update docker-compose.yml
   # Restart services
   docker stack deploy -c docker-compose.yml nomos
   ```

4. **Implement rate limiting:**
   ```python
   # Add rate limiting middleware
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   
   @app.get("/api/slow-endpoint")
   @limiter.limit("10/minute")
   async def slow_endpoint():
       # ...
   ```

### High Error Rates

**Symptoms:**
- Increased 4xx/5xx errors
- Failed requests
- User reports of errors

**Diagnosis:**
```bash
# 1. Check error rate metrics
curl -X GET "http://localhost:8060/api/monitoring/metrics?metric=api.error_rate"

# 2. Identify error sources
SELECT 
  dimensions->>'endpoint' as endpoint,
  dimensions->>'status_code' as status,
  COUNT(*) as count
FROM metrics 
WHERE metric_name = 'api.errors'
GROUP BY endpoint, status 
ORDER BY count DESC;

# 3. Check recent errors
SELECT 
  timestamp,
  dimensions->>'endpoint' as endpoint,
  dimensions->>'error_type' as error
FROM metrics 
WHERE metric_name = 'api.errors'
ORDER BY timestamp DESC 
LIMIT 50;

# 4. Review API logs
docker logs nomos-api | grep -i error
```

**Solutions:**
1. **Fix common errors:**
   ```bash
   # Check for specific error patterns
   docker logs nomos-api | grep "404" | head -20
   docker logs nomos-api | grep "500" | head -20
   
   # Fix missing routes, validation errors, etc.
   ```

2. **Improve error handling:**
   ```python
   # Add specific error handlers
   @app.exception_handler(RequestValidationError)
   async def validation_exception_handler(request, exc):
       return JSONResponse(
           status_code=422,
           content={"detail": exc.errors()},
       )
   ```

3. **Add input validation:**
   ```python
   # Use Pydantic models for validation
   class UserCreate(BaseModel):
       email: EmailStr
       password: str = Field(min_length=12, max_length=72)
       
       @validator('password')
       def password_complexity(cls, v):
           if not re.search(r'[A-Z]', v):
               raise ValueError('Password must contain uppercase letter')
           # ... other checks
           return v
   ```

4. **Implement circuit breakers:**
   ```python
   # Add circuit breaker for external services
   from pybreaker import CircuitBreaker
   
   breaker = CircuitBreaker(fail_max=3, reset_timeout=60)
   
   @breaker
   def call_external_service():
       # ...
   ```

### Agent Performance Issues

**Symptoms:**
- Slow agent responses
- High agent error rates
- Agents going stale

**Diagnosis:**
```bash
# 1. Check agent metrics
curl -X GET "http://localhost:8060/api/monitoring/metrics?metric=agent.response_time"

# 2. Identify problematic agents
SELECT 
  dimensions->>'agent_id' as agent,
  AVG(value) as avg_response_time,
  COUNT(*) as request_count
FROM metrics 
WHERE metric_name = 'agent.response_time'
GROUP BY agent 
ORDER BY avg_response_time DESC;

# 3. Check agent error rates
SELECT 
  dimensions->>'agent_id' as agent,
  SUM(CASE WHEN dimensions->>'status' = 'error' THEN 1 ELSE 0 END) as errors,
  COUNT(*) as total
FROM metrics 
WHERE metric_name = 'agent.tasks'
GROUP BY agent;

# 4. Check agent logs
# (Requires access to agent containers)
```

**Solutions:**
1. **Restart problematic agents:**
   ```bash
   # Identify agent containers
   docker ps | grep agent
   
   # Restart specific agent
   docker restart [agent_container]
   ```

2. **Scale agent fleet:**
   ```yaml
   # Add more agents
   nomos-agent:
     deploy:
       replicas: 5
   
   # Update and redeploy
   docker stack deploy -c docker-compose.yml nomos
   ```

3. **Optimize agent workload:**
   ```bash
   # Redistribute tasks
   # Implement task queues
   # Add task prioritization
   ```

4. **Improve agent monitoring:**
   ```python
   # Add more detailed agent metrics
   def record_agent_metrics(agent_id, task):
       record_metric(
           'agent.task_duration',
           task.duration,
           {'agent_id': agent_id, 'task_type': task.type}
       )
       record_metric(
           'agent.memory_usage',
           task.memory_used,
           {'agent_id': agent_id}
       )
   ```

## Logging and Monitoring

### Logs Not Appearing

**Symptoms:**
- Missing log entries
- Incomplete log files
- No logs for specific events

**Diagnosis:**
```bash
# 1. Check log configuration
cat nomos-api/logging.conf

# 2. Verify log levels
LOG_LEVEL=info

# 3. Check log file permissions
ls -la /var/log/nomos/

# 4. Test logging
curl -X GET "http://localhost:8060/api/health"
docker logs nomos-api | tail -20
```

**Solutions:**
1. **Fix log configuration:**
   ```python
   # Verify logging setup
   import logging
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s %(levelname)s %(message)s',
       handlers=[
           logging.FileHandler('/var/log/nomos/api.log'),
           logging.StreamHandler()
       ]
   )
   ```

2. **Check log rotation:**
   ```bash
   # Verify logrotate configuration
   cat /etc/logrotate.d/nomos
   
   # Test log rotation
   logrotate -f /etc/logrotate.d/nomos
   ```

3. **Increase log level:**
   ```bash
   # Set to debug for more details
   LOG_LEVEL=debug
   
   # Restart API
docker restart nomos-api
   
   # Check debug logs
docker logs -f nomos-api
   ```

4. **Check log permissions:**
   ```bash
   # Fix permissions
   chown nomos:nomos /var/log/nomos/
   chmod 755 /var/log/nomos/
   chmod 644 /var/log/nomos/*.log
   
   # Restart API
docker restart nomos-api
   ```

### Metrics Not Updating

**Symptoms:**
- Stale metric values
- No new metric data
- Dashboard showing old data

**Diagnosis:**
```bash
# 1. Check metric collection
SELECT MAX(timestamp) FROM metrics;

# 2. Verify middleware is active
curl -X GET "http://localhost:8060/api/health" | grep middleware

# 3. Check for collection errors
SELECT error_count FROM metrics_collection_status;

# 4. Test manual metric recording
curl -X POST "http://localhost:8060/api/monitoring/metrics" \
  -H "Content-Type: application/json" \
  -d '{"metric_name": "test.metric", "value": 1.0}'
```

**Solutions:**
1. **Restart metrics collection:**
   ```bash
   # Restart API to reset middleware
docker restart nomos-api
   
   # Check new metrics
   SELECT * FROM metrics WHERE metric_name = 'api.request_count'
   ORDER BY timestamp DESC LIMIT 5;
   ```

2. **Fix middleware registration:**
   ```python
   # Ensure middleware is registered
   from nomos_api.middleware.metrics import MetricsMiddleware
   
   app.add_middleware(MetricsMiddleware)
   
   # Verify in main.py
   ```

3. **Check database connectivity:**
   ```bash
   # Test database connection
   docker exec nomos-api psql -U nomos -c "SELECT 1"
   
   # Check for connection pool issues
   SELECT count(*) FROM pg_stat_activity WHERE datname = 'nomos';
   ```

4. **Implement metric validation:**
   ```python
   # Add validation before recording
   def record_metric(metric_name, value, dimensions):
       try:
           # Validate inputs
           if not metric_name:
               raise ValueError("Metric name required")
           
           # Insert into database
           # ...
           
           return True
       except Exception as e:
           logger.error(f"Failed to record metric {metric_name}: {e}")
           return False
   ```

## Advanced Troubleshooting

### Database Performance Analysis

**Tools:**
```bash
# 1. Check slow queries
SELECT query, total_time, calls, mean_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

# 2. Analyze query plans
EXPLAIN ANALYZE SELECT * FROM metrics WHERE timestamp > NOW() - INTERVAL '1 hour';

# 3. Check index usage
SELECT schemaname, relname, indexrelname, idx_scan
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

# 4. Monitor locks
SELECT locktype, relation::regclass, mode, granted
FROM pg_locks 
WHERE NOT granted;
```

**Optimizations:**
```sql
# 1. Add missing indexes
CREATE INDEX idx_metrics_timestamp_name ON metrics(timestamp, metric_name);

# 2. Partition large tables
CREATE TABLE metrics (
    LIKE metrics INCLUDING DEFAULTS
) PARTITION BY RANGE (timestamp);

# 3. Optimize queries
SELECT metric_name, AVG(value)
FROM metrics 
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY metric_name;

# 4. Add materialized views
CREATE MATERIALIZED VIEW hourly_metrics AS
SELECT 
  DATE_TRUNC('hour', timestamp) as hour,
  metric_name,
  AVG(value) as avg_value
FROM metrics 
GROUP BY hour, metric_name;
```

### Network Connectivity Issues

**Diagnosis:**
```bash
# 1. Check container networking
docker network inspect nomos_default

# 2. Test DNS resolution
docker exec nomos-api cat /etc/resolv.conf
docker exec nomos-api nslookup nomos-postgres

# 3. Test port connectivity
docker exec nomos-api telnet nomos-postgres 5432
docker exec nomos-api nc -zv nomos-postgres 5432

# 4. Check firewall rules
iptables -L -n
```

**Solutions:**
```bash
# 1. Restart Docker network
docker network disconnect nomos_default nomos-api
docker network connect nomos_default nomos-api

# 2. Fix DNS configuration
# Update /etc/docker/daemon.json
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}

# 3. Check service discovery
# Verify container names match service names
docker ps --format "{{.Names}}"

# 4. Test with direct IPs
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' nomos-postgres
```

### Memory Leaks

**Diagnosis:**
```bash
# 1. Monitor memory usage
docker stats --no-stream nomos-api

# 2. Check Python memory
pip install memory-profiler
docker exec nomos-api python -m memory_profiler app.py

# 3. Analyze heap
pip install objgraph
docker exec nomos-api python -c "import objgraph; objgraph.show_most_common_types()"

# 4. Check for growing data structures
# Look for unbounded lists, caches, etc.
```

**Solutions:**
```python
# 1. Implement proper cleanup
class MetricsCache:
    def __init__(self, max_size=1000):
        self.cache = {}
        self.max_size = max_size
    
    def add(self, key, value):
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            # Remove oldest entries
            oldest = min(self.cache.keys())
            del self.cache[oldest]

# 2. Use weak references
import weakref

class AgentRegistry:
    def __init__(self):
        self.agents = weakref.WeakValueDictionary()
    
    def register(self, agent_id, agent):
        self.agents[agent_id] = agent

# 3. Add garbage collection
import gc

def cleanup():
    gc.collect()
    # Additional cleanup

# 4. Profile memory usage
@profile
def process_large_dataset():
    # ...
```

### Deadlocks

**Diagnosis:**
```bash
# 1. Check for blocked processes
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid,
       blocked_activity.query AS blocked_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity 
  ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks 
  ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.DATABASE IS NOT DISTINCT FROM blocked_locks.DATABASE
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
  AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
  AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
  AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
  AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
  AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
  AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
  AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity 
  ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.GRANTED;

# 2. Check for long-running transactions
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity 
WHERE state = 'active'
ORDER BY duration DESC;

# 3. Monitor lock timeouts
SELECT count(*) 
FROM metrics 
WHERE metric_name = 'database.lock_timeout';
```

**Solutions:**
```python
# 1. Add timeout to database operations
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://nomos:password@postgres/nomos',
    connect_args={'connect_timeout': 5},
    pool_pre_ping=True
)

# 2. Implement retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def with_retry(func, *args, **kwargs):
    return func(*args, **kwargs)

# 3. Use shorter transactions
async def update_metrics():
    async with session.begin():
        # Do minimal work
        session.add(metric)
    # Don't hold transaction open

# 4. Add deadlock detection
try:
    # Database operation
    session.commit()
except DeadlockDetected:
    logger.warning("Deadlock detected, retrying...")
    session.rollback()
    time.sleep(random.uniform(0.1, 0.5))
    # Retry operation
```

## Conclusion

This comprehensive troubleshooting guide covers common issues with the NomOS monitoring and infrastructure hardening features. Use these diagnostic steps and solutions to quickly identify and resolve problems, ensuring system reliability and performance.