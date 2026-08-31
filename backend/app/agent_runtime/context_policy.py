from dataclasses import dataclass


@dataclass(frozen=True)
class ContextPolicy:
    policy_id: str
    capability_id: str
    allowed_categories: frozenset[str]
    max_items: int = 50

    def permits(self, category: str) -> bool:
        return category in self.allowed_categories
