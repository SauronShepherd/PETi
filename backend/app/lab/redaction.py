from __future__ import annotations

from typing import Any

FORBIDDEN_PROPERTY_KEYS = frozenset({
    "email", "pet_name", "user_name", "prompt", "goal", "response", "comment",
    "content", "url", "token", "base64", "bytes", "media", "question", "answer",
})


def validate_event_properties(properties: dict[str, Any], allowed: frozenset[str]) -> dict[str, Any]:
    unknown = set(properties) - allowed
    forbidden = {key for key in properties if key.lower() in FORBIDDEN_PROPERTY_KEYS}
    if unknown or forbidden: raise ValueError("LAB_EVENT_PROPERTIES_NOT_ALLOWED")
    result: dict[str, Any] = {}
    for key, value in properties.items():
        if value is None or isinstance(value, (bool, int, float)):
            result[key] = value
        elif isinstance(value, str):
            if len(value) > 128 or any(marker in value.lower() for marker in ("http://", "https://", "@gmail", "bearer ")):
                raise ValueError("LAB_EVENT_PROPERTY_VALUE_NOT_ALLOWED")
            result[key] = value
        elif isinstance(value, (list, tuple)) and len(value) <= 10 and all(isinstance(item, str) and len(item) <= 64 for item in value):
            result[key] = list(value)
        else:
            raise ValueError("LAB_EVENT_PROPERTY_VALUE_NOT_ALLOWED")
    return result
