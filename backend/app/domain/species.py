from dataclasses import dataclass


@dataclass(frozen=True)
class SpeciesRegistryEntry:
    species_code: str
    display_name: str
    profile_enabled: bool
    public_enabled: bool
    capability_pack_version: str | None = None


@dataclass(frozen=True)
class SpeciesCapabilityPack:
    species: str
    version: str
    profile_enabled: bool
    supported_analysis_types: tuple[str, ...] = ()
    enabled_analysis_types: tuple[str, ...] = ()
    taxonomy_versions: tuple[str, ...] = ()
    safety_policy_version: str | None = None
    evaluation_certificate_ids: tuple[str, ...] = ()
    public_enabled: bool = True

    def allows(self, analysis_type: str, public: bool = False) -> bool:
        return (
            self.profile_enabled
            and (not public or self.public_enabled)
            and analysis_type in self.enabled_analysis_types
        )
