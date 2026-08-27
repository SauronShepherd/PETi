import pytest
from app.ai.providers.fake import FakeAIProvider
from app.analysis.service import AnalysisError, AnalysisService
from app.analytics import AnalyticsRecorder
from app.credits.service import CreditService
from app.media.domain import MediaAsset, MediaPurpose, MediaStatus, MediaType, RetentionClass
from app.media.service import MediaService
from app.operations.platform import OperationsService
from app.repositories.memory import InMemoryAnimalRepository, InMemorySpeciesRepository
from app.services.pets import PetService


class UnsafePlatformProvider(FakeAIProvider):
    def analyze(self, media, prompt="", user_context=None):
        return type(
            "Response",
            (),
            {
                "payload": {
                    "summary": "The pet is diagnosed with cancer.",
                    "observations": [{"text": "visible finding"}],
                    "evidence_quality": "MEDIUM",
                },
                "usage": type("Usage", (), {"__dict__": {"input_tokens": 1, "output_tokens": 1}})(),
                "provider": "FAKE",
                "model": "unsafe-test",
                "accepted": True,
            },
        )()


class SpecialistLeakProvider(FakeAIProvider):
    def analyze(self, prepared_media, prompt="", user_context=None):
        response = super().analyze(prepared_media, prompt, user_context)
        response.payload["observations"].append({"text": "periodontal stage 2 is confirmed"})
        return response


def test_fake_peti_check_vertical_slice_consumes_once_and_persists_result():
    pets = PetService(InMemoryAnimalRepository(), InMemorySpeciesRepository())
    pet = pets.create("u", "Milo", "DOG", "pet-key")
    media = MediaService(pets)
    media.assets["media-1"] = MediaAsset(
        "media-1", "u", MediaType.IMAGE, MediaPurpose.ANALYSIS_SOURCE, "image/jpeg",
        RetentionClass.TRANSIENT_ANALYSIS, animal_id=pet.id, status=MediaStatus.READY,
        )
    media.assets["media-1"].storage_object = "media/media-1/source"
    media.storage.put("local-media", "media/media-1/source", b"image", "image/jpeg")
    credits = CreditService()
    credits.grant("u", "FREE_ALLOWANCE", 1)
    reservation = credits.reserve("u", "PETI_CHECK", "request-1", "funding-key")
    analytics = AnalyticsRecorder()
    operations = OperationsService(analytics)
    service = AnalysisService(pets, media, credits, provider=FakeAIProvider(), analytics=analytics, costs=operations.costs)

    job = service.create("u", pet.id, "PETI_CHECK", ["media-1"], None, reservation.id, "submit-key")
    result = service.process_next()

    assert result is not None
    assert job.status.value == "COMPLETED"
    assert result.structured_payload["source_media_ids"] == ["media-1"]
    assert result.media_asset_ids == ["media-1"]
    assert result.provider_config_version == "1.0.0"
    assert "reference" not in str(result.__dict__)
    assert len(operations.costs.records) == 1
    assert next(iter(operations.costs.records.values())).analysis_id == job.id
    assert credits.reservations[reservation.id].status.value == "CONSUMED"
    service.process(job.id)
    events = [event["event"] for event in analytics.events]
    assert events.count("check_started") == 1
    assert events.count("check_completed") == 1
    assert events.count("check_safety_state") == 1


def test_possible_interpretations_server_flag_gates_output():
    pets = PetService(InMemoryAnimalRepository(), InMemorySpeciesRepository())
    pet = pets.create("u", "Milo", "DOG", "pet-key-flag")
    media = MediaService(pets)
    media.assets["media-flag"] = MediaAsset(
        "media-flag", "u", MediaType.IMAGE, MediaPurpose.ANALYSIS_SOURCE, "image/jpeg",
        RetentionClass.TRANSIENT_ANALYSIS, animal_id=pet.id, status=MediaStatus.READY,
        )
    media.assets["media-flag"].storage_object = "media/media-flag/source"
    media.storage.put("local-media", "media/media-flag/source", b"image", "image/jpeg")
    credits = CreditService()
    credits.grant("u", "FREE_ALLOWANCE", 1)
    reservation = credits.reserve("u", "PETI_CHECK", "request-flag", "funding-flag")
    service = AnalysisService(
        pets, media, credits, provider=FakeAIProvider(), possible_interpretations_enabled=False
    )
    job = service.create("u", pet.id, "PETI_CHECK", ["media-flag"], None, reservation.id, "submit-flag")
    result = service.process(job.id)
    assert result.structured_payload["possible_interpretations"] == []


