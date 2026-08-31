import json
from dataclasses import dataclass, field
from threading import RLock
from typing import Protocol


class AgentTaskQueue(Protocol):
    def enqueue_agent(
        self,
        *,
        run_id: str,
        owner_user_id: str,
        media_asset_ids: list[str],
        context: str | None = None,
    ) -> bool: ...


class AgentQueueError(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentTask:
    run_id: str
    owner_user_id: str
    media_asset_ids: tuple[str, ...] = field(default_factory=tuple)
    context: str | None = None


class FakeAgentTaskQueue:
    def __init__(self) -> None:
        self.items: list[AgentTask] = []
        self.lock = RLock()

    def enqueue_agent(
        self,
        *,
        run_id: str,
        owner_user_id: str,
        media_asset_ids: list[str],
        context: str | None = None,
    ) -> bool:
        with self.lock:
            if any(item.run_id == run_id for item in self.items):
                return False
            self.items.append(
                AgentTask(run_id, owner_user_id, tuple(media_asset_ids), context)
            )
            return True

    def pop(self) -> AgentTask | None:
        with self.lock:
            return self.items.pop(0) if self.items else None


class CloudAgentTaskQueue:
    def __init__(
        self,
        client,
        *,
        project: str,
        location: str,
        queue: str,
        worker_url: str,
        service_account: str,
        audience: str | None = None,
    ) -> None:
        self.client = client
        self.parent = client.queue_path(project, location, queue)
        base_worker_url = worker_url.rstrip("/")
        self.worker_url = base_worker_url + "/internal/tasks/agent"
        self.service_account = service_account
        self.audience = audience or base_worker_url

    def enqueue_agent(
        self,
        *,
        run_id: str,
        owner_user_id: str,
        media_asset_ids: list[str],
        context: str | None = None,
    ) -> bool:
        payload = {
            "run_id": run_id,
            "owner_user_id": owner_user_id,
            "media_asset_ids": list(media_asset_ids),
            "context": context,
        }
        task = {
            "name": f"{self.parent}/tasks/agent-{run_id}",
            "http_request": {
                "http_method": "POST",
                "url": self.worker_url,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload, separators=(",", ":")).encode(),
                "oidc_token": {
                    "service_account_email": self.service_account,
                    "audience": self.audience,
                },
            },
        }
        try:
            self.client.create_task(request={"parent": self.parent, "task": task})
            return True
        except Exception as exc:
            if "ALREADY_EXISTS" in str(exc):
                return False
            raise AgentQueueError("AGENT_QUEUE_SUBMISSION_FAILED") from exc
