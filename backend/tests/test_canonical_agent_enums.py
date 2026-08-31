import pytest
from app.domain.agents.enums import RunStatus, legacy_run_status


def test_legacy_statuses_map_explicitly_to_canonical_values():
    assert legacy_run_status("QUEUED") is RunStatus.EXECUTING
    assert legacy_run_status("CANCELLED") is RunStatus.CANCELED


def test_unknown_legacy_status_fails_closed():
    with pytest.raises(ValueError, match="AGENT_RUN_STATUS_UNKNOWN"):
        legacy_run_status("UNKNOWN")
