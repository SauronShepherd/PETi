from app.agent_runtime.claim_composition import compose_claims


def test_claims_require_evidence_and_preserve_asset_refs():
    result = compose_claims({"observations": [{"statement": "Visible formed stool", "source_media_ids": ["asset-7"]}, {"statement": "No trace"}]}, ["asset-1"])
    assert result == [
        {"claim_type": "OBSERVED", "text": "Visible formed stool", "evidence_ids": ["asset-7"]},
        {"claim_type": "OBSERVED", "text": "No trace", "evidence_ids": ["asset-1"]},
    ]
