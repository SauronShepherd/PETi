import base64
from urllib.parse import urlencode

import pytest
from app.advertising.google_ssv_verifier import GoogleSsvVerifier


def test_unknown_google_key_fails_closed():
    verifier = GoogleSsvVerifier(list)
    with pytest.raises(ValueError, match="REWARD_VERIFICATION_KEY_UNKNOWN"):
        verifier.verify("user_id=u&transaction_id=t&signature=abc&key_id=unknown")


def test_google_ssv_accepts_valid_signed_query():
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_numbers = private_key.public_key().public_numbers()

    def encode_int(value: int) -> str:
        raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    values = {
        "user_id": "user-1",
        "transaction_id": "tx-1",
        "reward_amount": "1",
        "key_id": "key-1",
    }
    signed = urlencode({key: value for key, value in values.items() if key != "key_id"}).encode()
    signature = private_key.sign(signed, padding.PKCS1v15(), hashes.SHA256())
    query = urlencode({**values, "signature": base64.b64encode(signature).decode()})

    verifier = GoogleSsvVerifier(
        lambda: [{"keyId": "key-1", "n": encode_int(public_numbers.n), "e": encode_int(public_numbers.e)}]
    )

    assert verifier.verify(query) == {
        key: value for key, value in values.items() if key != "key_id"
    }
