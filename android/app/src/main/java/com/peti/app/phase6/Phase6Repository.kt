package com.peti.app.phase6

import com.peti.app.auth.AccessTokenProvider
import com.peti.app.auth.CorrelationIds
import java.net.HttpURLConnection
import java.net.URL

interface Phase6Repository {
    suspend fun timeline(animalId: String, itemType: String? = null): String
    suspend fun measurements(animalId: String, sourceClass: String? = null, includeAiEstimates: Boolean = false): String
    suspend fun measurementTrend(animalId: String, sourceClass: String? = null, includeAiEstimates: Boolean = false): String
    suspend fun logMeasurement(animalId: String, requestJson: String, idempotencyKey: String): String
    suspend fun care(animalId: String): String
    suspend fun occurrences(animalId: String): String
    suspend fun createCare(animalId: String, requestJson: String, idempotencyKey: String): String
    suspend fun occurrenceAction(occurrenceId: String, action: String, requestJson: String? = null, idempotencyKey: String? = null): String
    suspend fun notificationPreferences(): String
    suspend fun updateNotificationPreferences(requestJson: String): String
    suspend fun registerDevice(requestJson: String): String
}

class ApiPhase6Repository(private val baseUrl: String, private val tokens: AccessTokenProvider) : Phase6Repository {
    private suspend fun request(method: String, path: String, body: String? = null, idempotencyKey: String? = null): String {
        val connection = (URL(baseUrl + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method; connectTimeout = 10_000; readTimeout = 10_000
            setRequestProperty("Accept", "application/json")
            setRequestProperty("X-Correlation-ID", CorrelationIds.next())
            tokens.getAccessToken(false)?.let { setRequestProperty("Authorization", "Bearer $it") }
            idempotencyKey?.let { setRequestProperty("Idempotency-Key", it) }
            if (body != null) { doOutput = true; setRequestProperty("Content-Type", "application/json"); outputStream.use { it.write(body.toByteArray()) } }
        }
        val response = (if (connection.responseCode in 200..299) connection.inputStream else connection.errorStream).bufferedReader().use { it.readText() }
        if (connection.responseCode !in 200..299) error(response.ifBlank { "HTTP ${connection.responseCode}" })
        return response
    }
    override suspend fun timeline(animalId: String, itemType: String?): String = request("GET", "/v1/pets/$animalId/timeline" + (itemType?.let { "?item_type=$it" } ?: ""))
    override suspend fun measurements(animalId: String, sourceClass: String?, includeAiEstimates: Boolean): String {
        val query = buildList {
            sourceClass?.let { add("source_class=$it") }
            if (includeAiEstimates) add("include_ai_estimates=true")
        }.joinToString("&").takeIf { it.isNotEmpty() }?.let { "?$it" } ?: ""
        return request("GET", "/v1/pets/$animalId/measurements$query")
    }
    override suspend fun measurementTrend(animalId: String, sourceClass: String?, includeAiEstimates: Boolean): String {
        val query = buildList {
            sourceClass?.let { add("source_class=$it") }
            if (includeAiEstimates) add("include_ai_estimates=true")
        }.joinToString("&").takeIf { it.isNotEmpty() }?.let { "?$it" } ?: ""
        return request("GET", "/v1/pets/$animalId/measurements/trend$query")
    }
    override suspend fun logMeasurement(animalId: String, requestJson: String, idempotencyKey: String) = request("POST", "/v1/pets/$animalId/measurements", requestJson, idempotencyKey)
    override suspend fun care(animalId: String) = request("GET", "/v1/pets/$animalId/care")
    override suspend fun occurrences(animalId: String) = request("GET", "/v1/pets/$animalId/care-occurrences")
    override suspend fun createCare(animalId: String, requestJson: String, idempotencyKey: String) = request("POST", "/v1/pets/$animalId/care", requestJson, idempotencyKey)
    override suspend fun occurrenceAction(occurrenceId: String, action: String, requestJson: String?, idempotencyKey: String?) = request("POST", "/v1/care-occurrences/$occurrenceId/$action", requestJson, idempotencyKey)
    override suspend fun notificationPreferences() = request("GET", "/v1/me/notification-preferences")
    override suspend fun updateNotificationPreferences(requestJson: String) = request("PATCH", "/v1/me/notification-preferences", requestJson)
    override suspend fun registerDevice(requestJson: String) = request("POST", "/v1/me/devices", requestJson)
}
