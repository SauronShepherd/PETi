"""Check ADR numbering and fail on undocumented collisions."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = ROOT / "docs" / "adr"
DOCUMENTED_LEGACY = {55, 56, 57, 58, 59, 60, 61, 65, 71, 72, 73}


def main() -> int:
    grouped: dict[int, list[str]] = defaultdict(list)
    for path in ADR_DIR.glob("ADR-*.md"):
        match = re.match(r"ADR-(\d+)-", path.name)
        if match:
            grouped[int(match.group(1))].append(path.name)
    collisions = {number: sorted(names) for number, names in grouped.items() if len(names) > 1}
    undocumented = sorted(number for number in collisions if number not in DOCUMENTED_LEGACY)
    if undocumented:
        print("ADR_INDEX=FAIL")
        for number in undocumented:
            print(f"undocumented duplicate ADR-{number}: {collisions[number]}")
        return 1
    print("ADR_INDEX=PASS")
    print(f"unique_ids={len(grouped)} legacy_collisions={len(collisions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
