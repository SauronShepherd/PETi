import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "eval"))
import run as evaluation_runner


def test_real_evaluator_preserves_all_critical_gates(monkeypatch):
    delegated = {
        "case_results": [{"id": "case-1", "pass": True}],
        "metrics": {"cases": 1, "passed": 1, "failed": 0},
        "critical_gates": {
            "dangerous_under_triage": True,
            "diagnosis_language": True,
            "fabricated_measurement": True,
            "medication_guidance": True,
            "false_reassurance": True,
            "schema_pass": True,
        },
    }
    monkeypatch.setenv("PETI_REAL_EVAL_COMMAND", "approved-evaluator")
    monkeypatch.setattr(
        evaluation_runner.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout=__import__("json").dumps(delegated)
        ),
    )

    results, metrics, gates = evaluation_runner.run_real("held_out")

    assert results == delegated["case_results"]
    assert metrics == delegated["metrics"]
    assert gates == delegated["critical_gates"]


def test_real_evaluator_rejects_missing_gate(monkeypatch):
    monkeypatch.setenv("PETI_REAL_EVAL_COMMAND", "approved-evaluator")
    monkeypatch.setattr(
        evaluation_runner.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout='{"case_results":[{"id":"case-1"}],"metrics":{"cases":1}}',
        ),
    )

    with pytest.raises(SystemExit, match="critical_gates"):
        evaluation_runner.run_real("held_out")
