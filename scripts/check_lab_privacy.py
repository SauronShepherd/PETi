"""Static, fail-closed privacy/cardinality contract gate for PETi Lab."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors: list[str] = []
    schemas = sorted((ROOT / "contracts" / "lab").glob("*.schema.json"))
    if len(schemas) != 7: errors.append(f"expected 7 Lab schemas, found {len(schemas)}")
    for path in schemas:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("$schema") != "https://json-schema.org/draft/2020-12/schema": errors.append(f"{path.name}: wrong schema draft")
        except (OSError, json.JSONDecodeError) as exc: errors.append(f"{path.name}: {exc}")
    rules = (ROOT / "firestore.rules").read_text(encoding="utf-8")
    if "allow read, write: if false" not in rules: errors.append("Firestore browser rules are not fail-closed")
    rollup = json.loads((ROOT / "contracts/lab/metric-rollup-v1.schema.json").read_text(encoding="utf-8"))
    allowed = set(rollup["properties"]["dimensions"]["propertyNames"]["enum"])
    forbidden = {"user_id", "owner_user_id", "pet_id", "run_id", "response_id", "comment", "prompt"}
    if allowed & forbidden: errors.append(f"forbidden rollup dimensions: {sorted(allowed & forbidden)}")
    fixture = json.loads((ROOT / "web/demo/lab/data.json").read_text(encoding="utf-8"))
    blob = json.dumps(fixture)
    if "SYNTHETIC_DEMO" not in blob: errors.append("demo fixture lacks SYNTHETIC_DEMO classification")
    if errors:
        print(json.dumps({"status": "FAILED", "errors": errors}, indent=2)); return 1
    print(json.dumps({"status": "PASSED", "schemas": len(schemas), "rollup_dimensions": sorted(allowed)})); return 0


if __name__ == "__main__": raise SystemExit(main())
