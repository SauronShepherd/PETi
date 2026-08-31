from copy import deepcopy
from datetime import timedelta
from threading import RLock


class MemoryAgentRepository:
    """Deterministic reference implementation; production correctness is CAS-shaped."""
    def __init__(self):
        self.runs, self.steps, self.claims = {}, {}, {}
        self.lock = RLock()

    def create_run_with_initial_step(self, run, step):
        with self.lock:
            if run["id"] in self.runs:
                return
            self.runs[run["id"]] = {**deepcopy(run), "run_version": int(run.get("run_version", 0))}
            self.steps[(run["id"], step["id"])] = deepcopy(step)

    def get_run_owned(self, run_id, owner_user_id):
        run = self.runs.get(run_id)
        return deepcopy(run) if run and run.get("owner_user_id") == owner_user_id else None

    def transition_run(self, run_id, owner_user_id, expected_version, status):
        with self.lock:
            run = self.runs.get(run_id)
            if not run or run.get("owner_user_id") != owner_user_id or run.get("run_version", 0) != expected_version:
                return False
            run["status"], run["run_version"] = status, expected_version + 1
            return True

    def list_steps(self, run_id):
        return [deepcopy(step) for (rid, _), step in self.steps.items() if rid == run_id]

    def ensure_steps(self, run_id, steps):
        with self.lock:
            for step in steps:
                key = (run_id, step["id"])
                if key not in self.steps:
                    self.steps[key] = deepcopy({"run_id": run_id, "status": "READY", **step})

    def cancel_steps(self, run_id):
        with self.lock:
            count = 0
            for (rid, _), step in self.steps.items():
                if rid == run_id and step.get("status") in {"READY", "RETRY_SCHEDULED", "RUNNING"}:
                    step.update({"status": "CANCELLED", "lease_owner": None, "lease_expires_at": None})
                    count += 1
            return count

    def persist_claims(self, run_id, owner_user_id, claims):
        run = self.get_run_owned(run_id, owner_user_id)
        if not run:
            return False
        self.claims[run_id] = deepcopy([{**claim, "run_id": run_id} for claim in claims])
        return True

    def list_claims(self, run_id, owner_user_id):
        return deepcopy(self.claims.get(run_id, [])) if self.get_run_owned(run_id, owner_user_id) else []

    def claim_step(self, run_id, step_id, worker_id, now, lease_seconds=300):
        with self.lock:
            step = self.steps.get((run_id, step_id))
            if not step or step.get("status") not in {"READY", "RETRY_SCHEDULED"}:
                return False
            expiry = step.get("lease_expires_at")
            if expiry and expiry > now:
                return False
            step.update({"status": "RUNNING", "lease_owner": worker_id, "lease_expires_at": now + timedelta(seconds=lease_seconds), "lease_epoch": int(step.get("lease_epoch", 0)) + 1, "attempt_count": int(step.get("attempt_count", 0)) + 1})
            return True

    def commit_step_result(self, run_id, step_id, worker_id, lease_epoch, result):
        with self.lock:
            step = self.steps.get((run_id, step_id))
            if not step or step.get("status") != "RUNNING" or step.get("lease_owner") != worker_id or step.get("lease_epoch") != lease_epoch:
                return False
            step.update({"status": "SUCCEEDED", "result": deepcopy(result), "lease_owner": None, "lease_expires_at": None})
            return True

    def schedule_step_retry(self, run_id, step_id, worker_id, lease_epoch, now):
        with self.lock:
            step = self.steps.get((run_id, step_id))
            if not step or step.get("status") != "RUNNING" or step.get("lease_owner") != worker_id or step.get("lease_epoch") != lease_epoch:
                return False
            step.update({"status": "RETRY_SCHEDULED", "lease_owner": None, "lease_expires_at": None, "last_retry_at": now})
            return True
