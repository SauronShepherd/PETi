"""Validate demo fixtures; never writes them into production collections."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.lab.demo import validate_demo_fixture


def main() -> int:
    fixture = validate_demo_fixture(json.loads((ROOT / "web/demo/lab/data.json").read_text(encoding="utf-8")))
    print(json.dumps({"status": "VALID", "classification": fixture["data_classification"], "runs": len(fixture["runs"])})); return 0


if __name__ == "__main__": raise SystemExit(main())
