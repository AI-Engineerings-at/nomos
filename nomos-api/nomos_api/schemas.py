"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256, examples=["Mani Ruf"])
    role: str = Field(..., min_length=1, max_length=256, examples=["external-secretary"])
    company: str = Field(..., min_length=1, max_length=256, examples=["AI Engineering"])
    email: str = Field(..., examples=["mani@ai-engineering.at"])
    risk_class: str = Field(default="limited", pattern="^(minimal|limited|high)$")


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    company: str
    email: str
    risk_class: str
    status: str
    manifest_hash: str
    compliance_status: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class FleetResponse(BaseModel):
    agents: list[AgentResponse]
    total: int


class ComplianceResponse(BaseModel):
    agent_id: str
    status: str
    missing_documents: list[str]
    errors: list[str]
    warnings: list[str]


class AuditEntryResponse(BaseModel):
    sequence: int
    event_type: str
    agent_id: str
    data: dict
    chain_hash: str
    timestamp: str


class AuditResponse(BaseModel):
    agent_id: str
    entries: list[AuditEntryResponse]
    total: int


class AuditVerifyResponse(BaseModel):
    agent_id: str
    valid: bool
    entries_checked: int
    errors: list[str]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


# --- Auth Schemas ---


class LoginRequest(BaseModel):
    email: str = Field(..., examples=["admin@nomos.local"])
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    message: str
    role: str
    email: str


class LogoutResponse(BaseModel):
    message: str


class TotpSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class TotpVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class TotpVerifyResponse(BaseModel):
    verified: bool


class RecoveryRequest(BaseModel):
    email: str
    recovery_phrase: str
    new_password: str = Field(..., min_length=12)


class RecoveryResponse(BaseModel):
    message: str


# --- User Schemas ---


class UserCreateRequest(BaseModel):
    email: str = Field(..., examples=["user@nomos.local"])
    password: str = Field(..., min_length=12)
    role: str = Field(default="user", pattern="^(admin|user|officer)$")


class UserCreateResponse(BaseModel):
    id: str
    email: str
    role: str
    recovery_key: str  # shown ONCE at creation


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    totp_enabled: bool
    session_timeout_hours: int
    is_active: bool
    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int


class UserUpdateRequest(BaseModel):
    role: str | None = Field(default=None, pattern="^(admin|user|officer)$")
    session_timeout_hours: int | None = Field(default=None, ge=1, le=168)
    is_active: bool | None = None
