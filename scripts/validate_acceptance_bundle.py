"""Validate the sanitized Phase 4/5 customer-path acceptance evidence."""

import argparse
import json
import sys
from pathlib import Path

SCENARIOS = {
    "funded_check",
    "rewarded_funding",
    "abstention",
    "urgent_safety",
    "reopen_process_death",
    "account_isolation",
}
FORBIDDEN_KEYS = {"raw_media", "id_token", "signed_url", "raw_owner_context"}
REQUIRED_FIELDS = {"job_id", "result_id", "reservation_ledger", "provider_request_id", "analytics_events"}


def validate(document: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["bundle must be a JSON object"]
    if document.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    scenarios = document.get("scenarios")
    if not isinstance(scenarios, dict):
        return errors + ["scenarios must be an object"]
    if set(scenarios) != SCENARIOS:
        errors.append("scenarios must contain exactly the six required scenario names")
    for name, evidence in scenarios.items():
        if not isinstance(evidence, dict):
            errors.append(f"{name}: evidence must be an object")
            continue
        missing = REQUIRED_FIELDS - set(evidence)
        if missing:
            errors.append(f"{name}: missing fields: {', '.join(sorted(missing))}")
        if not isinstance(evidence.get("analytics_events"), list):
            errors.append(f"{name}: analytics_events must be a list")
    serialized = json.dumps(document, ensure_ascii=False).lower()
    for key in FORBIDDEN_KEYS:
        if key in serialized:
            errors.append(f"forbidden sensitive evidence key: {key}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    try:
        document = json.loads(args.bundle.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid acceptance bundle: {exc}", file=sys.stderr)
        return 2
    errors = validate(document)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"Acceptance bundle valid: {args.bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
