"""Phase 7 Veterinary Record Vault domain and service.

The document bytes remain owned by the Phase 3 media pipeline.  This module
stores only owner-scoped metadata, extraction candidates, review audit, and
explicitly accepted documented facts.
"""
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from threading import RLock
from uuid import uuid4


class DocumentType(StrEnum):
    VETERINARY_REPORT = "VETERINARY_REPORT"
    LAB_RESULT = "LAB_RESULT"
    VACCINATION_RECORD = "VACCINATION_RECORD"
    PRESCRIPTION_RECORD = "PRESCRIPTION_RECORD"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    IMAGING_REPORT = "IMAGING_REPORT"
    INVOICE_OR_VISIT_SUMMARY = "INVOICE_OR_VISIT_SUMMARY"
    OTHER = "OTHER"


class ExtractionStatus(StrEnum):
    NOT_REQUESTED = "NOT_REQUESTED"
    QUEUED = "QUEUED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CandidateStatus(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    CONFIRMED = "CONFIRMED"
    CORRECTED = "CORRECTED"
    REJECTED = "REJECTED"


class ReviewAction(StrEnum):
    CONFIRM = "CONFIRM"
    CORRECT = "CORRECT"
    REJECT = "REJECT"


FACT_TYPES = {
    "WEIGHT", "TEMPERATURE", "VACCINATION", "MEDICATION_DOCUMENTATION",
    "DIAGNOSIS_DOCUMENTATION", "PROCEDURE", "LAB_VALUE", "VISIT_DATE",
    "PROVIDER_NAME", "FOLLOW_UP_DATE", "FREEFORM_CLINICAL_NOTE",
}


@dataclass
class SourceAnchor:
    document_id: str
    page_number: int | None = None
    page_label: str | None = None
    bounding_box: dict | None = None
    text_snippet: str | None = None
    anchor_type: str = "DOCUMENT_ONLY"


@dataclass
class VeterinaryDocument:
    id: str
    owner_user_id: str
    animal_id: str
    source_media_id: str
    document_type: DocumentType
    title: str
    document_date: datetime | None = None
    provider_name: str | None = None
    notes: str | None = None
    extraction_status: ExtractionStatus = ExtractionStatus.NOT_REQUESTED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None


@dataclass
class CandidateFact:
    id: str
    document_id: str
    owner_user_id: str
    animal_id: str
    extraction_analysis_id: str
    fact_type: str
    candidate_value: str | None = None
    candidate_unit: str | None = None
    candidate_text: str | None = None
    event_date: datetime | None = None
    date_precision: str | None = None
    source_anchor: SourceAnchor | None = None
    confidence: str = "LOW"
    status: CandidateStatus = CandidateStatus.PENDING_REVIEW
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    reviewed_at: datetime | None = None


@dataclass
class CandidateFactReview:
    id: str
    candidate_fact_id: str
    user_id: str
    action: ReviewAction
    corrected_value: str | None = None
    corrected_unit: str | None = None
    corrected_text: str | None = None
    corrected_date: datetime | None = None
    reviewed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DocumentedFact:
    id: str
    owner_user_id: str
    animal_id: str
    fact_type: str
    value: str | None = None
    unit: str | None = None
    normalized_value: str | None = None
    normalized_unit: str | None = None
    text_value: str | None = None
    event_date: datetime | None = None
    date_precision: str | None = None
    source_class: str = "DOCUMENTED"
    source_document_id: str = ""
    source_candidate_fact_id: str | None = None
    source_anchor: SourceAnchor | None = None
    review_action: ReviewAction = ReviewAction.CONFIRM
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None


class RecordVaultError(ValueError):
    pass


