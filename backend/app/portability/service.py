import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from threading import RLock
from typing import Any
from uuid import uuid4


@dataclass
class ShareGrant:
    owner_user_id: str
    pet_id: str
    scope: str
    expires_at: datetime
    id: str | None = None
    token_digest: str = ""
    revoked_at: datetime | None = None


class PortabilityService:
    def __init__(self, data_provider, store: Any | None = None, clock=None):
        self.data_provider, self.store = data_provider, store
        self.clock = clock or (lambda: datetime.now(UTC))
        self.exports: dict[str, dict] = {}
        self.shares: dict[str, ShareGrant] = {}
        self.lock = RLock()
        self._hydrate()

    def _hydrate(self) -> None:
        if not self.store or not hasattr(self.store, "all"):
            return
        try:
            rows = self.store.all("portability_share_grants")
        except Exception:  # noqa: BLE001 - invalid grants must not authorize sharing
            rows = []
        for row in rows:
            try:
                data = dict(row)
                for key in ("expires_at", "revoked_at"):
                    value = data.get(key)
                    if value is not None and not isinstance(value, datetime):
                        data[key] = datetime.fromisoformat(str(value))
                grant = ShareGrant(**{key: data[key] for key in ShareGrant.__dataclass_fields__ if key in data})
                if grant.id:
                    self.shares[grant.id] = grant
            except (KeyError, TypeError, ValueError):
                continue

    def _save(self, grant: ShareGrant) -> None:
        if self.store and hasattr(self.store, "put"):
            self.store.put("portability_share_grants", grant)

    def export(self, owner: str, pet_id: str, include_raw_media: bool = False) -> dict:
        if not isinstance(include_raw_media, bool):
            raise TypeError("EXPORT_RAW_MEDIA_FLAG_INVALID")
        data = self.data_provider(owner, pet_id)
        digest = self._package_digest(pet_id, data, include_raw_media)
        return {"manifest": {"schema": "PETI_PORTABLE_PACKAGE", "version": "1.0.0", "generated_at": self.clock().isoformat(), "raw_media_included": include_raw_media, "content_sha256": digest}, "pet_id": pet_id, "sections": data, "billing": None}

    @staticmethod
    def _package_digest(pet_id: str, sections: dict, include_raw_media: bool) -> str:
        canonical = json.dumps(
            {"pet_id": pet_id, "sections": sections, "raw_media_included": include_raw_media},
            sort_keys=True, separators=(",", ":"), default=str,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()

    def create_share(self, owner: str, pet_id: str, scope: str = "READ_ONLY", ttl_hours: int = 24) -> dict:
        with self.lock:
            return self._create_share(owner, pet_id, scope, ttl_hours)

    def _create_share(self, owner: str, pet_id: str, scope: str = "READ_ONLY", ttl_hours: int = 24) -> dict:
        if scope not in {"READ_ONLY", "VISIT_PACKET"} or isinstance(ttl_hours, bool) or not isinstance(ttl_hours, int) or not 1 <= ttl_hours <= 168: raise ValueError("SHARE_POLICY_INVALID")
        token = token_urlsafe(32)
        token_digest = hashlib.sha256(token.encode()).hexdigest()
        grant = ShareGrant(owner, pet_id, scope, self.clock() + timedelta(hours=ttl_hours), str(uuid4()), token_digest=token_digest)
        assert grant.id is not None
        self.shares[grant.id] = grant
        self._save(grant)
        return {"share_id": grant.id, "token": token, "expires_at": grant.expires_at.isoformat(), "scope": scope}

    def revoke(self, owner: str, share_id: str):
        with self.lock:
            return self._revoke(owner, share_id)

    def _revoke(self, owner: str, share_id: str):
        grant = self.shares.get(share_id)
        if not grant or grant.owner_user_id != owner: raise ValueError("SHARE_NOT_FOUND")
        grant.revoked_at = self.clock()
        self._save(grant)
        public = asdict(grant)
        public.pop("token_digest", None)
        return public

    def resolve_share(self, share_id: str, token: str) -> ShareGrant:
        with self.lock:
            return self._resolve_share(share_id, token)

    def _resolve_share(self, share_id: str, token: str) -> ShareGrant:
        if not isinstance(share_id, str) or not isinstance(token, str):
            raise ValueError("SHARE_NOT_FOUND")  # noqa: TRY004 - conceal malformed credentials
        grant = self.shares.get(share_id)
        if not grant or grant.revoked_at or grant.expires_at <= self.clock():
            raise ValueError("SHARE_NOT_FOUND")
        if hashlib.sha256(token.encode()).hexdigest() != grant.token_digest:
            raise ValueError("SHARE_NOT_FOUND")
        return grant

    def import_preview(self, owner: str, package: dict) -> dict:
        if not isinstance(package, dict):
            raise ValueError("IMPORT_SCHEMA_UNSUPPORTED")  # noqa: TRY004 - public import error contract
        if not isinstance(package.get("manifest"), dict) or package["manifest"].get("schema") != "PETI_PORTABLE_PACKAGE": raise ValueError("IMPORT_SCHEMA_UNSUPPORTED")
        manifest = package.get("manifest", {})
        raw_media_included = manifest.get("raw_media_included", False)
        if not isinstance(raw_media_included, bool):
            raise ValueError("IMPORT_INTEGRITY_INVALID")  # noqa: TRY004 - public import error contract
        if not isinstance(package.get("pet_id"), str) or not isinstance(package.get("sections"), dict):
            raise ValueError("IMPORT_INTEGRITY_INVALID")  # noqa: TRY004 - public import error contract
        expected = manifest.get("content_sha256")
        if expected:
            actual = self._package_digest(package.get("pet_id", ""), package.get("sections", {}), raw_media_included)
            if expected != actual:
                raise ValueError("IMPORT_INTEGRITY_INVALID")
        return {"import_id": str(uuid4()), "status": "PREVIEW_REQUIRED", "owner_user_id": owner, "duplicate_policy": "PRESERVE_AND_LINK", "sections": list(package.get("sections", {}).keys()) if isinstance(package.get("sections"), dict) else []}
