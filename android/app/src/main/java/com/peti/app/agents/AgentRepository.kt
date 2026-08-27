package com.peti.app.agents

import com.peti.app.auth.AccessTokenProvider
import com.peti.app.auth.CorrelationIds
import java.net.HttpURLConnection
import java.net.URL

interface AgentRepository { suspend fun createSession(petId: String): String; suspend fun createRun(petId: String, goal: String, sessionId: String?): String; suspend fun getRun(runId: String): String; suspend fun cancelRun(runId: String): String }

class ApiAgentRepository(private val baseUrl: String, private val tokens: AccessTokenProvider) : AgentRepository {
    private suspend fun request(method: String, path: String, body: String? = null): String {
        val connection = (URL(baseUrl + path).openConnection() as HttpURLConnection).apply { requestMethod = method; connectTimeout = 10_000; readTimeout = 10_000; setRequestProperty("Accept", "application/json"); setRequestProperty("X-Correlation-ID", CorrelationIds.next()); tokens.getAccessToken(false)?.let { setRequestProperty("Authorization", "Bearer $it") }; if (body != null) { doOutput = true; setRequestProperty("Content-Type", "application/json"); outputStream.use { it.write(body.toByteArray()) } } }
        val stream = if (connection.responseCode in 200..299) connection.inputStream else connection.errorStream
        val response = stream.bufferedReader().use { it.readText() }; if (connection.responseCode !in 200..299) error(response.ifBlank { "HTTP ${connection.responseCode}" }); return response
    }
    override suspend fun createSession(petId: String) = request("POST", "/v1/dogs/$petId/agent-sessions")
    override suspend fun createRun(petId: String, goal: String, sessionId: String?) = request("POST", "/v1/dogs/$petId/agent-runs", "{\"goal\":\"${goal.replace("\\", "\\\\").replace("\"", "\\\"")}\"${sessionId?.let { ",\"session_id\":\"$it\"" } ?: ""}}")
    override suspend fun getRun(runId: String) = request("GET", "/v1/agent-runs/$runId")
    override suspend fun cancelRun(runId: String) = request("POST", "/v1/agent-runs/$runId/cancel")
}

class LocalAgentRepository : AgentRepository { override suspend fun createSession(petId: String) = "{\"status\":\"ACTIVE\"}"; override suspend fun createRun(petId: String, goal: String, sessionId: String?) = "{\"state\":\"QUEUED\"}"; override suspend fun getRun(runId: String) = "{\"state\":\"QUEUED\"}"; override suspend fun cancelRun(runId: String) = "{\"state\":\"CANCELLED\"}" }
