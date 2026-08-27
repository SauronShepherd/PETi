# mypy: ignore-errors
from datetime import UTC, datetime
from threading import RLock

from app.domain.species import SpeciesCapabilityPack, SpeciesRegistryEntry
from app.domain.users import User, UserRole


class InMemoryUserRepository:
    def __init__(self):
        self.by_uid: dict[str, User] = {}
        self.lock = RLock()
        self.counter = 0

    def get_or_create(self, firebase_uid: str) -> User:
        with self.lock:
            if firebase_uid in self.by_uid:
                user = self.by_uid[firebase_uid]
                if user.deleted_at is not None:
                    raise ValueError("ACCOUNT_DELETED")
                return user
            self.counter += 1
            now = datetime.now(UTC)
            user = User(f"user-{self.counter}", firebase_uid, created_at=now, updated_at=now)
            self.by_uid[firebase_uid] = user
            return user

    def tombstone(self, firebase_uid: str) -> None:
        with self.lock:
            user = self.by_uid.get(firebase_uid) or next(
                (item for item in self.by_uid.values() if item.id == firebase_uid), None
            )
            if user:
                user.deleted_at = datetime.now(UTC)
                user.updated_at = user.deleted_at

    def provision(self, firebase_uid: str, role: UserRole, persona: str | None = None) -> User:
        user = self.get_or_create(firebase_uid)
        user.role = role
        user.internal_persona_code = persona
        user.billing_exempt = role in (UserRole.INTERNAL_TEST, UserRole.ADMIN)
        user.ads_exempt = user.billing_exempt
        user.updated_at = datetime.now(UTC)
        return user


class InMemorySpeciesRepository:
    def __init__(self):
        self.entries = {
            "DOG": SpeciesRegistryEntry("DOG", "Dog", True, True, "DOG-v1"),
        }
        self.packs = {
            "DOG": SpeciesCapabilityPack(
                "DOG",
                "DOG-v1",
                True,
                supported_analysis_types=("PLATFORM_MULTIMODAL_SMOKE", "PETI_CHECK", "DOG_INITIAL_SCAN", "DOG_DENTAL_CHECK", "DOG_FECES_CHECK", "DOG_BODY_CHECK"),
                enabled_analysis_types=("PLATFORM_MULTIMODAL_SMOKE", "PETI_CHECK", "DOG_INITIAL_SCAN", "DOG_DENTAL_CHECK", "DOG_FECES_CHECK", "DOG_BODY_CHECK"),
                safety_policy_version="PETI_CHECK-SAFETY-v1",
                public_enabled=True,
            ),
        }

    def list_public_profile_species(self):
        return [x for x in self.entries.values() if x.profile_enabled and x.public_enabled]

    def get_species(self, code):
        return self.entries.get(code.upper())

    def get_capability_pack(self, code):
        return self.packs.get(code.upper())


class InMemoryAnimalRepository:
    def __init__(self):
        self.items = {}
        self.lock = RLock()

    def create(self, pet):
        with self.lock:
            self.items[pet.id] = pet
        return pet

    def list_owned(self, owner):
        return [p for p in self.items.values() if p.owner_user_id == owner and p.deleted_at is None]

    def get_owned(self, owner, pet_id):
        p = self.items.get(pet_id)
        return p if p and p.owner_user_id == owner and p.deleted_at is None else None
