"""Versioned species capability packs with fail-closed feature resolution."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CapabilityPack:
    species: str
    version: str
    status: str
    capabilities: dict
    release_certificate: str | None = None


class CapabilityRegistry:
    def __init__(self):
        self.packs: dict[str, CapabilityPack] = {
            "DOG": CapabilityPack("DOG", "1.0.0", "PUBLIC", {"profile": True, "measurements": True, "care": True, "records": True, "peti_check": True, "initial_scan": True, "dental": True, "feces": True, "body": True}, "dog-v1-certified"),
            "CAT": CapabilityPack("CAT", "1.0.0", "PROFILE_ONLY", {"profile": True, "measurements": True, "care": True, "records": True}, "cat-profile-v1"),
        }

    def resolve(self, species: str) -> CapabilityPack:
        return self.packs.get(species.upper(), CapabilityPack(species.upper(), "0.0.0", "UNSUPPORTED", {}))

    def require(self, species: str, capability: str) -> CapabilityPack:
        pack = self.resolve(species)
        if pack.status != "PUBLIC" or not pack.capabilities.get(capability, False):
            raise ValueError("CAPABILITY_NOT_AVAILABLE")
        return pack

    @staticmethod
    def public(pack: CapabilityPack) -> dict:
        return asdict(pack)
