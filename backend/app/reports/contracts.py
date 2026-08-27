from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from threading import RLock


class WeekKeyService:
    def key(self, at: datetime, timezone: str = "UTC"):
        from .service import WeeklyReportService
        return WeeklyReportService.key("unbound", at, timezone).week_key


class WeeklyReportSourceSelector:
    def select(self, timeline, measurements, facts):
        return {"timeline": list(timeline), "measurements": list(measurements), "facts": list(facts), "source_precedence": ["DOCUMENTED", "MEASURED", "REPORTED", "ESTIMATED"]}


class WeeklySectionBuilder:
    def __init__(self, section_type): self.section_type = section_type
    def build(self, evidence_bundle):
        state = "EVIDENCE_AVAILABLE" if evidence_bundle else "NOT_ENOUGH_DATA"
        return {"section_type": self.section_type, "state": state, "source_references": [asdict(x) if hasattr(x, "__dataclass_fields__") else x for x in evidence_bundle]}


class WeeklyReportRepository:
    def __init__(self): self.items = {}
    def save(self, report): self.items[report.id] = report; return report
    def get(self, report_id): return self.items.get(report_id)


class EmailGateway:
    def __init__(self): self.deliveries = set()
    def send(self, delivery_key, address, safe_summary):
        if delivery_key in self.deliveries: return {"status": "DUPLICATE_SUPPRESSED"}
        self.deliveries.add(delivery_key); return {"status": "QUEUED", "address": address, "summary": safe_summary}


@dataclass(frozen=True)
class SourceReference:
    source_type: str
    source_id: str
    source_version: str = "1.0.0"


@dataclass
class WeeklyReportPreferences:
    user_id: str
    enabled: bool = True
    timezone: str = "UTC"
    email_enabled: bool = False


@dataclass
class WeeklyReportNarrationV1:
    overall_summary: str
    section_narratives: dict[str, str]
    claim_sources: list[SourceReference] = field(default_factory=list)
    schema_version: str = "1.0.0"


class NarrationValidationError(ValueError):
    pass


class WeeklyReportNarrationValidator:
    """Safety boundary for optional prose; deterministic report data stays authoritative."""

    FORBIDDEN_TERMS = ("diagnosis", "diagnose", "prognosis", "prescription", "guaranteed recovery", "cure")
    URGENCY_TERMS = ("urgent", "promptly", "veterinary", "emergency", "immediately")

    @classmethod
    def validate(cls, narration: WeeklyReportNarrationV1, report) -> dict[str, object]:
        if narration.schema_version != "1.0.0":
            raise NarrationValidationError("WEEKLY_REPORT_NARRATION_SCHEMA_UNSUPPORTED")
        text = " ".join([narration.overall_summary, *narration.section_narratives.values()]).lower()
        forbidden = [term for term in cls.FORBIDDEN_TERMS if term in text]
        report_source_ids = {str(item.get("source_entity_id")) for item in report.source_references}
        unknown_sources = [ref.source_id for ref in narration.claim_sources if ref.source_id not in report_source_ids]
        required_urgency = bool(report.safety_guidance) or any(
            str(section.get("state", "")).upper() == "URGENT" for section in report.sections
        )
        urgency_preserved = not required_urgency or any(term in text for term in cls.URGENCY_TERMS)
        result = {
            "valid": not forbidden and not unknown_sources and urgency_preserved,
            "forbidden_terms": forbidden,
            "unknown_sources": unknown_sources,
            "urgency_preserved": urgency_preserved,
        }
        if not result["valid"]:
            raise NarrationValidationError("WEEKLY_REPORT_NARRATION_UNSAFE")
        return result


class WeeklyReportDispatcher:
    def __init__(self, generator):
        self.generator, self.idempotency, self.lock = generator, set(), RLock()
    def dispatch(self, owner, pet_id, week_key, *, idempotency_key):
        if not owner or not pet_id or not week_key or not idempotency_key:
            raise ValueError("WEEKLY_REPORT_DISPATCH_IDENTITY_REQUIRED")
        with self.lock:
            if idempotency_key in self.idempotency:
                return {"status": "DUPLICATE_SUPPRESSED", "idempotency_key": idempotency_key}
            report = self.generator(owner, pet_id, week_key)
            self.idempotency.add(idempotency_key)
            return {"status": "DISPATCHED", "report": report, "idempotency_key": idempotency_key}


class WeeklyReportReconciler:
    def reconcile(self, report, source_ids):
        known = {str(x.get("source_entity_id")) for x in report.source_references}
        missing = [x for x in source_ids if str(x) not in known]
        return {"report_id": report.id, "missing_sources": missing, "complete": not missing, "reconciled_at": datetime.now(UTC).isoformat()}
