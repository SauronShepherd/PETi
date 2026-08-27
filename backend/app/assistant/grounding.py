from dataclasses import asdict, dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class Citation:
    source_entity_type: str
    source_entity_id: str
    pet_id: str
    excerpt: str


class GroundedAssistant:
    def __init__(self, search): self.search = search

    def answer(self, owner: str, pet_id: str, question: str) -> dict:
        lowered = question.lower().strip()
        if not lowered: raise ValueError("ASSISTANT_QUESTION_REQUIRED")
        if len(lowered) > 500: raise ValueError("ASSISTANT_QUESTION_TOO_LONG")
        hits = self.search(owner, question, pet_id) or []
        citations = []
        seen: set[tuple[str, str]] = set()
        for hit in hits:
            entity_type, entity_id = str(hit.get("type", "")), str(hit.get("id", ""))
            hit_pet_id = str(hit.get("pet_id", pet_id))
            key = (entity_type, entity_id)
            if not entity_type or not entity_id or hit_pet_id != pet_id or key in seen:
                continue
            seen.add(key)
            citations.append(Citation(entity_type, entity_id, pet_id, str(hit.get("title", ""))[:500]))
            if len(citations) == 8:
                break
        medical = any(word in lowered for word in ("diagnose", "what disease", "prescribe", "dose", "emergency"))
        if medical:
            text = "I can point to recorded PETi history, but I cannot diagnose, prescribe, or determine an emergency from history alone. Contact a veterinarian for clinical advice."
            answer_type = "SAFETY_REDIRECT"
        elif citations:
            text = "I found matching PETi records. Open the cited sources to review the recorded history; this summary does not add facts beyond them."
            answer_type = "GROUNDED_SUMMARY"
        else:
            text = "I could not find a matching PETi source, so I cannot provide a factual history answer."
            answer_type = "INSUFFICIENT_EVIDENCE"
        return {"schema_version": "1.0.0", "answer_type": answer_type, "text": text, "claims": [], "citations": [asdict(x) for x in citations], "generated_at": datetime.now(UTC).isoformat(), "grounding_status": "GROUNDED" if citations else "NO_SOURCE"}
