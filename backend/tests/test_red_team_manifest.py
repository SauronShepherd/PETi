import json
from pathlib import Path

from app.peti_check.guardrails import validate_payload_text


def test_checked_in_red_team_manifest_passes_critical_rules():
    manifest = json.loads(
        (Path(__file__).parents[2] / "eval/peti_check/red_team_v1.json").read_text()
    )
    for case in manifest["cases"]:
        assert set(case["forbidden"]).issubset(set(validate_payload_text(case["payload"])))
