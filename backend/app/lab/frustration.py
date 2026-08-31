from __future__ import annotations

from .enums import FeedbackReason, FeedbackValue

FRICTION_WEIGHTS = {"run_failed": 30, "context_repeated": 18, "response_regenerated": 15, "user_abandoned": 20}


def friction_index(events: list, feedback: list) -> dict:
    contributions = {name: sum(1 for event in events if event.event_name == name) * weight for name, weight in FRICTION_WEIGHTS.items()}
    contributions["negative_feedback"] = sum(item.removed_at is None and item.value is FeedbackValue.NOT_QUITE for item in feedback) * 25
    contributions["friction_reasons"] = sum(1 for item in feedback for reason in item.reasons if reason in {
        FeedbackReason.TOO_SLOW, FeedbackReason.REPETITIVE, FeedbackReason.REPEATED_CONTEXT_REQUEST,
    }) * 12
    return {"value": min(100, sum(contributions.values())), "contributions": contributions, "version": "1.0.0"}
