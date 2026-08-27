package com.peti.app.media

/** UI-neutral contracts used by Photo Picker, SAF, and CameraX adapters. */
interface MediaSourcePicker {
    suspend fun pick(type: MediaType): MediaSource?
}

interface CameraCaptureProvider {
    suspend fun capturePhoto(): MediaSource?
    suspend fun captureVideo(maxDurationMs: Long): MediaSource?
}

class FakeMediaSourcePicker(private val source: MediaSource? = null) : MediaSourcePicker {
    override suspend fun pick(type: MediaType): MediaSource? = source?.takeIf { it.mediaType == type }
}

class FakeCameraCaptureProvider(private val source: MediaSource? = null) : CameraCaptureProvider {
    override suspend fun capturePhoto(): MediaSource? = source?.takeIf { it.mediaType == MediaType.IMAGE }
    override suspend fun captureVideo(maxDurationMs: Long): MediaSource? = source?.takeIf { it.mediaType == MediaType.VIDEO && (it.durationMs ?: 0) <= maxDurationMs }
}
