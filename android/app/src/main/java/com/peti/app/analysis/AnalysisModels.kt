package com.peti.app.analysis

enum class AnalysisStatus { CREATED, FUNDING_RESERVED, QUEUED, PREPARING_MEDIA, CALLING_PROVIDER, VALIDATING_OUTPUT, APPLYING_GUARDRAILS, APPLYING_SAFETY, PERSISTING_RESULT, COMPLETED, FAILED_RETRYABLE, FAILED_FINAL, CANCELED }

data class AnalysisJob(
    val id: String,
    val animalId: String,
    val analysisType: String,
    val status: AnalysisStatus,
    val mediaAssetIds: List<String>,
    val result: AnalysisResult? = null,
)

data class AnalysisResult(
    val id: String,
    val jobId: String,
    val summary: String,
    val safetyState: String,
    val provider: String,
    val model: String,
    val evidenceQuality: String = "LOW",
    val limitations: List<String> = emptyList(),
    val sourceMediaIds: List<String> = emptyList(),
    val observations: List<String> = emptyList(),
    val uncertainties: List<String> = emptyList(),
    val interpretations: List<String> = emptyList(),
    val redFlags: List<String> = emptyList(),
    val recommendedActions: List<String> = emptyList(),
)
