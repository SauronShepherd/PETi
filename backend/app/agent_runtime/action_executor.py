"""Deterministic bridge from an approved agent action to canonical Care."""
import json
from datetime import UTC, datetime
from hashlib import sha256


class CareActionExecutor:
    def __init__(self, care, pets, *, clock=None):
        self.care, self.pets = care, pets
        self.clock = clock
        self._receipts = {}

    def execute(self, owner: str, pet_id: str, action: dict, idempotency_key: str):
        if idempotency_key in self._receipts:
            return dict(self._receipts[idempotency_key])
        if action.get("action_type") not in {"CARE_REMINDER", "FOLLOW_UP_REMINDER"}:
            raise ValueError("AGENT_ACTION_TYPE_NOT_ALLOWED")
        args = dict(action.get("arguments") or {})
        title = str(args.get("title") or action.get("summary") or "PETi follow-up")[:200]
        due_at = args.get("due_at")
        if due_at is None:
            raise ValueError("AGENT_REMINDER_DUE_AT_REQUIRED")
        if isinstance(due_at, str):
            try:
                due_at = datetime.fromisoformat(due_at)
            except ValueError as exc:
                raise ValueError("AGENT_REMINDER_DUE_AT_INVALID") from exc
        if not isinstance(due_at, datetime):
            raise ValueError("AGENT_REMINDER_DUE_AT_INVALID")  # noqa: TRY004
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=UTC)
        payload = {
            "category": "FOLLOW_UP",
            "title": title,
            "due_at": due_at,
            "notification_enabled": bool(args.get("notification_enabled", True)),
            "timezone": str(args.get("timezone", "UTC")),
            "repeat_frequency": "ONCE",
            "repeat_interval": 1,
            "notes": "Created from an approved PETi agent action.",
        }
        item = self.care.create_care(owner, pet_id, payload, idempotency_key, self.pets)
        receipt = {"receipt_id": sha256(json.dumps({"action": action.get("id"), "care_id": item.id}, sort_keys=True).encode()).hexdigest(), "status": "EXECUTED", "care_id": item.id}
        self._receipts[idempotency_key] = receipt
        return dict(receipt)
