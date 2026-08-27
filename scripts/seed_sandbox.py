"""Builds deterministic seed descriptions; does not contact GCP."""
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SandboxIdentity:
    user_id: str
    pet_id: str
    species: str = "DOG"


def seed_plan() -> dict:
    return {"identities": [asdict(SandboxIdentity("sandbox-owner", "sandbox-dog"))], "provider": "FAKE", "billing": "FAKE", "raw_media": False}


if __name__ == "__main__":
    print(json.dumps({"status": "PLAN_ONLY", **seed_plan()}, sort_keys=True))
