"""Build deterministic, split PETi Lab demo fixtures from the canonical replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "web/demo/lab/data.json"
OUT = SOURCE.parent


def dump(name: str, value) -> dict:
    path = OUT / name
    content = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(content, encoding="utf-8")
    return {"file": name, "sha256": hashlib.sha256(content.encode()).hexdigest(), "bytes": len(content.encode())}


def main() -> int:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    if data.get("data_classification") != "SYNTHETIC_DEMO": raise SystemExit("demo must be SYNTHETIC_DEMO")
    files = [dump("overview.json", data["overview"]), dump("runs.json", data["runs"]),
        dump("agents.json", data["agents"]), dump("models.json", data["models"]),
        dump("feedback.json", data["feedback"]), dump("evaluations.json", data["safety"])]
    details = data.get("run_details", {})
    files += [dump("run-luna.json", details["demo-run-luna"]), dump("run-max.json", details["demo-run-max"])]
    manifest = {"schema_version": "1.0.0", "data_classification": "SYNTHETIC_DEMO",
        "fixture_id": "peti-veterinary-ai-lab-demo-v1", "scenarios": ["LUNA_HEALTHY", "MAX_REVIEW_REQUIRED"],
        "source": "data.json", "files": files, "contains_real_user_data": False}
    dump("manifest.json", manifest)
    print(json.dumps({"status": "BUILT", "files": len(files) + 1})); return 0


if __name__ == "__main__": raise SystemExit(main())
