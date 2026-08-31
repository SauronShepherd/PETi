from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import ClassVar


class RetentionPolicy:
    CLASSES: ClassVar[set[str]] = {"USER_UNTIL_DELETE", "TRANSIENT_PROCESSING", "SHORT_LIVED_AUDIT", "BOUNDED_BILLING_AUDIT"}
    def validate(self, retention_class):
        if retention_class not in self.CLASSES: raise ValueError("RETENTION_CLASS_INVALID")
        return retention_class


@dataclass
class DeletionPlan:
    owner_user_id: str
    entities: list[str]
    idempotency_key: str
    dependencies: dict[str, tuple[str, ...]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class DeletionJobState:
    FREEZE_ACCOUNT = "FREEZE_ACCOUNT"
    CANCEL_QUEUED_WORK = "CANCEL_QUEUED_WORK"
    DELETE_DERIVED_DATA = "DELETE_DERIVED_DATA"
    DELETE_CANONICAL_DATA = "DELETE_CANONICAL_DATA"
    DELETE_OBJECTS = "DELETE_OBJECTS"
    VERIFY_NO_RESIDUAL_DATA = "VERIFY_NO_RESIDUAL_DATA"
    COMPLETE = "COMPLETE"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"


class DeletionDependencyResolver:
    ORDER: ClassVar[list[str]] = ["tasks", "notifications", "search_projection", "memory", "lab", "reports", "analyses", "records", "measurements", "media", "pets", "account"]
    def plan(self, owner, idempotency_key):
        return DeletionPlan(owner, list(self.ORDER), idempotency_key, self.dependencies(owner))

    def ordered_domains(self, plan: DeletionPlan) -> tuple[str, ...]:
        """Return the executable domain order carried by a deletion plan."""
        allowed = set(plan.entities)
        return tuple(domain for domain in self.ORDER if domain in allowed)

    def dependencies(self, owner: str) -> dict[str, tuple[str, ...]]:
        return {
            "reports": ("analyses", "records", "measurements", "timeline"),
            "lab": ("agent_runs", "feedback", "reviews", "comments"),
            "analyses": ("media", "pets"),
            "records": ("candidate_facts", "documented_facts"),
            "candidate_facts": ("records",),
            "documented_facts": ("measurements", "timeline"),
            "measurements": ("weekly_reports",),
            "timeline": ("weekly_reports",),
            "media": ("pets",),
            "pets": ("account",),
            "account": (),
        }


class DeletionTaskGate:
    """Process-local tombstone gate for queued work adapters."""

    def __init__(self):
        self._frozen: set[str] = set()
        self._queued: dict[str, set[str]] = {}
        self._lock = RLock()

    def freeze(self, owner_user_id: str) -> None:
        with self._lock:
            self._frozen.add(owner_user_id)

    def is_frozen(self, owner_user_id: str) -> bool:
        with self._lock:
            return owner_user_id in self._frozen

    def enqueue(self, owner_user_id: str, task_id: str) -> bool:
        """Register local queued work; frozen accounts cannot enqueue new work."""
        with self._lock:
            if owner_user_id in self._frozen:
                return False
            self._queued.setdefault(owner_user_id, set()).add(task_id)
            return True

    def cancel_queued(self, owner_user_id: str) -> int:
        """Cancel locally registered work and return the number cancelled."""
        with self._lock:
            return len(self._queued.pop(owner_user_id, set()))

    def queued_count(self, owner_user_id: str) -> int:
        with self._lock:
            return len(self._queued.get(owner_user_id, set()))

    def run_if_allowed(self, owner_user_id: str, work: Callable[[], object]):
        if self.is_frozen(owner_user_id):
            return {"status": "NO_OP", "reason": "ACCOUNT_DELETED"}
        return work()


class DeletionReconciler:
    def __init__(self):
        self._lock = RLock()
        self._snapshots: dict[tuple[str, str], dict] = {}

    def reconcile(self, plan, completed):
        if not plan.owner_user_id or not plan.idempotency_key:
            raise ValueError("DELETION_PLAN_IDENTITY_REQUIRED")
        supplied = set(completed)
        unknown = sorted(supplied.difference(plan.entities))
        if unknown:
            raise ValueError("DELETION_STEP_UNKNOWN")
        pending = [step for step in plan.entities if step not in supplied]
        result = {
            "owner_user_id": plan.owner_user_id,
            "idempotency_key": plan.idempotency_key,
            "completed": [step for step in plan.entities if step in supplied],
            "pending": pending,
            "complete": not pending,
            "reconciled_at": datetime.now(UTC).isoformat(),
        }
        with self._lock:
            self._snapshots[(plan.owner_user_id, plan.idempotency_key)] = result
            return dict(result)

    def snapshot(self, owner_user_id, idempotency_key):
        with self._lock:
            return self._snapshots.get((owner_user_id, idempotency_key))


class DeletionResidualVerifier:
    def __init__(self, inventory=None):
        self.inventory = inventory or {}

    def verify(self, owner, remaining_counts=None):
        remaining_counts = dict(remaining_counts or {})
        if self.inventory:
            remaining_counts.update(
                {
                    domain: int(provider(owner) or 0)
                    for domain, provider in self.inventory.items()
                }
            )
        residuals = {k: v for k, v in remaining_counts.items() if v}
        return {"owner_user_id": owner, "residuals": residuals, "verified": not residuals, "verified_at": datetime.now(UTC).isoformat()}


class MediaStorageResidualInventory:
    """Independent media residual inventory backed by metadata and storage.

    The caller cannot provide counts: the inventory derives owned metadata and
    then probes each canonical object in the storage adapter.
    """

    def __init__(self, metadata_store, storage):
        self.metadata_store = metadata_store
        self.storage = storage

    def __call__(self, owner: str) -> int:
        if not hasattr(self.metadata_store, "list_owned"):
            raise ValueError("MEDIA_RESIDUAL_INVENTORY_UNAVAILABLE")
        residuals = 0
        for asset in self.metadata_store.list_owned(owner):
            bucket = asset.get("storage_bucket") or getattr(self.storage, "bucket_name", "")
            name = asset.get("storage_object", "")
            if not name:
                continue
            # Adapters return None for a confirmed missing object. Any other
            # exception is deliberately propagated: an IAM/network failure
            # must not be mistaken for an empty bucket.
            if self.storage.stat_object(bucket, name) is not None:
                residuals += 1
        return residuals


class OwnerCollectionResidualInventory:
    """Count non-deleted owner-scoped documents in a Firestore-style store."""

    def __init__(self, store, collection: str):
        self.store = store
        self.collection = collection

    def __call__(self, owner: str) -> int:
        if not hasattr(self.store, "list_owned"):
            raise ValueError("OWNER_RESIDUAL_INVENTORY_UNAVAILABLE")
        return sum(
            1 for item in self.store.list_owned(self.collection, owner)
            if not (item.get("deleted_at") if isinstance(item, dict) else getattr(item, "deleted_at", None))
        )


class AccountDeletionJob:
    """Idempotent deletion state machine; adapters perform each domain step."""
    STATES = (DeletionJobState.FREEZE_ACCOUNT, DeletionJobState.CANCEL_QUEUED_WORK, DeletionJobState.DELETE_DERIVED_DATA, DeletionJobState.DELETE_CANONICAL_DATA, DeletionJobState.DELETE_OBJECTS, DeletionJobState.VERIFY_NO_RESIDUAL_DATA, DeletionJobState.COMPLETE)

    def __init__(self, plan: DeletionPlan, step_runner: Callable[[str, str], dict] | None = None, residual_verifier: DeletionResidualVerifier | None = None, task_gate: DeletionTaskGate | None = None):
        self.plan = plan
        self.state = DeletionJobState.FREEZE_ACCOUNT
        self.completed: list[str] = []
        self.step_runner: Callable[[str, str], dict] = step_runner or (lambda _step, _owner: {})
        self.residual_verifier = residual_verifier or DeletionResidualVerifier()
        self.task_gate = task_gate or DeletionTaskGate()
        self.lock = RLock()

    def run_once(self, remaining_counts=None):
        with self.lock:
            if self.state == DeletionJobState.COMPLETE:
                return self.snapshot()
            if self.state == DeletionJobState.FAILED_RETRYABLE:
                # A residual failure is recoverable: adapters may have removed
                # some objects after the previous verification attempt.
                self.state = DeletionJobState.VERIFY_NO_RESIDUAL_DATA
            if self.state == DeletionJobState.VERIFY_NO_RESIDUAL_DATA:
                verification = self.residual_verifier.verify(self.plan.owner_user_id, remaining_counts or {})
                if not verification["verified"]:
                    self.state = DeletionJobState.FAILED_RETRYABLE
                    return {**self.snapshot(), "verification": verification}
                self.completed.append(self.state)
                self.state = DeletionJobState.COMPLETE
                return {**self.snapshot(), "verification": verification}
            if self.state == DeletionJobState.FREEZE_ACCOUNT:
                self.task_gate.freeze(self.plan.owner_user_id)
            if self.state == DeletionJobState.CANCEL_QUEUED_WORK:
                result = {"cancelled": self.task_gate.cancel_queued(self.plan.owner_user_id)}
            else:
                result = self.step_runner(self.state, self.plan.owner_user_id)
            self.completed.append(self.state)
            index = self.STATES.index(self.state)
            self.state = self.STATES[index + 1]
            return {**self.snapshot(), "step_result": result}

    def snapshot(self):
        return {"owner_user_id": self.plan.owner_user_id, "idempotency_key": self.plan.idempotency_key, "state": self.state, "completed": list(self.completed)}


class TombstonePurger:
    def purge(self, tombstones): return {"purged": len(tombstones), "status": "COMPLETE"}
