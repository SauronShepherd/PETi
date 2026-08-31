from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar


class DirectIntent(StrEnum):
    SHOW_LATEST_MEASURED_WEIGHT = "SHOW_LATEST_MEASURED_WEIGHT"
    SHOW_NEXT_REMINDER = "SHOW_NEXT_REMINDER"
    OPEN_KNOWN_RESULT = "OPEN_KNOWN_RESULT"
    OPEN_KNOWN_DOCUMENT = "OPEN_KNOWN_DOCUMENT"
    SHOW_MEASUREMENT_HISTORY = "SHOW_MEASUREMENT_HISTORY"
    SHOW_CARE_STATUS = "SHOW_CARE_STATUS"
    START_KNOWN_FECES_CAPTURE = "START_KNOWN_FECES_CAPTURE"


@dataclass(frozen=True)
class FastPathResult:
    intent: DirectIntent
    requires_model: bool = False
    target: str | None = None


class FastPathResolver:
    _phrases: ClassVar[dict[str, DirectIntent]] = {
        "show latest measured weight": DirectIntent.SHOW_LATEST_MEASURED_WEIGHT,
        "show next reminder": DirectIntent.SHOW_NEXT_REMINDER,
        "show measurement history": DirectIntent.SHOW_MEASUREMENT_HISTORY,
        "show care status": DirectIntent.SHOW_CARE_STATUS,
        "start feces capture": DirectIntent.START_KNOWN_FECES_CAPTURE,
    }

    def resolve(self, text: str) -> FastPathResult | None:
        normalized = " ".join(str(text or "").lower().strip().split())
        intent = self._phrases.get(normalized)
        return FastPathResult(intent) if intent else None
