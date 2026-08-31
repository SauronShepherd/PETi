"""Bounded, provider-backed execution for the PETi agent run contract.

The executor deliberately keeps orchestration in application code: the model
may produce observations, but it cannot choose tools, change ownership, or
write durable state outside the supplied gateway and run store.
"""
from dataclasses import asdict
from threading import RLock
from uuid import uuid4

from app.agents.contracts import AgentOrchestrator, EvidenceReference, RunState
from app.agents.technical_contracts import ExecutionPlan, PlanNode
from app.ai.providers.base import AIProvider, ProviderError

from .adk_graph import build_peti_agent, graph_metadata
from .instrumentation import InvocationContext, invocation_scope
from .release_policy import ModelPolicy, validate_policy


class AgentExecutionService:
    def __init__(
        self,
        runs: AgentOrchestrator,
        provider: AIProvider,
        *,
        policy: ModelPolicy | None = None,
        lab=None,
    ):
        self.runs = runs
        self.provider = provider
        self.policy = validate_policy(policy or ModelPolicy(model=getattr(provider, "model", "configured-server-model")))
        self._execution_lock = RLock()
        self.lab = lab
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
        self.runs._set_state(run, RunState.RUNNING)
        run.started_at = run.started_at or self.runs.clock()
        self.runs._persist_run(run)
        plan = ExecutionPlan(run.id, "peti-care-review-v1", [
            PlanNode("plan", "CONTROL", "ORCHESTRATOR", [], "execution-plan-v1"),
            PlanNode("evidence-intake", "EVIDENCE", "EVIDENCE_INTAKE", ["plan"], "evidence-summary-v1"),
            PlanNode("peti-check", "MODEL", "PET_SPECIALIST", ["evidence-intake"], "peti-check-v1"),
            PlanNode("safety-review", "POLICY", "SAFETY_REVIEW", ["peti-check"], "safety-decision-v1"),
            PlanNode("care-report", "SYNTHESIS", "CARE_REPORT", ["safety-review"], "care-report-v1"),
        ], "agent-response-v1")
        run.plan_id = plan.id; run.recipe_id = plan.recipe_id; self.runs._persist_run(run)
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
                response = self.provider.analyze(media, "Return JSON observations only. Include observations, evidence_quality, uncertainty, limitations, provenance, and safety_guidance. Never diagnose, prescribe, or claim a condition is ruled out.", context)
            if self.lab and model_call and not getattr(self.provider, "instrumented", False):
                self.lab.complete_model_call(run, model_call[0], model_call[1], response)
            evidence = []
            if run.pet_id:
                evidence.append(EvidenceReference("MEDIA", "input", run.pet_id, owner))
            commit({"step_id": "peti-check", "output": response.payload, "schema_version": "1.0.0", "safety_state": "PENDING_REVIEW"}, evidence)
            if self.lab and specialist_started is not None:
                observations = response.payload.get("observations", [])
                self.lab.complete_step(run, "peti-check", "PET_SPECIALIST", specialist_started, safety_state="PENDING_REVIEW", evidence_count=len(evidence), claim_count=len(observations) if isinstance(observations, list) else 0)
                self.lab.handoff(run, "PET_SPECIALIST", "SAFETY_REVIEW", "SAFETY_GATE_REQUIRED", len(evidence))
            safety_started = self.lab.start_step(run, "safety-review", "SAFETY_REVIEW") if self.lab else None
            commit({"step_id": "safety-review", "output": {"decision": "REVIEW_REQUIRED", "provider": response.provider, "model": response.model, "usage": asdict(response.usage)}, "schema_version": "1.0.0"})
            if self.lab and safety_started is not None:
                self.lab.complete_step(run, "safety-review", "SAFETY_REVIEW", safety_started, safety_state="REVIEW_REQUIRED", outcome="SAFETY_ROUTED")
                self.lab.handoff(run, "SAFETY_REVIEW", "CARE_REPORT", "SAFETY_DECISION_AVAILABLE", len(evidence))
            report_started = self.lab.start_step(run, "care-report", "CARE_REPORT") if self.lab else None
            commit({"step_id": "care-report", "output": {"status": "PENDING_REVIEW", "actions": [], "source_step": "safety-review"}, "schema_version": "1.0.0"})
            if self.lab and report_started is not None:
                self.lab.complete_step(run, "care-report", "CARE_REPORT", report_started, safety_state="REVIEW_REQUIRED")
            result = {"answer_type": "GROUNDED_OBSERVATIONS", "schema_version": "1.0.0", "status": "REVIEW_REQUIRED", "outcome": "SAFETY_ROUTED", "safety_state": "REVIEW_REQUIRED", "payload": response.payload}
            published = self.lab.publish_response(run, outcome="SAFETY_ROUTED", safety_state="REVIEW_REQUIRED", provider=response.provider, model=response.model) if self.lab else None
            if published:
                result["response_id"] = published.id
                result["feedback_eligible"] = published.eligible_for_feedback
            current = self.runs.get(owner, run_id)
            self.runs.complete(owner, run_id, result, lease_epoch=lease_epoch, expected_version=current.run_version)
            if self.lab and published:
                self.lab.complete_run(run, published)
            result_public = self.runs.get(owner, run_id).public()
            self.runs.release_execution_lease(owner, run_id, lease_owner)
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
            self.runs.release_execution_lease(owner, run_id, lease_owner)
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
            self.runs.release_execution_lease(owner, run_id, lease_owner)
            raise
