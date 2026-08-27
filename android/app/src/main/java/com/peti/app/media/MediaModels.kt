package com.peti.app.media

enum class MediaType { IMAGE, VIDEO, AUDIO, DOCUMENT }
enum class MediaUploadState { DRAFT, SESSION_CREATED, UPLOADING, RETRYING, FINALIZING, READY, FAILED, CANCELED }
data class MediaSource(val contentUri: String, val mediaType: MediaType, val mimeType: String?, val displayName: String?, val sizeBytes: Long?, val durationMs: Long?)
data class MediaUploadTask(
    val localId: String,
    val ownerUserId: String,
    val source: MediaSource,
    val state: MediaUploadState = MediaUploadState.DRAFT,
    val mediaId: String? = null,
    val sessionId: String? = null,
    val uploadUrl: String? = null,
    val uploadHeaders: Map<String, String> = emptyMap(),
    val errorCode: String? = null,
)

interface MediaUploadRepository {
    suspend fun createSession(task: MediaUploadTask): MediaUploadTask
    suspend fun upload(task: MediaUploadTask): MediaUploadTask
    suspend fun finalize(task: MediaUploadTask): MediaUploadTask
}

class FakeMediaUploadRepository : MediaUploadRepository {
    override suspend fun createSession(task: MediaUploadTask) = task.copy(state = MediaUploadState.SESSION_CREATED, mediaId = "fake-media-${task.localId}", sessionId = "fake-session-${task.localId}")
    override suspend fun upload(task: MediaUploadTask) = task.copy(state = MediaUploadState.FINALIZING)
    override suspend fun finalize(task: MediaUploadTask) = task.copy(state = MediaUploadState.READY)
}
