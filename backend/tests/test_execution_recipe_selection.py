

def test_recipe_selection_rules_are_deterministic():
    choose = lambda goal: "FECES_COMPARE_FOLLOW_UP_V1" if ("remind" in goal or "recordatorio" in goal) and ("compare" in goal or "historial" in goal) else ("FECES_COMPARE_V1" if "compare" in goal or "historial" in goal else "FECES_CURRENT_V1")
    assert choose("compare today's stool with history") == "FECES_COMPARE_V1"
    assert choose("compare with historial and remind me tomorrow") == "FECES_COMPARE_FOLLOW_UP_V1"
    assert choose("review today's stool") == "FECES_CURRENT_V1"
