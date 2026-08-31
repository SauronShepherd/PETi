"""Fail when required current judge documents are missing."""
from pathlib import Path

REQUIRED = {"START_HERE.md", "QUICKSTART.md", "PRODUCT_AND_PROBLEM.md", "ARCHITECTURE.md", "MULTI_AGENT_RUNTIME.md", "PROOF_OF_ACTION.md", "SAFETY_PRIVACY_AND_AUTHORITY.md", "DEMO_RUNBOOK.md", "TESTING_AND_VERIFICATION.md", "KNOWN_LIMITATIONS.md", "REPOSITORY_MAP.md", "TROUBLESHOOTING.md"}


def main() -> int:
    root = Path(__file__).resolve().parents[2] / "docs/judges"
    missing = sorted(name for name in REQUIRED if not (root / name).is_file())
    if missing:
        print("Missing judge documents: " + ", ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
