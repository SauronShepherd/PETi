package com.peti.app.analysis

interface AnalysisRepository {
    suspend fun create(
        animalId: String,
        mediaAssetIds: List<String>,
        fundingReservationId: String,
        idempotencyKey: String,
        userContext: String? = null,
    ): AnalysisJob

    suspend fun get(jobId: String): AnalysisJob

    suspend fun listHistory(animalId: String): List<AnalysisJob>
}

class FakeAnalysisRepository : AnalysisRepository {
    private val jobs = mutableMapOf<String, AnalysisJob>()
    override suspend fun create(animalId: String, mediaAssetIds: List<String>, fundingReservationId: String, idempotencyKey: String, userContext: String?): AnalysisJob {
        jobs[idempotencyKey]?.let { return it }
        val job = AnalysisJob(idempotencyKey, animalId, "PETI_CHECK", AnalysisStatus.COMPLETED, mediaAssetIds, AnalysisResult("result-$idempotencyKey", idempotencyKey, "Media review completed.", "CLEAR", "FAKE", "fake-v1"))
        jobs[idempotencyKey] = job
        return job
    }
    override suspend fun get(jobId: String): AnalysisJob = jobs.values.first { it.id == jobId }

    override suspend fun listHistory(animalId: String): List<AnalysisJob> =
        jobs.values.filter { it.animalId == animalId && it.analysisType == "PETI_CHECK" }
}

class AnalysisStatusReducer {
    fun reduce(previous: AnalysisJob?, incoming: AnalysisJob): AnalysisJob {
        if (previous == null) return incoming
        if (previous.status == AnalysisStatus.COMPLETED || previous.status == AnalysisStatus.CANCELED) return previous
        return incoming
    }
}
