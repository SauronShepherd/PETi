"""Describes sandbox reset boundaries without deleting anything implicitly."""
import json


def reset_plan() -> dict:
    return {"collections": ["users", "pets", "media", "analyses", "weekly_reports", "agent_runs"], "buckets": ["sandbox-media", "sandbox-derived"], "requires_explicit_confirmation": True}


if __name__ == "__main__":
    print(json.dumps({"status": "PLAN_ONLY", **reset_plan()}, sort_keys=True))
