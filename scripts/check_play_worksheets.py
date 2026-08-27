"""Validate Play compliance worksheets are populated and scope-consistent."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "DATA_SAFETY_WORKSHEET.md": ("Data category", "Firebase identity", "Billing identifiers"),
    "HEALTH_APPS_DECLARATION_WORKSHEET.md": ("Safety controls", "does not diagnose", "veterinarian"),
    "PERMISSIONS_WORKSHEET.md": ("Capability", "Photo/document import", "Camera capture"),
    "PLAY_REVIEWER_INSTRUCTIONS.md": ("reviewer test account", "account-deletion", "must not use production"),
    "PLAY_SUBMISSION_CHECKLIST.md": ("Repository checks", "Play Console checks", "NO_GO_EXTERNAL_EVIDENCE_PENDING"),
}


def main() -> int:
    failures: list[str] = []
    for name, markers in FILES.items():
        path = ROOT / "release" / name
        if not path.exists():
            failures.append(f"missing:{name}")
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.splitlines()) < 12:
            failures.append(f"too_short:{name}")
        for marker in markers:
            if marker.lower() not in text.lower():
                failures.append(f"missing_marker:{name}:{marker}")
    data_safety = (ROOT / "release" / "DATA_SAFETY_WORKSHEET.md").read_text(encoding="utf-8").lower()
    for forbidden in ("collaboration", "search projections", "conversations"):
        if forbidden in data_safety and "out-of-scope" not in data_safety:
            failures.append(f"out_of_scope_declared_without_boundary:{forbidden}")
    if failures:
        print("PLAY_WORKSHEETS=FAIL")
        print("\n".join(failures))
        return 1
    print("PLAY_WORKSHEETS=PASS_SOURCE_DECLARATIONS_EXTERNAL_SUBMISSION_PENDING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
