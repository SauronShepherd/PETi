"""Trusted operator-only role provisioning tool; never exposed as a customer route.

By default this targets Firestore. Use ``--local`` only for a disposable local
fixture; it must never be used as evidence of production provisioning.
"""
import argparse
from app.domain.users import UserRole
from app.repositories.memory import InMemoryUserRepository

def validate_inputs(firebase_uid: str, role: UserRole, persona: str | None) -> None:
    if not firebase_uid.strip():
        raise ValueError("firebase_uid must not be empty")
    if persona is not None and role not in (UserRole.INTERNAL_TEST, UserRole.ADMIN):
        raise ValueError("internal_persona_code is only valid for internal roles")
    if persona is not None and not persona.strip():
        raise ValueError("internal_persona_code must not be empty")


def build_repository(local: bool, project: str | None):
    if local:
        return InMemoryUserRepository()
    from google.cloud import firestore
    from app.repositories.firestore import FirestoreUserRepository

    return FirestoreUserRepository(firestore.Client(project=project) if project else firestore.Client())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--firebase-uid", required=True)
    parser.add_argument("--role", choices=[x.value for x in UserRole], required=True)
    parser.add_argument("--internal-persona-code")
    parser.add_argument("--project", help="GCP project; defaults to ADC project resolution")
    parser.add_argument("--local", action="store_true", help="Use an ephemeral in-memory fixture")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without writing")
    args = parser.parse_args()
    role = UserRole(args.role)
    try:
        validate_inputs(args.firebase_uid, role, args.internal_persona_code)
    except ValueError as exc:
        parser.error(str(exc))
    if args.dry_run:
        print(f"would provision firebase_uid={args.firebase_uid} role={role.value}")
        return
    user = build_repository(args.local, args.project).provision(
        args.firebase_uid, role, args.internal_persona_code
    )
    print(f"provisioned {user.id} role={user.role.value}")

if __name__ == "__main__": main()
