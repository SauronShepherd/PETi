from app.agent_runtime.capability_registry import CapabilityDescriptor

CAPABILITIES_V1 = (
    CapabilityDescriptor("GOAL_RESOLUTION", "1.0.0", "goal-resolver", (), "goal-resolution-v1", ("GOAL",)),
    CapabilityDescriptor("EVIDENCE_INTAKE", "1.0.0", "evidence-intake", ("media_asset_ids",), "evidence-intake-v1", ("MEDIA",)),
    CapabilityDescriptor("FECES_CURRENT_ASSESSMENT", "1.0.0", "feces-specialist", ("current_evidence",), "feces-result-v1", ("MEDIA",)),
    CapabilityDescriptor("FECES_LONGITUDINAL_COMPARE", "1.0.0", "longitudinal-specialist", ("current_result", "prior_results"), "longitudinal-result-v1", ("FECES_HISTORY",)),
    CapabilityDescriptor("FINAL_SYNTHESIS", "1.0.0", "synthesis", ("validated_claims",), "agent-answer-v1"),
    CapabilityDescriptor("CARE_FOLLOW_UP_PROPOSAL", "1.0.0", "care-planner", ("validated_claims",), "proposed-action-v1"),
    CapabilityDescriptor("CREATE_CARE_REMINDER_ACTION", "1.0.0", "care-action-executor", ("approved_action",), "action-receipt-v1", mutation_scopes=()),
)
