from concurrent.futures import ThreadPoolExecutor

from app.credits.domain import FundingSource, OperationType, ReservationStatus
from app.credits.service import CreditService, FundingError


def test_reservation_is_idempotent_and_preserves_provenance():
    s = CreditService()
    s.grant("u", FundingSource.REWARDED_AD, 1)
    s.grant("u", FundingSource.PROMOTIONAL, 2)
    first = s.reserve("u", OperationType.AI_VIDEO_STANDARD, "op-1", "key-1")
    retry = s.reserve("u", OperationType.AI_VIDEO_STANDARD, "op-1", "key-1")
    assert retry.id == first.id and sum(a.amount for a in first.allocation) == 3
    assert [a.funding_source for a in first.allocation] == [
        FundingSource.REWARDED_AD,
        FundingSource.PROMOTIONAL,
    ]


def test_consume_and_release_are_terminal_and_safe():
    s = CreditService()
    s.grant("u", FundingSource.FREE_ALLOWANCE, 1)
    r = s.reserve("u", OperationType.AI_PHOTO_STANDARD, "op-1", "key-1")
    assert s.consume(r.id, "exec-1").status == ReservationStatus.CONSUMED
    assert s.consume(r.id, "exec-1").status == ReservationStatus.CONSUMED
    try:
        s.release(r.id)
    except FundingError as e:
        assert str(e) == "CREDIT_RESERVATION_NOT_RELEASABLE"


def test_insufficient_funding_leaves_no_partial_reservation():
    s = CreditService()
    s.profiles[OperationType.AI_VIDEO_STANDARD] = s.profiles[
        OperationType.AI_VIDEO_STANDARD
    ].__class__(OperationType.AI_VIDEO_STANDARD, 1, 10)
    s.grant("u", FundingSource.FREE_ALLOWANCE, 1)
    try:
        s.reserve("u", OperationType.AI_VIDEO_STANDARD, "op-1", "key-1")
    except FundingError as e:
        assert str(e) == "FUNDING_REQUIRED"
    assert not s.reservations
    assert sum(g.reserved_amount for g in s.grants.values()) == 0


def test_concurrent_reservation_race_one_wins_without_negative_balance():
    service = CreditService()
    service.grant("u", FundingSource.FREE_ALLOWANCE, 1)
    service.materialize_allowance = lambda _user: None

    def attempt(index):
        try:
            reservation = service.reserve("u", OperationType.AI_PHOTO_STANDARD, f"op-{index}", f"key-{index}")
            return reservation.id
        except FundingError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=12) as pool:
        outcomes = list(pool.map(attempt, range(12)))
    assert sum(isinstance(value, str) and value.startswith("FUNDING_REQUIRED") for value in outcomes) == 11
    assert len({value for value in outcomes if not str(value).startswith("FUNDING_REQUIRED")}) == 1
    assert sum(grant.reserved_amount for grant in service.grants.values()) == 1
    service.audit()
