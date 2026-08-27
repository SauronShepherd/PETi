package com.peti.app.media

import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import android.Manifest
import android.content.pm.PackageManager

@Composable
fun AudioCaptureDialog(onCaptured: (MediaSource) -> Unit, onDismiss: () -> Unit) {
    val context = LocalContext.current
    val controller = remember(context) { AudioCaptureController(context) }
    var recording by remember { mutableStateOf(false) }
    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        if (granted) recording = controller.start()
        else onDismiss()
    }
    DisposableEffect(Unit) { onDispose { controller.cancel() } }
    AlertDialog(
        onDismissRequest = { controller.cancel(); onDismiss() },
        title = { Text("Record observation") },
        text = { Text(if (recording) "Recording audio… stop when finished." else "Record a short voice observation for PETi Check.") },
        confirmButton = {
            Button(onClick = {
                if (recording) controller.stop()?.let { onCaptured(it) } ?: onDismiss()
                else if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                    recording = controller.start()
                } else {
                    permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                }
            }) { Text(if (recording) "Stop and use" else "Start recording") }
        },
        dismissButton = { Button(onClick = { controller.cancel(); onDismiss() }) { Text("Cancel") } },
    )
}
