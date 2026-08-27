"""Read-only credit ledger audit entry point for operational use."""
import json
import sys


def audit(service):
    result = service.audit()
    if result.get("status") != "OK":
        raise RuntimeError("LEDGER_AUDIT_FAILED")
    return result


if __name__ == "__main__":
    print(json.dumps({"status": "SCRIPT_REQUIRES_SERVICE_WIRING", "read_only": True}))
