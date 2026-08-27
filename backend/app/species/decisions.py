from dataclasses import dataclass


@dataclass(frozen=True)
class SpeciesExpansionDecision:
    candidate_species: str
    demand_score: int
    evidence_score: int
    safety_score: int
    decision: str
    rationale: str


class SpeciesSelectionRubric:
    def decide(self, candidate, demand, evidence, safety):
        decision = "PROFILE_ONLY" if min(evidence, safety) < 3 else ("REVIEW" if demand >= 3 else "REJECT")
        return SpeciesExpansionDecision(candidate, demand, evidence, safety, decision, "Evidence and safety gates precede demand-only expansion.")
