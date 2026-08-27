package com.peti.app.future

import com.peti.app.auth.AccessTokenProvider
import com.peti.app.auth.CorrelationIds
import java.net.HttpURLConnection
import java.net.URL

interface FutureRepository { suspend fun search(query: String, petId: String?): String; suspend fun export(petId: String): String; suspend fun createThread(petId: String): String; suspend fun message(threadId: String, text: String): String }
class ApiFutureRepository(private val baseUrl: String, private val tokens: AccessTokenProvider) : FutureRepository {
    private suspend fun request(method: String, path: String, body: String? = null): String { val c = (URL(baseUrl + path).openConnection() as HttpURLConnection).apply { requestMethod = method; connectTimeout = 10_000; readTimeout = 10_000; setRequestProperty("Accept", "application/json"); setRequestProperty("X-Correlation-ID", CorrelationIds.next()); tokens.getAccessToken(false)?.let { setRequestProperty("Authorization", "Bearer $it") }; if (body != null) { doOutput = true; setRequestProperty("Content-Type", "application/json"); outputStream.use { it.write(body.toByteArray()) } } }; val stream = if (c.responseCode in 200..299) c.inputStream else c.errorStream; val text = stream.bufferedReader().use { it.readText() }; if (c.responseCode !in 200..299) error(text.ifBlank { "HTTP ${c.responseCode}" }); return text }
    override suspend fun search(query: String, petId: String?) = request("POST", "/v1/search", "{\"query\":\"$query\"${petId?.let { ",\"pet_id\":\"$it\"" } ?: ""}}")
    override suspend fun export(petId: String) = request("POST", "/v1/pets/$petId/exports")
    override suspend fun createThread(petId: String) = request("POST", "/v1/pets/$petId/assistant/threads", "{\"title\":\"Pet history\"}")
    override suspend fun message(threadId: String, text: String) = request("POST", "/v1/assistant/threads/$threadId/messages", "{\"text\":\"$text\"}")
}
class LocalFutureRepository : FutureRepository { override suspend fun search(query: String, petId: String?) = "{\"results\":[]}"; override suspend fun export(petId: String) = "{\"status\":\"READY\"}"; override suspend fun createThread(petId: String) = "{\"status\":\"CREATED\"}"; override suspend fun message(threadId: String, text: String) = "{\"grounding_status\":\"NO_MATCHING_SOURCE\"}" }
