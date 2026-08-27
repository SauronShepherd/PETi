package com.peti.app.media

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.peti.app.createAppServices

/**
 * Process-death recovery boundary. The app registers its coordinator before
 * scheduling work; no media bytes or credentials are placed in WorkManager
 * input data.
 */
object MediaUploadWorkerRegistry {
    @Volatile
    var coordinator: MediaUploadCoordinator? = null
}

class MediaUploadWorker(
    appContext: Context,
    params: WorkerParameters,
) : CoroutineWorker(appContext, params) {
    override suspend fun doWork(): Result {
        val localId = inputData.getString(KEY_LOCAL_ID) ?: return Result.failure()
        // WorkManager may recreate the process without MainActivity. Rebuild
        // the app service graph from application context so durable metadata
        // can resume the task; no credentials or media bytes are carried in
        // WorkManager input data.
        val coordinator = MediaUploadWorkerRegistry.coordinator
            ?: runCatching { createAppServices(applicationContext).mediaUpload }.getOrNull()
            ?: return Result.retry()
        return if (coordinator.retry(localId)) Result.success() else Result.retry()
    }

    companion object {
        const val KEY_LOCAL_ID = "local_id"
    }
}
