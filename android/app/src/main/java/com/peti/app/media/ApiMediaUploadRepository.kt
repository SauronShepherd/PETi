package com.peti.app.media

import android.net.Uri
import com.peti.app.auth.AccessTokenProvider
import com.peti.app.auth.CorrelationIds
import java.net.HttpURLConnection
import java.net.URL
import android.content.ContentResolver

/** Authenticated media API adapter; raw storage capabilities are never persisted or logged. */
class ApiMediaUploadRepository(
    private val baseUrl: String,
    private val tokens: AccessTokenProvider,
    private val contentResolver: ContentResolver,
) : MediaUploadRepository {
    private suspend fun request(method: String, path: String, body: String? = null, headers: Map<String, String> = emptyMap()): String {
        val connection = (URL(baseUrl + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method; connectTimeout = 10_000; readTimeout = 10_000; setRequestProperty("Accept", "application/json"); setRequestProperty("X-Correlation-ID", CorrelationIds.next())
            tokens.getAccessToken(false)?.let { setRequestProperty("Authorization", "Bearer $it") }
            headers.forEach { (key, value) -> setRequestProperty(key, value) }
            if (body != null) { doOutput = true; setRequestProperty("Content-Type", "application/json"); outputStream.use { it.write(body.toByteArray()) } }
        }
        val response = (if (connection.responseCode in 200..299) connection.inputStream else connection.errorStream).bufferedReader().readText()
        if (connection.responseCode !in 200..299) error(response.ifBlank { "HTTP ${connection.responseCode}" })
        return response
    }
    override suspend fun createSession(task: MediaUploadTask): MediaUploadTask {
        val source = task.source
        val isDocument = source.mediaType == MediaType.DOCUMENT
        val purpose = if (isDocument) "DOCUMENT_SOURCE" else "TEMPORARY_CAPTURE"
        val retention = if (isDocument) "CLINICAL_DOCUMENT" else "TRANSIENT_ANALYSIS"
        val body = "{\"media_type\":\"${source.mediaType}\",\"purpose\":\"$purpose\",\"mime_type\":\"${source.mimeType ?: "application/octet-stream"}\",\"size_bytes\":${source.sizeBytes ?: "null"},\"retention_class\":\"$retention\"}"
        val response = request("POST", "/v1/media/upload-sessions", body, mapOf("Idempotency-Key" to task.localId))
        val uploadUrl = response.string("upload_url")
        val contentType = source.mimeType ?: "application/octet-stream"
        return task.copy(
            state = MediaUploadState.SESSION_CREATED,
            mediaId = response.string("id"),
            sessionId = response.string("upload_session_id"),
            uploadUrl = uploadUrl,
            uploadHeaders = mapOf("Content-Type" to contentType),
        )
    }
    override suspend fun upload(task: MediaUploadTask): MediaUploadTask {
        val uploadUrl = task.uploadUrl ?: error("missing upload authorization")
        val input = contentResolver.openInputStream(Uri.parse(task.source.contentUri))
            ?: error("media source is unavailable")
        input.use { stream ->
            val connection = (URL(uploadUrl).openConnection() as HttpURLConnection).apply {
                requestMethod = "PUT"
                connectTimeout = 15_000
                readTimeout = 60_000
                doOutput = true
                task.source.sizeBytes?.let { setFixedLengthStreamingMode(it) }
                    ?: setChunkedStreamingMode(32 * 1024)
                task.uploadHeaders.forEach { (key, value) -> setRequestProperty(key, value) }
            }
            connection.outputStream.use { output -> stream.copyTo(output) }
            if (connection.responseCode !in 200..299) {
                error("media upload failed: HTTP ${connection.responseCode}")
            }
        }
        return task.copy(state = MediaUploadState.FINALIZING)
    }
    override suspend fun finalize(task: MediaUploadTask): MediaUploadTask {
        val response = request("POST", "/v1/media/${task.mediaId}/finalize", headers = mapOf("Upload-Session-Id" to (task.sessionId ?: error("missing session"))))
        return task.copy(state = MediaUploadState.READY, mediaId = response.string("id"))
    }
    private fun String.string(key: String) = Regex("\\\"$key\\\":\\\"([^\\\"]+)\\\"").find(this)?.groupValues?.get(1) ?: error("missing $key")
}
