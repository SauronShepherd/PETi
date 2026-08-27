from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class ActiveState(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass
class AnimalProfile:
    id: str
    owner_user_id: str
    species: str
    display_name: str
    active_state: ActiveState = ActiveState.ACTIVE
    avatar_media_id: str | None = None
    coat_color: str | None = None
    coat_pattern: str | None = None
    coat_length: str | None = None
    possible_breed_type: str | None = None
    life_stage_appearance: str | None = None
    morphology_description: str | None = None
    distinguishing_features: str | None = None
    profile_field_provenance: dict[str, str] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
