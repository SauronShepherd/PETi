from datetime import UTC, datetime

import pytest
from app.reports.contracts import (
    NarrationValidationError,
    SourceReference,
    WeeklyReportNarrationV1,
    WeeklyReportNarrationValidator,
)
from app.reports.service import WeeklyReport


def report(safety_guidance=None):
    return WeeklyReport(
        "report-1", "u", "pet", "2026-08-24", datetime(2026, 8, 24, tzinfo=UTC),
        datetime(2026, 8, 30, 23, 59, tzinfo=UTC), "UTC",
        sections=[{"section_type": "WEIGHT", "state": "EVIDENCE_AVAILABLE", "summary": "One measurement."}],
        source_references=[{"source_entity_type": "MEASUREMENT", "source_entity_id": "measurement-1"}],
        safety_guidance=safety_guidance or [],
    )


def test_narration_requires_known_sources_and_preserves_urgency():
    value = WeeklyReportNarrationV1(
        "Your report is ready. Contact a veterinarian promptly.",
        {"WEIGHT": "One measurement was recorded."},
        [SourceReference("MEASUREMENT", "measurement-1")],
    )
    result = WeeklyReportNarrationValidator.validate(value, report(["Seek veterinary care promptly."]))
    assert result["valid"] is True


def test_narration_rejects_diagnosis_and_unknown_source():
    value = WeeklyReportNarrationV1(
        "The diagnosis is clear.", {"WEIGHT": "Stable."}, [SourceReference("X", "not-in-report")]
    )
    with pytest.raises(NarrationValidationError, match="NARRATION_UNSAFE"):
        WeeklyReportNarrationValidator.validate(value, report())


def test_narration_cannot_downgrade_urgent_guidance():
    value = WeeklyReportNarrationV1("Everything looks fine.", {}, [])
    with pytest.raises(NarrationValidationError, match="NARRATION_UNSAFE"):
        WeeklyReportNarrationValidator.validate(value, report(["Seek veterinary care promptly."]))
