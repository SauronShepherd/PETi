from app.analysis.service import AnalysisService
from app.safety.engine import evaluate_safety


def test_urgent_owner_context_overrides_reassuring_model_summary():
    decision = evaluate_safety(
        {"summary": "Everything is clear", "red_flags": []}, "The dog has difficulty breathing"
    )
    assert decision.state == "URGENT"


def test_red_flag_text_is_visible_to_deterministic_safety_engine():
    decision = evaluate_safety({"summary": "Review", "red_flags": ["Severe bleeding is visible"]})
    assert decision.state == "URGENT"


def test_nested_observation_urgent_signal_cannot_be_downgraded():
    decision = evaluate_safety(
        {"summary": "Review", "observations": [{"text": "The dog has collapsed"}]}
    )
    assert decision.state == "URGENT"


def test_pipeline_safety_merge_rejects_downgrade_and_unknown_model_states():
    assert AnalysisService.merge_safety("URGENT", "CLEAR") == "URGENT"
    assert AnalysisService.merge_safety("URGENT", "REVIEW") == "URGENT"
    assert AnalysisService.merge_safety("CLEAR", "REVIEW") == "REVIEW"
    assert AnalysisService.merge_safety("CLEAR", "not-a-state") == "CLEAR"
