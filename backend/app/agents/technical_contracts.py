"""Concrete data contracts from the multi-agent LLD.

These models are transport-neutral and intentionally contain no hidden model
reasoning, treatment/prescription fields, or client-controlled policy authority.
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4


class ComplexityClass(StrEnum): D0 = "D0"; A1 = "A1"; A2 = "A2"; A3 = "A3"
class StepStatus(StrEnum): PENDING = "PENDING"; READY = "READY"; RUNNING = "RUNNING"; WAITING_EXTERNAL = "WAITING_EXTERNAL"; WAITING_CONTEXT = "WAITING_CONTEXT"; WAITING_APPROVAL = "WAITING_APPROVAL"; RETRY_SCHEDULED = "RETRY_SCHEDULED"; SUCCEEDED = "SUCCEEDED"; FAILED_FINAL = "FAILED_FINAL"; SKIPPED = "SKIPPED"; POLICY_BLOCKED = "POLICY_BLOCKED"; CANCELED = "CANCELED"
class GoalOutcome(StrEnum): ANSWERED = "ANSWERED"; ANSWERED_PARTIALLY = "ANSWERED_PARTIALLY"; INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"; NEEDS_CONTEXT = "NEEDS_CONTEXT"; NEEDS_NEW_OBSERVATION = "NEEDS_NEW_OBSERVATION"; ACTION_PROPOSED = "ACTION_PROPOSED"; SAFETY_ROUTED = "SAFETY_ROUTED"; POLICY_BLOCKED = "POLICY_BLOCKED"; FAILED = "FAILED"
class ClaimType(StrEnum): OBSERVED = "OBSERVED"; REPORTED = "REPORTED"; DOCUMENTED = "DOCUMENTED"; CONFIRMED = "CONFIRMED"; MEASURED = "MEASURED"; ESTIMATED = "ESTIMATED"; INTERPRETED = "INTERPRETED"; LONGITUDINAL_CHANGE = "LONGITUDINAL_CHANGE"; SAFETY_SIGNAL = "SAFETY_SIGNAL"
class CapabilityReleaseState(StrEnum): DISABLED = "DISABLED"; SHADOW = "SHADOW"; INTERNAL = "INTERNAL"; CLOSED_BETA = "CLOSED_BETA"; PUBLIC_CANARY = "PUBLIC_CANARY"; PUBLIC = "PUBLIC"; KILLED = "KILLED"


@dataclass
class Goal:
    id: str
    type: str
    target_dog_id: str
    subject_domain: str | None = None
    current_object_refs: list[str] = field(default_factory=list)
    interaction_source: str = "APP"
    version: int = 1


@dataclass
class RunBudget:
    max_agent_steps: int = 8; max_model_calls: int = 3; max_tool_calls: int = 12; max_repair_attempts: int = 1; max_media_bytes: int | None = 20_000_000; max_context_items: int | None = 50; max_wall_clock_seconds: int = 120; max_estimated_cost_microunits: int | None = 100


@dataclass
class PlanNode:
    node_id: str
    kind: str
    executor_id: str
    depends_on: list[str] = field(default_factory=list)
    output_schema: str = "1.0.0"
    required: bool = True
    input_refs: list[str] = field(default_factory=list)
    failure_policy: str = "FAIL_RUN"


@dataclass
class ExecutionPlan:
    run_id: str
    recipe_id: str
    nodes: list[PlanNode]
    expected_final_output_schema: str
    id: str = field(default_factory=lambda: str(uuid4()))
    version: int = 1
    validator_version: str = "1.0.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AgentStep:
    run_id: str
    node_id: str
    status: StepStatus = StepStatus.PENDING
    output: dict | None = None
    schema_version: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class ContextBundle:
    owner_user_id: str
    pet_id: str
    items: list[dict] = field(default_factory=list)
    context_policy_version: str = "1.0.0"


@dataclass
class ContextRequest:
    run_id: str
    request_type: str
    required_items: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class ContextResponse:
    request_id: str
    accepted: bool
    resource_refs: list[str] = field(default_factory=list)


@dataclass
class Claim:
    claim_type: ClaimType
    text: str
    evidence_ids: list[str] = field(default_factory=list)
    confidence: str | None = None


@dataclass
class ConflictSet:
    claim_ids: list[str]
    resolution: str = "PRESERVE_CONFLICT"


@dataclass
class AgentResult:
    outcome: GoalOutcome
    claims: list[Claim] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    safety_state: str = "SAFE_TO_DISPLAY"


@dataclass
class ProposedAction:
    action_type: str
    summary: str
    arguments: dict = field(default_factory=dict)
    requires_approval: bool = True


@dataclass
class ActionApproval:
    action_id: str
    approver_user_id: str
    approved: bool
    approved_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ActionReceipt:
    action_id: str
    status: str
    result_ref: str | None = None


@dataclass
class ObservationPlan:
    owner_user_id: str
    pet_id: str
    requested_observations: list[str]
    status: str = "DRAFT"
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class CapabilityDescriptor:
    capability_id: str
    agent_type: str
    input_schema_id: str
    output_schema_id: str
    release_state: CapabilityReleaseState = CapabilityReleaseState.DISABLED


@dataclass
class AgentModelBinding:
    provider: str
    model: str
    prompt_version: str
    schema_version: str
    safety_policy_version: str


@dataclass
class AgentRunUiState:
    run_id: str
    state: str
    progress_label: str
    evidence_count: int = 0
    resumable: bool = True


class ExampleUiState(AgentRunUiState):
    pass


class LongitudinalAgentResult(AgentResult):
    pass
