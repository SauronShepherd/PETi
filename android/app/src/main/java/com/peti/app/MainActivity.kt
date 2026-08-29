package com.peti.app

import android.os.Bundle
import android.Manifest
import android.content.pm.PackageManager
import android.content.Intent
import android.net.Uri
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.compose.setContent
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.ContextCompat
import androidx.compose.ui.unit.dp
import androidx.compose.ui.graphics.Color
import androidx.lifecycle.viewmodel.compose.viewModel
import com.peti.app.auth.*
import com.peti.app.pets.*
import com.peti.app.funding.*
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay
import com.peti.app.analysis.*
import com.peti.app.media.*
import com.peti.app.phase6.Phase6Panel
import com.peti.app.phase6.CareDeepLink
import com.peti.app.phase6.PetiMessagingRegistration
import com.peti.app.records.RecordsPanel
import com.peti.app.specialists.SpecialistPanel
import com.peti.app.reports.ReportsPanel
import com.peti.app.future.FuturePanel
import java.util.UUID

class MainActivity : ComponentActivity() {
    private val pendingOccurrence = mutableStateOf<String?>(null)
    override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); pendingOccurrence.value = CareDeepLink.occurrenceId(intent?.data?.toString()); setContent { PetiTheme { Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) { PetiApp(this@MainActivity, pendingOccurrence.value) } } } }
    override fun onNewIntent(intent: Intent) { super.onNewIntent(intent); setIntent(intent); pendingOccurrence.value = CareDeepLink.occurrenceId(intent.data?.toString()) }
}

