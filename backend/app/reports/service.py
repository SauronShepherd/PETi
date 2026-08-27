"""Deterministic, source-traceable Weekly PETi Report service."""
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from threading import RLock
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .contracts import WeeklyReportDispatcher, WeeklyReportReconciler


@dataclass(frozen=True)
class WeeklyReportKey:
    animal_id: str
    week_start: datetime
    week_end: datetime
    timezone: str
    week_key: str


@dataclass
class WeeklyReport:
    id: str
    owner_user_id: str
    animal_id: str
    week_key: str
    week_start: datetime
    week_end: datetime
    timezone: str
    report_version: str = "1.0.0"
    generation_status: str = "COMPLETED"
    sections: list[dict] = field(default_factory=list)
    source_references: list[dict] = field(default_factory=list)
    safety_guidance: list[str] = field(default_factory=list)
    change_state: str = "NOT_ENOUGH_DATA"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None


class ReportError(ValueError):
    pass


class WeeklyReportService:
    def __init__(self, pets, phase6, records=None, specialists=None, store=None, clock=None):
        self.pets, self.phase6, self.records, self.specialists, self.store = pets, phase6, records, specialists, store
        self.clock = clock or (lambda: datetime.now(UTC))
        self.reports: dict[str, WeeklyReport] = {}
        self.by_key: dict[tuple[str, str, str], str] = {}
        self.lock = RLock()
        self.dispatcher = WeeklyReportDispatcher(self._generate_for_week_key)
        self.reconciler = WeeklyReportReconciler()
        self._hydrate()

    def _generate_for_week_key(self, owner, pet_id, week_key):
        """Generate the canonical report for an explicit account-local week key."""
        try:
            at = datetime.strptime(str(week_key), "%Y-%m-%d").replace(tzinfo=UTC)
        except (TypeError, ValueError) as exc:
            raise ReportError("REPORT_WEEK_KEY_INVALID") from exc
        return self.generate(owner, pet_id, at=at, timezone="UTC")

    def dispatch_week(self, owner, pet_id, week_key, *, idempotency_key):
        """Scheduler/operator entry point with duplicate delivery suppression."""
        return self.dispatcher.dispatch(owner, pet_id, week_key, idempotency_key=idempotency_key)

    def reconcile_sources(self, owner, report_id, source_ids):
        """Reconcile expected source IDs without changing canonical report data."""
        return self.reconciler.reconcile(self.get(owner, report_id), source_ids)

    def _hydrate(self):
        if not self.store or not hasattr(self.store, "all"):
            return
        try:
            rows = self.store.all("weekly_reports")
        except Exception:  # noqa: BLE001 - transient durable outage must not crash startup
            rows = []
        for data in rows:
            try:
                data = dict(data)
                for key in ("week_start", "week_end", "created_at", "updated_at", "deleted_at"):
                    value = data.get(key)
                    if value is not None and not isinstance(value, datetime):
                        data[key] = datetime.fromisoformat(str(value))
                report = WeeklyReport(**{
                    key: data[key] for key in WeeklyReport.__dataclass_fields__ if key in data
                })
                self.reports[report.id] = report
                self.by_key[(report.owner_user_id, report.animal_id, report.week_key + ":" + report.report_version)] = report.id
            except (KeyError, TypeError, ValueError):
                continue

    @staticmethod
    def key(animal_id, at, timezone="UTC"):
        # Week boundaries belong to the account timezone, not the host clock.
        try:
            zone = ZoneInfo(timezone)
        except (ZoneInfoNotFoundError, ValueError):
            zone = ZoneInfo("UTC")
            timezone = "UTC"
        local = at.astimezone(zone)
        monday = (local - timedelta(days=local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = monday + timedelta(days=7) - timedelta(microseconds=1)
        return WeeklyReportKey(animal_id, monday, end, timezone, monday.strftime("%Y-%m-%d"))

    def _save(self, report):
        if self.store and hasattr(self.store, "put_raw"):
            self.store.put_raw("weekly_reports", report.id, asdict(report))

    def _pet(self, owner, pet_id):
        if not self.pets.get(owner, pet_id):
            raise ReportError("REPORT_PET_NOT_FOUND")

    def _owned(self, owner, report_id):
        report = self.reports.get(report_id)
        if not report or report.owner_user_id != owner or report.deleted_at:
            raise ReportError("REPORT_NOT_FOUND")
        return report

    def generate(self, owner, pet_id, at=None, timezone="UTC", report_version="1.0.0", idem=None):
        self._pet(owner, pet_id); at = at or self.clock(); key = self.key(pet_id, at, timezone)
        identity = (owner, pet_id, key.week_key + ":" + report_version)
        with self.lock:
            if identity in self.by_key:
                return self.reports[self.by_key[identity]]
            timeline = self.phase6.timeline(owner, pet_id, limit=100)
            sections = []
            references = []
            if timeline:
                sections.append({"section_type": "ACTIVITY_AND_OBSERVATIONS", "state": "EVIDENCE_AVAILABLE", "summary": f"{len(timeline)} recorded Timeline item(s)."})
                references.extend({"source_entity_type": x.get("source_entity_type"), "source_entity_id": x.get("source_entity_id")} for x in timeline if x.get("source_entity_id"))
                grouped = {
                    "FECES_CHECK": "FECES_OBSERVATIONS",
                    "BODY_CHECK": "BODY_OBSERVATIONS",
                    "DENTAL_CHECK": "DENTAL_OBSERVATIONS",
                    "CARE_OCCURRENCE": "CARE_ADHERENCE",
                }
                for source_type, section_type in grouped.items():
                    matching = [item for item in timeline if item.get("source_entity_type") == source_type]
                    if matching:
                        sections.append({
                            "section_type": section_type,
                            "state": "EVIDENCE_AVAILABLE",
                            "summary": f"{len(matching)} {source_type.replace('_', ' ').lower()} record(s) were reviewed.",
                        })
            measurements = [m for m in self.phase6.measurements.values() if m.owner_user_id == owner and m.animal_id == pet_id and not m.deleted_at and key.week_start <= m.measured_at <= key.week_end]
            if measurements:
                sections.append({"section_type": "WEIGHT", "state": "EVIDENCE_AVAILABLE", "summary": f"{len(measurements)} measurement(s) recorded this week."})
                references.extend({"source_entity_type": "MEASUREMENT", "source_entity_id": m.id} for m in measurements)
            else:
                sections.append({"section_type": "WEIGHT", "state": "NOT_ENOUGH_DATA", "summary": "No weight measurement was recorded this week."})
            comparable = sorted(measurements, key=lambda item: item.measured_at)
            if len(comparable) < 2:
                change_state = "NOT_ENOUGH_DATA"
            else:
                try:
                    change_state = (
                        "NO_MEANINGFUL_CHANGE"
                        if comparable[0].normalized_value == comparable[-1].normalized_value
                        else "MEANINGFUL_CHANGE"
                    )
                except AttributeError:
                    change_state = "NOT_ENOUGH_DATA"
            safety = []
            for item in timeline:
                if item.get("status") == "URGENT":
                    safety.append("Seek veterinary care promptly based on an urgent PETi Check result.")
            if self.records:
                facts = [f for f in self.records.facts_for(owner, pet_id) if self._fact_in_week(f, key.week_start, key.week_end)]
                if facts:
                    sections.append({"section_type": "CLINICAL_RECORDS", "state": "EVIDENCE_AVAILABLE", "summary": f"{len(facts)} documented fact(s) were reviewed this week."})
                    references.extend({"source_entity_type": "DOCUMENTED_FACT", "source_entity_id": f.id, "source_document_id": f.source_document_id} for f in facts)
            now = self.clock()
            report = WeeklyReport(str(uuid4()), owner, pet_id, key.week_key, key.week_start, key.week_end, timezone, report_version, sections=sections, source_references=references, safety_guidance=safety, change_state=change_state, created_at=now, updated_at=now)
            if not self.validate(report)["valid"]:
                raise ReportError("REPORT_SAFETY_VALIDATION_FAILED")
            self.reports[report.id] = report; self.by_key[identity] = report.id; self._save(report)
            return report

    @staticmethod
    def _fact_in_week(fact, week_start, week_end):
        value = fact.event_date
        if value is None:
            return True
        if isinstance(value, datetime):
            return week_start <= value <= week_end
        # Partial source dates are retained verbatim; compare their covered
        # calendar interval without fabricating a day in the domain object.
        if not isinstance(value, str):
            return False
        try:
            if fact.date_precision == "YEAR" and len(value) == 4:
                start = datetime(int(value), 1, 1, tzinfo=UTC)
                end = datetime(int(value) + 1, 1, 1, tzinfo=UTC)
            elif fact.date_precision == "MONTH" and len(value) == 7:
                year, month = map(int, value.split("-"))
                start = datetime(year, month, 1, tzinfo=UTC)
                end = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1, tzinfo=UTC)
            else:
                return False
        except (ValueError, TypeError):
            return False
        return start <= week_end and end > week_start

    def list(self, owner, pet_id):
        self._pet(owner, pet_id)
        return sorted((x for x in self.reports.values() if x.owner_user_id == owner and x.animal_id == pet_id and not x.deleted_at), key=lambda x: x.created_at, reverse=True)

    @staticmethod
    def validate(report: WeeklyReport) -> dict[str, object]:
        """Validate deterministic report safety before persistence or delivery."""
        material = [section for section in report.sections if section.get("state") == "EVIDENCE_AVAILABLE"]
        reference_ids = {item.get("source_entity_id") for item in report.source_references if item.get("source_entity_id")}
        untraceable = [section.get("section_type", "UNKNOWN") for section in material if not reference_ids]
        text = " ".join(str(section.get("summary", "")) for section in report.sections).lower()
        forbidden = [term for term in ("diagnosis", "diagnose", "prognosis", "prescription", "guaranteed recovery") if term in text]
        result = {
            "material_claim_source_traceability": not untraceable,
            "provenance_preserved": all(item.get("source_entity_type") and item.get("source_entity_id") for item in report.source_references),
            "diagnostic_language_absent": not forbidden,
            "untraceable_sections": untraceable,
            "forbidden_terms": forbidden,
        }
        result["valid"] = all(result[key] for key in ("material_claim_source_traceability", "provenance_preserved", "diagnostic_language_absent"))
        return result

    def get(self, owner, report_id):
        report = self._owned(owner, report_id)
        validation = self.validate(report)
        if not validation["valid"]:
            raise ReportError("REPORT_SAFETY_VALIDATION_FAILED")
        return report

    @staticmethod
    def public(value):
        return asdict(value)
