from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class PetMembership:
    owner_user_id: str
    animal_id: str
    member_user_id: str
    role: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "ACTIVE"


@dataclass
class PetInvitation:
    owner_user_id: str
    animal_id: str
    invitee: str
    role: str
    token_digest: str
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class PetCollaborationActivity:
    animal_id: str
    actor_user_id: str
    event_type: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
