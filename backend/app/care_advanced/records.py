from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class CarePlan:
    owner_user_id: str; animal_id: str; title: str; category: str; id: str = field(default_factory=lambda: str(uuid4())); status: str = "ACTIVE"; source: str = "OWNER_ENTERED"


@dataclass
class VaccinationRecord:
    owner_user_id: str; animal_id: str; name: str; administered_on: str | None = None; id: str = field(default_factory=lambda: str(uuid4())); source: str = "OWNER_ENTERED"


@dataclass
class MedicationRecord:
    owner_user_id: str; animal_id: str; name: str; strength: str | None = None; documented_dose: str | None = None; status: str = "ACTIVE"; id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class MedicationSchedule:
    medication_record_id: str; schedule_type: str; instructions: str; id: str = field(default_factory=lambda: str(uuid4())); timezone: str = "UTC"


@dataclass
class MedicationOccurrence:
    medication_schedule_id: str; due_at: datetime; status: str = "DUE"; id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class AppointmentRecord:
    owner_user_id: str; animal_id: str; appointment_type: str; scheduled_at: datetime | None = None; id: str = field(default_factory=lambda: str(uuid4())); status: str = "PLANNED"


@dataclass
class FollowUpItem:
    owner_user_id: str; animal_id: str; title: str; due_on: str | None = None; id: str = field(default_factory=lambda: str(uuid4())); status: str = "OPEN"


@dataclass
class ObservationJournalEntry:
    owner_user_id: str; animal_id: str; text: str; category: str = "GENERAL"; id: str = field(default_factory=lambda: str(uuid4())); created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class LongitudinalBundle:
    owner_user_id: str; animal_id: str; source_ids: list[str]; change_summary: list[str]; id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class VisitPreparation:
    owner_user_id: str; animal_id: str; questions: list[str]; source_ids: list[str]; id: str = field(default_factory=lambda: str(uuid4()))
