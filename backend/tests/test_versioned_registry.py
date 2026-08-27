import pytest
from app.ai.registry import ImmutableRegistry


def test_registry_rejects_mutating_used_version():
    registry = ImmutableRegistry()
    registry.register("p", "1", "original")
    registry.activate("p", "1")
    with pytest.raises(ValueError, match="IMMUTABLE"):
        registry.register("p", "1", "changed")
