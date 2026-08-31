from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from .contracts import InteractionResponse, ResponseFeedback, TraceContext, utcnow
from .enums import (
    NEGATIVE_FEEDBACK_REASONS,
    POSITIVE_FEEDBACK_REASONS,
    FeedbackReason,
    FeedbackValue,
)
from .hashing import feedback_id, owner_hash
from .repositories import InMemoryLabRepository
from .telemetry import TelemetryService


class FeedbackStore(Protocol):
    def get_response(self, response_id: str) -> InteractionResponse | None: ...
    def get_feedback(self, feedback_id: str) -> ResponseFeedback | None: ...
    def put(self, feedback: ResponseFeedback) -> ResponseFeedback: ...
    def put_comment(self, feedback_id: str, comment: str) -> None: ...
    def delete_comment(self, feedback_id: str) -> None: ...
    def put_with_comment(self, feedback: ResponseFeedback, comment: str | None) -> ResponseFeedback: ...


class FeedbackService:
    def __init__(
        self,
        store: FeedbackStore | InMemoryLabRepository,
        telemetry: TelemetryService,
        *,
        hash_secret: str,
    ) -> None:
        self.store = store
        self.telemetry = telemetry
        self.hash_secret = hash_secret

    def get(self, owner: str, response_id: str) -> ResponseFeedback | None:
        item = self.store.get_feedback(feedback_id(owner, response_id))
        if item and item.owner_user_id != owner:
            raise ValueError("LAB_FEEDBACK_NOT_FOUND")
        return item

    def upsert(
        self,
        owner: str,
        response_id: str,
        *,
        value: FeedbackValue | str,
        reasons: list[FeedbackReason | str] | None = None,
        comment: str | None = None,
        locale: str | None = None,
        source: str = "WEB",
    ) -> ResponseFeedback:
        response = self._owned_response(owner, response_id)
        parsed_value = FeedbackValue(value)
        parsed_reasons = [FeedbackReason(reason) for reason in (reasons or [])]
        self._validate_reasons(parsed_value, parsed_reasons)
        clean_comment = self._clean_comment(comment)
        item_id = feedback_id(owner, response_id)
        now = utcnow()
        item = ResponseFeedback(
            id=item_id,
            owner_user_id=owner,
            owner_hash=owner_hash(owner, self.hash_secret),
            response_id=response.id,
            run_id=response.run_id,
            interaction_id=response.interaction_id,
            value=parsed_value,
            reasons=parsed_reasons,
            comment_ref=item_id if clean_comment else None,
            source=source,
            locale=locale,
            environment=response.environment,
            data_classification=response.data_classification,
            created_at=now,
            updated_at=now,
        )
        previous = self.store.get_feedback(item_id)
        stored = self.store.put_with_comment(item, clean_comment)
        self.telemetry.emit(
            "feedback_updated" if previous else "feedback_submitted",
            context=self._context(response),
            properties={
                "value": stored.value.value,
                "reasons": [reason.value for reason in stored.reasons],
                "has_comment": bool(clean_comment),
                **({"revision": stored.revision} if previous else {}),
            },
            actor_type="USER",
        )
        return stored

    def remove(self, owner: str, response_id: str) -> ResponseFeedback:
        response = self._owned_response(owner, response_id)
        item = self.get(owner, response_id)
        if not item or item.removed_at:
            raise ValueError("LAB_FEEDBACK_NOT_FOUND")
        removed = self.store.put_with_comment(replace(item, updated_at=utcnow(), removed_at=utcnow()), None)
        self.telemetry.emit(
            "feedback_removed",
            context=self._context(response),
            properties={"revision": removed.revision},
            actor_type="USER",
        )
        return removed

    def _owned_response(self, owner: str, response_id: str) -> InteractionResponse:
        response = self.store.get_response(response_id)
        if not response or response.owner_user_id != owner or response.deleted_at:
            raise ValueError("LAB_RESPONSE_NOT_FOUND")
        if not response.eligible_for_feedback:
            raise ValueError("LAB_RESPONSE_NOT_FEEDBACK_ELIGIBLE")
        return response

    @staticmethod
    def _validate_reasons(value: FeedbackValue, reasons: list[FeedbackReason]) -> None:
        if len(reasons) > 5 or len(set(reasons)) != len(reasons):
            raise ValueError("LAB_FEEDBACK_REASONS_INVALID")
        allowed = POSITIVE_FEEDBACK_REASONS if value is FeedbackValue.HELPED else NEGATIVE_FEEDBACK_REASONS
        if any(reason not in allowed for reason in reasons):
            raise ValueError("LAB_FEEDBACK_REASON_VALUE_MISMATCH")

    @staticmethod
    def _clean_comment(comment: str | None) -> str | None:
        if comment is None:
            return None
        clean = comment.strip()
        if not clean:
            return None
        if len(clean) > 1000 or any(ord(char) < 32 and char not in "\n\t" for char in clean):
            raise ValueError("LAB_FEEDBACK_COMMENT_INVALID")
        return clean

    @staticmethod
    def _context(response: InteractionResponse) -> TraceContext:
        return TraceContext(
            correlation_id=response.interaction_id,
            interaction_id=response.interaction_id,
            run_id=response.run_id,
            owner_user_id=response.owner_user_id,
            pet_id=None,
            agent_id=None,
            deployment_id=response.deployment_id,
            environment=response.environment,
            data_classification=response.data_classification,
        )
