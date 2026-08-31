"""Verify critical PETi Lab data invariants from a JSON snapshot."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(data: dict) -> list[str]:
    errors = []
    runs = data.get("runs", []); responses = data.get("responses", []); feedback = data.get("feedback", [])
    response_ids = {x.get("id") for x in responses}; run_ids = {x.get("run_id") for x in runs}
    for run in runs:
        if run.get("status") == "SUCCEEDED" and not run.get("response_id"): errors.append(f"terminal run without response: {run.get('run_id')}")
    for item in feedback:
        if item.get("response_id") not in response_ids: errors.append(f"orphan feedback: {item.get('id')}")
    for step in data.get("steps", []):
        if step.get("run_id") not in run_ids: errors.append(f"orphan step: {step.get('id')}")
    event_ids = [x.get("id") for x in data.get("events", [])]
    if len(event_ids) != len(set(event_ids)): errors.append("duplicate event IDs")
    environments = {x.get("environment") for group in (runs, responses, feedback) for x in group if x.get("environment")}
    if len(environments) > 1: errors.append(f"cross-environment contamination: {sorted(environments)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("snapshot", type=Path); args = parser.parse_args()
    errors = verify(json.loads(args.snapshot.read_text(encoding="utf-8")))
    print(json.dumps({"status": "FAILED" if errors else "PASSED", "errors": errors}, indent=2)); return 1 if errors else 0


if __name__ == "__main__": raise SystemExit(main())
