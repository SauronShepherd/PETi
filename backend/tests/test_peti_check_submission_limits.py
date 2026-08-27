import pytest
from app.analysis.service import AnalysisError, AnalysisService
from app.credits.service import CreditService
from app.media.domain import MediaAsset, MediaStatus, MediaType
from app.media.service import MediaService
from app.repositories.memory import InMemoryAnimalRepository, InMemorySpeciesRepository
from app.services.pets import PetService


def _service():
    pets = PetService(InMemoryAnimalRepository(), InMemorySpeciesRepository())
    pet = pets.create("u", "Milo", "DOG", "pet-key")
    media = MediaService(pets)
    assets = []
    for index in range(6):
        asset = MediaAsset(
            f"m{index}",
            "u",
            MediaType.IMAGE,
            "ANALYSIS_SOURCE",
            "image/jpeg",
            "TRANSIENT_ANALYSIS",
            animal_id=pet.id,
            status=MediaStatus.READY,
        )
        media.assets[asset.id] = asset
        assets.append(asset.id)
    credits = CreditService()
    reservation = credits.reserve("u", "PETI_CHECK", "req", "key")
    return AnalysisService(pets, media, credits), pet.id, assets, reservation.id


def test_peti_check_rejects_more_than_five_media_items():
    service, pet_id, media_ids, reservation_id = _service()
    with pytest.raises(AnalysisError, match="PETI_CHECK_TOO_MANY_MEDIA_ITEMS"):
        service.create(
            "u", pet_id, "PETI_CHECK", media_ids, None, reservation_id, "submit-key"
        )


def test_peti_check_rejects_context_longer_than_five_hundred_characters():
    service, pet_id, media_ids, reservation_id = _service()
    with pytest.raises(AnalysisError, match="PETI_CHECK_CONTEXT_TOO_LONG"):
        service.create(
            "u",
            pet_id,
            "PETI_CHECK",
            media_ids[:1],
            "x" * 501,
            reservation_id,
            "submit-key",
        )
