package com.peti.app.media

import android.content.Context
import android.media.MediaRecorder
import androidx.core.content.FileProvider
import java.io.File

/** Small device adapter for user-controlled, short audio observations. */
class AudioCaptureController(private val context: Context) {
    private var recorder: MediaRecorder? = null
    private var file: File? = null
    private var startedAt: Long = 0

    fun start(): Boolean {
        if (recorder != null) return false
        val directory = File(context.cacheDir, "audio").apply { mkdirs() }
        val target = File.createTempFile("peti-audio-", ".m4a", directory)
        return runCatching {
            @Suppress("DEPRECATION")
            MediaRecorder().apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setOutputFile(target.absolutePath)
                prepare()
                start()
            }.also {
                recorder = it
                file = target
                startedAt = System.currentTimeMillis()
            }
        }.onFailure { target.delete() }.isSuccess
    }

    fun stop(): MediaSource? {
        val active = recorder ?: return null
        val target = file
        val duration = (System.currentTimeMillis() - startedAt).coerceAtLeast(0)
        return runCatching {
            active.stop()
            target?.takeIf { it.exists() && it.length() > 0 }?.let {
                MediaSource(
                    FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", it).toString(),
                    MediaType.AUDIO,
                    "audio/mp4",
                    it.name,
                    it.length(),
                    duration,
                )
            }
        }.getOrNull().also {
            runCatching { active.reset() }
            runCatching { active.release() }
            recorder = null
            file = null
            startedAt = 0
            if (it == null) target?.delete()
        }
    }

    fun cancel() {
        recorder?.let { runCatching { it.stop() }; runCatching { it.release() } }
        recorder = null
        file?.delete()
        file = null
        startedAt = 0
    }
}
