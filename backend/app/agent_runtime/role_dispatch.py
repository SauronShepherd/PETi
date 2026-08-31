"""Capability-bound model invocation boundary for ADK-backed role agents."""
from dataclasses import dataclass

from .agent_model_provider import AgentModelProvider, ProviderInvocationResult
from .semantic_validation import validate_longitudinal
from .structured_invocation import parse_with_bounded_repair


@dataclass(frozen=True)
class RoleInvocation:
    role: str
    model_binding: object
    prompt_version: str
    context_bundle: object
    response_schema: type
    timeout_seconds: float = 30.0


class RoleDispatcher:
    """Invokes only the role and schema selected by the validated plan node."""

    def __init__(self, provider: AgentModelProvider):
        self.provider = provider

    def dispatch(self, request: RoleInvocation) -> ProviderInvocationResult:
        if not request.role or not request.prompt_version:
            raise ValueError("AGENT_INVOCATION_METADATA_REQUIRED")
        result = self.provider.invoke(
            role=request.role,
            model_binding=request.model_binding,
            prompt_version=request.prompt_version,
            context_bundle=request.context_bundle,
            tool_declarations=[],
            response_schema=request.response_schema,
            timeout_seconds=request.timeout_seconds,
        )
        # Validate at the boundary; successors never receive untyped provider data.
        parsed = parse_with_bounded_repair(result.structured_payload, request.response_schema, max_attempts=0)
        if hasattr(parsed, "code"):
            raise ValueError(parsed.code)
        if request.role == "FECES_LONGITUDINAL_COMPARE":
            validate_longitudinal(result.structured_payload)
        return result

    def dispatch_many(self, requests: list[RoleInvocation]) -> list[ProviderInvocationResult]:
        """Run a validated linear subgraph, preserving one context/schema per role."""
        return [self.dispatch(request) for request in requests]
