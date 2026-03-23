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
