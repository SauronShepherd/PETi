"""Verify that unapproved research routes remain fail-closed outside LOCAL."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "backend/app/main.py").read_text(encoding="utf-8")
REQUIRED_MARKERS = (
    "def is_out_of_scope_route",
    "def reject_unapproved_scope",
    '"/v1/assistant"',
    '"/assistant/grounded-answer"',
    '"/agent-runs"',
    'Environment.LOCAL',
    '"ROUTE_NOT_ENABLED"',
)


def main() -> int:
    missing = [marker for marker in REQUIRED_MARKERS if marker not in MAIN]
    if missing:
        print("SCOPE_GUARD=FAIL")
        for marker in missing:
            print(f"missing marker: {marker}")
        return 1
    print("SCOPE_GUARD=PASS_FAIL_CLOSED_NON_LOCAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
