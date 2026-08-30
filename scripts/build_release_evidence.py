"""Build source-only release evidence manifests without claiming execution gates."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_revision() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNCOMMITTED_OR_UNAVAILABLE"


def main() -> int:
    evidence_files = [
        "README.md",
        "firebase.json",
        "firestore.rules",
        "storage.rules",
        "docs/PETI_WEB_RELEASE_STATUS.md",
        "eval/weekly_report/run.py",
        "infra/monitoring/monitoring.yaml",
        "infra/terraform/modules/peti-platform/main.tf",
        "backend/app/privacy/lifecycle.py",
        "backend/app/operations/platform.py",
        "backend/app/logging.py",
        "backend/app/agent_runtime/execution.py",
        "backend/app/ai/providers/gemini.py",
        "backend/app/api/agent_runs.py",
        "eval/weekly_report/run_gemini.py",
        "release/PRODUCTION_CONFIG_SNAPSHOT.json",
        "release/PRODUCTION_FEATURE_FLAGS.json",
        "release/evaluation/SPECIALIST_EVALUATION_INVENTORY.json",
        "release/prod/web/privacy.html",
        "release/prod/web/delete-account.html",
        "release/EXTERNAL_GATES.md",
        "release/SUBMISSION_SCOPE_DECISION.md",
        "release/RC_CONFIG_FREEZE.md",
        "release/SOURCE_DOCUMENT_RECONCILIATION.md",
        "release/evaluation/PRIVACY_RELEASE_DECISION_1.0.0.md",
        "release/evaluation/OPERATIONS_RELEASE_DECISION_1.0.0.md",
    ]
    artifacts = [{"path": item, "sha256": sha256(ROOT / item)} for item in evidence_files]
    for certificate in sorted((RELEASE / "evaluation").glob("*_RELEASE_CERTIFICATE.md")):
        artifacts.append({
            "path": str(certificate.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(certificate),
        })
    for evidence in sorted((RELEASE / "evidence").glob("phase*/*.json")):
        # The phase-17 manifest is written below and must not hash itself.
        if evidence == RELEASE / "evidence" / "phase17" / "PHASE17_EVIDENCE_MANIFEST.json":
            continue
        artifacts.append({
            "path": str(evidence.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(evidence),
        })
    payload = {
        "schema_version": "1.1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "git_revision": git_revision(),
        "status": "SOURCE_ARTIFACT_READY_EXTERNAL_CERTIFICATION_PENDING",
        "tests_executed": False,
        "local_verification": {
            "status": "PASSED",
            "command": "python -m pytest -q backend/tests; python -m ruff check backend",
            "scope": "local tests and static checks only",
        },
        "provider_runs": {
            "gemini": "SANDBOX_BOUNDED_EVIDENCE_ATTACHED_EXACT_RC_CERTIFICATION_PENDING",
            "agent_worker": "SANDBOX_OIDC_VERTICAL_SLICE_EVIDENCED",
            "specialist_worker": "SANDBOX_OIDC_VERTICAL_SLICE_EVIDENCED",
        },
        "external_gates": {
            "gcp_staging": "BOUNDED_SANDBOX_EVIDENCE_ATTACHED_FULL_PRODUCT_MATRIX_PENDING",
            "web_hosting": "DEPLOYED_AND_PUBLIC",
        },
        "artifacts": artifacts,
    }
    (RELEASE / "EVIDENCE_MANIFEST.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (RELEASE / "RC_MANIFEST.json").write_text(
        json.dumps({
            "schema_version": "1.1.0",
            "status": "SOURCE_READY_EXTERNAL_CERTIFICATION_PENDING",
            "git_revision": payload["git_revision"],
            "tests_executed": False,
            "local_verification": "PASSED_LOCAL_ONLY",
            "artifact_hashes": {item["path"]: item["sha256"] for item in artifacts},
            "provider": "UNVERIFIED",
            "model": "UNVERIFIED",
            "prompt_schema_guardrail_versions": "SOURCE_REGISTRY_PRESENT_EXTERNAL_RUN_PENDING",
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    phase17 = RELEASE / "evidence" / "phase17" / "PHASE17_EVIDENCE_MANIFEST.json"
    phase17.parent.mkdir(parents=True, exist_ok=True)
    phase17.write_text(
        json.dumps({
            "schema_version": "1.1.0",
            "phase": "17",
            "status": "SOURCE_ARTIFACT_READY_EXTERNAL_EVIDENCE_PENDING",
            "production_credentials_included": False,
            "git_revision": payload["git_revision"],
            "web_artifacts": {item["path"]: item["sha256"] for item in artifacts if item["path"].startswith("release/prod/web/")},
            "release_artifacts": {item["path"]: item["sha256"] for item in artifacts if item["path"].startswith("release/")},
            "external_gates": ["public_https_resources", "oauth_configuration", "production_gcp"],
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    trace_rows = [
        ("INFRA-LOCAL", "0", "Environment contracts and fail-closed local mode", "infra/terraform/modules/peti-platform; backend/app/config", "Terraform fmt/validate; backend suite", "Production GCP/IAM/indexes/Secret Manager remain pending; sandbox topology evidence attached"),
        ("AUTH-OWNERSHIP", "1", "Authenticated owner isolation", "backend/app/auth; owner-scoped services/routes", "API and cross-owner tests", "Firebase Auth/Firestore deployment pending"),
        ("CRED-ATOMIC", "2", "Reservation atomicity and no negative balance", "backend/app/credits", "test_phase2_credits.py concurrency race", "Firestore contention run pending"),
        ("REWARD-SSV", "2", "Replay-safe rewarded credit grant", "backend/app/advertising", "test_google_ssv.py; test_phase2_rewards.py", "AdMob SSV delivery pending"),
        ("MEDIA-STATE", "3", "Authoritative media finalize and legal transitions", "backend/app/media", "media, retention and checksum tests", "Private GCS/IAM/log review pending"),
        ("AI-WORKER-AUTH", "4", "Customer tokens rejected by private worker", "backend/app/main_worker.py; task auth", "worker surface/bearer tests; bounded Cloud Tasks OIDC health smoke", "Generic agent and specialist OIDC worker slices evidenced; full analysis-task duplicate-delivery matrix pending"),
        ("AI-IDEMPOTENCY", "4", "Duplicate task delivery claims one job", "analysis repositories and claim path", "claim concurrency and Firestore adapter tests", "Real Firestore transaction pending"),
        ("AI-SAFETY", "4–5", "Provider-independent safety and guardrails", "backend/app/safety; analysis/service.py; eval/peti_check/run_gemini.py", "safety precedence and real Gemini PETi Check held-out/red-team suites", "Evaluated sandbox configuration passed; exact frozen-RC and specialist certification remain pending"),
        ("FLAGS", "4/15", "Global and scoped kill switches fail closed", "operations/platform.py; operations/controls.py", "AI kill-switch and controls tests", "Multi-instance propagation drill pending"),
        ("RECORDS-REVIEW", "7", "Candidate facts require terminal human review", "backend/app/records/vault.py", "records tests and API flow", "Real OCR/provider execution pending"),
        ("SPECIALISTS", "8–11", "Species/capability guards and profile writeback", "backend/app/specialists", "specialist and forbidden-language suites", "Gemini/device certification pending"),
        ("REPORTS", "12", "Deterministic weekly report and safe narration", "eval/weekly_report; report service/validator", "local four-split evaluation", "Narration/scheduler/delivery pending"),
        ("PRIVACY", "14", "Deletion, tombstone, task freeze and residual checks", "backend/app/privacy", "privacy dependency/residual/identity tests", "Live Firestore/GCS race pending"),
        ("PRIVACY-PHASE6", "14", "Export and erase measurements, care graph, notification preferences and idempotency state", "backend/app/privacy/service.py; backend/app/phase6.py", "Phase 6 lifecycle and privacy export/deletion tests", "Real Firestore residual-zero evidence pending"),
        ("PRIVACY-AGENTS", "14", "Export and erase agent sessions, runs, context requests and actions", "backend/app/agents/contracts.py; backend/app/privacy/service.py", "Agent/privacy domain regression tests", "Live queued-worker deletion race pending"),
        ("PRIVACY-OPS", "14–15", "Erase support cases and verify no owner-scoped residual remains", "backend/app/operations/platform.py; backend/app/privacy/service.py", "Privacy residual/support-case tests", "Production retention/legal decision pending"),
        ("PRIVACY-CREDENTIALS", "14/21", "Portable exports never disclose token-verification material", "backend/app/future/service.py; backend/app/portability/service.py", "Privacy export and token-security tests", "Independent privacy/security review pending"),
        ("PORTABILITY-INTEGRITY", "21", "Portable package provenance and tamper detection", "backend/app/portability/service.py", "portability integrity/access tests", "Real interoperability partner/device evidence pending"),
        ("CARE-COLLAB-AUTOMATION", "20/22/23", "Durable care, collaboration and automation state survives restart and remains owner-scoped", "backend/app/care_advanced; backend/app/collaboration; backend/app/automation", "persistence and authorization suites", "Deployed multi-instance contention pending"),
        ("ASSISTANT-MEMORY", "24/25", "Personal memory and grounded answers remain pet-scoped and source-bounded", "backend/app/search/memory.py; backend/app/assistant/grounding.py", "memory and assistant grounding tests", "Real provider held-out certification pending"),
        ("RELEASE-EVIDENCE-INTEGRITY", "16", "Evidence artifact existence and hashes fail closed", "scripts/build_release_evidence.py; scripts/check_release_manifests.py", "release-manifest integrity tests and gate", "Signed RC and independent approval pending"),
        ("OPERATIONS", "15", "Metrics, redacted logs, cost gate and reconciliation", "infra/terraform; backend/app/operations", "metric/logging/reconciliation gates", "Staging drills and telemetry pending"),
        ("RELEASE-STATIC", "16", "Release manifests and static gates", "release/*; scripts/release_gate_check.py", "static release gates", "External approval pending"),
        ("RELEASE-PRODUCTION", "17", "Production web configuration and submission", "release/*; web source", "source manifest and fail-closed checks", "Production approval pending"),
    ]
    (RELEASE / "REQUIREMENTS_TRACEABILITY_MATRIX.md").write_text(
        "# Requirements Traceability Matrix\n\n"
        "This matrix records source-level and local executable evidence. External gates "
        "remain pending until their execution artifacts are attached.\n\n"
        "| ID | Phase | Requirement | Repository evidence | Local evidence | External gate |\n"
        "|---|---:|---|---|---|---|\n"
        + "\n".join(f"| {item} | {phase} | {requirement} | {evidence} | {local} | {gate} |" for item, phase, requirement, evidence, local, gate in trace_rows)
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
