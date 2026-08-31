from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class InvocationContext:
    owner_user_id: str
    run_id: str
    step_id: str
    agent_id: str
    correlation_id: str
    deployment_id: str
    prompt_version: str = "1.0.0"
    schema_version: str = "1.0.0"
    safety_policy_version: str = "1.0.0"


_current: ContextVar[InvocationContext | None] = ContextVar("peti_invocation_context", default=None)


def current_invocation() -> InvocationContext | None:
    return _current.get()


@contextmanager
def invocation_scope(context: InvocationContext) -> Iterator[InvocationContext]:
    token = _current.set(context)
    try:
        yield context
    finally:
        _current.reset(token)
