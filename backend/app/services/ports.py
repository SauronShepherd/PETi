from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol


class FakeScenario(StrEnum):
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    MALFORMED_OUTPUT = "MALFORMED_OUTPUT"
    SAFETY_VIOLATION = "SAFETY_VIOLATION"


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FakeClock:
    def __init__(self, value: datetime):
        self.value = value

    def now(self) -> datetime:
        return self.value


class IdGenerator(Protocol):
    def new_id(self) -> str: ...


class UuidGenerator:
    def new_id(self) -> str:
        import uuid

        return uuid.uuid4().hex


class FakeIdGenerator:
    def __init__(self) -> None:
        self.i = 0

    def new_id(self) -> str:
        self.i += 1
        return f"fake-{self.i}"


class AIProvider(Protocol):
    def analyze(self, payload: object) -> object: ...


class FakeAIProvider:
    def __init__(self, scenario: FakeScenario = FakeScenario.SUCCESS):
        self.scenario = scenario

    def analyze(self, payload: object) -> object:
        if self.scenario is not FakeScenario.SUCCESS:
            raise RuntimeError(self.scenario.value)
        return {"status": "candidate", "payload": payload}


class MediaPreparation(Protocol):
    def prepare(self, payload: object) -> object: ...


class StructuredValidator(Protocol):
    def validate(self, payload: object) -> object: ...


class SemanticGuardrail(Protocol):
    def check(self, payload: object) -> object: ...


class SafetyEngine(Protocol):
    def assess(self, payload: object) -> object: ...
