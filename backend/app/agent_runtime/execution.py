"""Bounded, provider-backed execution for the PETi agent run contract.

The executor deliberately keeps orchestration in application code: the model
may produce observations, but it cannot choose tools, change ownership, or
write durable state outside the supplied gateway and run store.
"""
from dataclasses import asdict
from threading import RLock
from types import SimpleNamespace
from uuid import uuid4

from app.agents.contracts import AgentOrchestrator, EvidenceReference, RunState
from app.agents.schemas import EvidenceIntakeResultV1, FecesAgentResultV1, LongitudinalAgentResultV1
from app.agents.technical_contracts import ExecutionPlan, PlanNode
from app.ai.providers.base import AIProvider, ProviderError, ProviderUsage

from .adk_graph import build_peti_agent, graph_metadata
from .agent_model_provider import AgentModelProvider, ProviderInvocationResult
from .capability_registry import CapabilityRegistry
from .claim_composition import compose_claims
from .config.capabilities_v1 import CAPABILITIES_V1
from .instrumentation import InvocationContext, invocation_scope
from .longitudinal_selector import select_compatible_candidates
from .plan_validator import PlanValidator
from .recipe_registry import resolve_recipe
from .release_policy import ModelPolicy, validate_policy
from .role_dispatch import RoleDispatcher, RoleInvocation
from .semantic_validation import deterministic_feces_safety, validate_synthesis


