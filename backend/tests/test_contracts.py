from app.domain.foundations import (
    CloudCreditAccount,
    CloudCreditLedgerEntry,
    FundingSource,
    LedgerDirection,
)
from app.services.funding import FundingResolver


def test_credit_and_funding_boundaries_are_server_side():
    account = CloudCreditAccount("acct-1", 2)
    entry = CloudCreditLedgerEntry(
        "entry-1", account.account_id, LedgerDirection.GRANT, 2, FundingSource.PROMOTIONAL
    )
    assert entry.account_id == account.account_id
    assert FundingResolver().resolve(available_credits=2, required_credits=1).value == "FUNDED"
    assert (
        FundingResolver().resolve(available_credits=0, required_credits=1).value
        == "REWARDED_AD_REQUIRED"
    )
