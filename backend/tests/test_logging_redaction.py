import io
import json
import logging

from app.logging import JsonFormatter


def test_logging_redacts_sentinel_tokens_and_signed_urls():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("sentinel-redaction")
    logger.handlers = [handler]
    logger.propagate = False
    logger.warning("token eyJheader.payload.signature https://example.test/x?X-Goog-Signature=secret", extra={"peti_fields": {"operation": "x", "purchase_token": "purchase-secret"}})
    line = stream.getvalue()
    data = json.loads(line)
    assert "purchase-secret" not in line
    assert "eyJheader.payload.signature" not in line
    assert "X-Goog-Signature=secret" not in line
    assert data["purchase_token"] == "[REDACTED_SENSITIVE_FIELD]"


def test_logging_redacts_all_registered_sensitive_field_types():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("sensitive-fields-redaction")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.info(
        "notification and identity metadata",
        extra={
            "peti_fields": {
                "fcm_token": "fcm-secret",
                "device_token": "device-secret",
                "firebase_token": "firebase-secret",
                "signed_url": "https://signed.example/object",
            }
        },
    )
    line = stream.getvalue()
    data = json.loads(line)
    for key in ("fcm_token", "device_token", "firebase_token", "signed_url"):
        assert data[key] == "[REDACTED_SENSITIVE_FIELD]"
    assert all(secret not in line for secret in ("fcm-secret", "device-secret", "firebase-secret"))


def test_logging_keeps_only_safe_media_metadata():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("media-redaction")
    logger.handlers = [handler]
    logger.propagate = False
    logger.warning(
        "Authorization: Bearer secret-api-key bytes=YWJj",
        extra={"peti_fields": {
            "media_asset_id": "asset-1", "modality": "IMAGE", "media_size_bytes": 3,
            "media_sha256": "abc", "authorization": "Bearer secret",
            "inline_data": "YWJj",
        }},
    )
    line = stream.getvalue()
    assert "secret-api-key" not in line and "YWJj" not in line
    assert "asset-1" in line and "IMAGE" in line and "media_size_bytes" in line
