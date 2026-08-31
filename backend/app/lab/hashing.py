import hashlib
import hmac
from collections.abc import Mapping


def owner_hash(owner_user_id: str, secret: str, *, key_id: str | None = None) -> str:
    if not owner_user_id or not secret:
        raise ValueError("LAB_HASH_INPUT_INVALID")
    digest = hmac.new(secret.encode(), owner_user_id.encode(), hashlib.sha256).hexdigest()
    return f"{key_id}:{digest}" if key_id else digest


def owner_hash_matches(
    owner_user_id: str,
    stored_hash: str,
    keys: Mapping[str, str],
    *,
    legacy_secret: str | None = None,
) -> bool:
    """Verify pseudonyms while active and previous HMAC keys overlap."""
    if ":" in stored_hash:
        key_id, _ = stored_hash.split(":", 1)
        secret = keys.get(key_id)
        if not secret:
            return False
        return hmac.compare_digest(
            stored_hash, owner_hash(owner_user_id, secret, key_id=key_id)
        )
    if not legacy_secret:
        return False
    return hmac.compare_digest(stored_hash, owner_hash(owner_user_id, legacy_secret))


def feedback_id(owner_user_id: str, response_id: str) -> str:
    if not owner_user_id or not response_id:
        raise ValueError("LAB_FEEDBACK_ID_INPUT_INVALID")
    return hashlib.sha256(f"{owner_user_id}:{response_id}".encode()).hexdigest()[:40]
