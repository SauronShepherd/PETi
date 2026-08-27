from datetime import UTC, datetime, timedelta

from app.credits.domain import FundingSource, OperationType, ReservationStatus
from app.credits.service import CreditService


def test_cost_profiles_version_and_expiration_audit():
    service = CreditService()
    profile = service.create_cost_profile(OperationType.AI_PHOTO_STANDARD, 4)
    assert (
        profile.version == 2 and service.profiles[OperationType.AI_PHOTO_STANDARD].credit_cost == 4
    )
    grant = service.grant("u", FundingSource.PROMOTIONAL, 2)
    grant.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert service.expire() == 1 and grant.remaining_amount == 0
    assert service.audit()["status"] == "OK"


def test_expiring_reservation_releases_funds():
    service = CreditService()
    service.grant("u", FundingSource.FREE_ALLOWANCE, 1)
    reservation = service.reserve("u", OperationType.AI_PHOTO_STANDARD, "op", "key")
    reservation.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert service.expire() == 1 and reservation.status == ReservationStatus.EXPIRED


def test_expiring_reservation_persists_expired_terminal_state():
    class Store:
        def __init__(self):
            self.rows = {}

        def append(self, collection, key, data):
            self.rows[(collection, key)] = dict(data)

        def list_all(self, collection):
            return [data for (name, _), data in self.rows.items() if name == collection]

    store = Store()
    service = CreditService(store)
    service.grant("u", FundingSource.FREE_ALLOWANCE, 1)
    reservation = service.reserve("u", OperationType.AI_PHOTO_STANDARD, "op-persist", "key-persist")
    reservation.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert service.expire() == 1
    restarted = CreditService(store)
    assert restarted.reservations[reservation.id].status == ReservationStatus.EXPIRED
