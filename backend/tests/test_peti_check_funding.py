from app.credits.domain import OperationType
from app.credits.service import CreditService, FundingError


def test_peti_check_has_server_authoritative_cost_profile():
    service = CreditService()
    service.grant("u", "FREE_ALLOWANCE", 1)
    quote = service.quote("u", OperationType.PETI_CHECK)
    assert quote["operation_type"] == OperationType.PETI_CHECK
    assert quote["required_credits"] == 1
    reservation = service.reserve("u", OperationType.PETI_CHECK, "check-1", "funding-key")
    assert reservation.operation_type == OperationType.PETI_CHECK


def test_peti_check_insufficient_funding_fails_before_reservation():
    service = CreditService()
    service.profiles[OperationType.PETI_CHECK] = service.profiles[
        OperationType.PETI_CHECK
    ].__class__(OperationType.PETI_CHECK, 1, 4)
    try:
        service.reserve("u", OperationType.PETI_CHECK, "check-1", "funding-key")
    except FundingError as exc:
        assert str(exc) == "FUNDING_REQUIRED"
    else:
        raise AssertionError("expected funding failure")
