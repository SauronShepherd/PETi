from app.ai.providers.fake import FakeAIProvider
from app.analysis.service import AnalysisService
from app.config.settings import Settings
from app.credits.service import CreditService
from app.economics.policy import EconomicsPolicy
from app.media.domain import MediaAsset, MediaPurpose, MediaStatus, MediaType, RetentionClass
from app.media.service import MediaService
from app.operations.platform import OperationsService
from app.repositories.memory import InMemoryAnimalRepository, InMemorySpeciesRepository
from app.services.pets import PetService


def test_analysis_service_honors_server_ai_kill_switch():
    pets = PetService(InMemoryAnimalRepository(), InMemorySpeciesRepository())
    pet = pets.create("u", "Milo", "DOG", "kill-switch-pet")
    media = MediaService(pets)
    media.assets["m"] = MediaAsset(
        "m", "u", MediaType.IMAGE, MediaPurpose.ANALYSIS_SOURCE, "image/jpeg",
        RetentionClass.TRANSIENT_ANALYSIS, animal_id=pet.id, status=MediaStatus.READY,
    )
    credits = CreditService()
    credits.grant("u", "FREE_ALLOWANCE", 1)
    reservation = credits.reserve("u", "PETI_CHECK", "kill-switch-request", "kill-switch-funding")
    service = AnalysisService(pets, media, credits, ai_enabled=False)
    job = service.create("u", pet.id, "PETI_CHECK", ["m"], None, reservation.id, "kill-switch-submit")
    assert service.process(job.id) is None
    assert str(job.status) == "FAILED_FINAL"
    assert job.failed_at is not None
    assert str(credits.reservations[reservation.id].status) == "RELEASED"


def test_provider_and_model_kill_switches_are_server_configured():
    service = AnalysisService.__new__(AnalysisService)
    service.provider_enabled = False
    service.model_enabled = False
    settings = Settings(ai_provider_enabled=False, ai_model_enabled=False)
    assert not settings.ai_provider_enabled and not settings.ai_model_enabled
    assert not service.provider_enabled and not service.model_enabled


def test_ai_kill_switch_does_not_block_historical_result_reads():
    pets = PetService(InMemoryAnimalRepository(), InMemorySpeciesRepository())
    pet = pets.create("u", "Milo", "DOG", "historical-pet")
    media = MediaService(pets)
    media.assets["m"] = MediaAsset(
        "m", "u", MediaType.IMAGE, MediaPurpose.ANALYSIS_SOURCE, "image/jpeg",
        RetentionClass.TRANSIENT_ANALYSIS, animal_id=pet.id, status=MediaStatus.READY,
    )
    credits = CreditService()
    credits.grant("u", "FREE_ALLOWANCE", 1)
    reservation = credits.reserve("u", "PETI_CHECK", "historical-request", "historical-funding")
    service = AnalysisService(pets, media, credits, ai_enabled=False)
    job = service.create("u", pet.id, "PETI_CHECK", ["m"], None, reservation.id, "historical-submit")
    sentinel = object()
    job.status = "COMPLETED"
    service.results[job.id] = sentinel
    assert service.process(job.id) is sentinel


def test_economics_policy_blocks_new_analysis_and_releases_funding():
    pets = PetService(InMemoryAnimalRepository(), InMemorySpeciesRepository())
    pet = pets.create("u", "Milo", "DOG", "economics-kill-pet")
    media = MediaService(pets)
    media.assets["m-economics"] = MediaAsset(
        "m-economics", "u", MediaType.IMAGE, MediaPurpose.ANALYSIS_SOURCE, "image/jpeg",
        RetentionClass.TRANSIENT_ANALYSIS, animal_id=pet.id, status=MediaStatus.READY,
    )
    credits = CreditService()
    credits.grant("u", "FREE_ALLOWANCE", 1)
    reservation = credits.reserve("u", "PETI_CHECK", "economics-request", "economics-funding")
    policy = EconomicsPolicy()
    policy.kill_switch = True
    service = AnalysisService(pets, media, credits, economics_policy=policy)
    job = service.create("u", pet.id, "PETI_CHECK", ["m-economics"], None, reservation.id, "economics-submit")

    assert service.process(job.id) is None
    assert str(job.status) == "FAILED_FINAL"
    assert job.failed_at is not None
    assert str(credits.reservations[reservation.id].status) == "RELEASED"


