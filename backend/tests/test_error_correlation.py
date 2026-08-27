import asyncio
from types import SimpleNamespace

from app.api.errors import PetiError, error_handler
from app.api.v1 import CreateAnalysisRequest, create_analysis
from app.auth.models import AuthenticatedPrincipal


def test_error_envelope_uses_request_correlation_id():
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="cid-123"))
    response = asyncio.run(error_handler(request, PetiError("E", "failed")))
    assert response.body and b'"correlation_id":"cid-123"' in response.body


def test_correlation_id_propagates_end_to_end_into_analysis_creation():
    captured = {}

    class Analysis:
        def create(self, *args):
            captured["args"] = args
            return "job"

        def public_job(self, job):
            return {"id": job}

    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(analysis=Analysis())),
        state=SimpleNamespace(correlation_id="cid-analysis-123"),
    )
    body = CreateAnalysisRequest(
        animal_id="pet-1", media_asset_ids=["media-1"], funding_reservation_id="reservation-1"
    )
    principal = AuthenticatedPrincipal("firebase-1", "owner-1", "CUSTOMER", False, False)
    response = asyncio.run(create_analysis("pet-1", body, request, None, principal))

    assert response == {"id": "job"}
    assert captured["args"][-1] == "cid-analysis-123"
