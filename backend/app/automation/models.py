from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class AutomationExecution:
    rule_id: str
    evaluation_key: str
    outcome: str
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AutomationAuditEvent:
    rule_id: str
    actor_user_id: str | None
    event_type: str
    payload_safe: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CareTemplate:
    owner_user_id: str
    scope: str
    title: str
    occurrences: list[dict] = field(default_factory=list)
    version: int = 1


@dataclass
class OverdueEscalationPolicy:
    stages: list[dict]
    quiet_hours: dict = field(default_factory=dict)
    urgent_exception: bool = False