def test_global_ai_kill_switch_requires_admin_and_changes_runtime_state():
    operations = OperationsService()
    try:
        operations.set_ai_global_kill_switch(True, "CUSTOMER")
    except PermissionError as exc:
        assert str(exc) == "OPERATIONS_ADMIN_REQUIRED"
    else:
        raise AssertionError("non-admin must not change AI kill switch")
    assert operations.set_ai_global_kill_switch(True, "ADMIN") is True
    assert operations.flags["ai_global_kill_switch"] is True
    assert operations.set_ai_global_kill_switch(False, "ADMIN") is False


def test_global_kill_switch_restore_preserves_static_ai_baseline():
    service = AnalysisService.__new__(AnalysisService)
    service.configured_ai_enabled = False
    service.ai_enabled = False
    assert service.set_global_kill_switch(True) is False
    assert service.set_global_kill_switch(False) is False


def test_kill_switch_failure_state_is_persisted_for_restart():
    from app.analysis.domain import AnalysisJob, AnalysisStatus
    from app.analysis.repositories import InMemoryAnalysisJobRepository

    jobs = InMemoryAnalysisJobRepository()
    job = AnalysisJob("job-kill-persist", "owner", "pet", "DOG", "PETI_CHECK", [], "prompt", "schema", "funding")
    jobs.save(job)
    service = AnalysisService(
        None,
        None,
        type("Credits", (), {"release": lambda self, *_: None})(),
        provider=FakeAIProvider(),
        job_repository=jobs,
        ai_enabled=False,
    )

    assert service.process(job.id) is None
    persisted = jobs.get(job.id)
    assert persisted.status == AnalysisStatus.FAILED_FINAL
    assert persisted.last_error_code == "AI_DISABLED"
    assert persisted.failed_at is not None


def test_scoped_runtime_kill_switches_are_validated_and_separated():
    service = AnalysisService.__new__(AnalysisService)
    service.provider_kill_switches = {}
    service.model_kill_switches = {}
    service.species_kill_switches = {}
    assert service.set_runtime_kill_switch("provider", "GEMINI", True) is True
    assert service.provider_kill_switches == {"GEMINI": True}
    assert service.set_runtime_kill_switch("model", "gemini-2.5", True) is True
    assert service.set_runtime_kill_switch("species", "DOG", True) is True


def test_scoped_runtime_kill_switch_rejects_truthy_string_values():
    service = AnalysisService.__new__(AnalysisService)
    service.provider_kill_switches = {}
    service.model_kill_switches = {}
    service.species_kill_switches = {}

    try:
        service.set_runtime_kill_switch("provider", "GEMINI", "false")
    except TypeError as exc:
        assert str(exc) == "AI_KILL_SWITCH_VALUE_INVALID"
    else:
        raise AssertionError("truthy string must not enable a kill switch")
    assert service.provider_kill_switches == {}


def test_emergency_variable_cost_switch_requires_admin_and_fails_closed():
    operations = OperationsService()
    try:
        operations.set_variable_cost_intake(False, "CUSTOMER")
    except PermissionError as exc:
        assert str(exc) == "OPERATIONS_ADMIN_REQUIRED"
    else:
        raise AssertionError("non-admin changed emergency variable-cost switch")
    assert operations.set_variable_cost_intake(False, "ADMIN") is False
    assert not operations.variable_cost_intake_allowed()
    decision = operations.request_variable_cost_operation("PETI_CHECK", 1)
    assert not decision.allowed and decision.reason == "VARIABLE_COST_INTAKE_DISABLED"


def test_http_variable_cost_switch_requires_admin_and_validates_payload():
    from uuid import uuid4

    from app.domain.users import UserRole
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    customer = "ops-customer-http-" + uuid4().hex
    admin = "ops-admin-http-" + uuid4().hex
    app.state.users.provision(admin, UserRole.ADMIN)
    customer_headers = {"Authorization": f"Bearer local-test:{customer}"}
    admin_headers = {"Authorization": f"Bearer local-test:{admin}"}

    denied = client.post("/v1/internal/ops/feature-flags/variable-cost-intake", headers=customer_headers, json={"enabled": False})
    assert denied.status_code == 403
    disabled = client.post("/v1/internal/ops/feature-flags/variable-cost-intake", headers=admin_headers, json={"enabled": False})
    assert disabled.status_code == 200 and disabled.json()["variable_cost_intake_enabled"] is False
    enabled = client.post("/v1/internal/ops/feature-flags/variable-cost-intake", headers=admin_headers, json={"enabled": True})
    assert enabled.status_code == 200 and enabled.json()["variable_cost_intake_enabled"] is True
    invalid = client.post("/v1/internal/ops/feature-flags/variable-cost-intake", headers=admin_headers, json={"enabled": "false"})
    assert invalid.status_code == 422
