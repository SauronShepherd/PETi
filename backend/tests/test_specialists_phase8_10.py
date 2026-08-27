from types import SimpleNamespace

import pytest
from app.domain.species import SpeciesRegistryEntry
from app.repositories.memory import InMemoryAnimalRepository
from app.services.pets import PetService
from app.specialists.service import SpecialistError, SpecialistService


class Pets:
    def get(self, owner, pet_id):
        if owner in {"user-a", "user-b"} and pet_id == "dog-1":
            return SimpleNamespace(id=pet_id, species="DOG")
        if owner == "user-a" and pet_id == "cat-1":
            return SimpleNamespace(id=pet_id, species="CAT")
        return None


class Media:
    def get_owned(self, owner, media_id):
        if owner in {"user-a", "user-b"} and media_id.startswith("image-"):
            return SimpleNamespace(status="READY", media_type="IMAGE")
        return None


def service(flags=None):
    return SpecialistService(Pets(), Media(), release_flags=flags or {})


def test_specialist_public_release_fails_closed_until_certificate_is_validated():
    flags = {
        "dog_dental_check_enabled": True,
        "dog_dental_check_public_enabled": True,
        "dog_dental_check_evaluation_certificate_id": "PENDING",
    }
    with pytest.raises(SpecialistError, match="DENTAL_CHECK_NOT_AVAILABLE"):
        service(flags)._validate_release("DOG_DENTAL_CHECK")


def test_specialist_public_release_fails_closed_when_certificate_is_missing():
    flags = {
        "dog_dental_check_enabled": True,
        "dog_dental_check_public_enabled": True,
    }
    with pytest.raises(SpecialistError, match="DENTAL_CHECK_NOT_AVAILABLE"):
        service(flags)._validate_release("DOG_DENTAL_CHECK")


def test_initial_scan_keeps_candidates_pending_and_filters_forbidden_claims():
    result = service().create("user-a", "dog-1", "DOG_INITIAL_SCAN", {
        "media_asset_ids": ["image-1"],
        "result": {
            "profile_candidates": [
                {"field_type": "COAT_LENGTH", "candidate_value": "medium"},
                {"field_type": "EXACT_AGE", "candidate_value": "5 years"},
                {"field_type": "COAT_COLOR", "candidate_value": "healthy black"},
            ]
        },
    })
    assert result.result["profile_candidates"] == [{"field_type": "COAT_LENGTH", "candidate_value": "medium"}]


def test_initial_scan_rejects_non_dog_and_review_is_explicit():
    specialist = service()
    with pytest.raises(SpecialistError, match="SPECIES_INVALID"):
        specialist.create("user-a", "cat-1", "DOG_INITIAL_SCAN", {"media_asset_ids": ["image-1"]})

    result = specialist.create("user-a", "dog-1", "DOG_INITIAL_SCAN", {
        "media_asset_ids": ["image-1"],
        "result": {"profile_candidates": [{"field_type": "COAT_LENGTH", "candidate_value": "short"}]},
    })
    candidate = specialist.candidates_for("user-a", result.id)[0]
    assert candidate.status == "PENDING_REVIEW"
    specialist.review_initial_candidate("user-a", candidate.id, "correct", "medium")
    assert candidate.status == "CORRECTED"
    assert candidate.reviewed_value == "medium"


def test_feces_fails_closed_and_escalates_safety_deterministically():
    specialist = service()
    with pytest.raises(SpecialistError, match="SAMPLE_NOT_FRESH"):
        specialist.create("user-a", "dog-1", "DOG_FECES_CHECK", {
            "media_asset_ids": ["image-1"],
            "capture_manifest": {"freshness_confirmation": "NOT_FRESH", "producer_confirmation": True},
        })

    result = specialist.create("user-a", "dog-1", "DOG_FECES_CHECK", {
        "media_asset_ids": ["image-1"],
        "capture_manifest": {"freshness_confirmation": "FRESH_BEFORE_DISPOSAL", "producer_confirmation": True},
        "result": {"visible_findings": [{"finding_type": "DARK_BLACK_TAR_LIKE", "state": "OBSERVED"}]},
    })
    assert result.result["safety"] == "URGENT_VETERINARY_CONTACT"


def test_feces_multi_dog_producer_must_be_confirmed():
    specialist = service()
    with pytest.raises(SpecialistError, match="FECES_CHECK_PRODUCER_UNCONFIRMED"):
        specialist.create("user-a", "dog-1", "DOG_FECES_CHECK", {
            "media_asset_ids": ["image-1"],
            "capture_manifest": {
                "freshness_confirmation": "FRESH_BEFORE_DISPOSAL",
                "producer_confirmation": True,
                "multi_dog_environment": True,
                "target_dog_confirmed": False,
            },
        })


