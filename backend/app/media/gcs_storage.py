"""Production GCS adapter. Credentials come from ADC/service identity only."""

from datetime import timedelta
from hashlib import sha256
from typing import Any


class GcsObjectStorage:
    def __init__(self, client: Any, bucket_name: str):
        if not bucket_name:
            raise ValueError("MEDIA_BUCKET_REQUIRED")
        self.client = client
        self.bucket_name = bucket_name

    def create_upload_authorization(self, bucket, name, content_type, expires_seconds=900):
        blob = self.client.bucket(bucket or self.bucket_name).blob(name)
        return {
            "upload_url": blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expires_seconds),
                method="PUT",
                content_type=content_type,
            ),
            "required_headers": {"Content-Type": content_type},
        }

    def stat_object(self, bucket, name):
        blob = self.client.bucket(bucket or self.bucket_name).blob(name)
        blob.reload()
        return blob

    def read_object(self, bucket, name, max_bytes=10 * 1024 * 1024):
        blob = self.client.bucket(bucket or self.bucket_name).blob(name)
        try:
            blob.reload()
        except Exception:  # noqa: BLE001
            return None
        if blob.size is not None and blob.size > max_bytes:
            raise ValueError("MEDIA_OBJECT_TOO_LARGE")
        return blob.download_as_bytes()

    @staticmethod
    def checksum_object(blob):
        """Compute the declared SHA-256 over the canonical GCS bytes."""
        return sha256(blob.download_as_bytes()).hexdigest()

    def delete_object(self, bucket, name):
        self.client.bucket(bucket or self.bucket_name).blob(name).delete()

    def create_read_authorization(self, bucket, name, expires_seconds=300):
        blob = self.client.bucket(bucket or self.bucket_name).blob(name)
        try:
            blob.reload()
        except Exception:  # noqa: BLE001
            return None
        return {
            "read_url": blob.generate_signed_url(
                version="v4", expiration=timedelta(seconds=expires_seconds), method="GET"
            )
        }
