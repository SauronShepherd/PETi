from datetime import UTC, datetime
from types import SimpleNamespace

from app.records.vault import CandidateStatus, RecordVaultService, ReviewAction
from app.reports.service import WeeklyReportService


class Pets:
    def get(self, owner, pet_id):
        return SimpleNamespace(id=pet_id, owner_user_id=owner)


class Media:
    def __init__(self):
        self.asset = SimpleNamespace(
            id="media-1", status="READY", purpose="DOCUMENT_SOURCE",
            retention_class="CLINICAL_DOCUMENT", media_type="DOCUMENT",
            mime_type_declared="application/pdf", original_filename="visit.pdf",
        )

    def get_owned(self, owner, media_id):
        return self.asset if owner == "u" and media_id == self.asset.id else None

    def access(self, owner, media_id):
        return {"read_url": "local://document"}

    def delete(self, owner, media_id):
        return True


def test_local_fixture_stays_candidate_only_until_review():
    service = RecordVaultService(Pets(), Media())
    document = service.create("u", "pet-1", "media-1", {"document_type": "OTHER", "title": "Visit"})
    service.extract_local_fixture("u", document.id, "Weight: 22.4 lb\nTemperature: 101.7 F")
    candidates = service.candidates_for("u", document.id)
    assert {x.fact_type for x in candidates} == {"WEIGHT", "TEMPERATURE"}
    assert all(x.status == CandidateStatus.PENDING_REVIEW for x in candidates)
    _, fact = service.review("u", candidates[0].id, ReviewAction.CONFIRM.value)
    assert fact is not None and fact.source_document_id == document.id


def test_record_access_is_owner_scoped():
    service = RecordVaultService(Pets(), Media())
    document = service.create("u", "pet-1", "media-1", {})
    assert service.access("u", document.id)["read_url"].startswith("local://")
    try:
        service.access("other", document.id)
    except ValueError as exc:
        assert str(exc) == "RECORD_NOT_FOUND"
    else:
        raise AssertionError("cross-owner record access unexpectedly succeeded")


def test_record_vault_hydrates_serialized_document_timestamps():
    instant = datetime(2026, 8, 26, tzinfo=UTC)

    class Store:
        def all(self, collection):
            return [{
                "id": "doc-1", "owner_user_id": "u", "animal_id": "pet-1", "source_media_id": "media-1",
                "document_type": "OTHER", "title": "Visit", "document_date": instant.isoformat(),
                "extraction_status": "NOT_REQUESTED", "created_at": instant.isoformat(), "updated_at": instant.isoformat(),
                "deleted_at": None,
            }] if collection == "veterinary_documents" else []

    service = RecordVaultService(Pets(), Media(), store=Store())
    assert service.documents["doc-1"].document_date == instant
    assert service.documents["doc-1"].updated_at == instant


def test_record_vault_preserves_partial_candidate_dates_on_restart():
    class Store:
        def all(self, collection):
            return [{
                "id": "candidate-1", "document_id": "doc-1", "owner_user_id": "u", "animal_id": "pet-1",
                "extraction_analysis_id": "analysis-1", "fact_type": "VISIT_DATE", "event_date": "2026-05",
                "date_precision": "MONTH", "status": "PENDING_REVIEW", "created_at": datetime(2026, 8, 26, tzinfo=UTC).isoformat(),
                "reviewed_at": None,
            }] if collection == "candidate_facts" else []

    service = RecordVaultService(Pets(), Media(), store=Store())
    assert service.candidates["candidate-1"].event_date == "2026-05"


def test_repeated_extraction_request_is_idempotent():
    service = RecordVaultService(Pets(), Media())
    document = service.create("u", "pet-1", "media-1", {})
    service.extract_local_fixture("u", document.id, "Weight: 22.4 lb", "analysis-1")
    service.extract_local_fixture("u", document.id, "Weight: 22.4 lb", "analysis-1")
    candidates = service.candidates_for("u", document.id)
    assert len(candidates) == 1
    assert candidates[0].extraction_analysis_id == "analysis-1"


def test_correct_preserves_candidate_and_creates_corrected_documented_fact():
    service = RecordVaultService(Pets(), Media())
    document = service.create("u", "pet-1", "media-1", {})
    service.extract_local_fixture("u", document.id, "Weight: 44.1 lb", "analysis-correct")
    candidate = service.candidates_for("u", document.id)[0]
    reviewed, fact = service.review("u", candidate.id, ReviewAction.CORRECT.value, {
        "corrected_value": "44.6", "corrected_unit": "lb",
    })
    assert reviewed.candidate_value == "44.1" and reviewed.candidate_unit == "lb"
    assert fact is not None and fact.value == "44.6" and fact.unit == "lb"


