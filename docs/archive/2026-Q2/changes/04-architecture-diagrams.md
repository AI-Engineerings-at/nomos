# NomOS Monitoring and Infrastructure Hardening - Architecture Diagrams

## Table of Contents

1. [System Overview](#system-overview)
2. [Monitoring Architecture](#monitoring-architecture)
3. [Alerting Flow](#alerting-flow)
4. [Vault Integration](#vault-integration)
5. [Setup Wizard Flow](#setup-wizard-flow)
6. [Data Flow Diagrams](#data-flow-diagrams)
7. [Component Interactions](#component-interactions)
8. [Deployment Architecture](#deployment-architecture)

## System Overview

### High-Level Architecture

```mermaid
graph TD
    A[User] -->|HTTP/HTTPS| B[Caddy Reverse Proxy]
    B --> C[Nomos Console]
    B --> D[Nomos API]
    D --> E[PostgreSQL]
    D --> F[Valkey Cache]
    D --> G[Vault]
    D --> H[Nomos Gateway]
    H --> I[LLM Providers]
    
    J[Agents] -->|Heartbeats| D
    J -->|Task Results| D
    
    K[Monitoring System] -->|Metrics| D
    K -->|Alerts| C
    K -->|Notifications| L[Email/SMTP]
    K -->|Webhooks| M[Slack/Teams]
    
    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
    style C fill:#9f9,stroke:#333
    style D fill:#99f,stroke:#333
    style E fill:#ff9,stroke:#333
    style F fill:#f99,stroke:#333
    style G fill:#999,stroke:#333
    style H fill:#9f9,stroke:#333
    style I fill:#f9f,stroke:#333
    style J fill:#99f,stroke:#333
    style K fill:#ff6,stroke:#333
    style L fill:#6f6,stroke:#333
    style M fill:#66f,stroke:#333
```

### Component Relationships

```mermaid
classDiagram
    class User {
        +interacts with Console
        +receives Notifications
    }
    
    class Console {
        +Next.js frontend
        +displays Metrics
        +shows Alerts
        +Setup Wizard
    }
    
    class API {
        +FastAPI backend
        +collects Metrics
        +processes Alerts
        +manages Agents
    }
    
    class Monitoring {
        +MetricsService
        +AlertService
        +NotificationService
        +Background Jobs
    }
    
    class Database {
        +PostgreSQL
        +metrics table
        +alerts table
        +alert_rules table
    }
    
    class Vault {
        +secrets management
        +AppRole authentication
        +system secrets
        +database credentials
    }
    
    class Gateway {
        +OpenClaw plugin
        +LLM provider proxy
        +health monitoring
    }
    
    User --> Console
    Console --> API
    API --> Monitoring
    Monitoring --> Database
    API --> Vault
    API --> Gateway
    Monitoring --> Console
    Monitoring --> Email
    Monitoring --> Webhooks
```

## Monitoring Architecture

### Metrics Collection Flow

```mermaid
flowchart TD
    A[API Request] --> B[Request ID Middleware]
    B --> C[Structured Logging Middleware]
    C --> D[Metrics Middleware]
    D --> E[Metrics Service]
    E --> F[(metrics table)]
    
    G[Agent Heartbeat] --> H[Heartbeat Handler]
    H --> E
    
    I[System Health Checks] --> J[Health Router]
    J --> E
    
    K[Background Jobs] --> L[Metric Aggregation]
    L --> M[(aggregated_metrics table)]
    
    N[Visualization] --> O[Metrics API]
    O --> F
    O --> M
    
    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
    style C fill:#bbf,stroke:#333
    style D fill:#bbf,stroke:#333
    style E fill:#9f9,stroke:#333
    style F fill:#ff9,stroke:#333
    style G fill:#f9f,stroke:#333
    style H fill:#99f,stroke:#333
    style I fill:#f9f,stroke:#333
    style J fill:#99f,stroke:#333
    style K fill:#f99,stroke:#333
    style L fill:#f99,stroke:#333
    style M fill:#ff9,stroke:#333
    style N fill:#9f9,stroke:#333
    style O fill:#99f,stroke:#333
```

### Metrics Service Architecture

```mermaid
classDiagram
    class MetricsService {
        +record_metric(metric_name, value, dimensions)
        +get_current_value(metric_name, window)
        +get_metrics_series(metric_name, start, end, dimensions)
        +aggregate_metrics(metric_name, window, function)
    }
    
    class MetricsRepository {
        +insert_metric(metric)
        +get_metrics_query(metric_name, window)
        +get_series_query(metric_name, start, end)
    }
    
    class MetricsMiddleware {
        +process_request(request)
        +process_response(response)
        +record_api_metrics()
    }
    
    class AlertService {
        +check_alerts()
        +create_alert(rule, current_value)
        +acknowledge_alert(alert_id)
        +resolve_alert(alert_id)
    }
    
    MetricsService --> MetricsRepository
    MetricsMiddleware --> MetricsService
    AlertService --> MetricsService
    AlertService --> MetricsRepository
```

### Database Schema

```mermaid
erDiagram
    metrics ||--o{ alert_rules : "triggers"
    alert_rules ||--o{ alerts : "creates"
    
    metrics {
        bigint id PK
        timestamptz timestamp
        varchar(255) metric_name
        jsonb dimensions
        float value
        varchar(50) source
    }
    
    alert_rules {
        serial id PK
        varchar(255) metric_name
        varchar(50) threshold_type
        float threshold_value
        interval comparison_window
        varchar(50) severity
        jsonb notification_channels
        text description
        timestamptz created_at
        timestamptz updated_at
    }
    
    alerts {
        uuid id PK
        int rule_id FK
        varchar(50) severity
        varchar(255) metric_name
        float current_value
        float threshold_value
        timestamptz triggered_at
        timestamptz resolved_at
        varchar(50) notification_status
        jsonb notification_channels
        jsonb context
    }
    
    aggregated_metrics {
        bigint id PK
        timestamptz timestamp
        varchar(255) metric_name
        jsonb dimensions
        float avg_value
        float max_value
        float min_value
        int count
        varchar(50) aggregation_window
    }
```

## Alerting Flow

### Alert Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Triggered: check_alerts()
    Triggered --> Notifying: send_notifications()
    Notifying --> Active: notifications sent
    Active --> Acknowledged: acknowledge_alert()
    Acknowledged --> Resolved: resolve_alert()
    Active --> Resolved: auto-resolve
    Resolved --> [*]
    
    state Notifying {
        Email --> Webhook
        Webhook --> Console
    }
    
    state Auto-resolve {
        [*] --> Check: metric back to normal
        Check --> Resolve: yes
        Check --> Active: no
    }
```

### Alert Processing Flow

```mermaid
flowchart TD
    A[Start Alert Processing Job] --> B[Get All Active Alert Rules]
    B --> C{For Each Rule}
    C -->|Yes| D[Get Current Metric Value]
    D --> E{Threshold Breached?}
    E -->|Yes| F{Alert Already Active?}
    F -->|No| G[Create New Alert]
    G --> H[Send Notifications]
    H --> I[Log Alert]
    F -->|Yes| J[Update Existing Alert]
    E -->|No| K[Mark Rule Checked]
    C -->|No| L[End Job]
    
    style A fill:#9f9,stroke:#333
    style B fill:#bbf,stroke:#333
    style C fill:#f99,stroke:#333
    style D fill:#bbf,stroke:#333
    style E fill:#f99,stroke:#333
    style F fill:#f99,stroke:#333
    style G fill:#9f9,stroke:#333
    style H fill:#99f,stroke:#333
    style I fill:#ff9,stroke:#333
    style J fill:#ff9,stroke:#333
    style K fill:#bbf,stroke:#333
    style L fill:#9f9,stroke:#333
```

### Notification Service Architecture

```mermaid
classDiagram
    class NotificationService {
        +send_alert(alert)
        +send_email(recipients, subject, body)
        +send_webhook(url, payload)
        +send_console_notification(alert)
    }
    
    class EmailClient {
        +connect(smtp_host, smtp_port)
        +authenticate(username, password)
        +send(recipients, subject, body)
    }
    
    class WebhookClient {
        +send(url, payload)
        +retry(url, payload, max_attempts)
        +handle_response(response)
    }
    
    class ConsoleNotification {
        +broadcast(alert)
        +store_for_user(user_id, alert)
    }
    
    NotificationService --> EmailClient
    NotificationService --> WebhookClient
    NotificationService --> ConsoleNotification
```

## Vault Integration

### Vault Architecture

```mermaid
flowchart TD
    A[Vault Init Container] --> B[Initialize Vault]
    B --> C[Create AppRole]
    C --> D[Generate Secrets]
    D --> E[Store in Vault]
    E --> F[Write Credentials File]
    
    G[Nomos API] --> H[Read Credentials]
    H --> I[Authenticate with Vault]
    I --> J[Fetch Secrets]
    J --> K[Cache Secrets]
    
    L[Other Services] --> M[Read Secret Files]
    M --> N[Use Secrets]
    
    style A fill:#f99,stroke:#333
    style B fill:#9f9,stroke:#333
    style C fill:#9f9,stroke:#333
    style D fill:#9f9,stroke:#333
    style E fill:#9f9,stroke:#333
    style F fill:#9f9,stroke:#333
    style G fill:#99f,stroke:#333
    style H fill:#bbf,stroke:#333
    style I fill:#bbf,stroke:#333
    style J fill:#bbf,stroke:#333
    style K fill:#bbf,stroke:#333
    style L fill:#f9f,stroke:#333
    style M fill:#bbf,stroke:#333
    style N fill:#99f,stroke:#333
```

### Secrets Management Flow

```mermaid
sequenceDiagram
    participant Init as Vault Init Container
    participant Vault as Vault Server
    participant API as Nomos API
    participant DB as PostgreSQL
    
    Init->>Vault: operator init
    Vault-->>Init: unseal_keys, root_token
    Init->>Vault: secrets enable kv-v2 at nomos/
    Init->>Vault: policy write nomos-api
    Init->>Vault: auth enable approle
    Init->>Vault: write approle/role/nomos-api
    Init->>Vault: kv put nomos/secrets/system
    Init->>Vault: kv put nomos/secrets/database
    Init->>File: Write approle-creds.env
    
    API->>File: Read approle-creds.env
    API->>Vault: auth/approle/login
    Vault-->>API: client_token
    API->>Vault: kv/get nomos/secrets/system
    Vault-->>API: jwt_secret, plugin_api_key
    API->>Vault: kv/get nomos/secrets/database
    Vault-->>API: password
    API->>DB: Connect with credentials
    
    style Init fill:#f99,stroke:#333
    style Vault fill:#999,stroke:#333
    style API fill:#99f,stroke:#333
    style DB fill:#ff9,stroke:#333
```

### Vault Component Diagram

```mermaid
classDiagram
    class VaultClient {
        +connected
        +health_status()
        +login_with_approle(role_id, secret_id)
        +read_secret(path)
        +write_secret(path, data)
    }
    
    class VaultSource {
        +get_secret(path)
        +get_cached_secret(path)
        +invalidate_cache()
    }
    
    class VaultTTLCache {
        +get(key)
        +set(key, value, ttl)
        +delete(key)
        +invalidate_all()
    }
    
    class AppRoleCredentials {
        +role_id
        +secret_id
        +load_from_file()
        +refresh()
    }
    
    VaultClient --> VaultSource
    VaultSource --> VaultTTLCache
    VaultSource --> AppRoleCredentials
    AppRoleCredentials --> File: approle-creds.env
```

## Setup Wizard Flow

### Wizard State Machine

```mermaid
stateDiagram-v2
    [*] --> Loading
    Loading --> Step1: Vault Unseal Key
    Step1 --> Step2: Admin Account
    Step2 --> Step2b: 2FA Setup
    Step2b --> Step3: LLM Provider
    Step3 --> Step4: Complete
    Step4 --> [*]
    
    Step1: Fetch unseal key
    Step2: Create admin + recovery key
    Step2b: Setup TOTP (optional)
    Step3: Configure LLM provider (optional)
    Step4: Summary + finish
```

### Setup Wizard Sequence

```mermaid
sequenceDiagram
    participant User as User
    participant Console as Console
    participant API as API
    participant Vault as Vault
    participant DB as Database
    
    User->>Console: GET /setup
    Console->>API: GET /system/status
    API-->>Console: {setup_required: true}
    
    Console->>API: GET /system/unseal-key
    API->>Vault: Read init file
    Vault-->>API: unseal_key
    API-->>Console: {unseal_key: "...", auto_unseal: false}
    
    User->>Console: Submit unseal confirmation
    
    User->>Console: Enter admin credentials
    Console->>API: POST /users/bootstrap
    API->>DB: Create admin user
    API->>DB: Store recovery key
    API-->>Console: {user_id: "...", recovery_key: "..."}
    
    User->>Console: Confirm recovery key
    User->>Console: Setup 2FA (optional)
    Console->>API: POST /auth/2fa/setup
    API-->>Console: {qr_code: "...", secret: "..."}
    User->>Console: Enter TOTP code
    Console->>API: POST /auth/2fa/verify
    
    User->>Console: Select LLM provider
    User->>Console: Enter API key
    Console->>API: PATCH /settings
    Console->>API: GET /proxy/status
    API-->>Console: {status: "ok"}
    
    Console->>User: Show completion screen
    User->>Console: Click "Start Using NomOS"
    Console->>User: Redirect to /admin
    
    style User fill:#f9f,stroke:#333
    style Console fill:#9f9,stroke:#333
    style API fill:#99f,stroke:#333
    style Vault fill:#999,stroke:#333
    style DB fill:#ff9,stroke:#333
```

### Setup Wizard Components

```mermaid
classDiagram
    class SetupWizard {
        +currentStep
        +checkingStatus
        +checkError
        +nextStep()
        +prevStep()
        +submitStep()
    }
    
    class Step1Vault {
        +unsealKey
        +autoUnseal
        +keyConfirmed
        +fetchUnsealKey()
        +copyToClipboard()
    }
    
    class Step2Admin {
        +email
        +password
        +passwordConfirm
        +recoveryKey
        +recoveryConfirmed
        +createAdmin()
        +validatePassword()
    }
    
    class Step2TwoFA {
        +qrCode
        +totpCode
        +totpVerified
        +setup2FA()
        +verify2FA()
    }
    
    class Step3Provider {
        +selectedProvider
        +apiKey
        +providerTested
        +testProvider()
        +saveProvider()
    }
    
    class Step4Complete {
        +summary
        +finishSetup()
    }
    
    SetupWizard --> Step1Vault
    SetupWizard --> Step2Admin
    SetupWizard --> Step2TwoFA
    SetupWizard --> Step3Provider
    SetupWizard --> Step4Complete
```

## Data Flow Diagrams

### Metrics Data Flow

```mermaid
flowchart LR
    subgraph Sources
        A[API Requests] -->|request/response| B[Metrics Middleware]
        C[Agent Heartbeats] -->|agent metrics| D[Heartbeat Handler]
        E[System Checks] -->|component status| F[Health Router]
    end
    
    subgraph Collection
        B --> G[Metrics Service]
        D --> G
        F --> G
        G --> H[(metrics table)]
    end
    
    subgraph Processing
        H --> I[Aggregation Job]
        I --> J[(aggregated_metrics table)]
        J --> K[Retention Policy]
        K --> L[Archive]
    end
    
    subgraph Consumption
        H --> M[Metrics API]
        J --> M
        M --> N[Console Dashboard]
        M --> O[Alert Service]
        M --> P[External Monitoring]
    end
    
    style Sources fill:#f9f,stroke:#333
    style Collection fill:#9f9,stroke:#333
    style Processing fill:#bbf,stroke:#333
    style Consumption fill:#99f,stroke:#333
```

### Alert Data Flow

```mermaid
flowchart LR
    subgraph Configuration
        A[Admin] -->|create rule| B[Alert Rules API]
        B --> C[(alert_rules table)]
    end
    
    subgraph Processing
        C --> D[Alert Processing Job]
        D --> E[Metrics Service]
        E --> F[(metrics table)]
        D --> G{Threshold Check}
        G -->|breached| H[Create Alert]
        G -->|not breached| I[No Action]
        H --> J[(alerts table)]
    end
    
    subgraph Notification
        J --> K[Notification Service]
        K --> L[Email Client]
        K --> M[Webhook Client]
        K --> N[Console Notifications]
        L --> O[SMTP Server]
        M --> P[Slack/Teams]
        N --> Q[Console UI]
    end
    
    subgraph Management
        J --> R[Alerts API]
        R --> S[Admin]
        S -->|acknowledge| R
        S -->|resolve| R
        R --> J
    end
    
    style Configuration fill:#f9f,stroke:#333
    style Processing fill:#9f9,stroke:#333
    style Notification fill:#ff9,stroke:#333
    style Management fill:#99f,stroke:#333
```

### Request Flow with Monitoring

```mermaid
sequenceDiagram
    participant User as User
    participant Caddy as Caddy
    participant Console as Console
    participant API as API
    participant Middleware as Middleware
    participant Service as Service
    participant DB as Database
    
    User->>Caddy: GET /api/agents
    Caddy->>API: Forward request
    API->>Middleware: Request ID Middleware
    Middleware->>Middleware: Generate request_id
    Middleware->>Middleware: Add to request.state
    Middleware->>Service: Call next middleware
    
    Service->>Middleware: Structured Logging Middleware
    Middleware->>Middleware: Add logging context
    Middleware->>Service: Call next middleware
    
    Service->>Middleware: Metrics Middleware
    Middleware->>Middleware: Start timer
    Middleware->>Service: Call next middleware
    
    Service->>Service: Handle request
    Service->>DB: Query agents
    DB-->>Service: Return results
    
    Service->>Middleware: Return response
    Middleware->>Middleware: Stop timer
    Middleware->>MetricsService: Record API metrics
    MetricsService->>DB: Insert metric
    
    Middleware->>Logging: Log request
    Logging->>File: Write structured log
    
    Middleware->>User: Return response with X-Request-ID
    
    style User fill:#f9f,stroke:#333
    style Caddy fill:#bbf,stroke:#333
    style Console fill:#9f9,stroke:#333
    style API fill:#99f,stroke:#333
    style Middleware fill:#bbf,stroke:#333
    style Service fill:#99f,stroke:#333
    style DB fill:#ff9,stroke:#333
```

## Component Interactions

### Middleware Stack

```mermaid
classDiagram
    class Request
    class RequestIDMiddleware {
        +dispatch(request, call_next)
        +generate_request_id()
        +handle_exception(exc)
    }
    
    class StructuredLoggingMiddleware {
        +dispatch(request, call_next)
        +add_logging_context(request)
        +format_log_entry()
    }
    
    class MetricsMiddleware {
        +dispatch(request, call_next)
        +start_timer()
        +stop_timer()
        +record_metrics()
    }
    
    class ErrorHandlingMiddleware {
        +dispatch(request, call_next)
        +format_error_response(exc)
        +log_error()
    }
    
    Request --> RequestIDMiddleware
    RequestIDMiddleware --> StructuredLoggingMiddleware
    StructuredLoggingMiddleware --> MetricsMiddleware
    MetricsMiddleware --> ErrorHandlingMiddleware
    ErrorHandlingMiddleware --> RouteHandler
```

### API Router Structure

```mermaid
classDiagram
    class APIRouter
    
    class HealthRouter {
        +GET /health
        +GET /api/health
        +check_vault_status()
        +check_postgres()
        +check_valkey()
        +check_gateway()
    }
    
    class MonitoringRouter {
        +GET /metrics
        +GET /alerts
        +POST /alerts
        +PATCH /alerts/{id}
        +GET /alert-rules
        +POST /alert-rules
        +DELETE /alert-rules/{id}
    }
    
    class SystemRouter {
        +GET /system/status
        +GET /system/unseal-key
        +POST /system/setup
    }
    
    class UsersRouter {
        +POST /users/bootstrap
        +POST /users
        +GET /users/{id}
        +PATCH /users/{id}
    }
    
    APIRouter <|-- HealthRouter
    APIRouter <|-- MonitoringRouter
    APIRouter <|-- SystemRouter
    APIRouter <|-- UsersRouter
```

### Service Dependencies

```mermaid
graph TD
    A[API] --> B[MetricsService]
    A --> C[AlertService]
    A --> D[NotificationService]
    A --> E[VaultSource]
    A --> F[Database]
    
    B --> F
    C --> B
    C --> F
    D --> F
    E --> G[VaultClient]
    E --> H[VaultTTLCache]
    
    I[Background Worker] --> C
    I --> B
    
    style A fill:#99f,stroke:#333
    style B fill:#9f9,stroke:#333
    style C fill:#ff9,stroke:#333
    style D fill:#f99,stroke:#333
    style E fill:#999,stroke:#333
    style F fill:#ff9,stroke:#333
    style G fill:#999,stroke:#333
    style H fill:#999,stroke:#333
    style I fill:#f99,stroke:#333
```

## Deployment Architecture

### Docker Compose Architecture

```mermaid
flowchart TD
    subgraph Services
        A[nomos-caddy] -->|reverse proxy| B[nomos-console]
        A -->|reverse proxy| C[nomos-api]
        C --> D[nomos-postgres]
        C --> E[nomos-valkey]
        C --> F[nomos-vault]
        C --> G[nomos-worker]
        G --> D
        G --> E
        G --> F
        H[nomos-gateway] --> I[LLM Providers]
        C --> H
    end
    
    subgraph Volumes
        J[/vault/file] --> F
        J --> K[vault-init]
        K --> C
        K --> G
        K --> H
        L[postgres-data] --> D
        M[valkey-data] --> E
    end
    
    subgraph Networks
        N[nomos_default] --> A
        N --> B
        N --> C
        N --> D
        N --> E
        N --> F
        N --> G
        N --> H
    end
    
    style Services fill:#f9f,stroke:#333
    style Volumes fill:#ff9,stroke:#333
    style Networks fill:#9f9,stroke:#333
```

### Production Deployment

```mermaid
graph LR
    subgraph Load Balancer
        A[Internet] --> B[Cloud Load Balancer]
    end
    
    subgraph Kubernetes Cluster
        B --> C[Ingress Controller]
        C --> D[nomos-console Pods]
        C --> E[nomos-api Pods]
        
        subgraph Database
            E --> F[PostgreSQL StatefulSet]
            E --> G[Valkey Cluster]
        end
        
        subgraph Vault
            E --> H[Vault StatefulSet]
            E --> I[vault-init Job]
        end
        
        subgraph Workers
            J[nomos-worker Deployment] --> F
            J --> G
            J --> H
        end
        
        subgraph Gateway
            K[nomos-gateway Deployment] --> L[LLM Providers]
            E --> K
        end
    end
    
    subgraph Monitoring
        M[Prometheus] --> E
        M --> F
        M --> G
        M --> H
        N[Grafana] --> M
        O[Alertmanager] --> M
        O --> P[Email]
        O --> Q[Slack]
    end
    
    style Load Balancer fill:#bbf,stroke:#333
    style Kubernetes fill:#9f9,stroke:#333
    style Database fill:#ff9,stroke:#333
    style Vault fill:#999,stroke:#333
    style Workers fill:#f99,stroke:#333
    style Gateway fill:#99f,stroke:#333
    style Monitoring fill:#ff6,stroke:#333
```

### High Availability Architecture

```mermaid
graph TD
    A[User] --> B[Global Load Balancer]
    B --> C[Region 1]
    B --> D[Region 2]
    B --> E[Region 3]
    
    subgraph Region 1
        C --> F1[nomos-api x3]
        C --> G1[nomos-console x2]
        F1 --> H1[PostgreSQL HA]
        F1 --> I1[Valkey Cluster]
        F1 --> J1[Vault HA]
        F1 --> K1[nomos-worker x2]
        F1 --> L1[nomos-gateway x2]
    end
    
    subgraph Region 2
        D --> F2[nomos-api x3]
        D --> G2[nomos-console x2]
        F2 --> H2[PostgreSQL HA]
        F2 --> I2[Valkey Cluster]
        F2 --> J2[Vault HA]
        F2 --> K2[nomos-worker x2]
        F2 --> L2[nomos-gateway x2]
    end
    
    subgraph Region 3
        E --> F3[nomos-api x3]
        E --> G3[nomos-console x2]
        F3 --> H3[PostgreSQL HA]
        F3 --> I3[Valkey Cluster]
        F3 --> J3[Vault HA]
        F3 --> K3[nomos-worker x2]
        F3 --> L3[nomos-gateway x2]
    end
    
    subgraph Cross-Region
        H1 --> M[PostgreSQL Logical Replication]
        H2 --> M
        H3 --> M
        
        J1 --> N[Vault Replication]
        J2 --> N
        J3 --> N
    end
    
    subgraph Monitoring
        O[Prometheus Federation] --> F1
        O --> F2
        O --> F3
        P[Grafana] --> O
        Q[Alertmanager] --> O
    end
    
    style Region 1 fill:#9f9,stroke:#333
    style Region 2 fill:#9f9,stroke:#333
    style Region 3 fill:#9f9,stroke:#333
    style Cross-Region fill:#bbf,stroke:#333
    style Monitoring fill:#ff6,stroke:#333
```

## Conclusion

These architecture diagrams provide comprehensive visualizations of the NomOS monitoring and infrastructure hardening improvements. They illustrate component relationships, data flows, and deployment architectures to help understand the system design and implementation.