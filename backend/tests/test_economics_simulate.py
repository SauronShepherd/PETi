import pytest
from app.economics.simulate import simulate_scenarios


def test_simulate_scenarios_uses_integer_non_negative_inputs():
    assert simulate_scenarios([{"operations": 3, "units_per_operation": 4}])[0][
        "estimated_cost_units"
    ] == 12


@pytest.mark.parametrize(
    "scenario",
    [
        {"operations": True},
        {"operations": 1.5},
        {"operations": "1"},
        {"operations": -1},
        {"units_per_operation": False},
        {"units_per_operation": 1.5},
        {"units_per_operation": "1"},
        {"units_per_operation": -1},
        None,
    ],
)
def test_simulate_scenarios_rejects_malformed_inputs(scenario):
    with pytest.raises(ValueError, match="SCENARIO_"):
        simulate_scenarios([scenario])
