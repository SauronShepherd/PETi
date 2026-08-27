import pytest
from app.config.settings import Settings


def test_provider_timeout_must_be_positive():
    with pytest.raises(ValueError, match="must be positive"):
        Settings(provider_timeout_seconds=0).validate_startup()
