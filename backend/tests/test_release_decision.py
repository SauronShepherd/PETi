import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "eval" / "peti_check"))
from release_decision import build_decision


def test_release_decision_fails_closed_until_all_critical_gates_pass():
    decision = build_decision({"schema_pass": True})
    assert decision["go_no_go"] == "NO-GO"
    assert "diagnosis_language" in decision["missing_or_failed_gates"]


def test_release_decision_go_requires_every_critical_gate():
    gates = {
        "dangerous_under_triage": True,
        "diagnosis_language": True,
        "fabricated_measurement": True,
        "medication_guidance": True,
        "false_reassurance": True,
        "schema_pass": True,
    }
    assert build_decision(gates)["go_no_go"] == "GO"


def test_release_decision_persists_provider_configuration_identity():
    decision = build_decision(
        {gate: True for gate in (
            "dangerous_under_triage", "diagnosis_language", "fabricated_measurement",
            "medication_guidance", "false_reassurance", "schema_pass",
        )},
        "GEMINI",
        "gemini-2.5-flash",
        "vertex-v1",
    )
    assert decision["provider_config_version"] == "vertex-v1"
