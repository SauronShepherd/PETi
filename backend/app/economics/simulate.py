def simulate_scenarios(scenarios: list[dict]) -> list[dict]:
    results = []
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("SCENARIO_INVALID")  # noqa: TRY004
        operations = scenario.get("operations", 0)
        units = scenario.get("units_per_operation", 1)
        if (
            isinstance(operations, bool)
            or not isinstance(operations, int)
            or operations < 0
            or isinstance(units, bool)
            or not isinstance(units, int)
            or units < 0
        ):
            raise ValueError("SCENARIO_COST_INPUT_INVALID")
        results.append(
            {
                **scenario,
                "estimated_cost_units": operations * units,
                "safety_policy_unchanged": True,
            }
        )
    return results
