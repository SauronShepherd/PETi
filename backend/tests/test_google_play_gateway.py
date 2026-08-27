from app.billing.google_play import (
    GooglePlayPublisherGateway,
    GooglePlayPublisherVerifier,
    GooglePlayRtdnEvent,
    SubscriptionPurchaseV2,
)


class Response:
    status_code = 200

    def json(self):
        return {
            "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
            "acknowledgementState": "ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED",
            "lineItems": [{"productId": "peti_premium_monthly"}],
        }


class Session:
    def __init__(self):
        self.calls = []

    def get(self, url, timeout):
        self.calls.append((url, timeout))
        return Response()


def test_google_play_gateway_fetches_canonical_subscription_state():
    session = Session()
    gateway = GooglePlayPublisherGateway("com.peti.app", http_session=session)
    body = {"package_name": "com.peti.app", "product_id": "peti_premium_monthly", "purchase_token": "tok/1"}

    assert GooglePlayPublisherVerifier(gateway)(body)
    assert body["play_state"] == "SUBSCRIPTION_STATE_ACTIVE"
    assert "/applications/com.peti.app/" in session.calls[0][0]
    assert "tok%2F1" in session.calls[0][0]


def test_google_play_gateway_rejects_product_not_in_canonical_response():
    class WrongProductResponse(Response):
        def json(self):
            return {"lineItems": [{"productId": "other"}]}

    class WrongProductSession(Session):
        def get(self, url, timeout):
            return WrongProductResponse()

    gateway = GooglePlayPublisherGateway(http_session=WrongProductSession())
    try:
        gateway.verify("com.peti.app", "peti_premium_monthly", "tok")
    except ValueError as exc:
        assert str(exc) == "PREMIUM_PRODUCT_NOT_ALLOWED"
    else:
        raise AssertionError("untrusted product was accepted")


def test_google_play_verifier_rejects_non_string_purchase_fields():
    session = Session()
    gateway = GooglePlayPublisherGateway("com.peti.app", http_session=session)
    verifier = GooglePlayPublisherVerifier(gateway)
    body = {
        "package_name": "com.peti.app",
        "product_id": "peti_premium_monthly",
        "purchase_token": None,
    }

    try:
        verifier(body)
    except ValueError as exc:
        assert str(exc) == "PREMIUM_PURCHASE_INVALID"
    else:
        raise AssertionError("non-string purchase token was accepted")
    assert session.calls == []


def test_verified_subscription_rejects_malformed_identifiers():
    try:
        SubscriptionPurchaseV2.from_verified({
            "package_name": "com.peti.app",
            "product_id": "peti_premium_monthly",
            "purchase_token": None,
            "subscription_state": "SUBSCRIPTION_STATE_ACTIVE",
        })
    except ValueError as exc:
        assert str(exc) == "PREMIUM_VERIFICATION_INVALID"
    else:
        raise AssertionError("malformed verified subscription was accepted")


def test_rtdn_parser_rejects_non_mapping_payload():
    try:
        GooglePlayRtdnEvent.from_payload(None)
    except ValueError as exc:
        assert str(exc) == "RTDN_PAYLOAD_INVALID"
    else:
        raise AssertionError("non-mapping RTDN payload was accepted")
