package com.peti.app

import com.peti.app.media.*
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class UploadRecoveryTest {
    @Test fun retriesNetworkAndRefreshesExpiredAuthorization() {
        assertEquals(UploadFailureKind.RETRYABLE_NETWORK, UploadRetryPolicy.classify("network timeout").kind)
        assertEquals(UploadFailureKind.AUTHORIZATION_EXPIRED, UploadRetryPolicy.classify("upload expired").kind)
    }
    @Test fun accountSwitchClearsOnlyCurrentAccountTasks() {
        val source = MediaSource("content://x", MediaType.IMAGE, "image/png", null, 1, null)
        val store = InMemoryUploadTaskStore()
        store.save(MediaUploadTask("a", "user-a", source, MediaUploadState.UPLOADING))
        store.save(MediaUploadTask("b", "user-b", source, MediaUploadState.UPLOADING))
        store.clearAccount("user-a")
        assertTrue(store.pending("user-a").isEmpty())
        assertEquals(1, store.pending("user-b").size)
    }
}
