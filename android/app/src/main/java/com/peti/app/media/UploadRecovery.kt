package com.peti.app.media

import android.content.Context
import android.content.SharedPreferences
import org.json.JSONObject

enum class UploadFailureKind { RETRYABLE_NETWORK, AUTHORIZATION_EXPIRED, PERMANENT_VALIDATION, CANCELED }

data class UploadFailure(val kind: UploadFailureKind, val code: String)

object UploadRetryPolicy {
    fun classify(code: String): UploadFailure = when {
        code.contains("timeout", true) || code.contains("network", true) || code.startsWith("HTTP 5") -> UploadFailure(UploadFailureKind.RETRYABLE_NETWORK, code)
        code.contains("expired", true) || code.contains("401") || code.contains("403") -> UploadFailure(UploadFailureKind.AUTHORIZATION_EXPIRED, code)
        code.contains("cancel", true) -> UploadFailure(UploadFailureKind.CANCELED, code)
        else -> UploadFailure(UploadFailureKind.PERMANENT_VALIDATION, code)
    }
}

class InMemoryUploadTaskStore {
    private val tasks = linkedMapOf<String, MediaUploadTask>()
    fun save(task: MediaUploadTask) { tasks["${task.ownerUserId}:${task.localId}"] = task }
    fun pending(ownerUserId: String) = tasks.values.filter { it.ownerUserId == ownerUserId && it.state !in setOf(MediaUploadState.READY, MediaUploadState.CANCELED) }
    fun clearAccount(ownerUserId: String) { tasks.keys.filter { it.startsWith("$ownerUserId:") }.toList().forEach(tasks::remove) }
}

/** Durable local upload state; bytes remain in the caller-owned content URI. */
class SharedPreferencesUploadTaskStore(context: Context) {
    private val preferences: SharedPreferences =
        context.getSharedPreferences("peti_upload_tasks", Context.MODE_PRIVATE)

    fun save(task: MediaUploadTask) {
        val json = JSONObject()
            .put("localId", task.localId)
            .put("ownerUserId", task.ownerUserId)
            .put("contentUri", task.source.contentUri)
            .put("mediaType", task.source.mediaType.name)
            .put("mimeType", task.source.mimeType)
            .put("displayName", task.source.displayName)
            .put("sizeBytes", task.source.sizeBytes)
            .put("durationMs", task.source.durationMs)
            .put("state", task.state.name)
            .put("mediaId", task.mediaId)
            .put("sessionId", task.sessionId)
            .put("uploadUrl", task.uploadUrl)
            .put("errorCode", task.errorCode)
        preferences.edit().putString(key(task.ownerUserId, task.localId), json.toString()).apply()
    }

    fun pending(ownerUserId: String): List<MediaUploadTask> =
        preferences.all.keys.filter { it.startsWith("$ownerUserId:") }
            .mapNotNull { preferences.getString(it, null)?.let(::decode) }
            .filter { it.state !in setOf(MediaUploadState.READY, MediaUploadState.CANCELED) }

    fun pendingOwners(): Set<String> =
        preferences.all.keys.mapNotNull { it.substringBefore(':').takeIf(String::isNotEmpty) }.toSet()

    fun clearAccount(ownerUserId: String) {
        preferences.edit().also { editor ->
            preferences.all.keys.filter { it.startsWith("$ownerUserId:") }.forEach(editor::remove)
        }.apply()
    }

    private fun decode(raw: String): MediaUploadTask = JSONObject(raw).let { json ->
        MediaUploadTask(
            localId = json.getString("localId"),
            ownerUserId = json.getString("ownerUserId"),
            source = MediaSource(
                json.getString("contentUri"),
                MediaType.valueOf(json.getString("mediaType")),
                json.optString("mimeType").takeIf { it.isNotEmpty() },
                json.optString("displayName").takeIf { it.isNotEmpty() },
                if (json.isNull("sizeBytes")) null else json.getLong("sizeBytes"),
                if (json.isNull("durationMs")) null else json.getLong("durationMs"),
            ),
            state = MediaUploadState.valueOf(json.getString("state")),
            mediaId = json.optString("mediaId").takeIf { it.isNotEmpty() },
            sessionId = json.optString("sessionId").takeIf { it.isNotEmpty() },
            uploadUrl = json.optString("uploadUrl").takeIf { it.isNotEmpty() },
            errorCode = json.optString("errorCode").takeIf { it.isNotEmpty() },
        )
    }

    private fun key(ownerUserId: String, localId: String) = "$ownerUserId:$localId"
}
