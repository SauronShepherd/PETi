"""Validate release manifests remain internally consistent and fail-closed."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate_artifact(path_text: str, expected: str, label: str, failures: list[str]) -> None:
    path = (ROOT / path_text).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError:
        failures.append(f"{label} artifact escapes repository: {path_text}")
        return
    if not path.is_file():
        failures.append(f"{label} artifact is missing: {path_text}")
        return
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        failures.append(f"{label} artifact hash mismatch: {path_text}")

def main() -> int:
    evidence = load("release/EVIDENCE_MANIFEST.json")
    rc = load("release/RC_MANIFEST.json")
    phase17 = load("release/evidence/phase17/PHASE17_EVIDENCE_MANIFEST.json")
    failures = []
    for artifact in evidence.get("artifacts", []):
        if not isinstance(artifact, dict) or not artifact.get("path") or not artifact.get("sha256"):
            failures.append("evidence contains an invalid artifact declaration")
            continue
        validate_artifact(artifact["path"], artifact["sha256"], "evidence", failures)
    for path_text, expected in rc.get("artifact_hashes", {}).items():
        if not isinstance(path_text, str) or not isinstance(expected, str):
            failures.append("rc contains an invalid artifact hash declaration")
            continue
        validate_artifact(path_text, expected, "rc", failures)
    for name, item in (("evidence", evidence), ("rc", rc), ("phase17", phase17)):
        if "PENDING" not in str(item.get("status", "")):
            failures.append(f"{name} status is not pending-safe")
    if evidence.get("tests_executed") is True or rc.get("tests_executed") is True:
        failures.append("source manifests cannot claim tests_executed=true")
    if phase17.get("production_credentials_included") is not False:
        failures.append("phase17 must exclude production credentials")
    if not phase17.get("external_gates"):
        failures.append("phase17 external gates are missing")
    gradle = (ROOT / "android/app/build.gradle.kts").read_text(encoding="utf-8")
    for required_input in ("PETI_RELEASE_API_BASE_URL", "PETI_GOOGLE_WEB_CLIENT_ID"):
        if required_input not in gradle:
            failures.append(f"Android release input is missing: {required_input}")
    if "https://api.peti.example" in gradle:
        failures.append("Android release still contains the placeholder production API URL")
    if failures:
        print("RELEASE_MANIFESTS=FAIL")
        print("\n".join(failures))
        return 1
    print("RELEASE_MANIFESTS=PASS_FAIL_CLOSED_EXTERNAL_GATES_EXPLICIT")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
