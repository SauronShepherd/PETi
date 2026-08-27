import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
from validate_acceptance_bundle import SCENARIOS, validate


def _bundle():
    evidence = {
        "job_id": "job-1",
        "result_id": "result-1",
        "reservation_ledger": {"reservation": "consumed"},
        "provider_request_id": "provider-1",
        "analytics_events": [{"event": "check_completed", "check_id": "job-1"}],
    }
    return {"schema_version": "1.0.0", "scenarios": {name: evidence for name in SCENARIOS}}


def test_acceptance_bundle_requires_all_scenarios_and_sanitized_fields():
    assert validate(_bundle()) == []
    incomplete = _bundle()
    del incomplete["scenarios"]["urgent_safety"]
    assert any("exactly the six" in error for error in validate(incomplete))


def test_acceptance_bundle_rejects_sensitive_evidence():
    bundle = _bundle()
    bundle["scenarios"]["funded_check"]["signed_url"] = "must-not-be-stored"
    assert any("signed_url" in error for error in validate(bundle))
