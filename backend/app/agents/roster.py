from enum import StrEnum


class AgentType(StrEnum):
    ORCHESTRATOR = "ORCHESTRATOR"; FECES_SPECIALIST = "FECES_SPECIALIST"; DENTAL_SPECIALIST = "DENTAL_SPECIALIST"; CLINICAL_RECORDS = "CLINICAL_RECORDS"; LONGITUDINAL = "LONGITUDINAL"; CARE_PLANNING = "CARE_PLANNING"; WEEKLY_REPORT = "WEEKLY_REPORT"; QUALITY_OPS = "QUALITY_OPS"


AGENT_CAPABILITIES = {
    AgentType.ORCHESTRATOR: {"plan", "synthesize"}, AgentType.FECES_SPECIALIST: {"observe_feces"}, AgentType.DENTAL_SPECIALIST: {"observe_dental"}, AgentType.CLINICAL_RECORDS: {"read_records", "extract_candidates"}, AgentType.LONGITUDINAL: {"compare_sources"}, AgentType.CARE_PLANNING: {"propose_care"}, AgentType.WEEKLY_REPORT: {"build_report"}, AgentType.QUALITY_OPS: {"inspect_telemetry"},
}
