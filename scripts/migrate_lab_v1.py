"""Idempotent PETi Lab v1 registry migration; dry-run by default."""
from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--environment", required=True, choices=["LOCAL", "DEV", "STAGING", "PRODUCTION"])
    parser.add_argument("--apply", action="store_true"); parser.add_argument("--confirm-production", action="store_true")
    args = parser.parse_args()
    if args.environment == "PRODUCTION" and args.apply and not args.confirm_production:
        parser.error("production apply requires --confirm-production")
    record = {"id": "lab-v1", "schema_version": "1.0.0", "environment": args.environment,
              "deployment_revision": os.getenv("PETI_DEPLOYMENT_REVISION", "unknown"),
              "migrated_at": datetime.now(UTC).isoformat(), "mode": "APPLY" if args.apply else "DRY_RUN"}
    if args.apply:
        from google.cloud import firestore  # type: ignore[import-untyped]
        client = firestore.Client(project=os.getenv("PETI_PROJECT_ID"))
        client.collection("lab_migrations").document(record["id"]).set(record, merge=True)
    print(json.dumps(record)); return 0


if __name__ == "__main__": raise SystemExit(main())
