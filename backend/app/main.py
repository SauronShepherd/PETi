import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

from .advertising.google_ssv_verifier import GoogleSsvVerifier
from .advertising.service import RewardService
from .agent_runtime.execution import AgentExecutionService
from .agents.contracts import AgentOrchestrator
from .ai.providers import (
    AIProvider,
    FakeAIProvider,
    GeminiApiKeyPool,
    GeminiApiKeyTransport,
    GeminiProvider,
    VertexGeminiTransport,
    VertexGenAITransport,
)
from .analysis.firestore_repositories import (
    FirestoreAnalysisJobRepository,
    FirestoreAnalysisResultRepository,
)
from .analysis.queue import CloudTasksQueue, FakeTaskQueue, TaskQueue
from .analysis.service import AnalysisService
from .analytics import AnalyticsRecorder
from .api.agent_runs import router as agent_runs_router
from .api.errors import PetiError, error_handler
from .api.v1 import router as v1_router
from .assistant.grounding import GroundedAssistant
from .auth.task_auth import TaskAuthenticator
from .auth.verifiers import FirebaseIdentityVerifier, LocalTestIdentityVerifier
from .automation.rules import RuleEngine
from .care_advanced.domain import CareRecordsService
from .collaboration.service import CollaborationService
from .config import Environment, get_settings
from .credits.firestore_service import FirestoreEconomicStore
from .credits.service import CreditService
from .economics.policy import EconomicsPolicy
from .future.service import FutureService
from .infrastructure.firebase import create_firebase_auth, create_firebase_services
from .logging import configure_logging
from .media.firestore_metadata import FirestoreMediaMetadataStore
from .media.floci_storage import FlociObjectStorage
from .media.gcs_storage import GcsObjectStorage
from .media.retention import RetentionService
from .media.service import MediaService
from .operations.controls import RETENTION_CATEGORIES, AbuseGuard
from .operations.platform import FirestoreFeatureFlagStore, OperationsService
from .phase6 import Phase6Service, firebase_fcm_sender
from .phase6_firestore import FirestorePhase6Store
from .portability.service import PortabilityService
from .privacy.service import PrivacyService
from .records.vault import RecordVaultService
from .reports.service import WeeklyReportService
from .repositories.firestore import FirestoreAnimalRepository, FirestoreUserRepository
from .repositories.memory import (
    InMemoryAnimalRepository,
    InMemorySpeciesRepository,
    InMemoryUserRepository,
)
from .search.memory import MemoryService
from .search.service import SearchService
from .services.pets import PetService
from .specialists.service import SpecialistService
from .species.capabilities import CapabilityRegistry

configure_logging()
settings = get_settings()
app = FastAPI(title="PETi Cloud API", version="0.1.0")


def _web_origins(raw: str) -> list[str]:
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_web_origins(settings.web_allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)
def is_out_of_scope_route(path: str) -> bool:
    """Return true only for the explicitly unapproved research surfaces."""
    explicit = (
        "/v1/assistant", "/v1/collaboration", "/v1/portable-imports",
        "/v1/agent/runs", "/v1/search", "/v1/saved-searches",
    )
    if path.startswith(explicit):
        return True
    suffixes = (
        "/portable-export", "/shares", "/care-records", "/longitudinal-bundle",
        "/automation-rules", "/automation-suggestions", "/care-templates",
        "/members", "/invitations", "/collections", "/assistant/threads",
        "/assistant/grounded-answer", "/agent-sessions", "/agent-runs",
        "/agent/runs", "/observation-plans", "/memory", "/collaboration/memberships",
    )
    return any(path.endswith(s) or f"{s}/" in path for s in suffixes)


@app.middleware("http")
async def reject_unapproved_scope(request: Request, call_next: Callable[..., Awaitable[Response]]) -> Response:
    if settings.environment is not Environment.LOCAL and is_out_of_scope_route(request.url.path):
        return JSONResponse({"detail": "ROUTE_NOT_ENABLED"}, status_code=404)
    return await call_next(request)