def test_feces_fresh_red_blood_escalates_to_prompt_contact():
    specialist = service()
    result = specialist.create("user-a", "dog-1", "DOG_FECES_CHECK", {
        "media_asset_ids": ["image-1"],
        "capture_manifest": {"freshness_confirmation": "FRESH_BEFORE_DISPOSAL", "producer_confirmation": True},
        "result": {"visible_findings": [{"finding_type": "FRESH_RED_BLOOD_LIKE", "state": "OBSERVED"}]},
    })
    assert result.result["safety"] == "PROMPT_VETERINARY_CONTACT"


def test_feces_not_observed_worm_finding_cannot_claim_absence():
    specialist = service()
    result = specialist.create("user-a", "dog-1", "DOG_FECES_CHECK", {
        "media_asset_ids": ["image-1"],
        "capture_manifest": {"freshness_confirmation": "FRESH_BEFORE_DISPOSAL", "producer_confirmation": True},
        "result": {"visible_findings": [{
            "finding_type": "WORM_SEGMENT_LIKE", "state": "NOT_OBSERVED", "statement": "No worms are present.",
        }]},
    })
    finding = result.result["visible_findings"][0]
    assert "not observed" in finding["statement"].lower()
    assert "no worms are present" not in finding["statement"].lower()


def test_dental_finding_taxonomy_is_allowlisted():
    result = service().create("user-a", "dog-1", "DOG_DENTAL_CHECK", {
        "media_asset_ids": ["image-1"],
        "result": {"visible_findings": [
            {"finding_type": "GINGIVAL_REDNESS", "statement": "visible redness"},
            {"finding_type": "PERIODONTAL_STAGE", "statement": "stage 3"},
        ]},
    })
    assert [x["finding_type"] for x in result.result["visible_findings"]] == ["GINGIVAL_REDNESS"]


def test_body_check_filters_unknown_observations_and_keeps_safe_defaults():
    result = service().create("user-a", "dog-1", "DOG_BODY_CHECK", {
        "media_asset_ids": ["image-1"],
        "result": {
            "observations": [
                {"observation_type": "WAIST_DEFINITION_VISIBLE", "statement": "Visible waist."},
                {"observation_type": "DIAGNOSIS", "statement": "This proves disease."},
            ],
            "body_condition_category": "ROUNDED_APPEARANCE",
            "ai_weight_estimate": {"estimated_range": {"min": 10, "max": 12}},
        },
    })
    assert len(result.result["body_observations"]) == 1
    assert result.result["body_observations"][0]["observation_type"] == "WAIST_DEFINITION_VISIBLE"
    assert result.result["body_condition_category"] == "UNCERTAIN"
    assert result.result["ai_weight_estimate"] is None
    assert any("not a scale" in item for item in result.result["limitations"])


def test_body_check_flags_control_category_and_estimate_provenance():
    result = service({
        "dog_body_check_enabled": True,
        "dog_body_check_public_enabled": True,
        "dog_body_check_evaluation_certificate_id": "local-test-cert",
        "dog_body_condition_category_enabled": True,
        "dog_body_ai_weight_estimate_enabled": True,
    }).create("user-a", "dog-1", "DOG_BODY_CHECK", {
        "media_asset_ids": ["image-1"],
        "result": {
            "body_condition_category": "BALANCED_APPEARANCE",
            "ai_weight_estimate": {
                "estimated_value": 11.5,
                "unit": "KG",
                "confidence": "LOW",
            },
        },
    })
    assert result.result["body_condition_category"] == "BALANCED_APPEARANCE"
    assert result.result["ai_weight_estimate"]["source_class"] == "AI_ESTIMATED"
    assert any("not a measured weight" in item for item in result.result["ai_weight_estimate"]["limitations"])


def test_body_check_restricts_diagnostic_claims():
    result = SpecialistService._guardrail_result("DOG_BODY_CHECK", {
        "observations": [{"statement": "This diagnoses Cushing's disease."}],
    })
    assert "diagnoses" not in repr(result).lower()


def test_all_specialist_analysis_surfaces_are_owner_scoped():
    specialist = service()
    ids = []
    for analysis_type, body in (
        ("DOG_DENTAL_CHECK", {"result": {"visible_findings": []}}),
        ("DOG_FECES_CHECK", {
            "capture_manifest": {"freshness_confirmation": "FRESH_BEFORE_DISPOSAL", "producer_confirmation": True},
            "result": {},
        }),
        ("DOG_BODY_CHECK", {
            "capture_manifest": {"steps": [{"step_id": "SIDE_STANDING"}, {"step_id": "TOP_STANDING"}]},
            "result": {"observations": []},
        }),
    ):
        item = specialist.create("user-a", "dog-1", analysis_type, {"media_asset_ids": ["image-1"], **body})
        ids.append(item.id)

    for analysis_id in ids:
        with pytest.raises(SpecialistError, match="SPECIALIST_NOT_FOUND"):
            specialist.get("user-b", analysis_id)
        with pytest.raises(SpecialistError, match="SPECIALIST_NOT_FOUND"):
            specialist.delete("user-b", analysis_id)
        with pytest.raises(SpecialistError, match="SPECIALIST_NOT_FOUND"):
            specialist.comparison("user-b", analysis_id)


