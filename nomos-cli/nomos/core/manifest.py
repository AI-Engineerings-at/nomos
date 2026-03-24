"""NomOS Agent Manifest — Pydantic v2 models.

Defines the schema for agent-manifest.yaml files that customers fill out
to register an AI agent within the NomOS governance framework.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class RiskClass(str, Enum):
    minimal = "minimal"
    limited = "limited"
    high = "high"


class SandboxProfile(str, Enum):
    minimal = "minimal"
    limited = "limited"
    high_risk = "high-risk"


class IsolationLevel(str, Enum):
    strict = "strict"
    project = "project"
    shared = "shared"


class MemoryBackend(str, Enum):
    honcho = "honcho"
    local = "local"
    none = "none"


class ReviewMode(str, Enum):
    auto = "auto"
    manual = "manual"
    hybrid = "hybrid"


# ---------------------------------------------------------------------------
# Regex for agent ID validation
# ---------------------------------------------------------------------------

_AGENT_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class AgentIdentity(BaseModel):
    """Core agent metadata."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, max_length=128, description="Unique ID (lowercase, alphanumeric + hyphens)")
    name: str = Field(..., min_length=1, max_length=256, description="Human-readable name")
    role: str = Field(..., min_length=1, description="Agent role")
    risk_class: RiskClass = Field(default=RiskClass.limited, description="EU AI Act risk class")
    created_at: datetime = Field(..., description="ISO 8601 creation timestamp")
    manifest_version: str = Field(default="1.0.0", description="Manifest schema version")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not _AGENT_ID_RE.match(v):
            raise ValueError(f"Agent id must be lowercase alphanumeric with hyphens only, got: {v!r}")
        return v


class AgentDisplayIdentity(BaseModel):
    """Public-facing identity shown to end-users."""

    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(..., min_length=1, description="External display name")
    company: str = Field(..., min_length=1, description="Company name")
    email: str = Field(..., description="Agent email address")
    ai_disclosure: str = Field(
        default="Diese Nachricht wurde mit KI-Unterstuetzung erstellt.",
        description="AI disclosure text (Art. 50 EU AI Act)",
    )


class NemoClawConfig(BaseModel):
    """NemoClaw sandbox configuration."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(default=True)
    sandbox_profile: SandboxProfile = Field(default=SandboxProfile.limited)
    network_policy: str = Field(default="outbound-restricted")
    credential_guard: bool = Field(default=True)
    audit_logging: bool = Field(default=True)


class ComplianceConfig(BaseModel):
    """Compliance documents and sign-off requirements."""

    model_config = ConfigDict(extra="forbid")

    documents_required: list[str] = Field(
        default_factory=lambda: [
            "dpia",
            "verarbeitungsverzeichnis",
            "art50_transparency",
            "art14_killswitch",
            "art12_logging",
        ],
        description="Required compliance documents",
    )
    sign_off_required: bool = Field(default=True)
    blocking: bool = Field(default=True, description="Agent cannot start without signed docs")


class GovernanceConfig(BaseModel):
    """Governance hooks and kill-switch configuration."""

    model_config = ConfigDict(extra="forbid")

    hooks_enabled: list[str] = Field(
        default_factory=lambda: [
            "safety-gate",
            "quality-gate",
            "credential-guard",
            "kill-switch",
            "escalation-tracker",
            "audit-logger",
            "art50-labeler",
            "session-init",
        ],
        description="Active governance hooks",
    )
    kill_switch_authority: list[str] = Field(
        default_factory=list,
        description="Usernames who can trigger kill switch",
    )
    escalation_threshold: int = Field(default=2, ge=1)
    audit_retention_days: int = Field(default=365, ge=1)


class PIIFilterConfig(BaseModel):
    """PII filtering settings for memory."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(default=True)
    mask_emails: bool = Field(default=True)
    mask_phones: bool = Field(default=True)
    mask_addresses: bool = Field(default=True)
    keep_names: bool = Field(default=False)


class DeriverConfig(BaseModel):
    """Memory deriver configuration."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(default=True)
    review_mode: ReviewMode = Field(default=ReviewMode.auto)


class RetentionConfig(BaseModel):
    """Data retention periods."""

    model_config = ConfigDict(extra="forbid")

    session_messages_days: int = Field(default=90, ge=1)
    representations_days: int = Field(default=365, ge=1)
    audit_logs_days: int = Field(default=730, ge=1)


class MemoryConfig(BaseModel):
    """Memory backend and isolation configuration."""

    model_config = ConfigDict(extra="forbid")

    backend: MemoryBackend = Field(default=MemoryBackend.local)
    namespace: str = Field(default="", description="Auto-generated from agent.id if empty")
    isolation_level: IsolationLevel = Field(default=IsolationLevel.strict)
    pii_filter: PIIFilterConfig = Field(default_factory=PIIFilterConfig)
    deriver: DeriverConfig = Field(default_factory=DeriverConfig)
    retention: RetentionConfig = Field(default_factory=RetentionConfig)


class MultiAgentConfig(BaseModel):
    """Multi-agent collaboration settings."""

    model_config = ConfigDict(extra="forbid")

    inherits_rules_from: list[str] = Field(
        default_factory=lambda: ["shared-base-rules"],
    )
    project_scope: str = Field(default="", description="Shared memory scope")


# ---------------------------------------------------------------------------
# Root model
# ---------------------------------------------------------------------------


class AgentManifest(BaseModel):
    """Root model for a NomOS agent manifest file."""

    model_config = ConfigDict(extra="forbid")

    agent: AgentIdentity
    identity: AgentDisplayIdentity
    nemoclaw: NemoClawConfig = Field(default_factory=NemoClawConfig)
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    multi_agent: MultiAgentConfig = Field(default_factory=MultiAgentConfig)
    skills: list[str] = Field(default_factory=list)
