"""Typed, owner-scoped context source adapters.

Adapters keep persistence details out of the broker and make the data boundary
explicit for every released capability.
"""
from dataclasses import dataclass
from typing import Protocol


class ContextSource(Protocol):
    category: str

    def load(self, owner_user_id: str, pet_id: str) -> list[dict]: ...


@dataclass(frozen=True)
class _Source:
    category: str
    loader: object

    def load(self, owner_user_id: str, pet_id: str) -> list[dict]:
        rows = self.loader(owner_user_id, pet_id)
        return [dict(row) for row in rows if row.get("owner_user_id") == owner_user_id and row.get("pet_id") == pet_id]


class PetProfileContextSource(_Source):
    def __init__(self, loader): super().__init__("PET_PROFILE", loader)


class CurrentMediaContextSource(_Source):
    def __init__(self, loader): super().__init__("CURRENT_MEDIA", loader)


class SpecialistRecordContextSource(_Source):
    def __init__(self, loader): super().__init__("SPECIALIST_RECORDS", loader)


class PriorCandidateContextSource(_Source):
    def __init__(self, loader): super().__init__("PRIOR_CANDIDATES", loader)
