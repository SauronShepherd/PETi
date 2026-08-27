package com.peti.app.specialists

import com.peti.app.auth.AccessTokenProvider
import com.peti.app.auth.CorrelationIds
import java.net.HttpURLConnection
import java.net.URL

data class InitialScanCandidateUi(
    val id: String,
    val fieldType: String,
    val candidateValue: String,
    val status: String,
    val provenanceStatus: String,
)

fun parseInitialScanCandidates(payload: String): List<InitialScanCandidateUi> {
    val field = Regex("""\"([^\"]+)\"\s*:\s*\"((?:\\.|[^\"])*)\"""")
    fun value(objectText: String, name: String) = field.findAll(objectText)
        .firstOrNull { it.groupValues[1] == name }?.groupValues?.get(2)
        ?.replace("\\\"", "\"") ?: ""
    return Regex("""\{[^{}]*\}""").findAll(payload).map { match ->
        val text = match.value
        InitialScanCandidateUi(value(text, "id"), value(text, "field_type"), value(text, "candidate_value"), value(text, "status"), value(text, "provenance_status"))
    }.toList()
}

interface SpecialistRepository {
    suspend fun create(petId: String, type: String, body: String, idempotencyKey: String): String
    suspend fun list(petId: String, type: String): String
    suspend fun get(id: String, type: String): String
    suspend fun candidates(scanId: String): String
    suspend fun review(candidateId: String, action: String, body: String? = null): String
    suspend fun comparison(bodyCheckId: String): String
}

class ApiSpecialistRepository(private val baseUrl: String, private val tokens: AccessTokenProvider) : SpecialistRepository {
    private suspend fun request(method: String, path: String, body: String? = null, key: String? = null): String {
        val c = (URL(baseUrl + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method; connectTimeout = 10_000; readTimeout = 10_000
            setRequestProperty("Accept", "application/json")
            setRequestProperty("X-Correlation-ID", CorrelationIds.next())
            tokens.getAccessToken(false)?.let { setRequestProperty("Authorization", "Bearer $it") }
            key?.let { setRequestProperty("Idempotency-Key", it) }
            if (body != null) { doOutput = true; setRequestProperty("Content-Type", "application/json"); outputStream.use { it.write(body.toByteArray()) } }
        }
        val stream = if (c.responseCode in 200..299) c.inputStream else c.errorStream
        val text = stream.bufferedReader().use { it.readText() }
        if (c.responseCode !in 200..299) error(text.ifBlank { "HTTP ${c.responseCode}" })
        return text
    }
    private fun plural(type: String) = when (type) { "DOG_INITIAL_SCAN" -> "initial-scans"; "DOG_DENTAL_CHECK" -> "dental-checks"; "DOG_FECES_CHECK" -> "feces-checks"; else -> "body-checks" }
    override suspend fun create(petId: String, type: String, body: String, idempotencyKey: String) = request("POST", "/v1/pets/$petId/${plural(type)}", body, idempotencyKey)
    override suspend fun list(petId: String, type: String) = request("GET", "/v1/pets/$petId/${plural(type)}")
    override suspend fun get(id: String, type: String) = request("GET", "/v1/${plural(type)}/$id")
    override suspend fun candidates(scanId: String) = request("GET", "/v1/initial-scans/$scanId/candidates")
    override suspend fun review(candidateId: String, action: String, body: String?) = request("POST", "/v1/initial-scan-candidates/$candidateId/$action", body)
    override suspend fun comparison(bodyCheckId: String) = request("GET", "/v1/body-checks/$bodyCheckId/comparison")
}

class LocalSpecialistRepository : SpecialistRepository {
    override suspend fun create(petId: String, type: String, body: String, idempotencyKey: String) = "{\"analysis_type\":\"$type\",\"status\":\"COMPLETED\"}"
    override suspend fun list(petId: String, type: String) = "[]"
    override suspend fun get(id: String, type: String) = "{\"id\":\"$id\",\"analysis_type\":\"$type\"}"
    override suspend fun candidates(scanId: String) = "[]"
    override suspend fun review(candidateId: String, action: String, body: String?) = "{\"status\":\"${action.uppercase()}\"}"
    override suspend fun comparison(bodyCheckId: String) = "{\"status\":\"NOT_COMPARABLE\"}"
}
