package com.peti.app.analysis

enum class PetiCheckSafetyState { CLEAR, REVIEW, URGENT, INSUFFICIENT_EVIDENCE }
enum class EvidenceQualityLevel { HIGH, MEDIUM, LOW }

data class PetiCheckObservation(
    val text: String,
    val provenance: String = "VISIBLE",
    val confidence: String = "MEDIUM",
)

data class PetiCheckResultV1(
    val summary: String,
    val observations: List<PetiCheckObservation> = emptyList(),
    val uncertainties: List<String> = emptyList(),
    val possibleInterpretations: List<String> = emptyList(),
    val redFlags: List<String> = emptyList(),
    val recommendedActions: List<String> = emptyList(),
    val limitations: List<String> = emptyList(),
    val evidenceQuality: EvidenceQualityLevel = EvidenceQualityLevel.LOW,
    val safetyState: PetiCheckSafetyState = PetiCheckSafetyState.CLEAR,
    val sourceMediaIds: List<String> = emptyList(),
)

class PetiCheckStatusReducer {
    fun reduce(previous: AnalysisJob?, incoming: AnalysisJob): AnalysisJob {
        if (previous == null) return incoming
        if (previous.status == AnalysisStatus.COMPLETED || previous.status == AnalysisStatus.CANCELED) return previous
        return incoming
    }
}
