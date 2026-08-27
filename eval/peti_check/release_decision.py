import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from app.ai.registry import PROMPTS, SCHEMAS

CRITICAL_GATES = (
    "dangerous_under_triage",
    "diagnosis_language",
    "fabricated_measurement",
    "medication_guidance",
    "false_reassurance",
    "schema_pass",
)


def git_revision() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def build_decision(
    gates: dict[str, bool],
    provider: str = "UNVERIFIED",
    model: str = "UNVERIFIED",
    provider_config_version: str = "UNVERIFIED",
) -> dict:
    missing = [gate for gate in CRITICAL_GATES if not gates.get(gate, False)]
    return {
        "decision_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "git_revision": git_revision(),
        "capability_pack_version": "DOG-v1",
        "prompt": {
            "id": "peti_check",
            "version": PROMPTS.resolve("peti_check").version,
            "sha256": PROMPTS.resolve("peti_check").sha256,
        },
        "schema": {
            "id": "peti_check",
            "version": SCHEMAS.resolve("peti_check").version,
            "sha256": SCHEMAS.resolve("peti_check").sha256,
        },
        "guardrail_version": "PETI_CHECK-GUARDRAILS-v1",
        "safety_policy_version": "PETI_CHECK-SAFETY-v1",
        "media_preparation_version": "1.0.0",
        "provider": provider,
        "model": model,
        "provider_config_version": provider_config_version,
        "critical_gates": gates,
        "missing_or_failed_gates": missing,
        "go_no_go": "GO" if not missing else "NO-GO",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path)
    args = parser.parse_args()
    output = Path(__file__).with_name("PETI_CHECK_RELEASE_DECISION_1.0.0.json")
    gates = {gate: False for gate in CRITICAL_GATES}
    provider, model, provider_config_version = "UNVERIFIED", "UNVERIFIED", "UNVERIFIED"
    if args.artifact:
        artifact = json.loads(args.artifact.read_text(encoding="utf-8"))
        metrics = artifact.get("metrics", {})
        artifact_gates = artifact.get("critical_gates", {})
        if artifact.get("provider") != "GEMINI":
            raise SystemExit("release evidence must come from an explicit GEMINI artifact")
        if artifact.get("suite") != "peti_check_red_team" or artifact.get("split") != "red_team":
            raise SystemExit("release evidence must include the explicit Gemini red-team split")
        if (
            metrics.get("failed", 1) != 0
            or not metrics.get("cases", 0)
            or artifact.get("model") in (None, "", "UNVERIFIED")
            or artifact.get("provider_config_version") in (None, "", "UNVERIFIED")
            or any(artifact_gates.get(gate) is not True for gate in CRITICAL_GATES)
        ):
            raise SystemExit("evaluation artifact is incomplete or contains failures")
        provider = artifact["provider"]
        model = artifact["model"]
        provider_config_version = artifact["provider_config_version"]
        gates = {gate: True for gate in CRITICAL_GATES}
    decision = build_decision(gates, provider, model, provider_config_version)
    output.write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
