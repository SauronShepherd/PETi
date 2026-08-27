from app.analysis.domain import AnalysisJob, AnalysisStatus
from app.analysis.repositories import InMemoryAnalysisJobRepository
from app.analysis.service import AnalysisService


def test_cancel_marks_active_job_and_preserves_completed_job():
    repo = InMemoryAnalysisJobRepository()
    active = AnalysisJob(
        "a", "u", "p", "DOG", "PETI_CHECK", ["m"], "k", "r", "f", status=AnalysisStatus.QUEUED
    )
    complete = AnalysisJob(
        "c", "u", "p", "DOG", "PETI_CHECK", ["m"], "k2", "r2", "f2", status=AnalysisStatus.COMPLETED
    )
    repo.save(active)
    repo.save(complete)
    service = AnalysisService.__new__(AnalysisService)
    service.jobs = {}
    service.job_repository = repo
    service.credits = type("Credits", (), {"reservations": {}, "release": lambda *args: None})()
    assert service.cancel("u", "a").status == AnalysisStatus.CANCELED
    assert service.cancel("u", "c").status == AnalysisStatus.COMPLETED
