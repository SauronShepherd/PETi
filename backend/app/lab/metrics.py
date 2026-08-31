from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from .contracts import RufsClassification
from .enums import FeedbackValue, RufsState


@dataclass(frozen=True)
class ProportionMetric:
    value: float | None
    numerator: int
    denominator: int
    low: float | None
    high: float | None
    preliminary: bool


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    kind: str
    unit: str
    description: str
    version: str = "1.0.0"


METRIC_CATALOG = {
    item.name: item
    for item in (
        MetricDefinition("run_completion", "PROPORTION", "ratio", "Terminal runs that succeeded."),
        MetricDefinition("helpfulness", "PROPORTION", "ratio", "Active ratings marked HELPED."),
        MetricDefinition("feedback_coverage", "PROPORTION", "ratio", "Eligible responses with active feedback."),
        MetricDefinition("safe_completion", "PROPORTION", "ratio", "Terminal runs with an allowed safety outcome."),
        MetricDefinition("grounded_claim_rate", "PROPORTION", "ratio", "Claims backed by selected evidence."),
        MetricDefinition("known_usage_coverage", "PROPORTION", "ratio", "Model calls with reported token usage."),
        MetricDefinition("model_success_rate", "PROPORTION", "ratio", "Model calls completed successfully."),
        MetricDefinition("average_model_latency_ms", "MEAN", "milliseconds", "Mean model call latency."),
        MetricDefinition("evidence_per_run", "MEAN", "items", "Selected evidence per observed run."),
        MetricDefinition("rufs", "PROPORTION", "ratio", "Runs passing useful, grounded and safe dimensions."),
        MetricDefinition("friction_index", "INDEX", "points", "Bounded product-friction signal from 0 to 100."),
    )
}


def proportion(numerator: int, denominator: int, *, minimum_sample: int = 30) -> ProportionMetric:
    if numerator < 0 or denominator < 0 or numerator > denominator:
        raise ValueError("LAB_METRIC_COUNTS_INVALID")
    if denominator == 0:
        return ProportionMetric(None, numerator, denominator, None, None, True)
    value = numerator / denominator
    z = 1.959963984540054
    denominator_w = 1 + z * z / denominator
    center = (value + z * z / (2 * denominator)) / denominator_w
    margin = z * sqrt((value * (1 - value) + z * z / (4 * denominator)) / denominator) / denominator_w
    return ProportionMetric(value, numerator, denominator, max(0.0, center - margin), min(1.0, center + margin), denominator < minimum_sample)


def classify_rufs(
    *,
    outcome: str,
    safety_state: str,
    grounded_claims: int,
    total_claims: int,
    feedback_value: FeedbackValue | None,
    has_strong_friction: bool = False,
) -> RufsClassification:
    reasons: list[str] = []
    if feedback_value is FeedbackValue.HELPED and not has_strong_friction:
        useful = RufsState.PASS
    elif feedback_value is FeedbackValue.NOT_QUITE or has_strong_friction:
        useful = RufsState.FAIL
        reasons.append("NOT_USEFUL")
    else:
        useful = RufsState.UNKNOWN
        reasons.append("USEFULNESS_UNKNOWN")

    insufficient = outcome in {"INSUFFICIENT_EVIDENCE", "NEEDS_NEW_OBSERVATION"}
    if total_claims > 0 and grounded_claims == total_claims or insufficient:
        grounded = RufsState.PASS
    elif total_claims > 0:
        grounded = RufsState.FAIL
        reasons.append("UNGROUNDED_CLAIMS")
    else:
        grounded = RufsState.UNKNOWN
        reasons.append("GROUNDING_UNKNOWN")

    unsafe_states = {"UNSAFE", "POLICY_VIOLATION", "UNDER_TRIAGE"}
    if safety_state in unsafe_states:
        safe = RufsState.FAIL
        reasons.append("SAFETY_FAILURE")
    elif safety_state in {"SAFE_TO_DISPLAY", "REVIEW_REQUIRED", "SAFETY_ROUTED", "POLICY_BLOCKED"}:
        safe = RufsState.PASS
    else:
        safe = RufsState.UNKNOWN
        reasons.append("SAFETY_UNKNOWN")

    dimensions = (useful, grounded, safe)
    if RufsState.FAIL in dimensions:
        overall = RufsState.FAIL
    elif all(state is RufsState.PASS for state in dimensions):
        overall = RufsState.PASS
    else:
        overall = RufsState.UNKNOWN
    return RufsClassification(useful, grounded, safe, overall, tuple(reasons))
