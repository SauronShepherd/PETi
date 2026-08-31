from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentProgressItemPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step_id: str
    status: str
    label: str | None = None


class AgentRunPublic(BaseModel):
    """Presentation projection; never serializes raw internal steps/model state."""
    model_config = ConfigDict(extra="forbid")
    run_id: str
    dog_id: str | None
    status: str
    outcome: str | None = None
    progress_items: list[AgentProgressItemPublic] = Field(default_factory=list)
    context_requests: list[dict[str, Any]] = Field(default_factory=list)
    proposed_actions: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] | None = None
    partial_capabilities: list[str] = Field(default_factory=list)
    support_id: str


class AgentRunCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goal: str = Field(min_length=1, max_length=500)
    media_asset_ids: list[str] = Field(default_factory=list, max_length=5)
    source_object_refs: list[str] = Field(default_factory=list, max_length=5)
    session_id: str | None = None
    context: str | None = Field(default=None, max_length=2000)


def project_run(run) -> AgentRunPublic:
    steps = getattr(run, "steps", []) or []
    return AgentRunPublic(
        run_id=run.id,
        dog_id=run.pet_id,
        status=run.state.value,
        outcome=run.outcome,
        progress_items=[AgentProgressItemPublic(step_id=str(s.get("step_id", "final")), status="COMPLETED") for s in steps],
        support_id=run.correlation_id or run.id,
    )
