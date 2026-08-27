import pytest
from app.auth.task_auth import TaskAuthenticator


def test_task_auth_rejects_wrong_identity_and_audience():
    auth = TaskAuthenticator(
        "worker-caller@p.iam.gserviceaccount.com", "https://worker", local=False
    )
    with pytest.raises(ValueError, match="SERVICE_IDENTITY"):
        auth.verify("customer", "https://worker")
    with pytest.raises(ValueError, match="AUDIENCE"):
        auth.verify("worker-caller@p.iam.gserviceaccount.com", "https://other")


def test_local_emulator_identity_is_explicitly_supported():
    assert (
        TaskAuthenticator(local=True).verify("floci-cloud-tasks", None).service_account
        == "floci-cloud-tasks"
    )


def test_local_task_auth_rejects_non_string_audience():
    with pytest.raises(ValueError, match="TASK_SERVICE_IDENTITY_INVALID"):
        TaskAuthenticator(local=True).verify("floci-cloud-tasks", 123)


def test_non_local_task_auth_rejects_non_string_identity_values():
    auth = TaskAuthenticator("worker@example.com", "https://worker", local=False)
    with pytest.raises(ValueError, match="TASK_AUTHENTICATION_REQUIRED"):
        auth.verify(123, "https://worker")
    with pytest.raises(ValueError, match="TASK_AUTHENTICATION_REQUIRED"):
        auth.verify("worker@example.com", 123)
