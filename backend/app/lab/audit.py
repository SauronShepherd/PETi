from __future__ import annotations

from uuid import uuid4

from .contracts import AdminAuditEvent
from .hashing import owner_hash


def create_audit_event(secret: str, actor: str, action: str, target_type: str,
    target_id: str | None, correlation_id: str, *, outcome: str = "SUCCEEDED", metadata=None) -> AdminAuditEvent:
    return AdminAuditEvent(str(uuid4()), action, owner_hash(actor, secret), target_type,
        owner_hash(target_id, secret) if target_id else None, outcome, correlation_id, metadata=metadata or {})
