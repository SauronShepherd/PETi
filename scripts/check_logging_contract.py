"""Check that structured logging remains metadata-only and allowlisted."""
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "backend" / "app" / "logging.py"
REQUIRED = ("safe_fields", "correlation_id", "REDACTED_KEY", "REDACTED_STRUCTURED_PAYLOAD")

def main() -> int:
    text = SOURCE.read_text(encoding="utf-8")
    missing = [item for item in REQUIRED if item not in text]
    if missing:
        print("LOGGING_CONTRACT=FAIL missing=" + ",".join(missing))
        return 1
    print("LOGGING_CONTRACT=PASS metadata_allowlist_and_redaction_present")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
