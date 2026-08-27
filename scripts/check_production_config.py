"""Validate the checked-in production config is a secret-free, fail-closed template."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    snapshot = json.loads((ROOT / "release/PRODUCTION_CONFIG_SNAPSHOT.json").read_text(encoding="utf-8"))
    flags = json.loads((ROOT / "release/PRODUCTION_FEATURE_FLAGS.json").read_text(encoding="utf-8"))
    failures = []
    if snapshot.get("contains_secrets") is not False:
        failures.append("snapshot must declare contains_secrets=false")
    if snapshot.get("environment") != "PRODUCTION":
        failures.append("snapshot environment must be PRODUCTION")
    if flags.get("global_ai_enabled") is not False:
        failures.append("global AI must remain disabled in source template")
    if flags.get("assistant", {}).get("enabled") is not False:
        failures.append("assistant must remain disabled in source template")
    specialists = flags.get("specialists")
    if not isinstance(specialists, dict):
        failures.append("specialists must be an explicit object in source template")
    else:
        for capability, config in specialists.items():
            if not isinstance(config, dict):
                failures.append(f"specialist config must be an object: {capability}")
                continue
            if config.get("enabled") is not False or config.get("public_enabled") is not False:
                failures.append(f"specialist must remain disabled in source template: {capability}")
    if failures:
        print("PRODUCTION_CONFIG=FAIL")
        print("\n".join(failures))
        return 1
    print("PRODUCTION_CONFIG=PASS_SECRET_FREE_FAIL_CLOSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
