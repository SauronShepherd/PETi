"""Firestore persistence adapters for analysis jobs/results.

The worker uses these adapters behind the repository interfaces; no provider data is
written outside the normalized result document.
"""

from dataclasses import asdict
from threading import RLock
from typing import Any

from .domain import LEGAL_TRANSITIONS, AnalysisJob, AnalysisResult, AnalysisStatus
from .repositories import AnalysisJobRepository, AnalysisResultRepository


def _where(query: Any, field: str, value: Any) -> Any:
    from google.cloud.firestore_v1.base_query import FieldFilter  # type: ignore[import-untyped]

    try:
        return query.where(filter=FieldFilter(field, "==", value))
    except TypeError:
        return query.where(field, "==", value)


class FirestoreAnalysisJobRepository(AnalysisJobRepository):
    def __init__(self, client: Any):
        self.client = client
        self.claim_lock = RLock()

    def _ref(self, job_id):
        return self.client.collection("analysis_jobs").document(job_id)

    @staticmethod
    def _hydrate_job(raw: Any) -> AnalysisJob | None:
        try:
            data = dict(raw)
            data["status"] = AnalysisStatus(data["status"])
            return AnalysisJob(**data)
        except (KeyError, TypeError, ValueError):
            return None

    def get(self, job_id):
        snap = self._ref(job_id).get()
        if not snap.exists:
            return None
        return self._hydrate_job(snap.to_dict())

    def list_owned(self, owner_user_id, animal_id=None):
        query = _where(self.client.collection("analysis_jobs"), "owner_user_id", owner_user_id)
        if animal_id is not None:
            query = _where(query, "animal_id", animal_id)
        jobs = []
        for snap in query.stream():
            job = self._hydrate_job(snap.to_dict())
            if job is not None:
                jobs.append(job)
        return jobs

    def list_all(self):
        jobs = []
        for snap in self.client.collection("analysis_jobs").stream():
            job = self._hydrate_job(snap.to_dict())
            if job is not None:
                jobs.append(job)
        return jobs

    def save(self, job):
        data = asdict(job)
        data["status"] = job.status.value
        self._ref(job.id).set(data)
        return job

    def claim(self, job_id):
        ref = self._ref(job_id)
        if hasattr(self.client, "transaction"):
            from google.cloud.firestore_v1.transaction import (
                transactional,  # type: ignore[import-untyped]
            )

            transaction = self.client.transaction()

            @transactional
            def claim_in_transaction(tx):
                snap = tx.get(ref)
                if not snap.exists:
                    return None
                data = snap.to_dict()
                if data.get("status") not in {
                    AnalysisStatus.QUEUED.value,
                    AnalysisStatus.FAILED_RETRYABLE.value,
                }:
                    return None
                try:
                    attempt_count = int(data.get("attempt_count", 0)) + 1
                except (TypeError, ValueError):
                    return None
                tx.update(ref, {
                    "attempt_count": attempt_count,
                    "status": AnalysisStatus.PREPARING_MEDIA.value,
                })
                data["attempt_count"] = attempt_count
                data["status"] = AnalysisStatus.PREPARING_MEDIA.value
                return data

            data = claim_in_transaction(transaction)
            if data is None:
                return None
            return self._hydrate_job(data)

        # Lightweight adapters used by local tests do not expose transactions;
        # retain atomicity within that adapter while production uses Firestore
        # compare-and-set semantics above.
        with self.claim_lock:
            return self._claim_fallback(job_id)

    def _claim_fallback(self, job_id):
        job = self.get(job_id)
        if not job or job.status not in {
            AnalysisStatus.QUEUED,
            AnalysisStatus.FAILED_RETRYABLE,
        }:
            return None
        job.attempt_count += 1
        job.status = AnalysisStatus.PREPARING_MEDIA
        self.save(job)
        return job

    def transition(self, job_id, target):
        job = self.get(job_id)
        if not job:
            raise KeyError(job_id)
        if target not in LEGAL_TRANSITIONS.get(job.status, set()):
            raise ValueError(f"ILLEGAL_ANALYSIS_TRANSITION:{job.status}->{target}")
        job.status = target
        self.save(job)
        return job


class FirestoreAnalysisResultRepository(AnalysisResultRepository):
    def __init__(self, client: Any):
        self.client = client

    @staticmethod
    def _hydrate_result(raw: Any) -> AnalysisResult | None:
        try:
            return AnalysisResult(**dict(raw))
        except (KeyError, TypeError, ValueError):
            return None

    def get_by_job(self, job_id):
        docs = _where(self.client.collection("analysis_results"), "job_id", job_id).limit(1).stream()
        data = next(iter(docs), None)
        return self._hydrate_result(data.to_dict()) if data else None

    def save(self, result):
        existing = self.get_by_job(result.job_id)
        if existing and existing.id != result.id:
            raise ValueError("ANALYSIS_RESULT_IMMUTABLE")
        if existing and existing.id == result.id:
            return existing
        self.client.collection("analysis_results").document(result.id).create(asdict(result))
        return result
