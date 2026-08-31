"""Strict, provider-facing result envelopes for the released agent roles."""
from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GoalResolutionResultV1(_Strict):
    goal_type: str
    subject_domain: str
    required_capabilities: list[str] = Field(default_factory=list)
    required_context_categories: list[str] = Field(default_factory=list)
    selected_recipe_id: str
    fast_path: bool = False


class EvidenceIntakeResultV1(_Strict):
    usable: bool
    evidence_quality: str
    evidence_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class FecesAgentResultV1(_Strict):
    observations: list[dict] = Field(default_factory=list)
    evidence_quality: str
    uncertainty: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class LongitudinalAgentResultV1(_Strict):
    comparability: str
    change_label: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class CareAgentResultV1(_Strict):
    proposed_actions: list[dict] = Field(default_factory=list)
    requires_approval: bool = True


class SynthesisResultV1(_Strict):
    answer_type: str
    claims: list[dict] = Field(default_factory=list)
    safety_state: str
    evidence_ids: list[str] = Field(default_factory=list)
