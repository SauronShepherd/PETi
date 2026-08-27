from threading import RLock

from .domain import LEGAL_TRANSITIONS, AnalysisJob, AnalysisResult, AnalysisStatus


class AnalysisJobRepository:
    def get(self, job_id: str) -> AnalysisJob | None:
        raise NotImplementedError

    def save(self, job: AnalysisJob) -> AnalysisJob:
        raise NotImplementedError

    def claim(self, job_id: str) -> AnalysisJob | None:
        raise NotImplementedError

    def transition(self, job_id: str, target: AnalysisStatus) -> AnalysisJob:
        raise NotImplementedError

    def list_owned(self, owner_user_id: str, animal_id: str | None = None) -> list[AnalysisJob]:
        raise NotImplementedError

    def list_all(self) -> list[AnalysisJob]:
        raise NotImplementedError


class AnalysisResultRepository:
    def get_by_job(self, job_id: str) -> AnalysisResult | None:
        raise NotImplementedError

    def save(self, result: AnalysisResult) -> AnalysisResult:
        raise NotImplementedError


class InMemoryAnalysisJobRepository(AnalysisJobRepository):
    def __init__(self):
        self.items: dict[str, AnalysisJob] = {}
        self.lock = RLock()
        self.claimed: set[str] = set()

    def get(self, job_id):
        return self.items.get(job_id)

    def list_owned(self, owner_user_id, animal_id=None):
        return [
            job
            for job in self.items.values()
            if job.owner_user_id == owner_user_id
            and (animal_id is None or job.animal_id == animal_id)
        ]

    def list_all(self):
        return list(self.items.values())

    def save(self, job):
        with self.lock:
            self.items[job.id] = job
        return job

    def claim(self, job_id):
        with self.lock:
            job = self.items.get(job_id)
            if not job or job.status in {
                AnalysisStatus.COMPLETED,
                AnalysisStatus.FAILED_FINAL,
                AnalysisStatus.CANCELED,
            }:
                return None
            if job_id in self.claimed:
                return None
            self.claimed.add(job_id)
            job.attempt_count += 1
            return job

    def release_claim(self, job_id):
        with self.lock:
            self.claimed.discard(job_id)

    def transition(self, job_id, target):
        with self.lock:
            job = self.items[job_id]
            if target not in LEGAL_TRANSITIONS.get(job.status, set()):
                raise ValueError(f"ILLEGAL_ANALYSIS_TRANSITION:{job.status}->{target}")
            job.status = target
            return job


class InMemoryAnalysisResultRepository(AnalysisResultRepository):
    def __init__(self):
        self.items: dict[str, AnalysisResult] = {}
        self.lock = RLock()

    def get_by_job(self, job_id):
        return next((x for x in self.items.values() if x.job_id == job_id), None)

    def save(self, result):
        with self.lock:
            existing = self.get_by_job(result.job_id)
            if existing and existing.id != result.id:
                raise ValueError("ANALYSIS_RESULT_IMMUTABLE")
            self.items[result.id] = result
        return result
