"""Bounded, provider-backed execution for the PETi agent run contract.

The executor deliberately keeps orchestration in application code: the model
may produce observations, but it cannot choose tools, change ownership, or
write durable state outside the supplied gateway and run store.
"""
from dataclasses import asdict
from threading import RLock

from app.agents.contracts import AgentOrchestrator, EvidenceReference, RunState
from app.ai.providers.base import AIProvider, ProviderError

from .release_policy import ModelPolicy, validate_policy


class AgentExecutionService:
    def __init__(self, runs: AgentOrchestrator, provider: AIProvider, *, policy: ModelPolicy | None = None):
        self.runs = runs
        self.provider = provider
        self.policy = validate_policy(policy or ModelPolicy(model=getattr(provider, "model", "configured-server-model")))
        self._execution_lock = RLock()

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
        self.runs._set_state(run, RunState.RUNNING)
        self.runs._persist_run(run)
        plan = ["EVIDENCE_INTAKE", "PETI_CHECK", "SAFETY_REVIEW", "CARE_REPORT"]
        self.runs.commit_step(owner, run_id, {"step_id": "plan", "output": {"nodes": plan, "policy": asdict(self.policy)}, "schema_version": "1.0.0"})
        try:
            self.runs.commit_step(owner, run_id, {"step_id": "evidence-intake", "output": {"item_count": len(media.items), "media_version": getattr(media, "version", "1.0.0"), "status": "READY"}, "schema_version": "1.0.0"})
            response = self.provider.analyze(media, "Return JSON observations only. Include observations, evidence_quality, uncertainty, limitations, provenance, and safety_guidance. Never diagnose, prescribe, or claim a condition is ruled out.", context)
            evidence = []
            if run.pet_id:
                evidence.append(EvidenceReference("MEDIA", "input", run.pet_id, owner))
            self.runs.commit_step(owner, run_id, {"step_id": "peti-check", "output": response.payload, "schema_version": "1.0.0", "safety_state": "PENDING_REVIEW"}, evidence)
            self.runs.commit_step(owner, run_id, {"step_id": "safety-review", "output": {"decision": "REVIEW_REQUIRED", "provider": response.provider, "model": response.model, "usage": asdict(response.usage)}, "schema_version": "1.0.0"})
            self.runs.commit_step(owner, run_id, {"step_id": "care-report", "output": {"status": "PENDING_REVIEW", "actions": [], "source_step": "safety-review"}, "schema_version": "1.0.0"})
            result = {"answer_type": "GROUNDED_OBSERVATIONS", "schema_version": "1.0.0", "status": "REVIEW_REQUIRED", "payload": response.payload}
            self.runs.complete(owner, run_id, result)
            return self.runs.get(owner, run_id).public()
        except ProviderError as exc:
            self.runs._set_state(run, RunState.FAILED if not exc.retryable else RunState.WAITING)
            self.runs._persist_run(run)
            raise
        except Exception:
            # Never leave a durable run in RUNNING after an unexpected
            # provider/serialization failure.  The task may be retried, but
            # the persisted state must remain explicit and auditable.
            self.runs._set_state(run, RunState.FAILED)
            self.runs._persist_run(run)
            raise
