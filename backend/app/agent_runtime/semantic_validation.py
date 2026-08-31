"""Deterministic semantic gates applied after strict model parsing."""

ALLOWED_COMPARABILITY = {"COMPARABLE", "NOT_COMPARABLE", "INSUFFICIENT_DATA"}
ALLOWED_CHANGE = {None, "IMPROVED", "WORSENED", "NO_MATERIAL_CHANGE", "UNCERTAIN"}
URGENT_SIGNALS = {"COLLAPSE", "UNABLE_TO_KEEP_WATER_DOWN", "DARK_BLACK_TAR_LIKE"}
PROMPT_SIGNALS = {"MARKED_LETHARGY", "REPEATED_VOMITING", "FRESH_RED_BLOOD_LIKE"}
SAFETY_STATES = {"NORMAL_INFORMATION", "PROFESSIONAL_REVIEW_RECOMMENDED", "PROMPT_VETERINARY_CONTACT", "URGENT_VETERINARY_CONTACT"}


def validate_longitudinal(payload: dict) -> dict:
    comparability = str(payload.get("comparability", ""))
    if comparability not in ALLOWED_COMPARABILITY:
        raise ValueError("LONGITUDINAL_COMPARABILITY_INVALID")
    if comparability != "COMPARABLE" and payload.get("change_label") is not None:
        raise ValueError("LONGITUDINAL_CHANGE_WITHOUT_COMPARABILITY")
    if payload.get("change_label") not in ALLOWED_CHANGE:
        raise ValueError("LONGITUDINAL_CHANGE_INVALID")
    return payload


def deterministic_feces_safety(payload: dict, owner_context: dict | None = None) -> str:
    signals = {str(value).upper() for value in payload.get("red_flags", [])}
    context = owner_context or {}
    signals.update(key.upper() for key, value in context.items() if value is True)
    if signals & URGENT_SIGNALS:
        return "URGENT_VETERINARY_CONTACT"
    if signals & PROMPT_SIGNALS:
        return "PROMPT_VETERINARY_CONTACT"
    if payload.get("observations") or signals:
        return "PROFESSIONAL_REVIEW_RECOMMENDED"
    return "NORMAL_INFORMATION"


def validate_synthesis(claims: list[dict], safety_state: str) -> list[dict]:
    if safety_state not in SAFETY_STATES:
        raise ValueError("SYNTHESIS_SAFETY_STATE_INVALID")
    for claim in claims:
        if not isinstance(claim, dict) or not str(claim.get("text", "")).strip() or not claim.get("evidence_ids"):
            raise ValueError("SYNTHESIS_CLAIM_NOT_GROUNDED")
    return claims
