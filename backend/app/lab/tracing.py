from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from time import perf_counter
from typing import Any
from uuid import uuid4

from app.agents.contracts import AgentRun
from app.analysis.domain import AnalysisJob, AnalysisResult

from .contracts import (
    AgentRunTrace,
    AgentStepTrace,
    EvidenceUsageTrace,
    InteractionResponse,
    ModelCallTrace,
    SafetyDecisionTrace,
    ToolCallTrace,
    TraceContext,
)
from .enums import DataClassification, ResponseSourceType, TraceStatus
from .hashing import owner_hash
from .telemetry import TelemetryService


class LabTraceService:
    def __init__(
        self,
        repository: Any,
        telemetry: TelemetryService,
        *,
        hash_secret: str,
        environment: str,
        deployment_id: str,
        trace_retention_days: int = 180,
    ) -> None:
        self.repository = repository
        self.telemetry = telemetry
        self.hash_secret = hash_secret
        self.environment = environment
        self.deployment_id = deployment_id
        self.trace_retention_days = trace_retention_days

    @property
    def classification(self) -> DataClassification:
        return DataClassification.TEST if self.environment == "LOCAL" else DataClassification.REAL

    def context(self, run: AgentRun, *, step_id: str | None = None, agent_id: str | None = None) -> TraceContext:
        return TraceContext(
            correlation_id=run.correlation_id or run.id,
            interaction_id=run.interaction_id or run.id,
            run_id=run.id,
            step_id=step_id,
            owner_user_id=run.owner_user_id,
            pet_id=run.pet_id,
            agent_id=agent_id or run.agent_type,
            deployment_id=run.deployment_id or self.deployment_id,
            environment=self.environment,
            data_classification=self.classification,
        )

    def create_run(self, run: AgentRun) -> AgentRunTrace:
        trace = AgentRunTrace(
            run_id=run.id,
            interaction_id=run.interaction_id or run.id,
            correlation_id=run.correlation_id or run.id,
            owner_user_id=run.owner_user_id,
            owner_hash=owner_hash(run.owner_user_id, self.hash_secret),
            pet_id=run.pet_id,
            agent_type=run.agent_type,
            deployment_id=run.deployment_id or self.deployment_id,
            environment=self.environment,
            data_classification=self.classification,
            started_at=run.created_at,
            expires_at=run.created_at + timedelta(days=self.trace_retention_days),
        )
        self.repository.put_run(trace)
        self.telemetry.emit(
            "run_created",
            context=self.context(run),
            properties={"agent_type": run.agent_type, "goal_type": "USER_GOAL"},
            event_id=f"run-created:{run.id}",
        )
        return trace

    def start_run(self, run: AgentRun) -> None:
        trace = self.repository.get_run(run.id) or self.create_run(run)
        self.repository.transition_run(
            replace(trace, status=TraceStatus.STARTED, started_at=datetime.now(UTC),
                plan_id=run.plan_id, recipe_id=run.recipe_id),
            {TraceStatus.STARTED},
        )
        self.telemetry.emit(
            "run_started",
            context=self.context(run),
            properties={"agent_type": run.agent_type},
            event_id=f"run-started:{run.id}",
        )

    def start_step(self, run: AgentRun, step_id: str, agent_id: str, schema_version: str = "1.0.0") -> float:
        started = datetime.now(UTC)
        trace = AgentStepTrace(
            id=f"{run.id}:{step_id}",
            run_id=run.id,
            step_id=step_id,
            agent_id=agent_id,
            agent_version="1.0.0",
            schema_version=schema_version,
            status=TraceStatus.STARTED,
            started_at=started,
            correlation_id=run.correlation_id or run.id,
            deployment_id=run.deployment_id or self.deployment_id,
            environment=self.environment,
            data_classification=self.classification,
            expires_at=started + timedelta(days=self.trace_retention_days),
            owner_user_id=run.owner_user_id,
            owner_hash=owner_hash(run.owner_user_id, self.hash_secret),
        )
        self.repository.put_step(trace)
        self.telemetry.emit(
            "agent_step_started",
            context=self.context(run, step_id=step_id, agent_id=agent_id),
            properties={"agent_id": agent_id, "agent_version": "1.0.0", "schema_version": schema_version},
            event_id=f"step-started:{run.id}:{step_id}",
        )
        return perf_counter()

    def handoff(self, run: AgentRun, from_agent: str, to_agent: str, reason_code: str, evidence_count: int = 0) -> None:
        self.telemetry.emit("agent_handoff", context=self.context(run, agent_id=to_agent), properties={
            "from_agent": from_agent, "to_agent": to_agent,
            "reason_code": reason_code, "evidence_count": evidence_count,
        }, event_id=f"handoff:{run.id}:{from_agent}:{to_agent}")

    def complete_step(
        self,
        run: AgentRun,
        step_id: str,
        agent_id: str,
        started_perf: float,
        *,
        safety_state: str = "SAFE_TO_DISPLAY",
        evidence_count: int = 0,
        claim_count: int = 0,
        outcome: str = "SUCCEEDED",
    ) -> None:
        duration_ms = max(0, round((perf_counter() - started_perf) * 1000))
        existing = next((item for item in self.repository.list_steps(run.id) if item.step_id == step_id), None)
        if existing is None:
            return
        self.repository.transition_step(
            replace(
                existing,
                status=TraceStatus.SUCCEEDED,
                completed_at=datetime.now(UTC),
                duration_ms=duration_ms,
                evidence_count=evidence_count,
                claim_count=claim_count,
                safety_state=safety_state,
                outcome=outcome,
            ),
            {TraceStatus.STARTED},
        )
        if evidence_count or claim_count:
            self.repository.put_evidence_usage(EvidenceUsageTrace(
                f"{run.id}:{step_id}:evidence", run.id, step_id, "MULTIMODAL",
                evidence_count, claim_count, run.correlation_id or run.id,
                run.deployment_id or self.deployment_id, self.environment, self.classification,
                expires_at=datetime.now(UTC) + timedelta(days=self.trace_retention_days),
                owner_user_id=run.owner_user_id, owner_hash=owner_hash(run.owner_user_id, self.hash_secret)))
        if safety_state:
            self.repository.put_safety_decision(SafetyDecisionTrace(
                f"{run.id}:{step_id}:safety", run.id, step_id, safety_state, "1.0.0",
                run.correlation_id or run.id, run.deployment_id or self.deployment_id,
                self.environment, self.classification,
                expires_at=datetime.now(UTC) + timedelta(days=self.trace_retention_days),
                owner_user_id=run.owner_user_id, owner_hash=owner_hash(run.owner_user_id, self.hash_secret)))
        self.telemetry.emit(
            "agent_step_completed",
            context=self.context(run, step_id=step_id, agent_id=agent_id),
            properties={
                "agent_id": agent_id,
                "agent_version": "1.0.0",
                "outcome": outcome,
                "safety_state": safety_state,
                "duration_ms": duration_ms,
                "evidence_count": evidence_count,
                "claim_count": claim_count,
            },
            event_id=f"step-completed:{run.id}:{step_id}",
        )

    def fail_open_steps(self, run: AgentRun, *, error_code: str, retryable: bool) -> None:
        for existing in self.repository.list_steps(run.id):
            if existing.status is not TraceStatus.STARTED:
                continue
            completed = datetime.now(UTC)
            self.repository.transition_step(replace(existing, status=TraceStatus.FAILED,
                completed_at=completed, duration_ms=max(0, round((completed - existing.started_at).total_seconds() * 1000)),
                outcome="FAILED_RETRYABLE" if retryable else "FAILED_FINAL"), {TraceStatus.STARTED})
            self.telemetry.emit("agent_step_failed", context=self.context(run, step_id=existing.step_id, agent_id=existing.agent_id),
                properties={"agent_id": existing.agent_id, "error_code": error_code, "retryable": retryable},
                event_id=f"step-failed:{run.id}:{existing.step_id}:{error_code}")
        for existing in self.repository.list_tool_calls(run.id):
            if existing.status is not TraceStatus.STARTED:
                continue
            completed = datetime.now(UTC)
            self.repository.transition_tool_call(replace(existing, status=TraceStatus.FAILED,
                completed_at=completed,
                duration_ms=max(0, round((completed - existing.started_at).total_seconds() * 1000)),
                result_code=error_code), {TraceStatus.STARTED})

    def start_model_call(
        self,
        run: AgentRun,
        *,
        step_id: str,
        agent_id: str,
        provider: str,
        model_id: str,
        prompt_version: str = "1.0.0",
        schema_version: str = "1.0.0",
    ) -> tuple[str, float]:
        call_id = str(uuid4())
        trace = ModelCallTrace(
            id=call_id,
            run_id=run.id,
            step_id=step_id,
            agent_id=agent_id,
            correlation_id=run.correlation_id or run.id,
            provider=provider,
            model_id=model_id,
            status=TraceStatus.STARTED,
            started_at=datetime.now(UTC),
            prompt_version=prompt_version,
            schema_version=schema_version,
            safety_policy_version="1.0.0",
            deployment_id=run.deployment_id or self.deployment_id,
            environment=self.environment,
            data_classification=self.classification,
            expires_at=datetime.now(UTC) + timedelta(days=self.trace_retention_days),
            owner_user_id=run.owner_user_id,
            owner_hash=owner_hash(run.owner_user_id, self.hash_secret),
        )
        self.repository.put_model_call(trace)
        self.telemetry.emit(
            "model_call_started",
            context=self.context(run, step_id=step_id, agent_id=agent_id),
            properties={
                "provider": provider,
                "model_id": model_id,
                "prompt_version": prompt_version,
                "schema_version": schema_version,
            },
            event_id=f"model-call-started:{call_id}",
        )
        return call_id, perf_counter()

    def start_tool_call(self, run: AgentRun, *, step_id: str, agent_id: str, tool_id: str) -> tuple[str, float]:
        call_id = f"{run.id}:{step_id}:tool:{tool_id}"
        started = datetime.now(UTC)
        self.repository.put_tool_call(ToolCallTrace(
            call_id, run.id, step_id, agent_id, tool_id, TraceStatus.STARTED,
            run.correlation_id or run.id, run.deployment_id or self.deployment_id,
            self.environment, self.classification, started,
            expires_at=started + timedelta(days=self.trace_retention_days),
            owner_user_id=run.owner_user_id,
            owner_hash=owner_hash(run.owner_user_id, self.hash_secret),
        ))
        return call_id, perf_counter()

    def complete_tool_call(self, call_id: str, started_perf: float, *, result_code: str = "OK") -> None:
        trace = next((item for item in self.repository.list_tool_calls() if item.id == call_id), None)
        if trace is None:
            return
        self.repository.transition_tool_call(replace(
            trace, status=TraceStatus.SUCCEEDED, completed_at=datetime.now(UTC),
            duration_ms=max(0, round((perf_counter() - started_perf) * 1000)),
            result_code=result_code,
        ), {TraceStatus.STARTED})

    def complete_model_call(self, run: AgentRun, call_id: str, started_perf: float, response) -> None:
        trace = next(
            (item for item in self.repository.list_model_calls(run.id) if item.id == call_id), None
        )
        if trace is None:
            return
        latency_ms = max(0, round((perf_counter() - started_perf) * 1000))
        usage = response.usage
        usage_known = any(
            value is not None
            for value in (usage.input_tokens, usage.output_tokens, usage.cached_input_tokens)
        )
        completed = replace(
            trace,
            provider=response.provider,
            model_id=response.model,
            status=TraceStatus.SUCCEEDED,
            completed_at=datetime.now(UTC),
            latency_ms=usage.latency_ms if usage.latency_ms is not None else latency_ms,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cached_input_tokens=usage.cached_input_tokens,
            provider_request_id=usage.provider_request_id,
            usage_status="KNOWN" if usage_known else "UNKNOWN",
        )
        self.repository.transition_model_call(completed, {TraceStatus.STARTED})
        self.telemetry.emit(
            "model_call_completed",
            context=self.context(run, step_id=trace.step_id, agent_id=trace.agent_id),
            properties={
                "provider": response.provider,
                "model_id": response.model,
                "latency_ms": completed.latency_ms,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cached_input_tokens": usage.cached_input_tokens,
                "usage_status": completed.usage_status,
            },
            event_id=f"model-call-completed:{call_id}",
        )

    def fail_model_call(
        self,
        run: AgentRun,
        call_id: str,
        started_perf: float,
        *,
        error_code: str,
        retryable: bool,
    ) -> None:
        trace = next(
            (item for item in self.repository.list_model_calls(run.id) if item.id == call_id), None
        )
        if trace is None:
            return
        latency_ms = max(0, round((perf_counter() - started_perf) * 1000))
        self.repository.transition_model_call(
            replace(
                trace,
                status=TraceStatus.FAILED,
                completed_at=datetime.now(UTC),
                latency_ms=latency_ms,
                error_code=error_code,
                retryable=retryable,
            ),
            {TraceStatus.STARTED},
        )
        self.telemetry.emit(
            "model_call_failed",
            context=self.context(run, step_id=trace.step_id, agent_id=trace.agent_id),
            properties={
                "provider": trace.provider,
                "model_id": trace.model_id,
                "latency_ms": latency_ms,
                "error_code": error_code,
                "retryable": retryable,
            },
            event_id=f"model-call-failed:{call_id}",
        )

    def publish_response(
        self,
        run: AgentRun,
        *,
        outcome: str,
        safety_state: str,
        provider: str,
        model: str,
    ) -> InteractionResponse:
        response = InteractionResponse(
            owner_user_id=run.owner_user_id,
            owner_hash=owner_hash(run.owner_user_id, self.hash_secret),
            interaction_id=run.interaction_id or run.id,
            run_id=run.id,
            source_type=ResponseSourceType.AGENT_RUN,
            source_id=run.id,
            outcome=outcome,
            safety_state=safety_state,
            deployment_id=run.deployment_id or self.deployment_id,
            agent_version_set={run.agent_type: "1.0.0"},
            model_version_set=[{"provider": provider, "model": model}],
            environment=self.environment,
            data_classification=self.classification,
        )
        self.repository.create(response)
        self.telemetry.emit(
            "response_published",
            context=self.context(run),
            properties={
                "source_type": ResponseSourceType.AGENT_RUN.value,
                "outcome": outcome,
                "safety_state": safety_state,
                "feedback_eligible": True,
            },
            event_id=f"response-published:{response.id}",
        )
        return response

    def publish_analysis_response(
        self, job: AnalysisJob, result: AnalysisResult
    ) -> str:
        """Publish one immutable, feedback-eligible identity for an analysis result."""
        response_id = f"analysis-response-{job.id}"
        existing = self.repository.get_response(response_id)
        if existing:
            return existing.id
        interaction_id = job.correlation_id or job.id
        response = InteractionResponse(
            id=response_id,
            owner_user_id=job.owner_user_id,
            owner_hash=owner_hash(job.owner_user_id, self.hash_secret),
            interaction_id=interaction_id,
            run_id=job.id,
            source_type=ResponseSourceType.ANALYSIS,
            source_id=job.id,
            outcome="COMPLETED",
            safety_state=result.safety_state,
            deployment_id=self.deployment_id,
            model_version_set=[{
                "provider": result.provider,
                "model": result.provider_model,
                "prompt_version": result.prompt_version,
                "schema_version": result.schema_version,
            }],
            environment=self.environment,
            data_classification=self.classification,
        )
        self.repository.create(response)
        self.telemetry.emit(
            "response_published",
            context=TraceContext(
                correlation_id=interaction_id,
                interaction_id=interaction_id,
                run_id=job.id,
                owner_user_id=job.owner_user_id,
                pet_id=job.animal_id,
                deployment_id=self.deployment_id,
                environment=self.environment,
                data_classification=self.classification,
            ),
            properties={
                "source_type": ResponseSourceType.ANALYSIS.value,
                "outcome": "COMPLETED",
                "safety_state": result.safety_state,
                "feedback_eligible": True,
            },
            event_id=f"response-published:{response_id}",
        )
        return response.id

    def complete_run(self, run: AgentRun, response: InteractionResponse) -> None:
        trace = self.repository.get_run(run.id) or self.create_run(run)
        completed = datetime.now(UTC)
        duration = max(0, round((completed - trace.started_at).total_seconds() * 1000))
        self.repository.transition_run(
            replace(
                trace,
                status=TraceStatus.SUCCEEDED,
                outcome=response.outcome,
                safety_state=response.safety_state,
                response_id=response.id,
                completed_at=completed,
                duration_ms=duration,
            ),
            {TraceStatus.STARTED},
        )
        self.telemetry.emit(
            "run_completed",
            context=self.context(run),
            properties={
                "agent_type": run.agent_type,
                "outcome": response.outcome,
                "safety_state": response.safety_state,
                "duration_ms": duration,
            },
            event_id=f"run-completed:{run.id}",
        )

    def fail_run(self, run: AgentRun, *, error_code: str, retryable: bool) -> None:
        trace = self.repository.get_run(run.id) or self.create_run(run)
        completed = datetime.now(UTC)
        duration = max(0, round((completed - trace.started_at).total_seconds() * 1000))
        self.repository.transition_run(replace(trace, status=TraceStatus.FAILED,
            outcome="FAILED_RETRYABLE" if retryable else "FAILED_FINAL",
            completed_at=completed, duration_ms=duration), {TraceStatus.STARTED})
        self.telemetry.emit("run_failed", context=self.context(run), properties={
            "agent_type": run.agent_type, "error_code": error_code,
            "retryable": retryable, "duration_ms": duration,
        }, event_id=f"run-failed:{run.id}:{error_code}")
