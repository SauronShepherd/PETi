"""Deterministic same-dog candidate selection before longitudinal inference."""


def select_compatible_candidates(current: dict, candidates: list[dict], *, limit: int = 20) -> list[dict]:
    if not current.get("pet_id") or not current.get("modality") or not current.get("taxonomy_version"):
        return []
    selected = []
    for candidate in candidates:
        if (candidate.get("pet_id") != current["pet_id"]
                or candidate.get("modality") != current["modality"]
                or candidate.get("taxonomy_version") != current["taxonomy_version"]
                or candidate.get("evidence_quality") in {"INSUFFICIENT", "UNSPECIFIED"}):
            continue
        selected.append(dict(candidate))
    return selected[:max(0, limit)]
