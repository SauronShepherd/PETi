package com.peti.app.media

import android.content.Context
import androidx.work.Constraints
import androidx.work.Data
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.ExistingWorkPolicy
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class MediaUploadCoordinator(
    private val repository: MediaUploadRepository,
    private val durableStore: SharedPreferencesUploadTaskStore? = null,
    private val appContext: Context? = null,
) {
    private val _tasks = MutableStateFlow<Map<String, MediaUploadTask>>(
        durableStore?.let { store -> store.pendingOwners().flatMap { store.pending(it) }.associateBy(MediaUploadTask::localId) } ?: emptyMap()
    )
    init {
        MediaUploadWorkerRegistry.coordinator = this
        _tasks.value.values
            .filter { shouldResume(it) }
            .forEach { scheduleRetry(it.localId) }
    }
    val tasks: StateFlow<Map<String, MediaUploadTask>> = _tasks.asStateFlow()
    suspend fun enqueue(task: MediaUploadTask) {
        durableStore?.save(task)
        _tasks.value = _tasks.value + (task.localId to task)
        runCatching {
            val session = repository.createSession(task)
            val uploaded = repository.upload(session)
            repository.finalize(uploaded)
        }
            .onSuccess { durableStore?.save(it); _tasks.value = _tasks.value + (task.localId to it) }
            .onFailure {
                val failed = task.copy(state = MediaUploadState.FAILED, errorCode = it.message)
                durableStore?.save(failed)
                _tasks.value = _tasks.value + (task.localId to failed)
                if (UploadRetryPolicy.classify(it.message ?: "upload failed").kind == UploadFailureKind.RETRYABLE_NETWORK) {
                    scheduleRetry(task.localId)
                }
            }
    }
    fun cancel(localId: String) { _tasks.value[localId]?.let { val canceled = it.copy(state = MediaUploadState.CANCELED); durableStore?.save(canceled); _tasks.value = _tasks.value + (localId to canceled) } }
    fun clearAccount(ownerUserId: String) {
        durableStore?.clearAccount(ownerUserId)
        _tasks.value = _tasks.value.filterValues { it.ownerUserId != ownerUserId }
    }

    suspend fun retry(localId: String): Boolean {
        val task = _tasks.value[localId] ?: return false
        enqueue(task.copy(state = MediaUploadState.RETRYING, errorCode = null))
        return _tasks.value[localId]?.state == MediaUploadState.READY
    }

    private fun scheduleRetry(localId: String) {
        val context = appContext ?: return
        val request = OneTimeWorkRequestBuilder<MediaUploadWorker>()
            .setInputData(Data.Builder().putString(MediaUploadWorker.KEY_LOCAL_ID, localId).build())
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .build()
        WorkManager.getInstance(context).enqueueUniqueWork(
            "peti-upload-$localId",
            ExistingWorkPolicy.KEEP,
            request,
        )
    }

    private fun shouldResume(task: MediaUploadTask): Boolean =
        task.state in setOf(
            MediaUploadState.DRAFT,
            MediaUploadState.SESSION_CREATED,
            MediaUploadState.UPLOADING,
            MediaUploadState.RETRYING,
            MediaUploadState.FINALIZING,
        ) || (
            task.state == MediaUploadState.FAILED &&
                UploadRetryPolicy.classify(task.errorCode ?: "").kind == UploadFailureKind.RETRYABLE_NETWORK
            )
}
