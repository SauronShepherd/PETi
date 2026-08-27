package com.peti.app

import com.peti.app.media.*
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Test

class MediaUploadCoordinatorTest {
    @Test fun fakeUploadReachesReadyWithoutSemanticProcessing() = runBlocking {
        val source=MediaSource("content://fixture/image", MediaType.IMAGE, "image/png", "fixture.png", 3, null)
        val coordinator=MediaUploadCoordinator(FakeMediaUploadRepository())
        coordinator.enqueue(MediaUploadTask("local-1", "user-1", source))
        assertEquals(MediaUploadState.READY, coordinator.tasks.value["local-1"]?.state)
    }
    @Test fun pickerRejectsWrongMediaType() = runBlocking {
        val source=MediaSource("content://fixture/image", MediaType.IMAGE, "image/png", null, 3, null)
        assertEquals(null, FakeMediaSourcePicker(source).pick(MediaType.VIDEO))
    }

    @Test fun readyAudioTaskRetainsAudioTypeForSubmission() = runBlocking {
        val source = MediaSource("content://fixture/audio", MediaType.AUDIO, "audio/mp4", "fixture.m4a", 9, 1200)
        val coordinator = MediaUploadCoordinator(FakeMediaUploadRepository())
        coordinator.enqueue(MediaUploadTask("audio-1", "user-1", source))
        val ready = coordinator.tasks.value["audio-1"]
        assertEquals(MediaUploadState.READY, ready?.state)
        assertEquals(MediaType.AUDIO, ready?.source?.mediaType)
    }
}
