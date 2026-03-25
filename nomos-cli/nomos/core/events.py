"""NomOS Event Types — contract between all components.

Defines the canonical event types used by the hash chain, governance
hooks, API, and CLI. Adding a new event type here makes it available
everywhere.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field


class EventType(str, Enum):
    """Canonical NomOS event types."""

    # Agent lifecycle
    AGENT_CREATED = "agent.created"
    AGENT_DEPLOYED = "agent.deployed"
    AGENT_STOPPED = "agent.stopped"
    AGENT_RETIRED = "agent.retired"

    # Compliance
    COMPLIANCE_CHECK_PASSED = "compliance.check.passed"
    COMPLIANCE_CHECK_FAILED = "compliance.check.failed"
    COMPLIANCE_DOC_SIGNED = "compliance.doc.signed"

    # Governance
    GOVERNANCE_HOOK_TRIGGERED = "governance.hook.triggered"
    GOVERNANCE_HOOK_BLOCKED = "governance.hook.blocked"
    GOVERNANCE_KILL_SWITCH = "governance.kill_switch"
    GOVERNANCE_ESCALATION = "governance.escalation"

    # Audit
    AUDIT_CHAIN_CREATED = "audit.chain.created"
    AUDIT_CHAIN_VERIFIED = "audit.chain.verified"
    AUDIT_EXPORTED = "audit.exported"

    # Task dispatch
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # Budget
    BUDGET_WARNING = "budget.warning"
    BUDGET_EXCEEDED = "budget.exceeded"

    # Approval
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"

    # Config revision
    CONFIG_CHANGED = "config.changed"
    CONFIG_ROLLED_BACK = "config.rolled_back"


_VALID_EVENT_TYPES = {e.value for e in EventType}


def validate_event_type(event_type: str) -> bool:
    """Check if a string is a valid NomOS event type."""
    return event_type in _VALID_EVENT_TYPES


@dataclass
class NomOSEvent:
    """A single event occurrence."""

    event_type: str
    agent_id: str
    data: dict = field(default_factory=dict)
    timestamp: str = field(default="")

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }
