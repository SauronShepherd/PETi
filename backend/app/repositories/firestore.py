"""Firestore adapters. Imports are lazy so LOCAL_TEST remains dependency-free at runtime."""

from datetime import UTC, datetime
from threading import Lock
from typing import Any

from app.domain.animals import ActiveState, AnimalProfile
from app.domain.users import User, UserRole


def _where(query: Any, field: str, value: Any) -> Any:
    from google.cloud.firestore_v1.base_query import FieldFilter  # type: ignore[import-untyped]

    try:
        return query.where(filter=FieldFilter(field, "==", value))
    except TypeError:
        return query.where(field, "==", value)


class FirestoreUserRepository:
    def __init__(self, client: Any):
        self.client = client

    def _ref(self, firebase_uid: str) -> Any:
        return self.client.collection("users").document(firebase_uid)

    def get_or_create(self, firebase_uid: str) -> User:
        ref = self._ref(firebase_uid)
        if hasattr(self.client, "transaction"):
            from google.cloud.firestore_v1.transaction import (
                transactional,  # type: ignore[import-untyped]
            )

            now = datetime.now(UTC)
            transaction = self.client.transaction()

            @transactional
            def get_or_create_transaction(tx):
                snapshot = tx.get(ref)
                # google-cloud-firestore versions differ here: older clients
                # return a snapshot, while newer clients return an iterator of
                # snapshots for transaction reads.
                if not hasattr(snapshot, "exists"):
                    snapshot = next(iter(snapshot), None)
                if snapshot is None:
                    raise RuntimeError("FIRESTORE_TRANSACTION_READ_EMPTY")
                if snapshot.exists:
                    data = snapshot.to_dict()
                    if data.get("deleted_at") is not None:
                        raise ValueError("ACCOUNT_DELETED")
                    return data
                data = {
                    "id": firebase_uid,
                    "firebase_uid": firebase_uid,
                    "role": UserRole.CUSTOMER.value,
                    "billing_exempt": False,
                    "ads_exempt": False,
                    "internal_persona_code": None,
                    "created_at": now,
                    "updated_at": now,
                    "deleted_at": None,
                }
                tx.create(ref, data)
                return data

            data = get_or_create_transaction(transaction)
            data["role"] = UserRole(data["role"])
            return User(**data)
        snapshot = ref.get()
        if snapshot.exists:
            data = snapshot.to_dict()
            if data.get("deleted_at") is not None:
                raise ValueError("ACCOUNT_DELETED")
            data["role"] = UserRole(data["role"])
            return User(**data)
        now = datetime.now(UTC)
        user = User(firebase_uid, firebase_uid, created_at=now, updated_at=now)
        data = {
                "id": user.id,
                "firebase_uid": firebase_uid,
                "role": user.role.value,
                "billing_exempt": False,
                "ads_exempt": False,
                "internal_persona_code": None,
                "created_at": now,
                "updated_at": now,
                "deleted_at": None,
            }
        try:
            ref.create(data)
            return user
        except Exception as exc:
            # A concurrent creator may win between get() and create(). Read
            # back only when the adapter exposes the usual AlreadyExists error.
            if exc.__class__.__name__ != "AlreadyExists":
                raise
            existing = ref.get()
            if not existing.exists:
                raise
            existing_data = existing.to_dict()
            existing_data["role"] = UserRole(existing_data["role"])
            return User(**existing_data)

    def tombstone(self, firebase_uid: str) -> None:
        ref = self._ref(firebase_uid)
        snapshot = ref.get()
        if snapshot.exists:
            now = datetime.now(UTC)
            ref.update({"deleted_at": now, "updated_at": now})

    def provision(self, firebase_uid: str, role: UserRole, persona: str | None = None) -> User:
        """Idempotently apply an operator-assigned role to a real Firestore user."""
        user = self.get_or_create(firebase_uid)
        now = datetime.now(UTC)
        updates = {
            "role": role.value,
            "internal_persona_code": persona,
            "billing_exempt": role in (UserRole.INTERNAL_TEST, UserRole.ADMIN),
            "ads_exempt": role in (UserRole.INTERNAL_TEST, UserRole.ADMIN),
            "updated_at": now,
        }
        self._ref(firebase_uid).update(updates)
        for key, value in updates.items():
            setattr(user, key, value)
        return user


class FirestoreAnimalRepository:
    def __init__(self, client: Any):
        self.client = client
        self.lock = Lock()

    def create(self, pet: AnimalProfile) -> AnimalProfile:
        self.client.collection("animals").document(pet.id).create(
            {
                "id": pet.id,
                "owner_user_id": pet.owner_user_id,
                "species": pet.species,
                "display_name": pet.display_name,
                "avatar_media_id": pet.avatar_media_id,
                "coat_color": pet.coat_color,
                "coat_pattern": pet.coat_pattern,
                "coat_length": pet.coat_length,
                "possible_breed_type": pet.possible_breed_type,
                "life_stage_appearance": pet.life_stage_appearance,
                "morphology_description": pet.morphology_description,
                "distinguishing_features": pet.distinguishing_features,
                "profile_field_provenance": pet.profile_field_provenance,
                "active_state": pet.active_state.value,
                "created_at": pet.created_at,
                "updated_at": pet.updated_at,
                "deleted_at": pet.deleted_at,
            }
        )
        return pet

    def list_owned(self, owner: str) -> list[AnimalProfile]:
        return [
            self._from(x.to_dict())
            for x in _where(_where(self.client.collection("animals"), "owner_user_id", owner), "deleted_at", None).stream()
        ]

    def get_owned(self, owner: str, pet_id: str) -> AnimalProfile | None:
        snapshot = self.client.collection("animals").document(pet_id).get()
        if not snapshot.exists:
            return None
        pet = self._from(snapshot.to_dict())
        return pet if pet.owner_user_id == owner and pet.deleted_at is None else None

    def update(self, pet: AnimalProfile) -> AnimalProfile:
        self.client.collection("animals").document(pet.id).set(
            {
                "id": pet.id,
                "owner_user_id": pet.owner_user_id,
                "species": pet.species,
                "display_name": pet.display_name,
                "avatar_media_id": pet.avatar_media_id,
                "coat_color": pet.coat_color,
                "coat_pattern": pet.coat_pattern,
                "coat_length": pet.coat_length,
                "possible_breed_type": pet.possible_breed_type,
                "life_stage_appearance": pet.life_stage_appearance,
                "morphology_description": pet.morphology_description,
                "distinguishing_features": pet.distinguishing_features,
                "profile_field_provenance": pet.profile_field_provenance,
                "active_state": pet.active_state.value,
                "created_at": pet.created_at,
                "updated_at": pet.updated_at,
                "deleted_at": pet.deleted_at,
            }
        )
        return pet

    @staticmethod
    def _from(data: dict[str, Any]) -> AnimalProfile:
        data["active_state"] = ActiveState(data["active_state"])
        return AnimalProfile(**data)