class AgentExecutionService:
    def __init__(
        self,
        runs: AgentOrchestrator,
        provider: AIProvider,
        *,
        policy: ModelPolicy | None = None,
        lab=None,
        agent_model_provider: AgentModelProvider | None = None,
    ):
        self.runs = runs
        self.provider = provider
        self.policy = validate_policy(policy or ModelPolicy(model=getattr(provider, "model", "configured-server-model")))
        self._execution_lock = RLock()
        self.lab = lab
        self.agent_model_provider = agent_model_provider
        try:
            self.adk_agent = build_peti_agent(self.policy.model)
        except ModuleNotFoundError as exc:
            if exc.name != "google.adk":
                raise
            self.adk_agent = None

    def execute(self, owner: str, run_id: str, media, *, context: str | None = None) -> dict:
        """Execute one run atomically for in-process task redelivery.

        Cloud Tasks can deliver the same task concurrently.  Serialize the
        state transition and provider call so a second delivery observes the
        terminal run instead of issuing a duplicate provider request. Durable
        multi-instance contention still requires the deployed store gate.
        """
        with self._execution_lock:
            return self._execute(owner, run_id, media, context=context)

    def _execute(self, owner: str, run_id: str, media, *, context: str | None = None) -> dict:
        run = self.runs.get(owner, run_id)
        if run.state.value not in {"QUEUED", "RUNNING"}:
            if run.state.value in {"COMPLETED", "FAILED", "CANCELLED"}:
                return run.public()
            raise ValueError("AGENT_RUN_NOT_EXECUTABLE")
        lease_owner = str(uuid4())
        if not self.runs.acquire_execution_lease(owner, run_id, lease_owner):
            # Redelivery while another instance owns the provider call is a successful no-op.
            return {**run.public(), "duplicate_execution_prevented": True}
        run = self.runs.get(owner, run_id)
        lease_epoch = run.lease_epoch
        def commit(step, evidence=None):
            current = self.runs.get(owner, run_id)
            return self.runs.commit_step(
                owner, run_id, step, evidence,
                lease_epoch=lease_epoch,
                expected_version=current.run_version,
            )
        run.started_at = run.started_at or self.runs.clock()
        # started_at is part of the same fenced lifecycle write, not a loose
        # cache mutation.
        run = self.runs.transition_state_fenced(
            owner, run_id, RunState.RUNNING,
            lease_epoch=lease_epoch, expected_version=run.run_version,
            started_at=run.started_at,
        )
        goal_text = str(run.goal).lower()
        recipe_id = "FECES_COMPARE_FOLLOW_UP_V1" if ("remind" in goal_text or "recordatorio" in goal_text) and ("compare" in goal_text or "compara" in goal_text or "history" in goal_text or "historial" in goal_text) else ("FECES_COMPARE_V1" if "compare" in goal_text or "compara" in goal_text or "history" in goal_text or "historial" in goal_text else "FECES_CURRENT_V1")
        recipe = resolve_recipe(recipe_id)
        plan = ExecutionPlan(run.id, recipe.recipe_id, [
            PlanNode(node_id, kind, executor, list(deps), "1.0.0")
            for node_id, kind, executor, deps in recipe.nodes
        ], "agent-answer-v1")
        validator = PlanValidator(CapabilityRegistry(CAPABILITIES_V1))
        validator.validate([{"node_id": n.node_id, "executor_id": n.executor_id, "depends_on": n.depends_on} for n in plan.nodes], requires_final_safety=False, max_steps=run.policy_snapshot.get("max_steps", 8))
        run.plan_id = plan.id; run.recipe_id = plan.recipe_id; self.runs._persist_run(run)
        if self.runs.repository and hasattr(self.runs.repository, "ensure_steps"):
            self.runs.repository.ensure_steps(run.id, [{"id": node.node_id, "kind": node.kind, "executor_id": node.executor_id, "depends_on": node.depends_on} for node in plan.nodes])
        if self.lab:
            self.lab.start_run(run)
        model_call: tuple[str, float] | None = None
        plan_started = self.lab.start_step(run, "plan", "ORCHESTRATOR") if self.lab else None
        commit({"step_id": "plan", "output": {"plan": asdict(plan), "policy": asdict(self.policy), "agent_graph": graph_metadata(self.policy.model)}, "schema_version": "1.0.0"})
        if self.lab and plan_started is not None:
            self.lab.complete_step(run, "plan", "ORCHESTRATOR", plan_started)
        try:
            evidence_started = self.lab.start_step(run, "evidence-intake", "EVIDENCE_INTAKE") if self.lab else None
            evidence_tool = self.lab.start_tool_call(run, step_id="evidence-intake", agent_id="EVIDENCE_INTAKE", tool_id="evidence-catalog") if self.lab else None
            commit({"step_id": "evidence-intake", "output": {"item_count": len(media.items), "media_version": getattr(media, "version", "1.0.0"), "status": "READY"}, "schema_version": "1.0.0"})
            if self.lab and evidence_started is not None:
                if evidence_tool is not None:
                    self.lab.complete_tool_call(evidence_tool[0], evidence_tool[1], result_code="EVIDENCE_READY")
                self.lab.complete_step(run, "evidence-intake", "EVIDENCE_INTAKE", evidence_started, evidence_count=len(media.items))
                self.lab.handoff(run, "EVIDENCE_INTAKE", "PET_SPECIALIST", "PLAN_DEPENDENCY_READY", len(media.items))
            specialist_started = self.lab.start_step(run, "peti-check", "PET_SPECIALIST") if self.lab else None
            if self.lab and not getattr(self.provider, "instrumented", False):
                model_call = self.lab.start_model_call(
                    run,
                    step_id="peti-check",
                    agent_id="PET_SPECIALIST",
                    provider=getattr(self.provider, "name", "UNKNOWN"),
                    model_id=getattr(self.provider, "model", "UNKNOWN"),
                )
            invocation = InvocationContext(owner, run.id, "peti-check", "PET_SPECIALIST",
                run.correlation_id or run.id, run.deployment_id or "unknown")
            with invocation_scope(invocation):
                if self.agent_model_provider and recipe_id == "FECES_COMPARE_V1":
                    bundle = {"owner_user_id": owner, "run_id": run.id, "session_id": run.policy_snapshot.get("session_id") or run.id, "pet_id": run.pet_id, "items": [{"id": getattr(item, "id", None)} for item in media.items]}
                    current = {"pet_id": run.pet_id, "modality": "FECES", "taxonomy_version": "v1"}
                    candidates = [item for item in media.items if isinstance(item, dict)]
                    compatible = select_compatible_candidates(current, candidates)
                    dispatcher = RoleDispatcher(self.agent_model_provider)
                    role_requests = [
                        RoleInvocation("EVIDENCE_INTAKE", self.policy.model, self.policy.prompt_version, bundle, EvidenceIntakeResultV1),
                        RoleInvocation("FECES_CURRENT_ASSESSMENT", self.policy.model, self.policy.prompt_version, bundle, FecesAgentResultV1),
                    ]
                    if compatible:
                        role_requests.append(RoleInvocation("FECES_LONGITUDINAL_COMPARE", self.policy.model, self.policy.prompt_version, {**bundle, "prior_candidates": compatible}, LongitudinalAgentResultV1))
                    role_results = dispatcher.dispatch_many(role_requests)
                    last = role_results[-1] if compatible else ProviderInvocationResult("deterministic", "none", None, {"comparability": "INSUFFICIENT_DATA", "evidence_ids": []}, {})
                    response = SimpleNamespace(payload=last.structured_payload, provider=last.provider, model=last.model_id, usage=ProviderUsage(**{k: v for k, v in last.usage.items() if k in {"input_tokens", "output_tokens", "cached_input_tokens", "media_usage", "provider_request_id", "latency_ms"}}))
                else:
                    response = self.provider.analyze(media, "Return JSON observations only. Include observations, evidence_quality, uncertainty, limitations, provenance, and safety_guidance. Never diagnose, prescribe, or claim a condition is ruled out.", context)
            if self.lab and model_call and not getattr(self.provider, "instrumented", False):
                self.lab.complete_model_call(run, model_call[0], model_call[1], response)
            evidence = []
            for item in getattr(media, "items", []) or []:
                asset_id = item.get("id") if isinstance(item, dict) else getattr(item, "id", None)
                if asset_id:
                    evidence.append(EvidenceReference("MEDIA_ASSET", str(asset_id), run.pet_id or "", owner))
            commit({"step_id": "peti-check", "output": response.payload, "schema_version": "1.0.0", "safety_state": "PENDING_REVIEW"}, evidence)
            if self.lab and specialist_started is not None:
                observations = response.payload.get("observations", [])
                self.lab.complete_step(run, "peti-check", "PET_SPECIALIST", specialist_started, safety_state="PENDING_REVIEW", evidence_count=len(evidence), claim_count=len(observations) if isinstance(observations, list) else 0)
                self.lab.handoff(run, "PET_SPECIALIST", "SAFETY_REVIEW", "SAFETY_GATE_REQUIRED", len(evidence))
            safety_state = deterministic_feces_safety(response.payload, run.owner_context if hasattr(run, "owner_context") else None)
            safety_started = self.lab.start_step(run, "safety-review", "SAFETY_REVIEW") if self.lab else None
            commit({"step_id": "safety-review", "output": {"decision": safety_state, "provider": response.provider, "model": response.model, "usage": asdict(response.usage)}, "schema_version": "1.0.0", "safety_state": safety_state})
            if self.lab and safety_started is not None:
                self.lab.complete_step(run, "safety-review", "SAFETY_REVIEW", safety_started, safety_state=safety_state, outcome="SAFETY_DECISION_AVAILABLE")
                self.lab.handoff(run, "SAFETY_REVIEW", "CARE_REPORT", "SAFETY_DECISION_AVAILABLE", len(evidence))
            report_started = self.lab.start_step(run, "care-report", "CARE_REPORT") if self.lab else None
            commit({"step_id": "care-report", "output": {"status": safety_state, "actions": [], "source_step": "safety-review"}, "schema_version": "1.0.0", "safety_state": safety_state})
            if self.lab and report_started is not None:
                self.lab.complete_step(run, "care-report", "CARE_REPORT", report_started, safety_state=safety_state)
            claim_evidence_ids = [ref.entity_id for ref in evidence]
            claims = compose_claims(response.payload, claim_evidence_ids)
            validate_synthesis(claims, safety_state)
            self.runs.persist_claims(owner, run_id, claims)
            result = {"answer_type": "GROUNDED_OBSERVATIONS", "schema_version": "1.0.0", "status": safety_state, "outcome": "SAFETY_ROUTED" if safety_state != "NORMAL_INFORMATION" else "ANSWERED", "safety_state": safety_state, "claims": claims, "evidence_references": [asdict(ref) for ref in evidence], "payload": response.payload}
            published = self.lab.publish_response(run, outcome=result["outcome"], safety_state=safety_state, provider=response.provider, model=response.model) if self.lab else None
            if published:
                result["response_id"] = published.id
                result["feedback_eligible"] = published.eligible_for_feedback
            current = self.runs.get(owner, run_id)
            self.runs.complete(owner, run_id, result, lease_epoch=lease_epoch, expected_version=current.run_version)
            if self.lab and published:
                self.lab.complete_run(run, published)
            result_public = self.runs.get(owner, run_id).public()
            self.runs.release_execution_lease(owner, run_id, lease_owner, lease_epoch=lease_epoch, expected_version=self.runs.get(owner, run_id).run_version)
            return result_public
        except ProviderError as exc:
            if self.lab: self.lab.fail_open_steps(run, error_code=exc.code, retryable=exc.retryable)
            if self.lab and model_call and not getattr(self.provider, "instrumented", False):
                self.lab.fail_model_call(
                    run,
                    model_call[0],
                    model_call[1],
                    error_code=exc.code,
                    retryable=exc.retryable,
                )
            self.runs._set_state(run, RunState.FAILED if not exc.retryable else RunState.WAITING)
            self.runs._persist_run(run)
            if self.lab: self.lab.fail_run(run, error_code=exc.code, retryable=exc.retryable)
            self.runs.release_execution_lease(owner, run_id, lease_owner, lease_epoch=lease_epoch, expected_version=self.runs.get(owner, run_id).run_version)
            raise
        except Exception:
            if self.lab: self.lab.fail_open_steps(run, error_code="UNEXPECTED_PROVIDER_ERROR", retryable=False)
            if self.lab and model_call and not getattr(self.provider, "instrumented", False):
                self.lab.fail_model_call(
                    run,
                    model_call[0],
                    model_call[1],
                    error_code="UNEXPECTED_PROVIDER_ERROR",
                    retryable=False,
                )
            # Never leave a durable run in RUNNING after an unexpected
            # provider/serialization failure.  The task may be retried, but
            # the persisted state must remain explicit and auditable.
            self.runs._set_state(run, RunState.FAILED)
            self.runs._persist_run(run)
            if self.lab: self.lab.fail_run(run, error_code="UNEXPECTED_PROVIDER_ERROR", retryable=False)
            self.runs.release_execution_lease(owner, run_id, lease_owner, lease_epoch=lease_epoch, expected_version=self.runs.get(owner, run_id).run_version)
            raise
