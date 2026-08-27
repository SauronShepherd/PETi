from dataclasses import dataclass
from threading import RLock
from typing import Protocol


class TaskQueue(Protocol):
    def enqueue_analysis(self, job_id: str, task_id: str, schedule_time=None) -> bool: ...


@dataclass
class AnalysisTask:
    task_id: str
    job_id: str


class FakeTaskQueue:
    def __init__(self):
        self.items: list[AnalysisTask] = []
        self.lock = RLock()

    def enqueue_analysis(self, job_id: str, task_id: str, schedule_time=None):
        with self.lock:
            if any(x.task_id == task_id for x in self.items):
                return False
            self.items.append(AnalysisTask(task_id, job_id))
            return True

    def pop(self):
        with self.lock:
            return self.items.pop(0) if self.items else None

    def __len__(self):
        return len(self.items)


class CloudTasksQueue:
    """Production adapter boundary; SDK construction is kept out of domain code."""

    def __init__(
        self,
        client,
        project: str,
        location: str,
        queue: str,
        worker_url: str,
        service_account: str,
        audience: str | None = None,
    ):
        self.client, self.parent = client, client.queue_path(project, location, queue)
        self.worker_url, self.service_account, self.audience = (
            worker_url,
            service_account,
            audience or worker_url,
        )

    def enqueue_analysis(self, job_id: str, task_id: str, schedule_time=None):
        from google.cloud import tasks_v2  # type: ignore[attr-defined,import-untyped]

        task = {
            "name": f"{self.parent}/tasks/{task_id}",
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": self.worker_url,
                "headers": {"Content-Type": "application/json"},
                "body": f'{{"job_id":"{job_id}"}}'.encode(),
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
            raise
