package com.peti.app.media

import android.content.Context
import android.net.Uri
import androidx.core.content.FileProvider
import java.io.File
import java.util.UUID

/** Creates app-owned output destinations for ACTION_IMAGE/VIDEO_CAPTURE. */
object AndroidCameraCapture {
    data class PendingCapture(val uri: Uri, val mediaType: MediaType, val mimeType: String, val file: File)

    fun create(context: Context, mediaType: MediaType): PendingCapture {
        require(mediaType == MediaType.IMAGE || mediaType == MediaType.VIDEO)
        val extension = if (mediaType == MediaType.IMAGE) ".jpg" else ".mp4"
        val mime = if (mediaType == MediaType.IMAGE) "image/jpeg" else "video/mp4"
        val directory = File(context.cacheDir, "camera").apply { mkdirs() }
        val file = File(directory, "capture-${UUID.randomUUID()}$extension")
        val authority = "${context.packageName}.fileprovider"
        return PendingCapture(FileProvider.getUriForFile(context, authority, file), mediaType, mime, file)
    }
}
