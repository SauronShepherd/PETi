from app.agent_runtime.longitudinal_selector import select_compatible_candidates


def test_selector_is_same_pet_and_schema_compatible_only():
    current = {"pet_id": "dog-1", "modality": "FECES", "taxonomy_version": "v1"}
    candidates = [
        {"id": "ok", "pet_id": "dog-1", "modality": "FECES", "taxonomy_version": "v1", "evidence_quality": "GOOD"},
        {"id": "other-dog", "pet_id": "dog-2", "modality": "FECES", "taxonomy_version": "v1", "evidence_quality": "GOOD"},
        {"id": "bad-quality", "pet_id": "dog-1", "modality": "FECES", "taxonomy_version": "v1", "evidence_quality": "INSUFFICIENT"},
    ]
    assert [x["id"] for x in select_compatible_candidates(current, candidates)] == ["ok"]
