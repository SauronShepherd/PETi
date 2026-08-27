"""Static environment contract checker; intentionally not executed by Codex."""
from pathlib import Path


REQUIRED = ["backend/app/main.py", "android/app/build.gradle.kts", "infra/cloudrun/Dockerfile"]


def verify(root: str = ".") -> list[str]:
    base = Path(root)
    return [path for path in REQUIRED if not (base / path).exists()]


if __name__ == "__main__":
    missing = verify()
    raise SystemExit("missing: " + ", ".join(missing) if missing else "environment contract satisfied")
