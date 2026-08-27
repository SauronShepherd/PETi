from dataclasses import asdict
from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4

from app.ai.preparation.core import MediaPreparer
from app.ai.providers.base import ProviderError
from app.ai.registry import PROMPTS, SCHEMAS
from app.ai.validation.core import validate_smoke_payload
from app.media.domain import MediaType
from app.peti_check.contracts import PetiCheckResultV1
from app.peti_check.guardrails import sanitize_context, validate_payload_text
from app.safety.engine import evaluate_safety

from .domain import AnalysisJob, AnalysisResult, AnalysisStatus, transition
from .queue import FakeTaskQueue, TaskQueue


class AnalysisError(ValueError):
    pass


def _provider_acceptance(response: object) -> bool:
    accepted = getattr(response, "accepted", None)
    if not isinstance(accepted, bool):
        raise AnalysisError("PROVIDER_RESPONSE_INVALID")
    return accepted


def _usage_units(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AnalysisError("PROVIDER_USAGE_INVALID")
    return value


class FakeAIProvider:
    name = "FAKE"
    model = "fake-platform-smoke-v1"

    def analyze(self, prepared_media, user_context=None):
        return {
            "summary": "Local platform smoke analysis completed.",
            "evidence": [{"media_id": x, "observation": "media accepted"} for x in prepared_media],
            "confidence": "UNSPECIFIED",
        }, {
            "input_tokens": 12,
            "output_tokens": 18,
            "latency_ms": 1,
            "provider_request_id": str(uuid4()),
        }


class AnalysisService:
    @staticmethod
    def merge_safety(decision_state: str, model_state: str | None) -> str:
        """Combine deterministic and provider states using maximum severity."""
        severity = {
            "CLEAR": 0, "NORMAL_INFORMATION": 0,
            "MONITOR": 1, "REVIEW": 1, "PROFESSIONAL_REVIEW_RECOMMENDED": 1,
            "PROMPT_VETERINARY_CONTACT": 2, "INSUFFICIENT_EVIDENCE": 2,
            "URGENT": 3,
        }
        candidates = [decision_state]
        if model_state in severity:
            candidates.append(model_state)
        return max(candidates, key=lambda state: severity.get(state, 2))

    def __init__(
        self,
        pets,
        media,
        credits,
        queue=None,
        provider=None,
        job_repository=None,
        result_repository=None,
        modality_flags=None,
        max_attempts: int = 5,
        ai_enabled: bool = True,
        provider_enabled: bool = True,
        model_enabled: bool = True,
        possible_interpretations_enabled: bool = True,
        analytics=None,
        costs=None,
        economics_policy=None,
    ):
        self.pets, self.media, self.credits = pets, media, credits
        self.queue: TaskQueue = queue or FakeTaskQueue()
        self.provider = provider or FakeAIProvider()
        self.jobs: dict[str, AnalysisJob] = {}
        self.results: dict[str, AnalysisResult] = {}
        self.idempotency: dict[tuple[str, str], tuple[str, str]] = {}
        self.lock = RLock()
        self.configured_ai_enabled = ai_enabled
        self.ai_enabled = ai_enabled
        self.provider_enabled = provider_enabled
        self.model_enabled = model_enabled
        self.possible_interpretations_enabled = possible_interpretations_enabled
        self.analytics = analytics
        self.costs = costs
        self.economics_policy = economics_policy
        self.provider_kill_switches: dict[str, bool] = {}
        self.model_kill_switches: dict[str, bool] = {}
        self.species_kill_switches: dict[str, bool] = {}
        self.preparer = MediaPreparer()
        self.job_repository = job_repository
        self.result_repository = result_repository
        raw_modality_flags = modality_flags or {
            MediaType.IMAGE: True,
            MediaType.VIDEO: False,
            MediaType.AUDIO: False,
            MediaType.DOCUMENT: False,
        }
        self.modality_flags = {
            MediaType(key) if isinstance(key, str) else key: enabled
            for key, enabled in raw_modality_flags.items()
        }
        self.max_attempts = max_attempts

    def set_global_kill_switch(self, enabled: bool) -> bool:
        if not isinstance(enabled, bool):
            raise TypeError("AI_GLOBAL_KILL_SWITCH_INVALID")
        self.ai_enabled = self.configured_ai_enabled and not enabled
        return self.ai_enabled

    def set_runtime_kill_switch(self, scope: str, key: str, enabled: bool) -> bool:
        targets = {
            "provider": self.provider_kill_switches,
            "model": self.model_kill_switches,
            "species": self.species_kill_switches,
        }
        if scope not in targets or not key or len(key) > 120:
            raise ValueError("AI_KILL_SWITCH_SCOPE_INVALID")
        if not isinstance(enabled, bool):
            raise TypeError("AI_KILL_SWITCH_VALUE_INVALID")
        targets[scope][key] = enabled
        return enabled

    def create(
        self,
        owner,
        animal_id,
        analysis_type,
        media_ids,
        user_context,
        funding_id,
        key,
        correlation_id=None,
    ):
        if not key:
            raise AnalysisError("ANALYSIS_IDEMPOTENCY_KEY_REQUIRED")
        if analysis_type == "PETI_CHECK" and user_context and len(user_context) > 500:
            raise AnalysisError("PETI_CHECK_CONTEXT_TOO_LONG")
        user_context = sanitize_context(user_context)
        if analysis_type not in {"PLATFORM_MULTIMODAL_SMOKE", "PETI_CHECK"}:
            raise AnalysisError("ANALYSIS_TYPE_UNAVAILABLE")
        pet = self.pets.get(owner, animal_id)
        if not pet:
            raise AnalysisError("ANALYSIS_ANIMAL_NOT_FOUND")
        pack = getattr(self.pets, "species", None)
        pack = pack.get_capability_pack(pet.species) if pack else None
        if not pack or analysis_type not in pack.enabled_analysis_types:
            raise AnalysisError("ANALYSIS_TYPE_UNAVAILABLE_FOR_SPECIES")
        if not media_ids:
            raise AnalysisError(
                "PETI_CHECK_MEDIA_REQUIRED" if analysis_type == "PETI_CHECK" else "ANALYSIS_MEDIA_REQUIRED"
            )
        if analysis_type == "PETI_CHECK" and len(media_ids) > 5:
            raise AnalysisError("PETI_CHECK_TOO_MANY_MEDIA_ITEMS")
        for media_id in media_ids:
            asset = self.media.assets.get(media_id)
            if not asset or asset.owner_user_id != owner:
                raise AnalysisError("ANALYSIS_MEDIA_NOT_OWNED")
            if str(asset.status) != "READY":
                raise AnalysisError("ANALYSIS_MEDIA_NOT_READY")
            if analysis_type == "PETI_CHECK" and not self.modality_flags.get(
                asset.media_type, False
            ):
                raise AnalysisError("PETI_CHECK_MEDIA_UNSUPPORTED")
            capabilities = getattr(self.provider, "capabilities", None)
            if capabilities and asset.media_type.value not in capabilities.media_types:
                raise AnalysisError("ANALYSIS_PROVIDER_MEDIA_UNSUPPORTED")
        capabilities = getattr(self.provider, "capabilities", None)
        if capabilities and len(media_ids) > capabilities.max_media_items:
            raise AnalysisError("ANALYSIS_PROVIDER_MEDIA_LIMIT")
        reservation = self.credits.reservations.get(funding_id)
        if not reservation or reservation.user_id != owner or str(reservation.status) != "RESERVED":
            raise AnalysisError("ANALYSIS_FUNDING_INVALID")
        fingerprint = f"{animal_id}|{analysis_type}|{','.join(sorted(media_ids))}|{funding_id}"
        with self.lock:
            old = self.idempotency.get((owner, key))
            if old:
                if old[0] != fingerprint:
                    raise AnalysisError("ANALYSIS_IDEMPOTENCY_KEY_REUSE_CONFLICT")
                return self.jobs[old[1]]
            job = AnalysisJob(
                uuid4().hex,
                owner,
                animal_id,
                pet.species,
                analysis_type,
                media_ids,
                key,
                job_id_request(key),
                funding_id,
                user_context=user_context,
                correlation_id=correlation_id,
            )
            if analysis_type == "PETI_CHECK":
                job.prompt_id, job.schema_id = "peti_check", "peti_check"
                job.prompt_version, job.schema_version = "1.0.0", "1.0.0"
                job.safety_policy_version = "PETI_CHECK-SAFETY-v1"
            job.prompt_version = PROMPTS.resolve(job.prompt_id).version
            job.schema_version = SCHEMAS.resolve(job.schema_id).version
            job.prompt_hash = PROMPTS.resolve(job.prompt_id).sha256
            job.schema_hash = SCHEMAS.resolve(job.schema_id).sha256
            self.jobs[job.id] = job
            if self.job_repository:
                self.job_repository.save(job)
            self.idempotency[(owner, key)] = (fingerprint, job.id)
            job.status = transition(job.status, AnalysisStatus.QUEUED)
            job.queued_at = datetime.now(UTC)
            self.queue.enqueue_analysis(job.id, f"analysis-{job.id}")
            if self.job_repository:
                self.job_repository.save(job)
            return job

    def process_next(self):
        task = self.queue.pop()
        if not task:
            return None
        return self.process(task.job_id)

    def reconcile_queue(
        self, older_than_seconds: int = 60, now: datetime | None = None
    ) -> list[str]:
        now = now or datetime.now(UTC)
        jobs = self.job_repository.list_all() if self.job_repository else list(self.jobs.values())
        repaired = []
        for job in jobs:
            if job.status != AnalysisStatus.FUNDING_RESERVED:
                continue
            if (now - job.created_at).total_seconds() < older_than_seconds:
                continue
            if self.queue.enqueue_analysis(job.id, f"analysis-{job.id}"):
                job.status = AnalysisStatus.QUEUED
                job.queued_at = now
                if self.job_repository:
                    self.job_repository.save(job)
                repaired.append(job.id)
        return repaired

    def process(self, job_id):
        job = self.jobs.get(job_id)
        if not job and self.job_repository:
            job = self.job_repository.get(job_id)
            if job:
                self.jobs[job_id] = job
        if not job:
            raise AnalysisError("ANALYSIS_NOT_FOUND")
        if job.status == AnalysisStatus.COMPLETED:
            return self.results.get(job.id) or (
                self.result_repository.get_by_job(job.id) if self.result_repository else None
            )
        if self.economics_policy and job.analysis_type in self.economics_policy.profiles:
            try:
                self.economics_policy.authorize(job.analysis_type)
            except ValueError as exc:
                job.status = transition(job.status, AnalysisStatus.FAILED_FINAL)
                job.last_error_code = str(exc)
                job.failed_at = datetime.now(UTC)
                self.credits.release(job.funding_reservation_id, str(exc))
                if self.job_repository:
                    self.job_repository.save(job)
                return None
        provider_name = str(getattr(self.provider, "name", "UNKNOWN"))
        provider_model = str(getattr(self.provider, "model", "UNKNOWN"))
        runtime_disabled = (
            self.provider_kill_switches.get(provider_name, False)
            or self.model_kill_switches.get(provider_model, False)
            or self.species_kill_switches.get(str(job.species), False)
        )
        if runtime_disabled or not self.ai_enabled or not self.provider_enabled or not self.model_enabled:
            reason = (
                "AI_RUNTIME_KILL_SWITCH"
                if runtime_disabled
                else "AI_DISABLED"
                if not self.ai_enabled
                else "AI_PROVIDER_DISABLED"
                if not self.provider_enabled
                else "AI_MODEL_DISABLED"
            )
            job.status = transition(job.status, AnalysisStatus.FAILED_FINAL)
            job.last_error_code = reason
            job.failed_at = datetime.now(UTC)
            self.credits.release(job.funding_reservation_id, reason)
            if self.job_repository:
                self.job_repository.save(job)
            return None
        if self.job_repository:
            claimed = self.job_repository.claim(job_id)
            if claimed is None:
                existing = (
                    self.result_repository.get_by_job(job_id) if self.result_repository else None
                )
                if existing:
                    self.results[job_id] = existing
                return existing
            job = claimed
        else:
            job.attempt_count += 1
        job.started_at = datetime.now(UTC)
        if self.analytics and job.analysis_type == "PETI_CHECK":
            self.analytics.record("check_started", user_id=job.owner_user_id, check_id=job.id)
        provider_accepted = False
        try:
            job.status = AnalysisStatus.PREPARING_MEDIA
            if self.job_repository:
                self.job_repository.save(job)
            resolved_media = self.media.resolve_ai_media(
                job.owner_user_id, job.media_asset_ids, job.animal_id
            )
            prepared = self.preparer.prepare(resolved_media)
            job.status = AnalysisStatus.CALLING_PROVIDER
            if self.job_repository:
                self.job_repository.save(job)
            job.provider_call_count += 1
            try:
                response = self.provider.analyze(
                    prepared, PROMPTS.resolve(job.prompt_id).content, job.user_context
                )
            except TypeError:
                response = self.provider.analyze(list(job.media_asset_ids))
            if hasattr(response, "payload"):
                payload, usage = response.payload, response.usage.__dict__
                job.provider, job.provider_model = response.provider, response.model
                job.provider_config_version = getattr(self.provider, "config_version", "1.0.0")
                provider_accepted = _provider_acceptance(response)
            else:
                payload, usage = response
                provider_accepted = True
            if not provider_accepted:
                raise AnalysisError("PROVIDER_REQUEST_NOT_ACCEPTED")
            self.credits.consume(job.funding_reservation_id, f"analysis-{job.id}")
            if "evidence" in payload and "observations" not in payload:
                payload["observations"] = payload["evidence"]
            validation = validate_smoke_payload(payload)
            if not validation.valid:
                raise AnalysisError("AI_OUTPUT_SCHEMA_INVALID")
            if job.analysis_type == "PETI_CHECK":
                try:
                    payload["source_media_ids"] = list(job.media_asset_ids)
                    payload = PetiCheckResultV1.from_payload(payload).to_dict()
                    if not self.possible_interpretations_enabled:
                        payload["possible_interpretations"] = []
                except (TypeError, ValueError) as exc:
                    raise AnalysisError("PETI_CHECK_SCHEMA_INVALID") from exc
            job.status = AnalysisStatus.VALIDATING_OUTPUT
            if self.job_repository:
                self.job_repository.save(job)
            job.status = AnalysisStatus.APPLYING_GUARDRAILS
            violations = validate_payload_text(payload)
            if violations:
                raise AnalysisError("AI_SEMANTIC_GUARDRAIL_VIOLATION:" + ",".join(violations))
            job.status = AnalysisStatus.APPLYING_SAFETY
            decision = evaluate_safety(payload, job.user_context)
            model_safety = payload.get("safety_state")
            safety = self.merge_safety(decision.state, model_safety)
            job.status = AnalysisStatus.PERSISTING_RESULT
            if self.job_repository:
                self.job_repository.save(job)
            result = AnalysisResult(
                uuid4().hex,
                job.id,
                job.owner_user_id,
                job.animal_id,
                job.analysis_type,
                job.schema_id,
                job.schema_version,
                payload,
                "VALID",
                "PASS",
                safety,
                decision.reasons,
                job.provider,
                job.provider_model,
                job.prompt_version,
                job.guardrail_version,
                job.safety_policy_version,
                job.media_preparation_version,
                job.species_pack_version,
                usage,
                {
                    "operation_type": "PETI_CHECK"
                    if job.analysis_type == "PETI_CHECK"
                    else "AI_PHOTO_STANDARD",
                    "cost_profile_version": "1.0.0",
                    "funding_source_summary": "CREDIT_RESERVATION",
                    "credits_consumed": 1,
                    "provider_cost_estimate": None,
                    "preprocessing_cost_estimate": None,
                    "total_variable_cost_estimate": None,
                    "currency": None,
                    "calculation_version": "1.0.0",
                },
                prompt_hash=job.prompt_hash,
                schema_hash=job.schema_hash,
            )
            if self.costs:
                operation_type = "PETI_CHECK" if job.analysis_type == "PETI_CHECK" else "AI_PHOTO_STANDARD"
                input_units = _usage_units(usage.get("input_tokens"))
                output_units = _usage_units(usage.get("output_tokens"))
                self.costs.record(job.id, operation_type, input_units + output_units, input_units + output_units, job.provider)
            self.results[job.id] = result
            if self.result_repository:
                self.result_repository.save(result)
            job.status, job.completed_at = AnalysisStatus.COMPLETED, datetime.now(UTC)
            if self.analytics and job.analysis_type == "PETI_CHECK":
                self.analytics.record("check_completed", user_id=job.owner_user_id, check_id=job.id)
                self.analytics.record("check_safety_state", user_id=job.owner_user_id, check_id=job.id, safety_state=safety)
                if safety == "INSUFFICIENT_EVIDENCE":
                    self.analytics.record("check_abstained", user_id=job.owner_user_id, check_id=job.id)
            if self.job_repository:
                self.job_repository.save(job)
                if hasattr(self.job_repository, "release_claim"):
                    self.job_repository.release_claim(job.id)
            return result
        except Exception as exc:
            retryable = (
                isinstance(exc, ProviderError)
                and exc.retryable
                and job.attempt_count < self.max_attempts
            )
            job.status, job.last_error_code, job.failed_at = (
                AnalysisStatus.FAILED_RETRYABLE if retryable else AnalysisStatus.FAILED_FINAL,
                str(exc),
                datetime.now(UTC),
            )
            if self.analytics and job.analysis_type == "PETI_CHECK":
                self.analytics.record("check_failed", user_id=job.owner_user_id, check_id=job.id)
            if self.job_repository:
                self.job_repository.save(job)
                if hasattr(self.job_repository, "release_claim"):
                    self.job_repository.release_claim(job.id)
            if retryable:
                self.queue.enqueue_analysis(job.id, f"analysis-{job.id}-retry-{job.attempt_count}")
            elif not provider_accepted:
                try:
                    self.credits.release(job.funding_reservation_id, str(exc))
                except Exception:  # noqa: BLE001, S110
                    pass
            raise

    @staticmethod
    def public_job(job):
        data = asdict(job)
        data["status"] = str(job.status)
        return data

    @staticmethod
    def public_result(result):
        return asdict(result)

    def get_owned_result(self, owner_user_id, job_id):
        job = self.get_owned_job(owner_user_id, job_id)
        if not job:
            return None
        result = self.results.get(job_id)
        if result is None and self.result_repository:
            result = self.result_repository.get_by_job(job_id)
            if result:
                self.results[job_id] = result
        return result

    def get_owned_job(self, owner_user_id, job_id):
        job = self.jobs.get(job_id)
        if not job and self.job_repository:
            job = self.job_repository.get(job_id)
            if job:
                self.jobs[job.id] = job
        return job if job and job.owner_user_id == owner_user_id else None

    def list_owned_jobs(self, owner_user_id, animal_id=None):
        jobs = (
            self.job_repository.list_owned(owner_user_id, animal_id)
            if self.job_repository
            else list(self.jobs.values())
        )
        for job in jobs:
            self.jobs[job.id] = job
        return [
            job
            for job in jobs
            if job.owner_user_id == owner_user_id
            and (animal_id is None or job.animal_id == animal_id)
        ]

    def cancel(self, owner_user_id, job_id):
        job = self.get_owned_job(owner_user_id, job_id)
        if not job:
            raise AnalysisError("ANALYSIS_NOT_FOUND")
        if job.status in {
            AnalysisStatus.COMPLETED,
            AnalysisStatus.FAILED_FINAL,
            AnalysisStatus.CANCELED,
        }:
            return job
        job.status = AnalysisStatus.CANCELED
        job.last_error_code = "CANCELED_BY_USER"
        if self.job_repository:
            self.job_repository.save(job)
        reservation = self.credits.reservations.get(job.funding_reservation_id)
        if reservation and str(reservation.status) == "RESERVED":
            self.credits.release(job.funding_reservation_id, "CANCELED_BY_USER")
        return job


def job_id_request(key):
    return f"analysis-request-{key}"
