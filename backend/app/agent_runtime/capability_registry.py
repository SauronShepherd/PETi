from dataclasses import dataclass
from enum import StrEnum


class ReleaseState(StrEnum):
    DISABLED = "DISABLED"
    INTERNAL = "INTERNAL"
    PUBLIC = "PUBLIC"


@dataclass(frozen=True)
class CapabilityDescriptor:
    capability_id: str
    version: str
    executor_id: str
    required_inputs: tuple[str, ...]
    output_schema: str
    read_scopes: tuple[str, ...] = ()
    mutation_scopes: tuple[str, ...] = ()
    release_state: ReleaseState = ReleaseState.PUBLIC
    feature_flag: str | None = None
    final_safety_required: bool = True


class CapabilityRegistry:
    def __init__(self, descriptors=()):
        self._items = {(x.capability_id, x.version): x for x in descriptors}

    def get(self, capability_id: str, version: str = "1.0.0") -> CapabilityDescriptor:
        try:
            return self._items[(capability_id, version)]
        except KeyError as exc:
            raise ValueError("AGENT_CAPABILITY_NOT_RELEASED") from exc

    def register(self, descriptor: CapabilityDescriptor) -> None:
        self._items[(descriptor.capability_id, descriptor.version)] = descriptor
