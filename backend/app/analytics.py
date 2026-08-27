from dataclasses import dataclass, field
from datetime import UTC, datetime

ALLOWED_EVENTS = {
    "check_started",
    "check_funding_required",
    "check_submitted",
    "check_completed",
    "check_abstained",
    "check_failed",
    "check_safety_state",
    "timeline_viewed",
    "measurement_logged",
    "care_created",
    "care_completed",
    "care_skipped",
    "care_rescheduled",
    "notification_permission_result",
    "notification_delivered",
}


@dataclass
class AnalyticsRecorder:
    events: list[dict] = field(default_factory=list)

    def record(self, event: str, *, user_id: str, check_id: str | None = None, safety_state: str | None = None) -> None:
        if event not in ALLOWED_EVENTS:
            raise ValueError("ANALYTICS_EVENT_NOT_ALLOWED")
        if check_id and any(existing.get("event") == event and existing.get("check_id") == check_id for existing in self.events):
            return
        item = {"event": event, "user_id": user_id, "created_at": datetime.now(UTC).isoformat()}
        if check_id:
            item["check_id"] = check_id
        if safety_state:
            item["safety_state"] = safety_state
        self.events.append(item)
