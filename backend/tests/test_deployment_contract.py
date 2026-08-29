from pathlib import Path

from app.config import Environment
from app.main import app as api_app
from app.main import is_out_of_scope_route, settings
from fastapi.testclient import TestClient

ROOT = Path(__file__).parents[2]


def test_cloud_deployment_contract_keeps_worker_private_and_oidc_bound():
    text = (ROOT / "infra/cloudrun/README.md").read_text()
    deploy = (ROOT / "infra/cloudrun/deploy.ps1").read_text()
    assert "--no-allow-unauthenticated" in deploy
    assert "OIDC" in text or "OIDC" in (ROOT / "docs/PHASE_4_5_CLOUD_ACCEPTANCE_RUNBOOK.md").read_text()
    assert "roles/run.invoker" in deploy


def test_cloud_deployment_passes_dedicated_maintenance_authentication():
    deploy = (ROOT / "infra/cloudrun/deploy.ps1").read_text()
    for name in (
        "PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT",
        "PETI_MAINTENANCE_TASK_AUDIENCE",
    ):
        assert name in deploy
    assert "Require-Value \"PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT\"" in deploy
    assert "Require-Value \"PETI_MAINTENANCE_TASK_AUDIENCE\"" in deploy


def test_cloud_deployment_uses_canonical_bounded_queue_rate():
    deploy = (ROOT / "infra/cloudrun/deploy.ps1").read_text()
    queue = (ROOT / "infra/cloudrun/queue.yaml.template").read_text()
    assert "--max-concurrent-dispatches=10" in deploy
    assert "--max-dispatches-per-second=2" in deploy
    assert "max_dispatches_per_second: 2" in queue


def test_maintenance_scheduler_uses_dedicated_api_identity_contract():
    terraform = (ROOT / "infra/terraform/modules/peti-platform/main.tf").read_text()
    assert 'name  = "PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT"' in terraform
    assert 'name  = "PETI_MAINTENANCE_TASK_AUDIENCE"' in terraform
    assert 'uri         = "${google_cloud_run_v2_service.api.uri}/v1/internal/tasks/media-maintenance"' in terraform


def test_worker_has_separate_entrypoint():
    assert (ROOT / "backend/app/main_worker.py").exists()


def test_cloud_images_quote_pip_version_constraints():
    """Shell parsing must pass comparison constraints through to pip."""
    for filename in ("infra/cloudrun/Dockerfile", "infra/cloudrun/Dockerfile.worker"):
        dockerfile = (ROOT / filename).read_text()
        for requirement in (
            "google-cloud-storage>=2.18.0",
            "google-cloud-tasks>=2.16.0",
            "google-auth>=2.35.0",
            "google-genai>=1.0.0",
            "google-adk>=1.0.0",
            "cryptography>=43.0.0",
        ):
            assert f"'{requirement}'" in dockerfile


def test_cloud_images_run_as_non_root():
    for filename in ("infra/cloudrun/Dockerfile", "infra/cloudrun/Dockerfile.worker"):
        dockerfile = (ROOT / filename).read_text()
        assert "useradd --create-home --uid 10001 appuser" in dockerfile
        assert "USER appuser" in dockerfile


def test_deployment_keeps_peti_check_disabled_by_default():
    script = (ROOT / "infra/cloudrun/deploy.ps1").read_text()
    assert '"PETI_CHECK_ENABLED=false"' in script
    assert "PETI_PETI_CHECK_ENABLED" not in script


def test_dev_environment_example_matches_runtime_setting_names():
    example = (ROOT / "infra/cloudrun/env.dev.example").read_text()
    assert "PETI_CHECK_ENABLED=false" in example
    assert "PETI_PETI_CHECK_ENABLED" not in example
    for name in ("PETI_PROJECT_ID", "PETI_FIREBASE_PROJECT_ID", "PETI_MEDIA_BUCKET"):
        assert f"{name}=REQUIRED" in example


def test_root_environment_example_exposes_cloud_platform_settings():
    example = (ROOT / ".env.example").read_text()
    for name in (
        "PETI_ANALYSIS_QUEUE_NAME",
        "PETI_ANALYSIS_TASK_SERVICE_ACCOUNT",
        "PETI_ANALYSIS_TASK_AUDIENCE",
        "PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT",
        "PETI_MAINTENANCE_TASK_AUDIENCE",
        "PETI_FIREBASE_PROJECT_ID",
        "PETI_CHECK_ENABLED",
    ):
        assert name in example


def test_cloud_preflight_requires_real_credentials_or_active_gcloud_account():
    script = (ROOT / "infra/cloudrun/preflight.ps1").read_text()
    assert "gcloud auth list" in script
    assert "Test-Path -LiteralPath" in script
    assert "ADC or gcloud authenticated account" in script
    assert "PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT" in script
    assert "PETI_MAINTENANCE_TASK_AUDIENCE" in script


def test_gcp_deployment_requires_reviewed_cloud_controls():
    script = (ROOT / "infra/cloudrun/deploy.ps1").read_text()
    assert "PETI_AI_PROVIDER" in script
    assert "PETI_AI_ENABLED" in script
    assert "--no-allow-unauthenticated" in script
    assert 'Require-Value "PETI_PROJECT_ID"' in script
    assert 'PETI_CHECK_ENABLED=false' in script


def test_cloud_dev_vertical_slice_requires_firebase_prerequisites():
    script = (ROOT / "scripts/run-dev-vertical-slice.ps1").read_text()
    assert "PETI_AUTH_MODE" in script
    assert "FIREBASE" in script
    assert "PETI_FIREBASE_PROJECT_ID" in script
    assert "ADC" in script


def test_zero_cost_policy_is_documented_centrally():
    policy = (ROOT / "docs/ZERO_COST_POLICY.md").read_text()
    assert "FakeAI" in policy
    assert "billable GCP" in policy
    assert "explicit operator action" in policy
    assert "kill switches" in policy
def test_unapproved_scope_route_matcher_is_narrow_and_explicit():
    assert is_out_of_scope_route("/v1/assistant/threads")
    assert is_out_of_scope_route("/v1/pets/p1/assistant/grounded-answer")
    assert is_out_of_scope_route("/v1/pets/p1/portable-export")
    assert is_out_of_scope_route("/v1/pets/p1/automation-rules")
    assert is_out_of_scope_route("/v1/dogs/d1/agent-sessions")
    assert is_out_of_scope_route("/v1/agent-runs/r1")
    assert is_out_of_scope_route("/v1/agent/runs/r1")
    assert is_out_of_scope_route("/v1/search")
    assert is_out_of_scope_route("/v1/saved-searches")
    assert is_out_of_scope_route("/v1/pets/p1/memory")
    assert is_out_of_scope_route("/v1/pets/p1/collaboration/memberships")
    assert not is_out_of_scope_route("/v1/pets/p1")
    assert not is_out_of_scope_route("/v1/pets/p1/records")


def test_non_local_scope_guard_runs_before_authentication(monkeypatch):
    monkeypatch.setattr(settings, "environment", Environment.STAGING)
    response = TestClient(api_app).get("/v1/assistant/threads")
    assert response.status_code == 404
    assert response.json()["detail"] == "ROUTE_NOT_ENABLED"
    canonical = TestClient(api_app).get("/v1/pets")
    assert canonical.status_code == 401