def test_generic_analysis_applies_semantic_guardrails():
    pets = PetService(InMemoryAnimalRepository(), InMemorySpeciesRepository())
    pet = pets.create("u", "Milo", "DOG", "pet-key-generic-guardrail")
    media = MediaService(pets)
    media.assets["media-generic-guardrail"] = MediaAsset(
        "media-generic-guardrail", "u", MediaType.IMAGE, MediaPurpose.ANALYSIS_SOURCE,
        "image/jpeg", RetentionClass.TRANSIENT_ANALYSIS, animal_id=pet.id, status=MediaStatus.READY,
        )
    media.assets["media-generic-guardrail"].storage_object = "media/media-generic-guardrail/source"
    media.storage.put("local-media", "media/media-generic-guardrail/source", b"image", "image/jpeg")
    credits = CreditService()
    credits.grant("u", "FREE_ALLOWANCE", 1)
    reservation = credits.reserve("u", "AI_PHOTO_STANDARD", "request-generic", "funding-generic")
    service = AnalysisService(pets, media, credits, provider=UnsafePlatformProvider())
    job = service.create(
        "u", pet.id, "PLATFORM_MULTIMODAL_SMOKE", ["media-generic-guardrail"],
        None, reservation.id, "submit-generic-guardrail",
    )

    with pytest.raises(AnalysisError, match="AI_SEMANTIC_GUARDRAIL_VIOLATION"):
        service.process(job.id)


def test_media_failure_before_provider_releases_reserved_credit():
    pets = PetService(InMemoryAnimalRepository(), InMemorySpeciesRepository())
    pet = pets.create("u", "Milo", "DOG", "pet-key-release-media")
    media = MediaService(pets)
    asset, session = media.create_session(
        "u", pet.id, MediaType.IMAGE, MediaPurpose.ANALYSIS_SOURCE,
        "image/jpeg", 10, RetentionClass.TRANSIENT_ANALYSIS, "release-media",
    )
    media.storage.put(asset.storage_bucket, asset.storage_object, b"abc", "image/jpeg")
    media.finalize("u", asset.id, session.id)
    asset.status = MediaStatus.DELETED
    credits = CreditService()
    reservation = credits.reserve("u", "PETI_CHECK", "request-release", "funding-release")
    service = AnalysisService(pets, media, credits, provider=FakeAIProvider())
    job = service.create("u", pet.id, "PETI_CHECK", [asset.id], None, reservation.id, "submit-release")
    with pytest.raises(AnalysisError, match="MEDIA_AI_SOURCE_UNAVAILABLE"):
        service.process(job.id)
    assert credits.reservations[reservation.id].status.value == "RELEASED"


def test_peti_check_pipeline_rejects_specialist_shaped_payload():
    pets = PetService(InMemoryAnimalRepository(), InMemorySpeciesRepository())
    pet = pets.create("u", "Milo", "DOG", "pet-key-specialist-leak")
    media = MediaService(pets)
    media.assets["media-specialist-leak"] = MediaAsset(
        "media-specialist-leak", "u", MediaType.IMAGE, MediaPurpose.ANALYSIS_SOURCE,
        "image/jpeg", RetentionClass.TRANSIENT_ANALYSIS, animal_id=pet.id, status=MediaStatus.READY,
        )
    media.assets["media-specialist-leak"].storage_object = "media/media-specialist-leak/source"
    media.storage.put("local-media", "media/media-specialist-leak/source", b"image", "image/jpeg")
    credits = CreditService()
    credits.grant("u", "FREE_ALLOWANCE", 1)
    reservation = credits.reserve("u", "PETI_CHECK", "request-specialist-leak", "funding-specialist-leak")
    service = AnalysisService(pets, media, credits, provider=SpecialistLeakProvider())
    job = service.create("u", pet.id, "PETI_CHECK", ["media-specialist-leak"], None, reservation.id, "submit-specialist-leak")
    with pytest.raises(AnalysisError, match="AI_SEMANTIC_GUARDRAIL_VIOLATION"):
        service.process(job.id)
