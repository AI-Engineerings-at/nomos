# NomOS Monitoring and Infrastructure Hardening - Best Practices

## Table of Contents

1. [Monitoring Best Practices](#monitoring-best-practices)
2. [Alerting Best Practices](#alerting-best-practices)
3. [Vault Management Best Practices](#vault-management-best-practices)
4. [Security Best Practices](#security-best-practices)
5. [Performance Best Practices](#performance-best-practices)
6. [Operational Best Practices](#operational-best-practices)
7. [Development Best Practices](#development-best-practices)
8. [Compliance Best Practices](#compliance-best-practices)

## Monitoring Best Practices

### Metric Collection

**Do:**
- **Collect meaningful metrics**: Focus on metrics that provide actionable insights
- **Use appropriate sampling**: For high-volume metrics, implement sampling (e.g., 10% of requests)
- **Aggregate wisely**: Use time windows that match your operational needs (5m, 15m, 1h)
- **Dimension strategically**: Only add dimensions that will be used for filtering and analysis
- **Implement retention policies**: Balance detail with storage costs (e.g., 30 days raw, 1 year aggregated)

**Don't:**
- Collect every possible metric without consideration
- Store raw data indefinitely
- Add unnecessary dimensions that increase cardinality
- Sample metrics that need precise counting

**Example Configuration:**
```yaml
monitoring:
  metrics_retention_days: 30
  raw_metrics_retention_days: 7
  aggregated_metrics_retention_days: 365
  sampling:
    api.request_count: 0.1  # 10%
    agent.heartbeat: 0.05  # 5%
```

### Dashboard Design

**Do:**
- **Overview first**: Show high-level health score and critical alerts on main dashboard
- **Provide drill-down**: Detailed views for troubleshooting specific issues
- **Show historical context**: Display trends, not just current values
- **Make actionable**: Include links to relevant tools and documentation
- **Use consistent time ranges**: Align with operational cycles (24h, 7d, 30d)

**Don't:**
- Overload dashboards with too many metrics
- Show raw data without context
- Use inconsistent time ranges
- Forget to add titles and descriptions

**Recommended Dashboard Structure:**
```
Overview Dashboard:
- System health score
- Critical alerts summary
- API performance overview
- Agent fleet status
- Resource usage trends

API Performance Dashboard:
- Latency heatmap by endpoint
- Error rate trends
- Throughput metrics
- Cache efficiency
- Slow query analysis

Agent Fleet Dashboard:
- Online/stale/offline pie chart
- Response time distribution
- Task completion rates
- Resource usage by agent
- Agent error analysis

Compliance Dashboard:
- Incident timeline
- DSGVO deadline tracking
- Budget usage by agent
- Approval queue metrics
- Audit trail summary
```

### Metric Naming Conventions

**Use consistent naming:**
- `api.latency` - API response latency
- `api.error_rate` - API error rate
- `agent.response_time` - Agent response time
- `agent.stale_percentage` - Percentage of stale agents
- `system.cpu_usage` - System CPU usage
- `system.memory_usage` - System memory usage

**Naming pattern:**
`<component>.<metric_type>.<specific_metric>`

**Examples:**
- `database.connection_pool_usage`
- `cache.hit_ratio`
- `vault.response_time`
- `gateway.online_status`

## Alerting Best Practices

### Alert Configuration

**Do:**
- **Start conservative**: Begin with few critical alerts and expand gradually
- **Tune thresholds**: Adjust based on real-world behavior and baselines
- **Use appropriate severity**: Critical for immediate action, Warning for potential issues
- **Document alerts**: Include runbooks and resolution procedures for each alert type
- **Review regularly**: Monthly review of alert effectiveness and relevance

**Don't:**
- Create alerts for every metric
- Use overly sensitive thresholds
- Ignore alert fatigue
- Forget to document resolution procedures

**Alert Severity Guidelines:**
```
Critical:
- System down or severely degraded
- Data loss or corruption
- Security incidents
- Compliance deadline breaches
- Immediate action required (within 5 minutes)

Warning:
- Performance degradation
- Approaching capacity limits
- Increased error rates
- Potential issues that need investigation
- Action required within 1 hour

Info:
- Informational messages
- Maintenance notifications
- System events
- No immediate action required
```

### Alert Thresholds

**Establish baselines first:**
```bash
# Get baseline metrics for 7 days
SELECT 
  metric_name,
  AVG(value) as avg,
  STDDEV(value) as stddev,
  MAX(value) as max,
  MIN(value) as min
FROM metrics 
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY metric_name;
```

**Set thresholds based on baselines:**
```yaml
alert_rules:
  - metric_name: api.latency
    threshold_type: above
    threshold_value: avg + 3*stddev  # 3 standard deviations above average
    severity: warning
    comparison_window: 5m
    required_consecutive_breaches: 3

  - metric_name: api.error_rate
    threshold_type: above
    threshold_value: 0.05  # 5%
    severity: critical
    comparison_window: 5m
```

### Alert Grouping and Throttling

**Implement alert grouping:**
```python
# Group related alerts to reduce noise
def group_alerts(alerts):
    groups = {}
    for alert in alerts:
        # Group by metric name and dimensions
        key = f"{alert.metric_name}-{frozenset(alert.dimensions.items())}"
        if key not in groups:
            groups[key] = []
        groups[key].append(alert)
    return groups
```

**Add throttling:**
```yaml
# Throttle alerts to prevent flooding
alert_throttling:
  max_alerts_per_minute: 10
  cooldown_period: 30m
  group_similar_alerts: true
  group_window: 5m
```

### Notification Strategies

**Multi-channel notifications:**
```yaml
notification:
  channels:
    - email:admin@nomos.local
    - email:backup@nomos.local
    - webhook:https://slack.com/primary
    - webhook:https://slack.com/backup
  
  escalation:
    critical:
      - immediate: [email, slack]
      - 5m_no_ack: [pagerduty]
      - 15m_no_resolve: [phone]
    
    warning:
      - immediate: [email, slack]
      - 30m_no_ack: [email_escalation]
```

**Fallback notifications:**
```python
# Implement notification fallbacks
def send_notification(alert, channels):
    primary_channels = channels[:2]  # First 2 channels
    fallback_channels = channels[2:]  # Remaining channels
    
    success = False
    for channel in primary_channels:
        if send_via_channel(alert, channel):
            success = True
            break
    
    if not success:
        for channel in fallback_channels:
            send_via_channel(alert, channel)
```

## Vault Management Best Practices

### Vault Initialization

**Do:**
- **Use proper key management**: For production, use KMS auto-unseal (AWS KMS, Azure Key Vault, GCP CKMS)
- **Store unseal keys securely**: Use hardware security modules or secure key management systems
- **Implement key rotation**: Regularly rotate unseal keys and root tokens
- **Document recovery procedures**: Ensure recovery keys are stored securely and accessible

**Don't:**
- Use single unseal key with threshold 1 in production
- Store unseal keys in plaintext files
- Share root tokens
- Ignore key rotation

**Production Initialization:**
```bash
# Production initialization with auto-unseal
vault operator init \
  -key-shares=5 \
  -key-threshold=3 \
  -recovery-shares=5 \
  -recovery-threshold=3 \
  -pgp-keys="keybase:user1,keybase:user2,keybase:user3"
```

### Secret Management

**Do:**
- **Use dynamic secrets**: Where possible, use Vault's dynamic secrets engines
- **Implement secret rotation**: Regularly rotate static secrets
- **Use fine-grained policies**: Apply principle of least privilege
- **Audit secret access**: Monitor and log all secret access
- **Backup secrets**: Regularly backup Vault data

**Don't:**
- Store secrets in code or configuration files
- Use long-lived static secrets
- Grant broad access to secrets
- Ignore audit logs

**Secret Rotation Policy:**
```yaml
secret_rotation:
  jwt_secret: 30d
  plugin_api_key: 90d
  gateway_token: 90d
  database_password: 180d
  
  rotation_procedure:
    - generate_new_secret
    - store_in_vault
    - update_services
    - verify_functionality
    - revoke_old_secret
```

### AppRole Best Practices

**Do:**
- **Use short TTLs**: Set appropriate token time-to-live values
- **Implement secret_id rotation**: Regularly rotate secret IDs
- **Use pull mode**: Have applications pull credentials rather than push
- **Monitor token usage**: Track which roles are being used
- **Revoke unused roles**: Clean up unused AppRoles

**Don't:**
- Use long-lived tokens
- Share role IDs and secret IDs
- Hardcode AppRole credentials
- Ignore token expiration

**AppRole Configuration:**
```hcl
# AppRole configuration with short TTL
path "auth/approle/role/nomos-api" {
  capabilities = ["create", "read", "update", "delete"]
}

# Role configuration
vault write auth/approle/role/nomos-api \
  token_policies="nomos-api" \
  token_ttl=1h \
  token_max_ttl=4h \
  secret_id_ttl=0 \
  secret_id_num_uses=0
```

### Vault Backup and Recovery

**Do:**
- **Regular snapshots**: Take frequent Vault snapshots
- **Test restores**: Regularly test recovery procedures
- **Store backups securely**: Use encrypted storage for backups
- **Document recovery**: Maintain up-to-date recovery documentation
- **Monitor backup health**: Verify backup integrity

**Don't:**
- Ignore backup testing
- Store backups in the same location
- Forget to document recovery steps
- Assume backups work without testing

**Backup Procedure:**
```bash
# Daily snapshot backup
vault operator raft snapshot save nomos-vault-$(date +%Y%m%d).snap

# Encrypt backup
gpg --encrypt --recipient security-team@nomos.local nomos-vault-*.snap

# Store in multiple locations
aws s3 cp nomos-vault-*.snap.gpg s3://nomos-backups/vault/
gsutil cp nomos-vault-*.snap.gpg gs://nomos-backups/vault/

# Verify backup
vault operator raft snapshot restore --verify nomos-vault-latest.snap
```

## Security Best Practices

### Authentication and Authorization

**Do:**
- **Enforce strong passwords**: Minimum 12 characters with complexity requirements
- **Implement 2FA**: Require two-factor authentication for all users
- **Use role-based access control**: Assign permissions based on roles
- **Regularly review access**: Audit user permissions and access patterns
- **Implement session timeout**: Set appropriate session expiration

**Don't:**
- Allow weak passwords
- Skip 2FA for administrative accounts
- Grant excessive permissions
- Ignore access reviews
- Use long-lived sessions

**Password Policy:**
```yaml
password:
  min_length: 12
  require_uppercase: true
  require_lowercase: true
  require_digit: true
  require_special: true
  max_age: 90d
  history: 5
  lockout_threshold: 5
  lockout_duration: 15m
```

### Network Security

**Do:**
- **Use TLS everywhere**: Enforce HTTPS for all communications
- **Implement network segmentation**: Separate components into different networks
- **Use firewalls**: Restrict access to only necessary ports
- **Monitor network traffic**: Detect anomalies and suspicious activity
- **Regularly update dependencies**: Keep all software up-to-date

**Don't:**
- Use plain HTTP
- Expose internal services to the internet
- Allow broad network access
- Ignore security updates
- Use outdated software

**Network Configuration:**
```yaml
network:
  tls:
    enabled: true
    min_version: TLS1.2
    cipher_suites: "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
  
  firewalls:
    api:
      allowed_ips: ["10.0.0.0/8", "192.168.0.0/16"]
      allowed_ports: [8060]
    
    database:
      allowed_ips: ["10.0.1.0/24"]
      allowed_ports: [5432]
```

### Data Protection

**Do:**
- **Encrypt sensitive data**: At rest and in transit
- **Implement data masking**: For PII and sensitive information
- **Regularly audit data access**: Monitor who accesses what data
- **Implement data retention policies**: Don't keep data longer than necessary
- **Anonymize data**: For analytics and testing

**Don't:**
- Store sensitive data in plaintext
- Log PII or sensitive information
- Keep data indefinitely
- Share sensitive data unnecessarily
- Ignore data protection regulations

**Data Encryption:**
```yaml
data_protection:
  encryption:
    at_rest: AES-256
    in_transit: TLS1.2+
    key_rotation: 90d
  
  masking:
    enabled: true
    patterns:
      - "\d{4}-\d{4}-\d{4}-\d{4}"  # Credit cards
      - "\d{3}-\d{2}-\d{4}"        # SSN
      - ".+@.+\..+"                # Email addresses
```

## Performance Best Practices

### Database Optimization

**Do:**
- **Add appropriate indexes**: For frequently queried columns
- **Optimize queries**: Use EXPLAIN ANALYZE to identify slow queries
- **Implement connection pooling**: Reuse database connections
- **Use appropriate data types**: Choose the right type for each column
- **Monitor query performance**: Track slow queries and optimize them

**Don't:**
- Over-index (too many indexes slow down writes)
- Use SELECT * in production
- Ignore query performance
- Use N+1 queries
- Forget to analyze tables

**Indexing Strategy:**
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX idx_metrics_name ON metrics(metric_name);
CREATE INDEX idx_metrics_timestamp_name ON metrics(timestamp, metric_name);

-- Add composite indexes for common query patterns
CREATE INDEX idx_alerts_rule_status ON alerts(rule_id, status);
CREATE INDEX idx_alerts_severity_time ON alerts(severity, triggered_at);

-- Analyze tables regularly
ANALYZE metrics;
ANALYZE alerts;
```

### Caching Strategies

**Do:**
- **Cache frequently accessed data**: Reduce database load
- **Use appropriate TTLs**: Balance freshness with performance
- **Implement cache invalidation**: Ensure data consistency
- **Monitor cache efficiency**: Track hit/miss ratios
- **Use multi-level caching**: Combine in-memory and distributed caches

**Don't:**
- Cache everything indiscriminately
- Use overly long TTLs
- Forget to invalidate cache
- Ignore cache performance
- Cache large objects unnecessarily

**Caching Configuration:**
```yaml
cache:
  ttl:
    api_metrics: 60s
    agent_status: 30s
    system_health: 15s
    user_data: 300s
  
  invalidation:
    on_write: true
    on_delete: true
    manual: ["admin/cache/invalidate"]
  
  monitoring:
    hit_ratio_target: 0.8
    memory_limit: 512MB
```

### API Performance

**Do:**
- **Implement rate limiting**: Protect against abuse and overload
- **Use pagination**: For large result sets
- **Optimize payloads**: Return only necessary data
- **Use compression**: Reduce response sizes
- **Implement caching**: At the API level

**Don't:**
- Return large unfiltered result sets
- Ignore payload sizes
- Forget rate limiting
- Use inefficient serialization
- Ignore compression

**API Optimization:**
```python
# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/agents")
@limiter.limit("100/minute")
async def list_agents():
    # Paginated response
    return {
        "data": agents[offset:offset+limit],
        "total": total_count,
        "offset": offset,
        "limit": limit
    }

# Compression middleware
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Background Job Optimization

**Do:**
- **Use appropriate queue sizes**: Balance throughput with memory usage
- **Implement retry logic**: Handle transient failures
- **Monitor job performance**: Track execution times and failure rates
- **Use batch processing**: For high-volume operations
- **Implement prioritization**: For critical jobs

**Don't:**
- Overload queues
- Ignore job failures
- Forget to monitor performance
- Process items one-by-one unnecessarily
- Treat all jobs equally

**Job Configuration:**
```yaml
worker:
  concurrency: 4
  max_jobs: 1000
  retry:
    max_attempts: 3
    backoff: exponential
    jitter: true
  
  queues:
    high_priority:
      concurrency: 2
      max_jobs: 100
    
    default:
      concurrency: 2
      max_jobs: 500
    
    low_priority:
      concurrency: 1
      max_jobs: 1000
```

## Operational Best Practices

### Deployment Strategies

**Do:**
- **Use blue-green deployments**: Minimize downtime
- **Implement canary releases**: Test changes with small user groups
- **Use feature flags**: Enable gradual rollouts
- **Monitor deployments**: Watch for errors and performance issues
- **Have rollback plans**: Be prepared to revert quickly

**Don't:**
- Deploy without testing
- Release to all users at once
- Ignore deployment monitoring
- Forget rollback procedures
- Deploy during peak hours

**Deployment Checklist:**
```markdown
- [ ] Changes tested in staging
- [ ] Database migrations verified
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured
- [ ] Team notified
- [ ] Maintenance window scheduled (if needed)
- [ ] Deployment started
- [ ] Health checks passing
- [ ] Monitoring for 30 minutes
- [ ] Deployment complete
```

### Incident Management

**Do:**
- **Define incident severity levels**: Clear criteria for each level
- **Establish escalation procedures**: Know who to contact
- **Document resolution procedures**: For common incidents
- **Conduct post-mortems**: Learn from incidents
- **Test incident response**: Regular drills

**Don't:**
- Ignore incident severity
- Forget to communicate
- Skip documentation
- Blame individuals
- Ignore lessons learned

**Incident Severity Levels:**
```yaml
incident:
  severity:
    sev0:
      name: Critical
      description: System down or data loss
      response_time: 5 minutes
      escalation: Immediate
      notification: All channels
    
    sev1:
      name: High
      description: Major functionality impaired
      response_time: 15 minutes
      escalation: Team lead
      notification: Email + Slack
    
    sev2:
      name: Medium
      description: Partial functionality impaired
      response_time: 1 hour
      escalation: On-call
      notification: Email
    
    sev3:
      name: Low
      description: Minor issues
      response_time: 4 hours
      escalation: Next business day
      notification: Ticket
```

### Monitoring and Maintenance

**Do:**
- **Implement comprehensive monitoring**: Cover all critical components
- **Set up alerting**: For critical issues
- **Regular maintenance**: Schedule and perform regularly
- **Document procedures**: For common operations
- **Review logs**: Regularly check for issues

**Don't:**
- Ignore monitoring gaps
- Disable alerts
- Skip maintenance
- Forget documentation
- Ignore log warnings

**Maintenance Schedule:**
```markdown
Daily:
- Check system health dashboard
- Review active alerts
- Verify backup completion
- Check error logs

Weekly:
- Review metric trends
- Check database performance
- Verify cache efficiency
- Test failover procedures

Monthly:
- Review alert configurations
- Test disaster recovery
- Rotate secrets
- Update dependencies

Quarterly:
- Capacity planning review
- Architecture review
- Security audit
- Performance testing
```

## Development Best Practices

### Code Quality

**Do:**
- **Follow consistent style**: Use linters and formatters
- **Write tests**: Unit, integration, and end-to-end
- **Document code**: Clear comments and docstrings
- **Review code**: Peer reviews for all changes
- **Use type hints**: Improve code clarity and catch errors early

**Don't:**
- Ignore style guidelines
- Skip testing
- Forget documentation
- Skip code reviews
- Ignore type safety

**Code Quality Tools:**
```yaml
tools:
  python:
    - ruff: linting
    - black: formatting
    - mypy: type checking
    - pytest: testing
  
  typescript:
    - eslint: linting
    - prettier: formatting
    - tsc: type checking
    - vitest: testing
  
  ci:
    - github-actions: workflow automation
    - sonarqube: code quality analysis
```

### Testing Strategies

**Do:**
- **Write unit tests**: For individual components
- **Write integration tests**: For component interactions
- **Write end-to-end tests**: For user journeys
- **Test edge cases**: Handle unexpected inputs
- **Automate testing**: Run tests on every commit

**Don't:**
- Skip testing
- Only test happy paths
- Ignore test failures
- Forget to update tests
- Manually test everything

**Testing Pyramid:**
```markdown
Unit Tests (70%):
- Fast execution
- Isolated components
- Mock dependencies

Integration Tests (20%):
- Component interactions
- Database access
- External services

End-to-End Tests (10%):
- User journeys
- Full system
- Production-like environment
```

### Documentation Practices

**Do:**
- **Document APIs**: Clear endpoint documentation
- **Document architecture**: System diagrams and explanations
- **Document procedures**: Operational runbooks
- **Document decisions**: Architecture decision records
- **Keep documentation updated**: Review regularly

**Don't:**
- Skip documentation
- Let documentation get outdated
- Document obvious things
- Forget to document changes
- Hide documentation

**Documentation Structure:**
```
docs/
├── architecture/          # Architecture diagrams and explanations
├── api-reference/        # API documentation
├── development/          # Development guidelines
├── operations/           # Operational procedures
├── troubleshooting/       # Troubleshooting guides
├── decisions/             # Architecture decision records
└── changes/               # Change documentation
```

### Version Control

**Do:**
- **Use semantic commits**: Clear, descriptive commit messages
- **Write good commit messages**: Explain why, not just what
- **Use branches**: Feature branches for development
- **Review pull requests**: Before merging
- **Tag releases**: For version tracking

**Don't:**
- Commit directly to main
- Write vague commit messages
- Ignore pull request reviews
- Forget to tag releases
- Commit large unrelated changes

**Commit Message Guidelines:**
```markdown
Type: What kind of change
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Formatting, missing semi-colons, etc.
- refactor: Code refactoring
- perf: Performance improvements
- test: Adding or fixing tests
- chore: Maintenance tasks

Scope: Which component (optional)
- (api), (console), (vault), etc.

Subject: Brief description
- Use imperative mood
- Capitalize first letter
- No period at the end
- Less than 72 characters

Body: Detailed explanation (optional)
- Why the change was made
- What problem it solves
- Any breaking changes

Footer: References (optional)
- Closes #123
- Fixes #456
- Related to #789
```

## Compliance Best Practices

### Data Protection

**Do:**
- **Implement DSGVO compliance**: For EU data subjects
- **Document data processing**: Maintain records of processing activities
- **Implement data subject rights**: Procedures for access, rectification, erasure
- **Conduct DPIAs**: For high-risk processing
- **Appoint DPO**: If required

**Don't:**
- Ignore data protection regulations
- Forget to document processing
- Ignore data subject requests
- Skip DPIAs
- Forget DPO responsibilities

**DSGVO Compliance Checklist:**
```markdown
- [ ] Data processing inventory maintained
- [ ] Lawful basis for processing documented
- [ ] Data subject rights procedures in place
- [ ] Data protection by design and default
- [ ] Data breach notification procedure
- [ ] DPIA process for high-risk processing
- [ ] DPO appointed (if required)
- [ ] Records of processing activities maintained
- [ ] International data transfer mechanisms
- [ ] Training for staff
```

### Audit Trail

**Do:**
- **Implement comprehensive logging**: All significant actions
- **Maintain immutable logs**: Prevent tampering
- **Regularly review logs**: Detect anomalies
- **Retain logs appropriately**: Follow regulatory requirements
- **Protect log integrity**: Use digital signatures or hashes

**Don't:**
- Disable logging
- Allow log tampering
- Ignore log reviews
- Delete logs prematurely
- Store logs insecurely

**Audit Trail Configuration:**
```yaml
audit:
  logging:
    enabled: true
    retention: 365d
    integrity: sha256
    
  events:
    - user.login
    - user.logout
    - user.create
    - user.delete
    - agent.create
    - agent.delete
    - agent.assign
    - secret.access
    - secret.create
    - secret.delete
    - alert.create
    - alert.acknowledge
    - alert.resolve
```

### Incident Response

**Do:**
- **Define incident response plan**: Clear procedures
- **Train response team**: Regular exercises
- **Document incidents**: Detailed records
- **Report breaches**: Within regulatory timeframes
- **Learn from incidents**: Post-incident reviews

**Don't:**
- Ignore incident response planning
- Skip training
- Forget documentation
- Delay breach reporting
- Repeat mistakes

**Incident Response Plan:**
```markdown
1. Preparation:
   - Define roles and responsibilities
   - Establish communication channels
   - Prepare response tools
   - Train team members

2. Identification:
   - Detect security events
   - Determine if incident
   - Classify severity
   - Notify response team

3. Containment:
   - Short-term containment
   - Long-term containment
   - Evidence preservation
   - System isolation

4. Eradication:
   - Identify root cause
   - Remove malicious presence
   - Patch vulnerabilities
   - Verify removal

5. Recovery:
   - Restore systems
   - Monitor for recurrence
   - Test systems
   - Bring online gradually

6. Lessons Learned:
   - Conduct post-incident review
   - Document findings
   - Update procedures
   - Implement improvements
```

### Budget Control

**Do:**
- **Set budget limits**: For each agent
- **Monitor usage**: Track against limits
- **Implement alerts**: Before limits reached
- **Enforce limits**: Prevent overages
- **Review regularly**: Adjust as needed

**Don't:**
- Ignore budget tracking
- Allow unlimited spending
- Forget to alert
- Ignore overages
- Set unrealistic limits

**Budget Management:**
```yaml
budget:
  default_limit: 100.00  # EUR
  monitoring:
    warning_threshold: 0.8  # 80%
    critical_threshold: 0.95  # 95%
  
  enforcement:
    hard_limit: true
    action_on_limit: pause_agent
    
  reporting:
    daily_summary: true
    weekly_report: true
    monthly_review: true
```

## Conclusion

These best practices provide comprehensive guidance for operating and maintaining the enhanced NomOS monitoring and infrastructure hardening features. By following these recommendations, you can ensure system reliability, security, performance, and compliance with operational and regulatory requirements.