from app.specialists.service import SpecialistService


def test_feces_guardrail_catches_dehydration_and_parasite_variants():
    result = SpecialistService._guardrail_result("DOG_FECES_CHECK", {
        "summary": "dehydration is likely; parasites are absent",
        "observations": ["possible giardia"],
    })
    assert result["guardrail_status"] == "RESTRICTED"
    assert "dehydration" not in repr(result).lower()


def test_body_guardrail_catches_natural_language_obesity_variant():
    result = SpecialistService._guardrail_result("DOG_BODY_CHECK", {"summary": "obesity is confirmed"})
    assert result["guardrail_status"] == "RESTRICTED"


def test_feces_guardrail_catches_named_worm_species_and_dehydration():
    result = SpecialistService._guardrail_result(
        "DOG_FECES_CHECK", {"summary": "roundworm identified; dehydration confirmed"}
    )
    assert result["guardrail_status"] == "RESTRICTED"
    assert "roundworm" not in repr(result).lower()


def test_body_guardrail_catches_unlisted_diagnosis_language_and_breed_certainty():
    result = SpecialistService._guardrail_result(
        "DOG_BODY_CHECK", {"summary": "definitely a purebred shape; diagnosis is clear"}
    )
    assert result["guardrail_status"] == "RESTRICTED"
    assert "purebred" not in repr(result).lower()


def test_initial_scan_rejects_breed_certainty_language_in_candidate_text():
    result = SpecialistService._normalize_initial_result({
        "profile_candidates": [
            {"field_type": "POSSIBLE_BREED_TYPE", "candidate_value": "definitely a Labrador"},
            {"field_type": "POSSIBLE_BREED_TYPE", "candidate_value": "looks possibly like a retriever"},
        ],
    })
    assert [x["candidate_value"] for x in result["profile_candidates"]] == ["looks possibly like a retriever"]
    assert result["guardrail_status"] == "RESTRICTED"
