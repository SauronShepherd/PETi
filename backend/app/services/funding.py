from dataclasses import dataclass

from ..domain.foundations import FundingDecision


@dataclass(frozen=True)
class FundingResolver:
    """Phase-0 seam: no allowance or ad policy is implemented here yet."""

    def resolve(self, *, available_credits: int, required_credits: int) -> FundingDecision:
        if available_credits >= required_credits:
            return FundingDecision.FUNDED
        return FundingDecision.REWARDED_AD_REQUIRED
