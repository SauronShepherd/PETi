from __future__ import annotations


def validate_demo_fixture(data: dict) -> dict:
    if data.get("data_classification") != "SYNTHETIC_DEMO": raise ValueError("LAB_DEMO_CLASSIFICATION_REQUIRED")
    blob = str(data)
    if "owner_user_id" in blob or "REAL" in blob: raise ValueError("LAB_DEMO_PERSONAL_OR_REAL_DATA_FORBIDDEN")
    run_ids = {item.get("run_id") for item in data.get("runs", [])}
    if not {"demo-run-luna", "demo-run-max"}.issubset(run_ids): raise ValueError("LAB_DEMO_CORE_SCENARIOS_MISSING")
    return data
