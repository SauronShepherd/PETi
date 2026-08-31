from datetime import timedelta
from typing import Any


class FirestoreAgentRepository:
    """Firestore path adapter; mutation methods delegate to transactions."""
    def __init__(self, client: Any):
        self.client = client

    def _run(self, run_id):
        return self.client.collection("agent_runs").document(run_id)

    def create_run_with_initial_step(self, run, step):
        transaction = self.client.transaction()
        run_ref = self._run(run["id"])
        step_ref = run_ref.collection("steps").document(step["id"])
        transaction.create(run_ref, run)
        transaction.create(step_ref, step)
        transaction.commit()

    def get_run_owned(self, run_id, owner_user_id):
        snap = self._run(run_id).get()
        data = snap.to_dict() if snap.exists else None
        return data if data and data.get("owner_user_id") == owner_user_id else None

    def list_steps(self, run_id):
        return [dict(x.to_dict() or {}, id=x.id) for x in self._run(run_id).collection("steps").stream()]

    def ensure_steps(self, run_id, steps):
        batch = self.client.batch()
        existing = {step["id"] for step in self.list_steps(run_id)}
        for step in steps:
            if step["id"] not in existing:
                batch.create(self._run(run_id).collection("steps").document(step["id"]), {"run_id": run_id, "status": "READY", **step})
        batch.commit()

    def cancel_steps(self, run_id):
        steps = self.list_steps(run_id)
        batch = self.client.batch(); count = 0
        for step in steps:
            if step.get("status") in {"READY", "RETRY_SCHEDULED", "RUNNING"}:
                ref = self._run(run_id).collection("steps").document(step["id"])
                batch.update(ref, {"status": "CANCELLED", "lease_owner": None, "lease_expires_at": None})
                count += 1
        if count: batch.commit()
        return count

    def persist_claims(self, run_id, owner_user_id, claims):
        if not self.get_run_owned(run_id, owner_user_id):
            return False
        batch = self.client.batch()
        for index, claim in enumerate(claims):
            ref = self._run(run_id).collection("claims").document(str(index))
            batch.set(ref, {**dict(claim), "run_id": run_id, "owner_user_id": owner_user_id})
        batch.commit()
        return True

    def list_claims(self, run_id, owner_user_id):
        if not self.get_run_owned(run_id, owner_user_id):
            return []
        return [dict(x.to_dict() or {}, id=x.id) for x in self._run(run_id).collection("claims").stream()]

    def transition_run(self, run_id, owner_user_id, expected_version, status):
        transaction = self.client.transaction()
        ref = self._run(run_id)
        snap = ref.get(transaction=transaction)
        data = snap.to_dict() if snap.exists else None
        if not data or data.get("owner_user_id") != owner_user_id or int(data.get("run_version", 0)) != int(expected_version):
            return False
        data["status"] = status
        data["run_version"] = int(expected_version) + 1
        transaction.set(ref, data)
        transaction.commit()
        return True

    def claim_step(self, run_id, step_id, worker_id, now, lease_seconds=300):
        from google.cloud.firestore_v1.transaction import transactional
        transaction = self.client.transaction()
        ref = self._run(run_id).collection("steps").document(step_id)
        run_ref = self._run(run_id)
        @transactional
        def claim(tx):
            run_snap, step_snap = tx.get_all([run_ref, ref])
            run = run_snap.to_dict() if run_snap.exists else None
            step = step_snap.to_dict() if step_snap.exists else None
            if not run or not step or run.get("status") in {"COMPLETED", "CANCELED", "DELETED"}:
                return False
            if step.get("status") not in {"READY", "RETRY_SCHEDULED"}:
                return False
            expiry = step.get("lease_expires_at")
            if expiry and expiry > now:
                return False
            step.update({"status": "RUNNING", "lease_owner": worker_id, "lease_expires_at": now + timedelta(seconds=lease_seconds), "lease_epoch": int(step.get("lease_epoch", 0)) + 1, "attempt_count": int(step.get("attempt_count", 0)) + 1})
            tx.set(ref, step)
            return True
        return bool(claim(transaction))

    def renew_step_lease(self, run_id, step_id, worker_id, lease_epoch, now, lease_seconds=300):
        transaction = self.client.transaction()
        ref = self._run(run_id).collection("steps").document(step_id)
        snap = ref.get(transaction=transaction)
        step = snap.to_dict() if snap.exists else None
        if not step or step.get("status") != "RUNNING" or step.get("lease_owner") != worker_id or int(step.get("lease_epoch", 0)) != int(lease_epoch):
            return False
        step["lease_expires_at"] = now + timedelta(seconds=lease_seconds)
        transaction.set(ref, step)
        transaction.commit()
        return True

    def commit_step_result(self, run_id, step_id, worker_id, lease_epoch, result):
        from google.cloud.firestore_v1.transaction import transactional
        transaction = self.client.transaction()
        ref = self._run(run_id).collection("steps").document(step_id)
        @transactional
        def commit(tx):
            snap = tx.get(ref)
            if not hasattr(snap, "exists"):
                snap = next(iter(snap), None)
            if snap is None:
                return False
            step = snap.to_dict() if snap.exists else None
            if not step or step.get("status") != "RUNNING" or step.get("lease_owner") != worker_id or int(step.get("lease_epoch", 0)) != int(lease_epoch):
                return False
            step.update({"status": "SUCCEEDED", "result": result, "lease_owner": None, "lease_expires_at": None})
            tx.set(ref, step)
            return True
        return bool(commit(transaction))

    def schedule_step_retry(self, run_id, step_id, worker_id, lease_epoch, now):
        transaction = self.client.transaction(); ref = self._run(run_id).collection("steps").document(step_id)
        snap = ref.get(transaction=transaction); step = snap.to_dict() if snap.exists else None
        if not step or step.get("status") != "RUNNING" or step.get("lease_owner") != worker_id or int(step.get("lease_epoch", 0)) != int(lease_epoch): return False
        transaction.update(ref, {"status": "RETRY_SCHEDULED", "lease_owner": None, "lease_expires_at": None, "last_retry_at": now}); transaction.commit(); return True
