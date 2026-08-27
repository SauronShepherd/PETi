from datetime import timedelta
from typing import Any


class FlociObjectStorage:
    def __init__(self, client: Any, bucket_name: str = "peti-local-media"):
        self.client = client
        self.bucket_name = bucket_name
        bucket = client.bucket(bucket_name)
        if not bucket.exists():
            client.create_bucket(bucket)

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

    def put(self, bucket, name, content, content_type):
        blob = self.client.bucket(bucket or self.bucket_name).blob(name)
        blob.upload_from_string(content, content_type=content_type)

    def stat_object(self, bucket, name):
        blob = self.client.bucket(bucket or self.bucket_name).blob(name)
        try:
            blob.reload()
        except Exception:  # noqa: BLE001
            return None
        return blob

    def delete_object(self, bucket, name):
        self.client.bucket(bucket or self.bucket_name).blob(name).delete()

    def create_read_authorization(self, bucket, name, expires_seconds=300):
        blob = self.stat_object(bucket, name)
        if not blob:
            return None
        return {
            "read_url": blob.generate_signed_url(
                version="v4", expiration=timedelta(seconds=expires_seconds), method="GET"
            )
        }
