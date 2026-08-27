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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
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
    override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); pendingOccurrence.value = CareDeepLink.occurrenceId(intent?.data?.toString()); setContent { MaterialTheme { Surface(Modifier.fillMaxSize()) { Phase1App(this@MainActivity, pendingOccurrence.value) } } } }
    override fun onNewIntent(intent: Intent) { super.onNewIntent(intent); setIntent(intent); pendingOccurrence.value = CareDeepLink.occurrenceId(intent.data?.toString()) }
}

@Composable
private fun Phase1App(activity: ComponentActivity, pendingOccurrenceId: String? = null) {
    val scope = rememberCoroutineScope(); val context = LocalContext.current; val services = remember { createAppServices(context) }; val auth = services.auth; val pets = services.pets; val species = services.species
    var authState by remember { mutableStateOf<AuthState>(auth.authState.value) }; var name by remember { mutableStateOf("") }; var editName by remember { mutableStateOf("") }
    val petViewModel: PetViewModel = viewModel(factory = object : androidx.lifecycle.ViewModelProvider.Factory { override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T = PetViewModel(pets, species, PersistentSelectedPetStore(context)) as T }); val state by petViewModel.state.collectAsState()
    LaunchedEffect(authState) {
        val restored = authState as? AuthState.Authenticated ?: return@LaunchedEffect
        petViewModel.load(restored.userId)
    }
    val rewardedAds = if (AppConfig.environment == AppEnvironment.LOCAL) FakeRewardedAdGateway() else AdMobRewardedAdGateway(activity, BuildConfig.PETI_ADMOB_REWARDED_AD_UNIT_ID)
    val fundingViewModel: FundingViewModel = viewModel(factory = object : androidx.lifecycle.ViewModelProvider.Factory { override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T = FundingViewModel(services.funding, rewardedAds) as T }); val fundingState by fundingViewModel.state.collectAsState()
    Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("PETi", style = MaterialTheme.typography.headlineLarge); Text("Environment: ${AppConfig.environment.name}")
        pendingOccurrenceId?.let { Text("Care reminder opened: $it", modifier = Modifier.testTag("careDeepLinkOccurrence")) }
        when (val current = authState) {
            AuthState.SignedOut -> Button(modifier = Modifier.testTag("signIn"), onClick = { scope.launch { auth.signIn(); authState = auth.authState.value; if (authState is AuthState.Authenticated) petViewModel.load((authState as AuthState.Authenticated).userId) } }) { Text("Continue with Google") }
            is AuthState.Authenticated -> {
                LaunchedEffect(current.userId) { PetiMessagingRegistration.registerCurrent(context) }
                Text("Your pets"); if (state.pets.isEmpty() && !state.loading) Text("No pets yet")
                LazyColumn(Modifier.weight(1f, fill = false)) { items(state.pets) { pet -> Text("${pet.displayName} · ${pet.species}", Modifier.testTag("pet-${pet.id}").semantics { role = Role.Button; contentDescription = "Select ${pet.displayName}, ${pet.species}" }.clickable { petViewModel.select(current.userId, pet); editName = pet.displayName }.padding(12.dp)) } }
                OutlinedTextField(name, { name = it }, label = { Text("Pet name") }, modifier = Modifier.testTag("petName"))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { Button(modifier = Modifier.testTag("createPet"), onClick = { if (name.isNotBlank()) { petViewModel.create(name, current.userId); name = "" } }) { Text("Add pet") }; Button(onClick = { scope.launch { services.mediaUpload.clearAccount(current.userId); services.records.clearLocalAccount(); auth.signOut(); authState = AuthState.SignedOut } }) { Text("Sign out") } }
                state.selected?.let { selected -> Text("Selected: ${selected.displayName}"); OutlinedTextField(editName, { editName = it }, label = { Text("Edit pet name") }); Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { Button(onClick = { petViewModel.update(editName) }) { Text("Save") }; Button(onClick = { petViewModel.deleteSelected(current.userId) }) { Text("Delete") } } }
                state.selected?.let { selected ->
                    Phase6Panel(services.phase6, selected.id, pendingOccurrenceId, Modifier.testTag("phase6Panel"))
                    RecordsPanel(services.records, selected.id, Modifier.testTag("recordsPanel")) { readUrl ->
                        runCatching { activity.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(readUrl))) }
                            .onFailure { /* Keep the short-lived URL out of app state if no viewer is installed. */ }
                    }
                    SpecialistPanel(services.specialists, fundingViewModel, selected.id, Modifier.testTag("specialistPanel"))
                    ReportsPanel(services.reports, selected.id, Modifier.testTag("reportsPanel"))
                    FuturePanel(services.future, selected.id, Modifier.testTag("futurePanel"))
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
                                .onFailure { checkError = "Unable to restore this check" }
                        }
                    }
                    Text("PETi Check", style = MaterialTheme.typography.titleMedium)
                    Text("Use selected photo or video to record what you are noticing. PETi Check is non-diagnostic.")
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
                    Button(modifier = Modifier.testTag("petiCheckMedia"), onClick = { mediaPicker.launch("image/*") }) { Text("Choose media") }
                    Button(modifier = Modifier.testTag("petiCheckCamera"), onClick = { cameraXCaptureType = MediaType.IMAGE }) { Text("Take photo") }
                    Button(modifier = Modifier.testTag("petiCheckCameraVideo"), onClick = { cameraXCaptureType = MediaType.VIDEO }) { Text("Record video") }
                    Button(modifier = Modifier.testTag("petiCheckAudio"), onClick = { audioCaptureOpen = true }) { Text("Record audio") }
                    Button(modifier = Modifier.testTag("recordUpload"), onClick = { documentPicker.launch("application/pdf") }) { Text("Add veterinary document") }
                    uploadedDocumentId?.let { mediaId ->
                        Button(modifier = Modifier.testTag("recordCreate"), onClick = {
                            scope.launch {
                                runCatching { services.records.create(selected.id, "{\"source_media_id\":\"$mediaId\",\"document_type\":\"OTHER\",\"title\":\"Veterinary record\"}", UUID.randomUUID().toString()) }
                                    .onSuccess { recordStatus = "Private record added" }
                                    .onFailure { recordStatus = "Record could not be created" }
                            }
                        }) { Text("Save document to Records") }
                    }
                    recordStatus?.let { Text(it, modifier = Modifier.testTag("recordUploadStatus")) }
                    OutlinedTextField(
                        value = userContext,
                        onValueChange = { if (it.length <= 500) userContext = it },
                        label = { Text("What are you noticing? (optional)") },
                        supportingText = { Text("${userContext.length}/500") },
                        modifier = Modifier.testTag("petiCheckContext"),
                    )
                    uploadTasks.values.filter { it.ownerUserId == current.userId && it.state != MediaUploadState.READY }.forEach { task ->
                        Text("Preparing media: ${task.state}", modifier = Modifier.testTag("petiCheckMediaUpload"))
                    }
                    Button(modifier = Modifier.testTag("petiCheck"), onClick = {
                        val error = validator.validate(selectedMedia, userContext)
                        if (error != null) {
                            checkError = error
                        } else if (fundingState.quote?.operationType != OperationType.PETI_CHECK) {
                            checkError = "Get a current funding quote before starting PETi Check"
                            fundingViewModel.request(OperationType.PETI_CHECK)
                        } else if (fundingState.quote?.currentlyFundable != true) {
                            checkError = "PETI_CHECK_FUNDING_REQUIRED: choose the voluntary rewarded option below"
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
                    }) { Text("Start PETi Check") }
                    checkError?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.testTag("petiCheckError")) }
                    checkState?.let { job ->
                        Text("Check status: ${customerCheckStatus(job.status)}", modifier = Modifier.testTag("petiCheckStatus"))
                        if (job.status == AnalysisStatus.FAILED_FINAL) {
                            Text("Please try again later.", modifier = Modifier.testTag("petiCheckFailure"))
                        }
                        job.result?.let { result ->
                            if (result.safetyState == "URGENT") {
                                Text(
                                    "URGENT: seek veterinary help now",
                                    style = MaterialTheme.typography.titleLarge,
                                    color = MaterialTheme.colorScheme.error,
                                    modifier = Modifier.testTag("urgentSafetyBanner"),
                                )
                            } else if (result.safetyState == "INSUFFICIENT_EVIDENCE") {
                                Text(
                                    "There is not enough clear evidence in this media to assess reliably.",
                                    style = MaterialTheme.typography.titleMedium,
                                    modifier = Modifier.testTag("insufficientEvidenceBanner"),
                                )
                                Text(
                                    "Try a clearer, well-lit close-up or recapture the area of concern.",
                                    modifier = Modifier.testTag("recaptureGuidance"),
                                )
                            } else {
                                Text("Safety: ${result.safetyState}")
                            }
                            Text(result.summary, modifier = Modifier.testTag("petiCheckSummary"))
                            if (result.redFlags.isNotEmpty()) {
                                Text("Red flags", style = MaterialTheme.typography.titleMedium, modifier = Modifier.testTag("petiCheckRedFlagsHeading"))
                            }
                            result.observations.forEach { Text("Observation: $it", modifier = Modifier.testTag("petiCheckObservation")) }
                            result.interpretations.forEach { Text("Possible interpretation: $it", modifier = Modifier.testTag("petiCheckInterpretation")) }
                            result.uncertainties.forEach { Text("Uncertainty: $it", modifier = Modifier.testTag("petiCheckUncertainty")) }
                            result.redFlags.forEach { Text("Red flag: $it", modifier = Modifier.testTag("petiCheckRedFlag")) }
                            result.recommendedActions.forEach { Text("Recommended action: $it", modifier = Modifier.testTag("petiCheckAction")) }
                            Text("Evidence quality: ${result.evidenceQuality}", modifier = Modifier.testTag("evidenceQuality"))
                            result.limitations.forEach { limitation ->
                                Text("Limitation: $limitation", modifier = Modifier.testTag("petiCheckLimitation"))
                            }
                            if (result.sourceMediaIds.isNotEmpty()) {
                                Text("Source media: ${result.sourceMediaIds.joinToString()}", modifier = Modifier.testTag("petiCheckSourceMedia"))
                            }
                        }
                    }
                    Button(
                        modifier = Modifier.testTag("petiCheckHistory"),
                        onClick = { scope.launch { checkHistory = services.analysis.listHistory(selected.id) } },
                    ) { Text("View PETi Check history") }
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
                Text("Cloud funding", style = MaterialTheme.typography.titleMedium)
                fundingState.summary?.let { Text("Available credits: ${it.availableCredits}") }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(modifier = Modifier.testTag("fundingQuote"), onClick = { fundingViewModel.request(OperationType.PETI_CHECK) }) { Text("Check PETi Check funding") }
                    Button(modifier = Modifier.testTag("refreshCredits"), onClick = { fundingViewModel.refresh() }) { Text("Refresh credits") }
                }
                fundingState.quote?.let { quote ->
                    Text("Photo analysis: ${quote.requiredCredits} credit")
                    if (!quote.currentlyFundable && quote.rewardedAdAvailable) Button(modifier = Modifier.testTag("watchRewardedAd"), onClick = { fundingViewModel.watchAdAndRefresh() }) { Text("Watch ad to fund") }
                }
                fundingState.status.takeIf { it.isNotBlank() }?.let { Text(it) }
                fundingState.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            }
            else -> Text("Authentication unavailable. Please retry.")
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
