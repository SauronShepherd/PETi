from app.analysis.domain import AnalysisResult


def test_cost_metadata_preserves_observed_credit_and_unknown_provider_costs():
    result = AnalysisResult(
        "r", "j", "u", "a", "PETI_CHECK", "peti_check", "1.0.0", {}, "VALID", "PASS",
        "CLEAR", [], "FAKE", "fake-v1", "1.0.0", "1.0.0", "1.0.0", "1.0.0", "DOG-v1",
        {}, {"credits_consumed": 1, "provider_cost_estimate": None, "currency": None},
    )
    assert result.cost_metadata["credits_consumed"] == 1
    assert result.cost_metadata["provider_cost_estimate"] is None
