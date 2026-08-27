from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from app.analysis.domain import AnalysisJob
from app.analysis.repositories import InMemoryAnalysisJobRepository


def test_duplicate_delivery_claims_once_until_worker_releases_it():
    repository = InMemoryAnalysisJobRepository()
    repository.save(AnalysisJob("job", "u", "pet", "DOG", "PETI_CHECK", [], "k", "r", "f"))
    barrier = Barrier(2)

    def claim():
        barrier.wait()
        return repository.claim("job")

    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda _: claim(), range(2)))
    assert sum(item is not None for item in claims) == 1
    assert repository.get("job").attempt_count == 1
    repository.release_claim("job")
    assert repository.claim("job") is not None
