from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256


@dataclass
class StoredObject:
    bucket: str
    name: str
    content: bytes
    content_type: str
    created_at: datetime


class FakeObjectStorage:
    def __init__(self, bucket="local-media"):
        self.bucket = bucket
        self.objects = {}

    def create_upload_authorization(self, bucket, name, content_type, expires_seconds=900):
        return {
            "upload_url": f"fake://{bucket}/{name}",
            "required_headers": {"Content-Type": content_type},
            "expires_at": (datetime.now(UTC) + timedelta(seconds=expires_seconds)).isoformat(),
        }

    def put(self, bucket, name, content, content_type):
        self.objects[(bucket, name)] = StoredObject(
            bucket, name, content, content_type, datetime.now(UTC)
        )

    def stat_object(self, bucket, name):
        return self.objects.get((bucket, name))

    def read_object(self, bucket, name, max_bytes=10 * 1024 * 1024):
        obj = self.stat_object(bucket, name)
        if obj is None:
            return None
        if len(obj.content) > max_bytes:
            raise ValueError("MEDIA_OBJECT_TOO_LARGE")
        return obj.content

    def delete_object(self, bucket, name):
        self.objects.pop((bucket, name), None)

    def create_read_authorization(self, bucket, name, expires_seconds=300):
        if not self.stat_object(bucket, name):
            return None
        return {
            "read_url": f"fake://read/{bucket}/{name}",
            "expires_at": (datetime.now(UTC) + timedelta(seconds=expires_seconds)).isoformat(),
        }


def object_checksum(obj: StoredObject):
    return sha256(obj.content).hexdigest()
