from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from app.analysis.domain import AnalysisJob, AnalysisResult, AnalysisStatus
from app.analysis.firestore_repositories import (
    FirestoreAnalysisJobRepository,
    FirestoreAnalysisResultRepository,
)


class Snapshot:
    def __init__(self, data=None):
        self.data, self.exists = data, data is not None

    def to_dict(self):
        return dict(self.data)


class Doc:
    def __init__(self, store, key):
        self.store, self.key = store, key

    def get(self):
        return Snapshot(self.store.get(self.key))

    def set(self, data):
        self.store[self.key] = data

    def create(self, data):
        if self.key in self.store:
            raise ValueError("exists")
        self.store[self.key] = data


class Query:
    def __init__(self, store):
        self.store = store

    def where(self, *args):
        return self

    def limit(self, *args):
        return self

    def stream(self):
        return [Snapshot(x) for x in self.store.values()]


class Collection(Query):
    def document(self, key):
        return Doc(self.store, key)


class Client:
    def __init__(self):
        self.collections = {}

    def collection(self, name):
        return Collection(self.collections.setdefault(name, {}))


def test_firestore_job_round_trip_and_claim():
    client = Client()
    repo = FirestoreAnalysisJobRepository(client)
    job = AnalysisJob("j", "u", "a", "DOG", "PETI_CHECK", ["m"], "k", "r", "f", status=AnalysisStatus.QUEUED)
    repo.save(job)
    assert repo.get("j").id == "j"
    assert repo.claim("j").attempt_count == 1


def test_firestore_fallback_claim_is_single_winner_under_concurrency():
    client = Client()
    repo = FirestoreAnalysisJobRepository(client)
    repo.save(AnalysisJob("concurrent", "u", "a", "DOG", "PETI_CHECK", [], "k", "r", "f", status=AnalysisStatus.QUEUED))
    barrier = Barrier(2)

    def claim():
        barrier.wait()
        return repo.claim("concurrent")

    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda _: claim(), range(2)))

    assert sum(item is not None for item in claims) == 1
    assert repo.get("concurrent").attempt_count == 1


def test_firestore_result_immutable():
    client = Client()
    repo = FirestoreAnalysisResultRepository(client)
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
    repo.save(result)
    replacement = AnalysisResult(
        "r2",
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
    with pytest.raises(ValueError, match="IMMUTABLE"):
        repo.save(replacement)
def test_claim_fails_closed_on_malformed_attempt_count(monkeypatch):
    monkeypatch.setattr(
        "google.cloud.firestore_v1.transaction.transactional",
        lambda function: function,
    )
    class Snapshot:
        exists = True

        def to_dict(self):
            return {"status": "QUEUED", "attempt_count": "not-a-number"}

    class Transaction:
        def get(self, ref):
            return Snapshot()

    class Client:
        def collection(self, name):
            return self

        def document(self, name):
            return self

        def transaction(self):
            return Transaction()

    repository = FirestoreAnalysisJobRepository(Client())

    assert repository.claim("malformed") is None


def test_analysis_reads_skip_malformed_durable_rows():
    client = Client()
    client.collection("analysis_jobs").document("bad").set({"status": "NOT_A_STATUS"})
    repository = FirestoreAnalysisJobRepository(client)

    assert repository.get("bad") is None
    assert repository.list_all() == []


def test_analysis_result_reads_skip_malformed_durable_rows():
    client = Client()
    client.collection("analysis_results").document("bad").set({"job_id": "job"})
    repository = FirestoreAnalysisResultRepository(client)

    assert repository.get_by_job("job") is None
