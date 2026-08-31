import json

from app.agent_runtime.queue import CloudAgentTaskQueue, FakeAgentTaskQueue
from app.analysis.queue import CloudTasksQueue


class CloudTasksClient:
    def __init__(self):
        self.requests = []

    @staticmethod
    def queue_path(project, location, queue):
        return f"projects/{project}/locations/{location}/queues/{queue}"

    def create_task(self, request):
        self.requests.append(request)


def test_fake_agent_queue_is_idempotent_and_preserves_bounded_payload():
    queue = FakeAgentTaskQueue()
    assert queue.enqueue_agent(
        run_id="run-1",
        owner_user_id="owner-1",
        media_asset_ids=["media-1"],
        context="visible context",
    )
    assert not queue.enqueue_agent(
        run_id="run-1", owner_user_id="owner-1", media_asset_ids=[]
    )
    task = queue.pop()
    assert task is not None
    assert task.media_asset_ids == ("media-1",)


def test_cloud_agent_queue_targets_private_agent_worker_surface():
    client = CloudTasksClient()
    queue = CloudAgentTaskQueue(
        client,
        project="project",
        location="europe-west1",
        queue="analysis",
        worker_url="https://worker.example/",
        service_account="worker@example.iam.gserviceaccount.com",
        audience="https://worker.example",
    )
    assert queue.enqueue_agent(
        run_id="run-1",
        owner_user_id="owner-1",
        media_asset_ids=["media-1"],
    )
    task = client.requests[0]["task"]
    assert task["http_request"]["url"] == "https://worker.example/internal/tasks/agent"
    assert json.loads(task["http_request"]["body"])["run_id"] == "run-1"
    assert task["http_request"]["oidc_token"]["audience"] == "https://worker.example"


def test_analysis_queue_targets_analysis_worker_surface_not_service_root():
    client = CloudTasksClient()
    queue = CloudTasksQueue(
        client,
        "project",
        "europe-west1",
        "analysis",
        "https://worker.example/",
        "worker@example.iam.gserviceaccount.com",
    )
    queue.enqueue_analysis("job-1", "task-1")
    assert (
        client.requests[0]["task"]["http_request"]["url"]
        == "https://worker.example/internal/tasks/analysis"
    )

