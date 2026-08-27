from app.peti_check.contracts import PetiCheckResultV1


def test_evidence_quality_legacy_aliases_are_normalized_to_canonical_levels():
    assert PetiCheckResultV1.from_payload({"summary": "x", "evidence_quality": "HIGH"}).evidence_quality.level == "GOOD"
    assert PetiCheckResultV1.from_payload({"summary": "x", "evidence_quality": "MEDIUM"}).evidence_quality.level == "PARTIAL"
    assert PetiCheckResultV1.from_payload({"summary": "x", "evidence_quality": "LOW"}).evidence_quality.level == "INSUFFICIENT"
