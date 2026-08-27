from app.safety.engine import evaluate_safety


def test_peti_check_clear_vocabulary_is_preserved():
    assert evaluate_safety({"safety_state": "CLEAR"}).state == "CLEAR"


def test_deterministic_urgent_cannot_be_downgraded_by_model_state():
    decision = evaluate_safety({"safety_state": "REVIEW", "summary": "difficulty breathing"})
    assert decision.state == "URGENT"
