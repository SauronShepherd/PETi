"""Normalize a trusted release-decision manifest into the Lab evaluation registry.

Dry-run is the default. Production writes require both --apply and an exact
--confirm-project value so a local verification cannot mutate Firestore by accident.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.lab.contracts import EvaluationResult
from app.lab.evaluations import CRITICAL_GATES, validate_evaluation
from app.lab.firestore_repositories import FirestoreLabRepository


def normalize(path: Path, *, deployment_id: str, release_id: str) -> EvaluationResult:
    raw = json.loads(path.read_text(encoding="utf-8"))
    source = path.read_bytes()
    gate_values = raw.get("critical_gates")
    if not isinstance(gate_values, dict):
        raise TypeError("LAB_EVALUATION_GATES_INCOMPLETE")
    gates = {gate: "PASS" if gate_values.get(gate) is True else "FAIL" for gate in CRITICAL_GATES}
    generated = raw.get("generated_at")
    evaluated_at = datetime.fromisoformat(generated) if generated else datetime.now(UTC)
    item = EvaluationResult(
        id=f"eval-{hashlib.sha256(source).hexdigest()[:32]}",
        suite="PETI_CHECK_RELEASE",
        deployment_id=deployment_id,
        release_id=release_id,
        status="PASS" if raw.get("go_no_go") == "GO" else "FAIL",
        critical_gates=gates,
        metrics={},
        source_manifest_id=hashlib.sha256(source).hexdigest(),
        evaluated_at=evaluated_at,
    )
    return validate_evaluation(item)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--deployment-id", required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-project")
    args = parser.parse_args()
    item = normalize(args.input.resolve(), deployment_id=args.deployment_id, release_id=args.release_id)
    if not args.apply:
        print(json.dumps({"mode": "DRY_RUN", "evaluation": item.__dict__}, default=str, indent=2))
        return 0
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project or args.confirm_project != project:
        raise SystemExit("Refusing write: --confirm-project must match GOOGLE_CLOUD_PROJECT")
    from google.cloud import firestore

    FirestoreLabRepository(firestore.Client(project=project)).put_evaluation(item)
    print(json.dumps({"mode": "APPLIED", "project": project, "evaluation_id": item.id}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
