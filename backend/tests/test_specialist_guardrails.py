from app.specialists.service import SpecialistService


def test_dental_guardrail_filters_natural_language_and_underscore_claims():
    result = SpecialistService._guardrail_result("DOG_DENTAL_CHECK", {
        "statement": "periodontal stage 2 and bone-loss are confirmed",
        "observations": ["pocket depth is 4mm"],
        "visible_findings": [{"statement": "root damage and pulp vitality assessed"}],
        "recommended_actions": ["use antibiotic dose 5mg"],
    })
    serialized = repr(result).lower()
    assert "periodontal stage" not in serialized
    assert "pocket depth" not in serialized
    assert "root damage" not in serialized
    assert "antibiotic" not in serialized
    assert result["guardrail_status"] == "RESTRICTED"


def test_dental_guardrail_keeps_safe_visible_observation():
    result = SpecialistService._guardrail_result("DOG_DENTAL_CHECK", {
        "visible_findings": [{"statement": "A visible calculus-like deposit is present."}],
    })
    assert result["visible_findings"]
    assert result["visible_findings"][0]["statement"].startswith("A visible")


def test_dental_guardrail_blocks_absence_and_reordered_stage_claims():
    result = SpecialistService._guardrail_result("DOG_DENTAL_CHECK", {
        "areas_not_assessed": ["No dental disease is present."],
        "limitations": ["Stage 2 periodontal disease is confirmed."],
    })
    assert result["areas_not_assessed"] == []
    assert result["limitations"] == ["Provider language was filtered through the specialist safety guardrail."]
    assert result["guardrail_status"] == "RESTRICTED"


def test_dental_guardrail_blocks_abscess_claims():
    result = SpecialistService._guardrail_result("DOG_DENTAL_CHECK", {
        "visible_findings": [{"statement": "A dental abscess is confirmed."}],
    })
    assert "abscess" not in repr(result).lower()
    assert result["visible_findings"] == []


def test_dental_safety_escalates_owner_or_model_urgent_inputs():
    assert SpecialistService._dental_safety(
        {"owner_context": ["DIFFICULTY_BREATHING_REPORTED"]}, {"visible_findings": []}
    ) == "URGENT_VETERINARY_CONTACT"
    assert SpecialistService._dental_safety(
        {}, {"red_flags": ["MARKED_SWELLING_VISIBLE"]}
    ) == "PROMPT_VETERINARY_CONTACT"


def test_dental_safety_never_downgrades_visible_findings_or_low_evidence():
    assert SpecialistService._dental_safety(
        {}, {"visible_findings": [{"statement": "deposit"}], "evidence_quality": "GOOD"}
    ) == "PROFESSIONAL_REVIEW_RECOMMENDED"
    assert SpecialistService._dental_safety(
        {}, {"visible_findings": [], "evidence_quality": "INSUFFICIENT"}
    ) == "MONITOR"