app.state.settings = settings
app.add_exception_handler(PetiError, error_handler)  # type: ignore[arg-type]
if settings.storage_mode == "FIRESTORE_EMULATOR":
    from google.cloud import firestore  # type: ignore[attr-defined,import-untyped]

    if settings.firestore_emulator_host:
        import os

        os.environ["FIRESTORE_EMULATOR_HOST"] = settings.firestore_emulator_host
    firestore_client = firestore.Client(project="peti-local")
    import os

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from google.api_core.client_options import ClientOptions
    from google.cloud import storage  # type: ignore[attr-defined,import-untyped]
    from google.oauth2 import service_account

    local_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    local_pem = local_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    floci_credentials = service_account.Credentials.from_service_account_info(
        {
            "type": "service_account",
            "project_id": "peti-local",
            "private_key_id": "floci-local",
            "private_key": local_pem,
            "client_email": "peti@peti-local.iam.gserviceaccount.com",
            "client_id": "1",
            "token_uri": "http://127.0.0.1:4588/token",
        }
    )
    storage_client = storage.Client(
        project="peti-local",
        credentials=floci_credentials,
        client_options=ClientOptions(
            api_endpoint=os.getenv("STORAGE_EMULATOR_HOST", "http://127.0.0.1:4588")
        ),
    )
    app.state.identity_verifier = LocalTestIdentityVerifier()
    app.state.users = FirestoreUserRepository(firestore_client)
    app.state.animals = FirestoreAnimalRepository(firestore_client)
    app.state.firestore_client = firestore_client
    app.state.object_storage = FlociObjectStorage(storage_client)
elif settings.auth_mode == "FIREBASE":
    firebase_auth = create_firebase_auth(settings.firebase_project_id)
    app.state.identity_verifier = FirebaseIdentityVerifier(firebase_auth)
    if settings.storage_mode == "FIRESTORE":
        _, firestore_client = create_firebase_services(
            settings.firebase_project_id, settings.firestore_database_id
        )
        app.state.users = FirestoreUserRepository(firestore_client)
        app.state.animals = FirestoreAnimalRepository(firestore_client)
        app.state.firestore_client = firestore_client
        from google.cloud import storage  # type: ignore[attr-defined,import-untyped]

        app.state.object_storage = GcsObjectStorage(
            storage.Client(project=settings.project_id),
            settings.media_bucket or "",
        )
    else:
        # DEV smoke mode may use real Firebase identity with ephemeral data.
        # Persistent Firestore/GCS are enabled only when explicitly selected.
        app.state.users = InMemoryUserRepository()  # type: ignore[no-untyped-call]
        app.state.animals = InMemoryAnimalRepository()  # type: ignore[no-untyped-call]
else:
    app.state.identity_verifier = LocalTestIdentityVerifier()
    app.state.users = InMemoryUserRepository()  # type: ignore[no-untyped-call]
    app.state.animals = InMemoryAnimalRepository()  # type: ignore[no-untyped-call]
