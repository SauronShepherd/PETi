package com.peti.app

import com.peti.app.analysis.PetiCheckSubmissionValidator
import com.peti.app.analysis.ReadyMediaSelection
import com.peti.app.media.MediaType
import org.junit.Assert.assertEquals
import org.junit.Test

class PetiCheckSubmissionTest {
    private val image = ReadyMediaSelection("m1", MediaType.IMAGE, "u1", true)

    @Test fun requiresReadyMedia() {
        assertEquals("PETI_CHECK_MEDIA_REQUIRED", PetiCheckSubmissionValidator().validate(emptyList(), null))
        assertEquals("PETI_CHECK_MEDIA_NOT_READY", PetiCheckSubmissionValidator().validate(listOf(image.copy(ready = false)), null))
    }

    @Test fun videoIsFailClosedByDefault() {
        val video = image.copy(mediaId = "m2", mediaType = MediaType.VIDEO)
        assertEquals("PETI_CHECK_MEDIA_UNSUPPORTED", PetiCheckSubmissionValidator().validate(listOf(video), null))
    }

    @Test fun validatesBoundedContextAndCount() {
        assertEquals("PETI_CHECK_CONTEXT_TOO_LONG", PetiCheckSubmissionValidator().validate(listOf(image), "x".repeat(501)))
        assertEquals("PETI_CHECK_TOO_MANY_MEDIA_ITEMS", PetiCheckSubmissionValidator().validate(List(6) { image }, null))
    }
}
