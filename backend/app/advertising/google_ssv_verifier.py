"""Google rewarded-ad server-side verification with fail-closed key handling."""

import base64
import json
from urllib.parse import parse_qsl, urlencode
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
        pairs = parse_qsl(query, keep_blank_values=True)
        values = dict(pairs)
        signature = values.pop("signature", "")
        key_id = values.pop("key_id", "")
        if not signature or not key_id or not values:
            raise ValueError("REWARD_VERIFICATION_FAILED")
        key = next((x for x in self.key_loader() if str(x.get("keyId")) == key_id), None)
        if not key:
            raise ValueError("REWARD_VERIFICATION_KEY_UNKNOWN")
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding, rsa

        public_key = rsa.RSAPublicNumbers(
            e=int.from_bytes(base64.urlsafe_b64decode(key["e"] + "=="), "big"),
            n=int.from_bytes(base64.urlsafe_b64decode(key["n"] + "=="), "big"),
        ).public_key()
        signed = urlencode(values).encode()
        try:
            public_key.verify(
                base64.b64decode(signature), signed, padding.PKCS1v15(), hashes.SHA256()
            )
        except Exception as exc:
            raise ValueError("REWARD_VERIFICATION_FAILED") from exc
        return values
