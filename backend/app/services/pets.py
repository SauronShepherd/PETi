# mypy: ignore-errors
import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from app.domain.animals import AnimalProfile


class PetService:
    def __init__(self, animals, species):
        self.animals = animals
        self.species = species
        self.idempotency = {}
        self.lock = animals.lock

    def create(self, owner, name, species, key):
        if not key:
            raise ValueError("IDEMPOTENCY_KEY_REQUIRED")
        name = name.strip()
        code = species.strip().upper()
        if not name:
            raise ValueError("INVALID_PET_NAME")
        entry = self.species.get_species(code)
        if not entry or not entry.profile_enabled or not entry.public_enabled:
            raise ValueError("SPECIES_NOT_AVAILABLE")
        fingerprint = hashlib.sha256(
            json.dumps({"display_name": name, "species": code}, sort_keys=True).encode()
        ).hexdigest()
        idem = (owner, key)
        with self.lock:
            if idem in self.idempotency:
                old_fp, pet_id = self.idempotency[idem]
                if old_fp != fingerprint:
                    raise ValueError("IDEMPOTENCY_KEY_REUSE_CONFLICT")
                existing = self.animals.get_owned(owner, pet_id)
                if existing:
                    return existing
            now = datetime.now(UTC)
            pet = AnimalProfile(uuid4().hex, owner, code, name, created_at=now, updated_at=now)
            self.animals.create(pet)
            self.idempotency[idem] = (fingerprint, pet.id)
            return pet

    def list(self, owner):
        return self.animals.list_owned(owner)

    def get(self, owner, pet_id):
        return self.animals.get_owned(owner, pet_id)

    def update(self, owner, pet_id, name):
        p = self.get(owner, pet_id)
        if not p:
            return None
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("INVALID_PET_NAME")
            p.display_name = name
        p.updated_at = datetime.now(UTC)
        if hasattr(self.animals, "update"):
            self.animals.update(p)
        return p

    def update_profile_fields(self, owner, pet_id, values: dict[str, str], provenance: str) -> AnimalProfile | None:
        """Apply only user-reviewed, allowlisted profile suggestions."""
        p = self.get(owner, pet_id)
        if not p:
            return None
        allowed = {
            "COAT_COLOR": "coat_color", "COAT_PATTERN": "coat_pattern", "COAT_LENGTH": "coat_length",
            "POSSIBLE_BREED_TYPE": "possible_breed_type", "LIFE_STAGE_APPEARANCE": "life_stage_appearance",
            "MORPHOLOGY_DESCRIPTION": "morphology_description", "DISTINGUISHING_FEATURES": "distinguishing_features",
        }
        for field_type, value in values.items():
            attribute = allowed.get(field_type)
            if attribute and str(value).strip():
                setattr(p, attribute, str(value).strip())
                p.profile_field_provenance[field_type] = provenance
        p.updated_at = datetime.now(UTC)
        if hasattr(self.animals, "update"):
            self.animals.update(p)
        return p

    def delete(self, owner, pet_id):
        p = self.get(owner, pet_id)
        if not p:
            return False
        p.deleted_at = datetime.now(UTC)
        if hasattr(self.animals, "update"):
            self.animals.update(p)
        return True
