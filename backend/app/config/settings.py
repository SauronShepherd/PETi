from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "LOCAL"
    DEV = "DEV"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PETI_", env_file=".env", extra="ignore")
    environment: Environment = Environment.LOCAL
    project_id: str | None = None
    firestore_database: str | None = None
    media_bucket: str | None = None
    task_queue: str | None = None
    worker_url: str | None = None
    tasks_project_id: str | None = None
    tasks_location: str | None = None
    analysis_queue_name: str = "analysis"
    analysis_worker_url: str | None = None
    analysis_task_service_account: str | None = None
    analysis_task_audience: str | None = None
    analysis_expected_service_account: str | None = None
    maintenance_task_audience: str | None = None
    maintenance_expected_service_account: str | None = None
    max_task_attempts: int = 5
    task_dispatch_deadline_seconds: int = 300
    ai_enabled: bool = True
    ai_provider_enabled: bool = True
    ai_model_enabled: bool = True
    peti_check_enabled: bool = False
    peti_check_image_enabled: bool = True
    peti_check_video_enabled: bool = False
    peti_check_audio_enabled: bool = False
    possible_interpretations_enabled: bool = True
    ai_provider: str = "FAKE"
    ai_model: str = "fake-platform-smoke-v1"
    gemini_location: str | None = None
    provider_timeout_seconds: int = 90
    gemini_api_keys: str | None = None
    gemini_transport: str = "SDK"
    gemini_max_attempts: int = 3
    gemini_retry_backoff_seconds: float = 0.25
    gemini_daily_limit_per_key: int = 20
    service: str = "peti-api"
    deployment_revision: str = "local"
    auth_mode: str = "LOCAL_TEST"
    storage_mode: str = "MEMORY"
    firestore_emulator_host: str | None = None
    firebase_project_id: str | None = None
    web_allowed_origins: str = "http://localhost:4173,http://127.0.0.1:4173"
    firestore_project_id: str | None = None
    firestore_database_id: str | None = None
    media_bucket_region: str = "europe-west1"
    upload_url_ttl_seconds: int = 900
    download_url_ttl_seconds: int = 300
    simple_upload_max_bytes: int = 5_000_000
    resumable_upload_min_bytes: int = 5_000_000
    max_image_bytes: int = 20_000_000
    max_video_bytes: int = 500_000_000
    max_audio_bytes: int = 100_000_000
    max_document_bytes: int = 50_000_000
    agent_runtime_enabled: bool = False
    lab_enabled: bool = False
    lab_telemetry_enabled: bool = False
    lab_feedback_enabled: bool = False
    lab_admin_enabled: bool = False
    lab_rollups_enabled: bool = False
    lab_demo_enabled: bool = True
    lab_hash_secret: str = "local-lab-hash-secret"
    lab_comment_retention_days: int = 90
    lab_trace_retention_days: int = 180
    lab_event_retention_days: int = 90
    lab_rollup_min_sample: int = 30

    def validate_startup(self) -> None:
        if self.provider_timeout_seconds <= 0:
            raise ValueError("PETI_PROVIDER_TIMEOUT_SECONDS must be positive")
        if self.gemini_max_attempts <= 0 or self.gemini_max_attempts > 10:
            raise ValueError("PETI_GEMINI_MAX_ATTEMPTS must be between 1 and 10")
        if self.gemini_daily_limit_per_key <= 0:
            raise ValueError("PETI_GEMINI_DAILY_LIMIT_PER_KEY must be positive")
        if self.gemini_transport not in {"SDK", "REST"}:
            raise ValueError("PETI_GEMINI_TRANSPORT must be SDK or REST")
        if any(
            value <= 0
            for value in (
                self.lab_comment_retention_days,
                self.lab_trace_retention_days,
                self.lab_event_retention_days,
                self.lab_rollup_min_sample,
            )
        ):
            raise ValueError("PETI Lab retention and sample settings must be positive")
        if any((self.lab_telemetry_enabled, self.lab_feedback_enabled, self.lab_admin_enabled, self.lab_rollups_enabled)) and not self.lab_enabled:
            raise ValueError("PETI Lab subfeatures require PETI_LAB_ENABLED")
        if self.lab_feedback_enabled and not self.agent_runtime_enabled:
            raise ValueError("PETI Lab feedback requires PETI_AGENT_RUNTIME_ENABLED")
        if self.environment is not Environment.LOCAL and self.lab_enabled:
            if self.lab_hash_secret == "local-lab-hash-secret":
                raise ValueError("non-LOCAL PETi Lab requires PETI_LAB_HASH_SECRET")
            if self.storage_mode != "FIRESTORE":
                raise ValueError("non-LOCAL PETi Lab requires FIRESTORE storage")
        if self.environment is Environment.PRODUCTION and not self.project_id:
            raise ValueError("PRODUCTION requires PETI_PROJECT_ID")
        if self.environment is Environment.PRODUCTION and self.auth_mode != "FIREBASE":
            raise ValueError("PRODUCTION requires FIREBASE auth")
        if self.environment is Environment.PRODUCTION and self.peti_check_enabled:
            raise ValueError("PRODUCTION PETi Check requires an externally certified release flag")
        if self.environment is not Environment.LOCAL and self.auth_mode != "FIREBASE":
            raise ValueError("non-LOCAL environments require FIREBASE auth")
        if self.storage_mode not in {"MEMORY", "FIRESTORE_EMULATOR", "FIRESTORE"}:
            raise ValueError("PETI_STORAGE_MODE must be MEMORY, FIRESTORE_EMULATOR, or FIRESTORE")
        if self.environment is Environment.LOCAL and self.storage_mode == "FIRESTORE":
            raise ValueError("ZERO_COST_POLICY: LOCAL cannot use real Firestore; use MEMORY or FIRESTORE_EMULATOR")
        if self.storage_mode == "FIRESTORE_EMULATOR" and self.environment is not Environment.LOCAL:
            raise ValueError("FIRESTORE_EMULATOR is only allowed in LOCAL")
        if self.environment in {Environment.STAGING, Environment.PRODUCTION} and self.storage_mode == "MEMORY":
            raise ValueError("STAGING and PRODUCTION require durable Firestore storage")
        if self.environment is Environment.LOCAL and self.ai_provider != "FAKE":
            raise ValueError("ZERO_COST_POLICY: LOCAL must use FAKE AI provider")
        if self.environment is not Environment.LOCAL and not self.media_bucket:
            raise ValueError("non-LOCAL environments require PETI_MEDIA_BUCKET")
        if self.environment is not Environment.LOCAL:
            required = {"tasks_project_id": self.tasks_project_id}
            if not self.service.startswith("peti-worker"):
                required["analysis_worker_url"] = self.analysis_worker_url
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(f"non-LOCAL environments require {', '.join(missing)}")
            if self.ai_provider == "FAKE" and self.environment is Environment.PRODUCTION:
                raise ValueError("PRODUCTION cannot use FAKE AI provider")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_startup()
    return settings
