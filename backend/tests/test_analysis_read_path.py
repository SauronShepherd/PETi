from app.analysis.domain import AnalysisJob, AnalysisResult
from app.analysis.repositories import (
    InMemoryAnalysisJobRepository,
    InMemoryAnalysisResultRepository,
)
from app.analysis.service import AnalysisService


def test_repository_backed_owner_reads_reload_jobs():
    repo = InMemoryAnalysisJobRepository()
    job = AnalysisJob("j", "owner", "pet", "DOG", "PETI_CHECK", ["m"], "k", "r", "f")
    repo.save(job)
    service = AnalysisService.__new__(AnalysisService)
    service.jobs = {}
    service.job_repository = repo
    assert service.get_owned_job("owner", "j").id == "j"
    assert service.get_owned_job("other", "j") is None


def test_repository_backed_result_is_loaded_for_owned_job():
    jobs = InMemoryAnalysisJobRepository()
    results = InMemoryAnalysisResultRepository()
    job = AnalysisJob("j", "owner", "pet", "DOG", "PETI_CHECK", ["m"], "k", "r", "f")
    jobs.save(job)
    result = AnalysisResult(
        "result", "j", "owner", "pet", "PETI_CHECK", "peti_check", "1.0.0", {},
        "VALID", "PASS", "CLEAR", [], "FAKE", "fake-v1", "1.0.0", "1.0.0",
        "PETI_CHECK-SAFETY-v1", "1.0.0", "DOG-v1", {}, {},
    )
    results.save(result)
    service = AnalysisService.__new__(AnalysisService)
    service.jobs = {}
    service.results = {}
    service.job_repository = jobs
    service.result_repository = results
    assert service.get_owned_result("owner", "j").id == "result"
    assert service.get_owned_result("other", "j") is None


def test_completed_result_read_does_not_touch_funding():
    jobs = InMemoryAnalysisJobRepository()
    results = InMemoryAnalysisResultRepository()
    job = AnalysisJob("j", "owner", "pet", "DOG", "PETI_CHECK", ["m"], "k", "r", "f")
    jobs.save(job)
    class FundingSpy:
        def __getattr__(self, name):
            raise AssertionError(f"funding called while reading result: {name}")
    service = AnalysisService.__new__(AnalysisService)
    service.jobs = {}
    service.results = {}
    service.job_repository = jobs
    service.result_repository = results
    service.credits = FundingSpy()
    assert service.get_owned_result("owner", "j") is None