@Composable
private fun PetiApp(activity: ComponentActivity, pendingOccurrenceId: String? = null) {
    val scope = rememberCoroutineScope(); val context = LocalContext.current; val services = remember { createAppServices(context) }; val auth = services.auth; val pets = services.pets; val species = services.species
    var authState by remember { mutableStateOf<AuthState>(auth.authState.value) }; var name by remember { mutableStateOf("") }; var editName by remember { mutableStateOf("") }; var email by rememberSaveable { mutableStateOf("") }; var password by rememberSaveable { mutableStateOf("") }
    val petViewModel: PetViewModel = viewModel(factory = object : androidx.lifecycle.ViewModelProvider.Factory { override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T = PetViewModel(pets, species, PersistentSelectedPetStore(context)) as T }); val state by petViewModel.state.collectAsState()
    LaunchedEffect(authState) {
        val restored = authState as? AuthState.Authenticated ?: return@LaunchedEffect
        petViewModel.load(restored.userId)
    }
    val fundingViewModel: FundingViewModel = viewModel(factory = object : androidx.lifecycle.ViewModelProvider.Factory { override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T = FundingViewModel(services.funding, object : RewardedAdGateway { override suspend fun show(intent: RewardIntent) = false }) as T })
    val fundingState by fundingViewModel.state.collectAsState()
    var activeSection by rememberSaveable { mutableStateOf("HOME") }
    Column(Modifier.fillMaxSize()) {
    Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("PETi", style = MaterialTheme.typography.displaySmall, fontWeight = androidx.compose.ui.text.font.FontWeight.ExtraBold, color = MaterialTheme.colorScheme.primary)
        Text("Cuida mejor de tu mascota. ♥", color = MaterialTheme.colorScheme.onSurfaceVariant)
        pendingOccurrenceId?.let { Text("Recordatorio abierto: $it", modifier = Modifier.testTag("careDeepLinkOccurrence")) }
        when (val current = authState) {
            AuthState.SignedOut -> Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), elevation = CardDefaults.cardElevation(2.dp)) {
                Column(Modifier.fillMaxWidth().padding(24.dp), verticalArrangement = Arrangement.spacedBy(14.dp), horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally) {
                    Text("Tu compañero. Nuestro cuidado.", style = MaterialTheme.typography.headlineSmall, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                    Text("Organiza el bienestar de tu mascota y toma decisiones con información clara.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                    OutlinedTextField(email, { email = it }, label = { Text("Correo electrónico") }, modifier = Modifier.fillMaxWidth().testTag("email"), singleLine = true)
                    OutlinedTextField(password, { password = it }, label = { Text("Contraseña") }, modifier = Modifier.fillMaxWidth().testTag("password"), singleLine = true, visualTransformation = androidx.compose.ui.text.input.PasswordVisualTransformation())
                    Button(modifier = Modifier.fillMaxWidth().testTag("signIn"), onClick = { scope.launch { auth.signIn(email, password); authState = auth.authState.value; if (authState is AuthState.Authenticated) petViewModel.load((authState as AuthState.Authenticated).userId) } }, shape = MaterialTheme.shapes.medium) { Text("Iniciar sesión") }
                    if (authState is AuthState.AuthError) Text((authState as AuthState.AuthError).message, color = MaterialTheme.colorScheme.error, modifier = Modifier.testTag("authError"))
                }
            }
            is AuthState.Authenticated -> {
                LaunchedEffect(current.userId) { PetiMessagingRegistration.registerCurrent(context) }
                state.selected?.takeIf { activeSection == "HOME" }?.let { selected ->
                    PetiDashboard(selected, onScan = { activeSection = "SCAN" }, onHistory = { activeSection = "HISTORY" }, modifier = Modifier.testTag("homeDashboard"))
                }
                if (activeSection != "HOME" || state.selected == null) {
                    Text("Mis mascotas", style = MaterialTheme.typography.titleLarge, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold)
                }
                if (state.pets.isEmpty() && !state.loading) Text("Aún no has añadido ninguna mascota.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                if (activeSection != "HOME" || state.selected == null) Column(verticalArrangement = Arrangement.spacedBy(10.dp)) { state.pets.forEach { pet ->
                    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), elevation = CardDefaults.cardElevation(1.dp), modifier = Modifier.fillMaxWidth().testTag("pet-${pet.id}").semantics { role = Role.Button; contentDescription = "Select ${pet.displayName}, ${pet.species}" }.clickable { petViewModel.select(current.userId, pet); editName = pet.displayName }) {
                        Row(Modifier.padding(14.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                            Surface(shape = androidx.compose.foundation.shape.CircleShape, color = Color(0xFFFFD8D0), modifier = Modifier.size(58.dp)) { Box(contentAlignment = androidx.compose.ui.Alignment.Center) { Text("", style = MaterialTheme.typography.headlineSmall) } }
                            Spacer(Modifier.width(12.dp))
                            Column(Modifier.weight(1f)) { Text(pet.displayName, style = MaterialTheme.typography.titleMedium, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold); Text(pet.species, color = MaterialTheme.colorScheme.onSurfaceVariant); Text(if (pet.profileComplete) "Perfil completo" else "Completar perfil", color = if (pet.profileComplete) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.secondary) }
                            Text("›", style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.primary)
                        }
                    }
                } }
                if (activeSection != "HOME" || state.selected == null) Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFEAF8F6)), elevation = CardDefaults.cardElevation(1.dp), modifier = Modifier.fillMaxWidth().testTag("addPetCard")) {
                    Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text("Añade un nuevo miembro", style = MaterialTheme.typography.titleMedium, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold)
                        Text("Crea su perfil en pocos pasos y organiza mejor sus cuidados.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        OutlinedTextField(name, { name = it }, label = { Text("Nombre de tu mascota") }, modifier = Modifier.fillMaxWidth().testTag("petName"), singleLine = true)
                        Button(modifier = Modifier.fillMaxWidth().testTag("createPet"), onClick = { if (name.isNotBlank()) { petViewModel.create(name, current.userId); name = "" } }, shape = MaterialTheme.shapes.medium) { Text("Continuar") }
                    }
                }
                OutlinedButton(onClick = { scope.launch { services.mediaUpload.clearAccount(current.userId); services.records.clearLocalAccount(); auth.signOut(); authState = AuthState.SignedOut } }, modifier = Modifier.fillMaxWidth()) { Text("Cerrar sesión") }
                if (activeSection == "PROFILE") state.selected?.let { selected ->
                    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), elevation = CardDefaults.cardElevation(1.dp), modifier = Modifier.fillMaxWidth().testTag("profileCard")) {
                        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            Text("Perfil de ${selected.displayName}", style = MaterialTheme.typography.titleLarge, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold)
                            Text("Mantén sus datos organizados para personalizar su cuidado.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                            OutlinedTextField(editName, { editName = it }, label = { Text("Nombre") }, modifier = Modifier.fillMaxWidth())
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { Button(onClick = { petViewModel.update(editName) }) { Text("Guardar cambios") }; OutlinedButton(onClick = { petViewModel.deleteSelected(current.userId) }) { Text("Eliminar") } }
                        }
                    }
                }
                state.selected?.takeIf { activeSection != "HOME" }?.let { selected ->
                    if (activeSection == "HOME" || activeSection == "HISTORY") Phase6Panel(services.phase6, selected.id, pendingOccurrenceId, Modifier.testTag("phase6Panel"))
                    if (activeSection == "HISTORY") RecordsPanel(services.records, selected.id, Modifier.testTag("recordsPanel")) { readUrl ->
                        runCatching { activity.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(readUrl))) }
                            .onFailure { /* Keep the short-lived URL out of app state if no viewer is installed. */ }
                    }
                    if (activeSection == "SCAN") SpecialistPanel(services.specialists, fundingViewModel, selected.id, Modifier.testTag("specialistPanel"))
                    if (activeSection == "HISTORY") ReportsPanel(services.reports, selected.id, Modifier.testTag("reportsPanel"))
                    if (activeSection == "PROFILE") FuturePanel(services.future, selected.id, Modifier.testTag("futurePanel"))
                    if (activeSection == "SCAN") {
                    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), elevation = CardDefaults.cardElevation(2.dp), modifier = Modifier.fillMaxWidth().testTag("petiCheckCaptureCard")) {
                    Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    var checkState by remember(current.userId, selected.id) { mutableStateOf<AnalysisJob?>(null) }
                    var activeJobId by rememberSaveable(current.userId, selected.id) { mutableStateOf<String?>(null) }
                    var checkError by remember(current.userId, selected.id) { mutableStateOf<String?>(null) }
                    var checkHistory by remember(current.userId, selected.id) { mutableStateOf<List<AnalysisJob>>(emptyList()) }
                    LaunchedEffect(selected.id) { fundingViewModel.request(OperationType.PETI_CHECK) }
                    LaunchedEffect(activeJobId, selected.id) {
                        val jobId = activeJobId ?: return@LaunchedEffect
                        if (checkState?.id != jobId) {
                            runCatching { services.analysis.get(jobId) }
                                .onSuccess { restored -> checkState = restored }
                                .onFailure { checkError = "No se pudo recuperar este análisis" }
                        }
                    }
                    if (activeSection == "SCAN") Text("PETi Check", style = MaterialTheme.typography.titleMedium)
                    Text("Registra lo que estás observando con una foto, vídeo o audio. PETi Check no es un diagnóstico.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                    var selectedMedia by remember(current.userId, selected.id) { mutableStateOf(listOf<ReadyMediaSelection>()) }
                    var uploadedDocumentId by remember(current.userId, selected.id) { mutableStateOf<String?>(null) }
                    var recordStatus by remember(current.userId, selected.id) { mutableStateOf<String?>(null) }
                    val uploadTasks by services.mediaUpload.tasks.collectAsState()
                    val mediaPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
                        if (uri != null) {
                            val resolver = context.contentResolver
                            val mimeType = resolver.getType(uri) ?: "image/jpeg"
                            val size = resolver.openAssetFileDescriptor(uri, "r")?.use { it.length.takeIf { length -> length >= 0 } }
                            val localId = UUID.randomUUID().toString()
                            scope.launch {
                                services.mediaUpload.enqueue(
                                    MediaUploadTask(
                                        localId = localId,
                                        ownerUserId = current.userId,
                                        source = MediaSource(uri.toString(), MediaType.IMAGE, mimeType, null, size, null),
                                    ),
                                )
                            }
                        }
                    }
                    var pendingCameraCapture by remember(current.userId, selected.id) { mutableStateOf<AndroidCameraCapture.PendingCapture?>(null) }
                    var pendingCameraKind by remember(current.userId, selected.id) { mutableStateOf<MediaType?>(null) }
                    var cameraXCaptureType by remember(current.userId, selected.id) { mutableStateOf<MediaType?>(null) }
                    var audioCaptureOpen by remember(current.userId, selected.id) { mutableStateOf(false) }
                    val cameraPhotoLauncher = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { saved ->
                        val capture = pendingCameraCapture
                        pendingCameraCapture = null
                        pendingCameraKind = null
                        if (saved && capture != null) {
                            scope.launch {
                                services.mediaUpload.enqueue(
                                    MediaUploadTask(
                                        localId = UUID.randomUUID().toString(),
                                        ownerUserId = current.userId,
                                        source = MediaSource(capture.uri.toString(), MediaType.IMAGE, capture.mimeType, capture.file.name, capture.file.length(), null),
                                    ),
                                )
                            }
                        } else if (capture != null) {
                            capture.file.delete()
                        }
                    }
                    val cameraVideoLauncher = rememberLauncherForActivityResult(ActivityResultContracts.CaptureVideo()) { saved ->
                        val capture = pendingCameraCapture
                        pendingCameraCapture = null
                        pendingCameraKind = null
                        if (saved && capture != null) {
                            scope.launch {
                                services.mediaUpload.enqueue(
                                    MediaUploadTask(
                                        localId = UUID.randomUUID().toString(),
                                        ownerUserId = current.userId,
                                        source = MediaSource(capture.uri.toString(), MediaType.VIDEO, capture.mimeType, capture.file.name, capture.file.length(), null),
                                    ),
                                )
                            }
                        } else if (capture != null) {
                            capture.file.delete()
                        }
                    }
                    val cameraPermissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
                        val capture = pendingCameraCapture
                        if (!granted && capture != null) {
                            capture.file.delete(); pendingCameraCapture = null; pendingCameraKind = null
                        } else if (granted && capture != null) {
                            if (pendingCameraKind == MediaType.IMAGE) cameraPhotoLauncher.launch(capture.uri) else cameraVideoLauncher.launch(capture.uri)
                        }
                    }
                    fun launchCameraCapture(capture: AndroidCameraCapture.PendingCapture) {
                        pendingCameraCapture = capture
                        pendingCameraKind = capture.mediaType
                        if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                            if (capture.mediaType == MediaType.IMAGE) cameraPhotoLauncher.launch(capture.uri) else cameraVideoLauncher.launch(capture.uri)
                        } else cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
                    }
                    val documentPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
                        if (uri != null) {
                            val resolver = context.contentResolver
                            val mimeType = resolver.getType(uri) ?: "application/pdf"
                            if (mimeType in setOf("application/pdf", "image/jpeg", "image/png")) {
                                val size = resolver.openAssetFileDescriptor(uri, "r")?.use { it.length.takeIf { length -> length >= 0 } }
                                scope.launch { services.mediaUpload.enqueue(MediaUploadTask(UUID.randomUUID().toString(), current.userId, MediaSource(uri.toString(), MediaType.DOCUMENT, mimeType, null, size, null))) }
                            } else recordStatus = "Choose a PDF, JPEG, or PNG veterinary document"
                        }
                    }
                    LaunchedEffect(uploadTasks, current.userId) {
                        val ready = uploadTasks.values.firstOrNull { it.ownerUserId == current.userId && it.state == MediaUploadState.READY && it.mediaId != null }
                        if (ready != null) {
                            selectedMedia = listOf(
                                ReadyMediaSelection(ready.mediaId!!, ready.source.mediaType, current.userId, true),
                            )
                        }
                        uploadedDocumentId = uploadTasks.values.firstOrNull { it.ownerUserId == current.userId && it.source.mediaType == MediaType.DOCUMENT && it.state == MediaUploadState.READY && it.mediaId != null }?.mediaId
                    }
                    val validator = remember { PetiCheckSubmissionValidator() }
                    var userContext by remember(current.userId, selected.id) { mutableStateOf("") }
                    cameraXCaptureType?.let { captureType ->
                        CameraXCaptureDialog(
                            mediaType = captureType,
                            onCaptured = { source ->
                                cameraXCaptureType = null
                                scope.launch {
                                    services.mediaUpload.enqueue(
                                        MediaUploadTask(UUID.randomUUID().toString(), current.userId, source),
                                    )
                                }
                            },
                            onDismiss = { cameraXCaptureType = null },
                        )
                    }
                    if (audioCaptureOpen) {
                        AudioCaptureDialog(
                            onCaptured = { source ->
                                audioCaptureOpen = false
                                scope.launch { services.mediaUpload.enqueue(MediaUploadTask(UUID.randomUUID().toString(), current.userId, source)) }
                            },
                            onDismiss = { audioCaptureOpen = false },
                        )
                    }
                    Text("¿Qué quieres observar hoy?", style = MaterialTheme.typography.titleLarge, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold, color = Color(0xFF173E43))
                    PetiCaptureOption("Foto", "Detecta detalles visibles en una imagen.", "◉", Color(0xFFE2F7F4), Modifier.testTag("petiCheckMedia")) { mediaPicker.launch("image/*") }
                    PetiCaptureOption("Cámara", "Haz una foto guiada de tu mascota.", "▣", Color(0xFFFFF0E4), Modifier.testTag("petiCheckCamera")) { cameraXCaptureType = MediaType.IMAGE }
                    PetiCaptureOption("Vídeo", "Observa comportamiento, movimiento y postura.", "▶", Color(0xFFFFE9E5), Modifier.testTag("petiCheckCameraVideo")) { cameraXCaptureType = MediaType.VIDEO }
                    PetiCaptureOption("Audio", "Analiza sonidos, ladridos o quejidos.", "♬", Color(0xFFF0EAFE), Modifier.testTag("petiCheckAudio")) { audioCaptureOpen = true }
                    PetiCaptureOption("Documento veterinario", "Añade un informe para organizarlo en tu historial.", "▤", Color(0xFFEAF6F4), Modifier.testTag("recordUpload")) { documentPicker.launch("application/pdf") }
                    uploadedDocumentId?.let { mediaId ->
                        Button(modifier = Modifier.testTag("recordCreate"), onClick = {
                            scope.launch {
                                runCatching { services.records.create(selected.id, "{\"source_media_id\":\"$mediaId\",\"document_type\":\"OTHER\",\"title\":\"Veterinary record\"}", UUID.randomUUID().toString()) }
                                    .onSuccess { recordStatus = "Private record added" }
                                    .onFailure { recordStatus = "Record could not be created" }
                            }
                        }) { Text("Guardar documento") }
                    }
                    recordStatus?.let { Text(it, modifier = Modifier.testTag("recordUploadStatus")) }
                    OutlinedTextField(
                        value = userContext,
                        onValueChange = { if (it.length <= 500) userContext = it },
                        label = { Text("¿Qué estás observando? (opcional)") },
                        supportingText = { Text("${userContext.length}/500") },
                        modifier = Modifier.testTag("petiCheckContext"),
                    )
                    uploadTasks.values.filter { it.ownerUserId == current.userId && it.state != MediaUploadState.READY }.forEach { task ->
                        Text("Preparando contenido: ${task.state}", modifier = Modifier.testTag("petiCheckMediaUpload"))
                    }
                    Button(modifier = Modifier.testTag("petiCheck"), onClick = {
                        val error = validator.validate(selectedMedia, userContext)
                        if (error != null) {
                            checkError = error
                        } else if (fundingState.quote?.operationType != OperationType.PETI_CHECK) {
                            checkError = "Preparando el análisis. Inténtalo de nuevo en unos segundos."
                            fundingViewModel.request(OperationType.PETI_CHECK)
                        } else if (fundingState.quote?.currentlyFundable != true) {
                            checkError = "Este análisis no está disponible en este momento. Inténtalo de nuevo más tarde."
                        } else scope.launch {
                            checkError = null
                            runCatching {
                                val requestId = UUID.randomUUID().toString()
                                val reservationId = fundingViewModel.reserve(
                                    OperationType.PETI_CHECK,
                                    requestId,
                                    "peti-check-$requestId",
                                )
                                services.analysis.create(
                                    selected.id,
                                    selectedMedia.map { it.mediaId },
                                    reservationId,
                                    requestId,
                                    userContext.trim().takeIf { it.isNotEmpty() },
                                )
                            }.onSuccess { created ->
                                checkState = created
                                activeJobId = created.id
                                var currentJob = created
                                for (poll in 0 until 60) {
                                    if (currentJob.status in setOf(AnalysisStatus.COMPLETED, AnalysisStatus.FAILED_FINAL, AnalysisStatus.CANCELED)) break
                                    delay(2_000)
                                    currentJob = services.analysis.get(created.id)
                                    checkState = AnalysisStatusReducer().reduce(checkState, currentJob)
                                    if (currentJob.status in setOf(AnalysisStatus.COMPLETED, AnalysisStatus.FAILED_FINAL, AnalysisStatus.CANCELED)) break
                                    if (poll == 59) checkError = "This check is taking longer than expected. You can leave this screen and reopen it from history."
                                }
                            }
                                .onFailure { checkError = it.message ?: "PETI Check could not be submitted" }
                        }
                    }) { Text("Iniciar análisis") }
                    checkError?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.testTag("petiCheckError")) }
                    checkState?.let { job ->
                        Text("Estado: ${customerCheckStatus(job.status)}", modifier = Modifier.testTag("petiCheckStatus"))
                        if (job.status == AnalysisStatus.FAILED_FINAL) {
                            Text("Inténtalo de nuevo más tarde.", modifier = Modifier.testTag("petiCheckFailure"))
                        }
                        job.result?.let { result ->
                            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), elevation = CardDefaults.cardElevation(2.dp), modifier = Modifier.fillMaxWidth().testTag("petiCheckResultCard")) {
                            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("Resultado del análisis", style = MaterialTheme.typography.titleLarge, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold)
                            if (result.safetyState == "URGENT") {
                                Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFFFE8E4)), modifier = Modifier.fillMaxWidth().testTag("urgentSafetyBanner")) { Text("Atención prioritaria: busca ayuda veterinaria ahora.", Modifier.padding(12.dp), color = MaterialTheme.colorScheme.error, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold) }
                            } else if (result.safetyState == "INSUFFICIENT_EVIDENCE") {
                                Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF4E6)), modifier = Modifier.fillMaxWidth().testTag("insufficientEvidenceBanner")) { Column(Modifier.padding(12.dp)) { Text("Necesitamos evidencia más clara.", fontWeight = androidx.compose.ui.text.font.FontWeight.Bold); Text("Prueba una toma bien iluminada o vuelve a capturar el área.", modifier = Modifier.testTag("recaptureGuidance")) } }
                            } else {
                                AssistChip(onClick = {}, label = { Text("Estado: ${result.safetyState}") })
                            }
                            Text(result.summary, modifier = Modifier.testTag("petiCheckSummary"))
                            if (result.redFlags.isNotEmpty()) {
                                Text("Señales de alerta", style = MaterialTheme.typography.titleMedium, modifier = Modifier.testTag("petiCheckRedFlagsHeading"))
                            }
                            result.observations.forEach { Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFE2F7F4)), shape = MaterialTheme.shapes.medium, modifier = Modifier.fillMaxWidth().testTag("petiCheckObservation")) { Column(Modifier.padding(14.dp)) { Text("Observado por PETi", fontWeight = androidx.compose.ui.text.font.FontWeight.Bold, color = Color(0xFF008F87)); Text(it) } } }
                            result.interpretations.forEach { Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF3E6)), shape = MaterialTheme.shapes.medium, modifier = Modifier.fillMaxWidth().testTag("petiCheckInterpretation")) { Column(Modifier.padding(14.dp)) { Text("Posible interpretación", fontWeight = androidx.compose.ui.text.font.FontWeight.Bold, color = MaterialTheme.colorScheme.secondary); Text(it) } } }
                            result.uncertainties.forEach { Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFF3F0FF)), shape = MaterialTheme.shapes.medium, modifier = Modifier.fillMaxWidth().testTag("petiCheckUncertainty")) { Column(Modifier.padding(14.dp)) { Text("Qué no podemos saber", fontWeight = androidx.compose.ui.text.font.FontWeight.Bold); Text(it) } } }
                            result.redFlags.forEach { Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFFFE8E4)), shape = MaterialTheme.shapes.medium, modifier = Modifier.fillMaxWidth().testTag("petiCheckRedFlag")) { Column(Modifier.padding(14.dp)) { Text("Señal de alerta", fontWeight = androidx.compose.ui.text.font.FontWeight.Bold, color = MaterialTheme.colorScheme.error); Text(it) } } }
                            result.recommendedActions.forEach { Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFEAF6F4)), shape = MaterialTheme.shapes.medium, modifier = Modifier.fillMaxWidth().testTag("petiCheckAction")) { Column(Modifier.padding(14.dp)) { Text("Qué puedes hacer ahora", fontWeight = androidx.compose.ui.text.font.FontWeight.Bold, color = Color(0xFF008F87)); Text(it) } } }
                            Text("Calidad de la evidencia: ${result.evidenceQuality}", modifier = Modifier.testTag("evidenceQuality"))
                            result.limitations.forEach { limitation ->
                                Text("Límite: $limitation", modifier = Modifier.testTag("petiCheckLimitation"))
                            }
                            if (result.sourceMediaIds.isNotEmpty()) {
                                Text("Evidencia utilizada: ${result.sourceMediaIds.joinToString()}", modifier = Modifier.testTag("petiCheckSourceMedia"))
                            }
                            }
                            }
                        }
                    }
                    Button(
                        modifier = Modifier.testTag("petiCheckHistory"),
                        onClick = { scope.launch { checkHistory = services.analysis.listHistory(selected.id) } },
                    ) { Text("Ver historial de análisis") }
                    checkHistory.forEach { historical ->
                        Text(
                            "${historical.id}: ${historical.status}",
                            modifier = Modifier
                                .testTag("petiCheckHistory-${historical.id}")
                                .clickable { scope.launch { checkState = services.analysis.get(historical.id) } }
                                .padding(8.dp),
                        )
                    }
                }
                state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                HorizontalDivider()
                    }
                    }
                    }
            }
            else -> Text("No se puede iniciar sesión ahora. Inténtalo de nuevo.")
        }
        }
        NavigationBar(containerColor = MaterialTheme.colorScheme.surface, modifier = Modifier.height(80.dp)) {
            listOf("HOME" to ("Inicio" to Icons.Default.Home), "SCAN" to ("Analizar" to Icons.Default.CameraAlt), "HISTORY" to ("Historial" to Icons.Default.History), "PROFILE" to ("Perfil" to Icons.Default.Person)).forEach { (key, labelAndIcon) ->
                val (label, icon) = labelAndIcon
                NavigationBarItem(selected = activeSection == key, enabled = state.selected != null || key == "HOME", onClick = { activeSection = key }, modifier = Modifier.testTag("nav-$key"), icon = { Icon(icon, contentDescription = label, modifier = Modifier.size(22.dp)) }, label = { Text(label, style = MaterialTheme.typography.labelSmall) })
            }
        }
    }
}

private fun customerCheckStatus(status: AnalysisStatus): String = when (status) {
    AnalysisStatus.CREATED, AnalysisStatus.FUNDING_RESERVED -> "Preparing"
    AnalysisStatus.QUEUED -> "Queued"
    AnalysisStatus.PREPARING_MEDIA -> "Preparing"
    AnalysisStatus.CALLING_PROVIDER -> "Analyzing"
    AnalysisStatus.VALIDATING_OUTPUT, AnalysisStatus.APPLYING_GUARDRAILS, AnalysisStatus.APPLYING_SAFETY, AnalysisStatus.PERSISTING_RESULT -> "Checking result"
    AnalysisStatus.COMPLETED -> "Complete"
    AnalysisStatus.FAILED_RETRYABLE -> "Temporarily unavailable — retrying"
    AnalysisStatus.FAILED_FINAL -> "Could not complete this check"
    AnalysisStatus.CANCELED -> "Canceled"
}
