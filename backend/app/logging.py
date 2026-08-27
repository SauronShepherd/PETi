import logging
import re
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json

        message = record.getMessage()
        # Logs are metadata-only. Prevent accidental credentials/raw JSON from
        # escaping even if a future call site interpolates an exception string.
        api_key_pattern = r"AI" + r"za[0-9A-Za-z_-]{20,}"
        message = re.sub(api_key_pattern, "[REDACTED_KEY]", message)
        message = re.sub(r"-----BEGIN [^-]+ PRIVATE KEY-----.*?-----END [^-]+ PRIVATE KEY-----", "[REDACTED_KEY]", message, flags=re.DOTALL)
        message = re.sub(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED_TOKEN]", message)
        message = re.sub(r"https?://[^\s]+[?&](?:X-Goog-Signature|GoogleAccessId|Signature)=[^\s&]+[^\s]*", "[REDACTED_SIGNED_URL]", message)
        if message.lstrip().startswith(("{", "[")):
            message = "[REDACTED_STRUCTURED_PAYLOAD]"

        fields = getattr(record, "peti_fields", {})
        safe = safe_fields(**fields)
        safe = {key: _redact_field(key, value) for key, value in safe.items()}
        return json.dumps(
            {
                "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
                "service": "peti-api",
                "level": record.levelname,
                "message": message,
                **safe,
            }
        )


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def safe_fields(**fields: Any) -> dict[str, Any]:
    allowed = {
        "environment",
        "correlation_id",
        "operation",
        "status",
        "duration_ms",
        "analysis_id",
        "media_id",
        "operation_type",
        "purchase_token",
        "fcm_token",
        "device_token",
        "firebase_token",
        "signed_url",
    }
    return {key: value for key, value in fields.items() if key in allowed}


def _redact_field(key: str, value: Any) -> Any:
    if key.lower() in {"purchase_token", "fcm_token", "device_token", "firebase_token", "signed_url"}:
        return "[REDACTED_SENSITIVE_FIELD]"
    return value


@asynccontextmanager
async def timed_operation(
    logger: logging.Logger, operation: str, **fields: Any
) -> AsyncIterator[None]:
    started = time.perf_counter()
    try:
        yield
    finally:
        logger.info(
            "operation_complete",
            extra={
                "peti_fields": safe_fields(
                    operation=operation,
                    status="complete",
                    duration_ms=round((time.perf_counter() - started) * 1000, 2),
                    **fields,
                )
            },
        )
