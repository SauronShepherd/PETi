from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class ConversationThread:
    owner_user_id: str
    pet_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "ACTIVE"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ConversationMessage:
    thread_id: str
    actor: str
    text: str
    citations: list[dict] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    entity_type: str
    entity_id: str
    pet_id: str
    excerpt: str


@dataclass
class EvidenceBundle:
    question: str
    animal: str
    items: list[EvidenceItem] = field(default_factory=list)


class CitationValidator:
    def validate(self, claims, citations):
        allowed = {(x.entity_type, x.entity_id) for x in citations}
        return all(set(claim.get("citation_keys", [])) <= allowed for claim in claims)


@dataclass
class GroundedPetHistoryAnswerV1:
    answer_type: str
    answer_text: str
    citations: list[dict] = field(default_factory=list)
    schema_version: str = "1.0.0"


class PetHistoryAssistantSafetyPolicy:
    prohibited = ("diagnose", "prescribe", "invent", "reassure_without_source", "web_medical_retrieval")
    def classify(self, question: str):
        lowered = question.lower()
        return "SAFETY_REDIRECT" if any(x in lowered for x in ("diagnose", "prescribe", "emergency", "dose")) else "HISTORY_QUERY"
