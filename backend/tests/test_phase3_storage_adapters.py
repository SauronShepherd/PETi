from app.config.settings import Environment, Settings
from app.media.gcs_storage import GcsObjectStorage


def test_non_local_storage_fails_closed_without_bucket():
    try:
        Settings(
            environment=Environment.DEV, auth_mode="FIREBASE", storage_mode="MEMORY"
        ).validate_startup()
    except ValueError as exc:
        assert "MEDIA_BUCKET" in str(exc)


def test_gcs_adapter_scopes_signed_put_to_object_and_content_type():
    class Blob:
        def generate_signed_url(self, **kwargs):
            return "signed"

    class Bucket:
        def blob(self, name):
            assert name == "media/id/source"
            return Blob()

    class Client:
        def bucket(self, name):
            assert name == "bucket"
            return Bucket()

    result = GcsObjectStorage(Client(), "bucket").create_upload_authorization(
        "bucket", "media/id/source", "image/png"
    )
    assert (
        result["upload_url"] == "signed"
        and result["required_headers"]["Content-Type"] == "image/png"
    )
