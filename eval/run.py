"""Run a versioned PETi Check evaluation split and persist its evidence.

Fake evaluation is deterministic and safe for local/PR checks.  Real-provider
evaluation is deliberately explicit and currently requires the caller to
provide an adapter command through PETI_REAL_EVAL_COMMAND; the runner never
silently substitutes FakeAI for a requested Gemini run.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai.registry import PROMPTS, SCHEMAS
from app.peti_check.guardrails import validate_payload_text

CORPUS = ROOT / "eval" / "peti_check"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cases(split: str) -> tuple[str, list[dict], Path]:
    path = CORPUS / ("red_team_v1.json" if split == "red_team" else f"{split}.json")
    if not path.exists():
        raise SystemExit(f"evaluation split not found: {split}")
    document = json.loads(path.read_text(encoding="utf-8"))
    return document["manifest_version"], document.get("cases", []), path


def run_fake(cases: list[dict]) -> tuple[list[dict], dict]:
    results = []
    for case in cases:
        actual = sorted(validate_payload_text(case.get("payload", {})))
        expected = sorted(case.get("forbidden", []))
        results.append(
            {
                "id": case["id"],
                "violations": actual,
                "expected_violations": expected,
                "pass": set(expected).issubset(actual),
            }
        )
    passed = sum(result["pass"] for result in results)
    return results, {"cases": len(results), "passed": passed, "failed": len(results) - passed}


def run_real(split: str) -> tuple[list[dict], dict, dict[str, bool]]:
    command = os.environ.get("PETI_REAL_EVAL_COMMAND")
    if not command:
        raise SystemExit(
            "real provider evaluation requires PETI_REAL_EVAL_COMMAND; "
            "the runner will not silently use FakeAI"
        )
    completed = subprocess.run(
        [*command.split(), "--split", split], cwd=ROOT, check=False, text=True, capture_output=True
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)
    try:
        delegated = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit("real evaluator must print a JSON object to stdout") from exc
    results = delegated.get("case_results")
    metrics = delegated.get("metrics")
    critical_gates = delegated.get("critical_gates")
    if not isinstance(results, list) or not results or not isinstance(metrics, dict):
        raise SystemExit("real evaluator JSON must contain non-empty case_results and metrics")
    if not isinstance(critical_gates, dict):
        raise SystemExit("real evaluator JSON must contain critical_gates")
    required_gates = {
        "dangerous_under_triage",
        "diagnosis_language",
        "fabricated_measurement",
        "medication_guidance",
        "false_reassurance",
        "schema_pass",
    }
    if set(critical_gates) != required_gates or any(
        not isinstance(critical_gates[gate], bool) for gate in required_gates
    ):
        raise SystemExit("real evaluator critical_gates must contain exactly six boolean gates")
    if metrics.get("cases") != len(results):
        raise SystemExit("real evaluator metrics.cases must match case_results length")
    return results, metrics, critical_gates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("peti_check", "peti_check_red_team"), required=True)
    parser.add_argument(
        "--split", choices=("dev", "regression", "held_out", "red_team"), default="dev"
    )
    parser.add_argument("--provider", choices=("fake", "gemini"), default="fake")
    parser.add_argument("--environment", default="local")
    parser.add_argument("--model", default="UNVERIFIED")
    parser.add_argument("--config", default="UNVERIFIED")
    args = parser.parse_args()
    split = "red_team" if args.suite == "peti_check_red_team" else args.split
    manifest_version, cases, manifest_path = load_cases(split)
    if not cases:
        raise SystemExit(f"evaluation split is empty: {split}")
    if args.provider == "fake":
        results, metrics = run_fake(cases)
        critical_gates = {gate: False for gate in (
            "dangerous_under_triage",
            "diagnosis_language",
            "fabricated_measurement",
            "medication_guidance",
            "false_reassurance",
            "schema_pass",
        )}
    else:
        results, metrics, critical_gates = run_real(split)
    artifact = {
        "run_id": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        "created_at": datetime.now(UTC).isoformat(),
        "suite": args.suite,
        "split": split,
        "manifest_version": manifest_version,
        "manifest_sha256": sha256_file(manifest_path),
        "provider": args.provider.upper(),
        "model": args.model,
        "provider_config_version": args.config,
        "environment": args.environment,
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
        "metrics": metrics,
        "critical_gates": critical_gates,
        "case_results": results,
        "delegated_evidence": args.provider == "gemini",
    }
    output = CORPUS / f"run_{artifact['run_id']}_{split}_{args.provider}.json"
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": str(output), **metrics}, indent=2))
    return 1 if metrics.get("failed", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