class RecordVaultService:
    def __init__(self, pets, media, store=None, clock=None, phase6=None):
        self.pets, self.media, self.store, self.phase6 = pets, media, store, phase6
        self.clock = clock or (lambda: datetime.now(UTC))
        self.documents: dict[str, VeterinaryDocument] = {}
        self.candidates: dict[str, CandidateFact] = {}
        self.reviews: dict[str, list[CandidateFactReview]] = {}
        self.facts: dict[str, DocumentedFact] = {}
        self.extraction_requests: set[tuple[str, str, str]] = set()
        self.lock = RLock()
        self._hydrate()

    def _hydrate(self):
        if not self.store or not hasattr(self.store, "all"):
            return
        for collection, target, enum_fields in (
            ("veterinary_documents", self.documents, {"document_type": DocumentType, "extraction_status": ExtractionStatus}),
            ("candidate_facts", self.candidates, {"status": CandidateStatus}),
            ("documented_facts", self.facts, {"review_action": ReviewAction}),
            ):
            try:
                rows = self.store.all(collection)
            except Exception:  # noqa: BLE001 - one unavailable records collection must not crash startup
                rows = []
            for raw in rows:
                try:
                    raw = dict(raw)
                    datetime_fields = {
                        "veterinary_documents": ("document_date", "created_at", "updated_at", "deleted_at"),
                        # event_date may intentionally be a partial source date
                        # (for example, "2026-05"); retain it verbatim.
                        "candidate_facts": ("created_at", "reviewed_at"),
                        "documented_facts": ("created_at", "updated_at", "deleted_at"),
                    }[collection]
                    for key in datetime_fields:
                        value = raw.get(key)
                        if value is not None and not isinstance(value, datetime):
                            raw[key] = datetime.fromisoformat(str(value))
                    for key, enum in enum_fields.items():
                        raw[key] = enum(raw[key])
                    if raw.get("source_anchor"):
                        raw["source_anchor"] = SourceAnchor(**raw["source_anchor"])
                    item = (VeterinaryDocument if collection == "veterinary_documents" else CandidateFact if collection == "candidate_facts" else DocumentedFact)(**raw)
                    target[item.id] = item
                except (TypeError, KeyError, ValueError):
                    continue
        try:
            extraction_rows = self.store.all("record_extraction_requests")
        except Exception:  # noqa: BLE001 - unavailable auxiliary state must not crash startup
            extraction_rows = []
        for raw in extraction_rows:
            try:
                self.extraction_requests.add((raw["owner_user_id"], raw["document_id"], raw["analysis_id"]))
            except (KeyError, TypeError):
                continue

    def _save(self, collection, value):
        if self.store and hasattr(self.store, "put_raw"):
            data = asdict(value)
            self.store.put_raw(collection, value.id, data)

    def _owned_pet(self, owner, pet):
        if not self.pets.get(owner, pet):
            raise RecordVaultError("PET_NOT_FOUND")

    def _owned_document(self, owner, document_id):
        item = self.documents.get(document_id)
        if not item or item.owner_user_id != owner or item.deleted_at:
            raise RecordVaultError("RECORD_NOT_FOUND")
        return item

    def create(self, owner, pet, source_media_id, values):
        with self.lock:
            self._owned_pet(owner, pet)
            media = self.media.get_owned(owner, source_media_id)
            if not media or str(media.status) != "READY":
                raise RecordVaultError("RECORD_SOURCE_MEDIA_INVALID")
            if str(media.purpose) != "DOCUMENT_SOURCE" or str(media.retention_class) != "CLINICAL_DOCUMENT":
                raise RecordVaultError("RECORD_SOURCE_MEDIA_INVALID")
            if str(media.media_type) != "DOCUMENT":
                raise RecordVaultError("RECORD_FORMAT_UNSUPPORTED")
            if media.mime_type_declared == "application/pdf" and values.get("password_protected"):
                raise RecordVaultError("RECORD_PASSWORD_PROTECTED")
            try:
                doc_type = DocumentType(values.get("document_type", DocumentType.OTHER))
            except ValueError as exc:
                raise RecordVaultError("RECORD_METADATA_INVALID") from exc
            now = self.clock()
            item = VeterinaryDocument(str(uuid4()), owner, pet, source_media_id, doc_type,
                values.get("title") or media.original_filename or "Veterinary record",
                values.get("document_date"), values.get("provider_name"), values.get("notes"),
                created_at=now, updated_at=now)
            self.documents[item.id] = item
            self._save("veterinary_documents", item)
            return item

    def list(self, owner, pet):
        return sorted((x for x in self.documents.values() if x.owner_user_id == owner and x.animal_id == pet and not x.deleted_at), key=lambda x: (x.document_date or x.created_at), reverse=True)

    def get(self, owner, document_id):
        return self._owned_document(owner, document_id)

    def update(self, owner, document_id, values):
        item = self._owned_document(owner, document_id)
        for key in ("title", "document_date", "provider_name", "notes", "document_type"):
            if key in values:
                setattr(item, key, DocumentType(values[key]) if key == "document_type" else values[key])
        item.updated_at = self.clock(); self._save("veterinary_documents", item); return item

    def access(self, owner, document_id):
        item = self._owned_document(owner, document_id)
        try:
            return self.media.access(owner, item.source_media_id)
        except Exception as exc:
            raise RecordVaultError("RECORD_ACCESS_UNAVAILABLE") from exc

    def candidates_for(self, owner, document_id):
        self._owned_document(owner, document_id)
        return sorted((x for x in self.candidates.values() if x.owner_user_id == owner and x.document_id == document_id), key=lambda x: x.created_at)

    def extract(self, owner, document_id, payload=None, analysis_id=None):
        document = self._owned_document(owner, document_id)
        with self.lock:
            analysis_id = analysis_id or "document-extraction-" + document.id
            request_key = (owner, document.id, analysis_id)
            if request_key in self.extraction_requests:
                return document
            payload = payload or {}
            self._validate_extraction_payload(payload, document.id)
            document.extraction_status = ExtractionStatus.REVIEW_REQUIRED
            document.updated_at = self.clock()
            for raw in (payload or {}).get("fact_candidates", []):
                fact_type = str(raw.get("fact_type", ""))
                if fact_type not in FACT_TYPES:
                    continue
                anchor_raw = raw.get("source_anchor") or {"document_id": document.id, "anchor_type": "DOCUMENT_ONLY"}
                if anchor_raw.get("document_id") != document.id:
                    continue
                self._validate_fact_date(raw.get("event_date"), raw.get("date_precision"))
                anchor = SourceAnchor(**{k: anchor_raw.get(k) for k in SourceAnchor.__dataclass_fields__})
                item = CandidateFact(str(uuid4()), document.id, owner, document.animal_id, analysis_id, fact_type,
                    raw.get("candidate_value"), raw.get("candidate_unit"), raw.get("candidate_text"),
                    raw.get("event_date"), raw.get("date_precision"), anchor,
                    raw.get("confidence", "LOW") if raw.get("confidence") in {"LOW", "MEDIUM", "HIGH"} else "LOW")
                self.candidates[item.id] = item; self._save("candidate_facts", item)
            self.extraction_requests.add(request_key)
            self._save_extraction_request(owner, document.id, analysis_id)
            self._save("veterinary_documents", document)
            return document

    @staticmethod
    def _validate_extraction_payload(payload, document_id):
        required = {"document_metadata_candidates", "fact_candidates", "extraction_limitations"}
        if not isinstance(payload, dict) or not required.issubset(payload) or any(
            not isinstance(payload[name], list) for name in required
        ):
            raise RecordVaultError("RECORD_EXTRACTION_FAILED")
        allowed_anchor_types = {"PAGE", "REGION", "TEXT_SPAN", "DOCUMENT_ONLY"}
        for raw in payload["fact_candidates"]:
            if not isinstance(raw, dict) or raw.get("fact_type") not in FACT_TYPES:
                raise RecordVaultError("CANDIDATE_FACT_VALUE_INVALID")
            if raw.get("candidate_value") is None and raw.get("candidate_text") is None:
                raise RecordVaultError("CANDIDATE_FACT_VALUE_INVALID")
            anchor = raw.get("source_anchor")
            if not isinstance(anchor, dict) or anchor.get("document_id") != document_id:
                raise RecordVaultError("CANDIDATE_FACT_SOURCE_INVALID")
            if anchor.get("anchor_type", "DOCUMENT_ONLY") not in allowed_anchor_types:
                raise RecordVaultError("CANDIDATE_FACT_SOURCE_INVALID")
            if raw.get("confidence", "LOW") not in {"LOW", "MEDIUM", "HIGH"}:
                raise RecordVaultError("CANDIDATE_FACT_VALUE_INVALID")

    @staticmethod
    def _validate_fact_date(event_date, date_precision):
        if event_date is None:
            return
        if date_precision not in {"YEAR", "MONTH", "DAY"}:
            raise RecordVaultError("CANDIDATE_FACT_VALUE_INVALID")
        if isinstance(event_date, datetime):
            return
        if not isinstance(event_date, str):
            raise RecordVaultError("CANDIDATE_FACT_VALUE_INVALID")
        patterns = {"YEAR": r"^\d{4}$", "MONTH": r"^\d{4}-\d{2}$", "DAY": r"^\d{4}-\d{2}-\d{2}(?:T.*)?$"}
        if not re.fullmatch(patterns[date_precision], event_date):
            raise RecordVaultError("CANDIDATE_FACT_VALUE_INVALID")

    def _save_extraction_request(self, owner, document_id, analysis_id):
        if self.store and hasattr(self.store, "put_raw"):
            self.store.put_raw("record_extraction_requests", f"{owner}:{document_id}:{analysis_id}", {
                "owner_user_id": owner, "document_id": document_id, "analysis_id": analysis_id,
            })

    def extract_local_fixture(self, owner, document_id, fixture_text, analysis_id=None):
        """Deterministic LOCAL/Floci extraction adapter.

        This intentionally parses only explicit document-like values and emits
        review candidates. It is not a substitute for production OCR/VLM.
        """
        if not isinstance(fixture_text, str) or not fixture_text.strip():
            raise RecordVaultError("DOCUMENT_EXTRACTION_INPUT_REQUIRED")
        document = self._owned_document(owner, document_id)
        candidates = []
        patterns = (
            ("WEIGHT", r"(?i)\bweight\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(kg|lb)\b"),
            ("TEMPERATURE", r"(?i)\btemperature\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*([cf])\b"),
        )
        for fact_type, pattern in patterns:
            for match in re.finditer(pattern, fixture_text):
                value, unit = match.group(1).replace(",", "."), match.group(2).upper()
                candidates.append({
                    "fact_type": fact_type,
                    "candidate_value": value,
                    "candidate_unit": "°" + unit if fact_type == "TEMPERATURE" else unit.lower(),
                    "candidate_text": match.group(0),
                    "confidence": "HIGH",
                    "source_anchor": {
                        "document_id": document.id,
                        "anchor_type": "TEXT_SPAN",
                        "text_snippet": match.group(0),
                    },
                })
        return self.extract(
            owner,
            document_id,
            {"document_metadata_candidates": [], "fact_candidates": candidates, "extraction_limitations": ["LOCAL_FIXTURE"]},
            analysis_id or "local-document-extraction-" + document.id,
        )

    def review(self, owner, fact_id, action, values=None):
        values = values or {}
        with self.lock:
            candidate = self.candidates.get(fact_id)
            if not candidate or candidate.owner_user_id != owner:
                raise RecordVaultError("CANDIDATE_FACT_NOT_FOUND")
            if candidate.status != CandidateStatus.PENDING_REVIEW:
                # Review is a terminal, explicit human decision.  Returning
                # the prior value here allowed a rejected candidate to be
                # submitted again with CONFIRM/CORRECT and silently created
                # a documented fact, violating the review state machine.
                raise RecordVaultError("CANDIDATE_FACT_ALREADY_REVIEWED")
            try: action = ReviewAction(action)
            except ValueError as exc: raise RecordVaultError("CANDIDATE_FACT_VALUE_INVALID") from exc
            now = self.clock(); candidate.reviewed_at = now
            candidate.status = {ReviewAction.CONFIRM: CandidateStatus.CONFIRMED, ReviewAction.CORRECT: CandidateStatus.CORRECTED, ReviewAction.REJECT: CandidateStatus.REJECTED}[action]
            review = CandidateFactReview(str(uuid4()), fact_id, owner, action, values.get("corrected_value"), values.get("corrected_unit"), values.get("corrected_text"), values.get("corrected_date"), now)
            self.reviews.setdefault(fact_id, []).append(review); self._save("candidate_facts", candidate); self._save("candidate_fact_reviews", review)
            if action == ReviewAction.REJECT:
                return candidate, None
            fact = DocumentedFact(str(uuid4()), owner, candidate.animal_id, candidate.fact_type,
                values.get("corrected_value", candidate.candidate_value), values.get("corrected_unit", candidate.candidate_unit),
                text_value=values.get("corrected_text", candidate.candidate_text), event_date=values.get("corrected_date", candidate.event_date),
                date_precision=candidate.date_precision, source_document_id=candidate.document_id,
                source_candidate_fact_id=candidate.id, source_anchor=candidate.source_anchor, review_action=action,
                created_at=now, updated_at=now)
            self.facts[fact.id] = fact; self._save("documented_facts", fact)
            if self.phase6 and fact.fact_type in {"WEIGHT", "TEMPERATURE"} and fact.value and fact.unit:
                try:
                    self.phase6.measurement(
                        owner, fact.animal_id,
                        {"measurement_type": fact.fact_type, "original_value": fact.value,
                         "original_unit": fact.unit, "source_class": "DOCUMENTED",
                         "measured_at": fact.event_date if isinstance(fact.event_date, datetime) else now,
                         "notes": "Documented in veterinary record " + fact.source_document_id,
                         "source_document_id": fact.source_document_id},
                        "documented-fact:" + fact.id, self.pets,
                    )
                except ValueError:
                    # A documented clinical fact remains canonical even when
                    # its optional measurement projection is not applicable.
                    pass
            return candidate, fact

    def facts_for(self, owner, pet):
        return [x for x in self.facts.values() if x.owner_user_id == owner and x.animal_id == pet and not x.deleted_at]

    def deletion_preview(self, owner, document_id):
        document = self._owned_document(owner, document_id)
        candidate_ids = {x.id for x in self.candidates.values() if x.document_id == document.id and x.owner_user_id == owner}
        facts = [x for x in self.facts.values() if x.source_document_id == document.id and x.owner_user_id == owner and not x.deleted_at]
        measurements = []
        if self.phase6:
            measurements = [m for m in self.phase6.measurements.values()
                            if m.owner_user_id == owner and not m.deleted_at
                            and str(m.source_class) == "DOCUMENTED"
                            and m.source_document_id == document.id]
        return {"record_id": document.id, "dependent_candidate_count": len(candidate_ids), "dependent_documented_fact_count": len(facts), "dependent_measurement_count": len(measurements), "timeline_effects": len(facts) + len(measurements)}

    def delete(self, owner, document_id, confirm_dependencies=False):
        document = self._owned_document(owner, document_id); preview = self.deletion_preview(owner, document_id)
        if preview["dependent_documented_fact_count"] and not confirm_dependencies:
            raise RecordVaultError("RECORD_DELETE_DEPENDENCIES_EXIST")
        now = self.clock(); document.deleted_at = now; document.updated_at = now
        for item in self.candidates.values():
            if item.document_id == document.id: item.status = CandidateStatus.REJECTED; item.reviewed_at = now; self._save("candidate_facts", item)
        for item in self.facts.values():
            if item.source_document_id == document.id: item.deleted_at = now; item.updated_at = now; self._save("documented_facts", item)
        if self.phase6:
            for measurement in self.phase6.measurements.values():
                if (measurement.owner_user_id == owner and not measurement.deleted_at
                        and str(measurement.source_class) == "DOCUMENTED"
                        and measurement.source_document_id == document.id):
                    measurement.deleted_at = now
                    self.phase6._persist("measurements", measurement)
        self._save("veterinary_documents", document); self.media.delete(owner, document.source_media_id)
        return preview

    @staticmethod
    def public(value):
        return asdict(value)
