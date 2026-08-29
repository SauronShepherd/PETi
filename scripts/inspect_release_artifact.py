"""Inspect an optional signed Android artifact without requiring Play access."""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

FORBIDDEN = (
    "service-account.json",
    "google-services.json",
    "gemini",
    "generativeai",
    "tflite",
    "onnx",
    "local-test:",
    "debug-bypass",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path, nargs="?")
    parser.add_argument("--debug", action="store_true", help="inspect a debug artifact; permit the intentional local-test marker")
    args = parser.parse_args()
    if not args.artifact:
        print("RELEASE_ARTIFACT=NOT_PROVIDED")
        return 0
    if not args.artifact.exists() or args.artifact.suffix.lower() not in {".aab", ".apk"}:
        print("RELEASE_ARTIFACT=INVALID")
        return 1
    with zipfile.ZipFile(args.artifact) as archive:
        names = [name.lower() for name in archive.namelist()]
        content_names = "\n".join(names)
        # Inspect the archive payload as well as filenames. APK/AAB entries
        # may hide dependency identifiers in DEX/resources while keeping
        # innocuous filenames.
        payload = b"\n".join(
            archive.read(info)[:20_000_000]
            for info in archive.infolist()
            if not info.is_dir() and info.filename.upper() != "META-INF/MANIFEST.MF"
        ).lower()
    forbidden = tuple(marker for marker in FORBIDDEN if not (args.debug and marker == "local-test:"))
    findings = [marker for marker in forbidden if marker.encode() in payload or marker in content_names]
    if findings:
        print("RELEASE_ARTIFACT=FAIL")
        print("forbidden markers: " + ", ".join(sorted(set(findings))))
        return 1
    print("RELEASE_ARTIFACT=PASS_STATIC_ONLY")
    print(f"entries={len(names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
