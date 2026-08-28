package com.peti.app.media

import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView

@Composable
fun CameraXCaptureDialog(
    mediaType: MediaType,
    onCaptured: (MediaSource) -> Unit,
    onDismiss: () -> Unit,
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val controller = remember(context, lifecycleOwner) { CameraXCaptureController(context, lifecycleOwner) }
    val previewView = remember(context) { PreviewView(context) }
    var ready by remember { mutableStateOf(false) }
    var recording by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf(false) }

    LaunchedEffect(controller) {
        controller.bind(previewView, onReady = { ready = true }, onError = { error = true })
    }
    DisposableEffect(controller) { onDispose { controller.release() } }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (mediaType == MediaType.IMAGE) "Hacer una foto" else "Grabar vídeo") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                AndroidView(
                    factory = { previewView },
                    modifier = Modifier.fillMaxWidth().height(280.dp),
                )
                if (error) Text("Cámara no disponible")
            }
        },
        confirmButton = {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (ready && mediaType == MediaType.IMAGE) {
                    Button(onClick = { controller.capturePhoto { source -> if (source != null) onCaptured(source) } }) { Text("Capturar") }
                }
                if (ready && mediaType == MediaType.VIDEO) {
                    Button(onClick = {
                        if (recording) controller.stopVideo() else controller.startVideo { source -> recording = false; if (source != null) onCaptured(source) }
                        recording = !recording
                    }) { Text(if (recording) "Detener" else "Grabar") }
                }
                Button(onClick = onDismiss) { Text("Cancelar") }
            }
        },
    )
}
