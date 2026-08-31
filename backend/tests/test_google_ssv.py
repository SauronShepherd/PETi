import base64

import pytest
from app.advertising.google_ssv_verifier import GoogleSsvVerifier


def test_unknown_google_key_fails_closed():
    verifier = GoogleSsvVerifier(list)
    with pytest.raises(ValueError, match="REWARD_VERIFICATION_KEY_UNKNOWN"):
        verifier.verify("user_id=u&transaction_id=t&signature=abc&key_id=unknown")


def test_google_ssv_accepts_valid_signed_query():
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    private_key = ec.generate_private_key(ec.SECP256R1())

    signed = b"user_id=user-1&transaction_id=tx-1&reward_amount=1"
    signature = private_key.sign(signed, ec.ECDSA(hashes.SHA256()))
    query = signed.decode() + "&signature=" + base64.urlsafe_b64encode(signature).decode().rstrip("=") + "&key_id=key-1"

    verifier = GoogleSsvVerifier(
        lambda: [{"keyId": "key-1", "base64": base64.b64encode(private_key.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)).decode()}]
    )

    assert verifier.verify(query) == {
        "user_id": "user-1", "transaction_id": "tx-1", "reward_amount": "1"
    }
