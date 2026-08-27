from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = spec_from_file_location("check_release_manifests", ROOT / "scripts/check_release_manifests.py")
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_validate_artifact_accepts_matching_file(tmp_path):
    target = tmp_path / "artifact.txt"
    target.write_bytes(b"stable")
    failures = []
    import hashlib

    MODULE.ROOT = tmp_path
    MODULE.validate_artifact("artifact.txt", hashlib.sha256(b"stable").hexdigest(), "test", failures)
    assert failures == []


def test_validate_artifact_rejects_missing_and_tampered_files(tmp_path):
    target = tmp_path / "artifact.txt"
    target.write_bytes(b"changed")
    failures = []
    MODULE.ROOT = tmp_path
    MODULE.validate_artifact("missing.txt", "0" * 64, "test", failures)
    MODULE.validate_artifact("artifact.txt", "0" * 64, "test", failures)
    assert any("missing" in item for item in failures)
    assert any("mismatch" in item for item in failures)
