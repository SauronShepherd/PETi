from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyDecision:
    state: str
    reasons: list[str]


def evaluate_safety(result: dict, user_context: str | None = None) -> SafetyDecision:
    def collect(value):
        if isinstance(value, dict):
            return " ".join(collect(item) for item in value.values())
        if isinstance(value, (list, tuple)):
            return " ".join(collect(item) for item in value)
        return str(value)

    text = f"{collect(result)} {user_context or ''}".lower()
    signals = (
        ("difficulty breathing", "DIFFICULTY_BREATHING"),
        ("unconscious", "UNCONSCIOUS"),
        ("severe bleeding", "SEVERE_BLEEDING"),
        ("collapse", "COLLAPSE"),
        ("blue gums", "CYANOSIS"),
        ("cannot stand", "INABILITY_TO_STAND"),
    )
    reasons = [code for phrase, code in signals if phrase in text and f"no {phrase}" not in text]
    if reasons:
        return SafetyDecision("URGENT", reasons)
    state = str(result.get("safety_state", "")) if isinstance(result, dict) else ""
    allowed = {
        "CLEAR", "REVIEW", "URGENT", "INSUFFICIENT_EVIDENCE",
        "MONITOR", "PROFESSIONAL_REVIEW_RECOMMENDED", "PROMPT_VETERINARY_CONTACT", "NORMAL_INFORMATION",
    }
    return SafetyDecision(state if state in allowed else "INSUFFICIENT_EVIDENCE", [])
