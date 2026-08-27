package com.peti.app.analysis

import com.peti.app.media.MediaType

data class ReadyMediaSelection(
    val mediaId: String,
    val mediaType: MediaType,
    val ownerUserId: String,
    val ready: Boolean,
)

class PetiCheckSubmissionValidator(
    private val videoEnabled: Boolean = false,
    private val audioEnabled: Boolean = false,
) {
    fun validate(media: List<ReadyMediaSelection>, context: String?): String? {
        if (media.isEmpty()) return "PETI_CHECK_MEDIA_REQUIRED"
        if (media.size > 5) return "PETI_CHECK_TOO_MANY_MEDIA_ITEMS"
        if (context != null && context.trim().length > 500) return "PETI_CHECK_CONTEXT_TOO_LONG"
        if (media.any { !it.ready }) return "PETI_CHECK_MEDIA_NOT_READY"
        if (media.any { it.mediaType == MediaType.DOCUMENT }) return "PETI_CHECK_MEDIA_UNSUPPORTED"
        if (media.any { it.mediaType == MediaType.VIDEO && !videoEnabled }) return "PETI_CHECK_MEDIA_UNSUPPORTED"
        if (media.any { it.mediaType == MediaType.AUDIO && !audioEnabled }) return "PETI_CHECK_MEDIA_UNSUPPORTED"
        return null
    }
}
