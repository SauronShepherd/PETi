from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class ShareAuditEvent:
    share_id: str
    event_type: str
    actor_user_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ImportJob:
    owner_user_id: str
    source_format: str
    status: str = "PREVIEW_REQUIRED"
    id: str = ""


@dataclass
class ImportLedger:
    import_job_id: str
    source_item_id: str
    target_entity_id: str | None
    outcome: str


@dataclass
class PETiPortablePackageV1:
    manifest: dict
    pet_identity: dict
    sections: dict
    attachment_manifest: list[dict] = field(default_factory=list)

    def validate(self):
        if self.manifest.get("schema") != "PETI_PORTABLE_PACKAGE" or self.manifest.get("version") != "1.0.0": raise ValueError("PORTABLE_PACKAGE_VERSION_UNSUPPORTED")
        return self
