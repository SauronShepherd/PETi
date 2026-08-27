"""Exercise the funding lifecycle locally without AI or external services."""

import json

from app.credits.domain import FundingSource, OperationType, ReservationStatus
from app.credits.service import CreditService


def run() -> dict[str, object]:
    service = CreditService()
    service.grant("internal-harness", FundingSource.INTERNAL_TEST, 2)

    consumed = service.reserve(
        "internal-harness", OperationType.AI_PHOTO_STANDARD,
        "harness-consume-operation", "harness-consume-idempotency",
    )
    service.consume(consumed.id, "harness-consume-execution")

    released = service.reserve(
        "internal-harness", OperationType.AI_PHOTO_STANDARD,
        "harness-release-operation", "harness-release-idempotency",
    )
    service.release(released.id, "HARNESS_RELEASE")
    audit = service.audit()
    assert consumed.status == ReservationStatus.CONSUMED
    assert released.status == ReservationStatus.RELEASED
    return {
        "status": "PASS",
        "consumed_reservation": consumed.id,
        "released_reservation": released.id,
        "audit": audit,
    }


if __name__ == "__main__":
    print(json.dumps(run(), default=str, sort_keys=True))
