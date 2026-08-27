"""Fail-closed structural validation for privacy-safe specialist manifests."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "eval" / "specialists"
SUITES = ("dog_body_check", "dog_dental_check", "dog_feces_check", "dog_initial_scan")
SPLITS = ("dev", "held_out", "red_team", "regression")


def main() -> int:
    errors: list[str] = []
    manifest_count = 0
    for suite in SUITES:
        for split in SPLITS:
            path = EVAL / suite / f"{split}.json"
            if not path.is_file():
                errors.append(f"missing:{path.relative_to(ROOT)}")
                continue
            manifest_count += 1
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"invalid_json:{path.relative_to(ROOT)}:{exc}")
                continue
            if not isinstance(data, dict):
                errors.append(f"not_object:{path.relative_to(ROOT)}")
                continue
            if data.get("suite") != suite or data.get("split") != split:
                errors.append(f"metadata:{path.relative_to(ROOT)}")
            if data.get("schema_version") != "1.0.0":
                errors.append(f"schema_version:{path.relative_to(ROOT)}")
            if split == "red_team" and not isinstance(data.get("must_reject_claims"), list):
                errors.append(f"missing_must_reject_claims:{path.relative_to(ROOT)}")
            if split in {"held_out", "regression"} and not (
                isinstance(data.get("release_gates"), list) or isinstance(data.get("cases"), list)
            ):
                errors.append(f"missing_acceptance_contract:{path.relative_to(ROOT)}")
            for field in ("allowed_findings", "required_safety_states", "must_reject_claims", "release_gates", "cases"):
                if field in data and not isinstance(data[field], list):
                    errors.append(f"field_not_list:{path.relative_to(ROOT)}:{field}")
    result = {"status": "PASS" if not errors else "FAIL", "manifests": manifest_count, "errors": errors}
    print(json.dumps(result, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
