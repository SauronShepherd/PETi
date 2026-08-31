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
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None

    def public(self): return asdict(self)


class AgentOrchestrator:
    """A durable-model seam. Provider execution is intentionally injected."""
    def __init__(self, context_broker=None, tool_gateway=None, store=None, clock=None):
        self.context_broker, self.tool_gateway, self.store = context_broker, tool_gateway, store
        self.clock = clock or (lambda: datetime.now(UTC))
        self.runs: dict[str, AgentRun] = {}
        self.sessions: dict[str, AgentSession] = {}
        self.context_requests: dict[str, dict] = {}
        self.actions: dict[str, dict] = {}
        self.observation_plans: dict[str, object] = {}
        self._hydrate()

    def _save(self, collection, key, value):
        if self.store and hasattr(self.store, "put_raw"):
            self.store.put_raw(collection, key, value)

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
                if not snap.exists: return False
                data = snap.to_dict() or {}
                if data.get("owner_user_id") != owner or data.get("state") not in {"QUEUED", "RUNNING"}: return False
                current_expiry = data.get("execution_lease_expires_at")
                if current_expiry and not isinstance(current_expiry, datetime):
                    current_expiry = datetime.fromisoformat(str(current_expiry))
                if current_expiry and current_expiry > now and data.get("execution_lease_owner") != lease_owner: return False
                tx.update(ref, {"execution_lease_owner": lease_owner, "execution_lease_expires_at": expires})
                return True
            acquired = bool(claim(transaction))
        else:
            run = self.get(owner, run_id)
            acquired = not (run.execution_lease_expires_at and run.execution_lease_expires_at > now and run.execution_lease_owner != lease_owner)
            if acquired:
                run.execution_lease_owner = lease_owner; run.execution_lease_expires_at = expires; self._persist_run(run)
        if acquired and run_id in self.runs:
            self.runs[run_id].execution_lease_owner = lease_owner
            self.runs[run_id].execution_lease_expires_at = expires
        return acquired

    def release_execution_lease(self, owner: str, run_id: str, lease_owner: str) -> None:
        run = self.get(owner, run_id)
        if run.execution_lease_owner != lease_owner: return
        run.execution_lease_owner = None; run.execution_lease_expires_at = None; self._persist_run(run)

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

    def create_session(self, owner, pet_id):
        session = AgentSession(owner, pet_id); self.sessions[session.id] = session; self._save("agent_sessions", session.id, asdict(session)); return session

    def get_session(self, owner, session_id):
        session = self.sessions.get(session_id)
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
        self._set_state(run, RunState.QUEUED); self.runs[run.id] = run; self._persist_run(run); return run

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
        run = self.get(owner, run_id); self._set_state(run, RunState.CANCELLED); self._persist_run(run); return run

    def request_context(self, owner, run_id, request_type, required_items=None):
        run = self.get(owner, run_id)
        request = {"id": str(uuid4()), "run_id": run.id, "request_type": request_type, "required_items": list(required_items or []), "status": "OPEN"}
        self.context_requests[request["id"]] = request; self._set_state(run, RunState.WAITING); self._save("agent_context_requests", request["id"], request); self._persist_run(run); return request

    def respond_context(self, owner, run_id, request_id, resource_refs):
        run = self.get(owner, run_id); request = self.context_requests.get(request_id)
        if not request or request["run_id"] != run.id or request["status"] != "OPEN": raise ValueError("AGENT_CONTEXT_REQUEST_NOT_FOUND")
        request.update({"status": "RESPONDED", "resource_refs": list(resource_refs or [])}); self._set_state(run, RunState.RUNNING); self._save("agent_context_requests", request_id, request); self._persist_run(run); return request

    def propose_action(self, owner, run_id, action_type, summary, arguments=None):
        run = self.get(owner, run_id); args = dict(arguments or {})
        action = {"id": str(uuid4()), "run_id": run.id, "action_type": action_type, "summary": summary, "arguments": args, "approval_payload_hash": self._action_hash(action_type, summary, args), "status": "PENDING_APPROVAL"}
        self.actions[action["id"]] = action; self._set_state(run, RunState.WAITING); self._save("agent_actions", action["id"], action); self._persist_run(run); return action

    def decide_action(self, owner, run_id, action_id, approved):
        run = self.get(owner, run_id); action = self.actions.get(action_id)
        if not action or action["run_id"] != run.id or action["status"] != "PENDING_APPROVAL": raise ValueError("AGENT_ACTION_NOT_FOUND")
        expected = self._action_hash(action["action_type"], action["summary"], action.get("arguments", {}))
        if action.get("approval_payload_hash") != expected:
            raise ValueError("AGENT_ACTION_PAYLOAD_CHANGED")
        action.update({"status": "APPROVED" if approved else "REJECTED", "approved_by": owner, "receipt_id": str(uuid4())})
        self._set_state(run, RunState.RUNNING); self._save("agent_actions", action_id, action); self._persist_run(run); return action

    def commit_step(self, owner, run_id, step: dict, evidence: list[EvidenceReference] | None = None):
        run = self.get(owner, run_id)
        if run.state in {RunState.CANCELLED, RunState.COMPLETED}: raise ValueError("AGENT_RUN_NOT_WRITABLE")
        step_id = step.get("step_id", str(uuid4()))
        if any(item.get("step_id") == step_id for item in run.steps):
            return run
        run.steps.append({"step_id": step_id, "output": step.get("output"), "schema_version": step.get("schema_version"), "safety_state": step.get("safety_state", "SAFE_TO_DISPLAY")})
        run.evidence.extend(evidence or []); self._set_state(run, RunState.RUNNING); self._persist_run(run); return run

    def complete(self, owner, run_id, result: dict):
        run = self.get(owner, run_id)
        if not run.evidence and result.get("answer_type") == "FACTUAL": raise ValueError("AGENT_RESULT_NOT_GROUNDED")
        self._set_state(run, RunState.COMPLETED)
        run.response_id = result.get("response_id")
        run.outcome = result.get("outcome") or result.get("status")
        run.safety_state = result.get("safety_state") or result.get("status")
        run.completed_at = self.clock()
        run.steps.append({"final": result, "schema_version": result.get("schema_version", "1.0.0")})
        self._persist_run(run)
        return run
