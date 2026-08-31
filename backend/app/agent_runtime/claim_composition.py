"""Deterministic claim materialization for customer-visible agent results."""


def compose_claims(payload: dict, evidence_ids: list[str]) -> list[dict]:
    claims = []
    fallback = [str(x) for x in evidence_ids]
    for raw in payload.get("observations", []) or []:
        if isinstance(raw, str):
            text, refs = raw, fallback
        elif isinstance(raw, dict):
            text = str(raw.get("statement") or raw.get("text") or "").strip()
            refs = [str(x) for x in (raw.get("source_media_ids") or raw.get("evidence_ids") or fallback)]
        else:
            continue
        if text and refs:
            claims.append({"claim_type": "OBSERVED", "text": text[:500], "evidence_ids": sorted(set(refs))})
    return claims
