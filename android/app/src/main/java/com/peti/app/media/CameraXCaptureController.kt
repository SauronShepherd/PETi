package com.peti.app.media

import android.content.Context
import android.net.Uri
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.video.FileOutputOptions
import androidx.camera.video.Quality
import androidx.camera.video.QualitySelector
import androidx.camera.video.Recorder
import androidx.camera.video.Recording
import androidx.camera.video.VideoCapture
import androidx.camera.video.VideoRecordEvent
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner
import java.io.File
import java.util.UUID
import java.util.concurrent.Executor

/** Embedded CameraX capture boundary; UI owns preview and permission state. */
class CameraXCaptureController(
    private val context: Context,
    private val lifecycleOwner: LifecycleOwner,
    private val executor: Executor = ContextCompat.getMainExecutor(context),
) {
    private var imageCapture: ImageCapture? = null
    private var videoCapture: VideoCapture<Recorder>? = null
    private var recording: Recording? = null
    private var provider: ProcessCameraProvider? = null

    fun bind(previewView: PreviewView, onReady: () -> Unit, onError: () -> Unit = {}) {
        val future = ProcessCameraProvider.getInstance(context)
        future.addListener({
            runCatching {
                val cameraProvider = future.get()
                provider = cameraProvider
                val preview = androidx.camera.core.Preview.Builder().build().also {
                    it.surfaceProvider = previewView.surfaceProvider
                }
                imageCapture = ImageCapture.Builder().build()
                videoCapture = VideoCapture.withOutput(
                    Recorder.Builder()
                        .setQualitySelector(QualitySelector.from(Quality.FHD))
                        .build(),
                )
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    lifecycleOwner,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    imageCapture,
                    videoCapture,
                )
            }.onSuccess { onReady() }.onFailure { onError() }
        }, executor)
    }

    fun capturePhoto(onComplete: (MediaSource?) -> Unit) {
        val capture = imageCapture ?: error("CAMERAX_NOT_BOUND")
        val file = outputFile(".jpg")
        capture.takePicture(
            ImageCapture.OutputFileOptions.Builder(file).build(),
            executor,
            object : ImageCapture.OnImageSavedCallback {
                override fun onError(exception: ImageCaptureException) {
                    file.delete(); onComplete(null)
                }

                override fun onImageSaved(outputFileResults: ImageCapture.OutputFileResults) {
                    onComplete(MediaSource(Uri.fromFile(file).toString(), MediaType.IMAGE, "image/jpeg", file.name, file.length(), null))
                }
            },
        )
    }

    fun startVideo(onComplete: (MediaSource?) -> Unit) {
        val capture = videoCapture ?: error("CAMERAX_NOT_BOUND")
        val file = outputFile(".mp4")
        recording = capture.output
            .prepareRecording(context, FileOutputOptions.Builder(file).build())
            .start(executor) { event ->
                if (event is VideoRecordEvent.Finalize) {
                    recording = null
                    if (event.hasError()) { file.delete(); onComplete(null) }
                    else onComplete(MediaSource(Uri.fromFile(file).toString(), MediaType.VIDEO, "video/mp4", file.name, file.length(), null))
                }
            }
    }

    fun stopVideo() { recording?.stop() }

    fun release() {
        recording?.close(); recording = null
        provider?.unbindAll()
        provider = null
    }

    private fun outputFile(extension: String): File = File(
        File(context.cacheDir, "camera-x").apply { mkdirs() },
        "capture-${UUID.randomUUID()}$extension",
    )
}
