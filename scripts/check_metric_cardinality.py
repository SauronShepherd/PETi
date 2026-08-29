"""CI gate for payload-free, bounded-cardinality monitoring labels."""
import re
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "infra" / "monitoring" / "monitoring.yaml"

def main() -> int:
    text = SOURCE.read_text(encoding="utf-8")
    required = ("payload_free: true", "max_cardinality_labels:", "forbidden_labels:")
    forbidden = ("user_id", "pet_id", "animal_id", "media_id", "job_id", "purchase_token", "raw_content")
    failures = [item for item in required if item not in text]
    labels_section = text.split("forbidden_labels:", 1)[1].split("\n", 1)[0] if "forbidden_labels:" in text else ""
    if any(label not in labels_section for label in forbidden):
        failures.append("forbidden high-cardinality labels incomplete")
    allowed_line = re.search(r"max_cardinality_labels:\s*\[([^]]+)\]", text)
    if allowed_line and len([x for x in allowed_line.group(1).split(",") if x.strip()]) > 8:
        failures.append("too many allowed metric labels")
    if failures:
        print("METRIC_CARDINALITY=FAIL")
        print("\n".join(failures))
        return 1
    print("METRIC_CARDINALITY=PASS bounded_payload_free_labels")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
