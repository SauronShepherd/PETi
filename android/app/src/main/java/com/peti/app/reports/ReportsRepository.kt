package com.peti.app.reports

import com.peti.app.auth.AccessTokenProvider
import com.peti.app.auth.CorrelationIds
import java.net.HttpURLConnection
import java.net.URL

interface ReportsRepository { suspend fun list(petId: String): String; suspend fun get(reportId: String): String; suspend fun generate(petId: String): String }

class ApiReportsRepository(private val baseUrl: String, private val tokens: AccessTokenProvider) : ReportsRepository {
    private suspend fun request(method: String, path: String, body: String? = null): String {
        val c = (URL(baseUrl + path).openConnection() as HttpURLConnection).apply { requestMethod = method; connectTimeout = 10_000; readTimeout = 10_000; setRequestProperty("Accept", "application/json"); setRequestProperty("X-Correlation-ID", CorrelationIds.next()); tokens.getAccessToken(false)?.let { setRequestProperty("Authorization", "Bearer $it") }; if (body != null) { doOutput = true; setRequestProperty("Content-Type", "application/json"); outputStream.use { it.write(body.toByteArray()) } } }
        val stream = if (c.responseCode in 200..299) c.inputStream else c.errorStream; val text = stream.bufferedReader().use { it.readText() }; if (c.responseCode !in 200..299) error(text.ifBlank { "HTTP ${c.responseCode}" }); return text
    }
    override suspend fun list(petId: String) = request("GET", "/v1/pets/$petId/reports")
    override suspend fun get(reportId: String) = request("GET", "/v1/reports/$reportId")
    override suspend fun generate(petId: String) = request("POST", "/v1/internal/reports/weekly/generate", "{\"animal_id\":\"$petId\"}")
}

class LocalReportsRepository : ReportsRepository { override suspend fun list(petId: String) = "[]"; override suspend fun get(reportId: String) = "{}"; override suspend fun generate(petId: String) = "{\"generation_status\":\"COMPLETED\"}" }
