import pytest
from app.assistant.grounding import GroundedAssistant


def test_grounded_assistant_filters_cross_pet_duplicate_and_empty_citations():
    assistant = GroundedAssistant(
        lambda owner, question, pet_id: [
            {"type": "RECORD", "id": "r1", "pet_id": pet_id, "title": "Vaccination"},
            {"type": "RECORD", "id": "r1", "pet_id": pet_id, "title": "Duplicate"},
            {"type": "RECORD", "id": "r2", "pet_id": "other-pet", "title": "Leak"},
            {"type": "", "id": "", "pet_id": pet_id, "title": "Invalid"},
        ]
    )
    answer = assistant.answer("owner-1", "pet-1", "vaccination")
    assert [(item["source_entity_type"], item["source_entity_id"]) for item in answer["citations"]] == [("RECORD", "r1")]
    assert answer["grounding_status"] == "GROUNDED"


@pytest.mark.parametrize("question", ["", "x" * 501])
def test_grounded_assistant_bounds_question_input(question):
    with pytest.raises(ValueError):
        GroundedAssistant(lambda *_: []).answer("owner-1", "pet-1", question)
