"""Static release gate checks; external certification remains explicitly pending."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".gradle", ".gradle-home", "__pycache__", ".terraform", "build", "artifacts", ".idea", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".claude"}
SOURCE_SUFFIXES = {".py", ".kt", ".kts", ".gradle", ".json", ".yaml", ".yml", ".ps1", ".tf", ".md", ".toml", ".properties"}
FORBIDDEN_NAMES = {"service-account.json", "credentials.json"}
FORBIDDEN_PATTERNS = (
    re.compile(r"AI" + r"za[0-9A-Za-z_-]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"local-test:[A-Za-z0-9_-]+"),
)
FORBIDDEN_AI_ANDROID = ("google.generativeai", "gemini", "VertexGeminiTransport")


def files() -> list[Path]:
    result: list[Path] = []
    for directory, names, filenames in os.walk(ROOT):
        names[:] = [name for name in names if name not in EXCLUDED]
        result.extend(Path(directory) / name for name in filenames if Path(name).suffix in SOURCE_SUFFIXES)
    return result


def main() -> int:
    failures: list[str] = []
    for path in files():
        is_firebase_client_config = path.name == "google-services.json" and path.parent == ROOT / "android" / "app"
        if path.name in FORBIDDEN_NAMES and "src" not in path.parts:
            failures.append(f"credential-like file outside Android source variant: {path.relative_to(ROOT)}")
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        test_path = any(part.lower() in {"tests", "test", "debugtest", "androidtest"} for part in path.parts) or path.name.lower().startswith("test") or "test-" in path.name.lower()
        if path.suffix in {".py", ".kt", ".kts", ".gradle", ".gradle.kts", ".json", ".yaml", ".yml", ".ps1", ".tf"}:
            for pattern in FORBIDDEN_PATTERNS:
                public_firebase_key = is_firebase_client_config and pattern.pattern.startswith("AI")
                if pattern.search(text) and not test_path and not public_firebase_key and "scripts/phase" not in str(path).replace("\\", "/"):
                    failures.append(f"sensitive/test-only marker in release source: {path.relative_to(ROOT)}")
    android = ROOT / "android" / "app" / "src" / "main"
    if android.exists():
        for path in android.rglob("*.kt"):
            text = path.read_text(encoding="utf-8")
            for marker in FORBIDDEN_AI_ANDROID:
                if marker.lower() in text.lower():
                    failures.append(f"Android local-AI/provider marker: {path.relative_to(ROOT)}")
    for name in ("release/EVIDENCE_MANIFEST.json", "release/RC_MANIFEST.json"):
        path = ROOT / name
        if not path.exists():
            failures.append(f"missing release manifest: {name}")
        else:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("tests_executed") is True:
                failures.append(f"release manifest claims tests executed without attached certification: {name}")
    if failures:
        print("RELEASE_GATE=FAIL")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print("RELEASE_GATE=PASS_STATIC_ONLY")
    print("External provider, Play, device, and production evidence remain pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