app.state.species = InMemorySpeciesRepository()  # type: ignore[no-untyped-call]
app.state.pets = PetService(app.state.animals, app.state.species)  # type: ignore[no-untyped-call]
app.state.economic_store = (
    FirestoreEconomicStore(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None
)
app.state.credits = CreditService(app.state.economic_store)
app.state.rewards = RewardService(
    app.state.credits,
    GoogleSsvVerifier(),
    store=app.state.economic_store,
)
app.state.abuse_guard = AbuseGuard()
app.state.retention_categories = RETENTION_CATEGORIES
app.state.media_metadata_store = (
    FirestoreMediaMetadataStore(getattr(app.state, "firestore_client", None))
    if hasattr(app.state, "firestore_client")
    else None
)
app.state.media = MediaService(
    app.state.pets,
    storage=getattr(app.state, "object_storage", None),
    bucket=settings.media_bucket or ("peti-local-media" if hasattr(app.state, "object_storage") else "local-media"),
    metadata_store=app.state.media_metadata_store,
)
app.state.retention = RetentionService(app.state.media)
analysis_job_repo = (
    FirestoreAnalysisJobRepository(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None
)
analysis_result_repo = (
    FirestoreAnalysisResultRepository(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None
)
provider: AIProvider = FakeAIProvider()
if settings.ai_provider == "GEMINI":
    if settings.gemini_api_keys:
        provider = GeminiProvider(
            settings.ai_model,
            GeminiApiKeyTransport(timeout_seconds=settings.provider_timeout_seconds),
            api_keys=GeminiApiKeyPool(settings.gemini_api_keys, settings.gemini_daily_limit_per_key),
            max_attempts=settings.gemini_max_attempts,
            backoff_seconds=settings.gemini_retry_backoff_seconds,
        )
    else:
        if not settings.project_id:
            raise ValueError("GEMINI provider requires PETI_PROJECT_ID")
        from google.auth import default as google_auth_default
        from google.auth.transport.requests import Request as GoogleAuthRequest

        credentials, _ = google_auth_default()

        def token_provider():
            if not credentials.valid or not credentials.token:
                credentials.refresh(GoogleAuthRequest())
            return credentials.token

        vertex_transport = (VertexGenAITransport(
            settings.project_id,
            settings.gemini_location or settings.tasks_location or "europe-west1",
            timeout_seconds=settings.provider_timeout_seconds,
        ) if settings.gemini_transport == "SDK" else VertexGeminiTransport(
            settings.project_id,
            settings.gemini_location or settings.tasks_location or "europe-west1",
            token_provider,
            timeout_seconds=settings.provider_timeout_seconds,
        ))
        provider = GeminiProvider(
            settings.ai_model,
            vertex_transport,
        )
if settings.environment is Environment.LOCAL:
    analysis_queue: TaskQueue = FakeTaskQueue()
else:
    from google.cloud import tasks_v2  # type: ignore[attr-defined,import-untyped]

    analysis_queue = CloudTasksQueue(
        tasks_v2.CloudTasksClient(),
        settings.tasks_project_id or settings.project_id or "",
        settings.tasks_location or "europe-west1",
        settings.analysis_queue_name,
        settings.analysis_worker_url or settings.worker_url or "",
        settings.analysis_task_service_account or "",
        settings.analysis_task_audience,
    )

app.state.analytics = AnalyticsRecorder()
app.state.operations = OperationsService(
    app.state.analytics,
    flag_store=FirestoreFeatureFlagStore(app.state.firestore_client)
    if hasattr(app.state, "firestore_client") else None,
    store=FirestorePhase6Store(app.state.firestore_client)
    if hasattr(app.state, "firestore_client") else None,
)
app.state.analysis = AnalysisService(
    app.state.pets,
    app.state.media,
    app.state.credits,
    analysis_queue,
    job_repository=analysis_job_repo,
    result_repository=analysis_result_repo,
    ai_enabled=settings.ai_enabled,
    provider_enabled=settings.ai_provider_enabled,
    model_enabled=settings.ai_model_enabled,
    possible_interpretations_enabled=settings.possible_interpretations_enabled,
    modality_flags={
        "IMAGE": settings.peti_check_image_enabled,
        "VIDEO": settings.peti_check_video_enabled,
        "AUDIO": settings.peti_check_audio_enabled,
        "DOCUMENT": False,
    },
    analytics=app.state.analytics,
    provider=provider,
    costs=app.state.operations.costs,
)
app.state.operations.apply_to_analysis(app.state.analysis)
app.state.phase6 = Phase6Service(
    FirestorePhase6Store(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None,
    analytics=app.state.analytics,
)
app.state.phase6_sender = None if settings.environment is Environment.LOCAL else firebase_fcm_sender
app.state.records = RecordVaultService(
    app.state.pets,
    app.state.media,
    store=FirestorePhase6Store(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None,
    phase6=app.state.phase6,
)
app.state.specialists = SpecialistService(
    app.state.pets,
    app.state.media,
    store=FirestorePhase6Store(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None,
    credits=app.state.credits,
)
app.state.reports = WeeklyReportService(
    app.state.pets,
    app.state.phase6,
    records=app.state.records,
    specialists=app.state.specialists,
    store=FirestorePhase6Store(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None,
)
app.state.memory = MemoryService(
    store=FirestorePhase6Store(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None,
)
app.state.privacy = PrivacyService(
    app.state.pets, app.state.media, app.state.phase6,
    records=app.state.records, specialists=app.state.specialists,
    reports=app.state.reports, users=app.state.users, credits=app.state.credits,
    operations=None, memory=app.state.memory,
    store=FirestorePhase6Store(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None,
)
app.state.future = FutureService(
    app.state.pets, app.state.phase6, records=app.state.records, reports=app.state.reports,
    store=FirestorePhase6Store(app.state.firestore_client) if hasattr(app.state, "firestore_client") else None,
)
app.state.economics = EconomicsPolicy()
app.state.analysis.economics_policy = app.state.economics
app.state.capabilities = CapabilityRegistry()
app.state.care_advanced = CareRecordsService(
    app.state.pets,
    store=FirestorePhase6Store(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None,
)
app.state.portability = PortabilityService(
    lambda owner, pet_id: app.state.privacy.export_pet(owner, pet_id),
    store=FirestorePhase6Store(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None,
)
app.state.automation = RuleEngine(
    store=FirestorePhase6Store(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None,
)
app.state.search = SearchService(lambda owner, pet_id: app.state.future.search(owner, "", pet_id))
app.state.assistant = GroundedAssistant(lambda owner, question, pet_id: app.state.future.search(owner, question, pet_id))
app.state.agents = AgentOrchestrator(
    store=FirestorePhase6Store(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None,
)
app.state.agent_execution = AgentExecutionService(app.state.agents, provider)
app.state.collaboration = CollaborationService(
    app.state.pets,
    store=FirestorePhase6Store(app.state.firestore_client)
    if hasattr(app.state, "firestore_client")
    else None,
)
app.state.privacy.care_advanced = app.state.care_advanced
app.state.privacy.collaboration = app.state.collaboration
app.state.privacy.future = app.state.future
app.state.privacy.portability = app.state.portability
app.state.privacy.attach_agents(app.state.agents)
app.state.privacy.attach_operations(app.state.operations)
app.state.specialists.release_flags = app.state.operations.flags
app.state.task_authenticator = TaskAuthenticator(
    settings.analysis_expected_service_account,
    settings.analysis_task_audience,
    settings.environment is Environment.LOCAL,
)
app.state.maintenance_task_authenticator = TaskAuthenticator(
    settings.maintenance_expected_service_account
    or settings.analysis_expected_service_account,
    settings.maintenance_task_audience or settings.analysis_task_audience,
    settings.environment is Environment.LOCAL,
)
app.include_router(v1_router)
app.include_router(agent_runs_router)


@app.middleware("http")
async def correlation(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    cid = request.headers.get("X-Correlation-ID") or str(uuid4())
    request.state.correlation_id = cid
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    response.headers["X-Response-Time-Ms"] = str(round((time.perf_counter() - started) * 1000, 2))
    return response


@app.get("/health/live", tags=["health"])
async def live() -> dict[str, str]:
    return {"status": "ok", "service": settings.service, "environment": settings.environment.value}


@app.get("/health/ready", tags=["health"])
async def ready() -> dict[str, str | bool]:
    return {
        "status": "ready",
        "environment": settings.environment.value,
        "dependencies_configured": True,
    }


@app.exception_handler(404)
async def not_found(request: Request, _: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "code": "NOT_FOUND",
            "message": "The requested resource was not found.",
            "correlation_id": request.state.correlation_id,
            "retryable": False,
        },
    )


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
    code = exc.detail if isinstance(exc.detail, str) else "REQUEST_FAILED"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": code,
            "message": "The request could not be completed.",
            "correlation_id": request.state.correlation_id,
            "retryable": False,
        },
    )
