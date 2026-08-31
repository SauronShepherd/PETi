import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4


class RunState(StrEnum):
    CREATED = "CREATED"; QUEUED = "QUEUED"; RUNNING = "RUNNING"; WAITING = "WAITING"; COMPLETED = "COMPLETED"; FAILED = "FAILED"; CANCELLED = "CANCELLED"


@dataclass
class AgentSession:
    owner_user_id: str
    pet_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "ACTIVE"
    bounded_conversation_summary: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class EvidenceReference:
    entity_type: str
    entity_id: str
    pet_id: str
    owner_user_id: str
    source_version: str = "1.0.0"


@dataclass
class AgentRun:
    owner_user_id: str
    pet_id: str | None
    goal: str
    agent_type: str = "ORCHESTRATOR"
    id: str = field(default_factory=lambda: str(uuid4()))
    state: RunState = RunState.CREATED
    steps: list[dict] = field(default_factory=list)
    evidence: list[EvidenceReference] = field(default_factory=list)
    policy_snapshot: dict = field(default_factory=dict)
    interaction_id: str | None = None
    correlation_id: str | None = None
    plan_id: str | None = None
    recipe_id: str | None = None
    deployment_id: str | None = None
    response_id: str | None = None
    outcome: str | None = None
    safety_state: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    execution_lease_owner: str | None = None
    execution_lease_expires_at: datetime | None = None
    lease_epoch: int = 0
    run_version: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None

    def public(self): return asdict(self)