def test_initial_scan_review_updates_canonical_profile_with_provenance():
    animals = InMemoryAnimalRepository()
    species = type("Species", (), {
        "get_species": lambda self, code: SpeciesRegistryEntry(code, code.title(), True, True, "DOG-v1"),
        "get_capability_pack": lambda self, code: None,
    })()
    pets = PetService(animals, species)
    pet = pets.create("user-a", "Luna", "DOG", "pet-1")
    specialist = SpecialistService(pets, Media())
    analysis = specialist.create("user-a", pet.id, "DOG_INITIAL_SCAN", {
        "media_asset_ids": ["image-1"],
        "result": {"profile_candidates": [{"field_type": "COAT_COLOR", "candidate_value": "black"}]},
    })
    candidate = specialist.candidates_for("user-a", analysis.id)[0]
    specialist.review_initial_candidate("user-a", candidate.id, "confirm")
    assert pets.get("user-a", pet.id).coat_color == "black"
    assert pets.get("user-a", pet.id).profile_field_provenance["COAT_COLOR"] == "USER_CONFIRMED"


def test_initial_scan_review_uses_server_profile_for_conflicts_and_correct_provenance():
    animals = InMemoryAnimalRepository()
    species = type("Species", (), {
        "get_species": lambda self, code: SpeciesRegistryEntry(code, code.title(), True, True, "DOG-v1"),
        "get_capability_pack": lambda self, code: None,
    })()
    pets = PetService(animals, species)
    pet = pets.create("user-a", "Luna", "DOG", "pet-1")
    pet.coat_color = "white"
    animals.items[pet.id] = pet
    specialist = SpecialistService(pets, Media())
    analysis = specialist.create("user-a", pet.id, "DOG_INITIAL_SCAN", {
        "media_asset_ids": ["image-1"],
        "result": {"profile_candidates": [{"field_type": "COAT_COLOR", "candidate_value": "black"}]},
    })
    candidate = specialist.candidates_for("user-a", analysis.id)[0]
    with pytest.raises(SpecialistError, match="INITIAL_SCAN_PROFILE_CONFLICT"):
        specialist.review_initial_candidate("user-a", candidate.id, "confirm")
    specialist.review_initial_candidate("user-a", candidate.id, "correct", "brown")
    assert pets.get("user-a", pet.id).coat_color == "brown"
    assert pets.get("user-a", pet.id).profile_field_provenance["COAT_COLOR"] == "USER_CORRECTED"


def test_specialist_results_are_owner_scoped_for_read_list_and_delete():
    specialist = service()
    analysis = specialist.create("user-a", "dog-1", "DOG_DENTAL_CHECK", {
        "media_asset_ids": ["image-1"],
        "result": {"visible_findings": [{"finding_type": "GINGIVAL_REDNESS", "statement": "visible redness"}]},
    })
    with pytest.raises(SpecialistError, match="SPECIALIST_NOT_FOUND"):
        specialist.get("user-b", analysis.id)
    assert specialist.list("user-b", "dog-1", "DOG_DENTAL_CHECK") == []
    with pytest.raises(SpecialistError, match="SPECIALIST_NOT_FOUND"):
        specialist.delete("user-b", analysis.id)
    assert specialist.get("user-a", analysis.id).id == analysis.id


def test_initial_scan_candidates_are_owner_scoped_for_list_and_review():
    specialist = service()
    analysis = specialist.create("user-a", "dog-1", "DOG_INITIAL_SCAN", {
        "media_asset_ids": ["image-1"],
        "result": {"profile_candidates": [{"field_type": "COAT_COLOR", "candidate_value": "black"}]},
    })
    candidate = specialist.candidates_for("user-a", analysis.id)[0]
    with pytest.raises(SpecialistError, match="SPECIALIST_NOT_FOUND"):
        specialist.candidates_for("user-b", analysis.id)
    with pytest.raises(SpecialistError, match="INITIAL_SCAN_CANDIDATE_NOT_FOUND"):
        specialist.review_initial_candidate("user-b", candidate.id, "reject")


def test_body_comparison_is_owner_scoped():
    specialist = service({
        "dog_body_check_enabled": True,
        "dog_body_check_public_enabled": True,
        "dog_body_check_evaluation_certificate_id": "local-test-cert",
        "dog_body_longitudinal_compare_enabled": True,
    })
    analysis = specialist.create("user-a", "dog-1", "DOG_BODY_CHECK", {
        "media_asset_ids": ["image-1"],
        "result": {"body_condition_category": "BALANCED_APPEARANCE", "observations": []},
        "capture_manifest": {"steps": [{"step_id": "SIDE_STANDING"}, {"step_id": "TOP_STANDING"}]},
    })
    with pytest.raises(SpecialistError, match="SPECIALIST_NOT_FOUND"):
        specialist.comparison("user-b", analysis.id)
