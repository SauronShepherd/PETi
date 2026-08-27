from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier

from app.privacy.service import PrivacyService


class Store:
    def __init__(self):
        self.rows = {}

    def all(self, collection):
        return list(self.rows.values()) if collection == "privacy_deletion_jobs" else []

    def put_raw(self, collection, key, data):
        self.rows[key] = data


class EmptyPets:
    def list(self, owner):
        return []


def make_privacy(store, clock=None):
    return PrivacyService(
        EmptyPets(),
        type("Media", (), {"list_owned": lambda self, owner: []})(),
        type("Phase6", (), {"measurements": {}, "care": {}, "remove_device_registrations": lambda self, owner: 0})(),
        store=store,
        clock=clock,
    )


def test_completed_deletion_job_hydrates_and_replays_idempotently():
    store = Store()
    first = make_privacy(store)
    result = first.delete_account("owner-1", confirm=True, idempotency_key="delete-1")
    assert result["job"]["state"] == "COMPLETE"

    restarted = make_privacy(store)
    replay = restarted.delete_account("owner-1", confirm=True, idempotency_key="delete-1")
    assert replay["idempotent_replay"] is True
    assert replay["job"]["state"] == "COMPLETE"


def test_deletion_completion_uses_injected_clock():
    instant = datetime(2026, 1, 1, tzinfo=UTC)
    result = make_privacy(Store(), clock=lambda: instant).delete_account(
        "owner-clock", confirm=True, idempotency_key="delete-clock"
    )
    assert result["completed_at"] == instant


def test_concurrent_account_deletion_is_single_execution():
    service = make_privacy(Store())
    calls = []
    original = service._perform_delete_account

    def counted_delete(owner, plan):
        calls.append(owner)
        return original(owner, plan)

    service._perform_delete_account = counted_delete
    barrier = Barrier(2)

    def delete():
        barrier.wait()
        return service.delete_account("owner-concurrent", confirm=True, idempotency_key="delete-once")

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: delete(), range(2)))

    assert len(calls) == 1
    assert sum(result.get("idempotent_replay", False) for result in results) == 1
