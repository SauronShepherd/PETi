"""Bounded structured-output parsing; never persists raw provider reasoning."""
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError


@dataclass(frozen=True)
class StructuredFailure:
    code: str = "AGENT_STRUCTURED_OUTPUT_INVALID"
    attempts: int = 0


def parse_with_bounded_repair(payload: dict, schema: type[BaseModel], *, repair=None, max_attempts: int = 1):
    """Return a validated model or a typed failure after bounded repair."""
    candidate = payload
    for attempt in range(max_attempts + 1):
        try:
            return schema.model_validate(candidate)
        except ValidationError:
            if attempt >= max_attempts or repair is None:
                return StructuredFailure(attempts=attempt + 1)
            candidate = repair(candidate)
            if not isinstance(candidate, dict):
                return StructuredFailure(attempts=attempt + 2)
