"""Google rewarded-ad server-side verification with fail-closed key handling."""

import base64
import json
from urllib.parse import parse_qsl
from urllib.request import urlopen

GOOGLE_KEYS_URL = "https://www.gstatic.com/admob/reward/verifier-keys.json"


class GoogleSsvVerifier:
    def __init__(self, key_loader=None):
        self.key_loader = key_loader or self._load_keys

    @staticmethod
    def _load_keys():
        with urlopen(GOOGLE_KEYS_URL, timeout=5) as response:
            return json.load(response)["keys"]

    def verify(self, query: str) -> dict[str, str]:
        # AdMob signs the exact ordered query prefix. Never parse and
        # re-encode the signed content: escaping, duplicate keys and order are
        # all part of the signed bytes.
        marker = "&signature="
        if marker not in query:
            raise ValueError("REWARD_VERIFICATION_FAILED")
        signed_query, tail = query.split(marker, 1)
        if "&key_id=" not in tail:
            raise ValueError("REWARD_VERIFICATION_FAILED")
        signature, key_tail = tail.split("&key_id=", 1)
        if not signature or not key_tail or "&" in key_tail:
            raise ValueError("REWARD_VERIFICATION_FAILED")
        values = dict(parse_qsl(signed_query, keep_blank_values=True))
        key_id = key_tail
        if not values:
            raise ValueError("REWARD_VERIFICATION_FAILED")
        key = next((x for x in self.key_loader() if str(x.get("keyId")) == key_id), None)
        if not key:
            raise ValueError("REWARD_VERIFICATION_KEY_UNKNOWN")
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives.serialization import (
            load_der_public_key,
            load_pem_public_key,
        )
        key_bytes = base64.b64decode(key["base64"]) if key.get("base64") else key.get("pem", "").encode()
        public_key = (load_pem_public_key(key_bytes) if key.get("pem") else load_der_public_key(key_bytes))
        try:
            verifier_args = (base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4)), signed_query.encode(), ec.ECDSA(hashes.SHA256()))
            if isinstance(public_key, ec.EllipticCurvePublicKey):
                public_key.verify(*verifier_args)
            else:
                raise ValueError("REWARD_VERIFICATION_KEY_ALGORITHM_UNSUPPORTED")  # noqa: TRY004
        except Exception as exc:
            raise ValueError("REWARD_VERIFICATION_FAILED") from exc
        return values
