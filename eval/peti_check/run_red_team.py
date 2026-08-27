import json
from pathlib import Path

from app.peti_check.guardrails import validate_payload_text


def main() -> int:
    manifest = json.loads((Path(__file__).parent / "red_team_v1.json").read_text())
    failures = []
    for case in manifest["cases"]:
        actual = set(validate_payload_text(case["payload"]))
        expected = set(case["forbidden"])
        if not expected.issubset(actual):
            failures.append(
                {"id": case["id"], "expected": sorted(expected), "actual": sorted(actual)}
            )
    print(
        json.dumps(
            {
                "manifest_version": manifest["manifest_version"],
                "cases": len(manifest["cases"]),
                "failures": failures,
            },
            indent=2,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
