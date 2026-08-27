"""Deterministic reward verifier for local and CI flows.

It deliberately accepts only tokens explicitly issued by the fixture, so tests
cannot accidentally turn an arbitrary client string into a credit grant.
"""

from dataclasses import dataclass, field


@dataclass
class FakeRewardVerifier:
    valid_tokens: set[str] = field(default_factory=set)

    def issue(self, token: str) -> str:
        if not token:
            raise ValueError("REWARD_TOKEN_REQUIRED")
        self.valid_tokens.add(token)
        return token

    def verify(self, reward_token: str) -> bool:
        return bool(reward_token and reward_token in self.valid_tokens)
