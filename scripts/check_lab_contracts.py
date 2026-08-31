from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    schemas = list((ROOT / "contracts/lab").glob("*.schema.json")); ids = set()
    for path in schemas:
        data = json.loads(path.read_text(encoding="utf-8")); schema_id = data.get("$id")
        if not schema_id or schema_id in ids: raise SystemExit(f"invalid or duplicate schema id: {path}")
        ids.add(schema_id)
    manifest = json.loads((ROOT / "web/demo/lab/manifest.json").read_text(encoding="utf-8"))
    if manifest.get("data_classification") != "SYNTHETIC_DEMO" or manifest.get("contains_real_user_data") is not False:
        raise SystemExit("invalid demo manifest")
    print(json.dumps({"status": "PASSED", "schemas": len(schemas), "demo_files": len(manifest["files"])})); return 0


if __name__ == "__main__": raise SystemExit(main())
