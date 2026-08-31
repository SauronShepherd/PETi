"""Conservative partial trace backfill. Unknown values remain UNKNOWN."""
from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--environment", required=True)
    parser.add_argument("--limit", type=int, default=100); parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 1000: parser.error("limit must be 1..1000")
    from google.cloud import firestore  # type: ignore[import-untyped]
    client = firestore.Client(project=os.getenv("PETI_PROJECT_ID")); counts = {"selected": 0, "written": 0, "skipped": 0, "errors": 0}
    for snapshot in client.collection("agent_runs").limit(args.limit).stream():
        counts["selected"] += 1; row = snapshot.to_dict() or {}
        if not row.get("owner_user_id") or not row.get("id", snapshot.id): counts["skipped"] += 1; continue
        trace = {"run_id": snapshot.id, "interaction_id": row.get("interaction_id", snapshot.id),
            "correlation_id": row.get("correlation_id", snapshot.id), "owner_user_id": row["owner_user_id"],
            "agent_type": row.get("agent_type", "UNKNOWN"), "environment": args.environment,
            "deployment_id": row.get("deployment_id", "UNKNOWN"), "status": "SUCCEEDED" if row.get("state") == "COMPLETED" else "FAILED" if row.get("state") == "FAILED" else "STARTED",
            "started_at": row.get("started_at") or row.get("created_at") or datetime.now(UTC), "trace_quality": "BACKFILLED_PARTIAL"}
        if args.apply: client.collection("agent_run_traces").document(snapshot.id).set(trace, merge=True)
        counts["written"] += 1
    print(json.dumps({"status": "COMPLETED", "mode": "APPLY" if args.apply else "DRY_RUN", **counts})); return 0


if __name__ == "__main__": raise SystemExit(main())
