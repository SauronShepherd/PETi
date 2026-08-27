import pytest
from app.analytics import AnalyticsRecorder


def test_analytics_is_allowlisted_and_payload_is_typed_only():
    recorder = AnalyticsRecorder()
    recorder.record("check_submitted", user_id="u1", check_id="c1")
    assert recorder.events[0]["event"] == "check_submitted"
    assert "raw_media" not in recorder.events[0]
    assert "user_context" not in recorder.events[0]


def test_unknown_analytics_event_is_rejected():
    with pytest.raises(ValueError, match="ANALYTICS_EVENT_NOT_ALLOWED"):
        AnalyticsRecorder().record("raw_question", user_id="u1")