class AgentOrchestrator:
    """A durable-model seam. Provider execution is intentionally injected."""
    def __init__(self, context_broker=None, tool_gateway=None, store=None, clock=None, action_executor=None, repository=None):
        self.context_broker, self.tool_gateway, self.store = context_broker, tool_gateway, store
        self.action_executor = action_executor
        self.repository = repository
        self.clock = clock or (lambda: datetime.now(UTC))
        self.runs: dict[str, AgentRun] = {}
        self.sessions: dict[str, AgentSession] = {}
        self.context_requests: dict[str, dict] = {}
        self.actions: dict[str, dict] = {}
        self.observation_plans: dict[str, object] = {}
        self._claims: dict[str, list[dict]] = {}
        self._hydrate()

    def _save(self, collection, key, value):
        if self.store and hasattr(self.store, "put_raw"):
            self.store.put_raw(collection, key, value)

    def _load_raw(self, collection, key):
        if not self.store or not hasattr(self.store, "client"):
            return None
        snap = self.store.client.collection(collection).document(key).get()
        return snap.to_dict() if snap.exists else None

    def persist_claims(self, owner, run_id, claims):
        self.get(owner, run_id)
        self._claims[run_id] = [dict(claim) for claim in claims]
        for index, claim in enumerate(claims):
            self._save("agent_claims", f"{run_id}:{index}", {**dict(claim), "run_id": run_id, "owner_user_id": owner})

    def list_claims(self, owner, run_id):
        if self.store and hasattr(self.store, "all"):
            return [dict(row) for row in self.store.all("agent_claims") if row.get("run_id") == run_id and row.get("owner_user_id") == owner]
        self.get(owner, run_id)
        return [dict(claim) for claim in self._claims.get(run_id, [])]

    def list_active_runs(self, owner, pet_id):
        return [run for run in self.runs.values() if run.owner_user_id == owner and run.pet_id == pet_id and run.state in {RunState.QUEUED, RunState.RUNNING, RunState.WAITING}]

    def _hydrate(self):
        if not self.store or not hasattr(self.store, "all"):
            return
        def rows(collection):
            try:
                return self.store.all(collection)
            except Exception:  # noqa: BLE001 - transient durable outage must not crash startup
                return []

        for data in rows("agent_sessions"):
            try:
                data = dict(data)
                for key in ("created_at", "updated_at", "started_at", "completed_at", "execution_lease_expires_at"):
                    value = data.get(key)
                    if value is not None and not isinstance(value, datetime):
                        data[key] = datetime.fromisoformat(str(value))
                item = AgentSession(**{k: data[k] for k in AgentSession.__dataclass_fields__ if k in data})
                self.sessions[item.id] = item
            except (KeyError, TypeError, ValueError):
                continue
        for data in rows("agent_runs"):
            try:
                data = dict(data)
                data["state"] = RunState(data["state"])
                data["evidence"] = [EvidenceReference(**x) for x in data.get("evidence", [])]
                for key in ("created_at", "updated_at", "started_at", "completed_at", "execution_lease_expires_at"):
                    value = data.get(key)
                    if value is not None and not isinstance(value, datetime):
                        data[key] = datetime.fromisoformat(str(value))
                item = AgentRun(**{k: data[k] for k in AgentRun.__dataclass_fields__ if k in data})
                self.runs[item.id] = item
            except (KeyError, TypeError, ValueError):
                continue
        for collection, target in (("agent_context_requests", self.context_requests), ("agent_actions", self.actions)):
            for data in rows(collection):
                try:
                    if isinstance(data, dict) and data.get("id"):
                        target[data["id"]] = data
                except (KeyError, TypeError, ValueError):
                    continue

    def _persist_run(self, run):
        data = asdict(run)
        data["state"] = run.state.value
        self._save("agent_runs", run.id, data)

    def acquire_execution_lease(self, owner: str, run_id: str, lease_owner: str, ttl_seconds: int = 300) -> bool:
        """Atomically claim provider execution across worker instances."""
        now = self.clock(); expires = now + timedelta(seconds=ttl_seconds)
        if self.store and hasattr(self.store, "client") and hasattr(self.store.client, "transaction"):
            from google.cloud.firestore_v1.transaction import (
                transactional,  # type: ignore[import-untyped]
            )
            ref = self.store.client.collection("agent_runs").document(run_id)
            transaction = self.store.client.transaction()
            @transactional
            def claim(tx):
                snap = tx.get(ref)
                if not hasattr(snap, "exists"):
                    snap = next(iter(snap), None)
                if snap is None:
                    return False
                if not snap.exists: return False
                data = snap.to_dict() or {}
                if data.get("owner_user_id") != owner or data.get("state") not in {"QUEUED", "RUNNING"}: return False
                current_expiry = data.get("execution_lease_expires_at")
                if current_expiry and not isinstance(current_expiry, datetime):
                    current_expiry = datetime.fromisoformat(str(current_expiry))
                if current_expiry and current_expiry > now and data.get("execution_lease_owner") != lease_owner: return False
                epoch = int(data.get("lease_epoch", 0)) + 1
                tx.update(ref, {"execution_lease_owner": lease_owner, "execution_lease_expires_at": expires, "lease_epoch": epoch, "run_version": int(data.get("run_version", 0)) + 1})
                return epoch
            epoch = claim(transaction)
            acquired = epoch is not False
        else:
            run = self.get(owner, run_id)
            acquired = not (run.execution_lease_expires_at and run.execution_lease_expires_at > now and run.execution_lease_owner != lease_owner)
            if acquired:
                run.execution_lease_owner = lease_owner; run.execution_lease_expires_at = expires; run.lease_epoch += 1; run.run_version += 1; self._persist_run(run)
        if acquired and run_id in self.runs:
            self.runs[run_id].execution_lease_owner = lease_owner
            self.runs[run_id].execution_lease_expires_at = expires
            self.runs[run_id].lease_epoch = int(epoch if self.store and hasattr(self.store, "client") else self.runs[run_id].lease_epoch)
        return acquired

    def release_execution_lease(self, owner: str, run_id: str, lease_owner: str, *, lease_epoch=None, expected_version=None) -> None:
        run = self.get(owner, run_id)
        if run.execution_lease_owner != lease_owner: return
        self._assert_fence(run, lease_epoch, expected_version)
        run.execution_lease_owner = None; run.execution_lease_expires_at = None
        next_version = (expected_version + 1) if expected_version is not None else run.run_version + 1
        run.run_version = next_version
        if lease_epoch is not None and expected_version is not None and self.store and hasattr(self.store, "put_agent_run_fenced"):
            if not self.store.put_agent_run_fenced(run.id, {**asdict(run), "state": run.state.value}, owner=owner, lease_epoch=lease_epoch, expected_version=expected_version):
                raise ValueError("STALE_AGENT_EXECUTION")
        else:
            self._persist_run(run)

    def _assert_fence(self, run, lease_epoch=None, expected_version=None):
        if lease_epoch is not None and run.lease_epoch != lease_epoch:
            raise ValueError("STALE_AGENT_EXECUTION")
        if expected_version is not None and run.run_version != expected_version:
            raise ValueError("STALE_AGENT_EXECUTION")

    @staticmethod
    def _action_hash(action_type, summary, arguments):
        payload = json.dumps({"action_type": action_type, "summary": summary, "arguments": arguments}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    def _set_state(self, run, target):
        allowed = {
            RunState.CREATED: {RunState.QUEUED, RunState.CANCELLED},
            RunState.QUEUED: {RunState.RUNNING, RunState.WAITING, RunState.COMPLETED, RunState.CANCELLED},
            RunState.RUNNING: {RunState.RUNNING, RunState.WAITING, RunState.COMPLETED, RunState.FAILED, RunState.CANCELLED},
            RunState.WAITING: {RunState.RUNNING, RunState.CANCELLED},
        }
        if target not in allowed.get(run.state, set()):
            raise ValueError("AGENT_INVALID_STATE_TRANSITION")
        run.state = target
        run.updated_at = self.clock()

    def transition_state_fenced(self, owner, run_id, target, *, lease_epoch, expected_version, started_at=None):
        """Persist a leased lifecycle transition through the same CAS gate as steps."""
        run = self.get(owner, run_id)
        self._assert_fence(run, lease_epoch, expected_version)
        if started_at is not None:
            run.started_at = started_at
        self._set_state(run, target)
        if self.store and hasattr(self.store, "put_agent_run_fenced"):
            if not self.store.put_agent_run_fenced(
                run.id, {**asdict(run), "state": run.state.value},
                owner=owner, lease_epoch=lease_epoch, expected_version=expected_version,
            ):
                raise ValueError("STALE_AGENT_EXECUTION")
            run.run_version = expected_version + 1
        else:
            run.run_version = expected_version + 1
            self._persist_run(run)
        return run

    def create_session(self, owner, pet_id):
        session = AgentSession(owner, pet_id); self.sessions[session.id] = session; self._save("agent_sessions", session.id, asdict(session)); return session

    def get_session(self, owner, session_id):
        session = self.sessions.get(session_id)
        raw = self._load_raw("agent_sessions", session_id)
        if raw:
            for key in ("created_at", "updated_at"):
                if raw.get(key) is not None and not isinstance(raw[key], datetime):
                    raw[key] = datetime.fromisoformat(str(raw[key]))
            try:
                session = AgentSession(**{k: raw[k] for k in AgentSession.__dataclass_fields__ if k in raw})
                self.sessions[session.id] = session
            except (TypeError, ValueError):
                session = None
        if not session or session.owner_user_id != owner or session.status != "ACTIVE": raise ValueError("AGENT_SESSION_NOT_FOUND")
        return session

    def create_run(
        self,
        owner,
        goal,
        pet_id=None,
        agent_type="ORCHESTRATOR",
        policy=None,
        session_id=None,
        interaction_id=None,
        correlation_id=None,
        deployment_id=None,
    ):
        if not goal or len(goal) > 1000: raise ValueError("AGENT_GOAL_INVALID")
        if session_id:
            session = self.get_session(owner, session_id)
            if session.pet_id != pet_id: raise ValueError("AGENT_SESSION_PET_MISMATCH")
        run = AgentRun(
            owner,
            pet_id,
            goal,
            agent_type=agent_type,
            policy_snapshot=policy
            or {
                "web": False,
                "medical_advice": False,
                "max_steps": 8,
                "session_id": session_id,
            },
            interaction_id=interaction_id or str(uuid4()),
            correlation_id=correlation_id or str(uuid4()),
            deployment_id=deployment_id,
        )
        self._set_state(run, RunState.QUEUED); self.runs[run.id] = run
        if self.repository:
            self.repository.create_run_with_initial_step(
                {**asdict(run), "state": run.state.value},
                {"id": "initial-coordination", "run_id": run.id, "status": "READY", "idempotency_key": f"initial:{run.id}"},
            )
        else:
            self._persist_run(run)
        return run

    def get(self, owner, run_id):
        run = self.runs.get(run_id)
        if self.store and hasattr(self.store, "client"):
            snapshot = self.store.client.collection("agent_runs").document(run_id).get()
            data = snapshot.to_dict() if snapshot.exists else None
            if data:
                try:
                    data["state"] = RunState(data["state"])
                    data["evidence"] = [EvidenceReference(**x) for x in data.get("evidence", [])]
                    for key in ("created_at", "updated_at", "started_at", "completed_at", "execution_lease_expires_at"):
                        value = data.get(key)
                        if value is not None and not isinstance(value, datetime):
                            data[key] = datetime.fromisoformat(str(value))
                    run = AgentRun(**{k: data[k] for k in AgentRun.__dataclass_fields__ if k in data})
                    self.runs[run.id] = run
                except (KeyError, TypeError, ValueError):
                    run = None
        if not run or run.owner_user_id != owner or run.deleted_at: raise ValueError("AGENT_RUN_NOT_FOUND")
        return run

    def cancel(self, owner, run_id):
        run = self.get(owner, run_id); expected = run.run_version; self._set_state(run, RunState.CANCELLED)
        data = {**asdict(run), "state": run.state.value}
        if self.store and hasattr(self.store, "put_agent_run_versioned"):
            if not self.store.put_agent_run_versioned(run.id, data, owner=owner, expected_version=expected):
                raise ValueError("STALE_AGENT_EXECUTION")
            run.run_version = expected + 1
        else:
            self._persist_run(run)
        if self.repository and hasattr(self.repository, "cancel_steps"):
            self.repository.cancel_steps(run.id)
        return run

    def request_context(self, owner, run_id, request_type, required_items=None):
        run = self.get(owner, run_id)
        expected = run.run_version
        request = {"id": str(uuid4()), "run_id": run.id, "request_type": request_type, "required_items": list(required_items or []), "status": "OPEN"}
        self.context_requests[request["id"]] = request; self._set_state(run, RunState.WAITING)
        if self.store and hasattr(self.store, "put_agent_run_versioned"):
            if not self.store.put_agent_run_versioned(run.id, {**asdict(run), "state": run.state.value}, owner=owner, expected_version=expected):
                raise ValueError("STALE_AGENT_EXECUTION")
            run.run_version = expected + 1
        else:
            self._persist_run(run)
        self._save("agent_context_requests", request["id"], request); return request

    def respond_context(self, owner, run_id, request_id, resource_refs):
        run = self.get(owner, run_id); expected = run.run_version; request = self.context_requests.get(request_id) or self._load_raw("agent_context_requests", request_id)
        if not request or request["run_id"] != run.id or request["status"] != "OPEN": raise ValueError("AGENT_CONTEXT_REQUEST_NOT_FOUND")
        request.update({"status": "RESPONDED", "resource_refs": list(resource_refs or [])}); self._set_state(run, RunState.RUNNING)
        if self.store and hasattr(self.store, "put_agent_run_versioned"):
            if not self.store.put_agent_run_versioned(run.id, {**asdict(run), "state": run.state.value}, owner=owner, expected_version=expected):
                raise ValueError("STALE_AGENT_EXECUTION")
            run.run_version = expected + 1
        else:
            self._persist_run(run)
        self._save("agent_context_requests", request_id, request); return request

    def propose_action(self, owner, run_id, action_type, summary, arguments=None):
        run = self.get(owner, run_id); expected = run.run_version; args = dict(arguments or {})
        action = {"id": str(uuid4()), "run_id": run.id, "action_type": action_type, "summary": summary, "arguments": args, "approval_payload_hash": self._action_hash(action_type, summary, args), "status": "PENDING_APPROVAL", "expires_at": self.clock() + timedelta(minutes=15)}
        self.actions[action["id"]] = action; self._set_state(run, RunState.WAITING)
        if self.store and hasattr(self.store, "put_agent_run_versioned"):
            if not self.store.put_agent_run_versioned(run.id, {**asdict(run), "state": run.state.value}, owner=owner, expected_version=expected):
                raise ValueError("STALE_AGENT_EXECUTION")
            run.run_version = expected + 1
        else:
            self._persist_run(run)
        self._save("agent_actions", action["id"], action); return action

    def decide_action(self, owner, run_id, action_id, approved, presented_payload_hash=None):
        run = self.get(owner, run_id); expected_version = run.run_version; action = self.actions.get(action_id) or self._load_raw("agent_actions", action_id)
        if not action or action["run_id"] != run.id or action["status"] != "PENDING_APPROVAL": raise ValueError("AGENT_ACTION_NOT_FOUND")
        expires_at = action.get("expires_at")
        if isinstance(expires_at, str): expires_at = datetime.fromisoformat(expires_at)
        if expires_at and expires_at <= self.clock():
            action["status"] = "EXPIRED"
            self._save("agent_actions", action_id, action)
            raise ValueError("AGENT_ACTION_EXPIRED")
        expected = self._action_hash(action["action_type"], action["summary"], action.get("arguments", {}))
        if action.get("approval_payload_hash") != expected:
            raise ValueError("AGENT_ACTION_PAYLOAD_CHANGED")
        if presented_payload_hash is not None and presented_payload_hash != expected:
            raise ValueError("AGENT_ACTION_APPROVAL_HASH_MISMATCH")
        action.update({"status": "APPROVED" if approved else "REJECTED", "approved_by": owner})
        if approved and self.action_executor:
            receipt = self.action_executor.execute(owner, run.pet_id, action, f"agent-action-{action['id']}")
            action["receipt"] = receipt
            action["receipt_id"] = receipt.get("receipt_id")
        elif not approved:
            # A rejected decision has an audit identifier, but it is not an
            # execution receipt and must never imply a Care mutation.
            action["decision_id"] = str(uuid4())
        approval_event = {
            "id": str(uuid4()),
            "action_id": action["id"],
            "run_id": run.id,
            "owner_user_id": owner,
            "approved": bool(approved),
            "payload_hash": expected,
            "created_at": self.clock(),
            "receipt": action.get("receipt"),
        }
        self._save("agent_action_approvals", approval_event["id"], approval_event)
        self._set_state(run, RunState.RUNNING)
        if self.store and hasattr(self.store, "put_agent_run_versioned"):
            if not self.store.put_agent_run_versioned(run.id, {**asdict(run), "state": run.state.value}, owner=owner, expected_version=expected_version):
                raise ValueError("STALE_AGENT_EXECUTION")
            run.run_version = expected_version + 1
        else:
            self._persist_run(run)
        self._save("agent_actions", action_id, action); return action

    def commit_step(self, owner, run_id, step: dict, evidence: list[EvidenceReference] | None = None, *, lease_epoch=None, expected_version=None):
        run = self.get(owner, run_id)
        self._assert_fence(run, lease_epoch, expected_version)
        if run.state in {RunState.CANCELLED, RunState.COMPLETED}: raise ValueError("AGENT_RUN_NOT_WRITABLE")
        step_id = step.get("step_id", str(uuid4()))
        if any(item.get("step_id") == step_id for item in run.steps):
            return run
        if self.repository and hasattr(self.repository, "claim_step"):
            worker_id = run.execution_lease_owner or owner
            repository_steps = self.repository.list_steps(run.id)
            if not any(item.get("id", item.get("step_id")) == step_id for item in repository_steps) and hasattr(self.repository, "ensure_steps"):
                self.repository.ensure_steps(run.id, [{"id": step_id, "step_id": step_id}])
                repository_steps = self.repository.list_steps(run.id)
            if any(item.get("id", item.get("step_id")) == step_id for item in repository_steps):
                now = self.clock()
                claimed = self.repository.claim_step(run.id, step_id, worker_id, now)
                if not claimed:
                    raise ValueError("STALE_AGENT_EXECUTION")
                leased = next(item for item in self.repository.list_steps(run.id) if item.get("id", item.get("step_id")) == step_id)
                if not self.repository.commit_step_result(run.id, step_id, worker_id, int(leased.get("lease_epoch", 0)), {"output": step.get("output"), "safety_state": step.get("safety_state", "SAFE_TO_DISPLAY")}):
                    raise ValueError("STALE_AGENT_EXECUTION")
        run.steps.append({"step_id": step_id, "output": step.get("output"), "schema_version": step.get("schema_version"), "safety_state": step.get("safety_state", "SAFE_TO_DISPLAY")})
        run.evidence.extend(evidence or []); self._set_state(run, RunState.RUNNING)
        if lease_epoch is not None and expected_version is not None and self.store and hasattr(self.store, "put_agent_run_fenced"):
            if not self.store.put_agent_run_fenced(run.id, {**asdict(run), "state": run.state.value}, owner=owner, lease_epoch=lease_epoch, expected_version=expected_version):
                raise ValueError("STALE_AGENT_EXECUTION")
            run.run_version = expected_version + 1
        else:
            self._persist_run(run)
        return run

    def complete(self, owner, run_id, result: dict, *, lease_epoch=None, expected_version=None):
        run = self.get(owner, run_id)
        self._assert_fence(run, lease_epoch, expected_version)
        if not run.evidence and result.get("answer_type") == "FACTUAL": raise ValueError("AGENT_RESULT_NOT_GROUNDED")
        self._set_state(run, RunState.COMPLETED)
        run.response_id = result.get("response_id")
        run.outcome = result.get("outcome") or result.get("status")
        run.safety_state = result.get("safety_state") or result.get("status")
        run.completed_at = self.clock()
        run.steps.append({"final": result, "schema_version": result.get("schema_version", "1.0.0")})
        self._persist_run(run)
        return run
