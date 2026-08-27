from app.specialists.service import SpecialistService


def test_initial_scan_candidate_provenance_tracks_user_decision():
    service = SpecialistService.__new__(SpecialistService)
    service.candidates = {}
    service.candidate_reviews = []
    service.analyses = {}
    service.clock = lambda: __import__("datetime").datetime.now(__import__("datetime").UTC)
    service.store = None
    service.release_flags = {}
    service.pets = type("Pets", (), {"get": lambda self, owner, pet_id: SimpleNamespace(species="DOG")})()
    # Use the normal candidate factory with a minimal analysis fixture.
    from types import SimpleNamespace
    analysis = SimpleNamespace(id="a", owner_user_id="u", animal_id="p")
    service._create_initial_candidates(analysis, [{"field_type": "COAT_COLOR", "candidate_value": "black"}])
    item = next(iter(service.candidates.values()))
    assert item.provenance_status == "AI_SUGGESTED"
    service.review_initial_candidate("u", item.id, "confirm")
    assert item.provenance_status == "USER_CONFIRMED"
