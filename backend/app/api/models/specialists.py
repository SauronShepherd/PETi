from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SpecialistCreateRequest(BaseModel):
    """Client-owned inputs only; provider output is intentionally impossible."""
    model_config = ConfigDict(extra="forbid")
    media_asset_ids: list[str] = Field(default_factory=list, max_length=8)
    source_media_ids: list[str] = Field(default_factory=list, max_length=8)
    capture_manifest: dict[str, Any] | None = None
    owner_context: dict[str, Any] | list[str] | None = None
    funding_reservation_id: str | None = None
    freshness_confirmation: str | None = None


class SpecialistWorkerCompletion(BaseModel):
    """Internal-only shape for a trusted worker completion."""
    model_config = ConfigDict(extra="forbid")
    analysis_id: str
    owner_user_id: str
    result: dict[str, Any]
    provider: str
    provider_model: str
