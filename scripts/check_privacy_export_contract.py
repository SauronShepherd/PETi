"""Static check for the account export contract and canonical domain coverage."""
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "backend" / "app" / "privacy" / "service.py"
REQUIRED = ("pets", "measurements", "care", "media", "export_manifest", "provenance_policy")

def main() -> int:
    text = SOURCE.read_text(encoding="utf-8")
    missing = [item for item in REQUIRED if f'"{item}"' not in text]
    if missing:
        print("PRIVACY_EXPORT=FAIL missing=" + ",".join(missing))
        return 1
    print("PRIVACY_EXPORT=PASS canonical_domains_and_provenance_manifest_present")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
