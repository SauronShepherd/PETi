"""Conservative repository scan for obvious committed secret material."""
from pathlib import Path
import subprocess
import re

PATTERNS = (re.compile(r"AIza[0-9A-Za-z_-]{30,}"), re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"))


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    ignored = {".git", ".tmp", "test-results", "node_modules", "__pycache__"}
    findings = []
    tracked = subprocess.run(["git", "-C", str(root), "ls-files"], check=True, capture_output=True, text=True).stdout.splitlines()
    for relative in tracked:
        path = root / relative
        if not path.is_file() or any(part in ignored for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(pattern.search(text) for pattern in PATTERNS):
            findings.append(str(path.relative_to(root)))
    if findings:
        print("Potential secret material in: " + ", ".join(sorted(findings)))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
