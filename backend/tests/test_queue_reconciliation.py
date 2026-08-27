from datetime import UTC, datetime, timedelta

from app.analysis.domain import AnalysisJob, AnalysisStatus
from app.analysis.queue import FakeTaskQueue
from app.analysis.repositories import InMemoryAnalysisJobRepository
from app.analysis.service import AnalysisService


def test_reconciler_requeues_old_pre_queue_job_with_deterministic_task_id():
    repo = InMemoryAnalysisJobRepository()
    queue = FakeTaskQueue()
    job = AnalysisJob(
        "j",
        "u",
        "a",
        "DOG",
        "PETI_CHECK",
        ["m"],
        "k",
        "r",
        "f",
        status=AnalysisStatus.FUNDING_RESERVED,
        created_at=datetime.now(UTC) - timedelta(minutes=5),
    )
    repo.save(job)
    service = AnalysisService.__new__(AnalysisService)
    service.job_repository = repo
    service.queue = queue
    assert service.reconcile_queue(60) == ["j"]
    assert repo.get("j").status == AnalysisStatus.QUEUED
    assert queue.items[0].task_id == "analysis-j"
