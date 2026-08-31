from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class Experiment:
    id: str
    name: str
    variants: tuple[dict[str, str], ...]
    allocation_basis_points: int
    status: str = "DRAFT"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        if len(self.variants) < 2 or not 0 <= self.allocation_basis_points <= 10_000:
            raise ValueError("LAB_EXPERIMENT_INVALID")


class ExperimentRegistry:
    """Read-only P0 registry; assignment/promotion deliberately remains disabled."""
    def __init__(self) -> None: self._items: dict[str, Experiment] = {}
    def register(self, item: Experiment) -> None:
        if item.status != "DRAFT": raise ValueError("LAB_EXPERIMENT_MUTATION_DISABLED")
        self._items.setdefault(item.id, item)
    def list(self) -> list[Experiment]: return sorted(self._items.values(), key=lambda item: item.id)
