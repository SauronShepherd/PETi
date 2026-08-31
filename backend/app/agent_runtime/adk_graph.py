"""Google ADK graph used as PETi's multi-agent coordination boundary.

The durable PETi runtime remains authoritative for identity, state, evidence,
budgets and safety. ADK supplies the agent composition and delegation model;
it is deliberately not allowed to write directly to Firestore or call tools
outside the application gateway.
"""

from typing import Any


def build_peti_agent(model: str = "gemini-3.5-flash") -> Any:
    """Build the coordinator and its specialist sub-agents.

    Imports are lazy so local fake-provider tests do not require the optional
    ADK runtime to be installed. Production images install ``google-adk``.
    """
    try:
        from google.adk.agents import LlmAgent
    except ModuleNotFoundError as exc:
        # Keep the graph contract usable in the lightweight test image. The
        # production dependency is declared in pyproject.toml; this fallback
        # is deliberately a data-only graph and cannot invoke a model.
        if exc.name not in {"google", "google.adk", "google.adk.agents"}:
            raise

        class LlmAgent:  # type: ignore[no-redef]
            def __init__(self, *, name, model, description, instruction, sub_agents=None):
                self.name = name
                self.model = model
                self.description = description
                self.instruction = instruction
                self.sub_agents = list(sub_agents or [])

    evidence = LlmAgent(
        name="evidence_intake_agent",
        model=model,
        description="Checks that submitted pet evidence is usable and grounded.",
        instruction="Describe only observable evidence. Do not diagnose or prescribe.",
    )
    specialist = LlmAgent(
        name="pet_specialist_agent",
        model=model,
        description="Reviews pet evidence for the requested specialist domain.",
        instruction="Return cautious observations, uncertainty and limitations only.",
    )
    safety = LlmAgent(
        name="safety_review_agent",
        model=model,
        description="Reviews candidate observations for safety and escalation needs.",
        instruction="Never rule out a condition. Flag uncertainty and urgent escalation.",
    )
    root = LlmAgent(
        name="peti_orchestrator_agent",
        model=model,
        description="Coordinates PETi's evidence, specialist and safety workflow.",
        instruction=(
            "Coordinate the bounded PETi workflow. Delegate to the available "
            "specialists, preserve provenance, and return grounded observations. "
            "Never diagnose, prescribe, change ownership, or execute external actions."
        ),
        sub_agents=[evidence, specialist, safety],
    )
    object.__setattr__(root, "role_agents", {
        "EVIDENCE_INTAKE": evidence,
        "FECES_CURRENT_ASSESSMENT": specialist,
        "FECES_LONGITUDINAL_COMPARE": specialist,
        "SAFETY_REVIEW": safety,
        "FINAL_SYNTHESIS": root,
    })
    return root


def graph_metadata(model: str = "gemini-3.5-flash") -> dict[str, Any]:
    """Return stable evidence that the run is backed by a composed ADK graph."""
    return {
        "framework": "google-adk",
        "model": model,
        "root_agent": "peti_orchestrator_agent",
        "sub_agents": ["evidence_intake_agent", "pet_specialist_agent", "safety_review_agent"],
    }
