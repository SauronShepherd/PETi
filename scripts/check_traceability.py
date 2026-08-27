"""Validate that the release traceability matrix is structured and honest."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "release" / "REQUIREMENTS_TRACEABILITY_MATRIX.md"
REQUIRED_DOMAIN_IDS = {
    "PRIVACY-PHASE6", "PRIVACY-AGENTS", "PRIVACY-OPS", "PRIVACY-CREDENTIALS",
    "PORTABILITY-INTEGRITY", "CARE-COLLAB-AUTOMATION", "ASSISTANT-MEMORY",
    "BILLING-TOKEN-BOUNDARY", "RELEASE-EVIDENCE-INTEGRITY",
}

def main() -> int:
    text = MATRIX.read_text(encoding="utf-8")
    required = ("ID", "Phase", "Requirement", "Repository evidence", "Local evidence", "External gate")
    missing = [item for item in required if item not in text]
    rows = [line for line in text.splitlines() if line.startswith("|") and "---" not in line]
    requirement_rows = [line for line in rows if line.split("|")[1].strip() not in {"ID", ""}]
    row_ids = {line.split("|")[1].strip() for line in requirement_rows}
    if missing or len(requirement_rows) < 27 or not REQUIRED_DOMAIN_IDS.issubset(row_ids):
        print("TRACEABILITY=FAIL")
        return 1
    if "pending" not in text.lower():
        print("TRACEABILITY=FAIL_UNHONEST_EXTERNAL_STATUS")
        return 1
    print(f"TRACEABILITY=PASS_SOURCE_LEVEL requirements={len(requirement_rows)} external_gates_explicit=true")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
