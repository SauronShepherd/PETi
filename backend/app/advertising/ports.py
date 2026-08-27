from typing import Protocol


class RewardVerifier(Protocol):
    def verify(self, reward_token: str) -> bool: ...


class AdvertisingGateway(Protocol):
    """Only funding flows may depend on this port; ordinary UI must not."""

    def request_reward(self) -> str: ...
