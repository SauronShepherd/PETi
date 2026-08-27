from app.analysis.domain import AnalysisJob, AnalysisResult, AnalysisStatus
from app.analysis.repositories import (
    InMemoryAnalysisJobRepository,
    InMemoryAnalysisResultRepository,
)


def test_repository_backed_worker_reload_short_circuits_completed_job():
    jobs, results = InMemoryAnalysisJobRepository(), InMemoryAnalysisResultRepository()
    job = AnalysisJob(
        "j", "u", "a", "DOG", "PETI_CHECK", ["m"], "k", "r", "f", status=AnalysisStatus.COMPLETED
    )
    result = AnalysisResult(
        "r",
        "j",
        "u",
        "a",
        "PETI_CHECK",
        "peti_check",
        "1",
        {},
        "VALID",
        "PASS",
        "CLEAR",
        [],
        "FAKE",
        "m",
        "1",
        "1",
        "1",
        "1",
        "DOG-v1",
        {},
        {},
    )
    jobs.save(job)
    results.save(result)
    assert jobs.get("j").status == AnalysisStatus.COMPLETED
    assert results.get_by_job("j").id == "r"
