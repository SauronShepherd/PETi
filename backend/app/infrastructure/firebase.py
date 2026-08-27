"""Application-scoped Firebase Admin factories; credentials come from ADC/IAM only."""

from typing import Any


def create_firebase_auth(project_id: str | None) -> Any:
    import firebase_admin
    from firebase_admin import auth, credentials

    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            credentials.ApplicationDefault(), {"projectId": project_id} if project_id else {}
        )
    return auth


def create_firebase_services(project_id: str | None, database_id: str | None) -> tuple[Any, Any]:
    from firebase_admin import firestore

    firebase_auth = create_firebase_auth(project_id)
    return firebase_auth, firestore.client(
        database_id=database_id
    ) if database_id else firestore.client()
