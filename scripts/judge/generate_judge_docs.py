"""Generate deterministic judge inventory artifacts from the checked-out tree."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = repo / "docs" / "judges" / "generated"
    output.mkdir(parents=True, exist_ok=True)
    inventory = {
        "schema_version": "1.0.0",
        "agents": sorted(str(p.relative_to(repo)).replace("\\", "/") for p in (repo / "backend/app/agents").rglob("*.py")),
        "recipes": sorted(str(p.relative_to(repo)).replace("\\", "/") for p in (repo / "backend/app/agent_runtime").glob("*recipe*")),
        "judge_documents": sorted(p.name for p in (repo / "docs/judges").glob("*.md")),
    }
    (output / "REPOSITORY_INVENTORY.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
