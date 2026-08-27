import pytest
from app.privacy.lifecycle import AccountDeletionJob, DeletionPlan, DeletionTaskGate
from app.repositories.memory import InMemoryUserRepository


def test_deleted_firebase_identity_cannot_resurrect_a_user():
    users = InMemoryUserRepository()
    user = users.get_or_create("firebase-uid")
    users.tombstone("firebase-uid")
    assert user.deleted_at is not None
    with pytest.raises(ValueError, match="ACCOUNT_DELETED"):
        users.get_or_create("firebase-uid")


def test_queued_work_becomes_noop_after_account_freeze():
    gate = DeletionTaskGate()
    executed = []
    gate.freeze("user-1")

    result = gate.run_if_allowed("user-1", lambda: executed.append("ran"))

    assert result == {"status": "NO_OP", "reason": "ACCOUNT_DELETED"}
    assert executed == []


def test_freeze_cancels_registered_queued_work_and_blocks_new_work():
    gate = DeletionTaskGate()
    assert gate.enqueue("user-queued", "task-1")
    assert gate.enqueue("user-queued", "task-2")
    gate.freeze("user-queued")

    assert gate.cancel_queued("user-queued") == 2
    assert gate.queued_count("user-queued") == 0
    assert not gate.enqueue("user-queued", "task-3")


def test_account_deletion_job_freezes_tasks_before_cancel_step():
    gate = DeletionTaskGate()
    job = AccountDeletionJob(
        DeletionPlan("user-2", ["FREEZE_ACCOUNT", "CANCEL_QUEUED_WORK"], "delete-2"),
        step_runner=lambda _step, _owner: {},
        task_gate=gate,
    )

    job.run_once()

    assert gate.is_frozen("user-2")
    assert gate.run_if_allowed("user-2", lambda: "must-not-run")["status"] == "NO_OP"


def test_account_deletion_job_cancels_queued_work():
    gate = DeletionTaskGate()
    gate.enqueue("user-3", "task-1")
    job = AccountDeletionJob(
        DeletionPlan("user-3", ["FREEZE_ACCOUNT", "CANCEL_QUEUED_WORK"], "delete-3"),
        task_gate=gate,
    )

    job.run_once()
    result = job.run_once()

    assert result["step_result"] == {"cancelled": 1}
    assert gate.queued_count("user-3") == 0