def test_rejected_candidate_cannot_be_reconfirmed():
    service = RecordVaultService(Pets(), Media())
    document = service.create("u", "pet-1", "media-1", {})
    service.extract_local_fixture("u", document.id, "Weight: 44.1 lb", "analysis-reject")
    candidate = service.candidates_for("u", document.id)[0]
    rejected, fact = service.review("u", candidate.id, ReviewAction.REJECT.value)
    assert rejected.status == CandidateStatus.REJECTED and fact is None
    try:
        service.review("u", candidate.id, ReviewAction.CONFIRM.value)
    except ValueError as exc:
        assert str(exc) == "CANDIDATE_FACT_ALREADY_REVIEWED"
    else:
        raise AssertionError("rejected candidate was re-confirmed")


class Phase6Measurements:
    def __init__(self):
        self.measurements = {}
        self.persisted = []

    def _persist(self, collection, value):
        self.persisted.append((collection, value))

    def measurement(self, *args, **kwargs):
        return None


def test_delete_document_keeps_unrelated_measured_weight():
    phase6 = Phase6Measurements()
    phase6.measurements["measured-1"] = SimpleNamespace(
        owner_user_id="u", deleted_at=None, source_class="MEASURED", notes="home scale",
    )
    service = RecordVaultService(Pets(), Media(), phase6=phase6)
    document = service.create("u", "pet-1", "media-1", {})
    service.extract_local_fixture("u", document.id, "Weight: 22.4 lb", "analysis-delete")
    candidate = service.candidates_for("u", document.id)[0]
    service.review("u", candidate.id, ReviewAction.CONFIRM.value)
    assert service.deletion_preview("u", document.id)["dependent_documented_fact_count"] == 1
    service.delete("u", document.id, confirm_dependencies=True)
    assert phase6.measurements["measured-1"].deleted_at is None


def test_delete_document_cascades_linked_documented_measurement_by_foreign_key():
    phase6 = Phase6Measurements()
    phase6.measurements["documented-1"] = SimpleNamespace(
        owner_user_id="u", deleted_at=None, source_class="DOCUMENTED",
        source_document_id="will-be-set", notes="owner edited notes",
    )
    service = RecordVaultService(Pets(), Media(), phase6=phase6)
    document = service.create("u", "pet-1", "media-1", {})
    phase6.measurements["documented-1"].source_document_id = document.id
    assert service.deletion_preview("u", document.id)["dependent_measurement_count"] == 1
    service.delete("u", document.id, confirm_dependencies=True)
    assert phase6.measurements["documented-1"].deleted_at is not None


def test_cloud_extraction_rejects_missing_schema_and_foreign_anchor():
    service = RecordVaultService(Pets(), Media())
    document = service.create("u", "pet-1", "media-1", {})
    try:
        service.extract("u", document.id, {"fact_candidates": []}, "invalid-schema")
    except ValueError as exc:
        assert str(exc) == "RECORD_EXTRACTION_FAILED"
    else:
        raise AssertionError("malformed extraction payload was accepted")
    try:
        service.extract("u", document.id, {
            "document_metadata_candidates": [], "extraction_limitations": [],
            "fact_candidates": [{"fact_type": "WEIGHT", "candidate_value": "2", "candidate_unit": "kg",
                                  "source_anchor": {"document_id": "other", "anchor_type": "PAGE"}}],
        }, "foreign-anchor")
    except ValueError as exc:
        assert str(exc) == "CANDIDATE_FACT_SOURCE_INVALID"
    else:
        raise AssertionError("foreign extraction anchor was accepted")


def test_partial_month_date_is_preserved_without_inventing_a_day():
    service = RecordVaultService(Pets(), Media())
    document = service.create("u", "pet-1", "media-1", {})
    service.extract("u", document.id, {
        "document_metadata_candidates": [], "extraction_limitations": [],
        "fact_candidates": [{"fact_type": "VISIT_DATE", "candidate_text": "May 2026",
                              "event_date": "2026-05", "date_precision": "MONTH",
                              "source_anchor": {"document_id": document.id, "anchor_type": "PAGE", "page_number": 1}}],
    }, "partial-date")
    candidate = service.candidates_for("u", document.id)[0]
    assert candidate.event_date == "2026-05" and candidate.date_precision == "MONTH"
    _, fact = service.review("u", candidate.id, ReviewAction.CONFIRM.value)
    assert fact is not None and fact.event_date == "2026-05" and fact.date_precision == "MONTH"
    assert WeeklyReportService._fact_in_week(fact, datetime(2026, 5, 4, tzinfo=UTC), datetime(2026, 5, 11, tzinfo=UTC))
